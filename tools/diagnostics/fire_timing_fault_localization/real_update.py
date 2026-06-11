#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np
import torch as th

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from python.testing.runtime import ensure_repo_imports, resolve_repo_path

ensure_repo_imports()

from python.rl.policy_algo.m3s1_grouped_stopping import (  # noqa: E402
    M3S1_CENSOR_EARLY_EVENT_PREFIX,
    M3S1_CENSOR_NONE,
    M3S1_CENSOR_TIMEOUT,
    M3S1GroupedStoppingEvidence,
    compute_m3s1_grouped_stopping_loss,
)
from tools.diagnostics.event_credit_head.offline_fit import (  # noqa: E402
    _concat_obs,
    _finite_float,
    _hold_action,
    _hyper,
    _obs_to_cpu,
    _policy_fire_mask_from_obs,
    _policy_launch_window_from_obs,
    _slice_obs,
    _to_serializable,
)
from tools.diagnostics.air_combat_weapon_employment_process_probe import _base_env, _build_env  # noqa: E402
from tools.eval.sb3_eval_base import load_json_config, load_sb3_policy  # noqa: E402


DEFAULT_SCENARIO = resolve_repo_path(
    "scenarios",
    "air_combat",
    "1v1",
    "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json",
)
DEFAULT_TRAIN_CONFIG = resolve_repo_path(
    "examples",
    "config",
    "training",
    "active",
    "air_combat",
    "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json",
)
DEFAULT_MODEL = resolve_repo_path(
    "experiments_tmp",
    "m3s2_support_preserve_8k_20260606_r2",
    "final_model.zip",
)


PARAM_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("event_head", ("hybrid_event_head.",)),
    ("m3_stopping_head", ("m3_stopping_norm.", "m3_stopping_head.")),
    ("action_net", ("action_net.",)),
    ("actor_mlp", ("mlp_extractor.policy_net.",)),
    ("shared_mlp", ("mlp_extractor.shared_net.",)),
    ("features", ("features_extractor.",)),
    ("critic_mlp", ("mlp_extractor.value_net.",)),
    ("value_net", ("value_net.",)),
    ("log_std", ("log_std",)),
)


@dataclass(frozen=True)
class RealM3S2Group:
    group_id: str
    episode_id: int
    row_indices: tuple[int, ...]
    step_indices: tuple[int, ...]
    legal_mask: tuple[bool, ...]
    quality_mask: tuple[bool, ...]
    accepted_event: tuple[bool, ...]
    censoring_kind: str
    censor_step: int | None
    support_horizon: int


def _model_action(model: Any, obs: Any, *, deterministic: bool) -> np.ndarray:
    action, _state = model.predict(obs, deterministic=bool(deterministic))
    return np.asarray(action, dtype=np.float32).reshape(-1)


def _collector_action_for_m3s2(
    model: Any,
    env: Any,
    obs: Any,
    *,
    collector_action: str,
    stochastic: bool,
) -> np.ndarray:
    mode = str(collector_action or "").strip().lower()
    if mode == "hold":
        return _hold_action(env)
    if mode in {"model", "model_event_hold"}:
        action = _model_action(model, obs, deterministic=not bool(stochastic))
        if mode == "model_event_hold" and int(action.size) > 9:
            action = action.copy()
            action[9] = 0.0
        return action
    raise ValueError(f"unknown collector_action: {collector_action}")


def _param_group_name(name: str) -> str:
    for group_name, prefixes in PARAM_GROUPS:
        if any(str(name).startswith(prefix) for prefix in prefixes):
            return group_name
    return "other"


def _set_optimizer_lrs(policy: Any, learning_rate: float) -> None:
    apply_lr = getattr(policy, "apply_optimizer_learning_rate", None)
    if callable(apply_lr):
        apply_lr(float(learning_rate), lr_mult=1.0)
        return
    optimizer = getattr(policy, "optimizer", None)
    if optimizer is None:
        return
    for group in optimizer.param_groups:
        group["lr"] = float(learning_rate)


