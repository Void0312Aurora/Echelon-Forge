from __future__ import annotations

import unittest
from types import SimpleNamespace

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import ef_py  # noqa: E402

from python.rl.profile.ground_profile import build_kernel_mission_command, infer_recovery_approach_type  # noqa: E402
from python.rl.tasking import bridge as tasking_bridge  # noqa: E402
from python.rl.tasking.common_core_profile import (  # noqa: E402
    apply_leader_intent_common_core_defaults,
    apply_pilot_report_common_core_defaults,
    apply_task_order_common_core_defaults,
)


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

        intent = ef_py.LeaderIntent()
        apply_leader_intent_common_core_defaults(intent, order=order, task_name="TASK_SUPPORT", default_tactical_unit_id=99)
        self.assertEqual(intent.service_profile, ef_py.ServiceProfile.Army)
        self.assertEqual(intent.task_family, ef_py.TaskFamily.Defend)
        self.assertEqual(intent.tactical_unit_type, ef_py.TacticalUnitType.TacticalUnit)
        self.assertEqual(intent.coordination_mode, ef_py.CoordinationMode.Support)
        self.assertEqual(int(intent.task_group_id), 6101)
        self.assertEqual(int(intent.tactical_unit_id), 5301)
        self.assertEqual(int(intent.officer_in_tactical_command), 5101)

        report = ef_py.PilotReport()
        apply_pilot_report_common_core_defaults(report, order=order, task_name="TASK_SUPPORT", default_tactical_unit_id=99)
        self.assertEqual(report.service_profile, ef_py.ServiceProfile.Army)
        self.assertEqual(report.task_family, ef_py.TaskFamily.Defend)
        self.assertEqual(report.tactical_unit_type, ef_py.TacticalUnitType.TacticalUnit)
        self.assertEqual(report.coordination_mode, ef_py.CoordinationMode.Support)
        self.assertEqual(int(report.task_group_id), 6101)
        self.assertEqual(int(report.tactical_unit_id), 5301)
        self.assertEqual(int(report.officer_in_tactical_command), 5101)

    def test_ground_mission_command_builder_is_minimal_compatibility_shell(self) -> None:
        loader = SimpleNamespace(
            mission_cmd={
                "command_code": 7,
                "target_heading": 90.0,
                "target_altitude": 12.0,
                "target_speed": 4.5,
                "formation_id": 3,
                "form_offset_x": 1.0,
                "form_offset_y": 2.0,
                "form_offset_z": 0.0,
                "assigned_target_id": 77,
                "authorization_to_fire": True,
                "takeoff_procedure_code": 99,
                "recovery_runway_id": 88,
            },
            leader_intent=None,
        )

        cmd = build_kernel_mission_command(loader)

        self.assertEqual(build_kernel_mission_command.__module__, "python.rl.profile.ground_profile")
        self.assertTrue(bool(cmd.active))
        self.assertEqual(int(cmd.command_code), 7)
        self.assertAlmostEqual(float(cmd.cmd_heading_deg), 90.0)
        self.assertAlmostEqual(float(cmd.cmd_altitude_m), 12.0)
        self.assertAlmostEqual(float(cmd.cmd_speed_mps), 4.5)
        self.assertEqual(int(cmd.formation_id), 3)
        self.assertAlmostEqual(float(cmd.form_offset_x), 1.0)
        self.assertAlmostEqual(float(cmd.form_offset_y), 2.0)
        self.assertEqual(int(cmd.assigned_target_id), 77)
        self.assertTrue(bool(cmd.authorization_to_fire))

    def test_ground_recovery_approach_inference_returns_binding_enum(self) -> None:
        none_value = getattr(ef_py.RecoveryApproachType, "None")
        self.assertEqual(infer_recovery_approach_type(SimpleNamespace(), task=None), none_value)

        order = ef_py.TaskOrder()
        order.recovery_approach_type = ef_py.RecoveryApproachType.Visual
        self.assertEqual(infer_recovery_approach_type(SimpleNamespace(), task=order), ef_py.RecoveryApproachType.Visual)


if __name__ == "__main__":
    unittest.main()
