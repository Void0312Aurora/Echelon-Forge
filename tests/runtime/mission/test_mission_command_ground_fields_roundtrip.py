from __future__ import annotations

import json
import unittest

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import ef_py # noqa: E402


class MissionCommandGroundFieldRoundtripTests(unittest.TestCase):
  def test_mission_command_python_bindings_expose_ground_static_task_fields(self) -> None:
    cmd = ef_py.MissionCommand()
    cmd.ground_task_mode = ef_py.GroundTaskMode.OccupyStatic
    cmd.objective_area_id = 7101
    cmd.objective_node_id = 7201
    cmd.ground_commander_id = 7301
    cmd.tactical_cadence_hz = 1.0

    directive = ef_py.mission_command_ground_static_task_directive(cmd)
    self.assertEqual(directive.ground_task_mode, ef_py.GroundTaskMode.OccupyStatic)
    self.assertEqual(int(directive.objective_area_id), 7101)
    self.assertEqual(int(directive.objective_node_id), 7201)
    self.assertEqual(int(directive.ground_commander_id), 7301)
    self.assertAlmostEqual(float(directive.tactical_cadence_hz), 1.0, places=6)

    ground = ef_py.mission_command_ground_owner_slice(cmd)
    ground.objective_area_id = 7102
    self.assertEqual(int(cmd.objective_area_id), 7102)

  def test_execution_episode_state_equivalence_tracks_ground_static_task_fields(self) -> None:
    lhs = ef_py.ExecutionEpisodeState()
    rhs = ef_py.ExecutionEpisodeState()

    for state in (lhs, rhs):
      state.has_mission_command = True
      state.mission_command.command_code = 2
      state.mission_command.ground_task_mode = ef_py.GroundTaskMode.SupportStatic
      state.mission_command.objective_area_id = 8101
      state.mission_command.objective_node_id = 8201
      state.mission_command.ground_commander_id = 8301
      state.mission_command.tactical_cadence_hz = 1.0
      state.mission_command.active = True
      state.has_mission_command_json = True
      state.mission_command_json = json.dumps(
        {
          "command_code": 2,
          "ground_task_mode": int(ef_py.GroundTaskMode.SupportStatic),
          "objective_area_id": 8101,
          "objective_node_id": 8201,
          "ground_commander_id": 8301,
          "tactical_cadence_hz": 1.0,
          "active": True,
        },
        ensure_ascii=True,
        sort_keys=True,
      )

    self.assertTrue(bool(ef_py.execution_episode_states_equivalent(lhs, rhs)))

    rhs.mission_command.objective_node_id = 8202
    self.assertFalse(bool(ef_py.execution_episode_states_equivalent(lhs, rhs)))

  def test_existing_state_json_is_backfilled_from_ground_static_task_fields(self) -> None:
    state = ef_py.ExecutionEpisodeState()
    state.has_mission_command = True
    state.mission_command.command_code = 2
    state.mission_command.ground_task_mode = ef_py.GroundTaskMode.MoveStatic
    state.mission_command.objective_area_id = 9101
    state.mission_command.objective_node_id = 9201
    state.mission_command.ground_commander_id = 9301
    state.mission_command.tactical_cadence_hz = 1.0
    state.mission_command.active = True
    state.has_mission_command_json = True
    state.mission_command_json = json.dumps(
      {
        "command_code": 2,
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
    self.assertEqual(int(mission_json["ground_task_mode"]), int(ef_py.GroundTaskMode.MoveStatic))
    self.assertEqual(int(mission_json["objective_area_id"]), 9101)
    self.assertEqual(int(mission_json["objective_node_id"]), 9201)
    self.assertEqual(int(mission_json["ground_commander_id"]), 9301)
    self.assertAlmostEqual(float(mission_json["tactical_cadence_hz"]), 1.0, places=6)


if __name__ == "__main__":
  unittest.main()
