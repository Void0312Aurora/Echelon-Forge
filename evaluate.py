import argparse
import os
import sys
import numpy as np
import time
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv

# Prefer locally built `ef_py` extension when present.
_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
_BUILD_DIR = os.path.join(_REPO_ROOT, "build")
if os.path.isdir(_BUILD_DIR) and any(
    fname.startswith("ef_py") and fname.endswith(".so") for fname in os.listdir(_BUILD_DIR)
):
    sys.path.insert(0, _BUILD_DIR)

# Add local path for gym wrapper
sys.path.insert(0, _REPO_ROOT)
from gym_envs.universal_env import UniversalEnv
from python.models.transformer import TransformerExtractor

def main():
    parser = argparse.ArgumentParser(description="Universal Evaluation for CMO")
    parser.add_argument("--scenario", type=str, required=True, help="Path to JSON scenario file")
    parser.add_argument("--model", type=str, required=True, help="Path to trained model (zip)")
    parser.add_argument("--episodes", type=int, default=10, help="Number of episodes to evaluate")
    parser.add_argument("--render", action="store_true", help="Render simulation (if supported)")
    parser.add_argument(
        "--action_mode",
        type=str,
        default="full",
        choices=["full", "takeoff2", "takeoff4"],
        help="Action space mode (must match training): full=17D, takeoff2=(pitch,throttle), takeoff4=(pitch,roll,rudder,throttle)",
    )
    
    args = parser.parse_args()
    
    scenario_path = os.path.abspath(args.scenario)
    if not os.path.exists(scenario_path):
        print(f"Error: Scenario file not found: {scenario_path}")
        return
        
    print(f"Evaluating Scenario: {scenario_path}")
    print(f"Loading Model: {args.model}")
    
    # Create Env
    def make_env():
        return UniversalEnv(scenario_path, action_mode=args.action_mode)
    
    vec_env = DummyVecEnv([make_env])
    
    # Load Model
    try:
        model_path = args.model
        if model_path.endswith(".zip"):
            model_path = model_path[:-4]
        model = PPO.load(model_path, env=vec_env)
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    # Metrics
    episode_rewards = []
    episode_lengths = []
    success_count = 0
    survival_count = 0
    
    for ep in range(args.episodes):
        obs = vec_env.reset()
        done = False
        total_reward = 0
        steps = 0
        
        # Mission Metrics per episode
        mission_success = False
        survived = True
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, rewards, dones, infos = vec_env.step(action)
            
            total_reward += rewards[0]
            steps += 1
            
            # Check custom metrics from obs or info
            # In our UniversalEnv, we pack mission status into obs["mission"]
            # [dist_to_obj, time_remaining, captured_flag, 0]
            # Since VecEnv wraps obs, we access obs['mission'][0]
            
            # However, for simple success check, we often rely on Termination + High Reward
            # Let's check infos if available, or deduce from reward spike
            
            # Check survival
            # Inferred from Total Reward (Crash usually gives large negative reward)
            
            # Simple check: If High Reward (Capture Bonus = 1000), it's a success
            if rewards[0] >= 500: # Threshold
                mission_success = True
                
            if dones[0]:
                # If we crashed, reward would be very low
                if rewards[0] < -500:
                    survived = False
                done = True
        
        episode_rewards.append(total_reward)
        episode_lengths.append(steps)
        if mission_success:
            success_count += 1
        if survived:
            survival_count += 1
            
        print(f"Episode {ep+1}/{args.episodes}: Reward={total_reward:.2f}, Steps={steps}, Success={mission_success}, Survived={survived}")

    # Summary
    print("\n" + "="*30)
    print("EVALUATION SUMMARY")
    print("="*30)
    print(f"Episodes: {args.episodes}")
    print(f"Mean Reward: {np.mean(episode_rewards):.2f} +/- {np.std(episode_rewards):.2f}")
    print(f"Mean Length: {np.mean(episode_lengths):.2f}")
    print(f"Success Rate: {success_count/args.episodes*100:.1f}%")
    print(f"Survival Rate: {survival_count/args.episodes*100:.1f}%")
    print("="*30)

if __name__ == "__main__":
    main()
