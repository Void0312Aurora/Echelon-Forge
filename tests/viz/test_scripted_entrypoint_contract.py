from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
VIZ_SESSION_PATH = REPO_ROOT / "examples" / "viz" / "runtime" / "viz_session.py"
TASK_EVAL_DRIVER_PATH = REPO_ROOT / "tools" / "eval" / "task_eval_driver.py"


def test_viz_scripted_entrypoint_uses_neutral_air_registry() -> None:
    source = VIZ_SESSION_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(VIZ_SESSION_PATH))

    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert "python.tasking_contracts.air_scripted_execution" in imported_modules
    assert "python.tasking_contracts.scripted_landing" in imported_modules
    assert "python.tasking_contracts.scripted_stable_flight" in imported_modules
    assert "python.tasking_contracts.scripted_takeoff" in imported_modules
    assert not any(module.startswith("python.rl.control.scripted_") for module in imported_modules)


def test_viz_combined_scripted_mode_is_registry_backed() -> None:
    source = VIZ_SESSION_PATH.read_text(encoding="utf-8")
    scripted_class = ast.parse(source, filename=str(VIZ_SESSION_PATH))
    class_nodes = [
        node
        for node in scripted_class.body
        if isinstance(node, ast.ClassDef) and node.name == "_ScriptedPolicy"
    ]
    assert len(class_nodes) == 1
    class_source = ast.get_source_segment(source, class_nodes[0]) or ""
    assert "AIR_SCRIPTED_MODEL_REGISTRY.create" in class_source
    assert "AIR_SCRIPTED_EXECUTION_MODEL_ID" in class_source
    assert "self._air_model.step(obs)" in class_source


def test_task_eval_scripted_builders_use_neutral_controllers() -> None:
    source = TASK_EVAL_DRIVER_PATH.read_text(encoding="utf-8")
    assert "python.tasking_contracts.scripted_stable_flight" in source
    assert "python.tasking_contracts.scripted_takeoff" in source
    assert "python.rl.control.scripted_stable_flight" not in source
    assert "python.rl.control.scripted_takeoff" not in source
