from __future__ import annotations

import pytest

from python.runtime_bootstrap import resolve_repo_path
from python.simulation.air.demo import run_facade_scripted_demo
from python.simulation import create_scenario_backend
from python.simulation.air.scenario_runtime import AirFacadeScenarioRuntime
from python.simulation.air.terminal import AirCombatTerminalState
from python.simulation.air.replay import AirFacadeReplaySession


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


def test_air_scenario_runtime_replays_compiled_path_semantics(tmp_path) -> None:
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
    assert len(first.frames) == len(second.frames) == 3
    assert first.frames == second.frames
    first_receipt = first.replay_receipt()
    second_receipt = second.replay_receipt()
    assert first_receipt.digest == second_receipt.digest
    assert first_receipt.as_dict()["digest"] == first_receipt.digest
    assert "entity_keys" not in first_receipt.as_dict()
    receipt_path = first_receipt.write_json(tmp_path / "air-replay.json")
    assert receipt_path.read_text(encoding="utf-8").endswith("\n")
    loaded = first_receipt.load_json(receipt_path)
    assert loaded.digest == first_receipt.digest
    assert loaded.verify() is True

    replay = AirFacadeReplaySession(loaded)
    assert replay.status == replay.READY
    replay.start()
    assert replay.status == replay.RUNNING
    assert replay.step() == loaded.frames[0]
    replay.pause()
    assert replay.status == replay.PAUSED
    replay.resume()
    assert list(replay.iter_frames()) == list(loaded.frames[1:])
    assert replay.status == replay.COMPLETED
    assert replay.step() is None

    tampered = loaded.as_dict()
    tampered["frames"][0]["positions_m"][0][0] += 1.0
    with pytest.raises(ValueError, match="digest mismatch"):
        loaded.from_dict(tampered)


def test_air_scenario_runtime_stops_bounded_run_at_terminal(monkeypatch) -> None:
    backend = create_scenario_backend(
        backend_id="facade_batch",
        database_path=DATABASE,
        scenario_path=SCENARIO,
    )
    terminal = AirCombatTerminalState(
        status="combat_win",
        reason="test_terminal",
        destroyed_target_ids=(2,),
        destroyed_own_ids=(),
        destroyed_target_keys=((0, 2),),
        destroyed_own_keys=(),
        damage_report_ids=(1,),
    )
    monkeypatch.setattr(backend, "evaluate_air_combat_terminal", lambda **_: terminal)
    runtime = AirFacadeScenarioRuntime(
        backend,
        own_slot_indices=(0,),
        target_slot_indices=(1,),
    )
    try:
        run = runtime.run(seed=23, steps=5)
    finally:
        runtime.close()

    assert run.steps == 1
    assert len(run.frames) == 1
    assert all(len(phases) == 1 for phases in run.phases)
    assert all(len(norms) == 2 for norms in run.action_norms)
    assert run.terminal is terminal
