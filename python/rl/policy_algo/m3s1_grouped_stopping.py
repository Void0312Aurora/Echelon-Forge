from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping, Sequence

import torch as th


M3S1_ROUTE_ON_POLICY = "on_policy"
M3S1_ROUTE_FORCED_HOLD_PROBE = "forced_hold_probe"
M3S1_ROUTE_COUNTERFACTUAL_REPLAY = "counterfactual_replay"

M3S1_CENSOR_NONE = "none"
M3S1_CENSOR_EARLY_EVENT_PREFIX = "early_event_prefix"
M3S1_CENSOR_FORCED_HOLD = "forced_hold"
M3S1_CENSOR_TIMEOUT = "timeout"
M3S1_CENSOR_UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class M3S1GroupedStoppingEvidence:
    """One ordered M3-S1 survival/stopping group.

    `support_horizon`, when present, is interpreted as the last supported
    `row_indices` value. `censor_step`, when present, is interpreted in
    `step_indices` coordinates.
    """

    group_id: int | str
    episode_id: int | str
    route_source: str
    row_indices: Sequence[int] | th.Tensor
    step_indices: Sequence[int] | th.Tensor
    env_indices: Sequence[int] | th.Tensor
    legal_mask: Sequence[bool] | th.Tensor
    quality_mask: Sequence[bool] | th.Tensor
    stopping_logits: th.Tensor
    accepted_event: Sequence[bool] | th.Tensor | None = None
    forced_hold: Sequence[bool] | th.Tensor | bool | None = None
    censoring_kind: str = M3S1_CENSOR_NONE
    censor_step: int | None = None
    support_horizon: int | None = None
    metadata: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class M3S1GroupedStoppingStats:
    group_count: int
    active_group_count: int
    skipped_group_count: int
    unsupported_group_count: int
    row_count: int
    active_row_count: int
    window_group_count: int
    no_window_group_count: int
    early_prefix_group_count: int
    right_censor_group_count: int
    boundary_cross_count: int
    boundary_cross_in_window_count: int
    closed_mask_stop_attempt_count: int
    mean_p_window: float
    mean_p_early: float
    mean_p_none: float
    mean_lambda: float
    mean_p_deadline: float
    mean_quality_delay: float
    mean_quality_boundary_logit: float
    mean_quality_boundary_margin_loss: float
    mean_quality_prewindow_logit_margin: float
    mean_quality_prewindow_margin_loss: float
    mean_window_balanced_bce_loss: float
    mean_prewindow_hazard_mean: float
    mean_prewindow_hazard_max: float
    mean_prewindow_hazard_target: float
    mean_prewindow_hazard_scale_loss: float
    mean_quality_hazard_target: float
    mean_quality_hazard_target_loss: float
    mean_prewindow_logit_ceiling: float
    mean_prewindow_logit_ceiling_loss: float
    mean_quality_logit_floor: float
    mean_quality_logit_floor_loss: float
    mean_loss: float
    max_group_loss: float


@dataclass(frozen=True)
class M3S1GroupedStoppingLoss:
    loss: th.Tensor
    unscaled_loss: th.Tensor
    stats: M3S1GroupedStoppingStats


