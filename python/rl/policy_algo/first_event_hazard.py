from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import torch as th
from torch.nn import functional as F


A6_FIRST_EVENT_FIELD_ACTIVE = "a6_first_event_active"
A6_FIRST_EVENT_FIELD_TARGET = "a6_first_event_target"
A6_FIRST_EVENT_FIELD_WEIGHT = "a6_first_event_weight"
A6_FIRST_EVENT_FIELD_SOURCE = "a6_first_event_source"
A6_FIRST_EVENT_FIELD_WINDOW_AGE = "a6_first_event_window_age"
A6_FIRST_EVENT_FIELD_WINDOW_ID = "a6_first_event_window_id"
A6_FIRST_EVENT_FIELD_HAD_ACCEPTED = "a6_first_event_had_accepted"
A6_FIRST_EVENT_FIELD_NAMES = (
    A6_FIRST_EVENT_FIELD_ACTIVE,
    A6_FIRST_EVENT_FIELD_TARGET,
    A6_FIRST_EVENT_FIELD_WEIGHT,
    A6_FIRST_EVENT_FIELD_SOURCE,
    A6_FIRST_EVENT_FIELD_WINDOW_AGE,
    A6_FIRST_EVENT_FIELD_WINDOW_ID,
    A6_FIRST_EVENT_FIELD_HAD_ACCEPTED,
)

A6_FIRST_EVENT_SOURCE_INACTIVE = 0
A6_FIRST_EVENT_SOURCE_ACCEPTED = 1
A6_FIRST_EVENT_SOURCE_CURRICULUM = 2
A6_FIRST_EVENT_SOURCE_CENSORED = 3
A6_FIRST_EVENT_SOURCE_DEADLINE = 4
A6_FIRST_EVENT_SOURCE_PREWINDOW = 5
A6_FIRST_EVENT_SOURCE_EARLY_ACCEPTED = 6
A6_FIRST_EVENT_SOURCE_SHADOW_QUALITY = 7
A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY = 8


@dataclass(frozen=True)
class FirstEventHazardLabels:
    active: th.Tensor
    target: th.Tensor
    weight: th.Tensor
    source: th.Tensor
    window_age: th.Tensor
    window_id: th.Tensor
    had_accepted: th.Tensor


@dataclass(frozen=True)
class FirstEventHazardLoss:
    loss: th.Tensor
    unscaled_loss: th.Tensor
    active_count: int
    positive_count: int
    weight_sum: float
    positive_frac: float


@dataclass(frozen=True)
class FirstEventCreditLoss:
    loss: th.Tensor
    value_loss: th.Tensor
    delta_align_loss: th.Tensor
    unscaled_value_loss: th.Tensor
    unscaled_delta_align_loss: th.Tensor
    active_count: int
    positive_count: int
    weight_sum: float
    positive_frac: float
    advantage_mean: float
    advantage_abs_mean: float
    projection_active_count: int = 0
    projection_candidate_count: int = 0
    projection_unsupported_count: int = 0
    projection_advantage_mean: float = 0.0
    projection_delta_mean: float = 0.0
    source_shadow_count: int = 0
    source_deadline_count: int = 0
    source_early_accepted_count: int = 0
    source_prewindow_count: int = 0
    source_legal_open_quality_count: int = 0
    source_legal_open_quality_positive_count: int = 0
    source_deadline_positive_count: int = 0
    source_shadow_positive_count: int = 0
    source_legal_open_quality_advantage_mean: float = 0.0


def current_first_event_curriculum_coef(
    initial_coef: float,
    progress_remaining: float,
    *,
    decay_completed_fraction: float = 0.25,
) -> float:
    initial = float(max(0.0, initial_coef))
    if initial <= 0.0:
        return 0.0
    decay_fraction = float(max(0.0, decay_completed_fraction))
    if decay_fraction <= 0.0:
        return 0.0
    progress = float(min(max(progress_remaining, 0.0), 1.0))
    completed = 1.0 - progress
    if completed >= decay_fraction:
        return 0.0
    return initial * max(0.0, 1.0 - completed / decay_fraction)


def _as_bool_list(values: Sequence[Any] | th.Tensor, *, default_len: int | None = None) -> list[bool]:
    if values is None:
        if default_len is None:
            return []
        return [False] * int(default_len)
    if th.is_tensor(values):
        return [bool(v) for v in values.detach().cpu().reshape(-1).tolist()]
    return [bool(v) for v in values]


