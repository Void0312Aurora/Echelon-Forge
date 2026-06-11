from __future__ import annotations

import math
import unittest
from dataclasses import dataclass

from python.testing.runtime import configure_sim_log_level, resolve_repo_path


configure_sim_log_level("error")

import ef_py # noqa: E402
from gym_envs.scenario_loader import ScenarioLoader # noqa: E402


_DB_PATH = resolve_repo_path("examples", "config", "database")
_SCENARIO_PATH = resolve_repo_path("scenarios", "test", "test_aero.json")
_G = 9.80665


@dataclass(frozen=True)
class FlightProbeResult:
  initial_alt_m: float
  final_alt_m: float
  initial_speed_mps: float
  final_speed_mps: float
  initial_ias_mps: float
  final_ias_mps: float
  final_vvi_mps: float
  final_pitch_deg: float
  final_roll_deg: float
  final_aoa_deg: float
  final_beta_deg: float
  max_abs_aoa_deg: float
  max_abs_beta_deg: float
  max_abs_roll_deg: float
  max_abs_pitch_deg: float
  max_g_load: float
  min_g_load: float
  final_pos_m: tuple[float, float, float]
  final_vel_mps: tuple[float, float, float]

  @property
  def delta_alt_m(self) -> float:
    return self.final_alt_m - self.initial_alt_m

  @property
  def delta_speed_mps(self) -> float:
    return self.final_speed_mps - self.initial_speed_mps

  @property
  def initial_specific_energy_j_kg(self) -> float:
    return (_G * self.initial_alt_m) + (0.5 * self.initial_speed_mps * self.initial_speed_mps)

  @property
  def final_specific_energy_j_kg(self) -> float:
    return (_G * self.final_alt_m) + (0.5 * self.final_speed_mps * self.final_speed_mps)

  @property
  def delta_specific_energy_j_kg(self) -> float:
    return self.final_specific_energy_j_kg - self.initial_specific_energy_j_kg


def _speed_mps(vel: tuple[float, float, float] | list[float]) -> float:
  return math.sqrt(sum(float(v) * float(v) for v in vel))


def _build_default_pilot_action(
  *,
  throttle: float,
  stick_pitch: float,
  stick_roll: float,
  rudder: float = 0.0,
) -> ef_py.PilotAction:
  pa = ef_py.PilotAction()
  pa.active = True
  pa.throttle = float(throttle)
  pa.stick_pitch = float(stick_pitch)
  pa.stick_roll = float(stick_roll)
  pa.rudder = float(rudder)
  pa.gear_handle = 0.0
  pa.flaps = 0.0
  pa.speedbrake = 0.0
  pa.brake = 0.0
  pa.brake_left = False
  pa.brake_right = False
  pa.radar_active = False
  pa.radar_scan_az = 0.0
  pa.radar_scan_el = 0.0
  pa.tms_up = False
  pa.master_arm = False
  pa.fire_weapon = False
  pa.fire_gun = False
  pa.weapon_select_id = 0
  pa.program_chaff = False
  pa.program_flare = False
  pa.jettison_emergency = False
  return pa


