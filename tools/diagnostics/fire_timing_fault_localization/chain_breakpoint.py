#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Sequence

import torch as th

_REPO_ROOT_HINT = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT_HINT = os.path.dirname(_REPO_ROOT_HINT)
_REPO_ROOT_HINT = os.path.dirname(_REPO_ROOT_HINT)
if _REPO_ROOT_HINT not in sys.path:
    sys.path.insert(0, _REPO_ROOT_HINT)
from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path

ensure_repo_imports()

from python.rl.policy_algo.model_contracts import FaultLocalizationResult, FaultStage  # noqa: E402
from tools.diagnostics.fire_timing_fault_localization.real_update import (  # noqa: E402
    DEFAULT_SCENARIO,
    DEFAULT_TRAIN_CONFIG,
    RealM3S2Group,
    _to_serializable,
    collect_real_batch,
)
from tools.eval.sb3_eval_base import load_json_config, load_sb3_policy  # noqa: E402


DEFAULT_MODEL = resolve_repo_path(
    "experiments_tmp",
    "scale_separated_contract_8k_20260606_r1",
    "final_model.zip",
)


@dataclass(frozen=True)
class ChainMasks:
    legal: th.Tensor
    quality: th.Tensor
    prewindow: th.Tensor
    eligible: th.Tensor


def _first_batch_size(obs: dict[str, th.Tensor]) -> int:
    for value in obs.values():
        if th.is_tensor(value) and value.ndim >= 1:
            return int(value.shape[0])
    return 0


def _masks_from_groups(groups: Sequence[RealM3S2Group], *, row_count: int) -> ChainMasks:
    legal = th.zeros((int(row_count),), dtype=th.bool)
    quality = th.zeros((int(row_count),), dtype=th.bool)
    for group in groups:
        for row, legal_value, quality_value in zip(group.row_indices, group.legal_mask, group.quality_mask):
            row_index = int(row)
            if 0 <= row_index < int(row_count):
                legal[row_index] = bool(legal_value)
                quality[row_index] = bool(quality_value)
    prewindow = legal & ~quality
    return ChainMasks(legal=legal, quality=quality, prewindow=prewindow, eligible=legal)


def _obs_to_device(obs: dict[str, th.Tensor], device: th.device) -> dict[str, th.Tensor]:
    return {
        key: value.to(device=device) if th.is_tensor(value) else th.as_tensor(value, device=device)
        for key, value in obs.items()
    }


def _actor_latent(policy: Any, obs: dict[str, th.Tensor]) -> th.Tensor:
    policy.set_training_mode(False)
    device = th.device(policy.device)
    with th.no_grad():
        obs_device = _obs_to_device(obs, device)
        features = policy.extract_features(obs_device, policy.pi_features_extractor)
        latent = policy.mlp_extractor.forward_actor(features)
    return latent.detach()


def _stopping_head_input(policy: Any, latent: th.Tensor) -> th.Tensor:
    normalizer = getattr(policy, "_stopping_latent", None)
    if callable(normalizer):
        return normalizer(latent)
    norm = getattr(policy, "stopping_norm", None)
    if norm is None:
        return latent
    return norm(latent)


def _window_classifier_head_input(policy: Any, latent: th.Tensor) -> th.Tensor:
    normalizer = getattr(policy, "_window_classifier_latent", None)
    if callable(normalizer):
        return normalizer(latent)
    norm = getattr(policy, "window_classifier_norm", None)
    if norm is None:
        return latent
    return norm(latent)


def _resolve_adapter_head_kind(policy: Any, requested: str = "auto") -> str:
    requested = str(requested or "auto").strip().lower()
    if requested in {"window", "window_classifier", "stopping_window_classifier"}:
        return "window_classifier"
    if requested in {"stopping", "stopping"}:
        return "stopping"
    if requested != "auto":
        raise ValueError(f"unknown adapter head kind: {requested!r}")
    if (
        bool(getattr(policy, "_hybrid_event_use_window_classifier_head", False))
        and getattr(policy, "window_classifier_head", None) is not None
    ):
        return "window_classifier"
    if (
        bool(getattr(policy, "_hybrid_event_use_stopping_head", False))
        and getattr(policy, "stopping_head", None) is not None
    ):
        return "stopping"
    if getattr(policy, "window_classifier_head", None) is not None:
        return "window_classifier"
    if getattr(policy, "stopping_head", None) is not None:
        return "stopping"
    raise RuntimeError("policy has no M3 head available for adapter probing")