def _as_episode_ids(values: Sequence[Any] | th.Tensor | None, count: int) -> list[int]:
    if values is None:
        return [0] * int(count)
    if th.is_tensor(values):
        return [int(v) for v in values.detach().cpu().reshape(-1).tolist()]
    return [int(v) for v in values]


def _is_authorized_ready(value: Any) -> bool:
    return str(value) == "AuthorizedReady"


def build_first_event_hazard_labels(
    *,
    engagement_state: Sequence[Any],
    fire_mask: Sequence[Any] | th.Tensor,
    fire_once_accepted: Sequence[Any] | th.Tensor | None = None,
    episode_id: Sequence[Any] | th.Tensor | None = None,
    launch_window_open: Sequence[Any] | th.Tensor | None = None,
    launch_window_min_window_age_steps: int = 1,
    launch_window_prewindow_hold_weight: float = 0.0,
    launch_window_early_accept_weight: float = 1.0,
    curriculum_weight: float = 0.0,
    curriculum_min_window_age_steps: int = 32,
    curriculum_blocked_episode_ids: Sequence[int] | set[int] | None = None,
    censored_survival_weight: float = 0.0,
    deadline_weight: float = 0.0,
    deadline_min_window_age_steps: int = 96,
    shadow_quality_after_early_accept: bool = False,
    shadow_quality_positive_weight: float = 0.0,
    legal_open_quality_weight: float = 0.0,
    legal_open_quality_min_window_age_steps: int = 1,
    device: th.device | str | None = None,
) -> FirstEventHazardLabels:
    states = list(engagement_state)
    count = len(states)
    fire_open = _as_bool_list(fire_mask)
    accepted = _as_bool_list(fire_once_accepted, default_len=count)
    episodes = _as_episode_ids(episode_id, count)
    launch_gate_enabled = launch_window_open is not None
    launch_open = _as_bool_list(launch_window_open, default_len=count) if launch_gate_enabled else [True] * count
    if not (len(fire_open) == len(accepted) == len(episodes) == len(launch_open) == count):
        raise ValueError("A6 first-event label inputs must have the same flattened length")

    active = [False] * count
    target = [0.0] * count
    weight = [0.0] * count
    source = [A6_FIRST_EVENT_SOURCE_INACTIVE] * count
    window_age = [0.0] * count
    window_id = [-1] * count
    had_accepted = [False] * count

    curriculum_weight = float(max(0.0, curriculum_weight))
    min_age = max(1, int(curriculum_min_window_age_steps))
    blocked_curriculum_episodes = {int(value) for value in (curriculum_blocked_episode_ids or [])}
    censored_weight = float(max(0.0, censored_survival_weight))
    deadline_weight = float(max(0.0, deadline_weight))
    deadline_min_age = max(1, int(deadline_min_window_age_steps))
    launch_min_age = max(1, int(launch_window_min_window_age_steps))
    prewindow_hold_weight = float(max(0.0, launch_window_prewindow_hold_weight))
    early_accept_weight = float(max(0.0, launch_window_early_accept_weight))
    shadow_quality_enabled = bool(shadow_quality_after_early_accept and launch_gate_enabled)
    shadow_quality_weight = float(max(0.0, shadow_quality_positive_weight))
    legal_open_quality_weight = float(max(0.0, legal_open_quality_weight))
    legal_open_quality_min_age = max(1, int(legal_open_quality_min_window_age_steps))
    legal_open_quality_enabled = bool(launch_gate_enabled and legal_open_quality_weight > 0.0)
    window_counter = 0

    ordered_episodes: list[int] = []
    seen_episodes: set[int] = set()
    for episode in episodes:
        if episode not in seen_episodes:
            ordered_episodes.append(episode)
            seen_episodes.add(episode)

    for episode in ordered_episodes:
        indices = [idx for idx, value in enumerate(episodes) if value == episode]
        cursor = 0
        episode_has_first_event = False
        curriculum_used = False
        while cursor < len(indices):
            idx = indices[cursor]
            in_first_window = (
                not episode_has_first_event
                and _is_authorized_ready(states[idx])
                and bool(fire_open[idx])
            )
            if not in_first_window:
                cursor += 1
                continue

            start = cursor
            while cursor < len(indices):
                step_idx = indices[cursor]
                if not (_is_authorized_ready(states[step_idx]) and bool(fire_open[step_idx])):
                    break
                cursor += 1
            window_indices = indices[start:cursor]
            current_window_id = window_counter
            window_counter += 1
            for age, step_idx in enumerate(window_indices, start=1):
                window_age[step_idx] = float(age)
                window_id[step_idx] = current_window_id
            quality_open = [
                (not launch_gate_enabled)
                or (bool(launch_open[step_idx]) and window_age[step_idx] >= float(launch_min_age))
                for step_idx in window_indices
            ]

            accepted_positions = [pos for pos, step_idx in enumerate(window_indices) if bool(accepted[step_idx])]
            if accepted_positions:
                tau_pos = int(accepted_positions[0])
                if quality_open[tau_pos]:
                    for pos, step_idx in enumerate(window_indices[: tau_pos + 1]):
                        active[step_idx] = True
                        target[step_idx] = 1.0 if pos == tau_pos else 0.0
                        weight[step_idx] = 1.0
                        source[step_idx] = A6_FIRST_EVENT_SOURCE_ACCEPTED
                        had_accepted[step_idx] = True
                else:
                    for step_idx in window_indices[: tau_pos + 1]:
                        step_is_accepted = bool(accepted[step_idx])
                        negative_weight = (
                            max(prewindow_hold_weight, early_accept_weight)
                            if step_is_accepted
                            else prewindow_hold_weight
                        )
                        active[step_idx] = negative_weight > 0.0
                        target[step_idx] = 0.0
                        weight[step_idx] = negative_weight
                        source[step_idx] = (
                            A6_FIRST_EVENT_SOURCE_EARLY_ACCEPTED
                            if step_is_accepted
                            else A6_FIRST_EVENT_SOURCE_PREWINDOW
                        )
                        had_accepted[step_idx] = True
                    if shadow_quality_enabled and shadow_quality_weight > 0.0:
                        for future_cursor in range(start + tau_pos + 1, len(indices)):
                            future_idx = indices[future_cursor]
                            future_age = float(future_cursor - start + 1)
                            if not (bool(launch_open[future_idx]) and future_age >= float(launch_min_age)):
                                continue
                            active[future_idx] = True
                            target[future_idx] = 1.0
                            weight[future_idx] = shadow_quality_weight
                            source[future_idx] = A6_FIRST_EVENT_SOURCE_SHADOW_QUALITY
                            window_age[future_idx] = future_age
                            window_id[future_idx] = current_window_id
                            had_accepted[future_idx] = True
                episode_has_first_event = True
                continue

            for pos, step_idx in enumerate(window_indices):
                source[step_idx] = A6_FIRST_EVENT_SOURCE_CENSORED
                if censored_weight > 0.0:
                    active[step_idx] = True
                    target[step_idx] = 0.0
                    weight[step_idx] = censored_weight
                if launch_gate_enabled and not quality_open[pos]:
                    source[step_idx] = A6_FIRST_EVENT_SOURCE_PREWINDOW
                    if prewindow_hold_weight > 0.0:
                        active[step_idx] = True
                        target[step_idx] = 0.0
                        weight[step_idx] = prewindow_hold_weight

            if curriculum_weight > 0.0 and not curriculum_used and episode not in blocked_curriculum_episodes:
                seed_pos = next(
                    (
                        pos
                        for pos, step_idx in enumerate(window_indices)
                        if quality_open[pos] and window_age[step_idx] >= float(min_age)
                    ),
                    None,
                )
                if seed_pos is not None:
                    for pos, step_idx in enumerate(window_indices[: seed_pos + 1]):
                        active[step_idx] = True
                        target[step_idx] = 1.0 if pos == seed_pos else 0.0
                        weight[step_idx] = curriculum_weight
                        source[step_idx] = A6_FIRST_EVENT_SOURCE_CURRICULUM
                    curriculum_used = True

            if deadline_weight > 0.0:
                for pos, step_idx in enumerate(window_indices):
                    if not quality_open[pos]:
                        continue
                    if window_age[step_idx] < float(deadline_min_age):
                        continue
                    active[step_idx] = True
                    target[step_idx] = 1.0
                    weight[step_idx] = deadline_weight
                    source[step_idx] = A6_FIRST_EVENT_SOURCE_DEADLINE

            if legal_open_quality_enabled:
                for pos, step_idx in enumerate(window_indices):
                    if not quality_open[pos]:
                        continue
                    if window_age[step_idx] < float(legal_open_quality_min_age):
                        continue
                    active[step_idx] = True
                    target[step_idx] = 1.0
                    weight[step_idx] = legal_open_quality_weight
                    source[step_idx] = A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY

    out_device = th.device(device) if device is not None else th.device("cpu")
    return FirstEventHazardLabels(
        active=th.tensor(active, dtype=th.bool, device=out_device),
        target=th.tensor(target, dtype=th.float32, device=out_device),
        weight=th.tensor(weight, dtype=th.float32, device=out_device),
        source=th.tensor(source, dtype=th.long, device=out_device),
        window_age=th.tensor(window_age, dtype=th.float32, device=out_device),
        window_id=th.tensor(window_id, dtype=th.long, device=out_device),
        had_accepted=th.tensor(had_accepted, dtype=th.bool, device=out_device),
    )


