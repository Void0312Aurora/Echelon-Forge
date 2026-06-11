from types import SimpleNamespace

import pytest

from python.rl.runtime.agent_shim import (
  COMPATIBILITY_ADAPTER,
  DIAGNOSTICS_ONLY,
  LAW14_MAINTAINED_READ_LABEL_ALLOWLIST,
  MAINTAINED,
  MERGE_REJECT_ON_CONFLICT,
  OBS_AGENT_OBSERVATION_COMPAT,
  OBS_DECISION_BELIEF_PACKET,
  OBS_DIAGNOSTICS_ORACLE,
  OBS_FACADE_OBSERVATION_PACKET,
  OBS_RAW_WORLD_TRUTH,
  ActionIntentCompat,
  CoordinationIntentCompat,
  DecisionBeliefCompat,
  ObservationProvenance,
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
  maintained_belief = observation_provenance(
    OBS_DECISION_BELIEF_PACKET,
    consumed_snapshot_version="belief:7",
    observation_packet_id="db:7",
  )
  compat = observation_provenance(OBS_AGENT_OBSERVATION_COMPAT)
  raw_truth = observation_provenance(OBS_RAW_WORLD_TRUTH)

  assert maintained.maintained_status == MAINTAINED
  assert maintained.is_maintained
  assert maintained.consumed_snapshot_version == "global:7"
  assert maintained_belief.maintained_status == MAINTAINED
  assert maintained_belief.information_state_layer == "DecisionBelief"
  assert maintained_belief.source_surface == "DecisionBelief"
  assert compat.maintained_status == COMPATIBILITY_ADAPTER
  assert raw_truth.maintained_status == DIAGNOSTICS_ONLY
  assert raw_truth.is_diagnostics_only
  assert LAW14_MAINTAINED_READ_LABEL_ALLOWLIST == (
    OBS_FACADE_OBSERVATION_PACKET,
    OBS_DECISION_BELIEF_PACKET,
  )


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


def test_maintained_agent_role_accepts_labeled_decision_belief_input():
  belief = DecisionBeliefCompat(
    belief_id="belief:track-kf:7",
    source_observation_versions=("global:11", "track:7"),
    memory_or_estimator_ref="estimator:kalman-track",
    confidence_kind="interval",
    confidence=0.91,
    lower_bound=0.75,
    upper_bound=0.98,
    maintained_status=MAINTAINED,
  )
  role = single_agent_role(
    world_index=4,
    agent_id=12,
    information_state_source=belief.as_consumable_provenance(source_layer="policy"),
    decision_model_kind="policy",
    decision_model_id="blue-policy-v1",
    maintained_status=MAINTAINED,
  )

  schema = role.as_dict()

  assert schema["maintained_status"] == MAINTAINED
  assert schema["information_state_source"]["label"] == OBS_DECISION_BELIEF_PACKET
  assert schema["information_state_source"]["information_state_layer"] == "DecisionBelief"
  assert schema["information_state_source"]["observation_packet_id"] == "belief:track-kf:7"
  assert schema["information_state_source"]["consumed_snapshot_version"] == "track:7"


def test_maintained_agent_role_rejects_compatibility_adapter_and_truth_inputs():
  with pytest.raises(
    ValueError,
    match="maintained consumer fixtures must use provenance-labeled ObservationPacket/DecisionBelief inputs",
  ):
    single_agent_role(
      agent_id=10,
      information_state_source=observation_provenance(OBS_AGENT_OBSERVATION_COMPAT),
      maintained_status=MAINTAINED,
    )

  with pytest.raises(
    ValueError,
    match="maintained consumer fixtures must use provenance-labeled ObservationPacket/DecisionBelief inputs",
  ):
    single_agent_role(
      agent_id=10,
      information_state_source=observation_provenance(
        OBS_RAW_WORLD_TRUTH,
        diagnostics_note="debug-only truth fixture",
      ),
      maintained_status=MAINTAINED,
    )

  with pytest.raises(
    ValueError,
    match="maintained consumer fixtures may only use the Law 14 ObservationPacket/DecisionBelief read-side allowlist",
  ):
    single_agent_role(
      agent_id=10,
      information_state_source=ObservationProvenance(
        label="manual_maintained_source",
        information_state_layer="DecisionBelief",
        source_surface="DecisionBelief",
        maintained_status=MAINTAINED,
        source_layer="policy",
      ),
      maintained_status=MAINTAINED,
    )

  with pytest.raises(
    ValueError,
    match="maintained consumer fixtures must not relabel privileged or raw surfaces as maintained",
  ):
    single_agent_role(
      agent_id=10,
      information_state_source=ObservationProvenance(
        label=OBS_FACADE_OBSERVATION_PACKET,
        information_state_layer="AgentObservation",
        source_surface="teacher, oracle, debug, or privileged helper",
        maintained_status=MAINTAINED,
        source_layer="policy",
      ),
      maintained_status=MAINTAINED,
    )


def test_default_agent_roles_use_maintained_facade_observation_provenance():
  default_single_role = single_agent_role(agent_id=10)
  default_roster_role = roster_slot_role(world_index=0, entity_id=10, roster_index=2)

  assert default_single_role.maintained_status == MAINTAINED
  assert default_single_role.information_state_source.label == OBS_FACADE_OBSERVATION_PACKET
  assert default_single_role.information_state_source.maintained_status == MAINTAINED
  assert default_roster_role.maintained_status == MAINTAINED
  assert default_roster_role.information_state_source.label == OBS_FACADE_OBSERVATION_PACKET
  assert default_roster_role.information_state_source.maintained_status == MAINTAINED


def test_maintained_intent_entry_points_reject_explicit_compatibility_role_provenance():
  compat_single_role = single_agent_role(
    agent_id=10,
    information_state_source=observation_provenance(OBS_AGENT_OBSERVATION_COMPAT),
    maintained_status=COMPATIBILITY_ADAPTER,
  )
  compat_roster_role = roster_slot_role(
    world_index=0,
    entity_id=10,
    roster_index=2,
    information_state_source=observation_provenance(OBS_AGENT_OBSERVATION_COMPAT),
    maintained_status=COMPATIBILITY_ADAPTER,
  )

  with pytest.raises(
    ValueError,
    match=(
      "ActionIntentCompat maintained business entry points require roles with explicit maintained "
      "ObservationPacket/DecisionBelief provenance"
    ),
  ):
    ActionIntentCompat(
      role=compat_single_role,
      payload=SimpleNamespace(throttle=0.8),
      maintained_status=MAINTAINED,
    )

  with pytest.raises(
    ValueError,
    match=(
      "CoordinationIntentCompat maintained business entry points require roles with explicit maintained "
      "ObservationPacket/DecisionBelief provenance"
    ),
  ):
    CoordinationIntentCompat(
      role=compat_roster_role,
      task_order=SimpleNamespace(task_id="hold-station"),
      maintained_status=MAINTAINED,
    )


def test_maintained_intent_entry_points_accept_explicit_maintained_role_provenance():
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
    target_entity_id=31,
    target_world_index=0,
    maintained_status=MAINTAINED,
  )
  coordination = CoordinationIntentCompat(
    role=role,
    task_order=SimpleNamespace(task_id="hold-station"),
    roster_scope={"world_index": 0},
    maintained_status=MAINTAINED,
  )

  assert action.as_dict()["maintained_status"] == MAINTAINED
  assert coordination.as_dict()["maintained_status"] == MAINTAINED


