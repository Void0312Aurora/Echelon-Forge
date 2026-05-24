from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import ef_py  # noqa: E402


class BindingsCommandSurfaceTests(unittest.TestCase):
    def test_owner_slice_types_and_helpers_are_visible_for_tasking_shells(self) -> None:
        order_core = ef_py.TaskOrderCore()
        order_air = ef_py.TaskOrderAir()
        order_naval = ef_py.TaskOrderNaval()
        leader_core = ef_py.LeaderIntentCore()
        leader_air = ef_py.LeaderIntentAir()
        leader_naval = ef_py.LeaderIntentNaval()
        pilot_core = ef_py.PilotReportCore()
        pilot_air = ef_py.PilotReportAir()
        pilot_naval = ef_py.PilotReportNaval()

        order_core.task_id = 99
        order_air.element_id = 66
        order_naval.officer_in_tactical_command = 7001
        leader_core.command_code = 17
        leader_air.formation_id = 41
        leader_naval.warfare_role_code = 9
        pilot_core.sender_id = 101
        pilot_air.element_id = 77
        pilot_naval.officer_in_tactical_command = 7002

        self.assertEqual(int(order_core.task_id), 99)
        self.assertEqual(int(order_air.element_id), 66)
        self.assertEqual(int(order_naval.officer_in_tactical_command), 7001)
        self.assertEqual(int(leader_core.command_code), 17)
        self.assertEqual(int(leader_air.formation_id), 41)
        self.assertEqual(int(leader_naval.warfare_role_code), 9)
        self.assertEqual(int(pilot_core.sender_id), 101)
        self.assertEqual(int(pilot_air.element_id), 77)
        self.assertEqual(int(pilot_naval.officer_in_tactical_command), 7002)

        order = ef_py.TaskOrder()
        order.task_id = 8
        order.task_type = ef_py.TaskType.CAPMission
        order.element_id = 13
        order.package_id = 21
        order.lead_aircraft_id = 9001
        order.anchor_x_m = 1200.0
        order.anchor_y_m = -300.0
        order.anchor_z_m = 6500.0
        order.station_type = ef_py.StationType.Racetrack
        order.station_radius_m = 18000.0
        order.station_leg_length_m = 32000.0
        order.station_heading_deg = 45.0
        order.altitude_block_min_m = 6100.0
        order.altitude_block_max_m = 7100.0
        order.target_altitude_m = 6600.0
        order.speed_min_mps = 190.0
        order.speed_max_mps = 230.0
        order.target_speed_mps = 210.0
        order.entry_condition_code = 3
        order.exit_condition_code = 4
        order.on_station_time_s = 900.0
        order.fuel_bingo_override_kg = 1200.0
        order.warfare_role_code = 4
        order.recovery_base_id = 22
        order.recovery_runway_id = 23
        order.recovery_approach_type = ef_py.RecoveryApproachType.ILS
        order.takeoff_procedure_id = ef_py.TakeoffProcedureType.Interval
        order.takeoff_clearance_id = ef_py.TakeoffClearanceState.ClearedForTakeoff
        order.takeoff_interval_s = 17.5
        order.runway_slot_id = ef_py.RunwaySlotPosition.Right
        order.officer_in_tactical_command = 8004
        order.formation_template_id = 91
        order.formation_contract_id = 92
        order.formation_role_id = ef_py.FormationRole.ElementLead
        order.wingman_slot_id = ef_py.WingmanSlot.Right
        order.join_policy_id = 5
        order.rejoin_policy_id = 6
        order.mutual_support_mode = 7
        order.support_sector_id = 501
        order.naval_station_type = ef_py.NavalStationType.Screen

        order_core_view = ef_py.task_order_shared_core(order)
        order_air_view = ef_py.task_order_air_owner_slice(order)
        order_naval_view = ef_py.task_order_naval_owner_slice(order)
        order_core_directive = ef_py.task_order_shared_core_directive(order)
        order_air_identity = ef_py.task_order_air_tasking_identity_directive(order)
        order_air_stationing = ef_py.task_order_air_stationing_directive(order)
        order_recovery = ef_py.task_order_air_recovery_directive(order)
        order_takeoff = ef_py.task_order_air_takeoff_directive(order)
        order_air_formation = ef_py.task_order_air_formation_directive(order)
        order_authority = ef_py.task_order_naval_command_authority(order)
        order_naval_stationing = ef_py.task_order_naval_stationing_directive(order)

        self.assertIsInstance(order_core_view, ef_py.TaskOrderCore)
        self.assertIsInstance(order_air_view, ef_py.TaskOrderAir)
        self.assertIsInstance(order_naval_view, ef_py.TaskOrderNaval)
        self.assertIsInstance(order_core_directive, ef_py.TaskOrderCore)
        self.assertIsInstance(
            order_air_identity,
            ef_py.TaskOrderAirTaskingIdentityDirective,
        )
        self.assertIsInstance(
            order_air_stationing,
            ef_py.TaskOrderAirStationingDirective,
        )
        self.assertIsInstance(order_recovery, ef_py.TaskOrderAirRecoveryDirective)
        self.assertIsInstance(order_takeoff, ef_py.TaskOrderAirTakeoffDirective)
        self.assertIsInstance(order_air_formation, ef_py.TaskOrderAirFormationDirective)
        self.assertIsInstance(
            order_authority,
            ef_py.TaskOrderNavalCommandAuthorityDirective,
        )
        self.assertIsInstance(
            order_naval_stationing,
            ef_py.TaskOrderNavalStationingDirective,
        )
        self.assertEqual(int(order_core_view.task_id), 8)
        self.assertEqual(int(order_air_view.element_id), 13)
        self.assertEqual(int(order_naval_view.warfare_role_code), 4)
        self.assertEqual(int(order_core_directive.task_id), 8)
        self.assertEqual(order_air_identity.task_type, ef_py.TaskType.CAPMission)
        self.assertEqual(int(order_air_identity.element_id), 13)
        self.assertEqual(int(order_air_identity.package_id), 21)
        self.assertEqual(int(order_air_identity.lead_aircraft_id), 9001)
        self.assertAlmostEqual(float(order_air_stationing.anchor_x_m), 1200.0)
        self.assertAlmostEqual(float(order_air_stationing.anchor_y_m), -300.0)
        self.assertAlmostEqual(float(order_air_stationing.anchor_z_m), 6500.0)
        self.assertEqual(order_air_stationing.station_type, ef_py.StationType.Racetrack)
        self.assertAlmostEqual(float(order_air_stationing.station_radius_m), 18000.0)
        self.assertAlmostEqual(float(order_air_stationing.station_leg_length_m), 32000.0)
        self.assertAlmostEqual(float(order_air_stationing.station_heading_deg), 45.0)
        self.assertAlmostEqual(float(order_air_stationing.altitude_block_min_m), 6100.0)
        self.assertAlmostEqual(float(order_air_stationing.altitude_block_max_m), 7100.0)
        self.assertAlmostEqual(float(order_air_stationing.target_altitude_m), 6600.0)
        self.assertAlmostEqual(float(order_air_stationing.speed_min_mps), 190.0)
        self.assertAlmostEqual(float(order_air_stationing.speed_max_mps), 230.0)
        self.assertAlmostEqual(float(order_air_stationing.target_speed_mps), 210.0)
        self.assertEqual(int(order_air_stationing.entry_condition_code), 3)
        self.assertEqual(int(order_air_stationing.exit_condition_code), 4)
        self.assertAlmostEqual(float(order_air_stationing.on_station_time_s), 900.0)
        self.assertAlmostEqual(float(order_air_stationing.fuel_bingo_override_kg), 1200.0)
        self.assertEqual(int(order_recovery.recovery_base_id), 22)
        self.assertEqual(int(order_recovery.recovery_runway_id), 23)
        self.assertEqual(
            order_recovery.recovery_approach_type,
            ef_py.RecoveryApproachType.ILS,
        )
        self.assertEqual(
            order_takeoff.takeoff_procedure_id,
            ef_py.TakeoffProcedureType.Interval,
        )
        self.assertEqual(
            order_takeoff.takeoff_clearance_id,
            ef_py.TakeoffClearanceState.ClearedForTakeoff,
        )
        self.assertAlmostEqual(float(order_takeoff.takeoff_interval_s), 17.5)
        self.assertEqual(order_takeoff.runway_slot_id, ef_py.RunwaySlotPosition.Right)
        self.assertEqual(int(order_air_formation.formation_template_id), 91)
        self.assertEqual(int(order_air_formation.formation_contract_id), 92)
        self.assertEqual(
            order_air_formation.formation_role_id,
            ef_py.FormationRole.ElementLead,
        )
        self.assertEqual(order_air_formation.wingman_slot_id, ef_py.WingmanSlot.Right)
        self.assertEqual(int(order_air_formation.join_policy_id), 5)
        self.assertEqual(int(order_air_formation.rejoin_policy_id), 6)
        self.assertEqual(int(order_air_formation.mutual_support_mode), 7)
        self.assertEqual(int(order_air_formation.support_sector_id), 501)
        self.assertEqual(int(order_authority.warfare_role_code), 4)
        self.assertEqual(int(order_authority.officer_in_tactical_command), 8004)
        self.assertEqual(
            order_naval_stationing.naval_station_type,
            ef_py.NavalStationType.Screen,
        )

        order_core_view.task_id = 55
        order_air_view.package_id = 6
        order_naval_view.officer_in_tactical_command = 9005

        self.assertEqual(int(order.task_id), 55)
        self.assertEqual(int(order.package_id), 6)
        self.assertEqual(int(order.officer_in_tactical_command), 9005)

        intent = ef_py.LeaderIntent()
        intent.command_code = 3
        intent.formation_id = 12
        intent.warfare_role_code = 5

        intent_core = ef_py.leader_intent_shared_core(intent)
        intent_air = ef_py.leader_intent_air_owner_slice(intent)
        intent_naval = ef_py.leader_intent_naval_owner_slice(intent)

        self.assertIsInstance(intent_core, ef_py.LeaderIntentCore)
        self.assertIsInstance(intent_air, ef_py.LeaderIntentAir)
        self.assertIsInstance(intent_naval, ef_py.LeaderIntentNaval)
        self.assertEqual(int(intent_core.command_code), 3)
        self.assertEqual(int(intent_air.formation_id), 12)
        self.assertEqual(int(intent_naval.warfare_role_code), 5)

        intent_core.command_code = 18
        intent_air.formation_id = 42
        intent_naval.officer_in_tactical_command = 7003

        self.assertEqual(int(intent.command_code), 18)
        self.assertEqual(int(intent.formation_id), 42)
        self.assertEqual(int(intent.officer_in_tactical_command), 7003)

        report = ef_py.PilotReport()
        report.sender_id = 8
        report.element_id = 13
        report.warfare_role_code = 4

        report_core = ef_py.pilot_report_shared_core(report)
        report_air = ef_py.pilot_report_air_owner_slice(report)
        report_naval = ef_py.pilot_report_naval_owner_slice(report)

        self.assertIsInstance(report_core, ef_py.PilotReportCore)
        self.assertIsInstance(report_air, ef_py.PilotReportAir)
        self.assertIsInstance(report_naval, ef_py.PilotReportNaval)
        self.assertEqual(int(report_core.sender_id), 8)
        self.assertEqual(int(report_air.element_id), 13)
        self.assertEqual(int(report_naval.warfare_role_code), 4)

        report_core.sender_id = 55
        report_air.phase_id = 6
        report_naval.officer_in_tactical_command = 8004

        self.assertEqual(int(report.sender_id), 55)
        self.assertEqual(int(report.phase_id), 6)
        self.assertEqual(int(report.officer_in_tactical_command), 8004)

    def test_runtime_bindings_expose_task_order_maintained_batch_surfaces(self) -> None:
        contract = ef_py.TaskOrderMaintainedBatchContract()
        contract.shared_core.task_id = 41
        contract.shared_core.active = True
        ef_py.task_order_maintained_air_tasking_identity(
            contract
        ).task_type = ef_py.TaskType.CAP
        ef_py.task_order_maintained_air_tasking_identity(contract).element_id = 7001
        ef_py.task_order_maintained_air_stationing(contract).target_altitude_m = 6100.0
        ef_py.task_order_maintained_air_stationing(contract).target_speed_mps = 205.0
        ef_py.task_order_maintained_air_stationing(
            contract
        ).station_type = ef_py.StationType.RouteCAP
        contract.air_recovery.recovery_base_id = 81
        contract.air_takeoff.takeoff_interval_s = 12.5
        ef_py.task_order_maintained_air_formation(
            contract
        ).formation_role_id = ef_py.FormationRole.Wingman
        ef_py.task_order_maintained_air_formation(
            contract
        ).wingman_slot_id = ef_py.WingmanSlot.Left
        contract.naval_command_authority.officer_in_tactical_command = 9001
        ef_py.task_order_maintained_naval_stationing(
            contract
        ).naval_station_type = ef_py.NavalStationType.Support

        assignment = ef_py.WorldTaskOrderMaintainedAssignment()
        assignment.world_index = 2
        assignment.entity_id = 77
        assignment.task_order = contract

        self.assertEqual(int(assignment.world_index), 2)
        self.assertEqual(int(assignment.entity_id), 77)
        self.assertEqual(int(assignment.task_order.shared_core.task_id), 41)
        self.assertTrue(bool(assignment.task_order.shared_core.active))
        self.assertEqual(
            ef_py.task_order_maintained_air_tasking_identity(
                assignment.task_order
            ).task_type,
            ef_py.TaskType.CAP,
        )
        self.assertEqual(
            int(
                ef_py.task_order_maintained_air_tasking_identity(
                    assignment.task_order
                ).element_id
            ),
            7001,
        )
        self.assertEqual(
            ef_py.task_order_maintained_air_stationing(
                assignment.task_order
            ).station_type,
            ef_py.StationType.RouteCAP,
        )
        self.assertAlmostEqual(
            float(
                ef_py.task_order_maintained_air_stationing(
                    assignment.task_order
                ).target_altitude_m
            ),
            6100.0,
        )
        self.assertAlmostEqual(
            float(
                ef_py.task_order_maintained_air_stationing(
                    assignment.task_order
                ).target_speed_mps
            ),
            205.0,
        )
        self.assertEqual(int(assignment.task_order.air_recovery.recovery_base_id), 81)
        self.assertAlmostEqual(float(assignment.task_order.air_takeoff.takeoff_interval_s), 12.5)
        self.assertEqual(
            ef_py.task_order_maintained_air_formation(
                assignment.task_order
            ).formation_role_id,
            ef_py.FormationRole.Wingman,
        )
        self.assertEqual(
            ef_py.task_order_maintained_air_formation(
                assignment.task_order
            ).wingman_slot_id,
            ef_py.WingmanSlot.Left,
        )
        self.assertEqual(
            int(assignment.task_order.naval_command_authority.officer_in_tactical_command),
            9001,
        )
        self.assertEqual(
            ef_py.task_order_maintained_naval_stationing(
                assignment.task_order
            ).naval_station_type,
            ef_py.NavalStationType.Support,
        )

        shell = ef_py.task_order_compatibility_shell_from_maintained_batch_contract(
            assignment.task_order
        )

        self.assertEqual(shell.task_type, ef_py.TaskType.CAP)
        self.assertEqual(int(shell.element_id), 7001)
        self.assertEqual(shell.station_type, ef_py.StationType.RouteCAP)
        self.assertAlmostEqual(float(shell.target_altitude_m), 6100.0)
        self.assertAlmostEqual(float(shell.target_speed_mps), 205.0)
        self.assertEqual(shell.formation_role_id, ef_py.FormationRole.Wingman)
        self.assertEqual(shell.wingman_slot_id, ef_py.WingmanSlot.Left)
        self.assertEqual(shell.naval_station_type, ef_py.NavalStationType.Support)

        roundtrip = ef_py.task_order_maintained_batch_contract(shell)
        self.assertEqual(
            ef_py.task_order_maintained_air_tasking_identity(roundtrip).task_type,
            ef_py.TaskType.CAP,
        )
        self.assertEqual(
            int(ef_py.task_order_maintained_air_tasking_identity(roundtrip).element_id),
            7001,
        )
        self.assertAlmostEqual(
            float(ef_py.task_order_maintained_air_stationing(roundtrip).target_speed_mps),
            205.0,
        )
        self.assertEqual(
            ef_py.task_order_maintained_air_formation(roundtrip).wingman_slot_id,
            ef_py.WingmanSlot.Left,
        )
        self.assertEqual(
            ef_py.task_order_maintained_naval_stationing(
                roundtrip
            ).naval_station_type,
            ef_py.NavalStationType.Support,
        )

    def test_mission_command_public_fields_match_expected_binding_surface(self) -> None:
        fields = tuple(name for name in dir(ef_py.MissionCommand()) if not name.startswith("_"))
        self.assertTupleEqual(
            fields,
            (
                "active",
                "assigned_target_id",
                "assigned_target_snapshot_time_s",
                "assigned_target_source_id",
                "assigned_target_track_id",
                "authorization_to_fire",
                "cmd_altitude_m",
                "cmd_heading_deg",
                "cmd_speed_mps",
                "command_code",
                "embarked_helo_entity_id",
                "engagement_authority_grantor_id",
                "engagement_authority_holder_id",
                "form_offset_x",
                "form_offset_y",
                "form_offset_z",
                "formation_id",
                "launch_helo",
                "recover_helo",
                "recovery_approach_type",
                "recovery_base_id",
                "recovery_runway_id",
                "reference_entity_id",
                "relay_oth_targeting",
                "roe_state",
                "route_ref_id",
                "runway_slot_id",
                "station_bearing_deg",
                "station_radius_m",
                "takeoff_clearance_id",
                "takeoff_interval_s",
                "takeoff_procedure_id",
                "threat_state",
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