def _head_module(policy: Any, head_kind: str) -> th.nn.Linear:
    if str(head_kind) == "window_classifier":
        target = getattr(policy, "window_classifier_head", None)
        if target is None:
            raise RuntimeError("policy has no window_classifier_head")
        return target
    if str(head_kind) == "stopping":
        target = getattr(policy, "stopping_head", None)
        if target is None:
            raise RuntimeError("policy has no stopping_head")
        return target
    raise ValueError(f"unknown M3 head kind: {head_kind!r}")


def _head_input(policy: Any, latent: th.Tensor, head_kind: str) -> th.Tensor:
    if str(head_kind) == "window_classifier":
        return _window_classifier_head_input(policy, latent)
    if str(head_kind) == "stopping":
        return _stopping_head_input(policy, latent)
    raise ValueError(f"unknown M3 head kind: {head_kind!r}")


def _classification_metrics(logits: th.Tensor, masks: ChainMasks) -> dict[str, Any]:
    logits = logits.detach().reshape(-1).cpu().float()
    labels = masks.quality.cpu().float()
    eligible = masks.eligible.cpu()
    prewindow = masks.prewindow.cpu()
    quality = masks.quality.cpu()
    if int(eligible.sum().item()) <= 0:
        return {
            "eligible_count": 0,
            "accuracy": 0.0,
            "prewindow_count": int(prewindow.sum().item()),
            "quality_count": int(quality.sum().item()),
            "prewindow_boundary_count": 0,
            "quality_boundary_count": 0,
            "quality_all_boundary": False,
            "prewindow_no_boundary": False,
        }
    predictions = logits >= 0.0
    correct = predictions[eligible] == (labels[eligible] > 0.5)
    pre_logits = logits[prewindow]
    quality_logits = logits[quality]
    quality_count = int(quality.sum().item())
    prewindow_count = int(prewindow.sum().item())
    pre_boundary = int((pre_logits >= 0.0).sum().item()) if prewindow_count > 0 else 0
    quality_boundary = int((quality_logits >= 0.0).sum().item()) if quality_count > 0 else 0
    return {
        "eligible_count": int(eligible.sum().item()),
        "accuracy": float(correct.float().mean().item()),
        "prewindow_count": prewindow_count,
        "quality_count": quality_count,
        "prewindow_logit_mean": float(pre_logits.mean().item()) if prewindow_count > 0 else 0.0,
        "prewindow_logit_max": float(pre_logits.max().item()) if prewindow_count > 0 else 0.0,
        "prewindow_prob_mean": float(th.sigmoid(pre_logits).mean().item()) if prewindow_count > 0 else 0.0,
        "quality_logit_mean": float(quality_logits.mean().item()) if quality_count > 0 else 0.0,
        "quality_logit_min": float(quality_logits.min().item()) if quality_count > 0 else 0.0,
        "quality_logit_max": float(quality_logits.max().item()) if quality_count > 0 else 0.0,
        "quality_prob_mean": float(th.sigmoid(quality_logits).mean().item()) if quality_count > 0 else 0.0,
        "prewindow_boundary_count": pre_boundary,
        "quality_boundary_count": quality_boundary,
        "quality_all_boundary": bool(quality_count > 0 and quality_boundary == quality_count),
        "prewindow_no_boundary": bool(pre_boundary == 0),
        "separation_margin": (
            float(quality_logits.min().item() - pre_logits.max().item())
            if quality_count > 0 and prewindow_count > 0
            else 0.0
        ),
    }


