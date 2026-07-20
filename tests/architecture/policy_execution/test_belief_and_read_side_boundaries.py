from __future__ import annotations

import ast
from pathlib import Path

from tests.support.xmacro_text import expand_header_field_incs


REPO_ROOT = Path(__file__).resolve().parents[3]
POLICY_CONTRACTS = REPO_ROOT / "src" / "runtime" / "contracts" / "policy_contracts.h"
INFORMATION_TRANSFORM_CONTRACTS = (
  REPO_ROOT / "src" / "runtime" / "contracts" / "information_transform_contracts.h"
)
FACADE_TYPES = REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade_types.h"
AGENT_SHIM = REPO_ROOT / "python" / "rl" / "runtime" / "agent_shim.py"
RUNTIME_FACADE_ESCAPE_HATCH_HELPERS = (
  REPO_ROOT / "tests" / "architecture" / "runtime_facade" / "helpers.py"
)


def _runtime_python_sources() -> list[Path]:
  return sorted(
    path
    for path in REPO_ROOT.joinpath("python", "rl", "runtime").rglob("*.py")
    if path != AGENT_SHIM
  )


def _call_name(node: ast.Call) -> str:
  if isinstance(node.func, ast.Name):
    return node.func.id
  if isinstance(node.func, ast.Attribute):
    return node.func.attr
  return ""


def _keyword_names(node: ast.Call) -> set[str]:
  return {str(keyword.arg) for keyword in node.keywords if keyword.arg is not None}


def _is_maintained_keyword(keyword: ast.keyword) -> bool:
  if keyword.arg != "maintained_status":
    return False
  value = keyword.value
  return (
    (isinstance(value, ast.Name) and value.id == "MAINTAINED")
    or (isinstance(value, ast.Constant) and value.value == "maintained")
  )


def _is_maintained_call(node: ast.Call) -> bool:
  return any(_is_maintained_keyword(keyword) for keyword in node.keywords)


def _is_default_role_call(node: ast.AST) -> bool:
  return (
    isinstance(node, ast.Call)
    and _call_name(node) in {"single_agent_role", "roster_slot_role"}
    and "information_state_source" not in _keyword_names(node)
  )


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
    "kPolicyMaintainedStatusAdapterProjection",
    "kPolicyMaintainedStatusDiagnosticsOnly",
  ):
    assert token in policy_header


def test_wp12_information_transformation_surface_reuses_policy_vocabulary_without_redefining_it() -> None:
  transform_header = INFORMATION_TRANSFORM_CONTRACTS.read_text(encoding="utf-8")

  assert '#include "runtime/contracts/policy_contracts.h"' in transform_header
  assert "kCanonicalInformationTransformations" in transform_header
  assert "validate_decision_belief_transformation" in transform_header
  assert "validate_decision_belief_to_action_intent_transformation" in transform_header
  assert "World Truth -> Sensed State" not in transform_header


def test_observation_packet_remains_facade_side_data_product() -> None:
  # ObservationBatchPacket's provenance field is schema-owned (I31): expand
  # the X-macro #include so this still matches the compiled field shape.
  facade_header = expand_header_field_incs(FACADE_TYPES.read_text(encoding="utf-8"))

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


def test_wp24l_maintained_role_helpers_default_to_facade_observation_provenance() -> None:
  shim_source = AGENT_SHIM.read_text(encoding="utf-8")

  assert "maintained_status: str = MAINTAINED" in shim_source
  assert "or observation_provenance(OBS_FACADE_OBSERVATION_PACKET)" in shim_source
  assert "or observation_provenance(OBS_AGENT_OBSERVATION_ADAPTER_PROJECTION)" not in shim_source


def test_wp24l_maintained_role_helper_call_sites_do_not_pass_adapter_projection_provenance() -> None:
  violations: list[tuple[str, int, str]] = []

  for path in _runtime_python_sources():
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
      if not isinstance(node, ast.Call):
        continue
      name = _call_name(node)
      if name not in {"single_agent_role", "roster_slot_role"}:
        continue
      if not _is_maintained_call(node):
        continue
      for keyword in node.keywords:
        if keyword.arg == "information_state_source" and ast.unparse(keyword.value).find(
          "OBS_AGENT_OBSERVATION_ADAPTER_PROJECTION"
        ) >= 0:
          violations.append((path.relative_to(REPO_ROOT).as_posix(), node.lineno, name))

  assert not violations, (
    "maintained role helper call sites must not opt back into adapter projection provenance: "
    f"{violations}"
  )


