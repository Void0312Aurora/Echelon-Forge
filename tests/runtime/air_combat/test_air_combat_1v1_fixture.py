from __future__ import annotations

import unittest
import numpy as np

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402
from gym_envs.scenario_loader import ScenarioLoader  # noqa: E402
from gym_envs.universal_env_parts.common import gym as _gym  # noqa: E402
from gym_envs.universal_env import build_universal_observation  # noqa: E402
from gym_envs.universal_env import UniversalEnv  # noqa: E402
from python.mission_obs_taxonomy import mission_observation_dim  # noqa: E402
from python.rl.tasking.bridge import LoaderOwnedScriptedOpponentKernelView  # noqa: E402


_SCENARIO_PATH = resolve_repo_path(
    "scenarios",
    "air_combat",
    "air_combat_1v1_headon_sensor_smoke_v1.json",
)
_STAGE0_SCENARIO_PATH = resolve_repo_path(
    "scenarios",
    "air_combat",
    "1v1",
    "air_combat_1v1_stage0_drone_weapon_employment_v1.json",
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

    @unittest.skipIf(_gym is None, "UniversalEnv requires optional dependency 'gymnasium'")
    def test_universal_env_loads_fixture_with_execution_observation_contract(self) -> None:
        env = UniversalEnv(
            _SCENARIO_PATH,
            include_visual=False,
            include_proprio=False,
            action_mode="full",
            mission_obs_mode="basic",
            runtime_compatibility_enabled=True,
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
        self.assertIsInstance(getattr(controller, "kernel", None), LoaderOwnedScriptedOpponentKernelView)

    def test_loader_compute_full_step_reports_combat_win_after_red_destroyed(self) -> None:
        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(_DB_PATH))

        loader = ScenarioLoader(sim)
        agent_id = int(loader.load_scenario(_SCENARIO_PATH, seed=20260516))
        red_id = int(loader.entities["Red_Fighter"])

        for _ in range(10):
            self.assertTrue(
                bool(
                    sim.debug_apply_local_proximity_hit(
                        agent_id,
                        red_id,
                        0.0,
                        0.0,
                        0.3,
                        240.0,
                        80.0,
                    )
                )
            )
            sim.step()
            if not bool(sim.is_unit_active(red_id)):
                break
        self.assertFalse(bool(sim.is_unit_active(red_id)))

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
        self.assertNotIn("objective_bonus", loader.last_reward_breakdown)
        self.assertGreater(float(loader.last_reward_breakdown.get("combat_win_bonus", 0.0)), 0.0)
        self.assertAlmostEqual(float(loader.last_reward_breakdown.get("total", 0.0)), 1500.0, places=6)
        self.assertGreater(float(reward), 0.0)

    def test_loader_compute_full_step_consumes_structured_damage_report_for_combat_win(self) -> None:
        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(_DB_PATH))

        loader = ScenarioLoader(sim)
        agent_id = int(loader.load_scenario(_SCENARIO_PATH, seed=20260516))
        red_id = int(loader.entities["Red_Fighter"])

        health_before = [float(value) for value in sim.get_unit_health(red_id)]
        self.assertTrue(bool(sim.is_unit_active(red_id)))

        for _ in range(2):
            self.assertTrue(
                bool(
                    sim.debug_apply_local_proximity_hit(
                        agent_id,
                        red_id,
                        0.0,
                        0.0,
                        0.3,
                        240.0,
                        80.0,
                    )
                )
            )

        events = sim.export_recent_engagement_events()
        self.assertGreaterEqual(len(events.damage_reports), 1)
        report = events.damage_reports[-1]
        self.assertTrue(bool(report.mobility_kill))
        self.assertEqual(str(report.loss_state_to), "mobility_kill")
        self.assertFalse(bool(report.destroyed))
        self.assertTrue(bool(sim.is_unit_active(red_id)))
        self.assertEqual([float(value) for value in sim.get_unit_health(red_id)], health_before)

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
            steps=1,
            max_steps=loader.get_max_steps(),
        )
        reward, terminated, truncated, _status = loader.compute_full_step(
            obs,
            sim,
            1,
            loader.get_max_steps(),
            truth=truth,
            inst_state=inst,
        )

        self.assertTrue(bool(terminated))
        self.assertFalse(bool(truncated))
        self.assertEqual(str(loader.last_termination_reason), "combat_win")
        self.assertNotIn("objective_bonus", loader.last_reward_breakdown)
        self.assertGreater(float(loader.last_reward_breakdown.get("combat_win_bonus", 0.0)), 0.0)
        self.assertAlmostEqual(float(loader.last_reward_breakdown.get("total", 0.0)), 1500.0, places=6)
        self.assertGreater(float(reward), 0.0)

    def test_loader_damage_report_shaping_consumes_nonterminal_structured_damage_once(self) -> None:
        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(_DB_PATH))

        loader = ScenarioLoader(sim)
        agent_id = int(loader.load_scenario(_SCENARIO_PATH, seed=20260516))
        red_id = int(loader.entities["Red_Fighter"])

        self.assertTrue(
            bool(
                sim.debug_apply_local_proximity_hit(
                    agent_id,
                    red_id,
                    0.0,
                    0.0,
                    0.3,
                    80.0,
                    40.0,
                )
            )
        )
        events = sim.export_recent_engagement_events()
        self.assertEqual(len(events.damage_reports), 1)
        report = events.damage_reports[0]
        self.assertLess(float(report.system_health_delta), 0.0)
        self.assertEqual(str(report.loss_state_to), "combat_capable")
        self.assertTrue(bool(sim.is_unit_active(red_id)))

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
            steps=1,
            max_steps=loader.get_max_steps(),
        )
        reward, terminated, truncated, _status = loader.compute_full_step(
            obs,
            sim,
            1,
            loader.get_max_steps(),
            truth=truth,
            inst_state=inst,
        )

        self.assertFalse(bool(terminated))
        self.assertFalse(bool(truncated))
        self.assertGreater(float(loader.last_reward_breakdown.get("air_combat_target_system_damage_progress", 0.0)), 0.0)
        self.assertGreater(float(loader.last_reward_breakdown.get("air_combat_target_mission_capability_progress", 0.0)), 0.0)
        self.assertAlmostEqual(float(loader.last_reward_breakdown.get("total", 0.0)), float(reward), places=6)
        self.assertGreater(float(reward), 0.0)

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
            steps=2,
            max_steps=loader.get_max_steps(),
        )
        reward2, terminated2, truncated2, _status2 = loader.compute_full_step(
            obs,
            sim,
            2,
            loader.get_max_steps(),
            truth=truth,
            inst_state=inst,
        )

        self.assertFalse(bool(terminated2))
        self.assertFalse(bool(truncated2))
        self.assertNotIn("air_combat_target_system_damage_progress", loader.last_reward_breakdown)
        self.assertAlmostEqual(float(loader.last_reward_breakdown.get("total", 0.0)), float(reward2), places=6)

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

    @unittest.skipIf(_gym is None, "UniversalEnv requires optional dependency 'gymnasium'")
    def test_stage0_drone_weapon_employment_fixed_fire_smoke_reaches_weapon_release(self) -> None:
        env = UniversalEnv(
            _STAGE0_SCENARIO_PATH,
            include_visual=False,
            include_proprio=True,
            action_mode="full",
            mission_obs_mode="basic",
            step_info_mode="full",
            execution_step_runtime_mode="compiled",
            flight_shaping_backend="compiled",
            runtime_compatibility_enabled=True,
        )
        try:
            _obs, _info = env.reset(seed=20260525)

            action = np.zeros((17,), dtype=np.float32)
            action[0] = 0.02
            action[3] = 0.65
            action[9] = 1.0
            action[13] = 1.0
            action[14] = 1.0
            action[16] = 1.0 / 7.0

            fired = False
            terminated = False
            truncated = False
            info: dict[str, object] = {}
            reports_before = len(env.sim.export_recent_engagement_events().damage_reports)
            for _ in range(int(env.max_steps)):
                _obs, _reward, terminated, truncated, info = env.step(action)
                missiles_remaining = int(
                    getattr(env.sim.get_agent_observation(env.agent_id), "missiles_remaining", -1)
                )
                if missiles_remaining < 4:
                    fired = True
                if terminated or truncated:
                    break

            self.assertTrue(fired)
            self.assertIn(str(info.get("termination_reason")), {"combat_win", "combat_timeout"})
            if bool(terminated):
                self.assertFalse(truncated)
                self.assertEqual(str(info.get("termination_reason")), "combat_win")
            else:
                self.assertTrue(truncated)
                self.assertEqual(str(info.get("termination_reason")), "combat_timeout")
            reward_terms = info.get("reward_terms", {})
            self.assertIsInstance(reward_terms, dict)
            reports_after = len(env.sim.export_recent_engagement_events().damage_reports)
            if str(info.get("termination_reason")) == "combat_win":
                self.assertGreater(float(reward_terms.get("combat_win_bonus", 0.0)), 0.0)
                self.assertGreater(reports_after, reports_before)
        finally:
            env.close()
