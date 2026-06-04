from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import torch as th

from python.mission_obs_taxonomy import (
    MISSION_OBS_AIR_COMBAT_C2_ROE_V1,
    MISSION_OBS_AIR_COMBAT_C2_ROE_V2,
    mission_observation_dim,
    mission_observation_field_index,
    mission_observation_has_field,
)


@dataclass(frozen=True)
class FirstEventLegalProjection:
    observations: dict[str, Any]
    active: th.Tensor
    unsupported_count: int


def _clone_observation_mapping(obs: dict[str, Any]) -> dict[str, Any]:
    return {key: value.clone() if th.is_tensor(value) else value for key, value in obs.items()}


_AIR_COMBAT_C2_ROE_MODES = (
    MISSION_OBS_AIR_COMBAT_C2_ROE_V1,
    MISSION_OBS_AIR_COMBAT_C2_ROE_V2,
)


def _air_combat_c2_roe_mode_from_dim(dim: int) -> str | None:
    for mode in _AIR_COMBAT_C2_ROE_MODES:
        if int(dim) == int(mission_observation_dim(mode)):
            return mode
    return None


def _mission_index(mode: str, field_name: str) -> int:
    return int(mission_observation_field_index(mode, field_name))


def _contact_evidence_from_obs(obs: dict[str, Any], n_envs: int, device: th.device) -> th.Tensor:
    mission = th.as_tensor(obs["mission"], device=device)
    mission_mode = _air_combat_c2_roe_mode_from_dim(int(mission.shape[1]))
    if mission_mode is None:
        evidence = th.zeros((int(n_envs),), dtype=th.bool, device=device)
    else:
        evidence = mission[:, _mission_index(mission_mode, "target_contact_present")].float() > 0.5

    contacts_history = obs.get("contacts_history")
    if contacts_history is not None:
        history = th.as_tensor(contacts_history, device=device)
        if history.ndim == 3 and int(n_envs) == 1 and int(history.shape[-1]) >= 1:
            history = history.reshape(1, *history.shape)
        if (
            history.ndim == 4
            and int(history.shape[0]) == int(n_envs)
            and int(history.shape[-1]) >= 1
            and int(history.shape[1]) > 0
        ):
            target_range = history[:, -1, :, 0].float()
            evidence = evidence | (th.isfinite(target_range) & (target_range > 0.0)).any(dim=1)

    contacts = obs.get("contacts")
    if contacts is not None:
        contact_tensor = th.as_tensor(contacts, device=device)
        if contact_tensor.ndim == 2 and int(n_envs) == 1 and int(contact_tensor.shape[-1]) >= 1:
            contact_tensor = contact_tensor.reshape(1, *contact_tensor.shape)
        if contact_tensor.ndim == 3 and int(contact_tensor.shape[0]) == int(n_envs) and int(contact_tensor.shape[-1]) >= 1:
            target_range = contact_tensor[..., 0].float()
            evidence = evidence | (th.isfinite(target_range) & (target_range > 0.0)).any(dim=1)

    return evidence


def project_air_combat_c2_roe_legal_open_observations(
    obs: Any,
    candidate_active: th.Tensor,
) -> FirstEventLegalProjection | None:
    """Project shadow-quality observations onto the legal first-shot decision surface.

    The projection is a training-only feature rewrite. It preserves contact and
    geometry facts, rewrites only the C2/ROE event-action legality fields, and
    reports unsupported rows instead of silently training closed-mask alignment.
    """

    if not isinstance(obs, dict) or "mission" not in obs:
        return None

    mission = th.as_tensor(obs["mission"])
    if mission.ndim != 2:
        return None
    mission_mode = _air_combat_c2_roe_mode_from_dim(int(mission.shape[1]))
    if mission_mode is None:
        return None

    active = candidate_active.to(device=mission.device).reshape(-1).to(dtype=th.bool)
    if int(active.numel()) != int(mission.shape[0]):
        raise ValueError("A7 legal projection active mask must match observation batch")

    evidence = _contact_evidence_from_obs(obs, int(mission.shape[0]), mission.device)
    if int(evidence.numel()) != int(active.numel()):
        raise ValueError("A7 legal projection contact evidence mask must match observation batch")

    projected_active = active & evidence
    unsupported_count = int((active & ~evidence).sum().detach().cpu().item())
    if int(projected_active.sum().detach().cpu().item()) <= 0:
        return FirstEventLegalProjection(
            observations=_clone_observation_mapping(obs),
            active=projected_active,
            unsupported_count=unsupported_count,
        )

    projected = _clone_observation_mapping(obs)

    mission_projected = mission.clone()
    rows = projected_active
    mission_projected[rows, _mission_index(mission_mode, "wcs_state")] = mission_projected.new_tensor(2.0)
    mission_projected[rows, _mission_index(mission_mode, "authorization_to_fire")] = mission_projected.new_tensor(1.0)
    mission_projected[rows, _mission_index(mission_mode, "engage_order_state")] = mission_projected.new_tensor(2.0)
    mission_projected[rows, _mission_index(mission_mode, "shot_policy_state")] = mission_projected.new_tensor(1.0)
    budget_idx = _mission_index(mission_mode, "shot_budget_remaining")
    mission_projected[rows, budget_idx] = th.clamp(mission_projected[rows, budget_idx], min=1.0)
    mission_projected[rows, _mission_index(mission_mode, "pending_assessment")] = mission_projected.new_tensor(0.0)
    mission_projected[rows, _mission_index(mission_mode, "target_contact_present")] = mission_projected.new_tensor(1.0)
    if mission_observation_has_field(mission_mode, "fire_mask_open"):
        mission_projected[rows, _mission_index(mission_mode, "fire_mask_open")] = mission_projected.new_tensor(1.0)
    projected["mission"] = mission_projected

    event_mask = projected.get("event_action_mask")
    if event_mask is not None:
        mask_tensor = th.as_tensor(event_mask, device=mission.device).clone()
        if mask_tensor.ndim == 1 and int(mask_tensor.numel()) >= 2 and int(mission.shape[0]) == 1:
            mask_tensor = mask_tensor.reshape(1, -1)
        if mask_tensor.ndim == 2 and int(mask_tensor.shape[0]) == int(mission.shape[0]) and int(mask_tensor.shape[1]) >= 2:
            mask_tensor[rows, 0] = mask_tensor.new_tensor(1.0)
            mask_tensor[rows, 1] = mask_tensor.new_tensor(1.0)
            projected["event_action_mask"] = mask_tensor.to(dtype=event_mask.dtype) if th.is_tensor(event_mask) else mask_tensor

    fire_mask = projected.get("fire_mask")
    if fire_mask is not None:
        fire_tensor = th.as_tensor(fire_mask, device=mission.device).clone().reshape(-1)
        if int(fire_tensor.numel()) == int(mission.shape[0]):
            fire_tensor[rows] = fire_tensor.new_tensor(1.0)
            projected["fire_mask"] = fire_tensor.reshape_as(fire_mask).to(dtype=fire_mask.dtype) if th.is_tensor(fire_mask) else fire_tensor

    return FirstEventLegalProjection(
        observations=projected,
        active=projected_active,
        unsupported_count=unsupported_count,
    )
