#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import math
import os
import sys
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch as th
from torch.nn import functional as F

_REPO_ROOT_HINT = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT_HINT = os.path.dirname(_REPO_ROOT_HINT)
_REPO_ROOT_HINT = os.path.dirname(_REPO_ROOT_HINT)
if _REPO_ROOT_HINT not in sys.path:
    sys.path.insert(0, _REPO_ROOT_HINT)
from python.runtime_bootstrap import ensure_repo_imports

ensure_repo_imports()

from python.rl.policy_algo.first_event_hazard import (  # noqa: E402
    FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY,
    FIRST_EVENT_SOURCE_SHADOW_QUALITY,
    FirstEventCreditLoss,
    FirstEventHazardLabels,
    build_first_event_hazard_labels,
    compute_first_event_credit_loss,
)
from python.rl.policy_algo.first_event_projection import (  # noqa: E402
    project_air_combat_c2_roe_legal_open_observations,
)
from python.rl.policy_algo.ppo_adaptive_kl import AdaptiveKLPPO  # noqa: E402
from tools.diagnostics.common import (  # noqa: E402
    EpisodeEnd,
    EpisodeStepTransition,
    collect_episode_steps,
)
from tools.diagnostics.event_credit_head.offline_fit import (  # noqa: E402
    DEFAULT_MODEL,
    DEFAULT_SCENARIO,
    DEFAULT_TRAIN_CONFIG,
    SOURCE_NAMES,
    _concat_obs,
    _finite_float,
    _hyper,
    _labels_to_device,
    _obs_to_cpu,
    _policy_fire_mask_from_obs,
    _policy_launch_window_from_obs,
    _slice_obs,
    _to_serializable,
    collect_fixed_batch,
    evaluate_credit_head,
    evaluate_label_summary,
)
from tools.diagnostics.air_combat_weapon_employment_process_probe import _build_env  # noqa: E402
from tools.eval.sb3_eval_base import load_json_config, load_sb3_policy  # noqa: E402


PARAM_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("credit_head", ("hybrid_event_credit_head.",)),
    ("event_head", ("hybrid_event_head.",)),
    ("actor_mlp", ("mlp_extractor.policy_net.",)),
    ("shared_mlp", ("mlp_extractor.shared_net.",)),
    ("critic_mlp", ("mlp_extractor.value_net.",)),
    ("action_net", ("action_net.",)),
    ("hmoe", ("hmoe_head_bank.",)),
    ("features", ("features_extractor.",)),
    ("log_std", ("log_std",)),
    ("value_net", ("value_net.",)),
)


@dataclass(frozen=True)
class OnlineRolloutBatch:
    observations: dict[str, th.Tensor]
    actions: th.Tensor
    old_values: th.Tensor
    old_log_prob: th.Tensor
    advantages: th.Tensor
    returns: th.Tensor
    labels: FirstEventHazardLabels
    meta: dict[str, Any]


def _param_group_name(name: str) -> str:
    for group_name, prefixes in PARAM_GROUPS:
        for prefix in prefixes:
            if name == prefix or name.startswith(prefix):
                return group_name
    return "other"


def _flatten_grads(policy, group_name: str | None = None) -> th.Tensor:
    chunks: list[th.Tensor] = []
    for name, param in policy.named_parameters():
        if group_name is not None and _param_group_name(str(name)) != str(group_name):
            continue
        if param.grad is None:
            continue
        chunks.append(param.grad.detach().reshape(-1).to(device="cpu", dtype=th.float64))
    if not chunks:
        return th.zeros((0,), dtype=th.float64)
    return th.cat(chunks, dim=0)


def _tensor_norm(value: th.Tensor) -> float:
    if int(value.numel()) <= 0:
        return 0.0
    norm = float(value.norm().item())
    return norm if math.isfinite(norm) else 0.0


def _cosine(a: th.Tensor, b: th.Tensor) -> float | None:
    if int(a.numel()) <= 0 or int(b.numel()) <= 0 or int(a.numel()) != int(b.numel()):
        return None
    denom = float(a.norm().item() * b.norm().item())
    if denom <= 0.0 or not math.isfinite(denom):
        return None
    value = float(th.dot(a, b).item() / denom)
    return value if math.isfinite(value) else None


def _optimizer_lrs(policy) -> list[dict[str, Any]]:
    optimizer = getattr(policy, "optimizer", None)
    if optimizer is None:
        return []
    out: list[dict[str, Any]] = []
    for index, group in enumerate(optimizer.param_groups):
        params = list(group.get("params", []))
        out.append(
            {
                "index": int(index),
                "name": str(group.get("name", "")),
                "lr": float(group.get("lr", 0.0)),
                "lr_scale": float(group.get("lr_scale", 1.0)),
                "param_count": int(sum(int(param.numel()) for param in params)),
            }
        )
    return out


def _set_optimizer_lrs(policy, learning_rate: float) -> None:
    apply_lr = getattr(policy, "apply_optimizer_learning_rate", None)
    if callable(apply_lr):
        apply_lr(float(learning_rate), lr_mult=1.0)
        return
    optimizer = getattr(policy, "optimizer", None)
    if optimizer is None:
        return
    for group in optimizer.param_groups:
        group["lr"] = float(learning_rate)


