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
    A6_FIRST_EVENT_SOURCE_CURRICULUM,
    A6_FIRST_EVENT_SOURCE_SHADOW_QUALITY,
    FirstEventCreditLoss,
    build_first_event_hazard_labels,
    compute_first_event_credit_loss,
    compute_first_event_hazard_loss,
    current_first_event_curriculum_coef,
    first_event_credit_batch_from_rollout_data,
    first_event_hazard_batch_from_rollout_data,
)
from .first_event_projection import project_air_combat_c2_roe_legal_open_observations
from .first_event_rollout_buffer import A6FirstEventDeviceDictRolloutBuffer, A6FirstEventDictRolloutBuffer


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
        a7_event_credit_legal_projection_enabled: bool = False,
        a7_event_credit_projection_value_coef: float = 0.0,
        a7_event_credit_projection_delta_align_coef: float = 0.0,
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
        self.a7_event_credit_legal_projection_enabled = bool(a7_event_credit_legal_projection_enabled)
        self.a7_event_credit_projection_value_coef = float(max(0.0, a7_event_credit_projection_value_coef))
        self.a7_event_credit_projection_delta_align_coef = float(
            max(0.0, a7_event_credit_projection_delta_align_coef)
        )
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

    def _first_event_label_collection_enabled(self) -> bool:
        return bool(self._a6_first_event_enabled() or self._a7_event_credit_enabled())

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
        if mission_tensor.ndim != 2 or int(mission_tensor.shape[0]) != int(n_envs) or int(mission_tensor.shape[1]) != 20:
            return None
        wcs_state = th.round(mission_tensor[:, 5].float()).to(dtype=th.long)
        authorization_to_fire = mission_tensor[:, 6] > 0.5
        engage_order_state = th.round(mission_tensor[:, 14].float()).to(dtype=th.long)
        shot_policy_state = th.round(mission_tensor[:, 15].float()).to(dtype=th.long)
        shot_budget_remaining = th.round(mission_tensor[:, 16].float()).to(dtype=th.long)
        pending_assessment = mission_tensor[:, 17] > 0.5
        target_contact_present = mission_tensor[:, 19] > 0.5
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
            device=self.device,
        )

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

    def _attach_a6_first_event_labels_to_rollout_buffer(
        self,
        rollout_buffer: RolloutBuffer,
        *,
        engagement_state: list[str],
        fire_mask: list[bool],
        fire_once_accepted: list[bool],
        episode_id: list[int],
        launch_window_open: list[bool] | None = None,
    ) -> None:
        if not self._first_event_label_collection_enabled():
            return
        setter = getattr(rollout_buffer, "set_a6_first_event_labels", None)
        if not callable(setter):
            return
        labels = self._build_a6_first_event_labels_from_rollout_infos(
            engagement_state=engagement_state,
            fire_mask=fire_mask,
            fire_once_accepted=fire_once_accepted,
            episode_id=episode_id,
            launch_window_open=launch_window_open,
        )
        setter(labels)
        self._record_a6_first_event_curriculum_seeds(labels, episode_id)

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

    def _first_event_credit_loss(self, rollout_data):
        if not self._a7_event_credit_enabled():
            return None
        batch = first_event_credit_batch_from_rollout_data(rollout_data)
        if batch is None:
            return None
        active, target, weight, window_id, source = batch
        obs = rollout_data.observations
        distribution = self.policy.get_distribution(obs)
        q_values_getter = getattr(distribution, "fire_event_q_values", None)
        if not callable(q_values_getter):
            return None
        q_values = q_values_getter()
        if q_values is None:
            return None
        logit_delta = None
        logit_delta_getter = getattr(distribution, "fire_event_logit_delta", None)
        if callable(logit_delta_getter):
            logit_delta = logit_delta_getter()
        delta_align_active = None
        if source is not None:
            delta_align_active = source.to(device=q_values.device) != int(A6_FIRST_EVENT_SOURCE_SHADOW_QUALITY)
        base_loss = compute_first_event_credit_loss(
            q_values,
            target.to(device=q_values.device),
            active.to(device=q_values.device),
            weight.to(device=q_values.device),
            event_logit_delta=logit_delta,
            window_id=window_id.to(device=q_values.device) if window_id is not None else None,
            value_coef=float(self.a7_event_credit_value_coef),
            delta_align_coef=float(self.a7_event_credit_delta_align_coef),
            delta_align_clip=float(self.a7_event_credit_delta_align_clip),
            delta_align_active=delta_align_active,
            positive_mass_cap=float(self.a7_event_credit_positive_mass_cap),
            negative_mass_cap=float(self.a7_event_credit_negative_mass_cap),
        )
        if (
            not self.a7_event_credit_legal_projection_enabled
            or source is None
            or (
                self.a7_event_credit_projection_value_coef <= 0.0
                and self.a7_event_credit_projection_delta_align_coef <= 0.0
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
                projection_unsupported_count=int(shadow_active.sum().detach().cpu().item()),
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
                projection_unsupported_count=int(projection.unsupported_count),
            )

        projected_distribution = self.policy.get_distribution(projection.observations)
        projected_q_getter = getattr(projected_distribution, "fire_event_q_values", None)
        if not callable(projected_q_getter):
            return base_loss
        projected_q_values = projected_q_getter()
        if projected_q_values is None:
            return base_loss
        projected_delta = None
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
            value_coef=float(self.a7_event_credit_projection_value_coef),
            delta_align_coef=float(self.a7_event_credit_projection_delta_align_coef),
            delta_align_clip=float(self.a7_event_credit_delta_align_clip),
            delta_align_active=projected_active.to(device=projected_q_values.device),
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
            projection_unsupported_count=int(projection.unsupported_count),
            projection_advantage_mean=projection_advantage_mean,
            projection_delta_mean=projection_delta_mean,
        )

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
        first_event_credit_projection_unsupported_counts = []
        first_event_credit_projection_advantage_means = []
        first_event_credit_projection_delta_means = []
        clip_fractions = []

        approx_kl_divs = []
        continue_training = True

        # train for n_epochs epochs
        for epoch in range(self.n_epochs):
            # Do a complete pass on the rollout buffer
            for rollout_data in self.rollout_buffer.get(self.batch_size):
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
                first_event_credit_loss = self._first_event_credit_loss(rollout_data)
                if first_event_credit_loss is not None:
                    first_event_credit_losses.append(float(first_event_credit_loss.loss.detach().cpu()))
                    first_event_credit_value_losses.append(float(first_event_credit_loss.value_loss.detach().cpu()))
                    first_event_credit_delta_align_losses.append(
                        float(first_event_credit_loss.delta_align_loss.detach().cpu())
                    )
                    first_event_credit_active_counts.append(int(first_event_credit_loss.active_count))
                    first_event_credit_positive_fracs.append(float(first_event_credit_loss.positive_frac))
                    first_event_credit_advantage_means.append(float(first_event_credit_loss.advantage_mean))
                    first_event_credit_projection_active_counts.append(
                        int(first_event_credit_loss.projection_active_count)
                    )
                    first_event_credit_projection_unsupported_counts.append(
                        int(first_event_credit_loss.projection_unsupported_count)
                    )
                    first_event_credit_projection_advantage_means.append(
                        float(first_event_credit_loss.projection_advantage_mean)
                    )
                    first_event_credit_projection_delta_means.append(
                        float(first_event_credit_loss.projection_delta_mean)
                    )
                    loss = loss + first_event_credit_loss.loss

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
                "a7/event_credit_legal_projection_enabled",
                float(self.a7_event_credit_legal_projection_enabled),
            )
            self.logger.record(
                "a7/event_credit_projection_value_coef",
                float(self.a7_event_credit_projection_value_coef),
            )
            self.logger.record(
                "a7/event_credit_projection_delta_align_coef",
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
                "a7/event_credit_projection_active_count_mean",
                (
                    float(np.mean(first_event_credit_projection_active_counts))
                    if first_event_credit_projection_active_counts
                    else 0.0
                ),
            )
            self.logger.record(
                "a7/event_credit_projection_unsupported_count_mean",
                (
                    float(np.mean(first_event_credit_projection_unsupported_counts))
                    if first_event_credit_projection_unsupported_counts
                    else 0.0
                ),
            )
            self.logger.record(
                "a7/event_credit_projection_advantage_mean",
                (
                    float(np.mean(first_event_credit_projection_advantage_means))
                    if first_event_credit_projection_advantage_means
                    else 0.0
                ),
            )
            self.logger.record(
                "a7/event_credit_projection_delta_mean",
                (
                    float(np.mean(first_event_credit_projection_delta_means))
                    if first_event_credit_projection_delta_means
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