def _passes_window_classifier(metrics: dict[str, Any], *, min_accuracy: float) -> bool:
    return bool(
        int(metrics.get("quality_count", 0)) > 0
        and int(metrics.get("prewindow_count", 0)) > 0
        and float(metrics.get("accuracy", 0.0)) >= float(min_accuracy)
        and bool(metrics.get("quality_all_boundary", False))
        and bool(metrics.get("prewindow_no_boundary", False))
    )


def _balanced_bce_loss(logits: th.Tensor, labels: th.Tensor) -> th.Tensor:
    labels = labels.to(device=logits.device, dtype=logits.dtype)
    pos = labels.sum().clamp_min(1.0)
    neg = (labels.numel() - labels.sum()).clamp_min(1.0)
    pos_weight = neg / pos
    return th.nn.functional.binary_cross_entropy_with_logits(logits, labels, pos_weight=pos_weight)


def _fit_linear_head(
    latent: th.Tensor,
    masks: ChainMasks,
    *,
    steps: int,
    learning_rate: float,
    seed: int,
    standardize: bool,
    init_head: th.nn.Linear | None = None,
) -> tuple[th.nn.Linear, th.nn.Linear, dict[str, Any]]:
    th.manual_seed(int(seed))
    device = latent.device
    eligible = masks.eligible.to(device=device)
    labels = masks.quality.to(device=device, dtype=latent.dtype)
    train_x = latent[eligible].detach()
    train_y = labels[eligible].detach()
    if int(train_x.shape[0]) <= 0:
        raise RuntimeError("chain breakpoint probe has no eligible rows")
    mean = train_x.mean(dim=0, keepdim=True) if bool(standardize) else th.zeros((1, latent.shape[1]), device=device)
    std = train_x.std(dim=0, keepdim=True).clamp_min(1.0e-6) if bool(standardize) else th.ones((1, latent.shape[1]), device=device)
    work_latent = (latent.detach() - mean) / std
    head = th.nn.Linear(int(latent.shape[1]), 1).to(device=device, dtype=latent.dtype)
    if init_head is not None and not bool(standardize):
        head.load_state_dict(copy.deepcopy(init_head.state_dict()))
    optimizer = th.optim.Adam(head.parameters(), lr=float(learning_rate))
    trace: list[dict[str, Any]] = []
    for step in range(1, int(steps) + 1):
        optimizer.zero_grad(set_to_none=True)
        logits = head(work_latent[eligible]).reshape(-1)
        loss = _balanced_bce_loss(logits, train_y)
        loss.backward()
        optimizer.step()
        if step == 1 or step == int(steps):
            with th.no_grad():
                all_logits = head(work_latent).reshape(-1)
                metrics = _classification_metrics(all_logits, masks)
            trace.append({"step": int(step), "loss": float(loss.detach().cpu().item()), **metrics})
    with th.no_grad():
        final_logits = head(work_latent).reshape(-1)
        final = _classification_metrics(final_logits, masks)
    final["steps"] = int(steps)
    final["learning_rate"] = float(learning_rate)
    final["standardized_input"] = bool(standardize)
    final["trace"] = trace
    raw_head = _fold_standardized_head(head, mean=mean, std=std)
    return head, raw_head, final


def _fold_standardized_head(head: th.nn.Linear, *, mean: th.Tensor, std: th.Tensor) -> th.nn.Linear:
    raw_head = th.nn.Linear(int(head.in_features), int(head.out_features)).to(
        device=head.weight.device,
        dtype=head.weight.dtype,
    )
    with th.no_grad():
        scale = std.reshape(1, -1).to(device=head.weight.device, dtype=head.weight.dtype)
        offset = mean.reshape(1, -1).to(device=head.weight.device, dtype=head.weight.dtype)
        raw_weight = head.weight / scale
        raw_bias = head.bias - (raw_weight * offset).sum(dim=1)
        raw_head.weight.copy_(raw_weight)
        raw_head.bias.copy_(raw_bias)
    return raw_head


