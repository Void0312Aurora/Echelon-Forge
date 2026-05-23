import argparse
import os
import sys
import json
import math

import numpy as np
import torch
# Enable TF32 for Ampere+ GPUs (significant speedup and memory savings)
torch.set_float32_matmul_precision('high')

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import CallbackList, CheckpointCallback

# Prefer the locally built `ef_py` extension when present (avoids accidentally using a stale
# site-packages wheel/so from the venv). `CMO_BUILD_DIR` can pin a specific build tree.
_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
_BUILD_DIR_NAMES = []
_ENV_BUILD_DIR = os.environ.get("CMO_BUILD_DIR", "").strip()
if _ENV_BUILD_DIR:
    _BUILD_DIR_NAMES.append(_ENV_BUILD_DIR)
_BUILD_DIR_NAMES.extend(["build-workshop", "build-gpu", "build"])
for _build_dir_name in _BUILD_DIR_NAMES:
    _BUILD_DIR = _build_dir_name if os.path.isabs(_build_dir_name) else os.path.join(_REPO_ROOT, _build_dir_name)
    if os.path.isdir(_BUILD_DIR):
        for _name in ("ef_py", "ef_py.cpython-313-x86_64-linux-gnu.so"):
            if os.path.exists(os.path.join(_BUILD_DIR, _name)) or any(
                fname.startswith("ef_py") and fname.endswith(".so") for fname in os.listdir(_BUILD_DIR)
            ):
                if _BUILD_DIR in sys.path:
                    sys.path.remove(_BUILD_DIR)
                sys.path.insert(0, _BUILD_DIR)
                break
        if sys.path[0] == _BUILD_DIR:
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
from python.training import (
    build_train_arg_parser,
    prepare_training_bootstrap,
    print_training_bootstrap_summary,
    warn_execution_visual_rollout_memory,
)
from python.rl.policy_algo.policies import HierarchicalMoEExecutionPolicy, SquashedMultiInputPolicy
from python.rl.policy_algo.ppo_adaptive_kl import AdaptiveKLPPO
from python.rl.support.nonfinite_probe import NonFiniteProbeError, NonFiniteTrainingProbe
from python.rl.runtime.shared_memory_vec_env import SharedMemorySubprocVecEnv
from python.rl.runtime.cooperative_world_batch_vec_env import CooperativeWorldBatchVecEnv
from python.rl.runtime.world_batch_vec_env import WorldBatchVecEnv
from python.rl.control.wrappers import MultiTimescaleActionWrapper, get_action_wrapper_spec

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
        spawn_speed_mps = 0.0
        vel = agent.get("vel", []) if isinstance(agent, dict) else []
        if isinstance(vel, list) and len(vel) >= 3:
            try:
                vx = float(vel[0])
                vy = float(vel[1])
                vz = float(vel[2])
                spawn_speed_mps = float(math.sqrt(vx * vx + vy * vy + vz * vz))
            except Exception:
                spawn_speed_mps = 0.0
        cmd_code = int(mission.get("command_code", 0)) if isinstance(mission, dict) else 0

        airborne_start = spawn_alt_m > 50.0
        runway_start = (spawn_alt_m <= 10.0) and (spawn_speed_mps <= 15.0)
        if cmd_code == 4:
            throttle_default = 0.45
            gear_default = 1.0
            flaps_default = 1.0
            speedbrake_default = 0.0
        elif airborne_start or (cmd_code == 3 and not runway_start):
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
        policy = getattr(model, "policy", None)
        action_net = getattr(policy, "action_net", None)
        hmoe_head_bank = getattr(policy, "hmoe_head_bank", None)

        def _apply_bias_vector(b):
            if b is None:
                return
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

        has_standard_bias = action_net is not None and getattr(action_net, "bias", None) is not None
        has_hmoe_bias = hmoe_head_bank is not None
        if not has_standard_bias and not has_hmoe_bias:
            return
        squash = bool(getattr(policy, "squash_output", False))
        with torch.no_grad():
            if has_standard_bias:
                _apply_bias_vector(action_net.bias)
            if has_hmoe_bias:
                for head in getattr(hmoe_head_bank, "family_heads", []):
                    bias = getattr(head, "bias", None)
                    if bias is not None:
                        bias.zero_()
                for family_subheads in getattr(hmoe_head_bank, "subexpert_heads", []):
                    for head in family_subheads:
                        bias = getattr(head, "bias", None)
                        if bias is not None:
                            bias.zero_()
    except Exception:
        return


