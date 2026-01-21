import argparse
import os
import sys
import json
import shutil
from datetime import datetime

import torch
# Enable TF32 for Ampere+ GPUs (significant speedup and memory savings)
torch.set_float32_matmul_precision('high')

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import CheckpointCallback

# Add local path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from gym_envs.universal_env import UniversalEnv
from python.models.transformer import TransformerExtractor

def get_policy_kwargs(train_config):
    # Parse policy_kwargs from JSON
    kwargs = train_config.get("hyperparameters", {}).get("policy_kwargs", {})
    
    # Check for custom features_extractor
    fe_name = kwargs.get("features_extractor_class")
    if fe_name == "TransformerExtractor":
        kwargs["features_extractor_class"] = TransformerExtractor
    
    return kwargs

def main():
    parser = argparse.ArgumentParser(description="Universal Training Base for CMO")
    parser.add_argument("--scenario", type=str, required=True, help="Path to JSON scenario file")
    parser.add_argument("--train_config", type=str, default="examples/config/training/default_ppo.json", help="Path to training config JSON")
    parser.add_argument("--test_only", action="store_true", help="Run in test mode without training")
    
    # New Experiment Args
    parser.add_argument("--run_name", type=str, default=None, help="Name of the run. If None, uses Timestamp.")
    parser.add_argument("--resume_path", type=str, default=None, help="Path to .zip model to resume training from.")
    parser.add_argument("--output_base", type=str, default="experiments", help="Base directory for experiments.")
    parser.add_argument("--n_envs", type=int, default=None, help="Number of parallel environments (overrides config)")
    
    args = parser.parse_args()
    
    # 1. Load Paths
    scenario_path = os.path.abspath(args.scenario)
    if not os.path.exists(scenario_path):
        print(f"Error: Scenario file not found: {scenario_path}")
        return

    train_cfg_path = os.path.abspath(args.train_config)
    if not os.path.exists(train_cfg_path):
        print(f"Error: Training config not found: {train_cfg_path}")
        return
        
    with open(train_cfg_path, 'r') as f:
        train_config = json.load(f)

    # 2. Setup Experiment Directory
    exp_dir = ""
    run_name = ""
    
    if args.resume_path:
        # Resume Mode: Use existing directory structure
        if not os.path.exists(args.resume_path):
            print(f"Error: Cannot resume, file not found: {args.resume_path}")
            return
        
        # Assume standard structure: experiments/run_name/checkpoints/model.zip or experiments/run_name/model.zip
        # We try to deduce the experiment root
        abs_resume = os.path.abspath(args.resume_path)
        parent_dir = os.path.dirname(abs_resume)
        
        if os.path.basename(parent_dir) == "checkpoints":
            exp_dir = os.path.dirname(parent_dir)
        else:
            exp_dir = parent_dir
            
        run_name = os.path.basename(exp_dir)
        print(f"Resuming Experiment: {run_name} at {exp_dir}")
        
    else:
        # New Run Mode
        if args.run_name:
            run_name = args.run_name
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            cfg_name = os.path.splitext(os.path.basename(train_cfg_path))[0]
            run_name = f"{timestamp}_{cfg_name}"
            
        exp_dir = os.path.join(args.output_base, run_name)
        
        # Check for existing interrupted model in this run folder
        interrupted_path = os.path.join(exp_dir, "checkpoints", "interrupted_model.zip")
        if os.path.exists(interrupted_path):
            print(f"Found interrupted checkpoint at {interrupted_path}")
            print("Auto-resuming from interrupted checkpoint...")
            args.resume_path = interrupted_path
        else:
            os.makedirs(exp_dir, exist_ok=True)
            print(f"Starting New Experiment: {run_name} at {exp_dir}")
        
        # Backup config
        shutil.copy(train_cfg_path, os.path.join(exp_dir, "train_config_backup.json"))
        shutil.copy(scenario_path, os.path.join(exp_dir, "scenario_backup.json"))

    # Directory Sub-structure
    ckpt_dir = os.path.join(exp_dir, "checkpoints")
    log_dir = os.path.join(exp_dir, "logs")
    os.makedirs(ckpt_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    # 3. Environment Setup
    n_envs = args.n_envs if args.n_envs is not None else train_config.get("n_envs", 1)
    
    print(f"Creating {n_envs} parallel environments...")
    print(f"Logging to {log_dir}")
    
    # We must delay env creation for resume if we want to ensure same config? 
    # For now we assume user provides correct params for resumption.
    vec_cls = SubprocVecEnv if n_envs > 1 else DummyVecEnv
    vec_env = make_vec_env(
        UniversalEnv,
        n_envs=n_envs,
        env_kwargs={"scenario_path": scenario_path},
        vec_env_cls=vec_cls
    )
    
    # Test Mode
    if args.test_only:
        if not args.resume_path:
            # Try to find 'final_model.zip' in exp_dir if just run_name provided
            possible_path = os.path.join(exp_dir, "final_model.zip")
            if os.path.exists(possible_path):
                load_path = possible_path
            else:
                print("Error: --test_only requires --resume_path or a valid existing run directory with final_model.zip")
                return
        else:
            load_path = args.resume_path
            
        print(f"Loading model for testing: {load_path}")
        model = PPO.load(load_path, env=vec_env)
        
        obs = vec_env.reset()
        for i in range(1000):
            action, _ = model.predict(obs)
            obs, rewards, dones, info = vec_env.step(action)
            if i % 100 == 0:
                print(f"Step {i}: Reward={rewards[0]:.2f}")
            if dones[0]:
                print("Episode Done.")
                obs = vec_env.reset()
        return

    # 4. Training Setup
    hyperparams = train_config.get("hyperparameters", {})
    total_timesteps = train_config.get("total_timesteps", 100000)
    save_freq = train_config.get("save_freq", 50000)

    # Feature Extractor Logic
    if "policy_kwargs" in hyperparams:
        p_kwargs = hyperparams["policy_kwargs"]
        if p_kwargs.get("features_extractor_class") == "TransformerExtractor":
            print("Using Transformer Feature Extractor")
            p_kwargs["features_extractor_class"] = TransformerExtractor

    if args.resume_path:
        print(f"Loading Checkpoint: {args.resume_path}")
        # Note: When loading, we might want to override env? PPO.load handles it.
        # But we must ensure hyperparameters match if we want to continue seamlessly?
        # PPO.load loads params from zip. The CLI hyperparams might be ignored? 
        # Yes, SB3 load Overwrites params. But we can pass custom_objects.
        # For simple resume, PPO.load is enough.
        model = PPO.load(args.resume_path, env=vec_env, tensorboard_log=log_dir, **hyperparams) 
        # Warning: passing hyperparams to load might error if they conflict with saved ones differently.
        # usually load(path, env=env) uses saved params.
        # But we want to use the NEW config if changed? No, resume implies continuing.
        # Let's just load.
        # Re-attaching tensorboard log is tricky. we need specific call.
    else:
        policy_name = train_config.get("policy", "MultiInputPolicy")
        model = PPO(policy_name, vec_env, verbose=1, tensorboard_log=log_dir, **hyperparams)
    
    print(f"Starting Training for {total_timesteps} steps...")
    
    checkpoint_callback = CheckpointCallback(
        save_freq=save_freq, 
        save_path=ckpt_dir,
        name_prefix="model" # naming: model_50000_steps.zip
    )
    
    try:
        # If resuming, we might want to adjust total_timesteps? 
        # reset_num_timesteps=False allows continuing TB logs seamlessly
        model.learn(total_timesteps=total_timesteps, callback=checkpoint_callback, reset_num_timesteps=(not args.resume_path))
        
        final_path = os.path.join(exp_dir, "final_model")
        print(f"Saving final model to {final_path}")
        model.save(final_path)
        print("Training Complete.")
        
    except KeyboardInterrupt:
        print("\nTraining Interrupted by User!")
        save_path = os.path.join(ckpt_dir, "interrupted_model")
        print(f"Saving emergency checkpoint to {save_path}...")
        model.save(save_path)
        print("Done.")
        sys.exit(0)

if __name__ == "__main__":
    main()
