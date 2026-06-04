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