def _compute_credit_loss_parts(
    policy,
    obs: dict[str, th.Tensor],
    labels: dict[str, th.Tensor],
    hyper: dict[str, Any],
    *,
    value_coef: float,
    delta_align_coef: float,
    include_projection: bool,
) -> FirstEventCreditLoss:
    distribution = policy.get_distribution(obs)
    q_getter = getattr(distribution, "fire_event_q_values", None)
    if not callable(q_getter):
        raise RuntimeError("policy distribution does not expose fire_event_q_values")
    q_values = q_getter()
    if q_values is None:
        raise RuntimeError("fire_event_q_values returned None")
    delta_getter = getattr(distribution, "fire_event_logit_delta", None)
    event_delta = delta_getter() if callable(delta_getter) else None
    source = labels["source"]
    delta_align_active = source != int(FIRST_EVENT_SOURCE_SHADOW_QUALITY)
    base_loss = compute_first_event_credit_loss(
        q_values,
        labels["target"],
        labels["active"],
        labels["weight"],
        event_logit_delta=event_delta,
        window_id=labels["window_id"],
        value_coef=float(value_coef),
        delta_align_coef=float(delta_align_coef),
        delta_align_clip=_finite_float(hyper.get("event_credit_delta_align_clip", 4.0), 4.0),
        delta_align_active=delta_align_active,
        positive_mass_cap=_finite_float(hyper.get("event_credit_positive_mass_cap", 1.0), 1.0),
        negative_mass_cap=_finite_float(hyper.get("event_credit_negative_mass_cap", 1.0), 1.0),
    )
    if not bool(include_projection):
        return base_loss
    if not bool(hyper.get("event_credit_legal_projection_enabled", False)):
        return base_loss
    projection_value_coef = _finite_float(hyper.get("event_credit_projection_value_coef", 0.0), 0.0)
    projection_delta_coef = _finite_float(hyper.get("event_credit_projection_delta_align_coef", 0.0), 0.0)
    if projection_value_coef <= 0.0 and projection_delta_coef <= 0.0:
        return base_loss

    shadow_active = labels["active"].reshape(-1).to(dtype=th.bool) & (
        source.reshape(-1).long() == int(FIRST_EVENT_SOURCE_SHADOW_QUALITY)
    )
    projection = project_air_combat_c2_roe_legal_open_observations(obs, shadow_active)
    if projection is None:
        return base_loss
    projected_active = projection.active.to(device=q_values.device).reshape(-1).to(dtype=th.bool)
    if int(projected_active.sum().detach().cpu().item()) <= 0:
        return FirstEventCreditLoss(
            loss=base_loss.loss,
            value_loss=base_loss.value_loss,
            delta_align_loss=base_loss.delta_align_loss,
            unscaled_value_loss=base_loss.unscaled_value_loss,
            unscaled_delta_align_loss=base_loss.unscaled_delta_align_loss,
            active_count=base_loss.active_count,
            positive_count=base_loss.positive_count,
            weight_sum=base_loss.weight_sum,
            positive_frac=base_loss.positive_frac,
            advantage_mean=base_loss.advantage_mean,
            advantage_abs_mean=base_loss.advantage_abs_mean,
            projection_candidate_count=int(shadow_active.sum().detach().cpu().item()),
            projection_unsupported_count=int(projection.unsupported_count),
        )

    projected_distribution = policy.get_distribution(projection.observations)
    projected_q_getter = getattr(projected_distribution, "fire_event_q_values", None)
    if not callable(projected_q_getter):
        return base_loss
    projected_q_values = projected_q_getter()
    if projected_q_values is None:
        return base_loss
    projected_delta_getter = getattr(projected_distribution, "fire_event_logit_delta", None)
    projected_delta = projected_delta_getter() if callable(projected_delta_getter) else None
    projected_targets = th.ones_like(labels["target"].reshape(-1), dtype=th.float32, device=projected_q_values.device)
    projection_loss = compute_first_event_credit_loss(
        projected_q_values,
        projected_targets,
        projected_active.to(device=projected_q_values.device),
        labels["weight"].to(device=projected_q_values.device),
        event_logit_delta=projected_delta,
        window_id=labels["window_id"].to(device=projected_q_values.device),
        value_coef=float(projection_value_coef) if float(value_coef) > 0.0 else 0.0,
        delta_align_coef=float(projection_delta_coef) if float(delta_align_coef) > 0.0 else 0.0,
        delta_align_clip=_finite_float(hyper.get("event_credit_delta_align_clip", 4.0), 4.0),
        delta_align_active=projected_active.to(device=projected_q_values.device),
        positive_mass_cap=_finite_float(hyper.get("event_credit_positive_mass_cap", 1.0), 1.0),
        negative_mass_cap=_finite_float(hyper.get("event_credit_negative_mass_cap", 1.0), 1.0),
    )
    combined_active = int(base_loss.active_count) + int(projection_loss.active_count)
    combined_positive = int(base_loss.positive_count) + int(projection_loss.positive_count)
    return FirstEventCreditLoss(
        loss=base_loss.loss + projection_loss.loss,
        value_loss=base_loss.value_loss + projection_loss.value_loss,
        delta_align_loss=base_loss.delta_align_loss + projection_loss.delta_align_loss,
        unscaled_value_loss=base_loss.unscaled_value_loss + projection_loss.unscaled_value_loss,
        unscaled_delta_align_loss=base_loss.unscaled_delta_align_loss
        + projection_loss.unscaled_delta_align_loss,
        active_count=combined_active,
        positive_count=combined_positive,
        weight_sum=float(base_loss.weight_sum) + float(projection_loss.weight_sum),
        positive_frac=(float(combined_positive) / float(combined_active)) if combined_active > 0 else 0.0,
        advantage_mean=base_loss.advantage_mean,
        advantage_abs_mean=base_loss.advantage_abs_mean,
        projection_active_count=int(projection_loss.active_count),
        projection_candidate_count=int(shadow_active.sum().detach().cpu().item()),
        projection_unsupported_count=int(projection.unsupported_count),
    )


