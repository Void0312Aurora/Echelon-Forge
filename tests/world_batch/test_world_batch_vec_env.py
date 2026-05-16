from __future__ import annotations

import json
import tempfile
import unittest

import numpy as np

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import torch  # noqa: E402,F401

import ef_py  # noqa: E402

from gym_envs.universal_env import UniversalEnv  # noqa: E402
from python.rl.control.wrappers import MultiTimescaleActionWrapper  # noqa: E402
from python.rl.policy_algo.device_dict_rollout_buffer import DeviceDictRolloutBuffer  # noqa: E402
from python.rl.policy_algo.ppo_adaptive_kl import AdaptiveKLPPO  # noqa: E402
from python.rl.runtime.shared_memory_vec_env import SharedMemorySubprocVecEnv  # noqa: E402
from python.rl.runtime.world_batch_vec_env import WorldBatchVecEnv  # noqa: E402
from tests.support._leader_env_runtime_test_support import CounterDictEnv  # noqa: E402


def _inline_vec_env_scenario() -> dict:
    return {
        "scenario_name": "phase4_world_batch_vec_env_inline",
        "meta": {
            "max_steps": 1,
        },
        "environment": {
            "time_step": 0.05,
            "terrain_type": "legacy",
            "wind": {
                "speed_mps": 4.0,
                "dir_from_deg": 180.0,
                "shear_mps_per_km": 0.0,
            },
            "zones": [
                {
                    "name": "Runway_A",
                    "x": 0.0,
                    "y": 0.0,
                    "width": 60.0,
                    "length": 2500.0,
                    "heading": 90.0,
                    "surface": "Concrete",
                }
            ],
        },
        "mission_command": {
            "command_code": 2,
            "target_heading": 90.0,
            "target_altitude": 1200.0,
            "target_speed": 180.0,
        },
        "entities": [
            {
                "name": "Lead",
                "type": "Aircraft",
                "side": "Blue",
                "is_agent": True,
                "pos": [-1400.0, 0.0, 1200.0],
                "vel": [0.0, 180.0, 0.0],
                "heading": 90.0,
            }
        ],
    }


def _inline_vec_env_route_transition_scenario() -> dict:
    scenario = _inline_vec_env_scenario()
    scenario["meta"]["max_steps"] = 3
    scenario["mission_command"] = {
        "command_code": 3,
        "target_heading": 90.0,
        "target_altitude": 1200.0,
        "target_speed": 180.0,
        "waypoint_mode": "flyby",
        "waypoints": [
            {"x": -1350.0, "y": 0.0, "z": 1200.0, "radius_m": 1200.0},
        ],
        "post_waypoint_transition": {
            "command_code": 2,
            "target_heading": 45.0,
            "target_altitude": 900.0,
            "target_speed": 160.0,
            "phase_name": "post_route",
            "transition_reward": 123.0,
        },
    }
    return scenario


def _inline_air_combat_scripted_opponent_scenario() -> dict:
    return {
        "scenario_name": "air_combat_world_batch_scripted_opponent_inline",
        "environment": {
            "time_step": 0.05,
            "max_steps": 320,
            "terrain_type": "flat",
            "wind": {
                "speed_mps": 0.0,
                "dir_from_deg": 0.0,
                "shear_mps_per_km": 0.0,
            },
        },
        "mission_command": {
            "command_code": 0,
            "target_heading": 0.0,
            "target_altitude": 1200.0,
            "target_speed": 180.0,
            "assigned_target_name": "Red_Fighter",
            "authorization_to_fire": True,
        },
        "entities": [
            {
                "name": "Blue_Fighter",
                "type": "F-16C_Block50",
                "side": "Blue",
                "is_agent": True,
                "pos": [0.0, 0.0, 1200.0],
                "vel": [0.0, 180.0, 0.0],
                "heading": 0.0,
                "ammo": {
                    "missiles_remaining": 4,
                    "max_missiles": 4,
                },
                "weapon_cooldown": {
                    "cooldown_s": 0.75,
                    "last_fire_time": -1.0,
                },
            },
            {
                "name": "Red_Fighter",
                "type": "F-16C_Block50",
                "side": "Red",
                "pos": [0.0, 8000.0, 1200.0],
                "vel": [0.0, -180.0, 0.0],
                "heading": 180.0,
                "scripted_agent": {
                    "name": "red_scripted_agent",
                    "target_name": "Blue_Fighter",
                    "fire_range_m": 9000.0,
                    "threat_range_m": 9000.0,
                    "merge_range_m": 3500.0,
                },
                "ammo": {
                    "missiles_remaining": 4,
                    "max_missiles": 4,
                },
                "weapon_cooldown": {
                    "cooldown_s": 0.75,
                    "last_fire_time": -1.0,
                },
            },
        ],
    }


