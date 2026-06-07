from __future__ import annotations

from examples.viz.runtime.viz_session import _is_ground_tasking_profile, _scenario_tasking_profile


def test_ground_tasking_profiles_suppress_cruise_marker_fallback_aliases() -> None:
    for alias in ("ground", "land", "army"):
        assert _is_ground_tasking_profile(alias)

    assert not _is_ground_tasking_profile("air")
    assert not _is_ground_tasking_profile("naval")


def test_scenario_tasking_profile_resolution_prefers_explicit_top_level_profile() -> None:
    scenario_data = {
        "tasking_profile": "ground",
        "mission_command": {"tasking_profile": "air"},
        "task_order": {"tasking_profile": "naval"},
    }

    assert _scenario_tasking_profile(scenario_data) == "ground"


def test_scenario_tasking_profile_resolution_falls_back_to_nested_profiles() -> None:
    assert _scenario_tasking_profile({"mission_command": {"tasking_profile": "land"}}) == "land"
    assert _scenario_tasking_profile({"task_order": {"tasking_profile": "army"}}) == "army"
