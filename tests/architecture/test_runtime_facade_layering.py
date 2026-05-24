from __future__ import annotations

import ast
from dataclasses import dataclass, fields
from pathlib import Path

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

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
TASKING_BRIDGE = REPO_ROOT / "python" / "rl" / "tasking" / "bridge.py"
RUNTIME_CONTRACTS = REPO_ROOT / "src" / "runtime" / "contracts"
RUNTIME_FACADE = REPO_ROOT / "src" / "runtime" / "facade"
RUNTIME_BINDINGS = REPO_ROOT / "src" / "interfaces" / "python" / "bindings_runtime.cpp"
GPU_BINDINGS = REPO_ROOT / "src" / "interfaces" / "python" / "bindings_gpu.cpp"
WORLD_BATCH_RUNTIME_H = REPO_ROOT / "src" / "core" / "engine" / "world_batch_runtime.h"
WORLD_BATCH_RUNTIME_CPP = REPO_ROOT / "src" / "core" / "engine" / "world_batch_runtime.cpp"
CORE_SRC = REPO_ROOT / "src" / "core"
SCENARIO_RUNTIME = REPO_ROOT / "python" / "scenario" / "runtime"
UNIVERSAL_ENV = REPO_ROOT / "gym_envs" / "universal_env.py"


def _source() -> str:
    return WORLD_BATCH_VEC_ENV.read_text(encoding="utf-8")


def _adapter_source() -> str:
    return WORLD_BATCH_ADAPTER.read_text(encoding="utf-8")


def _leader_source() -> str:
    return LEADER_WORLD_BATCH_RUNTIME.read_text(encoding="utf-8")


def _runtime_access_source() -> str:
    return WORLD_BATCH_RUNTIME_ACCESS.read_text(encoding="utf-8")


def _gpu_bindings_source() -> str:
    return GPU_BINDINGS.read_text(encoding="utf-8")


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


def _iter_non_test_python_paths() -> list[Path]:
    excluded_prefixes = (".git", ".venv", "__pycache__", "build", "dist", "node_modules", "archive", "temp")
    return [
        path
        for path in sorted(REPO_ROOT.rglob("*.py"))
        if not any(part.startswith(excluded_prefixes) for part in path.parts)
        and not path.relative_to(REPO_ROOT).as_posix().startswith("tests/")
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
        "tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py",
        "tests/world_batch/test_world_batch_vec_env.py",
    }


def _wp22_loader_sim_guard_scope() -> dict[str, tuple[str, ...]]:
    return {
        "python/rl/runtime/world_batch_vec_env.py": (
            "handle.loader.sim,",
            "handle.loader.sim)",
        ),
        "python/rl/runtime/cooperative_world_batch_vec_env.py": (
            "slot_state.loader.sim,",
            "slot_state.loader.sim)",
            "loader.sim.get_time_step(",
        ),
        "python/rl/runtime/leader_world_batch_runtime.py": (
            "handle.loader.sim,",
            "handle.loader.sim)",
        ),
        "python/rl/runtime/single_world_batch_runtime.py": (
            "self.access.sim(env_idx),",
            "self.access.sim(env_idx))",
            "handle.loader.sim,",
            "handle.loader.sim)",
        ),
        "python/rl/tasking/bridge.py": (
            "loader.sim.set_mission_command(",
            "loader.sim.set_task_order(",
            "loader.sim.set_leader_intent(",
            "loader.sim.set_pilot_report(",
            "loader.sim.get_agent_observation(",
            "loader.sim.get_instrument_state(",
            "loader.sim.get_time_step(",
        ),
        "gym_envs/scenario_loader/behavior_runtime/naval_screen.py": (
            "loader.sim.get_unit_position(",
            "loader.sim.get_unit_velocity(",
            "loader.sim.is_unit_active(",
        ),
        "gym_envs/scenario_loader/behavior_runtime/command_chain.py": (
            "loader.sim.set_mission_command(",
            "loader.sim.get_time_step(",
        ),
        "gym_envs/scenario_loader/step_evaluation.py": (
            "loader.sim.get_time_step(",
        ),
        "gym_envs/scenario_loader/execution_runtime/shadow.py": (
            "loader.sim.get_time_step(",
        ),
        "gym_envs/scenario_loader/behavior_runtime/post_waypoint_transition.py": (
            "loader.sim.get_time_step(",
        ),
        "gym_envs/scenario_loader/behavior_runtime/scripted_opponents.py": (
            "loader.sim,",
            "loader.sim)",
        ),
        "gym_envs/scenario_loader/loading.py": (
            "loader.sim,",
            "loader.sim)",
        ),
        "gym_envs/scenario_loader/runtime_state.py": (
            "loader.sim,",
            "loader.sim)",
            "loader.sim.",
        ),
        "gym_envs/leader_env_parts/decision_runtime/commands.py": (
            "loader.sim.get_agent_observation(",
            "loader.sim.get_instrument_state(",
            "env.unwrapped.sim.get_time_step(",
        ),
        "gym_envs/leader_env_parts/bridges.py": (
            "loader.sim.set_task_order(",
            "loader.sim.set_leader_intent(",
            "loader.sim.set_pilot_report(",
        ),
    }


def _runtime_escape_hatch_path_allowlist() -> set[str]:
    return {
        path
        for path, allowance in SCOPED_ESCAPE_HATCH_ALLOWLIST.items()
        if allowance.runtime_calls or allowance.runtime_world_calls
    }


def _batch_runtime_attribute_lines(path: Path) -> list[int]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return sorted(
        {
            int(getattr(node, "lineno", 0) or 0)
            for node in ast.walk(tree)
            if isinstance(node, ast.Attribute) and node.attr == "batch_runtime"
        }
    )


