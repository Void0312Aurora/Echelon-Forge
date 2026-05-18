from __future__ import annotations

import copy
import json
import math
import unittest

import numpy as np

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402

from gym_envs.scenario_loader import ScenarioLoader  # noqa: E402


def _controller_route_guidance_scenario() -> dict:
    return {
        "scenario_name": "execution_episode_controller_route_guidance",
        "environment": {
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
        },
        "mission_command": {
            "command_code": 3,
            "target_heading": 90.0,
            "target_altitude": 1200.0,
            "target_speed": 180.0,
            "waypoint_mode": "flyby",
            "waypoints": [
                {"x": 1000.0, "y": 1000.0, "z": 1500.0, "radius_m": 800.0, "speed_mps": 210.0},
                {"x": 2500.0, "y": 1500.0, "z": 1500.0, "radius_m": 800.0, "speed_mps": 190.0},
            ],
        },
        "entities": [
            {
                "name": "Lead",
                "type": "F-16C_Block50",
                "side": "Blue",
                "is_agent": True,
                "pos": [-1400.0, 0.0, 1200.0],
                "vel": [0.0, 180.0, 0.0],
                "heading": 90.0,
            }
        ],
        "rewards": {
            "survival_reward": 0.02,
            "heading_error_weight": -0.1,
        },
        "objectives": [
            {
                "type": "conditional",
                "reward": 25.0,
                "conditions": [
                    {"property": "ground_track_error_deg", "op": "<=", "value": 180.0},
                ],
            }
        ],
    }


def _controller_parity_scenario() -> dict:
    return {
        "scenario_name": "execution_episode_controller_parity",
        "environment": {
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
        },
        "mission_command": {
            "command_code": 3,
            "target_heading": 90.0,
            "target_altitude": 1200.0,
            "target_speed": 180.0,
            "route_ref_id": 77,
            "waypoint_mode": "flyby",
            "waypoints": [
                {"x": -500.0, "y": 0.0, "z": 1200.0, "radius_m": 800.0, "speed_mps": 180.0},
                {"x": 2500.0, "y": 1500.0, "z": 1200.0, "radius_m": 800.0, "speed_mps": 170.0},
            ],
        },
        "entities": [
            {
                "name": "Lead",
                "type": "F-16C_Block50",
                "side": "Blue",
                "is_agent": True,
                "pos": [-1400.0, 0.0, 1200.0],
                "vel": [0.0, 180.0, 0.0],
                "heading": 90.0,
            }
        ],
        "objectives": [
            {
                "type": "conditional",
                "reward": 300.0,
                "conditions": [
                    {"property": "speed", "op": ">=", "value": 100.0},
                ],
            }
        ],
        "rewards": {
            "survival_reward": 0.02,
            "speed_reward_weight": 0.1,
            "heading_error_weight": -0.1,
            "waypoint_progress_weight": 0.01,
            "waypoint_distance_weight": -0.0005,
            "waypoint_reached_bonus": 20.0,
            "localizer_weight": -0.5,
            "glideslope_weight": -0.5,
            "dme_progress_weight": 0.01,
            "capture_bonus": 2.0,
            "sink_rate_weight": -0.2,
        },
    }


