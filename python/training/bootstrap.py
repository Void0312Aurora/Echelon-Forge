from __future__ import annotations

import argparse
import atexit
import json
import os
import random
import shutil
from dataclasses import dataclass
from datetime import datetime
from typing import Any, TextIO

import numpy as np

try:
    import fcntl
except ModuleNotFoundError:  # pragma: no cover - Windows smoke paths do not expose fcntl
    fcntl = None

from python.env_config import resolve_env_settings


SUPPORTED_AGENT_LAYERS = frozenset({"execution", "leader", "cooperative_execution"})
_TORCH: Any | None = None
_TORCH_IMPORT_ERROR: Exception | None = None


def _load_torch() -> Any | None:
    global _TORCH, _TORCH_IMPORT_ERROR
    if _TORCH is not None:
        return _TORCH
    if _TORCH_IMPORT_ERROR is not None:
        return None
    try:
        import torch as torch_module
    except Exception as exc:  # pragma: no cover - optional dependency boundary
        _TORCH_IMPORT_ERROR = exc
        return None
    _TORCH = torch_module
    return _TORCH


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
    torch_module = _load_torch()
    if torch_module is None:
        print("[WARN] PyTorch is not installed; skipping torch seed initialization.")
        return
    torch_module.manual_seed(seed)
    if torch_module.cuda.is_available():
        torch_module.cuda.manual_seed_all(seed)


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
    if fcntl is not None:
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
        if fcntl is not None:
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


def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _realpath(value: str) -> str:
    return os.path.normcase(os.path.realpath(os.path.abspath(value)))


def _declared_path_candidates(path_value: str, train_cfg_path: str) -> list[str]:
    raw = str(path_value).strip()
    if not raw:
        return []
    if os.path.isabs(raw):
        return [_realpath(raw)]
    roots = (
        _repo_root(),
        os.path.dirname(os.path.abspath(train_cfg_path)),
        os.getcwd(),
    )
    out: list[str] = []
    seen: set[str] = set()
    for root in roots:
        candidate = _realpath(os.path.join(root, raw))
        if candidate not in seen:
            seen.add(candidate)
            out.append(candidate)
    return out


def validate_declared_training_entry_paths(
    *,
    scenario_path: str,
    train_cfg_path: str,
    train_config: dict[str, Any],
) -> str | None:
    naval_entry = train_config.get("naval_entry")
    if not isinstance(naval_entry, dict):
        return None

    declared_scenario = str(naval_entry.get("scenario_path", "") or "").strip()
    if declared_scenario:
        scenario_real = _realpath(scenario_path)
        if scenario_real not in _declared_path_candidates(declared_scenario, train_cfg_path):
            return (
                "Error: train config naval_entry.scenario_path="
                f"{declared_scenario!r} does not match --scenario {scenario_path!r}. "
                "Use the scenario declared by the active entry, or update the entry metadata."
            )

    declared_contract = str(naval_entry.get("contract_path", "") or "").strip()
    if declared_contract:
        contract_candidates = _declared_path_candidates(declared_contract, train_cfg_path)
        existing_contracts = [candidate for candidate in contract_candidates if os.path.exists(candidate)]
        if not existing_contracts:
            return (
                "Error: train config naval_entry.contract_path="
                f"{declared_contract!r} could not be resolved from the repository root, "
                "train config directory, or current working directory."
            )
        if declared_scenario:
            try:
                with open(existing_contracts[0], "r", encoding="utf-8") as handle:
                    contract = json.load(handle)
            except Exception as exc:
                return (
                    "Error: train config naval_entry.contract_path="
                    f"{declared_contract!r} could not be read as JSON: {exc}"
                )
            contract_scenario = str(contract.get("scenario", "") or "").strip() if isinstance(contract, dict) else ""
            if contract_scenario:
                declared_scenario_paths = set(_declared_path_candidates(declared_scenario, train_cfg_path))
                contract_scenario_paths = set(_declared_path_candidates(contract_scenario, existing_contracts[0]))
                if declared_scenario_paths.isdisjoint(contract_scenario_paths):
                    return (
                        "Error: train config naval_entry.contract_path="
                        f"{declared_contract!r} points to scenario {contract_scenario!r}, "
                        f"but naval_entry.scenario_path is {declared_scenario!r}."
                    )

    return None


def validate_declared_training_entry_env_surface(
    *,
    train_config: dict[str, Any],
    env_settings: dict[str, Any] | None,
) -> str | None:
    naval_entry = train_config.get("naval_entry")
    if not isinstance(naval_entry, dict):
        return None

    if env_settings is None:
        return (
            "Error: train config naval_entry requires execution env settings so the "
            "naval action and observation surfaces can be checked."
        )

    action_mode = str(env_settings.get("action_mode", "") or "").strip()
    mission_obs_mode = str(env_settings.get("mission_obs_mode", "") or "").strip().lower()
    if action_mode != "naval_station3":
        return (
            "Error: train config naval_entry requires action_mode='naval_station3' "
            f"for the current N4 naval station-order surface, got {action_mode!r}."
        )
    if mission_obs_mode != "naval_screen_station_v1":
        return (
            "Error: train config naval_entry requires mission_obs_mode='naval_screen_station_v1' "
            f"for the current N4 naval policy observation surface, got {mission_obs_mode!r}."
        )

    return None


