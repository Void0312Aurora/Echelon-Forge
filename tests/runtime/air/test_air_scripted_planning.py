from __future__ import annotations

from python.tasking_contracts.air_scripted_planning import AirEngagementPlanner


def _planner(**overrides):
    values = {
        "target_contact_present": True,
        "authorization_to_fire": True,
        "fire_mask_open": True,
        "launch_window_open": True,
        "quality_window_ready": True,
        "pending_assessment": False,
        "shot_budget_remaining": 1.0,
        "target_range_m": 16000.0,
        "target_track_age_s": 0.5,
        "contact_bearing_deg": 0.0,
        "contact_elevation_deg": 0.0,
        "closing_speed_mps": 250.0,
    }
    values.update(overrides)
    return AirEngagementPlanner().plan(**values)


def test_planner_commits_from_a_high_quality_launch_position() -> None:
    plan = _planner()

    assert plan.mode == "commit"
    assert plan.selected_candidate == "hold"
    assert plan.fire_recommended is True
    assert plan.current_utility >= 0.50
    assert "quality_window_ready" in plan.reason_codes


def test_planner_selects_a_reposition_candidate_when_geometry_is_poor() -> None:
    plan = _planner(
        target_range_m=28000.0,
        target_track_age_s=1.0,
        contact_bearing_deg=35.0,
        contact_elevation_deg=12.0,
        closing_speed_mps=80.0,
        quality_window_ready=False,
    )

    assert plan.mode == "reposition"
    assert plan.fire_recommended is False
    assert plan.selected_candidate in {"intercept", "reposition"}
    assert abs(plan.guidance_roll) > 0.0 or abs(plan.guidance_throttle) > 0.0
    assert "utility_below_commit_threshold" in plan.reason_codes


def test_planner_blocks_release_while_assessment_is_pending() -> None:
    plan = _planner(pending_assessment=True)

    assert plan.mode == "assess"
    assert plan.fire_recommended is False
    assert plan.selected_candidate == "hold"
    assert plan.reason_codes == ("pending_assessment",)


def test_planner_is_compatible_with_observations_without_contact_geometry() -> None:
    plan = _planner(target_range_m=0.0, target_track_age_s=0.0, closing_speed_mps=0.0)

    assert plan.fire_recommended is True
    assert "range_geometry_unavailable" in plan.reason_codes
