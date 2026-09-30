from __future__ import annotations

from pathlib import Path

from python.tasking_contracts.air.strategy import assessment, contracts, planning, weapons


REPO_ROOT = Path(__file__).resolve().parents[3]
STRATEGY_ROOT = REPO_ROOT / "python" / "tasking_contracts" / "air" / "strategy"


def test_air_strategy_has_a_physical_algorithm_layer() -> None:
    assert (STRATEGY_ROOT / "__init__.py").is_file()
    assert {path.name for path in STRATEGY_ROOT.glob("*.py")} == {
        "__init__.py",
        "action.py",
        "assessment.py",
        "contracts.py",
        "observation.py",
        "planning.py",
        "weapons.py",
    }


def test_air_strategy_has_no_flat_compatibility_paths() -> None:
    assert not any(STRATEGY_ROOT.parent.parent.glob("air_scripted_*.py"))


def test_air_strategy_modules_do_not_depend_on_rl_or_environment_adapters() -> None:
    for source in STRATEGY_ROOT.glob("*.py"):
        text = source.read_text(encoding="utf-8")
        assert "python.rl" not in text
        assert "gym_envs" not in text
        assert "ef_py" not in text


def test_engagement_orchestrator_delegates_observation_and_action_adapters() -> None:
    source = (
        REPO_ROOT / "python" / "tasking_contracts" / "air" / "engagement" / "model.py"
    ).read_text(encoding="utf-8")
    assert "self.observation_adapter.decode(" in source
    assert "self.action_adapter.apply(" in source
    assert "def _mission_values(" not in source
    assert "def _contact_geometry(" not in source
    assert "self._fire_latched" not in source
