from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CMAKE_LISTS = REPO_ROOT / "CMakeLists.txt"
COUNTERFACTUAL_HEADER = (
  REPO_ROOT
  / "src"
  / "runtime"
  / "contracts"
  / "counterfactual_replay_contracts.h"
)
COUNTERFACTUAL_CONSTANTS = (
  REPO_ROOT
  / "src"
  / "runtime"
  / "contracts"
  / "counterfactual_replay_contract_constants.h"
)
COUNTERFACTUAL_TYPES = (
  REPO_ROOT
  / "src"
  / "runtime"
  / "contracts"
  / "counterfactual_replay_contract_types.h"
)
COUNTERFACTUAL_VALIDATION = (
  REPO_ROOT
  / "src"
  / "runtime"
  / "contracts"
  / "counterfactual_replay_contract_validation.h"
)
COUNTERFACTUAL_VALIDATION_HELPERS = (
  REPO_ROOT
  / "src"
  / "runtime"
  / "contracts"
  / "counterfactual_replay_validation_helpers.h"
)
COUNTERFACTUAL_REPLAY_VALIDATION = (
  REPO_ROOT
  / "src"
  / "runtime"
  / "contracts"
  / "counterfactual_replay_replay_validation.h"
)
COUNTERFACTUAL_COUNTERFACTUAL_VALIDATION = (
  REPO_ROOT
  / "src"
  / "runtime"
  / "contracts"
  / "counterfactual_replay_counterfactual_validation.h"
)
COUNTERFACTUAL_EXPERIMENT_VALIDATION = (
  REPO_ROOT
  / "src"
  / "runtime"
  / "contracts"
  / "counterfactual_replay_experiment_validation.h"
)
WINDOW_COORDINATOR = (
  REPO_ROOT
  / "src"
  / "runtime"
  / "facade"
  / "runtime_window_coordinator.h"
)
WINDOW_COORDINATOR_HELPERS = (
  REPO_ROOT
  / "src"
  / "runtime"
  / "facade"
  / "runtime_window_coordinator_helpers.h"
)
WINDOW_COORDINATOR_SELECTION_HELPERS = (
  REPO_ROOT
  / "src"
  / "runtime"
  / "facade"
  / "runtime_window_coordinator_selection_helpers.h"
)
WINDOW_COORDINATOR_CALLBACK_HELPERS = (
  REPO_ROOT
  / "src"
  / "runtime"
  / "facade"
  / "runtime_window_coordinator_callback_helpers.h"
)
WINDOW_COORDINATOR_CADENCE_TRACE_HELPERS = (
  REPO_ROOT
  / "src"
  / "runtime"
  / "facade"
  / "runtime_window_coordinator_cadence_trace_helpers.h"
)
WINDOW_COORDINATOR_EXECUTION_HELPERS = (
  REPO_ROOT
  / "src"
  / "runtime"
  / "facade"
  / "runtime_window_coordinator_execution_helpers.h"
)
SIMULATION_KERNEL_SYSTEMS = (
  REPO_ROOT
  / "src"
  / "core"
  / "engine"
  / "simulation_kernel_systems.cpp"
)
SIMULATION_KERNEL_HEADER = (
  REPO_ROOT
  / "src"
  / "core"
  / "engine"
  / "simulation_kernel.h"
)
ENGAGEMENT_EVENT_TYPES = (
  REPO_ROOT
  / "src"
  / "core"
  / "engine"
  / "engagement_event_types.h"
)
SIMULATION_KERNEL_CPP = (
  REPO_ROOT
  / "src"
  / "core"
  / "engine"
  / "simulation_kernel.cpp"
)
SIMULATION_KERNEL_SERVICES = (
  REPO_ROOT
  / "src"
  / "core"
  / "engine"
  / "simulation_kernel_services.cpp"
)
SIMULATION_KERNEL_SERVICES_HEADER = (
  REPO_ROOT
  / "src"
  / "core"
  / "engine"
  / "simulation_kernel_services.h"
)
SIMULATION_KERNEL_WEAPON_API = (
  REPO_ROOT
  / "src"
  / "core"
  / "engine"
  / "simulation_kernel_weapon_api.cpp"
)
SIMULATION_KERNEL_WEAPON_RELEASE_SERVICE = (
  REPO_ROOT
  / "src"
  / "core"
  / "engine"
  / "simulation_kernel_weapon_release_service.cpp"
)
SIMULATION_KERNEL_WEAPON_RELEASE_SERVICE_HEADER = (
  REPO_ROOT
  / "src"
  / "core"
  / "engine"
  / "simulation_kernel_weapon_release_service.h"
)
SIMULATION_KERNEL_ENGAGEMENT_EVENT_STORE = (
  REPO_ROOT
  / "src"
  / "core"
  / "engine"
  / "simulation_kernel_engagement_event_store.h"
)
SIMULATION_KERNEL_ENGAGEMENT_EVENT_STORE_CPP = (
  REPO_ROOT
  / "src"
  / "core"
  / "engine"
  / "simulation_kernel_engagement_event_store.cpp"
)
SIMULATION_KERNEL_DAMAGE_DEBUG_API = (
  REPO_ROOT
  / "src"
  / "core"
  / "engine"
  / "simulation_kernel_damage_debug_api.cpp"
)
ENGAGEMENT_EVENT_RECORDER = (
  REPO_ROOT
  / "src"
  / "core"
  / "interfaces"
  / "engagement_event_recorder.h"
)
WEAPON_RELEASE_DAMAGE_BRIDGE = (
  REPO_ROOT
  / "src"
  / "core"
  / "interfaces"
  / "weapon_release_damage_bridge.h"
)
PILOT_WEAPON_RELEASE_SYSTEM = (
  REPO_ROOT
  / "src"
  / "systems"
  / "combat"
  / "pilot_weapon_release_system.h"
)
NAVAL_MISSION_WEAPON_RELEASE_SYSTEM = (
  REPO_ROOT
  / "src"
  / "systems"
  / "domains"
  / "naval"
  / "naval_mission_weapon_release_system.h"
)
BINDINGS_CORE = (
  REPO_ROOT
  / "src"
  / "interfaces"
  / "python"
  / "bindings_core.cpp"
)
BINDINGS_DIR = REPO_ROOT / "src" / "interfaces" / "python"
DEFAULT_EFFECTS_MODEL = (
  REPO_ROOT
  / "src"
  / "models"
  / "weapons"
  / "default_effects_model.cpp"
)
DEFAULT_SENSOR_MODEL = (
  REPO_ROOT
  / "src"
  / "models"
  / "systems"
  / "default_sensor_model.cpp"
)
GENERIC_LOGISTICS_SYSTEM = (
  REPO_ROOT
  / "src"
  / "systems"
  / "systems"
  / "logistics_system.h"
)
NAVAL_LOGISTICS_SYSTEM = (
  REPO_ROOT
  / "src"
  / "systems"
  / "domains"
  / "naval"
  / "naval_logistics_system.h"
)
NAVAL_SENSOR_MARITIME_ADAPTER = (
  REPO_ROOT
  / "src"
  / "models"
  / "domains"
  / "naval"
  / "naval_sensor_maritime_adapter.h"
)
DEFAULT_EFFECTS_LEGACY_DETAIL = (
  REPO_ROOT
  / "src"
  / "models"
  / "weapons"
  / "detail"
  / "default_effects_legacy_detail.inc"
)
DEFAULT_EFFECTS_AIR_DOMAIN = (
  REPO_ROOT
  / "src"
  / "models"
  / "domains"
  / "air"
  / "default_effects_air_domain.h"
)
DEFAULT_EFFECTS_DOMAIN_ROUTING_DETAIL = (
  REPO_ROOT
  / "src"
  / "models"
  / "weapons"
  / "detail"
  / "default_effects_domain_routing_detail.inc"
)
COMPONENT_DOMAINS_ROOT = REPO_ROOT / "src" / "components" / "domains"
SYSTEM_DOMAINS_ROOT = REPO_ROOT / "src" / "systems" / "domains"
MODEL_DOMAINS_ROOT = REPO_ROOT / "src" / "models" / "domains"
DOMAIN_COMPONENT_REQUIRED_DIRS = (
  COMPONENT_DOMAINS_ROOT / "air" / "platform",
  COMPONENT_DOMAINS_ROOT / "air" / "combat",
  COMPONENT_DOMAINS_ROOT / "air" / "command",
  COMPONENT_DOMAINS_ROOT / "air" / "tasking",
  COMPONENT_DOMAINS_ROOT / "naval" / "platform",
  COMPONENT_DOMAINS_ROOT / "naval" / "combat",
  COMPONENT_DOMAINS_ROOT / "naval" / "command",
  COMPONENT_DOMAINS_ROOT / "naval" / "tasking",
  COMPONENT_DOMAINS_ROOT / "ground" / "combat",
  COMPONENT_DOMAINS_ROOT / "ground" / "command",
  COMPONENT_DOMAINS_ROOT / "ground" / "tasking",
)
DOMAIN_COMPONENT_RETIRED_FLAT_DIRS = (
  REPO_ROOT / "src" / "components" / "air",
  REPO_ROOT / "src" / "components" / "naval",
  REPO_ROOT / "src" / "components" / "combat" / "air",
  REPO_ROOT / "src" / "components" / "combat" / "naval",
  REPO_ROOT / "src" / "components" / "combat" / "ground",
  REPO_ROOT / "src" / "components" / "command" / "air",
  REPO_ROOT / "src" / "components" / "command" / "naval",
  REPO_ROOT / "src" / "components" / "command" / "ground",
  REPO_ROOT / "src" / "components" / "tasking" / "air",
  REPO_ROOT / "src" / "components" / "tasking" / "naval",
  REPO_ROOT / "src" / "components" / "tasking" / "ground",
)
DOMAIN_COMPONENT_RETIRED_INCLUDE_PREFIXES = (
  'components/air/',
  'components/naval/',
  'components/combat/air/',
  'components/combat/naval/',
  'components/combat/ground/',
  'components/command/air/',
  'components/command/naval/',
  'components/command/ground/',
  'components/tasking/air/',
  'components/tasking/naval/',
  'components/tasking/ground/',
)
DOMAIN_SYSTEM_REQUIRED_DIRS = (
  SYSTEM_DOMAINS_ROOT / "air",
  SYSTEM_DOMAINS_ROOT / "naval",
)
DOMAIN_MODEL_REQUIRED_DIRS = (
  MODEL_DOMAINS_ROOT / "air",
  MODEL_DOMAINS_ROOT / "naval",
  MODEL_DOMAINS_ROOT / "ground",
)
DOMAIN_SYSTEM_MODEL_RETIRED_FLAT_DIRS = (
  REPO_ROOT / "src" / "systems" / "air",
  REPO_ROOT / "src" / "systems" / "naval",
  REPO_ROOT / "src" / "systems" / "ground",
  REPO_ROOT / "src" / "models" / "air",
  REPO_ROOT / "src" / "models" / "naval",
  REPO_ROOT / "src" / "models" / "ground",
)
DOMAIN_SYSTEM_MODEL_RETIRED_INCLUDE_PREFIXES = (
  'systems/air/',
  'systems/naval/',
  'systems/ground/',
  'models/air/',
  'models/naval/',
  'models/ground/',
)
DOMAIN_SEPARATION_RETIRED_PUBLIC_FILES = (
  REPO_ROOT / "src" / "components" / "combat" / "damage.h",
  REPO_ROOT / "src" / "components" / "combat" / "weapon.h",
  REPO_ROOT / "src" / "systems" / "combat" / "damage_system.h",
  REPO_ROOT / "src" / "components" / "physics" / "flight_dynamics_tuning.h",
  REPO_ROOT / "src" / "systems" / "physics" / "aero_state_system.h",
  REPO_ROOT / "src" / "systems" / "physics" / "aerodynamics_system.h",
  REPO_ROOT / "src" / "systems" / "physics" / "control_system.h",
  REPO_ROOT / "src" / "systems" / "physics" / "propulsion_system.h",
  REPO_ROOT
  / "src"
  / "models"
  / "weapons"
  / "detail"
  / "default_effects_air_platform_resolution_detail.inc",
)
DOMAIN_SEPARATION_RETIRED_INCLUDE_STRINGS = (
  '#include "components/combat/damage.h"',
  '#include "components/combat/weapon.h"',
  '#include "systems/combat/damage_system.h"',
  '#include "components/physics/flight_dynamics_tuning.h"',
  '#include "systems/physics/aero_state_system.h"',
  '#include "systems/physics/aerodynamics_system.h"',
  '#include "systems/physics/control_system.h"',
  '#include "systems/physics/propulsion_system.h"',
  '#include "models/weapons/detail/default_effects_air_platform_resolution_detail.inc"',
)
STRUCTURAL_DOC_EN = (
  REPO_ROOT
  / "docs"
  / "task"
  / "simulation_architecture"
  / "archive"
  / "wp22_legacy_compatibility_retirement"
  / "wp22_structural_god_file_decomposition_cluster_20260522.md"
)
STRUCTURAL_DOC_ZH = (
  REPO_ROOT
  / "docs"
  / "task"
  / "simulation_architecture"
  / "archive"
  / "wp22_legacy_compatibility_retirement"
  / "wp22_structural_god_file_decomposition_cluster_20260522.zh.md"
)

