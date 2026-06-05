from __future__ import annotations

from dataclasses import dataclass, replace
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

from python.mission_obs_taxonomy import (
    MISSION_OBS_AIR_COMBAT_C2_ROE_V1,
    MISSION_OBS_AIR_COMBAT_C2_ROE_V2,
    mission_observation_dim,
    mission_observation_field_index,
    mission_observation_has_field,
)

from .device_dict_rollout_buffer import DeviceDictRolloutBuffer
from .first_event_hazard import (
    A6_FIRST_EVENT_SOURCE_CURRICULUM,
    A6_FIRST_EVENT_SOURCE_DEADLINE,
    A6_FIRST_EVENT_SOURCE_EARLY_ACCEPTED,
    A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY,
    A6_FIRST_EVENT_SOURCE_PREWINDOW,
    A6_FIRST_EVENT_SOURCE_SHADOW_QUALITY,
    FirstEventCreditLoss,
    FirstEventHazardLabels,
    FirstEventPolicyMarginLoss,
    build_first_event_hazard_labels,
    compute_first_event_credit_loss,
    compute_first_event_hazard_loss,
    compute_first_event_policy_margin_loss,
    current_first_event_curriculum_coef,
    first_event_credit_batch_from_rollout_data,
    first_event_hazard_batch_from_rollout_data,
)
from .first_event_projection import project_air_combat_c2_roe_legal_open_observations
from .first_event_rollout_buffer import A6FirstEventDeviceDictRolloutBuffer, A6FirstEventDictRolloutBuffer
from .m3s1_grouped_stopping import (
    M3S1_CENSOR_EARLY_EVENT_PREFIX,
    M3S1_CENSOR_NONE,
    M3S1_CENSOR_TIMEOUT,
    M3S1_ROUTE_ON_POLICY,
    M3S1GroupedStoppingEvidence,
    M3S1GroupedStoppingLoss,
    compute_m3s1_grouped_stopping_loss,
)


_AIR_COMBAT_C2_ROE_MODES = (
    MISSION_OBS_AIR_COMBAT_C2_ROE_V1,
    MISSION_OBS_AIR_COMBAT_C2_ROE_V2,
)


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
    observations: dict[str, Any]
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


def _air_combat_c2_roe_mode_from_dim(dim: int) -> str | None:
    for mode in _AIR_COMBAT_C2_ROE_MODES:
        if int(dim) == int(mission_observation_dim(mode)):
            return mode
    return None


def _mission_column(mission: th.Tensor, mode: str, field_name: str) -> th.Tensor:
    return mission[:, mission_observation_field_index(mode, field_name)]


