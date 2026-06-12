from __future__ import annotations

import copy
import math
import os
import unittest
from unittest import mock

import numpy as np

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py # noqa: E402

from gym_envs.scenario_loader import ScenarioLoader # noqa: E402
from gym_envs.scenario_loader import normalize_execution_step_runtime_mode # noqa: E402
from gym_envs.scenario_loader import normalize_flight_shaping_backend # noqa: E402
from gym_envs.universal_env import build_step_info, build_universal_observation # noqa: E402


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
  def test_runtime_mode_normalizers_reject_legacy_inputs(self) -> None:
    with self.assertRaisesRegex(ValueError, "execution_step_runtime_mode='legacy' has been removed"):
      normalize_execution_step_runtime_mode(" legacy ")
    with self.assertRaisesRegex(ValueError, "flight_shaping_backend='legacy' has been removed"):
      normalize_flight_shaping_backend(" legacy ")

    for mode_alias in ("python", "off", "0", "false", "on", "1", "true"):
      with self.subTest(alias=mode_alias):
        with self.assertRaisesRegex(ValueError, "Unknown execution_step_runtime_mode"):
          normalize_execution_step_runtime_mode(mode_alias)
        with self.assertRaisesRegex(ValueError, "Unknown flight_shaping_backend"):
          normalize_flight_shaping_backend(mode_alias)

  def test_flight_shaping_backend_ignores_environment_compatibility_override(self) -> None:
    with mock.patch.dict(os.environ, {"CMO_FLIGHT_SHAPING_BACKEND": "legacy"}):
      self.assertEqual(normalize_flight_shaping_backend(None), "auto")

      loader = ScenarioLoader(ef_py.SimulationKernel())
      self.assertEqual(loader.flight_shaping_backend, "auto")
      self.assertEqual(loader._flight_shaping_backend_mode(), "compiled")
      loader.use_compiled_execution_step_runtime = False
      self.assertEqual(loader._flight_shaping_backend_mode(), "compiled")

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

  def _run_controller_shadow_once(
    self,
    scenario_data: dict,
    *,
    seed: int,
    steps: int = 1,
    advance_state: bool = False,
  ) -> dict:
    sim = ef_py.SimulationKernel()
    self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))
    loader = ScenarioLoader(sim)
    loader.use_compiled_execution_step_runtime = True
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
      steps=int(steps),
      max_steps=loader.get_max_steps(),
    )
    ils_vec = loader.get_ils_observation(float(truth.x), float(truth.y), float(inst.alt_baro))
    return loader.compare_execution_episode_controller_shadow(
      truth=truth,
      inst_obj=inst,
      inst_vec=np.asarray(obs["instruments"], dtype=np.float32),
      ils_vec=np.asarray(ils_vec[:4], dtype=np.float32),
      steps=int(steps),
      max_steps=loader.get_max_steps(),
      mission_obs_mode="nav_v2",
      advance_state=bool(advance_state),
    )

  def test_update_behaviors_nonhierarchical_route_updates_guidance_targets(self) -> None:
    sim = ef_py.SimulationKernel()
    self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))
    loader = ScenarioLoader(sim)
    agent_id = loader.load_scenario_data(copy.deepcopy(_route_scenario()), seed=7)
    self.assertIsNotNone(agent_id)

    truth = sim.get_agent_observation(int(agent_id))
    inst = sim.get_instrument_state(int(agent_id))
    route_result = loader._query_route_guidance_result(truth=truth, inst=inst)
    self.assertIsNotNone(route_result)

    wp_idx = int(getattr(route_result, "idx", 0))
    wp = loader.waypoints[wp_idx]
    expected_heading = float(getattr(route_result, "cmd_track_deg", 0.0))
    expected_altitude = float(wp.get("altitude_m", loader.mission_cmd.get("target_altitude", 0.0)))
    expected_speed = float(wp.get("speed_mps", loader.mission_cmd.get("target_speed", 0.0)))

    loader.mission_cmd["target_heading"] = -999.0
    loader.mission_cmd["target_altitude"] = -999.0
    loader.mission_cmd["target_speed"] = -999.0

    loader.update_nonhierarchical_behaviors(truth=truth, inst=inst, sync_to_kernel=False)

    self.assertAlmostEqual(float(loader.mission_cmd["target_heading"]), expected_heading, places=6)
    self.assertAlmostEqual(float(loader.mission_cmd["target_altitude"]), expected_altitude, places=6)
    self.assertAlmostEqual(float(loader.mission_cmd["target_speed"]), expected_speed, places=6)

  def test_update_behaviors_route_target_altitude_includes_formation_slot_offset(self) -> None:
    sim = ef_py.SimulationKernel()
    self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))
    loader = ScenarioLoader(sim)
    scenario = copy.deepcopy(_route_scenario())
    scenario["mission_command"]["form_offset_z"] = 30.0
    agent_id = loader.load_scenario_data(scenario, seed=11)
    self.assertIsNotNone(agent_id)

    truth = sim.get_agent_observation(int(agent_id))
    inst = sim.get_instrument_state(int(agent_id))
    route_result = loader._query_route_guidance_result(truth=truth, inst=inst)
    self.assertIsNotNone(route_result)
    assert route_result is not None

    wp_idx = int(getattr(route_result, "idx", 0))
    wp = loader.waypoints[wp_idx]
    expected_altitude = float(wp.get("altitude_m", wp.get("z", loader.mission_cmd.get("target_altitude", 0.0)))) + 30.0
    loader.mission_cmd["target_altitude"] = -999.0

    loader.update_nonhierarchical_behaviors(truth=truth, inst=inst, sync_to_kernel=False)
    self.assertAlmostEqual(float(loader.mission_cmd["target_altitude"]), expected_altitude, places=6)

  def test_prepare_step_evaluation_compact_cruise_skips_step_info(self) -> None:
    sim = ef_py.SimulationKernel()
    self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))
    loader = ScenarioLoader(sim)
    loader.use_compiled_execution_step_runtime = True
    agent_id = loader.load_scenario_data(copy.deepcopy(_route_scenario()), seed=17)
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
    inst_vec = np.asarray(obs["instruments"], dtype=np.float32)
    ils_vec = np.asarray(inst_vec[-4:], dtype=np.float32) if inst_vec.size >= 4 else np.zeros((4,), dtype=np.float32)

    loader.reset_runtime_eval_cache()
    step_eval = loader._prepare_step_evaluation(
      truth=truth,
      inst_obj=inst,
      inst_vec=inst_vec,
      ils_vec=ils_vec,
      steps=1,
      max_steps=loader.get_max_steps(),
      mission_obs_mode=None,
      defer_compiled_runtime=True,
      compact_output=True,
    )

    self.assertTrue(bool(step_eval.get("_compact_output", False)))
    self.assertIn(step_eval.get("_runtime_deferred_kind"), {"episode", "frame"})
    runtime_inputs = step_eval.get("_runtime_deferred_inputs")
    self.assertIsNotNone(runtime_inputs)
    self.assertFalse(bool(getattr(runtime_inputs, "has_step_info", True)))

  def test_compute_full_step_reuses_cached_step_evaluation(self) -> None:
    sim_cached = ef_py.SimulationKernel()
    self.assertTrue(sim_cached.load_database(resolve_repo_path("examples", "config", "database")))
    loader_cached = ScenarioLoader(sim_cached)
    loader_cached.use_compiled_execution_step_runtime = True
    agent_id_cached = loader_cached.load_scenario_data(copy.deepcopy(_route_scenario()), seed=19)
    self.assertIsNotNone(agent_id_cached)

    truth_cached = sim_cached.get_agent_observation(int(agent_id_cached))
    inst_cached = sim_cached.get_instrument_state(int(agent_id_cached))
    obs_cached = build_universal_observation(
      loader_cached,
      inst_cached,
      truth_cached,
      mission_obs_mode="nav_v2",
      max_contacts=10,
      max_rwr=4,
      include_proprio=False,
      last_action=None,
      action_space=None,
      steps=1,
      max_steps=loader_cached.get_max_steps(),
    )
    inst_vec_cached = np.asarray(obs_cached["instruments"], dtype=np.float32)
    ils_vec_cached = (
      np.asarray(inst_vec_cached[-4:], dtype=np.float32)
      if inst_vec_cached.size >= 4
      else np.zeros((4,), dtype=np.float32)
    )

    loader_cached.reset_runtime_eval_cache()
    cached_step_eval = loader_cached._prepare_step_evaluation(
      truth=truth_cached,
      inst_obj=inst_cached,
      inst_vec=inst_vec_cached,
      ils_vec=ils_vec_cached,
      steps=1,
      max_steps=loader_cached.get_max_steps(),
      mission_obs_mode=None,
    )
    self.assertIsInstance(cached_step_eval, dict)

    original_prepare = loader_cached._prepare_step_evaluation

    def _fail_prepare(*args, **kwargs): # pragma: no cover - defensive
      raise AssertionError("compute_full_step unexpectedly rebuilt step evaluation")

    loader_cached._prepare_step_evaluation = _fail_prepare # type: ignore[method-assign]
    try:
      reward_cached, terminated_cached, truncated_cached, status_cached = loader_cached.compute_full_step(
        obs_cached,
        sim_cached,
        1,
        loader_cached.get_max_steps(),
        truth=truth_cached,
        inst_state=inst_cached,
        step_evaluation=cached_step_eval,
      )
    finally:
      loader_cached._prepare_step_evaluation = original_prepare # type: ignore[method-assign]

    sim_fresh = ef_py.SimulationKernel()
    self.assertTrue(sim_fresh.load_database(resolve_repo_path("examples", "config", "database")))
    loader_fresh = ScenarioLoader(sim_fresh)
    loader_fresh.use_compiled_execution_step_runtime = True
    agent_id_fresh = loader_fresh.load_scenario_data(copy.deepcopy(_route_scenario()), seed=19)
    self.assertIsNotNone(agent_id_fresh)

    truth_fresh = sim_fresh.get_agent_observation(int(agent_id_fresh))
    inst_fresh = sim_fresh.get_instrument_state(int(agent_id_fresh))
    obs_fresh = build_universal_observation(
      loader_fresh,
      inst_fresh,
      truth_fresh,
      mission_obs_mode="nav_v2",
      max_contacts=10,
      max_rwr=4,
      include_proprio=False,
      last_action=None,
      action_space=None,
      steps=1,
      max_steps=loader_fresh.get_max_steps(),
    )
    reward_fresh, terminated_fresh, truncated_fresh, status_fresh = loader_fresh.compute_full_step(
      obs_fresh,
      sim_fresh,
      1,
      loader_fresh.get_max_steps(),
      truth=truth_fresh,
      inst_state=inst_fresh,
    )

    self.assertAlmostEqual(float(reward_cached), float(reward_fresh), places=6)
    self.assertEqual(bool(terminated_cached), bool(terminated_fresh))
    self.assertEqual(bool(truncated_cached), bool(truncated_fresh))
    self.assertEqual(list(status_cached), list(status_fresh))

  def test_prepare_step_evaluation_reuses_waypoint_guidance_state_within_step(self) -> None:
    sim = ef_py.SimulationKernel()
    self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))
    loader = ScenarioLoader(sim)
    loader.use_compiled_execution_step_runtime = True
    agent_id = loader.load_scenario_data(copy.deepcopy(_route_scenario()), seed=23)
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
    inst_vec = np.asarray(obs["instruments"], dtype=np.float32)
    ils_vec = np.asarray(inst_vec[-4:], dtype=np.float32) if inst_vec.size >= 4 else np.zeros((4,), dtype=np.float32)

    loader.reset_runtime_eval_cache()
    with mock.patch.object(
      loader,
      "_query_route_guidance_result",
      wraps=loader._query_route_guidance_result,
    ) as mocked_route_query:
      entry = loader._prepare_step_evaluation(
        truth=truth,
        inst_obj=inst,
        inst_vec=inst_vec,
        ils_vec=ils_vec,
        steps=1,
        max_steps=loader.get_max_steps(),
        mission_obs_mode=None,
      )

    self.assertIsInstance(entry, dict)
    self.assertLessEqual(mocked_route_query.call_count, 1)
    self.assertIn("waypoint_guidance_state", loader._runtime_eval_cache)

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

  def test_selected_paths_match_compiled_runtime_modes(self) -> None:
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
        python_step = self._run_loader_once(case["scenario"], seed=case["seed"], compiled=False)
        compiled = self._run_loader_once(case["scenario"], seed=case["seed"], compiled=True)
        self._assert_loader_results_match(python_step, compiled)
        if "terminated" in case:
          self.assertEqual(bool(compiled["terminated"]), bool(case["terminated"]))
        if "termination_reason" in case:
          self.assertEqual(str(compiled["termination_reason"]), str(case["termination_reason"]))

  def test_compute_full_step_rejects_missing_compiled_flight_shaping_products(self) -> None:
    sim = ef_py.SimulationKernel()
    self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))
    loader = ScenarioLoader(sim)
    loader.use_compiled_execution_step_runtime = False
    agent_id = loader.load_scenario_data(copy.deepcopy(_takeoff_shaping_scenario()), seed=37)
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

    with mock.patch.object(loader, "_compute_flight_shaping_products", return_value=None):
      with self.assertRaisesRegex(RuntimeError, "legacy flight shaping fallback has been removed"):
        loader.compute_full_step(obs, sim, 1, loader.get_max_steps())

  def test_flight_shaping_backends_match_compiled_reference(self) -> None:
    scenario = _takeoff_shaping_scenario()
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

    self._assert_loader_results_match(compiled_backend, gpu_backend)
    self._assert_loader_results_match(compiled_backend, compiled_runtime)
    self._assert_loader_results_match(compiled_backend, gpu_backend_with_compiled_runtime)

  def test_compiled_episode_runtime_prefers_cxx_reward_metadata(self) -> None:
    sim = ef_py.SimulationKernel()
    self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))
    loader = ScenarioLoader(sim)
    loader.use_compiled_execution_step_runtime = True
    agent_id = loader.load_scenario_data(copy.deepcopy(_takeoff_shaping_scenario()), seed=61)
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

    original = loader._apply_compiled_flight_shaping_terms

    def _unexpected_apply(*_args, **_kwargs):
      raise AssertionError("compiled default path should consume C++ reward breakdown metadata")

    loader._apply_compiled_flight_shaping_terms = _unexpected_apply
    try:
      reward, terminated, truncated, status = loader.compute_full_step(
        obs,
        sim,
        1,
        loader.get_max_steps(),
        truth=truth,
        inst_state=inst,
      )
    finally:
      loader._apply_compiled_flight_shaping_terms = original

    self.assertFalse(bool(terminated))
    self.assertFalse(bool(truncated))
    self.assertEqual(len(status), 4)
    self.assertIn("speed_reward", loader.last_reward_breakdown)
    self.assertAlmostEqual(float(loader.last_reward_breakdown["total"]), float(reward), places=6)
    self.assertEqual(
      str(loader.last_termination_reason),
      str(
        ef_py.termination_reason_name(
          loader._get_cached_step_evaluation()["frame_products"].final_reason_code
        )
      ),
    )

  def test_execution_episode_controller_shadow_matches_compiled_step_evaluation(self) -> None:
    cases = (
      ("objective", _objective_scenario(), 51),
      ("route", _route_scenario(), 52),
      ("approach", _approach_scenario(), 53),
      ("takeoff_shaping", _takeoff_shaping_scenario(), 54),
    )
    for case_name, scenario_data, seed in cases:
      with self.subTest(case=case_name):
        report = self._run_controller_shadow_once(scenario_data, seed=seed)
        comparison = dict(report["comparison"])
        self.assertTrue(bool(comparison["overall_match"]), msg=f"{case_name}: {comparison}")

  def test_execution_episode_controller_shadow_step_exports_advanced_state(self) -> None:
    report = self._run_controller_shadow_once(_route_scenario(), seed=55, steps=1, advance_state=True)
    comparison = dict(report["comparison"])
    self.assertTrue(bool(comparison["overall_match"]), msg=str(comparison))
    shadow_state = report["shadow_state"]
    shadow_products = report["shadow_frame_products"]
    self.assertEqual(int(shadow_state.step_count), 1)
    self.assertAlmostEqual(
      float(shadow_state.last_reward_total),
      float(shadow_products.compiled_reward_total),
      places=6,
    )
    self.assertEqual(
      str(shadow_state.last_termination_reason),
      str(ef_py.termination_reason_name(shadow_products.final_reason_code)),
    )


if __name__ == "__main__":
  unittest.main()
