from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WORLD_BATCH_VEC_ENV = REPO_ROOT / "python" / "rl" / "world_batch_vec_env.py"


def _source() -> str:
    return WORLD_BATCH_VEC_ENV.read_text(encoding="utf-8")


def test_world_batch_vec_env_keeps_direct_runtime_fallback_inside_adapter() -> None:
    tree = ast.parse(_source())
    allowed_classes = {"_RuntimeFacadeAdapter"}
    violations: list[tuple[int, str]] = []
    class_stack: list[str] = []

    class Visitor(ast.NodeVisitor):
        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            class_stack.append(node.name)
            self.generic_visit(node)
            class_stack.pop()

        def visit_Attribute(self, node: ast.Attribute) -> None:
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


def test_world_batch_vec_env_does_not_branch_on_facade_presence_in_main_class() -> None:
    source = _source()
    main_class = source.split("class WorldBatchVecEnv", 1)[1]
    assert "_runtime_facade is not None" not in main_class
    assert "_runtime_facade is None" not in main_class


def test_runtime_facade_escape_hatch_is_documented() -> None:
    header = (REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade.h").read_text(encoding="utf-8")
    assert "Compatibility escape hatch" in header
    assert "Maintained frontends should use facade-level request/result APIs" in header
