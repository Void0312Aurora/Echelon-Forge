"""Subdomain dataclasses and helpers shared by the AdaptiveKLPPO mixins.

Extracted from ``ppo_adaptive_kl.py`` so the per-subdomain mixin modules can
import the frozen dataclasses they operate on without a circular dependency on
the main algorithm module. These names are re-exported from
``ppo_adaptive_kl`` for backwards compatibility with existing test/tool
imports (e.g. ``from python.rl.policy_algo.ppo_adaptive_kl import _M3S2WindowClassifierReplay``).
"""

from __future__ import annotations

from dataclasses import dataclass

import torch as th

from python.mission_obs_taxonomy import (
    MISSION_OBS_AIR_COMBAT_C2_ROE_V1,
    MISSION_OBS_AIR_COMBAT_C2_ROE_V2,
    mission_observation_dim,
    mission_observation_field_index,
)


_AIR_COMBAT_C2_ROE_MODES = (
    MISSION_OBS_AIR_COMBAT_C2_ROE_V1,
    MISSION_OBS_AIR_COMBAT_C2_ROE_V2,
)


def _air_combat_c2_roe_mode_from_dim(dim: int) -> str | None:
    for mode in _AIR_COMBAT_C2_ROE_MODES:
        if int(dim) == int(mission_observation_dim(mode)):
            return mode
    return None


def _mission_column(mission: th.Tensor, mode: str, field_name: str) -> th.Tensor:
    return mission[:, mission_observation_field_index(mode, field_name)]


@dataclass(frozen=True)
class _A7FirstEventRolloutRow:
    engagement_state: str
    fire_mask: bool
    fire_once_accepted: bool
    episode_id: int
    launch_window_open: bool


@dataclass(frozen=True)
class _M3S1GroupedStoppingSidecarGroup:
    group_id: int | str
    episode_id: int | str
    row_indices: tuple[int, ...]
    step_indices: tuple[int, ...]
    env_indices: tuple[int, ...]
    legal_mask: tuple[bool, ...]
    quality_mask: tuple[bool, ...]
    accepted_event: tuple[bool, ...]
    censoring_kind: str
    censor_step: int | None
    support_horizon: int | None


@dataclass(frozen=True)
class _M3S1GroupedStoppingSidecar:
    groups: tuple[_M3S1GroupedStoppingSidecarGroup, ...]
    observations: dict
    accepted_event_count: int = 0
    one_shot_violation_count: int = 0
    closed_mask_accepted_event_count: int = 0


@dataclass(frozen=True)
class _M3S1GroupedStoppingDiagnostics:
    stop_logit_mean: float = 0.0
    stop_logit_desirable_mean: float = 0.0
    stop_logit_prewindow_mean: float = 0.0
    stop_logit_no_window_mean: float = 0.0
    stop_logit_closed_mask_mean: float = 0.0
    event_logit_delta_diagnostic_mean: float = 0.0
    stop_logit_count: int = 0
    stop_logit_desirable_count: int = 0
    stop_logit_prewindow_count: int = 0
    stop_logit_no_window_count: int = 0
    closed_mask_row_count: int = 0
    event_logit_delta_diagnostic_count: int = 0


@dataclass(frozen=True)
class _M3S2WindowClassifierLoss:
    loss: th.Tensor
    unscaled_loss: th.Tensor
    balanced_bce_loss: th.Tensor
    prewindow_logit_ceiling_loss: th.Tensor
    quality_logit_floor_loss: th.Tensor
    active_count: int
    positive_count: int
    negative_count: int
    group_count: int
    positive_logit_mean: float
    negative_logit_mean: float
    positive_prob_mean: float
    negative_prob_mean: float
    accuracy: float
    replay_enabled: bool = False
    replay_used: bool = False
    replay_positive_count: int = 0
    replay_negative_count: int = 0


@dataclass(frozen=True)
class _M3S2FireBoundaryLoss:
    loss: th.Tensor
    unscaled_loss: th.Tensor
    balanced_bce_loss: th.Tensor
    negative_logit_ceiling_loss: th.Tensor
    positive_logit_floor_loss: th.Tensor
    active_count: int
    positive_count: int
    negative_count: int
    group_count: int
    executable_positive_logit_mean: float
    executable_negative_logit_mean: float
    executable_positive_prob_mean: float
    executable_negative_prob_mean: float
    direct_head_positive_delta_mean: float
    direct_head_negative_delta_mean: float
    accuracy: float
    boundary_cross_count: int
    boundary_cross_in_window_count: int
