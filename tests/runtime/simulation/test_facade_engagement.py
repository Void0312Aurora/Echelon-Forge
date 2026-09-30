from __future__ import annotations

import ef_py
import pytest

from python.runtime_bootstrap import resolve_repo_path
from python.simulation.facade_batch import FacadeBatchBackend
from python.simulation.air.engagement import AirEngagementFacts, AirScriptedEngagementController


DATABASE = resolve_repo_path("examples", "config", "database")


def _setup(seeds: tuple[int, ...]) -> ef_py.BatchWorldSetupRequest:
    request = ef_py.BatchWorldSetupRequest()
    request.seeds = list(seeds)
    request.time_steps = [0.05]
    spawns = []
    for name, side, x, heading, vx in (
        ("Blue", ef_py.Side.Blue, 0.0, 90.0, 180.0),
        ("Red", ef_py.Side.Red, 8000.0, -90.0, -180.0),
    ):
        spawn = ef_py.WorldSpawnRequest()
        spawn.world_index = 0
        spawn.side = side
        spawn.type_name = "F-16C_Block50"
        spawn.entity_name = name
        spawn.x = x
        spawn.y = 0.0
        spawn.z = 1200.0
        spawn.heading = heading
        spawn.vx = vx
        spawn.ammo_override_enabled = True
        spawn.max_missiles = 4
        spawn.missiles_remaining = 4
        spawn.weapon_cooldown_override_enabled = True
        spawn.weapon_cooldown_s = 0.75
        spawn.weapon_last_fire_time = -1.0
        spawns.append(spawn)
    request.spawn_requests = spawns
    return request


def _setup_generic_target(seeds: tuple[int, ...]) -> ef_py.BatchWorldSetupRequest:
    request = ef_py.BatchWorldSetupRequest()
    request.seeds = list(seeds)
    request.time_steps = [0.05]
    spawns = []
    for name, side, type_name, x, y, heading, vx, vy in (
        ("Blue_Fighter", ef_py.Side.Blue, "F-16C_Block50", 0.0, 0.0, 0.0, 0.0, 230.0),
        ("Red_Generic", ef_py.Side.Red, "Aircraft", 0.0, 12000.0, 180.0, 0.0, -160.0),
    ):
        spawn = ef_py.WorldSpawnRequest()
        spawn.world_index = 0
        spawn.side = side
        spawn.type_name = type_name
        spawn.entity_name = name
        spawn.x = x
        spawn.y = y
        spawn.z = 7000.0
        spawn.heading = heading
        spawn.vx = vx
        spawn.vy = vy
        spawn.ammo_override_enabled = True
        spawn.max_missiles = 4
        spawn.missiles_remaining = 4
        spawn.weapon_cooldown_override_enabled = True
        spawn.weapon_cooldown_s = 0.75
        spawn.weapon_last_fire_time = -1.0
        spawns.append(spawn)
    request.spawn_requests = spawns
    return request


def _launch_request(shooter_id: int, target_id: int, sim_time_s: float) -> ef_py.LaunchRequest:
    request = ef_py.LaunchRequest()
    request.request_id = 1
    request.shooter.world_index = 0
    request.shooter.entity_id = shooter_id
    request.target_entity.world_index = 0
    request.target_entity.entity_id = target_id
    request.has_target_entity = True
    request.target_track_id = target_id
    request.has_target_track = True
    request.station_id = "air:pylon"
    request.authority = "scripted_tactical"
    request.requested_munition_family = "missile"
    request.requested_time_s = float(sim_time_s)
    request.merge_policy = "reject_on_conflict"
    return request


