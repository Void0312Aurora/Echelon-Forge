from __future__ import annotations

import ef_py

from python.runtime_bootstrap import resolve_repo_path
from python.simulation.air.engagement import AirEngagementFacts, AirScriptedEngagementController
from python.simulation.air.runtime import AirEngagementRuntimeInput, AirScriptedEngagementRuntimeModel
from python.simulation.facade_batch import FacadeBatchBackend
from python.tasking_contracts.common.decision_runtime import (
    DECISION_RUNTIME_ACTION_DECIDED,
    DECISION_RUNTIME_ACTION_HELD,
    DecisionRuntimeAgent,
    DecisionRuntimeAgentSpec,
)


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


def test_air_scripted_controller_uses_common_runtime_hold_and_replay_identity() -> None:
    backend = FacadeBatchBackend(
        database_path=DATABASE,
        setup_factory=_setup,
        controlled_spawn_indices=(0, 1),
    )
    runtime = DecisionRuntimeAgent(
        DecisionRuntimeAgentSpec(
            agent_id="blue-1",
            model_id="air.engagement.facade_scripted",
            domain="air",
            role_id="air_tactical_engagement_controller",
            model_kind="scripted",
            decision_period_s=1.0,
            authority_scope="air:engagement",
        ),
            AirScriptedEngagementRuntimeModel(
                controller=AirScriptedEngagementController(weapon_station_id=1)
            ),
    )
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
        packet = AirEngagementRuntimeInput(
            native_observation=current.observations[0],
            instruments=current.instruments[0],
            command=command,
            facts=facts,
        )
        runtime.reset(context={"observation": packet}, episode_seed=17)
        first = runtime.step(observation=packet, clock_s=0.0, observation_version="air:v2")
        held = runtime.step(observation=packet, clock_s=0.1, observation_version="air:v2")

        assert first.report.action_source == DECISION_RUNTIME_ACTION_DECIDED
        assert held.report.action_source == DECISION_RUNTIME_ACTION_HELD
        assert first.action.pilot_action.fire_weapon is True
        assert runtime.replay_identity == "blue-1:air.engagement.facade_scripted:seed=17:reset=1"
    finally:
        runtime.close()
        backend.close()
