from __future__ import annotations

import numpy as np
import pytest

from python.tasking_contracts.air.registry import AIR_SCRIPTED_MODEL_REGISTRY
from python.tasking_contracts.air.execution.model import AIR_SCRIPTED_EXECUTION_MODEL_ID
from python.tasking_contracts.joint.coordination import (
    JOINT_SCRIPTED_COORDINATION_MODEL_ID,
    JOINT_SCRIPTED_MODEL_REGISTRY,
    SCRIPTED_JOINT_TASK_GRAPH_VERSION,
    ScriptedJointCoordinationIntent,
    ScriptedJointTaskGraph,
)
from python.tasking_contracts.joint.runtime import ScriptedJointRuntimeConsumer
from python.tasking_contracts.joint.command_link import ScriptedJointCommandLink
from python.tasking_contracts.naval.execution import (
    NAVAL_SCRIPTED_MODEL_REGISTRY,
    NAVAL_STATION_HOLD_MODEL_ID,
)
from python.tasking_contracts.joint.projection import (
    project_joint_intent_to_compiled_packet,
)
from python.tasking_contracts.common.decision_runtime import (
    DECISION_RUNTIME_ACTION_DECIDED,
    DecisionRuntimeAgent,
    DecisionRuntimeAgentSpec,
)


def _graph() -> dict:
    return {
        "version": SCRIPTED_JOINT_TASK_GRAPH_VERSION,
        "graph_id": "joint.air_naval_screen_demo_v1",
        "task_group_id": 17,
        "coordination_mode": "support",
        "nodes": [
            {
                "node_id": "air:lead",
                "domain": "air",
                "role_id": "autopilot_controller",
                "service_profile": "air_force",
                "task_group_id": 17,
                "coordination_mode": "support",
                "authority_scope": "platform_control",
                "payload_ref": "air.execution.phase_scripted",
            },
            {
                "node_id": "naval:screen",
                "domain": "naval",
                "role_id": "naval_warfare_commander",
                "service_profile": "navy",
                "task_group_id": 17,
                "coordination_mode": "support",
                "authority_scope": "naval_station_command",
                "payload_ref": "naval.station.screen_hold",
            },
            {
                "node_id": "joint:director",
                "domain": "joint",
                "role_id": "joint_coordination_director",
                "service_profile": "joint",
                "task_group_id": 17,
                "coordination_mode": "support",
                "authority_scope": "task_graph_coordination",
                "payload_ref": JOINT_SCRIPTED_COORDINATION_MODEL_ID,
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
                "supporting_node_id": "naval:screen",
                "supported_node_id": "air:lead",
            },
        ],
    }


def test_joint_task_graph_is_versioned_and_keeps_domain_payloads_as_references() -> None:
    graph = ScriptedJointTaskGraph.from_mapping(_graph())
    assert graph.graph_id == "joint.air_naval_screen_demo_v1"
    assert graph.task_group_id == 17
    assert graph.active_node_ids() == ("air:lead", "naval:screen", "joint:director")
    assert {node.payload_ref for node in graph.nodes} == {
        "air.execution.phase_scripted",
        "naval.station.screen_hold",
        JOINT_SCRIPTED_COORDINATION_MODEL_ID,
    }


def test_joint_coordination_producer_runs_through_neutral_runtime() -> None:
    model = JOINT_SCRIPTED_MODEL_REGISTRY.create_for(
        domain="joint",
        role_id="joint_coordination_director",
        model_id=JOINT_SCRIPTED_COORDINATION_MODEL_ID,
    )
    agent = DecisionRuntimeAgent(
        DecisionRuntimeAgentSpec(
            agent_id="joint:director",
            model_id=JOINT_SCRIPTED_COORDINATION_MODEL_ID,
            domain="joint",
            role_id="joint_coordination_director",
            decision_period_s=1.0,
            communication_state="available",
            authority_scope="task_graph_coordination",
        ),
        model,
    )
    try:
        agent.reset(context={"task_graph": _graph()}, episode_seed=11)
        result = agent.step(
            observation={"declared_tracks": []},
            clock_s=0.0,
            observation_version="joint:0",
            context={},
        )
        assert result.report.action_source == DECISION_RUNTIME_ACTION_DECIDED
        assert isinstance(result.action, ScriptedJointCoordinationIntent)
        assert result.action.graph_id == "joint.air_naval_screen_demo_v1"
        assert result.action.target_node_ids == ("air:lead",)
        assert result.action.clock_s == 0.0
        assert result.action.observation_version == "joint:0"
        assert result.action.communication_state == "available"
        assert result.action.authority_scope == "task_graph_coordination"
    finally:
        agent.close()