def _distribution_summary(policy: Any, obs: dict[str, th.Tensor], masks: ChainMasks) -> dict[str, Any]:
    policy.set_training_mode(False)
    device = th.device(policy.device)
    with th.no_grad():
        obs_device = _obs_to_device(obs, device)
        distribution = policy.get_distribution(obs_device)
        delta_getter = getattr(distribution, "fire_event_logit_delta", None)
        if not callable(delta_getter):
            raise RuntimeError("policy distribution does not expose fire_event_logit_delta")
        delta = delta_getter()
        if delta is None:
            raise RuntimeError("fire_event_logit_delta returned None")
        mode = distribution.mode()
    layout = getattr(policy, "_hybrid_action_layout", None)
    event_index = None if layout is None else layout.event_action_index
    if event_index is None:
        raise RuntimeError("policy has no hybrid event action index")
    event_mode_high = mode[:, int(event_index)].detach().cpu().reshape(-1) > 0.5
    out = _classification_metrics(delta.detach().cpu().reshape(-1), masks)
    out["event_mode_fire_count"] = int(event_mode_high.sum().item())
    out["event_mode_fire_prewindow_count"] = int((event_mode_high & masks.prewindow.cpu()).sum().item())
    out["event_mode_fire_quality_count"] = int((event_mode_high & masks.quality.cpu()).sum().item())
    out["edge_trigger"] = _edge_trigger_summary(event_mode_high, masks)
    return out


def _window_classifier_recalibration_summary(
    policy: Any,
    obs: dict[str, th.Tensor],
    masks: ChainMasks,
    *,
    head_kind: str,
) -> dict[str, Any]:
    if str(head_kind) != "window_classifier":
        return {"enabled": False, "reason": "adapter_head_is_not_window_classifier"}
    latent_getter = getattr(policy, "get_window_latent", None)
    standardization_updater = getattr(
        policy,
        "update_window_classifier_input_standardization",
        None,
    )
    mean_buffer = getattr(policy, "window_classifier_input_mean", None)
    std_buffer = getattr(policy, "window_classifier_input_std", None)
    initialized = getattr(policy, "window_classifier_input_standardization_initialized", None)
    if (
        not callable(latent_getter)
        or not callable(standardization_updater)
        or mean_buffer is None
        or std_buffer is None
        or initialized is None
    ):
        return {"enabled": False, "reason": "standardization_buffers_unavailable"}
    eligible = masks.eligible.to(device=th.device(policy.device), dtype=th.bool)
    if int(eligible.sum().detach().cpu().item()) <= 0:
        return {"enabled": False, "reason": "no_eligible_rows"}

    old_mean = mean_buffer.detach().clone()
    old_std = std_buffer.detach().clone()
    old_initialized = initialized.detach().clone()
    try:
        policy.set_training_mode(False)
        device = th.device(policy.device)
        obs_device = _obs_to_device(obs, device)
        with th.no_grad():
            raw_latent = latent_getter(obs_device, detach_latent=True)
            raw_latent = raw_latent.reshape(int(raw_latent.shape[0]), -1)
            eligible_latent = raw_latent[eligible]
            base_getter = getattr(policy, "_window_classifier_base_latent", None)
            base_latent = (
                base_getter(eligible_latent).detach()
                if callable(base_getter)
                else eligible_latent.detach()
            )
            saved_mean = mean_buffer.detach().to(device=device, dtype=base_latent.dtype).reshape(1, -1)
            saved_std = std_buffer.detach().to(device=device, dtype=base_latent.dtype).reshape(1, -1)
            fixed_mean = base_latent.mean(dim=0, keepdim=True)
            fixed_std = base_latent.std(dim=0, unbiased=False, keepdim=True).clamp_min(1.0e-6)
            saved_z = (base_latent - saved_mean) / saved_std.clamp_min(1.0e-6)
            shift = {
                "saved_z_mean_abs_mean": float(saved_z.mean(dim=0).abs().mean().item()),
                "saved_z_std_mean": float(saved_z.std(dim=0, unbiased=False).mean().item()),
                "mean_delta_l2": float((fixed_mean - saved_mean).norm().item()),
                "std_ratio_mean": float((fixed_std / saved_std.clamp_min(1.0e-6)).mean().item()),
                "std_ratio_min": float((fixed_std / saved_std.clamp_min(1.0e-6)).min().item()),
                "std_ratio_max": float((fixed_std / saved_std.clamp_min(1.0e-6)).max().item()),
            }
        updated = bool(standardization_updater(eligible_latent))
        distribution = _distribution_summary(policy, obs, masks) if updated else {}
        with th.no_grad():
            latent = _actor_latent(policy, obs)
            head_input = _head_input(policy, latent, head_kind)
            logits = _head_module(policy, head_kind)(head_input).reshape(-1).detach().cpu()
        return {
            "enabled": True,
            "updated": bool(updated),
            "eligible_count": int(eligible.sum().detach().cpu().item()),
            "buffer_shift": shift,
            "distribution_after_fixed_batch_recalibration": distribution,
            "head_after_fixed_batch_recalibration": _classification_metrics(logits, masks),
        }
    finally:
        with th.no_grad():
            mean_buffer.copy_(old_mean)
            std_buffer.copy_(old_std)
            initialized.copy_(old_initialized)


