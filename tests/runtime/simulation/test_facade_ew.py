from __future__ import annotations

import ef_py
import numpy as np
from types import SimpleNamespace

from python.runtime_bootstrap import resolve_repo_path
from python.simulation.air.ew import AirScriptedEWController
from python.tasking_contracts.air.ew.model import AirScriptedEWIntent
from python.simulation.facade_batch import FacadeBatchBackend


DATABASE = resolve_repo_path("examples", "config", "database")


class _SinglePassEWModel:
    dt = 0.05

    def __init__(self) -> None:
        self.calls = 0
        self.last_intent = None

    def reset(self, *, context) -> None:
        del context
        self.calls = 0
        self.last_intent = None

    def decide(self, *, observation, context, dt):
        del observation, context, dt
        self.calls += 1
        self.last_intent = AirScriptedEWIntent(
            threat_detected=False,
            launch_warning=False,
            track_locked=False,
            strongest_signal=0.0,
            strongest_bearing_deg=0.0,
            countermeasure_plan="hold",
            jammer_mode="unchanged",
            action_owner_status="native_action_owner_required",
            observation_version=f"call-{self.calls}",
        )
        return np.zeros((14,), dtype=np.float32)

    def close(self) -> None:
        pass


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
    request.authority = "scripted_red"
    request.requested_munition_family = "missile"
    request.requested_time_s = float(sim_time_s)
    request.merge_policy = "reject_on_conflict"
    return request


def test_scripted_ew_controller_responds_to_native_launch_warning() -> None:
    backend = FacadeBatchBackend(
        database_path=DATABASE,
        setup_factory=_setup,
        controlled_spawn_indices=(0, 1),
    )
    controller = AirScriptedEWController()
    try:
        backend.seed(17)
        current = backend.reset()
        blue_key, red_key = current.entity_keys
        hold = ef_py.PilotAction()
        hold.active = True
        hold.throttle = 1.0
        current = backend.step({blue_key: hold, red_key: hold})
        launch = backend.apply_launch_requests(
            (_launch_request(red_key[1], blue_key[1], float(current.observations[1].sim_time)),),
            diagnostic_only=True,
        )
        assert launch[0].accepted is True

        warning_seen = False
        for _ in range(80):
            current = backend.step({blue_key: hold, red_key: hold})
            warning_seen = any(bool(row.is_launch) for row in current.observations[0].rwr_warnings)
            if warning_seen:
                break
        assert warning_seen is True

        controller.reset(
            observation=current.observations[0],
            instruments=current.instruments[0],
            doctrine="countermeasure_ready",
        )
        decision = controller.decide(
            observation=current.observations[0],
            instruments=current.instruments[0],
            doctrine="countermeasure_ready",
            observation_version="facade-rwr:launch-warning",
        )
        assert decision.intent.launch_warning is True
        assert decision.intent.countermeasure_plan == "request_chaff_and_flare"
        before_chaff = int(current.instruments[0].countermeasure_chaff_remaining)

        after = current
        for _ in range(12):
            after = backend.step({blue_key: decision.pilot_action, red_key: hold})
            if int(after.instruments[0].countermeasure_chaff_remaining) < before_chaff:
                break
        assert int(after.instruments[0].countermeasure_chaff_remaining) < before_chaff
    finally:
        controller.close()
        backend.close()


def test_scripted_ew_controller_reports_intent_from_same_decision_pass() -> None:
    model = _SinglePassEWModel()
    controller = AirScriptedEWController(model=model)
    observation = SimpleNamespace(contacts=[], rwr_warnings=[])
    instruments = SimpleNamespace()
    controller.reset(observation=observation, instruments=instruments)
    decision = controller.decide(observation=observation, instruments=instruments)
    assert model.calls == 1
    assert decision.intent is model.last_intent
    assert decision.intent.observation_version == "call-1"
    controller.close()
