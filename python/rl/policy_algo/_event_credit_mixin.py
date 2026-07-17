"""A7 event-credit / policy-margin subdomain mixin for ``AdaptiveKLPPO``.

Holds the A7 (event-credit value/alignment, policy margin, cross-rollout
shadow) methods. Depends on A6 helpers (label building, slicing) and the
``first_event_hazard`` batch builders. Assumes the host class sets the A7
``self.*`` configuration attributes and exposes the A6 methods.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import torch as th

from .first_event_hazard import (
    FIRST_EVENT_SOURCE_DEADLINE,
    FIRST_EVENT_SOURCE_EARLY_ACCEPTED,
    FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY,
    FIRST_EVENT_SOURCE_PREWINDOW,
    FIRST_EVENT_SOURCE_SHADOW_QUALITY,
    FirstEventCreditLoss,
    FirstEventHazardLabels,
    FirstEventPolicyMarginLoss,
    compute_first_event_credit_loss,
    compute_first_event_policy_margin_loss,
    first_event_credit_batch_from_rollout_data,
)
from .first_event_projection import project_air_combat_c2_roe_legal_open_observations

from ._adaptive_kl_support import _FirstEventRolloutRow, _TrainEpochStats


class _EventCreditMixin:
    def _event_credit_enabled(self) -> bool:
        return bool(
            self.event_credit_value_coef > 0.0
            or self.event_credit_delta_align_coef > 0.0
            or self.event_credit_projection_value_coef > 0.0
            or self.event_credit_projection_delta_align_coef > 0.0
        )

    def _event_policy_margin_enabled(self) -> bool:
        return bool(
            self.event_policy_margin_coef > 0.0
            or self.event_policy_projection_margin_coef > 0.0
        )

    def _first_event_aux_enabled(self) -> bool:
        return bool(self._event_credit_enabled() or self._event_policy_margin_enabled())

    @staticmethod
    def _first_event_rows_to_inputs(
        rows: list[_FirstEventRolloutRow],
    ) -> tuple[list[str], list[bool], list[bool], list[int], list[bool]]:
        return (
            [row.engagement_state for row in rows],
            [bool(row.fire_mask) for row in rows],
            [bool(row.fire_once_accepted) for row in rows],
            [int(row.episode_id) for row in rows],
            [bool(row.launch_window_open) for row in rows],
        )

    @staticmethod
    def _first_event_rows_from_rollout_inputs(
        *,
        engagement_state: list[str],
        fire_mask: list[bool],
        fire_once_accepted: list[bool],
        episode_id: list[int],
        launch_window_open: list[bool],
    ) -> list[_FirstEventRolloutRow]:
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
            _FirstEventRolloutRow(
                engagement_state=str(engagement_state[idx]),
                fire_mask=bool(fire_mask[idx]),
                fire_once_accepted=bool(fire_once_accepted[idx]),
                episode_id=int(episode_id[idx]),
                launch_window_open=bool(launch_window_open[idx]),
            )
            for idx in range(count)
        ]

    @staticmethod
    def _first_event_rows_by_env(
        rows: list[_FirstEventRolloutRow],
        *,
        n_envs: int,
    ) -> list[list[_FirstEventRolloutRow]]:
        env_count = max(1, int(n_envs))
        per_env: list[list[_FirstEventRolloutRow]] = [[] for _ in range(env_count)]
        for flat_idx, row in enumerate(rows):
            per_env[int(flat_idx) % env_count].append(row)
        return per_env

    def _cross_rollout_first_event_enabled(self, launch_window_open: list[bool] | None) -> bool:
        return bool(
            not self._first_event_enabled()
            and self._first_event_aux_enabled()
            and launch_window_open is not None
        )

    def _get_first_event_rollout_history(
        self, n_envs: int
    ) -> list[list[_FirstEventRolloutRow]]:
        env_count = max(1, int(n_envs))
        history = getattr(self, "_first_event_rollout_history", None)
        if not isinstance(history, list) or len(history) != env_count:
            history = [[] for _ in range(env_count)]
            self._first_event_rollout_history = history
        return history

    def _build_cross_rollout_first_event_labels(
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
        list[list[_FirstEventRolloutRow]],
        int,
    ]:
        current_rows = self._first_event_rows_from_rollout_inputs(
            engagement_state=engagement_state,
            fire_mask=fire_mask,
            fire_once_accepted=fire_once_accepted,
            episode_id=episode_id,
            launch_window_open=launch_window_open,
        )
        current_rows_by_env = self._first_event_rows_by_env(current_rows, n_envs=n_envs)
        history = self._get_first_event_rollout_history(n_envs)
        prefix_rows: list[_FirstEventRolloutRow] = []
        for env_idx, rows in enumerate(current_rows_by_env):
            if not rows:
                continue
            carried = history[env_idx]
            if carried and int(carried[-1].episode_id) == int(rows[0].episode_id):
                prefix_rows.extend(carried)

        local_labels = self._build_first_event_labels_from_rollout_infos(
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
        ) = self._first_event_rows_to_inputs(combined_rows)
        combined_labels = self._build_first_event_labels_from_rollout_infos(
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

    def _update_first_event_rollout_history(
        self,
        *,
        current_rows_by_env: list[list[_FirstEventRolloutRow]],
        n_envs: int,
        env_episode_id_after_rollout: np.ndarray | list[int] | None,
    ) -> list[list[_FirstEventRolloutRow]]:
        history = self._get_first_event_rollout_history(n_envs)
        final_episode_id: list[int] | None = None
        if env_episode_id_after_rollout is not None:
            final_array = np.asarray(env_episode_id_after_rollout, dtype=np.int64).reshape(-1)
            if int(final_array.size) == int(len(history)):
                final_episode_id = [int(value) for value in final_array.tolist()]

        for env_idx, rows in enumerate(current_rows_by_env):
            carried = history[env_idx]
            kept: list[_FirstEventRolloutRow] = []
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

    def _first_event_history_has_pending_shadow(
        self, rows: list[_FirstEventRolloutRow]
    ) -> bool:
        if not rows:
            return False
        launch_min_age = max(1, int(self.first_event_launch_window_min_window_age_steps))
        cursor = 0
        while cursor < len(rows):
            row = rows[cursor]
            if not (str(row.engagement_state) == "AuthorizedReady" and bool(row.fire_mask)):
                cursor += 1
                continue
            start = cursor
            while cursor < len(rows):
                window_row = rows[cursor]
                if not (
                    str(window_row.engagement_state) == "AuthorizedReady"
                    and bool(window_row.fire_mask)
                ):
                    break
                cursor += 1
            for pos, window_row in enumerate(rows[start:cursor]):
                if not bool(window_row.fire_once_accepted):
                    continue
                age = int(pos) + 1
                quality_open = bool(window_row.launch_window_open) and age >= launch_min_age
                return not quality_open
        return False

    def _record_cross_rollout_first_event_stats(
        self,
        *,
        labels: FirstEventHazardLabels,
        local_labels: FirstEventHazardLabels,
        history: list[list[_FirstEventRolloutRow]],
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
            & (source == int(FIRST_EVENT_SOURCE_SHADOW_QUALITY))
        )
        local_positive_shadow = (
            local_active
            & (local_weight > 0.0)
            & (local_target > 0.5)
            & (local_source == int(FIRST_EVENT_SOURCE_SHADOW_QUALITY))
        )
        recovered_shadow = positive_shadow & ~local_positive_shadow
        changed = (
            (active != local_active)
            | ((target - local_target).abs() > 1.0e-6)
            | ((weight - local_weight).abs() > 1.0e-6)
            | (source != local_source)
        )
        self._cross_rollout_last_context_row_count = int(prefix_count)
        self._cross_rollout_last_carried_shadow_positive_count = int(
            recovered_shadow.sum().item()
        )
        self._cross_rollout_last_first_event_count = int(changed.sum().item())
        self._cross_rollout_last_carried_shadow_pending_envs = int(
            sum(1 for rows in history if self._first_event_history_has_pending_shadow(rows))
        )

    def _reset_cross_rollout_first_event_stats(self) -> None:
        self._cross_rollout_last_context_row_count = 0
        self._cross_rollout_last_carried_shadow_positive_count = 0
        self._cross_rollout_last_first_event_count = 0
        self._cross_rollout_last_carried_shadow_pending_envs = 0

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
        from dataclasses import replace

        if not self._event_credit_enabled():
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
            delta_align_active = source.to(device=q_values.device) != int(
                FIRST_EVENT_SOURCE_SHADOW_QUALITY
            )
        if self.event_credit_delta_align_positive_only and logit_delta is not None:
            positive_credit = (q_values[:, 1] - q_values[:, 0]).detach() > 0.0
            delta_align_active = (
                positive_credit
                if delta_align_active is None
                else delta_align_active.to(device=q_values.device).reshape(-1).to(dtype=th.bool)
                & positive_credit
            )
        base_loss = compute_first_event_credit_loss(
            q_values,
            target.to(device=q_values.device),
            active.to(device=q_values.device),
            weight.to(device=q_values.device),
            event_logit_delta=logit_delta,
            window_id=window_id.to(device=q_values.device) if window_id is not None else None,
            value_coef=(
                float(self.event_credit_value_coef)
                if value_coef is None
                else float(max(0.0, value_coef))
            ),
            delta_align_coef=(
                float(self.event_credit_delta_align_coef)
                if delta_align_coef is None
                else float(max(0.0, delta_align_coef))
            ),
            delta_align_clip=float(self.event_credit_delta_align_clip),
            delta_align_active=delta_align_active,
            positive_mass_cap=float(self.event_credit_positive_mass_cap),
            negative_mass_cap=float(self.event_credit_negative_mass_cap),
        )
        source_stats: dict[str, int] = {}
        if source is not None:
            source_flat = source.to(device=q_values.device).reshape(-1).long()
            active_flat = active.to(device=q_values.device).reshape(-1).to(dtype=th.bool)
            weight_flat = weight.to(device=q_values.device).reshape(-1)
            source_active = active_flat & (weight_flat > 0.0)

            def _source_count(value: int) -> int:
                return int(
                    (source_active & (source_flat == int(value))).sum().detach().cpu().item()
                )

            positive_flat = target.to(device=q_values.device).reshape(-1) > 0.5
            advantage = q_values[:, 1] - q_values[:, 0]
            legal_open_quality_mask = source_active & (
                source_flat == int(FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY)
            )

            def _source_positive_count(value: int) -> int:
                return int(
                    (source_active & positive_flat & (source_flat == int(value)))
                    .sum()
                    .detach()
                    .cpu()
                    .item()
                )

            def _source_advantage_mean(mask: th.Tensor) -> float:
                selected = advantage[mask]
                return (
                    float(selected.detach().mean().cpu().item())
                    if int(selected.numel()) > 0
                    else 0.0
                )

            source_stats = {
                "source_shadow_count": _source_count(FIRST_EVENT_SOURCE_SHADOW_QUALITY),
                "source_deadline_count": _source_count(FIRST_EVENT_SOURCE_DEADLINE),
                "source_early_accepted_count": _source_count(FIRST_EVENT_SOURCE_EARLY_ACCEPTED),
                "source_prewindow_count": _source_count(FIRST_EVENT_SOURCE_PREWINDOW),
                "source_legal_open_quality_count": _source_count(
                    FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY
                ),
                "source_legal_open_quality_positive_count": _source_positive_count(
                    FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY
                ),
                "source_deadline_positive_count": _source_positive_count(
                    FIRST_EVENT_SOURCE_DEADLINE
                ),
                "source_shadow_positive_count": _source_positive_count(
                    FIRST_EVENT_SOURCE_SHADOW_QUALITY
                ),
                "source_legal_open_quality_advantage_mean": _source_advantage_mean(
                    legal_open_quality_mask
                ),
            }
            base_loss = replace(
                base_loss,
                projection_candidate_count=source_stats["source_shadow_count"],
                **source_stats,
            )
        if (
            not self.event_credit_legal_projection_enabled
            or source is None
            or (
                self.event_credit_projection_value_coef <= 0.0
                and self.event_credit_projection_delta_align_coef <= 0.0
            )
            or (
                projection_value_coef is not None
                and projection_delta_align_coef is not None
                and float(projection_value_coef) <= 0.0
                and float(projection_delta_align_coef) <= 0.0
            )
        ):
            return base_loss

        shadow_active = active.to(device=q_values.device).reshape(-1).to(dtype=th.bool) & (
            source.to(device=q_values.device).reshape(-1).long()
            == int(FIRST_EVENT_SOURCE_SHADOW_QUALITY)
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
        projected_active = (
            projection.active.to(device=q_values.device).reshape(-1).to(dtype=th.bool)
        )
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
        projected_targets = th.ones_like(
            target.to(device=q_values.device, dtype=th.float32).reshape(-1)
        )
        projection_loss = compute_first_event_credit_loss(
            projected_q_values,
            projected_targets.to(device=projected_q_values.device),
            projected_active.to(device=projected_q_values.device),
            weight.to(device=projected_q_values.device),
            event_logit_delta=projected_delta,
            window_id=window_id.to(device=projected_q_values.device)
            if window_id is not None
            else None,
            value_coef=(
                float(self.event_credit_projection_value_coef)
                if projection_value_coef is None
                else float(max(0.0, projection_value_coef))
            ),
            delta_align_coef=(
                float(self.event_credit_projection_delta_align_coef)
                if projection_delta_align_coef is None
                else float(max(0.0, projection_delta_align_coef))
            ),
            delta_align_clip=float(self.event_credit_delta_align_clip),
            delta_align_active=(
                projected_active.to(device=projected_q_values.device)
                if not self.event_credit_delta_align_positive_only or projected_delta is None
                else (
                    projected_active.to(device=projected_q_values.device)
                    & ((projected_q_values[:, 1] - projected_q_values[:, 0]).detach() > 0.0)
                )
            ),
            positive_mass_cap=float(self.event_credit_positive_mass_cap),
            negative_mass_cap=float(self.event_credit_negative_mass_cap),
        )
        projected_advantage = projected_q_values[:, 1] - projected_q_values[:, 0]
        projected_weighted_advantage = projected_advantage[
            projected_active.to(device=projected_q_values.device)
        ]
        projection_advantage_mean = (
            float(projected_weighted_advantage.detach().mean().cpu().item())
            if int(projected_weighted_advantage.numel()) > 0
            else 0.0
        )
        projection_delta_mean = 0.0
        if projected_delta is not None:
            projected_delta_active = projected_delta.reshape(-1)[
                projected_active.to(device=projected_delta.device)
            ]
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
            positive_frac=(float(combined_positive) / float(combined_active))
            if combined_active > 0
            else 0.0,
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
        from dataclasses import replace

        if not self._event_policy_margin_enabled():
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
            policy_active = source.to(device=logit_delta.device) != int(
                FIRST_EVENT_SOURCE_SHADOW_QUALITY
            )
        base_loss = compute_first_event_policy_margin_loss(
            logit_delta,
            target.to(device=logit_delta.device),
            active.to(device=logit_delta.device),
            weight.to(device=logit_delta.device),
            window_id=window_id.to(device=logit_delta.device) if window_id is not None else None,
            policy_active=policy_active,
            coef=(
                float(self.event_policy_margin_coef) if coef is None else float(max(0.0, coef))
            ),
            margin=float(self.event_policy_margin),
            positive_mass_cap=float(self.event_credit_positive_mass_cap),
            negative_mass_cap=float(self.event_credit_negative_mass_cap),
        )

        projection_margin_coef = (
            float(self.event_policy_projection_margin_coef)
            if projection_coef is None
            else float(max(0.0, projection_coef))
        )
        if (
            projection_margin_coef <= 0.0
            or not self.event_credit_legal_projection_enabled
            or source is None
        ):
            return base_loss

        shadow_active = active.to(device=logit_delta.device).reshape(-1).to(dtype=th.bool) & (
            source.to(device=logit_delta.device).reshape(-1).long()
            == int(FIRST_EVENT_SOURCE_SHADOW_QUALITY)
        )
        projection = project_air_combat_c2_roe_legal_open_observations(
            rollout_data.observations, shadow_active
        )
        if projection is None:
            return replace(
                base_loss,
                projection_active_count=int(shadow_active.sum().detach().cpu().item()),
            )
        projected_active = (
            projection.active.to(device=logit_delta.device).reshape(-1).to(dtype=th.bool)
        )
        if int(projected_active.sum().detach().cpu().item()) <= 0:
            return replace(base_loss, projection_active_count=0)

        projected_distribution = self.policy.get_distribution(projection.observations)
        projected_delta_getter = getattr(projected_distribution, "fire_event_logit_delta", None)
        if not callable(projected_delta_getter):
            return base_loss
        projected_delta = projected_delta_getter()
        if projected_delta is None:
            return base_loss
        projected_targets = th.ones_like(
            target.to(device=projected_delta.device, dtype=th.float32).reshape(-1)
        )
        projection_loss = compute_first_event_policy_margin_loss(
            projected_delta,
            projected_targets,
            projected_active.to(device=projected_delta.device),
            weight.to(device=projected_delta.device),
            window_id=window_id.to(device=projected_delta.device)
            if window_id is not None
            else None,
            coef=projection_margin_coef,
            margin=float(self.event_policy_margin),
            positive_mass_cap=float(self.event_credit_positive_mass_cap),
            negative_mass_cap=float(self.event_credit_negative_mass_cap),
        )
        projected_delta_active = projected_delta.reshape(-1)[
            projected_active.to(device=projected_delta.device)
        ]
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
            positive_frac=(float(combined_positive) / float(combined_active))
            if combined_active > 0
            else 0.0,
            delta_mean=base_loss.delta_mean,
            delta_positive_frac=base_loss.delta_positive_frac,
            projection_active_count=int(projection_loss.active_count),
            projection_delta_mean=projection_delta_mean,
        )

    def _event_credit_head_parameters(self) -> list[th.nn.Parameter]:
        credit_head = getattr(self.policy, "hybrid_event_credit_head", None)
        if credit_head is None:
            return []
        return [param for param in credit_head.parameters() if param.requires_grad]

    def _event_policy_margin_parameters(self) -> list[th.nn.Parameter]:
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
        if not self.event_policy_separate_update_enabled:
            return None, 0.0
        selected_params = self._event_policy_margin_parameters()
        if not selected_params:
            return None, 0.0

        selected_ids = {id(param) for param in selected_params}
        last_margin_loss: FirstEventPolicyMarginLoss | None = None
        max_grad_norm_seen = 0.0
        for _ in range(int(self.event_policy_separate_update_steps)):
            margin_loss = self._first_event_policy_margin_loss(
                rollout_data,
                coef=float(self.event_policy_margin_coef),
                projection_coef=float(self.event_policy_projection_margin_coef),
            )
            if margin_loss is None:
                break
            self.policy.optimizer.zero_grad(set_to_none=True)
            margin_loss.loss.backward()
            for param in self.policy.parameters():
                if id(param) not in selected_ids:
                    param.grad = None
            max_norm = float(self.event_policy_separate_update_max_grad_norm)
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
        if not self.event_credit_separate_update_enabled:
            return None, 0.0
        credit_params = self._event_credit_head_parameters()
        if not credit_params:
            return None, 0.0

        credit_loss = self._first_event_credit_loss(
            rollout_data,
            value_coef=float(self.event_credit_value_coef),
            delta_align_coef=0.0,
            projection_value_coef=float(self.event_credit_projection_value_coef),
            projection_delta_align_coef=0.0,
            detach_credit_latent=True,
        )
        if credit_loss is None:
            return None, 0.0

        self.policy.optimizer.zero_grad(set_to_none=True)
        credit_loss.loss.backward()
        max_norm = float(self.event_credit_separate_update_max_grad_norm)
        if max_norm > 0.0:
            grad_norm_tensor = th.nn.utils.clip_grad_norm_(credit_params, max_norm)
            grad_norm = float(grad_norm_tensor.detach().cpu().item())
        else:
            grad_norm = 0.0
        self.policy.optimizer.step()
        self.policy.optimizer.zero_grad(set_to_none=True)
        return credit_loss, grad_norm


    def _record_event_credit_logs(self, epoch_stats: "_TrainEpochStats") -> None:
        self.logger.record(
            "a7/event_credit_loss",
            float(np.mean(epoch_stats.first_event_credit_losses)) if epoch_stats.first_event_credit_losses else 0.0,
        )
        self.logger.record(
            "a7/event_credit_value_loss",
            float(np.mean(epoch_stats.first_event_credit_value_losses))
            if epoch_stats.first_event_credit_value_losses
            else 0.0,
        )
        self.logger.record(
            "a7/event_credit_delta_align_loss",
            (
                float(np.mean(epoch_stats.first_event_credit_delta_align_losses))
                if epoch_stats.first_event_credit_delta_align_losses
                else 0.0
            ),
        )
        self.logger.record("a7/event_credit_value_coef", float(self.event_credit_value_coef))
        self.logger.record(
            "a7/event_credit_delta_align_coef", float(self.event_credit_delta_align_coef)
        )
        self.logger.record(
            "a7/event_credit_delta_align_positive_only",
            float(self.event_credit_delta_align_positive_only),
        )
        self.logger.record(
            "a7/evc_separate_update_enabled",
            float(self.event_credit_separate_update_enabled),
        )
        self.logger.record(
            "a7/evc_separate_update_max_grad_norm",
            float(self.event_credit_separate_update_max_grad_norm),
        )
        self.logger.record(
            "a7/evc_separate_update_count_mean",
            (
                float(np.mean(epoch_stats.first_event_credit_separate_update_counts))
                if epoch_stats.first_event_credit_separate_update_counts
                else 0.0
            ),
        )
        self.logger.record(
            "a7/evc_separate_update_grad_norm_mean",
            (
                float(np.mean(epoch_stats.first_event_credit_separate_update_grad_norms))
                if epoch_stats.first_event_credit_separate_update_grad_norms
                else 0.0
            ),
        )
        self.logger.record(
            "a7/evc_cross_rollout_context_rows",
            float(getattr(self, "_cross_rollout_last_context_row_count", 0)),
        )
        self.logger.record(
            "a7/evc_carried_shadow_pending_envs",
            float(getattr(self, "_cross_rollout_last_carried_shadow_pending_envs", 0)),
        )
        self.logger.record(
            "a7/evc_carried_shadow_positive_count_mean",
            float(getattr(self, "_cross_rollout_last_carried_shadow_positive_count", 0)),
        )
        self.logger.record(
            "a7/evc_cross_rollout_first_event_count_mean",
            float(getattr(self, "_cross_rollout_last_first_event_count", 0)),
        )
        self.logger.record(
            "a7/event_credit_legal_open_quality_weight",
            float(self.event_credit_legal_open_quality_weight),
        )
        self.logger.record(
            "a7/evc_proj_enabled",
            float(self.event_credit_legal_projection_enabled),
        )
        self.logger.record(
            "a7/evc_proj_value_coef",
            float(self.event_credit_projection_value_coef),
        )
        self.logger.record(
            "a7/evc_proj_delta_coef",
            float(self.event_credit_projection_delta_align_coef),
        )
        self.logger.record(
            "a7/event_credit_active_count_mean",
            float(np.mean(epoch_stats.first_event_credit_active_counts))
            if epoch_stats.first_event_credit_active_counts
            else 0.0,
        )
        self.logger.record(
            "a7/event_credit_target_positive_frac",
            float(np.mean(epoch_stats.first_event_credit_positive_fracs))
            if epoch_stats.first_event_credit_positive_fracs
            else 0.0,
        )
        self.logger.record(
            "a7/event_credit_advantage_mean",
            float(np.mean(epoch_stats.first_event_credit_advantage_means))
            if epoch_stats.first_event_credit_advantage_means
            else 0.0,
        )
        self.logger.record(
            "a7/evc_proj_active_count_mean",
            (
                float(np.mean(epoch_stats.first_event_credit_projection_active_counts))
                if epoch_stats.first_event_credit_projection_active_counts
                else 0.0
            ),
        )
        self.logger.record(
            "a7/evc_proj_candidate_count_mean",
            (
                float(np.mean(epoch_stats.first_event_credit_projection_candidate_counts))
                if epoch_stats.first_event_credit_projection_candidate_counts
                else 0.0
            ),
        )
        self.logger.record(
            "a7/evc_proj_unsupported_count_mean",
            (
                float(np.mean(epoch_stats.first_event_credit_projection_unsupported_counts))
                if epoch_stats.first_event_credit_projection_unsupported_counts
                else 0.0
            ),
        )
        self.logger.record(
            "a7/evc_src_shadow_count_mean",
            float(np.mean(epoch_stats.first_event_credit_source_shadow_counts))
            if epoch_stats.first_event_credit_source_shadow_counts
            else 0.0,
        )
        self.logger.record(
            "a7/evc_src_deadline_count_mean",
            float(np.mean(epoch_stats.first_event_credit_source_deadline_counts))
            if epoch_stats.first_event_credit_source_deadline_counts
            else 0.0,
        )
        self.logger.record(
            "a7/evc_src_early_count_mean",
            float(np.mean(epoch_stats.first_event_credit_source_early_counts))
            if epoch_stats.first_event_credit_source_early_counts
            else 0.0,
        )
        self.logger.record(
            "a7/evc_src_pre_count_mean",
            float(np.mean(epoch_stats.first_event_credit_source_prewindow_counts))
            if epoch_stats.first_event_credit_source_prewindow_counts
            else 0.0,
        )
        self.logger.record(
            "a7/evc_src_legal_open_quality_count_mean",
            float(np.mean(epoch_stats.first_event_credit_source_legal_open_quality_counts))
            if epoch_stats.first_event_credit_source_legal_open_quality_counts
            else 0.0,
        )
        self.logger.record(
            "a7/evc_src_legal_open_quality_positive_count_mean",
            float(np.mean(epoch_stats.first_event_credit_source_legal_open_quality_positive_counts))
            if epoch_stats.first_event_credit_source_legal_open_quality_positive_counts
            else 0.0,
        )
        self.logger.record(
            "a7/evc_src_deadline_positive_count_mean",
            float(np.mean(epoch_stats.first_event_credit_source_deadline_positive_counts))
            if epoch_stats.first_event_credit_source_deadline_positive_counts
            else 0.0,
        )
        self.logger.record(
            "a7/evc_src_shadow_positive_count_mean",
            float(np.mean(epoch_stats.first_event_credit_source_shadow_positive_counts))
            if epoch_stats.first_event_credit_source_shadow_positive_counts
            else 0.0,
        )
        self.logger.record(
            "a7/evc_src_legal_open_quality_advantage_mean",
            float(np.mean(epoch_stats.first_event_credit_source_legal_open_quality_advantage_means))
            if epoch_stats.first_event_credit_source_legal_open_quality_advantage_means
            else 0.0,
        )
        self.logger.record(
            "a7/evc_proj_advantage_mean",
            (
                float(np.mean(epoch_stats.first_event_credit_projection_advantage_means))
                if epoch_stats.first_event_credit_projection_advantage_means
                else 0.0
            ),
        )
        self.logger.record(
            "a7/evc_proj_delta_mean",
            (
                float(np.mean(epoch_stats.first_event_credit_projection_delta_means))
                if epoch_stats.first_event_credit_projection_delta_means
                else 0.0
            ),
        )

    def _record_event_policy_margin_logs(self, epoch_stats: "_TrainEpochStats") -> None:
        self.logger.record(
            "a7/event_policy_margin_loss",
            float(np.mean(epoch_stats.first_event_policy_margin_losses))
            if epoch_stats.first_event_policy_margin_losses
            else 0.0,
        )
        self.logger.record(
            "a7/event_policy_margin_coef", float(self.event_policy_margin_coef)
        )
        self.logger.record("a7/event_policy_margin", float(self.event_policy_margin))
        self.logger.record(
            "a7/event_policy_projection_margin_coef",
            float(self.event_policy_projection_margin_coef),
        )
        self.logger.record(
            "a7/event_policy_separate_update_enabled",
            float(self.event_policy_separate_update_enabled),
        )
        self.logger.record(
            "a7/event_policy_separate_update_max_grad_norm",
            float(self.event_policy_separate_update_max_grad_norm),
        )
        self.logger.record(
            "a7/event_policy_separate_update_steps",
            int(self.event_policy_separate_update_steps),
        )
        self.logger.record(
            "a7/event_policy_separate_update_count_mean",
            (
                float(np.mean(epoch_stats.first_event_policy_margin_separate_update_counts))
                if epoch_stats.first_event_policy_margin_separate_update_counts
                else 0.0
            ),
        )
        self.logger.record(
            "a7/event_policy_separate_update_grad_norm_mean",
            (
                float(np.mean(epoch_stats.first_event_policy_margin_separate_update_grad_norms))
                if epoch_stats.first_event_policy_margin_separate_update_grad_norms
                else 0.0
            ),
        )
        self.logger.record(
            "a7/event_policy_margin_active_count_mean",
            (
                float(np.mean(epoch_stats.first_event_policy_margin_active_counts))
                if epoch_stats.first_event_policy_margin_active_counts
                else 0.0
            ),
        )
        self.logger.record(
            "a7/event_policy_margin_target_positive_frac",
            (
                float(np.mean(epoch_stats.first_event_policy_margin_positive_fracs))
                if epoch_stats.first_event_policy_margin_positive_fracs
                else 0.0
            ),
        )
        self.logger.record(
            "a7/event_policy_margin_delta_mean",
            (
                float(np.mean(epoch_stats.first_event_policy_margin_delta_means))
                if epoch_stats.first_event_policy_margin_delta_means
                else 0.0
            ),
        )
        self.logger.record(
            "a7/event_policy_margin_delta_positive_frac",
            (
                float(np.mean(epoch_stats.first_event_policy_margin_delta_positive_fracs))
                if epoch_stats.first_event_policy_margin_delta_positive_fracs
                else 0.0
            ),
        )
        self.logger.record(
            "a7/event_policy_margin_projection_active_count_mean",
            (
                float(np.mean(epoch_stats.first_event_policy_margin_projection_active_counts))
                if epoch_stats.first_event_policy_margin_projection_active_counts
                else 0.0
            ),
        )
        self.logger.record(
            "a7/event_policy_margin_projection_delta_mean",
            (
                float(np.mean(epoch_stats.first_event_policy_margin_projection_delta_means))
                if epoch_stats.first_event_policy_margin_projection_delta_means
                else 0.0
            ),
        )



_ = Any  # suppress unused-import
