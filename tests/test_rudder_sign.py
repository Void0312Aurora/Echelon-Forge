#!/usr/bin/env python3
"""
Regression: PilotAction.rudder sign convention.

PilotAction.rudder is defined as:
  +1.0 => "nose right" (NAV heading increases)
  -1.0 => "nose left"  (NAV heading decreases)

This test runs a deterministic takeoff (no wind/randomization), then applies a
positive/negative rudder pulse while airborne and checks the heading response
has the correct sign.
"""

from __future__ import annotations

import os
import sys

import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from gym_envs.universal_env import UniversalEnv


def _shortest_angle_deg(target: float, current: float) -> float:
    d = float(target) - float(current)
    while d > 180.0:
        d -= 360.0
    while d < -180.0:
        d += 360.0
    return d


def _run_episode(*, rudder_pulse: float) -> float:
    env = UniversalEnv("scenarios/takeoff.json", action_mode="takeoff4", include_visual=False)
    env.set_randomization_overrides(
        {
            "world_yaw_range": [0.0, 0.0],
            "wind_headwind_range": [0.0, 0.0],
            "wind_crosswind_range": [0.0, 0.0],
            "wind_shear_range": [0.0, 0.0],
        }
    )
    obs, _ = env.reset(seed=0)

    IDX_IAS = 0
    IDX_ALT = 2
    IDX_PITCH = 7
    IDX_HDG = 9

    pulse_started = False
    pulse_steps_left = 0
    hdg_before = None
    hdg_after = None

    for step in range(int(env.max_steps)):
        inst = obs["instruments"]
        ias = float(inst[IDX_IAS])
        alt = float(inst[IDX_ALT])
        pitch_deg = float(inst[IDX_PITCH])
        hdg = float(inst[IDX_HDG])

        # Simple deterministic takeoff schedule (no wind).
        if ias < 100.0:
            pitch_cmd = 0.0
        else:
            target_pitch = 15.0
            pitch_cmd = float(np.clip((target_pitch - pitch_deg) * 0.05, -1.0, 1.0))

        # Rudder pulse only once clearly airborne.
        rud = 0.0
        if alt > 80.0:
            if not pulse_started:
                pulse_started = True
                hdg_before = hdg
                # 2 seconds @ dt=0.05 => 40 steps
                pulse_steps_left = 40
            if pulse_steps_left > 0:
                rud = float(rudder_pulse)
                pulse_steps_left -= 1
            else:
                rud = 0.0
                if hdg_after is None:
                    hdg_after = hdg

        action = np.array([pitch_cmd, 0.0, rud, 1.0], dtype=np.float32)
        obs, _, terminated, truncated, _ = env.step(action)
        if terminated or truncated:
            break

        if pulse_started and hdg_after is not None:
            break

    if hdg_before is None or hdg_after is None:
        raise RuntimeError("rudder pulse window was not reached (did not get airborne fast enough)")

    return _shortest_angle_deg(hdg_after, hdg_before)


def main() -> int:
    d_pos = _run_episode(rudder_pulse=0.25)
    d_neg = _run_episode(rudder_pulse=-0.25)

    print(f"heading_delta_deg(+rudder) = {d_pos:+.3f}")
    print(f"heading_delta_deg(-rudder) = {d_neg:+.3f}")

    if not (d_pos > 0.5):
        print("FAIL: +rudder did not increase heading (nose right).")
        return 1
    if not (d_neg < -0.5):
        print("FAIL: -rudder did not decrease heading (nose left).")
        return 1

    print("PASS: rudder sign convention")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
