from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest import mock

from python.rl.leader_tasking import ScriptedC2TaskManager


_FAKE_EF = SimpleNamespace(
    TaskType=SimpleNamespace(Idle=0, Scramble=1, CAP=2, RTB=3, RecoverLand=4),
    StationType=SimpleNamespace(Orbit=10, Racetrack=11),
)


def _make_base_task_order():
    return SimpleNamespace(
        active=True,
        task_id=1,
        priority=1,
        issuer_id=900,
        assignee_id=17,
        task_type=0,
        target_altitude_m=1900.0,
        target_speed_mps=210.0,
        altitude_block_min_m=1400.0,
        altitude_block_max_m=2400.0,
        speed_min_mps=170.0,
        speed_max_mps=250.0,
        anchor_x_m=25000.0,
        anchor_y_m=16000.0,
        anchor_z_m=1900.0,
        station_type=_FAKE_EF.StationType.Racetrack,
        station_radius_m=15000.0,
        station_leg_length_m=28000.0,
        station_heading_deg=40.0,
        on_station_time_s=240.0,
        issue_time_s=0.0,
    )


def _make_loader(*, scenario_task_order: dict, mission_cmd: dict, waypoints: list[dict] | None = None, waypoint_idx: int = 0):
    return SimpleNamespace(
        agent_id=17,
        scenario_data={"task_order": dict(scenario_task_order)},
        mission_cmd=dict(mission_cmd),
        post_waypoint_transition=None,
        waypoints=list(waypoints or []),
        waypoint_idx=int(waypoint_idx),
        task_order=_make_base_task_order(),
    )


class TaskOrderRandomizationTests(unittest.TestCase):
    def test_task_only_scramble_preserves_randomized_task_center(self):
        loader = _make_loader(
            scenario_task_order={
                "task_id": 7713,
                "task_type": "CAP",
                "anchor_x_m": 26521.3,
                "anchor_y_m": -22253.3,
                "anchor_z_m": 2430.2,
                "station_type": "Racetrack",
                "station_radius_m": 12879.1,
                "station_leg_length_m": 26997.9,
                "station_heading_deg": 243.8,
                "target_altitude_m": 2430.2,
                "altitude_block_min_m": 1945.3,
                "altitude_block_max_m": 2915.1,
                "target_speed_mps": 211.9,
                "speed_min_mps": 180.5,
                "speed_max_mps": 243.3,
                "on_station_time_s": 324.7,
            },
            mission_cmd={
                "command_code": 2,
                "target_heading": 58.0,
                "target_altitude": 1900.0,
                "target_speed": 210.0,
            },
        )

        manager = ScriptedC2TaskManager()
        with mock.patch("python.rl.leader_tasking.ef_py", _FAKE_EF):
            manager._retask_order(loader, task_name=manager.TASK_SCRAMBLE, sim_time_s=0.0)

        task = loader.task_order
        self.assertAlmostEqual(float(task.target_altitude_m), 2430.2, places=3)
        self.assertAlmostEqual(float(task.target_speed_mps), 211.9, places=3)
        self.assertAlmostEqual(float(task.altitude_block_min_m), 1945.3, places=3)
        self.assertAlmostEqual(float(task.altitude_block_max_m), 2915.1, places=3)
        self.assertAlmostEqual(float(task.speed_min_mps), 180.5, places=3)
        self.assertAlmostEqual(float(task.speed_max_mps), 243.3, places=3)

    def test_route_driven_cap_recenters_block_on_active_waypoint(self):
        loader = _make_loader(
            scenario_task_order={
                "task_id": 7101,
                "task_type": "CAP",
                "anchor_x_m": 28000.0,
                "anchor_y_m": 14000.0,
                "anchor_z_m": 2100.0,
                "station_type": "Racetrack",
                "station_radius_m": 14500.0,
                "station_leg_length_m": 32000.0,
                "station_heading_deg": 35.0,
                "target_altitude_m": 2100.0,
                "altitude_block_min_m": 1650.0,
                "altitude_block_max_m": 2650.0,
                "target_speed_mps": 228.0,
                "speed_min_mps": 190.0,
                "speed_max_mps": 245.0,
                "on_station_time_s": 900.0,
            },
            mission_cmd={
                "command_code": 3,
                "target_heading": 72.0,
                "target_altitude": 2150.0,
                "target_speed": 235.0,
            },
            waypoints=[
                {"x": 20000.0, "y": 4000.0, "altitude_m": 1650.0, "speed_mps": 188.0, "radius_m": 1500.0, "waypoint_mode": "flyby"},
                {"x": 33000.0, "y": 15000.0, "altitude_m": 2550.0, "speed_mps": 225.0, "radius_m": 1750.0, "waypoint_mode": "flyby"},
            ],
            waypoint_idx=0,
        )

        manager = ScriptedC2TaskManager()
        with mock.patch("python.rl.leader_tasking.ef_py", _FAKE_EF):
            manager._retask_order(loader, task_name=manager.TASK_CAP, sim_time_s=0.0)

        task = loader.task_order
        self.assertAlmostEqual(float(task.target_altitude_m), 1650.0, places=3)
        self.assertAlmostEqual(float(task.altitude_block_min_m), 1200.0, places=3)
        self.assertAlmostEqual(float(task.altitude_block_max_m), 2200.0, places=3)
        self.assertAlmostEqual(float(task.target_speed_mps), 188.0, places=3)
        self.assertAlmostEqual(float(task.speed_min_mps), 150.0, places=3)
        self.assertAlmostEqual(float(task.speed_max_mps), 205.0, places=3)


if __name__ == "__main__":
    unittest.main()
