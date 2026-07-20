from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py # noqa: E402


def _make_kernel() -> tuple[ef_py.SimulationKernel, int]:
  sim = ef_py.SimulationKernel()
  sim.reset(31)
  assert sim.load_database(resolve_repo_path("examples", "config", "database"))
  entity_id = sim.spawn_unit(
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
  sim.set_command_link(int(entity_id), 0.0, 0.0)

  mission = ef_py.MissionCommand()
  mission.active = True
  mission.command_code = 2
  mission.cmd_heading_deg = 0.0
  mission.cmd_altitude_m = 1200.0
  mission.cmd_speed_mps = 180.0
  sim.set_mission_command(int(entity_id), mission)
  return sim, int(entity_id)


def _run_with_pilot_action(
  *,
  stick_roll: float = 0.0,
  stick_pitch: float = 0.0,
  rudder: float = 0.0,
  steps: int = 240,
) -> tuple[float, float]:
  sim, entity_id = _make_kernel()
  pilot = ef_py.PilotAction()
  pilot.active = True
  pilot.stick_roll = float(stick_roll)
  pilot.stick_pitch = float(stick_pitch)
  pilot.rudder = float(rudder)
  pilot.throttle = 0.75
  pilot.gear_handle = 1.0
  sim.set_pilot_action(entity_id, pilot)

  for _ in range(steps):
    sim.step()

  inst = sim.get_instrument_state(entity_id)
  return float(inst.heading), float(inst.roll)


def _shortest_signed_heading_delta_deg(heading_deg: float, reference_deg: float) -> float:
  return (float(heading_deg) - float(reference_deg) + 180.0) % 360.0 - 180.0


class ControlAuthorityArbitrationTests(unittest.TestCase):
  def test_near_zero_active_pilot_action_does_not_steal_mission_control(self) -> None:
    baseline_heading_deg, baseline_roll_deg = _run_with_pilot_action()
    heading_deg, roll_deg = _run_with_pilot_action(stick_roll=0.01)

    self.assertAlmostEqual(heading_deg, baseline_heading_deg, delta=2.0)
    self.assertAlmostEqual(roll_deg, baseline_roll_deg, delta=5.0)

  def test_nontrivial_active_pilot_action_overrides_mission_control(self) -> None:
    baseline_heading_deg, _baseline_roll_deg = _run_with_pilot_action()
    heading_deg, roll_deg = _run_with_pilot_action(stick_roll=0.6)

    self.assertGreater(
      _shortest_signed_heading_delta_deg(heading_deg, baseline_heading_deg),
      10.0,
    )
    self.assertGreater(roll_deg, 20.0)


if __name__ == "__main__":
  unittest.main()
