from __future__ import annotations

from tools.diagnostics.air_cooperative_ew_scripted_demo import run_demo


_SCENARIO_PATH = "scenarios/air_combat/cooperative_air_2v2_scripted_ew_response_v1.json"


def test_cooperative_ew_demo_reports_two_slot_warning_and_owner_trace() -> None:
    result = run_demo(
        scenario_path=_SCENARIO_PATH,
        seed=20260516,
        max_steps=204,
        response_doctrine="countermeasure_ready",
    )

    assert result["steps"] == 204
    assert result["terminated"] == [False, False]
    assert result["truncated"] == [False, False]
    assert result["termination_reasons"] == ["running", "running"]
    assert result["launch_warning_steps"] == [[162, 202], [202]]
    assert result["countermeasure_request_steps"] == [[162, 202], [202]]
    assert result["roster"] == [
        {
            "entity_name": "Lead",
            "formation_role_id": "ElementLead",
            "scripted_opponent_owner": True,
            "scripted_opponent_count": 2,
        },
        {
            "entity_name": "Wing",
            "formation_role_id": "Wingman",
            "scripted_opponent_owner": False,
            "scripted_opponent_count": 0,
        },
    ]
    assert [sample["chaff_remaining"] for sample in result["countermeasure_state_samples"][0]] == [60, 59]
    assert [sample["flare_remaining"] for sample in result["countermeasure_state_samples"][0]] == [30, 30]
    assert [sample["chaff_remaining"] for sample in result["countermeasure_state_samples"][1]] == [60]
    assert [sample["flare_remaining"] for sample in result["countermeasure_state_samples"][1]] == [30]
    assert all(report["active"] for report in result["scripted_opponent_reports"].values())
    assert all(int(report["target_id"]) > 0 for report in result["scripted_opponent_reports"].values())
    assert result["playable_boundary"] == "ew_response_demo_without_terminal_objective"


def test_cooperative_ew_demo_replays_owner_and_two_slot_trace() -> None:
    first = run_demo(
        scenario_path=_SCENARIO_PATH,
        seed=20260516,
        max_steps=204,
        response_doctrine="countermeasure_ready",
    )
    second = run_demo(
        scenario_path=_SCENARIO_PATH,
        seed=20260516,
        max_steps=204,
        response_doctrine="countermeasure_ready",
    )

    for key in (
        "steps",
        "terminated",
        "truncated",
        "termination_reasons",
        "roster",
        "launch_warning_steps",
        "countermeasure_request_steps",
        "countermeasure_state_samples",
        "scripted_opponent_reports",
        "scripted_runtime_decisions",
    ):
        assert first[key] == second[key]
    assert first["scripted_runtime_identity"] == second["scripted_runtime_identity"]
