#!/usr/bin/env python3
"""
Diagnose why ep_rew_mean is -3920 (should be ~85).
Hypothesis: on_runway flag is incorrectly returning False.
"""
import sys
import os

from python.testing.runtime import ensure_repo_imports

REPO_ROOT = ensure_repo_imports()
os.chdir(REPO_ROOT)

from gym_envs.universal_env import UniversalEnv
import numpy as np

def main():
    print("=" * 70)
    print("REWARD BREAKDOWN DIAGNOSIS")
    print("=" * 70)
    
    env = UniversalEnv(scenario_path="scenarios/takeoff/takeoff.json")
    obs, _ = env.reset(seed=42)
    
    # Check initial state
    inst = env.sim.get_instrument_state(env.agent_id)
    print("\n1. INITIAL STATE")
    print("-" * 50)
    print(f"  on_runway: {getattr(inst, 'on_runway', 'N/A')}")
    print(f"  gear_stress: {getattr(inst, 'gear_stress', 'N/A')}")
    print(f"  gear_collapsed: {getattr(inst, 'gear_collapsed', 'N/A')}")
    print(f"  lat: {getattr(inst, 'lat', 'N/A')}")
    print(f"  lon: {getattr(inst, 'lon', 'N/A')}")
    
    # Test a few steps with throttle
    print("\n2. STEP-BY-STEP ANALYSIS (10 steps)")
    print("-" * 50)
    
    action = np.zeros(17, dtype=np.float32)
    action[3] = 1.0  # Full throttle
    
    total_reward = 0.0
    for i in range(10):
        obs, reward, done, trunc, info = env.step(action)
        total_reward += reward
        
        inst = env.sim.get_instrument_state(env.agent_id)
        truth = env.sim.get_agent_observation(env.agent_id)
        
        on_rwy = getattr(inst, 'on_runway', 'N/A')
        gear_stress = getattr(inst, 'gear_stress', 0.0)
        
        print(f"  Step {i+1}: reward={reward:+.2f}, on_runway={on_rwy}, "
              f"stress={gear_stress:.3f}, z={truth.z:.2f}")
        
        if done:
            print(f"  TERMINATED at step {i+1}")
            break
    
    print(f"\n  Sum of first 10 rewards: {total_reward:.2f}")
    print(f"  Expected if off_runway: ~{-2.0 * 10}")
    
    # Run longer to see total
    print("\n3. FULL EPISODE (100 steps)")
    print("-" * 50)
    
    obs, _ = env.reset(seed=42)
    total_reward = 0.0
    on_runway_count = 0
    off_runway_count = 0
    
    for i in range(100):
        obs, reward, done, trunc, info = env.step(action)
        total_reward += reward
        
        inst = env.sim.get_instrument_state(env.agent_id)
        on_rwy = getattr(inst, 'on_runway', True)
        
        if on_rwy:
            on_runway_count += 1
        else:
            off_runway_count += 1
        
        if done:
            print(f"  TERMINATED at step {i+1}")
            break
    
    print(f"  Total reward (100 steps): {total_reward:.2f}")
    print(f"  On-runway steps: {on_runway_count}")
    print(f"  Off-runway steps: {off_runway_count}")
    print(f"  Expected reward if always on-runway: ~{0.01 * 100}")
    print(f"  Expected reward if always off-runway: ~{-2.0 * 100}")
    
    print()

if __name__ == "__main__":
    main()
