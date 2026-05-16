from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import ef_py  # noqa: E402


class BindingsCommandSurfaceTests(unittest.TestCase):
    def test_mission_command_public_fields_match_expected_binding_surface(self) -> None:
        fields = tuple(name for name in dir(ef_py.MissionCommand()) if not name.startswith("_"))
        self.assertTupleEqual(
            fields,
            (
                "active",
                "assigned_target_id",
                "authorization_to_fire",
                "cmd_altitude_m",
                "cmd_heading_deg",
                "cmd_speed_mps",
                "command_code",
                "form_offset_x",
                "form_offset_y",
                "form_offset_z",
                "formation_id",
                "recovery_approach_type",
                "recovery_base_id",
                "recovery_runway_id",
                "route_ref_id",
                "runway_slot_id",
                "takeoff_clearance_id",
                "takeoff_interval_s",
                "takeoff_procedure_id",
            ),
        )

    def test_pilot_action_public_fields_match_expected_binding_surface(self) -> None:
        fields = tuple(name for name in dir(ef_py.PilotAction()) if not name.startswith("_"))
        self.assertTupleEqual(
            fields,
            (
                "active",
                "brake",
                "brake_left",
                "brake_right",
                "fire_gun",
                "fire_weapon",
                "flaps",
                "gear_handle",
                "jettison_emergency",
                "master_arm",
                "program_chaff",
                "program_flare",
                "radar_active",
                "radar_scan_az",
                "radar_scan_el",
                "rudder",
                "speedbrake",
                "stick_pitch",
                "stick_roll",
                "throttle",
                "tms_up",
                "weapon_select_id",
            ),
        )

    def test_comm_packet_public_fields_match_expected_binding_surface(self) -> None:
        fields = tuple(name for name in dir(ef_py.CommPacket()) if not name.startswith("_"))
        self.assertTupleEqual(
            fields,
            (
                "entity_ref",
                "location_x",
                "location_y",
                "location_z",
                "sender_id",
                "status_code",
                "target_receiver_id",
                "timestamp",
                "type",
                "value",
            ),
        )


if __name__ == "__main__":
    unittest.main()
