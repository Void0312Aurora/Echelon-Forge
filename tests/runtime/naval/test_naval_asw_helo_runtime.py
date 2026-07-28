from __future__ import annotations

import math
import unittest

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py # noqa: E402


class NavalAswHeloRuntimeTests(unittest.TestCase):
  _DB_PATH = resolve_repo_path("examples", "config", "database")
  _OPEN_WATER_X = 1_000_000.0
  _OPEN_WATER_Y = 1_000_000.0

  def _kernel(self, seed: int = 9100) -> ef_py.SimulationKernel:
    kernel = ef_py.SimulationKernel()
    kernel.reset(seed)
    kernel.set_time_step(0.5)
    self.assertTrue(kernel.load_database(self._DB_PATH))
    return kernel

  @staticmethod
  def _find_detection(kernel: ef_py.SimulationKernel, owner_id: int, target_id: int):
    for det in kernel.get_detections(owner_id):
      if int(det.target_id) == int(target_id):
        return det
    return None

  def test_submarine_type_loads_from_database(self) -> None:
    kernel = self._kernel(9101)
    sub_id = kernel.spawn_unit(
      ef_py.Side.Red,
      "Kilo_Class_MVP",
      self._OPEN_WATER_X,
      self._OPEN_WATER_Y,
      -80.0,
      heading=180.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=-3.5,
      vz=0.0,
    )
    self.assertGreater(int(sub_id), 0)
    self.assertEqual(kernel.get_unit_type(int(sub_id)), int(ef_py.UnitType.Submarine))

  def test_surface_ship_sonar_generates_stable_submarine_contact(self) -> None:
    kernel = self._kernel(9102)
    ddg_id = kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_ASW_Helo_MVP",
      self._OPEN_WATER_X,
      self._OPEN_WATER_Y,
      0.0,
      heading=0.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=4.0,
      vz=0.0,
    )
    sub_id = kernel.spawn_unit(
      ef_py.Side.Red,
      "Kilo_Class_MVP",
      self._OPEN_WATER_X + 2_000.0,
      self._OPEN_WATER_Y + 14_000.0,
      -85.0,
      heading=180.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=-2.5,
      vz=0.0,
    )

    sonar_track_seen = False
    for _ in range(80):
      kernel.step()
      obs = kernel.get_agent_observation(int(ddg_id))
      sonar_track_seen = sonar_track_seen or any(
        int(track.id) == int(sub_id) and int(track.source) == 5
        for track in obs.contacts
      )
      if sonar_track_seen:
        break

    self.assertTrue(sonar_track_seen)

  def test_environment_maritime_state_override_also_modulates_sonar_contact(self) -> None:
    target_offset_x = 2_000.0
    target_offset_y = 16_000.0

    calm_kernel = self._kernel(9104)
    calm_ddg = calm_kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_ASW_Helo_MVP",
      self._OPEN_WATER_X,
      self._OPEN_WATER_Y,
      0.0,
      heading=0.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=4.0,
      vz=0.0,
    )
    calm_sub = calm_kernel.spawn_unit(
      ef_py.Side.Red,
      "Kilo_Class_MVP",
      self._OPEN_WATER_X + target_offset_x,
      self._OPEN_WATER_Y + target_offset_y,
      -85.0,
      heading=180.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=-2.5,
      vz=0.0,
    )

    calm_detection = None
    for _ in range(20):
      calm_kernel.step()
      calm_detection = self._find_detection(calm_kernel, int(calm_ddg), int(calm_sub))
      if calm_detection is not None:
        break

    rough_kernel = self._kernel(9105)
    rough_kernel.set_maritime_state(6.0, 120.0, 5.0)
    rough_ddg = rough_kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_ASW_Helo_MVP",
      self._OPEN_WATER_X,
      self._OPEN_WATER_Y,
      0.0,
      heading=0.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=4.0,
      vz=0.0,
    )
    rough_sub = rough_kernel.spawn_unit(
      ef_py.Side.Red,
      "Kilo_Class_MVP",
      self._OPEN_WATER_X + target_offset_x,
      self._OPEN_WATER_Y + target_offset_y,
      -85.0,
      heading=180.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=-2.5,
      vz=0.0,
    )

    rough_detection = None
    for _ in range(20):
      rough_kernel.step()
      rough_detection = self._find_detection(rough_kernel, int(rough_ddg), int(rough_sub))
      if rough_detection is not None:
        break

    self.assertIsNotNone(calm_detection)
    self.assertIsNotNone(rough_detection)
    self.assertGreater(float(calm_detection.snr_db), float(rough_detection.snr_db) + 4.0)

  def test_embarked_helo_launch_relay_and_recover_forms_minimal_closed_loop(self) -> None:
    kernel = self._kernel(9103)
    host_id = kernel.spawn_unit(
      ef_py.Side.Blue,
      "DDG-51_Flight_I_ASW_Helo_MVP",
      self._OPEN_WATER_X,
      self._OPEN_WATER_Y,
      0.0,
      heading=0.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=5.0,
      vz=0.0,
    )
    red_surface_id = kernel.spawn_unit(
      ef_py.Side.Red,
      "Red_Surface_Combatant_Minimal",
      self._OPEN_WATER_X,
      self._OPEN_WATER_Y + 55_000.0,
      0.0,
      heading=180.0,
      pitch=0.0,
      roll=0.0,
      vx=0.0,
      vy=-4.0,
      vz=0.0,
    )

    helo_id = int(kernel.debug_get_embarked_helo(int(host_id)))
    self.assertGreater(helo_id, 0)
    host_pos0 = kernel.get_unit_position(int(host_id))
    helo_pos0 = kernel.get_unit_position(helo_id)
    self.assertLess(math.dist(host_pos0, helo_pos0), 250.0)

    launch_cmd = ef_py.MissionCommand()
    launch_cmd.active = True
    launch_cmd.command_code = 31
    launch_cmd.embarked_helo_entity_id = helo_id
    launch_cmd.launch_helo = True
    launch_cmd.cmd_heading_deg = 0.0
    launch_cmd.cmd_speed_mps = 55.0
    kernel.set_mission_command(int(host_id), launch_cmd)

    airborne = False
    for _ in range(12):
      kernel.step()
      helo_pos = kernel.get_unit_position(helo_id)
      if float(helo_pos[2]) > 100.0:
        airborne = True
        break
    self.assertTrue(airborne)

    relay_seen = False
    relay_cmd = ef_py.MissionCommand()
    relay_cmd.active = True
    relay_cmd.command_code = 33
    relay_cmd.embarked_helo_entity_id = helo_id
    relay_cmd.relay_oth_targeting = True
    relay_cmd.assigned_target_id = int(red_surface_id)
    relay_cmd.cmd_speed_mps = 55.0
    kernel.set_mission_command(int(host_id), relay_cmd)

    for _ in range(120):
      kernel.step()
      host_obs = kernel.get_agent_observation(int(host_id))
      relay_seen = relay_seen or any(
        int(track.id) == int(red_surface_id) and int(track.source) == 3
        for track in host_obs.contacts
      )
      if relay_seen:
        break
    self.assertTrue(relay_seen)

    recover_cmd = ef_py.MissionCommand()
    recover_cmd.active = True
    recover_cmd.command_code = 32
    recover_cmd.embarked_helo_entity_id = helo_id
    recover_cmd.recover_helo = True
    recover_cmd.cmd_speed_mps = 35.0
    kernel.set_mission_command(int(host_id), recover_cmd)

    recovered = False
    for _ in range(160):
      kernel.step()
      host_pos = kernel.get_unit_position(int(host_id))
      helo_pos = kernel.get_unit_position(helo_id)
      if math.dist(host_pos, helo_pos) < 80.0 and float(helo_pos[2]) <= 1.0:
        recovered = True
        break
    self.assertTrue(recovered)


if __name__ == "__main__":
  unittest.main()
