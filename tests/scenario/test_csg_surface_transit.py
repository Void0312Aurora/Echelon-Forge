"""S1-A/B full-duration transit on the maintained facade command path."""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import pytest

from python.runtime_bootstrap import resolve_repo_path
from python.scenario.compiler import validate_group_composition
from python.scenario.runtime.csg_replay import capture_csg_replay, iter_csg_spectator_frames


SCENARIOS = ["csg_s1_ford_vs_fujian_named_v1", "csg_s1_ford_mirror_v1"]


@pytest.mark.parametrize("stem", SCENARIOS)
def test_full_duration_surface_screen_holds_through_two_turns_and_stop(stem: str) -> None:
    path = resolve_repo_path("scenarios", "naval", "csg", f"{stem}.json")
    source = json.loads(Path(path).read_text(encoding="utf-8"))
    replay = capture_csg_replay(path, seed=20261008)
    frames = replay["frames"]
    assert len(frames) == source["environment"]["max_steps"] + 1 == 7201
    assert replay["duration_s"] == 3600.0
    assert len(replay["verification"]["transit"]) == 2
    assert all(g["complete"] and g["waypoint_index"] == 3 for g in replay["verification"]["transit"])
    initial = {u["name"]: u for u in frames[0]["units"]}
    for frame in frames:
        assert {u["name"] for u in frame["units"]} == set(initial)
        assert all(math.isfinite(float(u[axis])) for u in frame["units"]
                   for axis in ("x", "y", "z", "heading", "speed"))
    for group in source["groups"]:
        gid = group["group_id"]
        guide_name = f"{gid}__{group['transit']['guide_member_id']}"
        guide_initial = initial[guide_name]
        surface_names = [name for name, unit in initial.items()
                         if name.startswith(f"{gid}__") and unit["type"] == "Ship"]
        for name in surface_names:
            if name == guide_name:
                continue
            dx = initial[name]["x"] - guide_initial["x"]
            dy = initial[name]["y"] - guide_initial["y"]
            errors = []
            for frame in frames:
                units = {u["name"]: u for u in frame["units"]}
                errors.append(math.hypot(units[name]["x"] - units[guide_name]["x"] - dx,
                                         units[name]["y"] - units[guide_name]["y"] - dy))
            # Scenario acceptance bounds, not calibrated operational accuracy:
            # <1.5 km during maneuvering; <250 m after the terminal settling leg.
            assert max(errors) < 1500.0, (name, max(errors))
            assert max(errors[-601:]) < 250.0, (name, max(errors[-601:]))
            final = next(u for u in frames[-1]["units"] if u["name"] == name)
            assert final["speed"] < 0.1, (name, final["speed"])
        guide_final = next(u for u in frames[-1]["units"] if u["name"] == guide_name)
        assert guide_final["speed"] < 0.1
        assert abs(guide_final["y"] - guide_initial["y"]) > 1500.0


def test_transit_route_validation_fails_closed() -> None:
    path = resolve_repo_path("scenarios", "naval", "csg", f"{SCENARIOS[1]}.json")
    source = json.loads(Path(path).read_text(encoding="utf-8"))
    root = Path(resolve_repo_path("."))
    for key, value in (("guide_member_id", "ssn"), ("speed_mps", -1.0),
                       ("arrival_radius_m", 0.0), ("waypoint_offsets_m", []),
                       ("waypoint_offsets_m", [[float("nan"), 0.0]]), ("unknown", 1)):
        bad = copy.deepcopy(source)
        bad["groups"][0]["transit"][key] = value
        with pytest.raises(ValueError):
            validate_group_composition(bad, project_root=root)


def test_transit_replay_matches_live_spectator_with_same_seed() -> None:
    path = resolve_repo_path("scenarios", "naval", "csg", f"{SCENARIOS[1]}.json")
    replay = capture_csg_replay(path, seed=20261008, max_steps=40)
    live = list(iter_csg_spectator_frames(path, seed=20261008, max_steps=40))
    assert live == replay["frames"]
    assert any(u["speed"] > 0.0 for u in live[-1]["units"] if u["type"] == "Ship")
