from __future__ import annotations

import unittest

from python.rl.coarse_route_propagator import (
    CoarseRouteConfig,
    RouteSnapshot,
    RouteWaypoint,
    compare_route_states,
    project_route_window,
)


class CoarseRoutePropagatorTests(unittest.TestCase):
    def test_zero_horizon_keeps_state(self):
        snap = RouteSnapshot(
            sim_time_s=10.0,
            x_m=100.0,
            y_m=200.0,
            altitude_m=1500.0,
            heading_deg=90.0,
            ground_track_deg=90.0,
            ground_speed_mps=180.0,
            vertical_speed_mps=0.0,
            wind_speed_mps=0.0,
            wind_from_deg=0.0,
            target_heading_deg=90.0,
            target_altitude_m=1500.0,
            target_speed_mps=180.0,
            lnav_bank_limit_deg=25.0,
            command_code=3,
            waypoint_idx=0,
        )
        out = project_route_window(snap, waypoints=[], horizon_s=0.0)
        self.assertAlmostEqual(out.state.x_m, snap.x_m)
        self.assertAlmostEqual(out.state.y_m, snap.y_m)
        self.assertEqual(out.state.waypoint_idx, snap.waypoint_idx)

    def test_level_route_projection_moves_toward_waypoint(self):
        snap = RouteSnapshot(
            sim_time_s=0.0,
            x_m=0.0,
            y_m=0.0,
            altitude_m=1000.0,
            heading_deg=90.0,
            ground_track_deg=90.0,
            ground_speed_mps=200.0,
            vertical_speed_mps=0.0,
            wind_speed_mps=0.0,
            wind_from_deg=0.0,
            target_heading_deg=90.0,
            target_altitude_m=1000.0,
            target_speed_mps=200.0,
            lnav_bank_limit_deg=30.0,
            command_code=3,
            waypoint_idx=0,
        )
        out = project_route_window(
            snap,
            waypoints=[RouteWaypoint(x_m=0.0, y_m=5000.0, altitude_m=1000.0, speed_mps=200.0, radius_m=200.0)],
            horizon_s=5.0,
        )
        self.assertGreater(out.state.y_m, snap.y_m)
        self.assertGreater(out.state.ground_track_deg, 10.0)
        self.assertLess(abs(out.state.x_m), 1500.0)
        self.assertAlmostEqual(out.state.altitude_m, 1000.0, delta=80.0)

    def test_waypoint_advances_when_capture_radius_reached(self):
        snap = RouteSnapshot(
            sim_time_s=0.0,
            x_m=0.0,
            y_m=0.0,
            altitude_m=1000.0,
            heading_deg=0.0,
            ground_track_deg=0.0,
            ground_speed_mps=200.0,
            vertical_speed_mps=0.0,
            wind_speed_mps=0.0,
            wind_from_deg=0.0,
            target_heading_deg=0.0,
            target_altitude_m=1000.0,
            target_speed_mps=200.0,
            lnav_bank_limit_deg=30.0,
            command_code=3,
            waypoint_idx=0,
        )
        out = project_route_window(
            snap,
            waypoints=[
                RouteWaypoint(x_m=0.0, y_m=150.0, altitude_m=1000.0, speed_mps=200.0, radius_m=250.0),
                RouteWaypoint(x_m=0.0, y_m=4000.0, altitude_m=1200.0, speed_mps=190.0, radius_m=250.0),
            ],
            horizon_s=1.0,
            config=CoarseRouteConfig(min_waypoint_capture_radius_m=180.0),
        )
        self.assertEqual(out.state.waypoint_idx, 1)
        self.assertEqual(out.waypoint_advances, 1)

    def test_compare_route_states_reports_differences(self):
        a = RouteSnapshot(
            sim_time_s=0.0,
            x_m=0.0,
            y_m=0.0,
            altitude_m=1000.0,
            heading_deg=0.0,
            ground_track_deg=0.0,
            ground_speed_mps=200.0,
            vertical_speed_mps=0.0,
            wind_speed_mps=0.0,
            wind_from_deg=0.0,
            target_heading_deg=0.0,
            target_altitude_m=1000.0,
            target_speed_mps=200.0,
            lnav_bank_limit_deg=25.0,
            command_code=3,
            waypoint_idx=1,
        )
        b = RouteSnapshot(
            sim_time_s=0.0,
            x_m=300.0,
            y_m=400.0,
            altitude_m=1025.0,
            heading_deg=10.0,
            ground_track_deg=12.0,
            ground_speed_mps=195.0,
            vertical_speed_mps=0.0,
            wind_speed_mps=0.0,
            wind_from_deg=0.0,
            target_heading_deg=0.0,
            target_altitude_m=1000.0,
            target_speed_mps=200.0,
            lnav_bank_limit_deg=25.0,
            command_code=3,
            waypoint_idx=2,
        )
        err = compare_route_states(a, b)
        self.assertAlmostEqual(err.position_error_m, 500.0, delta=1.0e-6)
        self.assertEqual(err.waypoint_idx_error, -1)
        self.assertTrue(err.waypoint_mismatch)


if __name__ == "__main__":
    unittest.main()
