from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE = REPO_ROOT / "python" / "simulation" / "facade_batch.py"


def test_facade_batch_provider_uses_only_compiled_simulation_binding() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "import ef_py" in source
    assert "python.rl" not in source
    assert "gym_envs" not in source
    assert "WorldBatchRuntime" not in source
    assert "RuntimeFacade(" in source
    assert "apply_world_setup(" in source
