from __future__ import annotations

from tests.runtime.air_combat.ew_trace_invariants import (
    assert_continuous_warning,
    assert_interval_gated_consumption,
)
from tools.diagnostics.air_cooperative_ew_scripted_demo import run_demo


_SCENARIO_PATH = "scenarios/air_combat/cooperative_air_2v2_scripted_ew_response_v1.json"
_SCENARIO_4V4_PATH = "scenarios/air_combat/cooperative_air_4v4_scripted_ew_response_v1.json"
_MAX_STEPS = 204


def _assert_slot_response(result: dict, slot: int, *, first_warning_step: int) -> None:
    warning_steps = result["launch_warning_steps"][slot]
    first = assert_continuous_warning(warning_steps, last_step=_MAX_STEPS)
    assert first == first_warning_step
    assert result["countermeasure_request_steps"][slot] == warning_steps
    assert_interval_gated_consumption(
        result["countermeasure_state_samples"][slot],
        first_warning_step=first,
        chaff_requested=True,
        flare_requested=True,
    )


def test_cooperative_ew_demo_reports_two_slot_warning_and_owner_trace() -> None:
    result = run_demo(
        scenario_path=_SCENARIO_PATH,
        seed=20260516,
        max_steps=_MAX_STEPS,
        response_doctrine="countermeasure_ready",
    )

    assert result["steps"] == _MAX_STEPS
    assert result["terminated"] == [False, False]
    assert result["truncated"] == [False, False]
    assert result["termination_reasons"] == ["running", "running"]
    # Each slot warns continuously from the first missile inbound on it.
    _assert_slot_response(result, 0, first_warning_step=123)
    _assert_slot_response(result, 1, first_warning_step=163)
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
    assert all(report["active"] for report in result["scripted_opponent_reports"].values())
    assert all(int(report["target_id"]) > 0 for report in result["scripted_opponent_reports"].values())
    assert result["playable_boundary"] == "ew_response_demo_without_terminal_objective"


def test_cooperative_ew_demo_replays_owner_and_two_slot_trace() -> None:
    first = run_demo(
        scenario_path=_SCENARIO_PATH,
        seed=20260516,
        max_steps=_MAX_STEPS,
        response_doctrine="countermeasure_ready",
    )
    second = run_demo(
        scenario_path=_SCENARIO_PATH,
        seed=20260516,
        max_steps=_MAX_STEPS,
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


def test_cooperative_ew_v2_routes_jammer_per_slot_and_replays() -> None:
    first = run_demo(
        scenario_path=_SCENARIO_PATH,
        seed=20260516,
        max_steps=_MAX_STEPS,
        response_doctrine="countermeasure_ready",
        jammer_doctrine="self_protect_on_lock",
    )
    second = run_demo(
        scenario_path=_SCENARIO_PATH,
        seed=20260516,
        max_steps=_MAX_STEPS,
        response_doctrine="countermeasure_ready",
        jammer_doctrine="self_protect_on_lock",
    )

    assert first["action_mode"] == "air_ew_hybrid_v2"
    assert first["jammer_doctrine"] == "self_protect_on_lock"
    assert first["steps"] == _MAX_STEPS
    assert first["terminated"] == [False, False]
    assert all(first["jammer_request_steps"][slot] for slot in range(2))
    assert first["jammer_request_steps"] == first["jammer_transmit_steps"]
    for key in (
        "steps",
        "terminated",
        "truncated",
        "termination_reasons",
        "roster",
        "launch_warning_steps",
        "countermeasure_request_steps",
        "countermeasure_state_samples",
        "jammer_request_steps",
        "jammer_transmit_steps",
        "scripted_opponent_reports",
        "scripted_runtime_decisions",
    ):
        assert first[key] == second[key]
    assert first["scripted_runtime_identity"] == second["scripted_runtime_identity"]


def test_cooperative_ew_4v4_routes_all_roster_slots_and_replays() -> None:
    first = run_demo(
        scenario_path=_SCENARIO_4V4_PATH,
        seed=20260516,
        max_steps=_MAX_STEPS,
        response_doctrine="countermeasure_ready",
    )
    second = run_demo(
        scenario_path=_SCENARIO_4V4_PATH,
        seed=20260516,
        max_steps=_MAX_STEPS,
        response_doctrine="countermeasure_ready",
    )

    assert first["steps"] == _MAX_STEPS
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
    # Element A is engaged from the head-on start; element B's first inbound
    # missiles arrive later. Every slot's launch rows reach its 4-row RWR
    # observation because rows are ordered launch > lock > plain.
    for slot, first_warning_step in enumerate((3, 3, 123, 163)):
        _assert_slot_response(first, slot, first_warning_step=first_warning_step)
    assert len(first["scripted_opponent_reports"]) == 4
    assert all(report["active"] for report in first["scripted_opponent_reports"].values())
    assert len(first["scripted_runtime_identity"]) == 4
    assert len(set(first["scripted_runtime_identity"])) == 4
    assert first["scripted_runtime_decisions"] == [_MAX_STEPS] * 4
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
