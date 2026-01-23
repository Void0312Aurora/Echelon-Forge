#!/usr/bin/env python3
"""
Debug script using the full environment path to verify zones are properly registered.
Creates environment via UniversalEnv (same as training) and checks terrain.
"""
import sys
import os
sys.path.insert(0, os.path.abspath("."))

from gym_envs.universal_env import UniversalEnv
import numpy as np

def main():
    print("=" * 70)
    print("FULL ENVIRONMENT TERRAIN CHECK")
    print("=" * 70)
    
    env = UniversalEnv(scenario_path="scenarios/takeoff.json")
    obs, _ = env.reset(seed=42)
    
    print("\n1. INITIAL STATE")
    print("-" * 50)
    pos = env.sim.get_unit_position(env.agent_id)
    print(f"  Aircraft position: ({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})")
    
    # Run 100 steps with full throttle and log speed
    print("\n2. PHYSICS TRACE (100 steps @ full throttle)")
    print("-" * 50)
    
    action = np.zeros(17, dtype=np.float32)
    action[3] = 1.0  # Full throttle
    action[4] = 1.0  # Gear down
    
    speeds = []
    positions = []
    
    for i in range(100):
        obs, reward, done, trunc, info = env.step(action)
        pos = env.sim.get_unit_position(env.agent_id)
        speed = obs['instruments'][0]  # IAS
        speeds.append(speed)
        positions.append(pos[0])
        
        if i in [0, 9, 19, 49, 99]:
            print(f"  Step {i+1}: x={pos[0]:.1f}, speed={speed:.1f} m/s")
        
        if done:
            print(f"  TERMINATED at step {i+1}")
            break
    
    # Calculate acceleration
    if len(speeds) > 10:
        dt = env.sim.get_time_step()
        accel = (speeds[-1] - speeds[0]) / (len(speeds) * dt)
        print(f"\n  Average acceleration: {accel:.1f} m/s²")
    
    # Expected values
    print("\n3. ANALYSIS")
    print("-" * 50)
    
    expected_thrust = 76310.0  # N (mil)
    mass = 8570.0 + 3175.0  # Empty + fuel
    expected_accel_no_friction = expected_thrust / mass  # ~6.5 m/s²
    
    # With friction on Concrete (mu=0.02):
    friction_concrete = 0.02 * mass * 9.8  # ~2300 N
    expected_accel_concrete = (expected_thrust - friction_concrete) / mass  # ~6.3 m/s²
    
    # With friction on SoftDirt (mu=0.15):
    friction_dirt = 0.15 * mass * 9.8  # ~17200 N
    expected_accel_dirt = (expected_thrust - friction_dirt) / mass  # ~5.0 m/s²
    
    print(f"  Expected accel (no friction): {expected_accel_no_friction:.1f} m/s²")
    print(f"  Expected accel (Concrete mu=0.02): {expected_accel_concrete:.1f} m/s²")
    print(f"  Expected accel (SoftDirt mu=0.15): {expected_accel_dirt:.1f} m/s²")
    print(f"  Actual accel: {accel:.1f} m/s²")
    
    # Diagnosis
    print("\n4. DIAGNOSIS")
    print("=" * 70)
    
    if accel > expected_accel_concrete * 0.8:
        print("  ✓ Acceleration matches Concrete terrain. Zones are working!")
    elif accel > expected_accel_dirt * 0.8:
        print("  ⚠ Acceleration matches SoftDirt terrain.")
        print("    Aircraft is NOT on Runway zone!")
        print("    Check: spawn position, zone geometry, zone registration order.")
    else:
        print("  ✗ Acceleration is very low. Check:")
        print("    - Propulsion component values")
        print("    - Ground contact system")
        print("    - Brake state")

if __name__ == "__main__":
    main()
