from __future__ import annotations

import ast
from dataclasses import dataclass, fields
from pathlib import Path

from gym_envs.scenario_loader.runtime_state import (
    SCENARIO_LOADER_STATE_SHELL_ATTRS,
    SCENARIO_LOADER_STATE_SHELL_BLOCKED_OWNER_CANDIDATE,
    SCENARIO_LOADER_STATE_SHELL_CLASSIFICATION_BUCKETS,
    SCENARIO_LOADER_STATE_SHELL_CLASSIFICATIONS,
    SCENARIO_LOADER_STATE_SHELL_RUNTIME_MIRROR_ONLY,
    SCENARIO_LOADER_STATE_SHELL_SCENARIO_CONTENT_ADAPTER,
    SCENARIO_LOADER_STATE_SHELL_TRANSITIONAL_BEHAVIOR_MIRROR,
    ScenarioLoaderStateShell,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
WORLD_BATCH_VEC_ENV = REPO_ROOT / "python" / "rl" / "runtime" / "world_batch_vec_env.py"
WORLD_BATCH_ADAPTER = REPO_ROOT / "python" / "rl" / "runtime" / "world_batch" / "adapter.py"
WORLD_BATCH_RUNTIME_ACCESS = REPO_ROOT / "python" / "rl" / "runtime" / "world_batch" / "runtime_access.py"
LEADER_WORLD_BATCH_RUNTIME = REPO_ROOT / "python" / "rl" / "runtime" / "leader_world_batch_runtime.py"
RUNTIME_CONTRACTS = REPO_ROOT / "src" / "runtime" / "contracts"
RUNTIME_FACADE = REPO_ROOT / "src" / "runtime" / "facade"
RUNTIME_BINDINGS = REPO_ROOT / "src" / "interfaces" / "python" / "bindings_runtime.cpp"
CORE_SRC = REPO_ROOT / "src" / "core"


def _source() -> str:
    return WORLD_BATCH_VEC_ENV.read_text(encoding="utf-8")


def _adapter_source() -> str:
    return WORLD_BATCH_ADAPTER.read_text(encoding="utf-8")


def _leader_source() -> str:
    return LEADER_WORLD_BATCH_RUNTIME.read_text(encoding="utf-8")


def _runtime_access_source() -> str:
    return WORLD_BATCH_RUNTIME_ACCESS.read_text(encoding="utf-8")


def _maintained_execution_episode_compat_read_allowlist() -> set[str]:
    return {
        "python/rl/runtime/world_batch/adapter.py",
        "python/rl/runtime/world_batch/compat.py",
        "tests/world_batch/test_world_batch_vec_env.py",
    }


def _iter_maintained_python_paths() -> list[Path]:
    return [
        *REPO_ROOT.joinpath("python", "rl", "runtime").rglob("*.py"),
        *(
            path
            for path in REPO_ROOT.joinpath("tests").rglob("*.py")
            if "tests/architecture/" not in path.relative_to(REPO_ROOT).as_posix()
        ),
    ]


def _iter_maintained_facade_guard_paths() -> list[Path]:
    return [
        *REPO_ROOT.joinpath("python", "rl", "runtime").rglob("*.py"),
        *REPO_ROOT.joinpath("tests", "runtime").rglob("*.py"),
        REPO_ROOT / "tests" / "world_batch" / "test_world_batch_vec_env.py",
    ]


def _class_stack(tree: ast.AST) -> dict[ast.AST, list[str]]:
    stack: list[str] = []
    out: dict[ast.AST, list[str]] = {}

    class Visitor(ast.NodeVisitor):
        def generic_visit(self, node: ast.AST) -> None:
            out[node] = list(stack)
            super().generic_visit(node)

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            out[node] = list(stack)
            stack.append(node.name)
            self.generic_visit(node)
            stack.pop()

    Visitor().visit(tree)
    return out


def _compat_batch_runtime_consumer_allowlist() -> set[str]:
    return {
        "tests/world_batch/test_world_batch_vec_env.py",
    }


def _runtime_escape_hatch_path_allowlist() -> set[str]:
    return {
        path
        for path, allowance in SCOPED_ESCAPE_HATCH_ALLOWLIST.items()
        if allowance.runtime_calls or allowance.runtime_world_calls
    }


@dataclass(frozen=True)
class EscapeHatchAllowance:
    runtime_calls: int
    runtime_world_calls: int
    world_batch_ctor_calls: int
    classification: str
    tier: str


SCOPED_ESCAPE_HATCH_ALLOWLIST = {
    "python/rl/runtime/world_batch/adapter.py": EscapeHatchAllowance(
        runtime_calls=1,
        runtime_world_calls=0,
        world_batch_ctor_calls=1,
        classification="compatibility_only",
        tier="maintained_training_path",
    ),
    "tests/runtime/facade/test_runtime_facade.py": EscapeHatchAllowance(
        runtime_calls=0,
        runtime_world_calls=0,
        world_batch_ctor_calls=1,
        classification="compatibility_only",
        tier="test_only",
    ),
    "tests/runtime/engagement/test_facade_engagement_export.py": EscapeHatchAllowance(
        runtime_calls=2,
        runtime_world_calls=2,
        world_batch_ctor_calls=0,
        classification="diagnostics_only",
        tier="test_only",
    ),
    "tests/runtime/engagement/test_live_engagement_event_capture.py": EscapeHatchAllowance(
        runtime_calls=2,
        runtime_world_calls=2,
        world_batch_ctor_calls=0,
        classification="diagnostics_only",
        tier="test_only",
    ),
    "tests/runtime/engagement/test_facade_engagement_evidence_gates.py": EscapeHatchAllowance(
        runtime_calls=1,
        runtime_world_calls=1,
        world_batch_ctor_calls=0,
        classification="diagnostics_only",
        tier="test_only",
    ),
    "tests/runtime/engagement/test_trace_replay_gates.py": EscapeHatchAllowance(
        runtime_calls=1,
        runtime_world_calls=1,
        world_batch_ctor_calls=0,
        classification="diagnostics_only",
        tier="test_only",
    ),
}


EXPECTED_SCENARIO_LOADER_STATE_SHELL_CLASSIFICATION_BY_BUCKET = {
    SCENARIO_LOADER_STATE_SHELL_SCENARIO_CONTENT_ADAPTER: frozenset(
        {
            "_cached_route_ref_id",
            "waypoints",
        }
    ),
    SCENARIO_LOADER_STATE_SHELL_RUNTIME_MIRROR_ONLY: frozenset(
        {
            "_waypoint_leg_origin_x",
            "_waypoint_leg_origin_y",
            "_waypoint_prev_dist_m",
            "gear_bonus_awarded",
            "last_reward_breakdown",
            "last_termination_reason",
            "liftoff_awarded",
            "off_runway_steps",
            "prev_alt",
            "prev_speed",
            "waypoint_idx",
            "waypoint_total_route_length_m",
        }
    ),
    SCENARIO_LOADER_STATE_SHELL_TRANSITIONAL_BEHAVIOR_MIRROR: frozenset(
        {
            "_approach_prev_dme_m",
            "_approach_prev_gs_abs",
            "_approach_prev_loc_abs",
            "mission_phase_name",
            "post_waypoint_transition",
        }
    ),
    SCENARIO_LOADER_STATE_SHELL_BLOCKED_OWNER_CANDIDATE: frozenset(
        {
            "leader_intent",
            "pilot_report",
            "task_order",
        }
    ),
}


def _runtime_escape_hatch_counts(path: Path) -> tuple[int, int, int]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    runtime_calls = 0
    runtime_world_calls = 0
    world_batch_ctor_calls = 0

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:
            nonlocal runtime_calls, runtime_world_calls, world_batch_ctor_calls
            func = node.func
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "ef_py"
                and func.attr == "WorldBatchRuntime"
            ):
                world_batch_ctor_calls += 1
            if isinstance(func, ast.Attribute) and func.attr == "runtime":
                runtime_calls += 1
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "world"
                and isinstance(func.value, ast.Call)
                and isinstance(func.value.func, ast.Attribute)
                and func.value.func.attr == "runtime"
            ):
                runtime_world_calls += 1
            self.generic_visit(node)

    Visitor().visit(tree)
    return runtime_calls, runtime_world_calls, world_batch_ctor_calls


