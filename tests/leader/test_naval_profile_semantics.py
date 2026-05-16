from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import ef_py  # noqa: E402

from python.rl.tasking.bridge import normalize_task_order_spec, resolve_tasking_profile  # noqa: E402
from python.rl.tasking.common_core_profile import (  # noqa: E402
    apply_leader_intent_common_core_defaults,
    apply_pilot_report_common_core_defaults,
    apply_task_order_common_core_defaults,
)


class NavalProfileSemanticTests(unittest.TestCase):
    def test_bridge_resolves_naval_profile(self) -> None:
        profile = resolve_tasking_profile("naval")
        self.assertEqual(profile.__name__.split(".")[-1], "naval_adapter")

    def test_normalize_task_order_spec_uses_naval_defaults(self) -> None:
        normalized = normalize_task_order_spec(
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
        normalized = normalize_task_order_spec(
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


if __name__ == "__main__":
    unittest.main()
