from __future__ import annotations

import unittest
from types import SimpleNamespace

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import ef_py  # noqa: E402

from python.rl.tasking.common_core_profile import (  # noqa: E402
    apply_task_order_common_core_defaults,
    apply_task_order_common_core_spec,
    normalize_task_order_spec,
    task_observation_codes,
)
from python.rl.tasking.leader_tasking import RuleBasedLeaderPhaseManager, ScriptedC2TaskManager  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
