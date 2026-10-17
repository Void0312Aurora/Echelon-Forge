from __future__ import annotations

import json
import os
from collections import deque
from types import MethodType
from typing import Any

import numpy as np
import torch as th
from gymnasium import spaces
from torch.nn import functional as F

from stable_baselines3.common.distributions import (
    BernoulliDistribution,
    CategoricalDistribution,
    DiagGaussianDistribution,
    MultiCategoricalDistribution,
    StateDependentNoiseDistribution,
)

from python.models.transformer import (
    TemporalTransformerExtractor,
    TransformerExtractor,
    TransformerVisualExtractor,
    preprocess_transformer_observations,
)
from python.rl.policy_algo.policies import SquashedMultiInputPolicy


class NonFiniteProbeError(RuntimeError):
    """Raised when the non-finite probe observes the first NaN/Inf."""

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
        items = {str(key): _summary_for_value(item) for key, item in value.items()}
        return {
            "kind": "dict",
            "keys": list(value.keys()),
            "items": items,
            "finite": all(bool(item.get("finite", True)) for item in items.values()),
        }

    arr = np.asarray(_to_numpy(value))
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
            bad.append({"name": str(name), "summary": summary})
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
        self.history: deque[dict[str, Any]] = deque(maxlen=max(1, int(history_limit)))
        self.context: dict[str, Any] = {}

    def set_context(self, **kwargs: Any) -> None:
        self.context.update(kwargs)

    def record(self, stage: str, summary: dict[str, Any], *, note: str | None = None) -> None:
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
        self.record(stage, summary, note=note)
        if not bool(summary.get("finite", True)):
            raise NonFiniteProbeError(
                {
                    "stage": str(stage),
                    "context": dict(self.context),
                    "summary": summary,
                    "recent_history": list(self.history),
                }
            )

    def check_named_tensors(self, stage: str, named_tensors: list[tuple[str, Any]], *, note: str | None = None) -> None:
        summary = _summary_for_named_tensors(named_tensors)
        self.record(stage, summary, note=note)
        if not bool(summary.get("finite", True)):
            raise NonFiniteProbeError(
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

def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def write_nonfinite_probe_report(path: str, report: dict[str, Any]) -> None:
    _ensure_parent_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=True, indent=2, default=_json_default)


