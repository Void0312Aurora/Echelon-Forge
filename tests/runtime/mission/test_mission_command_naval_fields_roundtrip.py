from __future__ import annotations

import json
import unittest

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

import ef_py  # noqa: E402


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


if __name__ == "__main__":
  unittest.main()