def _selected_params(model: Any, scope: str) -> list[tuple[str, th.nn.Parameter]]:
    scope = str(scope)
    selected: list[tuple[str, th.nn.Parameter]] = []
    current_params = set()
    getter = getattr(model, "_m3s2_event_window_parameters", None)
    if not callable(getter):
        getter = getattr(model, "_a7_event_policy_margin_parameters", None)
    if callable(getter):
        current_params = {id(param) for param in getter()}
    for name, param in model.policy.named_parameters():
        if not bool(param.requires_grad):
            continue
        group = _param_group_name(str(name))
        include = False
        if scope == "current":
            include = id(param) in current_params
        elif scope == "event_head":
            include = group == "event_head"
        elif scope == "m3_stopping_head":
            include = group == "m3_stopping_head"
        elif scope == "current_plus_features":
            include = id(param) in current_params or group == "features"
        elif scope == "actor_all":
            include = group in {"event_head", "action_net", "actor_mlp", "shared_mlp", "features"}
        else:
            raise ValueError(f"unknown update scope: {scope}")
        if include:
            selected.append((str(name), param))
    if not selected:
        raise RuntimeError(f"scope {scope!r} selected no trainable parameters")
    return selected


def _build_groups_from_rows(
    *,
    fire_mask: Sequence[bool],
    fire_once_accepted: Sequence[bool],
    episode_id: Sequence[int],
    launch_window_open: Sequence[bool],
    launch_min_age: int,
) -> list[RealM3S2Group]:
    count = len(fire_mask)
    if not (len(fire_once_accepted) == len(episode_id) == len(launch_window_open) == count):
        raise ValueError("M3-S2 real probe rows must have matching lengths")
    ordered_episodes: list[int] = []
    seen: set[int] = set()
    for value in episode_id:
        episode = int(value)
        if episode not in seen:
            ordered_episodes.append(episode)
            seen.add(episode)

    groups: list[RealM3S2Group] = []
    for group_counter, episode in enumerate(ordered_episodes):
        indices = [idx for idx, value in enumerate(episode_id) if int(value) == int(episode)]
        if not indices:
            continue
        row_indices: list[int] = []
        legal: list[bool] = []
        quality: list[bool] = []
        accepted: list[bool] = []
        legal_window_age = 0
        for flat_idx in indices:
            is_legal = bool(fire_mask[int(flat_idx)])
            legal_window_age = legal_window_age + 1 if is_legal else 0
            row_indices.append(int(flat_idx))
            legal.append(is_legal)
            quality.append(
                bool(is_legal)
                and bool(launch_window_open[int(flat_idx)])
                and int(legal_window_age) >= max(1, int(launch_min_age))
            )
            accepted.append(bool(fire_once_accepted[int(flat_idx)]))
            if accepted[-1]:
                break
        accepted_positions = [idx for idx, value in enumerate(accepted) if bool(value)]
        if accepted_positions and not bool(quality[int(accepted_positions[0])]):
            censoring_kind = M3S1_CENSOR_EARLY_EVENT_PREFIX
            censor_step = int(row_indices[int(accepted_positions[0])])
        elif accepted_positions:
            censoring_kind = M3S1_CENSOR_NONE
            censor_step = int(row_indices[int(accepted_positions[0])])
        else:
            censoring_kind = M3S1_CENSOR_TIMEOUT
            censor_step = None
        groups.append(
            RealM3S2Group(
                group_id=f"{episode}:{group_counter}",
                episode_id=int(episode),
                row_indices=tuple(row_indices),
                step_indices=tuple(row_indices),
                legal_mask=tuple(legal),
                quality_mask=tuple(quality),
                accepted_event=tuple(accepted),
                censoring_kind=censoring_kind,
                censor_step=censor_step,
                support_horizon=max(row_indices) if row_indices else -1,
            )
        )
    return groups


