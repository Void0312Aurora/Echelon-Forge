#!/usr/bin/env python3
"""
Analyze reward function behavior and propose improvements.
"""
import sys
import os
sys.path.insert(0, os.path.abspath("."))

from gym_envs.universal_env import UniversalEnv
import numpy as np

def main():
    print("=" * 70)
    print("REWARD FUNCTION ANALYSIS")
    print("=" * 70)
    
    env = UniversalEnv(scenario_path="scenarios/takeoff.json")
    obs, _ = env.reset(seed=42)
    
    # Test 1: Zero action (baseline)
    print("\n1. ZERO ACTION BASELINE (50 steps)")
    print("-" * 50)
    
    zero_action = np.zeros(17, dtype=np.float32)
    rewards_zero = []
    for i in range(50):
        obs, reward, done, trunc, info = env.step(zero_action)
        rewards_zero.append(reward)
        if done: break
    
    print(f"  Rewards: min={min(rewards_zero):.4f}, max={max(rewards_zero):.4f}, mean={np.mean(rewards_zero):.4f}")
    print(f"  Variance: {np.var(rewards_zero):.6f}")
    
    # Test 2: Full throttle (good action)
    print("\n2. FULL THROTTLE (50 steps)")
    print("-" * 50)
    obs, _ = env.reset(seed=42)
    
    throttle_action = np.zeros(17, dtype=np.float32)
    throttle_action[3] = 1.0  # Full throttle
    
    rewards_throttle = []
    speeds = [0.0]
    for i in range(50):
        obs, reward, done, trunc, info = env.step(throttle_action)
        rewards_throttle.append(reward)
        speeds.append(obs['instruments'][0])
        if done: break
    
    print(f"  Rewards: min={min(rewards_throttle):.4f}, max={max(rewards_throttle):.4f}, mean={np.mean(rewards_throttle):.4f}")
    print(f"  Variance: {np.var(rewards_throttle):.6f}")
    print(f"  Final speed: {speeds[-1]:.1f} m/s")
    
    # Analyze reward components
    print("\n3. REWARD BREAKDOWN (per step)")
    print("-" * 50)
    
    # Assuming dt = 0.05s, at 5 m/s² accel, each step adds ~0.25 m/s
    # speed_progress_weight = 0.05 => reward = 0.25 * 0.05 = 0.0125
    # survival = 0.1 => reward = 0.1
    # Total expected = 0.1125 per step
    
    print("  Expected per step:")
    print("    survival: 0.1")
    print("    speed_progress: d_speed * 0.05")
    print("      At 0.25 m/s increase: 0.25 * 0.05 = 0.0125")
    print("      At 0.5 m/s increase: 0.5 * 0.05 = 0.025")
    print("    altitude_progress: 0 (on ground)")
    print("    Total: ~0.11-0.13")
    print()
    print("  Actual mean reward:", f"{np.mean(rewards_throttle):.4f}")
    
    # Compute actual speed deltas
    speed_deltas = [speeds[i+1] - speeds[i] for i in range(len(speeds)-1)]
    print(f"\n  Speed deltas: mean={np.mean(speed_deltas):.3f}, max={max(speed_deltas):.3f}")
    
    # Key insight
    print("\n4. REWARD SIGNAL DIAGNOSIS")
    print("=" * 70)
    
    signal_strength = np.mean(rewards_throttle) - np.mean(rewards_zero)
    print(f"  Signal strength (throttle - zero): {signal_strength:.4f}")
    
    if signal_strength < 0.05:
        print("  ⚠ WEAK SIGNAL: Difference between good and bad actions is < 0.05")
        print("    Agent will have difficulty learning which actions are better.")
        print()
        print("  RECOMMENDED FIXES:")
        print("    1. INCREASE speed_progress_weight from 0.05 to 0.5 or higher")
        print("    2. ADD velocity reward (not just delta): reward += speed * 0.001")
        print("    3. REDUCE survival baseline to 0.0 (it adds noise, not signal)")
    else:
        print("  ✓ Signal strength appears adequate.")

if __name__ == "__main__":
    main()