def _edge_trigger_summary(event_high: th.Tensor, masks: ChainMasks) -> dict[str, Any]:
    high = event_high.detach().cpu().reshape(-1).to(dtype=th.bool)
    legal = masks.legal.cpu()
    quality = masks.quality.cpu()
    prewindow = masks.prewindow.cpu()
    pulses: list[dict[str, Any]] = []
    previous = False
    for row, value in enumerate(high.tolist()):
        current = bool(value)
        if current and not previous:
            pulses.append(
                {
                    "row": int(row),
                    "legal": bool(legal[row].item()) if row < int(legal.numel()) else False,
                    "quality": bool(quality[row].item()) if row < int(quality.numel()) else False,
                    "prewindow": bool(prewindow[row].item()) if row < int(prewindow.numel()) else False,
                }
            )
        previous = current
    legal_pulses = [pulse for pulse in pulses if bool(pulse["legal"])]
    quality_pulses = [pulse for pulse in pulses if bool(pulse["quality"])]
    prewindow_pulses = [pulse for pulse in pulses if bool(pulse["prewindow"])]
    return {
        "pulse_count": int(len(pulses)),
        "legal_pulse_count": int(len(legal_pulses)),
        "quality_pulse_count": int(len(quality_pulses)),
        "prewindow_pulse_count": int(len(prewindow_pulses)),
        "first_pulse": pulses[0] if pulses else None,
        "first_legal_pulse": legal_pulses[0] if legal_pulses else None,
        "first_quality_pulse": quality_pulses[0] if quality_pulses else None,
    }


def _install_head(policy: Any, head: th.nn.Linear, *, head_kind: str) -> None:
    target = _head_module(policy, head_kind)
    target.load_state_dict(copy.deepcopy(head.state_dict()))


def _adapter_summary_for_head(
    *,
    model_path: str,
    algo: str,
    device: str,
    obs: dict[str, th.Tensor],
    masks: ChainMasks,
    head: th.nn.Linear,
    head_kind: str,
    label_contract: dict[str, Any],
) -> dict[str, Any]:
    adapter_model = load_sb3_policy(model_path, algo=algo, device=device)
    _install_head(adapter_model.policy, head, head_kind=head_kind)
    adapter_distribution = _distribution_summary(adapter_model.policy, obs, masks)
    with th.no_grad():
        adapter_latent = _actor_latent(adapter_model.policy, obs)
        adapter_head_input = _head_input(adapter_model.policy, adapter_latent, head_kind)
        installed_logits = _head_module(adapter_model.policy, head_kind)(adapter_head_input).reshape(-1).detach().cpu()
    try:
        dist = adapter_model.policy.get_distribution(_obs_to_device(obs, th.device(adapter_model.policy.device)))
        adapter_delta = dist.fire_event_logit_delta().detach().cpu().reshape(-1)
    except Exception:
        adapter_delta = th.full_like(installed_logits, float("nan"))
    delta_diff = (
        float((adapter_delta - installed_logits).abs().max().item())
        if int(adapter_delta.numel()) == int(installed_logits.numel())
        else float("inf")
    )
    delta_identity_pass = bool(delta_diff <= 1.0e-5)
    adapter_pass = bool(
        int(adapter_distribution.get("event_mode_fire_prewindow_count", 0)) == 0
        and int(adapter_distribution.get("event_mode_fire_quality_count", 0))
        == int(label_contract.get("quality_count", 0))
    )
    edge = adapter_distribution.get("edge_trigger", {})
    edge_pass = bool(
        int(edge.get("quality_pulse_count", 0)) == 1
        and int(edge.get("prewindow_pulse_count", 0)) == 0
        and bool((edge.get("first_quality_pulse") or {}).get("quality", False))
    )
    return {
        **adapter_distribution,
        "head_kind": str(head_kind),
        "delta_matches_installed_head_max_abs": delta_diff,
        "delta_identity_pass": delta_identity_pass,
        "pass": adapter_pass,
        "edge_trigger_pass": edge_pass,
    }


