from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from python.rl.tasking.bridge import (  # noqa: E402
    apply_loader_owned_world_layout_to_kernel,
    loader_owned_raw_sim_compat,
    loader_owned_scripted_opponent_kernel_compat,
    resolve_loader_time_step,
    sync_loader_command_chain,
    sync_loader_mission_command,
)
from python.rl.tasking.leader_tasking import build_kernel_mission_command  # noqa: E402


class LeaderTaskingRuntimeTests(unittest.TestCase):
    def test_resolve_loader_time_step_reads_loader_owned_raw_sim_compatibility_seam(self) -> None:
        sim = SimpleNamespace(get_time_step=Mock(return_value=0.2))
        loader = SimpleNamespace(
            sim=sim,
            scenario_data={},
            _compiled_runtime_metadata=None,
            _compiled_scenario=None,
        )

        self.assertAlmostEqual(resolve_loader_time_step(loader, default=0.05), 0.2, places=6)
        sim.get_time_step.assert_called_once_with()

    def test_sync_loader_mission_command_uses_loader_owned_compatibility_seam(self) -> None:
        sim = SimpleNamespace(set_mission_command=Mock())
        loader = SimpleNamespace(agent_id=9, sim=sim)
        cmd = object()

        sync_loader_mission_command(loader, cmd)

        sim.set_mission_command.assert_called_once_with(9, cmd)

    def test_loader_owned_scripted_opponent_kernel_compat_proxies_required_operations(self) -> None:
        sim = SimpleNamespace(
            is_unit_active=Mock(side_effect=[True, False]),
            get_unit_position=Mock(return_value=(1.0, 2.0, 3.0)),
            get_agent_observation=Mock(return_value=SimpleNamespace(label="obs")),
            set_command=Mock(),
            fire_missile=Mock(return_value=42),
        )
        loader = SimpleNamespace(sim=sim)

        compat = loader_owned_scripted_opponent_kernel_compat(loader)

        self.assertTrue(compat.is_unit_active(7))
        self.assertFalse(compat.is_unit_active(8))
        self.assertEqual(compat.get_unit_position(7), (1.0, 2.0, 3.0))
        self.assertEqual(getattr(compat.get_agent_observation(7), "label", ""), "obs")
        compat.set_command(7, 90.0, 250.0, 1200.0)
        self.assertEqual(compat.fire_missile(7, 11), 42)
        sim.set_command.assert_called_once_with(7, 90.0, 250.0, 1200.0)
        sim.fire_missile.assert_called_once_with(7, 11)

    def test_rule_based_leader_phase_manager_sync_to_kernel_prefers_loader_owned_bridge(self) -> None:
        manager = build_kernel_mission_command.__globals__["RuleBasedLeaderPhaseManager"]()
        sync_hook = Mock()
        loader = SimpleNamespace(
            agent_id=7,
            task_order=SimpleNamespace(active=True),
            leader_intent=SimpleNamespace(active=True),
            pilot_report=SimpleNamespace(active=True),
            _sync_kernel_command_chain=sync_hook,
        )

        manager.sync_to_kernel(loader)

        sync_hook.assert_called_once_with()

    def test_loader_owned_raw_sim_compatibility_facade_supports_command_chain_writes(self) -> None:
        sim = SimpleNamespace(
            set_task_order=Mock(),
            set_leader_intent=Mock(),
            set_pilot_report=Mock(),
            set_mission_command=Mock(),
        )
        loader = SimpleNamespace(sim=sim)
        compat = loader_owned_raw_sim_compat(loader)

        order = object()
        intent = object()
        report = object()
        cmd = object()
        compat.sync_task_order(5, order)
        compat.sync_leader_intent(5, intent)
        compat.sync_pilot_report(5, report)
        compat.sync_mission_command(5, cmd)

        sim.set_task_order.assert_called_once_with(5, order)
        sim.set_leader_intent.assert_called_once_with(5, intent)
        sim.set_pilot_report.assert_called_once_with(5, report)
        sim.set_mission_command.assert_called_once_with(5, cmd)

    def test_apply_loader_owned_world_layout_to_kernel_uses_named_loader_owned_seam(self) -> None:
        sim = object()
        loader = SimpleNamespace(sim=sim)
        layout = object()
        apply_mock = Mock(return_value=SimpleNamespace(agent_id=41))

        original_import_module = apply_loader_owned_world_layout_to_kernel.__globals__["import_module"]
        apply_loader_owned_world_layout_to_kernel.__globals__["import_module"] = Mock(
            return_value=SimpleNamespace(apply_world_layout_to_kernel=apply_mock)
        )
        try:
            applied = apply_loader_owned_world_layout_to_kernel(loader, layout)
        finally:
            apply_loader_owned_world_layout_to_kernel.__globals__["import_module"] = original_import_module

        self.assertEqual(int(applied.agent_id), 41)
        apply_mock.assert_called_once_with(sim, layout)

    def test_apply_loader_owned_world_layout_to_kernel_requires_loader_sim(self) -> None:
        loader = SimpleNamespace(sim=None)

        with self.assertRaisesRegex(RuntimeError, "loader-owned world-layout kernel-apply seam requires loader.sim"):
            apply_loader_owned_world_layout_to_kernel(loader, object())

    def test_sync_loader_command_chain_reentrant_loader_owned_path_falls_back_to_compatibility_seam(self) -> None:
        sim = SimpleNamespace(
            set_task_order=Mock(),
            set_leader_intent=Mock(),
            set_pilot_report=Mock(),
        )
        loader = SimpleNamespace(
            agent_id=12,
            sim=sim,
            task_order=object(),
            leader_intent=object(),
            pilot_report=object(),
            _loader_owned_command_chain_sync_in_progress=False,
        )

        def _reenter() -> None:
            sync_loader_command_chain(loader)

        loader._sync_kernel_command_chain = _reenter

        sync_loader_command_chain(loader)

        sim.set_task_order.assert_called_once_with(12, loader.task_order)
        sim.set_leader_intent.assert_called_once_with(12, loader.leader_intent)
        sim.set_pilot_report.assert_called_once_with(12, loader.pilot_report)

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

    def test_build_kernel_mission_command_falls_back_to_mission_cmd_fields(self) -> None:
        loader = SimpleNamespace(
            mission_cmd={
                "command_code": 2,
                "target_heading": 123.0,
                "target_altitude": 3100.0,
                "target_speed": 222.0,
                "takeoff_procedure_code": 2,
                "takeoff_clearance_code": 3,
                "takeoff_interval_s": 4.5,
                "runway_slot_code": 1,
                "formation_id": 31,
                "form_offset_x": 220.0,
                "form_offset_y": -75.0,
                "form_offset_z": 18.0,
                "assigned_target_id": 4401,
                "authorization_to_fire": True,
            },
            leader_intent=None,
            task_order=None,
            waypoints=[],
        )

        cmd = build_kernel_mission_command(loader)
        self.assertEqual(int(cmd.command_code), 2)
        self.assertAlmostEqual(float(cmd.cmd_heading_deg), 123.0, places=6)
        self.assertAlmostEqual(float(cmd.cmd_altitude_m), 3100.0, places=6)
        self.assertAlmostEqual(float(cmd.cmd_speed_mps), 222.0, places=6)
        self.assertEqual(int(cmd.takeoff_procedure_id), 2)
        self.assertEqual(int(cmd.takeoff_clearance_id), 3)
        self.assertAlmostEqual(float(cmd.takeoff_interval_s), 4.5, places=6)
        self.assertEqual(int(cmd.runway_slot_id), 1)
        self.assertEqual(int(cmd.formation_id), 31)
        self.assertAlmostEqual(float(cmd.form_offset_x), 220.0, places=6)
        self.assertAlmostEqual(float(cmd.form_offset_y), -75.0, places=6)
        self.assertAlmostEqual(float(cmd.form_offset_z), 18.0, places=6)
        self.assertEqual(int(cmd.assigned_target_id), 4401)
        self.assertTrue(bool(cmd.authorization_to_fire))

    def test_build_kernel_mission_command_writes_route_ref_id_only_for_active_route_leg(self) -> None:
        loader = SimpleNamespace(
            mission_cmd={
                "command_code": 3,
                "target_heading": 123.0,
                "target_altitude": 3100.0,
                "target_speed": 222.0,
            },
            leader_intent=SimpleNamespace(
                command_code=3,
                cmd_heading_deg=123.0,
                cmd_altitude_m=3100.0,
                cmd_speed_mps=222.0,
            ),
            task_order=None,
            waypoints=[
                {"x": 1000.0, "y": 2000.0, "z": 3100.0, "speed_mps": 222.0, "radius_m": 900.0},
            ],
            waypoint_idx=0,
        )

        cmd = build_kernel_mission_command(loader)

        self.assertEqual(int(cmd.command_code), 3)
        self.assertGreater(int(cmd.route_ref_id), 0)

        loader.leader_intent.command_code = 2
        cmd_vector = build_kernel_mission_command(loader)
        self.assertEqual(int(cmd_vector.command_code), 2)
        self.assertEqual(int(cmd_vector.route_ref_id), 0)

        loader.leader_intent.command_code = 3
        loader.waypoint_idx = 9
        cmd_no_active_leg = build_kernel_mission_command(loader)
        self.assertEqual(int(cmd_no_active_leg.command_code), 3)
        self.assertEqual(int(cmd_no_active_leg.route_ref_id), 0)

    def test_build_kernel_mission_command_writes_recovery_fields_only_for_landing_command(self) -> None:
        loader = SimpleNamespace(
            mission_cmd={
                "command_code": 4,
                "target_heading": 178.0,
                "target_altitude": 900.0,
                "target_speed": 155.0,
            },
            leader_intent=SimpleNamespace(
                command_code=4,
                cmd_heading_deg=178.0,
                cmd_altitude_m=900.0,
                cmd_speed_mps=155.0,
                recovery_base_id=501,
                recovery_runway_id=17,
                recovery_approach_type=2,
            ),
            task_order=None,
            waypoints=[],
        )

        landing_cmd = build_kernel_mission_command(loader)
        self.assertEqual(int(landing_cmd.command_code), 4)
        self.assertEqual(int(landing_cmd.recovery_base_id), 501)
        self.assertEqual(int(landing_cmd.recovery_runway_id), 17)
        self.assertEqual(int(landing_cmd.recovery_approach_type), 2)

        loader.leader_intent.command_code = 2
        vector_cmd = build_kernel_mission_command(loader)
        self.assertEqual(int(vector_cmd.command_code), 2)
        self.assertEqual(int(vector_cmd.recovery_base_id), 0)
        self.assertEqual(int(vector_cmd.recovery_runway_id), 0)
        self.assertEqual(int(vector_cmd.recovery_approach_type), 0)


if __name__ == "__main__":
    unittest.main()
