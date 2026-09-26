from __future__ import annotations

from pathlib import Path

from python.tasking_contracts import air_scripted_assessment as legacy_assessment
from python.tasking_contracts import air_scripted_planning as legacy_planning
from python.tasking_contracts import air_scripted_strategy_contracts as legacy_contracts
from python.tasking_contracts import air_scripted_weapons as legacy_weapons
from python.tasking_contracts.air.strategy import assessment, contracts, planning, weapons


REPO_ROOT = Path(__file__).resolve().parents[3]
STRATEGY_ROOT = REPO_ROOT / "python" / "tasking_contracts" / "air" / "strategy"


def test_air_strategy_has_a_physical_algorithm_layer() -> None:
    assert (STRATEGY_ROOT / "__init__.py").is_file()
    assert {path.name for path in STRATEGY_ROOT.glob("*.py")} == {
        "__init__.py",
        "assessment.py",
        "contracts.py",
        "planning.py",
        "weapons.py",
    }


def test_flat_air_strategy_paths_are_compatibility_shells_only() -> None:
    assert legacy_assessment.AirPostLaunchAssessment is assessment.AirPostLaunchAssessment
    assert legacy_assessment.AirPostLaunchAssessmentReport is assessment.AirPostLaunchAssessmentReport
    assert legacy_planning.AirEngagementPlanner is planning.AirEngagementPlanner
    assert legacy_planning.AirEngagementPlan is planning.AirEngagementPlan
    assert legacy_contracts.AirPlanningContext is contracts.AirPlanningContext
    assert legacy_contracts.AirTacticalDecision is contracts.AirTacticalDecision
    assert legacy_weapons.AirWeaponEnvelope is weapons.AirWeaponEnvelope


def test_air_strategy_modules_do_not_depend_on_rl_or_environment_adapters() -> None:
    for source in STRATEGY_ROOT.glob("*.py"):
        text = source.read_text(encoding="utf-8")
        assert "python.rl" not in text
        assert "gym_envs" not in text
        assert "ef_py" not in text