def _controller_runtime_state_matches_loader_state(runtime_state, loader_state) -> bool:
    def _canonicalize_json(raw: str) -> str:
        if not isinstance(raw, str) or not raw.strip():
            return str(raw or "")
        try:
            parsed = json.loads(raw)
        except Exception:
            return str(raw)

        def _strip_internal_fields(value):
            if isinstance(value, dict):
                return {
                    str(key): _strip_internal_fields(item)
                    for key, item in value.items()
                    if not str(key).startswith("_")
                }
            if isinstance(value, list):
                return [_strip_internal_fields(item) for item in value]
            return value

        return json.dumps(_strip_internal_fields(parsed), ensure_ascii=True, sort_keys=True)

    def _route_digest(state) -> list[tuple[float, float, float, float, float, float, str]]:
        route = []
        for waypoint in list(getattr(state, "route_waypoints", [])):
            route.append(
                (
                    float(getattr(waypoint, "x_m", 0.0)),
                    float(getattr(waypoint, "y_m", 0.0)),
                    float(getattr(waypoint, "z_m", 0.0)),
                    float(getattr(waypoint, "radius_m", 0.0)),
                    float(getattr(waypoint, "altitude_m", 0.0)),
                    float(getattr(waypoint, "speed_mps", 0.0)),
                    str(getattr(waypoint, "waypoint_mode", "")),
                )
            )
        return route

    runtime_digest = {
        "has_mission_command_json": bool(getattr(runtime_state, "has_mission_command_json", False)),
        "mission_command_json": _canonicalize_json(str(getattr(runtime_state, "mission_command_json", ""))),
        "route_waypoints": _route_digest(runtime_state),
        "has_post_waypoint_transition_json": bool(getattr(runtime_state, "has_post_waypoint_transition_json", False)),
        "post_waypoint_transition_json": _canonicalize_json(str(getattr(runtime_state, "post_waypoint_transition_json", ""))),
        "mission_phase_name": str(getattr(runtime_state, "mission_phase_name", "")),
        "has_cached_route_ref_id": bool(getattr(runtime_state, "has_cached_route_ref_id", False)),
        "cached_route_ref_id": int(getattr(runtime_state, "cached_route_ref_id", 0)),
    }
    loader_digest = {
        "has_mission_command_json": bool(getattr(loader_state, "has_mission_command_json", False)),
        "mission_command_json": _canonicalize_json(str(getattr(loader_state, "mission_command_json", ""))),
        "route_waypoints": _route_digest(loader_state),
        "has_post_waypoint_transition_json": bool(getattr(loader_state, "has_post_waypoint_transition_json", False)),
        "post_waypoint_transition_json": _canonicalize_json(str(getattr(loader_state, "post_waypoint_transition_json", ""))),
        "mission_phase_name": str(getattr(loader_state, "mission_phase_name", "")),
        "has_cached_route_ref_id": bool(getattr(loader_state, "has_cached_route_ref_id", False)),
        "cached_route_ref_id": int(getattr(loader_state, "cached_route_ref_id", 0)),
    }
    return runtime_digest == loader_digest