def collect_real_m3s2_batch(
    *,
    model: Any,
    scenario: str,
    train_config: dict[str, Any],
    episodes: int,
    max_steps: int,
    seed: int,
    collector_action: str,
    stochastic: bool,
) -> tuple[dict[str, th.Tensor], list[RealM3S2Group], dict[str, Any]]:
    hyper = _hyper(train_config)
    env = _build_env(scenario, train_config)
    obs_items: list[dict[str, th.Tensor]] = []
    fire_mask: list[bool] = []
    launch_window_open: list[bool] = []
    fire_once_accepted: list[bool] = []
    episode_ids: list[int] = []
    episode_lengths: list[int] = []
    try:
        for ep in range(int(episodes)):
            obs, _info = env.reset(seed=int(seed) + int(ep))
            base_env = _base_env(env)
            ep_max_steps = int(max_steps) if int(max_steps) > 0 else int(getattr(base_env, "max_steps", 0) or 1200)
            steps_this_ep = 0
            for _step in range(1, ep_max_steps + 1):
                obs_tensor = _obs_to_cpu(model.policy, obs)
                policy_fire_mask = _policy_fire_mask_from_obs(obs_tensor, 1)
                policy_launch_window = _policy_launch_window_from_obs(obs_tensor, 1, hyper=hyper)
                action = _collector_action_for_m3s2(
                    model,
                    env,
                    obs,
                    collector_action=str(collector_action),
                    stochastic=bool(stochastic),
                )
                new_obs, _reward, terminated, truncated, info = env.step(action)
                row = info if isinstance(info, dict) else {}
                mask_open = (
                    bool(policy_fire_mask[0])
                    if policy_fire_mask is not None and len(policy_fire_mask) >= 1
                    else bool(row.get("fire_mask", row.get("authorization_to_fire", False)))
                )
                launch_open = (
                    bool(policy_launch_window[0])
                    if policy_launch_window is not None and len(policy_launch_window) >= 1
                    else bool(mask_open)
                )
                accepted = bool(row.get("fire_once_accepted", False))
                obs_items.append(obs_tensor)
                fire_mask.append(bool(mask_open))
                launch_window_open.append(bool(launch_open))
                fire_once_accepted.append(bool(accepted))
                episode_ids.append(int(ep))
                steps_this_ep += 1
                obs = new_obs
                if bool(terminated or truncated):
                    break
            episode_lengths.append(int(steps_this_ep))
    finally:
        try:
            env.close()
        except Exception:
            pass

    groups = _build_groups_from_rows(
        fire_mask=fire_mask,
        fire_once_accepted=fire_once_accepted,
        episode_id=episode_ids,
        launch_window_open=launch_window_open,
        launch_min_age=int(hyper.get("a6_first_event_launch_window_min_window_age_steps", 1)),
    )
    quality_rows = sum(sum(1 for value in group.quality_mask if bool(value)) for group in groups)
    legal_rows = sum(sum(1 for value in group.legal_mask if bool(value)) for group in groups)
    meta = {
        "collector_action": str(collector_action),
        "stochastic": bool(stochastic),
        "episodes": int(episodes),
        "episode_lengths": episode_lengths,
        "steps": int(sum(episode_lengths)),
        "group_count": int(len(groups)),
        "legal_rows": int(legal_rows),
        "quality_rows": int(quality_rows),
        "accepted_count": int(sum(1 for value in fire_once_accepted if bool(value))),
        "launch_min_age": int(hyper.get("a6_first_event_launch_window_min_window_age_steps", 1)),
    }
    return _concat_obs(obs_items), groups, meta


def _group_obs(obs: dict[str, th.Tensor], group: RealM3S2Group, device: th.device) -> dict[str, th.Tensor]:
    indices = th.as_tensor(group.row_indices, dtype=th.long)
    return _slice_obs(obs, indices, device)


