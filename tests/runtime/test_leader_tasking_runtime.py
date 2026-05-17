from __future__ import annotations

import unittest
from types import SimpleNamespace

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from python.rl.tasking.leader_tasking import build_kernel_mission_command  # noqa: E402


class LeaderTaskingRuntimeTests(unittest.TestCase):
    def test_build_kernel_mission_command_maps_formation_offsets(self) -> None:
        leader_intent = SimpleNamespace(
            command_code=2,
            cmd_heading_deg=67.0,
            cmd_altitude_m=2100.0,
            cmd_speed_mps=205.0,
            takeoff_procedure_id=2,
            takeoff_clearance_id=3,
            takeoff_interval_s=5.0,
            runway_slot_id=2,
            formation_id=9,
            form_offset_x=150.0,
            form_offset_y=-80.0,
            form_offset_z=25.0,
            assigned_target_id=0,
            authorization_to_fire=False,
        )
        loader = SimpleNamespace(
            mission_cmd={
                "command_code": 2,
                "target_heading": 90.0,
                "target_altitude": 1200.0,
                "target_speed": 180.0,
            },
            leader_intent=leader_intent,
            task_order=None,
            waypoints=[],
        )

        cmd = build_kernel_mission_command(loader)
        self.assertEqual(int(cmd.command_code), 2)
        self.assertAlmostEqual(float(cmd.cmd_heading_deg), 67.0, places=6)
        self.assertAlmostEqual(float(cmd.cmd_altitude_m), 2100.0, places=6)
        self.assertAlmostEqual(float(cmd.cmd_speed_mps), 205.0, places=6)
        self.assertEqual(int(cmd.takeoff_procedure_id), 2)
        self.assertEqual(int(cmd.takeoff_clearance_id), 3)
        self.assertAlmostEqual(float(cmd.takeoff_interval_s), 5.0, places=6)
        self.assertEqual(int(cmd.runway_slot_id), 2)
        self.assertEqual(int(cmd.formation_id), 9)
        self.assertAlmostEqual(float(cmd.form_offset_x), 150.0, places=6)
        self.assertAlmostEqual(float(cmd.form_offset_y), -80.0, places=6)
        self.assertAlmostEqual(float(cmd.form_offset_z), 25.0, places=6)

    def test_build_kernel_mission_command_falls_back_to_mission_cmd_fields(self) -> None:
        loader = SimpleNamespace(
            mission_cmd={
                "command_code": 2,
                "target_heading": 123.0,
                "target_altitude": 3100.0,
                "target_speed": 222.0,
                "takeoff_procedure_code": 2,
                "takeoff_clearance_code": 3,
                "takeoff_interval_s": 4.5,
                "runway_slot_code": 1,
                "formation_id": 31,
                "form_offset_x": 220.0,
                "form_offset_y": -75.0,
                "form_offset_z": 18.0,
                "assigned_target_id": 4401,
                "authorization_to_fire": True,
            },
            leader_intent=None,
            task_order=None,
            waypoints=[],
        )

        cmd = build_kernel_mission_command(loader)
        self.assertEqual(int(cmd.command_code), 2)
        self.assertAlmostEqual(float(cmd.cmd_heading_deg), 123.0, places=6)
        self.assertAlmostEqual(float(cmd.cmd_altitude_m), 3100.0, places=6)
        self.assertAlmostEqual(float(cmd.cmd_speed_mps), 222.0, places=6)
        self.assertEqual(int(cmd.takeoff_procedure_id), 2)
        self.assertEqual(int(cmd.takeoff_clearance_id), 3)
        self.assertAlmostEqual(float(cmd.takeoff_interval_s), 4.5, places=6)
        self.assertEqual(int(cmd.runway_slot_id), 1)
        self.assertEqual(int(cmd.formation_id), 31)
        self.assertAlmostEqual(float(cmd.form_offset_x), 220.0, places=6)
        self.assertAlmostEqual(float(cmd.form_offset_y), -75.0, places=6)
        self.assertAlmostEqual(float(cmd.form_offset_z), 18.0, places=6)
        self.assertEqual(int(cmd.assigned_target_id), 4401)
        self.assertTrue(bool(cmd.authorization_to_fire))

    def test_build_kernel_mission_command_writes_route_ref_id_only_for_active_route_leg(self) -> None:
        loader = SimpleNamespace(
            mission_cmd={
                "command_code": 3,
                "target_heading": 123.0,
                "target_altitude": 3100.0,
                "target_speed": 222.0,
            },
            leader_intent=SimpleNamespace(
                command_code=3,
                cmd_heading_deg=123.0,
                cmd_altitude_m=3100.0,
                cmd_speed_mps=222.0,
            ),
            task_order=None,
            waypoints=[
                {"x": 1000.0, "y": 2000.0, "z": 3100.0, "speed_mps": 222.0, "radius_m": 900.0},
            ],
            waypoint_idx=0,
        )

        cmd = build_kernel_mission_command(loader)

        self.assertEqual(int(cmd.command_code), 3)
        self.assertGreater(int(cmd.route_ref_id), 0)

        loader.leader_intent.command_code = 2
        cmd_vector = build_kernel_mission_command(loader)
        self.assertEqual(int(cmd_vector.command_code), 2)
        self.assertEqual(int(cmd_vector.route_ref_id), 0)

        loader.leader_intent.command_code = 3
        loader.waypoint_idx = 9
        cmd_no_active_leg = build_kernel_mission_command(loader)
        self.assertEqual(int(cmd_no_active_leg.command_code), 3)
        self.assertEqual(int(cmd_no_active_leg.route_ref_id), 0)

    def test_build_kernel_mission_command_writes_recovery_fields_only_for_landing_command(self) -> None:
        loader = SimpleNamespace(
            mission_cmd={
                "command_code": 4,
                "target_heading": 178.0,
                "target_altitude": 900.0,
                "target_speed": 155.0,
            },
            leader_intent=SimpleNamespace(
                command_code=4,
                cmd_heading_deg=178.0,
                cmd_altitude_m=900.0,
                cmd_speed_mps=155.0,
                recovery_base_id=501,
                recovery_runway_id=17,
                recovery_approach_type=2,
            ),
            task_order=None,
            waypoints=[],
        )

        landing_cmd = build_kernel_mission_command(loader)
        self.assertEqual(int(landing_cmd.command_code), 4)
        self.assertEqual(int(landing_cmd.recovery_base_id), 501)
        self.assertEqual(int(landing_cmd.recovery_runway_id), 17)
        self.assertEqual(int(landing_cmd.recovery_approach_type), 2)

        loader.leader_intent.command_code = 2
        vector_cmd = build_kernel_mission_command(loader)
        self.assertEqual(int(vector_cmd.command_code), 2)
        self.assertEqual(int(vector_cmd.recovery_base_id), 0)
        self.assertEqual(int(vector_cmd.recovery_runway_id), 0)
        self.assertEqual(int(vector_cmd.recovery_approach_type), 0)


if __name__ == "__main__":
    unittest.main()
