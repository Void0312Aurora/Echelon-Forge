"""A6 first-event hazard subdomain mixin for ``AdaptiveKLPPO``.

Holds the A6 (first-event hazard / launch-window) methods. The mixin assumes
the host class exposes the A6 ``self.*`` configuration attributes set in
``AdaptiveKLPPO.__init__`` plus the A7 methods (it reaches into the A7
cross-rollout label path when A6 targets are disabled). The module-level
A6 ROE helpers live in ``_adaptive_kl_support``.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import torch as th
from gymnasium import spaces

from stable_baselines3.common.buffers import RolloutBuffer

from .first_event_hazard import (
    A6_FIRST_EVENT_SOURCE_CURRICULUM,
    FirstEventHazardLabels,
    build_first_event_hazard_labels,
    compute_first_event_hazard_loss,
    current_first_event_curriculum_coef,
    first_event_hazard_batch_from_rollout_data,
)
from python.mission_obs_taxonomy import mission_observation_has_field

from ._adaptive_kl_support import (
    _A7FirstEventRolloutRow,
    _TrainEpochStats,
    _air_combat_c2_roe_mode_from_dim,
    _mission_column,
)


class _A6FirstEventMixin:
    def _a6_first_event_enabled(self) -> bool:
        return bool(
            self.a6_first_event_hazard_coef > 0.0
            or self.a6_first_event_curriculum_coef > 0.0
            or self.a6_first_event_censored_survival_weight > 0.0
            or self.a6_first_event_deadline_weight > 0.0
        )

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
        mission = obs.get("mission")
        if mission is not None:
            mission_tensor = th.as_tensor(mission)
            if mission_tensor.ndim == 2 and int(mission_tensor.shape[0]) == int(n_envs):
                mission_mode = _air_combat_c2_roe_mode_from_dim(int(mission_tensor.shape[1]))
                if mission_mode is not None and mission_observation_has_field(
                    mission_mode, "quality_window_ready"
                ):
                    fire_mask = (
                        _mission_column(mission_tensor, mission_mode, "quality_window_ready") > 0.5
                    )
                    return [bool(value) for value in fire_mask.detach().cpu().reshape(-1).tolist()]
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
        wcs_state = th.round(_mission_column(mission_tensor, mission_mode, "wcs_state").float()).to(
            dtype=th.long
        )
        authorization_to_fire = (
            _mission_column(mission_tensor, mission_mode, "authorization_to_fire") > 0.5
        )
        engage_order_state = th.round(
            _mission_column(mission_tensor, mission_mode, "engage_order_state").float()
        ).to(dtype=th.long)
        shot_policy_state = th.round(
            _mission_column(mission_tensor, mission_mode, "shot_policy_state").float()
        ).to(dtype=th.long)
        shot_budget_remaining = th.round(
            _mission_column(mission_tensor, mission_mode, "shot_budget_remaining").float()
        ).to(dtype=th.long)
        pending_assessment = (
            _mission_column(mission_tensor, mission_mode, "pending_assessment") > 0.5
        )
        target_contact_present = (
            _mission_column(mission_tensor, mission_mode, "target_contact_present") > 0.5
        )
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
                if mission_mode is not None and mission_observation_has_field(
                    mission_mode, "launch_window_open"
                ):
                    launch_window = (
                        _mission_column(mission_tensor, mission_mode, "launch_window_open") > 0.5
                    )
                    return [
                        bool(value) for value in launch_window.detach().cpu().reshape(-1).tolist()
                    ]

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
            if (
                contacts_candidate.ndim == 2
                and int(n_envs) == 1
                and int(contacts_candidate.shape[-1]) >= 5
            ):
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

    def _a6_first_event_launch_window_from_policy_obs(
        self, obs: Any, n_envs: int
    ) -> list[bool] | None:
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
            launch_window_min_window_age_steps=int(
                self.a6_first_event_launch_window_min_window_age_steps
            ),
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
                0.0 if use_a6_targets else float(self.a7_event_credit_shadow_quality_weight)
            ),
            legal_open_quality_weight=(
                0.0 if use_a6_targets else float(self.a7_event_credit_legal_open_quality_weight)
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
        from dataclasses import replace

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


    def _record_a6_first_event_logs(self, epoch_stats: "_TrainEpochStats") -> None:
        self.logger.record(
            "a6/hazard_loss",
            float(np.mean(epoch_stats.first_event_hazard_losses)) if epoch_stats.first_event_hazard_losses else 0.0,
        )
        self.logger.record("a6/hazard_coef", float(self.a6_first_event_hazard_coef))
        self.logger.record(
            "a6/curriculum_coef", float(self._current_a6_first_event_curriculum_coef())
        )
        self.logger.record("a6/deadline_weight", float(self.a6_first_event_deadline_weight))
        self.logger.record(
            "a6/launch_window_enabled", float(self.a6_first_event_launch_window_enabled)
        )
        self.logger.record(
            "a6/launch_window_prewindow_hold_weight",
            float(self.a6_first_event_launch_window_prewindow_hold_weight),
        )
        self.logger.record(
            "a6/active_count_mean",
            float(np.mean(epoch_stats.first_event_hazard_active_counts))
            if epoch_stats.first_event_hazard_active_counts
            else 0.0,
        )
        self.logger.record(
            "a6/target_positive_frac",
            float(np.mean(epoch_stats.first_event_hazard_positive_fracs))
            if epoch_stats.first_event_hazard_positive_fracs
            else 0.0,
        )



# Suppress unused-import warnings for symbols re-exported transitively.
_ = (spaces, _A7FirstEventRolloutRow)