class NonFiniteTrainingProbe:
    """
    Runtime training probe that aborts on the first non-finite tensor and writes a report.

    This is meant for real training runs, so it is opt-in and activated from `train.py`
    after model construction/loading.
    """

    def __init__(
        self,
        *,
        report_path: str,
        run_metadata: dict[str, Any] | None = None,
        history_limit: int = 384,
        enabled: bool = True,
    ):
        self.report_path = os.path.abspath(report_path)
        self.enabled = bool(enabled)
        self.run_metadata = dict(run_metadata or {})
        self.recorder = TraceRecorder(history_limit=history_limit)

    def install(self, model) -> None:
        if not self.enabled:
            return
        policy = getattr(model, "policy", None)
        if not isinstance(policy, SquashedMultiInputPolicy):
            raise TypeError(f"non-finite probe currently expects SquashedMultiInputPolicy, got {type(policy)}")

        self.recorder.set_context(
            phase="setup",
            policy_class=type(policy).__name__,
            extractor_class=type(policy.features_extractor).__name__,
            device=str(getattr(model, "device", "<unknown>")),
        )
        self.recorder.check_named_tensors("setup.params.loaded", _parameter_payload(policy))

        self._patch_policy(policy)
        self._patch_algo(model)
        self._patch_save_exclusions(model)

        setattr(model, "_nonfinite_probe", self)
        setattr(model, "_nonfinite_probe_report_path", self.report_path)

    def build_error_report(self, model, error: NonFiniteProbeError) -> dict[str, Any]:
        policy = getattr(model, "policy", None)
        report = {
            "status": "nonfinite_detected",
            "report_path": self.report_path,
            "run_metadata": dict(self.run_metadata),
            "model_num_timesteps_at_failure": int(getattr(model, "num_timesteps", -1)),
            "n_updates_at_failure": int(getattr(model, "_n_updates", -1)),
            "device": str(getattr(model, "device", "<unknown>")),
            "cuda_available": bool(th.cuda.is_available()),
            "cuda_device_name": th.cuda.get_device_name(0) if th.cuda.is_available() else None,
            "policy_class": type(policy).__name__ if policy is not None else None,
            "extractor_class": type(policy.features_extractor).__name__ if policy is not None else None,
            "policy_kwargs": getattr(model, "policy_kwargs", None),
            "failure": error.report,
            "recent_history": list(self.recorder.history),
        }
        return report

    def write_error_report(self, model, error: NonFiniteProbeError) -> str:
        report = self.build_error_report(model, error)
        write_nonfinite_probe_report(self.report_path, report)
        return self.report_path

    def _patch_transformer_extractor(self, extractor: TransformerExtractor) -> None:
        tracer = self.recorder

        def traced_forward(self, observations: dict[str, th.Tensor]) -> th.Tensor:
            tracer.check("extractor.obs.instruments", observations["instruments"])
            tracer.check("extractor.obs.contacts", observations["contacts"])
            tracer.check("extractor.obs.rwr", observations["rwr"])
            tracer.check("extractor.obs.mission", observations["mission"])
            if self.has_proprio:
                tracer.check("extractor.obs.proprio", observations["proprio"])

            amp_enabled = bool(
                getattr(self, "_autocast_enabled_for_forward", lambda: bool(th.cuda.is_available() and self.use_amp))()
            )
            amp_dtype = getattr(self, "_autocast_dtype", lambda: th.float16)()
            with th.autocast("cuda", enabled=amp_enabled, dtype=amp_dtype):
                processed = preprocess_transformer_observations(observations)
                s_inst = processed["instruments"]
                s_contacts = processed["contacts"]
                s_rwr = processed["rwr"]
                s_mission = processed["mission"]
                tracer.check("extractor.proc.instruments", s_inst)
                tracer.check("extractor.proc.contacts", s_contacts)
                tracer.check("extractor.proc.rwr", s_rwr)
                tracer.check("extractor.proc.mission", s_mission)

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
                    emb_proprio = self.embed_proprio(processed["proprio"]).unsqueeze(1) + self.type_embed(self.idx_proprio)
                    tracer.check("extractor.proc.proprio", processed["proprio"])
                    tracer.check("extractor.emb_proprio", emb_proprio)
                    emb_parts.append(emb_proprio)
                if getattr(self, "has_ew_state", False):
                    emb_ew_state = self.embed_ew_state(processed["ew_state"]).unsqueeze(1) + self.type_embed(
                        self.idx_ew_state
                    )
                    tracer.check("extractor.emb_ew_state", emb_ew_state)
                    emb_parts.append(emb_ew_state)

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

    def _patch_policy(self, policy: SquashedMultiInputPolicy) -> None:
        tracer = self.recorder
        if isinstance(policy.features_extractor, TransformerExtractor):
            self._patch_transformer_extractor(policy.features_extractor)
        elif isinstance(policy.features_extractor, TransformerVisualExtractor):
            raise ValueError("non-finite probe currently supports TransformerExtractor-based policies only")
        elif isinstance(policy.features_extractor, TemporalTransformerExtractor):
            # Generic policy-level tensor checks still cover temporal extractor inputs/outputs.
            pass

        original_get_action_dist_from_latent = policy._get_action_dist_from_latent
        original_forward = policy.forward
        original_evaluate_actions = policy.evaluate_actions
        original_predict_values = policy.predict_values

        def traced_get_action_dist_from_latent(self, latent_pi: th.Tensor, *args, **kwargs):
            tracer.check("policy.latent_pi.pre_dist", latent_pi)
            distribution = original_get_action_dist_from_latent(latent_pi, *args, **kwargs)

            if hasattr(self, "log_std"):
                tracer.check("policy.log_std", self.log_std)

            inner_dist = getattr(distribution, "distribution", None)
            if inner_dist is not None:
                mean_actions = getattr(inner_dist, "mean", None)
                if mean_actions is not None:
                    tracer.check("policy.mean_actions", mean_actions)
                action_std = getattr(inner_dist, "stddev", None)
                if action_std is not None:
                    tracer.check("policy.action_std", action_std)

            get_route_stats = getattr(self, "get_hmoe_route_stats", None)
            if callable(get_route_stats):
                try:
                    route_stats = get_route_stats()
                except Exception:
                    route_stats = None
                if isinstance(route_stats, dict):
                    for key, value in route_stats.items():
                        try:
                            tracer.check(f"policy.route_stats.{str(key).replace('/', '.')}", np.asarray([float(value)]))
                        except Exception:
                            continue

            return distribution

        def traced_forward(self, obs, deterministic: bool = False):
            if isinstance(obs, dict):
                for key, value in obs.items():
                    tracer.check(f"policy.forward.obs.{key}", value)
            else:
                tracer.check("policy.forward.obs", obs)
            actions, values, log_prob = original_forward(obs, deterministic=deterministic)
            tracer.check("policy.forward.values", values)
            tracer.check("policy.forward.actions.reshaped", actions)
            tracer.check("policy.forward.log_prob", log_prob)
            return actions, values, log_prob

        def traced_evaluate_actions(self, obs, actions: th.Tensor):
            if isinstance(obs, dict):
                for key, value in obs.items():
                    tracer.check(f"policy.evaluate.obs.{key}", value)
            else:
                tracer.check("policy.evaluate.obs", obs)
            tracer.check("policy.evaluate.actions.input", actions)
            values, log_prob, entropy = original_evaluate_actions(obs, actions)
            tracer.check("policy.evaluate.log_prob", log_prob)
            tracer.check("policy.evaluate.values", values)
            if entropy is not None:
                tracer.check("policy.evaluate.entropy", entropy)
            return values, log_prob, entropy

        def traced_predict_values(self, obs):
            if isinstance(obs, dict):
                for key, value in obs.items():
                    tracer.check(f"policy.predict_values.obs.{key}", value)
            else:
                tracer.check("policy.predict_values.obs", obs)
            values = original_predict_values(obs)
            tracer.check("policy.predict_values.values", values)
            return values

        policy._get_action_dist_from_latent = MethodType(traced_get_action_dist_from_latent, policy)
        policy.forward = MethodType(traced_forward, policy)
        policy.evaluate_actions = MethodType(traced_evaluate_actions, policy)
        policy.predict_values = MethodType(traced_predict_values, policy)

    def _patch_algo(self, model) -> None:
        """Attach to the canonical PPO owner; never replace its algorithms."""
        setattr(model, "_training_observer", _TrainingTraceObserver(self.recorder))
    def _patch_save_exclusions(self, model) -> None:
        original_excluded_save_params = model._excluded_save_params

        def traced_excluded_save_params(self) -> list[str]:
            excluded = list(original_excluded_save_params())
            extra = {
                "_nonfinite_probe",
                "_nonfinite_probe_report_path",
                "_training_observer",
                "_excluded_save_params",
            }
            for name in extra:
                if name not in excluded:
                    excluded.append(name)
            return excluded

        model._excluded_save_params = MethodType(traced_excluded_save_params, model)