def _run_probe(
  *,
  throttle: float,
  stick_pitch: float = 0.0,
  stick_roll: float = 0.0,
  rudder: float = 0.0,
  steps: int = 120,
  seed: int = 0,
) -> FlightProbeResult:
  sim = ef_py.SimulationKernel()
  if not sim.load_database(_DB_PATH):
    raise AssertionError("failed to load runtime database")

  loader = ScenarioLoader(sim)
  agent_id = int(loader.load_scenario(_SCENARIO_PATH, seed=seed))
  if agent_id <= 0:
    raise AssertionError("scenario did not spawn an agent")

  inst0 = sim.get_instrument_state(agent_id)
  pos0 = tuple(float(v) for v in sim.get_unit_position(agent_id))
  vel0 = tuple(float(v) for v in sim.get_unit_velocity(agent_id))

  max_abs_aoa = abs(float(getattr(inst0, "aoa", 0.0)))
  max_abs_beta = abs(float(getattr(inst0, "beta", 0.0)))
  max_abs_roll = abs(float(getattr(inst0, "roll", 0.0)))
  max_abs_pitch = abs(float(getattr(inst0, "pitch", 0.0)))
  max_g_load = float(getattr(inst0, "g_load", 0.0))
  min_g_load = float(getattr(inst0, "g_load", 0.0))

  pa = _build_default_pilot_action(
    throttle=throttle,
    stick_pitch=stick_pitch,
    stick_roll=stick_roll,
    rudder=rudder,
  )

  for _ in range(int(steps)):
    sim.set_pilot_action(agent_id, pa)
    sim.step()
    inst = sim.get_instrument_state(agent_id)
    max_abs_aoa = max(max_abs_aoa, abs(float(getattr(inst, "aoa", 0.0))))
    max_abs_beta = max(max_abs_beta, abs(float(getattr(inst, "beta", 0.0))))
    max_abs_roll = max(max_abs_roll, abs(float(getattr(inst, "roll", 0.0))))
    max_abs_pitch = max(max_abs_pitch, abs(float(getattr(inst, "pitch", 0.0))))
    g_load = float(getattr(inst, "g_load", 0.0))
    max_g_load = max(max_g_load, g_load)
    min_g_load = min(min_g_load, g_load)

  inst1 = sim.get_instrument_state(agent_id)
  pos1 = tuple(float(v) for v in sim.get_unit_position(agent_id))
  vel1 = tuple(float(v) for v in sim.get_unit_velocity(agent_id))

  return FlightProbeResult(
    initial_alt_m=pos0[2],
    final_alt_m=pos1[2],
    initial_speed_mps=_speed_mps(vel0),
    final_speed_mps=_speed_mps(vel1),
    initial_ias_mps=float(getattr(inst0, "ias", 0.0)),
    final_ias_mps=float(getattr(inst1, "ias", 0.0)),
    final_vvi_mps=float(getattr(inst1, "vvi", 0.0)),
    final_pitch_deg=float(getattr(inst1, "pitch", 0.0)),
    final_roll_deg=float(getattr(inst1, "roll", 0.0)),
    final_aoa_deg=float(getattr(inst1, "aoa", 0.0)),
    final_beta_deg=float(getattr(inst1, "beta", 0.0)),
    max_abs_aoa_deg=max_abs_aoa,
    max_abs_beta_deg=max_abs_beta,
    max_abs_roll_deg=max_abs_roll,
    max_abs_pitch_deg=max_abs_pitch,
    max_g_load=max_g_load,
    min_g_load=min_g_load,
    final_pos_m=pos1,
    final_vel_mps=vel1,
  )


class FlightDynamicsRealismGuardTests(unittest.TestCase):
  def test_full_throttle_improves_specific_energy_relative_to_idle(self) -> None:
    # Keep this probe in the pre-departure envelope so we measure propulsion
    # benefit before the coarse model falls into a highly post-stall regime.
    idle = _run_probe(throttle=0.0, steps=60)
    full = _run_probe(throttle=1.0, steps=60)

    self.assertGreater(full.final_speed_mps, idle.final_speed_mps + 8.0)
    self.assertGreater(
      full.delta_specific_energy_j_kg,
      idle.delta_specific_energy_j_kg + 1500.0,
    )

  def test_pitch_up_response_trades_speed_for_altitude_and_aoa(self) -> None:
    shallow = _run_probe(throttle=0.8, stick_pitch=0.2, steps=120)
    steep = _run_probe(throttle=0.8, stick_pitch=0.4, steps=120)

    self.assertGreater(shallow.delta_alt_m, 30.0)
    self.assertGreater(steep.delta_alt_m, shallow.delta_alt_m + 50.0)
    self.assertGreater(shallow.max_abs_aoa_deg, 1.5)
    self.assertGreater(steep.max_abs_aoa_deg, shallow.max_abs_aoa_deg + 1.0)
    self.assertLess(steep.final_speed_mps, shallow.final_speed_mps - 8.0)
    self.assertGreater(steep.max_g_load, shallow.max_g_load)

  def test_roll_response_is_left_right_symmetric(self) -> None:
    right = _run_probe(throttle=0.7, stick_roll=0.3, steps=80)
    left = _run_probe(throttle=0.7, stick_roll=-0.3, steps=80)

    self.assertGreater(right.final_roll_deg, 20.0)
    self.assertLess(left.final_roll_deg, -20.0)
    self.assertAlmostEqual(
      abs(right.final_roll_deg),
      abs(left.final_roll_deg),
      delta=3.0,
    )
    self.assertLess(right.final_pos_m[1] * left.final_pos_m[1], 0.0)
    self.assertAlmostEqual(
      abs(right.final_pos_m[1]),
      abs(left.final_pos_m[1]),
      delta=3.0,
    )
    self.assertLess(right.max_abs_beta_deg, 2.0)
    self.assertLess(left.max_abs_beta_deg, 2.0)

  def test_moderate_probes_remain_in_coarse_substall_region(self) -> None:
    shallow = _run_probe(throttle=0.8, stick_pitch=0.2, steps=120)
    roll = _run_probe(throttle=0.7, stick_roll=0.3, steps=80)

    self.assertLess(shallow.max_abs_aoa_deg, 10.0)
    self.assertLess(roll.max_abs_aoa_deg, 5.0)
    self.assertLess(roll.max_abs_beta_deg, 2.0)
    self.assertLess(shallow.max_g_load, 3.0)
    self.assertGreaterEqual(shallow.min_g_load, 0.0)


if __name__ == "__main__":
  unittest.main()
