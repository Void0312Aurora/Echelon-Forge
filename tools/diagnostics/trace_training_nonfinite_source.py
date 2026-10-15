#!/usr/bin/env python3
"""
Trace the first non-finite tensor during resumed PPO training.

This script is diagnostic-only. It reconstructs the maintained cooperative
training flow from `train.py`, patches the loaded policy/algo with finite-value
probes, and stops on the first NaN/Inf with a JSON report.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import traceback
from collections import deque
from pathlib import Path
from types import MethodType, SimpleNamespace
from typing import Any

import numpy as np
import torch as th
from gymnasium import spaces
from torch.nn import functional as F

from python.runtime_bootstrap import configure_sim_log_level, ensure_repo_imports

REPO_ROOT = ensure_repo_imports()
os.chdir(REPO_ROOT)

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback, CallbackList
from stable_baselines3.common.distributions import (
    BernoulliDistribution,
    CategoricalDistribution,
    DiagGaussianDistribution,
    MultiCategoricalDistribution,
    StateDependentNoiseDistribution,
)
from stable_baselines3.common.utils import explained_variance, obs_as_tensor
from stable_baselines3.common.vec_env import VecEnv

from train import apply_global_seed
from python.env_config import resolve_env_settings
from python.models.transformer import TransformerExtractor, TransformerVisualExtractor
from python.rl.runtime.cooperative_world_batch_vec_env import CooperativeWorldBatchVecEnv
from python.rl.policy_algo.policies import SquashedMultiInputPolicy
from python.rl.policy_algo.ppo_adaptive_kl import AdaptiveKLPPO
from python.rl.control.wrappers import MultiTimescaleActionWrapper, get_action_wrapper_spec
from python.training_callbacks import ScenarioCurriculumCallback
from tools.diagnostics.common import add_model_load_args, add_probe_run_args


class NonFiniteTraceError(RuntimeError):
    """Raised when the first NaN/Inf is observed."""

    def __init__(self, report: dict[str, Any]):
        self.report = report
        stage = report.get("stage", "<unknown>")
        super().__init__(f"non-finite detected at {stage}")


def _json_default(value: Any) -> Any:
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if th.is_tensor(value):
        return value.detach().cpu().tolist()
    return repr(value)


def _to_numpy(value: Any) -> np.ndarray:
    if th.is_tensor(value):
        return value.detach().float().cpu().numpy()
    return np.asarray(value)


def _summary_for_value(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return {
            "kind": "dict",
            "keys": list(value.keys()),
            "items": {str(key): _summary_for_value(item) for key, item in value.items()},
        }

    arr = _to_numpy(value)
    arr = np.asarray(arr)
    summary: dict[str, Any] = {
        "kind": "tensor" if th.is_tensor(value) else "array",
        "shape": list(arr.shape),
        "dtype": str(arr.dtype),
    }
    if th.is_tensor(value):
        summary["device"] = str(value.device)
        summary["requires_grad"] = bool(value.requires_grad)

    if arr.size == 0:
        summary.update(
            {
                "size": 0,
                "finite": True,
                "nan_count": 0,
                "posinf_count": 0,
                "neginf_count": 0,
            }
        )
        return summary

    flat = arr.reshape(-1)
    finite_mask = np.isfinite(flat)
    nan_mask = np.isnan(flat)
    posinf_mask = np.isposinf(flat)
    neginf_mask = np.isneginf(flat)

    summary.update(
        {
            "size": int(flat.size),
            "finite": bool(finite_mask.all()),
            "nan_count": int(nan_mask.sum()),
            "posinf_count": int(posinf_mask.sum()),
            "neginf_count": int(neginf_mask.sum()),
        }
    )

    finite_values = flat[finite_mask]
    if finite_values.size > 0:
        summary.update(
            {
                "min": float(finite_values.min()),
                "max": float(finite_values.max()),
                "mean": float(finite_values.mean()),
                "std": float(finite_values.std()),
            }
        )

    if not finite_mask.all():
        first_bad = int(np.flatnonzero(~finite_mask)[0])
        summary["first_bad_flat_index"] = first_bad
        try:
            summary["first_bad_index"] = list(np.unravel_index(first_bad, arr.shape))
        except Exception:
            summary["first_bad_index"] = [first_bad]
        summary["first_bad_value"] = repr(flat[first_bad])

    return summary


def _summary_for_named_tensors(named_tensors: list[tuple[str, Any]]) -> dict[str, Any]:
    bad: list[dict[str, Any]] = []
    count = 0
    for name, value in named_tensors:
        summary = _summary_for_value(value)
        if not bool(summary.get("finite", True)):
            entry = {"name": str(name), "summary": summary}
            bad.append(entry)
        count += 1
    return {
        "kind": "named_tensors",
        "count": int(count),
        "finite": len(bad) == 0,
        "bad": bad[:16],
    }


def _parameter_payload(module: th.nn.Module) -> list[tuple[str, Any]]:
    return [(name, param.data) for name, param in module.named_parameters()]


def _gradient_payload(module: th.nn.Module) -> list[tuple[str, Any]]:
    payload: list[tuple[str, Any]] = []
    for name, param in module.named_parameters():
        if param.grad is not None:
            payload.append((name, param.grad))
    return payload


class TraceRecorder:
    def __init__(self, *, history_limit: int = 256):
        self.history: deque[dict[str, Any]] = deque(maxlen=int(history_limit))
        self.context: dict[str, Any] = {}

    def set_context(self, **kwargs: Any) -> None:
        self.context.update(kwargs)

    def _record(self, stage: str, summary: dict[str, Any], *, note: str | None = None) -> None:
        event = {
            "stage": str(stage),
            "context": dict(self.context),
            "summary": summary,
        }
        if note:
            event["note"] = str(note)
        self.history.append(event)

    def check(self, stage: str, value: Any, *, note: str | None = None) -> None:
        summary = _summary_for_value(value)
        self._record(stage, summary, note=note)
        if not bool(summary.get("finite", True)):
            raise NonFiniteTraceError(
                {
                    "stage": str(stage),
                    "context": dict(self.context),
                    "summary": summary,
                    "recent_history": list(self.history),
                }
            )

    def check_named_tensors(self, stage: str, named_tensors: list[tuple[str, Any]], *, note: str | None = None) -> None:
        summary = _summary_for_named_tensors(named_tensors)
        self._record(stage, summary, note=note)
        if not bool(summary.get("finite", True)):
            raise NonFiniteTraceError(
                {
                    "stage": str(stage),
                    "context": dict(self.context),
                    "summary": summary,
                    "recent_history": list(self.history),
                }
            )


class _TrainingTraceObserver:
    """Adapter for the canonical PPO observation points."""

    def __init__(self, recorder: TraceRecorder):
        self.recorder = recorder

    def observe(
        self,
        stage: str,
        *,
        value=None,
        named_tensors=None,
        context: dict[str, Any] | None = None,
    ) -> None:
        if context:
            self.recorder.set_context(**context)
        if named_tensors is not None:
            self.recorder.check_named_tensors(stage, list(named_tensors))
        elif value is not None:
            self.recorder.check(stage, value)

class _PassThroughCallback(BaseCallback):
    def _on_step(self) -> bool:
        return True


def _algo_class_from_name(name: str):
    normalized = str(name or "PPO").strip()
    if normalized in ("AdaptiveKLPPO", "PPOAdaptiveKL", "PPO_AdaptiveKL"):
        return AdaptiveKLPPO
    return PPO


def _build_env_settings(train_config: dict[str, Any]) -> dict[str, Any]:
    args = SimpleNamespace(
        include_visual=None,
        include_proprio=None,
        mission_obs_mode=None,
        visual_downsample=None,
        visual_update_interval=None,
        action_mode=None,
        execution_step_runtime_mode=None,
        step_info_mode=None,
        flight_shaping_backend=None,
    )
    return resolve_env_settings(train_config, args)


def _build_cooperative_env(
    *,
    scenario_path: str,
    train_config: dict[str, Any],
    training_seed: int | None,
) -> VecEnv:
    runtime_cfg = train_config.get("runtime", {}) if isinstance(train_config.get("runtime", {}), dict) else {}
    env_settings = _build_env_settings(train_config)
    wrapper_class, wrapper_kwargs = get_action_wrapper_spec(train_config)
    if wrapper_class is not None and wrapper_class is not MultiTimescaleActionWrapper:
        raise ValueError("cooperative_execution diagnostics only supports MultiTimescaleActionWrapper")
    vec_env = CooperativeWorldBatchVecEnv(
        scenario_path=os.path.abspath(scenario_path),
        n_envs=int(train_config.get("n_envs", 1)),
        worker_threads=runtime_cfg.get("world_batch_threads"),
        batch_observation_backend=str(runtime_cfg.get("batch_observation_backend", "auto")),
        batch_visual_backend=str(runtime_cfg.get("batch_visual_backend", "auto")),
        action_wrapper_kwargs=wrapper_kwargs if wrapper_class is MultiTimescaleActionWrapper else None,
        **env_settings,
    )
    vec_env.seed(training_seed)
    return vec_env


def _apply_initial_curriculum_stage(vec_env: VecEnv, train_config: dict[str, Any]) -> None:
    curriculum_cfg = train_config.get("curriculum", {}) if isinstance(train_config.get("curriculum", {}), dict) else {}
    stages = curriculum_cfg.get("stages")
    if not isinstance(stages, list) or not stages:
        return
    stage0 = stages[0]
    overrides0 = stage0.get("randomization_overrides", stage0.get("randomization", {}))
    vec_env.env_method("set_randomization_overrides", overrides0)
    leader_overrides0 = stage0.get("leader_env_overrides", {})
    if isinstance(leader_overrides0, dict) and leader_overrides0:
        vec_env.env_method("set_leader_overrides", leader_overrides0)


def _build_callback(train_config: dict[str, Any]) -> BaseCallback | CallbackList | None:
    callbacks: list[BaseCallback] = []
    curriculum_cfg = train_config.get("curriculum", {}) if isinstance(train_config.get("curriculum", {}), dict) else {}
    stages = curriculum_cfg.get("stages")
    if isinstance(stages, list) and stages:
        callbacks.append(
            ScenarioCurriculumCallback(
                stages=list(stages),
                check_freq=int(curriculum_cfg.get("check_freq", 10_000)),
            )
        )
    if not callbacks:
        return _PassThroughCallback()
    if len(callbacks) == 1:
        return callbacks[0]
    return CallbackList(callbacks)


def _patch_transformer_extractor(extractor: TransformerExtractor, tracer: TraceRecorder) -> None:
    def traced_forward(self, observations: dict[str, th.Tensor]) -> th.Tensor:
        tracer.check("extractor.obs.instruments", observations["instruments"])
        tracer.check("extractor.obs.contacts", observations["contacts"])
        tracer.check("extractor.obs.rwr", observations["rwr"])
        tracer.check("extractor.obs.mission", observations["mission"])
        if self.has_proprio:
            tracer.check("extractor.obs.proprio", observations["proprio"])

        with th.autocast("cuda", enabled=(th.cuda.is_available() and self.use_amp)):
            s_inst = observations["instruments"]
            s_contacts = observations["contacts"]
            s_rwr = observations["rwr"]
            s_mission = observations["mission"]

            emb_inst = self.embed_instruments(s_inst).unsqueeze(1) + self.type_embed(self.idx_inst)
            tracer.check("extractor.emb_inst", emb_inst)

            emb_contacts = self.embed_contact(s_contacts) + self.type_embed(self.idx_contact)
            tracer.check("extractor.emb_contacts", emb_contacts)

            emb_rwr = self.embed_rwr(s_rwr) + self.type_embed(self.idx_rwr)
            tracer.check("extractor.emb_rwr", emb_rwr)

            emb_mission = self.embed_mission(s_mission).unsqueeze(1) + self.type_embed(self.idx_mission)
            tracer.check("extractor.emb_mission", emb_mission)

            emb_parts = [emb_inst, emb_mission]
            if self.has_proprio:
                emb_proprio = self.embed_proprio(observations["proprio"]).unsqueeze(1) + self.type_embed(self.idx_proprio)
                tracer.check("extractor.emb_proprio", emb_proprio)
                emb_parts.append(emb_proprio)

            sequence = th.cat([*emb_parts, emb_contacts, emb_rwr], dim=1)
            tracer.check("extractor.sequence", sequence)

            x = sequence
            if self._use_checkpointing and self.training:
                from torch.utils.checkpoint import checkpoint

                for layer_idx, layer in enumerate(self.transformer.layers):
                    x = checkpoint(layer, x, use_reentrant=False)
                    tracer.check(f"extractor.layer_{layer_idx}.out", x)
            else:
                for layer_idx, layer in enumerate(self.transformer.layers):
                    x = layer(x)
                    tracer.check(f"extractor.layer_{layer_idx}.out", x)
                if self.transformer.norm is not None:
                    x = self.transformer.norm(x)
                    tracer.check("extractor.encoder_norm", x)

            cls_token = x[:, 0, :]
            tracer.check("extractor.cls_token", cls_token)
            out = self.ln_final(cls_token)
            tracer.check("extractor.ln_final", out)
        out = out.float()
        tracer.check("extractor.output", out)
        return out

    extractor.forward = MethodType(traced_forward, extractor)


def _patch_policy(policy: SquashedMultiInputPolicy, tracer: TraceRecorder) -> None:
    if isinstance(policy.features_extractor, TransformerExtractor):
        _patch_transformer_extractor(policy.features_extractor, tracer)
    elif isinstance(policy.features_extractor, TransformerVisualExtractor):
        raise ValueError("this tracer currently targets TransformerExtractor-based policies only")

    def traced_get_action_dist_from_latent(self, latent_pi: th.Tensor):
        tracer.check("policy.latent_pi.pre_dist", latent_pi)
        mean_actions = self.action_net(latent_pi)
        tracer.check("policy.mean_actions", mean_actions)

        if hasattr(self, "log_std"):
            tracer.check("policy.log_std", self.log_std)
            action_std = th.ones_like(mean_actions) * self.log_std.exp()
            tracer.check("policy.action_std", action_std)

        if isinstance(self.action_dist, DiagGaussianDistribution):
            return self.action_dist.proba_distribution(mean_actions, self.log_std)
        if isinstance(self.action_dist, CategoricalDistribution):
            return self.action_dist.proba_distribution(action_logits=mean_actions)
        if isinstance(self.action_dist, MultiCategoricalDistribution):
            return self.action_dist.proba_distribution(action_logits=mean_actions)
        if isinstance(self.action_dist, BernoulliDistribution):
            return self.action_dist.proba_distribution(action_logits=mean_actions)
        if isinstance(self.action_dist, StateDependentNoiseDistribution):
            return self.action_dist.proba_distribution(mean_actions, self.log_std, latent_pi)
        raise ValueError("Invalid action distribution")

    def traced_forward(self, obs, deterministic: bool = False):
        if isinstance(obs, dict):
            for key, value in obs.items():
                tracer.check(f"policy.forward.obs.{key}", value)
        else:
            tracer.check("policy.forward.obs", obs)

        features = self.extract_features(obs)
        if isinstance(features, tuple):
            tracer.check("policy.forward.features.pi", features[0])
            tracer.check("policy.forward.features.vf", features[1])
            latent_pi = self.mlp_extractor.forward_actor(features[0])
            latent_vf = self.mlp_extractor.forward_critic(features[1])
        else:
            tracer.check("policy.forward.features", features)
            latent_pi, latent_vf = self.mlp_extractor(features)
        tracer.check("policy.forward.latent_pi", latent_pi)
        tracer.check("policy.forward.latent_vf", latent_vf)

        values = self.value_net(latent_vf)
        tracer.check("policy.forward.values", values)
        distribution = self._get_action_dist_from_latent(latent_pi)
        actions = distribution.get_actions(deterministic=deterministic)
        tracer.check("policy.forward.actions.raw", actions)
        log_prob = distribution.log_prob(actions)
        tracer.check("policy.forward.log_prob", log_prob)
        actions = actions.reshape((-1, *self.action_space.shape))
        tracer.check("policy.forward.actions.reshaped", actions)
        return actions, values, log_prob

    def traced_evaluate_actions(self, obs, actions: th.Tensor):
        if isinstance(obs, dict):
            for key, value in obs.items():
                tracer.check(f"policy.evaluate.obs.{key}", value)
        else:
            tracer.check("policy.evaluate.obs", obs)
        tracer.check("policy.evaluate.actions.input", actions)

        features = self.extract_features(obs)
        if isinstance(features, tuple):
            tracer.check("policy.evaluate.features.pi", features[0])
            tracer.check("policy.evaluate.features.vf", features[1])
            latent_pi = self.mlp_extractor.forward_actor(features[0])
            latent_vf = self.mlp_extractor.forward_critic(features[1])
        else:
            tracer.check("policy.evaluate.features", features)
            latent_pi, latent_vf = self.mlp_extractor(features)
        tracer.check("policy.evaluate.latent_pi", latent_pi)
        tracer.check("policy.evaluate.latent_vf", latent_vf)

        distribution = self._get_action_dist_from_latent(latent_pi)
        log_prob = distribution.log_prob(actions)
        tracer.check("policy.evaluate.log_prob", log_prob)
        values = self.value_net(latent_vf)
        tracer.check("policy.evaluate.values", values)
        entropy = distribution.entropy()
        if entropy is not None:
            tracer.check("policy.evaluate.entropy", entropy)
        return values, log_prob, entropy

    def traced_predict_values(self, obs):
        if isinstance(obs, dict):
            for key, value in obs.items():
                tracer.check(f"policy.predict_values.obs.{key}", value)
        else:
            tracer.check("policy.predict_values.obs", obs)

        features = super(type(self), self).extract_features(obs, self.vf_features_extractor)
        tracer.check("policy.predict_values.features", features)
        latent_vf = self.mlp_extractor.forward_critic(features)
        tracer.check("policy.predict_values.latent_vf", latent_vf)
        values = self.value_net(latent_vf)
        tracer.check("policy.predict_values.values", values)
        return values

    policy._get_action_dist_from_latent = MethodType(traced_get_action_dist_from_latent, policy)
    policy.forward = MethodType(traced_forward, policy)
    policy.evaluate_actions = MethodType(traced_evaluate_actions, policy)
    policy.predict_values = MethodType(traced_predict_values, policy)


def _patch_algo(model: AdaptiveKLPPO, tracer: TraceRecorder) -> None:
    """Observe the maintained PPO implementation without replacing it."""
    setattr(model, "_training_observer", _TrainingTraceObserver(tracer))

def _write_report(path: str, report: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=True, indent=2, default=_json_default)


def _print_summary(report: dict[str, Any]) -> None:
    summary = {
        "status": report.get("status"),
        "report_path": report.get("report_path"),
        "resume_path": report.get("resume_path"),
        "timesteps_requested": report.get("timesteps_requested"),
        "model_num_timesteps_at_load": report.get("model_num_timesteps_at_load"),
        "model_num_timesteps_after_run": report.get("model_num_timesteps_after_run"),
        "model_num_timesteps_at_failure": report.get("model_num_timesteps_at_failure"),
    }
    failure = report.get("failure")
    if isinstance(failure, dict):
        summary["failure_stage"] = failure.get("stage")
        summary["failure_context"] = failure.get("context")
    print(json.dumps(summary, ensure_ascii=True, indent=2, default=_json_default))


def main() -> int:
    parser = argparse.ArgumentParser(description="Trace the first non-finite tensor during resumed PPO training.")
    add_probe_run_args(
        parser,
        include=["scenario"],
        defaults={"scenario": "experiments/coop_takeoff_to_cruise_formal_fixed_20260513/scenario_backup.json"},
        helps={"scenario": "Scenario JSON used for the failing run."},
    )
    add_model_load_args(
        parser,
        include=["train_config"],
        defaults={"train_config": "experiments/coop_takeoff_to_cruise_formal_fixed_20260513/train_config_backup.json"},
        helps={"train_config": "Train config JSON used for the failing run."},
    )
    parser.add_argument(
        "--resume_path",
        default="experiments/coop_takeoff_to_cruise_formal_fixed_20260513/checkpoints/model_65536_steps.zip",
        help="Checkpoint to resume from.",
    )
    parser.add_argument(
        "--timesteps",
        type=int,
        default=8192,
        help="Additional timesteps to train after loading the checkpoint.",
    )
    add_probe_run_args(
        parser,
        include=["seed"],
        defaults={"seed": None},
        helps={"seed": "Optional global seed. Defaults to the train config seed when present."},
    )
    parser.add_argument(
        "--report_path",
        default="output/trace_training_nonfinite_source_report.json",
        help="Path to the JSON report.",
    )
    parser.add_argument(
        "--sim_log_level",
        default="warn",
        choices=["debug", "info", "warn", "error"],
        help="Simulator log level for the diagnostic run.",
    )
    args = parser.parse_args()

    configure_sim_log_level(args.sim_log_level)

    scenario_path = os.path.abspath(args.scenario)
    train_config_path = os.path.abspath(args.train_config)
    resume_path = os.path.abspath(args.resume_path)
    report_path = os.path.abspath(args.report_path)

    with open(train_config_path, "r", encoding="utf-8") as f:
        train_config = json.load(f)

    training_seed = args.seed
    if training_seed is None and "seed" in train_config:
        try:
            training_seed = int(train_config.get("seed"))
        except Exception:
            training_seed = None
    if training_seed is not None:
        apply_global_seed(int(training_seed))

    algo_cls = _algo_class_from_name(str(train_config.get("algo", "PPO")))
    vec_env = _build_cooperative_env(
        scenario_path=scenario_path,
        train_config=train_config,
        training_seed=training_seed,
    )
    _apply_initial_curriculum_stage(vec_env, train_config)
    callback = _build_callback(train_config)

    tracer = TraceRecorder(history_limit=384)

    model = algo_cls.load(resume_path, env=vec_env, tensorboard_log=None)
    if not isinstance(model, AdaptiveKLPPO):
        raise TypeError(f"expected AdaptiveKLPPO checkpoint, got {type(model)}")
    if not isinstance(model.policy, SquashedMultiInputPolicy):
        raise TypeError(f"expected SquashedMultiInputPolicy, got {type(model.policy)}")

    tracer.set_context(
        phase="setup",
        num_timesteps=int(model.num_timesteps),
        policy_class=type(model.policy).__name__,
        extractor_class=type(model.policy.features_extractor).__name__,
    )
    tracer.check_named_tensors("setup.params.loaded", _parameter_payload(model.policy))
    _patch_policy(model.policy, tracer)
    _patch_algo(model, tracer)

    report: dict[str, Any] = {
        "status": "ok",
        "scenario": scenario_path,
        "train_config": train_config_path,
        "resume_path": resume_path,
        "report_path": report_path,
        "timesteps_requested": int(args.timesteps),
        "seed": None if training_seed is None else int(training_seed),
        "model_num_timesteps_at_load": int(model.num_timesteps),
        "policy_kwargs": getattr(model, "policy_kwargs", None),
        "device": str(model.device),
        "cuda_available": bool(th.cuda.is_available()),
        "cuda_device_name": th.cuda.get_device_name(0) if th.cuda.is_available() else None,
    }

    try:
        model.learn(total_timesteps=int(args.timesteps), callback=callback, reset_num_timesteps=False)
        report["status"] = "completed_without_nonfinite"
        report["model_num_timesteps_after_run"] = int(model.num_timesteps)
        report["recent_history"] = list(tracer.history)
    except NonFiniteTraceError as exc:
        report["status"] = "nonfinite_detected"
        report["model_num_timesteps_at_failure"] = int(model.num_timesteps)
        report["failure"] = exc.report
        report["recent_history"] = list(tracer.history)
    except Exception as exc:  # pragma: no cover - unexpected diagnostic failure
        report["status"] = "unexpected_exception"
        report["model_num_timesteps_at_failure"] = int(model.num_timesteps)
        report["exception"] = repr(exc)
        report["traceback"] = traceback.format_exc()
        report["recent_history"] = list(tracer.history)
        _write_report(report_path, report)
        _print_summary(report)
        return 2
    finally:
        try:
            vec_env.close()
        except Exception:
            pass

    _write_report(report_path, report)
    _print_summary(report)
    return 0 if report["status"] != "unexpected_exception" else 2


if __name__ == "__main__":
    raise SystemExit(main())