def compute_m3s1_grouped_stopping_loss(
    groups: Sequence[M3S1GroupedStoppingEvidence],
    *,
    coef: float = 1.0,
    early_mass_coef: float = 1.0,
    early_mass_budget: float = 0.05,
    early_survival_coef: float = 0.0,
    prefix_early_mass_budget: float | None = None,
    no_event_coef: float = 1.0,
    window_delay_coef: float = 0.0,
    window_deadline_coef: float = 0.0,
    window_deadline_steps: int = 0,
    window_quality_boundary_coef: float = 0.0,
    window_quality_boundary_logit: float = 0.0,
    window_contrastive_margin_coef: float = 0.0,
    window_contrastive_margin: float = 0.0,
    window_balanced_bce_coef: float = 0.0,
    window_prewindow_hazard_scale_coef: float = 0.0,
    window_prewindow_hazard_target: float = 0.0,
    window_quality_hazard_target_coef: float = 0.0,
    window_quality_hazard_target: float = 0.5,
    window_prewindow_logit_ceiling_coef: float = 0.0,
    window_prewindow_logit_ceiling: float = -2.0,
    window_quality_logit_floor_coef: float = 0.0,
    window_quality_logit_floor: float = 2.0,
    eps: float = 1.0e-8,
    boundary_threshold: float = 0.0,
) -> M3S1GroupedStoppingLoss:
    """Compute the P2 grouped stopping objective over complete groups.

    The objective is intentionally group-preserving: each group builds
    `lambda_t = M_t * sigmoid(z_t)`, cumulative survival, event mass, desirable
    window mass, early mass, and no-event mass before contributing one grouped
    loss term. It is not equivalent to independent row-wise BCE.
    """

    zero_base = _zero_like_group_logits(groups)
    group_losses: list[th.Tensor] = []
    p_window_values: list[float] = []
    p_early_values: list[float] = []
    p_none_values: list[float] = []
    p_deadline_values: list[float] = []
    quality_delay_values: list[float] = []
    quality_boundary_logit_values: list[float] = []
    quality_boundary_margin_loss_values: list[float] = []
    quality_prewindow_logit_margin_values: list[float] = []
    quality_prewindow_margin_loss_values: list[float] = []
    window_balanced_bce_loss_values: list[float] = []
    prewindow_hazard_mean_values: list[float] = []
    prewindow_hazard_max_values: list[float] = []
    prewindow_hazard_target_values: list[float] = []
    prewindow_hazard_scale_loss_values: list[float] = []
    quality_hazard_target_values: list[float] = []
    quality_hazard_target_loss_values: list[float] = []
    prewindow_logit_ceiling_values: list[float] = []
    prewindow_logit_ceiling_loss_values: list[float] = []
    quality_logit_floor_values: list[float] = []
    quality_logit_floor_loss_values: list[float] = []
    lambda_values: list[float] = []

    group_count = len(groups)
    active_group_count = 0
    skipped_group_count = 0
    unsupported_group_count = 0
    row_count = 0
    active_row_count = 0
    window_group_count = 0
    no_window_group_count = 0
    early_prefix_group_count = 0
    right_censor_group_count = 0
    boundary_cross_count = 0
    boundary_cross_in_window_count = 0
    closed_mask_stop_attempt_count = 0

    prefix_budget = early_mass_budget if prefix_early_mass_budget is None else prefix_early_mass_budget
    eps_value = float(max(eps, 1.0e-12))

    for group in groups:
        prepared = _prepare_group(group)
        row_count += int(prepared.logits.numel())
        if prepared.censoring_kind == M3S1_CENSOR_UNSUPPORTED:
            unsupported_group_count += 1
            skipped_group_count += 1
            continue

        supported = prepared.support_mask
        supported_count = int(supported.sum().detach().cpu().item())
        if supported_count <= 0:
            skipped_group_count += 1
            continue

        supported_logits = prepared.logits[supported]
        supported_legal = prepared.legal_mask[supported]
        supported_quality = prepared.quality_mask[supported]
        supported_steps = prepared.step_indices[supported]
        supported_accepted = prepared.accepted_event[supported]
        legal_count = int(supported_legal.sum().detach().cpu().item())
        active_row_count += legal_count

        boundary = supported_logits >= float(boundary_threshold)
        boundary_cross_count += int((boundary & supported_legal).sum().detach().cpu().item())
        boundary_cross_in_window_count += int(
            (boundary & supported_legal & supported_quality).sum().detach().cpu().item()
        )
        closed_mask_stop_attempt_count += int((boundary & ~supported_legal).sum().detach().cpu().item())
        if legal_count <= 0:
            skipped_group_count += 1
            continue
        active_group_count += 1

        if prepared.censoring_kind == M3S1_CENSOR_EARLY_EVENT_PREFIX:
            early_prefix_group_count += 1
            tau_pos = _first_tau_position(supported_steps, supported_accepted, prepared.censor_step)
            before_tau = th.arange(supported_count, device=supported_logits.device) < tau_pos
            group_loss, p_early, p_none, lambda_mean = _early_prefix_loss(
                supported_logits,
                supported_legal,
                before_tau,
                early_mass_coef=float(early_mass_coef),
                early_mass_budget=float(prefix_budget),
                early_survival_coef=float(early_survival_coef),
                eps=eps_value,
            )
            group_losses.append(group_loss)
            p_window_values.append(0.0)
            p_early_values.append(p_early)
            p_none_values.append(p_none)
            p_deadline_values.append(0.0)
            quality_delay_values.append(0.0)
            quality_boundary_logit_values.append(0.0)
            quality_boundary_margin_loss_values.append(0.0)
            quality_prewindow_logit_margin_values.append(0.0)
            quality_prewindow_margin_loss_values.append(0.0)
            window_balanced_bce_loss_values.append(0.0)
            prewindow_hazard_mean_values.append(0.0)
            prewindow_hazard_max_values.append(0.0)
            prewindow_hazard_target_values.append(0.0)
            prewindow_hazard_scale_loss_values.append(0.0)
            quality_hazard_target_values.append(0.0)
            quality_hazard_target_loss_values.append(0.0)
            prewindow_logit_ceiling_values.append(0.0)
            prewindow_logit_ceiling_loss_values.append(0.0)
            quality_logit_floor_values.append(0.0)
            quality_logit_floor_loss_values.append(0.0)
            lambda_values.append(lambda_mean)
            continue

        if prepared.censoring_kind in (M3S1_CENSOR_FORCED_HOLD, M3S1_CENSOR_TIMEOUT):
            right_censor_group_count += 1

        executable_quality = supported_quality & supported_legal
        has_window = bool(executable_quality.any().detach().cpu().item())
        (
            group_loss,
            p_window,
            p_early,
            p_none,
            p_deadline,
            quality_delay,
            quality_boundary_logit,
            quality_boundary_margin_loss,
            quality_prewindow_logit_margin,
            quality_prewindow_margin_loss,
            window_balanced_bce_loss,
            prewindow_hazard_mean,
            prewindow_hazard_max,
            prewindow_hazard_target,
            prewindow_hazard_scale_loss,
            quality_hazard_target,
            quality_hazard_target_loss,
            prewindow_logit_ceiling,
            prewindow_logit_ceiling_loss,
            quality_logit_floor,
            quality_logit_floor_loss,
            lambda_mean,
        ) = _window_or_no_event_loss(
            supported_logits,
            supported_legal,
            executable_quality,
            has_window=has_window,
            early_mass_coef=float(early_mass_coef),
            early_mass_budget=float(early_mass_budget),
            early_survival_coef=float(early_survival_coef),
            no_event_coef=float(no_event_coef),
            window_delay_coef=float(window_delay_coef),
            window_deadline_coef=float(window_deadline_coef),
            window_deadline_steps=int(window_deadline_steps),
            window_quality_boundary_coef=float(window_quality_boundary_coef),
            window_quality_boundary_logit=float(window_quality_boundary_logit),
            window_contrastive_margin_coef=float(window_contrastive_margin_coef),
            window_contrastive_margin=float(window_contrastive_margin),
            window_balanced_bce_coef=float(window_balanced_bce_coef),
            window_prewindow_hazard_scale_coef=float(window_prewindow_hazard_scale_coef),
            window_prewindow_hazard_target=float(window_prewindow_hazard_target),
            window_quality_hazard_target_coef=float(window_quality_hazard_target_coef),
            window_quality_hazard_target=float(window_quality_hazard_target),
            window_prewindow_logit_ceiling_coef=float(window_prewindow_logit_ceiling_coef),
            window_prewindow_logit_ceiling=float(window_prewindow_logit_ceiling),
            window_quality_logit_floor_coef=float(window_quality_logit_floor_coef),
            window_quality_logit_floor=float(window_quality_logit_floor),
            eps=eps_value,
        )
        group_losses.append(group_loss)
        p_window_values.append(p_window)
        p_early_values.append(p_early)
        p_none_values.append(p_none)
        p_deadline_values.append(p_deadline)
        quality_delay_values.append(quality_delay)
        quality_boundary_logit_values.append(quality_boundary_logit)
        quality_boundary_margin_loss_values.append(quality_boundary_margin_loss)
        quality_prewindow_logit_margin_values.append(quality_prewindow_logit_margin)
        quality_prewindow_margin_loss_values.append(quality_prewindow_margin_loss)
        window_balanced_bce_loss_values.append(window_balanced_bce_loss)
        prewindow_hazard_mean_values.append(prewindow_hazard_mean)
        prewindow_hazard_max_values.append(prewindow_hazard_max)
        prewindow_hazard_target_values.append(prewindow_hazard_target)
        prewindow_hazard_scale_loss_values.append(prewindow_hazard_scale_loss)
        quality_hazard_target_values.append(quality_hazard_target)
        quality_hazard_target_loss_values.append(quality_hazard_target_loss)
        prewindow_logit_ceiling_values.append(prewindow_logit_ceiling)
        prewindow_logit_ceiling_loss_values.append(prewindow_logit_ceiling_loss)
        quality_logit_floor_values.append(quality_logit_floor)
        quality_logit_floor_loss_values.append(quality_logit_floor_loss)
        lambda_values.append(lambda_mean)
        if has_window:
            window_group_count += 1
        else:
            no_window_group_count += 1

    if group_losses:
        unscaled = th.stack(group_losses).mean()
    else:
        unscaled = zero_base
    loss = float(coef) * unscaled if float(coef) > 0.0 else zero_base
    loss_values = [float(value.detach().cpu().item()) for value in group_losses]
    stats = M3S1GroupedStoppingStats(
        group_count=group_count,
        active_group_count=active_group_count,
        skipped_group_count=skipped_group_count,
        unsupported_group_count=unsupported_group_count,
        row_count=row_count,
        active_row_count=active_row_count,
        window_group_count=window_group_count,
        no_window_group_count=no_window_group_count,
        early_prefix_group_count=early_prefix_group_count,
        right_censor_group_count=right_censor_group_count,
        boundary_cross_count=boundary_cross_count,
        boundary_cross_in_window_count=boundary_cross_in_window_count,
        closed_mask_stop_attempt_count=closed_mask_stop_attempt_count,
        mean_p_window=_mean(p_window_values),
        mean_p_early=_mean(p_early_values),
        mean_p_none=_mean(p_none_values),
        mean_lambda=_mean(lambda_values),
        mean_p_deadline=_mean(p_deadline_values),
        mean_quality_delay=_mean(quality_delay_values),
        mean_quality_boundary_logit=_mean(quality_boundary_logit_values),
        mean_quality_boundary_margin_loss=_mean(quality_boundary_margin_loss_values),
        mean_quality_prewindow_logit_margin=_mean(quality_prewindow_logit_margin_values),
        mean_quality_prewindow_margin_loss=_mean(quality_prewindow_margin_loss_values),
        mean_window_balanced_bce_loss=_mean(window_balanced_bce_loss_values),
        mean_prewindow_hazard_mean=_mean(prewindow_hazard_mean_values),
        mean_prewindow_hazard_max=_mean(prewindow_hazard_max_values),
        mean_prewindow_hazard_target=_mean(prewindow_hazard_target_values),
        mean_prewindow_hazard_scale_loss=_mean(prewindow_hazard_scale_loss_values),
        mean_quality_hazard_target=_mean(quality_hazard_target_values),
        mean_quality_hazard_target_loss=_mean(quality_hazard_target_loss_values),
        mean_prewindow_logit_ceiling=_mean(prewindow_logit_ceiling_values),
        mean_prewindow_logit_ceiling_loss=_mean(prewindow_logit_ceiling_loss_values),
        mean_quality_logit_floor=_mean(quality_logit_floor_values),
        mean_quality_logit_floor_loss=_mean(quality_logit_floor_loss_values),
        mean_loss=_mean(loss_values),
        max_group_loss=max(loss_values) if loss_values else 0.0,
    )
    return M3S1GroupedStoppingLoss(loss=loss, unscaled_loss=unscaled.detach(), stats=stats)


