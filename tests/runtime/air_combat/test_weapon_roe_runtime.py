from __future__ import annotations

import unittest

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py # noqa: E402

from gym_envs.scenario_loader import ScenarioLoader # noqa: E402


_DB_PATH = resolve_repo_path("examples", "config", "database")
_SCENARIO_PATH = resolve_repo_path(
  "scenarios",
  "air_combat",
  "air_combat_1v1_headon_sensor_smoke_v1.json",
)


def _load_fixture(seed: int = 20260517) -> tuple[ef_py.SimulationKernel, ScenarioLoader, int, int]:
  sim = ef_py.SimulationKernel()
  if not sim.load_database(_DB_PATH):
    raise AssertionError("failed to load runtime database")
  loader = ScenarioLoader(sim)
  blue_id = int(loader.load_scenario(_SCENARIO_PATH, seed=seed))
  red_id = int(loader.entities["Red_Fighter"])
  return sim, loader, blue_id, red_id


def _wait_for_track(sim: ef_py.SimulationKernel, shooter_id: int, target_id: int, *, max_steps: int = 160) -> None:
  for _ in range(max_steps):
    sim.step()
    obs = sim.get_agent_observation(shooter_id)
    if any(int(getattr(track, "id", 0)) == target_id for track in getattr(obs, "contacts", [])):
      return
  raise AssertionError("expected shooter to acquire target track")


def _fire_with_pilot_action(sim: ef_py.SimulationKernel, shooter_id: int) -> int:
  pilot = ef_py.PilotAction()
  pilot.active = True
  pilot.master_arm = True
  pilot.fire_weapon = True
  sim.set_pilot_action(shooter_id, pilot)
  sim.step()
  return int(getattr(sim.get_agent_observation(shooter_id), "missiles_remaining", -1))


class WeaponRoeRuntimeTests(unittest.TestCase):
  def test_hold_blocks_implicit_fallback_release(self) -> None:
    sim, _loader, blue_id, red_id = _load_fixture(seed=20260517)
    _wait_for_track(sim, blue_id, red_id)

    mission = ef_py.MissionCommand()
    mission.active = True
    mission.roe_state = 1
    sim.set_mission_command(blue_id, mission)

    missiles_before = int(getattr(sim.get_agent_observation(blue_id), "missiles_remaining", -1))
    missiles_after = _fire_with_pilot_action(sim, blue_id)

    self.assertEqual(missiles_after, missiles_before)

  def test_tight_requires_explicit_authorized_assigned_target(self) -> None:
    sim, _loader, blue_id, red_id = _load_fixture(seed=20260518)
    _wait_for_track(sim, blue_id, red_id)

    mission = ef_py.MissionCommand()
    mission.active = True
    mission.roe_state = 2
    mission.authorization_to_fire = True
    sim.set_mission_command(blue_id, mission)

    missiles_before = int(getattr(sim.get_agent_observation(blue_id), "missiles_remaining", -1))
    missiles_after = _fire_with_pilot_action(sim, blue_id)
    self.assertEqual(missiles_after, missiles_before)

    mission.assigned_target_id = red_id
    mission.authorization_to_fire = False
    sim.set_mission_command(blue_id, mission)
    missiles_after_without_authorization = _fire_with_pilot_action(sim, blue_id)
    self.assertEqual(missiles_after_without_authorization, missiles_before)

    mission.authorization_to_fire = True
    mission.engagement_authority_holder_id = blue_id + 99
    sim.set_mission_command(blue_id, mission)
    missiles_after_holder_mismatch = _fire_with_pilot_action(sim, blue_id)
    self.assertEqual(missiles_after_holder_mismatch, missiles_before)

    mission.engagement_authority_holder_id = blue_id
    sim.set_mission_command(blue_id, mission)
    missiles_after_authorized = _fire_with_pilot_action(sim, blue_id)
    self.assertEqual(missiles_after_authorized, missiles_before - 1)

  def test_free_and_zero_fail_closed_without_explicit_authorization(self) -> None:
    for roe_state in (0, 3):
      sim, _loader, blue_id, red_id = _load_fixture(seed=20260520 + roe_state)
      _wait_for_track(sim, blue_id, red_id)

      mission = ef_py.MissionCommand()
      mission.active = True
      mission.roe_state = roe_state
      sim.set_mission_command(blue_id, mission)

      missiles_before = int(getattr(sim.get_agent_observation(blue_id), "missiles_remaining", -1))
      missiles_after = _fire_with_pilot_action(sim, blue_id)
      self.assertEqual(
        missiles_after,
        missiles_before,
        f"expected fail-closed hold without explicit authorization for roe_state={roe_state}",
      )


if __name__ == "__main__":
  unittest.main()
