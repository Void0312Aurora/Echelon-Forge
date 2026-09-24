from __future__ import annotations

import pytest

from python.tasking_contracts.joint_scripted_coordination import (
    JOINT_SCRIPTED_COORDINATION_MODEL_ID,
    JOINT_SCRIPTED_MODEL_REGISTRY,
    SCRIPTED_JOINT_TASK_GRAPH_VERSION,
    ScriptedJointCoordinationIntent,
    ScriptedJointTaskGraph,
)
from python.tasking_contracts.scripted_runtime import (
    SCRIPTED_RUNTIME_ACTION_DECIDED,
    ScriptedRuntimeAgent,
    ScriptedRuntimeAgentSpec,
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
    agent = ScriptedRuntimeAgent(
        ScriptedRuntimeAgentSpec(
            agent_id="joint:director",
            model_id=JOINT_SCRIPTED_COORDINATION_MODEL_ID,
            domain="joint",
            role_id="joint_coordination_director",
            decision_period_s=1.0,
            action_hold_s=1.0,
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
        assert result.report.action_source == SCRIPTED_RUNTIME_ACTION_DECIDED
        assert isinstance(result.action, ScriptedJointCoordinationIntent)
        assert result.action.graph_id == "joint.air_naval_screen_demo_v1"
        assert result.action.target_node_ids == ("air:lead", "naval:screen", "joint:director")
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
