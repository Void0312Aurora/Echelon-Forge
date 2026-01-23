#!/usr/bin/env python3
"""
Manual Takeoff Test Script
Tests if the physics engine allows the aircraft to naturally take off.
Applies: Full throttle, gradual elevator pull at rotation speed.
"""
import os
import sys

import numpy as np

# Add repo root and build to path
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_dir)
sys.path.append(os.path.join(base_dir, "build"))

import ef_py
from gym_envs.scenario_loader import ScenarioLoader

def main():
    sim = ef_py.SimulationKernel()
    sim.load_database("examples/config/database")
    loader = ScenarioLoader(sim)
    agent_id = loader.load_scenario(os.path.join(base_dir, "scenarios/takeoff.json"), seed=42)
    
    print("="*60)
    print("MANUAL TAKEOFF TEST")
    print("="*60)
    
    # Action layout: [pitch, roll, rudder, throttle, gear, flaps, speedbrake, ...]
    # We'll use a simple controller:
    # - Full throttle
    # - Neutral stick until speed > 80 m/s, then pull back (pitch up)
    # - Retract gear after altitude > 20m
    
    target_pitch = 15.0

    for step in range(2000):
        inst = sim.get_instrument_state(agent_id)
        speed = inst.ias
        alt = inst.alt_baro
        aoa = inst.aoa
        pitch = inst.pitch
        gear = inst.gear_pos

        pa = ef_py.PilotAction()
        pa.active = True

        pa.stick_roll = 0.0
        pa.rudder = 0.0
        pa.throttle = 1.0
        pa.flaps = 0.0
        pa.speedbrake = 0.0
        pa.brake = 0.0
        pa.brake_left = False
        pa.brake_right = False

        if speed < 100.0:
            pa.stick_pitch = 0.0  # Wait for Vr
        else:
            pitch_err = target_pitch - pitch
            pa.stick_pitch = float(np.clip(pitch_err * 0.05, -1.0, 1.0))

        # Gear control
        pa.gear_handle = 0.0 if alt > 30.0 else 1.0

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

        sim.set_pilot_action(agent_id, pa)
        sim.step()

        truth = sim.get_agent_observation(agent_id)
        
        # Print status every 50 steps
        if step % 50 == 0:
            print(
                f"[Step {step:4d}] Speed: {speed:6.1f} m/s | Alt: {alt:6.1f} m | "
                f"AoA: {aoa:5.1f}° | Pitch: {pitch:5.1f}° | Gear: {gear:.1f}"
            )
            print(f"         -> Truth: vx={truth.vx:.2f}, vy={truth.vy:.2f}, vz={truth.vz:.2f}, z={truth.z:.2f}, health={truth.health}")
        
        # Check for success
        if alt > 300.0 and speed > 150.0:
            print("\n" + "="*60)
            print("SUCCESS! Aircraft has taken off and reached safe altitude.")
            print(f"Final: Alt={alt:.1f}m, Speed={speed:.1f}m/s")
            print("="*60)
            return True
            
    
    print("\n" + "="*60)
    print(f"TIMEOUT! Did not reach target in 2000 steps.")
    print(f"Final: Alt={alt:.1f}m, Speed={speed:.1f}m/s")
    print("="*60)
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
