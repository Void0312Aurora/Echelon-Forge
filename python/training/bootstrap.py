from __future__ import annotations

import argparse
import atexit
import fcntl
import json
import os
import random
import shutil
from dataclasses import dataclass
from datetime import datetime
from typing import Any, TextIO

import numpy as np
import torch

from python.env_config import resolve_env_settings


SUPPORTED_AGENT_LAYERS = frozenset({"execution", "leader", "cooperative_execution"})


@dataclass
class TrainingBootstrap:
    args: argparse.Namespace
    scenario_path: str
    train_cfg_path: str
    train_config: dict[str, Any]
    agent_layer: str
    env_settings: dict[str, Any] | None
    exp_dir: str
    run_name: str
    ckpt_dir: str
    log_dir: str
    runtime_cfg: dict[str, Any]
    training_seed: int | None
    torch_threads: int
    torch_interop_threads: int
    n_envs: int
    leader_env_cls: type[Any] | None
    leader_batched_vec_env_cls: type[Any] | None
    exp_lock: TextIO


def apply_global_seed(seed: int) -> None:
    seed = int(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def acquire_experiment_lock(exp_dir: str) -> TextIO | None:
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
        "argv": os.sys.argv,
        "acquired_at": datetime.now().isoformat(timespec="seconds"),
    }
    lock_file.seek(0)
    lock_file.truncate()
    lock_file.write(json.dumps(lock_info, ensure_ascii=True) + "\n")
    lock_file.flush()

    def _release_lock() -> None:
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


def _resolve_agent_layer(train_config: dict[str, Any]) -> str | None:
    agent_layer = str(train_config.get("agent_layer", "execution")).strip().lower() or "execution"
    if agent_layer not in SUPPORTED_AGENT_LAYERS:
        print(f"Error: unknown agent_layer {agent_layer!r} in train config")
        return None
    return agent_layer


def _load_leader_runtime_classes(agent_layer: str) -> tuple[type[Any] | None, type[Any] | None]:
    if agent_layer != "leader":
        return None, None
    from gym_envs.leader_env import LeaderTrainingEnv
    from python.rl.runtime.leader_batched_vec_env import LeaderBatchedVecEnv

    return LeaderTrainingEnv, LeaderBatchedVecEnv


def _resolve_training_seed(args: argparse.Namespace, train_config: dict[str, Any]) -> int | None:
    training_seed = args.seed
    if training_seed is None and "seed" in train_config:
        try:
            training_seed = int(train_config.get("seed"))
        except Exception:
            training_seed = None
    return training_seed


def _configure_torch_runtime(
    args: argparse.Namespace,
    runtime_cfg: dict[str, Any],
) -> tuple[int, int]:
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

    return int(torch_threads), int(torch_interop_threads)


