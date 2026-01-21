#!/usr/bin/env python3
"""
Debug Aero State Test
Checks if dynamic_pressure is being calculated correctly.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gym_envs.universal_env import UniversalEnv
import numpy as np

def main():
    env = UniversalEnv("scenarios/takeoff.json")
    obs, _ = env.reset()
    
    print("="*60)
    print("DEBUG AERO STATE")
    print("="*60)
    
    for step in range(200):
        inst = obs["instruments"]
        
        # Build action (17 dims) - full throttle
        action = np.zeros(17, dtype=np.float32)
        action[3] = 1.0  # Throttle
        action[4] = 1.0  # Gear down
        
        obs, reward, terminated, truncated, info = env.step(action)
        truth = env.sim.get_agent_observation(env.agent_id)
        
        # Get instrument values
        ias = inst[0]   # IAS
        mach = inst[1]  # Mach
        alt = inst[2]   # Alt
        aoa = inst[5]   # AoA
        
        if step % 20 == 0:
            print(f"[Step {step:3d}]")
            print(f"  Truth: vx={truth.vx:.2f}, vy={truth.vy:.2f}, vz={truth.vz:.2f}, speed={truth.speed:.2f}")
            print(f"  Obs:   IAS={ias:.2f}, Mach={mach:.4f}, Alt={alt:.2f}, AoA={aoa:.2f}")
            print()
        
        if terminated:
            print("Episode terminated.")
            break

if __name__ == "__main__":
    main()
