from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from gym_envs.scenario_loader import ScenarioLoader # noqa: E402
from gym_envs.universal_env import mission_observation_dim as env_mission_observation_dim # noqa: E402
from python.mission_obs_taxonomy import ( # noqa: E402
  AIR_COMBAT_MISSION_OBS_MODES,
  BASE_MISSION_OBS_MODES,
  COOPERATIVE_MISSION_OBS_MODES,
  NAVAL_MISSION_OBS_MODES,
  mission_observation_field_index,
  mission_observation_python_owned,
  mission_obs_mode_code,
  mission_observation_dim,
  mission_observation_field_names,
)


class MissionObservationTaxonomyTests(unittest.TestCase):
  def test_shared_taxonomy_matches_runtime_entrypoints(self) -> None:
    modes = (
      list(BASE_MISSION_OBS_MODES)
      + list(COOPERATIVE_MISSION_OBS_MODES)
      + list(NAVAL_MISSION_OBS_MODES)
      + list(AIR_COMBAT_MISSION_OBS_MODES)
    )
    self.assertEqual(
      modes,
      [
        "basic",
        "nav_v1",
        "nav_v2",
        "nav_v2_formation_v1",
        "nav_v2_formation_role_v1",
        "nav_v2_cooperative_takeoff_v1",
        "naval_screen_station_v1",
        "air_combat_c2_roe_v1",
        "air_combat_c2_roe_v2",
      ],
    )

    for expected_code, mode in enumerate(modes):
      fields = mission_observation_field_names(mode)
      self.assertEqual(mission_obs_mode_code(mode), expected_code)
      self.assertEqual(mission_observation_dim(mode), len(fields))
      self.assertEqual(env_mission_observation_dim(mode), len(fields))
      self.assertEqual(ScenarioLoader._mission_observation_mode_code(mode), expected_code)

    self.assertEqual(ScenarioLoader._mission_observation_mode_code(""), mission_obs_mode_code("basic"))

  def test_shared_taxonomy_keeps_expected_field_layouts(self) -> None:
    self.assertEqual(
      mission_observation_field_names("basic"),
      [
        "command_code",
        "target_heading_deg",
        "target_altitude_m",
        "target_speed_mps",
      ],
    )
    self.assertEqual(
      mission_observation_field_names("nav_v2")[4:],
      [
        "selected_steerpoint",
        "steerpoint_mode_code",
        "dist_m",
        "bearing_rel_deg",
        "altitude_delta_m",
        "cdi_norm",
        "track_angle_error_deg",
        "leg_distance_remaining_m",
        "next_turn_deg",
        "distance_to_turn_m",
      ],
    )
    self.assertEqual(
      mission_observation_field_names("nav_v2_formation_v1")[-3:],
      ["form_offset_x_m", "form_offset_y_m", "form_offset_z_m"],
    )
    self.assertEqual(
      mission_observation_field_names("nav_v2_formation_role_v1")[-4:],
      [
        "self_role_code",
        "self_formation_role_code",
        "relative_slot_code",
        "reference_relative_slot_code",
      ],
    )
    self.assertEqual(
      mission_observation_field_names("nav_v2_cooperative_takeoff_v1")[14:],
      [
        "takeoff_procedure_code",
        "takeoff_clearance_code",
        "takeoff_interval_s",
        "runway_slot_code",
        "form_offset_x_m",
        "form_offset_y_m",
        "form_offset_z_m",
        "self_role_code",
        "self_formation_role_code",
        "relative_slot_code",
        "reference_relative_slot_code",
      ],
    )
    self.assertEqual(mission_observation_field_index("basic", "command_code"), 0)
    self.assertEqual(mission_observation_field_index("nav_v2", "selected_steerpoint"), 4)
    self.assertEqual(mission_observation_field_index("nav_v2_formation_v1", "form_offset_x_m"), 14)
    self.assertEqual(mission_observation_field_index("nav_v2_formation_role_v1", "self_role_code"), 17)
    self.assertEqual(
      mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "takeoff_procedure_code"),
      14,
    )
    self.assertEqual(
      mission_observation_field_index("nav_v2_cooperative_takeoff_v1", "reference_relative_slot_code"),
      24,
    )

  def test_naval_screen_station_observation_has_domain_fields(self) -> None:
    mode = "naval_screen_station_v1"

    self.assertTrue(mission_observation_python_owned(mode))
    self.assertEqual(mission_observation_dim(mode), 23)
    self.assertEqual(env_mission_observation_dim(mode), 23)
    self.assertEqual(ScenarioLoader._mission_observation_mode_code(mode), 6)
    self.assertEqual(ScenarioLoader._python_owned_mission_observation_mode(mode), True)
    self.assertEqual(
      mission_observation_field_names(mode),
      [
        "command_code",
        "target_heading_deg",
        "target_speed_mps",
        "station_radius_m",
        "station_bearing_deg",
        "station_error_m",
        "station_error_norm",
        "screen_separation_m",
        "screen_separation_error_m",
        "own_relative_x_m",
        "own_relative_y_m",
        "desired_relative_x_m",
        "desired_relative_y_m",
        "target_contact_present",
        "support_track_present",
        "report_chain_seen",
        "roe_state",
        "authorization_to_fire",
        "assigned_target_id",
        "assigned_target_source_id",
        "self_role_code",
        "relative_slot_code",
        "reference_relative_slot_code",
      ],
    )
    self.assertEqual(mission_observation_field_index(mode, "station_radius_m"), 3)
    self.assertEqual(mission_observation_field_index(mode, "target_contact_present"), 13)
    self.assertEqual(mission_observation_field_index(mode, "roe_state"), 16)
    self.assertEqual(mission_observation_field_index(mode, "reference_relative_slot_code"), 22)

  def test_air_combat_c2_roe_observation_has_release_discipline_fields(self) -> None:
    mode = "air_combat_c2_roe_v1"

    self.assertTrue(mission_observation_python_owned(mode))
    self.assertEqual(mission_observation_dim(mode), 20)
    self.assertEqual(env_mission_observation_dim(mode), 20)
    self.assertEqual(ScenarioLoader._mission_observation_mode_code(mode), 7)
    self.assertEqual(ScenarioLoader._python_owned_mission_observation_mode(mode), True)
    self.assertEqual(
      mission_observation_field_names(mode),
      [
        "command_code",
        "target_heading_deg",
        "target_altitude_m",
        "target_speed_mps",
        "roe_state",
        "wcs_state",
        "authorization_to_fire",
        "engagement_authority_holder_id",
        "engagement_authority_grantor_id",
        "assigned_target_id",
        "assigned_target_track_id",
        "assigned_target_source_id",
        "assigned_target_snapshot_time_s",
        "target_identity_state",
        "engage_order_state",
        "shot_policy_state",
        "shot_budget_remaining",
        "pending_assessment",
        "own_missiles_in_flight_count",
        "target_contact_present",
      ],
    )
    self.assertEqual(mission_observation_field_index(mode, "roe_state"), 4)
    self.assertEqual(mission_observation_field_index(mode, "authorization_to_fire"), 6)
    self.assertEqual(mission_observation_field_index(mode, "shot_policy_state"), 15)
    self.assertEqual(mission_observation_field_index(mode, "target_contact_present"), 19)

  def test_air_combat_c2_roe_v2_adds_state_completion_fields(self) -> None:
    mode = "air_combat_c2_roe_v2"

    self.assertTrue(mission_observation_python_owned(mode))
    self.assertEqual(mission_observation_dim(mode), 29)
    self.assertEqual(env_mission_observation_dim(mode), 29)
    self.assertEqual(ScenarioLoader._mission_observation_mode_code(mode), 8)
    self.assertEqual(ScenarioLoader._python_owned_mission_observation_mode(mode), True)
    self.assertEqual(mission_observation_field_index(mode, "target_contact_present"), 19)
    self.assertEqual(mission_observation_field_index(mode, "fire_mask_open"), 20)
    self.assertEqual(mission_observation_field_index(mode, "launch_window_open"), 21)
    self.assertEqual(mission_observation_field_index(mode, "quality_window_ready"), 22)
    self.assertEqual(mission_observation_field_index(mode, "legal_open_age_steps"), 23)
    self.assertEqual(mission_observation_field_index(mode, "launch_window_age_steps"), 25)
    self.assertEqual(mission_observation_field_index(mode, "target_range_m"), 27)
    self.assertEqual(mission_observation_field_index(mode, "target_track_age_s"), 28)


if __name__ == "__main__":
  unittest.main()