def _compute_ppo_loss(policy, batch: OnlineRolloutBatch, indices: th.Tensor, hyper: dict[str, Any]) -> tuple[th.Tensor, dict[str, Any]]:
    device = th.device(policy.device)
    obs = _slice_obs(batch.observations, indices, device)
    actions = batch.actions.index_select(0, indices.to(device=batch.actions.device)).to(device=device)
    old_log_prob = batch.old_log_prob.index_select(0, indices.to(device=batch.old_log_prob.device)).to(device=device)
    old_values = batch.old_values.index_select(0, indices.to(device=batch.old_values.device)).to(device=device)
    returns = batch.returns.index_select(0, indices.to(device=batch.returns.device)).to(device=device)
    advantages = batch.advantages.index_select(0, indices.to(device=batch.advantages.device)).to(device=device)
    if bool(hyper.get("normalize_advantage", True)) and int(advantages.numel()) > 1:
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1.0e-8)

    values, log_prob, entropy = policy.evaluate_actions(obs, actions)
    values = values.flatten()
    log_prob = log_prob.flatten()
    clip_range = _finite_float(hyper.get("clip_range", 0.2), 0.2)
    clip_range_vf = _finite_float(hyper.get("clip_range_vf", clip_range), clip_range)
    ratio = th.exp(log_prob - old_log_prob)
    policy_loss = -th.min(
        advantages * ratio,
        advantages * th.clamp(ratio, 1.0 - clip_range, 1.0 + clip_range),
    ).mean()
    values_pred = old_values + th.clamp(values - old_values, -clip_range_vf, clip_range_vf)
    value_loss = F.mse_loss(returns, values_pred)
    entropy_loss = -th.mean(-log_prob) if entropy is None else -th.mean(entropy)
    log_ratio = log_prob - old_log_prob
    approx_kl = th.mean((th.exp(log_ratio) - 1.0) - log_ratio)
    loss = (
        policy_loss
        + _finite_float(hyper.get("ent_coef", 0.0), 0.0) * entropy_loss
        + _finite_float(hyper.get("vf_coef", 0.0), 0.0) * value_loss
        + _finite_float(hyper.get("kl_penalty_coef", 0.0), 0.0) * approx_kl
    )
    meta = {
        "policy_loss": float(policy_loss.detach().cpu().item()),
        "value_loss": float(value_loss.detach().cpu().item()),
        "entropy_loss": float(entropy_loss.detach().cpu().item()),
        "approx_kl": float(approx_kl.detach().cpu().item()),
        "advantage_mean": float(advantages.detach().mean().cpu().item()),
        "advantage_std": float(advantages.detach().std().cpu().item()) if int(advantages.numel()) > 1 else 0.0,
        "ratio_mean": float(ratio.detach().mean().cpu().item()),
    }
    return loss, meta


def _loss_for_kind(
    policy,
    kind: str,
    obs: dict[str, th.Tensor],
    labels: dict[str, th.Tensor],
    hyper: dict[str, Any],
    *,
    include_projection: bool,
    online_batch: OnlineRolloutBatch | None,
    indices: th.Tensor,
) -> tuple[th.Tensor, dict[str, Any]]:
    if kind == "value":
        loss_obj = _compute_credit_loss_parts(
            policy,
            obs,
            labels,
            hyper,
            value_coef=_finite_float(hyper.get("event_credit_value_coef", 0.0), 0.0),
            delta_align_coef=0.0,
            include_projection=include_projection,
        )
        return loss_obj.loss, _credit_loss_meta(loss_obj)
    if kind == "delta":
        loss_obj = _compute_credit_loss_parts(
            policy,
            obs,
            labels,
            hyper,
            value_coef=0.0,
            delta_align_coef=_finite_float(hyper.get("event_credit_delta_align_coef", 0.0), 0.0),
            include_projection=include_projection,
        )
        return loss_obj.loss, _credit_loss_meta(loss_obj)
    if kind == "combined":
        loss_obj = _compute_credit_loss_parts(
            policy,
            obs,
            labels,
            hyper,
            value_coef=_finite_float(hyper.get("event_credit_value_coef", 0.0), 0.0),
            delta_align_coef=_finite_float(hyper.get("event_credit_delta_align_coef", 0.0), 0.0),
            include_projection=include_projection,
        )
        return loss_obj.loss, _credit_loss_meta(loss_obj)
    if kind == "ppo":
        if online_batch is None:
            raise RuntimeError("ppo loss requested without an online rollout batch")
        return _compute_ppo_loss(policy, online_batch, indices, hyper)
    if kind == "ppo_plus_a7":
        if online_batch is None:
            raise RuntimeError("ppo_plus_a7 loss requested without an online rollout batch")
        ppo_loss, ppo_meta = _compute_ppo_loss(policy, online_batch, indices, hyper)
        credit_loss = _compute_credit_loss_parts(
            policy,
            obs,
            labels,
            hyper,
            value_coef=_finite_float(hyper.get("event_credit_value_coef", 0.0), 0.0),
            delta_align_coef=_finite_float(hyper.get("event_credit_delta_align_coef", 0.0), 0.0),
            include_projection=include_projection,
        )
        meta = dict(ppo_meta)
        meta.update({f"{key}": value for key, value in _credit_loss_meta(credit_loss).items()})
        return ppo_loss + credit_loss.loss, meta
    raise ValueError(f"unknown loss kind: {kind}")


def _credit_loss_meta(loss_obj: FirstEventCreditLoss) -> dict[str, Any]:
    return {
        "loss": float(loss_obj.loss.detach().cpu().item()),
        "value_loss": float(loss_obj.value_loss.detach().cpu().item()),
        "delta_align_loss": float(loss_obj.delta_align_loss.detach().cpu().item()),
        "unscaled_value_loss": float(loss_obj.unscaled_value_loss.detach().cpu().item()),
        "unscaled_delta_align_loss": float(loss_obj.unscaled_delta_align_loss.detach().cpu().item()),
        "active_count": int(loss_obj.active_count),
        "positive_count": int(loss_obj.positive_count),
        "positive_frac": float(loss_obj.positive_frac),
        "weight_sum": float(loss_obj.weight_sum),
        "advantage_mean": float(loss_obj.advantage_mean),
        "advantage_abs_mean": float(loss_obj.advantage_abs_mean),
        "projection_active_count": int(loss_obj.projection_active_count),
        "projection_candidate_count": int(loss_obj.projection_candidate_count),
        "projection_unsupported_count": int(loss_obj.projection_unsupported_count),
    }


