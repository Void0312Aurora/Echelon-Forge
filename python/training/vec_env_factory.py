"""Vectorized-environment construction for the training entrypoint.

Owns backend selection (`resolve_vec_env_spec`) and the concrete
world-batch / cooperative / leader vec-env builders that `train.py` used to
inline. Heavy runtime dependencies are pulled lazily through
:mod:`python.training.deps`, so importing this module stays cheap.
"""

from __future__ import annotations

import json
from typing import Any

from .bootstrap import TrainingBootstrap
from .deps import load_training_dependencies


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
    deps = load_training_dependencies()
    use_batched_execution_inference = bool(runtime_cfg.get("batched_execution_inference", False))
    allow_experimental_singleprocess_batched_leader = bool(
        runtime_cfg.get("allow_experimental_singleprocess_batched_leader", False)
    )
    use_shared_memory_vec_env = bool(runtime_cfg.get("shared_memory_vec_env", False))

    if agent_layer != "leader":
        if int(n_envs) <= 1:
            return deps.DummyVecEnv, {}, False
        return (deps.SharedMemorySubprocVecEnv if use_shared_memory_vec_env else deps.SubprocVecEnv), {}, False

    if use_batched_execution_inference and not allow_experimental_singleprocess_batched_leader:
        print(
            "[WARN] runtime.batched_execution_inference is currently disabled by default for leader training. "
            "The available implementation routes all leader envs through a single-process batched loop and "
            "has measured significantly lower FPS than SubprocVecEnv with frozen execution. "
            "Using standard multi-process env stepping instead."
        )

    if use_batched_execution_inference and allow_experimental_singleprocess_batched_leader:
        if use_shared_memory_vec_env:
            print(
                "[WARN] runtime.shared_memory_vec_env is ignored when experimental single-process "
                "batched leader inference is enabled."
            )
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
                    "use_shared_world_batch_runtime": bool(runtime_cfg.get("leader_world_batch_runtime", False)),
                    "world_batch_threads": runtime_cfg.get("world_batch_threads"),
                },
                True,
            )

    if int(n_envs) <= 1:
        return deps.DummyVecEnv, {}, False
    return (deps.SharedMemorySubprocVecEnv if use_shared_memory_vec_env else deps.SubprocVecEnv), {}, False


def _world_batch_worker_thread_summary(vec_env) -> tuple[int, int]:
    runtime_facade = getattr(vec_env, "runtime_facade", None)
    if runtime_facade is None:
        raise RuntimeError("World batch worker-thread logging requires a runtime_facade accessor.")
    return int(runtime_facade.worker_threads()), int(runtime_facade.effective_worker_threads())


def _count_control_slots_from_scenario(scenario_path: str) -> int:
    try:
        with open(scenario_path, "r", encoding="utf-8") as handle:
            scenario = json.load(handle)
    except Exception:
        return 1
    if not isinstance(scenario, dict):
        return 1

    roster = scenario.get("cooperative_roster")
    if isinstance(roster, dict):
        members = roster.get("members")
        if isinstance(members, list):
            count = sum(1 for member in members if isinstance(member, dict) and bool(member.get("is_agent", True)))
            if count > 0:
                return int(count)

    entities = scenario.get("entities")
    if isinstance(entities, list):
        count = sum(1 for entity in entities if isinstance(entity, dict) and bool(entity.get("is_agent", False)))
        if count > 0:
            return int(count)
    return 1


def _effective_auto_backend(requested: Any, *, auto_default: str) -> str:
    backend = str(requested if requested is not None else "auto").strip().lower() or "auto"
    return auto_default if backend == "auto" else backend