def test_maintained_intent_entry_points_reject_relabelled_raw_or_compat_role_provenance():
  compat_relabelled = single_agent_role(
    agent_id=10,
    information_state_source=ObservationProvenance(
      label=OBS_FACADE_OBSERVATION_PACKET,
      information_state_layer="AgentObservation",
      source_surface="get_agent_observation or get_agent_observations_batch",
      maintained_status=MAINTAINED,
    ),
    maintained_status=COMPATIBILITY_ADAPTER,
  )
  raw_relabelled = roster_slot_role(
    world_index=0,
    entity_id=10,
    roster_index=2,
    information_state_source=ObservationProvenance(
      label=OBS_FACADE_OBSERVATION_PACKET,
      information_state_layer="AgentObservation",
      source_surface="raw runtime or SimulationKernel",
      maintained_status=MAINTAINED,
    ),
    maintained_status=COMPATIBILITY_ADAPTER,
  )
  object.__setattr__(compat_relabelled, "maintained_status", MAINTAINED)
  object.__setattr__(raw_relabelled, "maintained_status", MAINTAINED)

  with pytest.raises(
    ValueError,
    match="maintained consumer fixtures must not relabel privileged or raw surfaces as maintained",
  ):
    ActionIntentCompat(
      role=compat_relabelled,
      payload=SimpleNamespace(throttle=0.8),
      maintained_status=MAINTAINED,
    )

  with pytest.raises(
    ValueError,
    match="maintained consumer fixtures must not relabel privileged or raw surfaces as maintained",
  ):
    CoordinationIntentCompat(
      role=raw_relabelled,
      task_order=SimpleNamespace(task_id="hold-station"),
      maintained_status=MAINTAINED,
    )