def _gradient_stats_for_loss(
    policy,
    kind: str,
    obs: dict[str, th.Tensor],
    labels: dict[str, th.Tensor],
    hyper: dict[str, Any],
    *,
    include_projection: bool,
    max_grad_norm: float,
    online_batch: OnlineRolloutBatch | None,
    indices: th.Tensor,
) -> dict[str, Any]:
    policy.optimizer.zero_grad(set_to_none=True)
    loss, meta = _loss_for_kind(
        policy,
        kind,
        obs,
        labels,
        hyper,
        include_projection=include_projection,
        online_batch=online_batch,
        indices=indices,
    )
    loss.backward()
    total_grad = _flatten_grads(policy)
    total_norm = _tensor_norm(total_grad)
    clip_scale = 1.0
    if float(max_grad_norm) > 0.0 and total_norm > float(max_grad_norm):
        clip_scale = float(max_grad_norm) / max(total_norm, 1.0e-12)
    groups: dict[str, Any] = {}
    for group_name, _prefixes in PARAM_GROUPS:
        vec = _flatten_grads(policy, group_name)
        groups[group_name] = {
            "norm": _tensor_norm(vec),
            "effective_norm_after_global_clip": _tensor_norm(vec) * clip_scale,
            "nonzero": int(vec.numel() > 0 and _tensor_norm(vec) > 0.0),
            "elements": int(vec.numel()),
        }
    other = _flatten_grads(policy, "other")
    groups["other"] = {
        "norm": _tensor_norm(other),
        "effective_norm_after_global_clip": _tensor_norm(other) * clip_scale,
        "nonzero": int(other.numel() > 0 and _tensor_norm(other) > 0.0),
        "elements": int(other.numel()),
    }
    vectors = {name: _flatten_grads(policy, name) for name, _prefixes in PARAM_GROUPS}
    vectors["all"] = total_grad
    policy.optimizer.zero_grad(set_to_none=True)
    return {
        "kind": str(kind),
        "loss": float(loss.detach().cpu().item()),
        "loss_meta": meta,
        "total_grad_norm": float(total_norm),
        "global_clip_scale": float(clip_scale),
        "groups": groups,
        "_vectors": vectors,
    }


def _select_indices(labels: FirstEventHazardLabels, count: int, batch_size: int, seed: int) -> th.Tensor:
    batch = min(int(batch_size), int(count))
    if batch >= count:
        return th.arange(count, dtype=th.long)
    rng = np.random.default_rng(int(seed))
    active = labels.active.detach().cpu().reshape(-1).to(dtype=th.bool)
    weight = labels.weight.detach().cpu().reshape(-1).float()
    source = labels.source.detach().cpu().reshape(-1).long()
    target = labels.target.detach().cpu().reshape(-1).float()
    legal_positive = active & (weight > 0.0) & (target > 0.5) & (
        source == int(FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY)
    )
    active_negative = active & (weight > 0.0) & (target <= 0.5)
    selected: list[int] = []
    for mask, quota_frac in ((legal_positive, 0.5), (active_negative, 0.25)):
        candidates = th.nonzero(mask, as_tuple=False).reshape(-1).cpu().numpy().astype(np.int64)
        if candidates.size <= 0:
            continue
        quota = min(candidates.size, max(1, int(round(batch * quota_frac))))
        selected.extend(rng.choice(candidates, size=quota, replace=False).astype(np.int64).tolist())
    selected_set = {int(value) for value in selected}
    remaining_quota = batch - len(selected_set)
    if remaining_quota > 0:
        remaining = np.asarray([idx for idx in range(count) if idx not in selected_set], dtype=np.int64)
        if remaining.size > 0:
            selected.extend(rng.choice(remaining, size=min(remaining_quota, remaining.size), replace=False).tolist())
    selected = sorted({int(value) for value in selected})[:batch]
    if len(selected) < batch:
        extras = [idx for idx in range(count) if idx not in set(selected)]
        selected.extend(extras[: batch - len(selected)])
    return th.as_tensor(selected[:batch], dtype=th.long)


