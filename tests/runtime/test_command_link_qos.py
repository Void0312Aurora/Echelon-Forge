from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402


def _spawn_aircraft_with_link(*, latency_s: float) -> tuple[ef_py.SimulationKernel, int]:
    kernel = ef_py.SimulationKernel()
    kernel.reset(6201)
    kernel.set_time_step(0.1)
    assert kernel.load_database(resolve_repo_path("examples", "config", "database"))

    entity_id = kernel.spawn_unit(
        ef_py.Side.Blue,
        "Aircraft",
        0.0,
        0.0,
        1200.0,
        heading=90.0,
        pitch=0.0,
        roll=0.0,
        vx=180.0,
        vy=0.0,
        vz=0.0,
    )
    kernel.set_command_link(int(entity_id), latency_s, 0.0)
    return kernel, int(entity_id)


def _mission(*, heading_deg: float, command_code: int) -> ef_py.MissionCommand:
    cmd = ef_py.MissionCommand()
    cmd.active = True
    cmd.command_code = command_code
    cmd.cmd_heading_deg = heading_deg
    cmd.cmd_altitude_m = 1500.0 + command_code
    cmd.cmd_speed_mps = 180.0 + command_code
    return cmd


def _step_until_first_active_mission(
    kernel: ef_py.SimulationKernel,
    entity_id: int,
    *,
    max_steps: int = 20,
) -> ef_py.MissionCommand:
    for _ in range(max_steps):
        kernel.step()
        cmd = kernel.get_mission_command(entity_id)
        if bool(cmd.active):
            return cmd
    raise AssertionError(f"expected entity {entity_id} to receive an active mission command")


def _step_until_command_code(
    kernel: ef_py.SimulationKernel,
    entity_id: int,
    command_code: int,
    *,
    max_steps: int = 20,
) -> ef_py.MissionCommand:
    for _ in range(max_steps):
        kernel.step()
        cmd = kernel.get_mission_command(entity_id)
        if bool(cmd.active) and int(cmd.command_code) == command_code:
            return cmd
    raise AssertionError(
        f"expected entity {entity_id} to receive mission command {command_code}"
    )


class MissionCommandLinkQosTests(unittest.TestCase):
    def test_two_pending_mission_commands_deliver_in_submission_order(self) -> None:
        kernel, entity_id = _spawn_aircraft_with_link(latency_s=0.2)

        first = _mission(heading_deg=15.0, command_code=11)
        second = _mission(heading_deg=75.0, command_code=22)

        kernel.set_mission_command(entity_id, first)
        kernel.set_mission_command(entity_id, second)

        before_delivery = kernel.get_mission_command(entity_id)
        self.assertFalse(bool(before_delivery.active))

        first_delivered = _step_until_first_active_mission(kernel, entity_id)
        self.assertTrue(bool(first_delivered.active))
        self.assertEqual(int(first_delivered.command_code), 11)
        self.assertAlmostEqual(float(first_delivered.cmd_heading_deg), 15.0, places=6)
        self.assertAlmostEqual(float(first_delivered.cmd_speed_mps), 191.0, places=6)

        second_delivered = _step_until_command_code(kernel, entity_id, 22)
        self.assertEqual(int(second_delivered.command_code), 22)
        self.assertAlmostEqual(float(second_delivered.cmd_heading_deg), 75.0, places=6)
        self.assertAlmostEqual(float(second_delivered.cmd_speed_mps), 202.0, places=6)

    def test_second_submission_no_longer_silently_overwrites_first_pending_mission(self) -> None:
        kernel, entity_id = _spawn_aircraft_with_link(latency_s=0.3)

        first = _mission(heading_deg=20.0, command_code=101)
        second = _mission(heading_deg=140.0, command_code=202)

        kernel.set_mission_command(entity_id, first)
        kernel.set_mission_command(entity_id, second)

        delivered = _step_until_first_active_mission(kernel, entity_id)
        self.assertEqual(int(delivered.command_code), 101)
        self.assertAlmostEqual(float(delivered.cmd_heading_deg), 20.0, places=6)
        self.assertNotEqual(int(delivered.command_code), 202)

        delivered_next = _step_until_command_code(kernel, entity_id, 202)
        self.assertEqual(int(delivered_next.command_code), 202)
        self.assertAlmostEqual(float(delivered_next.cmd_heading_deg), 140.0, places=6)

    def test_pending_movement_refresh_uses_newer_deliver_time(self) -> None:
        kernel, entity_id = _spawn_aircraft_with_link(latency_s=0.3)

        kernel.set_command(entity_id, 15.0, 210.0, 1800.0)
        first_pending = kernel.debug_get_pending_movement_command(entity_id)
        self.assertTrue(bool(first_pending["active"]))
        self.assertAlmostEqual(float(first_pending["deliver_time"]), 0.3, places=6)
        self.assertAlmostEqual(float(first_pending["target_heading"]), 15.0, places=6)

        kernel.step()
        kernel.set_command(entity_id, 135.0, 190.0, 1600.0)

        refreshed_pending = kernel.debug_get_pending_movement_command(entity_id)
        self.assertTrue(bool(refreshed_pending["active"]))
        self.assertAlmostEqual(float(refreshed_pending["deliver_time"]), 0.4, places=6)
        self.assertAlmostEqual(float(refreshed_pending["target_heading"]), 135.0, places=6)
        self.assertAlmostEqual(float(refreshed_pending["target_speed"]), 190.0, places=6)
        self.assertAlmostEqual(float(refreshed_pending["target_altitude"]), 1600.0, places=6)

    def test_pending_action_refresh_uses_newer_deliver_time(self) -> None:
        kernel, entity_id = _spawn_aircraft_with_link(latency_s=0.25)

        kernel.set_action(entity_id, 0.2, -0.4, 0.1, 0.0, False, False, False)
        first_pending = kernel.debug_get_pending_action_command(entity_id)
        self.assertTrue(bool(first_pending["active"]))
        self.assertAlmostEqual(float(first_pending["deliver_time"]), 0.25, places=6)
        self.assertAlmostEqual(float(first_pending["turn_rate_cmd"]), 0.2, places=6)

        kernel.step()
        kernel.set_action(entity_id, -0.7, 0.8, -0.6, 0.3, True, False, True)

        refreshed_pending = kernel.debug_get_pending_action_command(entity_id)
        self.assertTrue(bool(refreshed_pending["active"]))
        self.assertAlmostEqual(float(refreshed_pending["deliver_time"]), 0.35, places=6)
        self.assertAlmostEqual(float(refreshed_pending["turn_rate_cmd"]), -0.7, places=6)
        self.assertAlmostEqual(float(refreshed_pending["accel_cmd"]), 0.8, places=6)
        self.assertAlmostEqual(float(refreshed_pending["climb_rate_cmd"]), -0.6, places=6)
        self.assertAlmostEqual(float(refreshed_pending["fire_cmd"]), 0.3, places=6)
        self.assertTrue(bool(refreshed_pending["release_chaff"]))
        self.assertFalse(bool(refreshed_pending["release_flare"]))
        self.assertTrue(bool(refreshed_pending["jettison_tanks"]))


if __name__ == "__main__":
    unittest.main()
