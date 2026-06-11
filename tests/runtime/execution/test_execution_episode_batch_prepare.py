from __future__ import annotations

import copy
import json
import unittest

import numpy as np

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py # noqa: E402

from gym_envs.scenario_loader import ScenarioLoader # noqa: E402


def _assert_float_list_close(testcase: unittest.TestCase, lhs, rhs, places: int = 6) -> None:
  testcase.assertEqual(len(lhs), len(rhs))
  for left, right in zip(lhs, rhs):
    testcase.assertAlmostEqual(float(left), float(right), places=places)


def _assert_episode_products_close(
  testcase: unittest.TestCase,
  lhs,
  rhs,
  *,
  places: int = 6,
) -> None:
  testcase.assertEqual(bool(lhs.valid), bool(rhs.valid))
  testcase.assertEqual(bool(lhs.mission_observation_evaluated), bool(rhs.mission_observation_evaluated))
  testcase.assertEqual(bool(lhs.step_info_evaluated), bool(rhs.step_info_evaluated))
  testcase.assertEqual(bool(lhs.execution_step_evaluated), bool(rhs.execution_step_evaluated))
  testcase.assertEqual(bool(lhs.flight_shaping_evaluated), bool(rhs.flight_shaping_evaluated))
  testcase.assertEqual(bool(lhs.outcome_evaluated), bool(rhs.outcome_evaluated))
  testcase.assertAlmostEqual(float(lhs.compiled_reward_total), float(rhs.compiled_reward_total), places=places)
  testcase.assertEqual(bool(lhs.terminated), bool(rhs.terminated))
  testcase.assertEqual(lhs.reason_code, rhs.reason_code)
  testcase.assertEqual(lhs.final_reason_code, rhs.final_reason_code)
  testcase.assertAlmostEqual(float(lhs.status0), float(rhs.status0), places=places)
  testcase.assertAlmostEqual(float(lhs.status1), float(rhs.status1), places=places)
  testcase.assertAlmostEqual(float(lhs.status2), float(rhs.status2), places=places)
  testcase.assertAlmostEqual(float(lhs.status3), float(rhs.status3), places=places)

  if bool(lhs.mission_observation_evaluated) and bool(rhs.mission_observation_evaluated):
    testcase.assertEqual(int(lhs.mission_observation.mode_code), int(rhs.mission_observation.mode_code))
    testcase.assertEqual(bool(lhs.mission_observation.nav_valid), bool(rhs.mission_observation.nav_valid))
    _assert_float_list_close(
      testcase,
      list(lhs.mission_observation.values),
      list(rhs.mission_observation.values),
      places=places,
    )

  if bool(lhs.step_info_evaluated) and bool(rhs.step_info_evaluated):
    testcase.assertEqual(bool(lhs.step_info.on_ground), bool(rhs.step_info.on_ground))
    testcase.assertEqual(bool(lhs.step_info.airborne), bool(rhs.step_info.airborne))
    testcase.assertEqual(bool(lhs.step_info.on_runway_geom), bool(rhs.step_info.on_runway_geom))
    testcase.assertAlmostEqual(float(lhs.step_info.runway_cross_m), float(rhs.step_info.runway_cross_m), places=places)
    testcase.assertAlmostEqual(float(lhs.step_info.runway_along_m), float(rhs.step_info.runway_along_m), places=places)

  if bool(lhs.execution_step_evaluated) and bool(rhs.execution_step_evaluated):
    testcase.assertAlmostEqual(
      float(lhs.execution_step.compiled_reward_total),
      float(rhs.execution_step.compiled_reward_total),
      places=places,
    )
    testcase.assertEqual(bool(lhs.execution_step.waypoint_evaluated), bool(rhs.execution_step.waypoint_evaluated))
    testcase.assertEqual(bool(lhs.execution_step.approach_evaluated), bool(rhs.execution_step.approach_evaluated))
    testcase.assertEqual(bool(lhs.execution_step.objective_evaluated), bool(rhs.execution_step.objective_evaluated))
    testcase.assertEqual(int(lhs.execution_step.matched_objective_index), int(rhs.execution_step.matched_objective_index))

    if bool(lhs.execution_step.waypoint_evaluated) and bool(rhs.execution_step.waypoint_evaluated):
      testcase.assertAlmostEqual(
        float(lhs.execution_step.waypoint.waypoint_progress),
        float(rhs.execution_step.waypoint.waypoint_progress),
        places=places,
      )
      testcase.assertAlmostEqual(
        float(lhs.execution_step.waypoint.waypoint_distance),
        float(rhs.execution_step.waypoint.waypoint_distance),
        places=places,
      )
      testcase.assertEqual(bool(lhs.execution_step.waypoint.arrived), bool(rhs.execution_step.waypoint.arrived))

    if bool(lhs.execution_step.approach_evaluated) and bool(rhs.execution_step.approach_evaluated):
      testcase.assertAlmostEqual(
        float(lhs.execution_step.approach.approach_localizer),
        float(rhs.execution_step.approach.approach_localizer),
        places=places,
      )
      testcase.assertAlmostEqual(
        float(lhs.execution_step.approach.approach_glideslope),
        float(rhs.execution_step.approach.approach_glideslope),
        places=places,
      )
      testcase.assertAlmostEqual(
        float(lhs.execution_step.approach.approach_capture_bonus),
        float(rhs.execution_step.approach.approach_capture_bonus),
        places=places,
      )

    if bool(lhs.execution_step.objective_evaluated) and bool(rhs.execution_step.objective_evaluated):
      testcase.assertEqual(bool(lhs.execution_step.objective.matched), bool(rhs.execution_step.objective.matched))
      testcase.assertAlmostEqual(
        float(lhs.execution_step.objective.objective_bonus),
        float(rhs.execution_step.objective.objective_bonus),
        places=places,
      )

  if bool(lhs.flight_shaping_evaluated) and bool(rhs.flight_shaping_evaluated):
    testcase.assertAlmostEqual(
      float(lhs.flight_shaping.speed_reward),
      float(rhs.flight_shaping.speed_reward),
      places=places,
    )
    testcase.assertAlmostEqual(
      float(lhs.flight_shaping.heading_error_penalty),
      float(rhs.flight_shaping.heading_error_penalty),
      places=places,
    )
    testcase.assertAlmostEqual(
      float(lhs.flight_shaping.roll_stability),
      float(rhs.flight_shaping.roll_stability),
      places=places,
    )


