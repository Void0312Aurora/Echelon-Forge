from __future__ import annotations

from types import SimpleNamespace

from python.simulation.air.terminal import AirCombatTerminalEvaluator


def _report(*, target_id: int, destroyed: bool, report_id: int, world_index: int = 0) -> SimpleNamespace:
    return SimpleNamespace(
        target=SimpleNamespace(entity_id=target_id, world_index=world_index),
        destroyed=destroyed,
        report_id=report_id,
    )


def test_air_terminal_evaluator_requires_destroyed_damage_report_for_win() -> None:
    evaluator = AirCombatTerminalEvaluator()
    running = evaluator.evaluate(
        SimpleNamespace(damage_reports=[_report(target_id=20, destroyed=False, report_id=1)]),
        own_entity_ids=(10,),
        target_entity_ids=(20,),
    )
    won = evaluator.evaluate(
        SimpleNamespace(damage_reports=[_report(target_id=20, destroyed=True, report_id=2)]),
        own_entity_ids=(10,),
        target_entity_ids=(20,),
    )

    assert running.status == "running"
    assert running.reason == "no_terminal_damage_report"
    assert won.status == "combat_win"
    assert won.reason == "all_targets_destroyed"
    assert won.damage_report_ids == (2,)


def test_air_terminal_evaluator_prefers_own_loss_over_target_win() -> None:
    evaluator = AirCombatTerminalEvaluator()
    state = evaluator.evaluate(
        SimpleNamespace(
            damage_reports=[
                _report(target_id=10, destroyed=True, report_id=3),
                _report(target_id=20, destroyed=True, report_id=4),
            ]
        ),
        own_entity_ids=(10,),
        target_entity_ids=(20,),
    )

    assert state.status == "combat_loss"
    assert state.reason == "own_entity_destroyed"
    assert state.destroyed_own_ids == (10,)
    assert state.destroyed_target_ids == (20,)


def test_air_terminal_evaluator_keeps_world_identity_when_entity_ids_repeat() -> None:
    evaluator = AirCombatTerminalEvaluator()
    state = evaluator.evaluate(
        SimpleNamespace(damage_reports=[_report(target_id=20, destroyed=True, report_id=5, world_index=1)]),
        own_entity_ids=((0, 10),),
        target_entity_ids=((1, 20),),
    )
    assert state.status == "combat_win"
    assert state.destroyed_target_keys == ((1, 20),)