def _world_call_lines(path: Path) -> list[int]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return sorted(
        {
            int(getattr(node, "lineno", 0) or 0)
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "world"
        }
    )


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
            if isinstance(func, ast.Attribute) and func.attr == "runtime_compatibility_quarantine":
                runtime_calls += 1
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "world_compatibility_quarantine"
                and isinstance(func.value, ast.Call)
                and isinstance(func.value.func, ast.Attribute)
                and func.value.func.attr == "runtime_compatibility_quarantine"
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


def test_world_batch_adapter_keeps_runtime_escape_hatch_lazy_and_explicit() -> None:
    source = _adapter_source()
    assert "self.facade.runtime_compatibility_quarantine() if self.facade is not None" not in source
    assert "def _compat_runtime_handle(self):" in source
    assert "def _compat_world(self, index: int):" in source
    assert "def world(self, index: int):" not in source
    assert "def world_compatibility_quarantine(self, index: int):" in source
    assert "class _WorldAccessProxy:" in source
    assert "def _scenario_loader_runtime(self, index: int) -> _ScenarioLoaderRuntimeProxy:" in source
    assert "def _build_runtime_world_layout_request(self, world_index: int, layout: Any):" in source
    assert "def _apply_runtime_world_layout_request(self, request: Any) -> Any:" in source
    assert "def _materialize_applied_world(self, world_index: int, layout: Any, entity_ids: Sequence[Any]) -> AppliedScenarioWorld:" in source
    assert "self._compat_runtime = self.facade.runtime_compatibility_quarantine()" in source
    assert "self._compat_runtime = None" in source
    assert "self._compat_runtime_handle().world_compatibility_quarantine(int(index))" in source
    assert "return _WorldAccessProxy(self, int(index))" in source
    assert "apply_world_layout_to_kernel(self.world_compatibility_quarantine(int(world_index)), layout)" not in source
    assert "ScenarioLoader(self.world_compatibility_quarantine(int(index)))" not in source
    assert "ScenarioLoader(self._compat_world(int(index)))" not in source
    assert "ScenarioLoader(self._scenario_loader_runtime(int(index)))" in source
    assert "self.world_compatibility_quarantine(int(world_index)).get_time_step()" not in source
    assert "self.world_compatibility_quarantine(int(world_index)).get_visual_observation(" not in source
    assert 'hasattr(self.world_compatibility_quarantine(int(world_index)), "get_visual_observation_downsampled")' not in source
    assert "def _require_compatibility_fallback(self, surface: str) -> None:" in source
    assert '_require_compatibility_fallback("RuntimeFacadeAdapter.legacy_visual_observation")' in source
    assert "return build_runtime_world_layout_request(" in source
    assert "return apply_runtime_world_layout_request_maintained(self.facade, request)" in source
    assert "apply_runtime_world_layout_request_compatibility_quarantine(" in source
    assert 'runtime_compatibility_required_message("RuntimeFacadeAdapter.apply_world_layout")' in source
    assert "result = self._apply_runtime_world_layout_request(request)" in source
    assert "self.facade.world_time_step(int(world_index))" in source
    assert "batch_target = self.facade if self.facade is not None else self._compat_runtime_handle()" in source
    assert "compute_world_batch_visual_observation_batch_numpy(" in source
    assert "compute_world_batch_visual_observation_batch_export(" in source
    step_worlds_section = source.split("def step_worlds(self, world_indices: Sequence[int]) -> None:", 1)[1].split(
        "def set_mission_commands_maintained_batch",
        1,
    )[0]
    assert "self.facade.step_batch()" in step_worlds_section
    assert 'runtime_compatibility_required_message("RuntimeFacadeAdapter.step_worlds")' in step_worlds_section
    assert "self._compat_runtime_handle().step_worlds(indices)" in step_worlds_section
    assert step_worlds_section.index("self.facade.step_batch()") < step_worlds_section.index(
        "self._compat_runtime_handle().step_worlds(indices)"
    )


def test_runtime_world_layout_setup_seam_stays_named_and_explicit() -> None:
    seam_source = (REPO_ROOT / "python" / "scenario" / "runtime" / "world_setup_compat.py").read_text(encoding="utf-8")

    assert "def build_runtime_world_layout_request(" in seam_source
    assert "def apply_runtime_world_layout_request_maintained(setup_target: Any, request: Any) -> Any:" in seam_source
    assert "def apply_runtime_world_layout_request_compatibility_quarantine(runtime: Any, request: Any) -> Any:" in seam_source
    assert "def apply_runtime_world_layout_request_compat(runtime: Any, request: Any) -> Any:" in seam_source
    assert "def apply_world_setup_request_maintained(setup_target: Any, request: Any) -> list[int]:" in seam_source
    assert 'hasattr(setup_target, "world")' in seam_source
    assert 'not hasattr(setup_target, "facade")' in seam_source
    assert "def apply_world_setup_payload_maintained(" in seam_source
    assert "def apply_world_setup_payload_compatibility_quarantine(" in seam_source
    assert "def read_runtime_world_time_step_compat(" in seam_source
    assert "RuntimeWorldLayoutRequestCompat" in seam_source
    assert "RuntimeWorldLayoutResultCompat" in seam_source


