from __future__ import annotations

import unittest

import torch as th

from python.mission_obs_taxonomy import mission_observation_dim, mission_observation_field_index
from python.rl.policy_algo.hmoe_routing import (
  FAMILY_COMBAT_WEAPONS,
  FAMILY_DEPARTURE_NAV,
  FAMILY_FORMATION_COOPERATIVE,
  FAMILY_RECOVERY_LANDING,
  FAMILY_TAKEOFF_GROUND,
  route_from_mission_observation,
)


class PolicyRoutingContractTests(unittest.TestCase):
  def test_route_from_nav_v2_cooperative_takeoff_layout(self) -> None:
    mission = th.tensor(
      [
        [1.0, 90.0, 500.0, 180.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.0, 3.0, 5.0, 2.0, 120.0, -45.0, 30.0, 22.0, 2.0, 12.0, 11.0],
        [4.0, 180.0, 400.0, 160.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.0, 3.0, 5.0, 2.0, 120.0, -45.0, 30.0, 22.0, 2.0, 12.0, 11.0],
      ],
      dtype=th.float32,
    )
    instruments = th.tensor(
      [
        [40.0, 0.0, 0.0, 5.0],
        [70.0, 0.0, 0.0, 200.0],
      ],
      dtype=th.float32,
    )
    route = route_from_mission_observation(mission, instruments=instruments)
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
    instruments = th.tensor(
      [
        [210.0, 0.0, 0.0, 1200.0],
        [210.0, 0.0, 0.0, 1200.0],
      ],
      dtype=th.float32,
    )
    route = route_from_mission_observation(mission, instruments=instruments)
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
    instruments = th.tensor(
      [
        [210.0, 0.0, 0.0, 1200.0],
        [210.0, 0.0, 0.0, 1200.0],
      ],
      dtype=th.float32,
    )
    route = route_from_mission_observation(mission, instruments=instruments)
    self.assertEqual([FAMILY_DEPARTURE_NAV, FAMILY_DEPARTURE_NAV], route.family_index.tolist())
    self.assertEqual([0, 1], route.subexpert_index.tolist())

  def test_route_keeps_takeoff_family_for_route_command_during_low_alt_departure(self) -> None:
    mission = th.tensor(
      [
        [3.0, 90.0, 600.0, 180.0, 1.0, 0.0, 1200.0, 5.0, 450.0, 0.02, 8.0, 2000.0, 0.0, 0.0, 2.0, 4.0, 6.0, 1.0, 0.0, 0.0, 0.0, 21.0, 1.0, 11.0, 0.0],
        [3.0, 90.0, 600.0, 180.0, 1.0, 0.0, 1200.0, 5.0, 450.0, 0.02, 8.0, 2000.0, 0.0, 0.0, 3.0, 1.0, 6.0, 1.0, 180.0, -90.0, 25.0, 22.0, 2.0, 12.0, 11.0],
      ],
      dtype=th.float32,
    )
    instruments = th.tensor(
      [
        [85.0, 0.0, 0.0, 60.0],
        [80.0, 0.0, 0.0, 45.0],
      ],
      dtype=th.float32,
    )
    route = route_from_mission_observation(mission, instruments=instruments)
    self.assertEqual([FAMILY_TAKEOFF_GROUND, FAMILY_TAKEOFF_GROUND], route.family_index.tolist())
    self.assertEqual([1, 2], route.subexpert_index.tolist())

  def test_route_uses_departure_family_for_post_liftoff_route_capture(self) -> None:
    mission = th.tensor(
      [
        [3.0, 90.0, 1400.0, 205.0, 1.0, 0.0, 8000.0, 20.0, 950.0, 0.55, 28.0, 12000.0, 0.0, 0.0, 2.0, 5.0, 6.0, 1.0, 180.0, -90.0, 25.0, 21.0, 1.0, 11.0, 0.0],
        [3.0, 90.0, 1400.0, 205.0, 1.0, 0.0, 8000.0, 20.0, 950.0, 0.40, 24.0, 12000.0, 0.0, 0.0, 2.0, 5.0, 6.0, 1.0, 180.0, -90.0, 25.0, 22.0, 2.0, 12.0, 11.0],
      ],
      dtype=th.float32,
    )
    instruments = th.tensor(
      [
        [170.0, 0.0, 0.0, 350.0],
        [175.0, 0.0, 0.0, 420.0],
      ],
      dtype=th.float32,
    )
    route = route_from_mission_observation(mission, instruments=instruments)
    self.assertEqual([FAMILY_DEPARTURE_NAV, FAMILY_DEPARTURE_NAV], route.family_index.tolist())
    self.assertEqual([1, 1], route.subexpert_index.tolist())

  def test_route_detects_landing_family_from_low_altitude_descent_profile(self) -> None:
    mission = th.tensor(
      [
        [3.0, 90.0, 300.0, 120.0, 1.0, 0.0, 1500.0, 5.0, -500.0, 0.10, 6.0, 3000.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
      ],
      dtype=th.float32,
    )
    instruments = th.tensor(
      [
        [110.0, 0.0, 0.0, 280.0],
      ],
      dtype=th.float32,
    )
    route = route_from_mission_observation(mission, instruments=instruments)
    self.assertEqual([FAMILY_RECOVERY_LANDING], route.family_index.tolist())
    self.assertEqual([0], route.subexpert_index.tolist())

  def test_route_detects_air_combat_c2_roe_weapons_family(self) -> None:
    mission = th.tensor(
      [
        [2.0, 0.0, 7000.0, 230.0, 2.0, 2.0, 1.0, 101.0, 9001.0, 301.0, 301.0, 0.0, 12.5, 3.0, 2.0, 1.0, 1.0, 0.0, 0.0, 1.0],
        [2.0, 0.0, 7000.0, 230.0, 2.0, 1.0, 1.0, 101.0, 9001.0, 301.0, 301.0, 0.0, 12.5, 3.0, 3.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        [2.0, 0.0, 7000.0, 230.0, 2.0, 2.0, 1.0, 101.0, 9001.0, 301.0, 301.0, 0.0, 12.5, 3.0, 2.0, 1.0, 0.0, 1.0, 1.0, 1.0],
      ],
      dtype=th.float32,
    )

    route = route_from_mission_observation(mission)

    self.assertEqual([FAMILY_COMBAT_WEAPONS, FAMILY_COMBAT_WEAPONS, FAMILY_COMBAT_WEAPONS], route.family_index.tolist())
    self.assertEqual([1, 0, 2], route.subexpert_index.tolist())

  def test_route_detects_air_combat_c2_roe_v2_state_completed_fire_mask(self) -> None:
    mode = "air_combat_c2_roe_v2"
    mission = th.zeros((2, mission_observation_dim(mode)), dtype=th.float32)
    mission[:, mission_observation_field_index(mode, "shot_policy_state")] = 1.0
    mission[:, mission_observation_field_index(mode, "shot_budget_remaining")] = 1.0
    mission[:, mission_observation_field_index(mode, "target_contact_present")] = 1.0
    mission[0, mission_observation_field_index(mode, "fire_mask_open")] = 1.0
    mission[1, mission_observation_field_index(mode, "pending_assessment")] = 1.0

    route = route_from_mission_observation(mission)

    self.assertEqual([FAMILY_COMBAT_WEAPONS, FAMILY_COMBAT_WEAPONS], route.family_index.tolist())
    self.assertEqual([1, 2], route.subexpert_index.tolist())


if __name__ == "__main__":
  unittest.main()
