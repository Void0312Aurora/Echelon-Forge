from __future__ import annotations

from python.tasking_contracts.air.strategy.assessment import (
    AIR_ASSESSMENT_IN_FLIGHT,
    AIR_ASSESSMENT_REATTACK_READY,
    AIR_ASSESSMENT_TERMINAL_OBSERVED,
    AIR_ASSESSMENT_TRACK_LOST,
    AirPostLaunchAssessment,
)


def _assessment(**overrides):
    values = {
        "pending_assessment": False,
        "target_contact_present": True,
        "own_missiles_in_flight_count": 0.0,
        "shot_budget_remaining": 1.0,
        "target_track_age_s": 0.5,
        "event_info": {"release_executed": True},
    }
    values.update(overrides)
    return AirPostLaunchAssessment().observe(**values)


def test_release_stays_in_flight_while_native_assessment_is_pending() -> None:
    report = _assessment(pending_assessment=True, own_missiles_in_flight_count=1.0)

    assert report.state == AIR_ASSESSMENT_IN_FLIGHT
    assert report.outcome == "pending"
    assert report.blocks_fire is True
    assert report.allow_reattack is False


def test_explicit_target_effect_is_the_only_terminal_hit_evidence() -> None:
    report = _assessment(event_info={"release_executed": True, "target_effect_observed": True})

    assert report.state == AIR_ASSESSMENT_TERMINAL_OBSERVED
    assert report.outcome == "hit_evidence"
    assert report.confidence == 1.0
    assert report.allow_reattack is False
    assert report.blocks_fire is True


def test_clear_gate_allows_inconclusive_reattack() -> None:
    report = _assessment()

    assert report.state == AIR_ASSESSMENT_REATTACK_READY
    assert report.outcome == "inconclusive"
    assert report.confidence == 0.0
    assert report.allow_reattack is True
    assert "no_terminal_effect_evidence" in report.reason_codes


def test_contact_loss_is_not_interpreted_as_a_kill() -> None:
    report = _assessment(target_contact_present=False)

    assert report.state == AIR_ASSESSMENT_TRACK_LOST
    assert report.outcome == "inconclusive"
    assert report.allow_reattack is False
    assert "no_terminal_effect_evidence" in report.reason_codes