def print_test_only_preflight_runtime_summary(bootstrap: TrainingBootstrap) -> None:
    """Print the runtime summary surface for `--test_only` preflight failures.

    Mirrors the effective-runtime lines the vec-env builders emit, without
    constructing any environment (and without importing torch/SB3).
    """
    runtime_cfg = bootstrap.runtime_cfg
    env_settings = bootstrap.env_settings
    if env_settings is None:
        return

    agent_layer = bootstrap.agent_layer
    if agent_layer == "execution":
        use_world_batch_vec_env = bool(runtime_cfg.get("world_batch_vec_env", False))
        if not use_world_batch_vec_env:
            return
        configured_threads = runtime_cfg.get("world_batch_threads", "<default=1>")
        effective_threads = 1 if configured_threads == "<default=1>" else configured_threads
        print(
            "World batch runtime: "
            f"configured_threads={configured_threads} "
            f"effective_threads={effective_threads}"
        )
        if env_settings["include_visual"]:
            requested_visual_backend = str(runtime_cfg.get("batch_visual_backend", "auto"))
            print(
                "World batch visual runtime: "
                f"requested_backend={requested_visual_backend} "
                f"effective_backend={_effective_auto_backend(requested_visual_backend, auto_default='compiled')}"
            )
        requested_reward_backend = env_settings.get("flight_shaping_backend") or "auto"
        print(
            "Execution reward runtime: "
            f"requested_backend={requested_reward_backend} "
            f"effective_backend={_effective_auto_backend(requested_reward_backend, auto_default='legacy')}"
        )
        print(
            "Execution policy observation bridge: "
            f"enabled={bool(runtime_cfg.get('policy_observation_torch_bridge', True))}"
        )
        print(
            "World batch observation return mode: "
            f"mode={str(runtime_cfg.get('observation_return_mode', 'copy'))}"
        )
        if runtime_cfg.get("database_path"):
            print(f"World batch database: path={runtime_cfg.get('database_path')}")
        return

    if agent_layer == "cooperative_execution":
        slots_per_world = _count_control_slots_from_scenario(bootstrap.scenario_path)
        total_slots = int(bootstrap.n_envs) * int(slots_per_world)
        print(
            "Cooperative runtime: "
            f"worlds={bootstrap.n_envs} "
            f"slots_per_world={slots_per_world} "
            f"total_slots={total_slots} "
            f"world_batch_threads={runtime_cfg.get('world_batch_threads', '<default=1>')}"
        )
        requested_observation_backend = str(runtime_cfg.get("batch_observation_backend", "auto"))
        print(
            "Cooperative observation runtime: "
            f"requested_backend={requested_observation_backend} "
            f"effective_backend={_effective_auto_backend(requested_observation_backend, auto_default='legacy')}"
        )
        if env_settings["include_visual"]:
            requested_visual_backend = str(runtime_cfg.get("batch_visual_backend", "auto"))
            print(
                "Cooperative visual runtime: "
                f"requested_backend={requested_visual_backend} "
                f"effective_backend={_effective_auto_backend(requested_visual_backend, auto_default='compiled')}"
            )
        if runtime_cfg.get("database_path"):
            print(f"Cooperative database: path={runtime_cfg.get('database_path')}")


