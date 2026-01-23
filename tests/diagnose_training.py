#!/usr/bin/env python3
"""
Diagnostic script to check training environment health.
Verifies: action mapping, observation flow, reward signals, and physics response.
"""
import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath("."))

from gym_envs.universal_env import UniversalEnv

def main():
    print("=" * 70)
    print("TRAINING ENVIRONMENT DIAGNOSTIC")
    print("=" * 70)
    
    env = UniversalEnv(scenario_path="scenarios/takeoff.json")
    obs, _ = env.reset(seed=42)
    
    print("\n1. INITIAL STATE")
    print("-" * 50)
    print(f"  Position: x={env.sim.get_unit_position(env.agent_id)[0]:.1f}, "
          f"y={env.sim.get_unit_position(env.agent_id)[1]:.1f}, "
          f"z={env.sim.get_unit_position(env.agent_id)[2]:.1f}")
    print(f"  Heading: {env.sim.get_unit_heading(env.agent_id):.1f} deg")
    print(f"  Speed (from obs): {obs['instruments'][0]:.1f} m/s (IAS)")
    print(f"  Alt (from obs): {obs['instruments'][2]:.1f} m (Baro)")
    print(f"  Throttle observation: {obs['instruments'][15]:.2f}") # engine_rpm
    
    print("\n2. ACTION SPACE")
    print("-" * 50)
    print(f"  Shape: {env.action_space.shape}")
    print(f"  Low: {env.action_space.low[:4]}...") 
    print(f"  High: {env.action_space.high[:4]}...")
    
    # Test 1: Zero action (should maintain position or sink gently)
    print("\n3. TEST: ZERO ACTION (10 steps)")
    print("-" * 50)
    zero_action = np.zeros(17, dtype=np.float32)
    zero_action[3] = 0.0  # Zero throttle
    
    cum_reward_zero = 0.0
    for i in range(10):
        obs, reward, done, trunc, info = env.step(zero_action)
        cum_reward_zero += reward
        if i == 0 or i == 9:
            pos = env.sim.get_unit_position(env.agent_id)
            print(f"  Step {i+1}: pos=({pos[0]:.1f},{pos[1]:.1f},{pos[2]:.1f}), "
                  f"speed={obs['instruments'][0]:.1f}, reward={reward:.3f}")
        if done:
            print(f"  TERMINATED at step {i+1}!")
            break
    print(f"  Total reward (zero action): {cum_reward_zero:.2f}")
    
    # Test 2: Full throttle (should accelerate)
    print("\n4. TEST: FULL THROTTLE (20 steps)")
    print("-" * 50)
    obs, _ = env.reset(seed=42)
    
    full_throttle = np.zeros(17, dtype=np.float32)
    full_throttle[3] = 1.0  # Full throttle
    
    cum_reward_throttle = 0.0
    initial_speed = obs['instruments'][0]
    for i in range(20):
        obs, reward, done, trunc, info = env.step(full_throttle)
        cum_reward_throttle += reward
        if i == 0 or i == 9 or i == 19:
            pos = env.sim.get_unit_position(env.agent_id)
            print(f"  Step {i+1}: pos=({pos[0]:.1f},{pos[1]:.1f},{pos[2]:.1f}), "
                  f"speed={obs['instruments'][0]:.1f}, reward={reward:.3f}")
        if done:
            print(f"  TERMINATED at step {i+1}!")
            break
    final_speed = obs['instruments'][0]
    print(f"  Speed change: {initial_speed:.1f} -> {final_speed:.1f} m/s")
    print(f"  Total reward (full throttle): {cum_reward_throttle:.2f}")
    
    # Test 3: Random actions to see variance
    print("\n5. TEST: RANDOM ACTIONS (50 steps)")
    print("-" * 50)
    obs, _ = env.reset(seed=42)
    
    rewards = []
    speeds = []
    for i in range(50):
        action = env.action_space.sample()
        action[3] = np.clip(action[3], 0.8, 1.0)  # Keep throttle high
        obs, reward, done, trunc, info = env.step(action)
        rewards.append(reward)
        speeds.append(obs['instruments'][0])
        if done:
            print(f"  TERMINATED at step {i+1}!")
            break
    
    print(f"  Reward stats: min={min(rewards):.2f}, max={max(rewards):.2f}, mean={np.mean(rewards):.2f}")
    print(f"  Speed stats: min={min(speeds):.1f}, max={max(speeds):.1f}, final={speeds[-1]:.1f}")
    
    # Analysis
    print("\n" + "=" * 70)
    print("DIAGNOSIS")
    print("=" * 70)
    
    issues = []
    
    if abs(final_speed - initial_speed) < 1.0:
        issues.append("CRITICAL: Throttle has NO EFFECT on speed! Check thrust mapping.")
    
    if cum_reward_throttle <= cum_reward_zero:
        issues.append("WARNING: Full throttle reward <= zero action reward. Check reward shaping.")
        
    if max(rewards) - min(rewards) < 0.1:
        issues.append("WARNING: Reward variance is very low. Agent may receive no learning signal.")
    
    if len(issues) == 0:
        print("  ✓ No obvious issues detected. Environment seems responsive.")
    else:
        for issue in issues:
            print(f"  ✗ {issue}")
    
    print()

if __name__ == "__main__":
    main()