def test_diagnostics_only_agent_role_keeps_truth_fixture_explicitly_allowed():
  role = single_agent_role(
    agent_id=10,
    information_state_source=observation_provenance(
      OBS_RAW_WORLD_TRUTH,
      diagnostics_note="debug-only truth fixture",
    ),
    maintained_status=DIAGNOSTICS_ONLY,
  )

  schema = role.as_dict()

  assert schema["maintained_status"] == DIAGNOSTICS_ONLY
  assert schema["information_state_source"]["maintained_status"] == DIAGNOSTICS_ONLY
  assert schema["information_state_source"]["information_state_layer"] == "WorldTruth"
  assert schema["information_state_source"]["diagnostics_note"] == "debug-only truth fixture"


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


def test_diagnostics_or_compat_sources_are_not_promoted_to_maintained_belief_provenance():
  diagnostics_belief = DecisionBeliefCompat(
    belief_id="belief:oracle:1",
    source_observation_versions=("truth:raw",),
    memory_or_estimator_ref="oracle:teacher",
    maintained_status=DIAGNOSTICS_ONLY,
    diagnostics_reason="post-hoc oracle audit",
    uses_truth_state=True,
  )

  with pytest.raises(
    ValueError,
    match="only maintained DecisionBelief inputs may be promoted to maintained read-side provenance",
  ):
    diagnostics_belief.as_consumable_provenance()