def test_scenario_loader_state_shell_classification_is_architecture_contract() -> None:
    shell_fields = frozenset(field_def.name for field_def in fields(ScenarioLoaderStateShell))
    expected_buckets = frozenset(EXPECTED_SCENARIO_LOADER_STATE_SHELL_CLASSIFICATION_BY_BUCKET)

    assert shell_fields == SCENARIO_LOADER_STATE_SHELL_ATTRS
    assert frozenset(SCENARIO_LOADER_STATE_SHELL_CLASSIFICATIONS) == shell_fields
    assert SCENARIO_LOADER_STATE_SHELL_CLASSIFICATION_BUCKETS == expected_buckets

    actual_by_bucket = {
        bucket: frozenset(
            attr
            for attr, classification in SCENARIO_LOADER_STATE_SHELL_CLASSIFICATIONS.items()
            if classification == bucket
        )
        for bucket in expected_buckets
    }
    assert actual_by_bucket == EXPECTED_SCENARIO_LOADER_STATE_SHELL_CLASSIFICATION_BY_BUCKET


def test_world_batch_adapter_keeps_direct_runtime_fallback_inside_adapter() -> None:
    runtime_calls, runtime_world_calls, world_batch_ctor_calls = _runtime_escape_hatch_counts(WORLD_BATCH_ADAPTER)
    assert runtime_calls == 1
    assert runtime_world_calls == 0
    assert world_batch_ctor_calls == 1