def _prepare_experiment_layout(
    args: argparse.Namespace,
    scenario_path: str,
    train_cfg_path: str,
) -> tuple[str, str, str, str, TextIO] | None:
    if args.resume_path and args.init_from:
        print("Error: --resume_path and --init_from are mutually exclusive.")
        return None

    exp_dir = ""
    run_name = ""
    if args.resume_path:
        if not os.path.exists(args.resume_path):
            print(f"Error: Cannot resume, file not found: {args.resume_path}")
            return None

        abs_resume = os.path.abspath(args.resume_path)
        parent_dir = os.path.dirname(abs_resume)
        if os.path.basename(parent_dir) == "checkpoints":
            exp_dir = os.path.dirname(parent_dir)
        else:
            exp_dir = parent_dir
        run_name = os.path.basename(exp_dir)
        print(f"Resuming Experiment: {run_name} at {exp_dir}")
    else:
        if args.run_name:
            run_name = args.run_name
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            cfg_name = os.path.splitext(os.path.basename(train_cfg_path))[0]
            run_name = f"{timestamp}_{cfg_name}"

        exp_dir = os.path.join(args.output_base, run_name)
        interrupted_path = os.path.join(exp_dir, "checkpoints", "interrupted_model.zip")
        if os.path.exists(interrupted_path):
            print(f"Found interrupted checkpoint at {interrupted_path}")
            print("Auto-resuming from interrupted checkpoint...")
            args.resume_path = interrupted_path
        else:
            os.makedirs(exp_dir, exist_ok=True)
            print(f"Starting New Experiment: {run_name} at {exp_dir}")

        shutil.copy(train_cfg_path, os.path.join(exp_dir, "train_config_backup.json"))
        shutil.copy(scenario_path, os.path.join(exp_dir, "scenario_backup.json"))

    ckpt_dir = os.path.join(exp_dir, "checkpoints")
    log_dir = os.path.join(exp_dir, "logs")
    os.makedirs(ckpt_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    exp_lock = acquire_experiment_lock(exp_dir)
    if exp_lock is None:
        return None
    return exp_dir, run_name, ckpt_dir, log_dir, exp_lock


def prepare_training_bootstrap(args: argparse.Namespace) -> TrainingBootstrap | None:
    scenario_path = os.path.abspath(args.scenario)
    if not os.path.exists(scenario_path):
        print(f"Error: Scenario file not found: {scenario_path}")
        return None

    train_cfg_path = os.path.abspath(args.train_config)
    if not os.path.exists(train_cfg_path):
        print(f"Error: Training config not found: {train_cfg_path}")
        return None

    with open(train_cfg_path, "r", encoding="utf-8") as f:
        train_config = json.load(f)

    agent_layer = _resolve_agent_layer(train_config)
    if agent_layer is None:
        return None

    leader_env_cls, leader_batched_vec_env_cls = _load_leader_runtime_classes(agent_layer)
    env_settings = resolve_env_settings(train_config, args) if agent_layer in {"execution", "cooperative_execution"} else None

    layout = _prepare_experiment_layout(args, scenario_path, train_cfg_path)
    if layout is None:
        return None
    exp_dir, run_name, ckpt_dir, log_dir, exp_lock = layout

    runtime_cfg = train_config.get("runtime", {}) if isinstance(train_config.get("runtime", {}), dict) else {}
    training_seed = _resolve_training_seed(args, train_config)
    if training_seed is not None:
        apply_global_seed(int(training_seed))
        print(f"Training seed: {int(training_seed)}")

    torch_threads, torch_interop_threads = _configure_torch_runtime(args, runtime_cfg)
    n_envs = int(args.n_envs if args.n_envs is not None else train_config.get("n_envs", 1))

    return TrainingBootstrap(
        args=args,
        scenario_path=scenario_path,
        train_cfg_path=train_cfg_path,
        train_config=train_config,
        agent_layer=agent_layer,
        env_settings=env_settings,
        exp_dir=exp_dir,
        run_name=run_name,
        ckpt_dir=ckpt_dir,
        log_dir=log_dir,
        runtime_cfg=runtime_cfg,
        training_seed=training_seed,
        torch_threads=torch_threads,
        torch_interop_threads=torch_interop_threads,
        n_envs=n_envs,
        leader_env_cls=leader_env_cls,
        leader_batched_vec_env_cls=leader_batched_vec_env_cls,
        exp_lock=exp_lock,
    )


def print_training_bootstrap_summary(bootstrap: TrainingBootstrap) -> None:
    args = bootstrap.args
    train_config = bootstrap.train_config
    runtime_cfg = bootstrap.runtime_cfg
    env_settings = bootstrap.env_settings
    agent_layer = bootstrap.agent_layer

    print(f"Creating {bootstrap.n_envs} parallel environments...")
    print(f"Logging to {bootstrap.log_dir}")
    print(f"Agent layer: {agent_layer}")
    print(
        "Runtime parallelism: "
        f"torch_threads={bootstrap.torch_threads} "
        f"torch_interop_threads={bootstrap.torch_interop_threads} "
        f"shared_memory_vec_env={bool(runtime_cfg.get('shared_memory_vec_env', False))} "
        f"world_batch_vec_env={bool(runtime_cfg.get('world_batch_vec_env', False))} "
        f"world_batch_threads={runtime_cfg.get('world_batch_threads', '<default=1>')} "
        f"OMP_NUM_THREADS={os.environ.get('OMP_NUM_THREADS', '<unset>')} "
        f"MKL_NUM_THREADS={os.environ.get('MKL_NUM_THREADS', '<unset>')} "
        f"OPENBLAS_NUM_THREADS={os.environ.get('OPENBLAS_NUM_THREADS', '<unset>')}"
    )
    if agent_layer == "leader":
        print(
            "Leader runtime: "
            f"batched_execution_inference={bool(runtime_cfg.get('batched_execution_inference', False))} "
            f"leader_world_batch_runtime={bool(runtime_cfg.get('leader_world_batch_runtime', False))} "
            f"execution_device={str(runtime_cfg.get('execution_device', 'cpu'))} "
            f"execution_use_autocast={bool(runtime_cfg.get('execution_use_autocast', False))} "
            f"step_executor_workers={int(runtime_cfg.get('step_executor_workers', 0))} "
            f"leader_execution_torch_threads={runtime_cfg.get('leader_execution_torch_threads', '<auto>')} "
            f"leader_execution_torch_interop_threads={runtime_cfg.get('leader_execution_torch_interop_threads', '<auto>')}"
        )
        leader_cfg = train_config.get("leader_env", {}) if isinstance(train_config.get("leader_env", {}), dict) else {}
        print(
            "Leader env settings: "
            f"decision_interval_steps={int(leader_cfg.get('decision_interval_steps', 20))} "
            f"execution_backend={str(leader_cfg.get('execution_backend', 'scripted'))} "
            f"execution_action_repeat={int(leader_cfg.get('execution_action_repeat', 1))} "
            f"execution_train_config={leader_cfg.get('execution_train_config', '<none>')} "
            f"execution_model_path={leader_cfg.get('execution_model_path', '<none>')}"
        )
        return

    if env_settings is None:
        return
    if agent_layer == "execution":
        print(
            "Effective env settings: "
            f"action_mode={env_settings['action_mode']} "
            f"include_visual={env_settings['include_visual']} "
            f"include_proprio={env_settings['include_proprio']} "
            f"mission_obs_mode={env_settings['mission_obs_mode']} "
            f"flight_shaping_backend={env_settings.get('flight_shaping_backend', '<auto>') or 'auto'} "
            f"step_info_mode={env_settings['step_info_mode']} "
            f"visual_downsample={env_settings['visual_downsample']} "
            f"visual_update_interval={env_settings['visual_update_interval']}"
        )
        return

    cooperative_cfg = train_config.get("cooperative_execution", {})
    if not isinstance(cooperative_cfg, dict):
        cooperative_cfg = {}
    print(
        "Cooperative env settings: "
        f"action_mode={env_settings['action_mode']} "
        f"include_visual={env_settings['include_visual']} "
        f"include_proprio={env_settings['include_proprio']} "
        f"mission_obs_mode={env_settings['mission_obs_mode']} "
        f"step_info_mode={env_settings['step_info_mode']} "
        f"visual_downsample={env_settings['visual_downsample']} "
        f"visual_update_interval={env_settings['visual_update_interval']} "
        f"policy_route={cooperative_cfg.get('policy_route', 'shared_execution')}"
    )


def warn_execution_visual_rollout_memory(bootstrap: TrainingBootstrap) -> None:
    env_settings = bootstrap.env_settings
    if bootstrap.agent_layer != "execution" or env_settings is None or not env_settings["include_visual"]:
        return
    try:
        n_steps = int(bootstrap.train_config.get("hyperparameters", {}).get("n_steps", 2048))
    except Exception:
        n_steps = 2048
    ds = int(env_settings["visual_downsample"])
    visual_elems = (48 // ds) * (96 // ds) * 10
    est_bytes = int(bootstrap.n_envs) * int(n_steps) * int(visual_elems) * 4
    if est_bytes >= 4 * 1024**3:
        gib = est_bytes / (1024**3)
        print(
            f"[WARN] include_visual=True with visual_downsample={ds}, n_envs={bootstrap.n_envs}, n_steps={n_steps} "
            f"will allocate ~{gib:.1f} GiB just for the visual rollout buffer. "
            "Consider reducing n_envs/n_steps or increasing --visual_downsample."
        )
    if ds > 1:
        print(
            f"[INFO] visual_downsample={ds} reduces ARB render resolution, visual tensor size, and model/rollout cost. "
            "For additional simulator wall-clock gains, also consider increasing --visual_update_interval."
        )