def test_wp24_scenario_setup_default_path_uses_maintained_facade_target() -> None:
    batch_apply = (SCENARIO_RUNTIME / "batch_apply.py").read_text(encoding="utf-8")
    adapter = _adapter_source()

    assert "def load_compiled_scenario_for_setup_target(" in batch_apply
    assert "def apply_world_layouts_to_setup_target(" in batch_apply
    assert "facade_setup_target" in batch_apply
    assert "apply_world_setup_payload_maintained(" in batch_apply
    assert "apply_world_setup_payload_compat(" not in batch_apply
    assert "load_compiled_scenario_batch = load_compiled_scenario_for_setup_target" in batch_apply

    assert "apply_world_setup_request_maintained(self.facade, request)" in adapter
    assert "apply_world_setup_request_compatibility_quarantine(" in adapter
    assert 'runtime_compatibility_required_message("RuntimeFacadeAdapter.apply_world_setup")' in adapter
    assert 'runtime_compatibility_required_message("RuntimeFacadeAdapter.apply_world_setup_batch")' in adapter


def test_wp24_scenario_raw_setup_fallbacks_are_quarantined_by_name() -> None:
    setup_source = (SCENARIO_RUNTIME / "world_setup_compat.py").read_text(encoding="utf-8")
    tree = ast.parse(setup_source)
    offenders: list[tuple[str, int, str]] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for child in ast.walk(node):
            if not (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Attribute)
                and child.func.attr in {"apply_world_setup_batch", "apply_world_layout"}
            ):
                continue
            if child.func.attr == "apply_world_layout" and node.name == "apply_runtime_world_layout_request_maintained":
                continue
            if "compatibility_quarantine" not in node.name:
                offenders.append((node.name, int(getattr(child, "lineno", 0) or 0), child.func.attr))

    assert not offenders, f"raw setup fallback calls must stay inside compatibility_quarantine helpers: {offenders}"


def test_wp24_scenario_runtime_does_not_construct_raw_runtime_on_production_path() -> None:
    violations: list[tuple[str, int, str]] = []
    forbidden_markers = ("ef_py.SimulationKernel(", "ef_py.WorldBatchRuntime(")

    for path in SCENARIO_RUNTIME.rglob("*.py"):
        rel = path.relative_to(REPO_ROOT).as_posix()
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            for marker in forbidden_markers:
                if marker in stripped:
                    violations.append((rel, lineno, stripped))

    assert not violations, (
        "scenario runtime setup must use maintained facade/adapter setup targets instead of "
        f"constructing raw runtime objects: {violations}"
    )


def test_wp24_universal_env_raw_kernel_path_is_explicit_compatibility_quarantine() -> None:
    universal_env = UNIVERSAL_ENV.read_text(encoding="utf-8")
    train_source = (REPO_ROOT / "train.py").read_text(encoding="utf-8")

    assert "runtime_compatibility_enabled: bool = False" in universal_env
    assert "self.runtime_compatibility_enabled = _normalize_runtime_compatibility_enabled(" in universal_env
    assert "if not self.runtime_compatibility_enabled:" in universal_env
    assert "_raw_universal_env_compatibility_required_message()" in universal_env
    assert universal_env.index("if not self.runtime_compatibility_enabled:") < universal_env.index(
        "self.sim = ef_py.SimulationKernel()"
    )
    assert "ef_py.WorldBatchRuntime(" not in universal_env
    assert "WorldBatchVecEnv/RuntimeFacadeAdapter" in universal_env

    assert "The standard UniversalEnv execution path owns a raw SimulationKernel" in train_source
    assert "runtime.world_batch_vec_env=true" in train_source
    assert "env.runtime_compatibility_enabled=true" in train_source


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
    assert ".runtime_compatibility_quarantine()" not in source
    assert ".world_compatibility_quarantine(" not in source
    assert "WorldBatchRuntime" not in source
    assert "RuntimeFacade" not in source


def test_leader_world_batch_runtime_does_not_reach_raw_world_handles() -> None:
    source = _leader_source()
    assert ".batch_runtime.world_compatibility_quarantine(" not in source
    assert ".world_vec.batch_runtime.world_compatibility_quarantine(" not in source


def test_leader_world_batch_runtime_keeps_batch_runtime_as_compat_only_surface() -> None:
    source = _leader_source()
    assert "self.batch_runtime.get_instrument_states_batch(" not in source
    assert "self.batch_runtime.get_agent_observations_batch(" not in source
    assert "self.batch_runtime.set_pilot_actions_batch(" not in source
    assert "self.batch_runtime.step_worlds(" not in source


def test_world_batch_vec_env_batch_runtime_requires_explicit_runtime_compatibility_flag() -> None:
    source = _source()
    assert "def batch_runtime(self):" in source
    assert "runtime_compatibility_enabled" in source
    assert "vec_env.batch_runtime" in source


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


def test_wp22_public_batch_runtime_consumers_stay_explicit_and_localized() -> None:
    allowlist = {
        "python/rl/runtime/cooperative_world_batch_vec_env.py",
        "python/rl/runtime/leader_world_batch_runtime.py",
        "python/rl/runtime/single_world_batch_runtime.py",
        "python/rl/runtime/world_batch/compat.py",
        "python/rl/runtime/world_batch_vec_env.py",
        "tools/diagnostics/benchmarks/world_batch_vec_env.py",
        "train.py",
    }
    violations: list[tuple[str, int]] = []

    for path in _iter_non_test_python_paths():
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel in allowlist:
            continue
        for lineno in _batch_runtime_attribute_lines(path):
            violations.append((rel, lineno))

    assert not violations, (
        "WP22 maintained non-test Python paths must keep vec_env.batch_runtime inside the explicit "
        f"compatibility/diagnostics allowlist only: {violations}"
    )


def test_wp22_public_world_escape_hatch_consumers_stay_explicit_and_localized() -> None:
    allowlist = {
        "python/rl/runtime/world_batch/adapter.py",
    }
    violations: list[tuple[str, int]] = []

    for path in _iter_non_test_python_paths():
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel in allowlist:
            continue
        for lineno in _world_call_lines(path):
            violations.append((rel, lineno))

    assert not violations, (
        "WP22 maintained non-test Python paths must keep public `.world_compatibility_quarantine()` escape-hatch calls inside the explicit "
        f"compatibility adapter allowlist only: {violations}"
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
        "maintained facade-layer paths must keep RuntimeFacade.runtime_compatibility_quarantine() escape hatches inside the "
        f"explicit compatibility/diagnostics allowlist only: {violations}"
    )


