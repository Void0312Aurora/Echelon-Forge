"""Subdomain dataclasses and helpers shared by the AdaptiveKLPPO mixins.

Extracted from ``ppo_adaptive_kl.py`` so the per-subdomain mixin modules can
import the frozen dataclasses they operate on without a circular dependency on
the main algorithm module. These names are re-exported from
``ppo_adaptive_kl`` for backwards compatibility with existing test/tool
imports (e.g. ``from python.rl.policy_algo.ppo_adaptive_kl import _M3S2WindowClassifierReplay``).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import torch as th

from .first_event_hazard import (
    FirstEventCreditLoss,
    FirstEventPolicyMarginLoss,
)

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


@dataclass
class _TrainEpochStats:
    """Per-``train()`` accumulator container.

    Holds the per-minibatch logging lists that ``AdaptiveKLPPO.train()``
    appends to inside the SB3-style optimization loop and then reduces in the
    diagnostic-logging section. Extracted from ``train()`` so the diagnostic
    logging blocks can move into their per-subdomain mixins while operating on
    a single explicit state object instead of ~40 free local variables.

    Field names match the original ``train()`` local accumulators one-for-one,
    so this is a pure structural refactor with no behavior change.
    """

    entropy_losses: list = field(default_factory=list)
    pg_losses: list = field(default_factory=list)
    value_losses: list = field(default_factory=list)
    action_mean_regularization_losses: list = field(default_factory=list)
    first_event_hazard_losses: list = field(default_factory=list)
    first_event_hazard_active_counts: list = field(default_factory=list)
    first_event_hazard_positive_fracs: list = field(default_factory=list)
    first_event_credit_losses: list = field(default_factory=list)
    first_event_credit_value_losses: list = field(default_factory=list)
    first_event_credit_delta_align_losses: list = field(default_factory=list)
    first_event_credit_active_counts: list = field(default_factory=list)
    first_event_credit_positive_fracs: list = field(default_factory=list)
    first_event_credit_advantage_means: list = field(default_factory=list)
    first_event_credit_projection_active_counts: list = field(default_factory=list)
    first_event_credit_projection_candidate_counts: list = field(default_factory=list)
    first_event_credit_projection_unsupported_counts: list = field(default_factory=list)
    first_event_credit_projection_advantage_means: list = field(default_factory=list)
    first_event_credit_projection_delta_means: list = field(default_factory=list)
    first_event_credit_source_shadow_counts: list = field(default_factory=list)
    first_event_credit_source_deadline_counts: list = field(default_factory=list)
    first_event_credit_source_early_counts: list = field(default_factory=list)
    first_event_credit_source_prewindow_counts: list = field(default_factory=list)
    first_event_credit_source_legal_open_quality_counts: list = field(default_factory=list)
    first_event_credit_source_legal_open_quality_positive_counts: list = field(
        default_factory=list
    )
    first_event_credit_source_deadline_positive_counts: list = field(default_factory=list)
    first_event_credit_source_shadow_positive_counts: list = field(default_factory=list)
    first_event_credit_source_legal_open_quality_advantage_means: list = field(
        default_factory=list
    )
    first_event_credit_separate_update_grad_norms: list = field(default_factory=list)
    first_event_credit_separate_update_counts: list = field(default_factory=list)
    first_event_policy_margin_losses: list = field(default_factory=list)
    first_event_policy_margin_active_counts: list = field(default_factory=list)
    first_event_policy_margin_positive_fracs: list = field(default_factory=list)
    first_event_policy_margin_delta_means: list = field(default_factory=list)
    first_event_policy_margin_delta_positive_fracs: list = field(default_factory=list)
    first_event_policy_margin_projection_active_counts: list = field(default_factory=list)
    first_event_policy_margin_projection_delta_means: list = field(default_factory=list)
    first_event_policy_margin_separate_update_grad_norms: list = field(default_factory=list)
    first_event_policy_margin_separate_update_counts: list = field(default_factory=list)
    clip_fractions: list = field(default_factory=list)
    approx_kl_divs: list = field(default_factory=list)

    def append_first_event_credit_stats(
        self,
        credit_loss: FirstEventCreditLoss,
        *,
        total_loss=None,
        value_loss=None,
        delta_align_loss=None,
    ) -> None:
        self.first_event_credit_losses.append(
            float((credit_loss.loss if total_loss is None else total_loss).detach().cpu())
        )
        self.first_event_credit_value_losses.append(
            float((credit_loss.value_loss if value_loss is None else value_loss).detach().cpu())
        )
        self.first_event_credit_delta_align_losses.append(
            float(
                (credit_loss.delta_align_loss if delta_align_loss is None else delta_align_loss)
                .detach()
                .cpu()
            )
        )
        self.first_event_credit_active_counts.append(int(credit_loss.active_count))
        self.first_event_credit_positive_fracs.append(float(credit_loss.positive_frac))
        self.first_event_credit_advantage_means.append(float(credit_loss.advantage_mean))
        self.first_event_credit_projection_active_counts.append(
            int(credit_loss.projection_active_count)
        )
        self.first_event_credit_projection_candidate_counts.append(
            int(credit_loss.projection_candidate_count)
        )
        self.first_event_credit_projection_unsupported_counts.append(
            int(credit_loss.projection_unsupported_count)
        )
        self.first_event_credit_projection_advantage_means.append(
            float(credit_loss.projection_advantage_mean)
        )
        self.first_event_credit_projection_delta_means.append(
            float(credit_loss.projection_delta_mean)
        )
        self.first_event_credit_source_shadow_counts.append(int(credit_loss.source_shadow_count))
        self.first_event_credit_source_deadline_counts.append(
            int(credit_loss.source_deadline_count)
        )
        self.first_event_credit_source_early_counts.append(
            int(credit_loss.source_early_accepted_count)
        )
        self.first_event_credit_source_prewindow_counts.append(
            int(credit_loss.source_prewindow_count)
        )
        self.first_event_credit_source_legal_open_quality_counts.append(
            int(credit_loss.source_legal_open_quality_count)
        )
        self.first_event_credit_source_legal_open_quality_positive_counts.append(
            int(credit_loss.source_legal_open_quality_positive_count)
        )
        self.first_event_credit_source_deadline_positive_counts.append(
            int(credit_loss.source_deadline_positive_count)
        )
        self.first_event_credit_source_shadow_positive_counts.append(
            int(credit_loss.source_shadow_positive_count)
        )
        self.first_event_credit_source_legal_open_quality_advantage_means.append(
            float(credit_loss.source_legal_open_quality_advantage_mean)
        )

    def append_first_event_policy_margin_stats(
        self,
        margin_loss: FirstEventPolicyMarginLoss,
    ) -> None:
        self.first_event_policy_margin_losses.append(float(margin_loss.loss.detach().cpu()))
        self.first_event_policy_margin_active_counts.append(int(margin_loss.active_count))
        self.first_event_policy_margin_positive_fracs.append(float(margin_loss.positive_frac))
        self.first_event_policy_margin_delta_means.append(float(margin_loss.delta_mean))
        self.first_event_policy_margin_delta_positive_fracs.append(
            float(margin_loss.delta_positive_frac)
        )
        self.first_event_policy_margin_projection_active_counts.append(
            int(margin_loss.projection_active_count)
        )
        self.first_event_policy_margin_projection_delta_means.append(
            float(margin_loss.projection_delta_mean)
        )