def _m3s2_loss_from_real_groups(policy: Any, obs: dict[str, th.Tensor], groups: Sequence[RealM3S2Group], hyper: dict[str, Any]):
    device = th.device(policy.device)
    evidence: list[M3S1GroupedStoppingEvidence] = []
    for group in groups:
        dist = policy.get_distribution(_group_obs(obs, group, device))
        getter = getattr(dist, "fire_event_logit_delta", None)
        if not callable(getter):
            raise RuntimeError("policy distribution does not expose fire_event_logit_delta")
        logits = getter()
        if logits is None:
            raise RuntimeError("fire_event_logit_delta returned None")
        evidence.append(
            M3S1GroupedStoppingEvidence(
                group_id=group.group_id,
                episode_id=group.episode_id,
                route_source="real_fixed_probe",
                row_indices=group.row_indices,
                step_indices=group.step_indices,
                env_indices=[0] * len(group.row_indices),
                legal_mask=group.legal_mask,
                quality_mask=group.quality_mask,
                stopping_logits=logits.reshape(-1),
                accepted_event=group.accepted_event,
                censoring_kind=group.censoring_kind,
                censor_step=group.censor_step,
                support_horizon=group.support_horizon,
            )
        )
    return compute_m3s1_grouped_stopping_loss(
        evidence,
        coef=float(hyper.get("m3s2_event_window_coef", 1.0)),
        early_mass_coef=float(hyper.get("m3s2_event_window_early_mass_coef", 1.0)),
        early_mass_budget=float(hyper.get("m3s2_event_window_early_mass_budget", 0.05)),
        early_survival_coef=float(hyper.get("m3s2_event_window_early_survival_coef", 0.0)),
        no_event_coef=float(hyper.get("m3s2_event_window_no_event_coef", 1.0)),
        window_delay_coef=float(hyper.get("m3s2_event_window_delay_coef", 0.0)),
        window_deadline_coef=float(hyper.get("m3s2_event_window_deadline_coef", 0.0)),
        window_deadline_steps=int(hyper.get("m3s2_event_window_deadline_steps", 0)),
        window_quality_boundary_coef=float(hyper.get("m3s2_event_window_quality_boundary_coef", 0.0)),
        window_quality_boundary_logit=float(hyper.get("m3s2_event_window_quality_boundary_logit", 0.0)),
        window_contrastive_margin_coef=float(hyper.get("m3s2_event_window_contrastive_margin_coef", 0.0)),
        window_contrastive_margin=float(hyper.get("m3s2_event_window_contrastive_margin", 0.0)),
        window_balanced_bce_coef=float(hyper.get("m3s2_event_window_balanced_bce_coef", 0.0)),
        window_prewindow_hazard_scale_coef=float(
            hyper.get("m3s2_event_window_prewindow_hazard_scale_coef", 0.0)
        ),
        window_prewindow_hazard_target=float(hyper.get("m3s2_event_window_prewindow_hazard_target", 0.0)),
        window_quality_hazard_target_coef=float(
            hyper.get("m3s2_event_window_quality_hazard_target_coef", 0.0)
        ),
        window_quality_hazard_target=float(hyper.get("m3s2_event_window_quality_hazard_target", 0.5)),
        window_prewindow_logit_ceiling_coef=float(
            hyper.get("m3s2_event_window_prewindow_logit_ceiling_coef", 0.0)
        ),
        window_prewindow_logit_ceiling=float(hyper.get("m3s2_event_window_prewindow_logit_ceiling", -2.0)),
        window_quality_logit_floor_coef=float(
            hyper.get("m3s2_event_window_quality_logit_floor_coef", 0.0)
        ),
        window_quality_logit_floor=float(hyper.get("m3s2_event_window_quality_logit_floor", 2.0)),
        boundary_threshold=0.0,
    )


def _cumulative_risk(probs: th.Tensor) -> float:
    if int(probs.numel()) <= 0:
        return 0.0
    safe = probs.detach().cpu().to(dtype=th.float64).clamp(min=0.0, max=1.0 - 1.0e-12)
    return float(1.0 - th.exp(th.log1p(-safe).sum()).item())


