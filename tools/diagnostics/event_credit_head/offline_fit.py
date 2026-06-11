#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import Counter
from typing import Any

import numpy as np
import torch as th

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from python.testing.runtime import ensure_repo_imports, resolve_repo_path

ensure_repo_imports()

from python.rl.policy_algo.first_event_hazard import (
    A6_FIRST_EVENT_SOURCE_ACCEPTED,
    A6_FIRST_EVENT_SOURCE_CENSORED,
    A6_FIRST_EVENT_SOURCE_CURRICULUM,
    A6_FIRST_EVENT_SOURCE_DEADLINE,
    A6_FIRST_EVENT_SOURCE_EARLY_ACCEPTED,
    A6_FIRST_EVENT_SOURCE_INACTIVE,
    A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY,
    A6_FIRST_EVENT_SOURCE_PREWINDOW,
    A6_FIRST_EVENT_SOURCE_SHADOW_QUALITY,
    FirstEventHazardLabels,
    build_first_event_hazard_labels,
    compute_first_event_credit_loss,
)
from python.rl.policy_algo.ppo_adaptive_kl import AdaptiveKLPPO
from tools.diagnostics.air_combat_weapon_employment_process_probe import _base_action, _base_env, _build_env
from tools.eval.sb3_eval_base import load_json_config, load_sb3_policy


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
    "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_state_completed_world_batch_probe_v1.json",
)
DEFAULT_MODEL = resolve_repo_path(
    "experiments_tmp",
    "a7_state_completed_opportunity_32k_20260604_r1",
    "final_model.zip",
)

SOURCE_NAMES = {
    A6_FIRST_EVENT_SOURCE_INACTIVE: "inactive",
    A6_FIRST_EVENT_SOURCE_ACCEPTED: "accepted",
    A6_FIRST_EVENT_SOURCE_CURRICULUM: "curriculum",
    A6_FIRST_EVENT_SOURCE_CENSORED: "censored",
    A6_FIRST_EVENT_SOURCE_DEADLINE: "deadline",
    A6_FIRST_EVENT_SOURCE_PREWINDOW: "prewindow",
    A6_FIRST_EVENT_SOURCE_EARLY_ACCEPTED: "early_accepted",
    A6_FIRST_EVENT_SOURCE_SHADOW_QUALITY: "shadow_quality",
    A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY: "legal_open_quality",
}


def _hyper(train_config: dict[str, Any]) -> dict[str, Any]:
    value = train_config.get("hyperparameters", {})
    return value if isinstance(value, dict) else {}


def _finite_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return float(default)
    return out if math.isfinite(out) else float(default)


