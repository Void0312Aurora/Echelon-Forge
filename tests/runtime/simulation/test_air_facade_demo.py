from __future__ import annotations

import pytest

from python.runtime_bootstrap import resolve_repo_path
from python.simulation.air.demo import run_facade_scripted_demo
from python.simulation import create_scenario_backend
from python.simulation.air.scenario_runtime import AirFacadeScenarioRuntime


DATABASE = resolve_repo_path("examples", "config", "database")
SCENARIO = resolve_repo_path(
    "scenarios", "air_combat", "air_combat_1v1_headon_sensor_smoke_v1.json"
)


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


def test_air_scenario_runtime_owns_compiled_command_chain_and_terminal_lifecycle() -> None:
    backend = create_scenario_backend(
        backend_id="facade_batch",
        database_path=DATABASE,
        scenario_path=SCENARIO,
    )
    runtime = AirFacadeScenarioRuntime(
        backend,
        own_slot_indices=(0,),
        target_slot_indices=(1,),
    )
    try:
        runtime.reset(23)
        result = runtime.step()
        assert result.step_index == 1
        assert set(result.decisions) == set(result.actions) == set(result.snapshot.entity_keys)
        assert all(result.command_chain[name] for name in (
            "task_orders", "leader_intents", "pilot_reports", "mission_commands"
        ))
        assert result.terminal is not None
        assert result.terminal.status == "running"
        assert result.terminal.reason == "no_terminal_damage_report"
        first_own_key = runtime.own_entity_keys[0]
        runtime.reset(23)
        assert runtime.own_entity_keys[0] != first_own_key
        replay_step = runtime.step()
        assert replay_step.terminal is not None
        assert replay_step.terminal.status == "running"
    finally:
        runtime.close()


def test_air_scenario_runtime_replays_compiled_path_semantics() -> None:
    traces = []
    for _ in range(2):
        backend = create_scenario_backend(
            backend_id="facade_batch",
            database_path=DATABASE,
            scenario_path=SCENARIO,
        )
        runtime = AirFacadeScenarioRuntime(backend)
        try:
            traces.append(runtime.run(seed=31, steps=3))
        finally:
            runtime.close()

    first, second = traces
    assert first.steps == second.steps == 3
    assert first.phases == second.phases
    assert first.final_sim_time_s == second.final_sim_time_s
    assert first.final_positions_m == second.final_positions_m
    assert first.action_norms == second.action_norms
    assert first.replay_identities == second.replay_identities
