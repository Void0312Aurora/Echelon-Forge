from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import ef_py  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