def first_event_hazard_batch_from_observations(obs: Any) -> tuple[th.Tensor, th.Tensor, th.Tensor] | None:
    if not isinstance(obs, dict):
        return None
    return first_event_hazard_batch_from_mapping(obs)


def first_event_hazard_batch_from_mapping(mapping: dict[str, Any]) -> tuple[th.Tensor, th.Tensor, th.Tensor] | None:
    if A6_FIRST_EVENT_FIELD_ACTIVE not in mapping or A6_FIRST_EVENT_FIELD_TARGET not in mapping:
        return None
    active = th.as_tensor(mapping[A6_FIRST_EVENT_FIELD_ACTIVE]).reshape(-1).to(dtype=th.bool)
    target = th.as_tensor(mapping[A6_FIRST_EVENT_FIELD_TARGET]).reshape(-1).to(dtype=th.float32)
    if A6_FIRST_EVENT_FIELD_WEIGHT in mapping:
        weight = th.as_tensor(mapping[A6_FIRST_EVENT_FIELD_WEIGHT]).reshape(-1).to(dtype=th.float32)
    else:
        weight = th.ones_like(target, dtype=th.float32)
    if not (int(active.numel()) == int(target.numel()) == int(weight.numel())):
        raise ValueError("A6 first-event hazard observation fields must flatten to the same length")
    return active, target, weight


