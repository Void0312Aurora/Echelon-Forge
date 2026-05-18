from __future__ import annotations

import unittest
import numpy as np

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402
from gym_envs.scenario_loader import ScenarioLoader  # noqa: E402
from gym_envs.universal_env import build_universal_observation  # noqa: E402
from gym_envs.universal_env import UniversalEnv  # noqa: E402
from python.mission_obs_taxonomy import mission_observation_dim  # noqa: E402


_SCENARIO_PATH = resolve_repo_path(
    "scenarios",
    "air_combat",
    "air_combat_1v1_headon_sensor_smoke_v1.json",
)
_DB_PATH = resolve_repo_path("examples", "config", "database")


class AirCombat1v1FixtureTests(unittest.TestCase):
    def test_loader_fixture_exposes_hostile_contact_and_weapon_state(self) -> None:
        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(_DB_PATH))

        loader = ScenarioLoader(sim)
        agent_id = int(loader.load_scenario(_SCENARIO_PATH, seed=20260516))
        self.assertGreater(agent_id, 0)
        self.assertEqual(agent_id, int(loader.entities["Blue_Fighter"]))
        self.assertIn("Red_Fighter", loader.entities)
        red_id = int(loader.entities["Red_Fighter"])
        self.assertEqual(int(loader.primary_target_id or 0), red_id)
        self.assertEqual(str(loader.primary_target_name), "Red_Fighter")

        obs = None
        saw_contact = False
        hostile_track = None
        for _ in range(120):
            sim.step()
            obs = sim.get_agent_observation(agent_id)
            hostile_track = next(
                (track for track in getattr(obs, "contacts", []) if int(getattr(track, "id", 0)) == red_id),
                None,
            )
            if hostile_track is None:
                continue
            saw_contact = True
            if int(getattr(hostile_track, "classification", 0)) == 2:
                break

        self.assertIsNotNone(obs)
        self.assertTrue(saw_contact)
        self.assertEqual(int(getattr(obs, "missiles_remaining", -1)), 4)
        self.assertTrue(bool(getattr(obs, "can_fire", False)))
        self.assertIsNotNone(hostile_track)
        self.assertEqual(int(getattr(hostile_track, "classification", 0)), 2)
        self.assertIn(int(getattr(hostile_track, "source", 0)), {1, 3})

    def test_universal_env_loads_fixture_with_execution_observation_contract(self) -> None:
        env = UniversalEnv(
            _SCENARIO_PATH,
            include_visual=False,
            include_proprio=False,
            action_mode="full",
            mission_obs_mode="basic",
        )
        try:
            obs, _info = env.reset(seed=20260516)
            self.assertEqual(obs["contacts"].shape, (env.max_contacts, 5))
            self.assertEqual(obs["rwr"].shape, (env.max_rwr, 4))
            self.assertEqual(obs["mission"].shape, (mission_observation_dim("basic"),))
        finally:
            env.close()

    def test_loader_registers_red_scripted_opponent_from_scenario(self) -> None:
        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(_DB_PATH))

        loader = ScenarioLoader(sim)
        _agent_id = int(loader.load_scenario(_SCENARIO_PATH, seed=20260516))
        red_id = int(loader.entities["Red_Fighter"])
        blue_id = int(loader.entities["Blue_Fighter"])

        self.assertIn(red_id, loader.scripted_opponents)
        controller = loader.scripted_opponents[red_id]
        self.assertEqual(int(getattr(controller, "target_id", 0)), blue_id)
        self.assertEqual(int(loader.scripted_opponent_reports[red_id]["target_id"]), blue_id)

    def test_loader_compute_full_step_reports_combat_win_after_red_destroyed(self) -> None:
        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(_DB_PATH))

        loader = ScenarioLoader(sim)
        agent_id = int(loader.load_scenario(_SCENARIO_PATH, seed=20260516))
        red_id = int(loader.entities["Red_Fighter"])

        for _ in range(60):
            sim.step()
            obs = sim.get_agent_observation(agent_id)
            if any(int(getattr(track, "id", 0)) == red_id for track in getattr(obs, "contacts", [])):
                break

        missile_id = int(sim.fire_missile(agent_id, red_id))
        self.assertGreater(missile_id, 0)

        terminated = False
        truncated = False
        reward = 0.0
        for step in range(1, 280):
            sim.step()
            truth = sim.get_agent_observation(agent_id)
            inst = sim.get_instrument_state(agent_id)
            obs = build_universal_observation(
                loader,
                inst,
                truth,
                mission_obs_mode="basic",
                max_contacts=10,
                max_rwr=4,
                include_proprio=False,
                last_action=None,
                action_space=None,
                steps=step,
                max_steps=loader.get_max_steps(),
            )
            reward, terminated, truncated, _status = loader.compute_full_step(
                obs,
                sim,
                step,
                loader.get_max_steps(),
                truth=truth,
                inst_state=inst,
            )
            if terminated or truncated:
                break

        self.assertTrue(bool(terminated))
        self.assertFalse(bool(truncated))
        self.assertEqual(str(loader.last_termination_reason), "combat_win")
        self.assertGreater(float(loader.last_reward_breakdown.get("combat_win_bonus", 0.0)), 0.0)
        self.assertGreater(float(reward), 0.0)

    def test_loader_scripted_red_opponent_updates_command_and_can_fire(self) -> None:
        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(_DB_PATH))

        loader = ScenarioLoader(sim)
        _agent_id = int(loader.load_scenario(_SCENARIO_PATH, seed=20260516))
        red_id = int(loader.entities["Red_Fighter"])

        red_obs0 = sim.get_agent_observation(red_id)
        initial_missiles = int(getattr(red_obs0, "missiles_remaining", -1))
        self.assertEqual(initial_missiles, 4)

        saw_behavior = False
        red_fired = False
        for step in range(1, 220):
            sim.step()
            blue_truth = sim.get_agent_observation(int(loader.agent_id))
            blue_inst = sim.get_instrument_state(int(loader.agent_id))
            loader.steps = step
            loader.update_behaviors(step * sim.get_time_step(), truth=blue_truth, inst=blue_inst)

            report = loader.scripted_opponent_reports.get(red_id, {})
            if bool(report.get("active", False)):
                saw_behavior = True
            if bool(report.get("fired", False)):
                red_fired = True
                break

        self.assertTrue(saw_behavior)
        self.assertTrue(red_fired)

        red_obs1 = sim.get_agent_observation(red_id)
        self.assertLess(int(getattr(red_obs1, "missiles_remaining", -1)), initial_missiles)