def test_wp22_loader_owned_runtime_paths_do_not_reintroduce_scattered_raw_sim_seams() -> None:
    scope = _wp22_loader_sim_guard_scope()
    violations: list[tuple[str, str]] = []

    for rel, markers in scope.items():
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        for marker in markers:
            if marker in text:
                violations.append((rel, marker))

    assert not violations, (
        "WP22 maintained loader/runtime paths must use loader-owned seams or "
        f"explicit tasking compatibility helpers instead of scattered raw loader.sim access: {violations}"
    )


def test_wp22_naval_screen_raw_unit_state_seam_stays_named_and_localized() -> None:
    text = (REPO_ROOT / "gym_envs" / "scenario_loader" / "behavior_runtime" / "naval_screen.py").read_text(encoding="utf-8")
    bridge_text = TASKING_BRIDGE.read_text(encoding="utf-8")

    assert "def _read_naval_screen_reference_motion(" in text
    assert "def _prefer_last_active_naval_screen_reference(" in text
    assert "loader_owned_raw_sim_compat(loader)" in text
    assert "loader.sim.get_unit_position(" not in text
    assert "loader.sim.get_unit_velocity(" not in text
    assert "loader.sim.is_unit_active(" not in text
    assert "class LoaderOwnedRawSimCompatibilityFacade:" in bridge_text
    assert "def get_unit_position(self, entity_id: int) -> Any:" in bridge_text
    assert "def get_unit_velocity(self, entity_id: int) -> Any:" in bridge_text
    assert "def is_unit_active(self, entity_id: int) -> bool:" in bridge_text


def test_wp22_tasking_bridge_quarantines_raw_mission_and_command_chain_sync_helpers() -> None:
    text = TASKING_BRIDGE.read_text(encoding="utf-8")

    assert "class LoaderOwnedRawSimCompatibilityFacade:" in text
    assert "def loader_owned_raw_sim_compat(loader: Any) -> LoaderOwnedRawSimCompatibilityFacade:" in text
    assert "def sync_loader_mission_command(loader: Any, cmd: Any) -> None:" in text
    assert "def sync_loader_command_chain_compat(loader: Any) -> None:" in text
    assert "def sync_task_order(self, agent_id: Any, task_order: Any) -> None:" in text
    assert "def sync_leader_intent(self, agent_id: Any, leader_intent: Any) -> None:" in text
    assert "def sync_pilot_report(self, agent_id: Any, pilot_report: Any) -> None:" in text
    assert "def sync_mission_command(self, agent_id: Any, cmd: Any) -> None:" in text
    assert "loader.sim.set_mission_command(" not in text
    assert "loader.sim.set_task_order(" not in text
    assert "loader.sim.set_leader_intent(" not in text
    assert "loader.sim.set_pilot_report(" not in text


def test_wp22_scripted_opponent_kernel_access_stays_named_and_localized() -> None:
    text = (REPO_ROOT / "gym_envs" / "scenario_loader" / "behavior_runtime" / "scripted_opponents.py").read_text(
        encoding="utf-8"
    )
    bridge_text = TASKING_BRIDGE.read_text(encoding="utf-8")

    assert "loader_owned_scripted_opponent_kernel_compat(loader)" in text
    assert "loader.sim," not in text
    assert "class LoaderOwnedScriptedOpponentKernelCompat:" in bridge_text
    assert "def loader_owned_scripted_opponent_kernel_compat(loader: Any) -> LoaderOwnedScriptedOpponentKernelCompat:" in bridge_text


def test_wp22_loading_world_layout_kernel_apply_stays_named_and_localized() -> None:
    text = (REPO_ROOT / "gym_envs" / "scenario_loader" / "loading.py").read_text(encoding="utf-8")
    bridge_text = TASKING_BRIDGE.read_text(encoding="utf-8")

    assert "apply_loader_owned_world_layout_to_kernel(loader, world_layout)" in text
    assert "apply_world_layout_to_kernel(loader.sim, world_layout)" not in text
    assert "loader.sim," not in text
    assert "def apply_loader_owned_world_layout_to_kernel(loader: Any, layout: Any) -> Any:" in bridge_text
    assert "loader-owned world-layout kernel-apply seam" in bridge_text


def test_wp22_runtime_state_execution_episode_export_drops_empty_raw_loader_guard() -> None:
    text = (REPO_ROOT / "gym_envs" / "scenario_loader" / "runtime_state.py").read_text(encoding="utf-8")

    assert 'hasattr(loader.sim, "__class__")' not in text
    assert 'if not hasattr(__import__("ef_py"), "ExecutionEpisodeState"):' in text
    assert 'raise RuntimeError("ef_py.ExecutionEpisodeState is not available")' in text


def test_world_batch_compat_names_loader_owned_reward_and_info_runtime_helpers() -> None:
    text = (REPO_ROOT / "python" / "rl" / "runtime" / "world_batch" / "compat.py").read_text(encoding="utf-8")

    assert "def resolve_loader_runtime_sim(loader: Any) -> Any:" in text
    assert "def compute_loader_step_outcome(" in text
    assert "def build_loader_step_info(" in text


def test_leader_world_batch_runtime_does_not_call_runtime_facade_compatibility_quarantine() -> None:
    tree = ast.parse(_leader_source())
    violations: list[tuple[int, str]] = []

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "runtime_compatibility_quarantine":
                violations.append((node.lineno, "runtime_compatibility_quarantine()"))
            self.generic_visit(node)

    Visitor().visit(tree)
    assert not violations, f"leader runtime escaped facade adapter layering: {violations}"


