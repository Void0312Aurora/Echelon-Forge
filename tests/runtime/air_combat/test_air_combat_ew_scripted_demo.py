from __future__ import annotations

from pathlib import Path

import pytest

from tests.runtime.air_combat.ew_trace_invariants import (
    INITIAL_CHAFF,
    INITIAL_FLARE,
    assert_continuous_warning,
    assert_interval_gated_consumption,
)
from tools.diagnostics.air_combat_ew_scripted_demo import PLAYABLE_BOUNDARY, run_demo


_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCENARIO_PATH = str(_REPO_ROOT / "scenarios" / "air_combat" / "air_combat_1v1_c2_roe_ew_terminal_v1.json")
_SEED = 20260516
_MAX_STEPS = 600
_REPLAY_KEYS = (
    "action_mode",
    "steps",
    "terminated",
    "truncated",
    "termination_reason",
    "fire_once_accepted_steps",
    "release_executed_steps",
    "launch_warning_steps",
    "countermeasure_request_steps",
    "pre_request_countermeasure_state",
    "countermeasure_state_samples",
    "jammer_request_steps",
    "jammer_transmit_steps",
    "scripted_decision_info",
    "scripted_runtime_identity",
    "scripted_runtime_decisions",
    "native_state_sample_last_step",
    "last_info",
)


def _run(**kwargs):
    return run_demo(
        scenario_path=_SCENARIO_PATH,
        seed=_SEED,
        max_steps=_MAX_STEPS,
        response_doctrine="countermeasure_ready",
        **kwargs,
    )


@pytest.fixture(scope="module")
def v1_report() -> dict:
    return _run()


@pytest.fixture(scope="module")
def v2_report() -> dict:
    return _run(jammer_doctrine="self_protect_on_lock")


def _assert_terminal_combat_win(report: dict) -> None:
    # Blue's single C2/ROE shot is accepted and released on step 2 and the
    # native terminal objective closes before the episode budget.
    assert report["terminated"] is True
    assert report["truncated"] is False
    assert report["termination_reason"] == "combat_win"
    assert report["steps"] < _MAX_STEPS
    assert report["fire_once_accepted_steps"] == [2]
    assert report["release_executed_steps"] == [2]
    assert report["last_info"]["mission_status"] == [0.0, 0.0, 0.0, 1.0]
    assert report["last_info"]["reward_terms"]["combat_win_bonus"] == 1500.0


def _assert_native_countermeasure_trace(report: dict) -> int:
    # Red's scripted missile is inbound on every frame from its launch until
    # Blue's kill, so native MAWS warns continuously through the terminal step
    # and the scripted model requests on exactly those frames.
    first_warning = assert_continuous_warning(report["launch_warning_steps"], last_step=report["steps"])
    assert 2 < first_warning < report["steps"]
    assert report["countermeasure_request_steps"] == report["launch_warning_steps"]
    # The inventory is full on the step before the first request, then the
    # native dispenser releases one chaff and one flare per release interval.
    before = report["pre_request_countermeasure_state"]
    assert before["step"] == first_warning - 1
    assert (before["chaff_remaining"], before["flare_remaining"]) == (INITIAL_CHAFF, INITIAL_FLARE)
    samples = report["countermeasure_state_samples"]
    assert [sample["step"] for sample in samples] == list(
        range(first_warning, report["native_state_sample_last_step"] + 1)
    )
    assert_interval_gated_consumption(
        samples,
        first_warning_step=first_warning,
        chaff_requested=True,
        flare_requested=True,
    )
    assert samples[-1]["chaff_remaining"] < INITIAL_CHAFF
    assert samples[-1]["flare_remaining"] < INITIAL_FLARE
    return first_warning


def test_v1_combat_ew_demo_closes_combat_win_with_native_countermeasures(v1_report: dict) -> None:
    assert v1_report["action_mode"] == "air_ew_hybrid_v1"
    _assert_terminal_combat_win(v1_report)
    _assert_native_countermeasure_trace(v1_report)
    assert v1_report["jammer_request_steps"] == []
    assert v1_report["jammer_transmit_steps"] == []
    assert v1_report["scripted_runtime_decisions"] == v1_report["steps"]
    assert v1_report["scripted_runtime_identity"].startswith(
        "air-combat-ew-scripted-demo:air.combat_ew.c2_roe_ew_scripted:seed=20260516"
    )
    assert v1_report["playable_boundary"] == PLAYABLE_BOUNDARY
    assert "not a playable EW claim" in PLAYABLE_BOUNDARY


def test_v2_combat_ew_demo_keys_the_native_jammer_on_the_requested_frames(
    v1_report: dict, v2_report: dict
) -> None:
    assert v2_report["action_mode"] == "air_ew_hybrid_v2"
    _assert_terminal_combat_win(v2_report)
    first_warning = _assert_native_countermeasure_trace(v2_report)
    requests = v2_report["jammer_request_steps"]
    assert requests and requests[0] <= first_warning
    # The native owner reports the pod transmitting on every requested frame
    # it can be sampled on (the terminal step auto-resets).
    sampled = [step for step in requests if step <= v2_report["native_state_sample_last_step"]]
    assert v2_report["jammer_transmit_steps"] == sampled
    # The jammer tail does not change the engagement outcome on this fixture.
    for key in ("steps", "termination_reason", "release_executed_steps", "launch_warning_steps"):
        assert v2_report[key] == v1_report[key]


def test_v2_hold_jammer_doctrine_never_transmits() -> None:
    report = _run(jammer_doctrine="hold")
    assert report["action_mode"] == "air_ew_hybrid_v2"
    _assert_terminal_combat_win(report)
    assert report["jammer_request_steps"] == []
    assert report["jammer_transmit_steps"] == []


def test_combat_ew_demo_replays_the_same_seed_exactly(v2_report: dict) -> None:
    replay = _run(jammer_doctrine="self_protect_on_lock")
    for key in _REPLAY_KEYS:
        assert replay[key] == v2_report[key], key


def test_combat_ew_demo_rejects_half_declared_burst_program() -> None:
    with pytest.raises(ValueError, match="both dispense_burst_s and dispense_bearing_gate_deg"):
        _run(dispense_burst_s=1.0)
