from __future__ import annotations

import ef_py
import numpy as np
import pytest

from python.runtime_bootstrap import resolve_repo_path
from python.simulation.facade_batch import FacadeBatchBackend
from python.simulation.joint.facade import JointFacadeCommandRouter, JointFacadeReportRouter
from python.tasking_contracts.air.execution.model import AIR_SCRIPTED_EXECUTION_MODEL_ID
from python.tasking_contracts.air.registry import AIR_SCRIPTED_MODEL_REGISTRY
from python.tasking_contracts.joint.coordination import (
    JOINT_SCRIPTED_MODEL_REGISTRY,
    SCRIPTED_JOINT_TASK_GRAPH_VERSION,
    ScriptedJointTaskGraph,
)
from python.tasking_contracts.joint.runtime import ScriptedJointRuntimeConsumer
from python.tasking_contracts.naval.execution import (
    NAVAL_SCRIPTED_MODEL_REGISTRY,
    NAVAL_STATION_HOLD_MODEL_ID,
)


DATABASE = resolve_repo_path("examples", "config", "database")


def _graph() -> ScriptedJointTaskGraph:
    return ScriptedJointTaskGraph.from_mapping(
        {
            "version": SCRIPTED_JOINT_TASK_GRAPH_VERSION,
            "graph_id": "joint.facade_air_naval_command_v1",
            "task_group_id": 3,
            "coordination_mode": "support",
            "nodes": [
                {
                    "node_id": "air:lead",
                    "domain": "air",
                    "role_id": "autopilot_controller",
                    "service_profile": "air_force",
                    "task_group_id": 3,
                    "coordination_mode": "support",
                    "authority_scope": "platform_control",
                    "payload_ref": AIR_SCRIPTED_EXECUTION_MODEL_ID,
                },
                {
                    "node_id": "naval:screen",
                    "domain": "naval",
                    "role_id": "naval_warfare_commander",
                    "service_profile": "navy",
                    "task_group_id": 3,
                    "coordination_mode": "support",
                    "authority_scope": "naval_station_command",
                    "payload_ref": NAVAL_STATION_HOLD_MODEL_ID,
                },
                {
                    "node_id": "joint:director",
                    "domain": "joint",
                    "role_id": "joint_coordination_director",
                    "service_profile": "joint",
                    "task_group_id": 3,
                    "coordination_mode": "support",
                    "authority_scope": "task_graph_coordination",
                    "payload_ref": "joint.coordination.task_graph_scripted",
                },
            ],
            "authority_edges": [
                {
                    "parent_node_id": "joint:director",
                    "child_node_id": "air:lead",
                    "relationship": "commands",
                },
                {
                    "parent_node_id": "joint:director",
                    "child_node_id": "naval:screen",
                    "relationship": "supports",
                },
            ],
        }
    )


def _setup(seeds: tuple[int, ...]) -> ef_py.BatchWorldSetupRequest:
    request = ef_py.BatchWorldSetupRequest()
    request.seeds = list(seeds)
    request.time_steps = [0.05]
    air = ef_py.WorldSpawnRequest()
    air.world_index = 0
    air.side = ef_py.Side.Blue
    air.type_name = "F-16C_Block50"
    air.entity_name = "JointAirLead"
    air.is_agent = True
    air.x = 0.0
    air.y = 0.0
    air.z = 1200.0
    air.heading = 90.0
    air.vx = 180.0
    naval = ef_py.WorldSpawnRequest()
    naval.world_index = 0
    naval.side = ef_py.Side.Blue
    naval.type_name = "DDG-51_Flight_I_ASW_Helo_MVP"
    naval.entity_name = "JointNavalScreen"
    naval.is_agent = True
    naval.x = -1400.0
    naval.y = 0.0
    naval.z = 0.0
    naval.heading = 90.0
    naval.vx = 10.29
    request.spawn_requests = [air, naval]
    return request


def _air_command(envelope):
    del envelope
    command = ef_py.MissionCommand()
    command.active = True
    command.command_code = 2
    command.cmd_heading_deg = 90.0
    command.cmd_altitude_m = 1500.0
    command.cmd_speed_mps = 180.0
    return command


def _naval_command(envelope):
    del envelope
    command = ef_py.MissionCommand()
    command.active = True
    command.command_code = 32
    command.cmd_heading_deg = 90.0
    command.cmd_speed_mps = 10.29
    command.reference_entity_id = 1
    command.station_radius_m = 14000.0
    command.station_bearing_deg = 45.0
    return command


def test_joint_graph_routes_opaque_intent_to_air_and_naval_facade_commands() -> None:
    backend = FacadeBatchBackend(database_path=DATABASE, setup_factory=_setup)
    consumer = ScriptedJointRuntimeConsumer(
        _graph(),
        registries={
            "air": AIR_SCRIPTED_MODEL_REGISTRY,
            "naval": NAVAL_SCRIPTED_MODEL_REGISTRY,
            "joint": JOINT_SCRIPTED_MODEL_REGISTRY,
        },
        factory_kwargs_by_node={"air:lead": {"action_dim": 17, "dt": 0.05}, "naval:screen": {"action_dim": 3}},
    )
    try:
        snapshot = backend.reset()
        air_key, naval_key = snapshot.entity_keys
        air_observation = {
            "instruments": np.zeros((31,), dtype=np.float32),
            "mission": np.asarray([1.0, 90.0, 1000.0, 120.0], dtype=np.float32),
        }
        consumer.reset(
            context_by_node={
                "air:lead": {"observation": air_observation, "phase_name": "scramble"},
                "naval:screen": {"scenario": "n4"},
            },
            episode_seed=31,
        )
        first = consumer.step(
            observations={"air:lead": air_observation, "naval:screen": None, "joint:director": {}},
            clock_s=0.0,
        )
        consumer.route_intent(first["joint:director"].action, clock_s=0.0)
        consumer.step(
            observations={"air:lead": air_observation, "naval:screen": None, "joint:director": {}},
            clock_s=0.05,
        )
        router = JointFacadeCommandRouter(
            backend,
            entity_key_by_node={"air:lead": air_key, "naval:screen": naval_key},
            command_builder_by_node={"air:lead": _air_command, "naval:screen": _naval_command},
            task_graph=_graph(),
            ignored_node_ids=("joint:director",),
        )
        assert router.route(consumer.last_delivered_commands[:1]) == ("air:lead",)
        chain = backend.read_command_chain()
        assert chain["mission_commands"][0].shared_core.command_code == 2
        assert router.route(consumer.last_delivered_commands[1:2]) == ()

        def _report(envelope):
            report = ef_py.PilotReport()
            report.active = True
            report.sender_id = int(air_key[1] if envelope.target_node_id == "air:lead" else naval_key[1])
            return report

        report_router = JointFacadeReportRouter(
            backend,
            entity_key_by_node={"air:lead": air_key, "naval:screen": naval_key},
            report_builder_by_node={"air:lead": _report, "naval:screen": _report},
            ignored_node_ids=("joint:director",),
        )
        assert report_router.route(consumer.last_delivered_commands) == ("air:lead",)
        chain = backend.read_command_chain()
        assert chain["pilot_reports"][0].shared_core.active is True
    finally:
        consumer.close()
        backend.close()
