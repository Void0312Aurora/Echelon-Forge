"""Universal training entrypoint (thin orchestration).

Implementation lives in `python/training/`:
- `python.training.bootstrap`: config/scenario validation, run layout, seeding
- `python.training.deps`: lazy torch/SB3/policy dependency loading
- `python.training.action_bias`: initial action-head bias helpers
- `python.training.vec_env_factory`: vec-env backend selection and construction

The module-level names re-exported below are a compatibility surface for
existing callers (tests and diagnostics tools import them from `train`).
"""

from __future__ import annotations

import argparse
import math
import os
import sys

from python.runtime_bootstrap import configure_repo_imports


configure_repo_imports()

from python.training import (
    build_train_arg_parser,
    prepare_training_bootstrap,
    print_training_bootstrap_summary,
    warn_execution_visual_rollout_memory,
)
from python.training.action_bias import (
    apply_leader_action_bias,
    apply_safe_action_bias,
    infer_full_action_safe_defaults,
    maybe_initialize_hmoe_from_shared,
)
from python.training.bootstrap import apply_global_seed
from python.training.deps import (
    apply_policy_kwargs_feature_extractor_classes,
    get_policy_kwargs,
    load_training_dependencies,
)
from python.training.vec_env_factory import (
    build_cooperative_world_batch_vec_env,
    build_execution_world_batch_vec_env,
    build_leader_vec_env,
    print_test_only_preflight_runtime_summary,
    resolve_vec_env_spec,
)

__all__ = [
    "apply_global_seed",
    "apply_leader_action_bias",
    "apply_safe_action_bias",
    "get_policy_kwargs",
    "infer_full_action_safe_defaults",
    "load_training_dependencies",
    "main",
    "maybe_initialize_hmoe_from_shared",
    "resolve_vec_env_spec",
]


def _load_training_dependencies():
    """Compatibility shim for the historical in-module dependency loader."""
    return load_training_dependencies()


def _resolve_test_only_load_path(args: argparse.Namespace, exp_dir: str) -> str | None:
    if args.resume_path:
        return args.resume_path
    possible_path = os.path.join(exp_dir, "final_model.zip")
    if os.path.exists(possible_path):
        return possible_path
    return None


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
    training_seed = bootstrap.training_seed
    n_envs = bootstrap.n_envs
    print_training_bootstrap_summary(bootstrap)
    warn_execution_visual_rollout_memory(bootstrap)

    test_only_load_path = _resolve_test_only_load_path(args, exp_dir) if args.test_only else None
    if args.test_only and test_only_load_path is None:
        print_test_only_preflight_runtime_summary(bootstrap)
        print("Error: --test_only requires --resume_path or a valid existing run directory with final_model.zip")
        return

    deps = load_training_dependencies()

    if agent_layer == "execution":
        vec_env = build_execution_world_batch_vec_env(bootstrap)
        if vec_env is None:
            raise RuntimeError(
                "The standard UniversalEnv execution path owns a raw SimulationKernel and is "
                "retired from the maintained training config surface; set runtime.world_batch_vec_env=true "
                "for the maintained production setup path. Direct raw UniversalEnv diagnostics must be run outside "
                "the maintained training config surface."
            )
    elif agent_layer == "cooperative_execution":
        vec_env = build_cooperative_world_batch_vec_env(bootstrap)
    else:
        vec_env = build_leader_vec_env(bootstrap)

    effective_n_envs = int(getattr(vec_env, "num_envs", n_envs))
    curriculum_cfg = train_config.get("curriculum", {}) if isinstance(train_config.get("curriculum", {}), dict) else {}
    algo_name = str(train_config.get("algo", "PPO"))
    algo_cls = deps.PPO
    if algo_name in ("AdaptiveKLPPO", "PPOAdaptiveKL", "PPO_AdaptiveKL"):
        algo_cls = deps.AdaptiveKLPPO

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
        load_path = test_only_load_path
        assert load_path is not None
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
    apply_policy_kwargs_feature_extractor_classes(hyperparams)

    if args.resume_path:
        print(f"Loading Checkpoint: {args.resume_path}")
        model = algo_cls.load(args.resume_path, env=vec_env, tensorboard_log=log_dir)
    else:
        policy_name = train_config.get("policy", "MultiInputPolicy")
        policy_cls = policy_name
        if policy_name == "SquashedMultiInputPolicy":
            policy_cls = deps.SquashedMultiInputPolicy
        elif policy_name == "HierarchicalMoEExecutionPolicy":
            policy_cls = deps.HierarchicalMoEExecutionPolicy
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
            apply_safe_action_bias(model, env_settings["action_mode"], scenario_path, train_config=train_config)
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
        probe = deps.NonFiniteTrainingProbe(
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

    checkpoint_callback = deps.CheckpointCallback(
        save_freq=checkpoint_freq,
        save_path=ckpt_dir,
        name_prefix="model" # naming: model_50000_steps.zip
    )
    callbacks = [checkpoint_callback]
    force_hmoe_diagnostics = bool(getattr(model, "policy", None) is not None and hasattr(model.policy, "get_hmoe_route_stats"))
    if args.diagnostics or force_hmoe_diagnostics:
        callbacks.append(
            deps.CMODiagnosticsCallback(
                log_every_timesteps=int(args.diagnostics_every),
                preterm_window_steps=int(args.diagnostics_preterm_window),
            )
        )
        if force_hmoe_diagnostics and not args.diagnostics:
            print("Diagnostics: auto-enabled for HMoE route/parameter observability.")
    if isinstance(curriculum_cfg, dict) and curriculum_cfg.get("stages"):
        callbacks.append(
            deps.ScenarioCurriculumCallback(
                stages=list(curriculum_cfg["stages"]),
                check_freq=int(curriculum_cfg.get("check_freq", 10_000)),
            )
        )

    early_stop_cfg = train_config.get("early_stop", {}) if isinstance(train_config.get("early_stop", {}), dict) else {}
    best_ema_ckpt = os.path.join(ckpt_dir, "best_ema_model.zip")
    if bool(early_stop_cfg.get("enabled", False)):
        callbacks.append(
            deps.RewardPlateauEarlyStopCallback(
                min_timesteps=int(early_stop_cfg.get("min_timesteps", 200_000)),
                check_every_timesteps=int(early_stop_cfg.get("check_every_timesteps", 20_000)),
                patience_checks=int(early_stop_cfg.get("patience_checks", 6)),
                min_improvement=float(early_stop_cfg.get("min_improvement", 0.5)),
                ema_alpha=float(early_stop_cfg.get("ema_alpha", 0.05)),
                best_model_path=os.path.join(ckpt_dir, "best_ema_model"),
                verbose=1,
            )
        )

    callback = deps.CallbackList(callbacks) if len(callbacks) > 1 else checkpoint_callback
    
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
    except deps.NonFiniteProbeError as exc:
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