def build_execution_world_batch_vec_env(bootstrap: TrainingBootstrap):
    """Build the maintained world-batch execution vec env.

    Returns ``None`` when `runtime.world_batch_vec_env` is not enabled (including
    the unsupported-action-wrapper fallback); the caller owns the retirement
    error for that raw-UniversalEnv path.
    """
    deps = load_training_dependencies()
    train_config = bootstrap.train_config
    runtime_cfg = bootstrap.runtime_cfg
    env_settings = bootstrap.env_settings

    wrapper_class, wrapper_kwargs = deps.get_action_wrapper_spec(train_config)
    use_world_batch_vec_env = bool(runtime_cfg.get("world_batch_vec_env", False))
    world_batch_action_wrapper_kwargs = None
    if use_world_batch_vec_env and wrapper_class is not None:
        if wrapper_class is deps.MultiTimescaleActionWrapper:
            world_batch_action_wrapper_kwargs = dict(wrapper_kwargs or {})
        else:
            print(
                "[WARN] runtime.world_batch_vec_env does not support the requested action wrapper. "
                "Falling back to the standard vec env backend."
            )
            use_world_batch_vec_env = False

    if not use_world_batch_vec_env:
        return None

    world_batch_threads = runtime_cfg.get("world_batch_threads")
    batch_visual_backend = str(runtime_cfg.get("batch_visual_backend", "auto"))
    batch_observation_backend = str(runtime_cfg.get("batch_observation_backend", "auto"))
    policy_observation_torch_bridge = bool(runtime_cfg.get("policy_observation_torch_bridge", True))
    observation_return_mode = str(runtime_cfg.get("observation_return_mode", "copy"))
    post_launch_assessment_cfg = (
        runtime_cfg.get("air_combat_post_launch_assessment", {})
        if isinstance(runtime_cfg.get("air_combat_post_launch_assessment", {}), dict)
        else {}
    )
    hyper_cfg = train_config.get("hyperparameters", {})
    hyper_cfg = hyper_cfg if isinstance(hyper_cfg, dict) else {}
    post_launch_assessment_gamma = float(
        post_launch_assessment_cfg.get("gamma", hyper_cfg.get("gamma", 0.999))
    )
    vec_env = deps.WorldBatchVecEnv(
        scenario_path=bootstrap.scenario_path,
        n_envs=bootstrap.n_envs,
        worker_threads=world_batch_threads,
        database_path=runtime_cfg.get("database_path"),
        batch_observation_backend=batch_observation_backend,
        batch_visual_backend=batch_visual_backend,
        policy_observation_torch_bridge=policy_observation_torch_bridge,
        observation_return_mode=observation_return_mode,
        action_wrapper_kwargs=world_batch_action_wrapper_kwargs,
        air_combat_post_launch_assessment_enabled=bool(
            post_launch_assessment_cfg.get("enabled", False)
        ),
        air_combat_post_launch_assessment_stages=post_launch_assessment_cfg.get("stages"),
        air_combat_post_launch_assessment_max_steps=int(
            post_launch_assessment_cfg.get("max_steps", 0)
        ),
        air_combat_post_launch_assessment_timeout_s=float(
            post_launch_assessment_cfg.get("timeout_s", 0.0)
        ),
        air_combat_post_launch_assessment_gamma=post_launch_assessment_gamma,
        air_combat_post_launch_assessment_blue_throttle=float(
            post_launch_assessment_cfg.get("blue_throttle", 0.65)
        ),
        **env_settings,
    )
    vec_env.seed(bootstrap.training_seed)
    configured_threads, effective_threads = _world_batch_worker_thread_summary(vec_env)
    print(
        "World batch runtime: "
        f"configured_threads={configured_threads} "
        f"effective_threads={effective_threads}"
    )
    if env_settings["include_visual"]:
        print(
            "World batch visual runtime: "
            f"requested_backend={batch_visual_backend} "
            f"effective_backend={vec_env._batch_visual_backend_mode()}"
        )
    print(
        "Execution reward runtime: "
        f"requested_backend={vec_env.flight_shaping_backend} "
        f"effective_backend={vec_env._flight_shaping_backend_mode()}"
    )
    print(
        "Execution policy observation bridge: "
        f"enabled={bool(vec_env.policy_observation_torch_bridge)}"
    )
    print(
        "World batch observation return mode: "
        f"mode={vec_env.observation_return_mode}"
    )
    if runtime_cfg.get("database_path"):
        print(f"World batch database: path={vec_env._db_path}")
    if bool(post_launch_assessment_cfg.get("enabled", False)):
        print(
            "Air-combat post-launch assessment: "
            f"enabled=True max_steps={int(post_launch_assessment_cfg.get('max_steps', 0))} "
            f"timeout_s={float(post_launch_assessment_cfg.get('timeout_s', 0.0))} "
            f"gamma={post_launch_assessment_gamma}"
        )
    if world_batch_action_wrapper_kwargs:
        print("World batch action preprocessing: multi_timescale_action=enabled")
    return vec_env


