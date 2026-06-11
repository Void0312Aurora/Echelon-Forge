from __future__ import annotations

import unittest
from types import SimpleNamespace

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import ef_py # noqa: E402

from python.rl.profile import ground_profile, naval_profile # noqa: E402
from python.rl.tasking import bridge as tasking_bridge # noqa: E402
from python.rl.tasking.common_core_profile import ( # noqa: E402
  apply_leader_intent_common_core_defaults,
  apply_pilot_report_common_core_defaults,
  apply_task_order_common_core_defaults,
  apply_task_order_common_core_spec,
  normalize_task_order_spec,
  task_observation_codes,
)
from python.rl.tasking.leader_tasking import ( # noqa: E402
  RuleBasedLeaderPhaseManager,
  ScriptedC2TaskManager,
)


class _DummySim:
  def get_agent_observation(self, agent_id: int) -> SimpleNamespace:
    _ = agent_id
    return SimpleNamespace(x=1200.0, y=-800.0, z=5200.0, heading=90.0)

  def get_instrument_state(self, agent_id: int) -> SimpleNamespace:
    _ = agent_id
    return SimpleNamespace(
      alt_radar=1400.0,
      ground_speed=165.0,
      heading=90.0,
      alt_baro=5200.0,
      ias=165.0,
    )