def test_runtime_facade_escape_hatch_allowlist_stays_explicit() -> None:
    actual = {}
    for path in [
        WORLD_BATCH_ADAPTER,
        REPO_ROOT / "tests" / "runtime" / "facade" / "test_runtime_facade.py",
        REPO_ROOT / "tests" / "runtime" / "engagement" / "test_facade_engagement_export.py",
        REPO_ROOT / "tests" / "runtime" / "engagement" / "test_live_engagement_event_capture.py",
        REPO_ROOT / "tests" / "runtime" / "engagement" / "test_facade_engagement_evidence_gates.py",
        REPO_ROOT / "tests" / "runtime" / "engagement" / "test_trace_replay_gates.py",
    ]:
        counts = _runtime_escape_hatch_counts(path)
        if any(counts):
            allowlist_key = path.relative_to(REPO_ROOT).as_posix()
            actual[allowlist_key] = EscapeHatchAllowance(
                runtime_calls=counts[0],
                runtime_world_calls=counts[1],
                world_batch_ctor_calls=counts[2],
                classification=SCOPED_ESCAPE_HATCH_ALLOWLIST[allowlist_key].classification,
                tier=SCOPED_ESCAPE_HATCH_ALLOWLIST[allowlist_key].tier,
            )

    assert actual == SCOPED_ESCAPE_HATCH_ALLOWLIST, f"scoped escape hatch allowlist drifted: {actual}"


def test_world_batch_adapter_is_only_maintained_escape_hatch_in_scope() -> None:
    maintained = {
        path: allowance
        for path, allowance in SCOPED_ESCAPE_HATCH_ALLOWLIST.items()
        if allowance.tier == "maintained_training_path"
    }
    assert maintained == {
        "python/rl/runtime/world_batch/adapter.py": SCOPED_ESCAPE_HATCH_ALLOWLIST[
            "python/rl/runtime/world_batch/adapter.py"
        ]
    }


def test_world_batch_vec_env_does_not_branch_on_facade_presence_in_main_class() -> None:
    source = _source()
    main_class = source.split("class WorldBatchVecEnv", 1)[1]
    assert "_runtime_facade is not None" not in main_class
    assert "_runtime_facade is None" not in main_class


def test_world_batch_vec_env_main_class_does_not_cache_raw_runtime_handles() -> None:
    source = _source()
    main_class = source.split("class WorldBatchVecEnv", 1)[1]
    assert "_batch_runtime" not in main_class
    assert "_runtime_facade" not in main_class
    assert ".compat_runtime" not in main_class


def test_world_batch_vec_env_access_stays_thin_forwarder_without_raw_runtime_ownership() -> None:
    source = _runtime_access_source()
    assert ".batch_runtime." not in source
    assert ".runtime()" not in source
    assert ".world(" not in source
    assert "WorldBatchRuntime" not in source
    assert "RuntimeFacade" not in source


