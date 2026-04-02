from __future__ import annotations

import copy
import math
import unittest

import numpy as np

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402

from gym_envs.scenario_loader import ScenarioLoader  # noqa: E402
from gym_envs.universal_env import build_step_info, build_universal_observation  # noqa: E402


def _legacy_runway_environment() -> dict:
    return {
        "time_step": 0.05,
        "terrain_type": "legacy",
        "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
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
    }


def _lead_entity(*, pos: list[float], vel: list[float], heading: float = 90.0) -> dict:
    return {
        "name": "Lead",
        "type": "Aircraft",
        "side": "Blue",
        "is_agent": True,
        "pos": list(pos),
        "vel": list(vel),
        "heading": float(heading),
    }


def _legacy_runway_scenario(
    *,
    name: str,
    mission_command: dict,
    entity: dict,
    rewards: dict | None = None,
    objectives: list[dict] | None = None,
) -> dict:
    return {
        "scenario_name": str(name),
        "environment": _legacy_runway_environment(),
        "mission_command": copy.deepcopy(mission_command),
        "entities": [copy.deepcopy(entity)],
        "objectives": copy.deepcopy(list(objectives or [])),
        "rewards": copy.deepcopy(dict(rewards or {})),
    }


def _objective_scenario() -> dict:
    return _legacy_runway_scenario(
        name="loader_execution_step_objective_parity",
        mission_command={
            "command_code": 2,
            "target_heading": 90.0,
            "target_altitude": 1200.0,
            "target_speed": 180.0,
        },
        entity=_lead_entity(pos=[-1400.0, 0.0, 1200.0], vel=[0.0, 180.0, 0.0]),
        objectives=[
            {
                "type": "conditional",
                "reward": 75.0,
                "conditions": [{"property": "heading", "op": ">=", "value": 0.0}],
            }
        ],
        rewards={
            "survival": 0.02,
            "success_ground_track_error_penalty_weight": -0.1,
            "success_ground_track_error_deadband_deg": 0.0,
            "success_ground_track_error_norm_deg": 30.0,
            "success_ground_track_error_power": 1.0,
        },
    )


def _route_scenario() -> dict:
    return _legacy_runway_scenario(
        name="loader_execution_step_waypoint_parity",
        mission_command={
            "command_code": 3,
            "target_heading": 90.0,
            "target_altitude": 1200.0,
            "target_speed": 180.0,
            "waypoint_mode": "flyby",
            "waypoints": [
                {"x": -500.0, "y": 0.0, "z": 1200.0, "radius_m": 800.0},
                {"x": 2500.0, "y": 1500.0, "z": 1200.0, "radius_m": 800.0},
            ],
        },
        entity=_lead_entity(pos=[-1400.0, 0.0, 1200.0], vel=[0.0, 180.0, 0.0]),
        rewards={
            "survival": 0.02,
            "waypoint_distance_weight": -0.00004,
            "waypoint_cross_track_weight": -0.35,
            "waypoint_cross_track_deadband_m": 250.0,
            "waypoint_cross_track_norm_m": 1500.0,
            "waypoint_cross_track_power": 1.5,
            "waypoint_cross_track_clip": 2.0,
            "waypoint_reached_bonus": 25.0,
        },
    )


def _approach_scenario() -> dict:
    return {
        "scenario_name": "loader_execution_step_approach_parity",
        "imports": [{"file": "examples/config/prefabs/airbase_large_runway45.json"}],
        "environment": {
            "time_step": 0.05,
            "max_steps": 10,
            "terrain_type": "flat",
            "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
        },
        "mission_command": {
            "command_code": 4,
            "target_heading": 90.0,
            "target_altitude": 0.0,
            "target_speed": 82.0,
            "landing_mode": "ils_final",
            "reference_runway": "Runway 09",
            "threshold_crossing_height_m": 15.0,
        },
        "entities": [
            {
                "name": "Blue_F16",
                "type": "F-16C_Block50",
                "side": "Blue",
                "pos": [-4500.0, 0.0, 172.15775811444114],
                "vel": [82.0, 0.0, 0.0],
                "heading": 90.0,
                "is_agent": True,
            }
        ],
        "objectives": [],
        "rewards": {
            "survival": 0.02,
            "approach_localizer_improve_weight": 2.0,
            "approach_glideslope_improve_weight": 2.0,
            "approach_dme_progress_weight": 1.0,
            "approach_dme_progress_localizer_band": 0.3,
            "approach_dme_progress_glideslope_band": 0.3,
            "approach_capture_bonus": 5.0,
            "approach_capture_localizer_band": 0.3,
            "approach_capture_glideslope_band": 0.3,
        },
    }


