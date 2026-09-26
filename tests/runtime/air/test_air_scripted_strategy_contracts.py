from __future__ import annotations

import pytest

from python.tasking_contracts.air_scripted_planning import AirEngagementPlanner
from python.tasking_contracts.air_scripted_strategy_contracts import (
    AirAssessmentInput,
    AirPlanningContext,
    AirTacticalDecision,
    AirTacticalPlanner,
)


def _context(**overrides: object) -> AirPlanningContext:
    values: dict[str, object] = {
        "target_contact_present": True,
        "authorization_to_fire": True,
        "fire_mask_open": True,
        "launch_window_open": True,
        "quality_window_ready": True,
        "pending_assessment": False,
        "shot_budget_remaining": 1.0,
        "target_range_m": 16000.0,
    }
    values.update(overrides)
    return AirPlanningContext(**values)


def test_planner_projects_rich_plan_to_stable_decision_contract() -> None:
    planner = AirEngagementPlanner()
    decision = planner.decide(context=_context())

    assert isinstance(planner, AirTacticalPlanner)
    assert isinstance(decision, AirTacticalDecision)
    assert decision.fire_recommended is True
    assert decision.diagnostics["selected_candidate"] == "hold"
    assert decision.as_dict()["reason_codes"]


def test_planning_context_rejects_non_finite_or_negative_values() -> None:
    with pytest.raises(ValueError, match="target_range_m must be finite"):
        _context(target_range_m=float("nan"))
    with pytest.raises(ValueError, match="shot_budget_remaining must be non-negative"):
        _context(shot_budget_remaining=-1.0)


def test_decision_contract_bounds_guidance_and_freezes_diagnostics() -> None:
    decision = AirTacticalDecision(
        mode="reposition",
        selected_candidate="intercept",
        fire_recommended=False,
        guidance_roll=0.2,
        diagnostics={"source": "test"},
    )

    with pytest.raises(TypeError):
        decision.diagnostics["source"] = "mutated"  # type: ignore[index]
    with pytest.raises(ValueError, match="guidance_pitch"):
        AirTacticalDecision(
            mode="reposition",
            selected_candidate="intercept",
            fire_recommended=False,
            guidance_pitch=1.1,
        )


def test_assessment_input_is_typed_and_rejects_negative_evidence_counts() -> None:
    inputs = AirAssessmentInput(
        release_executed=True,
        pending_assessment=True,
        target_contact_present=True,
        own_missiles_in_flight_count=1.0,
        dt_s=0.05,
    )
    assert inputs.release_executed is True
    with pytest.raises(ValueError, match="dt_s must be non-negative"):
        AirAssessmentInput(
            release_executed=False,
            pending_assessment=False,
            target_contact_present=False,
            dt_s=-0.1,
        )
