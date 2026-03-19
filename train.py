import argparse
import atexit
import fcntl
import os
import sys
import json
import shutil
import math
from datetime import datetime

import numpy as np
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
from python.training_callbacks import (
    CMODiagnosticsCallback,
    ScenarioCurriculumCallback,
    RewardPlateauEarlyStopCallback,
)
from python.env_config import resolve_env_settings
from python.rl.ppo_adaptive_kl import AdaptiveKLPPO
from python.rl.policies import SquashedMultiInputPolicy
from python.rl.wrappers import get_action_wrapper_spec


def acquire_experiment_lock(exp_dir: str):
    """
    Prevent concurrent training processes from writing into the same experiment directory.

    This is especially important for resume flows, where a second accidental `train.py`
    invocation can silently corrupt checkpoints/logs and saturate CPU by duplicating the
    full simulation workload.
    """
    lock_path = os.path.join(exp_dir, ".train.lock")
    os.makedirs(exp_dir, exist_ok=True)
    lock_file = open(lock_path, "a+", encoding="utf-8")
    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock_file.seek(0)
        holder = lock_file.read().strip()
        print(f"Error: experiment directory is already locked by another training process: {exp_dir}")
        if holder:
            print(f"Active lock info: {holder}")
        lock_file.close()
        return None

    lock_info = {
        "pid": os.getpid(),
        "cwd": os.getcwd(),
        "argv": sys.argv,
        "acquired_at": datetime.now().isoformat(timespec="seconds"),
    }
    lock_file.seek(0)
    lock_file.truncate()
    lock_file.write(json.dumps(lock_info, ensure_ascii=True) + "\n")
    lock_file.flush()

    def _release_lock():
        try:
            lock_file.seek(0)
            lock_file.truncate()
            lock_file.flush()
        except Exception:
            pass
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
        try:
            lock_file.close()
        except Exception:
            pass

    atexit.register(_release_lock)
    return lock_file

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


def _unit_to_presquash(value: float) -> float:
    x = float(np.clip(2.0 * float(value) - 1.0, -0.999, 0.999))
    return float(math.atanh(x))


