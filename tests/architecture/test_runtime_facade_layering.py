from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WORLD_BATCH_VEC_ENV = REPO_ROOT / "python" / "rl" / "world_batch_vec_env.py"
RUNTIME_CONTRACTS = REPO_ROOT / "src" / "runtime" / "contracts"
RUNTIME_FACADE = REPO_ROOT / "src" / "runtime" / "facade"


def _source() -> str:
    return WORLD_BATCH_VEC_ENV.read_text(encoding="utf-8")


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


def test_world_batch_vec_env_keeps_direct_runtime_fallback_inside_adapter() -> None:
    tree = ast.parse(_source())
    allowed_classes = {"_RuntimeFacadeAdapter"}
    violations: list[tuple[int, str]] = []
    class_by_node = _class_stack(tree)

    class Visitor(ast.NodeVisitor):
        def visit_Attribute(self, node: ast.Attribute) -> None:
            class_stack = class_by_node.get(node, [])
            if (
                isinstance(node.value, ast.Name)
                and node.value.id == "ef_py"
                and node.attr == "WorldBatchRuntime"
                and (not class_stack or class_stack[-1] not in allowed_classes)
            ):
                violations.append((node.lineno, "ef_py.WorldBatchRuntime"))
            self.generic_visit(node)

    Visitor().visit(tree)
    assert not violations, f"direct runtime fallback escaped adapter: {violations}"


def test_runtime_facade_runtime_escape_hatch_stays_inside_adapter() -> None:
    tree = ast.parse(_source())
    allowed_classes = {"_RuntimeFacadeAdapter"}
    class_by_node = _class_stack(tree)
    violations: list[tuple[int, str]] = []

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:
            func = node.func
            class_stack = class_by_node.get(node, [])
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "runtime"
                and (not class_stack or class_stack[-1] not in allowed_classes)
            ):
                violations.append((node.lineno, "runtime()"))
            self.generic_visit(node)

    Visitor().visit(tree)
    assert not violations, f"RuntimeFacade.runtime() escaped compatibility adapter: {violations}"


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
