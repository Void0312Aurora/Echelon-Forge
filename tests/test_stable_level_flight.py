#!/usr/bin/env python3
"""
Stable level-flight regression test.

Purpose:
  Verify the physics + control-law stack can sustain stable flight without
  diverging, crashing, or producing NaNs/Inf.

Method:
  - Load `scenarios/test_aero.json` (airborne start).
  - Apply a simple (realistic) autopilot-like PID: roll-hold, altitude-hold, and
    airspeed-hold using only instrument signals.
  - Run for a long horizon (200s) and assert basic stability bounds.
"""

from __future__ import annotations

import math
import os
import sys

import numpy as np


def _finite(x: float) -> bool:
    try:
        return math.isfinite(float(x))
    except Exception:
        return False


def main() -> int:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, repo_root)
    sys.path.insert(0, os.path.join(repo_root, "build"))

    import ef_py  # type: ignore
    from gym_envs.scenario_loader import ScenarioLoader

    sim = ef_py.SimulationKernel()
    sim.load_database(os.path.join(repo_root, "examples/config/database"))
    loader = ScenarioLoader(sim)
    agent_id = loader.load_scenario(os.path.join(repo_root, "scenarios/test_aero.json"), seed=0)

    dt = float(sim.get_time_step())
    assert dt > 0.0

    inst0 = sim.get_instrument_state(agent_id)
    alt_ref = float(inst0.alt_baro)
    ias_ref = float(inst0.ias)

    pa = ef_py.PilotAction()
    pa.active = True
    pa.rudder = 0.0
    pa.gear_handle = 0.0
    pa.flaps = 0.0
    pa.speedbrake = 0.0
    pa.brake = 0.0
    pa.brake_left = False
    pa.brake_right = False

    # Avionics/weapons off
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

    thr = 0.6
    alt_int = 0.0

    min_alt = float("inf")
    max_abs_roll = 0.0
    max_abs_pitch = 0.0
    max_abs_g = 0.0

    steps = int(round(200.0 / dt))
    assert steps > 100

    for _ in range(steps):
        inst = sim.get_instrument_state(agent_id)
        truth = sim.get_agent_observation(agent_id)

        assert truth.health > 0.0, "Aircraft crashed during level-flight stability test."

        alt = float(inst.alt_baro)
        vvi = float(inst.vvi)
        ias = float(inst.ias)
        pitch = float(inst.pitch)
        roll = float(inst.roll)
        p = float(inst.p)
        q = float(inst.q)
        g_load = float(inst.g_load)

        for v in (alt, vvi, ias, pitch, roll, p, q, g_load):
            assert _finite(v), f"Non-finite instrument value during flight test: {v!r}"

        min_alt = min(min_alt, alt)
        max_abs_roll = max(max_abs_roll, abs(roll))
        max_abs_pitch = max(max_abs_pitch, abs(pitch))
        max_abs_g = max(max_abs_g, abs(g_load))

        # Roll hold (level wings): small P + rate damping.
        pa.stick_roll = float(np.clip(-0.03 * roll - 0.01 * p, -0.5, 0.5))

        # Altitude hold -> pitch target (deg), with integral to remove steady-state error.
        alt_err = alt_ref - alt
        alt_int = float(np.clip(alt_int + alt_err * dt, -2000.0, 2000.0))
        pitch_tgt = float(np.clip(0.02 * alt_err + 0.0005 * alt_int - 0.06 * vvi, -15.0, 15.0))
        pa.stick_pitch = float(np.clip(0.08 * (pitch_tgt - pitch) - 0.015 * q, -1.0, 1.0))

        # Airspeed hold via throttle (slow integrator).
        spd_err = ias_ref - ias
        thr = float(np.clip(thr + 0.003 * spd_err, 0.0, 1.0))
        pa.throttle = thr

        sim.set_pilot_action(agent_id, pa)
        sim.step()

    # Stability assertions (broad, realism-friendly bounds).
    assert min_alt > 800.0, f"Altitude dipped too low: min_alt={min_alt:.1f}m"
    assert max_abs_roll < 10.0, f"Excessive roll during level flight: max|roll|={max_abs_roll:.1f}deg"
    assert max_abs_pitch < 15.0, f"Excessive pitch during level flight: max|pitch|={max_abs_pitch:.1f}deg"
    assert max_abs_g < 3.0, f"Excessive G-load during level flight: max|g|={max_abs_g:.2f}"
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