def test_joint_task_graph_rejects_mismatched_node_group_and_unknown_edge() -> None:
    mismatched = _graph()
    mismatched["nodes"][1]["task_group_id"] = 18
    with pytest.raises(ValueError, match="task_group_id"):
        ScriptedJointTaskGraph.from_mapping(mismatched)

    unknown_edge = _graph()
    unknown_edge["authority_edges"][0]["child_node_id"] = "missing:node"
    with pytest.raises(ValueError, match="unknown node"):
        ScriptedJointTaskGraph.from_mapping(unknown_edge)

    multiple_directors = _graph()
    multiple_directors["nodes"].append(
        {
            **multiple_directors["nodes"][2],
            "node_id": "joint:assistant",
            "role_id": "joint_coordination_assistant",
        }
    )
    with pytest.raises(ValueError, match="exactly one active joint director"):
        ScriptedJointTaskGraph.from_mapping(multiple_directors)


def test_joint_intent_projection_keeps_unrepresented_common_fields_explicit() -> None:
    class _Roster:
        def __init__(self) -> None:
            self.roster_id = ""

    class _Packet:
        def __init__(self) -> None:
            self.source_type = "policy"
            self.source_id = ""
            self.update_clock = "adapter_step"
            self.merge_policy = "last_write_wins"
            self.target_roster = _Roster()
            self.produced_tasking_refs = []

    class _Ref:
        def __init__(self) -> None:
            self.kind = "unspecified"
            self.reference_id = ""

    class _Binding:
        CoordinationIntentPacket = _Packet
        ProducedIntentRef = _Ref

    model = JOINT_SCRIPTED_MODEL_REGISTRY.create_for(
        domain="joint",
        role_id="joint_coordination_director",
        model_id=JOINT_SCRIPTED_COORDINATION_MODEL_ID,
    )
    agent = DecisionRuntimeAgent(
        DecisionRuntimeAgentSpec(
            agent_id="joint:director",
            model_id=JOINT_SCRIPTED_COORDINATION_MODEL_ID,
            domain="joint",
            role_id="joint_coordination_director",
        ),
        model,
    )
    try:
        agent.reset(context={"task_graph": _graph()}, episode_seed=3)
        intent = agent.step(observation={}, clock_s=1.25, observation_version="joint:5").action
        projection = project_joint_intent_to_compiled_packet(intent, binding_module=_Binding)
        assert projection.packet.source_type == "scripted"
        assert projection.packet.source_id == "joint:director"
        assert projection.packet.target_roster.roster_id == "joint.air_naval_screen_demo_v1"
        assert [ref.reference_id for ref in projection.packet.produced_tasking_refs] == ["air:lead"]
        assert "task_group_id" in projection.omitted_fields
        assert "clock_s" in projection.omitted_fields
    finally:
        agent.close()


def test_joint_task_graph_consumes_air_naval_and_joint_nodes_on_one_runtime() -> None:
    consumer = ScriptedJointRuntimeConsumer(
        ScriptedJointTaskGraph.from_mapping(_graph()),
        registries={
            "air": AIR_SCRIPTED_MODEL_REGISTRY,
            "naval": NAVAL_SCRIPTED_MODEL_REGISTRY,
            "joint": JOINT_SCRIPTED_MODEL_REGISTRY,
        },
        factory_kwargs_by_node={
            "air:lead": {"action_dim": 17, "dt": 0.05},
            "naval:screen": {"action_dim": 3},
        },
    )
    air_observation = {
        "instruments": np.zeros((31,), dtype=np.float32),
        "mission": np.asarray([1.0, 90.0, 1000.0, 120.0], dtype=np.float32),
    }
    try:
        consumer.reset(
            context_by_node={
                "air:lead": {"observation": air_observation, "phase_name": "scramble"},
                "naval:screen": {"scenario": "n4"},
            },
            episode_seed=19,
        )
        first = consumer.step(
            observations={
                "air:lead": air_observation,
                "naval:screen": None,
                "joint:director": {},
            },
            clock_s=0.0,
            observation_versions={
                "air:lead": "air:0",
                "naval:screen": "naval:0",
                "joint:director": "joint:0",
            },
        )
        held = consumer.step(
            observations={
                "air:lead": air_observation,
                "naval:screen": None,
                "joint:director": {},
            },
            clock_s=0.1,
            observation_versions={
                "air:lead": "air:1",
                "naval:screen": "naval:1",
                "joint:director": "joint:1",
            },
        )
        assert consumer.active_node_ids == ("air:lead", "naval:screen", "joint:director")
        assert set(first) == set(consumer.active_node_ids)
        assert first["air:lead"].report.domain == "air"
        assert first["naval:screen"].report.domain == "naval"
        assert first["joint:director"].report.domain == "joint"
        assert first["air:lead"].action.shape == (17,)
        assert first["naval:screen"].action.shape == (3,)
        assert first["joint:director"].action.graph_id == "joint.air_naval_screen_demo_v1"
        assert held["air:lead"].report.action_source == "held"
        assert held["naval:screen"].report.action_source == "held"
        assert held["joint:director"].report.action_source == "held"
        assert consumer.roster.agent("air:lead").replay_identity.endswith("seed=19:reset=1")
        routed = consumer.route_intent(first["joint:director"].action, clock_s=0.1, delay_s=0.2)
        assert [item.target_node_id for item in routed] == ["air:lead"]
        consumer.step(
            observations={
                "air:lead": air_observation,
                "naval:screen": None,
                "joint:director": {},
            },
            clock_s=0.2,
            observation_versions={
                "air:lead": "air:2",
                "naval:screen": "naval:2",
                "joint:director": "joint:2",
            },
        )
        assert consumer.last_delivered_commands == ()
        consumer.step(
            observations={
                "air:lead": air_observation,
                "naval:screen": None,
                "joint:director": {},
            },
            clock_s=0.3,
            observation_versions={
                "air:lead": "air:3",
                "naval:screen": "naval:3",
                "joint:director": "joint:3",
            },
        )
        assert [item.target_node_id for item in consumer.last_delivered_commands] == ["air:lead"]
        assert set(consumer.pending_command_inboxes) == {"air:lead"}

        consumer.step(
            observations={
                "air:lead": air_observation,
                "naval:screen": None,
                "joint:director": {},
            },
            clock_s=1.0,
            observation_versions={
                "air:lead": "air:10",
                "naval:screen": "naval:10",
                "joint:director": "joint:10",
            },
        )
        assert consumer.pending_command_inboxes == {}
    finally:
        consumer.close()


