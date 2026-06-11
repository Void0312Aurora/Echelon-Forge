from __future__ import annotations

import unittest
from types import SimpleNamespace

import numpy as np

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py # noqa: E402

from gym_envs.scenario_loader import ScenarioLoader # noqa: E402
from gym_envs.universal_env import UniversalEnv, build_universal_observation # noqa: E402
from gym_envs.universal_env_parts import AIR_COMBAT_HYBRID_V1_ACTION_MODE # noqa: E402
from python.mission_obs_taxonomy import ( # noqa: E402
  mission_observation_dim,
  mission_observation_field_index,
)


_DB_PATH = resolve_repo_path("examples", "config", "database")
_STAGE1_SCENARIO_PATH = resolve_repo_path(
  "scenarios",
  "air_combat",
  "1v1",
  "air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json",
)
_STAGE1_C2_ROE_SCENARIO_PATH = resolve_repo_path(
  "scenarios",
  "air_combat",
  "1v1",
  "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json",
)


def _hybrid_hold_action() -> np.ndarray:
  action = np.zeros((12,), dtype=np.float32)
  action[3] = 0.62
  action[6] = 1.0
  action[8] = 1.0
  action[11] = 1.0
  return action


def _wait_for_assigned_target_track(
  sim: ef_py.SimulationKernel,
  shooter_id: int,
  target_id: int,
  *,
  max_steps: int = 160,
) -> object:
  for _ in range(max_steps):
    sim.step()
    truth = sim.get_agent_observation(shooter_id)
    for track in getattr(truth, "contacts", []) or []:
      if int(getattr(track, "id", 0) or 0) == int(target_id):
        return truth
  raise AssertionError("expected assigned target track before A3 observation check")


