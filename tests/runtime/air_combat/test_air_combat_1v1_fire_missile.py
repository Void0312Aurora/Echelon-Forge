from __future__ import annotations

import importlib.util
import unittest
import numpy as np

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402
from gym_envs.scenario_loader import ScenarioLoader  # noqa: E402
from gym_envs.universal_env import UniversalEnv  # noqa: E402
from python.scenario_compiler import ScenarioCompiler  # noqa: E402
from python.scenario_runtime import load_compiled_scenario_batch  # noqa: E402


_SCENARIO_PATH = resolve_repo_path(
    "scenarios",
    "air_combat",
    "air_combat_1v1_headon_sensor_smoke_v1.json",
)
_DB_PATH = resolve_repo_path("examples", "config", "database")
_HAS_GYMNASIUM = importlib.util.find_spec("gymnasium") is not None


def _load_fixture(seed: int = 20260516) -> tuple[ef_py.SimulationKernel, ScenarioLoader, int, int]:
    sim = ef_py.SimulationKernel()
    if not sim.load_database(_DB_PATH):
        raise AssertionError("failed to load runtime database")
    loader = ScenarioLoader(sim)
    blue_id = int(loader.load_scenario(_SCENARIO_PATH, seed=seed))
    red_id = int(loader.entities["Red_Fighter"])
    return sim, loader, blue_id, red_id


def _make_direct_fixture() -> tuple[ef_py.SimulationKernel, int, int]:
    sim = ef_py.SimulationKernel()
    if not sim.load_database(_DB_PATH):
        raise AssertionError("failed to load runtime database")
    sim.set_time_step(0.05)
    sim.set_terrain_type("flat")
    sim.set_wind(0.0, 0.0, 0.0)

    blue_id = int(sim.spawn_unit(
        ef_py.Side.Blue,
        "F-16C_Block50",
        0.0,
        0.0,
        1200.0,
        0.0,
        0.0,
        0.0,
        0.0,
        180.0,
        0.0,
    ))
    red_id = int(sim.spawn_unit(
        ef_py.Side.Red,
        "F-16C_Block50",
        0.0,
        8000.0,
        1200.0,
        180.0,
        0.0,
        0.0,
        0.0,
        -180.0,
        0.0,
    ))
    sim.set_unit_ammo(blue_id, 4, 4)
    sim.set_unit_ammo(red_id, 4, 4)
    sim.set_weapon_cooldown(blue_id, 0.75, -1.0)
    sim.set_weapon_cooldown(red_id, 0.75, -1.0)
    return sim, blue_id, red_id


def _wait_for_track(sim: ef_py.SimulationKernel, shooter_id: int, target_id: int, *, max_steps: int = 80) -> None:
    for _ in range(max_steps):
        sim.step()
        obs = sim.get_agent_observation(shooter_id)
        if any(int(getattr(track, "id", 0)) == target_id for track in getattr(obs, "contacts", [])):
            return
    raise AssertionError(f"expected shooter {shooter_id} to acquire target track {target_id}")


def _missile_ids(sim: ef_py.SimulationKernel) -> set[int]:
    return {
        int(unit.id)
        for unit in sim.get_all_units()
        if int(unit.type) == int(ef_py.UnitType.Missile)
    }


