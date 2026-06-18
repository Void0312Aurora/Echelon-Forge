"""M3-S2 event-window / fire-boundary / window-classifier subdomain mixin.

Holds the M3-S2 auxiliary losses (event-window, fire-boundary, window
classifier) plus the support-preserving collect plumbing that gates on the A6
launch-window config. All three M3-S2 losses consume the M3-S1 grouped-stopping
sidecar built by ``_M3S1GroupedStoppingMixin``.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import torch as th
from gymnasium import spaces
from torch.nn import functional as F

from .m3s1_grouped_stopping import (
    M3S1_CENSOR_EARLY_EVENT_PREFIX,
    M3S1_ROUTE_ON_POLICY,
    M3S1GroupedStoppingEvidence,
    M3S1GroupedStoppingLoss,
    compute_m3s1_grouped_stopping_loss,
)

from ._adaptive_kl_support import (
    _M3S1GroupedStoppingDiagnostics,
    _M3S2FireBoundaryLoss,
    _M3S2WindowClassifierLoss,
)
from ._m3s2_window_classifier_replay import _M3S2WindowClassifierReplay


class _M3S2EventWindowMixin:
    def _m3s2_event_window_enabled(self) -> bool:
        return bool(float(getattr(self, "m3s2_event_window_coef", 0.0)) > 0.0)

    def _m3s2_fire_boundary_enabled(self) -> bool:
        return bool(float(getattr(self, "m3s2_fire_boundary_coef", 0.0)) > 0.0)

    def _m3s2_window_classifier_enabled(self) -> bool:
        return bool(float(getattr(self, "m3s2_window_classifier_coef", 0.0)) > 0.0)

    def _m3s2_support_preserving_collect_enabled(self) -> bool:
        return bool(
            (
                (
                    (self._m3s2_event_window_enabled() or self._m3s2_window_classifier_enabled())
                    and self.m3s2_event_window_support_preserving_collect_enabled
                )
                or (
                    self._m3s2_fire_boundary_enabled()
                    and self.m3s2_fire_boundary_support_preserving_collect_enabled
                )
            )
            and self.a6_first_event_launch_window_enabled
        )

    def _m3s2_support_preserving_hold_quality_enabled(self) -> bool:
        return bool(
            self.m3s2_event_window_support_preserving_hold_quality_enabled
            or (
                self._m3s2_fire_boundary_enabled()
                and self.m3s2_fire_boundary_support_preserving_hold_quality_enabled
            )
        )

    def _m3s2_support_preserving_collect_masks(
        self,
        *,
        fire_mask: list[bool] | None,
        launch_window_open: list[bool] | None,
        n_envs: int,
    ) -> list[bool]:
        if not self._m3s2_support_preserving_collect_enabled():
            return [False] * int(n_envs)
        if fire_mask is None or launch_window_open is None:
            return [False] * int(n_envs)
        if len(fire_mask) < int(n_envs) or len(launch_window_open) < int(n_envs):
            return [False] * int(n_envs)

        ages = getattr(self, "_m3s2_support_preserving_collect_legal_open_age", None)
        if not isinstance(ages, np.ndarray) or int(ages.size) != int(n_envs):
            ages = np.zeros((int(n_envs),), dtype=np.int64)
        else:
            ages = ages.astype(np.int64, copy=True)

        min_age = max(1, int(self.a6_first_event_launch_window_min_window_age_steps))
        hold_mask: list[bool] = []
        candidate_count = 0
        quality_count = 0
        for env_idx in range(int(n_envs)):
            legal_open = bool(fire_mask[env_idx])
            launch_open = bool(launch_window_open[env_idx])
            if legal_open:
                ages[env_idx] += 1
            else:
                ages[env_idx] = 0
            quality_open = bool(legal_open and launch_open and int(ages[env_idx]) >= min_age)
            hold = bool(
                legal_open
                and (not quality_open or self._m3s2_support_preserving_hold_quality_enabled())
            )
            hold_mask.append(hold)
            candidate_count += int(legal_open)
            quality_count += int(quality_open)

        self._m3s2_support_preserving_collect_legal_open_age = ages
        self._m3s2_support_preserving_collect_hold_count += int(
            sum(1 for value in hold_mask if value)
        )
        self._m3s2_support_preserving_collect_candidate_count += int(candidate_count)
        self._m3s2_support_preserving_collect_quality_count += int(quality_count)
        return hold_mask

    def _m3s2_apply_support_preserving_collect_actions(
        self,
        obs_tensor: Any,
        actions_tensor: th.Tensor,
        log_probs: th.Tensor,
        hold_mask: list[bool],
    ) -> tuple[th.Tensor, th.Tensor]:
        if not hold_mask or not any(bool(value) for value in hold_mask):
            return actions_tensor, log_probs
        if not isinstance(self.action_space, spaces.Box):
            return actions_tensor, log_probs
        if int(actions_tensor.ndim) != 2 or int(actions_tensor.shape[1]) <= 9:
            return actions_tensor, log_probs

        mask = th.as_tensor(hold_mask, device=actions_tensor.device).reshape(-1).to(dtype=th.bool)
        if int(mask.numel()) != int(actions_tensor.shape[0]) or not bool(
            mask.any().detach().cpu().item()
        ):
            return actions_tensor, log_probs

        modified_actions = actions_tensor.clone()
        modified_actions[mask, 9] = modified_actions.new_tensor(0.0)
        distribution = self.policy.get_distribution(obs_tensor)
        return modified_actions, distribution.log_prob(modified_actions)

    def _m3s2_event_window_loss_from_sidecar(self) -> M3S1GroupedStoppingLoss | None:
        sidecar = getattr(self, "_m3s1_grouped_stopping_sidecar", None)
        if sidecar is None or not sidecar.groups:
            self._m3s2_last_event_window_diagnostics = _M3S1GroupedStoppingDiagnostics()
            return None
        use_stopping_head = bool(getattr(self, "m3s2_event_window_use_stopping_head", False))
        distribution_getter = getattr(self.policy, "get_distribution", None)
        stopping_getter = getattr(self.policy, "get_m3_stopping_logits", None)
        if use_stopping_head and not callable(stopping_getter):
            self._m3s2_last_event_window_diagnostics = _M3S1GroupedStoppingDiagnostics()
            return None
        if not use_stopping_head and not callable(distribution_getter):
            self._m3s2_last_event_window_diagnostics = _M3S1GroupedStoppingDiagnostics()
            return None

        evidence: list[M3S1GroupedStoppingEvidence] = []
        event_logit_values: list[float] = []
        event_logit_desirable_values: list[float] = []
        event_logit_prewindow_values: list[float] = []
        event_logit_no_window_values: list[float] = []
        event_logit_closed_mask_values: list[float] = []
        closed_mask_row_count = 0
        for group in sidecar.groups:
            obs = self._m3s1_observations_for_group(sidecar, group)
            if use_stopping_head:
                assert callable(stopping_getter)
                event_logit_delta = stopping_getter(obs, detach_latent=False)
            else:
                assert callable(distribution_getter)
                distribution = distribution_getter(obs)
                logit_delta_getter = getattr(distribution, "fire_event_logit_delta", None)
                if not callable(logit_delta_getter):
                    self._m3s2_last_event_window_diagnostics = _M3S1GroupedStoppingDiagnostics()
                    return None
                event_logit_delta = logit_delta_getter()
            if event_logit_delta is None:
                self._m3s2_last_event_window_diagnostics = _M3S1GroupedStoppingDiagnostics()
                return None
            if int(event_logit_delta.reshape(-1).numel()) != len(group.row_indices):
                raise ValueError("M3-S2 event window logits must match grouped sidecar rows")

            flat_logits = event_logit_delta.reshape(-1)
            supported_logits, supported_legal, desirable, prewindow, no_window = (
                self._m3s1_group_diagnostic_masks(group, flat_logits)
            )
            closed_mask = ~supported_legal
            self._m3s1_extend_float_values(event_logit_values, supported_logits)
            self._m3s1_extend_float_values(
                event_logit_desirable_values, supported_logits[desirable]
            )
            self._m3s1_extend_float_values(
                event_logit_prewindow_values, supported_logits[prewindow]
            )
            self._m3s1_extend_float_values(
                event_logit_no_window_values, supported_logits[no_window]
            )
            self._m3s1_extend_float_values(
                event_logit_closed_mask_values, supported_logits[closed_mask]
            )
            closed_mask_row_count += int(closed_mask.sum().detach().cpu().item())

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
                    stopping_logits=flat_logits,
                    accepted_event=group.accepted_event,
                    censoring_kind=group.censoring_kind,
                    censor_step=group.censor_step,
                    support_horizon=group.support_horizon,
                )
            )

        self._m3s2_last_event_window_diagnostics = _M3S1GroupedStoppingDiagnostics(
            stop_logit_mean=self._m3s1_mean(event_logit_values),
            stop_logit_desirable_mean=self._m3s1_mean(event_logit_desirable_values),
            stop_logit_prewindow_mean=self._m3s1_mean(event_logit_prewindow_values),
            stop_logit_no_window_mean=self._m3s1_mean(event_logit_no_window_values),
            stop_logit_closed_mask_mean=self._m3s1_mean(event_logit_closed_mask_values),
            event_logit_delta_diagnostic_mean=self._m3s1_mean(event_logit_values),
            stop_logit_count=len(event_logit_values),
            stop_logit_desirable_count=len(event_logit_desirable_values),
            stop_logit_prewindow_count=len(event_logit_prewindow_values),
            stop_logit_no_window_count=len(event_logit_no_window_values),
            closed_mask_row_count=int(closed_mask_row_count),
            event_logit_delta_diagnostic_count=len(event_logit_values),
        )

        return compute_m3s1_grouped_stopping_loss(
            evidence,
            coef=float(self.m3s2_event_window_coef),
            early_mass_coef=float(self.m3s2_event_window_early_mass_coef),
            early_mass_budget=float(self.m3s2_event_window_early_mass_budget),
            early_survival_coef=float(self.m3s2_event_window_early_survival_coef),
            no_event_coef=float(self.m3s2_event_window_no_event_coef),
            window_delay_coef=float(self.m3s2_event_window_delay_coef),
            window_deadline_coef=float(self.m3s2_event_window_deadline_coef),
            window_deadline_steps=int(self.m3s2_event_window_deadline_steps),
            window_quality_boundary_coef=float(self.m3s2_event_window_quality_boundary_coef),
            window_quality_boundary_logit=float(self.m3s2_event_window_quality_boundary_logit),
            window_contrastive_margin_coef=float(self.m3s2_event_window_contrastive_margin_coef),
            window_contrastive_margin=float(self.m3s2_event_window_contrastive_margin),
            window_balanced_bce_coef=float(self.m3s2_event_window_balanced_bce_coef),
            window_prewindow_hazard_scale_coef=float(
                self.m3s2_event_window_prewindow_hazard_scale_coef
            ),
            window_prewindow_hazard_target=float(self.m3s2_event_window_prewindow_hazard_target),
            window_quality_hazard_target_coef=float(
                self.m3s2_event_window_quality_hazard_target_coef
            ),
            window_quality_hazard_target=float(self.m3s2_event_window_quality_hazard_target),
            window_prewindow_logit_ceiling_coef=float(
                self.m3s2_event_window_prewindow_logit_ceiling_coef
            ),
            window_prewindow_logit_ceiling=float(self.m3s2_event_window_prewindow_logit_ceiling),
            window_quality_logit_floor_coef=float(self.m3s2_event_window_quality_logit_floor_coef),
            window_quality_logit_floor=float(self.m3s2_event_window_quality_logit_floor),
            boundary_threshold=0.0,
        )

    def _m3s2_event_window_dedicated_optimizer(
        self,
        selected_ids: set[int],
    ) -> th.optim.Optimizer | None:
        if not self.m3s2_event_window_dedicated_optimizer_enabled:
            return None
        param_groups: list[dict[str, Any]] = []
        for group in self.policy.optimizer.param_groups:
            selected = [
                param
                for param in group.get("params", [])
                if id(param) in selected_ids and bool(getattr(param, "requires_grad", False))
            ]
            if not selected:
                continue
            cloned_group = {key: value for key, value in group.items() if key != "params"}
            cloned_group["params"] = selected
            param_groups.append(cloned_group)
        if not param_groups:
            return None
        optimizer_cls = self.policy.optimizer.__class__
        defaults = dict(getattr(self.policy.optimizer, "defaults", {}))
        try:
            return optimizer_cls(param_groups, **defaults)
        except TypeError:
            return th.optim.Adam(param_groups)

    def _m3s2_event_window_parameters(self) -> list[th.nn.Parameter]:
        if bool(getattr(self, "m3s2_event_window_use_stopping_head", False)):
            selected: list[th.nn.Parameter] = []
            stopping_norm = getattr(self.policy, "m3_stopping_norm", None)
            if stopping_norm is not None:
                selected.extend(
                    param for param in stopping_norm.parameters() if param.requires_grad
                )
            stopping_head = getattr(self.policy, "m3_stopping_head", None)
            if stopping_head is not None:
                selected.extend(
                    param for param in stopping_head.parameters() if param.requires_grad
                )
            if selected:
                return selected
        return self._a7_event_policy_margin_parameters()

    def _m3s2_event_window_auxiliary_update(self) -> M3S1GroupedStoppingLoss | None:
        self._m3s2_last_event_window_loss = None
        self._m3s2_last_event_window_grad_norm = 0.0
        self._m3s2_last_event_window_diagnostics = _M3S1GroupedStoppingDiagnostics()
        if not self._m3s2_event_window_enabled():
            return None

        selected_params = (
            self._m3s2_event_window_parameters()
            if self.m3s2_event_window_separate_update_enabled
            else [param for param in self.policy.parameters() if param.requires_grad]
        )
        if not selected_params:
            return None
        selected_ids = {id(param) for param in selected_params}
        aux_optimizer = self._m3s2_event_window_dedicated_optimizer(selected_ids)
        optimizer = aux_optimizer if aux_optimizer is not None else self.policy.optimizer

        last_loss: M3S1GroupedStoppingLoss | None = None
        max_grad_norm_seen = 0.0
        for _ in range(int(self.m3s2_event_window_separate_update_steps)):
            event_window_loss = self._m3s2_event_window_loss_from_sidecar()
            if event_window_loss is None:
                break
            last_loss = event_window_loss
            self._m3s2_last_event_window_loss = event_window_loss
            if (
                not event_window_loss.loss.requires_grad
                or float(event_window_loss.loss.detach().cpu().item()) == 0.0
                or int(event_window_loss.stats.active_group_count) <= 0
            ):
                break
            self.policy.optimizer.zero_grad(set_to_none=True)
            if aux_optimizer is not None:
                aux_optimizer.zero_grad(set_to_none=True)
            event_window_loss.loss.backward()
            if self.m3s2_event_window_separate_update_enabled:
                for param in self.policy.parameters():
                    if id(param) not in selected_ids:
                        param.grad = None
            max_norm = float(self.m3s2_event_window_max_grad_norm)
            if max_norm > 0.0:
                grad_norm_tensor = th.nn.utils.clip_grad_norm_(selected_params, max_norm)
                grad_norm = float(grad_norm_tensor.detach().cpu().item())
            else:
                grad_norm = 0.0
            max_grad_norm_seen = max(max_grad_norm_seen, grad_norm)
            optimizer.step()
            self.policy.optimizer.zero_grad(set_to_none=True)
            if aux_optimizer is not None:
                aux_optimizer.zero_grad(set_to_none=True)
        self._m3s2_last_event_window_grad_norm = float(max_grad_norm_seen)
        return last_loss

    @staticmethod
    def _m3s2_masked_float_mean(values: th.Tensor, mask: th.Tensor) -> float:
        if not bool(mask.any().detach().cpu().item()):
            return 0.0
        return float(values[mask].detach().mean().cpu().item())

    def _m3s2_fire_boundary_logit_delta(
        self,
        obs: dict[str, th.Tensor],
    ) -> tuple[th.Tensor, th.Tensor | None] | None:
        if self.m3s2_fire_boundary_separate_update_enabled:
            fast_delta_getter = getattr(
                self.policy,
                "get_hybrid_event_fire_boundary_deltas_for_head_update",
                None,
            )
            if callable(fast_delta_getter):
                fast_deltas = fast_delta_getter(obs)
                if fast_deltas is not None:
                    executable_delta, direct_head_delta = fast_deltas
                    return executable_delta, direct_head_delta

        distribution_getter = getattr(self.policy, "get_distribution", None)
        if not callable(distribution_getter):
            return None
        distribution = distribution_getter(obs)
        logit_delta_getter = getattr(distribution, "fire_event_logit_delta", None)
        if not callable(logit_delta_getter):
            return None
        event_logit_delta = logit_delta_getter()
        if event_logit_delta is None:
            return None

        direct_head_delta: th.Tensor | None = None
        direct_delta_getter = getattr(self.policy, "get_hybrid_event_head_delta", None)
        if callable(direct_delta_getter):
            with th.no_grad():
                direct_head_delta = direct_delta_getter(obs, detach_latent=True)
        return event_logit_delta, direct_head_delta

    def _m3s2_fire_boundary_loss_from_sidecar(self) -> _M3S2FireBoundaryLoss | None:
        sidecar = getattr(self, "_m3s1_grouped_stopping_sidecar", None)
        if sidecar is None or not sidecar.groups:
            return None

        executable_logits: list[th.Tensor] = []
        direct_head_deltas: list[th.Tensor] = []
        labels: list[th.Tensor] = []
        group_count = 0
        for group in sidecar.groups:
            obs = self._m3s1_observations_for_group(sidecar, group)
            boundary_deltas = self._m3s2_fire_boundary_logit_delta(obs)
            if boundary_deltas is None:
                return None
            event_logit_delta, direct_delta = boundary_deltas
            flat_logits = event_logit_delta.reshape(-1)
            if int(flat_logits.numel()) != len(group.row_indices):
                raise ValueError("M3-S2 fire boundary logits must match grouped sidecar rows")

            supported_logits, supported_legal, desirable, _prewindow, _no_window = (
                self._m3s1_group_diagnostic_masks(group, flat_logits)
            )
            active = supported_legal
            if not bool(active.any().detach().cpu().item()):
                continue
            group_count += 1
            executable_logits.append(supported_logits[active])
            labels.append(desirable[active].to(dtype=supported_logits.dtype))

            if direct_delta is not None and int(direct_delta.reshape(-1).numel()) == len(
                group.row_indices
            ):
                (
                    supported_direct,
                    supported_direct_legal,
                    _direct_desirable,
                    _direct_pre,
                    _direct_none,
                ) = self._m3s1_group_diagnostic_masks(group, direct_delta.reshape(-1))
                direct_head_deltas.append(supported_direct[supported_direct_legal])

        if not executable_logits:
            return None

        logits = th.cat(executable_logits, dim=0).reshape(-1)
        target = th.cat(labels, dim=0).to(device=logits.device, dtype=logits.dtype).reshape(-1)
        if int(logits.numel()) != int(target.numel()):
            raise ValueError("M3-S2 fire boundary logits and labels must have matching rows")

        positives = target > 0.5
        negatives = ~positives
        zero = logits.new_tensor(0.0)
        loss_terms: list[th.Tensor] = []
        if bool(positives.any().detach().cpu().item()):
            loss_terms.append(
                F.binary_cross_entropy_with_logits(
                    logits[positives],
                    th.ones_like(logits[positives]),
                    reduction="mean",
                )
            )
        if bool(negatives.any().detach().cpu().item()):
            loss_terms.append(
                F.binary_cross_entropy_with_logits(
                    logits[negatives],
                    th.zeros_like(logits[negatives]),
                    reduction="mean",
                )
            )
        if not loss_terms:
            return None
        balanced_bce_loss = sum(loss_terms) / float(len(loss_terms))

        negative_logit_ceiling_loss = zero
        if bool(negatives.any().detach().cpu().item()):
            negative_logit_ceiling_loss = F.relu(
                logits[negatives] - float(self.m3s2_fire_boundary_negative_logit_ceiling)
            ).mean()

        positive_logit_floor_loss = zero
        if bool(positives.any().detach().cpu().item()):
            positive_logit_floor_loss = F.relu(
                float(self.m3s2_fire_boundary_positive_logit_floor) - logits[positives]
            ).mean()

        unscaled_loss = (
            balanced_bce_loss
            + float(self.m3s2_fire_boundary_negative_logit_ceiling_coef)
            * negative_logit_ceiling_loss
            + float(self.m3s2_fire_boundary_positive_logit_floor_coef) * positive_logit_floor_loss
        )
        loss = float(self.m3s2_fire_boundary_coef) * unscaled_loss

        probs = th.sigmoid(logits.detach())
        detached_logits = logits.detach()
        positive_count = int(positives.sum().detach().cpu().item())
        negative_count = int(negatives.sum().detach().cpu().item())
        predictions = detached_logits >= 0.0
        accuracy = float(
            (predictions == positives.detach()).to(dtype=th.float32).mean().detach().cpu().item()
        )
        boundary_cross_count = int((detached_logits >= 0.0).sum().detach().cpu().item())
        boundary_cross_in_window_count = int(
            ((detached_logits >= 0.0) & positives).sum().detach().cpu().item()
        )

        direct_positive_mean = 0.0
        direct_negative_mean = 0.0
        if direct_head_deltas:
            direct_values = th.cat(direct_head_deltas, dim=0).reshape(-1)
            if int(direct_values.numel()) == int(positives.numel()):
                direct_positive_mean = self._m3s2_masked_float_mean(direct_values, positives)
                direct_negative_mean = self._m3s2_masked_float_mean(direct_values, negatives)

        return _M3S2FireBoundaryLoss(
            loss=loss,
            unscaled_loss=unscaled_loss,
            balanced_bce_loss=balanced_bce_loss,
            negative_logit_ceiling_loss=negative_logit_ceiling_loss,
            positive_logit_floor_loss=positive_logit_floor_loss,
            active_count=int(logits.numel()),
            positive_count=positive_count,
            negative_count=negative_count,
            group_count=int(group_count),
            executable_positive_logit_mean=self._m3s2_masked_float_mean(detached_logits, positives),
            executable_negative_logit_mean=self._m3s2_masked_float_mean(detached_logits, negatives),
            executable_positive_prob_mean=self._m3s2_masked_float_mean(probs, positives),
            executable_negative_prob_mean=self._m3s2_masked_float_mean(probs, negatives),
            direct_head_positive_delta_mean=direct_positive_mean,
            direct_head_negative_delta_mean=direct_negative_mean,
            accuracy=accuracy,
            boundary_cross_count=boundary_cross_count,
            boundary_cross_in_window_count=boundary_cross_in_window_count,
        )

    def _m3s2_fire_boundary_dedicated_optimizer(
        self,
        selected_ids: set[int],
    ) -> th.optim.Optimizer | None:
        if not self.m3s2_fire_boundary_dedicated_optimizer_enabled:
            return None
        param_groups: list[dict[str, Any]] = []
        for group in self.policy.optimizer.param_groups:
            selected = [
                param
                for param in group.get("params", [])
                if id(param) in selected_ids and bool(getattr(param, "requires_grad", False))
            ]
            if not selected:
                continue
            cloned_group = {key: value for key, value in group.items() if key != "params"}
            cloned_group["params"] = selected
            param_groups.append(cloned_group)
        if not param_groups:
            return None
        optimizer_cls = self.policy.optimizer.__class__
        defaults = dict(getattr(self.policy.optimizer, "defaults", {}))
        try:
            return optimizer_cls(param_groups, **defaults)
        except TypeError:
            return th.optim.Adam(param_groups)

    def _m3s2_fire_boundary_parameters(self) -> list[th.nn.Parameter]:
        event_head = getattr(self.policy, "hybrid_event_head", None)
        if event_head is None:
            return []
        return [param for param in event_head.parameters() if param.requires_grad]

    def _m3s2_fire_boundary_auxiliary_update(self) -> _M3S2FireBoundaryLoss | None:
        self._m3s2_last_fire_boundary_loss = None
        self._m3s2_last_fire_boundary_grad_norm = 0.0
        if not self._m3s2_fire_boundary_enabled():
            return None

        selected_params = (
            self._m3s2_fire_boundary_parameters()
            if self.m3s2_fire_boundary_separate_update_enabled
            else [param for param in self.policy.parameters() if param.requires_grad]
        )
        if not selected_params:
            return None
        selected_ids = {id(param) for param in selected_params}
        aux_optimizer = self._m3s2_fire_boundary_dedicated_optimizer(selected_ids)
        optimizer = aux_optimizer if aux_optimizer is not None else self.policy.optimizer

        last_loss: _M3S2FireBoundaryLoss | None = None
        max_grad_norm_seen = 0.0
        for _ in range(int(self.m3s2_fire_boundary_separate_update_steps)):
            fire_boundary_loss = self._m3s2_fire_boundary_loss_from_sidecar()
            if fire_boundary_loss is None:
                break
            last_loss = fire_boundary_loss
            self._m3s2_last_fire_boundary_loss = fire_boundary_loss
            if (
                not fire_boundary_loss.loss.requires_grad
                or float(fire_boundary_loss.loss.detach().cpu().item()) == 0.0
                or int(fire_boundary_loss.active_count) <= 0
            ):
                break
            self.policy.optimizer.zero_grad(set_to_none=True)
            if aux_optimizer is not None:
                aux_optimizer.zero_grad(set_to_none=True)
            fire_boundary_loss.loss.backward()
            if self.m3s2_fire_boundary_separate_update_enabled:
                for param in self.policy.parameters():
                    if id(param) not in selected_ids:
                        param.grad = None
            max_norm = float(self.m3s2_fire_boundary_max_grad_norm)
            if max_norm > 0.0:
                grad_norm_tensor = th.nn.utils.clip_grad_norm_(selected_params, max_norm)
                grad_norm = float(grad_norm_tensor.detach().cpu().item())
            else:
                grad_norm = 0.0
            max_grad_norm_seen = max(max_grad_norm_seen, grad_norm)
            optimizer.step()
            self.policy.optimizer.zero_grad(set_to_none=True)
            if aux_optimizer is not None:
                aux_optimizer.zero_grad(set_to_none=True)

        final_loss = self._m3s2_fire_boundary_loss_from_sidecar()
        if final_loss is not None:
            last_loss = final_loss
            self._m3s2_last_fire_boundary_loss = final_loss
        self._m3s2_last_fire_boundary_grad_norm = float(max_grad_norm_seen)
        return last_loss

    def _m3s2_window_classifier_parameters(self) -> list[th.nn.Parameter]:
        selected: list[th.nn.Parameter] = []
        classifier_norm = getattr(self.policy, "m3_window_classifier_norm", None)
        if classifier_norm is not None:
            selected.extend(param for param in classifier_norm.parameters() if param.requires_grad)
        classifier_head = getattr(self.policy, "m3_window_classifier_head", None)
        if classifier_head is not None:
            selected.extend(param for param in classifier_head.parameters() if param.requires_grad)
        return selected

    def _m3s2_window_classifier_loss_from_sidecar(
        self,
        *,
        update_replay: bool = True,
        refresh_standardization: bool = True,
    ) -> _M3S2WindowClassifierLoss | None:
        sidecar = getattr(self, "_m3s1_grouped_stopping_sidecar", None)
        if sidecar is None or not sidecar.groups:
            return None
        latent_getter = getattr(self.policy, "get_m3_window_latent", None)
        logits_from_latent = getattr(self.policy, "get_m3_window_logits_from_latent", None)
        standardization_updater = getattr(
            self.policy,
            "update_m3_window_classifier_input_standardization",
            None,
        )
        if not callable(latent_getter) or not callable(logits_from_latent):
            return None

        active_latents: list[th.Tensor] = []
        active_labels: list[th.Tensor] = []
        active_observations: list[dict[str, th.Tensor]] = []
        group_count = 0
        for group in sidecar.groups:
            obs = self._m3s1_observations_for_group(sidecar, group)
            latents = latent_getter(
                obs,
                detach_latent=bool(self.m3s2_window_classifier_detach_latent),
            )
            if latents is None:
                return None
            flat_latents = latents.reshape(int(latents.shape[0]), -1)
            if int(flat_latents.shape[0]) != len(group.row_indices):
                raise ValueError("M3-S2 window classifier latents must match grouped sidecar rows")
            supported_latents, supported_legal, desirable, _prewindow, _no_window = (
                self._m3s1_group_diagnostic_masks(group, flat_latents)
            )
            row_positions = th.arange(
                len(group.row_indices), device=flat_latents.device, dtype=th.long
            )
            (
                supported_positions,
                _supported_legal_for_pos,
                _desirable_for_pos,
                _prewindow_for_pos,
                _no_window_for_pos,
            ) = self._m3s1_group_diagnostic_masks(group, row_positions)
            active = supported_legal
            if not bool(active.any().detach().cpu().item()):
                continue
            group_count += 1
            active_latents.append(supported_latents[active])
            active_labels.append(desirable[active].to(dtype=supported_latents.dtype))
            active_positions = supported_positions[active].reshape(-1).to(dtype=th.long)
            active_observations.append(
                {key: value.index_select(0, active_positions) for key, value in obs.items()}
            )

        if not active_latents:
            return None

        latents = th.cat(active_latents, dim=0).reshape(-1, int(active_latents[0].shape[-1]))
        labels = th.cat(active_labels, dim=0).reshape(-1)
        observations = self._m3s2_concat_observation_batches(active_observations)
        replay = getattr(self, "_m3s2_window_classifier_replay", None)
        replay_enabled = bool(self.m3s2_window_classifier_replay_enabled and replay is not None)
        replay_used = False
        if replay_enabled and isinstance(replay, _M3S2WindowClassifierReplay):
            if update_replay:
                replay.append(latents, labels, observations=observations)
            standardization_batch = replay.calibration_balanced(
                max_rows=int(self.m3s2_window_classifier_replay_batch_size),
                device=self.device,
                dtype=latents.dtype,
            )
            if (
                refresh_standardization
                and callable(standardization_updater)
                and standardization_batch is not None
            ):
                standardization_samples, _standardization_labels = standardization_batch
                if isinstance(standardization_samples, dict):
                    standardization_latents = latent_getter(
                        standardization_samples,
                        detach_latent=bool(self.m3s2_window_classifier_detach_latent),
                    )
                    if standardization_latents is None:
                        return None
                    standardization_latents = standardization_latents.reshape(
                        int(standardization_latents.shape[0]),
                        -1,
                    )
                else:
                    standardization_latents = standardization_samples.reshape(
                        int(standardization_samples.shape[0]),
                        -1,
                    )
                standardization_updater(standardization_latents)
            if replay.can_sample(
                min_positive=int(self.m3s2_window_classifier_replay_min_positive),
                min_negative=int(self.m3s2_window_classifier_replay_min_negative),
            ):
                sampled = replay.sample_balanced(
                    batch_size=int(self.m3s2_window_classifier_replay_batch_size),
                    device=self.device,
                    dtype=latents.dtype,
                )
                if sampled is not None:
                    replay_batch, labels = sampled
                    if isinstance(replay_batch, dict):
                        sampled_latents = latent_getter(
                            replay_batch,
                            detach_latent=bool(self.m3s2_window_classifier_detach_latent),
                        )
                        if sampled_latents is None:
                            return None
                        latents = sampled_latents.reshape(int(sampled_latents.shape[0]), -1)
                    else:
                        latents = replay_batch.reshape(int(replay_batch.shape[0]), -1)
                    replay_used = True

        if refresh_standardization and callable(standardization_updater) and not replay_used:
            standardization_updater(latents)
        logits = logits_from_latent(latents)
        if logits is None:
            return None
        logits = logits.reshape(-1)
        labels = labels.to(device=logits.device, dtype=logits.dtype).reshape(-1)
        if int(logits.numel()) != int(labels.numel()):
            raise ValueError("M3-S2 window classifier logits and labels must have matching rows")
        positives = labels > 0.5
        negatives = ~positives
        zero = logits.new_tensor(0.0)
        loss_terms: list[th.Tensor] = []
        if bool(positives.any().detach().cpu().item()):
            loss_terms.append(
                F.binary_cross_entropy_with_logits(
                    logits[positives],
                    th.ones_like(logits[positives]),
                    reduction="mean",
                )
            )
        if bool(negatives.any().detach().cpu().item()):
            loss_terms.append(
                F.binary_cross_entropy_with_logits(
                    logits[negatives],
                    th.zeros_like(logits[negatives]),
                    reduction="mean",
                )
            )
        if not loss_terms:
            return None
        balanced_bce_loss = sum(loss_terms) / float(len(loss_terms))

        prewindow_logit_ceiling_loss = zero
        if bool(negatives.any().detach().cpu().item()):
            prewindow_logit_ceiling_loss = F.relu(
                logits[negatives] - float(self.m3s2_window_classifier_prewindow_logit_ceiling)
            ).mean()

        quality_logit_floor_loss = zero
        if bool(positives.any().detach().cpu().item()):
            quality_logit_floor_loss = F.relu(
                float(self.m3s2_window_classifier_quality_logit_floor) - logits[positives]
            ).mean()

        unscaled_loss = (
            balanced_bce_loss
            + float(self.m3s2_window_classifier_prewindow_logit_ceiling_coef)
            * prewindow_logit_ceiling_loss
            + float(self.m3s2_window_classifier_quality_logit_floor_coef) * quality_logit_floor_loss
        )
        loss = float(self.m3s2_window_classifier_coef) * unscaled_loss

        probs = th.sigmoid(logits.detach())
        detached_logits = logits.detach()
        positive_count = int(positives.sum().detach().cpu().item())
        negative_count = int(negatives.sum().detach().cpu().item())
        predictions = probs >= 0.5
        accuracy = float(
            (predictions == positives.detach()).to(dtype=th.float32).mean().detach().cpu().item()
        )

        def _masked_mean(values: th.Tensor, mask: th.Tensor) -> float:
            if not bool(mask.any().detach().cpu().item()):
                return 0.0
            return float(values[mask].mean().detach().cpu().item())

        return _M3S2WindowClassifierLoss(
            loss=loss,
            unscaled_loss=unscaled_loss,
            balanced_bce_loss=balanced_bce_loss,
            prewindow_logit_ceiling_loss=prewindow_logit_ceiling_loss,
            quality_logit_floor_loss=quality_logit_floor_loss,
            active_count=int(logits.numel()),
            positive_count=positive_count,
            negative_count=negative_count,
            group_count=int(group_count),
            positive_logit_mean=_masked_mean(detached_logits, positives),
            negative_logit_mean=_masked_mean(detached_logits, negatives),
            positive_prob_mean=_masked_mean(probs, positives),
            negative_prob_mean=_masked_mean(probs, negatives),
            accuracy=accuracy,
            replay_enabled=replay_enabled,
            replay_used=replay_used,
            replay_positive_count=(
                int(replay.positive_count) if isinstance(replay, _M3S2WindowClassifierReplay) else 0
            ),
            replay_negative_count=(
                int(replay.negative_count) if isinstance(replay, _M3S2WindowClassifierReplay) else 0
            ),
        )

    def _m3s2_window_classifier_dedicated_optimizer(
        self,
        selected_ids: set[int],
    ) -> th.optim.Optimizer | None:
        if not self.m3s2_window_classifier_dedicated_optimizer_enabled:
            return None
        param_groups: list[dict[str, Any]] = []
        for group in self.policy.optimizer.param_groups:
            selected = [
                param
                for param in group.get("params", [])
                if id(param) in selected_ids and bool(getattr(param, "requires_grad", False))
            ]
            if not selected:
                continue
            cloned_group = {key: value for key, value in group.items() if key != "params"}
            cloned_group["params"] = selected
            param_groups.append(cloned_group)
        if not param_groups:
            return None
        optimizer_cls = self.policy.optimizer.__class__
        defaults = dict(getattr(self.policy.optimizer, "defaults", {}))
        try:
            return optimizer_cls(param_groups, **defaults)
        except TypeError:
            return th.optim.Adam(param_groups)

    @staticmethod
    def _m3s2_concat_observation_batches(
        batches: list[dict[str, th.Tensor]],
    ) -> dict[str, th.Tensor] | None:
        if not batches:
            return None
        keys = set(batches[0].keys())
        for batch in batches[1:]:
            if set(batch.keys()) != keys:
                raise ValueError("M3-S2 window classifier sidecar observation keys changed")
        return {key: th.cat([batch[key] for batch in batches], dim=0) for key in batches[0].keys()}

    def _m3s2_window_classifier_auxiliary_update(self) -> _M3S2WindowClassifierLoss | None:
        self._m3s2_last_window_classifier_loss = None
        self._m3s2_last_window_classifier_grad_norm = 0.0
        if not self._m3s2_window_classifier_enabled():
            return None

        selected_params = (
            self._m3s2_window_classifier_parameters()
            if self.m3s2_window_classifier_separate_update_enabled
            else [param for param in self.policy.parameters() if param.requires_grad]
        )
        if not selected_params:
            return None
        selected_ids = {id(param) for param in selected_params}
        aux_optimizer = self._m3s2_window_classifier_dedicated_optimizer(selected_ids)
        optimizer = aux_optimizer if aux_optimizer is not None else self.policy.optimizer

        last_loss: _M3S2WindowClassifierLoss | None = None
        best_loss_value: float | None = None
        best_param_values: list[th.Tensor] | None = None
        max_grad_norm_seen = 0.0

        def _capture_selected_params() -> list[th.Tensor]:
            return [param.detach().clone() for param in selected_params]

        def _restore_selected_params(values: list[th.Tensor]) -> None:
            with th.no_grad():
                for param, value in zip(selected_params, values):
                    param.copy_(value.to(device=param.device, dtype=param.dtype))

        def _maybe_capture_best(candidate: _M3S2WindowClassifierLoss) -> None:
            nonlocal best_loss_value, best_param_values
            loss_value = float(candidate.unscaled_loss.detach().cpu().item())
            if best_loss_value is None or loss_value < best_loss_value:
                best_loss_value = loss_value
                best_param_values = _capture_selected_params()

        for step_idx in range(int(self.m3s2_window_classifier_separate_update_steps)):
            classifier_loss = self._m3s2_window_classifier_loss_from_sidecar(
                update_replay=(step_idx == 0),
                refresh_standardization=(step_idx == 0),
            )
            if classifier_loss is None:
                break
            last_loss = classifier_loss
            self._m3s2_last_window_classifier_loss = classifier_loss
            _maybe_capture_best(classifier_loss)
            if (
                not classifier_loss.loss.requires_grad
                or float(classifier_loss.loss.detach().cpu().item()) == 0.0
                or int(classifier_loss.active_count) <= 0
            ):
                break
            self.policy.optimizer.zero_grad(set_to_none=True)
            if aux_optimizer is not None:
                aux_optimizer.zero_grad(set_to_none=True)
            classifier_loss.loss.backward()
            if self.m3s2_window_classifier_separate_update_enabled:
                for param in self.policy.parameters():
                    if id(param) not in selected_ids:
                        param.grad = None
            max_norm = float(self.m3s2_window_classifier_max_grad_norm)
            if max_norm > 0.0:
                grad_norm_tensor = th.nn.utils.clip_grad_norm_(selected_params, max_norm)
                grad_norm = float(grad_norm_tensor.detach().cpu().item())
            else:
                grad_norm = 0.0
            max_grad_norm_seen = max(max_grad_norm_seen, grad_norm)
            optimizer.step()
            self.policy.optimizer.zero_grad(set_to_none=True)
            if aux_optimizer is not None:
                aux_optimizer.zero_grad(set_to_none=True)
        final_post_step_loss = self._m3s2_window_classifier_loss_from_sidecar(
            update_replay=False,
            refresh_standardization=False,
        )
        if final_post_step_loss is not None:
            last_loss = final_post_step_loss
            self._m3s2_last_window_classifier_loss = final_post_step_loss
            _maybe_capture_best(final_post_step_loss)
        if best_param_values is not None:
            _restore_selected_params(best_param_values)
            restored_loss = self._m3s2_window_classifier_loss_from_sidecar(
                update_replay=False,
                refresh_standardization=False,
            )
            if restored_loss is not None:
                last_loss = restored_loss
                self._m3s2_last_window_classifier_loss = restored_loss
        self._m3s2_last_window_classifier_grad_norm = float(max_grad_norm_seen)
        return last_loss


_ = (Any, M3S1_CENSOR_EARLY_EVENT_PREFIX)  # suppress unused-import