def maybe_initialize_hmoe_from_shared(
    model: PPO,
    *,
    train_config: dict,
    args: argparse.Namespace,
) -> bool:
    policy = getattr(model, "policy", None)
    init_fn = getattr(policy, "initialize_hmoe_from_shared_action_head", None)
    if not callable(init_fn):
        return False

    hmoe_cfg = train_config.get("hmoe", {}) if isinstance(train_config.get("hmoe", {}), dict) else {}
    bootstrap_mode = str(hmoe_cfg.get("bootstrap_from_shared_action_head", "auto")).strip().lower()
    if bootstrap_mode in ("", "none", "off", "false", "0", "disable", "disabled"):
        return False
    if args.resume_path:
        return False
    # When init_from is provided, honor the checkpoint weights as-is.
    if args.init_from:
        return False

    init_fn()
    return True


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


def _world_batch_worker_thread_summary(vec_env) -> tuple[int, int]:
    runtime_facade = getattr(vec_env, "runtime_facade", None)
    if runtime_facade is None:
        raise RuntimeError("World batch worker-thread logging requires a runtime_facade accessor.")
    return int(runtime_facade.worker_threads()), int(runtime_facade.effective_worker_threads())


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
    use_shared_memory_vec_env = bool(runtime_cfg.get("shared_memory_vec_env", False))

    if agent_layer != "leader":
        if int(n_envs) <= 1:
            return DummyVecEnv, {}, False
        return (SharedMemorySubprocVecEnv if use_shared_memory_vec_env else SubprocVecEnv), {}, False

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
        return DummyVecEnv, {}, False
    return (SharedMemorySubprocVecEnv if use_shared_memory_vec_env else SubprocVecEnv), {}, False

