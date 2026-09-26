from __future__ import annotations

from tools.diagnostics.air_cooperative_ew_scripted_demo import run_demo


_SCENARIO_PATH = "scenarios/air_combat/cooperative_air_2v2_scripted_ew_response_v1.json"
_SCENARIO_4V4_PATH = "scenarios/air_combat/cooperative_air_4v4_scripted_ew_response_v1.json"


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
    assert [sample["flare_remaining"] for sample in result["countermeasure_state_samples"][0]] == [29]
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


def test_cooperative_ew_4v4_routes_all_roster_slots_and_replays() -> None:
    first = run_demo(
        scenario_path=_SCENARIO_4V4_PATH,
        seed=20260516,
        max_steps=204,
        response_doctrine="countermeasure_ready",
    )
    second = run_demo(
        scenario_path=_SCENARIO_4V4_PATH,
        seed=20260516,
        max_steps=204,
        response_doctrine="countermeasure_ready",
    )

    assert first["steps"] == 204
    assert first["terminated"] == [False, False, False, False]
    assert first["truncated"] == [False, False, False, False]
    assert first["termination_reasons"] == ["running"] * 4
    assert first["roster"] == [
        {
            "entity_name": "Blue_A_Lead",
            "formation_role_id": "ElementLead",
            "scripted_opponent_owner": True,
            "scripted_opponent_count": 4,
        },
        {
            "entity_name": "Blue_A_Wing",
            "formation_role_id": "Wingman",
            "scripted_opponent_owner": False,
            "scripted_opponent_count": 0,
        },
        {
            "entity_name": "Blue_B_Lead",
            "formation_role_id": "ElementLead",
            "scripted_opponent_owner": False,
            "scripted_opponent_count": 0,
        },
        {
            "entity_name": "Blue_B_Wing",
            "formation_role_id": "Wingman",
            "scripted_opponent_owner": False,
            "scripted_opponent_count": 0,
        },
    ]
    assert all(first["launch_warning_steps"])
    assert first["countermeasure_request_steps"] == first["launch_warning_steps"]
    assert len(first["scripted_opponent_reports"]) == 4
    assert all(report["active"] for report in first["scripted_opponent_reports"].values())
    assert [sample["chaff_remaining"] for sample in first["countermeasure_state_samples"][0]] == [60, 59, 58, 57, 56]
    assert [sample["chaff_remaining"] for sample in first["countermeasure_state_samples"][1]] == [60, 59, 58, 57, 56]
    assert [sample["chaff_remaining"] for sample in first["countermeasure_state_samples"][2]] == [60, 59]
    assert [sample["chaff_remaining"] for sample in first["countermeasure_state_samples"][3]] == [60]
    assert all(
        sample["flare_remaining"] == 30
        for slot_samples in first["countermeasure_state_samples"]
        for sample in slot_samples
    )
    assert len(first["scripted_runtime_identity"]) == 4
    assert len(set(first["scripted_runtime_identity"])) == 4
    assert first["scripted_runtime_decisions"] == [204, 204, 204, 204]
    assert first["playable_boundary"] == "ew_response_demo_without_terminal_objective"

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
