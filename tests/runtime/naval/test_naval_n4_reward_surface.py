from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from python.rl.runtime.world_batch_vec_env import WorldBatchVecEnv  # noqa: E402
from python.mission_obs_taxonomy import (  # noqa: E402
    mission_observation_dim,
    mission_observation_field_index,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
N4_SCENARIO = REPO_ROOT / "scenarios" / "naval" / "ddg51_take1_screen_threat_roe_v1.json"


class NavalN4RewardSurfaceTests(unittest.TestCase):
    def _make_env(self, *, action_mode: str = "naval_station3") -> WorldBatchVecEnv:
        return WorldBatchVecEnv(
            scenario_path=str(N4_SCENARIO),
            n_envs=1,
            include_visual=False,
            include_proprio=True,
            action_mode=action_mode,
            mission_obs_mode="naval_screen_station_v1",
            step_info_mode="full",
            execution_step_runtime_mode="compiled",
            flight_shaping_backend="compiled",
            worker_threads=1,
            batch_observation_backend="compiled",
            batch_visual_backend="compiled",
            policy_observation_torch_bridge=True,
            observation_return_mode="copy",
        )

    def test_n4_reward_surface_replaces_airfield_penalty_with_naval_terms(self) -> None:
        env = self._make_env()
        try:
            env.reset()
            action = np.array([[0.0, 0.0, 0.0]], dtype=np.float32)
            _obs, rewards, dones, infos = env.step(action)
            info = dict(infos[0])
            terms = dict(info.get("reward_terms", {}) or {})

            self.assertFalse(bool(dones[0]))
            self.assertTrue(np.isfinite(float(rewards[0])))
            self.assertEqual(float(terms.get("off_runway_penalty", 0.0)), -1.0)
            self.assertEqual(float(terms.get("naval_off_runway_penalty_suppressed", 0.0)), 1.0)
            self.assertIn("naval_station_error_penalty", terms)
            self.assertIn("naval_screen_separation_penalty", terms)
            self.assertIn("naval_pre_fire_roe_hold_bonus", terms)
            self.assertGreater(float(rewards[0]), -1.0)

            mission_status = np.asarray(info.get("mission_status", []), dtype=np.float32).reshape(-1)
            self.assertGreaterEqual(mission_status.size, 4)
            self.assertGreaterEqual(float(mission_status[0]), 0.0)
        finally:
            env.close()

    def test_n4_naval_observation_uses_station_contact_and_roe_fields(self) -> None:
        mode = "naval_screen_station_v1"
        env = self._make_env()
        try:
            obs = env.reset()
            mission = np.asarray(obs["mission"][0], dtype=np.float32)

            self.assertEqual(tuple(mission.shape), (mission_observation_dim(mode),))
            self.assertAlmostEqual(
                float(mission[mission_observation_field_index(mode, "station_radius_m")]),
                14816.0,
                delta=1.0e-3,
            )
            self.assertAlmostEqual(
                float(mission[mission_observation_field_index(mode, "station_bearing_deg")]),
                90.0,
                delta=1.0e-3,
            )
            self.assertLess(float(mission[mission_observation_field_index(mode, "station_error_m")]), 1.0)
            self.assertAlmostEqual(
                float(mission[mission_observation_field_index(mode, "screen_separation_m")]),
                14816.0,
                delta=1.0e-3,
            )
            self.assertEqual(float(mission[mission_observation_field_index(mode, "roe_state")]), 1.0)
            self.assertEqual(float(mission[mission_observation_field_index(mode, "authorization_to_fire")]), 0.0)
            self.assertGreater(float(mission[mission_observation_field_index(mode, "assigned_target_id")]), 0.0)
            self.assertEqual(float(mission[mission_observation_field_index(mode, "self_role_code")]), 11.0)
            self.assertEqual(float(mission[mission_observation_field_index(mode, "relative_slot_code")]), 11.0)

            obs_after, _rewards, _dones, _infos = env.step(np.array([[0.5, -0.5, 0.25]], dtype=np.float32))
            mission_after = np.asarray(obs_after["mission"][0], dtype=np.float32)
            self.assertAlmostEqual(
                float(mission_after[mission_observation_field_index(mode, "station_bearing_deg")]),
                102.5,
                delta=1.0e-3,
            )
            self.assertAlmostEqual(
                float(mission_after[mission_observation_field_index(mode, "station_radius_m")]),
                13916.0,
                delta=1.0e-3,
            )
            self.assertGreater(float(mission_after[mission_observation_field_index(mode, "station_error_m")]), 1000.0)
            self.assertEqual(float(mission_after[mission_observation_field_index(mode, "target_contact_present")]), 1.0)
        finally:
            env.close()

    def test_n4_naval_observation_reports_support_chain_when_seen(self) -> None:
        mode = "naval_screen_station_v1"
        env = self._make_env()
        try:
            obs = env.reset()
            support_track = 0.0
            report_chain = 0.0
            for _ in range(8):
                obs, _rewards, _dones, _infos = env.step(np.array([[0.0, 0.0, 0.0]], dtype=np.float32))
                mission = np.asarray(obs["mission"][0], dtype=np.float32)
                support_track = float(mission[mission_observation_field_index(mode, "support_track_present")])
                report_chain = float(mission[mission_observation_field_index(mode, "report_chain_seen")])
                if support_track > 0.0 or report_chain > 0.0:
                    break

            self.assertGreaterEqual(support_track, 1.0)
            self.assertGreaterEqual(report_chain, 0.5)
        finally:
            env.close()

    def test_n4_contact_and_report_terms_appear_after_contact_chain(self) -> None:
        env = self._make_env()
        try:
            env.reset()
            action = np.array([[0.0, 0.0, 0.0]], dtype=np.float32)
            last_terms: dict[str, float] = {}
            for _ in range(80):
                _obs, _rewards, _dones, infos = env.step(action)
                last_terms = dict(infos[0].get("reward_terms", {}) or {})
                if "naval_report_chain_bonus" in last_terms:
                    break

            self.assertIn("naval_contact_maintained_bonus", last_terms)
            self.assertIn("naval_shared_track_bonus", last_terms)
            self.assertIn("naval_report_chain_bonus", last_terms)
        finally:
            env.close()

    def test_naval_station3_action_updates_station_order_without_manual_takeover(self) -> None:
        env = self._make_env()
        try:
            env.reset()
            handle = env._handles[0]
            task = handle.loader.task_order
            base_radius = float(getattr(task, "station_radius_m", 0.0))
            base_heading = float(getattr(task, "station_heading_deg", 0.0))

            _obs, _rewards, _dones, infos = env.step(np.array([[0.5, -0.5, 0.25]], dtype=np.float32))
            task_after = handle.loader.task_order

            self.assertAlmostEqual(float(getattr(task_after, "station_heading_deg", 0.0)), base_heading + 12.5)
            self.assertAlmostEqual(float(getattr(task_after, "station_radius_m", 0.0)), base_radius - 900.0)
            self.assertEqual(tuple(np.asarray(handle.last_action, dtype=np.float32).shape), (3,))
            terms = dict(infos[0].get("reward_terms", {}) or {})
            self.assertIn("naval_station_error_penalty", terms)
            self.assertLess(float(terms.get("naval_station_action_bearing_penalty", 0.0)), 0.0)
            self.assertLess(float(terms.get("naval_station_action_radius_penalty", 0.0)), 0.0)
            self.assertLess(float(terms.get("naval_station_action_speed_penalty", 0.0)), 0.0)
        finally:
            env.close()

    def test_naval_station3_zero_action_keeps_station_order_neutral(self) -> None:
        env = self._make_env()
        try:
            env.reset()
            handle = env._handles[0]
            task = handle.loader.task_order
            base_radius = float(getattr(task, "station_radius_m", 0.0))
            base_heading = float(getattr(task, "station_heading_deg", 0.0))
            base_speed = float(getattr(task, "target_speed_mps", 0.0))

            for _ in range(20):
                _obs, rewards, dones, infos = env.step(np.array([[0.0, 0.0, 0.0]], dtype=np.float32))
                self.assertFalse(bool(dones[0]))
                self.assertTrue(np.isfinite(float(rewards[0])))
                terms = dict(infos[0].get("reward_terms", {}) or {})
                self.assertNotIn("naval_station_action_bearing_penalty", terms)
                self.assertNotIn("naval_station_action_radius_penalty", terms)
                self.assertNotIn("naval_station_action_speed_penalty", terms)

            task_after = handle.loader.task_order
            self.assertAlmostEqual(float(getattr(task_after, "station_heading_deg", 0.0)), base_heading)
            self.assertAlmostEqual(float(getattr(task_after, "station_radius_m", 0.0)), base_radius)
            self.assertAlmostEqual(float(getattr(task_after, "target_speed_mps", 0.0)), base_speed, delta=1.0e-5)
        finally:
            env.close()

    def test_naval_station3_needless_order_changes_are_penalized(self) -> None:
        env = self._make_env()
        try:
            env.reset()
            _zero_obs, zero_rewards, _zero_dones, zero_infos = env.step(np.array([[0.0, 0.0, 0.0]], dtype=np.float32))
            zero_terms = dict(zero_infos[0].get("reward_terms", {}) or {})

            env.close()
            env = self._make_env()
            env.reset()
            _obs, rewards, _dones, infos = env.step(np.array([[0.5, -0.5, 0.25]], dtype=np.float32))
            terms = dict(infos[0].get("reward_terms", {}) or {})

            self.assertNotIn("naval_station_action_radius_penalty", zero_terms)
            self.assertAlmostEqual(float(terms.get("naval_station_action_bearing_penalty", 0.0)), -0.04, places=6)
            self.assertAlmostEqual(float(terms.get("naval_station_action_radius_penalty", 0.0)), -0.06, places=6)
            self.assertAlmostEqual(float(terms.get("naval_station_action_speed_penalty", 0.0)), -0.01, places=6)
            self.assertLess(float(rewards[0]), float(zero_rewards[0]))
        finally:
            env.close()

    def test_n4_world_batch_ship_actions_change_motion(self) -> None:
        def run_action(action: np.ndarray) -> tuple[float, float]:
            env = self._make_env(action_mode="takeoff4")
            try:
                env.reset()
                handle = env._handles[0]
                for _ in range(120):
                    _obs, _rewards, _dones, _infos = env.step(action)
                truth = handle.last_truth
                return float(getattr(truth, "heading", 0.0)), float(getattr(truth, "speed", 0.0))
            finally:
                env.close()

        idle_heading, idle_speed = run_action(np.array([[0.0, 0.0, 0.0, 0.0]], dtype=np.float32))
        full_heading, full_speed = run_action(np.array([[0.0, 0.0, 0.0, 1.0]], dtype=np.float32))
        turn_heading, turn_speed = run_action(np.array([[0.0, 0.0, 1.0, 1.0]], dtype=np.float32))

        self.assertGreater(full_speed, idle_speed + 8.0)
        self.assertGreater(turn_speed, idle_speed + 8.0)
        self.assertGreater(abs(turn_heading - full_heading), 20.0)


if __name__ == "__main__":
    unittest.main()
