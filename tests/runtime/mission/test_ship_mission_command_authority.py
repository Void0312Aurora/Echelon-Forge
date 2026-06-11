from __future__ import annotations

import math
import unittest

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py # noqa: E402


def _spawn_ship(*, heading: float = 90.0, speed_mps: float = 10.29) -> tuple[ef_py.SimulationKernel, int]:
  kernel = ef_py.SimulationKernel()
  kernel.reset(6101)
  kernel.set_time_step(0.5)
  assert kernel.load_database(resolve_repo_path("examples", "config", "database"))

  entity_id = kernel.spawn_unit(
    ef_py.Side.Blue,
    "DDG-51_Flight_I_USS_Arleigh_Burke",
    0.0,
    0.0,
    0.0,
    heading=heading,
    pitch=0.0,
    roll=0.0,
    vx=speed_mps,
    vy=0.0,
    vz=0.0,
  )
  kernel.set_command_link(int(entity_id), 0.0, 0.0)
  return kernel, int(entity_id)


class ShipMissionCommandAuthorityTests(unittest.TestCase):
  def test_ship_set_command_updates_mission_command_authority(self) -> None:
    kernel, entity_id = _spawn_ship()

    kernel.set_command(entity_id, 15.0, 8.0, 123.0)
    mission = kernel.get_mission_command(entity_id)

    self.assertTrue(bool(mission.active))
    self.assertAlmostEqual(float(mission.cmd_heading_deg), 15.0, places=6)
    self.assertAlmostEqual(float(mission.cmd_speed_mps), 8.0, places=6)
    self.assertAlmostEqual(float(mission.cmd_altitude_m), 123.0, places=6)

    for _ in range(20):
      kernel.step()
    self.assertLess(float(kernel.get_unit_heading(entity_id)), 90.0)

  def test_ship_set_command_overrides_prior_mission_via_same_authority(self) -> None:
    kernel, entity_id = _spawn_ship()

    first = ef_py.MissionCommand()
    first.active = True
    first.command_code = 3
    first.cmd_heading_deg = 0.0
    first.cmd_speed_mps = 10.29
    kernel.set_mission_command(entity_id, first)

    kernel.step()
    heading_after_first = float(kernel.get_unit_heading(entity_id))
    self.assertLess(heading_after_first, 90.0)

    kernel.set_command(entity_id, 180.0, 9.5, 50.0)
    mission = kernel.get_mission_command(entity_id)
    self.assertTrue(bool(mission.active))
    self.assertAlmostEqual(float(mission.cmd_heading_deg), 180.0, places=6)
    self.assertAlmostEqual(float(mission.cmd_speed_mps), 9.5, places=6)
    self.assertAlmostEqual(float(mission.cmd_altitude_m), 50.0, places=6)

    for _ in range(6):
      kernel.step()

    heading_after_override = float(kernel.get_unit_heading(entity_id))
    self.assertGreater(heading_after_override, heading_after_first + 1.0)

  def test_ship_set_command_clears_relative_station_and_helo_semantics(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(6102)
    kernel.set_time_step(0.5)
    assert kernel.load_database(resolve_repo_path("examples", "config", "database"))

    reference_id = kernel.spawn_unit(
      ef_py.Side.Blue,
      "T-AKE-1_USNS_Lewis_and_Clark",
      0.0,
      0.0,
      0.0,
      heading=0.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=10.29,
      vz=0.0,
    )
    entity_id = kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_ASW_Helo_MVP",
      0.0,
      16000.0,
      0.0,
      heading=90.0,
      pitch=0.0,
      roll=0.0,
      vx=10.29,
      vy=0.0,
      vz=0.0,
    )
    kernel.set_command_link(int(entity_id), 0.0, 0.0)

    helo_id = int(kernel.debug_get_embarked_helo(int(entity_id)))
    self.assertGreater(helo_id, 0)

    station_cmd = ef_py.MissionCommand()
    station_cmd.active = True
    station_cmd.command_code = 3
    station_cmd.cmd_heading_deg = 90.0
    station_cmd.cmd_speed_mps = 10.29
    station_cmd.reference_entity_id = int(reference_id)
    station_cmd.station_radius_m = 14000.0
    station_cmd.station_bearing_deg = 0.0
    station_cmd.embarked_helo_entity_id = helo_id
    station_cmd.launch_helo = True
    station_cmd.recover_helo = True
    station_cmd.relay_oth_targeting = True
    station_cmd.authorization_to_fire = True
    kernel.set_mission_command(int(entity_id), station_cmd)

    kernel.step()
    guided_heading = float(kernel.get_unit_heading(int(entity_id)))
    self.assertGreater(guided_heading, 90.0)

    kernel.set_command(int(entity_id), 0.0, 9.5, 50.0)
    mission = kernel.get_mission_command(int(entity_id))

    self.assertTrue(bool(mission.active))
    self.assertAlmostEqual(float(mission.cmd_heading_deg), 0.0, places=6)
    self.assertAlmostEqual(float(mission.cmd_speed_mps), 9.5, places=6)
    self.assertAlmostEqual(float(mission.cmd_altitude_m), 50.0, places=6)
    self.assertEqual(int(mission.reference_entity_id), 0)
    self.assertAlmostEqual(float(mission.station_radius_m), 0.0, places=6)
    self.assertAlmostEqual(float(mission.station_bearing_deg), 0.0, places=6)
    self.assertEqual(int(mission.embarked_helo_entity_id), 0)
    self.assertFalse(bool(mission.launch_helo))
    self.assertFalse(bool(mission.recover_helo))
    self.assertFalse(bool(mission.relay_oth_targeting))
    self.assertTrue(bool(mission.authorization_to_fire))

    for _ in range(6):
      kernel.step()

    heading_after_override = float(kernel.get_unit_heading(int(entity_id)))
    self.assertLess(heading_after_override, guided_heading - 1.0)

  def test_submarine_set_command_clears_relative_station_semantics(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(6103)
    kernel.set_time_step(0.5)
    assert kernel.load_database(resolve_repo_path("examples", "config", "database"))

    reference_id = kernel.spawn_unit(
      ef_py.Side.Blue,
      "T-AKE-1_USNS_Lewis_and_Clark",
      0.0,
      0.0,
      0.0,
      heading=0.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=6.0,
      vz=0.0,
    )
    sub_id = kernel.spawn_unit(
      ef_py.Side.Blue,
      "Kilo_Class_MVP",
      0.0,
      12000.0,
      -80.0,
      heading=90.0,
      pitch=0.0,
      roll=0.0,
      vx=3.0,
      vy=0.0,
      vz=0.0,
    )
    kernel.set_command_link(int(sub_id), 0.0, 0.0)

    station_cmd = ef_py.MissionCommand()
    station_cmd.active = True
    station_cmd.command_code = 3
    station_cmd.cmd_heading_deg = 45.0
    station_cmd.cmd_speed_mps = 4.0
    station_cmd.cmd_altitude_m = 60.0
    station_cmd.reference_entity_id = int(reference_id)
    station_cmd.station_radius_m = 10000.0
    station_cmd.station_bearing_deg = 45.0
    kernel.set_mission_command(int(sub_id), station_cmd)

    mission_before = kernel.get_mission_command(int(sub_id))
    self.assertEqual(int(mission_before.reference_entity_id), int(reference_id))
    self.assertGreater(float(mission_before.station_radius_m), 0.0)

    kernel.set_command(int(sub_id), 210.0, 6.5, 120.0)
    mission_after = kernel.get_mission_command(int(sub_id))

    self.assertTrue(bool(mission_after.active))
    self.assertAlmostEqual(float(mission_after.cmd_heading_deg), 210.0, places=6)
    self.assertAlmostEqual(float(mission_after.cmd_speed_mps), 6.5, places=6)
    self.assertAlmostEqual(float(mission_after.cmd_altitude_m), 120.0, places=6)
    self.assertEqual(int(mission_after.reference_entity_id), 0)
    self.assertAlmostEqual(float(mission_after.station_radius_m), 0.0, places=6)
    self.assertAlmostEqual(float(mission_after.station_bearing_deg), 0.0, places=6)

    initial_heading_deg = float(kernel.get_unit_heading(int(sub_id)))
    initial_speed_mps = math.hypot(*(float(v) for v in kernel.get_unit_velocity(int(sub_id))[:2]))
    initial_depth_m = -float(kernel.get_unit_position(int(sub_id))[2])

    for _ in range(10):
      kernel.step()

    heading_after = float(kernel.get_unit_heading(int(sub_id)))
    speed_after_mps = math.hypot(*(float(v) for v in kernel.get_unit_velocity(int(sub_id))[:2]))
    depth_after_m = -float(kernel.get_unit_position(int(sub_id))[2])

    self.assertGreater(heading_after, initial_heading_deg + 5.0)
    self.assertGreater(speed_after_mps, initial_speed_mps + 0.2)
    self.assertGreater(depth_after_m, initial_depth_m + 10.0)
    self.assertLessEqual(depth_after_m, 120.0 + 1.0e-6)


if __name__ == "__main__":
  unittest.main()