def _first_failed_fault_stage(results: Sequence[FaultLocalizationResult]) -> str | None:
    for result in results:
        if not bool(result.checked):
            continue
        if not bool(result.passed):
            return result.stage.value
    return None


def _fault_localization_summary(
    *,
    label_contract: dict[str, Any],
    fresh_latent: dict[str, Any],
    trained_head: dict[str, Any],
    adapter_from_fresh: dict[str, Any],
    current_policy_pass: bool,
    first_breakpoint: str,
) -> dict[str, Any]:
    row_count = int(label_contract.get("row_count", 0))
    legal_count = int(label_contract.get("legal_count", 0))
    prewindow_count = int(label_contract.get("prewindow_count", 0))
    quality_count = int(label_contract.get("quality_count", 0))
    adapter_projection_pass = bool(adapter_from_fresh.get("pass", False))
    edge_trigger_pass = bool(adapter_from_fresh.get("edge_trigger_pass", False))

    if not adapter_projection_pass:
        adapter_verdict = "folded head did not map to supported fire event distribution"
    elif not edge_trigger_pass:
        adapter_verdict = "event distribution did not produce a legal quality-window edge trigger"
    else:
        adapter_verdict = "folded head projects through executable event adapter"

    results = [
        FaultLocalizationResult(
            stage=FaultStage.OBSERVATION,
            passed=row_count > 0,
            verdict="observation batch collected" if row_count > 0 else "no observation rows collected",
            evidence={"row_count": row_count},
        ),
        FaultLocalizationResult(
            stage=FaultStage.SUPPORT,
            passed=legal_count > 0,
            verdict="legal support rows exist" if legal_count > 0 else "no legal support rows",
            evidence={"legal_count": legal_count},
        ),
        FaultLocalizationResult(
            stage=FaultStage.LABEL,
            passed=bool(label_contract.get("pass", False)),
            verdict=(
                "prewindow and quality labels are present"
                if bool(label_contract.get("pass", False))
                else "missing prewindow or quality labels"
            ),
            evidence={
                "prewindow_count": prewindow_count,
                "quality_count": quality_count,
            },
        ),
        FaultLocalizationResult(
            stage=FaultStage.REPRESENTATION,
            passed=bool(fresh_latent.get("pass", False)),
            verdict=(
                "frozen actor latent can separate prewindow and quality rows"
                if bool(fresh_latent.get("pass", False))
                else "frozen actor latent cannot separate the timing boundary"
            ),
            evidence={
                "accuracy": float(fresh_latent.get("accuracy", 0.0)),
                "prewindow_boundary_count": int(fresh_latent.get("prewindow_boundary_count", 0)),
                "quality_boundary_count": int(fresh_latent.get("quality_boundary_count", 0)),
                "quality_count": int(fresh_latent.get("quality_count", 0)),
            },
        ),
        FaultLocalizationResult(
            stage=FaultStage.LOSS_OBJECT,
            passed=True,
            verdict="not checked by chain breakpoint probe; use structural-toy or real-update probes",
            evidence={},
            blocks_feature_addition=False,
            checked=False,
        ),
        FaultLocalizationResult(
            stage=FaultStage.ADAPTER,
            passed=adapter_projection_pass and edge_trigger_pass,
            verdict=adapter_verdict,
            evidence={
                "adapter_projection_pass": adapter_projection_pass,
                "edge_trigger_pass": edge_trigger_pass,
                "event_mode_fire_prewindow_count": int(
                    adapter_from_fresh.get("event_mode_fire_prewindow_count", 0)
                ),
                "event_mode_fire_quality_count": int(adapter_from_fresh.get("event_mode_fire_quality_count", 0)),
                "quality_count": quality_count,
            },
        ),
        FaultLocalizationResult(
            stage=FaultStage.OPTIMIZER,
            passed=bool(trained_head.get("pass", False)),
            verdict=(
                "current M3 head can be trained on the fixed latent boundary"
                if bool(trained_head.get("pass", False))
                else "current M3 head optimization fails on the fixed latent boundary"
            ),
            evidence={
                "accuracy": float(trained_head.get("accuracy", 0.0)),
                "prewindow_boundary_count": int(trained_head.get("prewindow_boundary_count", 0)),
                "quality_boundary_count": int(trained_head.get("quality_boundary_count", 0)),
                "quality_count": int(trained_head.get("quality_count", 0)),
            },
        ),
        FaultLocalizationResult(
            stage=FaultStage.EVALUATION,
            passed=bool(current_policy_pass),
            verdict=(
                "saved policy crosses deterministic execution-support boundary"
                if bool(current_policy_pass)
                else "saved policy does not cross deterministic execution-support boundary"
            ),
            evidence={"current_policy_distribution_pass": bool(current_policy_pass)},
        ),
    ]
    first_failed_stage = _first_failed_fault_stage(results)
    return {
        "mechanism_id": "m3s2.window_classifier_event_adapter",
        "legacy_first_breakpoint": str(first_breakpoint),
        "first_failed_stage": first_failed_stage,
        "blocks_feature_addition": first_failed_stage is not None,
        "stages": [result.as_dict() for result in results],
    }


