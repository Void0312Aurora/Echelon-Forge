from __future__ import annotations

import ef_py

from python.runtime_bootstrap import resolve_repo_path
from python.simulation.air.coordination import AirScriptedRosterCoordinator
from python.simulation.air.engagement import AirEngagementFacts, AirScriptedEngagementController
from python.simulation.facade_batch import FacadeBatchBackend


DATABASE = resolve_repo_path("examples", "config", "database")


def _setup(seeds: tuple[int, ...]) -> ef_py.BatchWorldSetupRequest:
    request = ef_py.BatchWorldSetupRequest()
    request.seeds = list(seeds)
    request.time_steps = [0.05]
    spawns = []
    entries = (
        ("BlueLead", ef_py.Side.Blue, 0.0, 0.0, 90.0, 180.0),
        ("BlueWing", ef_py.Side.Blue, 0.0, -120.0, 90.0, 180.0),
        ("RedLead", ef_py.Side.Red, 8000.0, 0.0, -90.0, -180.0),
        ("RedWing", ef_py.Side.Red, 8120.0, -120.0, -90.0, -180.0),
    )
    for name, side, x, y, heading, vx in entries:
        spawn = ef_py.WorldSpawnRequest()
        spawn.world_index = 0
        spawn.side = side
        spawn.type_name = "F-16C_Block50"
        spawn.entity_name = name
        spawn.x = x
        spawn.y = y
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


def _run(seed: int) -> tuple[tuple[int | None, ...], tuple[int, ...], tuple[bool, ...]]:
    backend = FacadeBatchBackend(
        database_path=DATABASE,
        setup_factory=_setup,
        controlled_spawn_indices=(0, 1, 2, 3),
    )
    controllers: list[AirScriptedEngagementController] = []
    try:
        backend.seed(seed)
        current = backend.reset()
        blue_keys = current.entity_keys[:2]
        red_keys = current.entity_keys[2:]
        hold = ef_py.PilotAction()
        hold.active = True
        hold.throttle = 1.0
        current = backend.step({key: hold for key in current.entity_keys})
        coordinator = AirScriptedRosterCoordinator()
        assignments = coordinator.assign_targets(
            observations={key: current.observations[index] for index, key in enumerate(current.entity_keys)},
            members={blue_keys[0]: "Lead", blue_keys[1]: "Wingman"},
            candidate_target_ids=[key[1] for key in red_keys],
            authorized_member_keys=blue_keys,
        )
        assert all(item.target_id is not None for item in assignments)
        assert len({item.target_id for item in assignments}) == 2

        actions = {key: hold for key in current.entity_keys}
        for assignment in assignments:
            target_id = int(assignment.target_id)
            command = ef_py.MissionCommand()
            command.active = True
            command.command_code = 1
            command.cmd_heading_deg = 90.0
            command.cmd_altitude_m = 1200.0
            command.cmd_speed_mps = 180.0
            command.authorization_to_fire = True
            command.assigned_target_id = target_id
            command.assigned_target_track_id = target_id
            command.engagement_authority_holder_id = assignment.member_key[1]
            backend.submit_mission_commands({assignment.member_key: command})
            controller = AirScriptedEngagementController(weapon_station_id=1)
            controllers.append(controller)
            member_index = current.entity_keys.index(assignment.member_key)
            facts = AirEngagementFacts(
                authorization_to_fire=True,
                target_contact_present=True,
                fire_mask_open=True,
                launch_window_open=True,
                quality_window_ready=True,
                shot_budget_remaining=4.0,
                target_range_m=assignment.target_range_m,
                target_track_age_s=assignment.track_age_s,
                assigned_target_id=target_id,
                assigned_target_track_id=target_id,
                engagement_authority_holder_id=assignment.member_key[1],
            )
            controller.reset(
                observation=current.observations[member_index],
                instruments=current.instruments[member_index],
                command=command,
                facts=facts,
            )
            decision = controller.decide(
                observation=current.observations[member_index],
                instruments=current.instruments[member_index],
                command=command,
                facts=facts,
            )
            actions[assignment.member_key] = decision.pilot_action

        after = backend.step(actions)
        ammo = tuple(int(after.observations[index].missiles_remaining) for index in range(2))
        packet = backend.export_engagement_events(entity_keys=blue_keys)
        accepted = tuple(bool(event.accepted) for event in packet.launch_events)
        return tuple(item.target_id for item in assignments), ammo, accepted
    finally:
        for controller in controllers:
            controller.close()
        backend.close()


def test_air_roster_coordinator_assigns_distinct_targets_and_replays() -> None:
    first = _run(11)
    second = _run(11)

    assert first == second
    assert len(first[0]) == 2
    assert all(ammo == 3 for ammo in first[1])
    assert first[2] == (True, True)


def test_air_roster_coordinator_fails_closed_for_unauthorized_wing() -> None:
    backend = FacadeBatchBackend(
        database_path=DATABASE,
        setup_factory=_setup,
        controlled_spawn_indices=(0, 1, 2, 3),
    )
    coordinator = AirScriptedRosterCoordinator()
    try:
        backend.seed(11)
        current = backend.reset()
        blue_keys = current.entity_keys[:2]
        red_keys = current.entity_keys[2:]
        hold = ef_py.PilotAction()
        hold.active = True
        hold.throttle = 1.0
        current = backend.step({key: hold for key in current.entity_keys})
        assignments = coordinator.assign_targets(
            observations={key: current.observations[index] for index, key in enumerate(current.entity_keys)},
            members={blue_keys[0]: "Lead", blue_keys[1]: "Wingman"},
            candidate_target_ids=[key[1] for key in red_keys],
            authorized_member_keys=(blue_keys[0],),
        )
        assert assignments[0].authorization_to_fire is True
        assert assignments[1].authorization_to_fire is False
        assert assignments[0].authority_holder_id == blue_keys[0][1]
        assert assignments[1].authority_holder_id == 0

        unprivileged = coordinator.assign_targets(
            observations={key: current.observations[index] for index, key in enumerate(current.entity_keys)},
            members={blue_keys[0]: "Lead", blue_keys[1]: "Wingman"},
            candidate_target_ids=[key[1] for key in red_keys],
        )
        assert all(item.authorization_to_fire is False for item in unprivileged)
        assert all(item.authority_holder_id == 0 for item in unprivileged)

        wing_command = ef_py.MissionCommand()
        wing_command.active = True
        wing_command.command_code = 1
        wing_command.assigned_target_id = int(assignments[1].target_id)
        wing_command.authorization_to_fire = False
        wing_command.engagement_authority_holder_id = 0
        backend.submit_mission_commands({blue_keys[1]: wing_command})
        fire = ef_py.PilotAction()
        fire.active = True
        fire.master_arm = True
        fire.fire_weapon = True
        fire.weapon_select_id = 1
        backend.step({blue_keys[0]: hold, blue_keys[1]: fire, red_keys[0]: hold, red_keys[1]: hold})
        packet = backend.export_engagement_events(entity_keys=(blue_keys[1],))
        assert not any(bool(event.accepted) for event in packet.launch_events)
    finally:
        backend.close()