def _masked_stats(prefix: str, logits: th.Tensor, mask: th.Tensor) -> dict[str, Any]:
    mask = mask.detach().cpu().reshape(-1).to(dtype=th.bool)
    logits = logits.detach().cpu().reshape(-1).float()
    if int(mask.sum().item()) <= 0:
        return {
            f"{prefix}_count": 0,
            f"{prefix}_logit_mean": 0.0,
            f"{prefix}_logit_max": 0.0,
            f"{prefix}_prob_mean": 0.0,
            f"{prefix}_prob_max": 0.0,
            f"{prefix}_boundary_count": 0,
            f"{prefix}_cumulative_risk": 0.0,
        }
    selected = logits[mask]
    probs = th.sigmoid(selected)
    return {
        f"{prefix}_count": int(mask.sum().item()),
        f"{prefix}_logit_mean": float(selected.mean().item()),
        f"{prefix}_logit_max": float(selected.max().item()),
        f"{prefix}_prob_mean": float(probs.mean().item()),
        f"{prefix}_prob_max": float(probs.max().item()),
        f"{prefix}_boundary_count": int((selected >= 0.0).sum().item()),
        f"{prefix}_cumulative_risk": _cumulative_risk(probs),
    }


def summarize_real_logits(policy: Any, obs: dict[str, th.Tensor], groups: Sequence[RealM3S2Group], hyper: dict[str, Any]) -> dict[str, Any]:
    policy.set_training_mode(False)
    device = th.device(policy.device)
    logits_chunks: list[th.Tensor] = []
    legal_chunks: list[th.Tensor] = []
    quality_chunks: list[th.Tensor] = []
    with th.no_grad():
        for group in groups:
            dist = policy.get_distribution(_group_obs(obs, group, device))
            getter = getattr(dist, "fire_event_logit_delta", None)
            if not callable(getter):
                continue
            logits = getter()
            if logits is None:
                continue
            logits_chunks.append(logits.detach().cpu().reshape(-1))
            legal_chunks.append(th.as_tensor(group.legal_mask, dtype=th.bool))
            quality_chunks.append(th.as_tensor(group.quality_mask, dtype=th.bool))
    if not logits_chunks:
        return {}
    logits_all = th.cat(logits_chunks)
    legal_all = th.cat(legal_chunks)
    quality_all = th.cat(quality_chunks)
    prewindow = legal_all & ~quality_all
    out = {
        "loss": float(_m3s2_loss_from_real_groups(policy, obs, groups, hyper).loss.detach().cpu().item()),
    }
    out.update(_masked_stats("all", logits_all, th.ones_like(legal_all, dtype=th.bool)))
    out.update(_masked_stats("legal", logits_all, legal_all))
    out.update(_masked_stats("prewindow", logits_all, prewindow))
    out.update(_masked_stats("quality", logits_all, quality_all))
    return out


def _param_delta(before: dict[str, th.Tensor], policy: Any) -> dict[str, Any]:
    groups: dict[str, list[float]] = {}
    total_sq = 0.0
    for name, param in policy.named_parameters():
        old = before.get(str(name))
        if old is None:
            continue
        delta = (param.detach().cpu() - old).reshape(-1).to(dtype=th.float64)
        norm = float(delta.norm().item()) if int(delta.numel()) > 0 else 0.0
        total_sq += norm * norm
        groups.setdefault(_param_group_name(str(name)), []).append(norm)
    return {
        "total_norm": float(math.sqrt(total_sq)),
        "by_group": {key: float(math.sqrt(sum(value * value for value in values))) for key, values in groups.items()},
    }