COUNTERFACTUAL_CONSTANT_ALLOWLIST = {
  "kReplayRestoreSupportBoundaryUnsupported",
  "kWorldlineBranchSupportStateMetadataOnly",
  "kCounterfactualRequestRejectionRestoreUnsupportedBoundary",
  "kScenarioGenerationArtifactKindRequestMetadata",
  "kCounterfactualAdmissionStateAdmitted",
  "kExperimentProfileClaimScopeDescriptive",
}

WINDOW_COORDINATOR_MAIN_MARKERS = {
  "classify_runtime_window_inputs(",
  "execute_runtime_window(",
  "enumerate_maintained_stage_node_manifests()",
}

WINDOW_COORDINATOR_HELPER_MARKERS = {
  "kRuntimeWindowBarrierInputInjection",
  "kRuntimeWindowBarrierWindowCommit",
  "kRuntimeWindowBarrierExport",
  "runtime_window_default_selected_slice_cadence_config()",
  "runtime_window_has_selected_barrier_order(",
}

WINDOW_COORDINATOR_SELECTION_HELPER_MARKERS = {
  "resolve_runtime_window_observation_request(",
  "resolve_runtime_window_engagement_request(",
  "runtime_window_pick_primary_trigger_request(",
}

WINDOW_COORDINATOR_CALLBACK_HELPER_MARKERS = {
  "runtime_window_collect_missing_export_callbacks(",
  "runtime_window_export_snapshot_evidence(",
}

