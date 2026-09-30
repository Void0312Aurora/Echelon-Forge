from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULES = (
    ROOT / "python" / "simulation" / "air" / "observation.py",
    ROOT / "python" / "simulation" / "air" / "director.py",
    ROOT / "python" / "simulation" / "air" / "action.py",
    ROOT / "python" / "simulation" / "air" / "demo.py",
    ROOT / "python" / "simulation" / "air" / "engagement.py",
    ROOT / "python" / "simulation" / "air" / "runtime.py",
    ROOT / "python" / "simulation" / "air" / "ew.py",
    ROOT / "python" / "simulation" / "air" / "coordination.py",
    ROOT / "python" / "simulation" / "air" / "terminal.py",
    ROOT / "python" / "simulation" / "facade_batch.py",
)


def test_scripted_air_observation_projection_has_no_rl_or_gym_imports() -> None:
    forbidden = ("python.rl", "gym_envs", "stable_baselines", "gymnasium")
    for path in MODULES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        assert not any(any(token in name for token in forbidden) for name in imports), path
