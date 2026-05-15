from __future__ import annotations

import unittest
from types import SimpleNamespace

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from python.rl.leader_tasking import build_kernel_mission_command  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