class CommonCoreSemanticTests(unittest.TestCase):
  def test_normalize_task_order_spec_without_profile_context_uses_common_fallback(self) -> None:
    normalized = normalize_task_order_spec(
      {
        "task_name": "TASK_CAP",
        "element_id": 88,
      }
    )

    self.assertEqual(normalized["service_profile"], ef_py.ServiceProfile.AirForce)
    self.assertEqual(normalized["task_family"], ef_py.TaskFamily.Patrol)
    self.assertEqual(normalized["task_type"], ef_py.TaskType.CAP)
    self.assertEqual(normalized["tactical_unit_type"], ef_py.TacticalUnitType.TacticalUnit)
    self.assertEqual(normalized["coordination_mode"], ef_py.CoordinationMode.Attached)

  def test_unknown_explicit_tasking_profile_raises_clear_error(self) -> None:
    with self.assertRaisesRegex(ValueError, "Unknown tasking profile"):
      normalize_task_order_spec({"tasking_profile": "space-force"})

  def test_split_dto_python_bindings_expose_common_and_air_fields(self) -> None:
    order = ef_py.TaskOrder()
    order.task_id = 11
    order.service_profile = ef_py.ServiceProfile.Navy
    order.task_family = ef_py.TaskFamily.Escort
    order.formation_role_id = ef_py.FormationRole.Wingman
    order.takeoff_interval_s = 7.5

    self.assertEqual(int(order.task_id), 11)
    self.assertEqual(order.service_profile, ef_py.ServiceProfile.Navy)
    self.assertEqual(order.task_family, ef_py.TaskFamily.Escort)
    self.assertEqual(order.formation_role_id, ef_py.FormationRole.Wingman)
    self.assertAlmostEqual(float(order.takeoff_interval_s), 7.5, places=6)

    intent = ef_py.LeaderIntent()
    intent.phase_id = ef_py.LeaderPhase.Departure
    intent.service_profile = ef_py.ServiceProfile.AirForce
    intent.task_family = ef_py.TaskFamily.Patrol
    intent.route_ref_id = 123

    self.assertEqual(intent.phase_id, ef_py.LeaderPhase.Departure)
    self.assertEqual(intent.service_profile, ef_py.ServiceProfile.AirForce)
    self.assertEqual(intent.task_family, ef_py.TaskFamily.Patrol)
    self.assertEqual(int(intent.route_ref_id), 123)

    report = ef_py.PilotReport()
    report.report_type = ef_py.CommMsgType.REP_JOINED
    report.task_id = 99
    report.service_profile = ef_py.ServiceProfile.Navy
    report.phase_id = int(ef_py.LeaderPhase.OnStation)
    report.formation_error_m = 12.5

    self.assertEqual(report.report_type, ef_py.CommMsgType.REP_JOINED)
    self.assertEqual(int(report.task_id), 99)
    self.assertEqual(report.service_profile, ef_py.ServiceProfile.Navy)
    self.assertEqual(int(report.phase_id), int(ef_py.LeaderPhase.OnStation))
    self.assertAlmostEqual(float(report.formation_error_m), 12.5, places=6)

  def test_normalize_task_order_spec_backfills_common_core(self) -> None:
    normalized = normalize_task_order_spec(
      {
        "task_family": "Recover",
        "recovery_base_id": 55,
        "recovery_runway_id": 7,
        "element_id": 88,
      }
    )

    self.assertEqual(normalized["service_profile"], ef_py.ServiceProfile.AirForce)
    self.assertEqual(normalized["task_family"], ef_py.TaskFamily.Recover)
    self.assertEqual(normalized["task_type"], ef_py.TaskType.RTB)
    self.assertEqual(normalized["tactical_unit_type"], ef_py.TacticalUnitType.TacticalUnit)
    self.assertEqual(normalized["command_relationship"], ef_py.CommandRelationship.TACON)
    self.assertEqual(normalized["authority_scope"], ef_py.AuthorityScope.Tactical)
    self.assertEqual(normalized["coordination_mode"], ef_py.CoordinationMode.Recover)
    self.assertEqual(int(normalized["recovery_site_id"]), 7)

  def test_common_core_explicit_order_override_wins(self) -> None:
    order = ef_py.TaskOrder()
    order.task_type = ef_py.TaskType.CAP

    apply_task_order_common_core_spec(
      order,
      {
        "service_profile": "Navy",
        "task_family": "Escort",
        "tactical_unit_type": "MissionPackage",
        "command_relationship": "Support",
        "authority_scope": "Operational",
        "coordination_mode": "Screen",
        "task_group_id": 601,
        "recovery_site_id": 44,
      },
    )
    apply_task_order_common_core_defaults(order, task_name="TASK_CAP")

    self.assertEqual(order.service_profile, ef_py.ServiceProfile.Navy)
    self.assertEqual(order.task_family, ef_py.TaskFamily.Escort)
    self.assertEqual(order.tactical_unit_type, ef_py.TacticalUnitType.MissionPackage)
    self.assertEqual(order.command_relationship, ef_py.CommandRelationship.Support)
    self.assertEqual(order.authority_scope, ef_py.AuthorityScope.Operational)
    self.assertEqual(order.coordination_mode, ef_py.CoordinationMode.Screen)
    self.assertEqual(int(order.task_group_id), 601)
    self.assertEqual(int(order.recovery_site_id), 44)

  def test_phase_manager_populates_common_core_chain(self) -> None:
    loader = SimpleNamespace(
      agent_id=42,
      sim=_DummySim(),
      mission_cmd={
        "target_heading": 90.0,
        "target_altitude": 5200.0,
        "target_speed": 210.0,
        "command_code": 3,
      },
      waypoints=[
        {"x": 0.0, "y": 0.0, "altitude_m": 5200.0, "speed_mps": 210.0},
        {"x": 15000.0, "y": 0.0, "altitude_m": 5200.0, "speed_mps": 210.0},
        {"x": 30000.0, "y": 5000.0, "altitude_m": 5200.0, "speed_mps": 210.0},
      ],
      waypoint_idx=0,
      scenario_data={},
      mission_phase_name="idle",
      post_waypoint_transition=None,
    )
    loader.get_ils_observation = lambda *args, **kwargs: [0.0, 0.0, 0.0, 99999.0]

    manager = RuleBasedLeaderPhaseManager()
    manager.reset(loader, sim_time_s=12.0, sync_to_kernel=False)

    self.assertEqual(loader.task_order.service_profile, ef_py.ServiceProfile.AirForce)
    self.assertEqual(loader.task_order.task_family, ef_py.TaskFamily.Patrol)
    self.assertEqual(loader.task_order.tactical_unit_type, ef_py.TacticalUnitType.Platform)
    self.assertEqual(loader.task_order.command_relationship, ef_py.CommandRelationship.TACON)
    self.assertEqual(loader.task_order.authority_scope, ef_py.AuthorityScope.Tactical)
    self.assertEqual(loader.task_order.coordination_mode, ef_py.CoordinationMode.Independent)

    self.assertEqual(loader.leader_intent.service_profile, ef_py.ServiceProfile.AirForce)
    self.assertEqual(loader.leader_intent.task_family, ef_py.TaskFamily.Patrol)
    self.assertEqual(loader.leader_intent.tactical_unit_type, ef_py.TacticalUnitType.Platform)
    self.assertEqual(int(loader.leader_intent.tactical_unit_id), 42)
    self.assertEqual(loader.leader_intent.coordination_mode, ef_py.CoordinationMode.Independent)

    self.assertEqual(loader.pilot_report.service_profile, ef_py.ServiceProfile.AirForce)
    self.assertEqual(loader.pilot_report.task_family, ef_py.TaskFamily.Patrol)
    self.assertEqual(loader.pilot_report.tactical_unit_type, ef_py.TacticalUnitType.Platform)
    self.assertEqual(int(loader.pilot_report.tactical_unit_id), 42)
    self.assertEqual(loader.pilot_report.coordination_mode, ef_py.CoordinationMode.Independent)

  def test_scripted_c2_retask_updates_common_core(self) -> None:
    order = ef_py.TaskOrder()
    order.active = True
    order.assignee_id = 42
    order.assignee_kind = ef_py.AssigneeKind.Element
    order.element_id = 77
    order.recovery_runway_id = 9

    loader = SimpleNamespace(
      agent_id=42,
      task_order=order,
      mission_cmd={"target_altitude": 2400.0, "target_speed": 190.0},
      scenario_data={},
      waypoints=[],
      waypoint_idx=0,
    )

    manager = ScriptedC2TaskManager()
    manager._retask_order(loader, task_name=manager.TASK_CAP, sim_time_s=5.0)
    self.assertEqual(order.task_family, ef_py.TaskFamily.Patrol)
    self.assertEqual(order.tactical_unit_type, ef_py.TacticalUnitType.TacticalUnit)
    self.assertEqual(order.coordination_mode, ef_py.CoordinationMode.Attached)

    manager._retask_order(loader, task_name=manager.TASK_RTB, sim_time_s=10.0)
    self.assertEqual(order.task_family, ef_py.TaskFamily.Recover)
    self.assertEqual(order.coordination_mode, ef_py.CoordinationMode.Recover)
    self.assertEqual(int(order.recovery_site_id), 9)

  def test_task_observation_codes_prefer_common_core(self) -> None:
    task = ef_py.TaskOrder()
    task.task_type = ef_py.TaskType.Idle
    task.station_type = ef_py.StationType.Racetrack
    task.task_family = ef_py.TaskFamily.Recover
    task.coordination_mode = ef_py.CoordinationMode.Recover
    task.tactical_unit_type = ef_py.TacticalUnitType.TacticalUnit

    primary_code, coordination_code, unit_code = task_observation_codes(task, fallback_phase_id=8)

    self.assertEqual(primary_code, float(int(ef_py.TaskType.RTB)))
    self.assertEqual(coordination_code, float(int(ef_py.StationType.Racetrack)))
    self.assertEqual(unit_code, 8.0)


