from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
POLICY_HEADER = REPO_ROOT / "src" / "runtime" / "contracts" / "policy_contracts.h"


def _header_text() -> str:
    return POLICY_HEADER.read_text(encoding="utf-8")


def _struct_body(header: str, struct_name: str) -> str:
    pattern = rf"\bstruct\s+{re.escape(struct_name)}\b[^{{;]*\{{(?P<body>.*?)\n\}};"
    match = re.search(pattern, header, flags=re.DOTALL)
    assert match is not None, f"{struct_name} is missing from {POLICY_HEADER}"
    return match.group("body")


def _assert_fields_present(body: str, fields: tuple[str, ...]) -> None:
    missing = [
        field
        for field in fields
        if re.search(rf"\b{re.escape(field)}\b", body) is None
    ]
    assert not missing, f"missing fields: {', '.join(missing)}"


def test_policy_contract_header_exists_at_stable_runtime_contract_path() -> None:
    assert POLICY_HEADER.is_file()


def test_policy_contract_header_does_not_include_core_or_engine_layers() -> None:
    header = _header_text()
    include_lines = re.findall(r"^\s*#\s*include\s+[<\"]([^>\"]+)[>\"]", header, flags=re.MULTILINE)

    forbidden = [
        include_path
        for include_path in include_lines
        if "core/" in include_path or "engine/" in include_path
    ]

    assert forbidden == []


def test_action_and_coordination_intent_contracts_expose_required_fields() -> None:
    header = _header_text()
    action_hold_policy = _struct_body(header, "ActionHoldPolicy")
    action_intent = _struct_body(header, "ActionIntentPacket")
    coordination_intent = _struct_body(header, "CoordinationIntentPacket")

    _assert_fields_present(
        action_hold_policy,
        (
            "policy_id",
            "action_family",
            "hold_mode",
            "validity_duration_s",
            "refresh_cadence_s",
            "target_control_cadence_s",
            "expiry_behavior",
            "interpolation_mode",
            "credit_assignment_latency_s",
            "credit_assignment_attribution_note",
            "diagnostics_reason",
        ),
    )
    assert "hold_last" in header
    assert "interpolate" in header
    assert "expire" in header
    assert "drop" in header

    _assert_fields_present(
        action_intent,
        (
            "source_id",
            "effective_time_s",
            "valid_until_s",
            "target",
            "action_family",
            "merge_policy",
            "action_interface",
        ),
    )
    assert "PilotAction" in action_intent or "MissionCommand" in action_intent

    _assert_fields_present(
        coordination_intent,
        (
            "source_type",
            "source_id",
            "target_roster",
            "update_clock",
            "merge_policy",
            "produced_tasking_refs",
            "produced_leader_intent_refs",
        ),
    )


def test_agent_role_and_decision_belief_contracts_expose_required_fields() -> None:
    header = _header_text()
    agent_role = _struct_body(header, "AgentRole")
    decision_belief = _struct_body(header, "DecisionBelief")

    _assert_fields_present(
        agent_role,
        (
            "role",
            "authority_scope",
            "information_state_source",
            "decision_model_ref",
            "action_interface",
        ),
    )
    _assert_fields_present(
        decision_belief,
        (
            "belief_id",
            "information_state_layer",
            "source_information_state",
            "source_observation_versions",
            "memory_or_estimator_ref",
            "confidence_shape",
            "maintained_status",
            "diagnostics_reason",
        ),
    )
    header_text = _header_text()
    assert "decision_belief_has_valid_provenance" in header_text
    assert "decision_belief_requires_diagnostics_only" in header_text


def test_action_hold_policy_defaults_are_conservative_and_declarative() -> None:
    header = _header_text()
    action_hold_policy = _struct_body(header, "ActionHoldPolicy")

    assert 'hold_mode = std::string(kActionHoldModeDrop)' in action_hold_policy
    assert 'validity_duration_s = 0.0' in action_hold_policy
    assert 'refresh_cadence_s = 0.0' in action_hold_policy
    assert 'target_control_cadence_s = 0.0' in action_hold_policy
    assert 'expiry_behavior = std::string(kActionHoldExpiryBehaviorDrop)' in action_hold_policy
    assert 'interpolation_mode = std::string(kActionHoldInterpolationModeNone)' in action_hold_policy
    assert 'credit_assignment_latency_s = 0.0' in action_hold_policy
    assert "runtime_cadence_not_implemented" in action_hold_policy


def test_action_hold_policy_header_exposes_fail_closed_normalizer_and_supported_modes() -> None:
    header = _header_text()

    assert "is_supported_action_hold_mode" in header
    assert "normalize_action_hold_policy" in header
    assert "unsupported_action_hold_mode_fail_closed_to_drop" in header
    assert "unsupported_action_hold_expiry_behavior_fail_closed_to_drop" in header
    assert "policy.hold_mode = std::string(kActionHoldModeDrop);" in header
    assert "policy.expiry_behavior = std::string(kActionHoldExpiryBehaviorDrop);" in header
    assert "policy.interpolation_mode = std::string(kActionHoldInterpolationModeNone);" in header