def main():
    parser = build_train_arg_parser()
    args = parser.parse_args()

    bootstrap = prepare_training_bootstrap(args)
    if bootstrap is None:
        return
    train_config = bootstrap.train_config
    agent_layer = bootstrap.agent_layer
    env_settings = bootstrap.env_settings
    scenario_path = bootstrap.scenario_path
    train_cfg_path = bootstrap.train_cfg_path
    exp_dir = bootstrap.exp_dir
    run_name = bootstrap.run_name
    ckpt_dir = bootstrap.ckpt_dir
    log_dir = bootstrap.log_dir
    runtime_cfg = bootstrap.runtime_cfg
    training_seed = bootstrap.training_seed
    n_envs = bootstrap.n_envs
    LeaderTrainingEnv = bootstrap.leader_env_cls
    LeaderBatchedVecEnv = bootstrap.leader_batched_vec_env_cls
    print_training_bootstrap_summary(bootstrap)
    warn_execution_visual_rollout_memory(bootstrap)

    if agent_layer == "execution":
        wrapper_class, wrapper_kwargs = get_action_wrapper_spec(train_config)
        use_world_batch_vec_env = bool(runtime_cfg.get("world_batch_vec_env", False))
        world_batch_action_wrapper_kwargs = None
        if use_world_batch_vec_env and wrapper_class is not None:
            if wrapper_class is MultiTimescaleActionWrapper:
                world_batch_action_wrapper_kwargs = dict(wrapper_kwargs or {})
            else:
                print(
                    "[WARN] runtime.world_batch_vec_env does not support the requested action wrapper. "
                    "Falling back to the standard vec env backend."
                )
                use_world_batch_vec_env = False

        if use_world_batch_vec_env:
            world_batch_threads = runtime_cfg.get("world_batch_threads")
            batch_visual_backend = str(runtime_cfg.get("batch_visual_backend", "auto"))
            batch_observation_backend = str(runtime_cfg.get("batch_observation_backend", "auto"))
            policy_observation_torch_bridge = bool(runtime_cfg.get("policy_observation_torch_bridge", True))
            observation_return_mode = str(runtime_cfg.get("observation_return_mode", "copy"))
            vec_env = WorldBatchVecEnv(
                scenario_path=scenario_path,
                n_envs=n_envs,
                worker_threads=world_batch_threads,
                batch_observation_backend=batch_observation_backend,
                batch_visual_backend=batch_visual_backend,
                policy_observation_torch_bridge=policy_observation_torch_bridge,
                observation_return_mode=observation_return_mode,
                action_wrapper_kwargs=world_batch_action_wrapper_kwargs,
                **env_settings,
            )
            vec_env.seed(training_seed)
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
            if world_batch_action_wrapper_kwargs:
                print("World batch action preprocessing: multi_timescale_action=enabled")
            active_batched_execution_inference = False
        else:
            # We must delay env creation for resume if we want to ensure same config?
            # For now we assume user provides correct params for resumption.
            if not bool(env_settings.get("runtime_compatibility_enabled", False)):
                raise RuntimeError(
                    "The standard UniversalEnv execution path owns a raw SimulationKernel and is "
                    "compatibility-only; set runtime.world_batch_vec_env=true for the maintained "
                    "production setup path, or set env.runtime_compatibility_enabled=true to opt in "
                    "to the quarantined legacy path explicitly."
                )
            vec_cls, vec_env_kwargs, active_batched_execution_inference = resolve_vec_env_spec(
                agent_layer=agent_layer,
                n_envs=n_envs,
                runtime_cfg=runtime_cfg,
                leader_batched_vec_env_cls=LeaderBatchedVecEnv,
            )
            vec_env = make_vec_env(
                UniversalEnv,
                n_envs=n_envs,
                env_kwargs={
                    "scenario_path": scenario_path,
                    **env_settings,
                },
                seed=training_seed,
                vec_env_cls=vec_cls,
                vec_env_kwargs=vec_env_kwargs,
                wrapper_class=wrapper_class,
                wrapper_kwargs=wrapper_kwargs,
            )
    elif agent_layer == "cooperative_execution":
        wrapper_class, wrapper_kwargs = get_action_wrapper_spec(train_config)
        if wrapper_class is not None and wrapper_class is not MultiTimescaleActionWrapper:
            print(
                "[WARN] cooperative_execution only supports the maintained multi_timescale action wrapper. "
                "Ignoring unsupported wrapper request."
            )
            wrapper_kwargs = None
        batch_visual_backend = str(runtime_cfg.get("batch_visual_backend", "auto"))
        batch_observation_backend = str(runtime_cfg.get("batch_observation_backend", "auto"))
        vec_env = CooperativeWorldBatchVecEnv(
            scenario_path=scenario_path,
            n_envs=n_envs,
            worker_threads=runtime_cfg.get("world_batch_threads"),
            batch_observation_backend=batch_observation_backend,
            batch_visual_backend=batch_visual_backend,
            action_wrapper_kwargs=wrapper_kwargs if wrapper_class is MultiTimescaleActionWrapper else None,
            **env_settings,
        )
        vec_env.seed(training_seed)
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
    else:
        vec_cls, vec_env_kwargs, active_batched_execution_inference = resolve_vec_env_spec(
            agent_layer=agent_layer,
            n_envs=n_envs,
            runtime_cfg=runtime_cfg,
            leader_batched_vec_env_cls=LeaderBatchedVecEnv,
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
            seed=training_seed,
            vec_env_cls=vec_cls,
            vec_env_kwargs=vec_env_kwargs,
        )

    effective_n_envs = int(getattr(vec_env, "num_envs", n_envs))
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
    if training_seed is not None and "seed" not in hyperparams:
        hyperparams = dict(hyperparams)
        hyperparams["seed"] = int(training_seed)
    total_timesteps = train_config.get("total_timesteps", 100000)
    save_freq = int(train_config.get("save_freq", 50000))
    # SB3 CheckpointCallback counts callback invocations, not aggregate env timesteps.
    # Interpret config `save_freq` as total timesteps so multi-env runs checkpoint on the
    # expected cadence instead of being stretched by `n_envs`.
    checkpoint_freq = max(1, int(math.ceil(float(save_freq) / float(max(1, effective_n_envs)))))

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
        elif policy_name == "HierarchicalMoEExecutionPolicy":
            policy_cls = HierarchicalMoEExecutionPolicy
        model = algo_cls(policy_cls, vec_env, verbose=1, tensorboard_log=log_dir, **hyperparams)
        hmoe_bootstrapped = maybe_initialize_hmoe_from_shared(
            model,
            train_config=train_config,
            args=args,
        )
        if hmoe_bootstrapped:
            print("HMoE bootstrap: initialized family heads from shared action head and reset subexpert residuals.")
        if args.init_from:
            init_path = os.path.abspath(args.init_from)
            if not os.path.exists(init_path):
                print(f"Error: Initialization checkpoint not found: {init_path}")
                return
            print(f"Initializing Parameters From: {init_path}")
            model.set_parameters(init_path, exact_match=False, device=hyperparams.get("device", "auto"))
        elif agent_layer in {"execution", "cooperative_execution"} and not args.no_init_safe_action_bias:
            apply_safe_action_bias(model, env_settings["action_mode"], scenario_path)
        elif agent_layer == "leader":
            apply_leader_action_bias(model)

    print(f"Rollout buffer: {type(model.rollout_buffer).__name__}")

    diagnostics_cfg = train_config.get("diagnostics", {}) if isinstance(train_config.get("diagnostics", {}), dict) else {}
    nonfinite_probe_enabled = diagnostics_cfg.get("nonfinite_probe")
    if args.nonfinite_probe is not None:
        nonfinite_probe_enabled = bool(args.nonfinite_probe)
    nonfinite_probe_enabled = bool(nonfinite_probe_enabled)

    nonfinite_probe_report = args.nonfinite_probe_report
    if nonfinite_probe_report is None:
        nonfinite_probe_report = diagnostics_cfg.get("nonfinite_probe_report")
    if nonfinite_probe_report is None:
        nonfinite_probe_report = os.path.join(exp_dir, "nonfinite_probe_report.json")
    elif not os.path.isabs(nonfinite_probe_report):
        nonfinite_probe_report = os.path.abspath(os.path.join(exp_dir, nonfinite_probe_report))

    nonfinite_probe_history = args.nonfinite_probe_history
    if nonfinite_probe_history is None:
        nonfinite_probe_history = diagnostics_cfg.get("nonfinite_probe_history", 384)
    nonfinite_probe_history = max(32, int(nonfinite_probe_history))

    probe = None
    if nonfinite_probe_enabled:
        probe = NonFiniteTrainingProbe(
            report_path=str(nonfinite_probe_report),
            history_limit=int(nonfinite_probe_history),
            run_metadata={
                "scenario": scenario_path,
                "train_config": train_cfg_path,
                "exp_dir": exp_dir,
                "run_name": run_name,
                "agent_layer": agent_layer,
                "resume_path": os.path.abspath(args.resume_path) if args.resume_path else None,
                "seed": None if training_seed is None else int(training_seed),
            },
            enabled=True,
        )
        probe.install(model)
        print(
            "Non-finite probe: "
            f"enabled=1 report={nonfinite_probe_report} history={int(nonfinite_probe_history)}"
        )
    else:
        print("Non-finite probe: enabled=0")
    
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
    force_hmoe_diagnostics = bool(getattr(model, "policy", None) is not None and hasattr(model.policy, "get_hmoe_route_stats"))
    if args.diagnostics or force_hmoe_diagnostics:
        callbacks.append(
            CMODiagnosticsCallback(
                log_every_timesteps=int(args.diagnostics_every),
                preterm_window_steps=int(args.diagnostics_preterm_window),
            )
        )
        if force_hmoe_diagnostics and not args.diagnostics:
            print("Diagnostics: auto-enabled for HMoE route/parameter observability.")
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
    except NonFiniteProbeError as exc:
        print("\nTraining aborted by non-finite probe.")
        if probe is not None:
            report_path = probe.write_error_report(model, exc)
            print(f"Non-finite probe report written to {report_path}")
        save_path = os.path.join(ckpt_dir, "nonfinite_probe_abort_model")
        print(f"Saving abort checkpoint to {save_path}...")
        model.save(save_path)
        print("Done.")
        raise

if __name__ == "__main__":
    main()
