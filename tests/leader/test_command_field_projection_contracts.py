from __future__ import annotations

import unittest
from types import SimpleNamespace

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

import ef_py # noqa: E402

from gym_envs.leader_env_parts import ( # noqa: E402
  LEADER_INTENT_FIELDS,
  PILOT_REPORT_FIELDS,
  TASK_ORDER_FIELDS,
  clone_leader_intent,
  clone_pilot_report,
  clone_task_order,
)


class NavalContractFieldTests(unittest.TestCase):
  def test_python_bindings_expose_naval_tasking_fields(self) -> None:
    order = ef_py.TaskOrder()
    order.warfare_role_code = int(ef_py.NavalWarfareRole.ScreenCommander)
    order.officer_in_tactical_command = 7101
    order.naval_station_type = ef_py.NavalStationType.Screen

    intent = ef_py.LeaderIntent()
    intent.warfare_role_code = int(ef_py.NavalWarfareRole.AirDefenseCommander)
    intent.officer_in_tactical_command = 7201

    report = ef_py.PilotReport()
    report.warfare_role_code = int(ef_py.NavalWarfareRole.SeaControlCommander)
    report.officer_in_tactical_command = 7301

    self.assertEqual(int(order.warfare_role_code), int(ef_py.NavalWarfareRole.ScreenCommander))
    self.assertEqual(int(order.officer_in_tactical_command), 7101)
    self.assertEqual(order.naval_station_type, ef_py.NavalStationType.Screen)
    self.assertEqual(int(intent.warfare_role_code), int(ef_py.NavalWarfareRole.AirDefenseCommander))
    self.assertEqual(int(intent.officer_in_tactical_command), 7201)
    self.assertEqual(int(report.warfare_role_code), int(ef_py.NavalWarfareRole.SeaControlCommander))
    self.assertEqual(int(report.officer_in_tactical_command), 7301)

  def test_simulation_kernel_tasking_roundtrip_preserves_naval_fields(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(17)

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

    order = ef_py.TaskOrder()
    order.service_profile = ef_py.ServiceProfile.Navy
    order.task_family = ef_py.TaskFamily.Escort
    order.coordination_mode = ef_py.CoordinationMode.Screen
    order.warfare_role_code = int(ef_py.NavalWarfareRole.ScreenCommander)
    order.officer_in_tactical_command = 7101
    order.naval_station_type = ef_py.NavalStationType.Screen

    intent = ef_py.LeaderIntent()
    intent.service_profile = ef_py.ServiceProfile.Navy
    intent.task_family = ef_py.TaskFamily.Escort
    intent.coordination_mode = ef_py.CoordinationMode.Screen
    intent.warfare_role_code = int(ef_py.NavalWarfareRole.AirDefenseCommander)
    intent.officer_in_tactical_command = 7201

    report = ef_py.PilotReport()
    report.service_profile = ef_py.ServiceProfile.Navy
    report.task_family = ef_py.TaskFamily.Escort
    report.coordination_mode = ef_py.CoordinationMode.Screen
    report.warfare_role_code = int(ef_py.NavalWarfareRole.SeaControlCommander)
    report.officer_in_tactical_command = 7301

    kernel.set_task_order(entity_id, order)
    kernel.set_leader_intent(entity_id, intent)
    kernel.set_pilot_report(entity_id, report)

    got_order = kernel.get_task_order(entity_id)
    got_intent = kernel.get_leader_intent(entity_id)
    got_report = kernel.get_pilot_report(entity_id)

    self.assertEqual(got_order.service_profile, ef_py.ServiceProfile.Navy)
    self.assertEqual(int(got_order.warfare_role_code), int(ef_py.NavalWarfareRole.ScreenCommander))
    self.assertEqual(int(got_order.officer_in_tactical_command), 7101)
    self.assertEqual(got_order.naval_station_type, ef_py.NavalStationType.Screen)
    self.assertEqual(got_intent.service_profile, ef_py.ServiceProfile.Navy)
    self.assertEqual(int(got_intent.warfare_role_code), int(ef_py.NavalWarfareRole.AirDefenseCommander))
    self.assertEqual(int(got_intent.officer_in_tactical_command), 7201)
    self.assertEqual(got_report.service_profile, ef_py.ServiceProfile.Navy)
    self.assertEqual(int(got_report.warfare_role_code), int(ef_py.NavalWarfareRole.SeaControlCommander))
    self.assertEqual(int(got_report.officer_in_tactical_command), 7301)


class TwoShipContractFieldTests(unittest.TestCase):
  def test_clone_field_lists_match_bound_contract_types(self) -> None:
    def public_data_fields(obj: object) -> set[str]:
      return {name for name in dir(obj) if not name.startswith("_")}

    self.assertSetEqual(public_data_fields(ef_py.TaskOrder()), set(TASK_ORDER_FIELDS))
    self.assertSetEqual(public_data_fields(ef_py.LeaderIntent()), set(LEADER_INTENT_FIELDS))
    self.assertSetEqual(public_data_fields(ef_py.PilotReport()), set(PILOT_REPORT_FIELDS))

  def test_clone_field_lists_follow_bound_field_order(self) -> None:
    def public_data_fields_in_order(obj: object) -> tuple[str, ...]:
      return tuple(name for name in dir(obj) if not name.startswith("_"))

    self.assertTupleEqual(public_data_fields_in_order(ef_py.TaskOrder()), TASK_ORDER_FIELDS)
    self.assertTupleEqual(public_data_fields_in_order(ef_py.LeaderIntent()), LEADER_INTENT_FIELDS)
    self.assertTupleEqual(public_data_fields_in_order(ef_py.PilotReport()), PILOT_REPORT_FIELDS)

  def test_clone_task_order_preserves_two_ship_fields(self) -> None:
    source = SimpleNamespace(
      task_id=41,
      task_type=ef_py.TaskType.CAP,
      service_profile=ef_py.ServiceProfile.AirForce,
      task_family=ef_py.TaskFamily.Patrol,
      tactical_unit_type=ef_py.TacticalUnitType.TacticalUnit,
      priority=3,
      issuer_id=1001,
      assignee_id=9001,
      command_relationship=ef_py.CommandRelationship.TACON,
      authority_scope=ef_py.AuthorityScope.Tactical,
      parent_node_id=5001,
      task_group_id=6001,
      supported_node_id=7001,
      supporting_node_id=8001,
      role_code=21,
      warfare_role_code=int(ef_py.NavalWarfareRole.ScreenCommander),
      coordination_mode=ef_py.CoordinationMode.Attached,
      relative_slot_code=12,
      assignee_kind=ef_py.AssigneeKind.Element,
      recovery_site_id=88,
      officer_in_tactical_command=7101,
      element_id=77,
      package_id=0,
      lead_aircraft_id=9001,
      active=True,
      issue_time_s=12.5,
      anchor_x_m=25000.0,
      anchor_y_m=12000.0,
      anchor_z_m=2000.0,
      station_type=ef_py.StationType.Racetrack,
      naval_station_type=ef_py.NavalStationType.Screen,
      station_radius_m=15000.0,
      station_leg_length_m=28000.0,
      station_heading_deg=35.0,
      altitude_block_min_m=1600.0,
      altitude_block_max_m=2600.0,
      target_altitude_m=2100.0,
      speed_min_mps=180.0,
      speed_max_mps=240.0,
      target_speed_mps=210.0,
      entry_condition_code=0,
      exit_condition_code=0,
      on_station_time_s=900.0,
      fuel_bingo_override_kg=1200.0,
      runway_slot_id=int(ef_py.RunwaySlotPosition.Left),
      takeoff_clearance_id=int(ef_py.TakeoffClearanceState.LineUpAndWait),
      takeoff_interval_s=45.0,
      takeoff_procedure_id=int(ef_py.TakeoffProcedureType.Wing),
      recovery_base_id=5,
      recovery_runway_id=2,
      recovery_approach_type=ef_py.RecoveryApproachType.ILS,
      formation_template_id=12,
      formation_contract_id=99,
      formation_role_id=ef_py.FormationRole.Wingman,
      wingman_slot_id=ef_py.WingmanSlot.Left,
      join_policy_id=3,
      rejoin_policy_id=4,
      mutual_support_mode=2,
      support_sector_id=501,
    )

    clone = clone_task_order(source)
    self.assertEqual(clone.service_profile, ef_py.ServiceProfile.AirForce)
    self.assertEqual(clone.task_family, ef_py.TaskFamily.Patrol)
    self.assertEqual(clone.tactical_unit_type, ef_py.TacticalUnitType.TacticalUnit)
    self.assertEqual(clone.command_relationship, ef_py.CommandRelationship.TACON)
    self.assertEqual(clone.authority_scope, ef_py.AuthorityScope.Tactical)
    self.assertEqual(int(clone.parent_node_id), 5001)
    self.assertEqual(int(clone.task_group_id), 6001)
    self.assertEqual(int(clone.supported_node_id), 7001)
    self.assertEqual(int(clone.supporting_node_id), 8001)
    self.assertEqual(int(clone.role_code), 21)
    self.assertEqual(int(clone.warfare_role_code), int(ef_py.NavalWarfareRole.ScreenCommander))
    self.assertEqual(clone.coordination_mode, ef_py.CoordinationMode.Attached)
    self.assertEqual(int(clone.relative_slot_code), 12)
    self.assertEqual(int(clone.recovery_site_id), 88)
    self.assertEqual(int(clone.officer_in_tactical_command), 7101)
    self.assertEqual(clone.assignee_kind, ef_py.AssigneeKind.Element)
    self.assertEqual(int(clone.element_id), 77)
    self.assertEqual(int(clone.lead_aircraft_id), 9001)
    self.assertEqual(clone.naval_station_type, ef_py.NavalStationType.Screen)
    self.assertEqual(clone.runway_slot_id, ef_py.RunwaySlotPosition.Left)
    self.assertEqual(clone.takeoff_clearance_id, ef_py.TakeoffClearanceState.LineUpAndWait)
    self.assertAlmostEqual(float(clone.takeoff_interval_s), 45.0, places=6)
    self.assertEqual(clone.takeoff_procedure_id, ef_py.TakeoffProcedureType.Wing)
    self.assertEqual(int(clone.formation_template_id), 12)
    self.assertEqual(clone.formation_role_id, ef_py.FormationRole.Wingman)
    self.assertEqual(clone.wingman_slot_id, ef_py.WingmanSlot.Left)
    self.assertEqual(int(clone.join_policy_id), 3)
    self.assertEqual(int(clone.support_sector_id), 501)

  def test_clone_leader_intent_preserves_two_ship_fields(self) -> None:
    source = SimpleNamespace(
      phase_id=ef_py.LeaderPhase.TransitToStation,
      element_phase_id=8,
      service_profile=ef_py.ServiceProfile.AirForce,
      task_family=ef_py.TaskFamily.Patrol,
      tactical_unit_type=ef_py.TacticalUnitType.TacticalUnit,
      tactical_unit_id=77,
      task_group_id=6001,
      role_code=21,
      warfare_role_code=int(ef_py.NavalWarfareRole.AirDefenseCommander),
      coordination_mode=ef_py.CoordinationMode.Follow,
      relative_slot_code=12,
      recovery_site_id=88,
      officer_in_tactical_command=7201,
      command_code=3,
      route_ref_id=7,
      runway_slot_id=int(ef_py.RunwaySlotPosition.Left),
      takeoff_clearance_id=int(ef_py.TakeoffClearanceState.LineUpAndWait),
      takeoff_interval_s=45.0,
      takeoff_procedure_id=int(ef_py.TakeoffProcedureType.Wing),
      recovery_base_id=5,
      recovery_runway_id=2,
      recovery_approach_type=ef_py.RecoveryApproachType.ILS,
      cmd_heading_deg=90.0,
      cmd_altitude_m=2200.0,
      cmd_speed_mps=205.0,
      formation_id=0,
      form_offset_x=0.0,
      form_offset_y=0.0,
      form_offset_z=0.0,
      assigned_target_id=0,
      authorization_to_fire=False,
      formation_mode_id=ef_py.FormationMode.Cruise,
      join_required_flag=True,
      rejoin_required_flag=False,
      split_flag=False,
      support_anchor_x_m=24000.0,
      support_anchor_y_m=11000.0,
      support_slot_offset_x_m=-500.0,
      support_slot_offset_y_m=180.0,
      wingman_command_mode=ef_py.WingmanCommandMode.HoldSlot,
      approach_armed=False,
      commit_to_land=False,
      abort_flag=False,
      active=True,
    )

    clone = clone_leader_intent(source)
    self.assertEqual(clone.service_profile, ef_py.ServiceProfile.AirForce)
    self.assertEqual(clone.task_family, ef_py.TaskFamily.Patrol)
    self.assertEqual(clone.tactical_unit_type, ef_py.TacticalUnitType.TacticalUnit)
    self.assertEqual(int(clone.tactical_unit_id), 77)
    self.assertEqual(int(clone.task_group_id), 6001)
    self.assertEqual(int(clone.role_code), 21)
    self.assertEqual(int(clone.warfare_role_code), int(ef_py.NavalWarfareRole.AirDefenseCommander))
    self.assertEqual(clone.coordination_mode, ef_py.CoordinationMode.Follow)
    self.assertEqual(int(clone.relative_slot_code), 12)
    self.assertEqual(int(clone.recovery_site_id), 88)
    self.assertEqual(int(clone.officer_in_tactical_command), 7201)
    self.assertEqual(int(clone.element_phase_id), 8)
    self.assertEqual(clone.runway_slot_id, ef_py.RunwaySlotPosition.Left)
    self.assertEqual(clone.takeoff_clearance_id, ef_py.TakeoffClearanceState.LineUpAndWait)
    self.assertAlmostEqual(float(clone.takeoff_interval_s), 45.0, places=6)
    self.assertEqual(clone.takeoff_procedure_id, ef_py.TakeoffProcedureType.Wing)
    self.assertEqual(clone.formation_mode_id, ef_py.FormationMode.Cruise)
    self.assertTrue(bool(clone.join_required_flag))
    self.assertAlmostEqual(float(clone.support_anchor_x_m), 24000.0, places=6)
    self.assertAlmostEqual(float(clone.support_slot_offset_y_m), 180.0, places=6)
    self.assertEqual(clone.wingman_command_mode, ef_py.WingmanCommandMode.HoldSlot)

  def test_clone_pilot_report_preserves_two_ship_fields(self) -> None:
    source = SimpleNamespace(
      report_type=ef_py.CommMsgType.REP_JOINED,
      sender_id=9002,
      task_id=41,
      service_profile=ef_py.ServiceProfile.AirForce,
      task_family=ef_py.TaskFamily.Patrol,
      tactical_unit_type=ef_py.TacticalUnitType.TacticalUnit,
      tactical_unit_id=77,
      task_group_id=6001,
      role_code=22,
      warfare_role_code=int(ef_py.NavalWarfareRole.SeaControlCommander),
      coordination_mode=ef_py.CoordinationMode.Attached,
      officer_in_tactical_command=7301,
      element_id=77,
      phase_id=int(ef_py.LeaderPhase.OnStation),
      formation_role_id=int(ef_py.FormationRole.Wingman),
      timestamp_s=31.5,
      status_value=1.0,
      entity_ref=0,
      location_x_m=25010.0,
      location_y_m=11980.0,
      location_z_m=2100.0,
      formation_error_m=12.0,
      bearing_error_deg=-4.5,
      closure_mps=6.0,
      separation_m=142.0,
      active=True,
    )

    clone = clone_pilot_report(source)
    self.assertEqual(clone.report_type, ef_py.CommMsgType.REP_JOINED)
    self.assertEqual(clone.service_profile, ef_py.ServiceProfile.AirForce)
    self.assertEqual(clone.task_family, ef_py.TaskFamily.Patrol)
    self.assertEqual(clone.tactical_unit_type, ef_py.TacticalUnitType.TacticalUnit)
    self.assertEqual(int(clone.tactical_unit_id), 77)
    self.assertEqual(int(clone.task_group_id), 6001)
    self.assertEqual(int(clone.role_code), 22)
    self.assertEqual(int(clone.warfare_role_code), int(ef_py.NavalWarfareRole.SeaControlCommander))
    self.assertEqual(clone.coordination_mode, ef_py.CoordinationMode.Attached)
    self.assertEqual(int(clone.officer_in_tactical_command), 7301)
    self.assertEqual(int(clone.element_id), 77)
    self.assertEqual(int(clone.formation_role_id), int(ef_py.FormationRole.Wingman))
    self.assertAlmostEqual(float(clone.formation_error_m), 12.0, places=6)
    self.assertAlmostEqual(float(clone.bearing_error_deg), -4.5, places=6)
    self.assertAlmostEqual(float(clone.closure_mps), 6.0, places=6)
    self.assertAlmostEqual(float(clone.separation_m), 142.0, places=6)


if __name__ == "__main__":
  unittest.main()
