from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import ef_py  # noqa: E402

from python.rl.profile.naval_profile import build_kernel_mission_command  # noqa: E402


class NavalMissionCommandMappingTests(unittest.TestCase):
    def test_mission_command_binding_roundtrip_exposes_naval_fields(self) -> None:
        cmd = ef_py.MissionCommand()
        cmd.reference_entity_id = 5201
        cmd.station_radius_m = 14500.0
        cmd.station_bearing_deg = 42.0

        self.assertEqual(int(cmd.reference_entity_id), 5201)
        self.assertAlmostEqual(float(cmd.station_radius_m), 14500.0, places=6)
        self.assertAlmostEqual(float(cmd.station_bearing_deg), 42.0, places=6)

    def test_build_kernel_mission_command_honors_mission_overrides_for_naval_fields(self) -> None:
        task = ef_py.TaskOrder()
        task.service_profile = ef_py.ServiceProfile.Navy
        task.task_family = ef_py.TaskFamily.Escort
        task.coordination_mode = ef_py.CoordinationMode.Screen
        task.station_heading_deg = 35.0
        task.station_radius_m = 14000.0
        task.target_speed_mps = 12.5
        task.target_altitude_m = 0.0

        agent_member = type("_Member", (), {"entity_id": 5101, "reference_entity_id": 5201})()
        loader = type(
            "_Loader",
            (),
            {
                "scenario_data": {
                    "mission_command": {
                        "reference_entity_id": 6201,
                        "station_radius_m": 16000.0,
                        "station_bearing_deg": 75.0,
                        "target_heading": 80.0,
                        "target_speed": 14.0,
                    }
                },
                "task_order": task,
                "mission_cmd": {},
                "agent_id": 5101,
                "active_roster": [agent_member],
                "get_active_roster_member": staticmethod(lambda entity_id=None, entity_name=None: agent_member),
            },
        )()

        cmd = build_kernel_mission_command(loader)

        self.assertEqual(int(cmd.reference_entity_id), 6201)
        self.assertAlmostEqual(float(cmd.station_radius_m), 16000.0, places=6)
        self.assertAlmostEqual(float(cmd.station_bearing_deg), 75.0, places=6)
        self.assertAlmostEqual(float(cmd.cmd_heading_deg), 80.0, places=6)
        self.assertAlmostEqual(float(cmd.cmd_speed_mps), 14.0, places=6)


if __name__ == "__main__":
    unittest.main()
