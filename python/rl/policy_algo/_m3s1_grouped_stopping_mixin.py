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

from .m3s1_grouped_stopping import (
    M3S1_CENSOR_EARLY_EVENT_PREFIX,
    M3S1_CENSOR_NONE,
    M3S1_CENSOR_TIMEOUT,
    M3S1_ROUTE_ON_POLICY,
    M3S1GroupedStoppingEvidence,
    M3S1GroupedStoppingLoss,
    compute_m3s1_grouped_stopping_loss,
)

from ._adaptive_kl_support import (
    _M3S1GroupedStoppingDiagnostics,
    _M3S1GroupedStoppingSidecar,
    _M3S1GroupedStoppingSidecarGroup,
)


class _M3S1GroupedStoppingMixin:
    def _m3s1_grouped_stopping_enabled(self) -> bool:
        return bool(float(getattr(self, "m3s1_grouped_stopping_coef", 0.0)) > 0.0)

    def _m3s1_grouped_stopping_sidecar_enabled(self) -> bool:
        return bool(
            self._m3s1_grouped_stopping_enabled()
            or self._m3s2_event_window_enabled()
            or self._m3s2_fire_boundary_enabled()
            or self._m3s2_window_classifier_enabled()
        )

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
        if not self._m3s1_grouped_stopping_sidecar_enabled():
            return None
        n_envs = max(1, int(getattr(rollout_buffer, "n_envs", 1)))
        count = len(fire_mask)
        if not (len(fire_once_accepted) == len(episode_id) == len(launch_window_open) == count):
            raise ValueError(
                "M3-S1 grouped stopping rollout rows must have the same flattened length"
            )
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
                    rows.append(
                        th.as_tensor(source[int(step_idx), int(env_idx)], device=self.device)
                    )
            observations[str(key)] = th.stack(rows, dim=0)
        return observations

    @staticmethod
    def _m3s1_extend_float_values(values: list[float], tensor: th.Tensor) -> None:
        values.extend(float(value) for value in tensor.detach().cpu().reshape(-1).tolist())

    @staticmethod
    def _m3s1_group_order(
        group: _M3S1GroupedStoppingSidecarGroup, *, device: th.device
    ) -> th.Tensor:
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
            first_quality = int(
                th.nonzero(desirable, as_tuple=False).flatten()[0].detach().cpu().item()
            )
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
            self._m3s1_extend_float_values(
                stop_logit_closed_mask_values, supported_logits[closed_mask]
            )
            closed_mask_row_count += int(closed_mask.sum().detach().cpu().item())

            event_logit_delta = self._m3s1_event_logit_delta_diagnostic(obs)
            if event_logit_delta is not None and int(event_logit_delta.numel()) == int(
                flat_logits.numel()
            ):
                order = self._m3s1_group_order(group, device=event_logit_delta.device)
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
                    and group.censoring_kind != M3S1_CENSOR_EARLY_EVENT_PREFIX
                ):
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
            grad_norm_tensor = th.nn.utils.clip_grad_norm_(
                self.policy.parameters(), self.max_grad_norm
            )
            self._m3s1_last_grouped_stopping_grad_norm = float(
                grad_norm_tensor.detach().cpu().item()
            )
            self.policy.optimizer.step()
            self.policy.optimizer.zero_grad(set_to_none=True)
        return grouped_loss


_ = Any  # suppress unused-import
