#!/usr/bin/env python3
"""
Regression: SB3-style midpoint actions should not lock the aircraft on the runway.

Untrained continuous policies commonly start near the midpoint of each action dim.
For [0,1] controls, that midpoint is 0.5. If we interpret 0.5 as "half brakes",
ground roll can be completely prevented, making training appear "stuck".
"""

import os
import sys

import numpy as np

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_dir)
sys.path.append(os.path.join(base_dir, "build"))

import ef_py
from gym_envs.scenario_loader import ScenarioLoader
from gym_envs.universal_env import half_to_unit


def test_midpoint_ground_roll():
    sim = ef_py.SimulationKernel()
    sim.load_database("examples/config/database")

    loader = ScenarioLoader(sim)
    agent_id = loader.load_scenario(os.path.join(base_dir, "scenarios/takeoff.json"), seed=42)
    assert agent_id is not None

    # Mimic SB3 initial action in env space:
    # - dims with low=-1/high=1 -> 0.0
    # - dims with low=0/high=1  -> 0.5
    action = np.zeros(17, dtype=np.float32)
    for idx in [3, 4, 5, 6, 7, 8, 9, 12, 13, 14, 15, 16]:
        action[idx] = 0.5

    for _ in range(200):  # 10 seconds at dt=0.05 (takeoff.json)
        pa = ef_py.PilotAction()
        pa.active = True

        pa.stick_pitch = float(action[0])
        pa.stick_roll = float(action[1])
        pa.rudder = float(action[2])
        pa.throttle = float(action[3])

        pa.gear_handle = float(action[4])
        pa.flaps = float(half_to_unit(float(action[5])))
        pa.speedbrake = float(half_to_unit(float(action[6])))

        pa.brake_left = bool(action[7] > 0.5)
        pa.brake_right = bool(action[8] > 0.5)
        pa.brake = float(half_to_unit(float(max(action[7], action[8]))))

        pa.radar_active = bool(action[9] > 0.5)
        pa.radar_scan_az = float(action[10]) * 60.0
        pa.radar_scan_el = float(action[11]) * 30.0
        pa.tms_up = bool(action[12] > 0.5)

        pa.master_arm = bool(action[13] > 0.5)
        pa.fire_weapon = bool(action[14] > 0.5)
        pa.fire_gun = bool(action[15] > 0.5)
        pa.weapon_select_id = int(action[16] * 7)

        pa.program_chaff = False
        pa.program_flare = False
        pa.jettison_emergency = False

        sim.set_pilot_action(agent_id, pa)
        sim.step()

    inst = sim.get_instrument_state(agent_id)
    assert inst.ias > 5.0, f"Expected ground roll acceleration; got IAS={inst.ias:.3f} m/s"


if __name__ == "__main__":
    test_midpoint_ground_roll()
    print("PASS: midpoint ground roll")