def _event_policy_stats(policy, obs: dict[str, th.Tensor], labels: FirstEventHazardLabels, *, batch_size: int) -> dict[str, Any]:
    device = th.device(policy.device)
    count = int(next(iter(obs.values())).shape[0])
    chunks: list[dict[str, th.Tensor]] = []
    policy.set_training_mode(False)
    with th.no_grad():
        for start in range(0, count, int(batch_size)):
            end = min(count, start + int(batch_size))
            indices = th.arange(start, end, dtype=th.long)
            dist = policy.get_distribution(_slice_obs(obs, indices, device))
            delta_getter = getattr(dist, "fire_event_logit_delta", None)
            prob_getter = getattr(dist, "fire_event_probability", None)
            mode = dist.mode().detach().to(device="cpu")
            if not callable(delta_getter) or not callable(prob_getter):
                continue
            delta = delta_getter()
            prob = prob_getter()
            if delta is None or prob is None:
                continue
            event_action_index = getattr(getattr(dist, "layout", None), "event_action_index", None)
            mode_fire = (
                mode[:, int(event_action_index)].reshape(-1) > 0.5
                if event_action_index is not None
                else th.zeros((int(mode.shape[0]),), dtype=th.bool)
            )
            chunks.append(
                {
                    "delta": delta.detach().to(device="cpu").reshape(-1),
                    "prob": prob.detach().to(device="cpu").reshape(-1),
                    "mode_fire": mode_fire.to(device="cpu").reshape(-1),
                }
            )
    if not chunks:
        return {}
    delta = th.cat([item["delta"] for item in chunks]).float()
    prob = th.cat([item["prob"] for item in chunks]).float()
    mode_fire = th.cat([item["mode_fire"] for item in chunks]).to(dtype=th.bool)
    source = labels.source.detach().cpu().reshape(-1).long()
    target = labels.target.detach().cpu().reshape(-1).float()
    active = labels.active.detach().cpu().reshape(-1).to(dtype=th.bool)
    weight = labels.weight.detach().cpu().reshape(-1).float()
    legal_positive = active & (weight > 0.0) & (target > 0.5) & (
        source == int(FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY)
    )

    def masked(name: str, mask: th.Tensor) -> dict[str, Any]:
        mask = mask.reshape(-1).to(dtype=th.bool)
        if int(mask.sum().item()) <= 0:
            return {
                f"{name}_count": 0,
                f"{name}_event_logit_delta_mean": 0.0,
                f"{name}_event_prob_fire_mean": 0.0,
                f"{name}_mode_fire_frac": 0.0,
            }
        return {
            f"{name}_count": int(mask.sum().item()),
            f"{name}_event_logit_delta_mean": float(delta[mask].mean().item()),
            f"{name}_event_prob_fire_mean": float(prob[mask].mean().item()),
            f"{name}_mode_fire_frac": float(mode_fire[mask].float().mean().item()),
        }

    out = {
        "count": int(delta.numel()),
        "event_logit_delta_mean": float(delta.mean().item()),
        "event_prob_fire_mean": float(prob.mean().item()),
        "mode_fire_frac": float(mode_fire.float().mean().item()),
    }
    out.update(masked("legal_open_quality_positive", legal_positive))
    return out


def _with_training_state(policy, value: bool) -> None:
    set_training_mode = getattr(policy, "set_training_mode", None)
    if callable(set_training_mode):
        set_training_mode(bool(value))


def _clone_model(model):
    return copy.deepcopy(model)


def _apply_repeated_updates(
    model,
    kind: str,
    obs_cpu: dict[str, th.Tensor],
    labels: FirstEventHazardLabels,
    indices: th.Tensor,
    hyper: dict[str, Any],
    *,
    include_projection: bool,
    learning_rate: float,
    max_grad_norm: float,
    steps: int,
    online_batch: OnlineRolloutBatch | None,
    eval_batch_size: int,
) -> dict[str, Any]:
    policy = model.policy
    _set_optimizer_lrs(policy, learning_rate)
    _with_training_state(policy, True)
    before = evaluate_credit_head(policy, obs_cpu, labels, batch_size=eval_batch_size)
    loss_trace: list[dict[str, Any]] = []
    for step in range(1, int(steps) + 1):
        device = th.device(policy.device)
        batch_obs = _slice_obs(obs_cpu, indices, device)
        batch_labels = _labels_to_device(labels, device, indices)
        policy.optimizer.zero_grad(set_to_none=True)
        loss, meta = _loss_for_kind(
            policy,
            kind,
            batch_obs,
            batch_labels,
            hyper,
            include_projection=include_projection,
            online_batch=online_batch,
            indices=indices,
        )
        loss.backward()
        total_norm = float(th.nn.utils.clip_grad_norm_(policy.parameters(), max_norm=float(max_grad_norm)).detach().cpu().item())
        policy.optimizer.step()
        if step == 1 or step == int(steps):
            loss_trace.append(
                {
                    "step": int(step),
                    "loss": float(loss.detach().cpu().item()),
                    "total_grad_norm_before_clip": total_norm,
                    "loss_meta": meta,
                }
            )
    after = evaluate_credit_head(policy, obs_cpu, labels, batch_size=eval_batch_size)
    event_after = _event_policy_stats(policy, obs_cpu, labels, batch_size=eval_batch_size)
    return {
        "kind": str(kind),
        "steps": int(steps),
        "learning_rate": float(learning_rate),
        "max_grad_norm": float(max_grad_norm),
        "before": before,
        "after": after,
        "event_policy_after": event_after,
        "loss_trace": loss_trace,
        "optimizer_lrs": _optimizer_lrs(policy),
    }


def _policy_step(policy, obs: Any, *, deterministic: bool) -> tuple[np.ndarray, float, float]:
    obs_tensor, _vectorized = policy.obs_to_tensor(obs)
    if not isinstance(obs_tensor, dict):
        raise TypeError("event-credit online rollout probe expects dict observations")
    with th.no_grad():
        actions, values, log_prob = policy(obs_tensor, deterministic=bool(deterministic))
    action_np = actions.detach().to(device="cpu").numpy().reshape(-1).astype(np.float32)
    value = float(values.detach().reshape(-1)[0].to(device="cpu").item())
    logp = float(log_prob.detach().reshape(-1)[0].to(device="cpu").item())
    return action_np, value, logp


def _policy_value(policy, obs: Any) -> float:
    obs_tensor, _vectorized = policy.obs_to_tensor(obs)
    if not isinstance(obs_tensor, dict):
        raise TypeError("event-credit online rollout probe expects dict observations")
    with th.no_grad():
        features = policy.extract_features(obs_tensor)
        if policy.share_features_extractor:
            _latent_pi, latent_vf = policy.mlp_extractor(features)
        else:
            _pi_features, vf_features = features
            latent_vf = policy.mlp_extractor.forward_critic(vf_features)
        value = policy.value_net(latent_vf)
    return float(value.detach().reshape(-1)[0].to(device="cpu").item())


