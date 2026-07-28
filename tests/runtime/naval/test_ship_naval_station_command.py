from __future__ import annotations

import math
import unittest

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py # noqa: E402


def _spawn_kernel() -> ef_py.SimulationKernel:
  kernel = ef_py.SimulationKernel()
  kernel.reset(6201)
  kernel.set_time_step(0.5)
  assert kernel.load_database(resolve_repo_path("examples", "config", "database"))
  return kernel


class ShipNavalStationCommandTests(unittest.TestCase):
  def test_ship_mission_command_station_fields_drive_relative_station_correction(self) -> None:
    kernel = _spawn_kernel()

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
    ddg_id = kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_USS_Arleigh_Burke",
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
    kernel.set_command_link(int(ddg_id), 0.0, 0.0)

    cmd = ef_py.MissionCommand()
    cmd.active = True
    cmd.command_code = 3
    cmd.cmd_heading_deg = 90.0
    cmd.cmd_altitude_m = 0.0
    cmd.cmd_speed_mps = 10.29
    cmd.reference_entity_id = int(reference_id)
    cmd.station_radius_m = 14000.0
    cmd.station_bearing_deg = 0.0
    kernel.set_mission_command(int(ddg_id), cmd)

    initial_heading = float(kernel.get_unit_heading(int(ddg_id)))
    initial_distance = math.dist(
      tuple(float(v) for v in kernel.get_unit_position(int(ddg_id))[:2]),
      tuple(float(v) for v in kernel.get_unit_position(int(reference_id))[:2]),
    )

    for _ in range(20):
      kernel.step()

    final_heading = float(kernel.get_unit_heading(int(ddg_id)))
    final_distance = math.dist(
      tuple(float(v) for v in kernel.get_unit_position(int(ddg_id))[:2]),
      tuple(float(v) for v in kernel.get_unit_position(int(reference_id))[:2]),
    )

    self.assertGreater(final_heading, initial_heading + 1.0)
    self.assertLess(final_distance, initial_distance - 50.0)

  def test_ship_station_command_inner_screen_accelerates_toward_forward_station(self) -> None:
    kernel = _spawn_kernel()

    reference_id = kernel.spawn_unit(
      ef_py.Side.Blue,
      "T-AKE-1_USNS_Lewis_and_Clark",
      0.0,
      0.0,
      0.0,
      heading=90.0,
      pitch=0.0,
      roll=0.0,
      vx=10.29,
      vy=0.0,
      vz=0.0,
    )
    ddg_id = kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_USS_Arleigh_Burke",
      13016.0,
      0.0,
      0.0,
      heading=90.0,
      pitch=0.0,
      roll=0.0,
      vx=10.29,
      vy=0.0,
      vz=0.0,
    )
    kernel.set_command_link(int(ddg_id), 0.0, 0.0)

    cmd = ef_py.MissionCommand()
    cmd.active = True
    cmd.command_code = 3
    cmd.cmd_heading_deg = 90.0
    cmd.cmd_altitude_m = 0.0
    cmd.cmd_speed_mps = 10.29
    cmd.reference_entity_id = int(reference_id)
    cmd.station_radius_m = 14816.0
    cmd.station_bearing_deg = 90.0
    kernel.set_mission_command(int(ddg_id), cmd)

    initial_speed = math.hypot(*tuple(float(v) for v in kernel.get_unit_velocity(int(ddg_id))[:2]))
    initial_error = abs(
      math.dist(
        tuple(float(v) for v in kernel.get_unit_position(int(ddg_id))[:2]),
        tuple(float(v) for v in kernel.get_unit_position(int(reference_id))[:2]),
      )
      - float(cmd.station_radius_m)
    )

    for _ in range(60):
      kernel.step()

    final_speed = math.hypot(*tuple(float(v) for v in kernel.get_unit_velocity(int(ddg_id))[:2]))
    final_error = abs(
      math.dist(
        tuple(float(v) for v in kernel.get_unit_position(int(ddg_id))[:2]),
        tuple(float(v) for v in kernel.get_unit_position(int(reference_id))[:2]),
      )
      - float(cmd.station_radius_m)
    )

    self.assertGreater(final_speed, initial_speed + 0.5)
    self.assertLess(final_error, initial_error - 25.0)

  def test_ship_without_station_fields_keeps_legacy_absolute_heading_behavior(self) -> None:
    kernel = _spawn_kernel()

    ddg_id = kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_USS_Arleigh_Burke",
      0.0,
      0.0,
      0.0,
      heading=90.0,
      pitch=0.0,
      roll=0.0,
      vx=10.29,
      vy=0.0,
      vz=0.0,
    )
    kernel.set_command_link(int(ddg_id), 0.0, 0.0)

    cmd = ef_py.MissionCommand()
    cmd.active = True
    cmd.command_code = 3
    cmd.cmd_heading_deg = 0.0
    cmd.cmd_altitude_m = 0.0
    cmd.cmd_speed_mps = 10.29
    kernel.set_mission_command(int(ddg_id), cmd)

    kernel.step()
    first_heading = float(kernel.get_unit_heading(int(ddg_id)))

    for _ in range(2250):
      kernel.step()

    final_heading = float(kernel.get_unit_heading(int(ddg_id)))
    self.assertLess(first_heading, 90.0)
    self.assertTrue(final_heading < 1.0 or final_heading > 359.0)


if __name__ == "__main__":
  unittest.main()