def _to_serializable(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, th.Tensor):
        if int(value.numel()) == 1:
            return value.detach().cpu().item()
        return value.detach().cpu().tolist()
    if isinstance(value, dict):
        return {str(k): _to_serializable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_serializable(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _obs_to_cpu(policy, obs: Any) -> dict[str, th.Tensor]:
    obs_tensor, _vectorized = policy.obs_to_tensor(obs)
    if not isinstance(obs_tensor, dict):
        raise TypeError("event-credit offline fit probe expects dict observations")
    return {
        str(key): th.as_tensor(value).detach().to(device="cpu")
        for key, value in obs_tensor.items()
    }


def _concat_obs(items: list[dict[str, th.Tensor]]) -> dict[str, th.Tensor]:
    if not items:
        raise ValueError("no observations collected")
    keys = tuple(items[0].keys())
    out: dict[str, th.Tensor] = {}
    for key in keys:
        out[key] = th.cat([item[key] for item in items], dim=0)
    return out


def _slice_obs(obs: dict[str, th.Tensor], indices: th.Tensor, device: th.device) -> dict[str, th.Tensor]:
    cpu_indices = indices.detach().to(device="cpu", dtype=th.long)
    return {
        key: value.index_select(0, cpu_indices).to(device=device)
        for key, value in obs.items()
    }


def _policy_fire_mask_from_obs(obs_tensor: dict[str, th.Tensor], n_envs: int) -> list[bool] | None:
    return AdaptiveKLPPO._a6_first_event_policy_fire_mask_from_obs(obs_tensor, n_envs)


def _policy_launch_window_from_obs(
    obs_tensor: dict[str, th.Tensor],
    n_envs: int,
    *,
    hyper: dict[str, Any],
) -> list[bool] | None:
    return AdaptiveKLPPO._a6_first_event_policy_launch_window_from_obs(
        obs_tensor,
        n_envs,
        min_range_m=_finite_float(hyper.get("a6_first_event_launch_window_min_range_m", 0.0), 0.0),
        max_range_m=_finite_float(hyper.get("a6_first_event_launch_window_max_range_m", 0.0), 0.0),
        max_track_age_s=_finite_float(
            hyper.get("a6_first_event_launch_window_max_track_age_s", float("inf")),
            float("inf"),
        ),
    )


def _model_action(model: Any, obs: Any, *, deterministic: bool) -> np.ndarray:
    action, _state = model.predict(obs, deterministic=bool(deterministic))
    return np.asarray(action, dtype=np.float32).reshape(-1)


def _hold_action(env) -> np.ndarray:
    base = _base_env(env)
    action_mode = str(getattr(base, "action_mode", "full"))
    action = _base_action(action_mode)
    columns = {
        "air_combat_hybrid_v1": {"radar_active": 6, "tms_up": 7, "master_arm": 8, "fire_weapon": 9},
    }.get(action_mode)
    if columns is not None:
        action[columns["radar_active"]] = 1.0
        action[columns["tms_up"]] = 1.0
        action[columns["master_arm"]] = 1.0
        action[columns["fire_weapon"]] = 0.0
    return action


def collect_fixed_batch(
    *,
    model: Any,
    scenario: str,
    train_config: dict[str, Any],
    episodes: int,
    max_steps: int,
    seed: int,
    collector_action: str,
    stochastic: bool,
) -> tuple[dict[str, th.Tensor], FirstEventHazardLabels, dict[str, Any]]:
    hyper = _hyper(train_config)
    env = _build_env(scenario, train_config)
    obs_items: list[dict[str, th.Tensor]] = []
    engagement_state: list[str] = []
    fire_mask: list[bool] = []
    fire_once_accepted: list[bool] = []
    launch_window_open: list[bool] = []
    episode_id: list[int] = []
    episode_lengths: list[int] = []
    accepted_steps: list[int] = []
    fire_open_steps = 0
    launch_open_steps = 0
    try:
        for ep in range(int(episodes)):
            obs, _info = env.reset(seed=int(seed) + int(ep))
            steps_this_ep = 0
            base_env = _base_env(env)
            ep_max_steps = int(max_steps) if int(max_steps) > 0 else int(getattr(base_env, "max_steps", 0) or 1200)
            for step in range(1, ep_max_steps + 1):
                obs_tensor = _obs_to_cpu(model.policy, obs)
                policy_fire_mask = _policy_fire_mask_from_obs(obs_tensor, 1)
                policy_launch_window = _policy_launch_window_from_obs(obs_tensor, 1, hyper=hyper)
                if str(collector_action) == "model":
                    action = _model_action(model, obs, deterministic=not bool(stochastic))
                elif str(collector_action) == "hold":
                    action = _hold_action(env)
                else:
                    raise ValueError(f"unknown collector action: {collector_action}")

                new_obs, _reward, terminated, truncated, info = env.step(action)
                row = info if isinstance(info, dict) else {}
                mask_open = (
                    bool(policy_fire_mask[0])
                    if policy_fire_mask is not None and len(policy_fire_mask) >= 1
                    else AdaptiveKLPPO._a6_first_event_fire_mask_from_info(row)
                )
                launch_open = (
                    bool(policy_launch_window[0])
                    if policy_launch_window is not None and len(policy_launch_window) >= 1
                    else bool(mask_open)
                )
                accepted = AdaptiveKLPPO._a6_first_event_bool(row.get("fire_once_accepted", False))

                obs_items.append(obs_tensor)
                engagement_state.append("AuthorizedReady" if mask_open else str(row.get("engagement_state", "") or ""))
                fire_mask.append(bool(mask_open))
                launch_window_open.append(bool(launch_open))
                fire_once_accepted.append(bool(accepted))
                episode_id.append(int(ep))
                fire_open_steps += int(bool(mask_open))
                launch_open_steps += int(bool(launch_open))
                if accepted:
                    accepted_steps.append(int(step))

                obs = new_obs
                steps_this_ep += 1
                if bool(terminated or truncated):
                    break
            episode_lengths.append(int(steps_this_ep))
    finally:
        try:
            env.close()
        except Exception:
            pass

    labels = build_first_event_hazard_labels(
        engagement_state=engagement_state,
        fire_mask=fire_mask,
        fire_once_accepted=fire_once_accepted,
        episode_id=episode_id,
        launch_window_open=launch_window_open if bool(hyper.get("a6_first_event_launch_window_enabled", False)) else None,
        launch_window_min_window_age_steps=int(hyper.get("a6_first_event_launch_window_min_window_age_steps", 1)),
        launch_window_prewindow_hold_weight=_finite_float(hyper.get("a7_event_credit_prewindow_hold_weight", 0.0), 0.0),
        launch_window_early_accept_weight=_finite_float(hyper.get("a7_event_credit_early_accept_weight", 1.0), 1.0),
        curriculum_weight=_finite_float(hyper.get("a7_event_credit_curriculum_coef", 0.0), 0.0),
        curriculum_min_window_age_steps=int(hyper.get("a7_event_credit_curriculum_min_window_age_steps", 32)),
        censored_survival_weight=_finite_float(hyper.get("a7_event_credit_censored_survival_weight", 0.0), 0.0),
        deadline_weight=_finite_float(hyper.get("a7_event_credit_deadline_weight", 0.0), 0.0),
        deadline_min_window_age_steps=int(hyper.get("a7_event_credit_deadline_min_window_age_steps", 96)),
        shadow_quality_after_early_accept=bool(_finite_float(hyper.get("a7_event_credit_shadow_quality_weight", 0.0), 0.0) > 0.0),
        shadow_quality_positive_weight=_finite_float(hyper.get("a7_event_credit_shadow_quality_weight", 0.0), 0.0),
        legal_open_quality_weight=_finite_float(hyper.get("a7_event_credit_legal_open_quality_weight", 0.0), 0.0),
        legal_open_quality_min_window_age_steps=int(hyper.get("a7_event_credit_legal_open_quality_min_window_age_steps", 1)),
        device="cpu",
    )
    source_counts = Counter(int(value) for value in labels.source.detach().cpu().reshape(-1).tolist())
    meta = {
        "collector_action": str(collector_action),
        "stochastic": bool(stochastic),
        "episodes": int(episodes),
        "episode_lengths": episode_lengths,
        "steps": int(sum(episode_lengths)),
        "fire_open_steps": int(fire_open_steps),
        "launch_open_steps": int(launch_open_steps),
        "accepted_count": int(sum(1 for value in fire_once_accepted if value)),
        "accepted_steps": accepted_steps,
        "source_counts_raw": {
            SOURCE_NAMES.get(int(key), str(key)): int(value)
            for key, value in sorted(source_counts.items())
        },
    }
    return _concat_obs(obs_items), labels, meta


def _labels_to_device(labels: FirstEventHazardLabels, device: th.device, indices: th.Tensor | None = None) -> dict[str, th.Tensor]:
    cpu_indices = indices.detach().to(device="cpu", dtype=th.long) if indices is not None else None

    def take(value: th.Tensor, dtype: th.dtype | None = None) -> th.Tensor:
        tensor = value
        if cpu_indices is not None:
            tensor = tensor.index_select(0, cpu_indices)
        tensor = tensor.to(device=device)
        if dtype is not None:
            tensor = tensor.to(dtype=dtype)
        return tensor

    return {
        "active": take(labels.active, th.bool),
        "target": take(labels.target, th.float32),
        "weight": take(labels.weight, th.float32),
        "source": take(labels.source, th.long),
        "window_id": take(labels.window_id, th.long),
    }


def _advantage_vector(policy, obs: dict[str, th.Tensor], *, batch_size: int) -> th.Tensor:
    device = th.device(policy.device)
    count = int(next(iter(obs.values())).shape[0])
    values: list[th.Tensor] = []
    policy.set_training_mode(False)
    with th.no_grad():
        for start in range(0, count, int(batch_size)):
            end = min(count, start + int(batch_size))
            indices = th.arange(start, end, dtype=th.long)
            dist = policy.get_distribution(_slice_obs(obs, indices, device))
            q_getter = getattr(dist, "fire_event_q_values", None)
            if not callable(q_getter):
                raise RuntimeError("policy distribution does not expose fire_event_q_values")
            q_values = q_getter()
            if q_values is None:
                raise RuntimeError("fire_event_q_values returned None")
            values.append((q_values[:, 1] - q_values[:, 0]).detach().to(device="cpu"))
    return th.cat(values, dim=0).reshape(-1)


def _subset_stats(name: str, mask: th.Tensor, target: th.Tensor, weight: th.Tensor, advantage: th.Tensor) -> dict[str, Any]:
    selected = mask.reshape(-1).to(dtype=th.bool)
    count = int(selected.sum().item())
    if count <= 0:
        return {
            f"{name}_count": 0,
            f"{name}_positive_count": 0,
            f"{name}_target_mean": 0.0,
            f"{name}_weight_sum": 0.0,
            f"{name}_advantage_mean": 0.0,
            f"{name}_advantage_positive_frac": 0.0,
            f"{name}_advantage_negative_frac": 0.0,
        }
    adv = advantage[selected]
    tgt = target[selected]
    w = weight[selected]
    return {
        f"{name}_count": count,
        f"{name}_positive_count": int((tgt > 0.5).sum().item()),
        f"{name}_target_mean": float(tgt.float().mean().item()),
        f"{name}_weight_sum": float(w.float().sum().item()),
        f"{name}_advantage_mean": float(adv.float().mean().item()),
        f"{name}_advantage_positive_frac": float((adv > 0.0).float().mean().item()),
        f"{name}_advantage_negative_frac": float((adv < 0.0).float().mean().item()),
    }


def evaluate_credit_head(policy, obs: dict[str, th.Tensor], labels: FirstEventHazardLabels, *, batch_size: int) -> dict[str, Any]:
    advantage = _advantage_vector(policy, obs, batch_size=batch_size)
    target = labels.target.detach().cpu().reshape(-1).float()
    weight = labels.weight.detach().cpu().reshape(-1).float()
    source = labels.source.detach().cpu().reshape(-1).long()
    active = labels.active.detach().cpu().reshape(-1).bool() & (weight > 0.0)
    stats: dict[str, Any] = {}
    stats.update(_subset_stats("active", active, target, weight, advantage))
    stats.update(_subset_stats("positive", active & (target > 0.5), target, weight, advantage))
    stats.update(_subset_stats("negative", active & (target <= 0.5), target, weight, advantage))
    for source_id, source_name in SOURCE_NAMES.items():
        stats.update(_subset_stats(f"source_{source_name}", active & (source == int(source_id)), target, weight, advantage))
    legal_positive = active & (source == int(A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY)) & (target > 0.5)
    stats.update(_subset_stats("legal_open_quality_positive", legal_positive, target, weight, advantage))
    return stats


def _trainable_param_names(policy, scope: str) -> list[str]:
    names: list[str] = []
    for name, param in policy.named_parameters():
        trainable = name.startswith("hybrid_event_credit_head.")
        if scope == "credit_head_actor_mlp":
            trainable = trainable or name.startswith("mlp_extractor.policy_net.")
            trainable = trainable or name.startswith("mlp_extractor.shared_net.")
        param.requires_grad_(bool(trainable))
        if trainable:
            names.append(str(name))
    if not names:
        raise RuntimeError(f"no trainable parameters selected for scope {scope!r}")
    return names


def fit_credit_head(
    policy,
    obs: dict[str, th.Tensor],
    labels: FirstEventHazardLabels,
    *,
    scope: str,
    steps: int,
    batch_size: int,
    learning_rate: float,
    positive_mass_cap: float,
    negative_mass_cap: float,
    log_every: int,
) -> dict[str, Any]:
    device = th.device(policy.device)
    count = int(next(iter(obs.values())).shape[0])
    trainable_names = _trainable_param_names(policy, scope)
    policy.set_training_mode(False)
    optimizer = th.optim.Adam([param for param in policy.parameters() if param.requires_grad], lr=float(learning_rate))
    losses: list[dict[str, Any]] = []
    rng = np.random.default_rng(20260604)
    for step in range(1, int(steps) + 1):
        batch_count = min(int(batch_size), count)
        if batch_count >= count:
            batch_indices_np = np.arange(count, dtype=np.int64)
        else:
            batch_indices_np = rng.choice(count, size=batch_count, replace=False).astype(np.int64)
        batch_indices = th.as_tensor(batch_indices_np, dtype=th.long)
        batch_obs = _slice_obs(obs, batch_indices, device)
        batch_labels = _labels_to_device(labels, device, batch_indices)
        dist = policy.get_distribution(batch_obs)
        q_getter = getattr(dist, "fire_event_q_values", None)
        if not callable(q_getter):
            raise RuntimeError("policy distribution does not expose fire_event_q_values")
        q_values = q_getter()
        if q_values is None:
            raise RuntimeError("fire_event_q_values returned None")
        loss_obj = compute_first_event_credit_loss(
            q_values,
            batch_labels["target"],
            batch_labels["active"],
            batch_labels["weight"],
            window_id=batch_labels["window_id"],
            value_coef=1.0,
            delta_align_coef=0.0,
            positive_mass_cap=float(positive_mass_cap),
            negative_mass_cap=float(negative_mass_cap),
        )
        optimizer.zero_grad(set_to_none=True)
        loss_obj.loss.backward()
        optimizer.step()
        if step == 1 or step == int(steps) or (int(log_every) > 0 and step % int(log_every) == 0):
            losses.append(
                {
                    "step": int(step),
                    "loss": float(loss_obj.loss.detach().cpu().item()),
                    "active_count": int(loss_obj.active_count),
                    "positive_frac": float(loss_obj.positive_frac),
                    "advantage_mean_batch": float(loss_obj.advantage_mean),
                }
            )
    return {
        "scope": str(scope),
        "steps": int(steps),
        "batch_size": int(batch_size),
        "learning_rate": float(learning_rate),
        "trainable_param_count": int(sum(param.numel() for param in policy.parameters() if param.requires_grad)),
        "trainable_param_names": trainable_names,
        "loss_trace": losses,
    }


def run_probe(args: argparse.Namespace) -> dict[str, Any]:
    scenario = os.path.abspath(args.scenario)
    train_config_path = os.path.abspath(args.train_config)
    model_path = os.path.abspath(args.model)
    train_config = load_json_config(train_config_path)
    hyper = _hyper(train_config)
    model = load_sb3_policy(model_path, algo=str(args.algo), device=str(args.device))
    obs, labels, collection = collect_fixed_batch(
        model=model,
        scenario=scenario,
        train_config=train_config,
        episodes=int(args.episodes),
        max_steps=int(args.max_steps),
        seed=int(args.seed),
        collector_action=str(args.collector_action),
        stochastic=bool(args.stochastic),
    )
    del model
    initial_model = load_sb3_policy(model_path, algo=str(args.algo), device=str(args.device))
    initial_stats = evaluate_credit_head(initial_model.policy, obs, labels, batch_size=int(args.eval_batch_size))
    del initial_model

    fit_results: list[dict[str, Any]] = []
    scopes = [scope.strip() for scope in str(args.scopes).split(",") if scope.strip()]
    for scope in scopes:
        fit_model = load_sb3_policy(model_path, algo=str(args.algo), device=str(args.device))
        before = evaluate_credit_head(fit_model.policy, obs, labels, batch_size=int(args.eval_batch_size))
        fit_meta = fit_credit_head(
            fit_model.policy,
            obs,
            labels,
            scope=scope,
            steps=int(args.fit_steps),
            batch_size=int(args.fit_batch_size),
            learning_rate=float(args.fit_lr),
            positive_mass_cap=_finite_float(hyper.get("a7_event_credit_positive_mass_cap", 1.0), 1.0),
            negative_mass_cap=_finite_float(hyper.get("a7_event_credit_negative_mass_cap", 1.0), 1.0),
            log_every=int(args.log_every),
        )
        after = evaluate_credit_head(fit_model.policy, obs, labels, batch_size=int(args.eval_batch_size))
        fit_results.append({"scope": scope, "before": before, "fit": fit_meta, "after": after})
        del fit_model

    payload = {
        "scenario": scenario,
        "train_config": train_config_path,
        "model": model_path,
        "algo": str(args.algo),
        "device": str(args.device),
        "seed": int(args.seed),
        "collection": collection,
        "label_summary": evaluate_label_summary(labels),
        "initial": initial_stats,
        "fits": fit_results,
    }
    if args.json_out:
        out_path = os.path.abspath(args.json_out)
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(_to_serializable(payload), f, indent=2, ensure_ascii=True)
            f.write("\n")
    return payload


def evaluate_label_summary(labels: FirstEventHazardLabels) -> dict[str, Any]:
    active = labels.active.detach().cpu().reshape(-1).bool()
    target = labels.target.detach().cpu().reshape(-1).float()
    weight = labels.weight.detach().cpu().reshape(-1).float()
    source = labels.source.detach().cpu().reshape(-1).long()
    weighted_active = active & (weight > 0.0)
    out: dict[str, Any] = {
        "count": int(active.numel()),
        "active_count": int(weighted_active.sum().item()),
        "positive_count": int((weighted_active & (target > 0.5)).sum().item()),
        "negative_count": int((weighted_active & (target <= 0.5)).sum().item()),
        "positive_frac": (
            float((weighted_active & (target > 0.5)).sum().item()) / float(max(1, int(weighted_active.sum().item())))
        ),
        "weight_sum": float(weight[weighted_active].sum().item()) if int(weighted_active.sum().item()) > 0 else 0.0,
    }
    for source_id, source_name in SOURCE_NAMES.items():
        mask = weighted_active & (source == int(source_id))
        out[f"source_{source_name}_count"] = int(mask.sum().item())
        out[f"source_{source_name}_positive_count"] = int((mask & (target > 0.5)).sum().item())
        out[f"source_{source_name}_weight_sum"] = float(weight[mask].sum().item()) if int(mask.sum().item()) > 0 else 0.0
    return out


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Offline supervised fit probe for the first-event credit head.")
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
    parser.add_argument("--fit_steps", type=int, default=1200)
    parser.add_argument("--fit_batch_size", type=int, default=512)
    parser.add_argument("--eval_batch_size", type=int, default=512)
    parser.add_argument("--fit_lr", type=float, default=1.0e-3)
    parser.add_argument("--scopes", default="credit_head,credit_head_actor_mlp")
    parser.add_argument("--log_every", type=int, default=100)
    parser.add_argument("--json_out", default="")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    payload = run_probe(args)
    print(json.dumps(_to_serializable(payload), indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