class ExecutionEpisodeControllerTests(unittest.TestCase):
    def test_controller_evaluate_matches_scenario_loader_frame_products(self) -> None:
        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))

        loader = ScenarioLoader(sim)
        agent_id = loader.load_scenario_data(copy.deepcopy(_controller_parity_scenario()), seed=41)
        self.assertIsNotNone(agent_id)

        loader.steps = 11
        loader.waypoint_idx = 0
        loader._waypoint_prev_dist_m = 975.0
        loader._waypoint_leg_origin_x = -1400.0
        loader._waypoint_leg_origin_y = 0.0
        loader.waypoint_total_route_length_m = 4200.0
        loader.prev_alt = 1185.0
        loader.prev_speed = 176.0
        loader.liftoff_awarded = True
        loader.gear_bonus_awarded = False
        loader.off_runway_steps = 1
        loader._approach_prev_dme_m = 4567.0
        loader._approach_prev_loc_abs = 0.12
        loader._approach_prev_gs_abs = 0.08

        truth = sim.get_agent_observation(agent_id)
        inst_obj = sim.get_instrument_state(agent_id)
        ils_vec = loader.get_ils_observation(float(truth.x), float(truth.y), float(inst_obj.alt_baro))
        inst_vec, _, _ = ef_py.compute_execution_observation_runtime_numpy(
            inst_obj,
            truth,
            float(ils_vec[0]),
            float(ils_vec[1]),
            float(ils_vec[2]),
            float(ils_vec[3]),
            int(loader.max_contacts),
            int(loader.max_rwr),
        )
        inst_vec = np.asarray(inst_vec, dtype=np.float32)
        mission_inputs = loader._build_mission_observation_runtime_inputs("nav_v2", truth=truth, inst=inst_obj)

        reference = loader._prepare_step_evaluation(
            truth=truth,
            inst_obj=inst_obj,
            inst_vec=inst_vec,
            ils_vec=np.asarray(ils_vec[:4], dtype=np.float32),
            steps=int(loader.steps),
            max_steps=250,
            mission_obs_mode="nav_v2",
        )
        reference_products = reference["frame_products"]

        batch_state = loader._build_step_evaluation_batch_env_state(
            truth=truth,
            inst_obj=inst_obj,
            inst_vec=inst_vec,
            ils_vec=np.asarray(ils_vec[:4], dtype=np.float32),
            steps=int(loader.steps),
            max_steps=250,
            mission_obs_mode="nav_v2",
            mission_observation_inputs=mission_inputs,
        )

        controller = ef_py.ExecutionEpisodeController()
        controller.import_state(loader.build_execution_episode_state())
        config = ef_py.StepEvaluationBatchConfig()
        actual = controller.evaluate(config, batch_state)

        self.assertTrue(bool(actual.valid))
        self.assertAlmostEqual(
            float(actual.compiled_reward_total),
            float(reference_products.compiled_reward_total),
            places=6,
        )
        self.assertEqual(bool(actual.terminated), bool(reference_products.terminated))
        self.assertEqual(actual.reason_code, reference_products.reason_code)
        self.assertEqual(actual.final_reason_code, reference_products.final_reason_code)
        self.assertAlmostEqual(float(actual.status0), float(reference_products.status0), places=6)
        self.assertAlmostEqual(float(actual.status1), float(reference_products.status1), places=6)
        self.assertAlmostEqual(float(actual.status2), float(reference_products.status2), places=6)
        self.assertAlmostEqual(float(actual.status3), float(reference_products.status3), places=6)
        self.assertEqual(
            bool(actual.mission_observation_evaluated),
            bool(reference_products.mission_observation_evaluated),
        )
        self.assertEqual(bool(actual.step_info_evaluated), bool(reference_products.step_info_evaluated))
        self.assertEqual(bool(actual.execution_step_evaluated), bool(reference_products.execution_step_evaluated))
        self.assertEqual(bool(actual.flight_shaping_evaluated), bool(reference_products.flight_shaping_evaluated))

    def test_controller_step_updates_owned_episode_state_from_runtime_products(self) -> None:
        controller = ef_py.ExecutionEpisodeController()

        episode_state = ef_py.ExecutionEpisodeState()
        episode_state.step_count = 4
        episode_state.waypoint_index = 0
        episode_state.has_waypoint_prev_dist_m = True
        episode_state.waypoint_prev_dist_m = 180.0
        episode_state.prev_altitude_m = 10.0
        episode_state.prev_ias_mps = 70.0
        episode_state.off_runway_steps = 2
        episode_state.has_approach_prev_dme_m = True
        episode_state.approach_prev_dme_m = 4500.0
        episode_state.has_approach_prev_loc_abs = True
        episode_state.approach_prev_loc_abs = 0.15
        episode_state.has_approach_prev_gs_abs = True
        episode_state.approach_prev_gs_abs = 0.14
        controller.import_state(episode_state)

        env_state = ef_py.StepEvaluationBatchEnvState()
        env_state.steps = 5
        env_state.truth_z = 120.0
        env_state.truth_speed = 110.0
        env_state.inst_vec = [0.0] * 20
        env_state.inst_vec[0] = 95.0
        env_state.inst_vec[2] = 125.0
        env_state.inst_vec[3] = 120.0
        env_state.inst_vec[7] = 6.0
        env_state.inst_vec[8] = 3.0
        env_state.inst_vec[10] = 1.1
        env_state.inst_vec[14] = 0.2
        env_state.inst_vec[18] = 0.0

        env_state.has_safety = True
        env_state.safety.finite_state_valid = True
        env_state.safety.health = 100.0
        env_state.safety.survival_reward = 0.02
        env_state.safety.runway_surface_phase = True
        env_state.safety.on_runway_task = False
        env_state.safety.off_runway_steps = 3

        env_state.has_waypoint = True
        env_state.waypoint.valid = True
        env_state.waypoint.waypoint_index = 0
        env_state.waypoint.waypoint_count = 1
        env_state.waypoint.dist_m = 80.0
        env_state.waypoint.waypoint_radius_m = 100.0
        env_state.waypoint.has_prev_dist = True
        env_state.waypoint.prev_dist_m = 180.0
        env_state.waypoint.progress_weight = 0.1
        env_state.waypoint.reached_bonus = 20.0

        env_state.has_approach = True
        env_state.approach.valid = True
        env_state.approach.ils_valid = True
        env_state.approach.ils_loc_dev = 0.05
        env_state.approach.ils_gs_dev = 0.04
        env_state.approach.ils_dme_m = 4000.0
        env_state.approach.has_prev_loc = True
        env_state.approach.prev_loc_abs = 0.15
        env_state.approach.has_prev_gs = True
        env_state.approach.prev_gs_abs = 0.14
        env_state.approach.has_prev_dme = True
        env_state.approach.prev_dme_m = 4500.0
        env_state.approach.localizer_improve_weight = 1.0
        env_state.approach.glideslope_improve_weight = 1.0
        env_state.approach.dme_progress_weight = 0.01
        env_state.approach.capture_bonus = 2.5

        env_state.has_flight_shaping = True
        env_state.flight_shaping.truth_altitude_m = 120.0
        env_state.flight_shaping.truth_speed_mps = 110.0
        env_state.flight_shaping.prev_altitude_m = 10.0
        env_state.flight_shaping.prev_ias_mps = 70.0
        env_state.flight_shaping.curr_ias_mps = 95.0
        env_state.flight_shaping.curr_alt_baro_m = 125.0
        env_state.flight_shaping.curr_alt_agl_m = 120.0
        env_state.flight_shaping.curr_gear_fraction = 0.0
        env_state.flight_shaping.curr_roll_deg = 3.0
        env_state.flight_shaping.curr_pitch_deg = 6.0
        env_state.flight_shaping.curr_yaw_rate_deg_s = 0.2
        env_state.flight_shaping.curr_g_load = 1.1
        env_state.flight_shaping.step_count = 5
        env_state.flight_shaping.target_altitude_m = 200.0
        env_state.flight_shaping.target_speed_mps = 150.0
        env_state.flight_shaping.heading_error_deg = 2.0
        env_state.flight_shaping.ground_track_error_deg = 2.0
        env_state.flight_shaping.preliftoff = False
        env_state.flight_shaping.on_runway_task = False
        env_state.flight_shaping.airborne = True
        env_state.flight_shaping.liftoff_bonus = 5.0
        env_state.flight_shaping.liftoff_speed_threshold_mps = 80.0
        env_state.flight_shaping.liftoff_alt_threshold_m = 5.0
        env_state.flight_shaping.gear_up_bonus = 7.0
        env_state.flight_shaping.gear_up_bonus_min_alt_agl_m = 50.0

        products = controller.step(ef_py.StepEvaluationBatchConfig(), env_state)
        updated = controller.export_state()

        self.assertTrue(bool(products.valid))
        self.assertEqual(int(updated.step_count), 5)
        self.assertAlmostEqual(float(updated.prev_altitude_m), 120.0, places=6)
        self.assertAlmostEqual(float(updated.prev_ias_mps), 95.0, places=6)
        self.assertTrue(bool(updated.liftoff_awarded))
        self.assertTrue(bool(updated.gear_bonus_awarded))
        self.assertEqual(int(updated.off_runway_steps), 3)
        self.assertEqual(int(updated.waypoint_index), 1)
        self.assertFalse(bool(updated.has_waypoint_prev_dist_m))
        self.assertTrue(bool(updated.has_approach_prev_dme_m))
        self.assertTrue(bool(updated.has_approach_prev_loc_abs))
        self.assertTrue(bool(updated.has_approach_prev_gs_abs))
        self.assertAlmostEqual(float(updated.approach_prev_dme_m), 4000.0, places=6)
        self.assertAlmostEqual(float(updated.approach_prev_loc_abs), 0.05, places=6)
        self.assertAlmostEqual(float(updated.approach_prev_gs_abs), 0.04, places=6)
        self.assertAlmostEqual(float(updated.last_reward_total), float(products.compiled_reward_total), places=6)
        self.assertEqual(
            str(updated.last_termination_reason),
            str(ef_py.termination_reason_name(products.final_reason_code)),
        )

    def test_controller_prepare_runtime_inputs_uses_owned_episode_state_in_fallback(self) -> None:
        controller = ef_py.ExecutionEpisodeController()

        episode_state = ef_py.ExecutionEpisodeState()
        episode_state.prev_altitude_m = 910.0
        episode_state.prev_ias_mps = 155.0
        episode_state.liftoff_awarded = True
        episode_state.gear_bonus_awarded = True
        episode_state.off_runway_steps = 4
        controller.import_state(episode_state)

        config = ef_py.StepEvaluationBatchConfig()
        config.target_heading_deg = 90.0

        env_state = ef_py.StepEvaluationBatchEnvState()
        env_state.truth_heading = 88.0
        env_state.truth_z = 0.5
        env_state.truth_speed = 70.0
        env_state.truth_vx = 0.0
        env_state.truth_vy = 70.0
        env_state.inst_vec = [0.0] * 20
        env_state.inst_vec[0] = 165.0
        env_state.inst_vec[3] = 0.5
        env_state.inst_vec[8] = 1.0
        env_state.inst_vec[10] = 1.0
        env_state.inst_vec[18] = 0.0

        runtime_inputs = controller.prepare_runtime_inputs(config, env_state)

        self.assertTrue(bool(runtime_inputs.has_execution_step))
        self.assertTrue(bool(runtime_inputs.has_flight_shaping))
        self.assertAlmostEqual(float(runtime_inputs.flight_shaping.prev_altitude_m), 910.0, places=6)
        self.assertAlmostEqual(float(runtime_inputs.flight_shaping.prev_ias_mps), 155.0, places=6)
        self.assertTrue(bool(runtime_inputs.flight_shaping.liftoff_awarded))
        self.assertTrue(bool(runtime_inputs.flight_shaping.gear_bonus_awarded))
        self.assertEqual(int(runtime_inputs.execution_step.safety.off_runway_steps), 5)

    def test_controller_prepare_runtime_inputs_overrides_rich_inputs_from_owned_state(self) -> None:
        controller = ef_py.ExecutionEpisodeController()

        episode_state = ef_py.ExecutionEpisodeState()
        episode_state.prev_altitude_m = 910.0
        episode_state.prev_ias_mps = 155.0
        episode_state.liftoff_awarded = True
        episode_state.gear_bonus_awarded = True
        episode_state.off_runway_steps = 4
        episode_state.waypoint_index = 2
        episode_state.has_waypoint_prev_dist_m = True
        episode_state.waypoint_prev_dist_m = 321.0
        episode_state.has_approach_prev_dme_m = True
        episode_state.approach_prev_dme_m = 4321.0
        episode_state.has_approach_prev_loc_abs = True
        episode_state.approach_prev_loc_abs = 0.21
        episode_state.has_approach_prev_gs_abs = True
        episode_state.approach_prev_gs_abs = 0.12
        controller.import_state(episode_state)

        env_state = ef_py.StepEvaluationBatchEnvState()
        env_state.has_safety = True
        env_state.safety.finite_state_valid = True
        env_state.safety.health = 100.0
        env_state.safety.runway_surface_phase = True
        env_state.safety.on_runway_task = False
        env_state.safety.off_runway_steps = 99

        env_state.has_waypoint = True
        env_state.waypoint.valid = True
        env_state.waypoint.waypoint_index = 0
        env_state.waypoint.waypoint_count = 5
        env_state.waypoint.dist_m = 1200.0
        env_state.waypoint.has_prev_dist = False
        env_state.waypoint.prev_dist_m = 0.0

        env_state.has_approach = True
        env_state.approach.valid = True
        env_state.approach.ils_valid = True
        env_state.approach.has_prev_dme = False
        env_state.approach.prev_dme_m = 0.0
        env_state.approach.has_prev_loc = False
        env_state.approach.prev_loc_abs = 0.0
        env_state.approach.has_prev_gs = False
        env_state.approach.prev_gs_abs = 0.0

        env_state.has_flight_shaping = True
        env_state.flight_shaping.prev_altitude_m = 12.0
        env_state.flight_shaping.prev_ias_mps = 34.0
        env_state.flight_shaping.liftoff_awarded = False
        env_state.flight_shaping.gear_bonus_awarded = False

        runtime_inputs = controller.prepare_runtime_inputs(ef_py.StepEvaluationBatchConfig(), env_state)

        self.assertTrue(bool(runtime_inputs.has_execution_step))
        self.assertTrue(bool(runtime_inputs.has_flight_shaping))
        self.assertEqual(int(runtime_inputs.execution_step.safety.off_runway_steps), 5)
        self.assertEqual(int(runtime_inputs.execution_step.waypoint.waypoint_index), 2)
        self.assertTrue(bool(runtime_inputs.execution_step.waypoint.has_prev_dist))
        self.assertAlmostEqual(float(runtime_inputs.execution_step.waypoint.prev_dist_m), 321.0, places=6)
        self.assertTrue(bool(runtime_inputs.execution_step.approach.has_prev_dme))
        self.assertAlmostEqual(float(runtime_inputs.execution_step.approach.prev_dme_m), 4321.0, places=6)
        self.assertTrue(bool(runtime_inputs.execution_step.approach.has_prev_loc))
        self.assertAlmostEqual(float(runtime_inputs.execution_step.approach.prev_loc_abs), 0.21, places=6)
        self.assertTrue(bool(runtime_inputs.execution_step.approach.has_prev_gs))
        self.assertAlmostEqual(float(runtime_inputs.execution_step.approach.prev_gs_abs), 0.12, places=6)
        self.assertAlmostEqual(float(runtime_inputs.flight_shaping.prev_altitude_m), 910.0, places=6)
        self.assertAlmostEqual(float(runtime_inputs.flight_shaping.prev_ias_mps), 155.0, places=6)
        self.assertTrue(bool(runtime_inputs.flight_shaping.liftoff_awarded))
        self.assertTrue(bool(runtime_inputs.flight_shaping.gear_bonus_awarded))

    def test_controller_prepare_runtime_inputs_applies_route_guidance_targets_before_runtime_eval(self) -> None:
        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))

        loader = ScenarioLoader(sim)
        agent_id = loader.load_scenario_data(copy.deepcopy(_controller_route_guidance_scenario()), seed=19)
        self.assertIsNotNone(agent_id)

        truth = sim.get_agent_observation(agent_id)
        inst_obj = sim.get_instrument_state(agent_id)
        ils_vec = loader.get_ils_observation(float(truth.x), float(truth.y), float(inst_obj.alt_baro))
        inst_vec, _, _ = ef_py.compute_execution_observation_runtime_numpy(
            inst_obj,
            truth,
            float(ils_vec[0]),
            float(ils_vec[1]),
            float(ils_vec[2]),
            float(ils_vec[3]),
            int(loader.max_contacts),
            int(loader.max_rwr),
        )
        inst_vec = np.asarray(inst_vec, dtype=np.float32)
        batch_state = loader._build_step_evaluation_batch_env_state(
            truth=truth,
            inst_obj=inst_obj,
            inst_vec=inst_vec,
            ils_vec=np.asarray(ils_vec[:4], dtype=np.float32),
            steps=1,
            max_steps=250,
            mission_obs_mode="nav_v2",
        )

        controller = ef_py.ExecutionEpisodeController()
        controller.import_state(loader.build_execution_episode_state())

        route_result = loader._query_route_guidance_result(truth=truth, inst=inst_obj)
        self.assertIsNotNone(route_result)
        active_wp = loader.waypoints[int(route_result.idx)]
        expected_heading = float(route_result.cmd_track_deg)
        expected_altitude = float(active_wp.get("altitude_m", active_wp.get("z", 0.0)))
        expected_speed = float(active_wp.get("speed_mps", 0.0))
        expected_heading_error = float(
            ef_py.compute_command_tracking_error_deg(
                expected_heading,
                float(getattr(truth, "heading", 0.0)),
                3,
                float(inst_vec[30]) if inst_vec.size > 30 else float("nan"),
            )
        )
        expected_ground_track_error = float(
            ef_py.compute_ground_track_error_deg(
                expected_heading,
                float(getattr(truth, "heading", 0.0)),
                float(inst_vec[30]) if inst_vec.size > 30 else float("nan"),
            )
        )

        runtime_inputs = controller.prepare_runtime_inputs(
            loader._build_execution_episode_controller_shadow_config(),
            batch_state,
        )

        self.assertTrue(bool(runtime_inputs.has_mission_observation))
        self.assertTrue(bool(runtime_inputs.has_flight_shaping))
        self.assertTrue(bool(runtime_inputs.has_execution_step))
        self.assertAlmostEqual(float(runtime_inputs.mission_observation.target_heading_deg), expected_heading, places=6)
        self.assertAlmostEqual(float(runtime_inputs.mission_observation.target_altitude_m), expected_altitude, places=6)
        self.assertAlmostEqual(float(runtime_inputs.mission_observation.target_speed_mps), expected_speed, places=6)
        self.assertAlmostEqual(float(runtime_inputs.flight_shaping.target_altitude_m), expected_altitude, places=6)
        self.assertAlmostEqual(float(runtime_inputs.flight_shaping.target_speed_mps), expected_speed, places=6)
        self.assertAlmostEqual(float(runtime_inputs.flight_shaping.heading_error_deg), expected_heading_error, places=6)
        self.assertAlmostEqual(
            float(runtime_inputs.flight_shaping.ground_track_error_deg),
            expected_ground_track_error,
            places=6,
        )
        self.assertAlmostEqual(
            float(runtime_inputs.execution_step.objective_inputs.target_heading_deg),
            expected_heading,
            places=6,
        )

    def test_controller_step_result_applies_non_landing_post_waypoint_transition(self) -> None:
        controller = ef_py.ExecutionEpisodeController()

        episode_state = ef_py.ExecutionEpisodeState()
        episode_state.step_count = 0
        episode_state.has_mission_command = True
        episode_state.mission_command.command_code = 3
        episode_state.mission_command.cmd_heading_deg = 90.0
        episode_state.mission_command.cmd_altitude_m = 1200.0
        episode_state.mission_command.cmd_speed_mps = 180.0
        episode_state.mission_command.active = True
        episode_state.has_mission_command_json = True
        episode_state.mission_command_json = json.dumps(
            {
                "command_code": 3,
                "route_ref_id": 77,
                "target_altitude": 1200.0,
                "target_heading": 90.0,
                "target_speed": 180.0,
                "waypoint_mode": "flyby",
                "waypoints": [
                    {"x": -1350.0, "y": 0.0, "z": 1200.0, "radius_m": 1200.0},
                ],
            },
            ensure_ascii=True,
            sort_keys=True,
        )
        route_waypoint = ef_py.SpatialRouteWaypoint()
        route_waypoint.x_m = -1350.0
        route_waypoint.y_m = 0.0
        route_waypoint.z_m = 1200.0
        route_waypoint.radius_m = 1200.0
        route_waypoint.altitude_m = 1200.0
        route_waypoint.speed_mps = 180.0
        route_waypoint.waypoint_mode = "flyby"
        episode_state.route_waypoints = [route_waypoint]
        episode_state.waypoint_index = 0
        episode_state.has_post_waypoint_transition_json = True
        episode_state.post_waypoint_transition_json = json.dumps(
            {
                "command_code": 2,
                "phase_name": "post_route",
                "target_altitude": 900.0,
                "target_heading": 45.0,
                "target_speed": 160.0,
                "transition_reward": 123.0,
            },
            ensure_ascii=True,
            sort_keys=True,
        )
        controller.import_state(episode_state)

        env_state = ef_py.StepEvaluationBatchEnvState()
        env_state.steps = 1
        env_state.truth_x = -1400.0
        env_state.truth_y = 0.0
        env_state.truth_z = 1200.0
        env_state.truth_speed = 180.0
        env_state.has_safety = True
        env_state.safety.finite_state_valid = True
        env_state.safety.health = 100.0
        env_state.safety.survival_reward = 0.02

        env_state.has_waypoint = True
        env_state.waypoint.valid = True
        env_state.waypoint.waypoint_index = 0
        env_state.waypoint.waypoint_count = 1
        env_state.waypoint.dist_m = 50.0
        env_state.waypoint.waypoint_radius_m = 1200.0
        env_state.waypoint.has_prev_dist = True
        env_state.waypoint.prev_dist_m = 120.0
        env_state.waypoint.progress_weight = 0.1
        env_state.waypoint.distance_weight = -0.001
        env_state.waypoint.reached_bonus = 20.0

        result = controller.step_result(ef_py.StepEvaluationBatchConfig(), env_state)

        self.assertTrue(bool(result.valid))
        self.assertTrue(bool(result.structural_state_changed))
        self.assertFalse(bool(result.terminated))
        self.assertFalse(bool(result.truncated))
        self.assertAlmostEqual(float(result.status0), 0.0, places=6)
        self.assertAlmostEqual(float(result.status1), 0.0, places=6)

        controller_state = result.controller_state
        self.assertEqual(int(controller_state.mission_command.command_code), 2)
        self.assertEqual(str(controller_state.mission_phase_name), "post_route")
        self.assertFalse(bool(controller_state.has_post_waypoint_transition_json))
        self.assertEqual(len(list(controller_state.route_waypoints)), 0)

        breakdown = json.loads(str(controller_state.last_reward_breakdown_json))
        self.assertAlmostEqual(float(breakdown["phase_transition_bonus"]), 123.0, places=6)
        self.assertAlmostEqual(float(controller_state.last_reward_total), float(result.reward_total), places=6)
        self.assertGreater(float(result.reward_total), 123.0)

    def test_controller_step_result_updates_pending_landing_vector_after_route_completion(self) -> None:
        controller = ef_py.ExecutionEpisodeController()

        episode_state = ef_py.ExecutionEpisodeState()
        episode_state.has_mission_command = True
        episode_state.mission_command.command_code = 3
        episode_state.mission_command.cmd_heading_deg = 298.0
        episode_state.mission_command.cmd_altitude_m = 420.0
        episode_state.mission_command.cmd_speed_mps = 84.0
        episode_state.mission_command.active = True
        episode_state.has_mission_command_json = True
        episode_state.mission_command_json = json.dumps(
            {
                "command_code": 3,
                "post_waypoint_transition": {
                    "approach_arm_before_threshold_m": 1000.0,
                    "command_code": 4,
                    "landing_mode": "ils_final",
                    "phase_name": "landing_ils",
                    "target_altitude": 0.0,
                    "target_heading": 90.0,
                    "target_speed": 82.0,
                },
                "target_altitude": 420.0,
                "target_heading": 298.0,
                "target_speed": 84.0,
                "waypoint_mode": "flyby",
                "waypoints": [
                    {"x": 1000.0, "y": 0.0, "z": 420.0, "radius_m": 800.0},
                ],
            },
            ensure_ascii=True,
            sort_keys=True,
        )
        route_waypoint = ef_py.SpatialRouteWaypoint()
        route_waypoint.x_m = 1000.0
        route_waypoint.y_m = 0.0
        route_waypoint.z_m = 420.0
        route_waypoint.radius_m = 800.0
        route_waypoint.altitude_m = 420.0
        route_waypoint.speed_mps = 84.0
        route_waypoint.waypoint_mode = "flyby"
        episode_state.route_waypoints = [route_waypoint]
        episode_state.waypoint_index = 1
        episode_state.has_post_waypoint_transition_json = True
        episode_state.post_waypoint_transition_json = json.dumps(
            {
                "phase_name": "landing_ils",
                "command_code": 4,
                "target_heading": 90.0,
                "target_altitude": 0.0,
                "target_speed": 82.0,
                "landing_mode": "ils_final",
                "approach_arm_before_threshold_m": 1000.0,
            },
            ensure_ascii=True,
            sort_keys=True,
        )
        controller.import_state(episode_state)

        env_state = ef_py.StepEvaluationBatchEnvState()
        env_state.steps = 5
        env_state.truth_x = -200.0
        env_state.truth_y = 200.0
        env_state.truth_z = 420.0
        env_state.truth_heading = 298.0
        env_state.ils_vec = [1.0, 0.0, 0.0, 25000.0]
        inst_vec = [0.0] * 42
        inst_vec[9] = 298.0
        env_state.inst_vec = inst_vec
        env_state.has_safety = True
        env_state.safety.finite_state_valid = True
        env_state.safety.health = 100.0
        env_state.safety.survival_reward = 0.02
        env_state.has_step_info = True
        env_state.step_info.has_runway_frame = True
        env_state.step_info.runway_frame.valid = True
        env_state.step_info.runway_frame.along_m = -3000.0
        env_state.step_info.runway_frame.cross_m = 0.0
        env_state.step_info.runway_frame.length_m = 2500.0
        env_state.step_info.runway_frame.width_m = 60.0
        env_state.step_info.runway_frame.heading_deg = 90.0

        result = controller.step_result(ef_py.StepEvaluationBatchConfig(), env_state)

        self.assertTrue(bool(result.valid))
        self.assertTrue(bool(result.structural_state_changed))
        self.assertFalse(bool(result.terminated))
        self.assertEqual(int(result.controller_state.mission_command.command_code), 3)
        self.assertTrue(bool(result.controller_state.has_post_waypoint_transition_json))

        runway_heading_rad = math.radians(90.0)
        fwd_x = math.sin(runway_heading_rad)
        fwd_y = math.cos(runway_heading_rad)
        right_x = math.cos(runway_heading_rad)
        right_y = -math.sin(runway_heading_rad)
        center_x = -200.0 - (-3000.0) * fwd_x - 0.0 * right_x
        center_y = 200.0 - (-3000.0) * fwd_y - 0.0 * right_y
        threshold_x = center_x - 0.5 * 2500.0 * fwd_x
        threshold_y = center_y - 0.5 * 2500.0 * fwd_y
        intercept_x = threshold_x - fwd_x * 1000.0
        intercept_y = threshold_y - fwd_y * 1000.0
        expected_heading = math.degrees(math.atan2(intercept_x - (-200.0), intercept_y - 200.0)) % 360.0
        self.assertAlmostEqual(
            float(result.controller_state.mission_command.cmd_heading_deg),
            float(expected_heading),
            places=6,
        )
        updated_mission_json = json.loads(str(result.controller_state.mission_command_json))
        self.assertAlmostEqual(float(updated_mission_json["target_heading"]), float(expected_heading), places=6)
        self.assertNotIn("phase_transition_bonus", json.loads(str(result.controller_state.last_reward_breakdown_json)))

    def test_controller_step_result_activates_landing_post_waypoint_transition_when_terminal_ready(self) -> None:
        controller = ef_py.ExecutionEpisodeController()

        episode_state = ef_py.ExecutionEpisodeState()
        episode_state.has_mission_command = True
        episode_state.mission_command.command_code = 3
        episode_state.mission_command.cmd_heading_deg = 90.0
        episode_state.mission_command.cmd_altitude_m = 420.0
        episode_state.mission_command.cmd_speed_mps = 84.0
        episode_state.mission_command.active = True
        episode_state.has_mission_command_json = True
        episode_state.mission_command_json = json.dumps(
            {
                "command_code": 3,
                "post_waypoint_transition": {
                    "command_code": 4,
                    "landing_mode": "ils_final",
                    "phase_name": "landing_ils",
                    "target_altitude": 0.0,
                    "target_heading": 90.0,
                    "target_speed": 82.0,
                    "transition_reward": 55.0,
                },
                "target_altitude": 420.0,
                "target_heading": 90.0,
                "target_speed": 84.0,
                "waypoint_mode": "flyby",
                "waypoints": [
                    {"x": 1000.0, "y": 0.0, "z": 420.0, "radius_m": 800.0},
                ],
            },
            ensure_ascii=True,
            sort_keys=True,
        )
        route_waypoint = ef_py.SpatialRouteWaypoint()
        route_waypoint.x_m = 1000.0
        route_waypoint.y_m = 0.0
        route_waypoint.z_m = 420.0
        route_waypoint.radius_m = 800.0
        route_waypoint.altitude_m = 420.0
        route_waypoint.speed_mps = 84.0
        route_waypoint.waypoint_mode = "flyby"
        episode_state.route_waypoints = [route_waypoint]
        episode_state.waypoint_index = 1
        episode_state.has_post_waypoint_transition_json = True
        episode_state.post_waypoint_transition_json = json.dumps(
            {
                "phase_name": "landing_ils",
                "command_code": 4,
                "target_heading": 90.0,
                "target_altitude": 0.0,
                "target_speed": 82.0,
                "landing_mode": "ils_final",
                "transition_reward": 55.0,
            },
            ensure_ascii=True,
            sort_keys=True,
        )
        controller.import_state(episode_state)

        env_state = ef_py.StepEvaluationBatchEnvState()
        env_state.steps = 6
        env_state.truth_x = -500.0
        env_state.truth_y = 0.0
        env_state.truth_z = 420.0
        env_state.truth_heading = 90.0
        env_state.ils_vec = [1.0, 0.0, 0.0, 10000.0]
        inst_vec = [0.0] * 42
        inst_vec[9] = 90.0
        env_state.inst_vec = inst_vec
        env_state.has_safety = True
        env_state.safety.finite_state_valid = True
        env_state.safety.health = 100.0
        env_state.safety.survival_reward = 0.02
        env_state.has_step_info = True
        env_state.step_info.has_runway_frame = True
        env_state.step_info.runway_frame.valid = True
        env_state.step_info.runway_frame.along_m = -500.0
        env_state.step_info.runway_frame.cross_m = 0.0
        env_state.step_info.runway_frame.length_m = 2500.0
        env_state.step_info.runway_frame.width_m = 60.0
        env_state.step_info.runway_frame.heading_deg = 90.0

        result = controller.step_result(ef_py.StepEvaluationBatchConfig(), env_state)

        self.assertTrue(bool(result.valid))
        self.assertTrue(bool(result.structural_state_changed))
        self.assertEqual(int(result.controller_state.mission_command.command_code), 4)
        self.assertFalse(bool(result.controller_state.has_post_waypoint_transition_json))
        self.assertEqual(str(result.controller_state.mission_phase_name), "landing_ils")
        self.assertEqual(len(list(result.controller_state.route_waypoints)), 0)
        breakdown = json.loads(str(result.controller_state.last_reward_breakdown_json))
        self.assertAlmostEqual(float(breakdown["phase_transition_bonus"]), 55.0, places=6)
        self.assertAlmostEqual(float(result.controller_state.last_reward_total), float(result.reward_total), places=6)
        self.assertGreaterEqual(float(result.reward_total), 55.0)


if __name__ == "__main__":
    unittest.main()
