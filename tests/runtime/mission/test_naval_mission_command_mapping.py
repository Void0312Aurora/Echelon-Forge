from __future__ import annotations

import unittest
from types import SimpleNamespace

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import ef_py  # noqa: E402

from python.rl.profile.naval_profile import build_kernel_mission_command  # noqa: E402
from python.rl.tasking import bridge as tasking_bridge  # noqa: E402


def _make_member(*, entity_id: int = 5101, reference_entity_id: int = 5201):
    return type("_Member", (), {"entity_id": entity_id, "reference_entity_id": reference_entity_id})()


class NavalMissionCommandMappingTests(unittest.TestCase):
    def test_mission_command_binding_roundtrip_exposes_naval_fields(self) -> None:
        cmd = ef_py.MissionCommand()
        cmd.reference_entity_id = 5201
        cmd.station_radius_m = 14500.0
        cmd.station_bearing_deg = 42.0
        cmd.threat_state = 4
        cmd.assigned_target_track_id = 6101
        cmd.assigned_target_source_id = 5101
        cmd.assigned_target_snapshot_time_s = 18.0

        self.assertEqual(int(cmd.reference_entity_id), 5201)
        self.assertAlmostEqual(float(cmd.station_radius_m), 14500.0, places=6)
        self.assertAlmostEqual(float(cmd.station_bearing_deg), 42.0, places=6)
        self.assertEqual(int(cmd.threat_state), 4)
        self.assertEqual(int(cmd.assigned_target_track_id), 6101)
        self.assertEqual(int(cmd.assigned_target_source_id), 5101)
        self.assertAlmostEqual(float(cmd.assigned_target_snapshot_time_s), 18.0, places=6)

    def test_tasking_profile_for_loader_prefers_explicit_profile_over_service_profile(self) -> None:
        task = ef_py.TaskOrder()
        task.service_profile = ef_py.ServiceProfile.Navy
        loader = SimpleNamespace(
            scenario_data={"tasking_profile": "air"},
            task_order=task,
            mission_cmd={},
        )

        profile = tasking_bridge.tasking_profile_for_loader(loader)

        self.assertIs(profile, tasking_bridge.resolve_tasking_profile("air"))

    def test_tasking_profile_for_loader_infers_naval_from_service_profile_when_tasking_profile_missing(self) -> None:
        task = ef_py.TaskOrder()
        task.service_profile = ef_py.ServiceProfile.Navy
        loader = SimpleNamespace(
            scenario_data={},
            task_order=task,
            mission_cmd={},
        )

        profile = tasking_bridge.tasking_profile_for_loader(loader)

        self.assertIs(profile, tasking_bridge.resolve_tasking_profile("naval"))

    def test_build_kernel_mission_command_honors_mission_overrides_for_naval_fields(self) -> None:
        task = ef_py.TaskOrder()
        task.service_profile = ef_py.ServiceProfile.Navy
        task.task_family = ef_py.TaskFamily.Escort
        task.coordination_mode = ef_py.CoordinationMode.Screen
        task.station_heading_deg = 35.0
        task.station_radius_m = 14000.0
        task.target_speed_mps = 12.5
        task.target_altitude_m = 0.0

        agent_member = _make_member()
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

    def test_build_kernel_mission_command_authors_expected_naval_field_matrix(self) -> None:
        task = ef_py.TaskOrder()
        task.service_profile = ef_py.ServiceProfile.Navy
        task.task_family = ef_py.TaskFamily.Recover
        task.coordination_mode = ef_py.CoordinationMode.Screen
        task.station_heading_deg = 35.0
        task.station_radius_m = 14000.0
        task.target_speed_mps = 12.5
        task.target_altitude_m = 0.0
        task.recovery_base_id = 9101
        task.recovery_runway_id = 14
        task.recovery_approach_type = ef_py.RecoveryApproachType.Visual

        agent_member = _make_member()
        loader = SimpleNamespace(
            scenario_data={
                "tasking_profile": "naval",
                "mission_command": {
                    "command_code": 32,
                    "reference_entity_id": 6201,
                    "station_radius_m": 16000.0,
                    "station_bearing_deg": 75.0,
                    "target_heading": 80.0,
                    "target_altitude": 15.0,
                    "target_speed": 14.0,
                    "assigned_target_id": 6202,
                    "threat_state": 5,
                    "assigned_target_track_id": 6202,
                    "assigned_target_source_id": 6201,
                    "assigned_target_snapshot_time_s": 42.0,
                    "recovery_base_id": 9201,
                    "recovery_runway_id": 24,
                    "recovery_approach_type": "ILS",
                    "formation_id": 73,
                    "form_offset_x": 240.0,
                    "form_offset_y": -110.0,
                    "form_offset_z": 18.0,
                    "embarked_helo_entity_id": 9301,
                    "launch_helo": True,
                    "recover_helo": False,
                    "relay_oth_targeting": True,
                },
            },
            task_order=task,
            mission_cmd={
                "reference_entity_id": 5301,
                "station_radius_m": 13000.0,
                "station_bearing_deg": 25.0,
                "assigned_target_id": 5302,
                "threat_state": 3,
                "assigned_target_track_id": 5302,
                "assigned_target_source_id": 5301,
                "assigned_target_snapshot_time_s": 24.0,
                "formation_id": 41,
                "form_offset_x": 90.0,
                "form_offset_y": -45.0,
                "form_offset_z": 6.0,
                "embarked_helo_entity_id": 9102,
                "launch_helo": False,
                "recover_helo": True,
                "relay_oth_targeting": False,
                "takeoff_procedure_code": int(ef_py.TakeoffProcedureType.Interval),
                "takeoff_clearance_code": int(ef_py.TakeoffClearanceState.ClearedForTakeoff),
                "takeoff_interval_s": 9.0,
                "runway_slot_code": int(ef_py.RunwaySlotPosition.Right),
            },
            agent_id=5101,
            active_roster=[agent_member],
            get_active_roster_member=staticmethod(lambda entity_id=None, entity_name=None: agent_member),
        )

        cmd = build_kernel_mission_command(loader)

        self.assertTrue(bool(cmd.active))
        self.assertEqual(int(cmd.command_code), 32)
        self.assertAlmostEqual(float(cmd.cmd_heading_deg), 80.0, places=6)
        self.assertAlmostEqual(float(cmd.cmd_altitude_m), 15.0, places=6)
        self.assertAlmostEqual(float(cmd.cmd_speed_mps), 14.0, places=6)
        self.assertEqual(int(cmd.reference_entity_id), 6201)
        self.assertAlmostEqual(float(cmd.station_radius_m), 16000.0, places=6)
        self.assertAlmostEqual(float(cmd.station_bearing_deg), 75.0, places=6)
        self.assertEqual(int(cmd.assigned_target_id), 6202)
        self.assertEqual(int(cmd.threat_state), 5)
        self.assertEqual(int(cmd.assigned_target_track_id), 6202)
        self.assertEqual(int(cmd.assigned_target_source_id), 6201)
        self.assertAlmostEqual(float(cmd.assigned_target_snapshot_time_s), 42.0, places=6)
        self.assertEqual(int(cmd.recovery_base_id), 9201)
        self.assertEqual(int(cmd.recovery_runway_id), 24)
        self.assertEqual(cmd.recovery_approach_type, ef_py.RecoveryApproachType.ILS)
        self.assertEqual(int(cmd.formation_id), 73)
        self.assertAlmostEqual(float(cmd.form_offset_x), 240.0, places=6)
        self.assertAlmostEqual(float(cmd.form_offset_y), -110.0, places=6)
        self.assertAlmostEqual(float(cmd.form_offset_z), 18.0, places=6)
        self.assertEqual(int(cmd.embarked_helo_entity_id), 9301)
        self.assertTrue(bool(cmd.launch_helo))
        self.assertFalse(bool(cmd.recover_helo))
        self.assertTrue(bool(cmd.relay_oth_targeting))

        self.assertEqual(int(cmd.route_ref_id), 0)
        self.assertEqual(cmd.takeoff_procedure_id, ef_py.TakeoffProcedureType.Unspecified)
        self.assertEqual(cmd.takeoff_clearance_id, ef_py.TakeoffClearanceState.Unspecified)
        self.assertAlmostEqual(float(cmd.takeoff_interval_s), 0.0, places=6)
        self.assertEqual(cmd.runway_slot_id, ef_py.RunwaySlotPosition.Unspecified)


if __name__ == "__main__":
    unittest.main()