def infer_full_action_safe_defaults(scenario_path: str) -> tuple[float, float, float, float]:
    """
    Infer reasonable initial throttle/gear defaults from the scenario.

    Full-action tasks are not all takeoff tasks. Airborne/cruise scenarios should not
    inherit a takeoff-style "gear down, near-max throttle" bias, otherwise PPO can get
    stuck around a bad initial mean for configuration controls.
    """
    throttle_default = 0.95
    gear_default = 1.0
    flaps_default = 0.0
    speedbrake_default = 0.0
    try:
        with open(scenario_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        mission = data.get("mission_command", {}) if isinstance(data, dict) else {}
        entities = data.get("entities", []) if isinstance(data, dict) else []
        agent = next((e for e in entities if isinstance(e, dict) and bool(e.get("is_agent", False))), None)
        pos = agent.get("pos", []) if isinstance(agent, dict) else []
        spawn_alt_m = float(pos[2]) if isinstance(pos, list) and len(pos) > 2 else 0.0
        cmd_code = int(mission.get("command_code", 0)) if isinstance(mission, dict) else 0

        airborne_start = spawn_alt_m > 50.0
        if cmd_code == 4:
            throttle_default = 0.45
            gear_default = 1.0
            flaps_default = 1.0
            speedbrake_default = 0.0
        elif airborne_start or cmd_code == 3:
            throttle_default = 0.60
            gear_default = 0.0
            flaps_default = 0.0
            speedbrake_default = 0.0
    except Exception:
        pass
    return float(throttle_default), float(gear_default), float(flaps_default), float(speedbrake_default)


def apply_safe_action_bias(model: PPO, action_mode: str, scenario_path: str):
    """
    Improve early exploration for mixed-range action spaces.

    SB3 PPO uses an (unbounded) Gaussian policy. For dimensions with bounds [0, 1],
    the default mean initialization at 0.0 tends to clip to 0.0 (e.g. throttle=0),
    which can trap learning in the "stationary on runway" regime. We bias those
    outputs toward realistic neutral/safe defaults.
    """
    try:
        action_net = getattr(model.policy, "action_net", None)
        if action_net is None or getattr(action_net, "bias", None) is None:
            return
        b = action_net.bias
        if b is None:
            return
        squash = bool(getattr(model.policy, "squash_output", False))
        with torch.no_grad():
            if action_mode == "full":
                if int(b.shape[0]) < 17:
                    return
                throttle_default, gear_default, flaps_default, speedbrake_default = infer_full_action_safe_defaults(scenario_path)
                # Safe defaults for the 17D "full" action layout in `gym_envs/universal_env.py`.
                # - throttle/gear are scenario-aware: takeoff starts on-ground, cruise starts airborne
                # - keep brakes/speedbrake/flaps and combat switches off by default
                if squash:
                    # With tanh-squash + unscale, bias=0 maps to the midpoint of [low,high].
                    # Push "off" switches below 0.5 by using negative pre-squash means.
                    b[3] = _unit_to_presquash(throttle_default)
                    b[4] = _unit_to_presquash(gear_default)
                    b[5] = _unit_to_presquash(flaps_default)
                    b[6] = _unit_to_presquash(speedbrake_default)

                    off_pre = -2.0
                    for idx in (7, 8, 9, 12, 13, 14, 15, 16):
                        b[idx] = off_pre
                else:
                    # Unbounded Gaussian + clip: bias directly corresponds to env action value.
                    b[3] = throttle_default
                    b[4] = gear_default
                    b[5] = flaps_default
                    b[6] = speedbrake_default
                    for idx in (7, 8, 9, 12, 13, 14, 15, 16):
                        b[idx] = 0.0
            elif action_mode == "takeoff2":
                if int(b.shape[0]) < 2:
                    return
                throttle_default = 1.0
                if squash:
                    b[1] = _unit_to_presquash(throttle_default)
                else:
                    b[1] = throttle_default
            elif action_mode == "takeoff4":
                if int(b.shape[0]) < 4:
                    return
                throttle_default = 1.0
                if squash:
                    b[3] = _unit_to_presquash(throttle_default)
                else:
                    b[3] = throttle_default
                # Keep lateral controls neutral at initialization so the early rollout explores
                # "accelerate straight" before searching over crosswind corrections.
                b[0] = 0.0
                b[1] = 0.0
                b[2] = 0.0
    except Exception:
        return


def apply_leader_action_bias(model: PPO):
    """
    Bias leader policies toward a mild post-departure route-selection default.

    The leader phase action uses:
    - near 0.0 -> teacher
    - moderately negative -> route

    A small negative bias helps the policy discover "leave departure / start route
    tasking" much earlier, while low-altitude guardrails in `LeaderTrainingEnv`
    still keep takeoff and early departure safe.
    """
    try:
        action_net = getattr(model.policy, "action_net", None)
        if action_net is None or getattr(action_net, "bias", None) is None:
            return
        b = action_net.bias
        if b is None or int(b.shape[0]) < 4:
            return
        squash = bool(getattr(model.policy, "squash_output", False))
        with torch.no_grad():
            phase_default = -0.35
            b[0] = float(np.arctanh(np.clip(phase_default, -0.999, 0.999))) if squash else phase_default
            b[1] = 0.0
            b[2] = 0.0
            b[3] = 0.0
    except Exception:
        return


def resolve_vec_env_spec(
    *,
    agent_layer: str,
    n_envs: int,
    runtime_cfg: dict,
    leader_batched_vec_env_cls,
):
    """
    Pick the vectorized-environment backend for the current training run.

    Leader training briefly experimented with `LeaderBatchedVecEnv`, which batches frozen
    execution-policy inference across envs on one process. In practice that optimization
    regressed throughput badly because it also collapsed environment stepping from
    `SubprocVecEnv` back to a single-process `DummyVecEnv`-style loop.

    Keep the experimental path available behind an explicit opt-in, but default leader
    runs back to normal multi-process vectorization.
    """
    use_batched_execution_inference = bool(runtime_cfg.get("batched_execution_inference", False))
    allow_experimental_singleprocess_batched_leader = bool(
        runtime_cfg.get("allow_experimental_singleprocess_batched_leader", False)
    )

    if agent_layer != "leader":
        return SubprocVecEnv if int(n_envs) > 1 else DummyVecEnv, {}, False

    if use_batched_execution_inference and not allow_experimental_singleprocess_batched_leader:
        print(
            "[WARN] runtime.batched_execution_inference is currently disabled by default for leader training. "
            "The available implementation routes all leader envs through a single-process batched loop and "
            "has measured significantly lower FPS than SubprocVecEnv with frozen execution. "
            "Using standard multi-process env stepping instead."
        )

    if use_batched_execution_inference and allow_experimental_singleprocess_batched_leader:
        if leader_batched_vec_env_cls is None:
            print(
                "[WARN] experimental leader batched vec env requested, but LeaderBatchedVecEnv is unavailable. "
                "Falling back to standard vec env."
            )
        else:
            return (
                leader_batched_vec_env_cls,
                {
                    "execution_device": str(runtime_cfg.get("execution_device", "cuda")),
                    "execution_use_autocast": bool(runtime_cfg.get("execution_use_autocast", True)),
                    "step_executor_workers": int(runtime_cfg.get("step_executor_workers", 0)),
                },
                True,
            )

    return SubprocVecEnv if int(n_envs) > 1 else DummyVecEnv, {}, False

def main():
    parser = argparse.ArgumentParser(description="Universal Training Base for CMO")
    parser.add_argument("--scenario", type=str, required=True, help="Path to JSON scenario file")
    parser.add_argument("--train_config", type=str, default="examples/config/training/default_ppo.json", help="Path to training config JSON")
    parser.add_argument("--test_only", action="store_true", help="Run in test mode without training")
    parser.add_argument(
        "--include_visual",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Include ARB visual observation (defaults to train_config env/policy settings).",
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
        choices=["basic", "nav_v1", "nav_v2"],
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
        choices=["full", "takeoff2", "takeoff4"],
        help="Action space mode (defaults to train_config env settings).",
    )
    
    # New Experiment Args
    parser.add_argument("--run_name", type=str, default=None, help="Name of the run. If None, uses Timestamp.")
    parser.add_argument("--resume_path", type=str, default=None, help="Path to .zip model to resume training from.")
    parser.add_argument(
        "--init_from",
        type=str,
        default=None,
        help="Path to a .zip model checkpoint used only to initialize model parameters. "
             "This preserves the new run directory, optimizer state, and hyperparameters.",
    )
    parser.add_argument("--output_base", type=str, default="experiments", help="Base directory for experiments.")
    parser.add_argument("--n_envs", type=int, default=None, help="Number of parallel environments (overrides config)")
    parser.add_argument(
        "--torch_threads",
        type=int,
        default=None,
        help="PyTorch intra-op CPU threads per process. If omitted, keep PyTorch defaults.",
    )
    parser.add_argument(
        "--torch_interop_threads",
        type=int,
        default=None,
        help="PyTorch inter-op CPU threads per process. If omitted, keep PyTorch defaults.",
    )
    parser.add_argument("--diagnostics", action="store_true", help="Log extra diagnostics scalars to TensorBoard")
    parser.add_argument(
        "--diagnostics_every",
        type=int,
        default=10000,
        help="Diagnostics logging interval (in environment timesteps, not gradient updates)",
    )
    parser.add_argument(
        "--diagnostics_preterm_window",
        type=int,
        default=32,
        help="How many recent steps to aggregate for pre-termination diagnostics.",
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

    agent_layer = str(train_config.get("agent_layer", "execution")).strip().lower() or "execution"
    if agent_layer not in {"execution", "leader"}:
        print(f"Error: unknown agent_layer {agent_layer!r} in train config")
        return

    if agent_layer == "leader":
        from gym_envs.leader_env import LeaderTrainingEnv
        from python.rl.leader_batched_vec_env import LeaderBatchedVecEnv
    else:
        LeaderTrainingEnv = None
        LeaderBatchedVecEnv = None

    env_settings = resolve_env_settings(train_config, args) if agent_layer == "execution" else None

    # 2. Setup Experiment Directory
    exp_dir = ""
    run_name = ""
    
    if args.resume_path and args.init_from:
        print("Error: --resume_path and --init_from are mutually exclusive.")
        return

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
    exp_lock = acquire_experiment_lock(exp_dir)
    if exp_lock is None:
        return

    runtime_cfg = train_config.get("runtime", {}) if isinstance(train_config.get("runtime", {}), dict) else {}

    torch_threads = args.torch_threads
    if torch_threads is None:
        torch_threads = runtime_cfg.get("torch_threads")
    if torch_threads is not None:
        torch_threads = max(1, int(torch_threads))
        torch.set_num_threads(torch_threads)
    else:
        torch_threads = int(torch.get_num_threads())

    torch_interop_threads = args.torch_interop_threads
    if torch_interop_threads is None:
        torch_interop_threads = runtime_cfg.get("torch_interop_threads")
    if torch_interop_threads is not None:
        torch_interop_threads = max(1, int(torch_interop_threads))
        try:
            torch.set_num_interop_threads(torch_interop_threads)
        except RuntimeError:
            pass
    else:
        try:
            torch_interop_threads = int(torch.get_num_interop_threads())
        except Exception:
            torch_interop_threads = -1

    # 3. Environment Setup
    n_envs = args.n_envs if args.n_envs is not None else train_config.get("n_envs", 1)
    
    print(f"Creating {n_envs} parallel environments...")
    print(f"Logging to {log_dir}")
    print(f"Agent layer: {agent_layer}")
    print(
        "Runtime parallelism: "
        f"torch_threads={torch_threads} "
        f"torch_interop_threads={torch_interop_threads} "
        f"OMP_NUM_THREADS={os.environ.get('OMP_NUM_THREADS', '<unset>')} "
        f"MKL_NUM_THREADS={os.environ.get('MKL_NUM_THREADS', '<unset>')} "
        f"OPENBLAS_NUM_THREADS={os.environ.get('OPENBLAS_NUM_THREADS', '<unset>')}"
    )
    if agent_layer == "leader":
        print(
            "Leader runtime: "
            f"batched_execution_inference={bool(runtime_cfg.get('batched_execution_inference', False))} "
            f"execution_device={str(runtime_cfg.get('execution_device', 'cuda'))} "
            f"execution_use_autocast={bool(runtime_cfg.get('execution_use_autocast', True))} "
            f"step_executor_workers={int(runtime_cfg.get('step_executor_workers', 0))} "
            f"leader_execution_torch_threads={runtime_cfg.get('leader_execution_torch_threads', '<auto>')} "
            f"leader_execution_torch_interop_threads={runtime_cfg.get('leader_execution_torch_interop_threads', '<auto>')}"
        )
    if agent_layer == "execution":
        print(
            "Effective env settings: "
            f"action_mode={env_settings['action_mode']} "
            f"include_visual={env_settings['include_visual']} "
            f"include_proprio={env_settings['include_proprio']} "
            f"mission_obs_mode={env_settings['mission_obs_mode']} "
            f"visual_downsample={env_settings['visual_downsample']} "
            f"visual_update_interval={env_settings['visual_update_interval']}"
        )
    else:
        leader_cfg = train_config.get("leader_env", {}) if isinstance(train_config.get("leader_env", {}), dict) else {}
        print(
            "Leader env settings: "
            f"decision_interval_steps={int(leader_cfg.get('decision_interval_steps', 20))} "
            f"execution_backend={str(leader_cfg.get('execution_backend', 'scripted'))} "
            f"execution_train_config={leader_cfg.get('execution_train_config', '<none>')} "
            f"execution_model_path={leader_cfg.get('execution_model_path', '<none>')}"
        )

    # Rough rollout-buffer memory warning for visual observations (DictRolloutBuffer stores full obs).
    try:
        n_steps = int(train_config.get("hyperparameters", {}).get("n_steps", 2048))
    except Exception:
        n_steps = 2048
    if agent_layer == "execution" and env_settings["include_visual"]:
        ds = int(env_settings["visual_downsample"])
        visual_elems = (48 // ds) * (96 // ds) * 10
        est_bytes = int(n_envs) * int(n_steps) * int(visual_elems) * 4
        if est_bytes >= 4 * 1024**3:
            gib = est_bytes / (1024**3)
            print(
                f"[WARN] include_visual=True with visual_downsample={ds}, n_envs={n_envs}, n_steps={n_steps} "
                f"will allocate ~{gib:.1f} GiB just for the visual rollout buffer. "
                "Consider reducing n_envs/n_steps or increasing --visual_downsample."
            )
    
    # We must delay env creation for resume if we want to ensure same config? 
    # For now we assume user provides correct params for resumption.
    vec_cls, vec_env_kwargs, active_batched_execution_inference = resolve_vec_env_spec(
        agent_layer=agent_layer,
        n_envs=n_envs,
        runtime_cfg=runtime_cfg,
        leader_batched_vec_env_cls=LeaderBatchedVecEnv,
    )

    if agent_layer == "execution":
        wrapper_class, wrapper_kwargs = get_action_wrapper_spec(train_config)
        vec_env = make_vec_env(
            UniversalEnv,
            n_envs=n_envs,
            env_kwargs={
                "scenario_path": scenario_path,
                **env_settings,
            },
            vec_env_cls=vec_cls,
            vec_env_kwargs=vec_env_kwargs,
            wrapper_class=wrapper_class,
            wrapper_kwargs=wrapper_kwargs,
        )
    else:
        leader_cfg = train_config.get("leader_env", {}) if isinstance(train_config.get("leader_env", {}), dict) else {}
        leader_execution_torch_threads = runtime_cfg.get("leader_execution_torch_threads")
        if leader_execution_torch_threads is None:
            if n_envs > 1 and str(leader_cfg.get("execution_backend", "scripted")).strip().lower() == "frozen_model":
                leader_execution_torch_threads = 1
        leader_execution_torch_interop_threads = runtime_cfg.get("leader_execution_torch_interop_threads")
        if leader_execution_torch_interop_threads is None:
            if n_envs > 1 and str(leader_cfg.get("execution_backend", "scripted")).strip().lower() == "frozen_model":
                leader_execution_torch_interop_threads = 1
        vec_env = make_vec_env(
            LeaderTrainingEnv,
            n_envs=n_envs,
            env_kwargs={
                "scenario_path": scenario_path,
                "decision_interval_steps": int(leader_cfg.get("decision_interval_steps", 20)),
                "execution_backend": str(leader_cfg.get("execution_backend", "scripted")),
                "execution_train_config": leader_cfg.get("execution_train_config"),
                "execution_model_path": leader_cfg.get("execution_model_path"),
                "execution_algo": str(leader_cfg.get("execution_algo", "auto")),
                "scripted_transition_alt_agl_m": float(leader_cfg.get("scripted_transition_alt_agl_m", 140.0)),
                "heading_bias_limit_deg": float(leader_cfg.get("heading_bias_limit_deg", 45.0)),
                "altitude_bias_limit_m": float(leader_cfg.get("altitude_bias_limit_m", 800.0)),
                "speed_bias_limit_mps": float(leader_cfg.get("speed_bias_limit_mps", 40.0)),
                "command_change_penalty": float(leader_cfg.get("command_change_penalty", 0.0)),
                "teacher_keep_deadband": float(leader_cfg.get("teacher_keep_deadband", 0.20)),
                "invalid_phase_penalty": float(leader_cfg.get("invalid_phase_penalty", 0.0)),
                "premature_approach_penalty": float(leader_cfg.get("premature_approach_penalty", 0.0)),
                "baseline_deviation_penalty": float(leader_cfg.get("baseline_deviation_penalty", 0.0)),
                "mode_change_penalty": float(leader_cfg.get("mode_change_penalty", 0.0)),
                "approach_gate_distance_m": float(leader_cfg.get("approach_gate_distance_m", 18000.0)),
                "approach_gate_cross_m": float(leader_cfg.get("approach_gate_cross_m", 3500.0)),
                "approach_gate_heading_error_deg": float(leader_cfg.get("approach_gate_heading_error_deg", 85.0)),
                "execution_torch_threads": (
                    None if leader_execution_torch_threads is None else int(leader_execution_torch_threads)
                ),
                "execution_torch_interop_threads": (
                    None
                    if leader_execution_torch_interop_threads is None
                    else int(leader_execution_torch_interop_threads)
                ),
            },
            vec_env_cls=vec_cls,
            vec_env_kwargs=vec_env_kwargs,
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
            leader_overrides0 = st0.get("leader_env_overrides", {})
            if isinstance(leader_overrides0, dict) and leader_overrides0:
                vec_env.env_method("set_leader_overrides", leader_overrides0)
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
    save_freq = int(train_config.get("save_freq", 50000))
    # SB3 CheckpointCallback counts callback invocations, not aggregate env timesteps.
    # Interpret config `save_freq` as total timesteps so multi-env runs checkpoint on the
    # expected cadence instead of being stretched by `n_envs`.
    checkpoint_freq = max(1, int(math.ceil(float(save_freq) / float(max(1, n_envs)))))

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
        if args.init_from:
            init_path = os.path.abspath(args.init_from)
            if not os.path.exists(init_path):
                print(f"Error: Initialization checkpoint not found: {init_path}")
                return
            print(f"Initializing Parameters From: {init_path}")
            model.set_parameters(init_path, exact_match=False, device=hyperparams.get("device", "auto"))
        elif agent_layer == "execution" and not args.no_init_safe_action_bias:
            apply_safe_action_bias(model, env_settings["action_mode"], scenario_path)
        elif agent_layer == "leader":
            apply_leader_action_bias(model)
    
    print(
        f"Starting Training for {total_timesteps} steps... "
        f"(checkpoint every {save_freq} total timesteps -> every {checkpoint_freq} callback steps)"
    )

    checkpoint_callback = CheckpointCallback(
        save_freq=checkpoint_freq,
        save_path=ckpt_dir,
        name_prefix="model" # naming: model_50000_steps.zip
    )
    callbacks = [checkpoint_callback]
    if args.diagnostics:
        callbacks.append(
            CMODiagnosticsCallback(
                log_every_timesteps=int(args.diagnostics_every),
                preterm_window_steps=int(args.diagnostics_preterm_window),
            )
        )
    if isinstance(curriculum_cfg, dict) and curriculum_cfg.get("stages"):
        callbacks.append(
            ScenarioCurriculumCallback(
                stages=list(curriculum_cfg["stages"]),
                check_freq=int(curriculum_cfg.get("check_freq", 10_000)),
            )
        )

    early_stop_cfg = train_config.get("early_stop", {}) if isinstance(train_config.get("early_stop", {}), dict) else {}
    best_ema_ckpt = os.path.join(ckpt_dir, "best_ema_model.zip")
    if bool(early_stop_cfg.get("enabled", False)):
        callbacks.append(
            RewardPlateauEarlyStopCallback(
                min_timesteps=int(early_stop_cfg.get("min_timesteps", 200_000)),
                check_every_timesteps=int(early_stop_cfg.get("check_every_timesteps", 20_000)),
                patience_checks=int(early_stop_cfg.get("patience_checks", 6)),
                min_improvement=float(early_stop_cfg.get("min_improvement", 0.5)),
                ema_alpha=float(early_stop_cfg.get("ema_alpha", 0.05)),
                best_model_path=os.path.join(ckpt_dir, "best_ema_model"),
                verbose=1,
            )
        )

    callback = CallbackList(callbacks) if len(callbacks) > 1 else checkpoint_callback
    
    try:
        # If resuming, we might want to adjust total_timesteps? 
        # reset_num_timesteps=False allows continuing TB logs seamlessly
        model.learn(total_timesteps=total_timesteps, callback=callback, reset_num_timesteps=(not args.resume_path))
        
        final_path = os.path.join(exp_dir, "final_model")
        export_best = bool(early_stop_cfg.get("enabled", False)) and bool(
            early_stop_cfg.get("export_best_as_final", True)
        )
        if export_best and os.path.exists(best_ema_ckpt):
            print(f"Saving final model from best EMA checkpoint: {best_ema_ckpt}")
            best_model = algo_cls.load(best_ema_ckpt, env=vec_env, tensorboard_log=log_dir)
            best_model.save(final_path)
        else:
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