class AdaptiveKLPPO(PPO):
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
        a6_first_event_hazard_coef: float = 0.0,
        a6_first_event_curriculum_coef: float = 0.0,
        a6_first_event_curriculum_decay_fraction: float = 0.25,
        a6_first_event_curriculum_min_window_age_steps: int = 32,
        a6_first_event_censored_survival_weight: float = 0.0,
        a6_first_event_deadline_weight: float = 0.0,
        a6_first_event_deadline_min_window_age_steps: int = 96,
        a6_first_event_launch_window_enabled: bool = False,
        a6_first_event_launch_window_min_range_m: float = 0.0,
        a6_first_event_launch_window_max_range_m: float = 0.0,
        a6_first_event_launch_window_max_track_age_s: float = 10.0,
        a6_first_event_launch_window_min_window_age_steps: int = 1,
        a6_first_event_launch_window_prewindow_hold_weight: float = 0.0,
        a6_first_event_launch_window_early_accept_weight: float = 1.0,
        a7_event_credit_value_coef: float = 0.0,
        a7_event_credit_delta_align_coef: float = 0.0,
        a7_event_credit_delta_align_clip: float = 4.0,
        a7_event_credit_delta_align_positive_only: bool = False,
        a7_event_credit_positive_mass_cap: float = 1.0,
        a7_event_credit_negative_mass_cap: float = 1.0,
        a7_event_credit_prewindow_hold_weight: float = 0.0,
        a7_event_credit_early_accept_weight: float = 1.0,
        a7_event_credit_curriculum_coef: float = 0.0,
        a7_event_credit_curriculum_min_window_age_steps: int = 32,
        a7_event_credit_censored_survival_weight: float = 0.0,
        a7_event_credit_deadline_weight: float = 0.0,
        a7_event_credit_deadline_min_window_age_steps: int = 96,
        a7_event_credit_shadow_quality_weight: float = 1.0,
        a7_event_credit_legal_open_quality_weight: float = 0.0,
        a7_event_credit_legal_open_quality_min_window_age_steps: int = 1,
        a7_event_credit_legal_projection_enabled: bool = False,
        a7_event_credit_projection_value_coef: float = 0.0,
        a7_event_credit_projection_delta_align_coef: float = 0.0,
        a7_event_credit_separate_update_enabled: bool = False,
        a7_event_credit_separate_update_max_grad_norm: float = 0.5,
        a7_event_policy_margin_coef: float = 0.0,
        a7_event_policy_margin: float = 2.0,
        a7_event_policy_projection_margin_coef: float = 0.0,
        a7_event_policy_separate_update_enabled: bool = False,
        a7_event_policy_separate_update_max_grad_norm: float = 0.5,
        a7_event_policy_separate_update_steps: int = 1,
        m3s1_grouped_stopping_coef: float = 0.0,
        m3s1_grouped_stopping_early_mass_coef: float = 1.0,
        m3s1_grouped_stopping_early_mass_budget: float = 0.05,
        m3s1_grouped_stopping_prefix_early_mass_budget: float | None = None,
        m3s1_grouped_stopping_no_event_coef: float = 1.0,
        m3s1_grouped_stopping_boundary_threshold: float = 0.0,
        m3s1_grouped_stopping_detach_latent: bool = False,
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
        self.a6_first_event_hazard_coef = float(max(0.0, a6_first_event_hazard_coef))
        self.a6_first_event_curriculum_coef = float(max(0.0, a6_first_event_curriculum_coef))
        self.a6_first_event_curriculum_decay_fraction = float(max(0.0, a6_first_event_curriculum_decay_fraction))
        self.a6_first_event_curriculum_min_window_age_steps = max(
            1,
            int(a6_first_event_curriculum_min_window_age_steps),
        )
        self.a6_first_event_censored_survival_weight = float(max(0.0, a6_first_event_censored_survival_weight))
        self.a6_first_event_deadline_weight = float(max(0.0, a6_first_event_deadline_weight))
        self.a6_first_event_deadline_min_window_age_steps = max(
            1,
            int(a6_first_event_deadline_min_window_age_steps),
        )
        self.a6_first_event_launch_window_enabled = bool(a6_first_event_launch_window_enabled)
        self.a6_first_event_launch_window_min_range_m = float(max(0.0, a6_first_event_launch_window_min_range_m))
        self.a6_first_event_launch_window_max_range_m = float(max(0.0, a6_first_event_launch_window_max_range_m))
        self.a6_first_event_launch_window_max_track_age_s = float(a6_first_event_launch_window_max_track_age_s)
        self.a6_first_event_launch_window_min_window_age_steps = max(
            1,
            int(a6_first_event_launch_window_min_window_age_steps),
        )
        self.a6_first_event_launch_window_prewindow_hold_weight = float(
            max(0.0, a6_first_event_launch_window_prewindow_hold_weight)
        )
        self.a6_first_event_launch_window_early_accept_weight = float(
            max(0.0, a6_first_event_launch_window_early_accept_weight)
        )
        self.a7_event_credit_value_coef = float(max(0.0, a7_event_credit_value_coef))
        self.a7_event_credit_delta_align_coef = float(max(0.0, a7_event_credit_delta_align_coef))
        self.a7_event_credit_delta_align_clip = float(max(0.0, a7_event_credit_delta_align_clip))
        self.a7_event_credit_delta_align_positive_only = bool(a7_event_credit_delta_align_positive_only)
        self.a7_event_credit_positive_mass_cap = float(max(0.0, a7_event_credit_positive_mass_cap))
        self.a7_event_credit_negative_mass_cap = float(max(0.0, a7_event_credit_negative_mass_cap))
        self.a7_event_credit_prewindow_hold_weight = float(max(0.0, a7_event_credit_prewindow_hold_weight))
        self.a7_event_credit_early_accept_weight = float(max(0.0, a7_event_credit_early_accept_weight))
        self.a7_event_credit_curriculum_coef = float(max(0.0, a7_event_credit_curriculum_coef))
        self.a7_event_credit_curriculum_min_window_age_steps = max(
            1,
            int(a7_event_credit_curriculum_min_window_age_steps),
        )
        self.a7_event_credit_censored_survival_weight = float(max(0.0, a7_event_credit_censored_survival_weight))
        self.a7_event_credit_deadline_weight = float(max(0.0, a7_event_credit_deadline_weight))
        self.a7_event_credit_deadline_min_window_age_steps = max(
            1,
            int(a7_event_credit_deadline_min_window_age_steps),
        )
        self.a7_event_credit_shadow_quality_weight = float(max(0.0, a7_event_credit_shadow_quality_weight))
        self.a7_event_credit_legal_open_quality_weight = float(max(0.0, a7_event_credit_legal_open_quality_weight))
        self.a7_event_credit_legal_open_quality_min_window_age_steps = max(
            1,
            int(a7_event_credit_legal_open_quality_min_window_age_steps),
        )
        self.a7_event_credit_legal_projection_enabled = bool(a7_event_credit_legal_projection_enabled)
        self.a7_event_credit_projection_value_coef = float(max(0.0, a7_event_credit_projection_value_coef))
        self.a7_event_credit_projection_delta_align_coef = float(
            max(0.0, a7_event_credit_projection_delta_align_coef)
        )
        self.a7_event_credit_separate_update_enabled = bool(a7_event_credit_separate_update_enabled)
        self.a7_event_credit_separate_update_max_grad_norm = float(
            max(0.0, a7_event_credit_separate_update_max_grad_norm)
        )
        self.a7_event_policy_margin_coef = float(max(0.0, a7_event_policy_margin_coef))
        self.a7_event_policy_margin = float(max(0.0, a7_event_policy_margin))
        self.a7_event_policy_projection_margin_coef = float(max(0.0, a7_event_policy_projection_margin_coef))
        self.a7_event_policy_separate_update_enabled = bool(a7_event_policy_separate_update_enabled)
        self.a7_event_policy_separate_update_max_grad_norm = float(
            max(0.0, a7_event_policy_separate_update_max_grad_norm)
        )
        self.a7_event_policy_separate_update_steps = max(1, int(a7_event_policy_separate_update_steps))
        self.m3s1_grouped_stopping_coef = float(max(0.0, m3s1_grouped_stopping_coef))
        self.m3s1_grouped_stopping_early_mass_coef = float(max(0.0, m3s1_grouped_stopping_early_mass_coef))
        self.m3s1_grouped_stopping_early_mass_budget = float(max(0.0, m3s1_grouped_stopping_early_mass_budget))
        self.m3s1_grouped_stopping_prefix_early_mass_budget = (
            None
            if m3s1_grouped_stopping_prefix_early_mass_budget is None
            else float(max(0.0, m3s1_grouped_stopping_prefix_early_mass_budget))
        )
        self.m3s1_grouped_stopping_no_event_coef = float(max(0.0, m3s1_grouped_stopping_no_event_coef))
        self.m3s1_grouped_stopping_boundary_threshold = float(m3s1_grouped_stopping_boundary_threshold)
        self.m3s1_grouped_stopping_detach_latent = bool(m3s1_grouped_stopping_detach_latent)
        self._m3s1_grouped_stopping_sidecar: _M3S1GroupedStoppingSidecar | None = None
        self._m3s1_last_grouped_stopping_loss: M3S1GroupedStoppingLoss | None = None
        self._m3s1_last_grouped_stopping_grad_norm = 0.0
        self._m3s1_last_grouped_stopping_diagnostics = _M3S1GroupedStoppingDiagnostics()
        super().__init__(*args, **kwargs)

    def _a6_first_event_enabled(self) -> bool:
        return bool(
            self.a6_first_event_hazard_coef > 0.0
            or self.a6_first_event_curriculum_coef > 0.0
            or self.a6_first_event_censored_survival_weight > 0.0
            or self.a6_first_event_deadline_weight > 0.0
        )

    def _a7_event_credit_enabled(self) -> bool:
        return bool(
            self.a7_event_credit_value_coef > 0.0
            or self.a7_event_credit_delta_align_coef > 0.0
            or self.a7_event_credit_projection_value_coef > 0.0
            or self.a7_event_credit_projection_delta_align_coef > 0.0
        )

    def _a7_event_policy_margin_enabled(self) -> bool:
        return bool(
            self.a7_event_policy_margin_coef > 0.0
            or self.a7_event_policy_projection_margin_coef > 0.0
        )

    def _a7_first_event_aux_enabled(self) -> bool:
        return bool(self._a7_event_credit_enabled() or self._a7_event_policy_margin_enabled())

    def _m3s1_grouped_stopping_enabled(self) -> bool:
        return bool(float(getattr(self, "m3s1_grouped_stopping_coef", 0.0)) > 0.0)

    def _first_event_label_collection_enabled(self) -> bool:
        return bool(
            self._a6_first_event_enabled()
            or self._a7_first_event_aux_enabled()
            or self._m3s1_grouped_stopping_enabled()
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
                    A6FirstEventDeviceDictRolloutBuffer
                    if self._first_event_label_collection_enabled()
                    else DeviceDictRolloutBuffer
                )
            elif self._first_event_label_collection_enabled() and isinstance(self.observation_space, spaces.Dict):
                self.rollout_buffer_class = A6FirstEventDictRolloutBuffer
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

    @staticmethod
    def _a6_first_event_bool(value: Any) -> bool:
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)

    @classmethod
    def _a6_first_event_fire_mask_from_info(cls, info: Any) -> bool:
        if not isinstance(info, dict):
            return False
        if "fire_mask" in info:
            return cls._a6_first_event_bool(info.get("fire_mask"))
        event_mask = info.get("event_action_mask", None)
        if th.is_tensor(event_mask):
            values = event_mask.detach().cpu().reshape(-1).tolist()
        elif isinstance(event_mask, np.ndarray):
            values = event_mask.reshape(-1).tolist()
        elif isinstance(event_mask, (list, tuple)):
            values = list(event_mask)
        else:
            values = []
        if len(values) >= 2:
            return cls._a6_first_event_bool(values[1])
        return False

    @staticmethod
    def _a6_first_event_policy_fire_mask_from_obs(obs: Any, n_envs: int) -> list[bool] | None:
        if not isinstance(obs, dict):
            return None
        explicit_event_mask = obs.get("event_action_mask")
        if explicit_event_mask is not None:
            mask = th.as_tensor(explicit_event_mask)
            if mask.ndim == 1:
                mask = mask.reshape(1, -1)
            if mask.ndim == 2 and int(mask.shape[1]) >= 2 and int(mask.shape[0]) == int(n_envs):
                return [bool(value) for value in mask[:, 1].detach().cpu().reshape(-1).tolist()]
        explicit_fire_mask = obs.get("fire_mask")
        if explicit_fire_mask is not None:
            mask = th.as_tensor(explicit_fire_mask).reshape(-1)
            if int(mask.numel()) == int(n_envs):
                return [bool(value) for value in mask.detach().cpu().tolist()]
        mission = obs.get("mission")
        if mission is None:
            return None
        mission_tensor = th.as_tensor(mission)
        if mission_tensor.ndim != 2 or int(mission_tensor.shape[0]) != int(n_envs):
            return None
        mission_mode = _air_combat_c2_roe_mode_from_dim(int(mission_tensor.shape[1]))
        if mission_mode is None:
            return None
        if mission_observation_has_field(mission_mode, "fire_mask_open"):
            fire_mask = _mission_column(mission_tensor, mission_mode, "fire_mask_open") > 0.5
            return [bool(value) for value in fire_mask.detach().cpu().reshape(-1).tolist()]
        wcs_state = th.round(_mission_column(mission_tensor, mission_mode, "wcs_state").float()).to(dtype=th.long)
        authorization_to_fire = _mission_column(mission_tensor, mission_mode, "authorization_to_fire") > 0.5
        engage_order_state = th.round(
            _mission_column(mission_tensor, mission_mode, "engage_order_state").float()
        ).to(dtype=th.long)
        shot_policy_state = th.round(
            _mission_column(mission_tensor, mission_mode, "shot_policy_state").float()
        ).to(dtype=th.long)
        shot_budget_remaining = th.round(
            _mission_column(mission_tensor, mission_mode, "shot_budget_remaining").float()
        ).to(dtype=th.long)
        pending_assessment = _mission_column(mission_tensor, mission_mode, "pending_assessment") > 0.5
        target_contact_present = _mission_column(mission_tensor, mission_mode, "target_contact_present") > 0.5
        engage_hold = (
            (engage_order_state == 3)
            | (engage_order_state == 4)
            | (engage_order_state == 5)
            | (engage_order_state == 6)
        )
        fire_mask = (
            target_contact_present
            & authorization_to_fire
            & (wcs_state != 1)
            & ~engage_hold
            & (shot_policy_state > 0)
            & (shot_budget_remaining > 0)
            & ~pending_assessment
        )
        return [bool(value) for value in fire_mask.detach().cpu().reshape(-1).tolist()]

    @staticmethod
    def _a6_first_event_policy_launch_window_from_obs(
        obs: Any,
        n_envs: int,
        *,
        min_range_m: float = 0.0,
        max_range_m: float = 0.0,
        max_track_age_s: float = 10.0,
    ) -> list[bool] | None:
        if not isinstance(obs, dict):
            return None

        mission = obs.get("mission")
        if mission is not None:
            mission_tensor = th.as_tensor(mission)
            if mission_tensor.ndim == 2 and int(mission_tensor.shape[0]) == int(n_envs):
                mission_mode = _air_combat_c2_roe_mode_from_dim(int(mission_tensor.shape[1]))
                if mission_mode is not None and mission_observation_has_field(mission_mode, "launch_window_open"):
                    launch_window = _mission_column(mission_tensor, mission_mode, "launch_window_open") > 0.5
                    return [bool(value) for value in launch_window.detach().cpu().reshape(-1).tolist()]

        contacts_tensor = None
        contacts_history = obs.get("contacts_history")
        if contacts_history is not None:
            history = th.as_tensor(contacts_history)
            if history.ndim == 3 and int(n_envs) == 1 and int(history.shape[-1]) >= 5:
                history = history.reshape(1, *history.shape)
            if (
                history.ndim == 4
                and int(history.shape[0]) == int(n_envs)
                and int(history.shape[-1]) >= 5
                and int(history.shape[1]) > 0
            ):
                contacts_tensor = history[:, -1, :, :]

        if contacts_tensor is None:
            contacts = obs.get("contacts")
            if contacts is None:
                return None
            contacts_candidate = th.as_tensor(contacts)
            if contacts_candidate.ndim == 2 and int(n_envs) == 1 and int(contacts_candidate.shape[-1]) >= 5:
                contacts_candidate = contacts_candidate.reshape(1, *contacts_candidate.shape)
            if (
                contacts_candidate.ndim == 3
                and int(contacts_candidate.shape[0]) == int(n_envs)
                and int(contacts_candidate.shape[-1]) >= 5
            ):
                contacts_tensor = contacts_candidate

        if contacts_tensor is None:
            return None

        contacts_float = contacts_tensor.float()
        target_range_m = contacts_float[..., 0]
        track_age_s = contacts_float[..., 4]
        valid = th.isfinite(target_range_m) & (target_range_m > 0.0)

        min_range = float(max(0.0, min_range_m))
        if min_range > 0.0:
            valid = valid & (target_range_m >= min_range)

        max_range = float(max(0.0, max_range_m))
        if np.isfinite(max_range) and max_range > 0.0:
            valid = valid & (target_range_m <= max_range)

        max_age = float(max_track_age_s)
        if np.isfinite(max_age) and max_age >= 0.0:
            valid = valid & th.isfinite(track_age_s) & (track_age_s <= max_age)

        per_env = valid.any(dim=1)
        if int(per_env.numel()) != int(n_envs):
            return None
        return [bool(value) for value in per_env.detach().cpu().reshape(-1).tolist()]

    def _a6_first_event_launch_window_from_policy_obs(self, obs: Any, n_envs: int) -> list[bool] | None:
        if not self.a6_first_event_launch_window_enabled:
            return None
        return self._a6_first_event_policy_launch_window_from_obs(
            obs,
            n_envs,
            min_range_m=float(self.a6_first_event_launch_window_min_range_m),
            max_range_m=float(self.a6_first_event_launch_window_max_range_m),
            max_track_age_s=float(self.a6_first_event_launch_window_max_track_age_s),
        )

    def _build_a6_first_event_labels_from_rollout_infos(
        self,
        *,
        engagement_state: list[str],
        fire_mask: list[bool],
        fire_once_accepted: list[bool],
        episode_id: list[int],
        launch_window_open: list[bool] | None = None,
    ):
        use_a6_targets = self._a6_first_event_enabled()
        return build_first_event_hazard_labels(
            engagement_state=engagement_state,
            fire_mask=fire_mask,
            fire_once_accepted=fire_once_accepted,
            episode_id=episode_id,
            launch_window_open=launch_window_open,
            launch_window_min_window_age_steps=int(self.a6_first_event_launch_window_min_window_age_steps),
            launch_window_prewindow_hold_weight=(
                float(self.a6_first_event_launch_window_prewindow_hold_weight)
                if use_a6_targets
                else float(self.a7_event_credit_prewindow_hold_weight)
            ),
            launch_window_early_accept_weight=(
                float(self.a6_first_event_launch_window_early_accept_weight)
                if use_a6_targets
                else float(self.a7_event_credit_early_accept_weight)
            ),
            curriculum_weight=(
                float(self._current_a6_first_event_curriculum_coef())
                if use_a6_targets
                else float(self.a7_event_credit_curriculum_coef)
            ),
            curriculum_min_window_age_steps=(
                int(self.a6_first_event_curriculum_min_window_age_steps)
                if use_a6_targets
                else int(self.a7_event_credit_curriculum_min_window_age_steps)
            ),
            curriculum_blocked_episode_ids=getattr(
                self,
                "_a6_first_event_curriculum_seeded_episode_ids",
                set(),
            ),
            censored_survival_weight=(
                float(self.a6_first_event_censored_survival_weight)
                if use_a6_targets
                else float(self.a7_event_credit_censored_survival_weight)
            ),
            deadline_weight=(
                float(self.a6_first_event_deadline_weight)
                if use_a6_targets
                else float(self.a7_event_credit_deadline_weight)
            ),
            deadline_min_window_age_steps=(
                int(self.a6_first_event_deadline_min_window_age_steps)
                if use_a6_targets
                else int(self.a7_event_credit_deadline_min_window_age_steps)
            ),
            shadow_quality_after_early_accept=bool(
                not use_a6_targets and self.a7_event_credit_shadow_quality_weight > 0.0
            ),
            shadow_quality_positive_weight=(
                0.0
                if use_a6_targets
                else float(self.a7_event_credit_shadow_quality_weight)
            ),
            legal_open_quality_weight=(
                0.0
                if use_a6_targets
                else float(self.a7_event_credit_legal_open_quality_weight)
            ),
            legal_open_quality_min_window_age_steps=(
                1
                if use_a6_targets
                else int(self.a7_event_credit_legal_open_quality_min_window_age_steps)
            ),
            device=self.device,
        )

    @staticmethod
    def _slice_first_event_labels(
        labels: FirstEventHazardLabels,
        *,
        start: int,
        count: int,
    ) -> FirstEventHazardLabels:
        end = int(start) + int(count)
        return replace(
            labels,
            active=labels.active[start:end],
            target=labels.target[start:end],
            weight=labels.weight[start:end],
            source=labels.source[start:end],
            window_age=labels.window_age[start:end],
            window_id=labels.window_id[start:end],
            had_accepted=labels.had_accepted[start:end],
        )

    @staticmethod
    def _a7_first_event_rows_to_inputs(
        rows: list[_A7FirstEventRolloutRow],
    ) -> tuple[list[str], list[bool], list[bool], list[int], list[bool]]:
        return (
            [row.engagement_state for row in rows],
            [bool(row.fire_mask) for row in rows],
            [bool(row.fire_once_accepted) for row in rows],
            [int(row.episode_id) for row in rows],
            [bool(row.launch_window_open) for row in rows],
        )

    @staticmethod
    def _a7_first_event_rows_from_rollout_inputs(
        *,
        engagement_state: list[str],
        fire_mask: list[bool],
        fire_once_accepted: list[bool],
        episode_id: list[int],
        launch_window_open: list[bool],
    ) -> list[_A7FirstEventRolloutRow]:
        count = len(engagement_state)
        if not (
            len(fire_mask)
            == len(fire_once_accepted)
            == len(episode_id)
            == len(launch_window_open)
            == count
        ):
            raise ValueError("A7 first-event rollout rows must have the same flattened length")
        return [
            _A7FirstEventRolloutRow(
                engagement_state=str(engagement_state[idx]),
                fire_mask=bool(fire_mask[idx]),
                fire_once_accepted=bool(fire_once_accepted[idx]),
                episode_id=int(episode_id[idx]),
                launch_window_open=bool(launch_window_open[idx]),
            )
            for idx in range(count)
        ]

    @staticmethod
    def _a7_first_event_rows_by_env(
        rows: list[_A7FirstEventRolloutRow],
        *,
        n_envs: int,
    ) -> list[list[_A7FirstEventRolloutRow]]:
        env_count = max(1, int(n_envs))
        per_env: list[list[_A7FirstEventRolloutRow]] = [[] for _ in range(env_count)]
        for flat_idx, row in enumerate(rows):
            per_env[int(flat_idx) % env_count].append(row)
        return per_env

    def _a7_cross_rollout_first_event_enabled(self, launch_window_open: list[bool] | None) -> bool:
        return bool(
            not self._a6_first_event_enabled()
            and self._a7_first_event_aux_enabled()
            and launch_window_open is not None
        )

    def _get_a7_first_event_rollout_history(self, n_envs: int) -> list[list[_A7FirstEventRolloutRow]]:
        env_count = max(1, int(n_envs))
        history = getattr(self, "_a7_first_event_rollout_history", None)
        if not isinstance(history, list) or len(history) != env_count:
            history = [[] for _ in range(env_count)]
            self._a7_first_event_rollout_history = history
        return history

    def _a7_build_cross_rollout_first_event_labels(
        self,
        *,
        engagement_state: list[str],
        fire_mask: list[bool],
        fire_once_accepted: list[bool],
        episode_id: list[int],
        launch_window_open: list[bool],
        n_envs: int,
    ) -> tuple[
        FirstEventHazardLabels,
        FirstEventHazardLabels,
        list[list[_A7FirstEventRolloutRow]],
        int,
    ]:
        current_rows = self._a7_first_event_rows_from_rollout_inputs(
            engagement_state=engagement_state,
            fire_mask=fire_mask,
            fire_once_accepted=fire_once_accepted,
            episode_id=episode_id,
            launch_window_open=launch_window_open,
        )
        current_rows_by_env = self._a7_first_event_rows_by_env(current_rows, n_envs=n_envs)
        history = self._get_a7_first_event_rollout_history(n_envs)
        prefix_rows: list[_A7FirstEventRolloutRow] = []
        for env_idx, rows in enumerate(current_rows_by_env):
            if not rows:
                continue
            carried = history[env_idx]
            if carried and int(carried[-1].episode_id) == int(rows[0].episode_id):
                prefix_rows.extend(carried)

        local_labels = self._build_a6_first_event_labels_from_rollout_infos(
            engagement_state=engagement_state,
            fire_mask=fire_mask,
            fire_once_accepted=fire_once_accepted,
            episode_id=episode_id,
            launch_window_open=launch_window_open,
        )
        if not prefix_rows:
            return local_labels, local_labels, current_rows_by_env, 0

        combined_rows = [*prefix_rows, *current_rows]
        (
            combined_engagement_state,
            combined_fire_mask,
            combined_fire_once_accepted,
            combined_episode_id,
            combined_launch_window_open,
        ) = self._a7_first_event_rows_to_inputs(combined_rows)
        combined_labels = self._build_a6_first_event_labels_from_rollout_infos(
            engagement_state=combined_engagement_state,
            fire_mask=combined_fire_mask,
            fire_once_accepted=combined_fire_once_accepted,
            episode_id=combined_episode_id,
            launch_window_open=combined_launch_window_open,
        )
        labels = self._slice_first_event_labels(
            combined_labels,
            start=len(prefix_rows),
            count=len(current_rows),
        )
        return labels, local_labels, current_rows_by_env, len(prefix_rows)

    def _update_a7_first_event_rollout_history(
        self,
        *,
        current_rows_by_env: list[list[_A7FirstEventRolloutRow]],
        n_envs: int,
        env_episode_id_after_rollout: np.ndarray | list[int] | None,
    ) -> list[list[_A7FirstEventRolloutRow]]:
        history = self._get_a7_first_event_rollout_history(n_envs)
        final_episode_id: list[int] | None = None
        if env_episode_id_after_rollout is not None:
            final_array = np.asarray(env_episode_id_after_rollout, dtype=np.int64).reshape(-1)
            if int(final_array.size) == int(len(history)):
                final_episode_id = [int(value) for value in final_array.tolist()]

        for env_idx, rows in enumerate(current_rows_by_env):
            carried = history[env_idx]
            kept: list[_A7FirstEventRolloutRow] = []
            if rows and carried and int(carried[-1].episode_id) == int(rows[0].episode_id):
                kept = list(carried)
            elif not rows and carried:
                kept = list(carried)

            current_episode = int(kept[-1].episode_id) if kept else None
            for row in rows:
                row_episode = int(row.episode_id)
                if current_episode is None or row_episode != current_episode:
                    kept = []
                    current_episode = row_episode
                kept.append(row)

            if final_episode_id is not None:
                if not kept or int(kept[-1].episode_id) != int(final_episode_id[env_idx]):
                    kept = []
            history[env_idx] = kept
        return history

    def _a7_first_event_history_has_pending_shadow(self, rows: list[_A7FirstEventRolloutRow]) -> bool:
        if not rows:
            return False
        launch_min_age = max(1, int(self.a6_first_event_launch_window_min_window_age_steps))
        cursor = 0
        while cursor < len(rows):
            row = rows[cursor]
            if not (str(row.engagement_state) == "AuthorizedReady" and bool(row.fire_mask)):
                cursor += 1
                continue
            start = cursor
            while cursor < len(rows):
                window_row = rows[cursor]
                if not (str(window_row.engagement_state) == "AuthorizedReady" and bool(window_row.fire_mask)):
                    break
                cursor += 1
            for pos, window_row in enumerate(rows[start:cursor]):
                if not bool(window_row.fire_once_accepted):
                    continue
                age = int(pos) + 1
                quality_open = bool(window_row.launch_window_open) and age >= launch_min_age
                return not quality_open
        return False

    def _record_a7_cross_rollout_first_event_stats(
        self,
        *,
        labels: FirstEventHazardLabels,
        local_labels: FirstEventHazardLabels,
        history: list[list[_A7FirstEventRolloutRow]],
        prefix_count: int,
    ) -> None:
        active = labels.active.detach().cpu().reshape(-1).to(dtype=th.bool)
        target = labels.target.detach().cpu().reshape(-1)
        weight = labels.weight.detach().cpu().reshape(-1)
        source = labels.source.detach().cpu().reshape(-1).long()
        local_active = local_labels.active.detach().cpu().reshape(-1).to(dtype=th.bool)
        local_target = local_labels.target.detach().cpu().reshape(-1)
        local_weight = local_labels.weight.detach().cpu().reshape(-1)
        local_source = local_labels.source.detach().cpu().reshape(-1).long()
        positive_shadow = (
            active
            & (weight > 0.0)
            & (target > 0.5)
            & (source == int(A6_FIRST_EVENT_SOURCE_SHADOW_QUALITY))
        )
        local_positive_shadow = (
            local_active
            & (local_weight > 0.0)
            & (local_target > 0.5)
            & (local_source == int(A6_FIRST_EVENT_SOURCE_SHADOW_QUALITY))
        )
        recovered_shadow = positive_shadow & ~local_positive_shadow
        changed = (
            (active != local_active)
            | ((target - local_target).abs() > 1.0e-6)
            | ((weight - local_weight).abs() > 1.0e-6)
            | (source != local_source)
        )
        self._a7_cross_rollout_last_context_row_count = int(prefix_count)
        self._a7_cross_rollout_last_carried_shadow_positive_count = int(
            recovered_shadow.sum().item()
        )
        self._a7_cross_rollout_last_first_event_count = int(changed.sum().item())
        self._a7_cross_rollout_last_carried_shadow_pending_envs = int(
            sum(1 for rows in history if self._a7_first_event_history_has_pending_shadow(rows))
        )

    def _reset_a7_cross_rollout_first_event_stats(self) -> None:
        self._a7_cross_rollout_last_context_row_count = 0
        self._a7_cross_rollout_last_carried_shadow_positive_count = 0
        self._a7_cross_rollout_last_first_event_count = 0
        self._a7_cross_rollout_last_carried_shadow_pending_envs = 0

    def _record_a6_first_event_curriculum_seeds(self, labels, episode_id: list[int]) -> None:
        seeded = getattr(self, "_a6_first_event_curriculum_seeded_episode_ids", None)
        if seeded is None:
            seeded = set()
            self._a6_first_event_curriculum_seeded_episode_ids = seeded
        sources = labels.source.detach().cpu().reshape(-1).tolist()
        targets = labels.target.detach().cpu().reshape(-1).tolist()
        for idx, source in enumerate(sources):
            if int(source) == A6_FIRST_EVENT_SOURCE_CURRICULUM and float(targets[idx]) > 0.5:
                seeded.add(int(episode_id[idx]))

    @staticmethod
    def _m3s1_rollout_observation_snapshot(rollout_buffer: RolloutBuffer) -> dict[str, Any] | None:
        observations = getattr(rollout_buffer, "observations", None)
        if not isinstance(observations, dict):
            return None
        snapshot: dict[str, Any] = {}
        for key, value in observations.items():
            if th.is_tensor(value):
                snapshot[str(key)] = value.detach().cpu().clone()
            else:
                snapshot[str(key)] = np.array(value, copy=True)
        return snapshot

    def _build_m3s1_grouped_stopping_sidecar(
        self,
        rollout_buffer: RolloutBuffer,
        *,
        fire_mask: list[bool],
        fire_once_accepted: list[bool],
        episode_id: list[int],
        launch_window_open: list[bool],
    ) -> _M3S1GroupedStoppingSidecar | None:
        if not self._m3s1_grouped_stopping_enabled():
            return None
        n_envs = max(1, int(getattr(rollout_buffer, "n_envs", 1)))
        count = len(fire_mask)
        if not (len(fire_once_accepted) == len(episode_id) == len(launch_window_open) == count):
            raise ValueError("M3-S1 grouped stopping rollout rows must have the same flattened length")
        if count <= 0 or count % n_envs != 0:
            return None

        observations = self._m3s1_rollout_observation_snapshot(rollout_buffer)
        if observations is None:
            return None

        ordered_episodes: list[int] = []
        seen_episodes: set[int] = set()
        for value in episode_id:
            episode = int(value)
            if episode not in seen_episodes:
                ordered_episodes.append(episode)
                seen_episodes.add(episode)

        launch_min_age = max(1, int(self.a6_first_event_launch_window_min_window_age_steps))
        groups: list[_M3S1GroupedStoppingSidecarGroup] = []
        group_counter = 0
        accepted_event_count = 0
        one_shot_violation_count = 0
        closed_mask_accepted_event_count = 0
        for episode in ordered_episodes:
            indices = [idx for idx, value in enumerate(episode_id) if int(value) == episode]
            if not indices:
                continue
            full_accepted_indices = [idx for idx in indices if bool(fire_once_accepted[int(idx)])]
            accepted_event_count += len(full_accepted_indices)
            one_shot_violation_count += max(0, len(full_accepted_indices) - 1)
            closed_mask_accepted_event_count += sum(
                1 for idx in full_accepted_indices if not bool(fire_mask[int(idx)])
            )

            group_flat_indices: list[int] = []
            legal_mask: list[bool] = []
            quality: list[bool] = []
            accepted: list[bool] = []
            legal_window_age = 0
            for raw_idx in indices:
                flat_idx = int(raw_idx)
                is_legal = bool(fire_mask[flat_idx])
                if is_legal:
                    legal_window_age += 1
                else:
                    legal_window_age = 0
                group_flat_indices.append(flat_idx)
                legal_mask.append(is_legal)
                quality.append(
                    is_legal
                    and bool(launch_window_open[flat_idx])
                    and legal_window_age >= launch_min_age
                )
                accepted.append(bool(fire_once_accepted[flat_idx]))
                if accepted[-1]:
                    break

            accepted_positions = [idx for idx, value in enumerate(accepted) if bool(value)]
            if accepted_positions and not bool(quality[int(accepted_positions[0])]):
                censoring_kind = M3S1_CENSOR_EARLY_EVENT_PREFIX
                censor_step = int(group_flat_indices[int(accepted_positions[0])] // n_envs)
            elif accepted_positions:
                censoring_kind = M3S1_CENSOR_NONE
                censor_step = int(group_flat_indices[int(accepted_positions[0])] // n_envs)
            else:
                censoring_kind = M3S1_CENSOR_TIMEOUT
                censor_step = None

            groups.append(
                _M3S1GroupedStoppingSidecarGroup(
                    group_id=f"{episode}:{group_counter}",
                    episode_id=int(episode),
                    row_indices=tuple(group_flat_indices),
                    step_indices=tuple(int(value // n_envs) for value in group_flat_indices),
                    env_indices=tuple(int(value % n_envs) for value in group_flat_indices),
                    legal_mask=tuple(legal_mask),
                    quality_mask=tuple(quality),
                    accepted_event=tuple(accepted),
                    censoring_kind=censoring_kind,
                    censor_step=censor_step,
                    support_horizon=max(group_flat_indices),
                )
            )
            group_counter += 1

        return _M3S1GroupedStoppingSidecar(
            groups=tuple(groups),
            observations=observations,
            accepted_event_count=int(accepted_event_count),
            one_shot_violation_count=int(one_shot_violation_count),
            closed_mask_accepted_event_count=int(closed_mask_accepted_event_count),
        )

    def _attach_a6_first_event_labels_to_rollout_buffer(
        self,
        rollout_buffer: RolloutBuffer,
        *,
        engagement_state: list[str],
        fire_mask: list[bool],
        fire_once_accepted: list[bool],
        episode_id: list[int],
        launch_window_open: list[bool] | None = None,
        env_episode_id_after_rollout: np.ndarray | list[int] | None = None,
    ) -> FirstEventHazardLabels | None:
        if not self._first_event_label_collection_enabled():
            return None
        setter = getattr(rollout_buffer, "set_a6_first_event_labels", None)
        if not callable(setter):
            return None
        use_cross_rollout = self._a7_cross_rollout_first_event_enabled(launch_window_open)
        local_labels = None
        current_rows_by_env = None
        prefix_count = 0
        n_envs = max(1, int(getattr(rollout_buffer, "n_envs", 1)))
        if use_cross_rollout:
            assert launch_window_open is not None
            labels, local_labels, current_rows_by_env, prefix_count = (
                self._a7_build_cross_rollout_first_event_labels(
                    engagement_state=engagement_state,
                    fire_mask=fire_mask,
                    fire_once_accepted=fire_once_accepted,
                    episode_id=episode_id,
                    launch_window_open=launch_window_open,
                    n_envs=n_envs,
                )
            )
        else:
            self._reset_a7_cross_rollout_first_event_stats()
            labels = self._build_a6_first_event_labels_from_rollout_infos(
                engagement_state=engagement_state,
                fire_mask=fire_mask,
                fire_once_accepted=fire_once_accepted,
                episode_id=episode_id,
                launch_window_open=launch_window_open,
            )
        setter(labels)
        if use_cross_rollout and local_labels is not None and current_rows_by_env is not None:
            history = self._update_a7_first_event_rollout_history(
                current_rows_by_env=current_rows_by_env,
                n_envs=n_envs,
                env_episode_id_after_rollout=env_episode_id_after_rollout,
            )
            self._record_a7_cross_rollout_first_event_stats(
                labels=labels,
                local_labels=local_labels,
                history=history,
                prefix_count=prefix_count,
            )
        self._record_a6_first_event_curriculum_seeds(labels, episode_id)
        return labels

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
        self._m3s1_grouped_stopping_sidecar = None
        self._m3s1_last_grouped_stopping_loss = None
        self._m3s1_last_grouped_stopping_grad_norm = 0.0
        self._m3s1_last_grouped_stopping_diagnostics = _M3S1GroupedStoppingDiagnostics()
        if self.use_sde:
            self.policy.reset_noise(env.num_envs)

        callback.on_rollout_start()
        collect_a6_first_event = bool(
            self._first_event_label_collection_enabled()
            and getattr(rollout_buffer, "supports_a6_first_event_labels", False)
        )
        a6_engagement_state: list[str] = []
        a6_fire_mask: list[bool] = []
        a6_fire_once_accepted: list[bool] = []
        a6_episode_id: list[int] = []
        a6_launch_window_open: list[bool] = []
        existing_a6_episode_id = getattr(self, "_a6_first_event_env_episode_id", None)
        if (
            collect_a6_first_event
            and isinstance(existing_a6_episode_id, np.ndarray)
            and int(existing_a6_episode_id.size) == int(env.num_envs)
        ):
            a6_env_episode_id = existing_a6_episode_id.astype(np.int64, copy=True)
        else:
            a6_env_episode_id = np.arange(env.num_envs, dtype=np.int64)
        if collect_a6_first_event and not hasattr(self, "_a6_first_event_curriculum_seeded_episode_ids"):
            self._a6_first_event_curriculum_seeded_episode_ids = set()

        while n_steps < n_rollout_steps:
            if self.use_sde and self.sde_sample_freq > 0 and n_steps % self.sde_sample_freq == 0:
                self.policy.reset_noise(env.num_envs)

            with th.no_grad():
                obs_tensor = self._get_policy_obs_tensor(env, self._last_obs)
                actions_tensor, values, log_probs = self.policy(obs_tensor)
            a6_policy_fire_mask = (
                self._a6_first_event_policy_fire_mask_from_obs(obs_tensor, env.num_envs)
                if collect_a6_first_event
                else None
            )
            a6_policy_launch_window = (
                self._a6_first_event_launch_window_from_policy_obs(obs_tensor, env.num_envs)
                if collect_a6_first_event
                else None
            )
            actions = actions_tensor.detach().cpu().numpy()

            clipped_actions = actions
            if isinstance(self.action_space, spaces.Box):
                if self.policy.squash_output:
                    clipped_actions = self.policy.unscale_action(clipped_actions)
                else:
                    clipped_actions = np.clip(actions, self.action_space.low, self.action_space.high)

            new_obs, rewards, dones, infos = env.step(clipped_actions)
            self.num_timesteps += env.num_envs

            if collect_a6_first_event:
                for env_idx, info in enumerate(infos):
                    row = info if isinstance(info, dict) else {}
                    if a6_policy_fire_mask is not None and env_idx < len(a6_policy_fire_mask):
                        policy_window_open = bool(a6_policy_fire_mask[env_idx])
                    else:
                        policy_window_open = self._a6_first_event_fire_mask_from_info(row)
                    a6_engagement_state.append(
                        "AuthorizedReady" if policy_window_open else str(row.get("engagement_state", "") or "")
                    )
                    a6_fire_mask.append(bool(policy_window_open))
                    a6_fire_once_accepted.append(self._a6_first_event_bool(row.get("fire_once_accepted", False)))
                    a6_episode_id.append(int(a6_env_episode_id[env_idx]))
                    if a6_policy_launch_window is not None and env_idx < len(a6_policy_launch_window):
                        a6_launch_window_open.append(bool(a6_policy_launch_window[env_idx]))
                    else:
                        a6_launch_window_open.append(bool(policy_window_open))

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
            if collect_a6_first_event:
                for env_idx, done in enumerate(dones):
                    if bool(done):
                        a6_env_episode_id[env_idx] += env.num_envs

        with th.no_grad():
            values = self.policy.predict_values(self._get_policy_obs_tensor(env, new_obs))  # type: ignore[arg-type]

        if collect_a6_first_event:
            self._a6_first_event_env_episode_id = a6_env_episode_id
            self._attach_a6_first_event_labels_to_rollout_buffer(
                rollout_buffer,
                engagement_state=a6_engagement_state,
                fire_mask=a6_fire_mask,
                fire_once_accepted=a6_fire_once_accepted,
                episode_id=a6_episode_id,
                launch_window_open=(
                    a6_launch_window_open
                    if self.a6_first_event_launch_window_enabled
                    else None
                ),
                env_episode_id_after_rollout=a6_env_episode_id,
            )
            if self._m3s1_grouped_stopping_enabled():
                self._m3s1_grouped_stopping_sidecar = self._build_m3s1_grouped_stopping_sidecar(
                    rollout_buffer,
                    fire_mask=a6_fire_mask,
                    fire_once_accepted=a6_fire_once_accepted,
                    episode_id=a6_episode_id,
                    launch_window_open=a6_launch_window_open,
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
                self.kl_penalty_coef = min(self.kl_penalty_coef * self.kl_adapt_factor, self.kl_penalty_coef_max)
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
                    self._clip_mult = min(self._clip_mult * self.kl_adapt_factor, self.clip_mult_max)
                self.kl_penalty_coef = max(self.kl_penalty_coef / self.kl_adapt_factor, self.kl_penalty_coef_min)
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

    def _action_mean_regularization_loss(self, obs, reference_actions: th.Tensor) -> th.Tensor | None:
        if self.action_mean_regularization_coef <= 0.0:
            return None
        if not isinstance(self.action_space, spaces.Box):
            return None

        distribution = self.policy.get_distribution(obs)
        deterministic_actions = distribution.mode().reshape(reference_actions.shape)
        target = self._action_mean_regularization_target_tensor(reference_actions)
        return F.mse_loss(deterministic_actions, target, reduction="mean")

    def _current_a6_first_event_curriculum_coef(self) -> float:
        return current_first_event_curriculum_coef(
            self.a6_first_event_curriculum_coef,
            float(self._current_progress_remaining),
            decay_completed_fraction=float(self.a6_first_event_curriculum_decay_fraction),
        )

    def _first_event_hazard_loss(self, rollout_data):
        if not self._a6_first_event_enabled():
            return None
        batch = first_event_hazard_batch_from_rollout_data(rollout_data)
        if batch is None:
            return None
        active, target, weight = batch
        obs = rollout_data.observations
        distribution = self.policy.get_distribution(obs)
        logit_delta_getter = getattr(distribution, "fire_event_logit_delta", None)
        if not callable(logit_delta_getter):
            return None
        event_logit_delta = logit_delta_getter()
        if event_logit_delta is None:
            return None
        return compute_first_event_hazard_loss(
            event_logit_delta,
            target.to(device=event_logit_delta.device),
            active.to(device=event_logit_delta.device),
            weight.to(device=event_logit_delta.device),
            coef=float(self.a6_first_event_hazard_coef),
        )

    def _first_event_credit_loss(
        self,
        rollout_data,
        *,
        value_coef: float | None = None,
        delta_align_coef: float | None = None,
        projection_value_coef: float | None = None,
        projection_delta_align_coef: float | None = None,
        detach_credit_latent: bool = False,
    ):
        if not self._a7_event_credit_enabled():
            return None
        batch = first_event_credit_batch_from_rollout_data(rollout_data)
        if batch is None:
            return None
        active, target, weight, window_id, source = batch
        obs = rollout_data.observations
        if detach_credit_latent:
            q_values_getter = getattr(self.policy, "get_hybrid_event_credit_values", None)
            if not callable(q_values_getter):
                return None
            q_values = q_values_getter(obs, detach_latent=True)
            distribution = None
        else:
            distribution = self.policy.get_distribution(obs)
            q_values_getter = getattr(distribution, "fire_event_q_values", None)
            if not callable(q_values_getter):
                return None
            q_values = q_values_getter()
        if q_values is None:
            return None
        logit_delta = None
        if distribution is not None:
            logit_delta_getter = getattr(distribution, "fire_event_logit_delta", None)
            if callable(logit_delta_getter):
                logit_delta = logit_delta_getter()
        delta_align_active = None
        if source is not None:
            delta_align_active = source.to(device=q_values.device) != int(A6_FIRST_EVENT_SOURCE_SHADOW_QUALITY)
        if self.a7_event_credit_delta_align_positive_only and logit_delta is not None:
            positive_credit = (q_values[:, 1] - q_values[:, 0]).detach() > 0.0
            delta_align_active = (
                positive_credit
                if delta_align_active is None
                else delta_align_active.to(device=q_values.device).reshape(-1).to(dtype=th.bool) & positive_credit
            )
        base_loss = compute_first_event_credit_loss(
            q_values,
            target.to(device=q_values.device),
            active.to(device=q_values.device),
            weight.to(device=q_values.device),
            event_logit_delta=logit_delta,
            window_id=window_id.to(device=q_values.device) if window_id is not None else None,
            value_coef=(
                float(self.a7_event_credit_value_coef)
                if value_coef is None
                else float(max(0.0, value_coef))
            ),
            delta_align_coef=(
                float(self.a7_event_credit_delta_align_coef)
                if delta_align_coef is None
                else float(max(0.0, delta_align_coef))
            ),
            delta_align_clip=float(self.a7_event_credit_delta_align_clip),
            delta_align_active=delta_align_active,
            positive_mass_cap=float(self.a7_event_credit_positive_mass_cap),
            negative_mass_cap=float(self.a7_event_credit_negative_mass_cap),
        )
        source_stats: dict[str, int] = {}
        if source is not None:
            source_flat = source.to(device=q_values.device).reshape(-1).long()
            active_flat = active.to(device=q_values.device).reshape(-1).to(dtype=th.bool)
            weight_flat = weight.to(device=q_values.device).reshape(-1)
            source_active = active_flat & (weight_flat > 0.0)

            def _source_count(value: int) -> int:
                return int((source_active & (source_flat == int(value))).sum().detach().cpu().item())

            positive_flat = target.to(device=q_values.device).reshape(-1) > 0.5
            advantage = q_values[:, 1] - q_values[:, 0]
            legal_open_quality_mask = source_active & (
                source_flat == int(A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY)
            )

            def _source_positive_count(value: int) -> int:
                return int(
                    (
                        source_active
                        & positive_flat
                        & (source_flat == int(value))
                    ).sum().detach().cpu().item()
                )

            def _source_advantage_mean(mask: th.Tensor) -> float:
                selected = advantage[mask]
                return (
                    float(selected.detach().mean().cpu().item())
                    if int(selected.numel()) > 0
                    else 0.0
                )

            source_stats = {
                "source_shadow_count": _source_count(A6_FIRST_EVENT_SOURCE_SHADOW_QUALITY),
                "source_deadline_count": _source_count(A6_FIRST_EVENT_SOURCE_DEADLINE),
                "source_early_accepted_count": _source_count(A6_FIRST_EVENT_SOURCE_EARLY_ACCEPTED),
                "source_prewindow_count": _source_count(A6_FIRST_EVENT_SOURCE_PREWINDOW),
                "source_legal_open_quality_count": _source_count(A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY),
                "source_legal_open_quality_positive_count": _source_positive_count(
                    A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY
                ),
                "source_deadline_positive_count": _source_positive_count(A6_FIRST_EVENT_SOURCE_DEADLINE),
                "source_shadow_positive_count": _source_positive_count(A6_FIRST_EVENT_SOURCE_SHADOW_QUALITY),
                "source_legal_open_quality_advantage_mean": _source_advantage_mean(legal_open_quality_mask),
            }
            base_loss = replace(
                base_loss,
                projection_candidate_count=source_stats["source_shadow_count"],
                **source_stats,
            )
        if (
            not self.a7_event_credit_legal_projection_enabled
            or source is None
            or (
                self.a7_event_credit_projection_value_coef <= 0.0
                and self.a7_event_credit_projection_delta_align_coef <= 0.0
            )
            or (
                projection_value_coef is not None
                and projection_delta_align_coef is not None
                and float(projection_value_coef) <= 0.0
                and float(projection_delta_align_coef) <= 0.0
            )
        ):
            return base_loss

        shadow_active = (
            active.to(device=q_values.device).reshape(-1).to(dtype=th.bool)
            & (source.to(device=q_values.device).reshape(-1).long() == int(A6_FIRST_EVENT_SOURCE_SHADOW_QUALITY))
        )
        projection = project_air_combat_c2_roe_legal_open_observations(obs, shadow_active)
        if projection is None:
            return FirstEventCreditLoss(
                loss=base_loss.loss,
                value_loss=base_loss.value_loss,
                delta_align_loss=base_loss.delta_align_loss,
                unscaled_value_loss=base_loss.unscaled_value_loss,
                unscaled_delta_align_loss=base_loss.unscaled_delta_align_loss,
                active_count=base_loss.active_count,
                positive_count=base_loss.positive_count,
                weight_sum=base_loss.weight_sum,
                positive_frac=base_loss.positive_frac,
                advantage_mean=base_loss.advantage_mean,
                advantage_abs_mean=base_loss.advantage_abs_mean,
                projection_candidate_count=int(shadow_active.sum().detach().cpu().item()),
                projection_unsupported_count=int(shadow_active.sum().detach().cpu().item()),
                **source_stats,
            )
        projected_active = projection.active.to(device=q_values.device).reshape(-1).to(dtype=th.bool)
        if int(projected_active.sum().detach().cpu().item()) <= 0:
            return FirstEventCreditLoss(
                loss=base_loss.loss,
                value_loss=base_loss.value_loss,
                delta_align_loss=base_loss.delta_align_loss,
                unscaled_value_loss=base_loss.unscaled_value_loss,
                unscaled_delta_align_loss=base_loss.unscaled_delta_align_loss,
                active_count=base_loss.active_count,
                positive_count=base_loss.positive_count,
                weight_sum=base_loss.weight_sum,
                positive_frac=base_loss.positive_frac,
                advantage_mean=base_loss.advantage_mean,
                advantage_abs_mean=base_loss.advantage_abs_mean,
                projection_candidate_count=int(shadow_active.sum().detach().cpu().item()),
                projection_unsupported_count=int(projection.unsupported_count),
                **source_stats,
            )

        if detach_credit_latent:
            projected_q_getter = getattr(self.policy, "get_hybrid_event_credit_values", None)
            if not callable(projected_q_getter):
                return base_loss
            projected_q_values = projected_q_getter(projection.observations, detach_latent=True)
            projected_distribution = None
        else:
            projected_distribution = self.policy.get_distribution(projection.observations)
            projected_q_getter = getattr(projected_distribution, "fire_event_q_values", None)
            if not callable(projected_q_getter):
                return base_loss
            projected_q_values = projected_q_getter()
        if projected_q_values is None:
            return base_loss
        projected_delta = None
        if projected_distribution is not None:
            projected_delta_getter = getattr(projected_distribution, "fire_event_logit_delta", None)
            if callable(projected_delta_getter):
                projected_delta = projected_delta_getter()
        projected_targets = th.ones_like(target.to(device=q_values.device, dtype=th.float32).reshape(-1))
        projection_loss = compute_first_event_credit_loss(
            projected_q_values,
            projected_targets.to(device=projected_q_values.device),
            projected_active.to(device=projected_q_values.device),
            weight.to(device=projected_q_values.device),
            event_logit_delta=projected_delta,
            window_id=window_id.to(device=projected_q_values.device) if window_id is not None else None,
            value_coef=(
                float(self.a7_event_credit_projection_value_coef)
                if projection_value_coef is None
                else float(max(0.0, projection_value_coef))
            ),
            delta_align_coef=(
                float(self.a7_event_credit_projection_delta_align_coef)
                if projection_delta_align_coef is None
                else float(max(0.0, projection_delta_align_coef))
            ),
            delta_align_clip=float(self.a7_event_credit_delta_align_clip),
            delta_align_active=(
                projected_active.to(device=projected_q_values.device)
                if not self.a7_event_credit_delta_align_positive_only or projected_delta is None
                else (
                    projected_active.to(device=projected_q_values.device)
                    & ((projected_q_values[:, 1] - projected_q_values[:, 0]).detach() > 0.0)
                )
            ),
            positive_mass_cap=float(self.a7_event_credit_positive_mass_cap),
            negative_mass_cap=float(self.a7_event_credit_negative_mass_cap),
        )
        projected_advantage = projected_q_values[:, 1] - projected_q_values[:, 0]
        projected_weighted_advantage = projected_advantage[projected_active.to(device=projected_q_values.device)]
        projection_advantage_mean = (
            float(projected_weighted_advantage.detach().mean().cpu().item())
            if int(projected_weighted_advantage.numel()) > 0
            else 0.0
        )
        projection_delta_mean = 0.0
        if projected_delta is not None:
            projected_delta_active = projected_delta.reshape(-1)[projected_active.to(device=projected_delta.device)]
            projection_delta_mean = (
                float(projected_delta_active.detach().mean().cpu().item())
                if int(projected_delta_active.numel()) > 0
                else 0.0
            )
        combined_active = int(base_loss.active_count) + int(projection_loss.active_count)
        combined_positive = int(base_loss.positive_count) + int(projection_loss.positive_count)
        return FirstEventCreditLoss(
            loss=base_loss.loss + projection_loss.loss,
            value_loss=base_loss.value_loss + projection_loss.value_loss,
            delta_align_loss=base_loss.delta_align_loss + projection_loss.delta_align_loss,
            unscaled_value_loss=base_loss.unscaled_value_loss + projection_loss.unscaled_value_loss,
            unscaled_delta_align_loss=base_loss.unscaled_delta_align_loss
            + projection_loss.unscaled_delta_align_loss,
            active_count=combined_active,
            positive_count=combined_positive,
            weight_sum=float(base_loss.weight_sum) + float(projection_loss.weight_sum),
            positive_frac=(float(combined_positive) / float(combined_active)) if combined_active > 0 else 0.0,
            advantage_mean=base_loss.advantage_mean,
            advantage_abs_mean=base_loss.advantage_abs_mean,
            projection_active_count=int(projection_loss.active_count),
            projection_candidate_count=int(shadow_active.sum().detach().cpu().item()),
            projection_unsupported_count=int(projection.unsupported_count),
            projection_advantage_mean=projection_advantage_mean,
            projection_delta_mean=projection_delta_mean,
            **source_stats,
        )

    def _first_event_policy_margin_loss(
        self,
        rollout_data,
        *,
        coef: float | None = None,
        projection_coef: float | None = None,
    ) -> FirstEventPolicyMarginLoss | None:
        if not self._a7_event_policy_margin_enabled():
            return None
        batch = first_event_credit_batch_from_rollout_data(rollout_data)
        if batch is None:
            return None
        active, target, weight, window_id, source = batch
        distribution = self.policy.get_distribution(rollout_data.observations)
        logit_delta_getter = getattr(distribution, "fire_event_logit_delta", None)
        if not callable(logit_delta_getter):
            return None
        logit_delta = logit_delta_getter()
        if logit_delta is None:
            return None

        policy_active = None
        if source is not None:
            policy_active = source.to(device=logit_delta.device) != int(A6_FIRST_EVENT_SOURCE_SHADOW_QUALITY)
        base_loss = compute_first_event_policy_margin_loss(
            logit_delta,
            target.to(device=logit_delta.device),
            active.to(device=logit_delta.device),
            weight.to(device=logit_delta.device),
            window_id=window_id.to(device=logit_delta.device) if window_id is not None else None,
            policy_active=policy_active,
            coef=(
                float(self.a7_event_policy_margin_coef)
                if coef is None
                else float(max(0.0, coef))
            ),
            margin=float(self.a7_event_policy_margin),
            positive_mass_cap=float(self.a7_event_credit_positive_mass_cap),
            negative_mass_cap=float(self.a7_event_credit_negative_mass_cap),
        )

        projection_margin_coef = (
            float(self.a7_event_policy_projection_margin_coef)
            if projection_coef is None
            else float(max(0.0, projection_coef))
        )
        if (
            projection_margin_coef <= 0.0
            or not self.a7_event_credit_legal_projection_enabled
            or source is None
        ):
            return base_loss

        shadow_active = (
            active.to(device=logit_delta.device).reshape(-1).to(dtype=th.bool)
            & (source.to(device=logit_delta.device).reshape(-1).long() == int(A6_FIRST_EVENT_SOURCE_SHADOW_QUALITY))
        )
        projection = project_air_combat_c2_roe_legal_open_observations(rollout_data.observations, shadow_active)
        if projection is None:
            return replace(
                base_loss,
                projection_active_count=int(shadow_active.sum().detach().cpu().item()),
            )
        projected_active = projection.active.to(device=logit_delta.device).reshape(-1).to(dtype=th.bool)
        if int(projected_active.sum().detach().cpu().item()) <= 0:
            return replace(base_loss, projection_active_count=0)

        projected_distribution = self.policy.get_distribution(projection.observations)
        projected_delta_getter = getattr(projected_distribution, "fire_event_logit_delta", None)
        if not callable(projected_delta_getter):
            return base_loss
        projected_delta = projected_delta_getter()
        if projected_delta is None:
            return base_loss
        projected_targets = th.ones_like(target.to(device=projected_delta.device, dtype=th.float32).reshape(-1))
        projection_loss = compute_first_event_policy_margin_loss(
            projected_delta,
            projected_targets,
            projected_active.to(device=projected_delta.device),
            weight.to(device=projected_delta.device),
            window_id=window_id.to(device=projected_delta.device) if window_id is not None else None,
            coef=projection_margin_coef,
            margin=float(self.a7_event_policy_margin),
            positive_mass_cap=float(self.a7_event_credit_positive_mass_cap),
            negative_mass_cap=float(self.a7_event_credit_negative_mass_cap),
        )
        projected_delta_active = projected_delta.reshape(-1)[projected_active.to(device=projected_delta.device)]
        projection_delta_mean = (
            float(projected_delta_active.detach().mean().cpu().item())
            if int(projected_delta_active.numel()) > 0
            else 0.0
        )
        combined_active = int(base_loss.active_count) + int(projection_loss.active_count)
        combined_positive = int(base_loss.positive_count) + int(projection_loss.positive_count)
        return FirstEventPolicyMarginLoss(
            loss=base_loss.loss + projection_loss.loss,
            unscaled_loss=base_loss.unscaled_loss + projection_loss.unscaled_loss,
            active_count=combined_active,
            positive_count=combined_positive,
            weight_sum=float(base_loss.weight_sum) + float(projection_loss.weight_sum),
            positive_frac=(float(combined_positive) / float(combined_active)) if combined_active > 0 else 0.0,
            delta_mean=base_loss.delta_mean,
            delta_positive_frac=base_loss.delta_positive_frac,
            projection_active_count=int(projection_loss.active_count),
            projection_delta_mean=projection_delta_mean,
        )

    def _a7_event_credit_head_parameters(self) -> list[th.nn.Parameter]:
        credit_head = getattr(self.policy, "hybrid_event_credit_head", None)
        if credit_head is None:
            return []
        return [param for param in credit_head.parameters() if param.requires_grad]

    def _a7_event_policy_margin_parameters(self) -> list[th.nn.Parameter]:
        selected: list[th.nn.Parameter] = []
        action_net = getattr(self.policy, "action_net", None)
        if action_net is not None:
            selected.extend(param for param in action_net.parameters() if param.requires_grad)
        event_head = getattr(self.policy, "hybrid_event_head", None)
        if event_head is not None:
            selected.extend(param for param in event_head.parameters() if param.requires_grad)
        mlp_extractor = getattr(self.policy, "mlp_extractor", None)
        policy_net = getattr(mlp_extractor, "policy_net", None)
        if policy_net is not None:
            selected.extend(param for param in policy_net.parameters() if param.requires_grad)
        return selected

    def _first_event_policy_margin_separate_update(
        self,
        rollout_data,
    ) -> tuple[FirstEventPolicyMarginLoss | None, float]:
        if not self.a7_event_policy_separate_update_enabled:
            return None, 0.0
        selected_params = self._a7_event_policy_margin_parameters()
        if not selected_params:
            return None, 0.0

        selected_ids = {id(param) for param in selected_params}
        last_margin_loss: FirstEventPolicyMarginLoss | None = None
        max_grad_norm_seen = 0.0
        for _ in range(int(self.a7_event_policy_separate_update_steps)):
            margin_loss = self._first_event_policy_margin_loss(
                rollout_data,
                coef=float(self.a7_event_policy_margin_coef),
                projection_coef=float(self.a7_event_policy_projection_margin_coef),
            )
            if margin_loss is None:
                break
            self.policy.optimizer.zero_grad(set_to_none=True)
            margin_loss.loss.backward()
            for param in self.policy.parameters():
                if id(param) not in selected_ids:
                    param.grad = None
            max_norm = float(self.a7_event_policy_separate_update_max_grad_norm)
            if max_norm > 0.0:
                grad_norm_tensor = th.nn.utils.clip_grad_norm_(selected_params, max_norm)
                grad_norm = float(grad_norm_tensor.detach().cpu().item())
            else:
                grad_norm = 0.0
            max_grad_norm_seen = max(max_grad_norm_seen, grad_norm)
            self.policy.optimizer.step()
            self.policy.optimizer.zero_grad(set_to_none=True)
            last_margin_loss = margin_loss
        return last_margin_loss, max_grad_norm_seen

    def _first_event_credit_separate_value_update(
        self,
        rollout_data,
    ) -> tuple[FirstEventCreditLoss | None, float]:
        if not self.a7_event_credit_separate_update_enabled:
            return None, 0.0
        credit_params = self._a7_event_credit_head_parameters()
        if not credit_params:
            return None, 0.0

        credit_loss = self._first_event_credit_loss(
            rollout_data,
            value_coef=float(self.a7_event_credit_value_coef),
            delta_align_coef=0.0,
            projection_value_coef=float(self.a7_event_credit_projection_value_coef),
            projection_delta_align_coef=0.0,
            detach_credit_latent=True,
        )
        if credit_loss is None:
            return None, 0.0

        self.policy.optimizer.zero_grad(set_to_none=True)
        credit_loss.loss.backward()
        max_norm = float(self.a7_event_credit_separate_update_max_grad_norm)
        if max_norm > 0.0:
            grad_norm_tensor = th.nn.utils.clip_grad_norm_(credit_params, max_norm)
            grad_norm = float(grad_norm_tensor.detach().cpu().item())
        else:
            grad_norm = 0.0
        self.policy.optimizer.step()
        self.policy.optimizer.zero_grad(set_to_none=True)
        return credit_loss, grad_norm

    def _m3s1_observations_for_group(
        self,
        sidecar: _M3S1GroupedStoppingSidecar,
        group: _M3S1GroupedStoppingSidecarGroup,
    ) -> dict[str, th.Tensor]:
        observations: dict[str, th.Tensor] = {}
        for key, source in sidecar.observations.items():
            rows = []
            for step_idx, env_idx in zip(group.step_indices, group.env_indices):
                if th.is_tensor(source):
                    rows.append(source[int(step_idx), int(env_idx)].to(device=self.device))
                else:
                    rows.append(th.as_tensor(source[int(step_idx), int(env_idx)], device=self.device))
            observations[str(key)] = th.stack(rows, dim=0)
        return observations

    @staticmethod
    def _m3s1_extend_float_values(values: list[float], tensor: th.Tensor) -> None:
        values.extend(float(value) for value in tensor.detach().cpu().reshape(-1).tolist())

    @staticmethod
    def _m3s1_group_order(group: _M3S1GroupedStoppingSidecarGroup, *, device: th.device) -> th.Tensor:
        env_indices = th.as_tensor(group.env_indices, device=device).reshape(-1).to(dtype=th.long)
        step_indices = th.as_tensor(group.step_indices, device=device).reshape(-1).to(dtype=th.long)
        if int(step_indices.numel()) <= 0:
            return th.empty((0,), dtype=th.long, device=device)
        env_stride = max(1, int(env_indices.max().detach().cpu().item()) + 1)
        return th.argsort(step_indices * env_stride + env_indices)

    def _m3s1_event_logit_delta_diagnostic(self, obs: dict[str, th.Tensor]) -> th.Tensor | None:
        distribution_getter = getattr(self.policy, "get_distribution", None)
        if not callable(distribution_getter):
            return None
        with th.no_grad():
            distribution = distribution_getter(obs)
            logit_delta_getter = getattr(distribution, "fire_event_logit_delta", None)
            if not callable(logit_delta_getter):
                return None
            logit_delta = logit_delta_getter()
            if logit_delta is None:
                return None
            return logit_delta.reshape(-1).detach()

    def _m3s1_group_diagnostic_masks(
        self,
        group: _M3S1GroupedStoppingSidecarGroup,
        logits: th.Tensor,
    ) -> tuple[th.Tensor, th.Tensor, th.Tensor, th.Tensor, th.Tensor]:
        device = logits.device
        order = self._m3s1_group_order(group, device=device)
        legal = th.as_tensor(group.legal_mask, device=device).reshape(-1).to(dtype=th.bool)
        quality = th.as_tensor(group.quality_mask, device=device).reshape(-1).to(dtype=th.bool)
        row_indices = th.as_tensor(group.row_indices, device=device).reshape(-1).to(dtype=th.long)
        step_indices = th.as_tensor(group.step_indices, device=device).reshape(-1).to(dtype=th.long)
        support = th.ones_like(legal, dtype=th.bool)
        if group.support_horizon is not None:
            support = support & (row_indices <= int(group.support_horizon))
        if group.censor_step is not None and group.censoring_kind != M3S1_CENSOR_EARLY_EVENT_PREFIX:
            support = support & (step_indices <= int(group.censor_step))

        logits = logits[order]
        legal = legal[order]
        quality = quality[order]
        support = support[order]
        supported_legal = legal[support]
        supported_quality = quality[support]
        desirable = supported_legal & supported_quality
        prewindow = th.zeros_like(desirable, dtype=th.bool)
        no_window = th.zeros_like(desirable, dtype=th.bool)
        if bool(desirable.any().detach().cpu().item()):
            first_quality = int(th.nonzero(desirable, as_tuple=False).flatten()[0].detach().cpu().item())
            positions = th.arange(int(desirable.numel()), device=device)
            prewindow = supported_legal & (~supported_quality) & (positions < first_quality)
        else:
            no_window = supported_legal
        return logits[support], supported_legal, desirable, prewindow, no_window

    @staticmethod
    def _m3s1_mean(values: list[float]) -> float:
        return float(sum(values) / len(values)) if values else 0.0

    def _m3s1_grouped_stopping_auxiliary_update(self) -> M3S1GroupedStoppingLoss | None:
        self._m3s1_last_grouped_stopping_grad_norm = 0.0
        self._m3s1_last_grouped_stopping_diagnostics = _M3S1GroupedStoppingDiagnostics()
        if not self._m3s1_grouped_stopping_enabled():
            return None
        sidecar = getattr(self, "_m3s1_grouped_stopping_sidecar", None)
        if sidecar is None or not sidecar.groups:
            return None
        stopping_getter = getattr(self.policy, "get_m3_stopping_logits", None)
        if not callable(stopping_getter):
            return None

        evidence: list[M3S1GroupedStoppingEvidence] = []
        stop_logit_values: list[float] = []
        stop_logit_desirable_values: list[float] = []
        stop_logit_prewindow_values: list[float] = []
        stop_logit_no_window_values: list[float] = []
        stop_logit_closed_mask_values: list[float] = []
        event_logit_delta_values: list[float] = []
        closed_mask_row_count = 0
        for group in sidecar.groups:
            obs = self._m3s1_observations_for_group(sidecar, group)
            stopping_logits = stopping_getter(
                obs,
                detach_latent=bool(self.m3s1_grouped_stopping_detach_latent),
            )
            if stopping_logits is None:
                return None
            if int(stopping_logits.reshape(-1).numel()) != len(group.row_indices):
                raise ValueError("M3-S1 stopping logits must match grouped sidecar rows")
            flat_logits = stopping_logits.reshape(-1)
            supported_logits, supported_legal, desirable, prewindow, no_window = (
                self._m3s1_group_diagnostic_masks(group, flat_logits)
            )
            closed_mask = ~supported_legal
            self._m3s1_extend_float_values(stop_logit_values, supported_logits)
            self._m3s1_extend_float_values(stop_logit_desirable_values, supported_logits[desirable])
            self._m3s1_extend_float_values(stop_logit_prewindow_values, supported_logits[prewindow])
            self._m3s1_extend_float_values(stop_logit_no_window_values, supported_logits[no_window])
            self._m3s1_extend_float_values(stop_logit_closed_mask_values, supported_logits[closed_mask])
            closed_mask_row_count += int(closed_mask.sum().detach().cpu().item())

            event_logit_delta = self._m3s1_event_logit_delta_diagnostic(obs)
            if event_logit_delta is not None and int(event_logit_delta.numel()) == int(flat_logits.numel()):
                order = self._m3s1_group_order(group, device=event_logit_delta.device)
                supported = th.ones(
                    (int(event_logit_delta.numel()),),
                    dtype=th.bool,
                    device=event_logit_delta.device,
                )
                row_indices = th.as_tensor(group.row_indices, device=event_logit_delta.device).reshape(-1).long()
                step_indices = th.as_tensor(group.step_indices, device=event_logit_delta.device).reshape(-1).long()
                if group.support_horizon is not None:
                    supported = supported & (row_indices <= int(group.support_horizon))
                if group.censor_step is not None and group.censoring_kind != M3S1_CENSOR_EARLY_EVENT_PREFIX:
                    supported = supported & (step_indices <= int(group.censor_step))
                self._m3s1_extend_float_values(
                    event_logit_delta_values,
                    event_logit_delta[order][supported[order]],
                )
            evidence.append(
                M3S1GroupedStoppingEvidence(
                    group_id=group.group_id,
                    episode_id=group.episode_id,
                    route_source=M3S1_ROUTE_ON_POLICY,
                    row_indices=group.row_indices,
                    step_indices=group.step_indices,
                    env_indices=group.env_indices,
                    legal_mask=group.legal_mask,
                    quality_mask=group.quality_mask,
                    stopping_logits=stopping_logits.reshape(-1),
                    accepted_event=group.accepted_event,
                    censoring_kind=group.censoring_kind,
                    censor_step=group.censor_step,
                    support_horizon=group.support_horizon,
                )
            )

        self._m3s1_last_grouped_stopping_diagnostics = _M3S1GroupedStoppingDiagnostics(
            stop_logit_mean=self._m3s1_mean(stop_logit_values),
            stop_logit_desirable_mean=self._m3s1_mean(stop_logit_desirable_values),
            stop_logit_prewindow_mean=self._m3s1_mean(stop_logit_prewindow_values),
            stop_logit_no_window_mean=self._m3s1_mean(stop_logit_no_window_values),
            stop_logit_closed_mask_mean=self._m3s1_mean(stop_logit_closed_mask_values),
            event_logit_delta_diagnostic_mean=self._m3s1_mean(event_logit_delta_values),
            stop_logit_count=len(stop_logit_values),
            stop_logit_desirable_count=len(stop_logit_desirable_values),
            stop_logit_prewindow_count=len(stop_logit_prewindow_values),
            stop_logit_no_window_count=len(stop_logit_no_window_values),
            closed_mask_row_count=int(closed_mask_row_count),
            event_logit_delta_diagnostic_count=len(event_logit_delta_values),
        )

        grouped_loss = compute_m3s1_grouped_stopping_loss(
            evidence,
            coef=float(self.m3s1_grouped_stopping_coef),
            early_mass_coef=float(self.m3s1_grouped_stopping_early_mass_coef),
            early_mass_budget=float(self.m3s1_grouped_stopping_early_mass_budget),
            prefix_early_mass_budget=self.m3s1_grouped_stopping_prefix_early_mass_budget,
            no_event_coef=float(self.m3s1_grouped_stopping_no_event_coef),
            boundary_threshold=float(self.m3s1_grouped_stopping_boundary_threshold),
        )
        self._m3s1_last_grouped_stopping_loss = grouped_loss
        if (
            grouped_loss.loss.requires_grad
            and float(grouped_loss.loss.detach().cpu().item()) != 0.0
            and int(grouped_loss.stats.active_group_count) > 0
        ):
            self.policy.optimizer.zero_grad(set_to_none=True)
            grouped_loss.loss.backward()
            grad_norm_tensor = th.nn.utils.clip_grad_norm_(self.policy.parameters(), self.max_grad_norm)
            self._m3s1_last_grouped_stopping_grad_norm = float(grad_norm_tensor.detach().cpu().item())
            self.policy.optimizer.step()
            self.policy.optimizer.zero_grad(set_to_none=True)
        return grouped_loss

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

        entropy_losses = []
        pg_losses, value_losses = [], []
        action_mean_regularization_losses = []
        first_event_hazard_losses = []
        first_event_hazard_active_counts = []
        first_event_hazard_positive_fracs = []
        first_event_credit_losses = []
        first_event_credit_value_losses = []
        first_event_credit_delta_align_losses = []
        first_event_credit_active_counts = []
        first_event_credit_positive_fracs = []
        first_event_credit_advantage_means = []
        first_event_credit_projection_active_counts = []
        first_event_credit_projection_candidate_counts = []
        first_event_credit_projection_unsupported_counts = []
        first_event_credit_projection_advantage_means = []
        first_event_credit_projection_delta_means = []
        first_event_credit_source_shadow_counts = []
        first_event_credit_source_deadline_counts = []
        first_event_credit_source_early_counts = []
        first_event_credit_source_prewindow_counts = []
        first_event_credit_source_legal_open_quality_counts = []
        first_event_credit_source_legal_open_quality_positive_counts = []
        first_event_credit_source_deadline_positive_counts = []
        first_event_credit_source_shadow_positive_counts = []
        first_event_credit_source_legal_open_quality_advantage_means = []
        first_event_credit_separate_update_grad_norms = []
        first_event_credit_separate_update_counts = []
        first_event_policy_margin_losses = []
        first_event_policy_margin_active_counts = []
        first_event_policy_margin_positive_fracs = []
        first_event_policy_margin_delta_means = []
        first_event_policy_margin_delta_positive_fracs = []
        first_event_policy_margin_projection_active_counts = []
        first_event_policy_margin_projection_delta_means = []
        first_event_policy_margin_separate_update_grad_norms = []
        first_event_policy_margin_separate_update_counts = []
        clip_fractions = []

        approx_kl_divs = []
        continue_training = True
        m3s1_grouped_stopping_loss: M3S1GroupedStoppingLoss | None = None

        def _append_first_event_credit_stats(
            credit_loss: FirstEventCreditLoss,
            *,
            total_loss=None,
            value_loss=None,
            delta_align_loss=None,
        ) -> None:
            first_event_credit_losses.append(
                float((credit_loss.loss if total_loss is None else total_loss).detach().cpu())
            )
            first_event_credit_value_losses.append(
                float((credit_loss.value_loss if value_loss is None else value_loss).detach().cpu())
            )
            first_event_credit_delta_align_losses.append(
                float(
                    (
                        credit_loss.delta_align_loss
                        if delta_align_loss is None
                        else delta_align_loss
                    ).detach().cpu()
                )
            )
            first_event_credit_active_counts.append(int(credit_loss.active_count))
            first_event_credit_positive_fracs.append(float(credit_loss.positive_frac))
            first_event_credit_advantage_means.append(float(credit_loss.advantage_mean))
            first_event_credit_projection_active_counts.append(int(credit_loss.projection_active_count))
            first_event_credit_projection_candidate_counts.append(int(credit_loss.projection_candidate_count))
            first_event_credit_projection_unsupported_counts.append(int(credit_loss.projection_unsupported_count))
            first_event_credit_projection_advantage_means.append(float(credit_loss.projection_advantage_mean))
            first_event_credit_projection_delta_means.append(float(credit_loss.projection_delta_mean))
            first_event_credit_source_shadow_counts.append(int(credit_loss.source_shadow_count))
            first_event_credit_source_deadline_counts.append(int(credit_loss.source_deadline_count))
            first_event_credit_source_early_counts.append(int(credit_loss.source_early_accepted_count))
            first_event_credit_source_prewindow_counts.append(int(credit_loss.source_prewindow_count))
            first_event_credit_source_legal_open_quality_counts.append(
                int(credit_loss.source_legal_open_quality_count)
            )
            first_event_credit_source_legal_open_quality_positive_counts.append(
                int(credit_loss.source_legal_open_quality_positive_count)
            )
            first_event_credit_source_deadline_positive_counts.append(
                int(credit_loss.source_deadline_positive_count)
            )
            first_event_credit_source_shadow_positive_counts.append(int(credit_loss.source_shadow_positive_count))
            first_event_credit_source_legal_open_quality_advantage_means.append(
                float(credit_loss.source_legal_open_quality_advantage_mean)
            )

        def _append_first_event_policy_margin_stats(
            margin_loss: FirstEventPolicyMarginLoss,
        ) -> None:
            first_event_policy_margin_losses.append(float(margin_loss.loss.detach().cpu()))
            first_event_policy_margin_active_counts.append(int(margin_loss.active_count))
            first_event_policy_margin_positive_fracs.append(float(margin_loss.positive_frac))
            first_event_policy_margin_delta_means.append(float(margin_loss.delta_mean))
            first_event_policy_margin_delta_positive_fracs.append(float(margin_loss.delta_positive_frac))
            first_event_policy_margin_projection_active_counts.append(int(margin_loss.projection_active_count))
            first_event_policy_margin_projection_delta_means.append(float(margin_loss.projection_delta_mean))

        # train for n_epochs epochs
        for epoch in range(self.n_epochs):
            # Do a complete pass on the rollout buffer
            for rollout_data in self.rollout_buffer.get(self.batch_size):
                separate_policy_margin_loss, separate_policy_margin_grad_norm = (
                    self._first_event_policy_margin_separate_update(rollout_data)
                    if self.a7_event_policy_separate_update_enabled
                    else (None, 0.0)
                )
                if separate_policy_margin_loss is not None:
                    first_event_policy_margin_separate_update_grad_norms.append(
                        float(separate_policy_margin_grad_norm)
                    )
                    first_event_policy_margin_separate_update_counts.append(1)
                    _append_first_event_policy_margin_stats(separate_policy_margin_loss)

                actions = rollout_data.actions
                if isinstance(self.action_space, spaces.Discrete):
                    actions = rollout_data.actions.long().flatten()

                values, log_prob, entropy = self.policy.evaluate_actions(rollout_data.observations, actions)
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
                pg_losses.append(policy_loss.item())
                clip_fraction = th.mean((th.abs(ratio - 1) > clip_range).float()).item()
                clip_fractions.append(clip_fraction)

                # Value loss
                if clip_range_vf is None:
                    values_pred = values
                else:
                    values_pred = rollout_data.old_values + th.clamp(
                        values - rollout_data.old_values, -clip_range_vf, clip_range_vf
                    )
                value_loss = F.mse_loss(rollout_data.returns, values_pred)
                value_losses.append(value_loss.item())

                # Entropy loss
                if entropy is None:
                    entropy_loss = -th.mean(-log_prob)
                else:
                    entropy_loss = -th.mean(entropy)
                entropy_losses.append(entropy_loss.item())

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
                    action_mean_regularization_losses.append(float(action_mean_regularization_loss.detach().cpu()))
                    loss = loss + float(self.action_mean_regularization_coef) * action_mean_regularization_loss
                first_event_hazard_loss = self._first_event_hazard_loss(rollout_data)
                if first_event_hazard_loss is not None:
                    first_event_hazard_losses.append(float(first_event_hazard_loss.loss.detach().cpu()))
                    first_event_hazard_active_counts.append(int(first_event_hazard_loss.active_count))
                    first_event_hazard_positive_fracs.append(float(first_event_hazard_loss.positive_frac))
                    loss = loss + first_event_hazard_loss.loss
                if not self.a7_event_policy_separate_update_enabled:
                    first_event_policy_margin_loss = self._first_event_policy_margin_loss(rollout_data)
                    if first_event_policy_margin_loss is not None:
                        _append_first_event_policy_margin_stats(first_event_policy_margin_loss)
                        loss = loss + first_event_policy_margin_loss.loss
                separate_credit_loss, separate_credit_grad_norm = (
                    self._first_event_credit_separate_value_update(rollout_data)
                    if self.a7_event_credit_separate_update_enabled
                    else (None, 0.0)
                )
                if separate_credit_loss is not None:
                    first_event_credit_separate_update_grad_norms.append(float(separate_credit_grad_norm))
                    first_event_credit_separate_update_counts.append(1)
                first_event_credit_loss = self._first_event_credit_loss(
                    rollout_data,
                    value_coef=0.0 if self.a7_event_credit_separate_update_enabled else None,
                    projection_value_coef=0.0 if self.a7_event_credit_separate_update_enabled else None,
                )
                if first_event_credit_loss is not None:
                    total_credit_loss = first_event_credit_loss.loss
                    value_credit_loss = first_event_credit_loss.value_loss
                    if separate_credit_loss is not None:
                        total_credit_loss = total_credit_loss + separate_credit_loss.loss.detach()
                        value_credit_loss = separate_credit_loss.value_loss
                    _append_first_event_credit_stats(
                        first_event_credit_loss,
                        total_loss=total_credit_loss,
                        value_loss=value_credit_loss,
                        delta_align_loss=first_event_credit_loss.delta_align_loss,
                    )
                    loss = loss + first_event_credit_loss.loss
                elif separate_credit_loss is not None:
                    _append_first_event_credit_stats(separate_credit_loss)

                # Early stopping based on observed KL (same criterion as SB3 PPO)
                with th.no_grad():
                    approx_kl_div = float(approx_kl.detach().cpu().numpy())
                approx_kl_divs.append(approx_kl_div)
                if self.target_kl is not None and approx_kl_div > 1.5 * float(self.target_kl):
                    continue_training = False
                    if self.verbose >= 1:
                        print(f"Early stopping at epoch {epoch} due to reaching max kl: {approx_kl_div:.4f}")
                    break

                # Optimization step
                self.policy.optimizer.zero_grad()
                loss.backward()
                th.nn.utils.clip_grad_norm_(self.policy.parameters(), self.max_grad_norm)
                self.policy.optimizer.step()

            self._n_updates += 1
            if not continue_training:
                break

        m3s1_grouped_stopping_loss = self._m3s1_grouped_stopping_auxiliary_update()

        explained_var = explained_variance(
            self._to_numpy_flat(self.rollout_buffer.values),
            self._to_numpy_flat(self.rollout_buffer.returns),
        )

        mean_kl = float(np.mean(approx_kl_divs)) if len(approx_kl_divs) > 0 else None
        self._adapt_kl_controls(mean_kl)

        # Logs
        self.logger.record("train/entropy_loss", float(np.mean(entropy_losses)))
        self.logger.record("train/policy_gradient_loss", float(np.mean(pg_losses)))
        self.logger.record("train/value_loss", float(np.mean(value_losses)))
        self.logger.record("train/approx_kl", float(np.mean(approx_kl_divs)) if len(approx_kl_divs) > 0 else 0.0)
        self.logger.record("train/clip_fraction", float(np.mean(clip_fractions)))
        self.logger.record("train/loss", float(loss.item()))
        self.logger.record("train/explained_variance", float(explained_var))
        if hasattr(self.policy, "log_std"):
            self.logger.record("train/std", float(th.exp(self.policy.log_std).mean().item()))
        if self.action_mean_regularization_coef > 0.0:
            self.logger.record(
                "train/action_mean_regularization_loss",
                float(np.mean(action_mean_regularization_losses)) if action_mean_regularization_losses else 0.0,
            )
            self.logger.record("train/action_mean_regularization_coef", float(self.action_mean_regularization_coef))
        if self._a6_first_event_enabled():
            self.logger.record(
                "a6/hazard_loss",
                float(np.mean(first_event_hazard_losses)) if first_event_hazard_losses else 0.0,
            )
            self.logger.record("a6/hazard_coef", float(self.a6_first_event_hazard_coef))
            self.logger.record("a6/curriculum_coef", float(self._current_a6_first_event_curriculum_coef()))
            self.logger.record("a6/deadline_weight", float(self.a6_first_event_deadline_weight))
            self.logger.record("a6/launch_window_enabled", float(self.a6_first_event_launch_window_enabled))
            self.logger.record(
                "a6/launch_window_prewindow_hold_weight",
                float(self.a6_first_event_launch_window_prewindow_hold_weight),
            )
            self.logger.record(
                "a6/active_count_mean",
                float(np.mean(first_event_hazard_active_counts)) if first_event_hazard_active_counts else 0.0,
            )
            self.logger.record(
                "a6/target_positive_frac",
                float(np.mean(first_event_hazard_positive_fracs)) if first_event_hazard_positive_fracs else 0.0,
            )
        if self._m3s1_grouped_stopping_enabled():
            sidecar = getattr(self, "_m3s1_grouped_stopping_sidecar", None)
            stats = m3s1_grouped_stopping_loss.stats if m3s1_grouped_stopping_loss is not None else None
            diagnostics = getattr(
                self,
                "_m3s1_last_grouped_stopping_diagnostics",
                _M3S1GroupedStoppingDiagnostics(),
            )
            active_row_count = float(stats.active_row_count) if stats else 0.0
            boundary_cross_count = float(stats.boundary_cross_count) if stats else 0.0
            boundary_cross_in_window_count = float(stats.boundary_cross_in_window_count) if stats else 0.0
            closed_mask_stop_attempt_count = float(stats.closed_mask_stop_attempt_count) if stats else 0.0
            closed_mask_row_count = float(diagnostics.closed_mask_row_count)
            self.logger.record("m3s1/grouped_stopping_coef", float(self.m3s1_grouped_stopping_coef))
            self.logger.record(
                "m3s1/grouped_stopping_loss",
                (
                    float(m3s1_grouped_stopping_loss.loss.detach().cpu().item())
                    if m3s1_grouped_stopping_loss is not None
                    else 0.0
                ),
            )
            self.logger.record(
                "m3s1/grouped_stopping_unscaled_loss",
                (
                    float(m3s1_grouped_stopping_loss.unscaled_loss.detach().cpu().item())
                    if m3s1_grouped_stopping_loss is not None
                    else 0.0
                ),
            )
            self.logger.record("m3s1/grouped_stopping_grad_norm", float(self._m3s1_last_grouped_stopping_grad_norm))
            self.logger.record("m3s1/grouped_sidecar_group_count", float(len(sidecar.groups)) if sidecar else 0.0)
            self.logger.record("m3s1/grouped_active_group_count", float(stats.active_group_count) if stats else 0.0)
            self.logger.record("m3s1/grouped_row_count", float(stats.row_count) if stats else 0.0)
            self.logger.record("m3s1/grouped_active_row_count", float(stats.active_row_count) if stats else 0.0)
            self.logger.record("m3s1/window_group_count", float(stats.window_group_count) if stats else 0.0)
            self.logger.record("m3s1/no_window_group_count", float(stats.no_window_group_count) if stats else 0.0)
            self.logger.record("m3s1/early_prefix_group_count", float(stats.early_prefix_group_count) if stats else 0.0)
            self.logger.record("m3s1/right_censor_group_count", float(stats.right_censor_group_count) if stats else 0.0)
            self.logger.record(
                "m3s1/grouped_labels_reached_loss",
                1.0 if stats and stats.active_group_count > 0 else 0.0,
            )
            self.logger.record("m3s1/hazard_desirable_mass", float(stats.mean_p_window) if stats else 0.0)
            self.logger.record("m3s1/hazard_early_mass", float(stats.mean_p_early) if stats else 0.0)
            self.logger.record("m3s1/no_event_mass", float(stats.mean_p_none) if stats else 0.0)
            self.logger.record("m3s1/stop_logit_mean", float(diagnostics.stop_logit_mean))
            self.logger.record("m3s1/stop_logit_desirable_mean", float(diagnostics.stop_logit_desirable_mean))
            self.logger.record("m3s1/stop_logit_prewindow_mean", float(diagnostics.stop_logit_prewindow_mean))
            self.logger.record("m3s1/stop_logit_no_window_mean", float(diagnostics.stop_logit_no_window_mean))
            self.logger.record("m3s1/stop_logit_closed_mask_mean", float(diagnostics.stop_logit_closed_mask_mean))
            self.logger.record("m3s1/stop_logit_count", float(diagnostics.stop_logit_count))
            self.logger.record("m3s1/stop_logit_desirable_count", float(diagnostics.stop_logit_desirable_count))
            self.logger.record("m3s1/stop_logit_prewindow_count", float(diagnostics.stop_logit_prewindow_count))
            self.logger.record("m3s1/stop_logit_no_window_count", float(diagnostics.stop_logit_no_window_count))
            self.logger.record(
                "m3s1/event_logit_delta_diagnostic_mean",
                float(diagnostics.event_logit_delta_diagnostic_mean),
            )
            self.logger.record(
                "m3s1/event_logit_delta_diagnostic_count",
                float(diagnostics.event_logit_delta_diagnostic_count),
            )
            self.logger.record("m3s1/boundary_cross_count", boundary_cross_count)
            self.logger.record(
                "m3s1/boundary_cross_ratio",
                boundary_cross_count / active_row_count if active_row_count > 0.0 else 0.0,
            )
            self.logger.record(
                "m3s1/boundary_cross_in_window_count",
                boundary_cross_in_window_count,
            )
            self.logger.record(
                "m3s1/boundary_cross_in_window_ratio",
                (
                    boundary_cross_in_window_count / boundary_cross_count
                    if boundary_cross_count > 0.0
                    else 0.0
                ),
            )
            self.logger.record(
                "m3s1/closed_mask_stop_attempt_count",
                closed_mask_stop_attempt_count,
            )
            self.logger.record("m3s1/closed_mask_row_count", closed_mask_row_count)
            self.logger.record(
                "m3s1/closed_mask_stop_attempt_ratio",
                (
                    closed_mask_stop_attempt_count / closed_mask_row_count
                    if closed_mask_row_count > 0.0
                    else 0.0
                ),
            )
            self.logger.record(
                "m3s1/accepted_event_count",
                float(sidecar.accepted_event_count) if sidecar else 0.0,
            )
            self.logger.record(
                "m3s1/one_shot_violation_count",
                float(sidecar.one_shot_violation_count) if sidecar else 0.0,
            )
            self.logger.record(
                "m3s1/closed_mask_accepted_event_count",
                float(sidecar.closed_mask_accepted_event_count) if sidecar else 0.0,
            )
            self.logger.record(
                "m3s1/grouped_stopping_detach_latent",
                float(self.m3s1_grouped_stopping_detach_latent),
            )
        if self._a7_event_credit_enabled():
            self.logger.record(
                "a7/event_credit_loss",
                float(np.mean(first_event_credit_losses)) if first_event_credit_losses else 0.0,
            )
            self.logger.record(
                "a7/event_credit_value_loss",
                float(np.mean(first_event_credit_value_losses)) if first_event_credit_value_losses else 0.0,
            )
            self.logger.record(
                "a7/event_credit_delta_align_loss",
                (
                    float(np.mean(first_event_credit_delta_align_losses))
                    if first_event_credit_delta_align_losses
                    else 0.0
                ),
            )
            self.logger.record("a7/event_credit_value_coef", float(self.a7_event_credit_value_coef))
            self.logger.record("a7/event_credit_delta_align_coef", float(self.a7_event_credit_delta_align_coef))
            self.logger.record(
                "a7/event_credit_delta_align_positive_only",
                float(self.a7_event_credit_delta_align_positive_only),
            )
            self.logger.record(
                "a7/evc_separate_update_enabled",
                float(self.a7_event_credit_separate_update_enabled),
            )
            self.logger.record(
                "a7/evc_separate_update_max_grad_norm",
                float(self.a7_event_credit_separate_update_max_grad_norm),
            )
            self.logger.record(
                "a7/evc_separate_update_count_mean",
                (
                    float(np.mean(first_event_credit_separate_update_counts))
                    if first_event_credit_separate_update_counts
                    else 0.0
                ),
            )
            self.logger.record(
                "a7/evc_separate_update_grad_norm_mean",
                (
                    float(np.mean(first_event_credit_separate_update_grad_norms))
                    if first_event_credit_separate_update_grad_norms
                    else 0.0
                ),
            )
            self.logger.record(
                "a7/evc_cross_rollout_context_rows",
                float(getattr(self, "_a7_cross_rollout_last_context_row_count", 0)),
            )
            self.logger.record(
                "a7/evc_carried_shadow_pending_envs",
                float(getattr(self, "_a7_cross_rollout_last_carried_shadow_pending_envs", 0)),
            )
            self.logger.record(
                "a7/evc_carried_shadow_positive_count_mean",
                float(getattr(self, "_a7_cross_rollout_last_carried_shadow_positive_count", 0)),
            )
            self.logger.record(
                "a7/evc_cross_rollout_first_event_count_mean",
                float(getattr(self, "_a7_cross_rollout_last_first_event_count", 0)),
            )
            self.logger.record(
                "a7/event_credit_legal_open_quality_weight",
                float(self.a7_event_credit_legal_open_quality_weight),
            )
            self.logger.record(
                "a7/evc_proj_enabled",
                float(self.a7_event_credit_legal_projection_enabled),
            )
            self.logger.record(
                "a7/evc_proj_value_coef",
                float(self.a7_event_credit_projection_value_coef),
            )
            self.logger.record(
                "a7/evc_proj_delta_coef",
                float(self.a7_event_credit_projection_delta_align_coef),
            )
            self.logger.record(
                "a7/event_credit_active_count_mean",
                float(np.mean(first_event_credit_active_counts)) if first_event_credit_active_counts else 0.0,
            )
            self.logger.record(
                "a7/event_credit_target_positive_frac",
                float(np.mean(first_event_credit_positive_fracs)) if first_event_credit_positive_fracs else 0.0,
            )
            self.logger.record(
                "a7/event_credit_advantage_mean",
                float(np.mean(first_event_credit_advantage_means)) if first_event_credit_advantage_means else 0.0,
            )
            self.logger.record(
                "a7/evc_proj_active_count_mean",
                (
                    float(np.mean(first_event_credit_projection_active_counts))
                    if first_event_credit_projection_active_counts
                    else 0.0
                ),
            )
            self.logger.record(
                "a7/evc_proj_candidate_count_mean",
                (
                    float(np.mean(first_event_credit_projection_candidate_counts))
                    if first_event_credit_projection_candidate_counts
                    else 0.0
                ),
            )
            self.logger.record(
                "a7/evc_proj_unsupported_count_mean",
                (
                    float(np.mean(first_event_credit_projection_unsupported_counts))
                    if first_event_credit_projection_unsupported_counts
                    else 0.0
                ),
            )
            self.logger.record(
                "a7/evc_src_shadow_count_mean",
                float(np.mean(first_event_credit_source_shadow_counts))
                if first_event_credit_source_shadow_counts
                else 0.0,
            )
            self.logger.record(
                "a7/evc_src_deadline_count_mean",
                float(np.mean(first_event_credit_source_deadline_counts))
                if first_event_credit_source_deadline_counts
                else 0.0,
            )
            self.logger.record(
                "a7/evc_src_early_count_mean",
                float(np.mean(first_event_credit_source_early_counts))
                if first_event_credit_source_early_counts
                else 0.0,
            )
            self.logger.record(
                "a7/evc_src_pre_count_mean",
                float(np.mean(first_event_credit_source_prewindow_counts))
                if first_event_credit_source_prewindow_counts
                else 0.0,
            )
            self.logger.record(
                "a7/evc_src_legal_open_quality_count_mean",
                float(np.mean(first_event_credit_source_legal_open_quality_counts))
                if first_event_credit_source_legal_open_quality_counts
                else 0.0,
            )
            self.logger.record(
                "a7/evc_src_legal_open_quality_positive_count_mean",
                float(np.mean(first_event_credit_source_legal_open_quality_positive_counts))
                if first_event_credit_source_legal_open_quality_positive_counts
                else 0.0,
            )
            self.logger.record(
                "a7/evc_src_deadline_positive_count_mean",
                float(np.mean(first_event_credit_source_deadline_positive_counts))
                if first_event_credit_source_deadline_positive_counts
                else 0.0,
            )
            self.logger.record(
                "a7/evc_src_shadow_positive_count_mean",
                float(np.mean(first_event_credit_source_shadow_positive_counts))
                if first_event_credit_source_shadow_positive_counts
                else 0.0,
            )
            self.logger.record(
                "a7/evc_src_legal_open_quality_advantage_mean",
                float(np.mean(first_event_credit_source_legal_open_quality_advantage_means))
                if first_event_credit_source_legal_open_quality_advantage_means
                else 0.0,
            )
            self.logger.record(
                "a7/evc_proj_advantage_mean",
                (
                    float(np.mean(first_event_credit_projection_advantage_means))
                    if first_event_credit_projection_advantage_means
                    else 0.0
                ),
            )
            self.logger.record(
                "a7/evc_proj_delta_mean",
                (
                    float(np.mean(first_event_credit_projection_delta_means))
                    if first_event_credit_projection_delta_means
                    else 0.0
                ),
            )

        if self._a7_event_policy_margin_enabled():
            self.logger.record(
                "a7/event_policy_margin_loss",
                float(np.mean(first_event_policy_margin_losses)) if first_event_policy_margin_losses else 0.0,
            )
            self.logger.record("a7/event_policy_margin_coef", float(self.a7_event_policy_margin_coef))
            self.logger.record("a7/event_policy_margin", float(self.a7_event_policy_margin))
            self.logger.record(
                "a7/event_policy_projection_margin_coef",
                float(self.a7_event_policy_projection_margin_coef),
            )
            self.logger.record(
                "a7/event_policy_separate_update_enabled",
                float(self.a7_event_policy_separate_update_enabled),
            )
            self.logger.record(
                "a7/event_policy_separate_update_max_grad_norm",
                float(self.a7_event_policy_separate_update_max_grad_norm),
            )
            self.logger.record(
                "a7/event_policy_separate_update_steps",
                int(self.a7_event_policy_separate_update_steps),
            )
            self.logger.record(
                "a7/event_policy_separate_update_count_mean",
                (
                    float(np.mean(first_event_policy_margin_separate_update_counts))
                    if first_event_policy_margin_separate_update_counts
                    else 0.0
                ),
            )
            self.logger.record(
                "a7/event_policy_separate_update_grad_norm_mean",
                (
                    float(np.mean(first_event_policy_margin_separate_update_grad_norms))
                    if first_event_policy_margin_separate_update_grad_norms
                    else 0.0
                ),
            )
            self.logger.record(
                "a7/event_policy_margin_active_count_mean",
                (
                    float(np.mean(first_event_policy_margin_active_counts))
                    if first_event_policy_margin_active_counts
                    else 0.0
                ),
            )
            self.logger.record(
                "a7/event_policy_margin_target_positive_frac",
                (
                    float(np.mean(first_event_policy_margin_positive_fracs))
                    if first_event_policy_margin_positive_fracs
                    else 0.0
                ),
            )
            self.logger.record(
                "a7/event_policy_margin_delta_mean",
                (
                    float(np.mean(first_event_policy_margin_delta_means))
                    if first_event_policy_margin_delta_means
                    else 0.0
                ),
            )
            self.logger.record(
                "a7/event_policy_margin_delta_positive_frac",
                (
                    float(np.mean(first_event_policy_margin_delta_positive_fracs))
                    if first_event_policy_margin_delta_positive_fracs
                    else 0.0
                ),
            )
            self.logger.record(
                "a7/event_policy_margin_projection_active_count_mean",
                (
                    float(np.mean(first_event_policy_margin_projection_active_counts))
                    if first_event_policy_margin_projection_active_counts
                    else 0.0
                ),
            )
            self.logger.record(
                "a7/event_policy_margin_projection_delta_mean",
                (
                    float(np.mean(first_event_policy_margin_projection_delta_means))
                    if first_event_policy_margin_projection_delta_means
                    else 0.0
                ),
            )

        self.logger.record("train/n_updates", int(self._n_updates), exclude="tensorboard")
        self.logger.record("train/clip_range", float(clip_range))
        if clip_range_vf is not None:
            self.logger.record("train/clip_range_vf", float(clip_range_vf))

        # Adaptive KL control logs
        self.logger.record("train/kl_penalty_coef", float(self.kl_penalty_coef))
        self.logger.record("train/kl_lr_mult", float(self._lr_mult))
        self.logger.record("train/kl_clip_mult", float(self._clip_mult))
        self.logger.record("train/kl_low_streak", int(self._low_kl_streak))
