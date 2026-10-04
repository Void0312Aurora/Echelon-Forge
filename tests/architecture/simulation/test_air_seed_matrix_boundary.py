from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATH = ROOT / "tools" / "diagnostics" / "flight_trajectory" / "air_c2_seed_matrix.py"


def test_air_seed_matrix_is_a_native_scripted_gate() -> None:
    source = SOURCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    forbidden = ("python.rl", "stable_baselines", "gymnasium")
    assert not any(any(token in name for token in forbidden) for name in imports)
    assert "DEFAULT_ACCEPTED_SEEDS = (0, 1, 2)" in source
    assert "_episode_fingerprint" in source
    assert "c2_report_valid" in source
    assert "replay_equal" in source
