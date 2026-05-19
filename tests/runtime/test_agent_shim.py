from types import SimpleNamespace

import pytest

from python.rl.runtime.agent_shim import (
    COMPATIBILITY_ADAPTER,
    DIAGNOSTICS_ONLY,
    MAINTAINED,
    MERGE_REJECT_ON_CONFLICT,
    OBS_AGENT_OBSERVATION_COMPAT,
    OBS_DIAGNOSTICS_ORACLE,
    OBS_FACADE_OBSERVATION_PACKET,
    OBS_RAW_WORLD_TRUTH,
    ActionIntentCompat,
    CoordinationIntentCompat,
    observation_provenance,
    roster_slot_role,
    single_agent_role,
)


def test_observation_provenance_labels_classify_boundaries():
    maintained = observation_provenance(
        OBS_FACADE_OBSERVATION_PACKET,
        consumed_snapshot_version="global:7",
        observation_packet_id="obs:7",
    )
    compat = observation_provenance(OBS_AGENT_OBSERVATION_COMPAT)
    raw_truth = observation_provenance(OBS_RAW_WORLD_TRUTH)

    assert maintained.maintained_status == MAINTAINED
    assert maintained.is_maintained
    assert maintained.consumed_snapshot_version == "global:7"
    assert compat.maintained_status == COMPATIBILITY_ADAPTER
    assert raw_truth.maintained_status == DIAGNOSTICS_ONLY
    assert raw_truth.is_diagnostics_only


def test_observation_provenance_keeps_truth_and_oracle_out_of_maintained_input():
    raw_truth = observation_provenance(
        OBS_RAW_WORLD_TRUTH,
        source_layer="debug_probe",
        diagnostics_note="raw kinematic state",
    )
    oracle = observation_provenance(
        OBS_DIAGNOSTICS_ORACLE,
        source_layer="teacher",
        diagnostics_note="privileged scoring helper",
    )

    assert raw_truth.as_dict() == {
        "label": OBS_RAW_WORLD_TRUTH,
        "information_state_layer": "WorldTruth",
        "source_surface": "raw runtime or SimulationKernel",
        "maintained_status": DIAGNOSTICS_ONLY,
        "source_layer": "debug_probe",
        "consumed_snapshot_version": None,
        "observation_packet_id": None,
        "diagnostics_note": "raw kinematic state",
    }
    assert oracle.information_state_layer == "DecisionBelief"
    assert oracle.maintained_status == DIAGNOSTICS_ONLY
    assert oracle.is_diagnostics_only
    assert "oracle" in oracle.source_surface


def test_unknown_observation_provenance_label_is_rejected():
    with pytest.raises(ValueError):
        observation_provenance("world_truth_but_safe")


def test_maintained_agent_role_uses_facade_observation_packet_metadata():
    source = observation_provenance(
        OBS_FACADE_OBSERVATION_PACKET,
        source_layer="facade",
        consumed_snapshot_version="global:11",
        observation_packet_id="obs:11",
    )
    role = single_agent_role(
        world_index=4,
        agent_id=12,
        information_state_source=source,
        decision_model_kind="policy",
        decision_model_id="blue-policy-v1",
        maintained_status=MAINTAINED,
    )

    schema = role.as_dict()

    assert schema["maintained_status"] == MAINTAINED
    assert schema["information_state_source"]["label"] == OBS_FACADE_OBSERVATION_PACKET
    assert schema["information_state_source"]["maintained_status"] == MAINTAINED
    assert schema["information_state_source"]["source_layer"] == "facade"
    assert schema["information_state_source"]["consumed_snapshot_version"] == "global:11"
    assert schema["information_state_source"]["observation_packet_id"] == "obs:11"
    assert schema["decision_model_ref"] == {"kind": "policy", "id": "blue-policy-v1"}


def test_diagnostics_agent_role_does_not_promote_oracle_belief_to_policy_input():
    oracle_source = observation_provenance(
        OBS_DIAGNOSTICS_ORACLE,
        source_layer="teacher",
        diagnostics_note="post-hoc reward audit",
    )
    role = single_agent_role(
        agent_id=7,
        information_state_source=oracle_source,
        decision_model_kind="oracle_audit",
        decision_model_id="teacher-debugger",
        maintained_status=DIAGNOSTICS_ONLY,
    )

    schema = role.as_dict()

    assert schema["maintained_status"] == DIAGNOSTICS_ONLY
    assert schema["information_state_source"]["information_state_layer"] == "DecisionBelief"
    assert schema["information_state_source"]["maintained_status"] == DIAGNOSTICS_ONLY
    assert schema["information_state_source"]["diagnostics_note"] == "post-hoc reward audit"
    assert schema["decision_model_ref"]["kind"] == "oracle_audit"