def first_event_hazard_batch_from_rollout_data(rollout_data: Any) -> tuple[th.Tensor, th.Tensor, th.Tensor] | None:
    if all(hasattr(rollout_data, field) for field in (A6_FIRST_EVENT_FIELD_ACTIVE, A6_FIRST_EVENT_FIELD_TARGET)):
        fields = {
            A6_FIRST_EVENT_FIELD_ACTIVE: getattr(rollout_data, A6_FIRST_EVENT_FIELD_ACTIVE),
            A6_FIRST_EVENT_FIELD_TARGET: getattr(rollout_data, A6_FIRST_EVENT_FIELD_TARGET),
        }
        if hasattr(rollout_data, A6_FIRST_EVENT_FIELD_WEIGHT):
            fields[A6_FIRST_EVENT_FIELD_WEIGHT] = getattr(rollout_data, A6_FIRST_EVENT_FIELD_WEIGHT)
        return first_event_hazard_batch_from_mapping(fields)
    return None


def first_event_credit_batch_from_rollout_data(
    rollout_data: Any,
) -> tuple[th.Tensor, th.Tensor, th.Tensor, th.Tensor | None, th.Tensor | None] | None:
    batch = first_event_hazard_batch_from_rollout_data(rollout_data)
    if batch is None:
        return None
    active, target, weight = batch
    window_id = (
        th.as_tensor(getattr(rollout_data, A6_FIRST_EVENT_FIELD_WINDOW_ID)).reshape(-1).to(dtype=th.long)
        if hasattr(rollout_data, A6_FIRST_EVENT_FIELD_WINDOW_ID)
        else None
    )
    if window_id is not None and int(window_id.numel()) != int(active.numel()):
        raise ValueError("A7 first-event credit window ids must match label length")
    source = (
        th.as_tensor(getattr(rollout_data, A6_FIRST_EVENT_FIELD_SOURCE)).reshape(-1).to(dtype=th.long)
        if hasattr(rollout_data, A6_FIRST_EVENT_FIELD_SOURCE)
        else None
    )
    if source is not None and int(source.numel()) != int(active.numel()):
        raise ValueError("A7 first-event credit sources must match label length")
    return active, target, weight, window_id, source