@dataclass(frozen=True)
class _PreparedGroup:
    logits: th.Tensor
    row_indices: th.Tensor
    step_indices: th.Tensor
    env_indices: th.Tensor
    legal_mask: th.Tensor
    quality_mask: th.Tensor
    accepted_event: th.Tensor
    support_mask: th.Tensor
    censoring_kind: str
    censor_step: int | None


def _prepare_group(group: M3S1GroupedStoppingEvidence) -> _PreparedGroup:
    logits = group.stopping_logits.reshape(-1)
    if not th.is_floating_point(logits):
        logits = logits.to(dtype=th.float32)
    if not bool(th.isfinite(logits).all().detach().cpu().item()):
        raise ValueError("M3-S1 stopping logits must be finite")
    device = logits.device
    row_indices = _as_long_tensor(group.row_indices, device=device)
    step_indices = _as_long_tensor(group.step_indices, device=device)
    env_indices = _as_long_tensor(group.env_indices, device=device)
    legal_mask = _as_bool_tensor(group.legal_mask, device=device)
    quality_mask = _as_bool_tensor(group.quality_mask, device=device)
    accepted_event = (
        th.zeros_like(legal_mask, dtype=th.bool)
        if group.accepted_event is None
        else _as_bool_tensor(group.accepted_event, device=device)
    )
    lengths = {
        int(logits.numel()),
        int(row_indices.numel()),
        int(step_indices.numel()),
        int(env_indices.numel()),
        int(legal_mask.numel()),
        int(quality_mask.numel()),
        int(accepted_event.numel()),
    }
    if len(lengths) != 1:
        raise ValueError("M3-S1 grouped stopping evidence fields must have the same flattened length")

    support_mask = th.ones_like(legal_mask, dtype=th.bool)
    if group.support_horizon is not None:
        support_mask = support_mask & (row_indices <= int(group.support_horizon))
    if group.censor_step is not None and group.censoring_kind != M3S1_CENSOR_EARLY_EVENT_PREFIX:
        support_mask = support_mask & (step_indices <= int(group.censor_step))

    if int(logits.numel()) > 0:
        env_stride = max(1, int(env_indices.max().detach().cpu().item()) + 1)
        order = th.argsort(step_indices * env_stride + env_indices)
    else:
        order = th.empty((0,), dtype=th.long, device=device)
    return _PreparedGroup(
        logits=logits[order],
        row_indices=row_indices[order],
        step_indices=step_indices[order],
        env_indices=env_indices[order],
        legal_mask=legal_mask[order],
        quality_mask=quality_mask[order],
        accepted_event=accepted_event[order],
        support_mask=support_mask[order],
        censoring_kind=str(group.censoring_kind),
        censor_step=group.censor_step,
    )