def build_cooperative_world_batch_vec_env(bootstrap: TrainingBootstrap):
    """Build the cooperative world-batch vec env with its runtime summary output."""
    deps = load_training_dependencies()
    train_config = bootstrap.train_config
    runtime_cfg = bootstrap.runtime_cfg
    env_settings = bootstrap.env_settings
    n_envs = bootstrap.n_envs

    wrapper_class, wrapper_kwargs = deps.get_action_wrapper_spec(train_config)
    if wrapper_class is not None and wrapper_class is not deps.MultiTimescaleActionWrapper:
        print(
            "[WARN] cooperative_execution only supports the maintained multi_timescale action wrapper. "
            "Ignoring unsupported wrapper request."
        )
        wrapper_kwargs = None
    batch_visual_backend = str(runtime_cfg.get("batch_visual_backend", "auto"))
    batch_observation_backend = str(runtime_cfg.get("batch_observation_backend", "auto"))
    vec_env = deps.CooperativeWorldBatchVecEnv(
        scenario_path=bootstrap.scenario_path,
        n_envs=n_envs,
        worker_threads=runtime_cfg.get("world_batch_threads"),
        database_path=runtime_cfg.get("database_path"),
        batch_observation_backend=batch_observation_backend,
        batch_visual_backend=batch_visual_backend,
        action_wrapper_kwargs=wrapper_kwargs if wrapper_class is deps.MultiTimescaleActionWrapper else None,
        **env_settings,
    )
    vec_env.seed(bootstrap.training_seed)
    print(
        "Cooperative runtime: "
        f"worlds={n_envs} "
        f"slots_per_world={int(getattr(vec_env, 'slots_per_world', 0))} "
        f"total_slots={int(getattr(vec_env, 'num_envs', n_envs))} "
        f"world_batch_threads={runtime_cfg.get('world_batch_threads', '<default=1>')}"
    )
    print(
        "Cooperative observation runtime: "
        f"requested_backend={batch_observation_backend} "
        f"effective_backend={vec_env._batch_observation_backend_mode()}"
    )
    if env_settings["include_visual"]:
        print(
            "Cooperative visual runtime: "
            f"requested_backend={batch_visual_backend} "
            f"effective_backend={vec_env._batch_visual_backend_mode()}"
        )
    if runtime_cfg.get("database_path"):
        print(f"Cooperative database: path={vec_env._db_path}")
    return vec_env


def build_leader_vec_env(bootstrap: TrainingBootstrap):
    """Build the leader-layer vec env via SB3 `make_vec_env` and the resolved backend."""
    deps = load_training_dependencies()
    train_config = bootstrap.train_config
    runtime_cfg = bootstrap.runtime_cfg
    n_envs = bootstrap.n_envs

    vec_cls, vec_env_kwargs, _active_batched_execution_inference = resolve_vec_env_spec(
        agent_layer=bootstrap.agent_layer,
        n_envs=n_envs,
        runtime_cfg=runtime_cfg,
        leader_batched_vec_env_cls=bootstrap.leader_batched_vec_env_cls,
    )
    leader_cfg = train_config.get("leader_env", {}) if isinstance(train_config.get("leader_env", {}), dict) else {}
    leader_execution_torch_threads = runtime_cfg.get("leader_execution_torch_threads")
    if leader_execution_torch_threads is None:
        if n_envs > 1 and str(leader_cfg.get("execution_backend", "scripted")).strip().lower() == "frozen_model":
            leader_execution_torch_threads = 1
    leader_execution_torch_interop_threads = runtime_cfg.get("leader_execution_torch_interop_threads")
    if leader_execution_torch_interop_threads is None:
        if n_envs > 1 and str(leader_cfg.get("execution_backend", "scripted")).strip().lower() == "frozen_model":
            leader_execution_torch_interop_threads = 1
    return deps.make_vec_env(
        bootstrap.leader_env_cls,
        n_envs=n_envs,
        env_kwargs={
            "scenario_path": bootstrap.scenario_path,
            "decision_interval_steps": int(leader_cfg.get("decision_interval_steps", 20)),
            "execution_backend": str(leader_cfg.get("execution_backend", "scripted")),
            "execution_train_config": leader_cfg.get("execution_train_config"),
            "execution_model_path": leader_cfg.get("execution_model_path"),
            "execution_algo": str(leader_cfg.get("execution_algo", "auto")),
            "execution_action_repeat": int(leader_cfg.get("execution_action_repeat", 1)),
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
            "execution_world_batch_runtime": bool(runtime_cfg.get("execution_world_batch_runtime", False)),
            "execution_world_batch_threads": runtime_cfg.get("execution_world_batch_threads"),
            "execution_torch_threads": (
                None if leader_execution_torch_threads is None else int(leader_execution_torch_threads)
            ),
            "execution_torch_interop_threads": (
                None
                if leader_execution_torch_interop_threads is None
                else int(leader_execution_torch_interop_threads)
            ),
            "execution_device": str(runtime_cfg.get("execution_device", "cpu")),
            "execution_use_autocast": bool(runtime_cfg.get("execution_use_autocast", False)),
        },
        seed=bootstrap.training_seed,
        vec_env_cls=vec_cls,
        vec_env_kwargs=vec_env_kwargs,
    )


__all__ = [
    "build_cooperative_world_batch_vec_env",
    "build_execution_world_batch_vec_env",
    "build_leader_vec_env",
    "print_test_only_preflight_runtime_summary",
    "resolve_vec_env_spec",
]