WINDOW_COORDINATOR_CADENCE_TRACE_HELPER_MARKERS = {
  "runtime_window_preferred_cadence_trace_record(",
  "build_runtime_window_cadence_trace(",
  "runtime_window_append_export_cadence_trace(",
}

WINDOW_COORDINATOR_EXECUTION_HELPER_MARKERS = {
  "runtime_window_fire_control_launch_record(",
  "runtime_window_effects_damage_record(",
  "runtime_window_observation_export_record(",
}

BINDINGS_DIAGNOSTICS_ALLOWLIST = {
  "get_sensor_debug_view",
  "get_track_debug_view",
  "get_tentative_track_debug_view",
  "get_flight_dynamics_debug_view",
  "debug_get_naval_weapon_counts",
  "debug_get_naval_stores",
  "debug_get_logistics_node",
  "debug_get_resupply_state",
  "debug_get_data_link_state",
  "debug_get_ground_contact_state",
  "debug_get_last_scan_time",
  "debug_get_contact_count",
  "debug_get_mass_state",
  "debug_get_pending_movement_command",
  "debug_get_pending_action_command",
  "debug_get_pending_mission_command_queue",
  "debug_get_embarked_helo",
  "debug_get_missile_runtime_state",
  "debug_get_aircraft_damage_state",
  "debug_get_aircraft_vulnerability_evidence_state",
  "debug_get_aircraft_vulnerability_authority_state",
  "debug_set_unit_truth_state",
  "set_contact_list",
  "set_missile_guidance_mechanism_profile",
  "set_missile_tuning",
  "get_missile_tuning",
  "debug_apply_proximity_hit",
  "debug_apply_local_proximity_hit",
  "debug_apply_profiled_local_proximity_hit",
  "debug_apply_profiled_local_proximity_hit_with_velocity",
  "debug_apply_profiled_local_proximity_hit_with_velocity_and_attitude",
}