def _window_or_no_event_loss(
    logits: th.Tensor,
    legal_mask: th.Tensor,
    quality_mask: th.Tensor,
    *,
    has_window: bool,
    early_mass_coef: float,
    early_mass_budget: float,
    early_survival_coef: float,
    no_event_coef: float,
    window_delay_coef: float,
    window_deadline_coef: float,
    window_deadline_steps: int,
    window_quality_boundary_coef: float,
    window_quality_boundary_logit: float,
    window_contrastive_margin_coef: float,
    window_contrastive_margin: float,
    window_balanced_bce_coef: float,
    window_prewindow_hazard_scale_coef: float,
    window_prewindow_hazard_target: float,
    window_quality_hazard_target_coef: float,
    window_quality_hazard_target: float,
    window_prewindow_logit_ceiling_coef: float,
    window_prewindow_logit_ceiling: float,
    window_quality_logit_floor_coef: float,
    window_quality_logit_floor: float,
    eps: float,
) -> tuple[
    th.Tensor,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
]:
    hazard, event_mass, p_none, log_survival_before, log_event_mass, log_p_none = _hazard_event_mass(
        logits,
        legal_mask,
    )
    p_deadline_value = 0.0
    quality_delay_value = 0.0
    quality_boundary_logit_value = 0.0
    quality_boundary_margin_loss_value = 0.0
    quality_prewindow_logit_margin_value = 0.0
    quality_prewindow_margin_loss_value = 0.0
    window_balanced_bce_loss_value = 0.0
    prewindow_hazard_mean_value = 0.0
    prewindow_hazard_max_value = 0.0
    prewindow_hazard_target_value = 0.0
    prewindow_hazard_scale_loss_value = 0.0
    quality_hazard_target_value = 0.0
    quality_hazard_target_loss_value = 0.0
    prewindow_logit_ceiling_value = 0.0
    prewindow_logit_ceiling_loss_value = 0.0
    quality_logit_floor_value = 0.0
    quality_logit_floor_loss_value = 0.0
    if has_window:
        first_quality_pos = int(th.nonzero(quality_mask, as_tuple=False).flatten()[0].detach().cpu().item())
        positions = th.arange(int(logits.numel()), device=logits.device)
        early_mask = (~quality_mask) & (positions < first_quality_pos) & legal_mask
        log_p_window_tensor = th.logsumexp(log_event_mass[quality_mask], dim=0)
        p_window_tensor = th.exp(log_p_window_tensor)
        if bool(early_mask.any().detach().cpu().item()):
            log_survival_to_window = log_survival_before[first_quality_pos]
            p_early_tensor = -th.expm1(log_survival_to_window)
        else:
            log_survival_to_window = logits.new_zeros((), dtype=log_event_mass.dtype)
            p_early_tensor = logits.new_zeros((), dtype=log_event_mass.dtype)
        early_penalty = th.clamp(p_early_tensor - float(early_mass_budget), min=0.0).pow(2)
        loss = -log_p_window_tensor + float(early_mass_coef) * early_penalty
        if float(early_survival_coef) > 0.0:
            loss = loss + float(early_survival_coef) * -log_survival_to_window
        quality_positions = th.nonzero(quality_mask, as_tuple=False).flatten()
        quality_count = int(quality_positions.numel())
        if quality_count > 0 and float(window_delay_coef) > 0.0:
            ranks = th.arange(quality_count, device=logits.device, dtype=logits.dtype)
            denom = float(max(1, quality_count - 1))
            normalized_delay = ranks / denom
            quality_weights = th.exp(log_event_mass[quality_positions] - log_p_window_tensor)
            expected_delay = (quality_weights.to(dtype=logits.dtype) * normalized_delay).sum()
            loss = loss + float(window_delay_coef) * expected_delay
            quality_delay_value = float(expected_delay.detach().cpu().item())
        if quality_count > 0 and float(window_deadline_coef) > 0.0 and int(window_deadline_steps) > 0:
            deadline_count = min(quality_count, int(window_deadline_steps))
            deadline_positions = quality_positions[:deadline_count]
            log_p_deadline_tensor = th.logsumexp(log_event_mass[deadline_positions], dim=0)
            p_deadline_tensor = th.exp(log_p_deadline_tensor)
            loss = loss + float(window_deadline_coef) * -log_p_deadline_tensor
            p_deadline_value = float(p_deadline_tensor.detach().cpu().item())
        if quality_count > 0:
            quality_logits = logits[quality_mask]
            quality_anchor = quality_logits.max()
            quality_boundary_margin_loss = th.clamp(
                float(window_quality_boundary_logit) - quality_anchor,
                min=0.0,
            )
            if float(window_quality_boundary_coef) > 0.0:
                loss = loss + float(window_quality_boundary_coef) * quality_boundary_margin_loss
            quality_boundary_logit_value = float(quality_anchor.detach().cpu().item())
            quality_boundary_margin_loss_value = float(quality_boundary_margin_loss.detach().cpu().item())
            quality_hazard_target_value = _bounded_probability(float(window_quality_hazard_target), eps=eps)
            quality_target_logit = _probability_logit(quality_hazard_target_value, eps=eps)
            quality_hazard_target_loss = th.clamp(quality_target_logit - quality_anchor, min=0.0).pow(2)
            if float(window_quality_hazard_target_coef) > 0.0:
                loss = loss + float(window_quality_hazard_target_coef) * quality_hazard_target_loss
            quality_hazard_target_loss_value = float(quality_hazard_target_loss.detach().cpu().item())
            quality_logit_floor_loss = th.clamp(float(window_quality_logit_floor) - quality_logits, min=0.0).pow(2).mean()
            if float(window_quality_logit_floor_coef) > 0.0:
                loss = loss + float(window_quality_logit_floor_coef) * quality_logit_floor_loss
            quality_logit_floor_value = float(quality_logits.min().detach().cpu().item())
            quality_logit_floor_loss_value = float(quality_logit_floor_loss.detach().cpu().item())
        if bool(early_mask.any().detach().cpu().item()):
            prewindow_anchor = logits[early_mask].max()
            quality_prewindow_margin = quality_anchor - prewindow_anchor
            margin_loss = th.clamp(float(window_contrastive_margin) - quality_prewindow_margin, min=0.0)
            if float(window_contrastive_margin_coef) > 0.0:
                loss = loss + float(window_contrastive_margin_coef) * margin_loss
            quality_prewindow_logit_margin_value = float(quality_prewindow_margin.detach().cpu().item())
            quality_prewindow_margin_loss_value = float(margin_loss.detach().cpu().item())
            prewindow_hazard = hazard[early_mask].to(dtype=logits.dtype)
            prewindow_hazard_mean_value = float(prewindow_hazard.mean().detach().cpu().item())
            prewindow_hazard_max_value = float(prewindow_hazard.max().detach().cpu().item())
            prewindow_hazard_target_value = _prewindow_hazard_target(
                explicit_target=float(window_prewindow_hazard_target),
                early_mass_budget=float(early_mass_budget),
                prewindow_count=int(prewindow_hazard.numel()),
                eps=eps,
            )
            prewindow_target_logit = _probability_logit(prewindow_hazard_target_value, eps=eps)
            prewindow_hazard_scale_loss = th.clamp(logits[early_mask] - prewindow_target_logit, min=0.0).pow(2).mean()
            if float(window_prewindow_hazard_scale_coef) > 0.0:
                loss = loss + float(window_prewindow_hazard_scale_coef) * prewindow_hazard_scale_loss
            prewindow_hazard_scale_loss_value = float(prewindow_hazard_scale_loss.detach().cpu().item())
            prewindow_logit_ceiling_loss = th.clamp(
                logits[early_mask] - float(window_prewindow_logit_ceiling),
                min=0.0,
            ).pow(2).mean()
            if float(window_prewindow_logit_ceiling_coef) > 0.0:
                loss = loss + float(window_prewindow_logit_ceiling_coef) * prewindow_logit_ceiling_loss
            prewindow_logit_ceiling_value = float(prewindow_anchor.detach().cpu().item())
            prewindow_logit_ceiling_loss_value = float(prewindow_logit_ceiling_loss.detach().cpu().item())
        bce_mask = (early_mask | quality_mask) & legal_mask
        if float(window_balanced_bce_coef) > 0.0 and bool(bce_mask.any().detach().cpu().item()):
            bce_logits = logits[bce_mask]
            bce_labels = quality_mask[bce_mask].to(dtype=logits.dtype)
            pos_count = bce_labels.sum()
            neg_count = bce_labels.numel() - pos_count
            if bool((pos_count > 0.0).detach().cpu().item()) and bool((neg_count > 0.0).detach().cpu().item()):
                pos_weight = 0.5 / pos_count.clamp_min(1.0)
                neg_weight = 0.5 / neg_count.clamp_min(1.0)
                weights = th.where(bce_labels > 0.5, pos_weight, neg_weight)
                bce_loss = th.nn.functional.binary_cross_entropy_with_logits(
                    bce_logits,
                    bce_labels,
                    weight=weights,
                    reduction="sum",
                )
                loss = loss + float(window_balanced_bce_coef) * bce_loss
                window_balanced_bce_loss_value = float(bce_loss.detach().cpu().item())
    else:
        p_window_tensor = event_mass.sum() * 0.0
        p_early_tensor = -th.expm1(log_p_none)
        loss = float(no_event_coef) * -log_p_none
    return (
        loss,
        float(p_window_tensor.detach().cpu().item()),
        float(p_early_tensor.detach().cpu().item()),
        float(p_none.detach().cpu().item()),
        p_deadline_value,
        quality_delay_value,
        quality_boundary_logit_value,
        quality_boundary_margin_loss_value,
        quality_prewindow_logit_margin_value,
        quality_prewindow_margin_loss_value,
        window_balanced_bce_loss_value,
        prewindow_hazard_mean_value,
        prewindow_hazard_max_value,
        prewindow_hazard_target_value,
        prewindow_hazard_scale_loss_value,
        quality_hazard_target_value,
        quality_hazard_target_loss_value,
        prewindow_logit_ceiling_value,
        prewindow_logit_ceiling_loss_value,
        quality_logit_floor_value,
        quality_logit_floor_loss_value,
        float(hazard.mean().detach().cpu().item()) if int(hazard.numel()) > 0 else 0.0,
    )