class WorldBatchVecEnvTests(unittest.TestCase):
    def test_world_batch_vec_env_applies_worker_thread_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/inline_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

            vec_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=2,
                include_visual=False,
                include_proprio=False,
                worker_threads=1,
            )
            try:
                self.assertEqual(int(vec_env.batch_runtime.worker_threads()), 1)
                self.assertEqual(int(vec_env.batch_runtime.effective_worker_threads()), 1)
            finally:
                vec_env.close()

    def test_world_batch_vec_env_steps_and_auto_resets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/inline_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

            vec_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=2,
                include_visual=False,
                include_proprio=True,
            )
            try:
                vec_env.seed(123)
                obs = vec_env.reset()
                self.assertEqual(obs["instruments"].shape, (2, 42))
                self.assertEqual(obs["proprio"].shape, (2, 17))
                self.assertTrue(np.allclose(obs["proprio"], 0.0))

                obs, rewards, dones, infos = vec_env.step(np.zeros((2, 17), dtype=np.float32))
                self.assertEqual(rewards.shape, (2,))
                self.assertTrue(np.all(dones == np.asarray([True, True])))
                self.assertIn("terminal_observation", infos[0])
                self.assertIn("episode", infos[0])
                self.assertGreaterEqual(int(infos[0]["episode"]["l"]), 1)
                self.assertTrue(np.allclose(obs["proprio"], 0.0))
                self.assertEqual(vec_env.reset_infos, [{}, {}])
            finally:
                vec_env.close()

    def test_world_batch_vec_env_reset_uses_runtime_facade_compatibly(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_data = _inline_vec_env_scenario()
            scenario_data["meta"]["max_steps"] = 2
            scenario_path = f"{tmpdir}/inline_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(scenario_data, f, ensure_ascii=True)

            vec_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=2,
                include_visual=False,
                include_proprio=False,
            )
            try:
                self.assertTrue(hasattr(vec_env, "runtime_facade"))
                self.assertIsNotNone(vec_env.runtime_facade)
                self.assertEqual(int(vec_env.runtime_facade.world_count()), 2)
                self.assertEqual(int(vec_env.batch_runtime.world_count()), 2)

                vec_env.seed(123)
                obs = vec_env.reset()

                self.assertEqual(obs["instruments"].shape, (2, 42))
                self.assertEqual(obs["contacts"].shape[0], 2)
                self.assertEqual(obs["mission"].shape[0], 2)
                self.assertIsNotNone(vec_env.envs[0].agent_id)
                self.assertIsNotNone(vec_env.envs[1].agent_id)
            finally:
                vec_env.close()

    def test_world_batch_vec_env_drives_scripted_red_opponent_on_default_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/air_combat_scripted_opponent.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_inline_air_combat_scripted_opponent_scenario(), f, ensure_ascii=True)

            vec_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=False,
            )
            try:
                vec_env.seed(20260516)
                _obs = vec_env.reset()
                loader_red_id = int(vec_env.envs[0].loader.entities["Red_Fighter"])
                initial_missiles = int(
                    getattr(vec_env.envs[0].loader.sim.get_agent_observation(loader_red_id), "missiles_remaining", -1)
                )

                action = np.zeros((1, 17), dtype=np.float32)
                action[0, 0] = 0.03
                action[0, 3] = 0.62
                action[0, 9] = 1.0

                saw_red_behavior = False
                red_fired = False
                for _ in range(220):
                    _obs, _rewards, dones, _infos = vec_env.step(action)
                    report = vec_env.envs[0].loader.scripted_opponent_reports.get(loader_red_id, {})
                    if bool(report.get("active", False)):
                        saw_red_behavior = True
                    missiles_remaining = int(
                        getattr(vec_env.envs[0].loader.sim.get_agent_observation(loader_red_id), "missiles_remaining", -1)
                    )
                    if missiles_remaining < initial_missiles:
                        red_fired = True
                        break
                    if bool(dones[0]):
                        break

                self.assertTrue(saw_red_behavior)
                self.assertTrue(red_fired)
            finally:
                vec_env.close()

    def test_world_batch_vec_env_supports_visual_observations(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/inline_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

            vec_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=2,
                include_visual=True,
                include_proprio=False,
                visual_downsample=2,
                visual_update_interval=2,
            )
            try:
                obs = vec_env.reset()
                self.assertEqual(obs["visual"].shape, (2, 24, 48, 10))
                obs2, rewards, dones, infos = vec_env.step(np.zeros((2, 17), dtype=np.float32))
                self.assertEqual(obs2["visual"].shape, (2, 24, 48, 10))
                self.assertEqual(rewards.shape, (2,))
                self.assertEqual(dones.shape, (2,))
                self.assertEqual(len(infos), 2)
            finally:
                vec_env.close()

    def test_world_batch_vec_env_supports_per_env_randomization_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_data = _inline_vec_env_scenario()
            scenario_data["meta"]["max_steps"] = 4
            scenario_data["environment"]["randomization"] = {
                "world_yaw_range": [-15.0, 15.0],
                "world_yaw_origin": [0.0, 0.0],
            }
            scenario_path = f"{tmpdir}/inline_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(scenario_data, f, ensure_ascii=True)

            vec_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=2,
                include_visual=False,
                include_proprio=False,
            )
            try:
                vec_env.env_method("set_randomization_overrides", {"world_yaw_range": [-5.0, -5.0]}, indices=[0])
                vec_env.env_method("set_randomization_overrides", {"world_yaw_range": [10.0, 10.0]}, indices=[1])
                obs = vec_env.reset()
                self.assertEqual(obs["instruments"].shape, (2, 42))
                overrides = vec_env.get_attr("randomization_overrides")
                self.assertEqual(float(overrides[0]["world_yaw_range"][0]), -5.0)
                self.assertEqual(float(overrides[1]["world_yaw_range"][0]), 10.0)
                yaw_values = vec_env.get_attr("world_yaw_deg")
                self.assertNotEqual(float(yaw_values[0]), float(yaw_values[1]))
            finally:
                vec_env.close()

    def test_world_batch_vec_env_compiled_batch_observation_matches_legacy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_data = _inline_vec_env_scenario()
            scenario_data["meta"]["max_steps"] = 2
            scenario_path = f"{tmpdir}/inline_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(scenario_data, f, ensure_ascii=True)

            legacy_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=2,
                include_visual=False,
                include_proprio=True,
                batch_observation_backend="legacy",
            )
            compiled_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=2,
                include_visual=False,
                include_proprio=True,
                batch_observation_backend="compiled",
            )
            try:
                legacy_env.seed(123)
                compiled_env.seed(123)
                legacy_obs = legacy_env.reset()
                compiled_obs = compiled_env.reset()
                for key in ("instruments", "contacts", "rwr", "mission", "proprio"):
                    self.assertTrue(
                        np.allclose(legacy_obs[key], compiled_obs[key], atol=1.0e-6),
                        msg=f"reset mismatch for key={key}",
                    )

                actions = np.zeros((2, 17), dtype=np.float32)
                legacy_obs, legacy_rewards, legacy_dones, _legacy_infos = legacy_env.step(actions)
                compiled_obs, compiled_rewards, compiled_dones, _compiled_infos = compiled_env.step(actions)
                for key in ("instruments", "contacts", "rwr", "mission", "proprio"):
                    self.assertTrue(
                        np.allclose(legacy_obs[key], compiled_obs[key], atol=1.0e-6),
                        msg=f"step mismatch for key={key}",
                    )
                self.assertTrue(np.allclose(legacy_rewards, compiled_rewards, atol=1.0e-6))
                self.assertTrue(np.array_equal(legacy_dones, compiled_dones))
            finally:
                legacy_env.close()
                compiled_env.close()

    def test_world_batch_vec_env_compiled_batch_visual_matches_legacy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_data = _inline_vec_env_scenario()
            scenario_data["meta"]["max_steps"] = 2
            scenario_path = f"{tmpdir}/inline_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(scenario_data, f, ensure_ascii=True)

            legacy_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=2,
                include_visual=True,
                include_proprio=False,
                visual_downsample=2,
                visual_update_interval=1,
                batch_visual_backend="legacy",
            )
            compiled_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=2,
                include_visual=True,
                include_proprio=False,
                visual_downsample=2,
                visual_update_interval=1,
                batch_visual_backend="compiled",
            )
            try:
                legacy_env.seed(123)
                compiled_env.seed(123)
                legacy_obs = legacy_env.reset()
                compiled_obs = compiled_env.reset()
                self.assertTrue(
                    np.allclose(legacy_obs["visual"], compiled_obs["visual"], atol=1.0e-5),
                    msg="reset visual mismatch",
                )

                actions = np.zeros((2, 17), dtype=np.float32)
                legacy_obs, legacy_rewards, legacy_dones, _legacy_infos = legacy_env.step(actions)
                compiled_obs, compiled_rewards, compiled_dones, _compiled_infos = compiled_env.step(actions)
                self.assertTrue(
                    np.allclose(legacy_obs["visual"], compiled_obs["visual"], atol=1.0e-5),
                    msg="step visual mismatch",
                )
                self.assertTrue(np.allclose(legacy_rewards, compiled_rewards, atol=1.0e-6))
                self.assertTrue(np.array_equal(legacy_dones, compiled_dones))
            finally:
                legacy_env.close()
                compiled_env.close()

    def test_world_batch_vec_env_binds_compiled_runtime_metadata_to_loaders(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_data = _inline_vec_env_scenario()
            scenario_data["environment"]["randomization"] = {
                "world_yaw_range": [-10.0, 10.0],
                "world_yaw_origin": [0.0, 0.0],
            }
            scenario_data["objectives"] = [
                {
                    "type": "conditional",
                    "reward": 25.0,
                    "conditions": [
                        {"property": "heading", "op": ">=", "value": 0.0},
                    ],
                }
            ]
            scenario_path = f"{tmpdir}/inline_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(scenario_data, f, ensure_ascii=True)

            vec_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=2,
                include_visual=False,
                include_proprio=False,
            )
            try:
                vec_env.seed(123)
                _ = vec_env.reset()
                for handle in vec_env.envs:
                    self.assertIsNotNone(handle.loader._compiled_runtime_metadata)
                    self.assertIs(handle.loader._compiled_runtime_metadata, vec_env._compiled_scenario.runtime_metadata)
                    self.assertEqual(len(handle.loader._compiled_conditional_objectives), 1)
                    self.assertEqual(len(handle.loader.ils_beacons), 1)
            finally:
                vec_env.close()

    def test_world_batch_vec_env_propagates_execution_step_runtime_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/inline_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

            vec_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=2,
                include_visual=False,
                include_proprio=False,
                execution_step_runtime_mode="legacy",
            )
            try:
                for handle in vec_env.envs:
                    self.assertEqual(handle.loader.execution_step_runtime_mode, "legacy")
                    self.assertFalse(bool(handle.loader.use_compiled_execution_step_runtime))
            finally:
                vec_env.close()

    def test_world_batch_vec_env_reports_effective_flight_shaping_backend_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/inline_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

            legacy_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=2,
                include_visual=False,
                include_proprio=False,
                execution_step_runtime_mode="legacy",
                flight_shaping_backend="auto",
            )
            compiled_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=2,
                include_visual=False,
                include_proprio=False,
                execution_step_runtime_mode="compiled",
                flight_shaping_backend="auto",
            )
            gpu_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=2,
                include_visual=False,
                include_proprio=False,
                execution_step_runtime_mode="compiled",
                flight_shaping_backend="gpu_host",
            )
            try:
                self.assertEqual(legacy_env._flight_shaping_backend_mode(), "legacy")
                self.assertEqual(compiled_env._flight_shaping_backend_mode(), "compiled")
                self.assertEqual(gpu_env._flight_shaping_backend_mode(), "gpu_host")
            finally:
                legacy_env.close()
                compiled_env.close()
                gpu_env.close()

    def test_world_batch_vec_env_execution_episode_controller_shadow_compare_flag_off_is_noop(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_data = _inline_vec_env_scenario()
            scenario_data["meta"]["max_steps"] = 2
            scenario_path = f"{tmpdir}/inline_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(scenario_data, f, ensure_ascii=True)

            vec_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=False,
            )
            try:
                vec_env.seed(123)
                _ = vec_env.reset()
                _obs, _rewards, dones, infos = vec_env.step(np.zeros((1, 17), dtype=np.float32))
                self.assertFalse(bool(dones[0]))
                self.assertNotIn("execution_episode_controller_shadow_compare", infos[0])
                self.assertEqual(vec_env.last_execution_episode_controller_shadow_compare, [None])
            finally:
                vec_env.close()

    def test_world_batch_vec_env_execution_episode_controller_shadow_compare_reports_parity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_data = _inline_vec_env_scenario()
            scenario_data["meta"]["max_steps"] = 2
            scenario_path = f"{tmpdir}/inline_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(scenario_data, f, ensure_ascii=True)

            vec_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                execution_episode_controller_shadow_compare=True,
            )
            try:
                vec_env.seed(123)
                _ = vec_env.reset()
                _obs, _rewards, dones, infos = vec_env.step(np.zeros((1, 17), dtype=np.float32))
                self.assertFalse(bool(dones[0]))
                report = infos[0].get("execution_episode_controller_shadow_compare")
                self.assertIsNotNone(report)
                comparison = dict(report["comparison"])
                self.assertTrue(bool(comparison["overall_match"]), msg=str(comparison))
                self.assertTrue(bool(report["advance_state"]))
                self.assertEqual(int(report["shadow_state"]["step_count"]), 1)
                latest_report = vec_env.last_execution_episode_controller_shadow_compare[0]
                self.assertIsNotNone(latest_report)
                self.assertTrue(bool(latest_report["comparison"]["overall_match"]))
            finally:
                vec_env.close()

    def test_world_batch_vec_env_execution_episode_controller_shadow_compare_resyncs_on_autoreset(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_data = _inline_vec_env_scenario()
            scenario_data["meta"]["max_steps"] = 1
            scenario_path = f"{tmpdir}/inline_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(scenario_data, f, ensure_ascii=True)

            vec_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=False,
                execution_episode_controller_shadow_compare=True,
            )
            try:
                vec_env.seed(123)
                _ = vec_env.reset()
                for step_idx in range(2):
                    _obs, _rewards, dones, infos = vec_env.step(np.zeros((1, 17), dtype=np.float32))
                    self.assertTrue(bool(dones[0]))
                    report = infos[0].get("execution_episode_controller_shadow_compare")
                    self.assertIsNotNone(report)
                    comparison = dict(report["comparison"])
                    self.assertTrue(bool(comparison["overall_match"]), msg=f"step={step_idx}: {comparison}")

                    ref = ef_py.WorldEntityRef()
                    ref.world_index = 0
                    ref.entity_id = int(vec_env.envs[0].agent_id)
                    controller_state = vec_env.batch_runtime.export_execution_episode_states_batch([ref])[0]
                    loader_state = vec_env.envs[0].loader.build_execution_episode_state()
                    self.assertTrue(ef_py.execution_episode_states_equivalent(controller_state, loader_state))
                    self.assertEqual(int(controller_state.step_count), 0)
            finally:
                vec_env.close()

    def test_world_batch_vec_env_execution_episode_controller_mainline_rejects_shadow_compare(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/inline_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_inline_vec_env_scenario(), f, ensure_ascii=True)

            with self.assertRaises(RuntimeError):
                WorldBatchVecEnv(
                    scenario_path=scenario_path,
                    n_envs=1,
                    include_visual=False,
                    include_proprio=False,
                    execution_episode_controller_shadow_compare=True,
                    execution_episode_controller_mainline=True,
                )

    def test_world_batch_vec_env_execution_episode_controller_mainline_matches_compiled_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_data = _inline_vec_env_scenario()
            scenario_data["meta"]["max_steps"] = 3
            scenario_path = f"{tmpdir}/inline_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(scenario_data, f, ensure_ascii=True)

            legacy_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=False,
                execution_step_runtime_mode="compiled",
                flight_shaping_backend="compiled",
            )
            mainline_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=False,
                execution_step_runtime_mode="compiled",
                flight_shaping_backend="compiled",
                execution_episode_controller_mainline=True,
            )
            try:
                legacy_env.seed(123)
                mainline_env.seed(123)
                legacy_obs = legacy_env.reset()
                mainline_obs = mainline_env.reset()
                for key in ("instruments", "contacts", "rwr", "mission"):
                    self.assertTrue(
                        np.allclose(np.asarray(legacy_obs[key]), np.asarray(mainline_obs[key]), atol=1.0e-6),
                        msg=f"reset mismatch for key={key}",
                    )

                action = np.zeros((1, 17), dtype=np.float32)
                for step_idx in range(2):
                    legacy_obs, legacy_rewards, legacy_dones, legacy_infos = legacy_env.step(action)
                    mainline_obs, mainline_rewards, mainline_dones, mainline_infos = mainline_env.step(action)
                    self.assertFalse(bool(legacy_dones[0]), msg=f"legacy unexpectedly done at step={step_idx}")
                    self.assertFalse(bool(mainline_dones[0]), msg=f"mainline unexpectedly done at step={step_idx}")
                    self.assertAlmostEqual(float(legacy_rewards[0]), float(mainline_rewards[0]), places=6)
                    self.assertTrue(
                        np.allclose(
                            np.asarray(legacy_infos[0]["mission_status"], dtype=np.float32),
                            np.asarray(mainline_infos[0]["mission_status"], dtype=np.float32),
                            atol=1.0e-6,
                        ),
                        msg=f"mission_status mismatch at step={step_idx}",
                    )
                    self.assertEqual(
                        legacy_infos[0].get("termination_reason"),
                        mainline_infos[0].get("termination_reason"),
                    )
                    self.assertEqual(
                        set(dict(legacy_infos[0].get("reward_terms", {})).keys()),
                        set(dict(mainline_infos[0].get("reward_terms", {})).keys()),
                    )
                    for key, value in dict(legacy_infos[0].get("reward_terms", {})).items():
                        self.assertAlmostEqual(
                            float(value),
                            float(dict(mainline_infos[0]["reward_terms"])[key]),
                            places=6,
                            msg=f"reward term mismatch for {key} at step={step_idx}",
                        )
                    for key in ("instruments", "contacts", "rwr", "mission"):
                        self.assertTrue(
                            np.allclose(np.asarray(legacy_obs[key]), np.asarray(mainline_obs[key]), atol=1.0e-5),
                            msg=f"step={step_idx} mismatch for key={key}",
                        )

                ref = ef_py.WorldEntityRef()
                ref.world_index = 0
                ref.entity_id = int(mainline_env.envs[0].agent_id)
                runtime_state = mainline_env.batch_runtime.export_execution_episode_states_batch([ref])[0]
                loader_state = mainline_env.envs[0].loader.build_execution_episode_state()
                self.assertTrue(
                    _controller_runtime_state_matches_loader_state(runtime_state, loader_state)
                )
            finally:
                legacy_env.close()
                mainline_env.close()

    def test_world_batch_vec_env_execution_episode_controller_mainline_resyncs_on_autoreset(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_data = _inline_vec_env_scenario()
            scenario_data["meta"]["max_steps"] = 1
            scenario_path = f"{tmpdir}/inline_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(scenario_data, f, ensure_ascii=True)

            vec_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=False,
                execution_step_runtime_mode="compiled",
                flight_shaping_backend="compiled",
                execution_episode_controller_mainline=True,
            )
            try:
                vec_env.seed(123)
                _ = vec_env.reset()
                for _step_idx in range(2):
                    _obs, _rewards, dones, _infos = vec_env.step(np.zeros((1, 17), dtype=np.float32))
                    self.assertTrue(bool(dones[0]))
                    self.assertTrue(bool(vec_env.batch_runtime.execution_episode_controller_ready(0)))
                    ref = ef_py.WorldEntityRef()
                    ref.world_index = 0
                    ref.entity_id = int(vec_env.envs[0].agent_id)
                    runtime_state = vec_env.batch_runtime.export_execution_episode_states_batch([ref])[0]
                    loader_state = vec_env.envs[0].loader.build_execution_episode_state()
                    self.assertEqual(int(runtime_state.step_count), 0)
                    self.assertTrue(
                        _controller_runtime_state_matches_loader_state(runtime_state, loader_state)
                    )
            finally:
                vec_env.close()

    def test_world_batch_vec_env_execution_episode_controller_mainline_reprime_handles_post_waypoint_transition(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/inline_route_transition_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_inline_vec_env_route_transition_scenario(), f, ensure_ascii=True)

            legacy_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=False,
                execution_step_runtime_mode="compiled",
                flight_shaping_backend="compiled",
            )
            mainline_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=False,
                execution_step_runtime_mode="compiled",
                flight_shaping_backend="compiled",
                execution_episode_controller_mainline=True,
            )
            try:
                legacy_env.seed(123)
                mainline_env.seed(123)
                _ = legacy_env.reset()
                _ = mainline_env.reset()
                action = np.zeros((1, 17), dtype=np.float32)
                _legacy_obs, legacy_rewards, legacy_dones, legacy_infos = legacy_env.step(action)
                _mainline_obs, mainline_rewards, mainline_dones, mainline_infos = mainline_env.step(action)

                self.assertAlmostEqual(float(legacy_rewards[0]), float(mainline_rewards[0]), places=6)
                self.assertEqual(bool(legacy_dones[0]), bool(mainline_dones[0]))
                self.assertTrue(
                    np.allclose(
                        np.asarray(legacy_infos[0]["mission_status"], dtype=np.float32),
                        np.asarray(mainline_infos[0]["mission_status"], dtype=np.float32),
                        atol=1.0e-6,
                    )
                )
                self.assertAlmostEqual(
                    float(mainline_infos[0]["reward_terms"]["phase_transition_bonus"]),
                    123.0,
                    places=6,
                )
                self.assertEqual(int(mainline_env.envs[0].loader.mission_cmd["command_code"]), 2)
                self.assertEqual(str(mainline_env.envs[0].loader.mission_phase_name), "post_route")

                ref = ef_py.WorldEntityRef()
                ref.world_index = 0
                ref.entity_id = int(mainline_env.envs[0].agent_id)
                runtime_state = mainline_env.batch_runtime.export_execution_episode_states_batch([ref])[0]
                loader_state = mainline_env.envs[0].loader.build_execution_episode_state()
                self.assertTrue(
                    _controller_runtime_state_matches_loader_state(runtime_state, loader_state)
                )
                self.assertEqual(str(runtime_state.mission_phase_name), "post_route")
                self.assertEqual(len(list(runtime_state.route_waypoints)), 0)
            finally:
                legacy_env.close()
                mainline_env.close()

    def test_world_batch_vec_env_execution_episode_controller_mainline_skips_python_behavior_updates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/inline_route_transition_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_inline_vec_env_route_transition_scenario(), f, ensure_ascii=True)

            vec_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=False,
                execution_step_runtime_mode="compiled",
                flight_shaping_backend="compiled",
                execution_episode_controller_mainline=True,
            )
            try:
                vec_env.seed(123)
                _ = vec_env.reset()

                def _unexpected_update_behaviors(*_args, **_kwargs):
                    raise AssertionError("mainline path should not call ScenarioLoader.update_behaviors()")

                vec_env.envs[0].loader.update_behaviors = _unexpected_update_behaviors
                obs, rewards, dones, infos = vec_env.step(np.zeros((1, 17), dtype=np.float32))

                self.assertFalse(bool(dones[0]))
                self.assertGreaterEqual(float(rewards[0]), 0.0)
                self.assertEqual(obs["mission"].shape[0], 1)
                self.assertIn("mission_status", infos[0])
            finally:
                vec_env.close()

    def test_world_batch_vec_env_mainline_prefers_facade_batch_step_contract_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/inline_route_transition_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_inline_vec_env_route_transition_scenario(), f, ensure_ascii=True)

            vec_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=False,
                execution_step_runtime_mode="compiled",
                flight_shaping_backend="compiled",
                execution_episode_controller_mainline=True,
            )
            try:
                vec_env.seed(123)
                _ = vec_env.reset()
                original = vec_env._step_execution_episode_controller_mainline_requests

                def _wrapped(requests):
                    result = original(requests)
                    step_result = result.step_results[0]
                    result.rewards = [-42.5]
                    result.terminated = [bool(step_result.terminated)]
                    result.truncated = [bool(step_result.truncated)]
                    result.status_vectors = [[9.0, 8.0, 7.0, 6.0]]
                    result.termination_reasons = ["facade_contract_reason"]
                    result.reward_breakdown_jsons = ['{"facade_bonus": 3.25, "total": -42.5}']
                    step_info_inputs = ef_py.StepInfoInputs()
                    step_info_inputs.on_runway = False
                    step_info_inputs.gear_collapsed = True
                    step_info_inputs.gear_stress = 12.5
                    step_info_inputs.alt_agl_m = 0.0
                    step_info_inputs.on_ground_alt_threshold_m = 2.5
                    step_info_inputs.airborne_alt_threshold_m = 5.0
                    step_info_inputs.has_runway_frame = True
                    step_info_inputs.runway_frame.valid = True
                    step_info_inputs.runway_frame.cross_m = 123.0
                    step_info_inputs.runway_frame.along_m = 456.0
                    step_info_inputs.runway_frame.length_m = 2000.0
                    step_info_inputs.runway_frame.width_m = 50.0
                    step_info_inputs.runway_width_margin_m = 2.0
                    step_info_inputs.runway_length_margin_m = 0.0
                    step_info = ef_py.compute_step_info_runtime(step_info_inputs)
                    result.step_infos = [step_info]
                    result.step_info_valid_flags = [True]
                    result.controller_state_changed_flags = [bool(step_result.structural_state_changed)]
                    return result

                vec_env._step_execution_episode_controller_mainline_requests = _wrapped
                _obs, rewards, dones, infos = vec_env.step(np.zeros((1, 17), dtype=np.float32))

                self.assertFalse(bool(dones[0]))
                self.assertAlmostEqual(float(rewards[0]), -42.5, places=6)
                self.assertTrue(
                    np.allclose(
                        np.asarray(infos[0]["mission_status"], dtype=np.float32),
                        np.asarray([9.0, 8.0, 7.0, 6.0], dtype=np.float32),
                        atol=1.0e-6,
                    )
                )
                self.assertEqual(str(infos[0]["termination_reason"]), "facade_contract_reason")
                self.assertAlmostEqual(float(infos[0]["reward_terms"]["facade_bonus"]), 3.25, places=6)
                self.assertAlmostEqual(float(infos[0]["reward_terms"]["total"]), -42.5, places=6)
                self.assertEqual(float(infos[0]["on_runway"]), 0.0)
                self.assertEqual(float(infos[0]["gear_collapsed"]), 1.0)
                self.assertAlmostEqual(float(infos[0]["gear_stress"]), 12.5, places=6)
                self.assertEqual(float(infos[0]["on_ground"]), 1.0)
                self.assertEqual(float(infos[0]["on_runway_geom"]), 0.0)
                self.assertAlmostEqual(float(infos[0]["runway_cross_m"]), 123.0, places=6)
                self.assertAlmostEqual(float(infos[0]["runway_along_m"]), 456.0, places=6)
            finally:
                vec_env.close()

    def test_world_batch_vec_env_matches_multi_timescale_action_wrapper(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_data = _inline_vec_env_scenario()
            scenario_data["meta"]["max_steps"] = 3
            scenario_path = f"{tmpdir}/inline_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(scenario_data, f, ensure_ascii=True)

            wrapper_kwargs = {
                "hold_steps": 4,
                "low_freq_indices": [4, 5, 6, 9, 12, 13, 14, 15, 16],
                "snap_binary_indices": [4, 9, 12, 13, 14, 15],
                "binary_hysteresis_indices": [4, 9, 12, 13, 14, 15],
                "binary_on_threshold": 0.75,
                "binary_off_threshold": 0.25,
                "binary_initial_values": {"4": 1.0, "9": 0.0, "12": 0.0, "13": 0.0, "14": 0.0, "15": 0.0},
                "center_deadband_indices": [5, 6, 7, 8],
                "center_deadband_center": 0.5,
                "center_deadband_half_width": 0.18,
                "scripted_baseline_mode": "stable_flight",
                "scripted_residual_scale": 0.0,
                "action_rate_penalty_coef": 0.0002,
            }
            direct_env = MultiTimescaleActionWrapper(
                UniversalEnv(
                    scenario_path=scenario_path,
                    include_visual=False,
                    include_proprio=True,
                    action_mode="full",
                    mission_obs_mode="basic",
                ),
                **wrapper_kwargs,
            )
            vec_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                action_wrapper_kwargs=wrapper_kwargs,
            )
            try:
                direct_obs, _direct_info = direct_env.reset(seed=123)
                vec_env.seed(123)
                vec_obs = vec_env.reset()
                for key in ("contacts", "rwr", "mission", "proprio"):
                    self.assertTrue(
                        np.allclose(np.asarray(direct_obs[key]), np.asarray(vec_obs[key][0]), atol=1.0e-5),
                        msg=f"reset mismatch for key={key}",
                    )

                action = np.full((17,), 0.9, dtype=np.float32)
                direct_obs_1, direct_reward_1, direct_done_1, direct_trunc_1, direct_info_1 = direct_env.step(action)
                vec_obs_1, vec_rew_1, vec_done_1, vec_info_1 = vec_env.step(action.reshape(1, -1))
                self.assertFalse(bool(direct_done_1 or direct_trunc_1))
                self.assertFalse(bool(vec_done_1[0]))
                for key in ("contacts", "rwr", "mission", "proprio"):
                    self.assertTrue(
                        np.allclose(np.asarray(direct_obs_1[key]), np.asarray(vec_obs_1[key][0]), atol=1.0e-5),
                        msg=f"step1 mismatch for key={key}",
                    )
                self.assertAlmostEqual(float(direct_reward_1), float(vec_rew_1[0]), places=5)
                self.assertTrue(
                    np.allclose(
                        np.asarray(direct_info_1["effective_action"], dtype=np.float32),
                        np.asarray(vec_info_1[0]["effective_action"], dtype=np.float32),
                        atol=1.0e-6,
                    )
                )

                direct_obs_2, direct_reward_2, direct_done_2, direct_trunc_2, direct_info_2 = direct_env.step(action)
                vec_obs_2, vec_rew_2, vec_done_2, vec_info_2 = vec_env.step(action.reshape(1, -1))
                self.assertTrue(
                    np.allclose(
                        np.asarray(direct_info_2["effective_action"], dtype=np.float32),
                        np.asarray(vec_info_2[0]["effective_action"], dtype=np.float32),
                        atol=1.0e-6,
                    )
                )
            finally:
                direct_env.close()
                vec_env.close()

    def test_world_batch_vec_env_cuda_bridge_uses_device_rollout_buffer(self) -> None:
        if not torch.cuda.is_available():
            self.skipTest("CUDA is not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_data = _inline_vec_env_scenario()
            scenario_data["meta"]["max_steps"] = 2
            scenario_path = f"{tmpdir}/inline_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(scenario_data, f, ensure_ascii=True)

            vec_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=2,
                include_visual=False,
                include_proprio=False,
                batch_observation_backend="gpu_host",
                policy_observation_torch_bridge=True,
            )
            try:
                model = AdaptiveKLPPO(
                    "MultiInputPolicy",
                    vec_env,
                    n_steps=2,
                    batch_size=4,
                    n_epochs=1,
                    learning_rate=3.0e-4,
                    gamma=0.99,
                    gae_lambda=0.95,
                    ent_coef=0.0,
                    vf_coef=0.5,
                    max_grad_norm=0.5,
                    device="cuda",
                    verbose=0,
                )
                self.assertIsInstance(model.rollout_buffer, DeviceDictRolloutBuffer)
                model.learn(total_timesteps=4)
                self.assertTrue(torch.is_tensor(model.rollout_buffer.observations["instruments"]))
                self.assertEqual(model.rollout_buffer.observations["instruments"].device.type, "cuda")
            finally:
                vec_env.close()

    def test_world_batch_vec_env_observation_return_mode_view_shares_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_data = _inline_vec_env_scenario()
            scenario_data["meta"]["max_steps"] = 2
            scenario_path = f"{tmpdir}/inline_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(scenario_data, f, ensure_ascii=True)

            vec_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=2,
                include_visual=False,
                include_proprio=True,
                observation_return_mode="view",
            )
            try:
                obs = vec_env.reset()
                self.assertTrue(np.shares_memory(obs["instruments"], vec_env.buf_obs["instruments"]))
                self.assertTrue(np.shares_memory(obs["proprio"], vec_env.buf_obs["proprio"]))

                obs, _rewards, _dones, _infos = vec_env.step(np.zeros((2, 17), dtype=np.float32))
                self.assertTrue(np.shares_memory(obs["instruments"], vec_env.buf_obs["instruments"]))
                self.assertTrue(np.shares_memory(obs["proprio"], vec_env.buf_obs["proprio"]))

                _obs, _rewards, dones, infos = vec_env.step(np.zeros((2, 17), dtype=np.float32))
                self.assertTrue(np.all(dones == np.asarray([True, True])))
                self.assertFalse(np.shares_memory(infos[0]["terminal_observation"]["instruments"], vec_env.buf_obs["instruments"][0]))
                self.assertFalse(np.shares_memory(infos[0]["terminal_observation"]["proprio"], vec_env.buf_obs["proprio"][0]))
            finally:
                vec_env.close()

    def test_world_batch_vec_env_observation_return_mode_copy_detaches_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_data = _inline_vec_env_scenario()
            scenario_data["meta"]["max_steps"] = 2
            scenario_path = f"{tmpdir}/inline_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(scenario_data, f, ensure_ascii=True)

            vec_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=2,
                include_visual=False,
                include_proprio=True,
            )
            try:
                obs = vec_env.reset()
                self.assertFalse(np.shares_memory(obs["instruments"], vec_env.buf_obs["instruments"]))
                self.assertFalse(np.shares_memory(obs["proprio"], vec_env.buf_obs["proprio"]))

                obs, _rewards, _dones, _infos = vec_env.step(np.zeros((2, 17), dtype=np.float32))
                self.assertFalse(np.shares_memory(obs["instruments"], vec_env.buf_obs["instruments"]))
                self.assertFalse(np.shares_memory(obs["proprio"], vec_env.buf_obs["proprio"]))
            finally:
                vec_env.close()