class AirCombat1v1FireMissileTests(unittest.TestCase):
    def test_scenario_level_ammo_override_applies_in_loader_and_batch_paths(self) -> None:
        scenario = {
            "scenario_name": "air_combat_1v1_ammo_override_inline",
            "environment": {
                "time_step": 0.05,
                "terrain_type": "flat",
                "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
            },
            "mission_command": {
                "command_code": 0,
                "target_heading": 0.0,
                "target_altitude": 1200.0,
                "target_speed": 180.0,
            },
            "entities": [
                {
                    "name": "Blue_Fighter",
                    "type": "F-16C_Block50",
                    "side": "Blue",
                    "pos": [0.0, 0.0, 1200.0],
                    "vel": [0.0, 180.0, 0.0],
                    "heading": 0.0,
                    "is_agent": True,
                    "ammo": {
                        "missiles_remaining": 2,
                        "max_missiles": 6,
                    },
                    "weapon_cooldown": {
                        "cooldown_s": 0.75,
                        "last_fire_time": -1.0,
                    },
                },
                {
                    "name": "Red_Fighter",
                    "type": "Aircraft",
                    "side": "Red",
                    "pos": [0.0, 8000.0, 1200.0],
                    "vel": [0.0, -180.0, 0.0],
                    "heading": 180.0,
                    "ammo": {
                        "missiles_remaining": 1,
                        "max_missiles": 1,
                    },
                },
            ],
        }

        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(_DB_PATH))
        loader = ScenarioLoader(sim)
        blue_id = int(loader.load_scenario_data(scenario, seed=20260516))
        red_id = int(loader.entities["Red_Fighter"])

        blue_obs = sim.get_agent_observation(blue_id)
        red_obs = sim.get_agent_observation(red_id)
        self.assertEqual(int(getattr(blue_obs, "missiles_remaining", -1)), 2)
        self.assertEqual(int(getattr(red_obs, "missiles_remaining", -1)), 1)

        compiled = ScenarioCompiler.compile_data(scenario)
        batch = ef_py.WorldBatchRuntime(1)
        self.assertTrue(batch.load_database(_DB_PATH))
        worlds = load_compiled_scenario_batch(batch, compiled, seeds=[20260516])
        self.assertEqual(len(worlds), 1)

        batch_blue = int(worlds[0].entities["Blue_Fighter"])
        batch_red = int(worlds[0].entities["Red_Fighter"])
        batch_blue_obs = batch.world(0).get_agent_observation(batch_blue)
        batch_red_obs = batch.world(0).get_agent_observation(batch_red)
        self.assertEqual(int(getattr(batch_blue_obs, "missiles_remaining", -1)), 2)
        self.assertEqual(int(getattr(batch_red_obs, "missiles_remaining", -1)), 1)

    def test_fire_missile_requires_active_track(self) -> None:
        sim, blue_id, red_id = _make_direct_fixture()

        missile_id = int(sim.fire_missile(blue_id, red_id))

        self.assertEqual(missile_id, 0)
        obs = sim.get_agent_observation(blue_id)
        self.assertEqual(int(getattr(obs, "missiles_remaining", -1)), 4)
        self.assertTrue(bool(getattr(obs, "can_fire", False)))

    def test_fire_missile_consumes_ammo_and_enforces_cooldown(self) -> None:
        sim, blue_id, red_id = _make_direct_fixture()
        _wait_for_track(sim, blue_id, red_id)

        obs = sim.get_agent_observation(blue_id)
        self.assertIsNotNone(obs)
        self.assertGreater(int(getattr(obs, "missiles_remaining", -1)), 0)
        self.assertTrue(bool(getattr(obs, "can_fire", False)))

        first_missile_id = int(sim.fire_missile(blue_id, red_id))
        self.assertGreater(first_missile_id, 0)

        post_fire = sim.get_agent_observation(blue_id)
        self.assertEqual(int(getattr(post_fire, "missiles_remaining", -1)), 3)
        self.assertFalse(bool(getattr(post_fire, "can_fire", True)))

        blocked_second = int(sim.fire_missile(blue_id, red_id))
        self.assertEqual(blocked_second, 0)

        for _ in range(60):
            sim.step()

        cooled = sim.get_agent_observation(blue_id)
        self.assertEqual(int(getattr(cooled, "missiles_remaining", -1)), 3)
        self.assertTrue(bool(getattr(cooled, "can_fire", False)))

    def test_fired_missile_does_not_retarget_friendly_and_kills_red(self) -> None:
        sim, blue_id, red_id = _make_direct_fixture()
        _wait_for_track(sim, blue_id, red_id)
        self.assertEqual(sim.get_unit_health(blue_id), [100.0, 100.0])
        self.assertEqual(sim.get_unit_health(red_id), [100.0, 100.0])

        missile_id = int(sim.fire_missile(blue_id, red_id))
        self.assertGreater(missile_id, 0)

        saw_red_in_missile_contacts = False
        for _ in range(260):
            sim.step()
            if sim.is_unit_active(missile_id):
                detections = sim.get_detections(missile_id)
                detection_ids = {int(det.target_id) for det in detections}
                if red_id in detection_ids:
                    saw_red_in_missile_contacts = True
                self.assertNotIn(blue_id, detection_ids)
            if not sim.is_unit_active(red_id):
                break

        self.assertTrue(saw_red_in_missile_contacts)
        self.assertTrue(sim.is_unit_active(blue_id))
        self.assertEqual(sim.get_unit_health(blue_id), [100.0, 100.0])
        self.assertFalse(sim.is_unit_active(red_id))
        self.assertEqual(sim.get_unit_health(red_id), [0.0, 0.0])

    def test_fire_weapon_bridge_uses_assigned_target_and_spawns_missile(self) -> None:
        sim, blue_id, red_id = _make_direct_fixture()
        _wait_for_track(sim, blue_id, red_id)

        pilot = ef_py.PilotAction()
        pilot.active = True
        pilot.weapon_select_id = 1
        sim.set_pilot_action(blue_id, pilot)

        missile_ids_before = _missile_ids(sim)
        pilot = ef_py.PilotAction()
        pilot.active = True
        pilot.master_arm = True
        pilot.fire_weapon = True
        pilot.weapon_select_id = 1
        sim.set_pilot_action(blue_id, pilot)
        sim.step()

        new_missile_ids = _missile_ids(sim) - missile_ids_before
        self.assertEqual(len(new_missile_ids), 1)
        missile_runtime = sim.debug_get_missile_runtime_state(next(iter(new_missile_ids)))
        self.assertAlmostEqual(float(missile_runtime["mass_total_kg"]), 152.0, delta=1.0e-6)
        self.assertAlmostEqual(float(missile_runtime["max_speed_mps"]), 1372.0, delta=1.0e-6)
        self.assertEqual(int(missile_runtime["sensor_type"]), int(ef_py.SensorType.Radar))

        post_fire = sim.get_agent_observation(blue_id)
        self.assertEqual(int(getattr(post_fire, "missiles_remaining", -1)), 3)
        self.assertFalse(bool(getattr(post_fire, "can_fire", True)))

    def test_fire_weapon_bridge_prefers_assigned_target_over_nearer_contact(self) -> None:
        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(_DB_PATH))
        sim.set_time_step(0.05)
        sim.set_terrain_type("flat")
        sim.set_wind(0.0, 0.0, 0.0)

        blue_id = int(sim.spawn_unit(
            ef_py.Side.Blue,
            "F-16C_Block50",
            0.0,
            0.0,
            1200.0,
            0.0,
            0.0,
            0.0,
            0.0,
            180.0,
            0.0,
        ))
        near_red_id = int(sim.spawn_unit(
            ef_py.Side.Red,
            "F-16C_Block50",
            0.0,
            7000.0,
            1200.0,
            180.0,
            0.0,
            0.0,
            0.0,
            -180.0,
            0.0,
        ))
        assigned_red_id = int(sim.spawn_unit(
            ef_py.Side.Red,
            "F-16C_Block50",
            1500.0,
            8000.0,
            1200.0,
            180.0,
            0.0,
            0.0,
            0.0,
            -180.0,
            0.0,
        ))
        sim.set_unit_ammo(blue_id, 4, 4)
        sim.set_weapon_cooldown(blue_id, 0.75, -1.0)

        _wait_for_track(sim, blue_id, near_red_id)
        _wait_for_track(sim, blue_id, assigned_red_id)

        obs = sim.get_agent_observation(blue_id)
        tracks = {int(getattr(track, "id", 0)): track for track in getattr(obs, "contacts", [])}
        self.assertIn(near_red_id, tracks)
        self.assertIn(assigned_red_id, tracks)
        self.assertLess(float(getattr(tracks[near_red_id], "range", 0.0)), float(getattr(tracks[assigned_red_id], "range", 0.0)))

        mission = ef_py.MissionCommand()
        mission.active = True
        mission.assigned_target_id = assigned_red_id
        mission.authorization_to_fire = True
        sim.set_mission_command(blue_id, mission)

        missile_ids_before = _missile_ids(sim)
        pilot = ef_py.PilotAction()
        pilot.active = True
        pilot.master_arm = True
        pilot.fire_weapon = True
        sim.set_pilot_action(blue_id, pilot)
        sim.step()

        new_missile_ids = _missile_ids(sim) - missile_ids_before
        self.assertEqual(len(new_missile_ids), 1)
        missile_runtime = sim.debug_get_missile_runtime_state(next(iter(new_missile_ids)))
        self.assertAlmostEqual(
            float(missile_runtime["filtered_range_m"]),
            float(getattr(tracks[assigned_red_id], "range", 0.0)),
            delta=100.0,
        )
        self.assertGreater(
            abs(float(missile_runtime["filtered_range_m"]) - float(getattr(tracks[near_red_id], "range", 0.0))),
            500.0,
        )

    @unittest.skipUnless(_HAS_GYMNASIUM, "UniversalEnv requires optional gymnasium dependency")
    def test_universal_env_full_action_surface_can_trigger_weapon_release(self) -> None:
        env = UniversalEnv(
            _SCENARIO_PATH,
            include_visual=False,
            include_proprio=False,
            action_mode="full",
            mission_obs_mode="basic",
        )
        try:
            _obs, _info = env.reset(seed=20260516)

            action = np.zeros((17,), dtype=np.float32)
            action[0] = 0.05
            action[3] = 0.6
            action[9] = 1.0
            action[13] = 1.0
            action[14] = 1.0

            fired = False
            for _ in range(120):
                _obs, _reward, terminated, truncated, _info = env.step(action)
                missiles_remaining = int(getattr(env.sim.get_agent_observation(env.agent_id), "missiles_remaining", -1))
                if missiles_remaining < 4:
                    fired = True
                    break
                if terminated or truncated:
                    break

            self.assertTrue(fired)
        finally:
            env.close()

    @unittest.skipUnless(_HAS_GYMNASIUM, "UniversalEnv requires optional gymnasium dependency")
    def test_universal_env_advances_red_scripted_opponent(self) -> None:
        env = UniversalEnv(
            _SCENARIO_PATH,
            include_visual=False,
            include_proprio=False,
            action_mode="full",
            mission_obs_mode="basic",
        )
        try:
            _obs, _info = env.reset(seed=20260516)
            red_id = int(env.loader.entities["Red_Fighter"])
            initial_missiles = int(getattr(env.sim.get_agent_observation(red_id), "missiles_remaining", -1))

            action = np.zeros((17,), dtype=np.float32)
            action[0] = 0.03
            action[3] = 0.62
            action[9] = 1.0

            saw_red_behavior = False
            red_fired = False
            for _ in range(220):
                _obs, _reward, terminated, truncated, _info = env.step(action)
                report = env.loader.scripted_opponent_reports.get(red_id, {})
                if bool(report.get("active", False)):
                    saw_red_behavior = True
                missiles_remaining = int(getattr(env.sim.get_agent_observation(red_id), "missiles_remaining", -1))
                if missiles_remaining < initial_missiles:
                    red_fired = True
                    break
                if terminated or truncated:
                    break

            self.assertTrue(saw_red_behavior)
            self.assertTrue(red_fired)
        finally:
            env.close()


if __name__ == "__main__":
    unittest.main()
