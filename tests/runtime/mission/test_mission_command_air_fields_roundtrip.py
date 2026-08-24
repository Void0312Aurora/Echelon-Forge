from __future__ import annotations

import json
import unittest

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

import ef_py  # noqa: E402


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


if __name__ == "__main__":
  unittest.main()
