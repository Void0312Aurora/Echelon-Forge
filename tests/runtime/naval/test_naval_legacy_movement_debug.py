from __future__ import annotations

import math
import unittest

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py # noqa: E402


def _make_kernel(seed: int) -> ef_py.SimulationKernel:
  kernel = ef_py.SimulationKernel()
  kernel.reset(seed)
  kernel.set_time_step(0.5)
  assert kernel.load_database(resolve_repo_path("examples", "config", "database"))
  return kernel


def _spawn_ship() -> tuple[ef_py.SimulationKernel, int]:
  kernel = _make_kernel(6201)
  entity_id = kernel.spawn_unit(
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
  kernel.set_command_link(int(entity_id), 0.0, 0.0)
  return kernel, int(entity_id)


def _spawn_submarine() -> tuple[ef_py.SimulationKernel, int]:
  kernel = _make_kernel(6202)
  entity_id = kernel.spawn_unit(
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
  kernel.set_command_link(int(entity_id), 0.0, 0.0)
  return kernel, int(entity_id)


class NavalLegacyMovementDebugTests(unittest.TestCase):
  def test_debug_hook_syncs_typed_control_state_and_exposes_legacy_mirror_fields(self) -> None:
    for label, spawner, heading_deg, speed_mps, altitude_m in (
      ("ship", _spawn_ship, 15.0, 8.0, 123.0),
      ("submarine", _spawn_submarine, 210.0, 6.5, 120.0),
    ):
      with self.subTest(platform=label):
        kernel, entity_id = spawner()

        kernel.debug_set_legacy_movement_command(
          entity_id,
          heading_deg,
          speed_mps,
          altitude_m,
          True,
        )

        movement = kernel.debug_get_legacy_movement_command(entity_id)
        mission = kernel.get_mission_command(entity_id)

        self.assertTrue(bool(movement["diagnostics_only"]))
        self.assertTrue(bool(movement["quarantined_surface"]))
        self.assertTrue(bool(movement["diagnostics_legacy_mirror"]))
        self.assertTrue(bool(movement["read_only_snapshot"]))
        self.assertFalse(bool(movement["maintained_truth"]))
        self.assertEqual(str(movement["diagnostics_quarantine_marker"]), "WP22-R1-2")
        self.assertEqual(str(movement["diagnostics_surface_kind"]), "diagnostics_legacy_mirror")
        self.assertEqual(
          str(movement["runtime_owner_kind"]),
          "mission_command_control_state_bridge",
        )
        self.assertEqual(str(movement["mirror_kind"]), "legacy_movement_command")
        self.assertEqual(str(movement["state_access_mode"]), "read_only_legacy_mirror")
        self.assertEqual(
          str(movement["mirror_truth_owner"]),
          "typed_control_state_bridge_projection",
        )
        self.assertTrue(bool(movement["active"]))
        self.assertAlmostEqual(float(movement["target_heading"]), heading_deg, places=6)
        self.assertAlmostEqual(float(movement["target_speed"]), speed_mps, places=6)
        self.assertAlmostEqual(float(movement["target_altitude"]), altitude_m, places=6)
        self.assertFalse(bool(movement["use_stick_control"]))
        self.assertTrue(bool(movement["control_state_present"]))
        self.assertTrue(bool(movement["control_state_active"]))
        self.assertAlmostEqual(float(movement["control_target_heading_deg"]), heading_deg, places=6)
        self.assertAlmostEqual(float(movement["control_target_speed_mps"]), speed_mps, places=6)
        self.assertAlmostEqual(float(movement["control_target_altitude_m"]), altitude_m, places=6)
        self.assertTrue(bool(movement["control_lagged_active"]))
        self.assertAlmostEqual(float(movement["control_lagged_heading_deg"]), heading_deg, places=6)
        self.assertAlmostEqual(float(movement["control_lagged_speed_mps"]), speed_mps, places=6)
        self.assertAlmostEqual(float(movement["control_lagged_altitude_m"]), altitude_m, places=6)
        self.assertFalse(bool(mission.active))
        self.assertAlmostEqual(float(mission.cmd_heading_deg), 0.0, places=6)
        self.assertAlmostEqual(float(mission.cmd_speed_mps), 0.0, places=6)
        self.assertAlmostEqual(float(mission.cmd_altitude_m), 0.0, places=6)

  def test_debug_hook_can_deactivate_typed_and_legacy_movement_state_together(self) -> None:
    for label, spawner in (
      ("ship", _spawn_ship),
      ("submarine", _spawn_submarine),
    ):
      with self.subTest(platform=label):
        kernel, entity_id = spawner()

        kernel.debug_set_legacy_movement_command(entity_id, 33.0, 4.0, 75.0, True)
        kernel.debug_set_legacy_movement_command(entity_id, 270.0, 1.0, 10.0, False)

        movement = kernel.debug_get_legacy_movement_command(entity_id)
        mission = kernel.get_mission_command(entity_id)

        self.assertTrue(bool(movement["diagnostics_only"]))
        self.assertTrue(bool(movement["quarantined_surface"]))
        self.assertTrue(bool(movement["control_state_present"]))
        self.assertFalse(bool(movement["active"]))
        self.assertFalse(bool(movement["control_state_active"]))
        self.assertFalse(bool(movement["control_lagged_active"]))
        self.assertFalse(bool(mission.active))

  def test_ship_motion_still_ignores_debug_legacy_transport_shell(self) -> None:
    kernel, entity_id = _spawn_ship()

    initial_heading_deg = float(kernel.get_unit_heading(entity_id))
    initial_speed_mps = math.hypot(*(float(v) for v in kernel.get_unit_velocity(entity_id)[:2]))

    kernel.debug_set_legacy_movement_command(entity_id, 0.0, 2.0, 500.0, True)

    for _ in range(12):
      kernel.step()

    heading_after_deg = float(kernel.get_unit_heading(entity_id))
    speed_after_mps = math.hypot(*(float(v) for v in kernel.get_unit_velocity(entity_id)[:2]))

    self.assertAlmostEqual(heading_after_deg, initial_heading_deg, delta=1.0)
    self.assertAlmostEqual(speed_after_mps, initial_speed_mps, delta=0.25)

  def test_ship_motion_consumes_nontrivial_pilot_action_as_manual_control(self) -> None:
    idle_kernel, idle_id = _spawn_ship()
    full_kernel, full_id = _spawn_ship()
    turn_kernel, turn_id = _spawn_ship()

    idle = ef_py.PilotAction()
    idle.active = True
    idle.throttle = 0.0
    idle_kernel.set_pilot_action(idle_id, idle)

    full = ef_py.PilotAction()
    full.active = True
    full.throttle = 1.0
    full_kernel.set_pilot_action(full_id, full)

    turn = ef_py.PilotAction()
    turn.active = True
    turn.throttle = 1.0
    turn.rudder = 1.0
    turn_kernel.set_pilot_action(turn_id, turn)

    for _ in range(40):
      idle_kernel.step()
      full_kernel.step()
      turn_kernel.step()

    idle_speed_mps = math.hypot(*(float(v) for v in idle_kernel.get_unit_velocity(idle_id)[:2]))
    full_speed_mps = math.hypot(*(float(v) for v in full_kernel.get_unit_velocity(full_id)[:2]))
    turn_heading_deg = float(turn_kernel.get_unit_heading(turn_id))

    self.assertGreater(full_speed_mps, idle_speed_mps + 4.0)
    self.assertGreater(turn_heading_deg, 95.0)

  def test_submarine_motion_still_ignores_debug_legacy_transport_shell(self) -> None:
    kernel, entity_id = _spawn_submarine()

    initial_heading_deg = float(kernel.get_unit_heading(entity_id))
    initial_speed_mps = math.hypot(*(float(v) for v in kernel.get_unit_velocity(entity_id)[:2]))
    initial_depth_m = -float(kernel.get_unit_position(entity_id)[2])

    kernel.debug_set_legacy_movement_command(entity_id, 210.0, 6.5, 120.0, True)

    for _ in range(10):
      kernel.step()

    heading_after_deg = float(kernel.get_unit_heading(entity_id))
    speed_after_mps = math.hypot(*(float(v) for v in kernel.get_unit_velocity(entity_id)[:2]))
    depth_after_m = -float(kernel.get_unit_position(entity_id)[2])

    self.assertAlmostEqual(heading_after_deg, initial_heading_deg, delta=1.0)
    self.assertAlmostEqual(speed_after_mps, initial_speed_mps, delta=0.25)
    self.assertAlmostEqual(depth_after_m, initial_depth_m, delta=1.0)


if __name__ == "__main__":
  unittest.main()