def test_wp24l_maintained_intents_do_not_inline_default_role_helpers() -> None:
  violations: list[tuple[str, int, str]] = []

  for path in _runtime_python_sources():
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
      if not isinstance(node, ast.Call):
        continue
      name = _call_name(node)
      if name not in {"ActionIntent", "CoordinationIntent"}:
        continue
      if not _is_maintained_call(node):
        continue
      for keyword in node.keywords:
        if keyword.arg == "role" and _is_default_role_call(keyword.value):
          violations.append((path.relative_to(REPO_ROOT).as_posix(), node.lineno, name))

  assert not violations, (
    "maintained intent call sites must not rely on default single_agent_role()/roster_slot_role() "
    f"with ambiguous provenance: {violations}"
  )


def test_wp24l_runtime_window_actions_require_explicit_maintained_provenance_and_authorization() -> None:
  adapter_source = (
    REPO_ROOT / "python" / "rl" / "runtime" / "world_batch" / "adapter.py"
  ).read_text(encoding="utf-8")
  single_world_source = (
    REPO_ROOT / "python" / "rl" / "runtime" / "single_world_batch_runtime.py"
  ).read_text(encoding="utf-8")
  leader_world_source = (
    REPO_ROOT / "python" / "rl" / "runtime" / "leader_world_batch_runtime.py"
  ).read_text(encoding="utf-8")

  assert "def _runtime_window_authorized_action_role(" in adapter_source
  assert "ef_py.authorize_maintained_action_intent(" in adapter_source
  assert "information_state_label: str | None = None" in adapter_source
  assert "unsupported provenance label" in adapter_source
  assert "requires explicit maintained " in adapter_source
  assert "ObservationPacket/DecisionBelief provenance and AgentRole authorization" in adapter_source

  for source in (single_world_source, leader_world_source):
    assert 'information_state_label="facade_observation_packet"' in source


def test_law14_read_side_allowlist_stays_focused() -> None:
  shim_source = AGENT_SHIM.read_text(encoding="utf-8")

  assert "LAW14_MAINTAINED_READ_LABEL_ALLOWLIST" in shim_source
  assert "OBS_FACADE_OBSERVATION_PACKET" in shim_source
  assert "OBS_DECISION_BELIEF_PACKET" in shim_source
  assert "OBS_AGENT_OBSERVATION_ADAPTER_PROJECTION" in shim_source
  assert "OBS_RAW_WORLD_TRUTH" in shim_source
  assert "OBS_DIAGNOSTICS_ORACLE" in shim_source
  assert (
    "maintained consumer fixtures may only use the Law 14 ObservationPacket/DecisionBelief read-side allowlist"
    in shim_source
  )
  assert "must not relabel privileged or raw surfaces as maintained" in shim_source


def test_maintained_intent_entry_points_validate_role_provenance() -> None:
  shim_source = AGENT_SHIM.read_text(encoding="utf-8")

  assert "_validate_maintained_entry_point_role" in shim_source
  assert "maintained business entry points require roles with explicit maintained " in shim_source
  assert "ObservationPacket/DecisionBelief provenance" in shim_source
  assert "if self.maintained_status == MAINTAINED:" in shim_source
  assert "entry_point=\"ActionIntent\"" in shim_source
  assert "entry_point=\"CoordinationIntent\"" in shim_source


def test_law14_boundary_does_not_add_new_raw_runtime_escape_hatch() -> None:
  layering_source = RUNTIME_FACADE_ESCAPE_HATCH_HELPERS.read_text(encoding="utf-8")

  assert "SCOPED_ESCAPE_HATCH_ALLOWLIST" in layering_source
  assert "classification=\"diagnostics_only\"" in layering_source
  assert "classification=\"compatibility_only\"" not in layering_source