def _run_probe(args: argparse.Namespace) -> dict[str, Any]:
    scenario = os.path.abspath(str(args.scenario))
    train_config_path = os.path.abspath(str(args.train_config))
    model_path = os.path.abspath(str(args.model))
    train_config = load_json_config(train_config_path)
    collector_model = load_sb3_policy(model_path, algo=str(args.algo), device=str(args.device))
    adapter_head_kind = _resolve_adapter_head_kind(collector_model.policy, str(args.adapter_head))
    obs, groups, collection = collect_real_batch(
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

    row_count = _first_batch_size(obs)
    masks = _masks_from_groups(groups, row_count=row_count)
    label_contract = {
        "row_count": int(row_count),
        "legal_count": int(masks.legal.sum().item()),
        "prewindow_count": int(masks.prewindow.sum().item()),
        "quality_count": int(masks.quality.sum().item()),
    }
    label_contract["pass"] = bool(
        label_contract["legal_count"] > 0
        and label_contract["prewindow_count"] > 0
        and label_contract["quality_count"] > 0
    )

    model = load_sb3_policy(model_path, algo=str(args.algo), device=str(args.device))
    latent = _actor_latent(model.policy, obs)
    adapter_head_kind = _resolve_adapter_head_kind(model.policy, str(args.adapter_head))
    head_input = _head_input(model.policy, latent, adapter_head_kind).detach()
    current_distribution = _distribution_summary(model.policy, obs, masks)
    initial_head = _head_module(model.policy, adapter_head_kind)
    current_head_logits = initial_head(head_input).reshape(-1)
    current_head = _classification_metrics(current_head_logits, masks)
    window_recalibration = _window_classifier_recalibration_summary(
        model.policy,
        obs,
        masks,
        head_kind=adapter_head_kind,
    )

    _fresh_head, fresh_raw_head, fresh_latent = _fit_linear_head(
        head_input,
        masks,
        steps=int(args.fit_steps),
        learning_rate=float(args.fit_lr),
        seed=int(args.seed),
        standardize=True,
    )
    trained_head, trained_raw_head, trained_head = _fit_linear_head(
        head_input,
        masks,
        steps=int(args.fit_steps),
        learning_rate=float(args.fit_lr),
        seed=int(args.seed),
        standardize=False,
        init_head=initial_head,
    )
    fresh_latent["pass"] = _passes_window_classifier(fresh_latent, min_accuracy=float(args.min_accuracy))
    trained_head["pass"] = _passes_window_classifier(trained_head, min_accuracy=float(args.min_accuracy))

    adapter_from_fresh = _adapter_summary_for_head(
        model_path=model_path,
        algo=str(args.algo),
        device=str(args.device),
        obs=obs,
        masks=masks,
        head=fresh_raw_head,
        head_kind=adapter_head_kind,
        label_contract=label_contract,
    )
    adapter_from_trained = _adapter_summary_for_head(
        model_path=model_path,
        algo=str(args.algo),
        device=str(args.device),
        obs=obs,
        masks=masks,
        head=trained_raw_head,
        head_kind=adapter_head_kind,
        label_contract=label_contract,
    )
    edge_fresh = adapter_from_fresh.get("edge_trigger", {})
    adapter_pass = bool(adapter_from_fresh.get("pass", False))
    edge_pass = bool(adapter_from_fresh.get("edge_trigger_pass", False))

    current_policy_pass = _passes_window_classifier(current_distribution, min_accuracy=float(args.min_accuracy))
    if not label_contract["pass"]:
        first_breakpoint = "label_target"
    elif not bool(fresh_latent["pass"]):
        first_breakpoint = "frozen_actor_latent"
    elif not adapter_pass:
        first_breakpoint = "action_distribution_adapter"
    elif not edge_pass:
        first_breakpoint = "edge_trigger_transport"
    elif not bool(trained_head["pass"]):
        first_breakpoint = "head_optimization_conditioning"
    elif not current_policy_pass:
        first_breakpoint = "online_training_or_learned_parameter_contract"
    else:
        first_breakpoint = "not_reproduced_on_fixed_batch"

    fault_localization = _fault_localization_summary(
        label_contract=label_contract,
        fresh_latent=fresh_latent,
        trained_head=trained_head,
        adapter_from_fresh=adapter_from_fresh,
        current_policy_pass=current_policy_pass,
        first_breakpoint=first_breakpoint,
    )

    payload = {
        "scenario": scenario,
        "train_config": train_config_path,
        "model": model_path,
        "algo": str(args.algo),
        "device": str(args.device),
        "seed": int(args.seed),
        "adapter_head_kind": str(adapter_head_kind),
        "collection": collection,
        "label_contract": label_contract,
        "current_policy_distribution": current_distribution,
        "current_head": current_head,
        "window_classifier_fixed_batch_recalibration": window_recalibration,
        "fresh_latent_linear_probe": fresh_latent,
        "trained_head_on_frozen_latent": trained_head,
        "adapter_after_folded_fresh_latent_head": adapter_from_fresh,
        "adapter_after_direct_trained_head": adapter_from_trained,
        "edge_trigger_after_trained_head": {
            **edge_fresh,
            "pass": edge_pass,
        },
        "verdict": {
            "label_contract_pass": bool(label_contract["pass"]),
            "fresh_latent_linear_probe_pass": bool(fresh_latent["pass"]),
            "trained_head_on_frozen_latent_pass": bool(trained_head["pass"]),
            "adapter_projection_pass": bool(adapter_pass),
            "edge_trigger_pass": bool(edge_pass),
            "current_policy_distribution_pass": bool(current_policy_pass),
            "first_breakpoint": first_breakpoint,
        },
        "fault_localization": fault_localization,
    }
    return _to_serializable(payload)


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
    parser.add_argument("--fit-steps", type=int, default=800)
    parser.add_argument("--fit-lr", type=float, default=0.01)
    parser.add_argument("--min-accuracy", type=float, default=0.99)
    parser.add_argument("--adapter-head", choices=("auto", "window_classifier", "stopping"), default="auto")
    parser.add_argument("--collector-action", choices=("hold", "model", "model_event_hold"), default="hold")
    parser.add_argument("--stochastic", action="store_true")
    parser.add_argument("--json-out", default="")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    payload = _run_probe(args)
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
