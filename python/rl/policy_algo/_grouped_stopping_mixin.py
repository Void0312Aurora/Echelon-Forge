"""M3-S1 grouped-stopping subdomain mixin for ``AdaptiveKLPPO``.

Holds the M3-S1 grouped-stopping sidecar build + auxiliary update. The loss
methods read A6 launch-window config; the diagnostics dataclass is also
borrowed by the M3-S2 event-window path (which constructs it for its own
diagnostics).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import torch as th
from stable_baselines3.common.buffers import RolloutBuffer

from .grouped_stopping import (
    CENSOR_EARLY_EVENT_PREFIX,
    CENSOR_NONE,
    CENSOR_TIMEOUT,
    ROUTE_ON_POLICY,
    GroupedStoppingEvidence,
    GroupedStoppingLoss,
    compute_grouped_stopping_loss,
)

from ._adaptive_kl_support import (
    _GroupedStoppingDiagnostics,
    _GroupedStoppingSidecar,
    _GroupedStoppingSidecarGroup,
)


class _GroupedStoppingMixin:
    def _grouped_stopping_enabled(self) -> bool:
        return bool(float(getattr(self, "grouped_stopping_coef", 0.0)) > 0.0)

    def _grouped_stopping_sidecar_enabled(self) -> bool:
        return bool(
            self._grouped_stopping_enabled()
            or self._event_window_enabled()
            or self._fire_boundary_enabled()
            or self._window_classifier_enabled()
        )

    @staticmethod
    def _rollout_observation_snapshot(rollout_buffer: RolloutBuffer) -> dict[str, Any] | None:
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

    def _build_grouped_stopping_sidecar(
        self,
        rollout_buffer: RolloutBuffer,
        *,
        fire_mask: list[bool],
        fire_once_accepted: list[bool],
        episode_id: list[int],
        launch_window_open: list[bool],
    ) -> _GroupedStoppingSidecar | None:
        if not self._grouped_stopping_sidecar_enabled():
            return None
        n_envs = max(1, int(getattr(rollout_buffer, "n_envs", 1)))
        count = len(fire_mask)
        if not (len(fire_once_accepted) == len(episode_id) == len(launch_window_open) == count):
            raise ValueError(
                "M3-S1 grouped stopping rollout rows must have the same flattened length"
            )
        if count <= 0 or count % n_envs != 0:
            return None

        observations = self._rollout_observation_snapshot(rollout_buffer)
        if observations is None:
            return None

        ordered_episodes: list[int] = []
        seen_episodes: set[int] = set()
        for value in episode_id:
            episode = int(value)
            if episode not in seen_episodes:
                ordered_episodes.append(episode)
                seen_episodes.add(episode)

        launch_min_age = max(1, int(self.first_event_launch_window_min_window_age_steps))
        groups: list[_GroupedStoppingSidecarGroup] = []
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
                censoring_kind = CENSOR_EARLY_EVENT_PREFIX
                censor_step = int(group_flat_indices[int(accepted_positions[0])] // n_envs)
            elif accepted_positions:
                censoring_kind = CENSOR_NONE
                censor_step = int(group_flat_indices[int(accepted_positions[0])] // n_envs)
            else:
                censoring_kind = CENSOR_TIMEOUT
                censor_step = None

            groups.append(
                _GroupedStoppingSidecarGroup(
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

        return _GroupedStoppingSidecar(
            groups=tuple(groups),
            observations=observations,
            accepted_event_count=int(accepted_event_count),
            one_shot_violation_count=int(one_shot_violation_count),
            closed_mask_accepted_event_count=int(closed_mask_accepted_event_count),
        )

    def _observations_for_group(
        self,
        sidecar: _GroupedStoppingSidecar,
        group: _GroupedStoppingSidecarGroup,
    ) -> dict[str, th.Tensor]:
        observations: dict[str, th.Tensor] = {}
        for key, source in sidecar.observations.items():
            rows = []
            for step_idx, env_idx in zip(group.step_indices, group.env_indices):
                if th.is_tensor(source):
                    rows.append(source[int(step_idx), int(env_idx)].to(device=self.device))
                else:
                    rows.append(
                        th.as_tensor(source[int(step_idx), int(env_idx)], device=self.device)
                    )
            observations[str(key)] = th.stack(rows, dim=0)
        return observations

    @staticmethod
    def _extend_float_values(values: list[float], tensor: th.Tensor) -> None:
        values.extend(float(value) for value in tensor.detach().cpu().reshape(-1).tolist())

    @staticmethod
    def _group_order(
        group: _GroupedStoppingSidecarGroup, *, device: th.device
    ) -> th.Tensor:
        env_indices = th.as_tensor(group.env_indices, device=device).reshape(-1).to(dtype=th.long)
        step_indices = th.as_tensor(group.step_indices, device=device).reshape(-1).to(dtype=th.long)
        if int(step_indices.numel()) <= 0:
            return th.empty((0,), dtype=th.long, device=device)
        env_stride = max(1, int(env_indices.max().detach().cpu().item()) + 1)
        return th.argsort(step_indices * env_stride + env_indices)

    def _event_logit_delta_diagnostic(self, obs: dict[str, th.Tensor]) -> th.Tensor | None:
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

    def _group_diagnostic_masks(
        self,
        group: _GroupedStoppingSidecarGroup,
        logits: th.Tensor,
    ) -> tuple[th.Tensor, th.Tensor, th.Tensor, th.Tensor, th.Tensor]:
        device = logits.device
        order = self._group_order(group, device=device)
        legal = th.as_tensor(group.legal_mask, device=device).reshape(-1).to(dtype=th.bool)
        quality = th.as_tensor(group.quality_mask, device=device).reshape(-1).to(dtype=th.bool)
        row_indices = th.as_tensor(group.row_indices, device=device).reshape(-1).to(dtype=th.long)
        step_indices = th.as_tensor(group.step_indices, device=device).reshape(-1).to(dtype=th.long)
        support = th.ones_like(legal, dtype=th.bool)
        if group.support_horizon is not None:
            support = support & (row_indices <= int(group.support_horizon))
        if group.censor_step is not None and group.censoring_kind != CENSOR_EARLY_EVENT_PREFIX:
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
            first_quality = int(
                th.nonzero(desirable, as_tuple=False).flatten()[0].detach().cpu().item()
            )
            positions = th.arange(int(desirable.numel()), device=device)
            prewindow = supported_legal & (~supported_quality) & (positions < first_quality)
        else:
            no_window = supported_legal
        return logits[support], supported_legal, desirable, prewindow, no_window

    @staticmethod
    def _mean(values: list[float]) -> float:
        return float(sum(values) / len(values)) if values else 0.0

    def _grouped_stopping_auxiliary_update(self) -> GroupedStoppingLoss | None:
        self._last_grouped_stopping_grad_norm = 0.0
        self._last_grouped_stopping_diagnostics = _GroupedStoppingDiagnostics()
        if not self._grouped_stopping_enabled():
            return None
        sidecar = getattr(self, "_grouped_stopping_sidecar", None)
        if sidecar is None or not sidecar.groups:
            return None
        stopping_getter = getattr(self.policy, "get_stopping_logits", None)
        if not callable(stopping_getter):
            return None

        evidence: list[GroupedStoppingEvidence] = []
        stop_logit_values: list[float] = []
        stop_logit_desirable_values: list[float] = []
        stop_logit_prewindow_values: list[float] = []
        stop_logit_no_window_values: list[float] = []
        stop_logit_closed_mask_values: list[float] = []
        event_logit_delta_values: list[float] = []
        closed_mask_row_count = 0
        for group in sidecar.groups:
            obs = self._observations_for_group(sidecar, group)
            stopping_logits = stopping_getter(
                obs,
                detach_latent=bool(self.grouped_stopping_detach_latent),
            )
            if stopping_logits is None:
                return None
            if int(stopping_logits.reshape(-1).numel()) != len(group.row_indices):
                raise ValueError("M3-S1 stopping logits must match grouped sidecar rows")
            flat_logits = stopping_logits.reshape(-1)
            supported_logits, supported_legal, desirable, prewindow, no_window = (
                self._group_diagnostic_masks(group, flat_logits)
            )
            closed_mask = ~supported_legal
            self._extend_float_values(stop_logit_values, supported_logits)
            self._extend_float_values(stop_logit_desirable_values, supported_logits[desirable])
            self._extend_float_values(stop_logit_prewindow_values, supported_logits[prewindow])
            self._extend_float_values(stop_logit_no_window_values, supported_logits[no_window])
            self._extend_float_values(
                stop_logit_closed_mask_values, supported_logits[closed_mask]
            )
            closed_mask_row_count += int(closed_mask.sum().detach().cpu().item())

            event_logit_delta = self._event_logit_delta_diagnostic(obs)
            if event_logit_delta is not None and int(event_logit_delta.numel()) == int(
                flat_logits.numel()
            ):
                order = self._group_order(group, device=event_logit_delta.device)
                supported = th.ones(
                    (int(event_logit_delta.numel()),),
                    dtype=th.bool,
                    device=event_logit_delta.device,
                )
                row_indices = (
                    th.as_tensor(group.row_indices, device=event_logit_delta.device)
                    .reshape(-1)
                    .long()
                )
                step_indices = (
                    th.as_tensor(group.step_indices, device=event_logit_delta.device)
                    .reshape(-1)
                    .long()
                )
                if group.support_horizon is not None:
                    supported = supported & (row_indices <= int(group.support_horizon))
                if (
                    group.censor_step is not None
                    and group.censoring_kind != CENSOR_EARLY_EVENT_PREFIX
                ):
                    supported = supported & (step_indices <= int(group.censor_step))
                self._extend_float_values(
                    event_logit_delta_values,
                    event_logit_delta[order][supported[order]],
                )
            evidence.append(
                GroupedStoppingEvidence(
                    group_id=group.group_id,
                    episode_id=group.episode_id,
                    route_source=ROUTE_ON_POLICY,
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

        self._last_grouped_stopping_diagnostics = _GroupedStoppingDiagnostics(
            stop_logit_mean=self._mean(stop_logit_values),
            stop_logit_desirable_mean=self._mean(stop_logit_desirable_values),
            stop_logit_prewindow_mean=self._mean(stop_logit_prewindow_values),
            stop_logit_no_window_mean=self._mean(stop_logit_no_window_values),
            stop_logit_closed_mask_mean=self._mean(stop_logit_closed_mask_values),
            event_logit_delta_diagnostic_mean=self._mean(event_logit_delta_values),
            stop_logit_count=len(stop_logit_values),
            stop_logit_desirable_count=len(stop_logit_desirable_values),
            stop_logit_prewindow_count=len(stop_logit_prewindow_values),
            stop_logit_no_window_count=len(stop_logit_no_window_values),
            closed_mask_row_count=int(closed_mask_row_count),
            event_logit_delta_diagnostic_count=len(event_logit_delta_values),
        )

        grouped_loss = compute_grouped_stopping_loss(
            evidence,
            coef=float(self.grouped_stopping_coef),
            early_mass_coef=float(self.grouped_stopping_early_mass_coef),
            early_mass_budget=float(self.grouped_stopping_early_mass_budget),
            prefix_early_mass_budget=self.grouped_stopping_prefix_early_mass_budget,
            no_event_coef=float(self.grouped_stopping_no_event_coef),
            boundary_threshold=float(self.grouped_stopping_boundary_threshold),
        )
        self._last_grouped_stopping_loss = grouped_loss
        if (
            grouped_loss.loss.requires_grad
            and float(grouped_loss.loss.detach().cpu().item()) != 0.0
            and int(grouped_loss.stats.active_group_count) > 0
        ):
            self.policy.optimizer.zero_grad(set_to_none=True)
            grouped_loss.loss.backward()
            grad_norm_tensor = th.nn.utils.clip_grad_norm_(
                self.policy.parameters(), self.max_grad_norm
            )
            self._last_grouped_stopping_grad_norm = float(
                grad_norm_tensor.detach().cpu().item()
            )
            self.policy.optimizer.step()
            self.policy.optimizer.zero_grad(set_to_none=True)
        return grouped_loss


    def _record_grouped_stopping_logs(self, grouped_stopping_loss) -> None:
        sidecar = getattr(self, "_grouped_stopping_sidecar", None)
        stats = (
            grouped_stopping_loss.stats if grouped_stopping_loss is not None else None
        )
        diagnostics = getattr(
            self,
            "_last_grouped_stopping_diagnostics",
            _GroupedStoppingDiagnostics(),
        )
        active_row_count = float(stats.active_row_count) if stats else 0.0
        boundary_cross_count = float(stats.boundary_cross_count) if stats else 0.0
        boundary_cross_in_window_count = (
            float(stats.boundary_cross_in_window_count) if stats else 0.0
        )
        closed_mask_stop_attempt_count = (
            float(stats.closed_mask_stop_attempt_count) if stats else 0.0
        )
        closed_mask_row_count = float(diagnostics.closed_mask_row_count)
        self.logger.record("m3s1/grouped_stopping_coef", float(self.grouped_stopping_coef))
        self.logger.record(
            "m3s1/grouped_stopping_loss",
            (
                float(grouped_stopping_loss.loss.detach().cpu().item())
                if grouped_stopping_loss is not None
                else 0.0
            ),
        )
        self.logger.record(
            "m3s1/grouped_stopping_unscaled_loss",
            (
                float(grouped_stopping_loss.unscaled_loss.detach().cpu().item())
                if grouped_stopping_loss is not None
                else 0.0
            ),
        )
        self.logger.record(
            "m3s1/grouped_stopping_grad_norm", float(self._last_grouped_stopping_grad_norm)
        )
        self.logger.record(
            "m3s1/grouped_sidecar_group_count", float(len(sidecar.groups)) if sidecar else 0.0
        )
        self.logger.record(
            "m3s1/grouped_active_group_count", float(stats.active_group_count) if stats else 0.0
        )
        self.logger.record("m3s1/grouped_row_count", float(stats.row_count) if stats else 0.0)
        self.logger.record(
            "m3s1/grouped_active_row_count", float(stats.active_row_count) if stats else 0.0
        )
        self.logger.record(
            "m3s1/window_group_count", float(stats.window_group_count) if stats else 0.0
        )
        self.logger.record(
            "m3s1/no_window_group_count", float(stats.no_window_group_count) if stats else 0.0
        )
        self.logger.record(
            "m3s1/early_prefix_group_count",
            float(stats.early_prefix_group_count) if stats else 0.0,
        )
        self.logger.record(
            "m3s1/right_censor_group_count",
            float(stats.right_censor_group_count) if stats else 0.0,
        )
        self.logger.record(
            "m3s1/grouped_labels_reached_loss",
            1.0 if stats and stats.active_group_count > 0 else 0.0,
        )
        self.logger.record(
            "m3s1/hazard_desirable_mass", float(stats.mean_p_window) if stats else 0.0
        )
        self.logger.record(
            "m3s1/hazard_early_mass", float(stats.mean_p_early) if stats else 0.0
        )
        self.logger.record(
            "m3s1/hazard_deadline_mass", float(stats.mean_p_deadline) if stats else 0.0
        )
        self.logger.record("m3s1/no_event_mass", float(stats.mean_p_none) if stats else 0.0)
        self.logger.record(
            "m3s1/quality_delay", float(stats.mean_quality_delay) if stats else 0.0
        )
        self.logger.record("m3s1/stop_logit_mean", float(diagnostics.stop_logit_mean))
        self.logger.record(
            "m3s1/stop_logit_desirable_mean", float(diagnostics.stop_logit_desirable_mean)
        )
        self.logger.record(
            "m3s1/stop_logit_prewindow_mean", float(diagnostics.stop_logit_prewindow_mean)
        )
        self.logger.record(
            "m3s1/stop_logit_no_window_mean", float(diagnostics.stop_logit_no_window_mean)
        )
        self.logger.record(
            "m3s1/stop_logit_closed_mask_mean", float(diagnostics.stop_logit_closed_mask_mean)
        )
        self.logger.record("m3s1/stop_logit_count", float(diagnostics.stop_logit_count))
        self.logger.record(
            "m3s1/stop_logit_desirable_count", float(diagnostics.stop_logit_desirable_count)
        )
        self.logger.record(
            "m3s1/stop_logit_prewindow_count", float(diagnostics.stop_logit_prewindow_count)
        )
        self.logger.record(
            "m3s1/stop_logit_no_window_count", float(diagnostics.stop_logit_no_window_count)
        )
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
            float(self.grouped_stopping_detach_latent),
        )



_ = Any  # suppress unused-import
