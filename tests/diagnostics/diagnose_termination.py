#!/usr/bin/env python3
"""
Diagnose early termination in training episodes.
Runs a few steps with random actions and prints termination reason.
"""
import sys
import os

from python.testing.runtime import ensure_repo_imports

REPO_ROOT = ensure_repo_imports()
os.chdir(REPO_ROOT)

import numpy as np
from gym_envs.universal_env import UniversalEnv

def diagnose_termination():
    env = UniversalEnv(scenario_path="scenarios/takeoff/takeoff.json")
    
    print("=" * 60)
    print("Episode Termination Diagnosis")
    print("=" * 60)
    
    obs, _ = env.reset(seed=42)
    
    for step in range(10):
        # Random action (exploration)
        action = env.action_space.sample()
        
        obs, reward, terminated, truncated, info = env.step(action)
        
        inst = obs["instruments"]
        print(f"Step {step+1}:")
        print(f"  Alt: {inst[2]:.1f}m, Speed: {inst[0]:.1f}m/s")
        print(f"  AoA: {inst[5]:.1f}°, Pitch: {inst[7]:.1f}°, Roll: {inst[8]:.1f}°")
        print(f"  Reward: {reward:.2f}, Terminated: {terminated}")
        
        if terminated:
            print(f"\n*** TERMINATED at step {step+1} ***")
            if abs(inst[5]) > 50.0:
                print("  Cause: AoA > 50° (Deep Stall)")
            elif abs(inst[7]) > 85.0:
                print("  Cause: Pitch > 85° (Extreme Pitch)")
            elif inst[2] < 100.0 and abs(inst[8]) > 135.0:
                print("  Cause: Roll > 135° at low altitude")
            else:
                print("  Cause: Unknown (likely health <= 0, crash)")
            break
    
    print("=" * 60)

if __name__ == "__main__":
    diagnose_termination()
