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

        def traced_collect_rollouts(self, env, callback, rollout_buffer, n_rollout_steps: int) -> bool:
            assert self._last_obs is not None, "No previous observation was provided"
            self.policy.set_training_mode(False)
            set_training_progress = getattr(self.policy, "set_hmoe_training_progress", None)
            if callable(set_training_progress):
                set_training_progress(float(self._current_progress_remaining))

            n_steps = 0
            rollout_buffer.reset()
            if self.use_sde:
                self.policy.reset_noise(env.num_envs)

            callback.on_rollout_start()

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

            with th.no_grad():
                values = self.policy.predict_values(self._get_policy_obs_tensor(env, new_obs))
                tracer.check("rollout.last_values", values)

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
            clip_fractions = []
            approx_kl_divs = []
            continue_training = True

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
