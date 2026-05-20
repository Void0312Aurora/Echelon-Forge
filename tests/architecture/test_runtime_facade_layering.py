from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WORLD_BATCH_VEC_ENV = REPO_ROOT / "python" / "rl" / "runtime" / "world_batch_vec_env.py"
WORLD_BATCH_ADAPTER = REPO_ROOT / "python" / "rl" / "runtime" / "world_batch" / "adapter.py"
LEADER_WORLD_BATCH_RUNTIME = REPO_ROOT / "python" / "rl" / "runtime" / "leader_world_batch_runtime.py"
RUNTIME_CONTRACTS = REPO_ROOT / "src" / "runtime" / "contracts"
RUNTIME_FACADE = REPO_ROOT / "src" / "runtime" / "facade"
CORE_SRC = REPO_ROOT / "src" / "core"


def _source() -> str:
    return WORLD_BATCH_VEC_ENV.read_text(encoding="utf-8")


def _adapter_source() -> str:
    return WORLD_BATCH_ADAPTER.read_text(encoding="utf-8")


def _leader_source() -> str:
    return LEADER_WORLD_BATCH_RUNTIME.read_text(encoding="utf-8")


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
