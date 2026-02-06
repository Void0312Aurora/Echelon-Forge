#!/usr/bin/env python3
"""
Takeoff + stable flight regression.

Purpose:
  Validate end-to-end stability across:
    - ground roll
    - rotation / liftoff
    - post-liftoff stable flight (no divergence / no crash)

This is not an RL test: it uses a simple scripted controller (autopilot-like)
based on instrument signals only.
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


def _no_randomization_overrides() -> dict:
    # Deterministic baseline: remove wind and world-yaw randomization.
    return {
        "world_yaw_range": [0.0, 0.0],
        # Global wind sampling
        "wind_speed_range": [0.0, 0.0],
        "wind_dir_from_range": [0.0, 0.0],
        # Runway-relative wind sampling
        "wind_headwind_range": [0.0, 0.0],
        "wind_crosswind_range": [0.0, 0.0],
        "wind_tailwind_max_mps": 0.0,
        # Shear
        "wind_shear_range": [0.0, 0.0],
    }


def main() -> int:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, repo_root)
    sys.path.insert(0, os.path.join(repo_root, "build"))

    import ef_py  # type: ignore
    from gym_envs.scenario_loader import ScenarioLoader

    sim = ef_py.SimulationKernel()
    sim.load_database(os.path.join(repo_root, "examples/config/database"))
    loader = ScenarioLoader(sim)
    loader.set_randomization_overrides(_no_randomization_overrides())
    agent_id = loader.load_scenario(os.path.join(repo_root, "scenarios/takeoff.json"), seed=0)

    dt = float(sim.get_time_step())
    assert dt > 0.0

    pa = ef_py.PilotAction()
    pa.active = True
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

    stage = "takeoff"
    thr = 1.0
    alt_ref = 0.0
    ias_ref = 0.0
    alt_int = 0.0
    stable_steps = 0

    min_alt_stable = float("inf")
    max_abs_roll = 0.0
    max_abs_pitch = 0.0

    max_steps = 2000
    for _ in range(max_steps):
        inst = sim.get_instrument_state(agent_id)
        truth = sim.get_agent_observation(agent_id)
        assert truth.health > 0.0, "Aircraft crashed during takeoff/stable flight test."

        # Basic finiteness guard
        for v in (
            inst.alt_baro,
            inst.alt_radar,
            inst.ias,
            inst.vvi,
            inst.pitch,
            inst.roll,
            inst.p,
            inst.q,
            inst.g_load,
        ):
            assert _finite(v), f"Non-finite instrument value: {v!r}"

        if stage == "takeoff":
            pa.throttle = 1.0
            pa.stick_roll = 0.0
            pa.rudder = 0.0

            # Rotate schedule (simple): wait for speed, then pull to target pitch.
            if float(inst.ias) < 100.0:
                pa.stick_pitch = 0.0
            else:
                pitch_err = 13.0 - float(inst.pitch)
                pa.stick_pitch = float(np.clip(pitch_err * 0.05, -1.0, 1.0))

            # Gear: down on runway, up after liftoff
            pa.gear_handle = 0.0 if float(inst.alt_baro) > 30.0 else 1.0

            # Switch to stability controller after reaching a safe flight regime.
            if float(inst.alt_baro) > 300.0 and float(inst.ias) > 150.0:
                stage = "stable"
                alt_ref = float(inst.alt_baro)
                ias_ref = float(inst.ias)
                thr = float(pa.throttle)
                alt_int = 0.0
                stable_steps = 0
                min_alt_stable = float("inf")

        else:
            stable_steps += 1

            alt = float(inst.alt_baro)
            vvi = float(inst.vvi)
            pitch = float(inst.pitch)
            roll = float(inst.roll)
            p = float(inst.p)
            q = float(inst.q)
            ias = float(inst.ias)

            min_alt_stable = min(min_alt_stable, alt)
            max_abs_roll = max(max_abs_roll, abs(roll))
            max_abs_pitch = max(max_abs_pitch, abs(pitch))

            # Roll hold
            pa.stick_roll = float(np.clip(-0.03 * roll - 0.01 * p, -0.6, 0.6))

            # Altitude hold (PI + vvi damping) -> pitch target (deg)
            alt_err = alt_ref - alt
            alt_int = float(np.clip(alt_int + alt_err * dt, -2000.0, 2000.0))
            pitch_tgt = float(np.clip(0.02 * alt_err + 0.0005 * alt_int - 0.06 * vvi, -15.0, 15.0))
            pa.stick_pitch = float(np.clip(0.08 * (pitch_tgt - pitch) - 0.015 * q, -1.0, 1.0))

            # Airspeed hold via throttle
            spd_err = ias_ref - ias
            thr = float(np.clip(thr + 0.003 * spd_err, 0.0, 1.0))
            pa.throttle = thr

            pa.rudder = 0.0
            pa.gear_handle = 0.0

        sim.set_pilot_action(agent_id, pa)
        sim.step()

    assert stage == "stable", "Did not reach stable flight phase within max_steps."
    assert stable_steps >= int(round(40.0 / dt)), f"Stable phase too short: {stable_steps} steps"
    assert min_alt_stable > 150.0, f"Altitude dipped too low during stable flight: min_alt={min_alt_stable:.1f}m"
    assert max_abs_roll < 20.0, f"Excessive roll in stable phase: max|roll|={max_abs_roll:.1f}deg"
    assert max_abs_pitch < 20.0, f"Excessive pitch in stable phase: max|pitch|={max_abs_pitch:.1f}deg"
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

