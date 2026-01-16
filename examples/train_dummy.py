import gymnasium as gym
import sys
import os
import numpy as np

# Ensure we can find the env
sys.path.append(os.getcwd())
from examples.gym_env.echelon_env import EchelonForgeEnv

def test_env():
    print("Initializing Environment...")
    env = EchelonForgeEnv()
    
    print("Resetting Environment...")
    obs, info = env.reset()
    print(f"Initial Obs: {obs}")
    
    # Test random actions
    print("Running random steps...")
    for i in range(10):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        print(f"Step {i}: Action={action}, Reward={reward:.4f}, Term={terminated}, Trunc={truncated}")
        print(f"       Obs: {obs}")
        
    print("Test Complete.")

if __name__ == "__main__":
    test_env()