def _cap_first_event_credit_window_mass(
    weights: th.Tensor,
    targets: th.Tensor,
    active_mask: th.Tensor,
    window_id: th.Tensor | None,
    *,
    positive_mass_cap: float,
    negative_mass_cap: float,
) -> th.Tensor:
    capped = weights.clone()
    if window_id is None:
        return capped

    ids = window_id.to(device=weights.device).reshape(-1).long()
    if int(ids.numel()) != int(weights.numel()):
        raise ValueError("A7 first-event credit window ids must match weights")

    for positive, cap in ((False, float(negative_mass_cap)), (True, float(positive_mass_cap))):
        if cap <= 0.0:
            continue
        sign_mask = targets > 0.5 if positive else targets <= 0.5
        valid = active_mask & sign_mask & (ids >= 0)
        if int(valid.sum().detach().cpu().item()) <= 0:
            continue
        for value in th.unique(ids[valid], sorted=False):
            group = valid & (ids == value)
            mass = capped[group].sum()
            mass_value = float(mass.detach().cpu().item())
            if mass_value > cap:
                capped[group] = capped[group] * (cap / max(mass_value, 1.0e-8))
    return capped


def compute_first_event_hazard_loss(
    event_logit_delta: th.Tensor,
    target: th.Tensor,
    active: th.Tensor,
    weight: th.Tensor | None = None,
    *,
    coef: float = 1.0,
) -> FirstEventHazardLoss:
    logits = event_logit_delta.reshape(-1)
    targets = target.to(device=logits.device, dtype=logits.dtype).reshape(-1)
    active_mask = active.to(device=logits.device).reshape(-1).to(dtype=th.bool)
    weights = (
        th.ones_like(targets)
        if weight is None
        else weight.to(device=logits.device, dtype=logits.dtype).reshape(-1)
    )
    if not (int(logits.numel()) == int(targets.numel()) == int(active_mask.numel()) == int(weights.numel())):
        raise ValueError("A6 first-event hazard tensors must flatten to the same length")

    finite = th.isfinite(logits) & th.isfinite(targets) & th.isfinite(weights)
    effective_weight = th.where(active_mask & finite, th.clamp(weights, min=0.0), th.zeros_like(weights))
    weight_sum_tensor = effective_weight.sum()
    positive_tensor = ((targets > 0.5) & (effective_weight > 0.0)).sum()
    active_tensor = (effective_weight > 0.0).sum()
    zero = logits.sum() * 0.0
    if float(coef) <= 0.0 or float(weight_sum_tensor.detach().cpu().item()) <= 0.0:
        return FirstEventHazardLoss(
            loss=zero,
            unscaled_loss=zero.detach(),
            active_count=int(active_tensor.detach().cpu().item()),
            positive_count=int(positive_tensor.detach().cpu().item()),
            weight_sum=float(weight_sum_tensor.detach().cpu().item()),
            positive_frac=0.0,
        )

    bce = F.binary_cross_entropy_with_logits(logits, targets, reduction="none")
    unscaled = (bce * effective_weight).sum() / weight_sum_tensor.clamp_min(1.0e-8)
    loss = float(coef) * unscaled
    positive_count = int(positive_tensor.detach().cpu().item())
    active_count = int(active_tensor.detach().cpu().item())
    return FirstEventHazardLoss(
        loss=loss,
        unscaled_loss=unscaled.detach(),
        active_count=active_count,
        positive_count=positive_count,
        weight_sum=float(weight_sum_tensor.detach().cpu().item()),
        positive_frac=(float(positive_count) / float(active_count)) if active_count > 0 else 0.0,
    )


