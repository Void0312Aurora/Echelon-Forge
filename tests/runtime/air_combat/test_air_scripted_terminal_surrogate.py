from __future__ import annotations

from pathlib import Path

import pytest

from tools.diagnostics.air_combat_scripted_demo import run_demo


_SCENARIO_PATH = str(
    Path(__file__).resolve().parents[3]
    / "scenarios"
    / "air_combat"
    / "1v1"
    / "air_combat_1v1_c2_roe_terminal_generic_aircraft_surrogate_v1.json"
)


def test_scripted_combat_demo_rejects_ungated_full_action_mode() -> None:
    with pytest.raises(ValueError, match="requires action_mode='air_combat_hybrid_v1'"):
        run_demo(
            scenario_path=_SCENARIO_PATH,
            seed=20260516,
            max_steps=1,
            action_mode="full",
            post_launch_assessment=False,
        )


def test_scripted_c2_roe_terminal_surrogate_closes_native_combat_win() -> None:
    result = run_demo(
        scenario_path=_SCENARIO_PATH,
        seed=20260516,
        max_steps=600,
        action_mode="air_combat_hybrid_v1",
        post_launch_assessment=False,
    )

    assert result["terminated"] is True
    assert result["truncated"] is False
    assert result["termination_reason"] == "combat_win"
    assert result["fire_once_accepted_steps"] == [2]
    assert result["release_executed_steps"] == [2]
    assert result["last_info"]["mission_status"] == [0.0, 0.0, 0.0, 1.0]
    assert result["last_info"]["reward_terms"]["combat_win_bonus"] == 1500.0