def test_joint_command_link_rejects_unknown_nodes_and_clock_reversal() -> None:
    link = ScriptedJointCommandLink(ScriptedJointTaskGraph.from_mapping(_graph()))
    try:
        with pytest.raises(KeyError, match="active graph nodes"):
            link.send(
                source_node_id="joint:director",
                target_node_id="missing:node",
                payload={},
                clock_s=0.0,
            )
        link.send(
            source_node_id="joint:director",
            target_node_id="air:lead",
            payload={"command": "hold"},
            clock_s=1.0,
            delay_s=1.0,
        )
        with pytest.raises(ValueError, match="clock moved backwards"):
            link.deliver(clock_s=0.5)
        assert link.deliver(clock_s=2.0)[0].payload == {"command": "hold"}
    finally:
        link.close()


@pytest.mark.parametrize("ttl_s,drop_prob,expected", [(0.5, 0.0, 0), (2.0, 0.0, 1), (2.0, 1.0, 0)])
def test_joint_inbox_checks_lifetime_at_domain_decision(
    monkeypatch, ttl_s, drop_prob, expected
) -> None:
    consumer = ScriptedJointRuntimeConsumer(
        ScriptedJointTaskGraph.from_mapping(_graph()),
        registries={
            "air": AIR_SCRIPTED_MODEL_REGISTRY,
            "naval": NAVAL_SCRIPTED_MODEL_REGISTRY,
            "joint": JOINT_SCRIPTED_MODEL_REGISTRY,
        },
        factory_kwargs_by_node={
            "air:lead": {"action_dim": 17, "dt": 0.05},
            "naval:screen": {"action_dim": 3},
        },
    )
    observation = {
        "instruments": np.zeros(31, dtype=np.float32),
        "mission": np.asarray([1, 90, 1000, 120], dtype=np.float32),
    }
    observations = {"air:lead": observation, "naval:screen": None, "joint:director": {}}
    received = []
    model = consumer.roster.agent("air:lead").model
    original_decide = model.decide

    def capture(*, observation, context=None, dt=0.0):
        received.append(tuple(context.get("joint_command_inbox", ())))
        return original_decide(observation=observation, context=context, dt=dt)

    monkeypatch.setattr(model, "decide", capture)
    try:
        consumer.reset(
            context_by_node={"air:lead": {"observation": observation, "phase_name": "scramble"}},
            episode_seed=19,
        )
        first = consumer.step(observations=observations, clock_s=0.0)
        consumer.route_intent(
            first["joint:director"].action,
            clock_s=0.1,
            delay_s=0.2,
            ttl_s=ttl_s,
            drop_prob=drop_prob,
        )
        consumer.step(observations=observations, clock_s=0.3)
        assert len(received) == 1
        assert bool(consumer.pending_command_inboxes) == (drop_prob == 0.0)
        consumer.step(observations=observations, clock_s=1.0)
        assert len(received[-1]) == expected
        assert consumer.pending_command_inboxes == {}
    finally:
        consumer.close()


def test_joint_command_link_rejects_support_only_edges() -> None:
    link = ScriptedJointCommandLink(ScriptedJointTaskGraph.from_mapping(_graph()))
    try:
        with pytest.raises(ValueError, match="undeclared command edge"):
            link.send(
                source_node_id="joint:director",
                target_node_id="naval:screen",
                payload={"command": "hold"},
                clock_s=0.0,
            )
        assert link.pending == ()
    finally:
        link.close()