def compute_first_event_credit_loss(
    event_q_values: th.Tensor,
    target: th.Tensor,
    active: th.Tensor,
    weight: th.Tensor | None = None,
    *,
    event_logit_delta: th.Tensor | None = None,
    window_id: th.Tensor | None = None,
    value_coef: float = 1.0,
    delta_align_coef: float = 0.0,
    delta_align_clip: float = 4.0,
    delta_align_active: th.Tensor | None = None,
    positive_mass_cap: float = 1.0,
    negative_mass_cap: float = 1.0,
) -> FirstEventCreditLoss:
    values = event_q_values.reshape(-1, 2)
    q_hold = values[:, 0]
    q_fire_once = values[:, 1]
    advantage = q_fire_once - q_hold
    targets = target.to(device=advantage.device, dtype=advantage.dtype).reshape(-1)
    active_mask = active.to(device=advantage.device).reshape(-1).to(dtype=th.bool)
    weights = (
        th.ones_like(targets)
        if weight is None
        else weight.to(device=advantage.device, dtype=advantage.dtype).reshape(-1)
    )
    if not (int(advantage.numel()) == int(targets.numel()) == int(active_mask.numel()) == int(weights.numel())):
        raise ValueError("A7 first-event credit tensors must flatten to the same length")

    finite = th.isfinite(advantage) & th.isfinite(targets) & th.isfinite(weights)
    if event_logit_delta is not None:
        delta = event_logit_delta.to(device=advantage.device, dtype=advantage.dtype).reshape(-1)
        if int(delta.numel()) != int(advantage.numel()):
            raise ValueError("A7 event-logit delta must match event credit batch length")
        finite = finite & th.isfinite(delta)
        if delta_align_active is None:
            delta_align_mask = th.ones_like(active_mask, dtype=th.bool)
        else:
            delta_align_mask = delta_align_active.to(device=advantage.device).reshape(-1).to(dtype=th.bool)
            if int(delta_align_mask.numel()) != int(advantage.numel()):
                raise ValueError("A7 delta-align active mask must match event credit batch length")
    else:
        delta = None
        delta_align_mask = None

    effective_weight = th.where(active_mask & finite, th.clamp(weights, min=0.0), th.zeros_like(weights))
    effective_weight = _cap_first_event_credit_window_mass(
        effective_weight,
        targets,
        active_mask & finite,
        window_id,
        positive_mass_cap=float(positive_mass_cap),
        negative_mass_cap=float(negative_mass_cap),
    )
    weight_sum_tensor = effective_weight.sum()
    positive_tensor = ((targets > 0.5) & (effective_weight > 0.0)).sum()
    active_tensor = (effective_weight > 0.0).sum()
    zero = advantage.sum() * 0.0
    if delta is not None:
        zero = zero + delta.sum() * 0.0
    if float(weight_sum_tensor.detach().cpu().item()) <= 0.0:
        return FirstEventCreditLoss(
            loss=zero,
            value_loss=zero,
            delta_align_loss=zero,
            unscaled_value_loss=zero.detach(),
            unscaled_delta_align_loss=zero.detach(),
            active_count=int(active_tensor.detach().cpu().item()),
            positive_count=int(positive_tensor.detach().cpu().item()),
            weight_sum=float(weight_sum_tensor.detach().cpu().item()),
            positive_frac=0.0,
            advantage_mean=float(advantage.detach().mean().cpu().item()) if int(advantage.numel()) > 0 else 0.0,
            advantage_abs_mean=float(advantage.detach().abs().mean().cpu().item()) if int(advantage.numel()) > 0 else 0.0,
        )

    value_bce = F.binary_cross_entropy_with_logits(advantage, targets, reduction="none")
    unscaled_value = (value_bce * effective_weight).sum() / weight_sum_tensor.clamp_min(1.0e-8)
    value_loss = float(max(0.0, value_coef)) * unscaled_value

    if delta is not None and float(delta_align_coef) > 0.0:
        clip = float(max(0.0, delta_align_clip))
        target_delta = advantage.detach()
        if clip > 0.0:
            target_delta = th.clamp(target_delta, min=-clip, max=clip)
        delta_per_item = F.smooth_l1_loss(delta, target_delta, reduction="none")
        delta_weight = th.where(
            delta_align_mask & finite,
            effective_weight,
            th.zeros_like(effective_weight),
        )
        delta_weight_sum = delta_weight.sum()
        if float(delta_weight_sum.detach().cpu().item()) > 0.0:
            unscaled_delta = (delta_per_item * delta_weight).sum() / delta_weight_sum.clamp_min(1.0e-8)
            delta_loss = float(delta_align_coef) * unscaled_delta
        else:
            unscaled_delta = zero.detach()
            delta_loss = zero
    else:
        unscaled_delta = zero.detach()
        delta_loss = zero

    positive_count = int(positive_tensor.detach().cpu().item())
    active_count = int(active_tensor.detach().cpu().item())
    return FirstEventCreditLoss(
        loss=value_loss + delta_loss,
        value_loss=value_loss,
        delta_align_loss=delta_loss,
        unscaled_value_loss=unscaled_value.detach(),
        unscaled_delta_align_loss=unscaled_delta.detach(),
        active_count=active_count,
        positive_count=positive_count,
        weight_sum=float(weight_sum_tensor.detach().cpu().item()),
        positive_frac=(float(positive_count) / float(active_count)) if active_count > 0 else 0.0,
        advantage_mean=float(advantage.detach().mean().cpu().item()),
        advantage_abs_mean=float(advantage.detach().abs().mean().cpu().item()),
    )
