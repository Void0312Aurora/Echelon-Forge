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
from stable_baselines3.common.callbacks import CallbackList, CheckpointCallback

# Prefer the locally built `ef_py` extension when present (avoids accidentally using a stale
# site-packages wheel/so from the venv).
_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
_BUILD_DIR = os.path.join(_REPO_ROOT, "build")
if os.path.isdir(_BUILD_DIR):
    for _name in ("ef_py", "ef_py.cpython-313-x86_64-linux-gnu.so"):
        if os.path.exists(os.path.join(_BUILD_DIR, _name)) or any(
            fname.startswith("ef_py") and fname.endswith(".so") for fname in os.listdir(_BUILD_DIR)
        ):
            sys.path.insert(0, _BUILD_DIR)
            break

# Add local path
sys.path.insert(0, _REPO_ROOT)
from gym_envs.universal_env import UniversalEnv
from python.models.transformer import TransformerExtractor, TransformerVisualExtractor
from python.training_callbacks import CMODiagnosticsCallback, ScenarioCurriculumCallback
from python.rl.ppo_adaptive_kl import AdaptiveKLPPO
from python.rl.policies import SquashedMultiInputPolicy
from python.rl.wrappers import MultiTimescaleActionWrapper

def get_policy_kwargs(train_config):
    # Parse policy_kwargs from JSON
    kwargs = train_config.get("hyperparameters", {}).get("policy_kwargs", {})
    
    # Check for custom features_extractor
    fe_name = kwargs.get("features_extractor_class")
    if fe_name == "TransformerExtractor":
        kwargs["features_extractor_class"] = TransformerExtractor
    elif fe_name == "TransformerVisualExtractor":
        kwargs["features_extractor_class"] = TransformerVisualExtractor
    
    return kwargs


def apply_safe_action_bias(model: PPO, action_mode: str):
    """
    Improve early exploration for mixed-range action spaces.

    SB3 PPO uses an (unbounded) Gaussian policy. For dimensions with bounds [0, 1],
    the default mean initialization at 0.0 tends to clip to 0.0 (e.g. throttle=0),
    which can trap learning in the "stationary on runway" regime. We bias those
    outputs toward realistic neutral/safe defaults.
    """
    if action_mode != "full":
        return
    try:
        action_net = getattr(model.policy, "action_net", None)
        if action_net is None or getattr(action_net, "bias", None) is None:
            return
        b = action_net.bias
        if b is None or int(b.shape[0]) < 17:
            return
        squash = bool(getattr(model.policy, "squash_output", False))
        with torch.no_grad():
            # Safe defaults for the 17D "full" action layout in `gym_envs/universal_env.py`.
            # - throttle: enough power to start ground roll
            # - gear: down
            # - keep brakes/speedbrake/flaps and combat switches off by default
            if squash:
                # With tanh-squash + unscale, bias=0 maps to the midpoint of [low,high].
                # Push "off" switches below 0.5 by using negative pre-squash means.
                b[3] = 1.5   # throttle -> ~0.95 after tanh+unscale (realistic takeoff power)
                b[4] = 2.0   # gear down  -> ~0.98 after tanh+unscale

                off_pre = -2.0
                for idx in (5, 6, 7, 8, 9, 12, 13, 14, 15, 16):
                    b[idx] = off_pre
            else:
                # Unbounded Gaussian + clip: bias directly corresponds to env action value.
                b[3] = 0.5   # throttle
                b[4] = 1.0   # gear down
                for idx in (5, 6, 7, 8, 9, 12, 13, 14, 15, 16):
                    b[idx] = 0.0
    except Exception:
        return