def test_agent_role_exposes_five_elements_without_runtime_dependency():
  role = single_agent_role(
    world_index=2,
    agent_id=42,
    information_state_source=observation_provenance(OBS_AGENT_OBSERVATION_COMPAT),
    maintained_status=COMPATIBILITY_ADAPTER,
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

  contract = role.as_contract()
  assert contract["role"]["role_id"] == "agent:2:42"
  assert contract["authority_scope"]["has_world_index"] is True
  assert contract["information_state_source"]["source_label"] == OBS_AGENT_OBSERVATION_COMPAT
  assert contract["action_interface"]["kind"] == "PilotActionAssignmentCompat"


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
  role = single_agent_role(
    world_index=0,
    agent_id=11,
    information_state_source=observation_provenance(OBS_AGENT_OBSERVATION_COMPAT),
    maintained_status=COMPATIBILITY_ADAPTER,
  )
  payload = SimpleNamespace(stick_pitch=0.25)
  assignment = SimpleNamespace(world_index=0, entity_id=11, action=payload)

  intent = ActionIntentCompat.from_pilot_assignment(
    assignment,
    role=role,
    input_snapshot_version="global:9",
    effective_time=12.0,
    valid_until=12.1,
    merge_policy=MERGE_REJECT_ON_CONFLICT,
    maintained_status=COMPATIBILITY_ADAPTER,
  )

  assert intent.payload is payload
  assert assignment.action is payload
  assert intent.target_world_index == 0
  assert intent.target_entity_id == 11
  assert intent.merge_policy == MERGE_REJECT_ON_CONFLICT
  assert intent.as_dict()["input_snapshot_version"] == "global:9"
  contract = intent.as_contract()
  assert contract["source_id"] == role.role_id
  assert contract["target"] == {"world_index": 0, "entity_id": 11}
  assert contract["action_interface"]["kind"] == "PilotActionAssignmentCompat"
  assert contract["has_pilot_action"] is True


def test_coordination_intent_records_payload_fields():
  role = single_agent_role(
    world_index=0,
    agent_id=5,
    role_type="flight_lead",
    action_interface="CommandChainAssignmentCompat",
    information_state_source=observation_provenance(OBS_AGENT_OBSERVATION_COMPAT),
    maintained_status=COMPATIBILITY_ADAPTER,
  )
  mission_command = SimpleNamespace(command_code=3)
  leader_intent = SimpleNamespace(active=True)

  intent = CoordinationIntentCompat(
    role=role,
    mission_command=mission_command,
    leader_intent=leader_intent,
    roster_scope={"team_id": 1},
    update_clock="leader_step",
    maintained_status=COMPATIBILITY_ADAPTER,
  )

  assert intent.payload_fields() == ("mission_command", "leader_intent")
  assert intent.as_dict()["roster_scope"] == {"team_id": 1}
  assert intent.as_dict()["update_clock"] == "leader_step"
  contract = intent.as_contract()
  assert contract["source_type"] == "policy"
  assert contract["target_roster"]["world_index"] == 0
  assert contract["produced_tasking_refs"][0]["kind"] == "tasking"
  assert contract["produced_leader_intent_refs"][0]["kind"] == "leader_intent"


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
      role=single_agent_role(
        agent_id=1,
        information_state_source=observation_provenance(OBS_AGENT_OBSERVATION_COMPAT),
        maintained_status=COMPATIBILITY_ADAPTER,
      ),
      payload=object(),
      merge_policy="random_order",
    )


def test_decision_belief_contract_allows_maintained_observation_derived_belief():
  belief = DecisionBeliefCompat(
    belief_id="belief:track-kf:7",
    source_observation_versions=("global:11", "track:7"),
    memory_or_estimator_ref="estimator:kalman-track",
    confidence_kind="interval",
    confidence=0.91,
    lower_bound=0.75,
    upper_bound=0.98,
    maintained_status=MAINTAINED,
  )

  schema = belief.as_dict()

  assert schema["belief_id"] == "belief:track-kf:7"
  assert schema["source_observation_versions"] == ("global:11", "track:7")
  assert schema["memory_or_estimator_ref"] == "estimator:kalman-track"
  assert schema["confidence_shape"]["kind"] == "interval"
  assert schema["maintained_status"] == MAINTAINED
  assert schema["uses_truth_state"] is False


def test_decision_belief_truth_and_raw_ecs_inputs_are_diagnostics_only():
  belief = DecisionBeliefCompat(
    belief_id="belief:oracle:1",
    source_observation_versions=("truth:raw",),
    memory_or_estimator_ref="oracle:teacher",
    maintained_status=DIAGNOSTICS_ONLY,
    diagnostics_reason="post-hoc oracle audit",
    uses_truth_state=True,
    uses_raw_ecs=True,
  )

  schema = belief.as_dict()

  assert schema["maintained_status"] == DIAGNOSTICS_ONLY
  assert schema["diagnostics_reason"] == "post-hoc oracle audit"
  assert schema["uses_truth_state"] is True
  assert schema["uses_raw_ecs"] is True

  with pytest.raises(ValueError):
    DecisionBeliefCompat(
      belief_id="belief:bad",
      source_observation_versions=("truth:raw",),
      memory_or_estimator_ref="oracle:teacher",
      maintained_status=MAINTAINED,
      uses_truth_state=True,
    )
