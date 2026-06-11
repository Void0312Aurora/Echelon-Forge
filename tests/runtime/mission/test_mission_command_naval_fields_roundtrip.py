from __future__ import annotations

import json
import unittest

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import ef_py # noqa: E402


class MissionCommandNavalFieldRoundtripTests(unittest.TestCase):
  def test_execution_episode_state_equivalence_tracks_naval_mission_fields(self) -> None:
    lhs = ef_py.ExecutionEpisodeState()
    rhs = ef_py.ExecutionEpisodeState()

    for state in (lhs, rhs):
      state.has_mission_command = True
      state.mission_command.command_code = 3
      state.mission_command.cmd_heading_deg = 82.0
      state.mission_command.cmd_altitude_m = 0.0
      state.mission_command.cmd_speed_mps = 12.0
      state.mission_command.route_ref_id = 77
      state.mission_command.reference_entity_id = 5201
      state.mission_command.station_radius_m = 14500.0
      state.mission_command.station_bearing_deg = 35.0
      state.mission_command.embarked_helo_entity_id = 9301
      state.mission_command.launch_helo = True
      state.mission_command.recover_helo = False
      state.mission_command.relay_oth_targeting = True
      state.mission_command.active = True
      state.has_mission_command_json = True
      state.mission_command_json = json.dumps(
        {
          "command_code": 3,
          "target_heading": 82.0,
          "target_altitude": 0.0,
          "target_speed": 12.0,
          "route_ref_id": 77,
          "reference_entity_id": 5201,
          "station_radius_m": 14500.0,
          "station_bearing_deg": 35.0,
          "embarked_helo_entity_id": 9301,
          "launch_helo": True,
          "recover_helo": False,
          "relay_oth_targeting": True,
          "active": True,
        },
        ensure_ascii=True,
        sort_keys=True,
      )

    self.assertTrue(bool(ef_py.execution_episode_states_equivalent(lhs, rhs)))

    rhs.mission_command.station_bearing_deg = 40.0
    self.assertFalse(bool(ef_py.execution_episode_states_equivalent(lhs, rhs)))

  def test_post_transition_roundtrip_preserves_naval_mission_fields(self) -> None:
    controller = ef_py.ExecutionEpisodeController()

    episode_state = ef_py.ExecutionEpisodeState()
    episode_state.has_mission_command = True
    episode_state.mission_command.command_code = 3
    episode_state.mission_command.cmd_heading_deg = 90.0
    episode_state.mission_command.cmd_altitude_m = 0.0
    episode_state.mission_command.cmd_speed_mps = 14.0
    episode_state.mission_command.route_ref_id = 77
    episode_state.mission_command.reference_entity_id = 5201
    episode_state.mission_command.station_radius_m = 14000.0
    episode_state.mission_command.station_bearing_deg = 30.0
    episode_state.mission_command.embarked_helo_entity_id = 9101
    episode_state.mission_command.launch_helo = False
    episode_state.mission_command.recover_helo = False
    episode_state.mission_command.relay_oth_targeting = False
    episode_state.mission_command.active = True
    episode_state.has_mission_command_json = True
    episode_state.mission_command_json = json.dumps(
      {
        "command_code": 3,
        "target_heading": 90.0,
        "target_altitude": 0.0,
        "target_speed": 14.0,
        "route_ref_id": 77,
        "reference_entity_id": 5201,
        "station_radius_m": 14000.0,
        "station_bearing_deg": 30.0,
        "embarked_helo_entity_id": 9101,
        "launch_helo": False,
        "recover_helo": False,
        "relay_oth_targeting": False,
        "waypoint_mode": "flyby",
        "waypoints": [
          {"x": -1350.0, "y": 0.0, "z": 0.0, "radius_m": 1200.0, "speed_mps": 14.0},
        ],
      },
      ensure_ascii=True,
      sort_keys=True,
    )
    route_waypoint = ef_py.SpatialRouteWaypoint()
    route_waypoint.x_m = -1350.0
    route_waypoint.y_m = 0.0
    route_waypoint.z_m = 0.0
    route_waypoint.radius_m = 1200.0
    route_waypoint.altitude_m = 0.0
    route_waypoint.speed_mps = 14.0
    route_waypoint.waypoint_mode = "flyby"
    episode_state.route_waypoints = [route_waypoint]
    episode_state.waypoint_index = 0
    episode_state.has_post_waypoint_transition_json = True
    episode_state.post_waypoint_transition_json = json.dumps(
      {
        "command_code": 2,
        "phase_name": "post_route",
        "target_altitude": 0.0,
        "target_heading": 45.0,
        "target_speed": 11.0,
        "reference_entity_id": 6201,
        "station_radius_m": 16000.0,
        "station_bearing_deg": 75.0,
        "embarked_helo_entity_id": 9201,
        "launch_helo": True,
        "recover_helo": False,
        "relay_oth_targeting": True,
        "transition_reward": 10.0,
      },
      ensure_ascii=True,
      sort_keys=True,
    )
    controller.import_state(episode_state)

    env_state = ef_py.StepEvaluationBatchEnvState()
    env_state.steps = 1
    env_state.truth_x = -1400.0
    env_state.truth_y = 0.0
    env_state.truth_z = 0.0
    env_state.truth_speed = 14.0
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
    self.assertEqual(int(result.controller_state.mission_command.reference_entity_id), 6201)
    self.assertAlmostEqual(float(result.controller_state.mission_command.station_radius_m), 16000.0, places=6)
    self.assertAlmostEqual(float(result.controller_state.mission_command.station_bearing_deg), 75.0, places=6)
    self.assertEqual(int(result.controller_state.mission_command.embarked_helo_entity_id), 9201)
    self.assertTrue(bool(result.controller_state.mission_command.launch_helo))
    self.assertFalse(bool(result.controller_state.mission_command.recover_helo))
    self.assertTrue(bool(result.controller_state.mission_command.relay_oth_targeting))

    mission_json = json.loads(str(result.controller_state.mission_command_json))
    self.assertEqual(int(mission_json["reference_entity_id"]), 6201)
    self.assertAlmostEqual(float(mission_json["station_radius_m"]), 16000.0, places=6)
    self.assertAlmostEqual(float(mission_json["station_bearing_deg"]), 75.0, places=6)
    self.assertEqual(int(mission_json["embarked_helo_entity_id"]), 9201)
    self.assertTrue(bool(mission_json["launch_helo"]))
    self.assertFalse(bool(mission_json["recover_helo"]))
    self.assertTrue(bool(mission_json["relay_oth_targeting"]))

  def test_existing_state_json_is_backfilled_from_naval_mission_command_fields(self) -> None:
    state = ef_py.ExecutionEpisodeState()
    state.has_mission_command = True
    state.mission_command.command_code = 3
    state.mission_command.cmd_heading_deg = 82.0
    state.mission_command.cmd_altitude_m = 0.0
    state.mission_command.cmd_speed_mps = 14.0
    state.mission_command.route_ref_id = 77
    state.mission_command.reference_entity_id = 5201
    state.mission_command.station_radius_m = 14500.0
    state.mission_command.station_bearing_deg = 35.0
    state.mission_command.embarked_helo_entity_id = 9301
    state.mission_command.launch_helo = True
    state.mission_command.recover_helo = False
    state.mission_command.relay_oth_targeting = True
    state.mission_command.active = True
    state.has_mission_command_json = True
    state.mission_command_json = json.dumps(
      {
        "command_code": 3,
        "target_heading": 82.0,
        "target_altitude": 0.0,
        "target_speed": 14.0,
        "route_ref_id": 77,
        "reference_entity_id": 5201,
        "station_radius_m": 14500.0,
        "station_bearing_deg": 35.0,
        "active": True,
      },
      ensure_ascii=True,
      sort_keys=True,
    )

    controller = ef_py.ExecutionEpisodeController()
    controller.import_state(state)

    exported = controller.export_state()

    self.assertTrue(bool(exported.has_mission_command_json))
    mission_json = json.loads(str(exported.mission_command_json))
    self.assertEqual(int(mission_json["reference_entity_id"]), 5201)
    self.assertAlmostEqual(float(mission_json["station_radius_m"]), 14500.0, places=6)
    self.assertAlmostEqual(float(mission_json["station_bearing_deg"]), 35.0, places=6)
    self.assertEqual(int(mission_json["embarked_helo_entity_id"]), 9301)
    self.assertTrue(bool(mission_json["launch_helo"]))
    self.assertFalse(bool(mission_json["recover_helo"]))
    self.assertTrue(bool(mission_json["relay_oth_targeting"]))


if __name__ == "__main__":
  unittest.main()