class GroundProfileSemanticTests(unittest.TestCase):
  def test_bridge_resolves_ground_aliases(self) -> None:
    for alias in ("army", "ground", "land"):
      profile = tasking_bridge.resolve_tasking_profile(alias)
      self.assertEqual(profile.__name__.split(".")[-1], "ground_adapter")

  def test_bridge_resolves_army_service_profile_to_ground(self) -> None:
    if not hasattr(ef_py.ServiceProfile, "Army"):
      self.skipTest("Army service profile binding not available")
    profile = tasking_bridge.resolve_tasking_profile(ef_py.ServiceProfile.Army)
    self.assertEqual(profile.__name__.split(".")[-1], "ground_adapter")

  def test_loader_profile_prefers_explicit_tasking_profile_over_army_service_profile(self) -> None:
    task = ef_py.TaskOrder()
    task.service_profile = ef_py.ServiceProfile.Army
    loader = SimpleNamespace(
      scenario_data={"tasking_profile": "air"},
      task_order=task,
      mission_cmd={},
    )

    profile = tasking_bridge.tasking_profile_for_loader(loader)

    self.assertIs(profile, tasking_bridge.resolve_tasking_profile("air"))

  def test_loader_profile_infers_ground_from_army_service_profile(self) -> None:
    task = ef_py.TaskOrder()
    task.service_profile = ef_py.ServiceProfile.Army
    loader = SimpleNamespace(
      scenario_data={},
      task_order=task,
      mission_cmd={},
    )

    profile = tasking_bridge.tasking_profile_for_loader(loader)

    self.assertIs(profile, tasking_bridge.resolve_tasking_profile("ground"))

  def test_loader_profile_fails_closed_for_unknown_explicit_profile(self) -> None:
    task = ef_py.TaskOrder()
    task.service_profile = ef_py.ServiceProfile.Army
    loader = SimpleNamespace(
      scenario_data={"tasking_profile": "groudn"},
      task_order=task,
      mission_cmd={},
    )

    with self.assertRaisesRegex(ValueError, "Unknown tasking profile"):
      tasking_bridge.tasking_profile_for_loader(loader)

  def test_loader_profile_fails_closed_for_unknown_service_profile_hint(self) -> None:
    loader = SimpleNamespace(
      scenario_data={"service_profile": "Armie"},
      task_order=None,
      mission_cmd={},
    )

    with self.assertRaisesRegex(ValueError, "Unknown tasking profile"):
      tasking_bridge.tasking_profile_for_loader(loader)

  def test_loader_profile_keeps_legacy_air_default_when_no_profile_hint_exists(self) -> None:
    loader = SimpleNamespace(
      scenario_data={},
      task_order=ef_py.TaskOrder(),
      mission_cmd={},
    )

    self.assertIs(tasking_bridge.tasking_profile_for_loader(loader), tasking_bridge.resolve_tasking_profile("air"))

  def test_normalize_task_order_spec_uses_ground_defaults(self) -> None:
    cases = {
      "TASK_MOVE": (
        ef_py.TaskFamily.Transit,
        ef_py.CommandRelationship.TACON,
        ef_py.CoordinationMode.Independent,
      ),
      "TASK_OCCUPY": (
        ef_py.TaskFamily.Defend,
        ef_py.CommandRelationship.TACON,
        ef_py.CoordinationMode.Independent,
      ),
      "TASK_SUPPORT": (
        ef_py.TaskFamily.Defend,
        ef_py.CommandRelationship.Support,
        ef_py.CoordinationMode.Support,
      ),
    }

    for task_name, expected in cases.items():
      normalized = tasking_bridge.normalize_task_order_spec(
        {
          "tasking_profile": "land",
          "task_name": task_name,
          "parent_node_id": 4201,
          "supported_node_id": 4202,
          "supporting_node_id": 4203,
        }
      )

      self.assertEqual(normalized["service_profile"], ef_py.ServiceProfile.Army)
      self.assertEqual(normalized["task_family"], expected[0])
      self.assertEqual(normalized["tactical_unit_type"], ef_py.TacticalUnitType.TacticalUnit)
      self.assertEqual(normalized["command_relationship"], expected[1])
      self.assertEqual(normalized["authority_scope"], ef_py.AuthorityScope.Tactical)
      self.assertEqual(normalized["coordination_mode"], expected[2])
      self.assertEqual(int(normalized["parent_node_id"]), 4201)
      self.assertEqual(int(normalized["supported_node_id"]), 4202)
      self.assertEqual(int(normalized["supporting_node_id"]), 4203)

  def test_common_core_defaults_preserve_ground_semantics_and_ids(self) -> None:
    move_order = ef_py.TaskOrder()
    move_order.service_profile = ef_py.ServiceProfile.Army
    apply_task_order_common_core_defaults(move_order, task_name="TASK_MOVE")
    self.assertEqual(move_order.ground_task_mode, ef_py.GroundTaskMode.MoveStatic)

    order = ef_py.TaskOrder()
    order.service_profile = ef_py.ServiceProfile.Army
    order.parent_node_id = 5101
    order.task_group_id = 6101
    order.supported_node_id = 5201
    order.supporting_node_id = 5301
    order.assignee_id = 5401

    apply_task_order_common_core_defaults(order, task_name="TASK_SUPPORT")

    self.assertEqual(order.service_profile, ef_py.ServiceProfile.Army)
    self.assertEqual(order.task_family, ef_py.TaskFamily.Defend)
    self.assertEqual(order.tactical_unit_type, ef_py.TacticalUnitType.TacticalUnit)
    self.assertEqual(order.command_relationship, ef_py.CommandRelationship.Support)
    self.assertEqual(order.authority_scope, ef_py.AuthorityScope.Tactical)
    self.assertEqual(order.coordination_mode, ef_py.CoordinationMode.Support)
    self.assertEqual(int(order.supported_node_id), 5201)
    self.assertEqual(int(order.supporting_node_id), 5301)
    self.assertEqual(int(order.officer_in_tactical_command), 5101)
    self.assertEqual(order.ground_task_mode, ef_py.GroundTaskMode.SupportStatic)
    self.assertEqual(int(order.objective_area_id), 5201)
    self.assertEqual(int(order.objective_node_id), 5201)
    self.assertEqual(int(order.ground_commander_id), 5101)

    intent = ef_py.LeaderIntent()
    apply_leader_intent_common_core_defaults(intent, order=order, task_name="TASK_SUPPORT", default_tactical_unit_id=99)
    self.assertEqual(intent.service_profile, ef_py.ServiceProfile.Army)
    self.assertEqual(intent.task_family, ef_py.TaskFamily.Defend)
    self.assertEqual(intent.tactical_unit_type, ef_py.TacticalUnitType.TacticalUnit)
    self.assertEqual(intent.coordination_mode, ef_py.CoordinationMode.Support)
    self.assertEqual(int(intent.task_group_id), 6101)
    self.assertEqual(int(intent.tactical_unit_id), 5301)
    self.assertEqual(int(intent.officer_in_tactical_command), 5101)
    self.assertEqual(intent.ground_status_phase, ef_py.GroundStatusPhase.SupportingStatic)
    self.assertEqual(intent.ground_task_mode, ef_py.GroundTaskMode.SupportStatic)
    self.assertEqual(int(intent.objective_area_id), 5201)
    self.assertEqual(int(intent.objective_node_id), 5201)
    self.assertEqual(int(intent.ground_commander_id), 5101)

    report = ef_py.PilotReport()
    apply_pilot_report_common_core_defaults(report, order=order, task_name="TASK_SUPPORT", default_tactical_unit_id=99)
    self.assertEqual(report.service_profile, ef_py.ServiceProfile.Army)
    self.assertEqual(report.task_family, ef_py.TaskFamily.Defend)
    self.assertEqual(report.tactical_unit_type, ef_py.TacticalUnitType.TacticalUnit)
    self.assertEqual(report.coordination_mode, ef_py.CoordinationMode.Support)
    self.assertEqual(int(report.task_group_id), 6101)
    self.assertEqual(int(report.tactical_unit_id), 5301)
    self.assertEqual(int(report.officer_in_tactical_command), 5101)
    self.assertEqual(report.ground_status_phase, ef_py.GroundStatusPhase.SupportingStatic)
    self.assertEqual(report.ground_task_mode, ef_py.GroundTaskMode.SupportStatic)
    self.assertEqual(int(report.objective_area_id), 5201)
    self.assertEqual(int(report.objective_node_id), 5201)
    self.assertEqual(int(report.ground_commander_id), 5101)

  def test_ground_mission_command_builder_populates_ground_static_command_slice(self) -> None:
    task = ef_py.TaskOrder()
    task.service_profile = ef_py.ServiceProfile.Army
    task.ground_task_mode = ef_py.GroundTaskMode.OccupyStatic
    task.objective_area_id = 7101
    task.objective_node_id = 7201
    task.ground_commander_id = 7301
    task.tactical_cadence_hz = 1.0
    loader = SimpleNamespace(
      task_order=task,
      mission_cmd={"command_code": 7},
      leader_intent=None,
    )

    cmd = ground_profile.build_kernel_mission_command(loader)

    self.assertEqual(ground_profile.build_kernel_mission_command.__module__, "python.rl.profile.ground_profile")
    self.assertTrue(bool(cmd.active))
    self.assertEqual(int(cmd.command_code), 7)
    self.assertEqual(cmd.ground_task_mode, ef_py.GroundTaskMode.OccupyStatic)
    self.assertEqual(int(cmd.objective_area_id), 7101)
    self.assertEqual(int(cmd.objective_node_id), 7201)
    self.assertEqual(int(cmd.ground_commander_id), 7301)
    self.assertAlmostEqual(float(cmd.tactical_cadence_hz), 1.0)

  def test_ground_mission_command_builder_infers_static_support_mode_without_air_fields(self) -> None:
    task = ef_py.TaskOrder()
    task.service_profile = ef_py.ServiceProfile.Army
    task.supported_node_id = 8101
    task.supporting_node_id = 8201
    task.parent_node_id = 8301
    loader = SimpleNamespace(
      task_order=task,
      mission_cmd={},
      leader_intent=None,
      c2_task_name="TASK_SUPPORT",
    )

    cmd = ground_profile.build_kernel_mission_command(loader)

    self.assertTrue(bool(cmd.active))
    self.assertEqual(cmd.ground_task_mode, ef_py.GroundTaskMode.SupportStatic)
    self.assertEqual(int(cmd.objective_area_id), 8101)
    self.assertEqual(int(cmd.objective_node_id), 8101)
    self.assertEqual(int(cmd.ground_commander_id), 8301)
    self.assertEqual(int(cmd.formation_id), 0)
    self.assertAlmostEqual(float(cmd.cmd_altitude_m), 0.0)

  def test_ground_recovery_approach_inference_returns_binding_enum(self) -> None:
    none_value = getattr(ef_py.RecoveryApproachType, "None")
    self.assertEqual(ground_profile.infer_recovery_approach_type(SimpleNamespace(), task=None), none_value)

    order = ef_py.TaskOrder()
    order.recovery_approach_type = ef_py.RecoveryApproachType.Visual
    self.assertEqual(ground_profile.infer_recovery_approach_type(SimpleNamespace(), task=order), ef_py.RecoveryApproachType.Visual)


