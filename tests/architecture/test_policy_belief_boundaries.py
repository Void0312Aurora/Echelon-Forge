from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
POLICY_CONTRACTS = REPO_ROOT / "src" / "runtime" / "contracts" / "policy_contracts.h"
FACADE_TYPES = REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade_types.h"
AGENT_SHIM = REPO_ROOT / "python" / "rl" / "runtime" / "agent_shim.py"


def test_decision_belief_contract_stays_separate_from_observation_packet_types() -> None:
    policy_header = POLICY_CONTRACTS.read_text(encoding="utf-8")
    belief_section = policy_header.split("struct DecisionBelief", 1)[1].split("};", 1)[0]

    assert "ObservationBatchPacket" not in belief_section
    assert "std::vector<AgentObservation>" not in belief_section
    assert "source_observation_versions" in belief_section
    assert "memory_or_estimator_ref" in belief_section
    assert "confidence_shape" in belief_section


def test_decision_belief_truth_or_raw_ecs_usage_is_marked_diagnostics_only() -> None:
    policy_header = POLICY_CONTRACTS.read_text(encoding="utf-8")

    assert "uses_truth_state" in policy_header
    assert "uses_raw_ecs" in policy_header
    assert "diagnostics_reason" in policy_header
    assert "maintained_status" in policy_header
    assert "decision_belief_requires_diagnostics_only" in policy_header
    assert "decision_belief_has_valid_provenance" in policy_header
    assert "source_information_state" in policy_header


def test_policy_contracts_publish_wp11_information_state_vocabulary() -> None:
    policy_header = POLICY_CONTRACTS.read_text(encoding="utf-8")

    for token in (
        "kPolicyInformationStateWorldTruth",
        "kPolicyInformationStateSensedState",
        "kPolicyInformationStateTrackState",
        "kPolicyInformationStateSharedTacticalPicture",
        "kPolicyInformationStateAgentObservation",
        "kPolicyInformationStateDecisionBelief",
        "kPolicyMaintainedStatusMaintained",
        "kPolicyMaintainedStatusCompatibilityAdapter",
        "kPolicyMaintainedStatusDiagnosticsOnly",
    ):
        assert token in policy_header


def test_observation_packet_remains_facade_side_data_product() -> None:
    facade_header = FACADE_TYPES.read_text(encoding="utf-8")

    assert "struct ObservationBatchPacket" in facade_header
    assert "struct DecisionBelief" not in facade_header
    assert "InformationStateSource provenance" in facade_header
    assert "InformationStateSource packet_provenance" in facade_header
    assert "InformationStateSource diagnostics_provenance" in facade_header


def test_wp11d_maintained_consumer_pregate_requires_labeled_packet_or_belief_inputs() -> None:
    shim_source = AGENT_SHIM.read_text(encoding="utf-8")

    assert "_validate_maintained_consumer_source" in shim_source
    assert (
        "maintained consumer fixtures must use provenance-labeled ObservationPacket/DecisionBelief inputs"
        in shim_source
    )
    assert 'information_state_source.information_state_layer not in {"AgentObservation", "DecisionBelief"}' in (
        shim_source
    )
    assert "consumer_status != MAINTAINED" in shim_source