def test_facade_batch_routes_scripted_launch_and_engagement_event_packet() -> None:
    backend = FacadeBatchBackend(
        database_path=DATABASE,
        setup_factory=_setup,
        controlled_spawn_indices=(0, 1),
    )
    try:
        backend.seed(17)
        initial = backend.reset()
        blue_key, red_key = initial.entity_keys
        action = ef_py.PilotAction()
        action.active = True
        action.throttle = 1.0
        current = backend.step({blue_key: action, red_key: action})
        assert list(current.observations[0].contacts)

        events = backend.apply_launch_requests(
            (_launch_request(blue_key[1], red_key[1], float(current.observations[0].sim_time)),),
            diagnostic_only=True,
        )
        assert len(events) == 1
        assert bool(events[0].accepted) is True
        assert bool(events[0].has_spawned_munition) is True
        assert int(backend.snapshot().observations[0].missiles_remaining) == 3

        packet = backend.export_engagement_events(entity_keys=(blue_key,))
        assert list(packet.launch_events)
        assert bool(packet.launch_events[-1].accepted) is True
        with pytest.raises(PermissionError, match="diagnostic-only"):
            backend.apply_launch_requests(
                (_launch_request(red_key[1], blue_key[1], float(current.observations[0].sim_time)),)
            )
    finally:
        backend.close()


def test_scripted_engagement_controller_reaches_native_fire_gate() -> None:
    backend = FacadeBatchBackend(
        database_path=DATABASE,
        setup_factory=_setup,
        controlled_spawn_indices=(0, 1),
    )
    controller = AirScriptedEngagementController(weapon_station_id=1)
    try:
        backend.seed(17)
        initial = backend.reset()
        blue_key, red_key = initial.entity_keys
        hold = ef_py.PilotAction()
        hold.active = True
        hold.throttle = 1.0
        current = backend.step({blue_key: hold, red_key: hold})

        command = ef_py.MissionCommand()
        command.active = True
        command.command_code = 1
        command.cmd_heading_deg = 90.0
        command.cmd_altitude_m = 1200.0
        command.cmd_speed_mps = 180.0
        command.authorization_to_fire = True
        command.assigned_target_id = red_key[1]
        command.assigned_target_track_id = red_key[1]
        command.engagement_authority_holder_id = blue_key[1]
        backend.submit_mission_commands({blue_key: command})

        facts = AirEngagementFacts(
            authorization_to_fire=True,
            target_contact_present=True,
            fire_mask_open=True,
            launch_window_open=True,
            quality_window_ready=True,
            shot_budget_remaining=4.0,
            target_range_m=8000.0,
            assigned_target_id=red_key[1],
            assigned_target_track_id=red_key[1],
            engagement_authority_holder_id=blue_key[1],
        )
        controller.reset(
            observation=current.observations[0],
            instruments=current.instruments[0],
            command=command,
            facts=facts,
        )
        decision = controller.decide(
            observation=current.observations[0],
            instruments=current.instruments[0],
            command=command,
            facts=facts,
        )
        assert bool(decision.pilot_action.fire_weapon) is True
        assert decision.runtime_info["tactical_decision"]["fire_recommended"] is True

        after = backend.step({blue_key: decision.pilot_action, red_key: hold})
        assert int(after.observations[0].missiles_remaining) == 3
        packet = backend.export_engagement_events(entity_keys=(blue_key,))
        assert packet.launch_events[-1].accepted is True
    finally:
        controller.close()
        backend.close()