BINDINGS_LEGACY_ALLOWLIST = {
  "debug_set_legacy_movement_command",
  "debug_get_legacy_movement_command",
}

MISSION_COMMAND_CONTROL_STATE = (
  REPO_ROOT
  / "src"
  / "components"
  / "command"
  / "common"
  / "mission_command_control_state.h"
)
AIR_CONTROL_RESOLUTION = (
  REPO_ROOT
  / "src"
  / "components"
  / "domains"
  / "air"
  / "command"
  / "control_input_resolution.h"
)

COUNTERFACTUAL_CLOSURE_BLOCKING_MAX_LINES = 1500
WINDOW_COORDINATOR_CLOSURE_BLOCKING_MAX_LINES = 1000
INLINE_REGISTERED_SYSTEM_PATTERN = re.compile(
  r'ecs\.system<[^>]+>\("([^"]+)"\)\s*\n\s*\.kind\(flecs::(OnUpdate|PreUpdate)\)'
)
EFFECTS_DAMAGE_RECORDER_SIGNATURE_PATTERN = re.compile(
  r"(?:virtual\s+)?(?:std::)?uint64_t\s+"
  r"(?:(?:SimulationKernelEngagementEventStore)::)?"
  r"(?P<name>record_effects_damage_event(?:_legacy)?)\s*"
  r"\((?P<params>[^)]*)\)"
)
DEBUG_DAMAGE_DTO_BUILDER_SIGNATURE = "build_debug_effects_damage_event_record("
DEBUG_DAMAGE_DTO_CALLER_SIGNATURES = (
  "bool SimulationKernel::debug_apply_proximity_hit(",
  "bool SimulationKernel::debug_apply_local_proximity_hit(",
  "bool SimulationKernel::debug_apply_profiled_local_proximity_hit_with_velocity_and_attitude(",
)