def test_runtime_facade_cpp_maintained_paths_do_not_drill_through_raw_runtime_or_world() -> None:
    source = (RUNTIME_FACADE / "runtime_facade.cpp").read_text(encoding="utf-8")

    assert "runtime_->world_compatibility_quarantine(" not in source
    assert "runtime_compatibility_quarantine().world_compatibility_quarantine(" not in source
    assert "runtime()->world_compatibility_quarantine(" not in source
    assert "facade->runtime_compatibility_quarantine().world_compatibility_quarantine(" not in source
    assert "runtime_->apply_world_layout(" in source
    assert "runtime_->world_time_step(" in source
    assert "runtime_->get_visual_candidate_ids_batch(" in source
    assert "collect_visual_binding_compatibility_scenes_from_candidate_ids_batch(" in source
    assert "runtime_->collect_visual_binding_compatibility_scenes_from_candidate_ids_batch(" in source
    assert "runtime_->collect_visual_binding_compatibility_scenes_batch(" not in source


def test_wp22_gpu_visual_binding_routes_through_named_world_batch_compatibility_helper() -> None:
    source = _gpu_bindings_source()

    assert ".world_compatibility_quarantine(" not in source
    assert "RuntimeFacade" in source
    assert "compute_runtime_facade_visual_binding_outputs(" in source
    assert "compute_compat_world_batch_visual_binding_outputs(" in source
    assert "collect_visual_binding_compatibility_scenes_batch(" in source
    assert "render_scenes_batch(" in source


def test_wp22_world_batch_runtime_quarantines_visual_binding_raw_world_access() -> None:
    header = WORLD_BATCH_RUNTIME_H.read_text(encoding="utf-8")
    impl = WORLD_BATCH_RUNTIME_CPP.read_text(encoding="utf-8")
    helper = (
        REPO_ROOT / "src" / "core" / "engine" / "world_batch_visual_binding_compatibility_helper.h"
    ).read_text(encoding="utf-8")

    assert "collect_visual_binding_compatibility_scenes_from_candidate_ids_batch(" in header
    assert "collect_visual_binding_compatibility_scenes_batch(" in header
    assert "Compatibility/diagnostics escape hatch only." in header
    assert "own candidate-id assembly" in header
    assert "WorldBatchRuntime::collect_visual_binding_compatibility_scenes_from_candidate_ids_batch(" in impl
    assert "WorldBatchRuntime::collect_visual_binding_compatibility_scenes_batch(" in impl
    assert "failed to collect visual scene for world batch visual compatibility helper" in impl
    assert "collect_scene_from_candidate_ids(" in helper


def test_wp22_world_batch_runtime_routes_setup_orchestration_through_named_helper() -> None:
    impl = WORLD_BATCH_RUNTIME_CPP.read_text(encoding="utf-8")
    helper = (REPO_ROOT / "src" / "core" / "engine" / "world_batch_setup_helper.h").read_text(encoding="utf-8")

    assert '#include "core/engine/world_batch_setup_helper.h"' in impl
    assert "world_batch_setup::apply_world_setup(" in impl
    assert "world_batch_setup::apply_terrain_assignments(" in impl
    assert "world_batch_setup::apply_wind_assignments(" in impl
    assert "world_batch_setup::append_zones(" in impl
    assert "inline void apply_setup_terrain_assignments(" in helper
    assert "world.set_terrain_type(WorldTerrainAssignment{}.terrain_type);" in helper
    assert "apply_setup_terrain_assignments(world, terrain_assignments, terrain_grouped_indices);" in helper
    apply_terrain_body = helper.split("inline void apply_terrain_assignments(", 1)[1].split(
        "inline void apply_setup_terrain_assignments(",
        1,
    )[0]
    assert "grouped_indices.empty()" not in apply_terrain_body


