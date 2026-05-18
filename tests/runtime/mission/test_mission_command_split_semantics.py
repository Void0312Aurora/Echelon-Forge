from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402


class MissionCommandSplitSemanticTests(unittest.TestCase):
    def test_mission_command_python_bindings_expose_common_and_air_fields(self) -> None:
        cmd = ef_py.MissionCommand()
        cmd.cmd_heading_deg = 67.0
        cmd.cmd_altitude_m = 2100.0
        cmd.cmd_speed_mps = 205.0
        cmd.command_code = 2
        cmd.route_ref_id = 991
        cmd.recovery_base_id = 55
        cmd.recovery_runway_id = 7
        cmd.recovery_approach_type = ef_py.RecoveryApproachType.ILS
        cmd.takeoff_procedure_id = ef_py.TakeoffProcedureType.Interval
        cmd.takeoff_clearance_id = ef_py.TakeoffClearanceState.ClearedForTakeoff
        cmd.takeoff_interval_s = 5.0
        cmd.runway_slot_id = ef_py.RunwaySlotPosition.Right
        cmd.formation_id = 9
        cmd.form_offset_x = 150.0
        cmd.form_offset_y = -80.0
        cmd.form_offset_z = 25.0
        cmd.assigned_target_id = 12345
        cmd.authorization_to_fire = True
        cmd.active = True

        self.assertAlmostEqual(float(cmd.cmd_heading_deg), 67.0, places=6)
        self.assertAlmostEqual(float(cmd.cmd_altitude_m), 2100.0, places=6)
        self.assertAlmostEqual(float(cmd.cmd_speed_mps), 205.0, places=6)
        self.assertEqual(int(cmd.command_code), 2)
        self.assertEqual(int(cmd.route_ref_id), 991)
        self.assertEqual(int(cmd.recovery_base_id), 55)
        self.assertEqual(int(cmd.recovery_runway_id), 7)
        self.assertEqual(cmd.recovery_approach_type, ef_py.RecoveryApproachType.ILS)
        self.assertEqual(cmd.takeoff_procedure_id, ef_py.TakeoffProcedureType.Interval)
        self.assertEqual(cmd.takeoff_clearance_id, ef_py.TakeoffClearanceState.ClearedForTakeoff)
        self.assertAlmostEqual(float(cmd.takeoff_interval_s), 5.0, places=6)
        self.assertEqual(cmd.runway_slot_id, ef_py.RunwaySlotPosition.Right)
        self.assertEqual(int(cmd.formation_id), 9)
        self.assertAlmostEqual(float(cmd.form_offset_x), 150.0, places=6)
        self.assertAlmostEqual(float(cmd.form_offset_y), -80.0, places=6)
        self.assertAlmostEqual(float(cmd.form_offset_z), 25.0, places=6)
        self.assertEqual(int(cmd.assigned_target_id), 12345)
        self.assertTrue(bool(cmd.authorization_to_fire))
        self.assertTrue(bool(cmd.active))

    def test_simulation_kernel_roundtrip_preserves_split_mission_command_fields(self) -> None:
        kernel = ef_py.SimulationKernel()
        kernel.reset(29)
        self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))

        entity_id = kernel.spawn_unit(
            ef_py.Side.Blue,
            "Aircraft",
            0.0,
            0.0,
            1000.0,
            heading=0.0,
            pitch=0.0,
            roll=0.0,
            vx=100.0,
            vy=0.0,
            vz=0.0,
        )
        self.assertGreater(int(entity_id), 0)
        kernel.set_command_link(int(entity_id), 0.0, 0.0)

        cmd = ef_py.MissionCommand()
        cmd.cmd_heading_deg = 45.0
        cmd.cmd_altitude_m = 1500.0
        cmd.cmd_speed_mps = 190.0
        cmd.command_code = 4
        cmd.route_ref_id = 77
        cmd.recovery_base_id = 55
        cmd.recovery_runway_id = 7
        cmd.recovery_approach_type = ef_py.RecoveryApproachType.ILS
        cmd.takeoff_procedure_id = ef_py.TakeoffProcedureType.Interval
        cmd.takeoff_clearance_id = ef_py.TakeoffClearanceState.LineUpAndWait
        cmd.takeoff_interval_s = 3.5
        cmd.runway_slot_id = ef_py.RunwaySlotPosition.Left
        cmd.formation_id = 17
        cmd.form_offset_x = 180.0
        cmd.form_offset_y = -90.0
        cmd.form_offset_z = 30.0
        cmd.assigned_target_id = 9001
        cmd.authorization_to_fire = False
        cmd.active = True

        kernel.set_mission_command(int(entity_id), cmd)
        got = kernel.get_mission_command(int(entity_id))

        self.assertAlmostEqual(float(got.cmd_heading_deg), 45.0, places=6)
        self.assertAlmostEqual(float(got.cmd_altitude_m), 1500.0, places=6)
        self.assertAlmostEqual(float(got.cmd_speed_mps), 190.0, places=6)
        self.assertEqual(int(got.command_code), 4)
        self.assertEqual(int(got.route_ref_id), 77)
        self.assertEqual(int(got.recovery_base_id), 55)
        self.assertEqual(int(got.recovery_runway_id), 7)
        self.assertEqual(got.recovery_approach_type, ef_py.RecoveryApproachType.ILS)
        self.assertEqual(got.takeoff_procedure_id, ef_py.TakeoffProcedureType.Interval)
        self.assertEqual(got.takeoff_clearance_id, ef_py.TakeoffClearanceState.LineUpAndWait)
        self.assertAlmostEqual(float(got.takeoff_interval_s), 3.5, places=6)
        self.assertEqual(got.runway_slot_id, ef_py.RunwaySlotPosition.Left)
        self.assertEqual(int(got.formation_id), 17)
        self.assertAlmostEqual(float(got.form_offset_x), 180.0, places=6)
        self.assertAlmostEqual(float(got.form_offset_y), -90.0, places=6)
        self.assertAlmostEqual(float(got.form_offset_z), 30.0, places=6)
        self.assertEqual(int(got.assigned_target_id), 9001)
        self.assertFalse(bool(got.authorization_to_fire))
        self.assertTrue(bool(got.active))


if __name__ == "__main__":
    unittest.main()