def run_update_scope(
    *,
    model_path: str,
    algo: str,
    device: str,
    obs: dict[str, th.Tensor],
    groups: Sequence[RealM3S2Group],
    hyper: dict[str, Any],
    scope: str,
    update_steps: int,
    learning_rate: float,
    max_grad_norm: float,
    reset_optimizer_state: bool,
) -> dict[str, Any]:
    model = load_sb3_policy(model_path, algo=algo, device=device)
    _set_optimizer_lrs(model.policy, learning_rate)
    if bool(reset_optimizer_state):
        model.policy.optimizer.state.clear()
    selected = _selected_params(model, scope)
    selected_ids = {id(param) for _name, param in selected}
    before_params = {str(name): param.detach().cpu().clone() for name, param in model.policy.named_parameters()}
    before = summarize_real_logits(model.policy, obs, groups, hyper)
    model.policy.set_training_mode(True)
    loss_trace: list[dict[str, Any]] = []
    for step in range(1, int(update_steps) + 1):
        model.policy.optimizer.zero_grad(set_to_none=True)
        loss_obj = _m3s2_loss_from_real_groups(model.policy, obs, groups, hyper)
        loss_obj.loss.backward()
        for param in model.policy.parameters():
            if id(param) not in selected_ids:
                param.grad = None
        grad_norm_tensor = th.nn.utils.clip_grad_norm_(
            [param for _name, param in selected],
            float(max_grad_norm),
        )
        model.policy.optimizer.step()
        model.policy.optimizer.zero_grad(set_to_none=True)
        if step == 1 or step == int(update_steps):
            loss_trace.append(
                {
                    "step": int(step),
                    "loss": float(loss_obj.loss.detach().cpu().item()),
                    "grad_norm_before_clip": float(grad_norm_tensor.detach().cpu().item()),
                    "active_group_count": int(loss_obj.stats.active_group_count),
                    "window_group_count": int(loss_obj.stats.window_group_count),
                    "boundary_cross_count": int(loss_obj.stats.boundary_cross_count),
                    "quality_boundary_logit": float(loss_obj.stats.mean_quality_boundary_logit),
                    "quality_boundary_margin_loss": float(loss_obj.stats.mean_quality_boundary_margin_loss),
                    "quality_prewindow_logit_margin": float(
                        loss_obj.stats.mean_quality_prewindow_logit_margin
                    ),
                    "contrastive_margin_loss": float(loss_obj.stats.mean_quality_prewindow_margin_loss),
                    "balanced_bce_loss": float(loss_obj.stats.mean_window_balanced_bce_loss),
                    "prewindow_hazard_mean": float(loss_obj.stats.mean_prewindow_hazard_mean),
                    "prewindow_hazard_max": float(loss_obj.stats.mean_prewindow_hazard_max),
                    "prewindow_hazard_target": float(loss_obj.stats.mean_prewindow_hazard_target),
                    "prewindow_hazard_scale_loss": float(loss_obj.stats.mean_prewindow_hazard_scale_loss),
                    "quality_hazard_target": float(loss_obj.stats.mean_quality_hazard_target),
                    "quality_hazard_target_loss": float(loss_obj.stats.mean_quality_hazard_target_loss),
                    "prewindow_logit_ceiling": float(loss_obj.stats.mean_prewindow_logit_ceiling),
                    "prewindow_logit_ceiling_loss": float(loss_obj.stats.mean_prewindow_logit_ceiling_loss),
                    "quality_logit_floor": float(loss_obj.stats.mean_quality_logit_floor),
                    "quality_logit_floor_loss": float(loss_obj.stats.mean_quality_logit_floor_loss),
                }
            )
    after = summarize_real_logits(model.policy, obs, groups, hyper)
    delta = _param_delta(before_params, model.policy)
    return {
        "scope": str(scope),
        "update_steps": int(update_steps),
        "learning_rate": float(learning_rate),
        "max_grad_norm": float(max_grad_norm),
        "reset_optimizer_state": bool(reset_optimizer_state),
        "selected_param_count": int(sum(int(param.numel()) for _name, param in selected)),
        "selected_param_groups": sorted({_param_group_name(name) for name, _param in selected}),
        "before": before,
        "after": after,
        "delta": {
            key: (
                float(after.get(key, 0.0)) - float(before.get(key, 0.0))
                if isinstance(after.get(key, 0.0), (int, float)) and isinstance(before.get(key, 0.0), (int, float))
                else None
            )
            for key in sorted(set(before) | set(after))
        },
        "param_delta": delta,
        "loss_trace": loss_trace,
    }


