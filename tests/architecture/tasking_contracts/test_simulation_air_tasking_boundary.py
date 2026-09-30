from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE = REPO_ROOT / "python" / "simulation" / "air" / "tasking.py"
LEGACY_RL_PROJECTION = REPO_ROOT / "python" / "rl" / "tasking" / "air_c2_task_order_projection.py"


def test_simulation_air_tasking_adapter_is_not_an_rl_or_gym_adapter() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "python.rl" not in source
    assert "gym_envs" not in source
    assert "from python.tasking_contracts.air.tasking.c2_manager import" in source


def test_legacy_rl_air_c2_projection_is_removed_after_simulation_migration() -> None:
    assert not LEGACY_RL_PROJECTION.exists()
