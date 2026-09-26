from __future__ import annotations

from tools.diagnostics.air_cooperative_combat_scripted_demo import run_demo


_SCENARIO_PATH = "scenarios/air_combat/cooperative_air_2v1_scripted_c2_roe_engagement_v1.json"


def test_cooperative_combat_scripted_demo_releases_from_both_aircraft_and_terminates() -> None:
    result = run_demo(scenario_path=_SCENARIO_PATH, seed=20260516, max_steps=2400)

    assert result["action_mode"] == "air_combat_hybrid_v1"
    assert result["terminated"] == [True, True]
    assert result["truncated"] == [False, False]
    assert result["termination_reasons"] == ["combat_win", "combat_win"]
    assert all(result["fire_once_accepted_steps"])
    assert all(result["release_executed_steps"])
    assert result["playable_boundary"] == "multi_aircraft_scripted_c2_roe_terminal_demo"


def test_cooperative_combat_scripted_demo_replays_event_trace() -> None:
    first = run_demo(scenario_path=_SCENARIO_PATH, seed=20260516, max_steps=2400)
    second = run_demo(scenario_path=_SCENARIO_PATH, seed=20260516, max_steps=2400)

    for key in (
        "steps",
        "terminated",
        "truncated",
        "termination_reasons",
        "roster",
        "fire_once_accepted_steps",
        "release_executed_steps",
        "scripted_decision_reports",
        "scripted_runtime_decisions",
    ):
        assert first[key] == second[key]
    assert first["scripted_runtime_identity"] == second["scripted_runtime_identity"]
