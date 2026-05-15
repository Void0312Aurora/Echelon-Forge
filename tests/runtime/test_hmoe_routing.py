from __future__ import annotations

import unittest

import torch as th

from python.rl.hmoe_routing import (
    FAMILY_DEPARTURE_NAV,
    FAMILY_FORMATION_COOPERATIVE,
    FAMILY_RECOVERY_LANDING,
    FAMILY_TAKEOFF_GROUND,
    route_from_mission_observation,
)


class HMoERoutingTests(unittest.TestCase):
    def test_route_from_nav_v2_cooperative_takeoff_layout(self) -> None:
        mission = th.tensor(
            [
                [1.0, 90.0, 500.0, 180.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.0, 3.0, 5.0, 2.0, 120.0, -45.0, 30.0, 22.0, 2.0, 12.0, 11.0],
                [4.0, 180.0, 400.0, 160.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.0, 3.0, 5.0, 2.0, 120.0, -45.0, 30.0, 22.0, 2.0, 12.0, 11.0],
            ],
            dtype=th.float32,
        )
        route = route_from_mission_observation(mission)
        self.assertEqual([FAMILY_TAKEOFF_GROUND, FAMILY_RECOVERY_LANDING], route.family_index.tolist())
        self.assertEqual([1, 0], route.subexpert_index.tolist())

    def test_route_from_nav_v2_formation_role_layout(self) -> None:
        mission = th.tensor(
            [
                [2.0, 33.0, 1333.0, 177.0, 1.0, 0.0, 1000.0, 10.0, 100.0, 0.1, 2.0, 5000.0, 0.0, 0.0, 120.0, -45.0, 30.0, 21.0, 1.0, 11.0, 0.0],
                [3.0, 33.0, 1333.0, 177.0, 1.0, 0.0, 1000.0, 10.0, 100.0, 0.1, 2.0, 5000.0, 0.0, 0.0, 120.0, -45.0, 30.0, 22.0, 2.0, 12.0, 11.0],
            ],
            dtype=th.float32,
        )
        route = route_from_mission_observation(mission)
        self.assertEqual([FAMILY_FORMATION_COOPERATIVE, FAMILY_FORMATION_COOPERATIVE], route.family_index.tolist())
        self.assertEqual([1, 2], route.subexpert_index.tolist())

    def test_route_from_plain_nav_v2_layout(self) -> None:
        mission = th.tensor(
            [
                [2.0, 33.0, 1333.0, 177.0, 1.0, 0.0, 1000.0, 10.0, 100.0, 0.1, 2.0, 5000.0, 0.0, 0.0],
                [3.0, 33.0, 1333.0, 177.0, 1.0, 0.0, 1000.0, 10.0, 100.0, 0.1, 2.0, 5000.0, 0.0, 0.0],
            ],
            dtype=th.float32,
        )
        route = route_from_mission_observation(mission)
        self.assertEqual([FAMILY_DEPARTURE_NAV, FAMILY_DEPARTURE_NAV], route.family_index.tolist())
        self.assertEqual([0, 1], route.subexpert_index.tolist())


if __name__ == "__main__":
    unittest.main()
