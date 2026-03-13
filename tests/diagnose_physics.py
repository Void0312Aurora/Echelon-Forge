#!/usr/bin/env python3
"""
Detailed physics diagnostic - checks thrust, drag, friction values directly from C++.
"""
import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath("."))

import ef_py

def main():
    print("=" * 70)
    print("DETAILED PHYSICS DIAGNOSTIC")
    print("=" * 70)
    
    sim = ef_py.SimulationKernel()
    sim.load_database("examples/config/database")
    sim.reset(42)
    
    # Spawn a single F-16
    eid = sim.spawn_unit(
        ef_py.Side.Blue,
        "Aircraft",  # Type
        -1400.0, 0.0, 2.1,  # Position
        90.0, 0.0, 0.0,     # Heading, Pitch, Roll
        0.0, 0.0, 0.0       # Velocity
    )
    
    print(f"\n1. SPAWNED UNIT (ID={eid})")
    print("-" * 50)
    
    # Get observation to check initial state
    obs = sim.get_agent_observation(eid)
    inst = sim.get_instrument_state(eid)
    
    print(f"  Initial position: ({obs.x:.1f}, {obs.y:.1f}, {obs.z:.1f})")
    print(f"  Initial heading: {obs.heading:.1f} deg")
    print(f"  Initial speed: {obs.speed:.2f} m/s")
    print(f"  Health: {obs.health:.1f}")
    
    # Apply full throttle action
    pilot = ef_py.PilotAction()
    pilot.active = True
    pilot.throttle = 1.0  # FULL throttle
    pilot.stick_pitch = 0.0
    pilot.stick_roll = 0.0
    pilot.rudder = 0.0
    pilot.brake = 0.0
    pilot.gear_handle = 1.0  # Gear down for ground
    pilot.flaps = 0.0
    
    sim.set_pilot_action(eid, pilot)
    
    print(f"\n2. APPLIED ACTION")
    print("-" * 50)
    print(f"  Throttle: {pilot.throttle}")
    print(f"  Brake: {pilot.brake}")
    print(f"  Gear: {pilot.gear_handle}")
    
    # Step simulation and track progress
    n_steps = 100
    print(f"\n3. SIMULATION PROGRESS ({n_steps} steps)")
    print("-" * 50)
    
    dt = sim.get_time_step()
    print(f"  Time step: {dt:.3f}s")
    
    positions = []
    speeds = []
    
    for i in range(n_steps):
        sim.step()
        
        obs = sim.get_agent_observation(eid)
        inst = sim.get_instrument_state(eid)
        
        positions.append((obs.x, obs.y, obs.z))
        speeds.append(obs.speed)
        
        if i in [0, 9, 19, 49, 99]:
            t = (i + 1) * dt
            print(f"  t={t:.2f}s: pos=({obs.x:.1f},{obs.y:.1f},{obs.z:.1f}), "
                  f"speed={obs.speed:.1f} m/s, IAS={inst.ias:.1f} m/s, eng={inst.engine_rpm:.0f}%")
    
    # Analyze
    print(f"\n4. ANALYSIS")
    print("-" * 50)
    
    # Expected physics:
    # Thrust F = 76310 N (mil) at throttle=1.0 (below 0.9 threshold for AB)
    # Mass m = 8570 kg (empty)
    # Acceleration a = F/m = 76310/8570 = 8.9 m/s²
    # Compare against the actual simulated horizon (n_steps * dt), not a hardcoded 5s.
    
    final_speed = speeds[-1]
    expected_accel = 76310.0 / 8570.0  # ~8.9 m/s²
    total_time = n_steps * dt
    expected_speed = expected_accel * total_time
    
    print(f"  Expected accel (no drag): {expected_accel:.1f} m/s²")
    print(f"  Simulated horizon: {total_time:.2f} s")
    print(f"  Expected speed at {total_time:.2f}s: {expected_speed:.1f} m/s")
    print(f"  Actual speed at {total_time:.2f}s: {final_speed:.1f} m/s")
    print(f"  Ratio: {final_speed/expected_speed*100:.1f}%")
    
    # Check if moving at all
    dx = positions[-1][0] - positions[0][0]
    print(f"  Distance traveled (X): {dx:.1f} m")
    
    # Diagnose issues
    print(f"\n5. DIAGNOSIS")
    print("=" * 70)
    
    if final_speed < 1.0:
        print("  ✗ CRITICAL: Almost no acceleration! Thrust is not being applied.")
        print("    Possible causes:")
        print("    - PilotAction.throttle not reaching ForceSystem")
        print("    - Propulsion component not loaded on entity")
        print("    - Ground friction coefficient too high")
    elif final_speed < expected_speed * 0.3:
        print("  ⚠ WARNING: Very low acceleration (< 30% expected).")
        print("    Possible causes:")
        print("    - Propulsion values incorrect or scaled down")
        print("    - High drag or friction")
        print("    - Mass is too high")
    elif final_speed < expected_speed * 0.7:
        print("  △ NOTICE: Moderate acceleration loss due to drag/friction (expected).")
    else:
        print("  ✓ Physics appear reasonable!")
    
    print()

if __name__ == "__main__":
    main()