def run_probe(args: argparse.Namespace) -> dict[str, Any]:
    scenario = os.path.abspath(str(args.scenario))
    train_config_path = os.path.abspath(str(args.train_config))
    model_path = os.path.abspath(str(args.model))
    train_config = load_json_config(train_config_path)
    hyper = _hyper(train_config)
    _apply_loss_overrides(hyper, args)
    collector_model = load_sb3_policy(model_path, algo=str(args.algo), device=str(args.device))
    obs, groups, collection = collect_real_m3s2_batch(
        model=collector_model,
        scenario=scenario,
        train_config=train_config,
        episodes=int(args.episodes),
        max_steps=int(args.max_steps),
        seed=int(args.seed),
        collector_action=str(args.collector_action),
        stochastic=bool(args.stochastic),
    )
    del collector_model
    base_model = load_sb3_policy(model_path, algo=str(args.algo), device=str(args.device))
    initial = summarize_real_logits(base_model.policy, obs, groups, hyper)
    del base_model

    learning_rate = float(args.learning_rate) if args.learning_rate is not None else _finite_float(hyper.get("learning_rate", 3.0e-5), 3.0e-5)
    max_grad_norm = float(args.max_grad_norm) if args.max_grad_norm is not None else _finite_float(hyper.get("m3s2_event_window_max_grad_norm", 2.0), 2.0)
    scopes = [scope.strip() for scope in str(args.scopes).split(",") if scope.strip()]
    updates = [
        run_update_scope(
            model_path=model_path,
            algo=str(args.algo),
            device=str(args.device),
            obs=obs,
            groups=groups,
            hyper=hyper,
            scope=scope,
            update_steps=int(args.update_steps),
            learning_rate=learning_rate,
            max_grad_norm=max_grad_norm,
            reset_optimizer_state=bool(args.reset_optimizer_state),
        )
        for scope in scopes
    ]
    payload = {
        "scenario": scenario,
        "train_config": train_config_path,
        "model": model_path,
        "algo": str(args.algo),
        "device": str(args.device),
        "seed": int(args.seed),
        "collection": collection,
        "initial": initial,
        "updates": updates,
        "verdict": {
            "has_quality_rows": bool(int(collection.get("quality_rows", 0)) > 0),
            "initial_quality_boundary": bool(int(initial.get("quality_boundary_count", 0)) > 0),
            "any_update_quality_boundary": any(
                int(update.get("after", {}).get("quality_boundary_count", 0)) > 0 for update in updates
            ),
            "any_update_raises_quality_logit": any(
                float(update.get("delta", {}).get("quality_logit_max", 0.0) or 0.0) > 0.0 for update in updates
            ),
        },
    }
    return _to_serializable(payload)


