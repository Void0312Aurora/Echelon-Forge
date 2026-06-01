from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
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
DEFAULT_EFFECTS_MODEL = (
    REPO_ROOT
    / "src"
    / "models"
    / "weapons"
    / "default_effects_model.cpp"
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
    "enumerate_wp10_maintained_stage_node_manifests()",
}

WINDOW_COORDINATOR_HELPER_MARKERS = {
    "kRuntimeWindowBarrierInputInjection",
    "kRuntimeWindowBarrierWindowCommit",
    "kRuntimeWindowBarrierExport",
    "runtime_window_default_wp17_selected_slice_cadence_config()",
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
    "set_contact_list",
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
    / "command"
    / "air"
    / "control_input_resolution.h"
)

COUNTERFACTUAL_CLOSURE_BLOCKING_MAX_LINES = 1500
WINDOW_COORDINATOR_CLOSURE_BLOCKING_MAX_LINES = 1000
INLINE_REGISTERED_SYSTEM_PATTERN = re.compile(
    r'ecs\.system<[^>]+>\("([^"]+)"\)\s*\n\s*\.kind\(flecs::(OnUpdate|PreUpdate)\)'
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _line_count(path: Path) -> int:
    return sum(1 for _ in path.open(encoding="utf-8"))


def _has_inline_definition(text: str, function_name: str) -> bool:
    pattern = re.compile(
        rf"\binline\b[\s\S]{{0,240}}?\b{re.escape(function_name)}\s*\("
    )
    return pattern.search(text) is not None


def _simulation_kernel_binding_names() -> list[str]:
    text = _text(BINDINGS_CORE)
    start = text.index('nb::class_<SimulationKernel> simulation_kernel(m, "SimulationKernel");')
    block = text[start:]
    return re.findall(r'\.def\("([^"]+)"', block)


def _extract_function_block(text: str, signature: str) -> str:
    start = text.rindex(signature)
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
    raise AssertionError(f"could not extract block for {signature}")


def test_wp22_counterfactual_structural_split_promotes_types_and_validation_owners() -> None:
    header_text = _text(COUNTERFACTUAL_HEADER)
    constants_text = _text(COUNTERFACTUAL_CONSTANTS)
    types_text = _text(COUNTERFACTUAL_TYPES)
    validation_text = _text(COUNTERFACTUAL_VALIDATION)
    helper_text = _text(COUNTERFACTUAL_VALIDATION_HELPERS)
    replay_validation_text = _text(COUNTERFACTUAL_REPLAY_VALIDATION)
    counterfactual_validation_text = _text(COUNTERFACTUAL_COUNTERFACTUAL_VALIDATION)
    experiment_validation_text = _text(COUNTERFACTUAL_EXPERIMENT_VALIDATION)

    assert '#include "runtime/contracts/counterfactual_replay_contract_constants.h"' in header_text
    assert '#include "runtime/contracts/counterfactual_replay_contract_types.h"' in header_text
    assert '#include "runtime/contracts/counterfactual_replay_contract_validation.h"' in header_text
    assert '#include "runtime/contracts/counterfactual_replay_counterfactual_validation.h"' in validation_text
    assert '#include "runtime/contracts/counterfactual_replay_experiment_validation.h"' in validation_text
    assert "struct ReplayEnvelope;" in header_text
    assert "validate_replay_envelope(" in header_text
    assert "struct ReplayEnvelope" not in constants_text
    assert "validate_replay_envelope(" not in constants_text
    assert "struct ReplayEnvelope {" in types_text
    assert "validate_replay_envelope(" not in types_text
    assert "replay_contract_is_blank(" in helper_text
    assert "validate_replay_envelope(" in replay_validation_text
    assert "validate_counterfactual_experiment_request(" in counterfactual_validation_text
    assert "make_experiment_evidence_bridge_record(" in experiment_validation_text
    assert "struct ReplayEnvelope {" not in replay_validation_text
    assert "struct ReplayEnvelope {" not in counterfactual_validation_text
    assert "struct ReplayEnvelope {" not in experiment_validation_text

    for marker in COUNTERFACTUAL_CONSTANT_ALLOWLIST:
        assert marker in constants_text, f"missing structural constant marker: {marker}"

    assert COUNTERFACTUAL_HEADER.stat().st_size < COUNTERFACTUAL_TYPES.stat().st_size
    assert COUNTERFACTUAL_HEADER.stat().st_size < COUNTERFACTUAL_REPLAY_VALIDATION.stat().st_size
    assert (
        COUNTERFACTUAL_HEADER.stat().st_size <
        COUNTERFACTUAL_COUNTERFACTUAL_VALIDATION.stat().st_size
    )
    assert (
        COUNTERFACTUAL_HEADER.stat().st_size <
        COUNTERFACTUAL_EXPERIMENT_VALIDATION.stat().st_size
    )


def test_wp22_counterfactual_validation_umbrella_stays_below_split_threshold() -> None:
    line_count = _line_count(COUNTERFACTUAL_VALIDATION)
    assert line_count < 300, (
        "WP22-E counterfactual validation umbrella should stay focused once family helpers "
        "are split into named companion headers"
    )


def test_wp22_counterfactual_contract_header_drops_below_closure_threshold() -> None:
    line_count = _line_count(COUNTERFACTUAL_HEADER)
    assert line_count < COUNTERFACTUAL_CLOSURE_BLOCKING_MAX_LINES, (
        "WP22-E counterfactual structural split is not complete until the public umbrella "
        "header falls below the 1500-line closure threshold"
    )


def test_wp22_runtime_window_coordinator_split_advances_with_named_helper_owners() -> None:
    header_text = _text(WINDOW_COORDINATOR)
    helper_text = _text(WINDOW_COORDINATOR_HELPERS)
    selection_text = _text(WINDOW_COORDINATOR_SELECTION_HELPERS)
    callback_text = _text(WINDOW_COORDINATOR_CALLBACK_HELPERS)
    cadence_text = _text(WINDOW_COORDINATOR_CADENCE_TRACE_HELPERS)
    execution_text = _text(WINDOW_COORDINATOR_EXECUTION_HELPERS)

    assert '#include "runtime/facade/runtime_window_coordinator_helpers.h"' in header_text
    assert '#include "runtime/facade/runtime_window_coordinator_selection_helpers.h"' in header_text
    assert '#include "runtime/facade/runtime_window_coordinator_callback_helpers.h"' in header_text
    assert '#include "runtime/facade/runtime_window_coordinator_cadence_trace_helpers.h"' in header_text
    assert '#include "runtime/facade/runtime_window_coordinator_execution_helpers.h"' in header_text
    for marker in WINDOW_COORDINATOR_MAIN_MARKERS:
        assert marker in header_text
    for marker in WINDOW_COORDINATOR_HELPER_MARKERS:
        assert marker in helper_text
    for marker in WINDOW_COORDINATOR_SELECTION_HELPER_MARKERS:
        assert marker in selection_text
        function_name = marker.split("(")[0]
        assert _has_inline_definition(selection_text, function_name)
        assert not _has_inline_definition(header_text, function_name)
    for marker in WINDOW_COORDINATOR_CALLBACK_HELPER_MARKERS:
        assert marker in callback_text
        function_name = marker.split("(")[0]
        assert _has_inline_definition(callback_text, function_name)
        assert not _has_inline_definition(header_text, function_name)
    for marker in WINDOW_COORDINATOR_CADENCE_TRACE_HELPER_MARKERS:
        assert marker in cadence_text
        function_name = marker.split("(")[0]
        assert _has_inline_definition(cadence_text, function_name)
        assert not _has_inline_definition(header_text, function_name)
    for marker in WINDOW_COORDINATOR_EXECUTION_HELPER_MARKERS:
        assert marker in execution_text
        function_name = marker.split("(")[0]
        assert _has_inline_definition(execution_text, function_name)
        assert not _has_inline_definition(header_text, function_name)

    assert "runtime_window_requests_conflict(" in header_text
    assert "runtime_window_requests_conflict(" not in helper_text
    assert "execute_runtime_window(" in header_text
    assert "execute_runtime_window(" not in helper_text
    assert "execute_runtime_window(" not in selection_text
    assert "execute_runtime_window(" not in callback_text
    assert "execute_runtime_window(" not in cadence_text
    assert "execute_runtime_window(" not in execution_text


def test_wp22_runtime_window_coordinator_header_drops_below_closure_threshold() -> None:
    line_count = _line_count(WINDOW_COORDINATOR)
    assert line_count < WINDOW_COORDINATOR_CLOSURE_BLOCKING_MAX_LINES, (
        "WP22-E runtime-window structural split is not complete until the coordinator header "
        "falls below the post-helper closure threshold"
    )


def test_wp22_pilot_weapon_release_moves_to_named_helper_and_simulation_kernel_systems_stays_inline_free() -> None:
    systems_text = _text(SIMULATION_KERNEL_SYSTEMS)
    helper_text = _text(PILOT_WEAPON_RELEASE_SYSTEM)
    naval_helper_text = _text(NAVAL_MISSION_WEAPON_RELEASE_SYSTEM)
    engagement_event_types_text = _text(ENGAGEMENT_EVENT_TYPES)
    kernel_header_text = _text(SIMULATION_KERNEL_HEADER)
    kernel_cpp_text = _text(SIMULATION_KERNEL_CPP)
    kernel_services_text = _text(SIMULATION_KERNEL_SERVICES)
    weapon_api_text = _text(SIMULATION_KERNEL_WEAPON_API)
    release_service_text = _text(SIMULATION_KERNEL_WEAPON_RELEASE_SERVICE)
    release_service_header_text = _text(SIMULATION_KERNEL_WEAPON_RELEASE_SERVICE_HEADER)
    engagement_store_text = _text(SIMULATION_KERNEL_ENGAGEMENT_EVENT_STORE)
    engagement_store_cpp_text = _text(SIMULATION_KERNEL_ENGAGEMENT_EVENT_STORE_CPP)
    damage_debug_text = _text(SIMULATION_KERNEL_DAMAGE_DEBUG_API)
    cmake_text = _text(CMAKE_LISTS)
    inline_systems = INLINE_REGISTERED_SYSTEM_PATTERN.findall(systems_text)
    inline_on_update = [name for name, kind in inline_systems if kind == "OnUpdate"]

    assert inline_on_update == [], (
        "simulation_kernel_systems.cpp must not accumulate registered-in-place inline "
        "OnUpdate systems once PilotWeaponRelease has been migrated to a named helper"
    )
    assert '#include "systems/combat/pilot_weapon_release_system.h"' in systems_text
    assert '#include "systems/naval/naval_mission_weapon_release_system.h"' in systems_text
    assert "IWeaponReleaseService& weapon_release_service = *this" not in systems_text
    assert "register_pilot_weapon_release_system(ecs, *weapon_release_service_)" in systems_text
    assert "register_naval_mission_weapon_release_system(ecs, *weapon_release_service_)" in systems_text
    assert "ecs.set<EngagementEventRecorderRef>({this})" not in systems_text
    assert "ecs.set<EngagementEventRecorderRef>({engagement_event_store_.get()})" in systems_text
    assert "class SimulationKernel :" not in kernel_header_text
    assert "public IWeaponReleaseService" not in kernel_header_text
    assert "public IEngagementEventRecorder" not in kernel_header_text
    assert "std::unique_ptr<IWeaponReleaseService> weapon_release_service_" in kernel_header_text
    assert (
        "std::unique_ptr<SimulationKernelEngagementEventStore> engagement_event_store_"
        in kernel_header_text
    )
    assert "RecentEngagementEvents recent_engagement_events_" not in kernel_header_text
    assert "struct RecentEngagementEvents" not in kernel_header_text
    assert '#include "core/engine/simulation_kernel_engagement_event_store.h"' not in kernel_header_text
    assert '#include "core/engine/engagement_event_types.h"' in kernel_header_text
    assert "struct RecentEngagementEvents" in engagement_event_types_text
    assert "next_engagement_event_id_" not in kernel_header_text
    assert "pending_effects_launch_event_id_" not in kernel_header_text
    assert "record_legacy_launch_event(" not in kernel_header_text
    assert "record_effects_damage_event(" not in kernel_header_text
    assert "capture_engagement_damage_state(" not in kernel_header_text
    assert "public IEngagementEventRecorder" in engagement_store_text
    assert "public IEngagementLaunchRecorder" in engagement_store_text
    assert '#include "core/interfaces/engagement_launch_recorder.h"' in engagement_store_text
    assert "RecentEngagementEvents recent_engagement_events_" in engagement_store_text
    assert "next_engagement_event_id_" in engagement_store_text
    assert "pending_effects_launch_event_id_" in engagement_store_text
    assert "SimulationKernelEngagementEventStore::record_legacy_launch_event(" in engagement_store_cpp_text
    assert "SimulationKernelEngagementEventStore::record_effects_damage_event(" in engagement_store_cpp_text
    assert "EngagementEffectsDamageEventRecord record" in engagement_store_text
    assert "EngagementEffectsDamageEventRecord event_record{}" in release_service_text
    assert "SimulationKernelEngagementEventStore::capture_engagement_damage_state(" in engagement_store_cpp_text
    assert "SimulationKernelEngagementEventStore::" not in damage_debug_text
    assert "SimulationKernelWeaponReleaseService final : public IWeaponReleaseService" not in kernel_cpp_text
    assert (
        "SimulationKernelEngagementEventRecorder final : public IEngagementEventRecorder"
        not in kernel_cpp_text
    )
    assert "SimulationKernelEngagementEventRecorder" not in kernel_services_text
    assert (
        "SimulationKernelWeaponReleaseService final : public IWeaponReleaseService"
        in release_service_header_text
    )
    assert (
        "SimulationKernelEngagementEventRecorder final : public IEngagementEventRecorder"
        not in kernel_services_text
    )
    assert "make_simulation_kernel_weapon_release_service(" in kernel_services_text
    assert "make_simulation_kernel_weapon_release_service(" in kernel_cpp_text
    assert "make_simulation_kernel_weapon_release_service(*this)" not in kernel_cpp_text
    assert "std::make_unique<SimulationKernelEngagementEventStore>(ecs)" in kernel_cpp_text
    assert "src/core/engine/simulation_kernel_engagement_event_store.cpp" in cmake_text
    assert "src/core/engine/simulation_kernel_services.cpp" in cmake_text
    assert "src/core/engine/simulation_kernel_weapon_release_service.cpp" in cmake_text
    assert "weapon_release_service_->fire_missile(" in weapon_api_text
    assert "weapon_release_service_->fire_naval_weapon(" in weapon_api_text
    assert "SimulationKernelWeaponReleaseService::fire_missile(" in release_service_text
    assert "SimulationKernelWeaponReleaseService::fire_weapon_from_pilot_action(" in release_service_text
    assert "SimulationKernelWeaponReleaseService::fire_naval_weapon_from_mission_command(" in release_service_text
    assert "launch_recorder_.record_legacy_launch_event(" in release_service_text
    assert "SimulationKernel&" not in release_service_header_text
    assert "SimulationKernel&" not in release_service_text
    assert "kernel_.fire_weapon_from_pilot_action(" not in kernel_services_text
    assert "kernel_.fire_naval_weapon_from_mission_command(" not in kernel_services_text
    assert 'ecs.system<const PilotAction>("PilotWeaponRelease")' not in systems_text
    assert 'query<const MissionCommand, const NavalWeaponSystem>()' not in kernel_cpp_text

    assert '#include "core/engine/simulation_kernel.h"' not in helper_text
    assert '#include "core/engine/simulation_kernel.h"' not in naval_helper_text
    assert "SimulationKernel&" not in helper_text
    assert "SimulationKernel&" not in naval_helper_text
    assert '#include "core/interfaces/weapon_release_service.h"' in helper_text
    assert '#include "core/interfaces/weapon_release_service.h"' in naval_helper_text
    assert "register_pilot_weapon_release_system(" in helper_text
    assert "IWeaponReleaseService& weapon_release_service" in helper_text
    assert 'ecs.system<const PilotAction>("PilotWeaponRelease")' in helper_text
    assert "fire_weapon_from_pilot_action(" in helper_text
    assert "register_naval_mission_weapon_release_system(" in naval_helper_text
    assert "IWeaponReleaseService& weapon_release_service" in naval_helper_text
    assert 'ecs.system<const MissionCommand, const NavalWeaponSystem>("NavalMissionWeaponRelease")' in naval_helper_text
    assert "fire_naval_weapon_from_mission_command(" in naval_helper_text


def test_tm04_weapon_release_service_is_not_a_kernel_forwarding_adapter() -> None:
    kernel_header_text = _text(SIMULATION_KERNEL_HEADER)
    kernel_services_text = _text(SIMULATION_KERNEL_SERVICES)
    weapon_api_text = _text(SIMULATION_KERNEL_WEAPON_API)
    release_service_text = _text(SIMULATION_KERNEL_WEAPON_RELEASE_SERVICE)
    release_service_header_text = _text(SIMULATION_KERNEL_WEAPON_RELEASE_SERVICE_HEADER)

    assert "friend class SimulationKernelWeaponReleaseService" not in kernel_header_text
    assert "fire_weapon_from_pilot_action(uint64_t attacker_id)" not in kernel_header_text
    assert "try_fire_naval_mission_weapon(" not in kernel_header_text
    assert '#include "simulation_kernel.h"' not in release_service_text
    assert "SimulationKernel&" not in release_service_header_text
    assert "SimulationKernel&" not in release_service_text
    assert "kernel_." not in kernel_services_text
    assert "kernel_." not in release_service_text
    assert "SimulationKernel::fire_weapon_from_pilot_action(" not in weapon_api_text
    assert "SimulationKernel::try_fire_naval_mission_weapon(" not in weapon_api_text
    for marker in (
        "SimulationKernelWeaponReleaseService::fire_missile(",
        "resolve_missile_launch_definition(",
        "naval_weapon_mounts::consume_mount_shot(",
        "launch_recorder_.record_legacy_launch_event(",
        "damage_recorder_.record_effects_damage_event(",
        "apply_proximity_hit_(",
    ):
        assert marker in release_service_text


def test_wp22_bindings_core_keeps_explicit_diagnostics_and_legacy_allowlists() -> None:
    names = _simulation_kernel_binding_names()
    binding_set = set(names)
    text = _text(BINDINGS_CORE)

    assert "Maintained SimulationKernel API surface" in text
    assert "Diagnostics-only introspection surface." in text
    assert "Legacy compatibility debug surface." in text
    assert "Diagnostics override surface." in text
    assert "bind_simulation_kernel_maintained_surface(simulation_kernel);" in text
    assert "bind_simulation_kernel_diagnostics_introspection_surface(simulation_kernel);" in text
    assert "bind_simulation_kernel_legacy_compatibility_debug_surface(simulation_kernel);" in text
    assert "bind_simulation_kernel_diagnostics_override_surface(simulation_kernel);" in text

    assert BINDINGS_DIAGNOSTICS_ALLOWLIST.issubset(binding_set)
    assert BINDINGS_LEGACY_ALLOWLIST.issubset(binding_set)

    for name in binding_set:
        if name.startswith("debug_"):
            assert name in BINDINGS_DIAGNOSTICS_ALLOWLIST | BINDINGS_LEGACY_ALLOWLIST, (
                "new debug binding requires an explicit WP22-E allowlist entry: "
                f"{name}"
            )

    assert "set_contact_list" in BINDINGS_DIAGNOSTICS_ALLOWLIST
    assert "debug_set_legacy_movement_command" in BINDINGS_LEGACY_ALLOWLIST


def test_wp22_bindings_core_direct_world_entity_drilling_stays_quarantined() -> None:
    text = _text(BINDINGS_CORE)
    maintained_block = _extract_function_block(
        text,
        "void bind_simulation_kernel_maintained_surface("
    )
    diagnostics_block = _extract_function_block(
        text,
        "void bind_simulation_kernel_diagnostics_introspection_surface("
    )
    legacy_block = _extract_function_block(
        text,
        "void bind_simulation_kernel_legacy_compatibility_debug_surface("
    )
    override_block = _extract_function_block(
        text,
        "void bind_simulation_kernel_diagnostics_override_surface("
    )
    quarantine_helper = _extract_function_block(
        text,
        "flecs::entity diagnostics_legacy_binding_entity_quarantine_lookup("
    )

    assert "self.get_world().entity(" not in maintained_block
    assert "lookup_entity(" not in maintained_block
    assert "self.get_world().entity(" not in override_block
    assert "WP22-R3 quarantine marker" in quarantine_helper
    assert "self.get_world().entity(" in quarantine_helper
    assert "diagnostics_legacy_binding_entity_quarantine_lookup(" in diagnostics_block
    assert "diagnostics_legacy_binding_entity_quarantine_lookup(" in legacy_block
    assert "self.get_world().entity(" not in diagnostics_block
    assert "self.get_world().entity(" not in legacy_block
    assert "lookup_entity(" not in text


def test_wp22_legacy_debug_setter_routes_through_bridge_helpers_not_direct_component_writes() -> None:
    text = _text(BINDINGS_CORE)
    legacy_block = _extract_function_block(
        text,
        "void bind_simulation_kernel_legacy_compatibility_debug_surface("
    )
    setter_block = _extract_function_block(
        legacy_block,
        '.def("debug_set_legacy_movement_command"'
    )

    assert "diagnostics_quarantined_legacy_movement_bridge_write(" in setter_block
    assert "diagnostics_legacy_binding_entity_quarantine_lookup(self, entity_id)" in setter_block
    assert "e.set<MovementCommand>" not in setter_block
    assert "make_legacy_autopilot_movement_command(" not in setter_block
    assert "set_compatibility_autopilot_movement_command(" not in setter_block
    assert "deactivate_compatibility_movement_command(e)" not in setter_block
    bridge_helper_block = _extract_function_block(
        text,
        "void diagnostics_quarantined_legacy_movement_bridge_write("
    )
    assert "WP22-R1-2 quarantine marker" in bridge_helper_block
    assert "set_compatibility_autopilot_movement_command(" in bridge_helper_block
    assert "deactivate_compatibility_movement_command(e)" in bridge_helper_block


def test_wp22_debug_movement_mirror_and_pending_shells_carry_quarantine_snapshot_markers() -> None:
    text = _text(BINDINGS_CORE)
    diagnostics_block = _extract_function_block(
        text,
        "void bind_simulation_kernel_diagnostics_introspection_surface("
    )
    legacy_block = _extract_function_block(
        text,
        "void bind_simulation_kernel_legacy_compatibility_debug_surface("
    )

    for binding_name in (
        "debug_get_pending_movement_command",
        "debug_get_pending_action_command",
    ):
        binding_block = _extract_function_block(
            diagnostics_block,
            f'.def("{binding_name}"'
        )
        assert "diagnostics_mark_read_only_snapshot(" in binding_block
        assert '"diagnostics_pending_transport_shell"' in binding_block
        assert 'out["diagnostics_transport_shell"] = true;' in binding_block
        assert 'out["read_only_snapshot"] = true;' not in binding_block
        assert 'out["maintained_truth"] = false;' not in binding_block
        assert 'out["state_access_mode"] = "read_only_transport_shell";' in binding_block
        assert 'out["transport_shell_truth_owner"] =' in binding_block
        assert "read-only transport shell snapshot" in binding_block

    legacy_getter_block = _extract_function_block(
        legacy_block,
        '.def("debug_get_legacy_movement_command"'
    )
    assert "diagnostics_mark_read_only_snapshot(" in legacy_getter_block
    assert '"diagnostics_legacy_mirror"' in legacy_getter_block
    assert 'out["diagnostics_legacy_mirror"] = true;' in legacy_getter_block
    assert 'out["state_access_mode"] = "read_only_legacy_mirror";' in legacy_getter_block
    assert 'out["mirror_truth_owner"] = "typed_control_state_bridge_projection";' in legacy_getter_block
    assert "read-only legacy movement shell mirror" in legacy_getter_block

    marker_helper = _extract_function_block(
        text,
        "void diagnostics_mark_read_only_snapshot("
    )
    assert 'out["diagnostics_only"] = true;' in marker_helper
    assert 'out["quarantined_surface"] = true;' in marker_helper
    assert 'out["read_only_snapshot"] = true;' in marker_helper
    assert 'out["maintained_truth"] = false;' in marker_helper
    assert 'out["diagnostics_quarantine_marker"] = "WP22-R1-2";' in marker_helper


def test_wp22_bindings_core_still_exposes_broad_surface_as_quarantined_fact() -> None:
    names = _simulation_kernel_binding_names()
    assert len(names) == 83, (
        "WP22-E first wave expects the broad SimulationKernel binding count to stay explicit; "
        "update this guard only with a deliberate allowlist reshaping change"
    )


def test_wp22_typed_air_control_state_seam_stays_small_and_owner_named() -> None:
    control_state_text = _text(MISSION_COMMAND_CONTROL_STATE)
    resolution_text = _text(AIR_CONTROL_RESOLUTION)
    line_count = _line_count(MISSION_COMMAND_CONTROL_STATE)

    assert "struct MissionCommandTypedAirControlState {" in control_state_text
    assert "Minimal typed ownership seam for air-control semantics" in control_state_text
    assert "MissionCommandTypedAirControlState typed_air_control{};" in control_state_text
    assert "mission_command_typed_air_control_active(" in control_state_text
    assert "reset_mission_command_typed_air_control_state(" in control_state_text
    assert "set_mission_command_typed_air_control_state(" in control_state_text
    assert "active_typed_air_control_state(" in resolution_text
    assert "MissionCommandTypedAirControlState" in resolution_text
    assert line_count < 160, (
        "typed air-control owner seam should remain a compact bridge-owned header, "
        "not a new god file"
    )


def test_wp22_exact_stage_inventory_stays_contract_ledger_not_runtime_truth_register() -> None:
    exact_stage_inventory = (
        REPO_ROOT / "src" / "core" / "engine" / "exact_stage_inventory.cpp"
    )
    text = _text(exact_stage_inventory)
    line_count = _line_count(exact_stage_inventory)

    for required in (
        "Guarded contract ledger for exact-stage migration evidence.",
        "They are not maintained implementation truth by themselves.",
        "maintained delayed-delivery truth lands in MissionCommandControlState",
        "PendingActionCommand remains a quarantined legacy transport shell in this slice.",
        "PendingActionCommand.typed_air_control_bridge (overlay projection)",
        "MissionCommandControlState is the maintained typed owner here.",
        "Propulsion runtime state is the maintained fuel-burn input here.",
    ):
        assert required in text

    for forbidden in (
        "Map normalized RL actions onto legacy heading/speed/altitude targets.",
        "Apply first-order lag to heading, speed, and altitude targets.",
        "Consumes the global frame clock. It is the first exact stage that mutates movement-command intent.",
        "optional compatibility mirror",
        "maintained command owner",
    ):
        assert forbidden not in text

    assert line_count < 500, (
        "exact-stage inventory should remain a compact contract ledger and guard surface, "
        "not expand into another structural god file"
    )


def test_wp22_command_link_pending_transport_headers_keep_typed_owner_markers_explicit() -> None:
    command_link = _text(REPO_ROOT / "src" / "components" / "command" / "command_link.h")
    bridge = _text(REPO_ROOT / "src" / "components" / "command" / "legacy_command_bridge.h")
    command_api = _text(REPO_ROOT / "src" / "core" / "engine" / "simulation_kernel_command_api.cpp")
    command_link_system = _text(REPO_ROOT / "src" / "systems" / "systems" / "command_link_system.h")

    for required in (
        "Diagnostics transport shell only; maintained delivery must consume typed_command.",
        "refresh_pending_movement_command_diagnostics_shell(",
        "typed_air_control_bridge",
        "Bridge-owned typed overlay snapshot only. This is not a full typed",
        "action replacement; it merely preserves the maintained air-control",
    ):
        assert required in command_link

    for required in (
        "refresh_compatibility_typed_air_control_from_pending_action_bridge(",
        "refresh_optional_pending_action_typed_air_control_bridge(",
    ):
        assert required in bridge

    for required in (
        "refresh_pending_action_command_typed_air_control_bridge(*pending);",
        "refresh_pending_movement_command_diagnostics_shell(*pending);",
    ):
        assert required in command_api

    for required in (
        "refresh_optional_pending_action_typed_air_control_bridge(",
        "refresh_pending_movement_command_diagnostics_shell(pending);",
    ):
        assert required in command_link_system


def test_a2_structured_air_effects_do_not_write_rl_score_authority() -> None:
    text = _text(DEFAULT_EFFECTS_MODEL)
    legacy_start = text.index("if (hp && !structured_air_target) {")
    legacy_end = text.index("// --- 2. Geometric Damage Logic (New) ---", legacy_start)
    structured_start = text.index("if (platform_damage && structured_air_target && structure_hit)")
    structured_end = text.index("// --- 3. Fallback to Randomized Effects (Legacy) ---", structured_start)

    legacy_block = text[legacy_start:legacy_end]
    structured_block = text[structured_start:structured_end]

    assert "score->total_reward" in legacy_block
    assert "score->hits_landed" in legacy_block
    assert "score->kills_confirmed" in legacy_block
    assert "score->" not in structured_block


def test_wp22_structural_docs_keep_noether_and_remaining_non_counterfactual_blockers_explicit() -> None:
    text_en = _text(STRUCTURAL_DOC_EN)
    text_zh = _text(STRUCTURAL_DOC_ZH)

    for required in (
        "Noether pass",
        "`PilotWeaponRelease` and naval mission weapon release now route through named",
        "`default_unit_factory.h` no longer direct-includes `legacy_command.h`",
        "`default_factory_legacy_spawn_compat.h` seed seam remains evaluation/guard",
    ):
        assert required in text_en

    for required in (
        "Noether pass",
        "`PilotWeaponRelease` 与 naval mission weapon release 现在都通过命名 helper system 注册",
        "`default_unit_factory.h` 已不再 direct include `legacy_command.h`",
        "`default_factory_legacy_spawn_compat.h` seed seam 在 typed control-state",
    ):
        assert required in text_zh

    for forbidden in (
        "naval post-step fire loop remains the explicit ordering blocker",
        "naval post-step ordering blocker remains live",
        "naval post-step fire loop 仍开放",
    ):
        assert forbidden not in text_en
        assert forbidden not in text_zh