class NavalProfileSemanticTests(unittest.TestCase):
  def test_bridge_resolves_naval_profile(self) -> None:
    profile = tasking_bridge.resolve_tasking_profile("naval")
    self.assertEqual(profile.__name__.split(".")[-1], "naval_adapter")

  def test_normalize_task_order_spec_uses_naval_defaults(self) -> None:
    normalized = tasking_bridge.normalize_task_order_spec(
      {
        "tasking_profile": "naval",
        "service_profile": "Navy",
        "task_group_id": 7001,
        "task_name": "TASK_SCREEN",
      }
    )
    self.assertEqual(normalized["service_profile"], ef_py.ServiceProfile.Navy)
    self.assertEqual(normalized["task_family"], ef_py.TaskFamily.Escort)
    self.assertEqual(normalized["tactical_unit_type"], ef_py.TacticalUnitType.CommandNode)
    self.assertEqual(normalized["coordination_mode"], ef_py.CoordinationMode.Screen)
    self.assertEqual(int(normalized["warfare_role_code"]), int(ef_py.NavalWarfareRole.ScreenCommander))
    self.assertEqual(normalized["naval_station_type"], ef_py.NavalStationType.Screen)
    self.assertEqual(int(normalized["officer_in_tactical_command"]), 7001)

  def test_common_core_defaults_can_keep_naval_semantics(self) -> None:
    order = ef_py.TaskOrder()
    order.service_profile = ef_py.ServiceProfile.Navy
    order.task_group_id = 7001
    order.parent_node_id = 7101
    apply_task_order_common_core_defaults(order, task_name="TASK_SCREEN")
    self.assertEqual(order.service_profile, ef_py.ServiceProfile.Navy)
    self.assertEqual(order.task_family, ef_py.TaskFamily.Escort)
    self.assertEqual(order.tactical_unit_type, ef_py.TacticalUnitType.CommandNode)
    self.assertEqual(order.coordination_mode, ef_py.CoordinationMode.Screen)
    self.assertEqual(int(order.warfare_role_code), int(ef_py.NavalWarfareRole.ScreenCommander))
    self.assertEqual(int(order.officer_in_tactical_command), 7001)
    self.assertEqual(order.naval_station_type, ef_py.NavalStationType.Screen)

    intent = ef_py.LeaderIntent()
    intent.service_profile = ef_py.ServiceProfile.Navy
    apply_leader_intent_common_core_defaults(intent, order=order, task_name="TASK_SCREEN", default_tactical_unit_id=99)
    self.assertEqual(intent.service_profile, ef_py.ServiceProfile.Navy)
    self.assertEqual(intent.task_family, ef_py.TaskFamily.Escort)
    self.assertEqual(intent.tactical_unit_type, ef_py.TacticalUnitType.CommandNode)
    self.assertEqual(intent.coordination_mode, ef_py.CoordinationMode.Screen)
    self.assertEqual(int(intent.warfare_role_code), int(ef_py.NavalWarfareRole.ScreenCommander))
    self.assertEqual(int(intent.officer_in_tactical_command), 7001)

    report = ef_py.PilotReport()
    report.service_profile = ef_py.ServiceProfile.Navy
    apply_pilot_report_common_core_defaults(report, order=order, task_name="TASK_SCREEN", default_tactical_unit_id=99)
    self.assertEqual(report.service_profile, ef_py.ServiceProfile.Navy)
    self.assertEqual(report.task_family, ef_py.TaskFamily.Escort)
    self.assertEqual(report.tactical_unit_type, ef_py.TacticalUnitType.CommandNode)
    self.assertEqual(report.coordination_mode, ef_py.CoordinationMode.Screen)
    self.assertEqual(int(report.warfare_role_code), int(ef_py.NavalWarfareRole.ScreenCommander))
    self.assertEqual(int(report.officer_in_tactical_command), 7001)

  def test_normalize_task_order_spec_infers_minimal_support_structure(self) -> None:
    normalized = tasking_bridge.normalize_task_order_spec(
      {
        "tasking_profile": "naval",
        "service_profile": "Navy",
        "task_group_id": 7401,
        "parent_node_id": 7411,
        "task_name": "TASK_SUPPORT",
      }
    )
    self.assertEqual(normalized["task_family"], ef_py.TaskFamily.Escort)
    self.assertEqual(normalized["coordination_mode"], ef_py.CoordinationMode.Support)
    self.assertEqual(normalized["tactical_unit_type"], ef_py.TacticalUnitType.CommandNode)
    self.assertEqual(int(normalized["warfare_role_code"]), int(ef_py.NavalWarfareRole.LogisticsCoordinator))
    self.assertEqual(normalized["naval_station_type"], ef_py.NavalStationType.Support)
    self.assertEqual(int(normalized["officer_in_tactical_command"]), 7401)

  def test_naval_mission_command_builder_populates_naval_station_fields(self) -> None:
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
        "scenario_data": {},
        "task_order": task,
        "mission_cmd": {},
        "agent_id": 5101,
        "active_roster": [agent_member],
        "get_active_roster_member": staticmethod(lambda entity_id=None, entity_name=None: agent_member),
      },
    )()

    cmd = naval_profile.build_kernel_mission_command(loader)

    self.assertTrue(bool(cmd.active))
    self.assertEqual(int(cmd.command_code), 3)
    self.assertEqual(int(cmd.reference_entity_id), 5201)
    self.assertAlmostEqual(float(cmd.station_radius_m), 14000.0, places=6)
    self.assertAlmostEqual(float(cmd.station_bearing_deg), 35.0, places=6)
    self.assertAlmostEqual(float(cmd.cmd_heading_deg), 35.0, places=6)
    self.assertAlmostEqual(float(cmd.cmd_speed_mps), 12.5, places=6)


if __name__ == "__main__":
  unittest.main()
