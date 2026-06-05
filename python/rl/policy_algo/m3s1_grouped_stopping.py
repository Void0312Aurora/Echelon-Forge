from __future__ import annotations

from dataclasses import dataclass
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
    prefix_early_mass_budget: float | None = None,
    no_event_coef: float = 1.0,
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
                eps=eps_value,
            )
            group_losses.append(group_loss)
            p_window_values.append(0.0)
            p_early_values.append(p_early)
            p_none_values.append(p_none)
            lambda_values.append(lambda_mean)
            continue

        if prepared.censoring_kind in (M3S1_CENSOR_FORCED_HOLD, M3S1_CENSOR_TIMEOUT):
            right_censor_group_count += 1

        executable_quality = supported_quality & supported_legal
        has_window = bool(executable_quality.any().detach().cpu().item())
        group_loss, p_window, p_early, p_none, lambda_mean = _window_or_no_event_loss(
            supported_logits,
            supported_legal,
            executable_quality,
            has_window=has_window,
            early_mass_coef=float(early_mass_coef),
            early_mass_budget=float(early_mass_budget),
            no_event_coef=float(no_event_coef),
            eps=eps_value,
        )
        group_losses.append(group_loss)
        p_window_values.append(p_window)
        p_early_values.append(p_early)
        p_none_values.append(p_none)
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
    no_event_coef: float,
    eps: float,
) -> tuple[th.Tensor, float, float, float, float]:
    hazard, event_mass, p_none = _hazard_event_mass(logits, legal_mask)
    if has_window:
        first_quality_pos = int(th.nonzero(quality_mask, as_tuple=False).flatten()[0].detach().cpu().item())
        positions = th.arange(int(logits.numel()), device=logits.device)
        early_mask = (~quality_mask) & (positions < first_quality_pos)
        p_window_tensor = event_mass[quality_mask].sum()
        p_early_tensor = event_mass[early_mask].sum()
        early_penalty = th.clamp(p_early_tensor - float(early_mass_budget), min=0.0).pow(2)
        loss = -th.log(p_window_tensor.clamp_min(eps)) + float(early_mass_coef) * early_penalty
    else:
        p_window_tensor = event_mass.sum() * 0.0
        p_early_tensor = event_mass.sum()
        loss = float(no_event_coef) * -th.log(p_none.clamp_min(eps))
    return (
        loss,
        float(p_window_tensor.detach().cpu().item()),
        float(p_early_tensor.detach().cpu().item()),
        float(p_none.detach().cpu().item()),
        float(hazard.mean().detach().cpu().item()) if int(hazard.numel()) > 0 else 0.0,
    )


def _early_prefix_loss(
    logits: th.Tensor,
    legal_mask: th.Tensor,
    before_tau: th.Tensor,
    *,
    early_mass_coef: float,
    early_mass_budget: float,
    eps: float,
) -> tuple[th.Tensor, float, float, float]:
    tau_logits = logits[before_tau]
    tau_legal = legal_mask[before_tau]
    hazard, event_mass, p_none = _hazard_event_mass(tau_logits, tau_legal)
    survival_to_tau = p_none
    p_early_tensor = event_mass.sum()
    early_penalty = th.clamp(p_early_tensor - float(early_mass_budget), min=0.0).pow(2)
    loss = -th.log(survival_to_tau.clamp_min(eps)) + float(early_mass_coef) * early_penalty
    return (
        loss,
        float(p_early_tensor.detach().cpu().item()),
        float(survival_to_tau.detach().cpu().item()),
        float(hazard.mean().detach().cpu().item()) if int(hazard.numel()) > 0 else 0.0,
    )


def _hazard_event_mass(logits: th.Tensor, legal_mask: th.Tensor) -> tuple[th.Tensor, th.Tensor, th.Tensor]:
    hazard = th.sigmoid(logits) * legal_mask.to(device=logits.device, dtype=logits.dtype)
    hazard = hazard.clamp(min=0.0, max=1.0 - 1.0e-7)
    log_survival_after = th.cumsum(th.log1p(-hazard), dim=0)
    zero = logits.new_zeros((1,))
    log_survival_before = th.cat((zero, log_survival_after[:-1]), dim=0)
    event_mass = th.exp(log_survival_before) * hazard
    p_none = th.exp(log_survival_after[-1]) if int(logits.numel()) > 0 else logits.sum() * 0.0 + 1.0
    return hazard, event_mass, p_none


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