def main():
    parser = argparse.ArgumentParser(description="Universal Training Base for CMO")
    parser.add_argument("--scenario", type=str, required=True, help="Path to JSON scenario file")
    parser.add_argument("--train_config", type=str, default="examples/config/training/default_ppo.json", help="Path to training config JSON")
    parser.add_argument("--test_only", action="store_true", help="Run in test mode without training")
    parser.add_argument("--include_visual", action="store_true", help="Include ARB visual observation (large/slow)")
    parser.add_argument(
        "--action_mode",
        type=str,
        default="full",
        choices=["full", "takeoff2", "takeoff4"],
        help="Action space mode (curriculum): full=17D, takeoff2=(pitch,throttle), takeoff4=(pitch,roll,rudder,throttle)",
    )
    
    # New Experiment Args
    parser.add_argument("--run_name", type=str, default=None, help="Name of the run. If None, uses Timestamp.")
    parser.add_argument("--resume_path", type=str, default=None, help="Path to .zip model to resume training from.")
    parser.add_argument("--output_base", type=str, default="experiments", help="Base directory for experiments.")
    parser.add_argument("--n_envs", type=int, default=None, help="Number of parallel environments (overrides config)")
    parser.add_argument("--diagnostics", action="store_true", help="Log extra diagnostics scalars to TensorBoard")
    parser.add_argument(
        "--diagnostics_every",
        type=int,
        default=50000,
        help="Diagnostics logging interval (in environment timesteps, not gradient updates)",
    )
    parser.add_argument(
        "--no_init_safe_action_bias",
        action="store_true",
        help="Disable safe initialization bias for mixed-range actions (throttle/brakes/flaps/etc).",
    )
    
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

    # Rough rollout-buffer memory warning for visual observations (DictRolloutBuffer stores full obs).
    try:
        n_steps = int(train_config.get("hyperparameters", {}).get("n_steps", 2048))
    except Exception:
        n_steps = 2048
    if args.include_visual:
        visual_elems = 48 * 96 * 10
        est_bytes = int(n_envs) * int(n_steps) * int(visual_elems) * 4
        if est_bytes >= 4 * 1024**3:
            gib = est_bytes / (1024**3)
            print(
                f"[WARN] include_visual=True with n_envs={n_envs}, n_steps={n_steps} will allocate ~{gib:.1f} GiB "
                "just for the visual rollout buffer. Consider reducing n_envs and/or n_steps."
            )
    
    # We must delay env creation for resume if we want to ensure same config? 
    # For now we assume user provides correct params for resumption.
    vec_cls = SubprocVecEnv if n_envs > 1 else DummyVecEnv

    wrapper_class = None
    wrapper_kwargs = None
    wrappers_cfg = train_config.get("wrappers", {}) if isinstance(train_config.get("wrappers", {}), dict) else {}
    mts_cfg = wrappers_cfg.get("multi_timescale_action")
    if isinstance(mts_cfg, dict) and bool(mts_cfg.get("enabled", False)):
        wrapper_class = MultiTimescaleActionWrapper
        wrapper_kwargs = {
            "hold_steps": int(mts_cfg.get("hold_steps", 4)),
            "low_freq_indices": mts_cfg.get(
                "low_freq_indices",
                # Do NOT include brakes in low-frequency indices: they are analog and needed for fine control.
                [4, 5, 6, 9, 12, 13, 14, 15, 16],
            ),
            "snap_binary_indices": mts_cfg.get(
                "snap_binary_indices",
                # Do NOT snap brakes to {0,1}: it turns small exploration noise into full braking.
                [4, 9, 12, 13, 14, 15],
            ),
            "action_rate_penalty_coef": float(mts_cfg.get("action_rate_penalty_coef", 0.0)),
        }

    vec_env = make_vec_env(
        UniversalEnv,
        n_envs=n_envs,
        env_kwargs={
            "scenario_path": scenario_path,
            "include_visual": args.include_visual,
            "action_mode": args.action_mode,
        },
        vec_env_cls=vec_cls,
        wrapper_class=wrapper_class,
        wrapper_kwargs=wrapper_kwargs,
    )

    curriculum_cfg = train_config.get("curriculum", {}) if isinstance(train_config.get("curriculum", {}), dict) else {}
    algo_name = str(train_config.get("algo", "PPO"))
    algo_cls = PPO
    if algo_name in ("AdaptiveKLPPO", "PPOAdaptiveKL", "PPO_AdaptiveKL"):
        algo_cls = AdaptiveKLPPO

    # Apply curriculum stage 0 *before* SB3 does its initial env.reset() inside learn().
    if isinstance(curriculum_cfg, dict) and curriculum_cfg.get("stages"):
        try:
            st0 = list(curriculum_cfg["stages"])[0]
            overrides0 = st0.get("randomization_overrides", st0.get("randomization", {}))
            vec_env.env_method("set_randomization_overrides", overrides0)
        except Exception as e:
            print(f"[WARN] failed to apply initial curriculum stage overrides: {e}")
    
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
        model = algo_cls.load(load_path, env=vec_env)
        
        obs = vec_env.reset()
        for i in range(1000):
            action, _ = model.predict(obs, deterministic=True)
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
        elif p_kwargs.get("features_extractor_class") == "TransformerVisualExtractor":
            print("Using Transformer+Visual Feature Extractor")
            p_kwargs["features_extractor_class"] = TransformerVisualExtractor

    if args.resume_path:
        print(f"Loading Checkpoint: {args.resume_path}")
        model = algo_cls.load(args.resume_path, env=vec_env, tensorboard_log=log_dir)
    else:
        policy_name = train_config.get("policy", "MultiInputPolicy")
        policy_cls = policy_name
        if policy_name == "SquashedMultiInputPolicy":
            policy_cls = SquashedMultiInputPolicy
        model = algo_cls(policy_cls, vec_env, verbose=1, tensorboard_log=log_dir, **hyperparams)
        if not args.no_init_safe_action_bias:
            apply_safe_action_bias(model, args.action_mode)
    
    print(f"Starting Training for {total_timesteps} steps...")
    
    checkpoint_callback = CheckpointCallback(
        save_freq=save_freq, 
        save_path=ckpt_dir,
        name_prefix="model" # naming: model_50000_steps.zip
    )
    callbacks = [checkpoint_callback]
    if args.diagnostics:
        callbacks.append(CMODiagnosticsCallback(log_every_timesteps=int(args.diagnostics_every)))
    if isinstance(curriculum_cfg, dict) and curriculum_cfg.get("stages"):
        callbacks.append(
            ScenarioCurriculumCallback(
                stages=list(curriculum_cfg["stages"]),
                check_freq=int(curriculum_cfg.get("check_freq", 10_000)),
            )
        )
    callback = CallbackList(callbacks) if len(callbacks) > 1 else checkpoint_callback
    
    try:
        # If resuming, we might want to adjust total_timesteps? 
        # reset_num_timesteps=False allows continuing TB logs seamlessly
        model.learn(total_timesteps=total_timesteps, callback=callback, reset_num_timesteps=(not args.resume_path))
        
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
