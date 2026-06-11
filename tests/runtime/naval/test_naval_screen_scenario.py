from __future__ import annotations

import json
import math
import unittest

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py # noqa: E402

from gym_envs.scenario_loader import ScenarioLoader # noqa: E402

_REPORT_TRACK_MSG_TYPE = int(getattr(ef_py.CommMsgType, "ReportTrack", getattr(ef_py.CommMsgType, "ReportContact")))


_SCENARIO_PATH = resolve_repo_path(
  "scenarios",
  "naval",
  "ddg51_take1_screen_contact_report_v1.json",
)
_CLOSING_SCENARIO_PATH = resolve_repo_path(
  "scenarios",
  "naval",
  "ddg51_take1_screen_closing_contact_v1.json",
)
_DB_PATH = resolve_repo_path("examples", "config", "database")


class NavalScreenScenarioTests(unittest.TestCase):
  def _scenario_entities(self, path: str) -> dict[str, dict]:
    with open(path, "r", encoding="utf-8") as handle:
      scenario = json.load(handle)
    return {
      str(entity["name"]): entity
      for entity in scenario.get("entities", [])
      if isinstance(entity, dict) and "name" in entity
    }

  def test_loader_fixture_applies_naval_screen_semantics(self) -> None:
    sim = ef_py.SimulationKernel()
    self.assertTrue(sim.load_database(_DB_PATH))

    loader = ScenarioLoader(sim)
    agent_id = int(loader.load_scenario(_SCENARIO_PATH, seed=20260516))
    self.assertGreater(agent_id, 0)
    self.assertEqual(agent_id, int(loader.entities["Blue_Screen_DDG51"]))
    self.assertIn("Blue_HVU_TAKE1", loader.entities)
    self.assertIn("Red_Surface_Contact", loader.entities)

    self.assertEqual(len(loader.active_roster), 2)
    ddg_member = loader.get_active_roster_member(entity_name="Blue_Screen_DDG51")
    hvu_member = loader.get_active_roster_member(entity_name="Blue_HVU_TAKE1")
    self.assertIsNotNone(ddg_member)
    self.assertIsNotNone(hvu_member)
    self.assertTrue(bool(ddg_member.is_agent))
    self.assertFalse(bool(hvu_member.is_agent))
    self.assertEqual(int(hvu_member.reference_entity_id), int(ddg_member.entity_id))

    task = sim.get_task_order(agent_id)
    report = sim.get_pilot_report(agent_id)
    self.assertTrue(bool(task.active))
    self.assertEqual(task.service_profile, ef_py.ServiceProfile.Navy)
    self.assertEqual(task.task_family, ef_py.TaskFamily.Escort)
    self.assertEqual(task.coordination_mode, ef_py.CoordinationMode.Screen)
    self.assertEqual(int(task.warfare_role_code), int(ef_py.NavalWarfareRole.ScreenCommander))
    self.assertEqual(task.naval_station_type, ef_py.NavalStationType.Screen)
    self.assertEqual(int(task.supported_node_id), 5201)
    self.assertEqual(int(task.supporting_node_id), 5101)
    self.assertEqual(report.service_profile, ef_py.ServiceProfile.Navy)
    self.assertEqual(report.task_family, ef_py.TaskFamily.Escort)
    self.assertEqual(report.coordination_mode, ef_py.CoordinationMode.Screen)
    sea_state, wave_heading_deg, wave_period_s = sim.get_maritime_state()
    self.assertAlmostEqual(float(sea_state), 0.0, places=6)
    self.assertAlmostEqual(float(wave_heading_deg), 90.0, places=6)
    self.assertAlmostEqual(float(wave_period_s), 8.0, places=6)

  def test_scenario_without_maritime_block_clears_environment_override(self) -> None:
    sim = ef_py.SimulationKernel()
    self.assertTrue(sim.load_database(_DB_PATH))
    sim.set_maritime_state(5.0, 180.0, 9.5)

    loader = ScenarioLoader(sim)
    scenario = {
      "scenario_name": "naval_no_maritime_block",
      "environment": {
        "time_step": 1.0,
        "terrain_type": "legacy",
        "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
      },
      "entities": [
        {
          "name": "Blue_Ship",
          "type": "DDG-51_Flight_I_USS_Arleigh_Burke",
          "side": "Blue",
          "is_agent": True,
          "pos": [0.0, 0.0, 0.0],
          "vel": [0.0, 10.29, 0.0],
          "heading": 0.0,
        }
      ],
    }

    agent_id = int(loader.load_scenario_data(scenario, seed=20260517))
    self.assertGreater(agent_id, 0)
    sea_state, wave_heading_deg, wave_period_s = sim.get_maritime_state()
    self.assertAlmostEqual(float(sea_state), 0.0, places=6)
    self.assertAlmostEqual(float(wave_heading_deg), 0.0, places=6)
    self.assertAlmostEqual(float(wave_period_s), 8.0, places=6)

  def test_explicit_calm_maritime_block_still_counts_as_environment_override(self) -> None:
    sim = ef_py.SimulationKernel()
    self.assertTrue(sim.load_database(_DB_PATH))
    sim.set_maritime_state(5.0, 270.0, 12.0)

    loader = ScenarioLoader(sim)
    scenario = {
      "scenario_name": "naval_explicit_calm_override",
      "environment": {
        "time_step": 1.0,
        "terrain_type": "legacy",
        "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
        "maritime": {
          "sea_state": 0.0,
          "wave_heading_deg": 135.0,
          "wave_period_s": 11.0,
        },
      },
      "entities": [
        {
          "name": "Blue_Ship",
          "type": "DDG-51_Flight_I_USS_Arleigh_Burke",
          "side": "Blue",
          "is_agent": True,
          "pos": [0.0, 0.0, 0.0],
          "vel": [0.0, 10.29, 0.0],
          "heading": 0.0,
        }
      ],
    }

    agent_id = int(loader.load_scenario_data(scenario, seed=20260517))
    self.assertGreater(agent_id, 0)
    sea_state, wave_heading_deg, wave_period_s = sim.get_maritime_state()
    self.assertAlmostEqual(float(sea_state), 0.0, places=6)
    self.assertAlmostEqual(float(wave_heading_deg), 135.0, places=6)
    self.assertAlmostEqual(float(wave_period_s), 11.0, places=6)

  def test_screen_geometry_places_contact_inside_ddg_picture_but_outside_hvu_local_sensor_range(self) -> None:
    entities = self._scenario_entities(_SCENARIO_PATH)
    ddg_pos = entities["Blue_Screen_DDG51"]["pos"]
    hvu_pos = entities["Blue_HVU_TAKE1"]["pos"]
    red_pos = entities["Red_Surface_Contact"]["pos"]

    ddg_to_red_m = math.dist(ddg_pos, red_pos)
    hvu_to_red_m = math.dist(hvu_pos, red_pos)

    self.assertLess(ddg_to_red_m, 46300.0)
    self.assertGreater(hvu_to_red_m, 36300.0)
    self.assertEqual(entities["Red_Surface_Contact"]["type"], "Red_Surface_Combatant_Minimal")

  def test_ddg_detects_surface_contact_and_hvu_receives_datalink_track_and_report(self) -> None:
    sim = ef_py.SimulationKernel()
    self.assertTrue(sim.load_database(_DB_PATH))

    loader = ScenarioLoader(sim)
    agent_id = int(loader.load_scenario(_SCENARIO_PATH, seed=20260516))
    ddg_id = int(loader.entities["Blue_Screen_DDG51"])
    hvu_id = int(loader.entities["Blue_HVU_TAKE1"])
    red_id = int(loader.entities["Red_Surface_Contact"])

    self.assertEqual(agent_id, ddg_id)

    ddg_first_local_contact_step = None
    hvu_first_track_step = None
    hvu_first_datalink_track_step = None
    hvu_first_report_step = None
    hvu_report_count = 0
    local_detection_confirmed = False

    for step in range(40):
      sim.step()
      ddg_obs = sim.get_agent_observation(ddg_id)
      hvu_obs = sim.get_agent_observation(hvu_id)

      ddg_tracks = {
        int(getattr(track, "id", 0)): track
        for track in getattr(ddg_obs, "contacts", [])
      }
      hvu_tracks = {
        int(getattr(track, "id", 0)): track
        for track in getattr(hvu_obs, "contacts", [])
      }
      hvu_messages = list(sim.get_unit_messages(hvu_id))

      if red_id in ddg_tracks and ddg_first_local_contact_step is None:
        ddg_first_local_contact_step = step
        local_detection_confirmed = int(getattr(ddg_tracks[red_id], "source", 0)) == 1

      if red_id in hvu_tracks and hvu_first_track_step is None:
        hvu_first_track_step = step
      if red_id in hvu_tracks and int(getattr(hvu_tracks[red_id], "source", 0)) == 3 and hvu_first_datalink_track_step is None:
        hvu_first_datalink_track_step = step
      report_tracks = [
        msg
        for msg in hvu_messages
        if int(getattr(msg, "type", 0)) == _REPORT_TRACK_MSG_TYPE
        and int(getattr(msg, "entity_ref", 0)) == red_id
      ]
      hvu_report_count += len(report_tracks)
      if report_tracks and hvu_first_report_step is None:
        hvu_first_report_step = step

      if (
        ddg_first_local_contact_step is not None
        and hvu_first_datalink_track_step is not None
        and hvu_first_report_step is not None
      ):
        break

    self.assertIsNotNone(ddg_first_local_contact_step)
    self.assertTrue(local_detection_confirmed)
    self.assertIsNotNone(hvu_first_track_step)
    self.assertIsNotNone(hvu_first_datalink_track_step)
    self.assertIsNotNone(hvu_first_report_step)
    self.assertGreaterEqual(hvu_first_track_step, ddg_first_local_contact_step)
    self.assertGreaterEqual(hvu_first_datalink_track_step, ddg_first_local_contact_step)
    self.assertGreaterEqual(hvu_first_report_step, ddg_first_local_contact_step)
    self.assertGreaterEqual(hvu_report_count, 1)
    self.assertLess(hvu_report_count, 12)

  def test_closing_variant_reduces_hvu_contact_range_while_preserving_blind_zone(self) -> None:
    entities = self._scenario_entities(_CLOSING_SCENARIO_PATH)
    ddg_pos0 = entities["Blue_Screen_DDG51"]["pos"]
    hvu_pos0 = entities["Blue_HVU_TAKE1"]["pos"]
    red_pos0 = entities["Red_Surface_Contact"]["pos"]

    initial_hvu_contact_m = math.dist(hvu_pos0, red_pos0)
    initial_screen_hvu_m = math.dist(ddg_pos0, hvu_pos0)
    self.assertGreater(initial_hvu_contact_m, 36300.0)
    self.assertLess(math.dist(ddg_pos0, red_pos0), 46300.0)

    sim = ef_py.SimulationKernel()
    self.assertTrue(sim.load_database(_DB_PATH))

    loader = ScenarioLoader(sim)
    agent_id = int(loader.load_scenario(_CLOSING_SCENARIO_PATH, seed=20260516))
    ddg_id = int(loader.entities["Blue_Screen_DDG51"])
    hvu_id = int(loader.entities["Blue_HVU_TAKE1"])
    red_id = int(loader.entities["Red_Surface_Contact"])

    self.assertEqual(agent_id, ddg_id)

    min_hvu_contact_m = initial_hvu_contact_m
    min_screen_hvu_m = initial_screen_hvu_m
    max_screen_hvu_m = initial_screen_hvu_m
    hvu_local_source_seen = False
    ddg_detected = False
    hvu_shared_track_received = False

    for _step in range(240):
      sim.step()
      ddg_obs = sim.get_agent_observation(ddg_id)
      hvu_obs = sim.get_agent_observation(hvu_id)

      ddg_tracks = {
        int(getattr(track, "id", 0)): track
        for track in getattr(ddg_obs, "contacts", [])
      }
      hvu_tracks = {
        int(getattr(track, "id", 0)): track
        for track in getattr(hvu_obs, "contacts", [])
      }

      if red_id in ddg_tracks:
        ddg_detected = ddg_detected or int(getattr(ddg_tracks[red_id], "source", 0)) == 1

      if red_id in hvu_tracks:
        track_source = int(getattr(hvu_tracks[red_id], "source", 0))
        hvu_local_source_seen = hvu_local_source_seen or track_source == 1
        hvu_shared_track_received = hvu_shared_track_received or track_source == 3

      hvu_pos = sim.get_unit_position(hvu_id)
      ddg_pos = sim.get_unit_position(ddg_id)
      red_pos = sim.get_unit_position(red_id)

      hvu_contact_m = math.dist(hvu_pos, red_pos)
      screen_hvu_m = math.dist(ddg_pos, hvu_pos)
      min_hvu_contact_m = min(min_hvu_contact_m, hvu_contact_m)
      min_screen_hvu_m = min(min_screen_hvu_m, screen_hvu_m)
      max_screen_hvu_m = max(max_screen_hvu_m, screen_hvu_m)

    self.assertTrue(ddg_detected)
    self.assertTrue(hvu_shared_track_received)
    self.assertFalse(hvu_local_source_seen)
    self.assertLess(min_hvu_contact_m, initial_hvu_contact_m)
    self.assertGreater(min_hvu_contact_m, 36300.0)
    self.assertGreaterEqual(min_screen_hvu_m, 14000.0)
    self.assertLessEqual(max_screen_hvu_m, 15500.0)
    self.assertGreater(min_hvu_contact_m, 37000.0)
    self.assertLess(min_hvu_contact_m, 38000.0)

  def test_screen_station_hold_recovers_after_heading_disturbance(self) -> None:
    sim = ef_py.SimulationKernel()
    self.assertTrue(sim.load_database(_DB_PATH))

    loader = ScenarioLoader(sim)
    agent_id = int(loader.load_scenario(_CLOSING_SCENARIO_PATH, seed=20260516))
    ddg_id = int(loader.entities["Blue_Screen_DDG51"])
    hvu_id = int(loader.entities["Blue_HVU_TAKE1"])
    self.assertEqual(agent_id, ddg_id)
    for _ in range(20):
      sim.step()
    sim.set_command_link(ddg_id, 0.0, 0.0)

    disturbed_cmd = ef_py.MissionCommand()
    disturbed_cmd.active = True
    disturbed_cmd.command_code = 3
    disturbed_cmd.cmd_heading_deg = 180.0
    disturbed_cmd.cmd_altitude_m = 0.0
    disturbed_cmd.cmd_speed_mps = 8.23
    sim.set_mission_command(ddg_id, disturbed_cmd)
    steady_separation_m = math.dist(sim.get_unit_position(ddg_id), sim.get_unit_position(hvu_id))

    for _ in range(600):
      sim.step()

    disturbed_separation_m = math.dist(sim.get_unit_position(ddg_id), sim.get_unit_position(hvu_id))
    self.assertLess(disturbed_separation_m, steady_separation_m - 500.0)

    direct_modes = []
    for step in range(2400):
      loader.update_behaviors(step * sim.get_time_step(), sync_to_kernel=True)
      direct_modes.append(bool(getattr(loader, "_naval_screen_use_direct_command", False)))
      sim.step()

    final_sep_m = math.dist(sim.get_unit_position(ddg_id), sim.get_unit_position(hvu_id))
    handoff_step = next((idx for idx, active in enumerate(direct_modes) if not active), None)
    self.assertGreater(final_sep_m, disturbed_separation_m + 1200.0)
    self.assertGreaterEqual(final_sep_m, 13650.0)
    self.assertLessEqual(final_sep_m, 15000.0)
    self.assertIsNotNone(handoff_step)
    self.assertGreater(handoff_step, 0)
    self.assertFalse(any(direct_modes[handoff_step:]))

  def test_screen_station_hold_settles_without_large_late_oscillation(self) -> None:
    sim = ef_py.SimulationKernel()
    self.assertTrue(sim.load_database(_DB_PATH))

    loader = ScenarioLoader(sim)
    agent_id = int(loader.load_scenario(_CLOSING_SCENARIO_PATH, seed=20260516))
    ddg_id = int(loader.entities["Blue_Screen_DDG51"])
    hvu_id = int(loader.entities["Blue_HVU_TAKE1"])
    self.assertEqual(agent_id, ddg_id)

    for _ in range(20):
      sim.step()
    sim.set_command_link(ddg_id, 0.0, 0.0)

    disturbed_cmd = ef_py.MissionCommand()
    disturbed_cmd.active = True
    disturbed_cmd.command_code = 3
    disturbed_cmd.cmd_heading_deg = 180.0
    disturbed_cmd.cmd_altitude_m = 0.0
    disturbed_cmd.cmd_speed_mps = 8.23
    sim.set_mission_command(ddg_id, disturbed_cmd)

    for _ in range(600):
      sim.step()

    separations = []
    direct_modes = []
    for step in range(2400):
      loader.update_behaviors(step * sim.get_time_step(), sync_to_kernel=True)
      direct_modes.append(bool(getattr(loader, "_naval_screen_use_direct_command", False)))
      sim.step()
      separations.append(math.dist(sim.get_unit_position(ddg_id), sim.get_unit_position(hvu_id)))

    self.assertGreater(len(separations), 1200)
    tail = separations[-600:]
    handoff_step = next((idx for idx, active in enumerate(direct_modes) if not active), None)
    self.assertGreaterEqual(min(tail), 13300.0)
    self.assertLessEqual(max(tail), 15100.0)
    self.assertLess(max(tail) - min(tail), 700.0)
    self.assertIsNotNone(handoff_step)
    self.assertFalse(any(direct_modes[handoff_step:]))


if __name__ == "__main__":
  unittest.main()
