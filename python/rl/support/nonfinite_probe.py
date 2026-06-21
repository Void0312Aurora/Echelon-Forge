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
        return {
            "kind": "dict",
            "keys": list(value.keys()),
            "items": {str(key): _summary_for_value(item) for key, item in value.items()},
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
        tracer = self.recorder

        def reset_grouped_stopping_state(algo) -> None:
            if not hasattr(algo, "_grouped_stopping_sidecar"):
                return
            algo._grouped_stopping_sidecar = None
            algo._last_grouped_stopping_loss = None
            algo._last_grouped_stopping_grad_norm = 0.0
            if hasattr(algo, "_last_event_window_loss"):
                algo._last_event_window_loss = None
                algo._last_event_window_grad_norm = 0.0
            if hasattr(algo, "_last_window_classifier_loss"):
                algo._last_window_classifier_loss = None
                algo._last_window_classifier_grad_norm = 0.0
            if hasattr(algo, "_last_fire_boundary_loss"):
                algo._last_fire_boundary_loss = None
                algo._last_fire_boundary_grad_norm = 0.0
            diagnostics = getattr(algo, "_last_grouped_stopping_diagnostics", None)
            if diagnostics is not None:
                try:
                    algo._last_grouped_stopping_diagnostics = type(diagnostics)()
                except Exception:
                    pass
            diagnostics = getattr(algo, "_last_event_window_diagnostics", None)
            if diagnostics is not None:
                try:
                    algo._last_event_window_diagnostics = type(diagnostics)()
                except Exception:
                    pass

        def grouped_stopping_enabled(algo) -> bool:
            enabled = getattr(algo, "_grouped_stopping_enabled", None)
            return bool(callable(enabled) and enabled())

        def grouped_stopping_sidecar_enabled(algo) -> bool:
            enabled = getattr(algo, "_grouped_stopping_sidecar_enabled", None)
            if callable(enabled):
                return bool(enabled())
            return bool(grouped_stopping_enabled(algo))

        def event_window_enabled(algo) -> bool:
            enabled = getattr(algo, "_event_window_enabled", None)
            return bool(callable(enabled) and enabled())

        def window_classifier_enabled(algo) -> bool:
            enabled = getattr(algo, "_window_classifier_enabled", None)
            return bool(callable(enabled) and enabled())

        def fire_boundary_enabled(algo) -> bool:
            enabled = getattr(algo, "_fire_boundary_enabled", None)
            return bool(callable(enabled) and enabled())

        def traced_collect_rollouts(self, env, callback, rollout_buffer, n_rollout_steps: int) -> bool:
            assert self._last_obs is not None, "No previous observation was provided"
            self.policy.set_training_mode(False)
            set_training_progress = getattr(self.policy, "set_hmoe_training_progress", None)
            if callable(set_training_progress):
                set_training_progress(float(self._current_progress_remaining))

            n_steps = 0
            rollout_buffer.reset()
            reset_grouped_stopping_state(self)
            self._support_preserving_collect_hold_count = 0
            self._support_preserving_collect_candidate_count = 0
            self._support_preserving_collect_quality_count = 0
            if self.use_sde:
                self.policy.reset_noise(env.num_envs)

            callback.on_rollout_start()
            first_event_label_collection_enabled = getattr(self, "_first_event_label_collection_enabled", None)
            if callable(first_event_label_collection_enabled):
                collect_first_event = bool(first_event_label_collection_enabled())
            else:
                collect_first_event = bool(getattr(self, "_first_event_enabled", lambda: False)())
            collect_first_event = bool(
                collect_first_event
                and getattr(rollout_buffer, "supports_first_event_labels", False)
            )
            engagement_state: list[str] = []
            fire_mask: list[bool] = []
            fire_once_accepted: list[bool] = []
            episode_id: list[int] = []
            launch_window_open: list[bool] = []
            existing_episode_id = getattr(self, "_first_event_env_episode_id", None)
            if (
                collect_first_event
                and isinstance(existing_episode_id, np.ndarray)
                and int(existing_episode_id.size) == int(env.num_envs)
            ):
                env_episode_id = existing_episode_id.astype(np.int64, copy=True)
            else:
                env_episode_id = np.arange(env.num_envs, dtype=np.int64)
            if collect_first_event and not hasattr(self, "_first_event_curriculum_seeded_episode_ids"):
                self._first_event_curriculum_seeded_episode_ids = set()

            while n_steps < n_rollout_steps:
                tracer.set_context(
                    phase="rollout",
                    rollout_step=int(n_steps),
                    num_timesteps=int(self.num_timesteps),
                    update_index=int(self._n_updates),
                )
                if self.use_sde and self.sde_sample_freq > 0 and n_steps % self.sde_sample_freq == 0:
                    self.policy.reset_noise(env.num_envs)

                with th.no_grad():
                    obs_tensor = self._get_policy_obs_tensor(env, self._last_obs)
                    if isinstance(obs_tensor, dict):
                        for key, value in obs_tensor.items():
                            tracer.check(f"rollout.obs_tensor.{key}", value)
                    else:
                        tracer.check("rollout.obs_tensor", obs_tensor)
                    actions_tensor, values, log_probs = self.policy(obs_tensor)
                    tracer.check("rollout.actions_tensor", actions_tensor)
                    tracer.check("rollout.values", values)
                    tracer.check("rollout.log_probs", log_probs)
                policy_fire_mask = None
                policy_launch_window = None
                if collect_first_event:
                    policy_mask_fn = getattr(self, "_first_event_policy_fire_mask_from_obs", None)
                    if callable(policy_mask_fn):
                        policy_fire_mask = policy_mask_fn(obs_tensor, env.num_envs)
                    launch_window_fn = getattr(self, "_first_event_launch_window_from_policy_obs", None)
                    if callable(launch_window_fn):
                        policy_launch_window = launch_window_fn(obs_tensor, env.num_envs)
                support_mask_fn = getattr(self, "_support_preserving_collect_masks", None)
                apply_support_fn = getattr(self, "_apply_support_preserving_collect_actions", None)
                if callable(support_mask_fn) and callable(apply_support_fn):
                    support_hold_mask = support_mask_fn(
                        fire_mask=policy_fire_mask,
                        launch_window_open=policy_launch_window,
                        n_envs=env.num_envs,
                    )
                    actions_tensor, log_probs = apply_support_fn(
                        obs_tensor,
                        actions_tensor,
                        log_probs,
                        support_hold_mask,
                    )
                    tracer.check("rollout.support_preserved_actions_tensor", actions_tensor)
                    tracer.check("rollout.support_preserved_log_probs", log_probs)
                actions = actions_tensor.detach().cpu().numpy()
                tracer.check("rollout.actions_numpy", actions)

                clipped_actions = actions
                if isinstance(self.action_space, spaces.Box):
                    if self.policy.squash_output:
                        clipped_actions = self.policy.unscale_action(clipped_actions)
                    else:
                        clipped_actions = np.clip(actions, self.action_space.low, self.action_space.high)
                tracer.check("rollout.clipped_actions", clipped_actions)

                new_obs, rewards, dones, infos = env.step(clipped_actions)
                tracer.check("rollout.rewards", rewards)
                tracer.check("rollout.dones", dones.astype(np.float32))
                if isinstance(new_obs, dict):
                    for key, value in new_obs.items():
                        tracer.check(f"rollout.new_obs.{key}", value)
                else:
                    tracer.check("rollout.new_obs", new_obs)

                self.num_timesteps += env.num_envs
                if collect_first_event:
                    fire_mask_from_info = getattr(self, "_first_event_fire_mask_from_info", None)
                    bool_from_info = getattr(self, "_first_event_bool", None)
                    for env_idx, info in enumerate(infos):
                        row = info if isinstance(info, dict) else {}
                        if policy_fire_mask is not None and env_idx < len(policy_fire_mask):
                            policy_window_open = bool(policy_fire_mask[env_idx])
                        elif callable(fire_mask_from_info):
                            policy_window_open = bool(fire_mask_from_info(row))
                        else:
                            policy_window_open = bool(row.get("fire_mask", False))
                        engagement_state.append(
                            "AuthorizedReady" if policy_window_open else str(row.get("engagement_state", "") or "")
                        )
                        if callable(fire_mask_from_info):
                            fire_mask.append(bool(policy_window_open))
                        else:
                            fire_mask.append(bool(policy_window_open))
                        if callable(bool_from_info):
                            fire_once_accepted.append(bool(bool_from_info(row.get("fire_once_accepted", False))))
                        else:
                            fire_once_accepted.append(bool(row.get("fire_once_accepted", False)))
                        episode_id.append(int(env_episode_id[env_idx]))
                        if policy_launch_window is not None and env_idx < len(policy_launch_window):
                            launch_window_open.append(bool(policy_launch_window[env_idx]))
                        else:
                            launch_window_open.append(bool(policy_window_open))
                callback.update_locals(locals())
                if not callback.on_step():
                    return False

                self._update_info_buffer(infos, dones)
                n_steps += 1

                if isinstance(self.action_space, spaces.Discrete):
                    actions = actions.reshape(-1, 1)

                for idx, done in enumerate(dones):
                    if (
                        done
                        and infos[idx].get("terminal_observation") is not None
                        and infos[idx].get("TimeLimit.truncated", False)
                    ):
                        terminal_obs = self.policy.obs_to_tensor(infos[idx]["terminal_observation"])[0]
                        with th.no_grad():
                            terminal_value = self.policy.predict_values(terminal_obs)[0]
                        rewards[idx] += self.gamma * terminal_value

                rollout_buffer.add(
                    obs_tensor if self._is_device_rollout_buffer(rollout_buffer) else self._last_obs,
                    actions_tensor if self._is_device_rollout_buffer(rollout_buffer) else actions,
                    rewards,
                    self._last_episode_starts,
                    values,
                    log_probs,
                )
                self._last_obs = new_obs
                self._last_episode_starts = dones
                if collect_first_event:
                    for env_idx, done in enumerate(dones):
                        if bool(done):
                            env_episode_id[env_idx] += env.num_envs
                            ages = getattr(self, "_support_preserving_collect_legal_open_age", None)
                            if isinstance(ages, np.ndarray) and int(ages.size) == int(env.num_envs):
                                ages[int(env_idx)] = 0

            with th.no_grad():
                values = self.policy.predict_values(self._get_policy_obs_tensor(env, new_obs))
                tracer.check("rollout.last_values", values)

            if collect_first_event:
                self._first_event_env_episode_id = env_episode_id
                attach_a6 = getattr(self, "_attach_first_event_labels_to_rollout_buffer", None)
                if callable(attach_a6):
                    attach_a6(
                        rollout_buffer,
                        engagement_state=engagement_state,
                        fire_mask=fire_mask,
                        fire_once_accepted=fire_once_accepted,
                        episode_id=episode_id,
                        launch_window_open=(
                            launch_window_open
                            if bool(getattr(self, "first_event_launch_window_enabled", False))
                            else None
                        ),
                        env_episode_id_after_rollout=env_episode_id,
                    )
                    for field in (
                        "first_event_active",
                        "first_event_target",
                        "first_event_weight",
                    ):
                        if hasattr(rollout_buffer, field):
                            tracer.check(f"rollout.buffer.{field}", getattr(rollout_buffer, field))
                build_sidecar = getattr(self, "_build_grouped_stopping_sidecar", None)
                if callable(build_sidecar) and grouped_stopping_sidecar_enabled(self):
                    self._grouped_stopping_sidecar = build_sidecar(
                        rollout_buffer,
                        fire_mask=fire_mask,
                        fire_once_accepted=fire_once_accepted,
                        episode_id=episode_id,
                        launch_window_open=launch_window_open,
                    )
                    sidecar = getattr(self, "_grouped_stopping_sidecar", None)
                    if sidecar is not None:
                        tracer.check(
                            "rollout.grouped_sidecar_group_count",
                            np.asarray([float(len(sidecar.groups))], dtype=np.float32),
                        )
            rollout_buffer.compute_returns_and_advantage(last_values=values, dones=dones)
            if isinstance(rollout_buffer.observations, dict):
                for key, value in rollout_buffer.observations.items():
                    tracer.check(f"rollout.buffer.obs.{key}", value)
            else:
                tracer.check("rollout.buffer.obs", rollout_buffer.observations)
            tracer.check("rollout.buffer.actions", rollout_buffer.actions)
            tracer.check("rollout.buffer.values", rollout_buffer.values)
            tracer.check("rollout.buffer.log_probs", rollout_buffer.log_probs)
            tracer.check("rollout.buffer.advantages", rollout_buffer.advantages)
            tracer.check("rollout.buffer.returns", rollout_buffer.returns)

            callback.update_locals(locals())
            callback.on_rollout_end()
            return True

        def traced_train(self) -> None:
            self.policy.set_training_mode(True)

            set_training_progress = getattr(self.policy, "set_hmoe_training_progress", None)
            if callable(set_training_progress):
                set_training_progress(float(self._current_progress_remaining))

            self._update_learning_rate(self.policy.optimizer)
            self._apply_lr_multiplier()

            clip_range = float(self.clip_range(self._current_progress_remaining))
            clip_range *= float(self._clip_mult)
            clip_range = float(np.clip(clip_range, 1e-4, 0.4))

            if self.clip_range_vf is not None:
                clip_range_vf = float(self.clip_range_vf(self._current_progress_remaining))
            else:
                clip_range_vf = None

            entropy_losses = []
            pg_losses, value_losses = [], []
            action_mean_regularization_losses = []
            first_event_hazard_losses = []
            first_event_hazard_active_counts = []
            first_event_hazard_positive_fracs = []
            first_event_credit_losses = []
            first_event_credit_value_losses = []
            first_event_credit_delta_align_losses = []
            first_event_credit_active_counts = []
            first_event_credit_positive_fracs = []
            first_event_credit_advantage_means = []
            first_event_credit_projection_active_counts = []
            first_event_credit_projection_candidate_counts = []
            first_event_credit_projection_unsupported_counts = []
            first_event_credit_projection_advantage_means = []
            first_event_credit_projection_delta_means = []
            first_event_credit_source_shadow_counts = []
            first_event_credit_source_deadline_counts = []
            first_event_credit_source_early_counts = []
            first_event_credit_source_prewindow_counts = []
            first_event_credit_source_legal_open_quality_counts = []
            first_event_credit_source_legal_open_quality_positive_counts = []
            first_event_credit_source_deadline_positive_counts = []
            first_event_credit_source_shadow_positive_counts = []
            first_event_credit_source_legal_open_quality_advantage_means = []
            first_event_credit_separate_update_grad_norms = []
            first_event_credit_separate_update_counts = []
            clip_fractions = []
            approx_kl_divs = []
            continue_training = True
            event_window_loss = None
            fire_boundary_loss = None
            grouped_stopping_loss = None

            tracer.check_named_tensors("train.params.start", _parameter_payload(self.policy))

            for epoch in range(self.n_epochs):
                for minibatch_idx, rollout_data in enumerate(self.rollout_buffer.get(self.batch_size)):
                    tracer.set_context(
                        phase="train",
                        epoch=int(epoch),
                        minibatch=int(minibatch_idx),
                        num_timesteps=int(self.num_timesteps),
                        update_index=int(self._n_updates),
                    )
                    tracer.check_named_tensors("train.params.batch_start", _parameter_payload(self.policy))

                    if isinstance(rollout_data.observations, dict):
                        for key, value in rollout_data.observations.items():
                            tracer.check(f"train.rollout_data.obs.{key}", value)
                    else:
                        tracer.check("train.rollout_data.obs", rollout_data.observations)
                    tracer.check("train.rollout_data.actions", rollout_data.actions)
                    tracer.check("train.rollout_data.old_values", rollout_data.old_values)
                    tracer.check("train.rollout_data.old_log_prob", rollout_data.old_log_prob)
                    tracer.check("train.rollout_data.advantages", rollout_data.advantages)
                    tracer.check("train.rollout_data.returns", rollout_data.returns)
                    for field in (
                        "first_event_active",
                        "first_event_target",
                        "first_event_weight",
                    ):
                        if hasattr(rollout_data, field):
                            tracer.check(f"train.rollout_data.{field}", getattr(rollout_data, field))

                    actions = rollout_data.actions
                    if isinstance(self.action_space, spaces.Discrete):
                        actions = rollout_data.actions.long().flatten()

                    values, log_prob, entropy = self.policy.evaluate_actions(rollout_data.observations, actions)
                    tracer.check("train.values.raw", values)
                    tracer.check("train.log_prob", log_prob)
                    if entropy is not None:
                        tracer.check("train.entropy.raw", entropy)
                    values = values.flatten()
                    tracer.check("train.values.flattened", values)

                    advantages = rollout_data.advantages
                    if self.normalize_advantage and len(advantages) > 1:
                        adv_mean = advantages.mean()
                        adv_std = advantages.std()
                        tracer.check("train.advantages.mean", adv_mean)
                        tracer.check("train.advantages.std", adv_std)
                        advantages = (advantages - adv_mean) / (adv_std + 1e-8)
                    tracer.check("train.advantages.used", advantages)

                    ratio = th.exp(log_prob - rollout_data.old_log_prob)
                    tracer.check("train.ratio", ratio)

                    policy_loss_1 = advantages * ratio
                    tracer.check("train.policy_loss_1", policy_loss_1)
                    policy_loss_2 = advantages * th.clamp(ratio, 1 - clip_range, 1 + clip_range)
                    tracer.check("train.policy_loss_2", policy_loss_2)
                    policy_loss = -th.min(policy_loss_1, policy_loss_2).mean()
                    tracer.check("train.policy_loss", policy_loss)
                    pg_losses.append(policy_loss.item())
                    clip_fraction = th.mean((th.abs(ratio - 1) > clip_range).float()).item()
                    clip_fractions.append(clip_fraction)

                    if clip_range_vf is None:
                        values_pred = values
                    else:
                        values_pred = rollout_data.old_values + th.clamp(
                            values - rollout_data.old_values, -clip_range_vf, clip_range_vf
                        )
                    tracer.check("train.values_pred", values_pred)
                    value_loss = F.mse_loss(rollout_data.returns, values_pred)
                    tracer.check("train.value_loss", value_loss)
                    value_losses.append(value_loss.item())

                    if entropy is None:
                        entropy_loss = -th.mean(-log_prob)
                    else:
                        entropy_loss = -th.mean(entropy)
                    tracer.check("train.entropy_loss", entropy_loss)
                    entropy_losses.append(entropy_loss.item())

                    log_ratio = log_prob - rollout_data.old_log_prob
                    tracer.check("train.log_ratio", log_ratio)
                    approx_kl = th.mean((th.exp(log_ratio) - 1) - log_ratio)
                    tracer.check("train.approx_kl", approx_kl)

                    loss = policy_loss + self.ent_coef * entropy_loss + self.vf_coef * value_loss
                    if self.kl_penalty_coef > 0.0:
                        loss = loss + float(self.kl_penalty_coef) * approx_kl
                    action_mean_regularization_loss = None
                    action_mean_regularization_fn = getattr(self, "_action_mean_regularization_loss", None)
                    if callable(action_mean_regularization_fn):
                        action_mean_regularization_loss = action_mean_regularization_fn(
                            rollout_data.observations,
                            actions,
                        )
                    if action_mean_regularization_loss is not None:
                        tracer.check("train.action_mean_regularization_loss", action_mean_regularization_loss)
                        action_mean_regularization_losses.append(
                            float(action_mean_regularization_loss.detach().cpu())
                        )
                        loss = loss + float(getattr(self, "action_mean_regularization_coef", 0.0)) * action_mean_regularization_loss
                    first_event_hazard_loss = None
                    first_event_hazard_fn = getattr(self, "_first_event_hazard_loss", None)
                    if callable(first_event_hazard_fn):
                        first_event_hazard_loss = first_event_hazard_fn(rollout_data)
                    if first_event_hazard_loss is not None:
                        tracer.check("train.first_event_hazard_loss", first_event_hazard_loss.loss)
                        first_event_hazard_losses.append(float(first_event_hazard_loss.loss.detach().cpu()))
                        first_event_hazard_active_counts.append(int(first_event_hazard_loss.active_count))
                        first_event_hazard_positive_fracs.append(float(first_event_hazard_loss.positive_frac))
                        loss = loss + first_event_hazard_loss.loss
                    separate_credit_loss = None
                    separate_credit_grad_norm = 0.0
                    if bool(getattr(self, "event_credit_separate_update_enabled", False)):
                        separate_update_fn = getattr(self, "_first_event_credit_separate_value_update", None)
                        if callable(separate_update_fn):
                            separate_credit_loss, separate_credit_grad_norm = separate_update_fn(rollout_data)
                        if separate_credit_loss is not None:
                            tracer.check(
                                "train.first_event_credit_separate_value_loss",
                                separate_credit_loss.value_loss,
                            )
                            first_event_credit_separate_update_grad_norms.append(
                                float(separate_credit_grad_norm)
                            )
                            first_event_credit_separate_update_counts.append(1)
                    first_event_credit_loss = None
                    first_event_credit_fn = getattr(self, "_first_event_credit_loss", None)
                    if callable(first_event_credit_fn):
                        first_event_credit_loss = first_event_credit_fn(
                            rollout_data,
                            value_coef=0.0
                            if bool(getattr(self, "event_credit_separate_update_enabled", False))
                            else None,
                            projection_value_coef=0.0
                            if bool(getattr(self, "event_credit_separate_update_enabled", False))
                            else None,
                        )
                    if first_event_credit_loss is not None:
                        total_credit_loss = first_event_credit_loss.loss
                        value_credit_loss = first_event_credit_loss.value_loss
                        if separate_credit_loss is not None:
                            total_credit_loss = total_credit_loss + separate_credit_loss.loss.detach()
                            value_credit_loss = separate_credit_loss.value_loss
                        tracer.check("train.first_event_credit_loss", first_event_credit_loss.loss)
                        tracer.check(
                            "train.first_event_credit_value_loss",
                            value_credit_loss,
                        )
                        tracer.check(
                            "train.first_event_credit_delta_align_loss",
                            first_event_credit_loss.delta_align_loss,
                        )
                        first_event_credit_losses.append(float(total_credit_loss.detach().cpu()))
                        first_event_credit_value_losses.append(
                            float(value_credit_loss.detach().cpu())
                        )
                        first_event_credit_delta_align_losses.append(
                            float(first_event_credit_loss.delta_align_loss.detach().cpu())
                        )
                        first_event_credit_active_counts.append(int(first_event_credit_loss.active_count))
                        first_event_credit_positive_fracs.append(float(first_event_credit_loss.positive_frac))
                        first_event_credit_advantage_means.append(float(first_event_credit_loss.advantage_mean))
                        first_event_credit_projection_active_counts.append(
                            int(getattr(first_event_credit_loss, "projection_active_count", 0))
                        )
                        first_event_credit_projection_candidate_counts.append(
                            int(getattr(first_event_credit_loss, "projection_candidate_count", 0))
                        )
                        first_event_credit_projection_unsupported_counts.append(
                            int(getattr(first_event_credit_loss, "projection_unsupported_count", 0))
                        )
                        first_event_credit_projection_advantage_means.append(
                            float(getattr(first_event_credit_loss, "projection_advantage_mean", 0.0))
                        )
                        first_event_credit_projection_delta_means.append(
                            float(getattr(first_event_credit_loss, "projection_delta_mean", 0.0))
                        )
                        first_event_credit_source_shadow_counts.append(
                            int(getattr(first_event_credit_loss, "source_shadow_count", 0))
                        )
                        first_event_credit_source_deadline_counts.append(
                            int(getattr(first_event_credit_loss, "source_deadline_count", 0))
                        )
                        first_event_credit_source_early_counts.append(
                            int(getattr(first_event_credit_loss, "source_early_accepted_count", 0))
                        )
                        first_event_credit_source_prewindow_counts.append(
                            int(getattr(first_event_credit_loss, "source_prewindow_count", 0))
                        )
                        first_event_credit_source_legal_open_quality_counts.append(
                            int(getattr(first_event_credit_loss, "source_legal_open_quality_count", 0))
                        )
                        first_event_credit_source_legal_open_quality_positive_counts.append(
                            int(getattr(first_event_credit_loss, "source_legal_open_quality_positive_count", 0))
                        )
                        first_event_credit_source_deadline_positive_counts.append(
                            int(getattr(first_event_credit_loss, "source_deadline_positive_count", 0))
                        )
                        first_event_credit_source_shadow_positive_counts.append(
                            int(getattr(first_event_credit_loss, "source_shadow_positive_count", 0))
                        )
                        first_event_credit_source_legal_open_quality_advantage_means.append(
                            float(getattr(first_event_credit_loss, "source_legal_open_quality_advantage_mean", 0.0))
                        )
                        loss = loss + first_event_credit_loss.loss
                    elif separate_credit_loss is not None:
                        first_event_credit_losses.append(float(separate_credit_loss.loss.detach().cpu()))
                        first_event_credit_value_losses.append(float(separate_credit_loss.value_loss.detach().cpu()))
                        first_event_credit_delta_align_losses.append(
                            float(separate_credit_loss.delta_align_loss.detach().cpu())
                        )
                        first_event_credit_active_counts.append(int(separate_credit_loss.active_count))
                        first_event_credit_positive_fracs.append(float(separate_credit_loss.positive_frac))
                        first_event_credit_advantage_means.append(float(separate_credit_loss.advantage_mean))
                        first_event_credit_projection_active_counts.append(
                            int(getattr(separate_credit_loss, "projection_active_count", 0))
                        )
                        first_event_credit_projection_candidate_counts.append(
                            int(getattr(separate_credit_loss, "projection_candidate_count", 0))
                        )
                        first_event_credit_projection_unsupported_counts.append(
                            int(getattr(separate_credit_loss, "projection_unsupported_count", 0))
                        )
                        first_event_credit_projection_advantage_means.append(
                            float(getattr(separate_credit_loss, "projection_advantage_mean", 0.0))
                        )
                        first_event_credit_projection_delta_means.append(
                            float(getattr(separate_credit_loss, "projection_delta_mean", 0.0))
                        )
                        first_event_credit_source_shadow_counts.append(
                            int(getattr(separate_credit_loss, "source_shadow_count", 0))
                        )
                        first_event_credit_source_deadline_counts.append(
                            int(getattr(separate_credit_loss, "source_deadline_count", 0))
                        )
                        first_event_credit_source_early_counts.append(
                            int(getattr(separate_credit_loss, "source_early_accepted_count", 0))
                        )
                        first_event_credit_source_prewindow_counts.append(
                            int(getattr(separate_credit_loss, "source_prewindow_count", 0))
                        )
                        first_event_credit_source_legal_open_quality_counts.append(
                            int(getattr(separate_credit_loss, "source_legal_open_quality_count", 0))
                        )
                        first_event_credit_source_legal_open_quality_positive_counts.append(
                            int(getattr(separate_credit_loss, "source_legal_open_quality_positive_count", 0))
                        )
                        first_event_credit_source_deadline_positive_counts.append(
                            int(getattr(separate_credit_loss, "source_deadline_positive_count", 0))
                        )
                        first_event_credit_source_shadow_positive_counts.append(
                            int(getattr(separate_credit_loss, "source_shadow_positive_count", 0))
                        )
                        first_event_credit_source_legal_open_quality_advantage_means.append(
                            float(getattr(separate_credit_loss, "source_legal_open_quality_advantage_mean", 0.0))
                        )
                    tracer.check("train.loss", loss)

                    with th.no_grad():
                        approx_kl_div = float(approx_kl.detach().cpu().numpy())
                    approx_kl_divs.append(approx_kl_div)
                    if self.target_kl is not None and approx_kl_div > 1.5 * float(self.target_kl):
                        continue_training = False
                        if self.verbose >= 1:
                            print(f"Early stopping at epoch {epoch} due to reaching max kl: {approx_kl_div:.4f}")
                        break

                    self.policy.optimizer.zero_grad()
                    loss.backward()
                    tracer.check_named_tensors("train.gradients.post_backward", _gradient_payload(self.policy))
                    grad_norm = th.nn.utils.clip_grad_norm_(self.policy.parameters(), self.max_grad_norm)
                    tracer.check("train.grad_norm", grad_norm)
                    tracer.check_named_tensors("train.gradients.post_clip", _gradient_payload(self.policy))
                    self.policy.optimizer.step()
                    tracer.check_named_tensors("train.params.post_step", _parameter_payload(self.policy))

                self._n_updates += 1
                if not continue_training:
                    break

            window_classifier_loss = None
            classifier_update_fn = getattr(self, "_window_classifier_auxiliary_update", None)
            if callable(classifier_update_fn):
                window_classifier_loss = classifier_update_fn()
                if window_classifier_loss is not None:
                    tracer.check(
                        "train.window_classifier_loss",
                        window_classifier_loss.loss,
                    )
                    tracer.check(
                        "train.window_classifier_unscaled_loss",
                        window_classifier_loss.unscaled_loss,
                    )
                    tracer.check(
                        "train.window_classifier_grad_norm",
                        np.asarray(
                            [float(getattr(self, "_last_window_classifier_grad_norm", 0.0))],
                            dtype=np.float32,
                        ),
                    )
                    tracer.check_named_tensors(
                        "train.params.post_window_classifier_update",
                        _parameter_payload(self.policy),
                    )

            fire_boundary_update_fn = getattr(self, "_fire_boundary_auxiliary_update", None)
            if callable(fire_boundary_update_fn):
                fire_boundary_loss = fire_boundary_update_fn()
                if fire_boundary_loss is not None:
                    tracer.check(
                        "train.fire_boundary_loss",
                        fire_boundary_loss.loss,
                    )
                    tracer.check(
                        "train.fire_boundary_unscaled_loss",
                        fire_boundary_loss.unscaled_loss,
                    )
                    tracer.check(
                        "train.fire_boundary_grad_norm",
                        np.asarray(
                            [float(getattr(self, "_last_fire_boundary_grad_norm", 0.0))],
                            dtype=np.float32,
                        ),
                    )
                    tracer.check_named_tensors(
                        "train.params.post_fire_boundary_update",
                        _parameter_payload(self.policy),
                    )

            event_window_update_fn = getattr(self, "_event_window_auxiliary_update", None)
            if callable(event_window_update_fn):
                event_window_loss = event_window_update_fn()
                if event_window_loss is not None:
                    tracer.check(
                        "train.event_window_loss",
                        event_window_loss.loss,
                    )
                    tracer.check(
                        "train.event_window_unscaled_loss",
                        event_window_loss.unscaled_loss,
                    )
                    tracer.check(
                        "train.event_window_grad_norm",
                        np.asarray(
                            [float(getattr(self, "_last_event_window_grad_norm", 0.0))],
                            dtype=np.float32,
                        ),
                    )
                    tracer.check_named_tensors("train.params.post_event_window_update", _parameter_payload(self.policy))

            grouped_stopping_update_fn = getattr(self, "_grouped_stopping_auxiliary_update", None)
            if callable(grouped_stopping_update_fn):
                grouped_stopping_loss = grouped_stopping_update_fn()
                if grouped_stopping_loss is not None:
                    tracer.check(
                        "train.grouped_stopping_loss",
                        grouped_stopping_loss.loss,
                    )
                    tracer.check(
                        "train.grouped_stopping_unscaled_loss",
                        grouped_stopping_loss.unscaled_loss,
                    )
                    tracer.check(
                        "train.grouped_stopping_grad_norm",
                        np.asarray(
                            [float(getattr(self, "_last_grouped_stopping_grad_norm", 0.0))],
                            dtype=np.float32,
                        ),
                    )
                    tracer.check_named_tensors("train.params.post_grouped_stopping_update", _parameter_payload(self.policy))

            explained_var = self._to_numpy_flat(self.rollout_buffer.values)
            explained_ret = self._to_numpy_flat(self.rollout_buffer.returns)
            tracer.check("train.rollout_buffer.values.flat", explained_var)
            tracer.check("train.rollout_buffer.returns.flat", explained_ret)
            explained = float(np.asarray([np.nan], dtype=np.float32)[0])
            try:
                from stable_baselines3.common.utils import explained_variance

                explained = float(explained_variance(explained_var, explained_ret))
            except Exception:
                explained = float("nan")
            tracer.check("train.explained_variance", np.asarray([explained], dtype=np.float32))

            mean_kl = float(np.mean(approx_kl_divs)) if len(approx_kl_divs) > 0 else None
            self._adapt_kl_controls(mean_kl)

            self.logger.record("train/entropy_loss", float(np.mean(entropy_losses)))
            self.logger.record("train/policy_gradient_loss", float(np.mean(pg_losses)))
            self.logger.record("train/value_loss", float(np.mean(value_losses)))
            self.logger.record("train/approx_kl", float(np.mean(approx_kl_divs)) if len(approx_kl_divs) > 0 else 0.0)
            self.logger.record("train/clip_fraction", float(np.mean(clip_fractions)))
            self.logger.record("train/loss", float(loss.item()))
            self.logger.record("train/explained_variance", float(explained))
            if hasattr(self.policy, "log_std"):
                self.logger.record("train/std", float(th.exp(self.policy.log_std).mean().item()))
            if float(getattr(self, "action_mean_regularization_coef", 0.0)) > 0.0:
                self.logger.record(
                    "train/action_mean_regularization_loss",
                    float(np.mean(action_mean_regularization_losses)) if action_mean_regularization_losses else 0.0,
                )
                self.logger.record(
                    "train/action_mean_regularization_coef",
                    float(getattr(self, "action_mean_regularization_coef", 0.0)),
                )
            if (
                float(getattr(self, "first_event_hazard_coef", 0.0)) > 0.0
                or float(getattr(self, "first_event_curriculum_coef", 0.0)) > 0.0
                or float(getattr(self, "first_event_deadline_weight", 0.0)) > 0.0
                or float(getattr(self, "first_event_censored_survival_weight", 0.0)) > 0.0
            ):
                curriculum_coef_fn = getattr(self, "_current_first_event_curriculum_coef", None)
                curriculum_coef = float(curriculum_coef_fn()) if callable(curriculum_coef_fn) else 0.0
                self.logger.record(
                    "a6/hazard_loss",
                    float(np.mean(first_event_hazard_losses)) if first_event_hazard_losses else 0.0,
                )
                self.logger.record("a6/hazard_coef", float(getattr(self, "first_event_hazard_coef", 0.0)))
                self.logger.record("a6/curriculum_coef", curriculum_coef)
                self.logger.record("a6/deadline_weight", float(getattr(self, "first_event_deadline_weight", 0.0)))
                self.logger.record(
                    "a6/launch_window_enabled",
                    float(bool(getattr(self, "first_event_launch_window_enabled", False))),
                )
                self.logger.record(
                    "a6/launch_window_prewindow_hold_weight",
                    float(getattr(self, "first_event_launch_window_prewindow_hold_weight", 0.0)),
                )
                self.logger.record(
                    "a6/active_count_mean",
                    float(np.mean(first_event_hazard_active_counts)) if first_event_hazard_active_counts else 0.0,
                )
                self.logger.record(
                    "a6/target_positive_frac",
                    float(np.mean(first_event_hazard_positive_fracs))
                    if first_event_hazard_positive_fracs
                    else 0.0,
                )
            if window_classifier_enabled(self):
                classifier_loss = window_classifier_loss or getattr(
                    self,
                    "_last_window_classifier_loss",
                    None,
                )
                self.logger.record(
                    "m3s2/window_classifier_coef",
                    float(getattr(self, "window_classifier_coef", 0.0)),
                )
                self.logger.record(
                    "m3s2/window_classifier_loss",
                    (
                        float(classifier_loss.loss.detach().cpu().item())
                        if classifier_loss is not None
                        else 0.0
                    ),
                )
                self.logger.record(
                    "m3s2/window_classifier_unscaled_loss",
                    (
                        float(classifier_loss.unscaled_loss.detach().cpu().item())
                        if classifier_loss is not None
                        else 0.0
                    ),
                )
                self.logger.record(
                    "m3s2/window_classifier_balanced_bce_loss",
                    (
                        float(classifier_loss.balanced_bce_loss.detach().cpu().item())
                        if classifier_loss is not None
                        else 0.0
                    ),
                )
                self.logger.record(
                    "m3s2/window_classifier_grad_norm",
                    float(getattr(self, "_last_window_classifier_grad_norm", 0.0)),
                )
                self.logger.record(
                    "m3s2/window_classifier_active_count",
                    float(classifier_loss.active_count) if classifier_loss is not None else 0.0,
                )
                self.logger.record(
                    "m3s2/window_classifier_positive_count",
                    float(classifier_loss.positive_count) if classifier_loss is not None else 0.0,
                )
                self.logger.record(
                    "m3s2/window_classifier_negative_count",
                    float(classifier_loss.negative_count) if classifier_loss is not None else 0.0,
                )
                self.logger.record(
                    "m3s2/window_classifier_positive_logit_mean",
                    float(classifier_loss.positive_logit_mean) if classifier_loss is not None else 0.0,
                )
                self.logger.record(
                    "m3s2/window_classifier_negative_logit_mean",
                    float(classifier_loss.negative_logit_mean) if classifier_loss is not None else 0.0,
                )
                self.logger.record(
                    "m3s2/window_classifier_accuracy",
                    float(classifier_loss.accuracy) if classifier_loss is not None else 0.0,
                )
                self.logger.record(
                    "m3s2/window_classifier_replay_enabled",
                    float(getattr(self, "window_classifier_replay_enabled", False)),
                )
                self.logger.record(
                    "m3s2/window_classifier_replay_storage_observation",
                    float(getattr(self, "window_classifier_replay_storage", "latent") == "observation"),
                )
                self.logger.record(
                    "m3s2/window_classifier_replay_used",
                    float(getattr(classifier_loss, "replay_used", False)) if classifier_loss is not None else 0.0,
                )
                self.logger.record(
                    "m3s2/window_classifier_replay_positive_count",
                    (
                        float(getattr(classifier_loss, "replay_positive_count", 0))
                        if classifier_loss is not None
                        else 0.0
                    ),
                )
                self.logger.record(
                    "m3s2/window_classifier_replay_negative_count",
                    (
                        float(getattr(classifier_loss, "replay_negative_count", 0))
                        if classifier_loss is not None
                        else 0.0
                    ),
                )
            if fire_boundary_enabled(self):
                fire_boundary_loss = fire_boundary_loss or getattr(
                    self,
                    "_last_fire_boundary_loss",
                    None,
                )
                active_count = float(getattr(fire_boundary_loss, "active_count", 0.0)) if fire_boundary_loss else 0.0
                boundary_cross_count = (
                    float(getattr(fire_boundary_loss, "boundary_cross_count", 0.0))
                    if fire_boundary_loss
                    else 0.0
                )
                boundary_cross_in_window_count = (
                    float(getattr(fire_boundary_loss, "boundary_cross_in_window_count", 0.0))
                    if fire_boundary_loss
                    else 0.0
                )
                self.logger.record("m3s2/fb_coef", float(getattr(self, "fire_boundary_coef", 0.0)))
                self.logger.record(
                    "m3s2/fb_loss",
                    (
                        float(fire_boundary_loss.loss.detach().cpu().item())
                        if fire_boundary_loss is not None
                        else 0.0
                    ),
                )
                self.logger.record(
                    "m3s2/fb_unscaled_loss",
                    (
                        float(fire_boundary_loss.unscaled_loss.detach().cpu().item())
                        if fire_boundary_loss is not None
                        else 0.0
                    ),
                )
                self.logger.record(
                    "m3s2/fb_bce_loss",
                    (
                        float(fire_boundary_loss.balanced_bce_loss.detach().cpu().item())
                        if fire_boundary_loss is not None
                        else 0.0
                    ),
                )
                self.logger.record(
                    "m3s2/fb_neg_ceiling_loss",
                    (
                        float(fire_boundary_loss.negative_logit_ceiling_loss.detach().cpu().item())
                        if fire_boundary_loss is not None
                        else 0.0
                    ),
                )
                self.logger.record(
                    "m3s2/fb_pos_floor_loss",
                    (
                        float(fire_boundary_loss.positive_logit_floor_loss.detach().cpu().item())
                        if fire_boundary_loss is not None
                        else 0.0
                    ),
                )
                self.logger.record(
                    "m3s2/fb_grad_norm",
                    float(getattr(self, "_last_fire_boundary_grad_norm", 0.0)),
                )
                self.logger.record(
                    "m3s2/fb_group_count",
                    float(getattr(fire_boundary_loss, "group_count", 0.0)) if fire_boundary_loss else 0.0,
                )
                self.logger.record("m3s2/fb_active_count", active_count)
                self.logger.record(
                    "m3s2/fb_positive_count",
                    float(getattr(fire_boundary_loss, "positive_count", 0.0)) if fire_boundary_loss else 0.0,
                )
                self.logger.record(
                    "m3s2/fb_negative_count",
                    float(getattr(fire_boundary_loss, "negative_count", 0.0)) if fire_boundary_loss else 0.0,
                )
                self.logger.record(
                    "m3s2/fb_pos_logit_mean",
                    (
                        float(fire_boundary_loss.executable_positive_logit_mean)
                        if fire_boundary_loss is not None
                        else 0.0
                    ),
                )
                self.logger.record(
                    "m3s2/fb_neg_logit_mean",
                    (
                        float(fire_boundary_loss.executable_negative_logit_mean)
                        if fire_boundary_loss is not None
                        else 0.0
                    ),
                )
                self.logger.record(
                    "m3s2/fb_pos_prob_mean",
                    (
                        float(fire_boundary_loss.executable_positive_prob_mean)
                        if fire_boundary_loss is not None
                        else 0.0
                    ),
                )
                self.logger.record(
                    "m3s2/fb_neg_prob_mean",
                    (
                        float(fire_boundary_loss.executable_negative_prob_mean)
                        if fire_boundary_loss is not None
                        else 0.0
                    ),
                )
                self.logger.record(
                    "m3s2/fb_direct_pos_delta_mean",
                    (
                        float(fire_boundary_loss.direct_head_positive_delta_mean)
                        if fire_boundary_loss is not None
                        else 0.0
                    ),
                )
                self.logger.record(
                    "m3s2/fb_direct_neg_delta_mean",
                    (
                        float(fire_boundary_loss.direct_head_negative_delta_mean)
                        if fire_boundary_loss is not None
                        else 0.0
                    ),
                )
                self.logger.record(
                    "m3s2/fb_accuracy",
                    float(getattr(fire_boundary_loss, "accuracy", 0.0)) if fire_boundary_loss else 0.0,
                )
                self.logger.record("m3s2/fb_cross_count", boundary_cross_count)
                self.logger.record(
                    "m3s2/fb_cross_ratio",
                    boundary_cross_count / active_count if active_count > 0.0 else 0.0,
                )
                self.logger.record("m3s2/fb_cross_in_window_count", boundary_cross_in_window_count)
                self.logger.record(
                    "m3s2/fb_cross_in_window_ratio",
                    (
                        boundary_cross_in_window_count / boundary_cross_count
                        if boundary_cross_count > 0.0
                        else 0.0
                    ),
                )
                self.logger.record(
                    "m3s2/fb_separate_update_enabled",
                    float(bool(getattr(self, "fire_boundary_separate_update_enabled", False))),
                )
                self.logger.record(
                    "m3s2/fb_dedicated_optimizer_enabled",
                    float(bool(getattr(self, "fire_boundary_dedicated_optimizer_enabled", False))),
                )
                self.logger.record(
                    "m3s2/fb_separate_update_steps",
                    int(getattr(self, "fire_boundary_separate_update_steps", 1)),
                )
                self.logger.record(
                    "m3s2/fb_neg_ceiling_coef",
                    float(getattr(self, "fire_boundary_negative_logit_ceiling_coef", 0.0)),
                )
                self.logger.record(
                    "m3s2/fb_neg_ceiling",
                    float(getattr(self, "fire_boundary_negative_logit_ceiling", 0.0)),
                )
                self.logger.record(
                    "m3s2/fb_pos_floor_coef",
                    float(getattr(self, "fire_boundary_positive_logit_floor_coef", 0.0)),
                )
                self.logger.record(
                    "m3s2/fb_pos_floor",
                    float(getattr(self, "fire_boundary_positive_logit_floor", 0.0)),
                )
                self.logger.record(
                    "m3s2/fb_support_collect_enabled",
                    float(bool(getattr(self, "fire_boundary_support_preserving_collect_enabled", False))),
                )
                self.logger.record(
                    "m3s2/fb_support_hold_quality_enabled",
                    float(bool(getattr(self, "fire_boundary_support_preserving_hold_quality_enabled", False))),
                )
            if event_window_enabled(self):
                sidecar = getattr(self, "_grouped_stopping_sidecar", None)
                stats = (
                    event_window_loss.stats
                    if event_window_loss is not None
                    else None
                )
                diagnostics = getattr(self, "_last_event_window_diagnostics", None)

                def stat_value(name: str) -> float:
                    return float(getattr(stats, name, 0.0)) if stats is not None else 0.0

                def diag_value(name: str) -> float:
                    return float(getattr(diagnostics, name, 0.0)) if diagnostics is not None else 0.0

                active_row_count = stat_value("active_row_count")
                boundary_cross_count = stat_value("boundary_cross_count")
                boundary_cross_in_window_count = stat_value("boundary_cross_in_window_count")
                closed_mask_stop_attempt_count = stat_value("closed_mask_stop_attempt_count")
                closed_mask_row_count = diag_value("closed_mask_row_count")
                self.logger.record(
                    "m3s2/event_window_coef",
                    float(getattr(self, "event_window_coef", 0.0)),
                )
                self.logger.record(
                    "m3s2/event_window_loss",
                    (
                        float(event_window_loss.loss.detach().cpu().item())
                        if event_window_loss is not None
                        else 0.0
                    ),
                )
                self.logger.record(
                    "m3s2/event_window_unscaled_loss",
                    (
                        float(event_window_loss.unscaled_loss.detach().cpu().item())
                        if event_window_loss is not None
                        else 0.0
                    ),
                )
                self.logger.record(
                    "m3s2/event_window_grad_norm",
                    float(getattr(self, "_last_event_window_grad_norm", 0.0)),
                )
                self.logger.record(
                    "m3s2/grouped_sidecar_group_count",
                    float(len(sidecar.groups)) if sidecar else 0.0,
                )
                self.logger.record("m3s2/grouped_active_group_count", stat_value("active_group_count"))
                self.logger.record("m3s2/grouped_row_count", stat_value("row_count"))
                self.logger.record("m3s2/grouped_active_row_count", active_row_count)
                self.logger.record("m3s2/window_group_count", stat_value("window_group_count"))
                self.logger.record("m3s2/no_window_group_count", stat_value("no_window_group_count"))
                self.logger.record("m3s2/early_prefix_group_count", stat_value("early_prefix_group_count"))
                self.logger.record("m3s2/right_censor_group_count", stat_value("right_censor_group_count"))
                self.logger.record("m3s2/hazard_window_mass", stat_value("mean_p_window"))
                self.logger.record("m3s2/hazard_early_mass", stat_value("mean_p_early"))
                self.logger.record("m3s2/hazard_deadline_mass", stat_value("mean_p_deadline"))
                self.logger.record("m3s2/no_event_mass", stat_value("mean_p_none"))
                self.logger.record("m3s2/quality_delay", stat_value("mean_quality_delay"))
                self.logger.record("m3s2/q_boundary_logit", stat_value("mean_quality_boundary_logit"))
                self.logger.record(
                    "m3s2/q_boundary_loss",
                    stat_value("mean_quality_boundary_margin_loss"),
                )
                self.logger.record(
                    "m3s2/q_pre_margin",
                    stat_value("mean_quality_prewindow_logit_margin"),
                )
                self.logger.record(
                    "m3s2/q_pre_margin_loss",
                    stat_value("mean_quality_prewindow_margin_loss"),
                )
                self.logger.record(
                    "m3s2/window_balanced_bce_loss",
                    stat_value("mean_window_balanced_bce_loss"),
                )
                self.logger.record("m3s2/prewindow_hazard_mean", stat_value("mean_prewindow_hazard_mean"))
                self.logger.record("m3s2/prewindow_hazard_max", stat_value("mean_prewindow_hazard_max"))
                self.logger.record("m3s2/prewindow_hazard_target", stat_value("mean_prewindow_hazard_target"))
                self.logger.record(
                    "m3s2/prewindow_hazard_scale_loss",
                    stat_value("mean_prewindow_hazard_scale_loss"),
                )
                self.logger.record("m3s2/quality_hazard_target", stat_value("mean_quality_hazard_target"))
                self.logger.record(
                    "m3s2/quality_hazard_target_loss",
                    stat_value("mean_quality_hazard_target_loss"),
                )
                self.logger.record(
                    "m3s2/prewindow_logit_ceiling",
                    stat_value("mean_prewindow_logit_ceiling"),
                )
                self.logger.record(
                    "m3s2/prewindow_logit_ceiling_loss",
                    stat_value("mean_prewindow_logit_ceiling_loss"),
                )
                self.logger.record(
                    "m3s2/quality_logit_floor",
                    stat_value("mean_quality_logit_floor"),
                )
                self.logger.record(
                    "m3s2/quality_logit_floor_loss",
                    stat_value("mean_quality_logit_floor_loss"),
                )
                self.logger.record("m3s2/event_logit_delta_mean", diag_value("stop_logit_mean"))
                self.logger.record("m3s2/event_logit_delta_window_mean", diag_value("stop_logit_desirable_mean"))
                self.logger.record("m3s2/event_logit_delta_prewindow_mean", diag_value("stop_logit_prewindow_mean"))
                self.logger.record("m3s2/event_logit_delta_no_window_mean", diag_value("stop_logit_no_window_mean"))
                self.logger.record("m3s2/event_logit_delta_closed_mask_mean", diag_value("stop_logit_closed_mask_mean"))
                self.logger.record("m3s2/event_logit_delta_count", diag_value("stop_logit_count"))
                self.logger.record("m3s2/event_logit_delta_window_count", diag_value("stop_logit_desirable_count"))
                self.logger.record("m3s2/event_logit_delta_prewindow_count", diag_value("stop_logit_prewindow_count"))
                self.logger.record("m3s2/event_logit_delta_no_window_count", diag_value("stop_logit_no_window_count"))
                self.logger.record("m3s2/boundary_cross_count", boundary_cross_count)
                self.logger.record(
                    "m3s2/boundary_cross_ratio",
                    boundary_cross_count / active_row_count if active_row_count > 0.0 else 0.0,
                )
                self.logger.record("m3s2/boundary_cross_in_window_count", boundary_cross_in_window_count)
                self.logger.record(
                    "m3s2/boundary_cross_in_window_ratio",
                    (
                        boundary_cross_in_window_count / boundary_cross_count
                        if boundary_cross_count > 0.0
                        else 0.0
                    ),
                )
                self.logger.record("m3s2/closed_mask_stop_attempt_count", closed_mask_stop_attempt_count)
                self.logger.record("m3s2/closed_mask_row_count", closed_mask_row_count)
                self.logger.record(
                    "m3s2/closed_mask_stop_attempt_ratio",
                    (
                        closed_mask_stop_attempt_count / closed_mask_row_count
                        if closed_mask_row_count > 0.0
                        else 0.0
                    ),
                )
                self.logger.record(
                    "m3s2/accepted_event_count",
                    float(getattr(sidecar, "accepted_event_count", 0.0)) if sidecar else 0.0,
                )
                self.logger.record(
                    "m3s2/one_shot_violation_count",
                    float(getattr(sidecar, "one_shot_violation_count", 0.0)) if sidecar else 0.0,
                )
                self.logger.record(
                    "m3s2/closed_mask_accepted_event_count",
                    float(getattr(sidecar, "closed_mask_accepted_event_count", 0.0)) if sidecar else 0.0,
                )
                self.logger.record(
                    "m3s2/event_window_separate_update_enabled",
                    float(bool(getattr(self, "event_window_separate_update_enabled", False))),
                )
                self.logger.record(
                    "m3s2/event_window_dedicated_optimizer_enabled",
                    float(bool(getattr(self, "event_window_dedicated_optimizer_enabled", False))),
                )
                self.logger.record(
                    "m3s2/event_window_use_stopping_head",
                    float(bool(getattr(self, "event_window_use_stopping_head", False))),
                )
                self.logger.record(
                    "m3s2/event_window_separate_update_steps",
                    int(getattr(self, "event_window_separate_update_steps", 1)),
                )
                self.logger.record(
                    "m3s2/event_window_delay_coef",
                    float(getattr(self, "event_window_delay_coef", 0.0)),
                )
                self.logger.record(
                    "m3s2/event_window_deadline_coef",
                    float(getattr(self, "event_window_deadline_coef", 0.0)),
                )
                self.logger.record(
                    "m3s2/event_window_deadline_steps",
                    int(getattr(self, "event_window_deadline_steps", 0)),
                )
                self.logger.record(
                    "m3s2/event_window_early_survival_coef",
                    float(getattr(self, "event_window_early_survival_coef", 0.0)),
                )
                self.logger.record(
                    "m3s2/ew_q_boundary_coef",
                    float(getattr(self, "event_window_quality_boundary_coef", 0.0)),
                )
                self.logger.record(
                    "m3s2/ew_q_boundary_logit",
                    float(getattr(self, "event_window_quality_boundary_logit", 0.0)),
                )
                self.logger.record(
                    "m3s2/ew_contrast_coef",
                    float(getattr(self, "event_window_contrastive_margin_coef", 0.0)),
                )
                self.logger.record(
                    "m3s2/ew_contrast_margin",
                    float(getattr(self, "event_window_contrastive_margin", 0.0)),
                )
                self.logger.record(
                    "m3s2/ew_balanced_bce_coef",
                    float(getattr(self, "event_window_balanced_bce_coef", 0.0)),
                )
                self.logger.record(
                    "m3s2/ew_prewindow_hazard_scale_coef",
                    float(getattr(self, "event_window_prewindow_hazard_scale_coef", 0.0)),
                )
                self.logger.record(
                    "m3s2/ew_prewindow_hazard_target",
                    float(getattr(self, "event_window_prewindow_hazard_target", 0.0)),
                )
                self.logger.record(
                    "m3s2/ew_quality_hazard_target_coef",
                    float(getattr(self, "event_window_quality_hazard_target_coef", 0.0)),
                )
                self.logger.record(
                    "m3s2/ew_quality_hazard_target",
                    float(getattr(self, "event_window_quality_hazard_target", 0.0)),
                )
                self.logger.record(
                    "m3s2/ew_prewindow_logit_ceiling_coef",
                    float(getattr(self, "event_window_prewindow_logit_ceiling_coef", 0.0)),
                )
                self.logger.record(
                    "m3s2/ew_prewindow_logit_ceiling",
                    float(getattr(self, "event_window_prewindow_logit_ceiling", 0.0)),
                )
                self.logger.record(
                    "m3s2/ew_quality_logit_floor_coef",
                    float(getattr(self, "event_window_quality_logit_floor_coef", 0.0)),
                )
                self.logger.record(
                    "m3s2/ew_quality_logit_floor",
                    float(getattr(self, "event_window_quality_logit_floor", 0.0)),
                )
                support_enabled = getattr(self, "_support_preserving_collect_enabled", None)
                self.logger.record(
                    "m3s2/support_preserving_collect_enabled",
                    float(callable(support_enabled) and support_enabled()),
                )
                self.logger.record(
                    "m3s2/support_preserving_hold_quality_enabled",
                    float(getattr(self, "event_window_support_preserving_hold_quality_enabled", False)),
                )
                self.logger.record(
                    "m3s2/support_preserving_hold_count",
                    float(getattr(self, "_support_preserving_collect_hold_count", 0)),
                )
                self.logger.record(
                    "m3s2/support_preserving_candidate_count",
                    float(getattr(self, "_support_preserving_collect_candidate_count", 0)),
                )
                self.logger.record(
                    "m3s2/support_preserving_quality_count",
                    float(getattr(self, "_support_preserving_collect_quality_count", 0)),
                )
            if grouped_stopping_enabled(self):
                sidecar = getattr(self, "_grouped_stopping_sidecar", None)
                stats = (
                    grouped_stopping_loss.stats
                    if grouped_stopping_loss is not None
                    else None
                )
                diagnostics = getattr(self, "_last_grouped_stopping_diagnostics", None)

                def stat_value(name: str) -> float:
                    return float(getattr(stats, name, 0.0)) if stats is not None else 0.0

                def diag_value(name: str) -> float:
                    return float(getattr(diagnostics, name, 0.0)) if diagnostics is not None else 0.0

                active_row_count = stat_value("active_row_count")
                boundary_cross_count = stat_value("boundary_cross_count")
                boundary_cross_in_window_count = stat_value("boundary_cross_in_window_count")
                closed_mask_stop_attempt_count = stat_value("closed_mask_stop_attempt_count")
                closed_mask_row_count = diag_value("closed_mask_row_count")
                self.logger.record(
                    "m3s1/grouped_stopping_coef",
                    float(getattr(self, "grouped_stopping_coef", 0.0)),
                )
                self.logger.record(
                    "m3s1/grouped_stopping_loss",
                    (
                        float(grouped_stopping_loss.loss.detach().cpu().item())
                        if grouped_stopping_loss is not None
                        else 0.0
                    ),
                )
                self.logger.record(
                    "m3s1/grouped_stopping_unscaled_loss",
                    (
                        float(grouped_stopping_loss.unscaled_loss.detach().cpu().item())
                        if grouped_stopping_loss is not None
                        else 0.0
                    ),
                )
                self.logger.record(
                    "m3s1/grouped_stopping_grad_norm",
                    float(getattr(self, "_last_grouped_stopping_grad_norm", 0.0)),
                )
                self.logger.record(
                    "m3s1/grouped_sidecar_group_count",
                    float(len(sidecar.groups)) if sidecar else 0.0,
                )
                self.logger.record("m3s1/grouped_active_group_count", stat_value("active_group_count"))
                self.logger.record("m3s1/grouped_row_count", stat_value("row_count"))
                self.logger.record("m3s1/grouped_active_row_count", active_row_count)
                self.logger.record("m3s1/window_group_count", stat_value("window_group_count"))
                self.logger.record("m3s1/no_window_group_count", stat_value("no_window_group_count"))
                self.logger.record("m3s1/early_prefix_group_count", stat_value("early_prefix_group_count"))
                self.logger.record("m3s1/right_censor_group_count", stat_value("right_censor_group_count"))
                self.logger.record(
                    "m3s1/grouped_labels_reached_loss",
                    1.0 if stats is not None and int(getattr(stats, "active_group_count", 0)) > 0 else 0.0,
                )
                self.logger.record("m3s1/hazard_desirable_mass", stat_value("mean_p_window"))
                self.logger.record("m3s1/hazard_early_mass", stat_value("mean_p_early"))
                self.logger.record("m3s1/no_event_mass", stat_value("mean_p_none"))
                self.logger.record("m3s1/stop_logit_mean", diag_value("stop_logit_mean"))
                self.logger.record("m3s1/stop_logit_desirable_mean", diag_value("stop_logit_desirable_mean"))
                self.logger.record("m3s1/stop_logit_prewindow_mean", diag_value("stop_logit_prewindow_mean"))
                self.logger.record("m3s1/stop_logit_no_window_mean", diag_value("stop_logit_no_window_mean"))
                self.logger.record("m3s1/stop_logit_closed_mask_mean", diag_value("stop_logit_closed_mask_mean"))
                self.logger.record("m3s1/stop_logit_count", diag_value("stop_logit_count"))
                self.logger.record("m3s1/stop_logit_desirable_count", diag_value("stop_logit_desirable_count"))
                self.logger.record("m3s1/stop_logit_prewindow_count", diag_value("stop_logit_prewindow_count"))
                self.logger.record("m3s1/stop_logit_no_window_count", diag_value("stop_logit_no_window_count"))
                self.logger.record(
                    "m3s1/event_logit_delta_diagnostic_mean",
                    diag_value("event_logit_delta_diagnostic_mean"),
                )
                self.logger.record(
                    "m3s1/event_logit_delta_diagnostic_count",
                    diag_value("event_logit_delta_diagnostic_count"),
                )
                self.logger.record("m3s1/boundary_cross_count", boundary_cross_count)
                self.logger.record(
                    "m3s1/boundary_cross_ratio",
                    boundary_cross_count / active_row_count if active_row_count > 0.0 else 0.0,
                )
                self.logger.record(
                    "m3s1/boundary_cross_in_window_count",
                    boundary_cross_in_window_count,
                )
                self.logger.record(
                    "m3s1/boundary_cross_in_window_ratio",
                    (
                        boundary_cross_in_window_count / boundary_cross_count
                        if boundary_cross_count > 0.0
                        else 0.0
                    ),
                )
                self.logger.record(
                    "m3s1/closed_mask_stop_attempt_count",
                    closed_mask_stop_attempt_count,
                )
                self.logger.record("m3s1/closed_mask_row_count", closed_mask_row_count)
                self.logger.record(
                    "m3s1/closed_mask_stop_attempt_ratio",
                    (
                        closed_mask_stop_attempt_count / closed_mask_row_count
                        if closed_mask_row_count > 0.0
                        else 0.0
                    ),
                )
                self.logger.record(
                    "m3s1/accepted_event_count",
                    float(getattr(sidecar, "accepted_event_count", 0.0)) if sidecar else 0.0,
                )
                self.logger.record(
                    "m3s1/one_shot_violation_count",
                    float(getattr(sidecar, "one_shot_violation_count", 0.0)) if sidecar else 0.0,
                )
                self.logger.record(
                    "m3s1/closed_mask_accepted_event_count",
                    float(getattr(sidecar, "closed_mask_accepted_event_count", 0.0)) if sidecar else 0.0,
                )
                self.logger.record(
                    "m3s1/grouped_stopping_detach_latent",
                    float(bool(getattr(self, "grouped_stopping_detach_latent", False))),
                )
            if bool(getattr(self, "_event_credit_enabled", lambda: False)()):
                self.logger.record(
                    "a7/event_credit_loss",
                    float(np.mean(first_event_credit_losses)) if first_event_credit_losses else 0.0,
                )
                self.logger.record(
                    "a7/event_credit_value_loss",
                    float(np.mean(first_event_credit_value_losses)) if first_event_credit_value_losses else 0.0,
                )
                self.logger.record(
                    "a7/event_credit_delta_align_loss",
                    (
                        float(np.mean(first_event_credit_delta_align_losses))
                        if first_event_credit_delta_align_losses
                        else 0.0
                    ),
                )
                self.logger.record(
                    "a7/event_credit_value_coef",
                    float(getattr(self, "event_credit_value_coef", 0.0)),
                )
                self.logger.record(
                    "a7/event_credit_delta_align_coef",
                    float(getattr(self, "event_credit_delta_align_coef", 0.0)),
                )
                self.logger.record(
                    "a7/event_credit_delta_align_positive_only",
                    float(bool(getattr(self, "event_credit_delta_align_positive_only", False))),
                )
                self.logger.record(
                    "a7/evc_separate_update_enabled",
                    float(bool(getattr(self, "event_credit_separate_update_enabled", False))),
                )
                self.logger.record(
                    "a7/evc_separate_update_max_grad_norm",
                    float(getattr(self, "event_credit_separate_update_max_grad_norm", 0.0)),
                )
                self.logger.record(
                    "a7/evc_separate_update_count_mean",
                    (
                        float(np.mean(first_event_credit_separate_update_counts))
                        if first_event_credit_separate_update_counts
                        else 0.0
                    ),
                )
                self.logger.record(
                    "a7/evc_separate_update_grad_norm_mean",
                    (
                        float(np.mean(first_event_credit_separate_update_grad_norms))
                        if first_event_credit_separate_update_grad_norms
                        else 0.0
                    ),
                )
                self.logger.record(
                    "a7/evc_cross_rollout_context_rows",
                    float(getattr(self, "_cross_rollout_last_context_row_count", 0)),
                )
                self.logger.record(
                    "a7/evc_carried_shadow_pending_envs",
                    float(getattr(self, "_cross_rollout_last_carried_shadow_pending_envs", 0)),
                )
                self.logger.record(
                    "a7/evc_carried_shadow_positive_count_mean",
                    float(getattr(self, "_cross_rollout_last_carried_shadow_positive_count", 0)),
                )
                self.logger.record(
                    "a7/evc_cross_rollout_first_event_count_mean",
                    float(getattr(self, "_cross_rollout_last_first_event_count", 0)),
                )
                self.logger.record(
                    "a7/event_credit_legal_open_quality_weight",
                    float(getattr(self, "event_credit_legal_open_quality_weight", 0.0)),
                )
                self.logger.record(
                    "a7/evc_proj_enabled",
                    float(bool(getattr(self, "event_credit_legal_projection_enabled", False))),
                )
                self.logger.record(
                    "a7/evc_proj_value_coef",
                    float(getattr(self, "event_credit_projection_value_coef", 0.0)),
                )
                self.logger.record(
                    "a7/evc_proj_delta_coef",
                    float(getattr(self, "event_credit_projection_delta_align_coef", 0.0)),
                )
                self.logger.record(
                    "a7/event_credit_active_count_mean",
                    float(np.mean(first_event_credit_active_counts)) if first_event_credit_active_counts else 0.0,
                )
                self.logger.record(
                    "a7/event_credit_target_positive_frac",
                    float(np.mean(first_event_credit_positive_fracs)) if first_event_credit_positive_fracs else 0.0,
                )
                self.logger.record(
                    "a7/event_credit_advantage_mean",
                    float(np.mean(first_event_credit_advantage_means)) if first_event_credit_advantage_means else 0.0,
                )
                self.logger.record(
                    "a7/evc_proj_active_count_mean",
                    (
                        float(np.mean(first_event_credit_projection_active_counts))
                        if first_event_credit_projection_active_counts
                        else 0.0
                    ),
                )
                self.logger.record(
                    "a7/evc_proj_candidate_count_mean",
                    (
                        float(np.mean(first_event_credit_projection_candidate_counts))
                        if first_event_credit_projection_candidate_counts
                        else 0.0
                    ),
                )
                self.logger.record(
                    "a7/evc_proj_unsupported_count_mean",
                    (
                        float(np.mean(first_event_credit_projection_unsupported_counts))
                        if first_event_credit_projection_unsupported_counts
                        else 0.0
                    ),
                )
                self.logger.record(
                    "a7/evc_src_shadow_count_mean",
                    float(np.mean(first_event_credit_source_shadow_counts))
                    if first_event_credit_source_shadow_counts
                    else 0.0,
                )
                self.logger.record(
                    "a7/evc_src_deadline_count_mean",
                    float(np.mean(first_event_credit_source_deadline_counts))
                    if first_event_credit_source_deadline_counts
                    else 0.0,
                )
                self.logger.record(
                    "a7/evc_src_early_count_mean",
                    float(np.mean(first_event_credit_source_early_counts))
                    if first_event_credit_source_early_counts
                    else 0.0,
                )
                self.logger.record(
                    "a7/evc_src_pre_count_mean",
                    float(np.mean(first_event_credit_source_prewindow_counts))
                    if first_event_credit_source_prewindow_counts
                    else 0.0,
                )
                self.logger.record(
                    "a7/evc_src_legal_open_quality_count_mean",
                    float(np.mean(first_event_credit_source_legal_open_quality_counts))
                    if first_event_credit_source_legal_open_quality_counts
                    else 0.0,
                )
                self.logger.record(
                    "a7/evc_src_legal_open_quality_positive_count_mean",
                    float(np.mean(first_event_credit_source_legal_open_quality_positive_counts))
                    if first_event_credit_source_legal_open_quality_positive_counts
                    else 0.0,
                )
                self.logger.record(
                    "a7/evc_src_deadline_positive_count_mean",
                    float(np.mean(first_event_credit_source_deadline_positive_counts))
                    if first_event_credit_source_deadline_positive_counts
                    else 0.0,
                )
                self.logger.record(
                    "a7/evc_src_shadow_positive_count_mean",
                    float(np.mean(first_event_credit_source_shadow_positive_counts))
                    if first_event_credit_source_shadow_positive_counts
                    else 0.0,
                )
                self.logger.record(
                    "a7/evc_src_legal_open_quality_advantage_mean",
                    float(np.mean(first_event_credit_source_legal_open_quality_advantage_means))
                    if first_event_credit_source_legal_open_quality_advantage_means
                    else 0.0,
                )
                self.logger.record(
                    "a7/evc_proj_advantage_mean",
                    (
                        float(np.mean(first_event_credit_projection_advantage_means))
                        if first_event_credit_projection_advantage_means
                        else 0.0
                    ),
                )
                self.logger.record(
                    "a7/evc_proj_delta_mean",
                    (
                        float(np.mean(first_event_credit_projection_delta_means))
                        if first_event_credit_projection_delta_means
                        else 0.0
                    ),
                )

            self.logger.record("train/n_updates", int(self._n_updates), exclude="tensorboard")
            self.logger.record("train/clip_range", float(clip_range))
            if clip_range_vf is not None:
                self.logger.record("train/clip_range_vf", float(clip_range_vf))
            self.logger.record("train/kl_penalty_coef", float(self.kl_penalty_coef))
            self.logger.record("train/kl_lr_mult", float(self._lr_mult))
            self.logger.record("train/kl_clip_mult", float(self._clip_mult))
            self.logger.record("train/kl_low_streak", int(self._low_kl_streak))

        model.collect_rollouts = MethodType(traced_collect_rollouts, model)
        model.train = MethodType(traced_train, model)

    def _patch_save_exclusions(self, model) -> None:
        original_excluded_save_params = model._excluded_save_params

        def traced_excluded_save_params(self) -> list[str]:
            excluded = list(original_excluded_save_params())
            extra = {
                "_nonfinite_probe",
                "_nonfinite_probe_report_path",
                "_excluded_save_params",
                "collect_rollouts",
                "train",
            }
            for name in extra:
                if name not in excluded:
                    excluded.append(name)
            return excluded

        model._excluded_save_params = MethodType(traced_excluded_save_params, model)