def _takeoff_shaping_scenario() -> dict:
    return _legacy_runway_scenario(
        name="loader_execution_step_takeoff_shaping_parity",
        mission_command={
            "command_code": 2,
            "target_heading": 90.0,
            "target_altitude": 1200.0,
            "target_speed": 180.0,
        },
        entity=_lead_entity(pos=[-1100.0, 5.0, 0.0], vel=[90.0, 0.0, 0.0]),
        rewards={
            "survival": 0.02,
            "roll_stability_weight": -0.001,
            "speed_reward_weight": 0.0005,
            "runway_centerline_m_penalty_weight": -0.02,
            "runway_centerline_m_deadband_m": 0.0,
            "runway_centerline_m_norm_m": 5.0,
            "runway_centerline_m_power": 2.0,
            "alignment_reward_weight": 0.2,
        },
    )


class ScenarioLoaderExecutionStepRuntimeParityTests(unittest.TestCase):
    def _run_loader_once(
        self,
        scenario_data: dict,
        *,
        seed: int,
        compiled: bool,
        flight_shaping_backend: str | None = None,
    ) -> dict:
        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))
        loader = ScenarioLoader(sim)
        loader.use_compiled_execution_step_runtime = bool(compiled)
        if flight_shaping_backend is not None:
            loader.set_flight_shaping_backend(flight_shaping_backend)
        agent_id = loader.load_scenario_data(copy.deepcopy(scenario_data), seed=seed)
        self.assertIsNotNone(agent_id)

        truth = sim.get_agent_observation(int(agent_id))
        inst = sim.get_instrument_state(int(agent_id))
        obs = build_universal_observation(
            loader,
            inst,
            truth,
            mission_obs_mode="nav_v2",
            max_contacts=10,
            max_rwr=4,
            include_proprio=False,
            last_action=None,
            action_space=None,
            steps=1,
            max_steps=loader.get_max_steps(),
        )
        reward, terminated, truncated, status = loader.compute_full_step(obs, sim, 1, loader.get_max_steps())
        info = build_step_info(
            loader,
            sim,
            int(agent_id),
            mission_status=status,
            terminated=terminated,
            truncated=truncated,
            inst_now=inst,
            truth_now=truth,
        )
        return {
            "mission_obs": np.asarray(obs["mission"], dtype=np.float32),
            "reward": float(reward),
            "terminated": bool(terminated),
            "truncated": bool(truncated),
            "status": np.asarray(status, dtype=np.float32),
            "step_info": dict(info),
            "reward_breakdown": dict(loader.last_reward_breakdown),
            "termination_reason": str(loader.last_termination_reason),
            "approach_prev_dme_m": loader._approach_prev_dme_m,
            "approach_prev_loc_abs": loader._approach_prev_loc_abs,
            "approach_prev_gs_abs": loader._approach_prev_gs_abs,
            "waypoint_prev_dist_m": loader._waypoint_prev_dist_m,
            "waypoint_idx": int(loader.waypoint_idx),
            "mission_phase_name": str(loader.mission_phase_name),
        }

    def _assert_loader_results_match(self, left: dict, right: dict) -> None:
        self.assertTrue(np.allclose(left["mission_obs"], right["mission_obs"], atol=1.0e-6))
        self.assertAlmostEqual(float(left["reward"]), float(right["reward"]), places=6)
        self.assertEqual(bool(left["terminated"]), bool(right["terminated"]))
        self.assertEqual(bool(left["truncated"]), bool(right["truncated"]))
        self.assertTrue(np.allclose(left["status"], right["status"], atol=1.0e-6))
        self.assertEqual(str(left["termination_reason"]), str(right["termination_reason"]))
        self.assertEqual(int(left["waypoint_idx"]), int(right["waypoint_idx"]))
        self.assertEqual(str(left["mission_phase_name"]), str(right["mission_phase_name"]))
        self.assertEqual(set(left["step_info"].keys()), set(right["step_info"].keys()))
        for key in left["step_info"].keys():
            left_value = left["step_info"][key]
            right_value = right["step_info"][key]
            if isinstance(left_value, np.ndarray) or isinstance(right_value, np.ndarray):
                self.assertTrue(
                    np.allclose(np.asarray(left_value, dtype=np.float32), np.asarray(right_value, dtype=np.float32), atol=1.0e-6),
                    msg=f"step info mismatch for {key}",
                )
            elif isinstance(left_value, str) or isinstance(right_value, str):
                self.assertEqual(str(left_value), str(right_value), msg=f"step info mismatch for {key}")
            elif isinstance(left_value, dict) or isinstance(right_value, dict):
                self.assertEqual(set(dict(left_value or {}).keys()), set(dict(right_value or {}).keys()))
                for term_key in dict(left_value or {}).keys():
                    self.assertAlmostEqual(
                        float(dict(left_value)[term_key]),
                        float(dict(right_value)[term_key]),
                        places=6,
                        msg=f"step info mismatch for {key}.{term_key}",
                    )
            else:
                self.assertAlmostEqual(float(left_value), float(right_value), places=6, msg=f"step info mismatch for {key}")
        self.assertEqual(set(left["reward_breakdown"].keys()), set(right["reward_breakdown"].keys()))
        for key in left["reward_breakdown"].keys():
            self.assertAlmostEqual(
                float(left["reward_breakdown"][key]),
                float(right["reward_breakdown"][key]),
                places=6,
                msg=f"reward breakdown mismatch for {key}",
            )
        for key in ("approach_prev_dme_m", "approach_prev_loc_abs", "approach_prev_gs_abs", "waypoint_prev_dist_m"):
            if left[key] is None or right[key] is None:
                self.assertEqual(left[key], right[key], msg=f"state mismatch for {key}")
            else:
                self.assertAlmostEqual(float(left[key]), float(right[key]), places=6, msg=f"state mismatch for {key}")

    def test_pending_landing_transition_retargets_heading_to_recovery_vector(self) -> None:
        class _Truth:
            x = -20000.0
            y = 10000.0
            z = 420.0

        class _DummySim:
            def get_agent_observation(self, _agent_id):
                return _Truth()

        loader = ScenarioLoader(_DummySim())
        loader.agent_id = 1
        loader.waypoints = []
        loader.waypoint_idx = 4
        loader.mission_cmd = {
            "command_code": 3,
            "target_heading": 298.0,
            "target_altitude": 420.0,
            "target_speed": 84.0,
        }
        loader.post_waypoint_transition = {
            "phase_name": "landing_ils",
            "command_code": 4,
            "target_heading": 90.0,
            "target_altitude": 0.0,
            "target_speed": 82.0,
            "landing_mode": "ils_final",
            "approach_arm_before_threshold_m": 1000.0,
        }
        loader._nearest_ils_beacon = lambda _x, _y: {"thr_x": 0.0, "thr_y": 0.0, "heading": 90.0}
        loader._post_waypoint_transition_ready = lambda: False

        transitioned = loader._maybe_activate_post_waypoint_transition(sync_to_kernel=False)

        expected_heading = math.degrees(math.atan2(-1000.0 - _Truth.x, 0.0 - _Truth.y)) % 360.0
        self.assertIsNone(transitioned)
        self.assertAlmostEqual(float(loader.mission_cmd["target_heading"]), float(expected_heading), places=6)

    def test_selected_paths_match_legacy_runtime(self) -> None:
        cases = (
            {
                "name": "objective",
                "scenario": _objective_scenario(),
                "seed": 11,
                "terminated": True,
                "termination_reason": "success_objective",
            },
            {
                "name": "waypoint",
                "scenario": _route_scenario(),
                "seed": 17,
            },
            {
                "name": "approach",
                "scenario": _approach_scenario(),
                "seed": 23,
            },
            {
                "name": "takeoff_shaping",
                "scenario": _takeoff_shaping_scenario(),
                "seed": 29,
            },
        )
        for case in cases:
            with self.subTest(case=case["name"]):
                legacy = self._run_loader_once(case["scenario"], seed=case["seed"], compiled=False)
                compiled = self._run_loader_once(case["scenario"], seed=case["seed"], compiled=True)
                self._assert_loader_results_match(legacy, compiled)
                if "terminated" in case:
                    self.assertEqual(bool(compiled["terminated"]), bool(case["terminated"]))
                if "termination_reason" in case:
                    self.assertEqual(str(compiled["termination_reason"]), str(case["termination_reason"]))

    def test_flight_shaping_backends_match_legacy_runtime(self) -> None:
        scenario = _takeoff_shaping_scenario()
        legacy = self._run_loader_once(
            scenario,
            seed=41,
            compiled=False,
            flight_shaping_backend="legacy",
        )
        compiled_backend = self._run_loader_once(
            scenario,
            seed=41,
            compiled=False,
            flight_shaping_backend="compiled",
        )
        gpu_backend = self._run_loader_once(
            scenario,
            seed=41,
            compiled=False,
            flight_shaping_backend="gpu_host",
        )
        compiled_runtime = self._run_loader_once(
            scenario,
            seed=41,
            compiled=True,
            flight_shaping_backend="compiled",
        )
        gpu_backend_with_compiled_runtime = self._run_loader_once(
            scenario,
            seed=41,
            compiled=True,
            flight_shaping_backend="gpu_host",
        )

        self._assert_loader_results_match(legacy, compiled_backend)
        self._assert_loader_results_match(legacy, gpu_backend)
        self._assert_loader_results_match(legacy, compiled_runtime)
        self._assert_loader_results_match(legacy, gpu_backend_with_compiled_runtime)


if __name__ == "__main__":
    unittest.main()
