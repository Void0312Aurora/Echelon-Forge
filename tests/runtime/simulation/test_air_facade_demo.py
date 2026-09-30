from __future__ import annotations

import pytest

from python.runtime_bootstrap import resolve_repo_path
from python.simulation.air.demo import run_facade_scripted_demo


DATABASE = resolve_repo_path("examples", "config", "database")


def test_direct_air_facade_demo_runs_and_replays_deterministically() -> None:
    first = run_facade_scripted_demo(database_path=DATABASE, seed=23, steps=8)
    second = run_facade_scripted_demo(database_path=DATABASE, seed=23, steps=8)

    assert first.steps == 8
    assert first.entity_keys == second.entity_keys
    assert first.initial_sim_time_s == (0.0, 0.0)
    assert first.final_sim_time_s == pytest.approx((0.4, 0.4))
    assert first.final_sim_time_s == second.final_sim_time_s
    assert first.final_positions_m == second.final_positions_m
    assert first.phases == second.phases
    assert all(phase for phases in first.phases for phase in phases)
    assert all(value >= 0.0 for norms in first.action_norms for value in norms)