def collect_online_rollout_batch(
    *,
    model: Any,
    scenario: str,
    train_config: dict[str, Any],
    episodes: int,
    max_steps: int,
    seed: int,
    stochastic: bool,
) -> OnlineRolloutBatch:
    policy = model.policy
    hyper = _hyper(train_config)
    gamma = _finite_float(hyper.get("gamma", 0.99), 0.99)
    gae_lambda = _finite_float(hyper.get("gae_lambda", 0.95), 0.95)
    env = _build_env(scenario, train_config)
    obs_items: list[dict[str, th.Tensor]] = []
    actions: list[np.ndarray] = []
    values: list[float] = []
    log_probs: list[float] = []
    rewards_by_episode: list[list[float]] = []
    values_by_episode: list[list[float]] = []
    bootstrap_values: list[float] = []
    terminated_flags: list[bool] = []
    engagement_state: list[str] = []
    fire_mask: list[bool] = []
    fire_once_accepted: list[bool] = []
    launch_window_open: list[bool] = []
    episode_id: list[int] = []
    release_steps: list[int] = []
    accepted_steps: list[int] = []
    fire_open_steps = 0
    launch_open_steps = 0

    def start_episode(
        _episode: int,
        _observation: Any,
    ) -> tuple[list[float], list[float]]:
        return [], []

    def prepare_step(
        _episode: int,
        _step: int,
        observation: Any,
        _episode_state: tuple[list[float], list[float]],
    ) -> tuple[np.ndarray, tuple[Any, ...]]:
        obs_tensor_cpu = _obs_to_cpu(policy, observation)
        policy_fire_mask = _policy_fire_mask_from_obs(obs_tensor_cpu, 1)
        policy_launch_window = _policy_launch_window_from_obs(
            obs_tensor_cpu,
            1,
            hyper=hyper,
        )
        action, value, log_prob = _policy_step(
            policy,
            observation,
            deterministic=not bool(stochastic),
        )
        return action, (
            obs_tensor_cpu,
            policy_fire_mask,
            policy_launch_window,
            value,
            log_prob,
        )

    def append_step(
        transition: EpisodeStepTransition,
        episode_state: tuple[list[float], list[float]],
    ) -> None:
        nonlocal fire_open_steps, launch_open_steps

        (
            obs_tensor_cpu,
            policy_fire_mask,
            policy_launch_window,
            value,
            log_prob,
        ) = transition.context
        row = transition.info if isinstance(transition.info, dict) else {}
        mask_open = (
            bool(policy_fire_mask[0])
            if policy_fire_mask is not None and len(policy_fire_mask) >= 1
            else AdaptiveKLPPO._first_event_fire_mask_from_info(row)
        )
        launch_open = (
            bool(policy_launch_window[0])
            if policy_launch_window is not None and len(policy_launch_window) >= 1
            else bool(mask_open)
        )
        accepted = AdaptiveKLPPO._first_event_bool(row.get("fire_once_accepted", False))
        ep_rewards, ep_values = episode_state

        obs_items.append(obs_tensor_cpu)
        actions.append(transition.action)
        values.append(float(value))
        log_probs.append(float(log_prob))
        ep_rewards.append(float(transition.reward))
        ep_values.append(float(value))
        engagement_state.append(
            "AuthorizedReady"
            if mask_open
            else str(row.get("engagement_state", "") or "")
        )
        fire_mask.append(bool(mask_open))
        launch_window_open.append(bool(launch_open))
        fire_once_accepted.append(bool(accepted))
        episode_id.append(int(transition.episode))
        fire_open_steps += int(bool(mask_open))
        launch_open_steps += int(bool(launch_open))
        if accepted:
            accepted_steps.append(int(transition.step))
        if int(row.get("missile_release_delta", row.get("missile_release", 0)) or 0) > 0:
            release_steps.append(int(transition.step))

    def finish_episode(
        episode_end: EpisodeEnd,
        episode_state: tuple[list[float], list[float]],
    ) -> None:
        ep_rewards, ep_values = episode_state
        rewards_by_episode.append(ep_rewards)
        values_by_episode.append(ep_values)
        terminated_flags.append(bool(episode_end.done))
        bootstrap_values.append(
            0.0
            if episode_end.done
            else _policy_value(policy, episode_end.final_observation)
        )

    episode_lengths = collect_episode_steps(
        env,
        episodes=int(episodes),
        max_steps=int(max_steps),
        seed=int(seed),
        prepare_step=prepare_step,
        on_step=append_step,
        on_episode_start=start_episode,
        on_episode_end=finish_episode,
    )

    advantages: list[float] = []
    returns: list[float] = []
    for ep_rewards, ep_values, bootstrap in zip(rewards_by_episode, values_by_episode, bootstrap_values):
        ep_adv = [0.0] * len(ep_rewards)
        last_gae = 0.0
        for idx in reversed(range(len(ep_rewards))):
            next_value = float(bootstrap) if idx == len(ep_rewards) - 1 else float(ep_values[idx + 1])
            delta = float(ep_rewards[idx]) + gamma * next_value - float(ep_values[idx])
            last_gae = delta + gamma * gae_lambda * last_gae
            ep_adv[idx] = float(last_gae)
        advantages.extend(ep_adv)
        returns.extend([float(adv + value) for adv, value in zip(ep_adv, ep_values)])

    labels = build_first_event_hazard_labels(
        engagement_state=engagement_state,
        fire_mask=fire_mask,
        fire_once_accepted=fire_once_accepted,
        episode_id=episode_id,
        launch_window_open=launch_window_open if bool(hyper.get("first_event_launch_window_enabled", False)) else None,
        launch_window_min_window_age_steps=int(hyper.get("first_event_launch_window_min_window_age_steps", 1)),
        launch_window_prewindow_hold_weight=_finite_float(hyper.get("event_credit_prewindow_hold_weight", 0.0), 0.0),
        launch_window_early_accept_weight=_finite_float(hyper.get("event_credit_early_accept_weight", 1.0), 1.0),
        curriculum_weight=_finite_float(hyper.get("event_credit_curriculum_coef", 0.0), 0.0),
        curriculum_min_window_age_steps=int(hyper.get("event_credit_curriculum_min_window_age_steps", 32)),
        censored_survival_weight=_finite_float(hyper.get("event_credit_censored_survival_weight", 0.0), 0.0),
        deadline_weight=_finite_float(hyper.get("event_credit_deadline_weight", 0.0), 0.0),
        deadline_min_window_age_steps=int(hyper.get("event_credit_deadline_min_window_age_steps", 96)),
        shadow_quality_after_early_accept=bool(_finite_float(hyper.get("event_credit_shadow_quality_weight", 0.0), 0.0) > 0.0),
        shadow_quality_positive_weight=_finite_float(hyper.get("event_credit_shadow_quality_weight", 0.0), 0.0),
        legal_open_quality_weight=_finite_float(hyper.get("event_credit_legal_open_quality_weight", 0.0), 0.0),
        legal_open_quality_min_window_age_steps=int(hyper.get("event_credit_legal_open_quality_min_window_age_steps", 1)),
        device="cpu",
    )
    meta = {
        "collector": "online_policy_rollout",
        "stochastic": bool(stochastic),
        "episodes": int(episodes),
        "episode_lengths": episode_lengths,
        "steps": int(sum(episode_lengths)),
        "fire_open_steps": int(fire_open_steps),
        "launch_open_steps": int(launch_open_steps),
        "accepted_count": int(sum(1 for value in fire_once_accepted if value)),
        "accepted_steps": accepted_steps,
        "release_steps": release_steps,
        "reward_mean": float(np.mean([r for ep in rewards_by_episode for r in ep])) if rewards_by_episode else 0.0,
        "advantage_mean": float(np.mean(advantages)) if advantages else 0.0,
        "advantage_std": float(np.std(advantages)) if advantages else 0.0,
        "return_mean": float(np.mean(returns)) if returns else 0.0,
    }
    return OnlineRolloutBatch(
        observations=_concat_obs(obs_items),
        actions=th.as_tensor(np.asarray(actions, dtype=np.float32), dtype=th.float32),
        old_values=th.as_tensor(values, dtype=th.float32).reshape(-1),
        old_log_prob=th.as_tensor(log_probs, dtype=th.float32).reshape(-1),
        advantages=th.as_tensor(advantages, dtype=th.float32).reshape(-1),
        returns=th.as_tensor(returns, dtype=th.float32).reshape(-1),
        labels=labels,
        meta=meta,
    )