def _early_prefix_loss(
    logits: th.Tensor,
    legal_mask: th.Tensor,
    before_tau: th.Tensor,
    *,
    early_mass_coef: float,
    early_mass_budget: float,
    early_survival_coef: float,
    eps: float,
) -> tuple[th.Tensor, float, float, float]:
    tau_logits = logits[before_tau]
    tau_legal = legal_mask[before_tau]
    hazard, event_mass, p_none, _, _, log_p_none = _hazard_event_mass(tau_logits, tau_legal)
    survival_to_tau = p_none
    p_early_tensor = -th.expm1(log_p_none)
    early_penalty = th.clamp(p_early_tensor - float(early_mass_budget), min=0.0).pow(2)
    loss = -log_p_none + float(early_mass_coef) * early_penalty
    if float(early_survival_coef) > 0.0:
        loss = loss + float(early_survival_coef) * -log_p_none
    return (
        loss,
        float(p_early_tensor.detach().cpu().item()),
        float(survival_to_tau.detach().cpu().item()),
        float(hazard.mean().detach().cpu().item()) if int(hazard.numel()) > 0 else 0.0,
    )


def _hazard_event_mass(
    logits: th.Tensor,
    legal_mask: th.Tensor,
) -> tuple[th.Tensor, th.Tensor, th.Tensor, th.Tensor, th.Tensor, th.Tensor]:
    work_logits = logits.to(dtype=th.float64)
    work_legal = legal_mask.to(device=logits.device, dtype=work_logits.dtype)
    hazard = th.sigmoid(work_logits) * work_legal
    hazard = hazard.clamp(min=0.0, max=1.0 - 1.0e-7)
    log_survival_after = th.cumsum(th.log1p(-hazard), dim=0)
    zero = work_logits.new_zeros((1,))
    log_survival_before = th.cat((zero, log_survival_after[:-1]), dim=0)
    neg_inf = work_logits.new_full(hazard.shape, -th.inf)
    log_hazard = th.where(hazard > 0.0, th.log(hazard.clamp_min(th.finfo(work_logits.dtype).tiny)), neg_inf)
    log_event_mass = log_survival_before + log_hazard
    event_mass = th.exp(log_event_mass)
    log_p_none = log_survival_after[-1] if int(logits.numel()) > 0 else work_logits.sum() * 0.0
    p_none = th.exp(log_p_none)
    return hazard, event_mass, p_none, log_survival_before, log_event_mass, log_p_none


