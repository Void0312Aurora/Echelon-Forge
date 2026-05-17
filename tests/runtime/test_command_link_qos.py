from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402


def _spawn_aircraft_with_link(*, latency_s: float, drop_prob: float = 0.0) -> tuple[ef_py.SimulationKernel, int]:
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
    kernel.set_command_link(int(entity_id), latency_s, drop_prob)
    return kernel, int(entity_id)


def _mission(
    *,
    heading_deg: float,
    command_code: int,
    roe_state: int = 0,
    engagement_authority_holder_id: int = 0,
    engagement_authority_grantor_id: int = 0,
    assigned_target_id: int = 0,
    authorization_to_fire: bool = False,
) -> ef_py.MissionCommand:
    cmd = ef_py.MissionCommand()
    cmd.active = True
    cmd.command_code = command_code
    cmd.cmd_heading_deg = heading_deg
    cmd.cmd_altitude_m = 1500.0 + command_code
    cmd.cmd_speed_mps = 180.0 + command_code
    cmd.roe_state = roe_state
    cmd.engagement_authority_holder_id = engagement_authority_holder_id
    cmd.engagement_authority_grantor_id = engagement_authority_grantor_id
    cmd.assigned_target_id = assigned_target_id
    cmd.authorization_to_fire = authorization_to_fire
    return cmd


def _assert_mission_matches(actual: ef_py.MissionCommand, expected: ef_py.MissionCommand) -> None:
    testcase = unittest.TestCase()
    testcase.assertTrue(bool(actual.active))
    testcase.assertEqual(int(actual.command_code), int(expected.command_code))
    testcase.assertAlmostEqual(float(actual.cmd_heading_deg), float(expected.cmd_heading_deg), places=6)
    testcase.assertAlmostEqual(float(actual.cmd_altitude_m), float(expected.cmd_altitude_m), places=6)
    testcase.assertAlmostEqual(float(actual.cmd_speed_mps), float(expected.cmd_speed_mps), places=6)
    testcase.assertEqual(int(actual.roe_state), int(expected.roe_state))
    testcase.assertEqual(
        int(actual.engagement_authority_holder_id),
        int(expected.engagement_authority_holder_id),
    )
    testcase.assertEqual(
        int(actual.engagement_authority_grantor_id),
        int(expected.engagement_authority_grantor_id),
    )
    testcase.assertEqual(int(actual.assigned_target_id), int(expected.assigned_target_id))
    testcase.assertEqual(bool(actual.authorization_to_fire), bool(expected.authorization_to_fire))


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
    def test_delayed_mission_command_preserves_roe_and_navigation_fields_until_atomic_delivery(self) -> None:
        kernel = ef_py.SimulationKernel()
        kernel.reset(6201)
        kernel.set_time_step(0.1)
        assert kernel.load_database(resolve_repo_path("examples", "config", "database"))

        entity_id = int(
            kernel.spawn_unit(
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
        )
        kernel.set_command_link(entity_id, 0.0, 0.0)

        baseline = _mission(
            heading_deg=35.0,
            command_code=7,
            roe_state=1,
            engagement_authority_holder_id=1101,
            engagement_authority_grantor_id=1001,
            assigned_target_id=1201,
            authorization_to_fire=False,
        )
        kernel.set_mission_command(entity_id, baseline)
        _assert_mission_matches(kernel.get_mission_command(entity_id), baseline)

        kernel.set_command_link(entity_id, 0.3, 0.0)
        delayed = _mission(
            heading_deg=145.0,
            command_code=9,
            roe_state=3,
            engagement_authority_holder_id=2101,
            engagement_authority_grantor_id=2001,
            assigned_target_id=2201,
            authorization_to_fire=True,
        )
        kernel.set_mission_command(entity_id, delayed)

        before_delivery = kernel.get_mission_command(entity_id)
        _assert_mission_matches(before_delivery, baseline)

        kernel.step()
        after_one_step = kernel.get_mission_command(entity_id)
        _assert_mission_matches(after_one_step, baseline)

        delivered = _step_until_command_code(kernel, entity_id, 9)
        _assert_mission_matches(delivered, delayed)

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

    def test_two_pending_mission_commands_preserve_distinct_roe_payloads_in_fifo_order(self) -> None:
        kernel, entity_id = _spawn_aircraft_with_link(latency_s=0.2)

        first = _mission(
            heading_deg=20.0,
            command_code=31,
            roe_state=1,
            engagement_authority_holder_id=3101,
            engagement_authority_grantor_id=3001,
            assigned_target_id=3201,
            authorization_to_fire=False,
        )
        second = _mission(
            heading_deg=155.0,
            command_code=32,
            roe_state=3,
            engagement_authority_holder_id=4101,
            engagement_authority_grantor_id=4001,
            assigned_target_id=4201,
            authorization_to_fire=True,
        )

        kernel.set_mission_command(entity_id, first)
        kernel.set_mission_command(entity_id, second)

        first_delivered = _step_until_command_code(kernel, entity_id, 31)
        _assert_mission_matches(first_delivered, first)
        self.assertNotEqual(int(first_delivered.roe_state), int(second.roe_state))
        self.assertNotEqual(
            int(first_delivered.engagement_authority_holder_id),
            int(second.engagement_authority_holder_id),
        )
        self.assertNotEqual(int(first_delivered.assigned_target_id), int(second.assigned_target_id))
        self.assertNotEqual(bool(first_delivered.authorization_to_fire), bool(second.authorization_to_fire))

        second_delivered = _step_until_command_code(kernel, entity_id, 32)
        _assert_mission_matches(second_delivered, second)

    def test_dropped_mission_command_does_not_mutate_existing_roe_state(self) -> None:
        kernel = ef_py.SimulationKernel()
        kernel.reset(6201)
        kernel.set_time_step(0.1)
        assert kernel.load_database(resolve_repo_path("examples", "config", "database"))

        entity_id = int(
            kernel.spawn_unit(
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
        )
        kernel.set_command_link(entity_id, 0.0, 0.0)

        baseline = _mission(
            heading_deg=55.0,
            command_code=41,
            roe_state=2,
            engagement_authority_holder_id=5101,
            engagement_authority_grantor_id=5001,
            assigned_target_id=5201,
            authorization_to_fire=False,
        )
        kernel.set_mission_command(entity_id, baseline)
        _assert_mission_matches(kernel.get_mission_command(entity_id), baseline)

        kernel.set_command_link(entity_id, 0.2, 1.0)
        dropped = _mission(
            heading_deg=175.0,
            command_code=42,
            roe_state=3,
            engagement_authority_holder_id=6101,
            engagement_authority_grantor_id=6001,
            assigned_target_id=6201,
            authorization_to_fire=True,
        )
        kernel.set_mission_command(entity_id, dropped)

        before_steps = kernel.get_mission_command(entity_id)
        _assert_mission_matches(before_steps, baseline)

        for _ in range(6):
            kernel.step()

        after_steps = kernel.get_mission_command(entity_id)
        _assert_mission_matches(after_steps, baseline)

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
