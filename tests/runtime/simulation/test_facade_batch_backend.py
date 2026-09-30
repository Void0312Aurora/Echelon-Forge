from __future__ import annotations

from types import SimpleNamespace

import ef_py
import numpy as np
import pytest

from python.runtime_bootstrap import resolve_repo_path
from python.simulation import create_single_backend
from python.simulation.air.tasking import make_scripted_c2_task_manager
from python.simulation.air.director import AirDirectorInput, AirScriptedDirector
from python.tasking_contracts.air.execution import AirScriptedExecutionModel


DATABASE = resolve_repo_path("examples", "config", "database")


def _setup(seeds: tuple[int, ...]) -> ef_py.BatchWorldSetupRequest:
    request = ef_py.BatchWorldSetupRequest()
    request.seeds = list(seeds)
    request.time_steps = [0.05]
    spawns = []
    for name, y_m in (("Lead", 0.0), ("Wing", -120.0)):
        spawn = ef_py.WorldSpawnRequest()
        spawn.world_index = 0
        spawn.side = ef_py.Side.Blue
        spawn.type_name = "F-16C_Block50"
        spawn.entity_name = name
        spawn.x = 0.0
        spawn.y = y_m
        spawn.z = 1200.0
        spawn.heading = 90.0
        spawn.vx = 180.0
        spawns.append(spawn)
    request.spawn_requests = spawns
    return request


def _action(throttle: float) -> ef_py.PilotAction:
    action = ef_py.PilotAction()
    action.active = True
    action.throttle = throttle
    return action


def test_facade_batch_runs_two_agents_and_roundtrips_scripted_c2_order() -> None:
    backend = create_single_backend(
        backend_id="facade_batch",
        database_path=DATABASE,
        setup_factory=_setup,
    )
    try:
        backend.seed(17)
        initial = backend.reset()
        assert len(initial.entity_keys) == 2
        lead_key, wing_key = initial.entity_keys
        assert lead_key[0] == wing_key[0] == 0
        assert lead_key[1] != wing_key[1]
        assert all(float(obs.sim_time) == 0.0 for obs in initial.observations)

        loader = SimpleNamespace(
            agent_id=lead_key[1],
            scenario_data={},
            mission_cmd={"target_altitude": 1200.0, "target_speed": 180.0},
            waypoints=[],
            waypoint_idx=0,
        )
        manager = make_scripted_c2_task_manager()
        manager.reset(loader)
        backend.submit_task_orders({lead_key: loader.task_order})
        chain = backend.read_command_chain()
        assert int(chain["task_orders"][0].shared_core.assignee_id) == lead_key[1]
        assert ef_py.task_order_maintained_air_tasking_identity(chain["task_orders"][0]).task_type == ef_py.TaskType.Scramble

        observations = backend.air_scripted_observations()
        assert len(observations) == 2
        assert observations[0]["instruments"].shape == (42,)
        assert observations[0]["contacts"].shape == (8, 5)
        assert observations[0]["rwr"].shape == (8, 4)
        assert observations[0]["mission"].shape[0] >= 4
        scripted_model = AirScriptedExecutionModel(action_dim=17)
        scripted_action = scripted_model.step(observations[0], phase_name="transit_to_station")
        assert scripted_action.shape == (17,)
        assert np.isfinite(scripted_action).all()

        native = initial
        direct_input = AirDirectorInput(
            entity_id=lead_key[1],
            sim_time_s=0.0,
            observation=native.observations[0],
            instruments=native.instruments[0],
            mission_command=SimpleNamespace(
                command_code=1,
                cmd_heading_deg=90.0,
                cmd_altitude_m=1200.0,
                cmd_speed_mps=180.0,
            ),
            waypoint_count=3,
            remaining_waypoints=3,
            ils=(1.0, 0.0, 0.0, 9000.0),
            task_name="TASK_SCRAMBLE",
        )
        decision = AirScriptedDirector().decide(direct_input)
        backend.submit_air_director_decisions({lead_key: decision})
        direct_chain = backend.read_command_chain()
        assert direct_chain["task_orders"][0].shared_core.assignee_id == lead_key[1]
        assert direct_chain["leader_intents"][0].shared_core.command_code == decision.leader_intent.command_code
        assert direct_chain["pilot_reports"][0].shared_core.sender_id == lead_key[1]
        assert direct_chain["mission_commands"][0].shared_core.command_code == decision.mission_command.command_code

        current = backend.step({lead_key: _action(1.0), wing_key: _action(0.25)})
        assert len(current.observations) == 2
        assert all(float(obs.sim_time) > 0.0 for obs in current.observations)
        assert float(current.instruments[0].throttle_pos) > float(current.instruments[1].throttle_pos)
        with pytest.raises(KeyError, match="uncontrolled"):
            backend.step({(0, 999999): _action(1.0)})

        replay = backend.reset()
        assert len(replay.entity_keys) == 2
        assert all(float(obs.sim_time) == 0.0 for obs in replay.observations)
    finally:
        backend.close()


def test_facade_batch_requires_reset_and_rejects_invalid_roster() -> None:
    backend = create_single_backend(
        backend_id="facade_batch",
        database_path=DATABASE,
        setup_factory=_setup,
        controlled_spawn_indices=(2,),
    )
    try:
        with pytest.raises(RuntimeError, match="reset"):
            backend.step({})
        with pytest.raises(ValueError, match="controlled spawn indices"):
            backend.reset()
    finally:
        backend.close()
