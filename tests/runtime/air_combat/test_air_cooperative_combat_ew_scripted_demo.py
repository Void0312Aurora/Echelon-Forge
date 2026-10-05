from __future__ import annotations

from tools.diagnostics.air_cooperative_combat_ew_scripted_demo import (
    PLAYABLE_BOUNDARY,
    run_demo,
)


_SCENARIO_PATH = (
    "scenarios/air_combat/"
    "cooperative_air_2v2_scripted_c2_roe_ew_terminal_v1.json"
)
_MAX_STEPS = 600


def _run() -> dict:
    return run_demo(
        scenario_path=_SCENARIO_PATH,
        seed=20260516,
        max_steps=_MAX_STEPS,
        response_doctrine="countermeasure_ready",
        jammer_doctrine="self_protect_on_lock",
    )


def test_cooperative_combat_ew_terminal_closes_both_slots() -> None:
    result = _run()

    assert result["action_mode"] == "air_ew_hybrid_v2"
    assert result["steps"] < _MAX_STEPS
    assert result["terminated"] == [True, True]
    assert result["truncated"] == [False, False]
    assert result["termination_reasons"] == ["combat_win", "combat_win"]
    assert result["fire_once_accepted_steps"] == [[2], [2]]
    assert result["release_executed_steps"] == [[2], [2]]
    assert [slot["target_owner_name"] for slot in result["roster"]] == [
        "Red_A",
        "Red_B",
    ]
    assert [slot["scripted_opponent_count"] for slot in result["roster"]] == [2, 0]
    assert len(result["scripted_opponent_reports"]) == 2
    assert all(
        report["mode"] == "idle"
        for report in result["scripted_opponent_reports"].values()
    )
    assert all(
        int(report["target_id"]) > 0
        for report in result["scripted_opponent_reports"].values()
    )

    for slot in range(2):
        assert result["launch_warning_steps"][slot]
        assert result["countermeasure_request_steps"][slot] == result[
            "launch_warning_steps"
        ][slot]
        assert result["jammer_request_steps"][slot]
        transmitted = result["jammer_transmit_steps"][slot]
        assert transmitted
        assert set(transmitted).issubset(
            set(result["jammer_request_steps"][slot])
        )
        assert max(transmitted) <= result["native_state_sample_last_step"]
        assert result["pre_request_countermeasure_state"][slot] == {
            "step": result["launch_warning_steps"][slot][0] - 1,
            "chaff_remaining": 60,
            "flare_remaining": 30,
            "last_release_time_s": 0.0,
        }
        samples = result["countermeasure_state_samples"][slot]
        assert samples
        assert samples[0]["chaff_remaining"] < 60
        assert samples[0]["flare_remaining"] < 30
        assert samples[-1]["chaff_remaining"] <= samples[0]["chaff_remaining"]
        assert samples[-1]["flare_remaining"] <= samples[0]["flare_remaining"]

    assert result["playable_boundary"] == PLAYABLE_BOUNDARY


def test_cooperative_combat_ew_terminal_replays_trace() -> None:
    first = _run()
    second = _run()

    for key in (
        "steps",
        "terminated",
        "truncated",
        "termination_reasons",
        "roster",
        "fire_once_accepted_steps",
        "release_executed_steps",
        "launch_warning_steps",
        "countermeasure_request_steps",
        "countermeasure_state_samples",
        "pre_request_countermeasure_state",
        "jammer_request_steps",
        "jammer_transmit_steps",
        "native_state_sample_last_step",
        "scripted_opponent_reports",
        "scripted_runtime_decisions",
    ):
        assert first[key] == second[key]
    assert first["scripted_runtime_identity"] == second["scripted_runtime_identity"]