def resolve_declared_runtime_database_path(
    *,
    train_cfg_path: str,
    runtime_cfg: dict[str, Any],
) -> tuple[str | None, str | None]:
    declared_database = str(runtime_cfg.get("database_path", "") or "").strip()
    if not declared_database:
        return None, None

    database_candidates = _declared_path_candidates(declared_database, train_cfg_path)
    existing_databases = [candidate for candidate in database_candidates if os.path.isdir(candidate)]
    if existing_databases:
        return existing_databases[0], None
    return (
        None,
        "Error: train config runtime.database_path="
        f"{declared_database!r} could not be resolved to an existing directory from "
        "the repository root, train config directory, or current working directory.",
    )


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
    torch_module = _load_torch()
    torch_threads = args.torch_threads
    if torch_threads is None:
        torch_threads = runtime_cfg.get("torch_threads")
    if torch_module is None:
        if torch_threads is not None:
            torch_threads = max(1, int(torch_threads))
        else:
            torch_threads = -1
        torch_interop_threads = args.torch_interop_threads
        if torch_interop_threads is None:
            torch_interop_threads = runtime_cfg.get("torch_interop_threads")
        if torch_interop_threads is not None:
            torch_interop_threads = max(1, int(torch_interop_threads))
        else:
            torch_interop_threads = -1
        return int(torch_threads), int(torch_interop_threads)

    if torch_threads is not None:
        torch_threads = max(1, int(torch_threads))
        torch_module.set_num_threads(torch_threads)
    else:
        torch_threads = int(torch_module.get_num_threads())

    torch_interop_threads = args.torch_interop_threads
    if torch_interop_threads is None:
        torch_interop_threads = runtime_cfg.get("torch_interop_threads")
    if torch_interop_threads is not None:
        torch_interop_threads = max(1, int(torch_interop_threads))
        try:
            torch_module.set_num_interop_threads(torch_interop_threads)
        except RuntimeError:
            pass
    else:
        try:
            torch_interop_threads = int(torch_module.get_num_interop_threads())
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
    create_backups = False
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
            if args.init_from:
                print(
                    "Error: an interrupted checkpoint was found, but --init_from was also "
                    "provided; remove the interrupted checkpoint or choose an explicit resume."
                )
                return None
            print(f"Found interrupted checkpoint at {interrupted_path}")
            print("Auto-resuming from interrupted checkpoint...")
            args.resume_path = interrupted_path
        else:
            os.makedirs(exp_dir, exist_ok=True)
            print(f"Starting New Experiment: {run_name} at {exp_dir}")
            create_backups = True

    ckpt_dir = os.path.join(exp_dir, "checkpoints")
    log_dir = os.path.join(exp_dir, "logs")
    os.makedirs(ckpt_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    exp_lock = acquire_experiment_lock(exp_dir)
    if exp_lock is None:
        return None
    if create_backups:
        try:
            shutil.copy(train_cfg_path, os.path.join(exp_dir, "train_config_backup.json"))
            shutil.copy(scenario_path, os.path.join(exp_dir, "scenario_backup.json"))
        except Exception:
            exp_lock.close()
            raise
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

    entry_error = validate_declared_training_entry_paths(
        scenario_path=scenario_path,
        train_cfg_path=train_cfg_path,
        train_config=train_config,
    )
    if entry_error is not None:
        print(entry_error)
        return None

    agent_layer = _resolve_agent_layer(train_config)
    if agent_layer is None:
        return None

    leader_env_cls, leader_batched_vec_env_cls = _load_leader_runtime_classes(agent_layer)
    env_settings = resolve_env_settings(train_config, args) if agent_layer in {"execution", "cooperative_execution"} else None
    env_surface_error = validate_declared_training_entry_env_surface(
        train_config=train_config,
        env_settings=env_settings,
    )
    if env_surface_error is not None:
        print(env_surface_error)
        return None

    runtime_cfg = train_config.get("runtime", {}) if isinstance(train_config.get("runtime", {}), dict) else {}
    runtime_cfg = dict(runtime_cfg)
    runtime_database_path, runtime_database_error = resolve_declared_runtime_database_path(
        train_cfg_path=train_cfg_path,
        runtime_cfg=runtime_cfg,
    )
    if runtime_database_error is not None:
        print(runtime_database_error)
        return None
    if runtime_database_path is not None:
        runtime_cfg["database_path"] = runtime_database_path

    layout = _prepare_experiment_layout(args, scenario_path, train_cfg_path)
    if layout is None:
        return None
    exp_dir, run_name, ckpt_dir, log_dir, exp_lock = layout

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
            f"visual_update_interval={env_settings['visual_update_interval']} "
            f"temporal_history_len={env_settings['temporal_history_len']}"
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
        f"temporal_history_len={env_settings['temporal_history_len']} "
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
