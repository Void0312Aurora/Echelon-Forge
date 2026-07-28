from __future__ import annotations

import unittest

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py # noqa: E402


class SimulationKernelCommandApiGuardTests(unittest.TestCase):
  def test_invalid_entity_setters_are_noops_and_getters_return_defaults(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(31)
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))

    invalid_id = 999_999_999

    kernel.set_command(invalid_id, 90.0, 180.0, 1200.0)
    kernel.set_stick_command(invalid_id, 0.2, -0.1, 0.7, True)
    kernel.set_action(invalid_id, 0.1, 0.2, -0.3, 0.0, False, False, False)
    kernel.set_command_link(invalid_id, 0.5, 0.25)
    kernel.set_action_space_config(invalid_id, 10.0, 5.0, 3.0, 100.0, 250.0, 0.0, 5000.0)
    kernel.set_command_lag(invalid_id, 0.5, 1.0, 1.5)
    kernel.send_message_command(invalid_id, 42, int(ef_py.CommMsgType.AssignTask), 99)

    pilot = ef_py.PilotAction()
    pilot.stick_roll = 0.4
    pilot.active = False
    kernel.set_pilot_action(invalid_id, pilot)

    mission = ef_py.MissionCommand()
    mission.command_code = 4
    kernel.set_mission_command(invalid_id, mission)

    order = ef_py.TaskOrder()
    order.task_id = 77
    kernel.set_task_order(invalid_id, order)

    intent = ef_py.LeaderIntent()
    intent.phase_id = ef_py.LeaderPhase.TransitToStation
    kernel.set_leader_intent(invalid_id, intent)

    report = ef_py.PilotReport()
    report.report_type = ef_py.CommMsgType.STATUS_POS
    kernel.set_pilot_report(invalid_id, report)

    self.assertFalse(bool(kernel.get_mission_command(invalid_id).active))
    self.assertFalse(bool(kernel.get_task_order(invalid_id).active))
    self.assertFalse(bool(kernel.get_leader_intent(invalid_id).active))
    self.assertFalse(bool(kernel.get_pilot_report(invalid_id).active))

  def test_roundtrip_tasking_and_mission_setters_force_active(self) -> None:
    kernel = ef_py.SimulationKernel()
    kernel.reset(37)
    self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))

    entity_id = kernel.spawn_unit(
      ef_py.Side.Blue,
      "Aircraft",
      0.0,
      0.0,
      1200.0,
      heading=0.0,
      pitch=0.0,
      roll=0.0,
      vx=100.0,
      vy=0.0,
      vz=0.0,
    )
    kernel.set_command_link(int(entity_id), 0.0, 0.0)

    mission = ef_py.MissionCommand()
    mission.command_code = 3
    mission.route_ref_id = 17
    mission.active = False
    kernel.set_mission_command(int(entity_id), mission)
    self.assertTrue(bool(kernel.get_mission_command(int(entity_id)).active))

    order = ef_py.TaskOrder()
    order.task_id = 501
    order.active = False
    kernel.set_task_order(int(entity_id), order)
    self.assertTrue(bool(kernel.get_task_order(int(entity_id)).active))

    intent = ef_py.LeaderIntent()
    intent.phase_id = ef_py.LeaderPhase.OnStation
    intent.active = False
    kernel.set_leader_intent(int(entity_id), intent)
    self.assertTrue(bool(kernel.get_leader_intent(int(entity_id)).active))

    report = ef_py.PilotReport()
    report.report_type = ef_py.CommMsgType.STATUS_POS
    report.active = False
    kernel.set_pilot_report(int(entity_id), report)
    self.assertTrue(bool(kernel.get_pilot_report(int(entity_id)).active))


if __name__ == "__main__":
  unittest.main()
