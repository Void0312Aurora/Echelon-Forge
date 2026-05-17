from __future__ import annotations

import math
import unittest

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402


def _make_kernel(seed: int) -> ef_py.SimulationKernel:
    kernel = ef_py.SimulationKernel()
    kernel.reset(seed)
    kernel.set_time_step(0.5)
    assert kernel.load_database(resolve_repo_path("examples", "config", "database"))
    return kernel


def _spawn_ship() -> tuple[ef_py.SimulationKernel, int]:
    kernel = _make_kernel(6201)
    entity_id = kernel.spawn_unit(
        ef_py.Side.Blue,
        "DDG-51_Flight_I_USS_Arleigh_Burke",
        0.0,
        0.0,
        0.0,
        heading=90.0,
        pitch=0.0,
        roll=0.0,
        vx=10.29,
        vy=0.0,
        vz=0.0,
    )
    kernel.set_command_link(int(entity_id), 0.0, 0.0)
    return kernel, int(entity_id)


def _spawn_submarine() -> tuple[ef_py.SimulationKernel, int]:
    kernel = _make_kernel(6202)
    entity_id = kernel.spawn_unit(
        ef_py.Side.Blue,
        "Kilo_Class_MVP",
        0.0,
        12000.0,
        -80.0,
        heading=90.0,
        pitch=0.0,
        roll=0.0,
        vx=3.0,
        vy=0.0,
        vz=0.0,
    )
    kernel.set_command_link(int(entity_id), 0.0, 0.0)
    return kernel, int(entity_id)


class NavalLegacyMovementDebugTests(unittest.TestCase):
    def test_debug_hook_constructs_active_legacy_movement_without_active_mission(self) -> None:
        for label, spawner, heading_deg, speed_mps, altitude_m in (
            ("ship", _spawn_ship, 15.0, 8.0, 123.0),
            ("submarine", _spawn_submarine, 210.0, 6.5, 120.0),
        ):
            with self.subTest(platform=label):
                kernel, entity_id = spawner()

                kernel.debug_set_legacy_movement_command(
                    entity_id,
                    heading_deg,
                    speed_mps,
                    altitude_m,
                    True,
                )

                movement = kernel.debug_get_legacy_movement_command(entity_id)
                mission = kernel.get_mission_command(entity_id)

                self.assertTrue(bool(movement["active"]))
                self.assertAlmostEqual(float(movement["target_heading"]), heading_deg, places=6)
                self.assertAlmostEqual(float(movement["target_speed"]), speed_mps, places=6)
                self.assertAlmostEqual(float(movement["target_altitude"]), altitude_m, places=6)
                self.assertFalse(bool(movement["use_stick_control"]))
                self.assertFalse(bool(mission.active))

    def test_ship_motion_ignores_active_legacy_movement_without_mission(self) -> None:
        kernel, entity_id = _spawn_ship()

        initial_heading_deg = float(kernel.get_unit_heading(entity_id))
        initial_speed_mps = math.hypot(*(float(v) for v in kernel.get_unit_velocity(entity_id)[:2]))

        kernel.debug_set_legacy_movement_command(entity_id, 0.0, 2.0, 500.0, True)

        for _ in range(12):
            kernel.step()

        heading_after_deg = float(kernel.get_unit_heading(entity_id))
        speed_after_mps = math.hypot(*(float(v) for v in kernel.get_unit_velocity(entity_id)[:2]))

        self.assertAlmostEqual(heading_after_deg, initial_heading_deg, delta=1.0)
        self.assertAlmostEqual(speed_after_mps, initial_speed_mps, delta=0.25)

    def test_submarine_motion_ignores_active_legacy_movement_without_mission(self) -> None:
        kernel, entity_id = _spawn_submarine()

        initial_heading_deg = float(kernel.get_unit_heading(entity_id))
        initial_speed_mps = math.hypot(*(float(v) for v in kernel.get_unit_velocity(entity_id)[:2]))
        initial_depth_m = -float(kernel.get_unit_position(entity_id)[2])

        kernel.debug_set_legacy_movement_command(entity_id, 210.0, 6.5, 120.0, True)

        for _ in range(10):
            kernel.step()

        heading_after_deg = float(kernel.get_unit_heading(entity_id))
        speed_after_mps = math.hypot(*(float(v) for v in kernel.get_unit_velocity(entity_id)[:2]))
        depth_after_m = -float(kernel.get_unit_position(entity_id)[2])

        self.assertAlmostEqual(heading_after_deg, initial_heading_deg, delta=1.0)
        self.assertAlmostEqual(speed_after_mps, initial_speed_mps, delta=0.25)
        self.assertAlmostEqual(depth_after_m, initial_depth_m, delta=1.0)


if __name__ == "__main__":
    unittest.main()