def test_leader_world_batch_runtime_does_not_reach_raw_world_handles() -> None:
    source = _leader_source()
    assert ".batch_runtime.world(" not in source
    assert ".world_vec.batch_runtime.world(" not in source


def test_leader_world_batch_runtime_keeps_batch_runtime_as_compat_only_surface() -> None:
    source = _leader_source()
    assert "self.batch_runtime.get_instrument_states_batch(" not in source
    assert "self.batch_runtime.get_agent_observations_batch(" not in source
    assert "self.batch_runtime.set_pilot_actions_batch(" not in source
    assert "self.batch_runtime.step_worlds(" not in source


def test_maintained_paths_do_not_add_new_execution_episode_batch_runtime_reads() -> None:
    forbidden_markers = (
        ".batch_runtime.export_execution_episode_states_batch(",
        ".batch_runtime.execution_episode_controller_ready(",
    )
    violations: list[tuple[str, int, str]] = []
    allowlist = _maintained_execution_episode_compat_read_allowlist()

    for path in _iter_maintained_python_paths():
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel in allowlist:
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if any(marker in stripped for marker in forbidden_markers):
                violations.append((rel, lineno, stripped))

    assert not violations, (
        "maintained paths must use vec-env/runtime facade execution-episode helpers instead of "
        f"compat batch_runtime reads: {violations}"
    )


def test_maintained_paths_do_not_add_new_batch_runtime_consumers_outside_compatibility_tests() -> None:
    violations: list[tuple[str, int, str]] = []
    allowlist = _compat_batch_runtime_consumer_allowlist()

    for path in _iter_maintained_facade_guard_paths():
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel in allowlist:
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if ".batch_runtime." in stripped:
                violations.append((rel, lineno, stripped))

    assert not violations, (
        "maintained facade-layer paths must keep vec_env.batch_runtime consumers inside explicit "
        f"compatibility tests only: {violations}"
    )


def test_maintained_paths_do_not_add_new_runtime_facade_runtime_consumers() -> None:
    allowlist = _runtime_escape_hatch_path_allowlist()
    violations: list[tuple[str, int, int]] = []

    for path in _iter_maintained_facade_guard_paths():
        rel = path.relative_to(REPO_ROOT).as_posix()
        runtime_calls, runtime_world_calls, _ = _runtime_escape_hatch_counts(path)
        if rel in allowlist:
            continue
        if runtime_calls or runtime_world_calls:
            violations.append((rel, runtime_calls, runtime_world_calls))

    assert not violations, (
        "maintained facade-layer paths must keep RuntimeFacade.runtime() escape hatches inside the "
        f"explicit compatibility/diagnostics allowlist only: {violations}"
    )


def test_leader_world_batch_runtime_does_not_call_runtime_facade_runtime() -> None:
    tree = ast.parse(_leader_source())
    violations: list[tuple[int, str]] = []

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "runtime":
                violations.append((node.lineno, "runtime()"))
            self.generic_visit(node)

    Visitor().visit(tree)
    assert not violations, f"leader runtime escaped facade adapter layering: {violations}"