def _assert_reward_breakdowns_close(
  testcase: unittest.TestCase,
  lhs_inputs,
  lhs_products,
  rhs_inputs,
  rhs_products,
  *,
  places: int = 6,
) -> None:
  lhs_breakdown = json.loads(
    ef_py.build_episode_reward_breakdown_json(
      lhs_inputs,
      lhs_products,
      float(lhs_products.compiled_reward_total),
      False,
      False,
      0.0,
    )
  )
  rhs_breakdown = json.loads(
    ef_py.build_episode_reward_breakdown_json(
      rhs_inputs,
      rhs_products,
      float(rhs_products.compiled_reward_total),
      False,
      False,
      0.0,
    )
  )
  testcase.assertEqual(set(lhs_breakdown.keys()), set(rhs_breakdown.keys()))
  for key in lhs_breakdown:
    testcase.assertAlmostEqual(float(lhs_breakdown[key]), float(rhs_breakdown[key]), places=places, msg=key)


def _runtime_batch_prepare_scenario() -> dict:
  return {
    "scenario_name": "execution_episode_batch_prepare_parity",
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


class ExecutionEpisodeBatchPrepareTests(unittest.TestCase):
  def test_batch_prepare_reward_termination_breakdown_matches_direct_runtime_inputs(self) -> None:
    config = ef_py.StepEvaluationBatchConfig()
    state = ef_py.StepEvaluationBatchEnvState()
    state.truncated = True

    state.has_mission_observation = True
    state.mission_observation.mode_code = 0
    state.mission_observation.command_code = 3.0
    state.mission_observation.target_heading_deg = 90.0
    state.mission_observation.target_altitude_m = 1000.0
    state.mission_observation.target_speed_mps = 120.0

    state.has_step_info = True
    state.step_info.on_runway = False
    state.step_info.alt_agl_m = 12.0
    state.step_info.on_ground_alt_threshold_m = 2.5
    state.step_info.airborne_alt_threshold_m = 5.0

    state.has_safety = True
    state.safety.finite_state_valid = True
    state.safety.health = 100.0
    state.safety.survival_reward = 0.02

    state.has_waypoint = True
    state.waypoint.valid = True
    state.waypoint.waypoint_index = 0
    state.waypoint.waypoint_count = 2
    state.waypoint.dist_m = 140.0
    state.waypoint.waypoint_radius_m = 100.0
    state.waypoint.has_prev_dist = True
    state.waypoint.prev_dist_m = 180.0
    state.waypoint.progress_weight = 0.1
    state.waypoint.distance_weight = -0.01
    state.waypoint_episode_success = False
    state.waypoint_episode_success_bonus = 500.0

    state.has_approach = True
    state.approach.valid = True
    state.approach.ils_valid = True
    state.approach.ils_loc_dev = 0.05
    state.approach.ils_gs_dev = 0.04
    state.approach.ils_dme_m = 4000.0
    state.approach.has_prev_loc = True
    state.approach.prev_loc_abs = 0.15
    state.approach.has_prev_gs = True
    state.approach.prev_gs_abs = 0.14
    state.approach.localizer_improve_weight = 1.5
    state.approach.glideslope_improve_weight = 1.5
    state.approach.capture_bonus = 2.5
    state.approach.capture_localizer_band = 0.1
    state.approach.capture_glideslope_band = 0.1

    state.has_objectives = True
    spec = ef_py.ConditionalObjectiveSpec()
    spec.reward_bonus = 250.0
    cond = ef_py.ConditionalObjectiveCondition()
    cond.property_code = ef_py.ConditionalObjectiveProperty.Speed
    cond.op_code = ef_py.ConditionalObjectiveOp.GreaterEqual
    cond.target_kind = ef_py.ConditionalObjectiveTargetKind.Literal
    cond.target_value = 90.0
    spec.conditions = [cond]
    state.objectives = [spec]
    state.objective_inputs.speed_mps = 120.0
    state.objective_inputs.target_speed_mps = 110.0

    state.has_flight_shaping = True
    state.flight_shaping.truth_speed_mps = 120.0
    state.flight_shaping.speed_reward_weight = 0.25
    state.flight_shaping.truth_altitude_m = 50.0
    state.flight_shaping.curr_roll_deg = 3.0
    state.flight_shaping.roll_stability_weight = -0.2
    state.include_roll_stability = True

    expected_inputs = ef_py.ExecutionEpisodeRuntimeInputs()
    expected_inputs.has_mission_observation = True
    expected_inputs.mission_observation = state.mission_observation
    expected_inputs.has_step_info = True
    expected_inputs.step_info = state.step_info
    expected_inputs.has_execution_step = True
    expected_inputs.execution_step.truncated = True
    expected_inputs.execution_step.safety = state.safety
    expected_inputs.execution_step.has_waypoint = True
    expected_inputs.execution_step.waypoint = state.waypoint
    expected_inputs.execution_step.waypoint_episode_success = state.waypoint_episode_success
    expected_inputs.execution_step.waypoint_episode_success_bonus = state.waypoint_episode_success_bonus
    expected_inputs.execution_step.has_approach = True
    expected_inputs.execution_step.approach = state.approach
    expected_inputs.execution_step.has_objectives = True
    expected_inputs.execution_step.objectives = state.objectives
    expected_inputs.execution_step.objective_inputs = state.objective_inputs
    expected_inputs.execution_step.objective_shaping = state.objective_shaping
    expected_inputs.has_flight_shaping = True
    expected_inputs.flight_shaping = state.flight_shaping
    expected_inputs.include_roll_stability = True

    expected = ef_py.compute_execution_episode_runtime(expected_inputs)
    actual_inputs = ef_py.prepare_step_evaluations_batch(config, [state])[0]
    actual = ef_py.compute_execution_episode_runtime(actual_inputs)

    _assert_episode_products_close(self, expected, actual)
    _assert_reward_breakdowns_close(self, expected_inputs, expected, actual_inputs, actual)

  def test_batch_prepare_matches_scenario_loader_step_evaluation(self) -> None:
    sim = ef_py.SimulationKernel()
    self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))

    loader = ScenarioLoader(sim)
    agent_id = loader.load_scenario_data(copy.deepcopy(_runtime_batch_prepare_scenario()), seed=31)
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
    self.assertTrue(bool(batch_state.has_episode_state))
    self.assertTrue(bool(batch_state.has_step_info))
    self.assertTrue(bool(batch_state.has_safety))
    self.assertTrue(bool(batch_state.has_flight_shaping))

    runtime_inputs = ef_py.prepare_step_evaluations_batch(
      ef_py.StepEvaluationBatchConfig(),
      [batch_state],
    )[0]
    batch_products = ef_py.compute_execution_episode_runtime(runtime_inputs)

    _assert_episode_products_close(self, reference_products, batch_products)


if __name__ == "__main__":
  unittest.main()