class AirCombatC2RoeMissionObservationTests(unittest.TestCase):
  def test_air_combat_c2_roe_v1_exposes_command_and_release_discipline_fields(self) -> None:
    mode = "air_combat_c2_roe_v1"
    sim = ef_py.SimulationKernel()
    self.assertTrue(sim.load_database(_DB_PATH))

    loader = ScenarioLoader(sim)
    agent_id = int(loader.load_scenario(_STAGE1_SCENARIO_PATH, seed=20260603))
    target_id = int(loader.primary_target_id or 0)
    self.assertGreater(target_id, 0)

    loader.mission_cmd.update(
      {
        "roe_state": 2,
        "wcs_state": 2,
        "engagement_authority_holder_id": agent_id,
        "engagement_authority_grantor_id": 9001,
        "assigned_target_track_id": target_id,
        "assigned_target_source_id": 9002,
        "assigned_target_snapshot_time_s": 12.5,
        "target_identity_state": 3,
        "engage_order_state": 2,
        "shot_policy_state": 1,
        "shot_budget_remaining": 1,
        "pending_assessment": True,
        "own_missiles_in_flight_count": 0,
      }
    )
    truth = _wait_for_assigned_target_track(sim, agent_id, target_id)
    inst = sim.get_instrument_state(agent_id)

    obs = build_universal_observation(
      loader,
      inst,
      truth,
      mission_obs_mode=mode,
      max_contacts=10,
      max_rwr=4,
      include_proprio=False,
      last_action=None,
      action_space=None,
      steps=1,
      max_steps=loader.get_max_steps(),
    )
    mission = np.asarray(obs["mission"], dtype=np.float32)

    self.assertEqual(tuple(mission.shape), (mission_observation_dim(mode),))
    self.assertEqual(float(mission[mission_observation_field_index(mode, "roe_state")]), 2.0)
    self.assertEqual(float(mission[mission_observation_field_index(mode, "wcs_state")]), 2.0)
    self.assertEqual(float(mission[mission_observation_field_index(mode, "authorization_to_fire")]), 1.0)
    self.assertEqual(
      float(mission[mission_observation_field_index(mode, "engagement_authority_holder_id")]),
      float(agent_id),
    )
    self.assertEqual(float(mission[mission_observation_field_index(mode, "assigned_target_id")]), float(target_id))
    self.assertEqual(
      float(mission[mission_observation_field_index(mode, "assigned_target_track_id")]),
      float(target_id),
    )
    self.assertEqual(float(mission[mission_observation_field_index(mode, "target_identity_state")]), 3.0)
    self.assertEqual(float(mission[mission_observation_field_index(mode, "engage_order_state")]), 2.0)
    self.assertEqual(float(mission[mission_observation_field_index(mode, "shot_policy_state")]), 1.0)
    self.assertEqual(float(mission[mission_observation_field_index(mode, "shot_budget_remaining")]), 1.0)
    self.assertEqual(float(mission[mission_observation_field_index(mode, "pending_assessment")]), 1.0)
    self.assertEqual(float(mission[mission_observation_field_index(mode, "target_contact_present")]), 1.0)

  def test_air_combat_c2_roe_v1_defaults_to_fail_closed_shot_policy(self) -> None:
    mode = "air_combat_c2_roe_v1"
    sim = ef_py.SimulationKernel()
    self.assertTrue(sim.load_database(_DB_PATH))

    loader = ScenarioLoader(sim)
    agent_id = int(loader.load_scenario(_STAGE1_SCENARIO_PATH, seed=20260604))
    loader.mission_cmd["roe_state"] = 3
    truth = sim.get_agent_observation(agent_id)
    inst = sim.get_instrument_state(agent_id)

    mission = loader.get_mission_observation(mode, truth=truth, inst=inst)

    self.assertEqual(tuple(mission.shape), (mission_observation_dim(mode),))
    self.assertEqual(float(mission[mission_observation_field_index(mode, "roe_state")]), 3.0)
    self.assertEqual(float(mission[mission_observation_field_index(mode, "wcs_state")]), 1.0)
    self.assertEqual(float(mission[mission_observation_field_index(mode, "shot_policy_state")]), 0.0)
    self.assertEqual(float(mission[mission_observation_field_index(mode, "shot_budget_remaining")]), 0.0)
    self.assertEqual(float(mission[mission_observation_field_index(mode, "pending_assessment")]), 0.0)

  def test_air_combat_c2_roe_v1_reflects_runtime_single_shot_assessment_state(self) -> None:
    mode = "air_combat_c2_roe_v1"
    sim = ef_py.SimulationKernel()
    self.assertTrue(sim.load_database(_DB_PATH))

    loader = ScenarioLoader(sim)
    agent_id = int(loader.load_scenario(_STAGE1_SCENARIO_PATH, seed=20260605))
    loader.mission_cmd.update(
      {
        "roe_state": 2,
        "wcs_state": 2,
        "authorization_to_fire": True,
        "engage_order_state": 2,
        "shot_policy_state": 1,
        "shot_budget_remaining": 1,
        "pending_assessment": False,
        "own_missiles_in_flight_count": 0,
      }
    )
    loader._air_combat_reward_release_count = 1
    truth = sim.get_agent_observation(agent_id)
    inst = sim.get_instrument_state(agent_id)

    mission = loader.get_mission_observation(mode, truth=truth, inst=inst)

    self.assertEqual(float(mission[mission_observation_field_index(mode, "shot_policy_state")]), 1.0)
    self.assertEqual(float(mission[mission_observation_field_index(mode, "shot_budget_remaining")]), 0.0)
    self.assertEqual(float(mission[mission_observation_field_index(mode, "pending_assessment")]), 1.0)
    self.assertEqual(float(mission[mission_observation_field_index(mode, "own_missiles_in_flight_count")]), 1.0)

  def test_air_combat_c2_roe_v1_reflects_current_missile_delta_before_reward_runs(self) -> None:
    mode = "air_combat_c2_roe_v1"
    sim = ef_py.SimulationKernel()
    self.assertTrue(sim.load_database(_DB_PATH))

    loader = ScenarioLoader(sim)
    agent_id = int(loader.load_scenario(_STAGE1_SCENARIO_PATH, seed=20260606))
    loader.mission_cmd.update(
      {
        "roe_state": 2,
        "wcs_state": 2,
        "authorization_to_fire": True,
        "engage_order_state": 2,
        "shot_policy_state": 1,
        "shot_budget_remaining": 1,
        "pending_assessment": False,
        "own_missiles_in_flight_count": 0,
      }
    )
    loader._air_combat_reward_release_count = 0
    loader._air_combat_c2_roe_initial_missiles = 4
    truth = SimpleNamespace(missiles_remaining=3, contacts=[])
    inst = sim.get_instrument_state(agent_id)

    mission = loader.get_mission_observation(mode, truth=truth, inst=inst)

    self.assertEqual(float(mission[mission_observation_field_index(mode, "shot_policy_state")]), 1.0)
    self.assertEqual(float(mission[mission_observation_field_index(mode, "shot_budget_remaining")]), 0.0)
    self.assertEqual(float(mission[mission_observation_field_index(mode, "pending_assessment")]), 1.0)
    self.assertEqual(float(mission[mission_observation_field_index(mode, "own_missiles_in_flight_count")]), 1.0)

  def test_air_combat_c2_roe_v2_exposes_state_completion_window_fields(self) -> None:
    mode = "air_combat_c2_roe_v2"
    sim = ef_py.SimulationKernel()
    self.assertTrue(sim.load_database(_DB_PATH))

    loader = ScenarioLoader(sim)
    agent_id = int(loader.load_scenario(_STAGE1_SCENARIO_PATH, seed=20260607))
    target_id = int(loader.primary_target_id or 0)
    self.assertGreater(target_id, 0)
    loader.mission_cmd.update(
      {
        "roe_state": 2,
        "wcs_state": 2,
        "authorization_to_fire": True,
        "engagement_authority_holder_id": agent_id,
        "assigned_target_id": target_id,
        "engage_order_state": 2,
        "shot_policy_state": 1,
        "shot_budget_remaining": 1,
        "pending_assessment": False,
      }
    )
    truth = SimpleNamespace(
      missiles_remaining=4,
      contacts=[
        SimpleNamespace(
          id=target_id,
          range=15000.0,
          azimuth=0.0,
          elevation=0.0,
          closing_speed=0.0,
          time_since_update=0.5,
          classification=3,
        )
      ],
    )

    mission = None
    for step in range(32):
      loader.steps = step
      mission = loader.get_mission_observation(mode, truth=truth, inst=None)
    assert mission is not None

    self.assertEqual(tuple(mission.shape), (mission_observation_dim(mode),))
    self.assertEqual(float(mission[mission_observation_field_index(mode, "fire_mask_open")]), 1.0)
    self.assertEqual(float(mission[mission_observation_field_index(mode, "launch_window_open")]), 1.0)
    self.assertEqual(float(mission[mission_observation_field_index(mode, "quality_window_ready")]), 1.0)
    self.assertEqual(float(mission[mission_observation_field_index(mode, "legal_open_age_steps")]), 32.0)
    self.assertEqual(float(mission[mission_observation_field_index(mode, "legal_open_age_norm")]), 1.0)
    self.assertEqual(float(mission[mission_observation_field_index(mode, "launch_window_age_steps")]), 32.0)
    self.assertEqual(float(mission[mission_observation_field_index(mode, "target_range_m")]), 15000.0)
    self.assertEqual(float(mission[mission_observation_field_index(mode, "target_track_age_s")]), 0.5)

    repeated = loader.get_mission_observation(mode, truth=truth, inst=None)
    self.assertEqual(float(repeated[mission_observation_field_index(mode, "legal_open_age_steps")]), 32.0)

    loader.steps = 33
    stale_truth = SimpleNamespace(
      missiles_remaining=4,
      contacts=[
        SimpleNamespace(
          id=target_id,
          range=15000.0,
          azimuth=0.0,
          elevation=0.0,
          closing_speed=0.0,
          time_since_update=8.0,
          classification=3,
        )
      ],
    )
    stale_mission = loader.get_mission_observation(mode, truth=stale_truth, inst=None)
    self.assertEqual(float(stale_mission[mission_observation_field_index(mode, "fire_mask_open")]), 1.0)
    self.assertEqual(float(stale_mission[mission_observation_field_index(mode, "launch_window_open")]), 0.0)
    self.assertEqual(float(stale_mission[mission_observation_field_index(mode, "quality_window_ready")]), 0.0)
    self.assertEqual(float(stale_mission[mission_observation_field_index(mode, "legal_open_age_steps")]), 33.0)
    self.assertEqual(float(stale_mission[mission_observation_field_index(mode, "launch_window_age_steps")]), 0.0)

  def test_air_combat_c2_roe_v2_runtime_window_age_advances_with_env_steps(self) -> None:
    mode = "air_combat_c2_roe_v2"
    env = UniversalEnv(
      _STAGE1_C2_ROE_SCENARIO_PATH,
      include_visual=False,
      include_proprio=True,
      action_mode=AIR_COMBAT_HYBRID_V1_ACTION_MODE,
      mission_obs_mode=mode,
      runtime_compatibility_enabled=True,
    )
    try:
      obs, _info = env.reset(seed=20260608)
      max_legal_age = 0.0
      first_quality = None
      for step in range(1, 420):
        obs, _reward, terminated, truncated, _info = env.step(_hybrid_hold_action())
        mission = np.asarray(obs["mission"], dtype=np.float32)
        max_legal_age = max(
          max_legal_age,
          float(mission[mission_observation_field_index(mode, "legal_open_age_steps")]),
        )
        if float(mission[mission_observation_field_index(mode, "quality_window_ready")]) > 0.5:
          first_quality = (step, mission)
          break
        if terminated or truncated:
          break
      self.assertIsNotNone(first_quality)
      quality_step, quality_mission = first_quality
      self.assertGreaterEqual(quality_step, 1)
      self.assertGreater(max_legal_age, 0.0)
      self.assertEqual(float(quality_mission[mission_observation_field_index(mode, "fire_mask_open")]), 1.0)
      self.assertEqual(float(quality_mission[mission_observation_field_index(mode, "launch_window_open")]), 1.0)
      self.assertGreaterEqual(
        float(quality_mission[mission_observation_field_index(mode, "legal_open_age_steps")]),
        32.0,
      )
    finally:
      env.close()


if __name__ == "__main__":
  unittest.main()
