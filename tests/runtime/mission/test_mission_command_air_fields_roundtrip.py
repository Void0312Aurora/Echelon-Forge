from __future__ import annotations

import json
import unittest

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import ef_py # noqa: E402


class MissionCommandAirFieldRoundtripTests(unittest.TestCase):
  def test_execution_episode_state_equivalence_tracks_air_mission_fields(self) -> None:
    lhs = ef_py.ExecutionEpisodeState()
    rhs = ef_py.ExecutionEpisodeState()

    for state in (lhs, rhs):
      state.has_mission_command = True
      state.mission_command.command_code = 4
      state.mission_command.cmd_heading_deg = 178.0
      state.mission_command.cmd_altitude_m = 900.0
      state.mission_command.cmd_speed_mps = 155.0
      state.mission_command.route_ref_id = 77
      state.mission_command.recovery_base_id = 501
      state.mission_command.recovery_runway_id = 17
      state.mission_command.recovery_approach_type = ef_py.RecoveryApproachType.ILS
      state.mission_command.takeoff_procedure_id = ef_py.TakeoffProcedureType.Interval
      state.mission_command.takeoff_clearance_id = ef_py.TakeoffClearanceState.LineUpAndWait
      state.mission_command.takeoff_interval_s = 6.5
      state.mission_command.runway_slot_id = ef_py.RunwaySlotPosition.Left
      state.mission_command.formation_id = 19
      state.mission_command.form_offset_x = 220.0
      state.mission_command.form_offset_y = -75.0
      state.mission_command.form_offset_z = 18.0
      state.mission_command.active = True
      state.has_mission_command_json = True
      state.mission_command_json = json.dumps(
        {
          "command_code": 4,
          "target_heading": 178.0,
          "target_altitude": 900.0,
          "target_speed": 155.0,
          "route_ref_id": 77,
          "recovery_base_id": 501,
          "recovery_runway_id": 17,
          "recovery_approach_type": "ILS",
          "takeoff_procedure_code": int(ef_py.TakeoffProcedureType.Interval),
          "takeoff_clearance_code": int(ef_py.TakeoffClearanceState.LineUpAndWait),
          "takeoff_interval_s": 6.5,
          "runway_slot_code": int(ef_py.RunwaySlotPosition.Left),
          "formation_id": 19,
          "form_offset_x": 220.0,
          "form_offset_y": -75.0,
          "form_offset_z": 18.0,
          "active": True,
        },
        ensure_ascii=True,
        sort_keys=True,
      )

    self.assertTrue(bool(ef_py.execution_episode_states_equivalent(lhs, rhs)))

    rhs.mission_command.form_offset_z = 24.0
    self.assertFalse(bool(ef_py.execution_episode_states_equivalent(lhs, rhs)))

  def test_post_transition_roundtrip_preserves_air_mission_fields(self) -> None:
    controller = ef_py.ExecutionEpisodeController()

    episode_state = ef_py.ExecutionEpisodeState()
    episode_state.has_mission_command = True
    episode_state.mission_command.command_code = 3
    episode_state.mission_command.cmd_heading_deg = 90.0
    episode_state.mission_command.cmd_altitude_m = 1200.0
    episode_state.mission_command.cmd_speed_mps = 180.0
    episode_state.mission_command.route_ref_id = 77
    episode_state.mission_command.active = True
    episode_state.has_mission_command_json = True
    episode_state.mission_command_json = json.dumps(
      {
        "command_code": 3,
        "target_heading": 90.0,
        "target_altitude": 1200.0,
        "target_speed": 180.0,
        "route_ref_id": 77,
        "waypoint_mode": "flyby",
        "waypoints": [
          {"x": -1350.0, "y": 0.0, "z": 1200.0, "radius_m": 1200.0, "speed_mps": 180.0},
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
    episode_state.waypoint_index = 1
    episode_state.has_post_waypoint_transition_json = True
    episode_state.post_waypoint_transition_json = json.dumps(
      {
        "command_code": 4,
        "phase_name": "landing_final",
        "target_altitude": 900.0,
        "target_heading": 178.0,
        "target_speed": 155.0,
        "route_ref_id": 901,
        "recovery_base_id": 501,
        "recovery_runway_id": 17,
        "recovery_approach_type": "ILS",
        "takeoff_procedure_code": int(ef_py.TakeoffProcedureType.Interval),
        "takeoff_clearance_code": int(ef_py.TakeoffClearanceState.LineUpAndWait),
        "takeoff_interval_s": 6.5,
        "runway_slot_code": int(ef_py.RunwaySlotPosition.Left),
        "formation_id": 19,
        "form_offset_x": 220.0,
        "form_offset_y": -75.0,
        "form_offset_z": 18.0,
        "transition_reward": 10.0,
      },
      ensure_ascii=True,
      sort_keys=True,
    )
    controller.import_state(episode_state)

    env_state = ef_py.StepEvaluationBatchEnvState()
    env_state.steps = 6
    env_state.truth_x = -500.0
    env_state.truth_y = 0.0
    env_state.truth_z = 1200.0
    env_state.truth_speed = 180.0
    env_state.truth_heading = 178.0
    env_state.ils_vec = [1.0, 0.0, 0.0, 10000.0]
    inst_vec = [0.0] * 42
    inst_vec[9] = 178.0
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
    env_state.step_info.runway_frame.heading_deg = 178.0

    result = controller.step_result(ef_py.StepEvaluationBatchConfig(), env_state)

    self.assertTrue(bool(result.valid))
    self.assertEqual(int(result.controller_state.mission_command.command_code), 4)
    self.assertEqual(int(result.controller_state.mission_command.route_ref_id), 0)
    self.assertEqual(int(result.controller_state.mission_command.recovery_base_id), 501)
    self.assertEqual(int(result.controller_state.mission_command.recovery_runway_id), 17)
    self.assertEqual(result.controller_state.mission_command.recovery_approach_type, ef_py.RecoveryApproachType.ILS)
    self.assertEqual(result.controller_state.mission_command.takeoff_procedure_id, ef_py.TakeoffProcedureType.Interval)
    self.assertEqual(
      result.controller_state.mission_command.takeoff_clearance_id,
      ef_py.TakeoffClearanceState.LineUpAndWait,
    )
    self.assertAlmostEqual(float(result.controller_state.mission_command.takeoff_interval_s), 6.5, places=6)
    self.assertEqual(result.controller_state.mission_command.runway_slot_id, ef_py.RunwaySlotPosition.Left)
    self.assertEqual(int(result.controller_state.mission_command.formation_id), 19)
    self.assertAlmostEqual(float(result.controller_state.mission_command.form_offset_x), 220.0, places=6)
    self.assertAlmostEqual(float(result.controller_state.mission_command.form_offset_y), -75.0, places=6)
    self.assertAlmostEqual(float(result.controller_state.mission_command.form_offset_z), 18.0, places=6)

    mission_json = json.loads(str(result.controller_state.mission_command_json))
    self.assertEqual(int(mission_json["route_ref_id"]), 901)
    self.assertEqual(int(mission_json["recovery_base_id"]), 501)
    self.assertEqual(int(mission_json["recovery_runway_id"]), 17)
    self.assertEqual(str(mission_json["recovery_approach_type"]), "ILS")
    self.assertEqual(int(mission_json["takeoff_procedure_code"]), int(ef_py.TakeoffProcedureType.Interval))
    self.assertEqual(
      int(mission_json["takeoff_clearance_code"]),
      int(ef_py.TakeoffClearanceState.LineUpAndWait),
    )
    self.assertAlmostEqual(float(mission_json["takeoff_interval_s"]), 6.5, places=6)
    self.assertEqual(int(mission_json["runway_slot_code"]), int(ef_py.RunwaySlotPosition.Left))
    self.assertEqual(int(mission_json["formation_id"]), 19)
    self.assertAlmostEqual(float(mission_json["form_offset_x"]), 220.0, places=6)
    self.assertAlmostEqual(float(mission_json["form_offset_y"]), -75.0, places=6)
    self.assertAlmostEqual(float(mission_json["form_offset_z"]), 18.0, places=6)

  def test_existing_state_json_is_backfilled_from_air_mission_command_fields(self) -> None:
    state = ef_py.ExecutionEpisodeState()
    state.has_mission_command = True
    state.mission_command.command_code = 4
    state.mission_command.cmd_heading_deg = 178.0
    state.mission_command.cmd_altitude_m = 900.0
    state.mission_command.cmd_speed_mps = 155.0
    state.mission_command.route_ref_id = 77
    state.mission_command.recovery_base_id = 501
    state.mission_command.recovery_runway_id = 17
    state.mission_command.recovery_approach_type = ef_py.RecoveryApproachType.ILS
    state.mission_command.takeoff_procedure_id = ef_py.TakeoffProcedureType.Interval
    state.mission_command.takeoff_clearance_id = ef_py.TakeoffClearanceState.LineUpAndWait
    state.mission_command.takeoff_interval_s = 6.5
    state.mission_command.runway_slot_id = ef_py.RunwaySlotPosition.Left
    state.mission_command.formation_id = 19
    state.mission_command.form_offset_x = 220.0
    state.mission_command.form_offset_y = -75.0
    state.mission_command.form_offset_z = 18.0
    state.mission_command.active = True
    state.has_mission_command_json = True
    state.mission_command_json = json.dumps(
      {
        "command_code": 4,
        "target_heading": 178.0,
        "target_altitude": 900.0,
        "target_speed": 155.0,
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
    self.assertEqual(int(mission_json["route_ref_id"]), 77)
    self.assertEqual(int(mission_json["recovery_base_id"]), 501)
    self.assertEqual(int(mission_json["recovery_runway_id"]), 17)
    self.assertEqual(str(mission_json["recovery_approach_type"]), "ILS")
    self.assertEqual(int(mission_json["takeoff_procedure_code"]), int(ef_py.TakeoffProcedureType.Interval))
    self.assertEqual(
      int(mission_json["takeoff_clearance_code"]),
      int(ef_py.TakeoffClearanceState.LineUpAndWait),
    )
    self.assertAlmostEqual(float(mission_json["takeoff_interval_s"]), 6.5, places=6)
    self.assertEqual(int(mission_json["runway_slot_code"]), int(ef_py.RunwaySlotPosition.Left))
    self.assertEqual(int(mission_json["formation_id"]), 19)
    self.assertAlmostEqual(float(mission_json["form_offset_x"]), 220.0, places=6)
    self.assertAlmostEqual(float(mission_json["form_offset_y"]), -75.0, places=6)
    self.assertAlmostEqual(float(mission_json["form_offset_z"]), 18.0, places=6)


if __name__ == "__main__":
  unittest.main()
