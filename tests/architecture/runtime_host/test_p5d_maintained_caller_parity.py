from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
COMPOSITION_TOOL_PATH = ROOT / "tools" / "maintenance" / "runtime_composition_migration_closure.py"
COMPOSITION_FIXTURE = (
    ROOT
    / "tests"
    / "architecture"
    / "composition"
    / "fixtures"
    / "default_runtime_composition_migration_closure.v1.json"
)


def _composition_tool():
    spec = importlib.util.spec_from_file_location(
        "runtime_composition_migration_closure", COMPOSITION_TOOL_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _maintained_python_paths() -> list[Path]:
    roots = (
        ROOT / "python" / "rl" / "runtime",
        ROOT / "python" / "testing" / "contracts",
        ROOT / "python" / "tasking_contracts",
        ROOT / "gym_envs",
        ROOT / "examples" / "viz" / "web_viz",
        ROOT / "tools" / "maintenance",
    )
    for root in roots:
        assert root.is_dir(), f"maintained caller root is missing: {root}"
        assert any(root.rglob("*.py")), f"maintained caller root is empty: {root}"
    paths: list[Path] = []
    for root in roots:
        paths.extend(sorted(root.rglob("*.py")))
    paths = [
        path
        for path in paths
        if "archive" not in path.relative_to(ROOT).parts
        and "__pycache__" not in path.relative_to(ROOT).parts
    ]
    assert paths, "maintained caller inventory unexpectedly has no Python files"
    return paths


def test_p5d_maintained_python_callers_have_no_raw_runtime_constructors() -> None:
    tool = _composition_tool()
    violations: list[tuple[str, str]] = []
    for path in _maintained_python_paths():
        source = path.read_text(encoding="utf-8")
        for symbol in ("SimulationKernel", "WorldBatchRuntime"):
            if tool.python_source_calls_ef_py_symbol(source, symbol):
                violations.append((path.relative_to(ROOT).as_posix(), symbol))
    assert not violations, (
        "P5-D maintained Python callers must not construct raw ef_py runtime owners; "
        f"raw constructors found: {violations}"
    )


def test_p5d_maintained_python_inventory_has_facade_entrypoints() -> None:
    expected = {
        "python/rl/runtime/world_batch/adapter.py": "class RuntimeFacadeAdapter",
        "python/testing/contracts/loader_command_chain.py": "RuntimeFacadeAdapter",
        "python/tasking_contracts/bridge_views.py": "class LoaderOwnedRuntimeView",
        "examples/viz/web_viz/server.py": "create_scenario_backend",
        "tools/maintenance/p5d_process_rollback_drill.py": "RuntimeFacadeAdapter",
    }
    for relative, marker in expected.items():
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert marker in source, f"maintained facade entrypoint disappeared from {relative}"


def test_p5d_native_inventory_and_closure_bind_to_the_same_migration_boundary() -> None:
    tool = _composition_tool()
    assert tool.scan_cpp_default_kernel_callers() == []
    assert "src/main.cpp" in tool.scan_cpp_runtime_facade_callers()

    record = tool.load_json(COMPOSITION_FIXTURE)
    tool.validate_record(record)
    surfaces = {row["surface_id"]: row for row in record["caller_inventory"]}
    assert "simulation_kernel.native_default_callers" not in surfaces
    assert surfaces["runtime_facade.maintained_host"]["callers"]
    assert surfaces["simulation_kernel.native_explicit_callers"]["callers"] == [
        "src/core/engine/world_batch_runtime.cpp"
    ]


def test_p5d_standalone_native_caller_uses_facade_only() -> None:
    source_path = ROOT / "src" / "main.cpp"
    source = source_path.read_text(encoding="utf-8")
    assert '#include "runtime/facade/runtime_facade.h"' in source
    assert "RuntimeFacade facade(" in source
    assert "facade.load_database(" in source
    assert "facade.apply_world_setup(" in source
    assert "facade.step_batch()" in source
    assert "SimulationKernel" not in source
    assert "WorldBatchRuntime" not in source
