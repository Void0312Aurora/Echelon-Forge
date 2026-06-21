"""Adaptive-KL PPO with auxiliary air-combat objective subdomains.

The algorithm carries four auxiliary subdomains layered on top of the base
PPO loop:

* **A6** first-event hazard / launch-window labels,
* **A7** event-credit value/alignment and policy-margin losses,
* **M3-S1** grouped-stopping auxiliary loss,
* **M3-S2** event-window / fire-boundary / window-classifier losses.

Each subdomain is implemented as a mixin module under this package
(``_first_event_mixin`` etc.); ``AdaptiveKLPPO`` composes them and keeps
only the core PPO loop, KL control, rollout plumbing, and the per-subdomain
logging that is interleaved with the core training step. The dataclasses and
the window-classifier replay buffer live in ``_adaptive_kl_support`` /
``_window_classifier_replay`` and are re-exported from this module for
backwards compatibility with existing test/diagnostic imports.
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np
import torch as th
from gymnasium import spaces
from torch.nn import functional as F

from stable_baselines3 import PPO
from stable_baselines3.common.buffers import RolloutBuffer
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.utils import explained_variance, obs_as_tensor
from stable_baselines3.common.vec_env import VecEnv

from .device_dict_rollout_buffer import DeviceDictRolloutBuffer
from .first_event_hazard import (
    FirstEventCreditLoss,
    FirstEventPolicyMarginLoss,
)
from .first_event_rollout_buffer import (
    FirstEventDeviceDictRolloutBuffer,
    FirstEventDictRolloutBuffer,
)
from .grouped_stopping import GroupedStoppingLoss

# Subdomain dataclasses, ROE helpers and the window-classifier replay buffer.
# Re-exported here so legacy imports such as
# ``from python.rl.policy_algo.ppo_adaptive_kl import _WindowClassifierReplay``
# keep working.
from ._adaptive_kl_support import (  # noqa: F401  (re-export)
    _FirstEventRolloutRow,
    _GroupedStoppingDiagnostics,
    _GroupedStoppingSidecar,
    _GroupedStoppingSidecarGroup,
    _FireBoundaryLoss,
    _WindowClassifierLoss,
    _TrainEpochStats,
    _air_combat_c2_roe_mode_from_dim,
    _mission_column,
)
from ._window_classifier_replay import _WindowClassifierReplay  # noqa: F401  (re-export)
from ._first_event_mixin import _FirstEventMixin
from ._event_credit_mixin import _EventCreditMixin
from ._grouped_stopping_mixin import _GroupedStoppingMixin
from ._event_window_mixin import _EventWindowMixin


class AdaptiveKLPPO(
    _EventWindowMixin,
    _GroupedStoppingMixin,
    _EventCreditMixin,
    _FirstEventMixin,
    PPO,
):
    """
    PPO variant with TRPO-like KL control:
    - Adds an (optional) KL penalty term to the loss.
    - Adapts learning-rate and clip-range multipliers to keep the observed KL near `target_kl`.

    This is designed to improve stability (avoid destructive updates). Low-KL boost behavior is
    intentionally conservative by default to avoid runaway update aggressiveness.
    """

    def __init__(
        self,
        *args,
        kl_penalty_coef: float = 0.0,
        kl_penalty_coef_min: float = 0.0,
        kl_penalty_coef_max: float = 50.0,
        kl_adaptive: bool = True,
        kl_adapt_factor: float = 1.5,
        lr_mult_min: float = 0.2,
        lr_mult_max: float = 3.0,
        clip_mult_min: float = 0.5,
        clip_mult_max: float = 2.0,
        low_kl_boost_patience: int = 2,
        boost_lr_on_low_kl: bool = True,
        boost_clip_on_low_kl: bool = False,
        action_mean_regularization_coef: float = 0.0,
        action_mean_regularization_target: Any = 0.0,
        first_event_hazard_coef: float = 0.0,
        first_event_curriculum_coef: float = 0.0,
        first_event_curriculum_decay_fraction: float = 0.25,
        first_event_curriculum_min_window_age_steps: int = 32,
        first_event_censored_survival_weight: float = 0.0,
        first_event_deadline_weight: float = 0.0,
        first_event_deadline_min_window_age_steps: int = 96,
        first_event_launch_window_enabled: bool = False,
        first_event_launch_window_min_range_m: float = 0.0,
        first_event_launch_window_max_range_m: float = 0.0,
        first_event_launch_window_max_track_age_s: float = 10.0,
        first_event_launch_window_min_window_age_steps: int = 1,
        first_event_launch_window_prewindow_hold_weight: float = 0.0,
        first_event_launch_window_early_accept_weight: float = 1.0,
        event_credit_value_coef: float = 0.0,
        event_credit_delta_align_coef: float = 0.0,
        event_credit_delta_align_clip: float = 4.0,
        event_credit_delta_align_positive_only: bool = False,
        event_credit_positive_mass_cap: float = 1.0,
        event_credit_negative_mass_cap: float = 1.0,
        event_credit_prewindow_hold_weight: float = 0.0,
        event_credit_early_accept_weight: float = 1.0,
        event_credit_curriculum_coef: float = 0.0,
        event_credit_curriculum_min_window_age_steps: int = 32,
        event_credit_censored_survival_weight: float = 0.0,
        event_credit_deadline_weight: float = 0.0,
        event_credit_deadline_min_window_age_steps: int = 96,
        event_credit_shadow_quality_weight: float = 1.0,
        event_credit_legal_open_quality_weight: float = 0.0,
        event_credit_legal_open_quality_min_window_age_steps: int = 1,
        event_credit_legal_projection_enabled: bool = False,
        event_credit_projection_value_coef: float = 0.0,
        event_credit_projection_delta_align_coef: float = 0.0,
        event_credit_separate_update_enabled: bool = False,
        event_credit_separate_update_max_grad_norm: float = 0.5,
        event_policy_margin_coef: float = 0.0,
        event_policy_margin: float = 2.0,
        event_policy_projection_margin_coef: float = 0.0,
        event_policy_separate_update_enabled: bool = False,
        event_policy_separate_update_max_grad_norm: float = 0.5,
        event_policy_separate_update_steps: int = 1,
        grouped_stopping_coef: float = 0.0,
        grouped_stopping_early_mass_coef: float = 1.0,
        grouped_stopping_early_mass_budget: float = 0.05,
        grouped_stopping_prefix_early_mass_budget: float | None = None,
        grouped_stopping_no_event_coef: float = 1.0,
        grouped_stopping_boundary_threshold: float = 0.0,
        grouped_stopping_detach_latent: bool = False,
        event_window_coef: float = 0.0,
        event_window_early_mass_coef: float = 1.0,
        event_window_early_mass_budget: float = 0.05,
        event_window_early_survival_coef: float = 0.0,
        event_window_no_event_coef: float = 1.0,
        event_window_delay_coef: float = 0.0,
        event_window_deadline_coef: float = 0.0,
        event_window_deadline_steps: int = 0,
        event_window_quality_boundary_coef: float = 0.0,
        event_window_quality_boundary_logit: float = 0.0,
        event_window_contrastive_margin_coef: float = 0.0,
        event_window_contrastive_margin: float = 0.0,
        event_window_balanced_bce_coef: float = 0.0,
        event_window_prewindow_hazard_scale_coef: float = 0.0,
        event_window_prewindow_hazard_target: float = 0.0,
        event_window_quality_hazard_target_coef: float = 0.0,
        event_window_quality_hazard_target: float = 0.5,
        event_window_prewindow_logit_ceiling_coef: float = 0.0,
        event_window_prewindow_logit_ceiling: float = -2.0,
        event_window_quality_logit_floor_coef: float = 0.0,
        event_window_quality_logit_floor: float = 2.0,
        event_window_use_stopping_head: bool = False,
        event_window_separate_update_enabled: bool = True,
        event_window_dedicated_optimizer_enabled: bool = False,
        event_window_separate_update_steps: int = 1,
        event_window_max_grad_norm: float = 2.0,
        event_window_support_preserving_collect_enabled: bool = False,
        event_window_support_preserving_hold_quality_enabled: bool = False,
        fire_boundary_coef: float = 0.0,
        fire_boundary_negative_logit_ceiling_coef: float = 0.0,
        fire_boundary_negative_logit_ceiling: float = -2.0,
        fire_boundary_positive_logit_floor_coef: float = 0.0,
        fire_boundary_positive_logit_floor: float = 2.0,
        fire_boundary_separate_update_enabled: bool = True,
        fire_boundary_dedicated_optimizer_enabled: bool = True,
        fire_boundary_separate_update_steps: int = 1,
        fire_boundary_max_grad_norm: float = 2.0,
        fire_boundary_support_preserving_collect_enabled: bool = False,
        fire_boundary_support_preserving_hold_quality_enabled: bool = False,
        window_classifier_coef: float = 0.0,
        window_classifier_prewindow_logit_ceiling_coef: float = 0.0,
        window_classifier_prewindow_logit_ceiling: float = -2.0,
        window_classifier_quality_logit_floor_coef: float = 0.0,
        window_classifier_quality_logit_floor: float = 2.0,
        window_classifier_detach_latent: bool = True,
        window_classifier_separate_update_enabled: bool = True,
        window_classifier_dedicated_optimizer_enabled: bool = True,
        window_classifier_separate_update_steps: int = 1,
        window_classifier_max_grad_norm: float = 2.0,
        window_classifier_replay_enabled: bool = False,
        window_classifier_replay_storage: str = "latent",
        window_classifier_replay_capacity: int = 4096,
        window_classifier_replay_batch_size: int = 1024,
        window_classifier_replay_min_positive: int = 1,
        window_classifier_replay_min_negative: int = 1,
        **kwargs,
    ):
        self.kl_penalty_coef = float(kl_penalty_coef)
        self.kl_penalty_coef_min = float(kl_penalty_coef_min)
        self.kl_penalty_coef_max = float(kl_penalty_coef_max)
        self.kl_adaptive = bool(kl_adaptive)
        self.kl_adapt_factor = float(kl_adapt_factor)
        self._lr_mult = 1.0
        self._clip_mult = 1.0
        self.lr_mult_min = float(lr_mult_min)
        self.lr_mult_max = float(lr_mult_max)
        self.clip_mult_min = float(clip_mult_min)
        self.clip_mult_max = float(clip_mult_max)
        self.low_kl_boost_patience = max(1, int(low_kl_boost_patience))
        self.boost_lr_on_low_kl = bool(boost_lr_on_low_kl)
        self.boost_clip_on_low_kl = bool(boost_clip_on_low_kl)
        self._low_kl_streak = 0
        self.action_mean_regularization_coef = float(max(0.0, action_mean_regularization_coef))
        self.action_mean_regularization_target = action_mean_regularization_target
        self.first_event_hazard_coef = float(max(0.0, first_event_hazard_coef))
        self.first_event_curriculum_coef = float(max(0.0, first_event_curriculum_coef))
        self.first_event_curriculum_decay_fraction = float(
            max(0.0, first_event_curriculum_decay_fraction)
        )
        self.first_event_curriculum_min_window_age_steps = max(
            1,
            int(first_event_curriculum_min_window_age_steps),
        )
        self.first_event_censored_survival_weight = float(
            max(0.0, first_event_censored_survival_weight)
        )
        self.first_event_deadline_weight = float(max(0.0, first_event_deadline_weight))
        self.first_event_deadline_min_window_age_steps = max(
            1,
            int(first_event_deadline_min_window_age_steps),
        )
        self.first_event_launch_window_enabled = bool(first_event_launch_window_enabled)
        self.first_event_launch_window_min_range_m = float(
            max(0.0, first_event_launch_window_min_range_m)
        )
        self.first_event_launch_window_max_range_m = float(
            max(0.0, first_event_launch_window_max_range_m)
        )
        self.first_event_launch_window_max_track_age_s = float(
            first_event_launch_window_max_track_age_s
        )
        self.first_event_launch_window_min_window_age_steps = max(
            1,
            int(first_event_launch_window_min_window_age_steps),
        )
        self.first_event_launch_window_prewindow_hold_weight = float(
            max(0.0, first_event_launch_window_prewindow_hold_weight)
        )
        self.first_event_launch_window_early_accept_weight = float(
            max(0.0, first_event_launch_window_early_accept_weight)
        )
        self.event_credit_value_coef = float(max(0.0, event_credit_value_coef))
        self.event_credit_delta_align_coef = float(max(0.0, event_credit_delta_align_coef))
        self.event_credit_delta_align_clip = float(max(0.0, event_credit_delta_align_clip))
        self.event_credit_delta_align_positive_only = bool(
            event_credit_delta_align_positive_only
        )
        self.event_credit_positive_mass_cap = float(max(0.0, event_credit_positive_mass_cap))
        self.event_credit_negative_mass_cap = float(max(0.0, event_credit_negative_mass_cap))
        self.event_credit_prewindow_hold_weight = float(
            max(0.0, event_credit_prewindow_hold_weight)
        )
        self.event_credit_early_accept_weight = float(
            max(0.0, event_credit_early_accept_weight)
        )
        self.event_credit_curriculum_coef = float(max(0.0, event_credit_curriculum_coef))
        self.event_credit_curriculum_min_window_age_steps = max(
            1,
            int(event_credit_curriculum_min_window_age_steps),
        )
        self.event_credit_censored_survival_weight = float(
            max(0.0, event_credit_censored_survival_weight)
        )
        self.event_credit_deadline_weight = float(max(0.0, event_credit_deadline_weight))
        self.event_credit_deadline_min_window_age_steps = max(
            1,
            int(event_credit_deadline_min_window_age_steps),
        )
        self.event_credit_shadow_quality_weight = float(
            max(0.0, event_credit_shadow_quality_weight)
        )
        self.event_credit_legal_open_quality_weight = float(
            max(0.0, event_credit_legal_open_quality_weight)
        )
        self.event_credit_legal_open_quality_min_window_age_steps = max(
            1,
            int(event_credit_legal_open_quality_min_window_age_steps),
        )
        self.event_credit_legal_projection_enabled = bool(
            event_credit_legal_projection_enabled
        )
        self.event_credit_projection_value_coef = float(
            max(0.0, event_credit_projection_value_coef)
        )
        self.event_credit_projection_delta_align_coef = float(
            max(0.0, event_credit_projection_delta_align_coef)
        )
        self.event_credit_separate_update_enabled = bool(event_credit_separate_update_enabled)
        self.event_credit_separate_update_max_grad_norm = float(
            max(0.0, event_credit_separate_update_max_grad_norm)
        )
        self.event_policy_margin_coef = float(max(0.0, event_policy_margin_coef))
        self.event_policy_margin = float(max(0.0, event_policy_margin))
        self.event_policy_projection_margin_coef = float(
            max(0.0, event_policy_projection_margin_coef)
        )
        self.event_policy_separate_update_enabled = bool(event_policy_separate_update_enabled)
        self.event_policy_separate_update_max_grad_norm = float(
            max(0.0, event_policy_separate_update_max_grad_norm)
        )
        self.event_policy_separate_update_steps = max(
            1, int(event_policy_separate_update_steps)
        )
        self.grouped_stopping_coef = float(max(0.0, grouped_stopping_coef))
        self.grouped_stopping_early_mass_coef = float(
            max(0.0, grouped_stopping_early_mass_coef)
        )
        self.grouped_stopping_early_mass_budget = float(
            max(0.0, grouped_stopping_early_mass_budget)
        )
        self.grouped_stopping_prefix_early_mass_budget = (
            None
            if grouped_stopping_prefix_early_mass_budget is None
            else float(max(0.0, grouped_stopping_prefix_early_mass_budget))
        )
        self.grouped_stopping_no_event_coef = float(
            max(0.0, grouped_stopping_no_event_coef)
        )
        self.grouped_stopping_boundary_threshold = float(
            grouped_stopping_boundary_threshold
        )
        self.grouped_stopping_detach_latent = bool(grouped_stopping_detach_latent)
        self.event_window_coef = float(max(0.0, event_window_coef))
        self.event_window_early_mass_coef = float(max(0.0, event_window_early_mass_coef))
        self.event_window_early_mass_budget = float(
            max(0.0, event_window_early_mass_budget)
        )
        self.event_window_early_survival_coef = float(
            max(0.0, event_window_early_survival_coef)
        )
        self.event_window_no_event_coef = float(max(0.0, event_window_no_event_coef))
        self.event_window_delay_coef = float(max(0.0, event_window_delay_coef))
        self.event_window_deadline_coef = float(max(0.0, event_window_deadline_coef))
        self.event_window_deadline_steps = max(0, int(event_window_deadline_steps))
        self.event_window_quality_boundary_coef = float(
            max(0.0, event_window_quality_boundary_coef)
        )
        self.event_window_quality_boundary_logit = float(
            event_window_quality_boundary_logit
        )
        self.event_window_contrastive_margin_coef = float(
            max(0.0, event_window_contrastive_margin_coef)
        )
        self.event_window_contrastive_margin = float(
            max(0.0, event_window_contrastive_margin)
        )
        self.event_window_balanced_bce_coef = float(
            max(0.0, event_window_balanced_bce_coef)
        )
        self.event_window_prewindow_hazard_scale_coef = float(
            max(0.0, event_window_prewindow_hazard_scale_coef)
        )
        self.event_window_prewindow_hazard_target = float(
            max(0.0, event_window_prewindow_hazard_target)
        )
        self.event_window_quality_hazard_target_coef = float(
            max(0.0, event_window_quality_hazard_target_coef)
        )
        self.event_window_quality_hazard_target = float(
            max(0.0, min(1.0, event_window_quality_hazard_target))
        )
        self.event_window_prewindow_logit_ceiling_coef = float(
            max(0.0, event_window_prewindow_logit_ceiling_coef)
        )
        self.event_window_prewindow_logit_ceiling = float(
            event_window_prewindow_logit_ceiling
        )
        self.event_window_quality_logit_floor_coef = float(
            max(0.0, event_window_quality_logit_floor_coef)
        )
        self.event_window_quality_logit_floor = float(event_window_quality_logit_floor)
        self.event_window_use_stopping_head = bool(event_window_use_stopping_head)
        self.event_window_separate_update_enabled = bool(
            event_window_separate_update_enabled
        )
        self.event_window_dedicated_optimizer_enabled = bool(
            event_window_dedicated_optimizer_enabled
        )
        self.event_window_separate_update_steps = max(
            1, int(event_window_separate_update_steps)
        )
        self.event_window_max_grad_norm = float(max(0.0, event_window_max_grad_norm))
        self.event_window_support_preserving_collect_enabled = bool(
            event_window_support_preserving_collect_enabled
        )
        self.event_window_support_preserving_hold_quality_enabled = bool(
            event_window_support_preserving_hold_quality_enabled
        )
        self.fire_boundary_coef = float(max(0.0, fire_boundary_coef))
        self.fire_boundary_negative_logit_ceiling_coef = float(
            max(0.0, fire_boundary_negative_logit_ceiling_coef)
        )
        self.fire_boundary_negative_logit_ceiling = float(
            fire_boundary_negative_logit_ceiling
        )
        self.fire_boundary_positive_logit_floor_coef = float(
            max(0.0, fire_boundary_positive_logit_floor_coef)
        )
        self.fire_boundary_positive_logit_floor = float(
            fire_boundary_positive_logit_floor
        )
        self.fire_boundary_separate_update_enabled = bool(
            fire_boundary_separate_update_enabled
        )
        self.fire_boundary_dedicated_optimizer_enabled = bool(
            fire_boundary_dedicated_optimizer_enabled
        )
        self.fire_boundary_separate_update_steps = max(
            1, int(fire_boundary_separate_update_steps)
        )
        self.fire_boundary_max_grad_norm = float(max(0.0, fire_boundary_max_grad_norm))
        self.fire_boundary_support_preserving_collect_enabled = bool(
            fire_boundary_support_preserving_collect_enabled
        )
        self.fire_boundary_support_preserving_hold_quality_enabled = bool(
            fire_boundary_support_preserving_hold_quality_enabled
        )
        self.window_classifier_coef = float(max(0.0, window_classifier_coef))
        self.window_classifier_prewindow_logit_ceiling_coef = float(
            max(0.0, window_classifier_prewindow_logit_ceiling_coef)
        )
        self.window_classifier_prewindow_logit_ceiling = float(
            window_classifier_prewindow_logit_ceiling
        )
        self.window_classifier_quality_logit_floor_coef = float(
            max(0.0, window_classifier_quality_logit_floor_coef)
        )
        self.window_classifier_quality_logit_floor = float(
            window_classifier_quality_logit_floor
        )
        self.window_classifier_detach_latent = bool(window_classifier_detach_latent)
        self.window_classifier_separate_update_enabled = bool(
            window_classifier_separate_update_enabled
        )
        self.window_classifier_dedicated_optimizer_enabled = bool(
            window_classifier_dedicated_optimizer_enabled
        )
        self.window_classifier_separate_update_steps = max(
            1,
            int(window_classifier_separate_update_steps),
        )
        self.window_classifier_max_grad_norm = float(
            max(0.0, window_classifier_max_grad_norm)
        )
        self.window_classifier_replay_enabled = bool(window_classifier_replay_enabled)
        self.window_classifier_replay_storage = str(
            window_classifier_replay_storage or "latent"
        ).lower()
        if self.window_classifier_replay_storage not in {"latent", "observation"}:
            raise ValueError(
                "window_classifier_replay_storage must be 'latent' or 'observation'"
            )
        self.window_classifier_replay_capacity = max(
            1, int(window_classifier_replay_capacity)
        )
        self.window_classifier_replay_batch_size = max(
            2, int(window_classifier_replay_batch_size)
        )
        self.window_classifier_replay_min_positive = max(
            1,
            int(window_classifier_replay_min_positive),
        )
        self.window_classifier_replay_min_negative = max(
            1,
            int(window_classifier_replay_min_negative),
        )
        self._grouped_stopping_sidecar: _GroupedStoppingSidecar | None = None
        self._last_grouped_stopping_loss: GroupedStoppingLoss | None = None
        self._last_grouped_stopping_grad_norm = 0.0
        self._last_grouped_stopping_diagnostics = _GroupedStoppingDiagnostics()
        self._last_event_window_loss: GroupedStoppingLoss | None = None
        self._last_event_window_grad_norm = 0.0
        self._last_event_window_diagnostics = _GroupedStoppingDiagnostics()
        self._last_fire_boundary_loss: _FireBoundaryLoss | None = None
        self._last_fire_boundary_grad_norm = 0.0
        self._last_window_classifier_loss: _WindowClassifierLoss | None = None
        self._last_window_classifier_grad_norm = 0.0
        self._window_classifier_replay = (
            _WindowClassifierReplay(
                capacity=self.window_classifier_replay_capacity,
                storage=self.window_classifier_replay_storage,
            )
            if self.window_classifier_replay_enabled
            else None
        )
        self._support_preserving_collect_legal_open_age: np.ndarray | None = None
        self._support_preserving_collect_hold_count = 0
        self._support_preserving_collect_candidate_count = 0
        self._support_preserving_collect_quality_count = 0
        super().__init__(*args, **kwargs)

    def _first_event_label_collection_enabled(self) -> bool:
        return bool(
            self._first_event_enabled()
            or self._first_event_aux_enabled()
            or self._grouped_stopping_enabled()
            or self._event_window_enabled()
            or self._fire_boundary_enabled()
            or self._window_classifier_enabled()
        )

    def _should_use_device_rollout_buffer(self) -> bool:
        if getattr(self.device, "type", str(self.device)) != "cuda":
            return False
        if not isinstance(self.observation_space, spaces.Dict):
            return False
        env = getattr(self, "env", None)
        if env is None:
            return False
        if not hasattr(env, "get_policy_observation_torch"):
            return False
        return bool(getattr(env, "policy_observation_torch_bridge", False))

    def _setup_model(self) -> None:
        if self.rollout_buffer_class is None:
            if self._should_use_device_rollout_buffer():
                self.rollout_buffer_class = (
                    FirstEventDeviceDictRolloutBuffer
                    if self._first_event_label_collection_enabled()
                    else DeviceDictRolloutBuffer
                )
            elif self._first_event_label_collection_enabled() and isinstance(
                self.observation_space, spaces.Dict
            ):
                self.rollout_buffer_class = FirstEventDictRolloutBuffer
        super()._setup_model()

    def _get_policy_obs_tensor(self, env: VecEnv, obs) -> th.Tensor | dict[str, th.Tensor]:
        if getattr(self.device, "type", str(self.device)) == "cuda":
            getter = getattr(env, "get_policy_observation_torch", None)
            if callable(getter):
                try:
                    obs_tensor = getter(device=self.device)
                except Exception:
                    obs_tensor = None
                if obs_tensor is not None:
                    return obs_tensor
        return obs_as_tensor(obs, self.device)  # type: ignore[arg-type]

    @staticmethod
    def _is_device_rollout_buffer(rollout_buffer: RolloutBuffer) -> bool:
        return bool(getattr(rollout_buffer, "store_on_device", False))

    @staticmethod
    def _to_numpy_flat(values) -> np.ndarray:
        if th.is_tensor(values):
            return values.detach().float().cpu().numpy().reshape(-1)
        return np.asarray(values, dtype=np.float32).reshape(-1)

    def collect_rollouts(
        self,
        env: VecEnv,
        callback: BaseCallback,
        rollout_buffer: RolloutBuffer,
        n_rollout_steps: int,
    ) -> bool:
        assert self._last_obs is not None, "No previous observation was provided"
        self.policy.set_training_mode(False)
        set_training_progress = getattr(self.policy, "set_hmoe_training_progress", None)
        if callable(set_training_progress):
            set_training_progress(float(self._current_progress_remaining))

        n_steps = 0
        rollout_buffer.reset()
        self._grouped_stopping_sidecar = None
        self._last_grouped_stopping_loss = None
        self._last_grouped_stopping_grad_norm = 0.0
        self._last_grouped_stopping_diagnostics = _GroupedStoppingDiagnostics()
        self._last_event_window_loss = None
        self._last_event_window_grad_norm = 0.0
        self._last_event_window_diagnostics = _GroupedStoppingDiagnostics()
        self._last_fire_boundary_loss = None
        self._last_fire_boundary_grad_norm = 0.0
        self._last_window_classifier_loss = None
        self._last_window_classifier_grad_norm = 0.0
        self._support_preserving_collect_hold_count = 0
        self._support_preserving_collect_candidate_count = 0
        self._support_preserving_collect_quality_count = 0
        if self.use_sde:
            self.policy.reset_noise(env.num_envs)

        callback.on_rollout_start()
        collect_first_event = bool(
            self._first_event_label_collection_enabled()
            and getattr(rollout_buffer, "supports_first_event_labels", False)
        )
        engagement_state: list[str] = []
        fire_mask: list[bool] = []
        fire_once_accepted: list[bool] = []
        episode_id: list[int] = []
        launch_window_open: list[bool] = []
        existing_episode_id = getattr(self, "_first_event_env_episode_id", None)
        if (
            collect_first_event
            and isinstance(existing_episode_id, np.ndarray)
            and int(existing_episode_id.size) == int(env.num_envs)
        ):
            env_episode_id = existing_episode_id.astype(np.int64, copy=True)
        else:
            env_episode_id = np.arange(env.num_envs, dtype=np.int64)
        if collect_first_event and not hasattr(
            self, "_first_event_curriculum_seeded_episode_ids"
        ):
            self._first_event_curriculum_seeded_episode_ids = set()

        while n_steps < n_rollout_steps:
            if self.use_sde and self.sde_sample_freq > 0 and n_steps % self.sde_sample_freq == 0:
                self.policy.reset_noise(env.num_envs)

            with th.no_grad():
                obs_tensor = self._get_policy_obs_tensor(env, self._last_obs)
                actions_tensor, values, log_probs = self.policy(obs_tensor)
            policy_fire_mask = (
                self._first_event_policy_fire_mask_from_obs(obs_tensor, env.num_envs)
                if collect_first_event
                else None
            )
            policy_launch_window = (
                self._first_event_launch_window_from_policy_obs(obs_tensor, env.num_envs)
                if collect_first_event
                else None
            )
            support_hold_mask = self._support_preserving_collect_masks(
                fire_mask=policy_fire_mask,
                launch_window_open=policy_launch_window,
                n_envs=env.num_envs,
            )
            actions_tensor, log_probs = self._apply_support_preserving_collect_actions(
                obs_tensor,
                actions_tensor,
                log_probs,
                support_hold_mask,
            )
            actions = actions_tensor.detach().cpu().numpy()

            clipped_actions = actions
            if isinstance(self.action_space, spaces.Box):
                if self.policy.squash_output:
                    clipped_actions = self.policy.unscale_action(clipped_actions)
                else:
                    clipped_actions = np.clip(
                        actions, self.action_space.low, self.action_space.high
                    )

            new_obs, rewards, dones, infos = env.step(clipped_actions)
            self.num_timesteps += env.num_envs

            if collect_first_event:
                for env_idx, info in enumerate(infos):
                    row = info if isinstance(info, dict) else {}
                    if policy_fire_mask is not None and env_idx < len(policy_fire_mask):
                        policy_window_open = bool(policy_fire_mask[env_idx])
                    else:
                        policy_window_open = self._first_event_fire_mask_from_info(row)
                    engagement_state.append(
                        "AuthorizedReady"
                        if policy_window_open
                        else str(row.get("engagement_state", "") or "")
                    )
                    fire_mask.append(bool(policy_window_open))
                    fire_once_accepted.append(
                        self._first_event_bool(row.get("fire_once_accepted", False))
                    )
                    episode_id.append(int(env_episode_id[env_idx]))
                    if policy_launch_window is not None and env_idx < len(
                        policy_launch_window
                    ):
                        launch_window_open.append(bool(policy_launch_window[env_idx]))
                    else:
                        launch_window_open.append(bool(policy_window_open))

            callback.update_locals(locals())
            if not callback.on_step():
                return False

            self._update_info_buffer(infos, dones)
            n_steps += 1

            if isinstance(self.action_space, spaces.Discrete):
                actions = actions.reshape(-1, 1)

            for idx, done in enumerate(dones):
                if (
                    done
                    and infos[idx].get("terminal_observation") is not None
                    and infos[idx].get("TimeLimit.truncated", False)
                ):
                    terminal_obs = self.policy.obs_to_tensor(infos[idx]["terminal_observation"])[0]
                    with th.no_grad():
                        terminal_value = self.policy.predict_values(terminal_obs)[0]  # type: ignore[arg-type]
                    rewards[idx] += self.gamma * terminal_value

            rollout_buffer.add(
                obs_tensor if self._is_device_rollout_buffer(rollout_buffer) else self._last_obs,  # type: ignore[arg-type]
                actions_tensor if self._is_device_rollout_buffer(rollout_buffer) else actions,
                rewards,
                self._last_episode_starts,  # type: ignore[arg-type]
                values,
                log_probs,
            )
            self._last_obs = new_obs  # type: ignore[assignment]
            self._last_episode_starts = dones
            if collect_first_event:
                for env_idx, done in enumerate(dones):
                    if bool(done):
                        env_episode_id[env_idx] += env.num_envs
                        ages = getattr(
                            self, "_support_preserving_collect_legal_open_age", None
                        )
                        if isinstance(ages, np.ndarray) and int(ages.size) == int(env.num_envs):
                            ages[int(env_idx)] = 0

        with th.no_grad():
            values = self.policy.predict_values(self._get_policy_obs_tensor(env, new_obs))  # type: ignore[arg-type]

        if collect_first_event:
            self._first_event_env_episode_id = env_episode_id
            self._attach_first_event_labels_to_rollout_buffer(
                rollout_buffer,
                engagement_state=engagement_state,
                fire_mask=fire_mask,
                fire_once_accepted=fire_once_accepted,
                episode_id=episode_id,
                launch_window_open=(
                    launch_window_open if self.first_event_launch_window_enabled else None
                ),
                env_episode_id_after_rollout=env_episode_id,
            )
            if self._grouped_stopping_sidecar_enabled():
                self._grouped_stopping_sidecar = self._build_grouped_stopping_sidecar(
                    rollout_buffer,
                    fire_mask=fire_mask,
                    fire_once_accepted=fire_once_accepted,
                    episode_id=episode_id,
                    launch_window_open=launch_window_open,
                )
        rollout_buffer.compute_returns_and_advantage(last_values=values, dones=dones)

        callback.update_locals(locals())
        callback.on_rollout_end()
        return True

    def _apply_lr_multiplier(self) -> None:
        if self.policy is None:
            return
        apply_grouped_lr = getattr(self.policy, "apply_optimizer_learning_rate", None)
        if callable(apply_grouped_lr):
            base_lr = float(self.lr_schedule(self._current_progress_remaining))
            apply_grouped_lr(base_lr, lr_mult=float(self._lr_mult))
            return
        if self._lr_mult == 1.0:
            return
        for param_group in self.policy.optimizer.param_groups:
            param_group["lr"] = float(param_group["lr"]) * float(self._lr_mult)

    def _adapt_kl_controls(self, mean_kl: Optional[float]) -> None:
        if not self.kl_adaptive or self.target_kl is None:
            return
        if mean_kl is None or not np.isfinite(mean_kl):
            return

        target = float(self.target_kl)
        if target <= 0:
            return

        high = 1.5 * target
        low = (1.0 / 1.5) * target

        # If KL is too high: shrink step sizes and increase penalty.
        if mean_kl > high:
            self._low_kl_streak = 0
            self._lr_mult = max(self._lr_mult / self.kl_adapt_factor, self.lr_mult_min)
            self._clip_mult = max(self._clip_mult / self.kl_adapt_factor, self.clip_mult_min)
            if self.kl_penalty_coef > 0.0:
                self.kl_penalty_coef = min(
                    self.kl_penalty_coef * self.kl_adapt_factor, self.kl_penalty_coef_max
                )
            else:
                # Enable penalty if it was disabled.
                self.kl_penalty_coef = min(0.5, self.kl_penalty_coef_max)

        # If KL is too low: grow step sizes and relax penalty.
        elif mean_kl < low:
            self._low_kl_streak += 1
            if self._low_kl_streak >= self.low_kl_boost_patience:
                if self.boost_lr_on_low_kl:
                    self._lr_mult = min(self._lr_mult * self.kl_adapt_factor, self.lr_mult_max)
                if self.boost_clip_on_low_kl:
                    self._clip_mult = min(
                        self._clip_mult * self.kl_adapt_factor, self.clip_mult_max
                    )
                self.kl_penalty_coef = max(
                    self.kl_penalty_coef / self.kl_adapt_factor, self.kl_penalty_coef_min
                )
        else:
            self._low_kl_streak = 0

    def _action_mean_regularization_target_tensor(self, reference_actions: th.Tensor) -> th.Tensor:
        target = th.as_tensor(
            np.asarray(self.action_mean_regularization_target, dtype=np.float32).reshape(-1),
            dtype=reference_actions.dtype,
            device=reference_actions.device,
        )
        if int(target.numel()) == 1:
            return target.reshape(1, 1).expand_as(reference_actions)

        action_dim = int(np.prod(reference_actions.shape[1:]))
        if int(target.numel()) != action_dim:
            raise ValueError(
                "action_mean_regularization_target must be a scalar or match the flattened action dimension: "
                f"got {int(target.numel())}, expected {action_dim}"
            )
        return target.reshape((1, *reference_actions.shape[1:])).expand_as(reference_actions)

    def _action_mean_regularization_loss(
        self, obs, reference_actions: th.Tensor
    ) -> th.Tensor | None:
        if self.action_mean_regularization_coef <= 0.0:
            return None
        if not isinstance(self.action_space, spaces.Box):
            return None

        distribution = self.policy.get_distribution(obs)
        deterministic_actions = distribution.mode().reshape(reference_actions.shape)
        target = self._action_mean_regularization_target_tensor(reference_actions)
        return F.mse_loss(deterministic_actions, target, reduction="mean")

    def train(self) -> None:  # noqa: C901 - keep SB3-like structure for clarity
        # Switch to train mode (affects batch norm / dropout)
        self.policy.set_training_mode(True)

        set_training_progress = getattr(self.policy, "set_hmoe_training_progress", None)
        if callable(set_training_progress):
            set_training_progress(float(self._current_progress_remaining))

        # Update optimizer learning rate (schedule) then apply adaptive multiplier.
        self._update_learning_rate(self.policy.optimizer)
        self._apply_lr_multiplier()

        # Compute current clip range (+ adaptive multiplier)
        clip_range = float(self.clip_range(self._current_progress_remaining))  # type: ignore[operator]
        clip_range *= float(self._clip_mult)
        clip_range = float(np.clip(clip_range, 1e-4, 0.4))

        # Optional: clip range for the value function
        if self.clip_range_vf is not None:
            clip_range_vf = float(self.clip_range_vf(self._current_progress_remaining))  # type: ignore[operator]
        else:
            clip_range_vf = None

        # Per-epoch logging accumulators, owned by an explicit container. The
        # optimization loop appends to ``stats.*`` and the per-subdomain
        # ``_record_*_logs`` mixin methods read from it.
        stats = _TrainEpochStats()
        continue_training = True
        window_classifier_loss: _WindowClassifierLoss | None = None
        fire_boundary_loss: _FireBoundaryLoss | None = None
        event_window_loss: GroupedStoppingLoss | None = None
        grouped_stopping_loss: GroupedStoppingLoss | None = None

        # train for n_epochs epochs
        for epoch in range(self.n_epochs):
            # Do a complete pass on the rollout buffer
            for rollout_data in self.rollout_buffer.get(self.batch_size):
                separate_policy_margin_loss, separate_policy_margin_grad_norm = (
                    self._first_event_policy_margin_separate_update(rollout_data)
                    if self.event_policy_separate_update_enabled
                    else (None, 0.0)
                )
                if separate_policy_margin_loss is not None:
                    stats.first_event_policy_margin_separate_update_grad_norms.append(
                        float(separate_policy_margin_grad_norm)
                    )
                    stats.first_event_policy_margin_separate_update_counts.append(1)
                    stats.append_first_event_policy_margin_stats(separate_policy_margin_loss)

                actions = rollout_data.actions
                if isinstance(self.action_space, spaces.Discrete):
                    actions = rollout_data.actions.long().flatten()

                values, log_prob, entropy = self.policy.evaluate_actions(
                    rollout_data.observations, actions
                )
                values = values.flatten()

                # Normalize advantage
                advantages = rollout_data.advantages
                if self.normalize_advantage and len(advantages) > 1:
                    advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

                # ratio between old and new policy
                ratio = th.exp(log_prob - rollout_data.old_log_prob)

                # clipped surrogate loss
                policy_loss_1 = advantages * ratio
                policy_loss_2 = advantages * th.clamp(ratio, 1 - clip_range, 1 + clip_range)
                policy_loss = -th.min(policy_loss_1, policy_loss_2).mean()

                # Logging
                stats.pg_losses.append(policy_loss.item())
                clip_fraction = th.mean((th.abs(ratio - 1) > clip_range).float()).item()
                stats.clip_fractions.append(clip_fraction)

                # Value loss
                if clip_range_vf is None:
                    values_pred = values
                else:
                    values_pred = rollout_data.old_values + th.clamp(
                        values - rollout_data.old_values, -clip_range_vf, clip_range_vf
                    )
                value_loss = F.mse_loss(rollout_data.returns, values_pred)
                stats.value_losses.append(value_loss.item())

                # Entropy loss
                if entropy is None:
                    entropy_loss = -th.mean(-log_prob)
                else:
                    entropy_loss = -th.mean(entropy)
                stats.entropy_losses.append(entropy_loss.item())

                # Approximate reverse KL (with gradient)
                log_ratio = log_prob - rollout_data.old_log_prob
                approx_kl = th.mean((th.exp(log_ratio) - 1) - log_ratio)

                loss = policy_loss + self.ent_coef * entropy_loss + self.vf_coef * value_loss
                if self.kl_penalty_coef > 0.0:
                    loss = loss + float(self.kl_penalty_coef) * approx_kl
                action_mean_regularization_loss = self._action_mean_regularization_loss(
                    rollout_data.observations,
                    actions,
                )
                if action_mean_regularization_loss is not None:
                    stats.action_mean_regularization_losses.append(
                        float(action_mean_regularization_loss.detach().cpu())
                    )
                    loss = (
                        loss
                        + float(self.action_mean_regularization_coef)
                        * action_mean_regularization_loss
                    )
                first_event_hazard_loss = self._first_event_hazard_loss(rollout_data)
                if first_event_hazard_loss is not None:
                    stats.first_event_hazard_losses.append(
                        float(first_event_hazard_loss.loss.detach().cpu())
                    )
                    stats.first_event_hazard_active_counts.append(
                        int(first_event_hazard_loss.active_count)
                    )
                    stats.first_event_hazard_positive_fracs.append(
                        float(first_event_hazard_loss.positive_frac)
                    )
                    loss = loss + first_event_hazard_loss.loss
                if not self.event_policy_separate_update_enabled:
                    first_event_policy_margin_loss = self._first_event_policy_margin_loss(
                        rollout_data
                    )
                    if first_event_policy_margin_loss is not None:
                        stats.append_first_event_policy_margin_stats(first_event_policy_margin_loss)
                        loss = loss + first_event_policy_margin_loss.loss
                separate_credit_loss, separate_credit_grad_norm = (
                    self._first_event_credit_separate_value_update(rollout_data)
                    if self.event_credit_separate_update_enabled
                    else (None, 0.0)
                )
                if separate_credit_loss is not None:
                    stats.first_event_credit_separate_update_grad_norms.append(
                        float(separate_credit_grad_norm)
                    )
                    stats.first_event_credit_separate_update_counts.append(1)
                first_event_credit_loss = self._first_event_credit_loss(
                    rollout_data,
                    value_coef=0.0 if self.event_credit_separate_update_enabled else None,
                    projection_value_coef=0.0
                    if self.event_credit_separate_update_enabled
                    else None,
                )
                if first_event_credit_loss is not None:
                    total_credit_loss = first_event_credit_loss.loss
                    value_credit_loss = first_event_credit_loss.value_loss
                    if separate_credit_loss is not None:
                        total_credit_loss = total_credit_loss + separate_credit_loss.loss.detach()
                        value_credit_loss = separate_credit_loss.value_loss
                    stats.append_first_event_credit_stats(
                        first_event_credit_loss,
                        total_loss=total_credit_loss,
                        value_loss=value_credit_loss,
                        delta_align_loss=first_event_credit_loss.delta_align_loss,
                    )
                    loss = loss + first_event_credit_loss.loss
                elif separate_credit_loss is not None:
                    stats.append_first_event_credit_stats(separate_credit_loss)

                # Early stopping based on observed KL (same criterion as SB3 PPO)
                with th.no_grad():
                    approx_kl_div = float(approx_kl.detach().cpu().numpy())
                stats.approx_kl_divs.append(approx_kl_div)
                if self.target_kl is not None and approx_kl_div > 1.5 * float(self.target_kl):
                    continue_training = False
                    if self.verbose >= 1:
                        print(
                            f"Early stopping at epoch {epoch} due to reaching max kl: {approx_kl_div:.4f}"
                        )
                    break

                # Optimization step
                self.policy.optimizer.zero_grad()
                loss.backward()
                th.nn.utils.clip_grad_norm_(self.policy.parameters(), self.max_grad_norm)
                self.policy.optimizer.step()

            self._n_updates += 1
            if not continue_training:
                break

        window_classifier_loss = self._window_classifier_auxiliary_update()
        fire_boundary_loss = self._fire_boundary_auxiliary_update()
        event_window_loss = self._event_window_auxiliary_update()
        grouped_stopping_loss = self._grouped_stopping_auxiliary_update()

        explained_var = explained_variance(
            self._to_numpy_flat(self.rollout_buffer.values),
            self._to_numpy_flat(self.rollout_buffer.returns),
        )

        mean_kl = float(np.mean(stats.approx_kl_divs)) if len(stats.approx_kl_divs) > 0 else None
        self._adapt_kl_controls(mean_kl)

        # Logs
        self.logger.record("train/entropy_loss", float(np.mean(stats.entropy_losses)))
        self.logger.record("train/policy_gradient_loss", float(np.mean(stats.pg_losses)))
        self.logger.record("train/value_loss", float(np.mean(stats.value_losses)))
        self.logger.record(
            "train/approx_kl", float(np.mean(stats.approx_kl_divs)) if len(stats.approx_kl_divs) > 0 else 0.0
        )
        self.logger.record("train/clip_fraction", float(np.mean(stats.clip_fractions)))
        self.logger.record("train/loss", float(loss.item()))
        self.logger.record("train/explained_variance", float(explained_var))
        if hasattr(self.policy, "log_std"):
            self.logger.record("train/std", float(th.exp(self.policy.log_std).mean().item()))
        if self.action_mean_regularization_coef > 0.0:
            self.logger.record(
                "train/action_mean_regularization_loss",
                float(np.mean(stats.action_mean_regularization_losses))
                if stats.action_mean_regularization_losses
                else 0.0,
            )
            self.logger.record(
                "train/action_mean_regularization_coef", float(self.action_mean_regularization_coef)
            )
        if self._first_event_enabled():
            self._record_first_event_logs(stats)
        if self._window_classifier_enabled():
            self._record_window_classifier_logs(window_classifier_loss)
        if self._fire_boundary_enabled():
            self._record_fire_boundary_logs(fire_boundary_loss)
        if self._event_window_enabled():
            self._record_event_window_logs(event_window_loss)
        if self._grouped_stopping_enabled():
            self._record_grouped_stopping_logs(grouped_stopping_loss)
        if self._event_credit_enabled():
            self._record_event_credit_logs(stats)

        if self._event_policy_margin_enabled():
            self._record_event_policy_margin_logs(stats)

        self.logger.record("train/n_updates", int(self._n_updates), exclude="tensorboard")
        self.logger.record("train/clip_range", float(clip_range))
        if clip_range_vf is not None:
            self.logger.record("train/clip_range_vf", float(clip_range_vf))

        # Adaptive KL control logs
        self.logger.record("train/kl_penalty_coef", float(self.kl_penalty_coef))
        self.logger.record("train/kl_lr_mult", float(self._lr_mult))
        self.logger.record("train/kl_clip_mult", float(self._clip_mult))
        self.logger.record("train/kl_low_streak", int(self._low_kl_streak))