def test_agent_role_exposes_five_elements_without_runtime_dependency():
    role = single_agent_role(
        world_index=2,
        agent_id=42,
        information_state_source=observation_provenance(OBS_AGENT_OBSERVATION_COMPAT),
        decision_model_kind="scripted_controller",
        decision_model_id="ScriptedStableFlightController",
    )

    schema = role.five_elements()

    assert schema["role"] == {
        "role_id": "agent:2:42",
        "role_type": "autopilot_controller",
    }
    assert schema["authority_scope"]["world_index"] == 2
    assert schema["authority_scope"]["entity_ids"] == [42]
    assert schema["information_state_source"]["maintained_status"] == COMPATIBILITY_ADAPTER
    assert schema["decision_model_ref"]["kind"] == "scripted_controller"
    assert schema["action_interface"] == "PilotActionAssignmentCompat"


def test_roster_slot_role_keeps_role_metadata():
    role = roster_slot_role(
        world_index=1,
        entity_id=99,
        roster_index=3,
        role_code=7,
        formation_role_id="wingman",
        policy_route="blue-wingman-policy",
    )

    assert role.role_id == "roster:1:3:99"
    assert role.role_type == "wingman"
    assert role.authority_scope["role_code"] == 7
    assert role.decision_model_ref["id"] == "blue-wingman-policy"


def test_action_intent_wrapper_does_not_mutate_assignment():
    role = single_agent_role(world_index=0, agent_id=11)
    payload = SimpleNamespace(stick_pitch=0.25)
    assignment = SimpleNamespace(world_index=0, entity_id=11, action=payload)

    intent = ActionIntentCompat.from_pilot_assignment(
        assignment,
        role=role,
        input_snapshot_version="global:9",
        effective_time=12.0,
        valid_until=12.1,
        merge_policy=MERGE_REJECT_ON_CONFLICT,
    )

    assert intent.payload is payload
    assert assignment.action is payload
    assert intent.target_world_index == 0
    assert intent.target_entity_id == 11
    assert intent.merge_policy == MERGE_REJECT_ON_CONFLICT
    assert intent.as_dict()["input_snapshot_version"] == "global:9"


def test_coordination_intent_records_payload_fields():
    role = single_agent_role(
        world_index=0,
        agent_id=5,
        role_type="flight_lead",
        action_interface="CommandChainAssignmentCompat",
    )
    mission_command = SimpleNamespace(command_code=3)
    leader_intent = SimpleNamespace(active=True)

    intent = CoordinationIntentCompat(
        role=role,
        mission_command=mission_command,
        leader_intent=leader_intent,
        roster_scope={"team_id": 1},
        update_clock="leader_step",
    )

    assert intent.payload_fields() == ("mission_command", "leader_intent")
    assert intent.as_dict()["roster_scope"] == {"team_id": 1}
    assert intent.as_dict()["update_clock"] == "leader_step"


def test_action_and_coordination_intents_preserve_policy_boundary_metadata():
    role = single_agent_role(
        world_index=0,
        agent_id=31,
        information_state_source=observation_provenance(
            OBS_FACADE_OBSERVATION_PACKET,
            consumed_snapshot_version="global:21",
            observation_packet_id="obs:21",
        ),
        maintained_status=MAINTAINED,
    )
    action = ActionIntentCompat(
        role=role,
        payload=SimpleNamespace(throttle=0.8),
        source_layer="policy",
        source_id="policy:blue:31",
        input_snapshot_version="global:21",
        effective_time=2.0,
        valid_until=2.1,
        target_entity_id=31,
        target_world_index=0,
        maintained_status=MAINTAINED,
    )
    coordination = CoordinationIntentCompat(
        role=role,
        task_order=SimpleNamespace(task_id="hold-station"),
        source_layer="orchestration",
        source_id="director:blue",
        input_snapshot_version="global:21",
        effective_time=2.0,
        valid_until=3.0,
        update_clock="facade_step",
        roster_scope={"team_id": 8, "world_index": 0},
        maintained_status=MAINTAINED,
    )

    action_schema = action.as_dict()
    coordination_schema = coordination.as_dict()

    assert action_schema["role_id"] == role.role_id
    assert action_schema["source_id"] == "policy:blue:31"
    assert action_schema["input_snapshot_version"] == "global:21"
    assert action_schema["maintained_status"] == MAINTAINED
    assert coordination_schema["payload_fields"] == ("task_order",)
    assert coordination_schema["source_layer"] == "orchestration"
    assert coordination_schema["roster_scope"] == {"team_id": 8, "world_index": 0}
    assert coordination_schema["maintained_status"] == MAINTAINED


def test_invalid_status_and_merge_policy_are_rejected():
    with pytest.raises(ValueError):
        single_agent_role(agent_id=1, maintained_status="mainline")

    with pytest.raises(ValueError):
        ActionIntentCompat(
            role=single_agent_role(agent_id=1),
            payload=object(),
            merge_policy="random_order",
        )