def _text(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def _contains_cpp_marker(text: str, marker: str) -> bool:
  def normalize(value: str) -> str:
    token_spaced = re.sub(r"([&*])", r" \1 ", value)
    return " ".join(token_spaced.split())

  return normalize(marker) in normalize(text)


def _maintained_source_texts() -> list[tuple[Path, str]]:
  source_roots = (REPO_ROOT / "src", REPO_ROOT / "src" / "tests")
  suffixes = {".c", ".cc", ".cpp", ".h", ".hpp", ".inc"}
  files: list[Path] = []
  for source_root in source_roots:
    if not source_root.exists():
      continue
    files.extend(
      path
      for path in source_root.rglob("*")
      if path.is_file() and path.suffix in suffixes
    )
  return [(path, _text(path)) for path in sorted(files)]


def _line_count(path: Path) -> int:
  return sum(1 for _ in path.open(encoding="utf-8"))


def _has_inline_definition(text: str, function_name: str) -> bool:
  pattern = re.compile(
    rf"\binline\b[\s\S]{{0,240}}?\b{re.escape(function_name)}\s*\("
  )
  return pattern.search(text) is not None


def _normalized_cpp_parameters(parameters: str) -> str:
  return re.sub(r"\s+", " ", parameters).strip()


def _effects_damage_recorder_signatures(text: str) -> list[tuple[str, str]]:
  return [
    (match.group("name"), _normalized_cpp_parameters(match.group("params")))
    for match in EFFECTS_DAMAGE_RECORDER_SIGNATURE_PATTERN.finditer(text)
  ]


def _assert_effects_damage_recorder_signatures_are_dto_only(
  source_name: str,
  text: str,
) -> None:
  signatures = _effects_damage_recorder_signatures(text)
  assert signatures == [
    ("record_effects_damage_event", "EngagementEffectsDamageEventRecord record")
  ], (
    f"{source_name} must keep effects damage recording DTO-shaped only; "
    "public or private long-argument recorder/store helpers are TM05 closure regressions"
  )


def _assert_debug_damage_paths_use_dto_builder(text: str) -> None:
  assert "build_debug_effects_damage_event_record(" in text, (
    "TM06 debug damage paths should build event DTOs through the named local helper"
  )
  helper_signature = re.search(
    r"EngagementEffectsDamageEventRecord\s+build_debug_effects_damage_event_record\(",
    text,
  )
  assert helper_signature is not None
  helper_block = _extract_function_block(text, helper_signature.group(0))
  assert "EngagementEffectsDamageEventRecord event_record{}" in helper_block
  effects_alias_pattern = r"EffectsEvent\s*&\s*effects\s*=\s*event_record\.effects;"
  assert re.search(effects_alias_pattern, helper_block)
  assert "engagement_events::apply_effects_result_fields(effects, input.effects_result);" in helper_block
  assert "return event_record;" in helper_block
  assert text.count("EngagementEffectsDamageEventRecord event_record{}") == 1, (
    "debug damage DTO default construction should stay centralized in "
    "build_debug_effects_damage_event_record"
  )
  assert len(re.findall(effects_alias_pattern, text)) == 1, (
    "debug EffectsEvent field population should not be duplicated in public debug methods"
  )
  assert text.count("engagement_events::apply_effects_result_fields(") == 1, (
    "debug effects-result DTO population should stay in the local builder helper"
  )

  for signature in DEBUG_DAMAGE_DTO_CALLER_SIGNATURES:
    caller_block = _extract_function_block(text, signature)
    assert "build_debug_effects_damage_event_record({" in caller_block
    assert "record_effects_damage_event(std::move(event_record))" in caller_block
    assert "impact.destruct();" in caller_block
    assert (
      caller_block.index("record_effects_damage_event(std::move(event_record))")
      < caller_block.index("impact.destruct();")
    )
    assert "EngagementEffectsDamageEventRecord event_record{}" not in caller_block
    assert not re.search(effects_alias_pattern, caller_block)
    assert "engagement_events::apply_effects_result_fields(" not in caller_block


def _python_binding_sources() -> list[str]:
  """File names of EF_PYTHON_BINDING_SOURCES in CMake (= registration) order."""
  lines = _text(CMAKE_LISTS).splitlines()
  start = next(
    index for index, line in enumerate(lines)
    if line.strip().startswith("set(EF_PYTHON_BINDING_SOURCES")
  )
  names: list[str] = []
  for line in lines[start + 1:]:
    stripped = line.strip()
    if stripped == ")":
      break
    match = re.fullmatch(r"src/interfaces/python/(\S+\.cpp)", stripped)
    if match:
      names.append(match.group(1))
  return names


def _binding_surface_text(prefix: str, detail_header: str) -> str:
  """Concatenated source text of one decomposed binding surface.

  The per-domain split keeps registration order locked across the
  orchestrator, the internal header, and the CMake source list, so joining
  the slices in CMake order reproduces the original single-file text for
  source-shape guards. The internal header goes first because the shared
  helpers that used to sit above bind_* in the single file now live there.
  """
  parts = [_text(BINDINGS_DIR / detail_header)]
  parts.extend(
    _text(BINDINGS_DIR / name)
    for name in _python_binding_sources()
    if name == f"{prefix}.cpp" or name.startswith(f"{prefix}_")
  )
  return "\n".join(parts)


def bindings_core_text() -> str:
  return _binding_surface_text("bindings_core", "bindings_core_detail.h")


def bindings_runtime_text() -> str:
  return _binding_surface_text("bindings_runtime", "bindings_runtime_detail.h")


def _diagnostics_introspection_text(text: str) -> str:
  """The diagnostics introspection surface, joined from its three sub-slices.

  bind_simulation_kernel_diagnostics_introspection_surface is a thin
  orchestrator since the bindings_core decomposition; the quarantine
  assertions apply to the concatenation of the three sub-surface bodies,
  which is textually equivalent to the old single function body.
  """
  return "".join(
    _extract_function_block(
      text, f"void bind_simulation_kernel_diagnostics_{part}("
    )
    for part in (
      "hit_and_view_surface",
      "platform_state_surface",
      "missile_runtime_surface",
    )
  )


def _simulation_kernel_binding_names() -> list[str]:
  text = bindings_core_text()
  start = text.index('nb::class_<SimulationKernel> simulation_kernel(m, "SimulationKernel");')
  block = text[start:]
  names = re.findall(r'\.def\s*\(\s*"([^"]+)"', block)
  return list(dict.fromkeys(names))


def _extract_function_block(text: str, signature: str) -> str:
  start = text.rindex(signature)
  return _extract_braced_block_after(text, start)


def _extract_binding_lambda_block(text: str, binding_name: str) -> str:
  pattern = re.compile(rf'\.def\s*\(\s*"{re.escape(binding_name)}"')
  match = pattern.search(text)
  if match is None:
    raise AssertionError(f"could not find binding for {binding_name}")
  return _extract_braced_block_after(text, match.start())


def _extract_braced_block_after(text: str, start: int) -> str:
  brace_start = text.index("{", start)
  depth = 0
  for idx in range(brace_start, len(text)):
    char = text[idx]
    if char == "{":
      depth += 1
    elif char == "}":
      depth -= 1
      if depth == 0:
        return text[start:idx + 1]
  raise AssertionError("could not extract braced block")


__all__ = tuple(name for name in globals() if not name.startswith("__"))