class VecEnvAdapterTests(unittest.TestCase):
    def test_returns_shared_observation_views(self):
        vec_env = SharedMemorySubprocVecEnv(
            [lambda env_id=i: CounterDictEnv(env_id) for i in range(2)],
            start_method="forkserver",
        )
        try:
            obs = vec_env.reset()
            self.assertEqual(obs["vec"].shape, (2, 3))
            self.assertEqual(obs["mat"].shape, (2, 2, 2))
            self.assertTrue(np.shares_memory(obs["vec"], vec_env.buf_obs["vec"]))
            self.assertTrue(np.allclose(obs["vec"][:, 1], np.asarray([0.0, 0.0], dtype=np.float32)))

            obs, rewards, dones, infos = vec_env.step(np.zeros((2, 1), dtype=np.float32))
            self.assertTrue(np.allclose(rewards, np.asarray([1.0, 1.0], dtype=np.float32)))
            self.assertTrue(np.all(dones == np.asarray([False, False])))
            self.assertTrue(np.allclose(obs["vec"][:, 1], np.asarray([1.0, 1.0], dtype=np.float32)))
            self.assertEqual(infos[0]["count"], 1)

            obs, rewards, dones, infos = vec_env.step(np.zeros((2, 1), dtype=np.float32))
            self.assertTrue(np.all(dones == np.asarray([True, True])))
            self.assertTrue(np.allclose(rewards, np.asarray([2.0, 2.0], dtype=np.float32)))
            self.assertTrue(np.allclose(obs["vec"][:, 1], np.asarray([0.0, 0.0], dtype=np.float32)))
            self.assertEqual(infos[0]["terminal_observation"]["vec"][1], 2.0)
            self.assertEqual(infos[1]["terminal_observation"]["vec"][1], 2.0)
        finally:
            vec_env.close()

    def test_world_batch_vec_env_reports_timing_breakdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_data = _inline_vec_env_scenario()
            scenario_data["meta"]["max_steps"] = 2
            scenario_path = f"{tmpdir}/inline_scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(scenario_data, f, ensure_ascii=True)

            vec_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=2,
                include_visual=False,
                include_proprio=False,
                collect_step_timing=True,
            )
            try:
                _ = vec_env.reset()
                self.assertIn("timing", vec_env.reset_infos[0])
                self.assertTrue(
                    "layout_build_ms" in vec_env.reset_infos[0]["timing"]
                    or "batch_setup_ms" in vec_env.reset_infos[0]["timing"]
                )
                self.assertIn("total_ms", vec_env.reset_infos[0]["timing"])

                _obs, _rewards, _dones, infos = vec_env.step(np.zeros((2, 17), dtype=np.float32))
                self.assertIn("timing", infos[0])
                self.assertIn("batch_step_ms", infos[0]["timing"])
                self.assertIn("command_sync_ms", infos[0]["timing"])
                self.assertIn("total_ms", infos[0]["timing"])
            finally:
                vec_env.close()


if __name__ == "__main__":
    unittest.main()