def _bounded_probability(value: float, *, eps: float) -> float:
    eps_value = float(max(eps, 1.0e-12))
    return float(min(max(float(value), eps_value), 1.0 - eps_value))


def _probability_logit(value: float, *, eps: float) -> float:
    probability = _bounded_probability(value, eps=eps)
    return float(math.log(probability) - math.log1p(-probability))


def _prewindow_hazard_target(
    *,
    explicit_target: float,
    early_mass_budget: float,
    prewindow_count: int,
    eps: float,
) -> float:
    if float(explicit_target) > 0.0:
        return _bounded_probability(float(explicit_target), eps=eps)
    if int(prewindow_count) <= 0:
        return 0.0
    budget = _bounded_probability(float(early_mass_budget), eps=eps)
    per_step = 1.0 - math.exp(math.log1p(-budget) / float(max(1, int(prewindow_count))))
    return _bounded_probability(per_step, eps=eps)


def _first_tau_position(steps: th.Tensor, accepted_event: th.Tensor, censor_step: int | None) -> int:
    accepted_positions = th.nonzero(accepted_event, as_tuple=False).flatten()
    if int(accepted_positions.numel()) > 0:
        return int(accepted_positions[0].detach().cpu().item())
    if censor_step is None:
        return int(steps.numel())
    censor_positions = th.nonzero(steps >= int(censor_step), as_tuple=False).flatten()
    if int(censor_positions.numel()) > 0:
        return int(censor_positions[0].detach().cpu().item())
    return int(steps.numel())


def _as_long_tensor(values: Sequence[int] | th.Tensor, *, device: th.device) -> th.Tensor:
    return th.as_tensor(values, device=device).reshape(-1).to(dtype=th.long)


def _as_bool_tensor(values: Sequence[bool] | th.Tensor, *, device: th.device) -> th.Tensor:
    return th.as_tensor(values, device=device).reshape(-1).to(dtype=th.bool)


def _zero_like_group_logits(groups: Sequence[M3S1GroupedStoppingEvidence]) -> th.Tensor:
    for group in groups:
        logits = group.stopping_logits
        if th.is_tensor(logits):
            return logits.reshape(-1).sum() * 0.0
    return th.zeros((), dtype=th.float32)


def _mean(values: Sequence[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.0