def test_scripted_pilot_path_resolves_database_munition_and_native_effect() -> None:
    """The maintained scripted action path must reach the database weapon owner."""

    backend = FacadeBatchBackend(
        database_path=DATABASE,
        setup_factory=_setup,
        controlled_spawn_indices=(0, 1),
    )
    controller = AirScriptedEngagementController(weapon_station_id=1)
    try:
        backend.seed(17)
        initial = backend.reset()
        blue_key, red_key = initial.entity_keys
        hold = ef_py.PilotAction()
        hold.active = True
        hold.throttle = 1.0
        current = backend.step({blue_key: hold, red_key: hold})

        command = ef_py.MissionCommand()
        command.active = True
        command.command_code = 1
        command.cmd_heading_deg = 90.0
        command.cmd_altitude_m = 1200.0
        command.cmd_speed_mps = 180.0
        command.authorization_to_fire = True
        command.assigned_target_id = red_key[1]
        command.assigned_target_track_id = red_key[1]
        command.engagement_authority_holder_id = blue_key[1]
        backend.submit_mission_commands({blue_key: command})

        facts = AirEngagementFacts(
            authorization_to_fire=True,
            target_contact_present=True,
            fire_mask_open=True,
            launch_window_open=True,
            quality_window_ready=True,
            shot_budget_remaining=4.0,
            target_range_m=8000.0,
            assigned_target_id=red_key[1],
            assigned_target_track_id=red_key[1],
            engagement_authority_holder_id=blue_key[1],
        )
        controller.reset(
            observation=current.observations[0],
            instruments=current.instruments[0],
            command=command,
            facts=facts,
        )
        decision = controller.decide(
            observation=current.observations[0],
            instruments=current.instruments[0],
            command=command,
            facts=facts,
        )
        assert decision.pilot_action.weapon_select_id == 1

        after = backend.step({blue_key: decision.pilot_action, red_key: hold})
        assert int(after.observations[0].missiles_remaining) == 3
        launch_packet = backend.export_engagement_events(
            entity_keys=(blue_key,),
            include_launch_requests=False,
            include_launch_events=True,
            include_damage_reports=False,
            include_effects_events=False,
        )
        assert launch_packet.launch_events[-1].selected_munition == "AIM-120C-7"

        # The deterministic seed and maintained F-16 geometry produce a native
        # component consequence; the test deliberately does not claim a kill.
        structural_delta = None
        for _ in range(180):
            backend.step({blue_key: hold, red_key: hold})
            packet = backend.export_engagement_events(
                entity_keys=(blue_key,),
                include_launch_requests=False,
                include_launch_events=False,
                include_damage_reports=True,
                include_effects_events=True,
            )
            for report in packet.damage_reports:
                if float(report.system_health_delta) < 0.0:
                    structural_delta = float(report.system_health_delta)
                    break
            if structural_delta is not None:
                break
        assert structural_delta is not None
    finally:
        controller.close()
        backend.close()


def _run_direct_generic_terminal_episode(seed: int) -> tuple[int, object, object]:
    backend = FacadeBatchBackend(
        database_path=DATABASE,
        setup_factory=_setup_generic_target,
        controlled_spawn_indices=(0, 1),
    )
    controller = AirScriptedEngagementController(weapon_station_id=1)
    try:
        backend.seed(seed)
        initial = backend.reset()
        blue_key, red_key = initial.entity_keys
        hold = ef_py.PilotAction()
        hold.active = True
        hold.throttle = 1.0
        current = backend.step({blue_key: hold, red_key: hold})

        command = ef_py.MissionCommand()
        command.active = True
        command.command_code = 2
        command.authorization_to_fire = True
        command.assigned_target_id = red_key[1]
        command.assigned_target_track_id = red_key[1]
        command.engagement_authority_holder_id = blue_key[1]
        backend.submit_mission_commands({blue_key: command})
        facts = AirEngagementFacts(
            authorization_to_fire=True,
            target_contact_present=True,
            fire_mask_open=True,
            launch_window_open=True,
            quality_window_ready=True,
            shot_budget_remaining=1.0,
            target_range_m=12000.0,
            assigned_target_id=red_key[1],
            assigned_target_track_id=red_key[1],
            engagement_authority_holder_id=blue_key[1],
        )
        controller.reset(
            observation=current.observations[0],
            instruments=current.instruments[0],
            command=command,
            facts=facts,
        )
        decision = controller.decide(
            observation=current.observations[0],
            instruments=current.instruments[0],
            command=command,
            facts=facts,
        )
        assert decision.pilot_action.fire_weapon is True
        current = backend.step({blue_key: decision.pilot_action, red_key: hold})
        assert int(current.observations[0].missiles_remaining) == 3

        terminal = None
        for _ in range(600):
            current = backend.step({blue_key: hold, red_key: hold})
            terminal = backend.evaluate_air_combat_terminal(
                own_entity_ids=(blue_key[1],),
                target_entity_ids=(red_key[1],),
                entity_keys=(blue_key, red_key),
            )
            if terminal.status != "running":
                break
        assert terminal is not None
        assert terminal.status == "combat_win"
        assert terminal.reason == "all_targets_destroyed"
        packet = backend.export_engagement_events(
            entity_keys=(blue_key,),
            include_launch_requests=False,
            include_launch_events=True,
            include_damage_reports=True,
            include_effects_events=True,
        )
        assert packet.launch_events[-1].selected_munition == "AIM-120C-7"
        report = packet.damage_reports[-1]
        assert bool(report.destroyed) is True
        return int(report.report_id), packet.effects_events[-1], report
    finally:
        controller.close()
        backend.close()


