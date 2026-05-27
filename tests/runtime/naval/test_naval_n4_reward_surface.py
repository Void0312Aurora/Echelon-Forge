from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from gym_envs.universal_env import UniversalEnv  # noqa: E402
from python.rl.runtime.world_batch_vec_env import WorldBatchVecEnv  # noqa: E402
from python.rl.runtime.cooperative_world_batch_vec_env import CooperativeWorldBatchVecEnv  # noqa: E402
from python.rl.runtime.leader_world_batch_runtime import LeaderWorldBatchExecutionRuntimeGroup  # noqa: E402
from python.rl.runtime.single_world_batch_runtime import build_single_world_batch_execution_runtime  # noqa: E402
from python.mission_obs_taxonomy import (  # noqa: E402
    mission_observation_dim,
    mission_observation_field_index,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
N4_SCENARIO = REPO_ROOT / "scenarios" / "naval" / "ddg51_take1_screen_threat_roe_v1.json"


class NavalN4RewardSurfaceTests(unittest.TestCase):
    def _naval_world_batch_settings(self) -> dict:
        return {
            "include_visual": False,
            "include_proprio": True,
            "action_mode": "naval_station3",
            "mission_obs_mode": "naval_screen_station_v1",
            "step_info_mode": "full",
            "execution_step_runtime_mode": "compiled",
            "flight_shaping_backend": "compiled",
            "batch_observation_backend": "compiled",
            "batch_visual_backend": "compiled",
        }

    def _make_env(self, *, action_mode: str = "naval_station3", scenario_path: str | Path | None = None) -> WorldBatchVecEnv:
        settings = self._naval_world_batch_settings()
        settings["action_mode"] = action_mode
        return WorldBatchVecEnv(
            scenario_path=str(scenario_path or N4_SCENARIO),
            n_envs=1,
            worker_threads=1,
            policy_observation_torch_bridge=True,
            observation_return_mode="copy",
            **settings,
        )

    def _single_slot_n4_scenario_path(self, tmpdir: str) -> str:
        scenario = json.loads(N4_SCENARIO.read_text(encoding="utf-8"))
        roster = dict(scenario.get("cooperative_roster", {}) or {})
        members = list(roster.get("members", []) or [])
        roster["members"] = [dict(members[0])] if members else [
            {"entity": "Blue_Screen_DDG51", "is_agent": True}
        ]
        roster["members"][0]["is_agent"] = True
        scenario["cooperative_roster"] = roster
        scenario_path = Path(tmpdir) / "single_slot_n4.json"
        scenario_path.write_text(json.dumps(scenario, ensure_ascii=True), encoding="utf-8")
        return str(scenario_path)

    def _full_roster_n4_scenario_path(self) -> str:
        return str(N4_SCENARIO)

    def _derived_n4_scenario_path(self, tmpdir: str, mutator) -> str:
        scenario = json.loads(N4_SCENARIO.read_text(encoding="utf-8"))
        mutator(scenario)
        scenario_path = Path(tmpdir) / "derived_n4.json"
        scenario_path.write_text(json.dumps(scenario, ensure_ascii=True), encoding="utf-8")
        return str(scenario_path)

    def _offset_ddg_station_radius(self, scenario: dict, offset_m: float) -> None:
        task = dict(scenario.get("task_order", {}) or {})
        station_radius_m = float(task.get("station_radius_m", 0.0)) + float(offset_m)
        heading_rad = math.radians(float(task.get("station_heading_deg", 0.0)))
        entities = list(scenario.get("entities", []) or [])
        ref = next(entity for entity in entities if entity.get("name") == "Blue_HVU_TAKE1")
        ddg = next(entity for entity in entities if entity.get("name") == "Blue_Screen_DDG51")
        ref_pos = list(ref.get("pos", [0.0, 0.0, 0.0]))
        ddg["pos"] = [
            float(ref_pos[0]) + math.sin(heading_rad) * station_radius_m,
            float(ref_pos[1]) + math.cos(heading_rad) * station_radius_m,
            0.0,
        ]

    def _make_coop_env(self, scenario_path: str, *, action_mode: str = "naval_station3") -> CooperativeWorldBatchVecEnv:
        settings = self._naval_world_batch_settings()
        settings["action_mode"] = action_mode
        return CooperativeWorldBatchVecEnv(
            scenario_path=scenario_path,
            n_envs=1,
            worker_threads=1,
            **settings,
        )

    def test_n4_reward_surface_does_not_emit_airfield_penalty(self) -> None:
        env = self._make_env()
        try:
            env.reset()
            action = np.array([[0.0, 0.0, 0.0]], dtype=np.float32)
            _obs, rewards, dones, infos = env.step(action)
            info = dict(infos[0])
            terms = dict(info.get("reward_terms", {}) or {})

            self.assertFalse(bool(dones[0]))
            self.assertTrue(np.isfinite(float(rewards[0])))
            self.assertNotIn("off_runway_penalty", terms)
            self.assertNotIn("naval_off_runway_penalty_suppressed", terms)
            self.assertNotIn("speed_reward", terms)
            self.assertNotIn("roll_stability", terms)
            self.assertIn("naval_station_error_penalty", terms)
            self.assertIn("naval_screen_separation_penalty", terms)
            self.assertIn("naval_pre_fire_roe_hold_bonus", terms)
            self.assertGreater(float(rewards[0]), -1.0)

            mission_status = np.asarray(info.get("mission_status", []), dtype=np.float32).reshape(-1)
            self.assertGreaterEqual(mission_status.size, 4)
            self.assertGreaterEqual(float(mission_status[0]), 0.0)
            for key in (
                "on_runway",
                "on_runway_geom",
                "runway_cross_m",
                "runway_along_m",
                "gear_collapsed",
                "gear_stress",
            ):
                self.assertNotIn(key, info)
        finally:
            env.close()

    def test_n4_naval_reward_surface_rejects_off_runway_suppression_regression(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            def _enable_suppression(scenario: dict) -> None:
                rewards = dict(scenario.get("rewards", {}) or {})
                rewards["naval_suppress_off_runway_penalty"] = True
                scenario["rewards"] = rewards

            scenario_path = self._derived_n4_scenario_path(tmpdir, _enable_suppression)
            env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=1,
                include_visual=False,
                include_proprio=True,
                action_mode="naval_station3",
                mission_obs_mode="naval_screen_station_v1",
                step_info_mode="full",
                execution_step_runtime_mode="compiled",
                flight_shaping_backend="compiled",
                worker_threads=1,
                batch_observation_backend="compiled",
                batch_visual_backend="compiled",
            )
            try:
                env.reset()
                with self.assertRaisesRegex(RuntimeError, "naval_suppress_off_runway_penalty is retired"):
                    env.step(np.zeros((1, 3), dtype=np.float32))
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

    def test_n4_naval_policy_instruments_filter_aircraft_specific_fields(self) -> None:
        env = self._make_env()
        try:
            obs = env.reset()
            inst = np.asarray(obs["instruments"][0], dtype=np.float32)
            self.assertGreaterEqual(inst.size, 42)

            aircraft_specific_indices = (
                0,   # IAS
                1,   # Mach
                2,   # barometric altitude
                3,   # radar altitude
                4,   # vertical speed
                5,   # AOA
                6,   # beta
                7,   # pitch
                10,  # G load
                18,  # gear
                19,  # flaps
                20,  # speedbrake
                38,  # ILS valid
                39,  # ILS localizer
                40,  # ILS glideslope
                41,  # ILS DME
            )
            for idx in aircraft_specific_indices:
                self.assertEqual(float(inst[idx]), 0.0, f"instrument index {idx} should be filtered")

            self.assertNotEqual(float(inst[9]), 0.0)
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

    def test_naval_station3_tiny_action_deadband_keeps_station_order_neutral(self) -> None:
        env = self._make_env()
        try:
            env.reset()
            handle = env._handles[0]
            task = handle.loader.task_order
            base_radius = float(getattr(task, "station_radius_m", 0.0))
            base_heading = float(getattr(task, "station_heading_deg", 0.0))
            base_speed = float(getattr(task, "target_speed_mps", 0.0))

            tiny_action = np.array([[0.004, -0.004, 0.004]], dtype=np.float32)
            for _ in range(20):
                obs, rewards, dones, infos = env.step(tiny_action)
                self.assertFalse(bool(dones[0]))
                self.assertTrue(np.isfinite(float(rewards[0])))
                self.assertTrue(np.allclose(np.asarray(obs["proprio"][0], dtype=np.float32), 0.0))
                terms = dict(infos[0].get("reward_terms", {}) or {})
                self.assertNotIn("naval_station_action_bearing_penalty", terms)
                self.assertNotIn("naval_station_action_radius_penalty", terms)
                self.assertNotIn("naval_station_action_speed_penalty", terms)

            task_after = handle.loader.task_order
            self.assertAlmostEqual(float(getattr(task_after, "station_heading_deg", 0.0)), base_heading)
            self.assertAlmostEqual(float(getattr(task_after, "station_radius_m", 0.0)), base_radius)
            self.assertAlmostEqual(float(getattr(task_after, "target_speed_mps", 0.0)), base_speed, delta=1.0e-5)
            self.assertTrue(np.allclose(np.asarray(handle.loader._naval_station3_last_action), 0.0))
            self.assertTrue(np.allclose(np.asarray(handle.last_action, dtype=np.float32), 0.0))
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

    def test_naval_station3_action_cannot_move_reward_reference_to_ownship(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = self._derived_n4_scenario_path(
                tmpdir,
                lambda scenario: self._offset_ddg_station_radius(scenario, -1800.0),
            )

            zero_env = self._make_env(scenario_path=scenario_path)
            action_env = self._make_env(scenario_path=scenario_path)
            try:
                zero_env.reset()
                _zero_obs, zero_rewards, _zero_dones, zero_infos = zero_env.step(
                    np.array([[0.0, 0.0, 0.0]], dtype=np.float32)
                )
                action_env.reset()
                _obs, rewards, _dones, infos = action_env.step(
                    np.array([[0.0, -1.0, 0.0]], dtype=np.float32)
                )

                terms = dict(infos[0].get("reward_terms", {}) or {})
                status = np.asarray(infos[0].get("mission_status", []), dtype=np.float32).reshape(-1)

                self.assertGreater(float(status[0]), 1700.0)
                self.assertNotIn("naval_station_band_bonus", terms)
                self.assertLess(float(rewards[0]), float(zero_rewards[0]))
                self.assertLess(float(terms.get("naval_station_action_radius_penalty", 0.0)), 0.0)
            finally:
                zero_env.close()
                action_env.close()

    def test_n4_world_batch_rejects_air_action_mode_for_naval_profile(self) -> None:
        env = self._make_env(action_mode="takeoff4")
        try:
            with self.assertRaisesRegex(RuntimeError, "Naval tasking profiles require action_mode='naval_station3'"):
                env.reset()
        finally:
            env.close()

    def test_n4_cooperative_batch_rejects_air_action_mode_for_naval_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = self._single_slot_n4_scenario_path(tmpdir)
            env = self._make_coop_env(scenario_path, action_mode="takeoff4")
            try:
                with self.assertRaisesRegex(RuntimeError, "Naval tasking profiles require action_mode='naval_station3'"):
                    env.reset()
            finally:
                env.close()

    def test_n4_cooperative_batch_naval_station3_updates_station_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = self._single_slot_n4_scenario_path(tmpdir)
            env = self._make_coop_env(scenario_path)
            try:
                env.reset()
                slot_state = env._slots[0]
                self.assertIsNotNone(slot_state)
                task = slot_state.loader.task_order
                base_radius = float(getattr(task, "station_radius_m", 0.0))
                base_heading = float(getattr(task, "station_heading_deg", 0.0))

                _obs, _rewards, _dones, _infos = env.step(np.array([[0.5, -0.5, 0.25]], dtype=np.float32))
                task_after = slot_state.loader.task_order

                self.assertAlmostEqual(float(getattr(task_after, "station_heading_deg", 0.0)), base_heading + 12.5)
                self.assertAlmostEqual(float(getattr(task_after, "station_radius_m", 0.0)), base_radius - 900.0)
                self.assertEqual(tuple(np.asarray(slot_state.last_action, dtype=np.float32).shape), (3,))
            finally:
                env.close()

    def test_n4_cooperative_batch_action_cannot_move_reward_reference_to_ownship(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = self._derived_n4_scenario_path(
                tmpdir,
                lambda scenario: self._offset_ddg_station_radius(scenario, -1800.0),
            )
            zero_env = self._make_coop_env(scenario_path)
            action_env = self._make_coop_env(scenario_path)
            try:
                zero_env.reset()
                _zero_obs, zero_rewards, _zero_dones, _zero_infos = zero_env.step(
                    np.array([[0.0, 0.0, 0.0]], dtype=np.float32)
                )
                action_env.reset()
                _obs, rewards, _dones, infos = action_env.step(
                    np.array([[0.0, -1.0, 0.0]], dtype=np.float32)
                )
                terms = dict(infos[0].get("reward_terms", {}) or {})
                status = np.asarray(infos[0].get("mission_status", []), dtype=np.float32).reshape(-1)

                self.assertGreater(float(status[0]), 1700.0)
                self.assertNotIn("naval_station_band_bonus", terms)
                self.assertLess(float(rewards[0]), float(zero_rewards[0]))
            finally:
                zero_env.close()
                action_env.close()

    def test_n4_cooperative_batch_naval_station3_tiny_action_deadband_updates_proprio(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = self._single_slot_n4_scenario_path(tmpdir)
            env = self._make_coop_env(scenario_path)
            try:
                env.reset()
                slot_state = env._slots[0]
                self.assertIsNotNone(slot_state)

                obs, _rewards, _dones, _infos = env.step(np.array([[0.004, -0.004, 0.004]], dtype=np.float32))

                self.assertTrue(np.allclose(np.asarray(obs["proprio"][0], dtype=np.float32), 0.0))
                self.assertTrue(np.allclose(np.asarray(slot_state.last_action, dtype=np.float32), 0.0))
                self.assertTrue(np.allclose(np.asarray(slot_state.loader._naval_station3_last_action), 0.0))
            finally:
                env.close()

    def test_n4_cooperative_batch_keeps_non_agent_support_roster_without_policy_slot(self) -> None:
        env = self._make_coop_env(self._full_roster_n4_scenario_path())
        try:
            obs = env.reset()
            self.assertEqual(int(env.slots_per_world), 1)
            self.assertEqual(int(env.num_envs), 1)
            self.assertEqual(tuple(np.asarray(obs["proprio"], dtype=np.float32).shape), (1, 3))

            slot_state = env._slots[0]
            self.assertIsNotNone(slot_state)
            self.assertEqual(str(slot_state.entity_name), "Blue_Screen_DDG51")
            self.assertEqual(int(slot_state.control_slot.roster_index), 0)
            roster = list(slot_state.loader.active_roster)
            self.assertEqual(len(roster), 2)
            self.assertEqual([(str(member.entity_name), bool(member.is_agent)) for member in roster], [
                ("Blue_Screen_DDG51", True),
                ("Blue_HVU_TAKE1", False),
            ])
            self.assertEqual(int(roster[1].reference_entity_id), int(slot_state.entity_id))

            last_terms: dict[str, float] = {}
            for _ in range(8):
                _obs, rewards, dones, infos = env.step(np.array([[0.0, 0.0, 0.0]], dtype=np.float32))
                self.assertFalse(bool(dones[0]))
                self.assertTrue(np.isfinite(float(rewards[0])))
                last_terms = dict(infos[0].get("reward_terms", {}) or {})
            self.assertIn("naval_contact_maintained_bonus", last_terms)
            self.assertIn("naval_shared_track_bonus", last_terms)
        finally:
            env.close()

    def test_n4_raw_universal_env_compat_naval_station3_tiny_action_deadband_updates_proprio(self) -> None:
        env = UniversalEnv(
            str(N4_SCENARIO),
            include_visual=False,
            include_proprio=True,
            action_mode="naval_station3",
            mission_obs_mode="naval_screen_station_v1",
            step_info_mode="full",
            execution_step_runtime_mode="compiled",
            flight_shaping_backend="compiled",
            runtime_compatibility_enabled=True,
        )
        try:
            env.reset(seed=7)

            obs, _reward, _terminated, _truncated, info = env.step(
                np.array([0.004, -0.004, 0.004], dtype=np.float32)
            )

            self.assertTrue(np.allclose(np.asarray(obs["proprio"], dtype=np.float32), 0.0))
            self.assertTrue(np.allclose(np.asarray(env._last_action, dtype=np.float32), 0.0))
            self.assertTrue(np.allclose(np.asarray(env.loader._naval_station3_last_action), 0.0))
            action_terms = {
                key: value
                for key, value in dict(info.get("reward_terms", {}) or {}).items()
                if "naval_station_action" in str(key)
            }
            self.assertEqual(action_terms, {})
        finally:
            env.close()

    def test_n4_single_world_runtime_naval_station3_tiny_action_deadband_updates_proprio(self) -> None:
        runtime = build_single_world_batch_execution_runtime(
            scenario_path=str(N4_SCENARIO),
            env_settings=self._naval_world_batch_settings(),
            worker_threads=1,
        )
        try:
            runtime.reset(seed=11)

            obs, _reward, _terminated, _truncated, info = runtime.step(
                np.array([0.004, -0.004, 0.004], dtype=np.float32)
            )
            handle = runtime.access.state(0)

            self.assertTrue(np.allclose(np.asarray(obs["proprio"], dtype=np.float32), 0.0))
            self.assertTrue(np.allclose(np.asarray(handle.last_action, dtype=np.float32), 0.0))
            self.assertTrue(np.allclose(np.asarray(handle.loader._naval_station3_last_action), 0.0))
            action_terms = {
                key: value
                for key, value in dict(info.get("reward_terms", {}) or {}).items()
                if "naval_station_action" in str(key)
            }
            self.assertEqual(action_terms, {})
        finally:
            runtime.close()

    def test_n4_leader_runtime_naval_station3_tiny_action_deadband_updates_proprio(self) -> None:
        env = self._make_env()
        try:
            env.seed(13)
            env.reset()
            group = LeaderWorldBatchExecutionRuntimeGroup(env)

            results = group.step_indices([0], [np.array([0.004, -0.004, 0.004], dtype=np.float32)])
            obs, _reward, _terminated, _truncated, info = results[0]
            handle = group.access.state(0)

            self.assertTrue(np.allclose(np.asarray(obs["proprio"], dtype=np.float32), 0.0))
            self.assertTrue(np.allclose(np.asarray(handle.last_action, dtype=np.float32), 0.0))
            self.assertTrue(np.allclose(np.asarray(handle.loader._naval_station3_last_action), 0.0))
            action_terms = {
                key: value
                for key, value in dict(info.get("reward_terms", {}) or {}).items()
                if "naval_station_action" in str(key)
            }
            self.assertEqual(action_terms, {})
        finally:
            env.close()


if __name__ == "__main__":
    unittest.main()