def _apply_loss_overrides(hyper: dict[str, Any], args: argparse.Namespace) -> None:
    overrides = {
        "m3s2_event_window_coef": getattr(args, "event_window_coef", None),
        "m3s2_event_window_early_mass_coef": getattr(args, "early_mass_coef", None),
        "m3s2_event_window_early_mass_budget": getattr(args, "early_mass_budget", None),
        "m3s2_event_window_early_survival_coef": getattr(args, "early_survival_coef", None),
        "m3s2_event_window_no_event_coef": getattr(args, "no_event_coef", None),
        "m3s2_event_window_delay_coef": getattr(args, "delay_coef", None),
        "m3s2_event_window_deadline_coef": getattr(args, "deadline_coef", None),
        "m3s2_event_window_deadline_steps": getattr(args, "deadline_steps", None),
        "m3s2_event_window_quality_boundary_coef": getattr(args, "quality_boundary_coef", None),
        "m3s2_event_window_quality_boundary_logit": getattr(args, "quality_boundary_logit", None),
        "m3s2_event_window_contrastive_margin_coef": getattr(args, "contrastive_margin_coef", None),
        "m3s2_event_window_contrastive_margin": getattr(args, "contrastive_margin", None),
        "m3s2_event_window_balanced_bce_coef": getattr(args, "balanced_bce_coef", None),
        "m3s2_event_window_prewindow_hazard_scale_coef": getattr(args, "prewindow_hazard_scale_coef", None),
        "m3s2_event_window_prewindow_hazard_target": getattr(args, "prewindow_hazard_target", None),
        "m3s2_event_window_quality_hazard_target_coef": getattr(args, "quality_hazard_target_coef", None),
        "m3s2_event_window_quality_hazard_target": getattr(args, "quality_hazard_target", None),
        "m3s2_event_window_prewindow_logit_ceiling_coef": getattr(args, "prewindow_logit_ceiling_coef", None),
        "m3s2_event_window_prewindow_logit_ceiling": getattr(args, "prewindow_logit_ceiling", None),
        "m3s2_event_window_quality_logit_floor_coef": getattr(args, "quality_logit_floor_coef", None),
        "m3s2_event_window_quality_logit_floor": getattr(args, "quality_logit_floor", None),
    }
    for key, value in overrides.items():
        if value is not None:
            hyper[key] = value


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", default=DEFAULT_SCENARIO)
    parser.add_argument("--train_config", default=DEFAULT_TRAIN_CONFIG)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--algo", default="auto")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--max-steps", type=int, default=2400)
    parser.add_argument("--seed", type=int, default=20260525)
    parser.add_argument("--collector-action", choices=("hold", "model", "model_event_hold"), default="hold")
    parser.add_argument("--stochastic", action="store_true")
    parser.add_argument("--scopes", default="current,current_plus_features")
    parser.add_argument("--update-steps", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=None)
    parser.add_argument("--max-grad-norm", type=float, default=None)
    parser.add_argument("--reset-optimizer-state", action="store_true")
    parser.add_argument("--event-window-coef", type=float, default=None)
    parser.add_argument("--early-mass-coef", type=float, default=None)
    parser.add_argument("--early-mass-budget", type=float, default=None)
    parser.add_argument("--early-survival-coef", type=float, default=None)
    parser.add_argument("--no-event-coef", type=float, default=None)
    parser.add_argument("--delay-coef", type=float, default=None)
    parser.add_argument("--deadline-coef", type=float, default=None)
    parser.add_argument("--deadline-steps", type=int, default=None)
    parser.add_argument("--quality-boundary-coef", type=float, default=None)
    parser.add_argument("--quality-boundary-logit", type=float, default=None)
    parser.add_argument("--contrastive-margin-coef", type=float, default=None)
    parser.add_argument("--contrastive-margin", type=float, default=None)
    parser.add_argument("--balanced-bce-coef", type=float, default=None)
    parser.add_argument("--prewindow-hazard-scale-coef", type=float, default=None)
    parser.add_argument("--prewindow-hazard-target", type=float, default=None)
    parser.add_argument("--quality-hazard-target-coef", type=float, default=None)
    parser.add_argument("--quality-hazard-target", type=float, default=None)
    parser.add_argument("--prewindow-logit-ceiling-coef", type=float, default=None)
    parser.add_argument("--prewindow-logit-ceiling", type=float, default=None)
    parser.add_argument("--quality-logit-floor-coef", type=float, default=None)
    parser.add_argument("--quality-logit-floor", type=float, default=None)
    parser.add_argument("--json-out", default="")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    payload = run_probe(args)
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.json_out:
        out_path = os.path.abspath(args.json_out)
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.write("\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