def test_runtime_facade_escape_hatch_is_documented() -> None:
    header = (REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade.h").read_text(encoding="utf-8")
    readme = (REPO_ROOT / "src" / "runtime" / "facade" / "README.md").read_text(encoding="utf-8")
    assert "Compatibility escape hatch" in header
    assert "Maintained frontends should use facade-level request/result APIs" in header
    assert "必须把访问集中在一个显式 adapter" in readme
    assert "不得直接调用 `RuntimeFacade.runtime_compatibility_quarantine()`" in readme
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


def test_wp24_task_order_maintained_batch_contract_has_runtime_facade_binding_wiring_while_compatibility_shells_are_removed() -> None:
    contracts_text = (RUNTIME_CONTRACTS / "world_batch_contracts.h").read_text(encoding="utf-8")
    facade_header = (RUNTIME_FACADE / "runtime_facade.h").read_text(encoding="utf-8")
    facade_types = (RUNTIME_FACADE / "runtime_facade_types.h").read_text(encoding="utf-8")
    facade_cpp = (RUNTIME_FACADE / "runtime_facade.cpp").read_text(encoding="utf-8")
    bindings_runtime = RUNTIME_BINDINGS.read_text(encoding="utf-8")
    runtime_header = WORLD_BATCH_RUNTIME_H.read_text(encoding="utf-8")

    assert "struct TaskOrderMaintainedBatchContract {" in contracts_text
    assert "struct WorldTaskOrderMaintainedAssignment {" in contracts_text
    assert "struct WorldTaskOrderAssignment" not in contracts_text
    assert "WorldTaskOrderCompatibilityAssignment" not in contracts_text

    assert "void set_task_orders_maintained_batch(" in runtime_header
    assert "std::vector<TaskOrderMaintainedBatchContract> get_task_orders_maintained_batch(" in runtime_header
    assert "void set_mission_commands_maintained_batch(" in runtime_header
    assert "std::vector<MissionCommandMaintainedBatchContract>" in runtime_header
    assert "get_mission_commands_maintained_batch(" in runtime_header
    assert "void set_leader_intents_maintained_batch(" in runtime_header
    assert "std::vector<LeaderIntentMaintainedBatchContract>" in runtime_header
    assert "get_leader_intents_maintained_batch(" in runtime_header
    assert "void set_pilot_reports_maintained_batch(" in runtime_header
    assert "std::vector<PilotReportMaintainedBatchContract>" in runtime_header
    assert "get_pilot_reports_maintained_batch(" in runtime_header
    assert "void set_task_orders_batch(" not in runtime_header
    assert "std::vector<TaskOrder> get_task_orders_batch(" not in runtime_header
    assert "void set_task_orders_compatibility_batch(" not in runtime_header
    assert "std::vector<TaskOrder> get_task_orders_compatibility_batch(" not in runtime_header

    assert "void set_task_orders_maintained_batch(" in facade_header
    assert "std::vector<TaskOrderMaintainedBatchContract> get_task_orders_maintained_batch(" in facade_header
    assert "void set_mission_commands_maintained_batch(" in facade_header
    assert "get_mission_commands_maintained_batch(" in facade_header
    assert "void set_leader_intents_maintained_batch(" in facade_header
    assert "get_leader_intents_maintained_batch(" in facade_header
    assert "void set_pilot_reports_maintained_batch(" in facade_header
    assert "get_pilot_reports_maintained_batch(" in facade_header
    assert "void set_task_orders_batch(" not in facade_header
    assert "std::vector<TaskOrder> get_task_orders_batch(" not in facade_header
    assert "void set_task_orders_compatibility_batch(" not in facade_header
    assert "std::vector<TaskOrder> get_task_orders_compatibility_batch(" not in facade_header
    assert "void set_mission_commands_batch(" not in facade_header
    assert "std::vector<MissionCommand> get_mission_commands_batch(" not in facade_header
    assert "void set_leader_intents_batch(" not in facade_header
    assert "std::vector<LeaderIntent> get_leader_intents_batch(" not in facade_header
    assert "void set_pilot_reports_batch(" not in facade_header
    assert "std::vector<PilotReport> get_pilot_reports_batch(" not in facade_header

    observation_request_section = facade_types.split("struct ObservationBatchRequest", 1)[1].split("struct TaskingBatchRequest", 1)[0]
    tasking_request_section = facade_types.split("struct TaskingBatchRequest", 1)[1].split("struct EngagementBatchRequest", 1)[0]
    execution_request_section = facade_types.split("struct ExecutionBatchStepRequest", 1)[1].split("struct DeviceResidentOutputDescriptor", 1)[0]
    assert "bool include_task_orders = false;" not in observation_request_section
    assert "bool include_task_order_contracts = false;" not in observation_request_section
    assert "bool include_mission_commands = false;" not in observation_request_section
    assert "bool include_leader_intents = false;" not in observation_request_section
    assert "bool include_pilot_reports = false;" not in observation_request_section
    assert "bool include_task_order_contracts = false;" in tasking_request_section
    assert "bool include_task_orders = false;" not in execution_request_section
    assert "bool include_task_order_contracts = false;" not in execution_request_section
    assert "bool include_mission_commands = false;" not in execution_request_section
    assert "bool include_leader_intents = false;" not in execution_request_section
    assert "bool include_pilot_reports = false;" not in execution_request_section

    observation_packet_section = facade_types.split("struct ObservationBatchPacket", 1)[1].split("struct EngagementEventPacket", 1)[0]
    tasking_packet_section = facade_types.split("struct TaskingBatchPacket", 1)[1].split("struct ExecutionBatchStepResult", 1)[0]
    assert "std::vector<TaskOrderMaintainedBatchContract> task_order_contracts;" not in observation_packet_section
    assert "std::vector<MissionCommand> mission_commands;" not in observation_packet_section
    assert "std::vector<LeaderIntent> leader_intents;" not in observation_packet_section
    assert "std::vector<PilotReport> pilot_reports;" not in observation_packet_section
    assert "std::vector<TaskOrder> task_orders;" not in observation_packet_section
    assert "std::vector<TaskOrderMaintainedBatchContract> task_order_contracts;" in tasking_packet_section
    assert "std::vector<MissionCommandMaintainedBatchContract> mission_command_contracts;" in tasking_packet_section
    assert "std::vector<LeaderIntentMaintainedBatchContract> leader_intent_contracts;" in tasking_packet_section
    assert "std::vector<PilotReportMaintainedBatchContract> pilot_report_contracts;" in tasking_packet_section
    assert "std::vector<MissionCommand> mission_commands;" not in tasking_packet_section
    assert "std::vector<LeaderIntent> leader_intents;" not in tasking_packet_section
    assert "std::vector<PilotReport> pilot_reports;" not in tasking_packet_section
    assert '"facade_tasking_packet"' in tasking_packet_section
    assert "kPolicySourceLabelFacadeObservationPacket" not in tasking_packet_section

    observation_request_helper_section = facade_cpp.split("ObservationBatchRequest observation_request_from_step_request", 1)[1].split("TaskingBatchRequest tasking_request_from_step_request", 1)[0]
    assert ".include_task_order_contracts = request.include_task_order_contracts," not in observation_request_helper_section
    assert "TaskingBatchRequest tasking_request_from_step_request" in facade_cpp
    tasking_request_helper_section = facade_cpp.split("TaskingBatchRequest tasking_request_from_step_request", 1)[1].split("std::uint64_t next_snapshot_version", 1)[0]
    assert ".include_task_order_contracts = request.include_task_order_contracts," not in tasking_request_helper_section
    assert ".include_mission_commands = request.include_mission_commands," not in tasking_request_helper_section
    assert ".include_leader_intents = request.include_leader_intents," not in tasking_request_helper_section
    assert ".include_pilot_reports = request.include_pilot_reports," not in tasking_request_helper_section

    export_vector_overload_section = facade_cpp.split("ObservationBatchPacket RuntimeFacade::export_observation_packet(const std::vector<WorldEntityRef>& refs) const", 1)[1].split("ObservationBatchPacket RuntimeFacade::export_observation_packet(const ObservationBatchRequest& request) const", 1)[0]
    assert ".include_task_orders = true," not in export_vector_overload_section
    assert ".include_task_order_contracts = true," not in export_vector_overload_section

    build_observation_packet_section = facade_cpp.split("ObservationBatchPacket RuntimeFacade::build_observation_packet", 1)[1].split("TaskingBatchPacket RuntimeFacade::build_tasking_packet", 1)[0]
    assert "if (request.include_task_order_contracts)" not in build_observation_packet_section
    assert "packet.task_order_contracts = runtime_->get_task_orders_maintained_batch(request.refs);" not in build_observation_packet_section
    assert "packet.mission_commands = runtime_->get_mission_commands_batch(request.refs);" not in build_observation_packet_section
    assert "if (request.include_task_orders)" not in build_observation_packet_section
    assert "runtime_->get_task_orders_batch(" not in build_observation_packet_section
    assert "runtime_->get_task_orders_compatibility_batch(request.refs);" not in build_observation_packet_section
    build_tasking_packet_section = facade_cpp.split("TaskingBatchPacket RuntimeFacade::build_tasking_packet", 1)[1]
    assert "if (request.include_task_order_contracts)" in build_tasking_packet_section
    assert "packet.task_order_contracts = runtime_->get_task_orders_maintained_batch(request.refs);" in build_tasking_packet_section
    assert "packet.mission_command_contracts =" in build_tasking_packet_section
    assert "runtime_->get_mission_commands_maintained_batch(request.refs);" in build_tasking_packet_section
    assert "packet.leader_intent_contracts =" in build_tasking_packet_section
    assert "runtime_->get_leader_intents_maintained_batch(request.refs);" in build_tasking_packet_section
    assert "packet.pilot_report_contracts =" in build_tasking_packet_section
    assert "runtime_->get_pilot_reports_maintained_batch(request.refs);" in build_tasking_packet_section
    assert "packet.mission_commands = runtime_->get_mission_commands_batch(request.refs);" not in build_tasking_packet_section
    assert "packet.leader_intents = runtime_->get_leader_intents_batch(request.refs);" not in build_tasking_packet_section
    assert "packet.pilot_reports = runtime_->get_pilot_reports_batch(request.refs);" not in build_tasking_packet_section

    assert '.def_rw("order", &WorldTaskOrderAssignment::order);' not in bindings_runtime
    assert '"set_task_orders_batch"' not in bindings_runtime
    assert '"get_task_orders_batch"' not in bindings_runtime
    assert '"set_task_orders_compatibility_batch"' not in bindings_runtime
    assert '"get_task_orders_compatibility_batch"' not in bindings_runtime
    facade_binding_section = bindings_runtime.split('nb::class_<RuntimeFacade>(m, "RuntimeFacade")', 1)[1]
    assert '"set_mission_commands_batch"' not in facade_binding_section
    assert '"get_mission_commands_batch"' not in facade_binding_section
    assert '"set_leader_intents_batch"' not in facade_binding_section
    assert '"get_leader_intents_batch"' not in facade_binding_section
    assert '"set_pilot_reports_batch"' not in facade_binding_section
    assert '"get_pilot_reports_batch"' not in facade_binding_section
    assert '"WorldTaskOrderAssignment"' not in bindings_runtime
    assert '"WorldTaskOrderCompatibilityAssignment"' not in bindings_runtime
    observation_request_binding_section = bindings_runtime.split('nb::class_<ObservationBatchRequest>(m, "ObservationBatchRequest")', 1)[1].split('nb::class_<TaskingBatchRequest>(m, "TaskingBatchRequest")', 1)[0]
    tasking_request_binding_section = bindings_runtime.split('nb::class_<TaskingBatchRequest>(m, "TaskingBatchRequest")', 1)[1].split('nb::class_<EngagementBatchRequest>(m, "EngagementBatchRequest")', 1)[0]
    observation_packet_binding_section = bindings_runtime.split('nb::class_<ObservationBatchPacket>(m, "ObservationBatchPacket")', 1)[1].split('nb::class_<TaskingBatchPacket>(m, "TaskingBatchPacket")', 1)[0]
    tasking_packet_binding_section = bindings_runtime.split('nb::class_<TaskingBatchPacket>(m, "TaskingBatchPacket")', 1)[1].split('nb::class_<EngagementEventPacket>(m, "EngagementEventPacket")', 1)[0]
    assert '"include_task_order_contracts"' not in observation_request_binding_section
    assert '"include_task_order_contracts"' in tasking_request_binding_section
    assert '"task_order_contracts"' not in observation_packet_binding_section
    assert '"task_order_contracts"' in tasking_packet_binding_section
    assert '"mission_command_contracts"' in tasking_packet_binding_section
    assert '"leader_intent_contracts"' in tasking_packet_binding_section
    assert '"pilot_report_contracts"' in tasking_packet_binding_section
    assert '"mission_commands"' not in tasking_packet_binding_section
    assert '"leader_intents"' not in tasking_packet_binding_section
    assert '"pilot_reports"' not in tasking_packet_binding_section
    assert '"include_task_orders"' not in bindings_runtime
    assert '"task_orders"' not in bindings_runtime
    assert '"TaskingBatchRequest"' in bindings_runtime
    assert '"TaskingBatchPacket"' in bindings_runtime
    assert '"export_tasking_packet"' in bindings_runtime
    assert 'nb::class_<TaskOrderMaintainedBatchContract>(m, "TaskOrderMaintainedBatchContract")' in bindings_runtime
    assert 'nb::class_<MissionCommandMaintainedBatchContract>(' in bindings_runtime
    assert 'nb::class_<LeaderIntentMaintainedBatchContract>(' in bindings_runtime
    assert 'nb::class_<PilotReportMaintainedBatchContract>(' in bindings_runtime
    assert 'nb::class_<WorldMissionCommandMaintainedAssignment>(' in bindings_runtime
    assert 'nb::class_<WorldTaskOrderMaintainedAssignment>(' in bindings_runtime
    assert 'nb::class_<WorldLeaderIntentMaintainedAssignment>(' in bindings_runtime
    assert 'nb::class_<WorldPilotReportMaintainedAssignment>(' in bindings_runtime
    assert '"set_mission_commands_maintained_batch"' in bindings_runtime
    assert '"get_mission_commands_maintained_batch"' in bindings_runtime
    assert '"set_task_orders_maintained_batch"' in bindings_runtime
    assert '"get_task_orders_maintained_batch"' in bindings_runtime
    assert '"set_leader_intents_maintained_batch"' in bindings_runtime
    assert '"get_leader_intents_maintained_batch"' in bindings_runtime
    assert '"set_pilot_reports_maintained_batch"' in bindings_runtime
    assert '"get_pilot_reports_maintained_batch"' in bindings_runtime


def test_wp24_python_maintained_observation_consumers_do_not_read_compatibility_task_orders() -> None:
    multi_agent_runtime = (
        REPO_ROOT / "python" / "rl" / "runtime" / "multi_agent_runtime.py"
    ).read_text(encoding="utf-8")
    world_batch_vec_env = (
        REPO_ROOT / "python" / "rl" / "runtime" / "world_batch_vec_env.py"
    ).read_text(encoding="utf-8")
    cooperative_vec_env = (
        REPO_ROOT / "python" / "rl" / "runtime" / "cooperative_world_batch_vec_env.py"
    ).read_text(encoding="utf-8")

    export_packet_section = multi_agent_runtime.split("def export_packet(", 1)[1].split("def export_tasking_packet(", 1)[0]
    assert "include_mission_commands" not in export_packet_section
    assert "include_task_order_contracts" not in export_packet_section
    assert "include_task_order_contracts: bool = False" in multi_agent_runtime
    assert "request.include_task_orders = False" not in multi_agent_runtime
    assert "ef_py.TaskingBatchRequest" in multi_agent_runtime
    assert "return self.runtime.export_tasking_packet(request)" in multi_agent_runtime
    assert ".task_orders" not in multi_agent_runtime

    for source in (world_batch_vec_env, cooperative_vec_env):
        assert "include_task_orders=False" not in source
        assert ".task_orders" not in source


def test_wp24_python_command_chain_business_writes_use_maintained_contracts() -> None:
    adapter = (
        REPO_ROOT / "python" / "rl" / "runtime" / "world_batch" / "adapter.py"
    ).read_text(encoding="utf-8")
    command_chain_cache = (
        REPO_ROOT / "python" / "rl" / "runtime" / "world_batch" / "command_chain_cache.py"
    ).read_text(encoding="utf-8")
    world_batch_vec_env = (
        REPO_ROOT / "python" / "rl" / "runtime" / "world_batch_vec_env.py"
    ).read_text(encoding="utf-8")
    cooperative_vec_env = (
        REPO_ROOT / "python" / "rl" / "runtime" / "cooperative_world_batch_vec_env.py"
    ).read_text(encoding="utf-8")
    multi_agent_runtime = (
        REPO_ROOT / "python" / "rl" / "runtime" / "multi_agent_runtime.py"
    ).read_text(encoding="utf-8")

    for source in (adapter, world_batch_vec_env, cooperative_vec_env):
        assert "WorldMissionCommandMaintainedAssignment" in source
        assert "WorldLeaderIntentMaintainedAssignment" in source
        assert "WorldPilotReportMaintainedAssignment" in source
        assert "set_mission_commands_maintained_batch" in source
        assert "set_leader_intents_maintained_batch" in source
        assert "set_pilot_reports_maintained_batch" in source

    for forbidden in (
        "WorldMissionCommandAssignment()",
        "WorldLeaderIntentAssignment()",
        "WorldPilotReportAssignment()",
        "set_mission_commands_batch(",
        "set_leader_intents_batch(",
        "set_pilot_reports_batch(",
        "project_world_leader_intent_assignment_transport",
        "project_world_pilot_report_assignment_transport",
    ):
        assert forbidden not in adapter
        assert forbidden not in world_batch_vec_env
        assert forbidden not in cooperative_vec_env

    for required in (
        "mission_command_maintained_batch_contract",
        "leader_intent_maintained_batch_contract",
        "pilot_report_maintained_batch_contract",
        "project_world_mission_command_maintained_assignment",
        "project_world_leader_intent_maintained_assignment",
        "project_world_pilot_report_maintained_assignment",
    ):
        assert required in command_chain_cache

    assert "get_mission_commands_maintained_batch" in multi_agent_runtime
    assert "get_mission_commands_batch" not in multi_agent_runtime
    assert "mission_commands=[]" not in multi_agent_runtime
    assert 'getattr(tasking_packet, "mission_commands"' not in multi_agent_runtime
