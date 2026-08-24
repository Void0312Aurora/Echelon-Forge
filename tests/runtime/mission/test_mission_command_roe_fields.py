from __future__ import annotations

import unittest
from types import SimpleNamespace

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

import ef_py # noqa: E402

from python.rl.profile.air_profile import build_kernel_mission_command as build_air_mission_command # noqa: E402
from python.rl.profile.naval_profile import build_kernel_mission_command as build_naval_mission_command # noqa: E402
from gym_envs.scenario_loader.runtime_state import apply_execution_episode_state # noqa: E402


class MissionCommandRoeFieldTests(unittest.TestCase):
  def test_execution_episode_equivalence_tracks_all_shared_target_provenance(self) -> None:
    changed_fields = {
      "threat_state": 4,
      "assigned_target_track_id": 5101,
      "assigned_target_source_id": 6101,
      "assigned_target_snapshot_time_s": 12.5,
    }

    for field_name, changed_value in changed_fields.items():
      lhs = ef_py.ExecutionEpisodeState()
      rhs = ef_py.ExecutionEpisodeState()
      lhs.has_mission_command = True
      rhs.has_mission_command = True

      with self.subTest(field_name=field_name):
        self.assertTrue(bool(ef_py.execution_episode_states_equivalent(lhs, rhs)))
        setattr(rhs.mission_command, field_name, changed_value)
        self.assertFalse(bool(ef_py.execution_episode_states_equivalent(lhs, rhs)))

  def test_python_bindings_expose_roe_and_engagement_authority_fields(self) -> None:
    cmd = ef_py.MissionCommand()
    cmd.roe_state = 2
    cmd.engagement_authority_holder_id = 4101
    cmd.engagement_authority_grantor_id = 3101
    cmd.threat_state = 5
    cmd.assigned_target_track_id = 4401
    cmd.assigned_target_source_id = 5101
    cmd.assigned_target_snapshot_time_s = 12.5

    intent = ef_py.LeaderIntent()
    intent.roe_state = 3
    intent.engagement_authority_holder_id = 4201
    intent.engagement_authority_grantor_id = 3201
    intent.threat_state = 6
    intent.assigned_target_track_id = 4501
    intent.assigned_target_source_id = 5201
    intent.assigned_target_snapshot_time_s = 13.5

    self.assertEqual(int(cmd.roe_state), 2)
    self.assertEqual(int(cmd.engagement_authority_holder_id), 4101)
    self.assertEqual(int(cmd.engagement_authority_grantor_id), 3101)
    self.assertEqual(int(cmd.threat_state), 5)
    self.assertEqual(int(cmd.assigned_target_track_id), 4401)
    self.assertEqual(int(cmd.assigned_target_source_id), 5101)
    self.assertAlmostEqual(float(cmd.assigned_target_snapshot_time_s), 12.5, places=6)
    self.assertEqual(int(intent.roe_state), 3)
    self.assertEqual(int(intent.engagement_authority_holder_id), 4201)
    self.assertEqual(int(intent.engagement_authority_grantor_id), 3201)
    self.assertEqual(int(intent.threat_state), 6)
    self.assertEqual(int(intent.assigned_target_track_id), 4501)
    self.assertEqual(int(intent.assigned_target_source_id), 5201)
    self.assertAlmostEqual(float(intent.assigned_target_snapshot_time_s), 13.5, places=6)

  def test_air_profile_build_kernel_mission_command_propagates_roe_fields(self) -> None:
    leader_intent = SimpleNamespace(
      command_code=2,
      cmd_heading_deg=67.0,
      cmd_altitude_m=2100.0,
      cmd_speed_mps=205.0,
      roe_state=2,
      engagement_authority_holder_id=7101,
      engagement_authority_grantor_id=7001,
      assigned_target_id=4401,
      authorization_to_fire=True,
    )
    loader = SimpleNamespace(
      mission_cmd={
        "command_code": 2,
        "target_heading": 123.0,
        "target_altitude": 3100.0,
        "target_speed": 222.0,
        "roe_state": 1,
        "engagement_authority_holder_id": 6101,
        "engagement_authority_grantor_id": 6001,
        "assigned_target_id": 4001,
        "authorization_to_fire": False,
      },
      leader_intent=leader_intent,
      task_order=None,
      waypoints=[],
    )

    cmd = build_air_mission_command(loader)
    self.assertEqual(int(cmd.roe_state), 2)
    self.assertEqual(int(cmd.engagement_authority_holder_id), 7101)
    self.assertEqual(int(cmd.engagement_authority_grantor_id), 7001)
    self.assertEqual(int(cmd.assigned_target_id), 4401)
    self.assertTrue(bool(cmd.authorization_to_fire))

  def test_naval_profile_build_kernel_mission_command_propagates_roe_fields(self) -> None:
    task = ef_py.TaskOrder()
    task.service_profile = ef_py.ServiceProfile.Navy
    task.task_family = ef_py.TaskFamily.Escort
    task.coordination_mode = ef_py.CoordinationMode.Screen
    task.station_heading_deg = 35.0
    task.station_radius_m = 14000.0
    task.target_speed_mps = 12.5
    task.target_altitude_m = 0.0

    agent_member = type("_Member", (), {"entity_id": 5101, "reference_entity_id": 5201})()
    loader = type(
      "_Loader",
      (),
      {
        "scenario_data": {
          "mission_command": {
            "reference_entity_id": 6201,
            "station_radius_m": 16000.0,
            "station_bearing_deg": 75.0,
            "target_heading": 80.0,
            "target_speed": 14.0,
            "roe_state": 3,
            "engagement_authority_holder_id": 8201,
            "engagement_authority_grantor_id": 8101,
            "assigned_target_id": 8301,
            "threat_state": 7,
            "assigned_target_track_id": 8301,
            "assigned_target_source_id": 5101,
            "assigned_target_snapshot_time_s": 24.5,
            "authorization_to_fire": True,
          }
        },
        "task_order": task,
        "mission_cmd": {
          "roe_state": 1,
          "engagement_authority_holder_id": 7201,
          "engagement_authority_grantor_id": 7101,
          "assigned_target_id": 7301,
          "threat_state": 4,
          "assigned_target_track_id": 7301,
          "assigned_target_source_id": 4101,
          "assigned_target_snapshot_time_s": 20.0,
          "authorization_to_fire": False,
        },
        "agent_id": 5101,
        "active_roster": [agent_member],
        "get_active_roster_member": staticmethod(lambda entity_id=None, entity_name=None: agent_member),
      },
    )()

    cmd = build_naval_mission_command(loader)

    self.assertEqual(int(cmd.roe_state), 3)
    self.assertEqual(int(cmd.engagement_authority_holder_id), 8201)
    self.assertEqual(int(cmd.engagement_authority_grantor_id), 8101)
    self.assertEqual(int(cmd.assigned_target_id), 8301)
    self.assertEqual(int(cmd.threat_state), 7)
    self.assertEqual(int(cmd.assigned_target_track_id), 8301)
    self.assertEqual(int(cmd.assigned_target_source_id), 5101)
    self.assertAlmostEqual(float(cmd.assigned_target_snapshot_time_s), 24.5, places=6)
    self.assertTrue(bool(cmd.authorization_to_fire))

  def test_runtime_state_fallback_preserves_threat_and_assigned_target_provenance(self) -> None:
    episode_state = ef_py.ExecutionEpisodeState()
    episode_state.has_mission_command = True
    episode_state.has_mission_command_json = False
    episode_state.mission_command.command_code = 3
    episode_state.mission_command.assigned_target_id = 9101
    episode_state.mission_command.threat_state = 8
    episode_state.mission_command.assigned_target_track_id = 9101
    episode_state.mission_command.assigned_target_source_id = 5101
    episode_state.mission_command.assigned_target_snapshot_time_s = 33.25
    episode_state.mission_command.authorization_to_fire = False
    episode_state.mission_command.active = True

    loader = SimpleNamespace(
      agent_id=None,
      steps=0,
      scenario_data={},
      route_waypoints=[],
      waypoints=[],
      waypoint_idx=0,
      waypoint_total_route_length_m=0.0,
      _waypoint_prev_dist_m=None,
      _waypoint_leg_origin_x=0.0,
      _waypoint_leg_origin_y=0.0,
      prev_alt=0.0,
      prev_speed=0.0,
      liftoff_awarded=False,
      gear_bonus_awarded=False,
      off_runway_steps=0,
      _approach_prev_dme_m=None,
      _approach_prev_loc_abs=None,
      _approach_prev_gs_abs=None,
      post_waypoint_transition=None,
      mission_phase_name="idle",
      _cached_route_ref_id=None,
      last_reward_breakdown={},
      last_termination_reason="idle",
      task_order=None,
      leader_intent=None,
      _rebuild_spatial_geometry=lambda: None,
    )

    apply_execution_episode_state(loader, episode_state)

    self.assertEqual(int(loader.mission_cmd["assigned_target_id"]), 9101)
    self.assertEqual(int(loader.mission_cmd["threat_state"]), 8)
    self.assertEqual(int(loader.mission_cmd["assigned_target_track_id"]), 9101)
    self.assertEqual(int(loader.mission_cmd["assigned_target_source_id"]), 5101)
    self.assertAlmostEqual(float(loader.mission_cmd["assigned_target_snapshot_time_s"]), 33.25, places=6)


if __name__ == "__main__":
  unittest.main()
