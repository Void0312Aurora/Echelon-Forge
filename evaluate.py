import argparse
import json
import os
import time

from python.runtime_bootstrap import configure_repo_imports


configure_repo_imports()

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv

from python.env_config import resolve_env_settings
from python.training.cli import ACTION_MODE_CHOICES, MISSION_OBS_MODE_CHOICES
from python.rl.policy_algo.ppo_adaptive_kl import AdaptiveKLPPO
from python.rl.control.wrappers import get_action_wrapper_spec
from python.rl.runtime.single_world_batch_runtime import build_single_world_batch_execution_runtime


def _build_evaluation_env(
    scenario_path: str,
    env_settings: dict,
    *,
    wrapper_class=None,
    wrapper_kwargs: dict | None = None,
    worker_threads: int | None = None,
):
    runtime = build_single_world_batch_execution_runtime(
        scenario_path=os.path.abspath(scenario_path),
        env_settings=dict(env_settings),
        wrapper_class=wrapper_class,
        wrapper_kwargs=wrapper_kwargs,
        worker_threads=worker_threads,
    )
    return runtime.policy_env

def main():
    parser = argparse.ArgumentParser(description="Universal Evaluation for CMO")
    parser.add_argument("--scenario", type=str, required=True, help="Path to JSON scenario file")
    parser.add_argument("--model", type=str, required=True, help="Path to trained model (zip)")
    parser.add_argument(
        "--algo",
        type=str,
        default="PPO",
        choices=["PPO", "AdaptiveKLPPO", "PPOAdaptiveKL", "PPO_AdaptiveKL"],
        help="Algorithm class used during training (must match checkpoint class).",
    )
    parser.add_argument("--episodes", type=int, default=10, help="Number of episodes to evaluate")
    parser.add_argument("--seed", type=int, default=None, help="Optional seed for reproducible episode randomization")
    parser.add_argument("--render", action="store_true", help="Render simulation (if supported)")
    parser.add_argument(
        "--include_visual",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Include visual observation in evaluation env (defaults to train_config/policy settings).",
    )
    parser.add_argument(
        "--include_proprio",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Include previous action in observations (defaults to train_config env settings).",
    )
    parser.add_argument(
        "--mission_obs_mode",
        type=str,
        default=None,
        choices=MISSION_OBS_MODE_CHOICES,
        help="Mission observation format (defaults to train_config env settings).",
    )
    parser.add_argument(
        "--visual_downsample",
        type=int,
        default=None,
        help="Visual downsample factor (defaults to train_config env settings).",
    )
    parser.add_argument(
        "--visual_update_interval",
        type=int,
        default=None,
        help="Visual refresh interval (defaults to train_config env settings).",
    )
    parser.add_argument(
        "--action_mode",
        type=str,
        default=None,
        choices=ACTION_MODE_CHOICES,
        help="Action space mode (defaults to train_config env settings).",
    )
    parser.add_argument(
        "--train_config",
        type=str,
        default=None,
        help="Optional training config JSON to apply the same action wrapper semantics used during training.",
    )
    
    args = parser.parse_args()

    if args.seed is not None:
        np.random.seed(int(args.seed))
    
    scenario_path = os.path.abspath(args.scenario)
    if not os.path.exists(scenario_path):
        print(f"Error: Scenario file not found: {scenario_path}")
        return
        
    print(f"Evaluating Scenario: {scenario_path}")
    print(f"Loading Model: {args.model}")

    train_config = None
    if args.train_config:
        cfg_path = os.path.abspath(args.train_config)
        if not os.path.exists(cfg_path):
            print(f"Error: Training config not found: {cfg_path}")
            return
        with open(cfg_path, "r", encoding="utf-8") as f:
            train_config = json.load(f)

    env_settings = resolve_env_settings(train_config, args)
    wrapper_class, wrapper_kwargs = get_action_wrapper_spec(train_config)
    print(
        "Effective eval env settings: "
        f"action_mode={env_settings['action_mode']} "
        f"include_visual={env_settings['include_visual']} "
        f"include_proprio={env_settings['include_proprio']} "
        f"mission_obs_mode={env_settings['mission_obs_mode']} "
        f"visual_downsample={env_settings['visual_downsample']} "
        f"visual_update_interval={env_settings['visual_update_interval']}"
    )
    
    # Create Env
    def make_env():
        runtime_cfg = (
            train_config.get("runtime", {})
            if isinstance(train_config, dict) and isinstance(train_config.get("runtime", {}), dict)
            else {}
        )
        return _build_evaluation_env(
            scenario_path,
            env_settings,
            wrapper_class=wrapper_class,
            wrapper_kwargs=wrapper_kwargs,
            worker_threads=runtime_cfg.get("world_batch_threads"),
        )
    
    vec_env = DummyVecEnv([make_env])
    
    # Load Model
    try:
        model_path = args.model
        if model_path.endswith(".zip"):
            model_path = model_path[:-4]
        algo_cls = PPO
        if args.algo in ("AdaptiveKLPPO", "PPOAdaptiveKL", "PPO_AdaptiveKL"):
            algo_cls = AdaptiveKLPPO
        model = algo_cls.load(model_path, env=vec_env)
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    # Metrics
    episode_rewards = []
    episode_lengths = []
    success_count = 0
    survival_count = 0
    term_reason_counts = {}
    
    for ep in range(args.episodes):
        if args.seed is not None:
            vec_env.seed(int(args.seed) + ep)
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
            
            info0 = infos[0] if isinstance(infos, (list, tuple)) and infos else {}
            ms = info0.get("mission_status") if isinstance(info0, dict) else None
            terminal_flag = None
            if ms is not None:
                try:
                    terminal_flag = float(ms[3])
                except Exception:
                    terminal_flag = None
            if terminal_flag is not None:
                if terminal_flag > 0.5:
                    mission_success = True
                elif terminal_flag < -0.5:
                    survived = False
            
            if dones[0]:
                term_reason = None
                if isinstance(info0, dict):
                    tr = info0.get("termination_reason")
                    if isinstance(tr, str) and tr.strip():
                        term_reason = tr.strip().lower()

                # Fallback for legacy envs/checkpoints that do not populate mission_status.
                if terminal_flag is None:
                    if rewards[0] >= 500:
                        mission_success = True
                        if term_reason is None:
                            term_reason = "success_fallback_reward"
                    if rewards[0] < -500:
                        survived = False
                        if term_reason is None:
                            term_reason = "failure_fallback_reward"
                elif terminal_flag < -0.5:
                    survived = False
                    if term_reason is None:
                        term_reason = "failure_mission_status"
                elif terminal_flag > 0.5 and term_reason is None:
                    term_reason = "success_mission_status"
                if term_reason is None:
                    term_reason = "done_unknown"
                term_reason_counts[term_reason] = int(term_reason_counts.get(term_reason, 0)) + 1
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
    if term_reason_counts:
        print("Termination Reasons:")
        for k in sorted(term_reason_counts.keys()):
            print(f"  {k}: {term_reason_counts[k]}")
    print("="*30)

if __name__ == "__main__":
    main()
