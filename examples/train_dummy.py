import sys
import os
import gymnasium as gym
import numpy as np

# Add src to path so we can import env.cmo_env
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "src")))

from env.cmo_env import CMOEnv

def main():
    print("Initializing CMO Gym Environment...")
    env = CMOEnv()
    
    obs, _ = env.reset(seed=123)
    print(f"Initial Observation: {obs}")
    
    total_reward = 0.0
    steps = 0
    terminated = False
    truncated = False
    
    print("Starting Dummy Agent Loop...")
    while not (terminated or truncated) and steps < 100:
        # Random Action
        action = env.action_space.sample()
        
        # Step
        obs, reward, terminated, truncated, info = env.step(action)
        
        total_reward += reward
        steps += 1
        
        if steps % 10 == 0:
            print(f"Step {steps}: Obs={obs[:3]}... Reward={reward:.4f} Total={total_reward:.4f}")
            
    print(f"Episode Finished in {steps} steps. Total Reward: {total_reward:.4f}")
    if terminated:
        print("Result: TERMINATED (Success/Fail Condition Met)")
    else:
        print("Result: TRUNCATED (Max Steps Reached)")

if __name__ == "__main__":
    main()