def _strip_vectors(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for entry in entries:
        clone = {key: value for key, value in entry.items() if key != "_vectors"}
        out.append(clone)
    return out


def _add_cosines(entries: list[dict[str, Any]]) -> dict[str, Any]:
    by_kind = {str(entry["kind"]): entry for entry in entries}
    out: dict[str, Any] = {}
    baseline = by_kind.get("value")
    if baseline is None:
        return out
    for other_name in ("delta", "combined", "ppo", "ppo_plus_a7"):
        other = by_kind.get(other_name)
        if other is None:
            continue
        for group_name in ("credit_head", "event_head", "actor_mlp", "shared_mlp", "features", "all"):
            out[f"{other_name}_vs_value/{group_name}"] = _cosine(
                baseline["_vectors"].get(group_name, th.zeros((0,), dtype=th.float64)),
                other["_vectors"].get(group_name, th.zeros((0,), dtype=th.float64)),
            )
    return out


def run_probe(args: argparse.Namespace) -> dict[str, Any]:
    scenario = os.path.abspath(args.scenario)
    train_config_path = os.path.abspath(args.train_config)
    model_path = os.path.abspath(args.model)
    train_config = load_json_config(train_config_path)
    hyper = _hyper(train_config)
    learning_rate = _finite_float(hyper.get("learning_rate", 3.0e-5), 3.0e-5)
    max_grad_norm = _finite_float(hyper.get("max_grad_norm", 0.5), 0.5)
    model = load_sb3_policy(model_path, algo=str(args.algo), device=str(args.device))
    _set_optimizer_lrs(model.policy, learning_rate)
    fixed_obs, fixed_labels, fixed_collection = collect_fixed_batch(
        model=model,
        scenario=scenario,
        train_config=train_config,
        episodes=int(args.episodes),
        max_steps=int(args.max_steps),
        seed=int(args.seed),
        collector_action=str(args.collector_action),
        stochastic=bool(args.stochastic),
    )
    fixed_count = int(next(iter(fixed_obs.values())).shape[0])
    indices = _select_indices(fixed_labels, fixed_count, int(args.batch_size), int(args.seed) + 17)
    device = th.device(model.policy.device)
    fixed_batch_obs = _slice_obs(fixed_obs, indices, device)
    fixed_batch_labels = _labels_to_device(fixed_labels, device, indices)

    online_batch: OnlineRolloutBatch | None = None
    online_indices = indices
    online_batch_obs = fixed_batch_obs
    online_batch_labels = fixed_batch_labels
    if bool(args.include_ppo):
        online_model = load_sb3_policy(model_path, algo=str(args.algo), device=str(args.device))
        _set_optimizer_lrs(online_model.policy, learning_rate)
        online_batch = collect_online_rollout_batch(
            model=online_model,
            scenario=scenario,
            train_config=train_config,
            episodes=int(args.online_episodes),
            max_steps=int(args.online_max_steps),
            seed=int(args.seed) + 1000,
            stochastic=bool(args.online_stochastic),
        )
        del online_model
        online_count = int(next(iter(online_batch.observations.values())).shape[0])
        online_indices = _select_indices(online_batch.labels, online_count, int(args.batch_size), int(args.seed) + 29)
        online_batch_obs = _slice_obs(online_batch.observations, online_indices, device)
        online_batch_labels = _labels_to_device(online_batch.labels, device, online_indices)

    _with_training_state(model.policy, True)
    fixed_kinds = ["value", "delta", "combined"]
    fixed_gradient_entries = [
        _gradient_stats_for_loss(
            model.policy,
            kind,
            fixed_batch_obs,
            fixed_batch_labels,
            hyper,
            include_projection=bool(args.include_projection),
            max_grad_norm=max_grad_norm,
            online_batch=None,
            indices=indices,
        )
        for kind in fixed_kinds
    ]
    fixed_gradient_cosines = _add_cosines(fixed_gradient_entries)
    online_gradient_entries: list[dict[str, Any]] = []
    online_gradient_cosines: dict[str, Any] = {}
    if online_batch is not None:
        online_kinds = ["value", "delta", "combined", "ppo", "ppo_plus_a7"]
        online_gradient_entries = [
            _gradient_stats_for_loss(
                model.policy,
                kind,
                online_batch_obs,
                online_batch_labels,
                hyper,
                include_projection=bool(args.include_projection),
                max_grad_norm=max_grad_norm,
                online_batch=online_batch,
                indices=online_indices,
            )
            for kind in online_kinds
        ]
        online_gradient_cosines = _add_cosines(online_gradient_entries)
    initial_credit_stats = evaluate_credit_head(model.policy, fixed_obs, fixed_labels, batch_size=int(args.eval_batch_size))
    initial_event_stats = _event_policy_stats(model.policy, fixed_obs, fixed_labels, batch_size=int(args.eval_batch_size))

    fixed_update_results: list[dict[str, Any]] = []
    online_update_results: list[dict[str, Any]] = []
    for kind in [value.strip() for value in str(args.update_kinds).split(",") if value.strip()]:
        if kind.startswith("ppo") and online_batch is None:
            continue
        update_model = load_sb3_policy(model_path, algo=str(args.algo), device=str(args.device))
        _set_optimizer_lrs(update_model.policy, learning_rate)
        if kind.startswith("ppo"):
            online_update_results.append(
                _apply_repeated_updates(
                    update_model,
                    kind,
                    online_batch.observations if online_batch is not None else fixed_obs,
                    online_batch.labels if online_batch is not None else fixed_labels,
                    online_indices,
                    hyper,
                    include_projection=bool(args.include_projection),
                    learning_rate=learning_rate,
                    max_grad_norm=max_grad_norm,
                    steps=int(args.update_steps),
                    online_batch=online_batch,
                    eval_batch_size=int(args.eval_batch_size),
                )
            )
        else:
            fixed_update_results.append(
                _apply_repeated_updates(
                    update_model,
                    kind,
                    fixed_obs,
                    fixed_labels,
                    indices,
                    hyper,
                    include_projection=bool(args.include_projection),
                    learning_rate=learning_rate,
                    max_grad_norm=max_grad_norm,
                    steps=int(args.update_steps),
                    online_batch=None,
                    eval_batch_size=int(args.eval_batch_size),
                )
            )
        del update_model

    payload = {
        "scenario": scenario,
        "train_config": train_config_path,
        "model": model_path,
        "algo": str(args.algo),
        "device": str(args.device),
        "seed": int(args.seed),
        "batch_size": int(args.batch_size),
        "selected_batch_count": int(indices.numel()),
        "include_projection": bool(args.include_projection),
        "learning_rate": float(learning_rate),
        "max_grad_norm": float(max_grad_norm),
        "optimizer_lrs": _optimizer_lrs(model.policy),
        "fixed_collection": fixed_collection,
        "fixed_label_summary": evaluate_label_summary(fixed_labels),
        "fixed_initial_credit": initial_credit_stats,
        "fixed_initial_event_policy": initial_event_stats,
        "online_collection": online_batch.meta if online_batch is not None else None,
        "online_label_summary": evaluate_label_summary(online_batch.labels) if online_batch is not None else None,
        "fixed_gradient_stats": _strip_vectors(fixed_gradient_entries),
        "fixed_gradient_cosines": fixed_gradient_cosines,
        "online_gradient_stats": _strip_vectors(online_gradient_entries),
        "online_gradient_cosines": online_gradient_cosines,
        "fixed_update_results": fixed_update_results,
        "online_update_results": online_update_results,
    }
    if args.json_out:
        out_path = os.path.abspath(args.json_out)
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(_to_serializable(payload), f, indent=2, ensure_ascii=True)
            f.write("\n")
    return payload


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Event-credit online update-path isolation probe.")
    parser.add_argument("--scenario", default=DEFAULT_SCENARIO)
    parser.add_argument("--train_config", default=DEFAULT_TRAIN_CONFIG)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--algo", default="auto")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--episodes", type=int, default=4)
    parser.add_argument("--max_steps", type=int, default=640)
    parser.add_argument("--seed", type=int, default=20260604)
    parser.add_argument("--collector_action", choices=["model", "hold"], default="model")
    parser.add_argument("--stochastic", action="store_true")
    parser.add_argument("--batch_size", type=int, default=512)
    parser.add_argument("--eval_batch_size", type=int, default=512)
    parser.add_argument("--include_projection", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--include_ppo", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--online_episodes", type=int, default=4)
    parser.add_argument("--online_max_steps", type=int, default=640)
    parser.add_argument("--online_stochastic", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--update_kinds", default="value,combined,ppo_plus_a7")
    parser.add_argument("--update_steps", type=int, default=8)
    parser.add_argument("--json_out", default="")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    payload = run_probe(args)
    print(json.dumps(_to_serializable(payload), indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