def test_direct_facade_scripted_surrogate_terminal_replays_deterministically() -> None:
    first = _run_direct_generic_terminal_episode(20260516)
    second = _run_direct_generic_terminal_episode(20260516)
    assert first[1].outcome_state == second[1].outcome_state == "damage_applied"
    assert first[1].miss_distance_m == second[1].miss_distance_m
    assert first[2].hp_delta == second[2].hp_delta == -180.0
    assert first[2].destroyed is True
    assert second[2].destroyed is True


def test_scripted_engagement_controller_blocks_repeat_fire_during_assessment() -> None:
    controller = AirScriptedEngagementController(weapon_station_id=1)
    observation = type(
        "Observation",
        (),
        {"contacts": [], "rwr_warnings": [], "x": 0.0, "y": 0.0, "z": 1200.0},
    )()
    instruments = type(
        "Instrument",
        (),
        {
            "alt_radar": 1200.0,
            "ias": 180.0,
            "heading": 90.0,
            "ground_speed": 180.0,
            "missiles_remaining": 3,
        },
    )()
    command = type(
        "Command",
        (),
        {
            "command_code": 1,
            "cmd_heading_deg": 90.0,
            "cmd_altitude_m": 1200.0,
            "cmd_speed_mps": 180.0,
            "authorization_to_fire": True,
            "assigned_target_id": 9,
            "assigned_target_track_id": 9,
        },
    )()
    facts = AirEngagementFacts(
        authorization_to_fire=True,
        target_contact_present=True,
        fire_mask_open=True,
        launch_window_open=True,
        quality_window_ready=True,
        shot_budget_remaining=3.0,
        pending_assessment=True,
        target_range_m=16000.0,
        assigned_target_id=9,
        assigned_target_track_id=9,
    )
    try:
        controller.reset(
            observation=observation,
            instruments=instruments,
            command=command,
            facts=facts,
        )
        decision = controller.decide(
            observation=observation,
            instruments=instruments,
            command=command,
            facts=facts,
            last_event_info={"release_executed": True},
        )
        assert bool(decision.pilot_action.fire_weapon) is False
        assert decision.runtime_info["post_launch_assessment"]["blocks_fire"] is True
    finally:
        controller.close()


def test_facade_air_terminal_entry_stays_running_without_destroyed_damage() -> None:
    backend = FacadeBatchBackend(
        database_path=DATABASE,
        setup_factory=_setup,
        controlled_spawn_indices=(0, 1),
    )
    try:
        backend.seed(17)
        initial = backend.reset()
        blue_key, red_key = initial.entity_keys
        state = backend.evaluate_air_combat_terminal(
            own_entity_ids=(blue_key[1],),
            target_entity_ids=(red_key[1],),
            entity_keys=(blue_key, red_key),
        )
        assert state.status == "running"
        assert state.reason == "no_terminal_damage_report"
    finally:
        backend.close()