def test_runtime_facade_escape_hatch_is_documented() -> None:
    header = (REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade.h").read_text(encoding="utf-8")
    readme = (REPO_ROOT / "src" / "runtime" / "facade" / "README.md").read_text(encoding="utf-8")
    assert "Compatibility escape hatch" in header
    assert "Maintained frontends should use facade-level request/result APIs" in header
    assert "必须把访问集中在一个显式 adapter" in readme
    assert "不得直接调用 `RuntimeFacade.runtime()`" in readme
    assert "不应缓存 raw `WorldBatchRuntime`" in readme


def test_runtime_contract_headers_do_not_include_engine_headers() -> None:
    header_paths = [
        *RUNTIME_CONTRACTS.glob("*.h"),
        *RUNTIME_FACADE.glob("*_types.h"),
    ]
    violations: list[tuple[str, int, str]] = []
    for path in header_paths:
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#include") and '"core/engine/' in stripped:
                violations.append((str(path.relative_to(REPO_ROOT)), lineno, stripped))

    assert not violations, f"runtime contract/facade type headers include engine headers: {violations}"


def test_runtime_facade_public_header_hides_engine_owner_storage() -> None:
    header = (RUNTIME_FACADE / "runtime_facade.h").read_text(encoding="utf-8")
    assert '#include "core/engine/world_batch_runtime.h"' not in header
    assert "class WorldBatchRuntime;" in header
    assert "std::unique_ptr<WorldBatchRuntime>" in header


def test_runtime_facade_does_not_include_or_call_gpu_helpers() -> None:
    gpu_markers = (
        '#include "gpu/',
        "#include <gpu/",
        "gpu::",
        "probe_gpu_device",
        "probe_device(",
        "last_visual_experiment_stats",
        "last_execution_observation_stats",
        "last_flight_shaping_stats",
        "device_resident",
        "last_visual_output_device_ptr",
        "last_execution_observation_output_device_ptr",
        "last_flight_shaping_output_device_ptr",
    )
    violations: list[tuple[str, str]] = []
    for path in sorted(RUNTIME_FACADE.glob("*")):
        if path.suffix not in {".h", ".cpp"}:
            continue
        source = path.read_text(encoding="utf-8")
        for marker in gpu_markers:
            if marker in source:
                violations.append((str(path.relative_to(REPO_ROOT)), marker))

    assert not violations, f"RuntimeFacade must not depend on GPU helper/probe implementation: {violations}"


def test_runtime_facade_capabilities_stay_independent_from_cuda_experiment_signals() -> None:
    source = (RUNTIME_FACADE / "runtime_facade.cpp").read_text(encoding="utf-8")
    capabilities_body = source.split("RuntimeCapabilities RuntimeFacade::capabilities() const noexcept {", 1)[1]
    capabilities_body = capabilities_body.split(
        "RuntimeFidelityAdmission RuntimeFacade::admit_fidelity_request(",
        1,
    )[0]

    forbidden_markers = (
        "EF_ENABLE_CUDA_EXPERIMENTS",
        "cuda_runtime_built",
        "cuda_runtime_available",
        "device_count",
        "active_device",
        "compute_major",
        "compute_minor",
        "runtime_version",
        "free_global_mem_bytes",
        "total_global_mem_bytes",
        "device_name",
        "error_message",
        "probe_gpu_device",
        "gpu::probe_device",
        "last_visual_experiment_stats",
        "last_execution_observation_stats",
        "last_flight_shaping_stats",
        "used_cuda",
        "device_view",
        "device_ptr",
        "last_visual_output_device_ptr",
        "last_execution_observation_output_device_ptr",
        "last_flight_shaping_output_device_ptr",
    )
    violations = [marker for marker in forbidden_markers if marker in capabilities_body]
    assert not violations, (
        "RuntimeFacade.capabilities() must stay fail-closed and must not read CUDA "
        f"availability/helper/probe/device-resident signals: {violations}"
    )


def test_runtime_binding_capability_surface_keeps_gpu_helper_signals_separate() -> None:
    source = RUNTIME_BINDINGS.read_text(encoding="utf-8")
    runtime_capabilities_block = source.split('nb::class_<RuntimeCapabilities>(m, "RuntimeCapabilities")', 1)[1]
    runtime_capabilities_block = runtime_capabilities_block.split(
        'nb::class_<RuntimeBatchConfig>(m, "RuntimeBatchConfig")',
        1,
    )[0]
    assert "cuda_runtime_available" not in runtime_capabilities_block
    assert "probe_gpu_device" not in runtime_capabilities_block
    assert "used_cuda" not in runtime_capabilities_block


def test_backend_profile_contract_marks_gpu_helpers_export_only_and_non_promoting() -> None:
    header = (RUNTIME_CONTRACTS / "backend_profile_contracts.h").read_text(encoding="utf-8")
    diagnostics_only_profile = header.split(
        "BackendProfileContract{\n            .backend_profile_id =\n                std::string(kBackendProfileIdGpuHelpersDiagnosticsOnly),",
        1,
    )[1]
    diagnostics_only_profile = diagnostics_only_profile.split(
        "BackendProfileContract{\n            .backend_profile_id =\n                std::string(kBackendProfileIdGpuExactUnmaintainedCandidate),",
        1,
    )[0]

    required_markers = (
        '.sync_policy = std::string(kBackendProfileSyncPolicyExportOnly)',
        "helper-local diagnostics buffers or probes only",
        "do not affect committed state",
        "never maintained state",
        "support stay false",
        "cannot accept it as maintained parity",
        ".exact_gpu_supported = false",
        ".resident_state_supported = false",
        ".shadow_supported = false",
        ".device_observation_view_supported = false",
    )
    missing = [marker for marker in required_markers if marker not in diagnostics_only_profile]
    assert not missing, (
        "GPU helper diagnostics-only backend profile drifted away from the WP19-C non-promotion "
        f"boundary: {missing}"
    )


def test_core_runtime_does_not_probe_gpu_for_facade_capability_projection() -> None:
    forbidden_markers = (
        "RuntimeCapabilities",
        "supports_exact_gpu_backend",
        "supports_resident_state",
        "supports_shadow_compare",
        "probe_gpu_device",
        "gpu::probe_device",
        "last_visual_experiment_stats",
        "last_execution_observation_stats",
        "last_flight_shaping_stats",
        "last_visual_output_device_ptr",
        "last_execution_observation_output_device_ptr",
        "last_flight_shaping_output_device_ptr",
    )
    violations: list[tuple[str, str]] = []
    for path in sorted(CORE_SRC.rglob("*")):
        if path.suffix not in {".h", ".cpp", ".cc", ".cxx"}:
            continue
        source = path.read_text(encoding="utf-8")
        for marker in forbidden_markers:
            if marker in source:
                violations.append((str(path.relative_to(REPO_ROOT)), marker))

    assert not violations, f"core runtime must not project maintained GPU/resident/shadow capabilities: {violations}"


def test_resident_state_candidate_stays_fail_closed_and_exports_remain_host_visible() -> None:
    contracts = (RUNTIME_CONTRACTS / "backend_profile_contracts.h").read_text(encoding="utf-8")
    facade_types = (RUNTIME_FACADE / "runtime_facade_types.h").read_text(encoding="utf-8")
    facade_cpp = (RUNTIME_FACADE / "runtime_facade.cpp").read_text(encoding="utf-8")

    assert "kBackendProfileIdResidentStateUnmaintainedCandidate" in contracts
    resident_section = contracts.split("kBackendProfileIdResidentStateUnmaintainedCandidate", 1)[1]
    assert ".sync_policy = std::string(kBackendProfileSyncPolicyUndeclaredBlocked)" in resident_section
    assert ".maintained_status =" in resident_section
    assert "kBackendProfileMaintainedStatusUnmaintainedCandidate" in resident_section
    assert ".resident_state_supported = false" in resident_section
    assert "Candidate backend-resident operational shards are not maintained truth." in resident_section
    assert "Blocked until ownership split, sync cadence/trigger, barriers, host-visible reconstruction/export" in resident_section

    capabilities_section = facade_cpp.split("RuntimeCapabilities RuntimeFacade::capabilities() const noexcept", 1)[1]
    assert ".supports_resident_state = false" in capabilities_section
    assert ".resident_state_candidate_profile_id =" in capabilities_section
    assert ".resident_state_candidate_parity_budget_ref =" in capabilities_section
    assert ".resident_state_rejection_reason =" in capabilities_section

    observation_packet_section = facade_types.split("struct ObservationBatchPacket", 1)[1].split("struct EngagementEventPacket", 1)[0]
    assert 'std::string barrier_id = "export";' in observation_packet_section
    assert "kPolicySourceLabelFacadeObservationPacket" in observation_packet_section
    assert "kPolicyMaintainedStatusMaintained" in observation_packet_section

    engagement_packet_section = facade_types.split("struct EngagementEventPacket", 1)[1].split("struct ExecutionBatchStepResult", 1)[0]
    assert 'std::string barrier_id = "export";' in engagement_packet_section
    assert 'std::string barrier_detail = "maintained_facade_export";' in engagement_packet_section
    assert "kPolicySourceLabelTrackStatePacket" in engagement_packet_section
    assert "kPolicySourceLabelWorldTruthDiagnostics" in engagement_packet_section
    assert "kPolicyMaintainedStatusDiagnosticsOnly" in engagement_packet_section
