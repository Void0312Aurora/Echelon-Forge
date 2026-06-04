from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import torch as th
import torch.nn as nn
from torch.distributions import Bernoulli, Categorical, Normal
from gymnasium import spaces

from stable_baselines3.common.distributions import SquashedDiagGaussianDistribution
from stable_baselines3.common.preprocessing import get_action_dim
from stable_baselines3.common.policies import MultiInputActorCriticPolicy

from .hmoe_routing import (
    DEFAULT_FAMILY_SUBEXPERT_COUNTS,
    FAMILY_DEPARTURE_NAV,
    family_name,
    route_from_mission_observation,
    subexpert_name,
)


class SquashedMultiInputPolicy(MultiInputActorCriticPolicy):
    """
    Multi-input PPO policy that uses a tanh-squashed Gaussian distribution for Box actions.

    Why:
    - SB3 PPO normally samples from an unbounded Gaussian and then clips actions before env.step().
      That breaks the PPO log-prob/ratio math for out-of-bound samples.
    - A squashed distribution keeps actions in (-1, 1) and uses SB3's `squash_output` path
      so actions are unscaled to env bounds without clipping mismatch.
    """

    def __init__(self, *args: Any, squash_output: Optional[bool] = True, **kwargs: Any):
        # SB3 asserts `squash_output=True` requires gSDE; we intentionally bypass that by:
        # - building as usual (unbounded DiagGaussian)
        # - swapping to SquashedDiagGaussianDistribution after init
        # - enabling the `squash_output` code path for unscale_action()
        super().__init__(*args, squash_output=False, **kwargs)

        if squash_output is None:
            squash_output = True

        if squash_output:
            if not isinstance(self.action_space, spaces.Box):
                raise TypeError(f"SquashedMultiInputPolicy only supports Box action spaces, got {type(self.action_space)}")
            self.action_dist = SquashedDiagGaussianDistribution(get_action_dim(self.action_space))
            self._squash_output = True

    def _get_constructor_parameters(self) -> dict[str, Any]:
        data = super()._get_constructor_parameters()
        data["squash_output"] = bool(self.squash_output)
        return data


class _HMoEHeadBank(nn.Module):
    def __init__(
        self,
        latent_dim: int,
        action_dim: int,
        *,
        family_subexpert_counts: tuple[int, ...],
    ) -> None:
        super().__init__()
        self.family_subexpert_counts = tuple(int(max(1, v)) for v in family_subexpert_counts)
        self.family_heads = nn.ModuleList([nn.Linear(int(latent_dim), int(action_dim)) for _ in self.family_subexpert_counts])
        self.subexpert_heads = nn.ModuleList(
            [
                nn.ModuleList([nn.Linear(int(latent_dim), int(action_dim)) for _ in range(count)])
                for count in self.family_subexpert_counts
            ]
        )
        self.reset_parameters()

    def reset_parameters(self) -> None:
        # Start HMoE from the shared-policy baseline and let routed heads learn residuals.
        # This keeps the initial policy close to the already-stable single-head PPO path.
        for head in self.family_heads:
            nn.init.zeros_(head.weight)
            nn.init.zeros_(head.bias)
        for family_subheads in self.subexpert_heads:
            for head in family_subheads:
                nn.init.zeros_(head.weight)
                nn.init.zeros_(head.bias)

    def forward(self, latent_pi: th.Tensor, family_index: th.Tensor, subexpert_index: th.Tensor) -> th.Tensor:
        batch_size = int(latent_pi.shape[0])
        action_dim = int(self.family_heads[0].out_features)
        out = latent_pi.new_zeros((batch_size, action_dim))

        for family_id, family_head in enumerate(self.family_heads):
            family_mask = family_index == int(family_id)
            if int(family_mask.sum().item()) <= 0:
                continue
            family_latent = latent_pi[family_mask]
            family_out = family_head(family_latent)
            family_subheads = self.subexpert_heads[family_id]
            family_subidx = subexpert_index[family_mask]
            family_sub_count = int(len(family_subheads))
            if family_sub_count > 0:
                family_subidx = th.clamp(family_subidx, min=0, max=family_sub_count - 1)
                residual = th.zeros_like(family_out)
                for sub_id, sub_head in enumerate(family_subheads):
                    sub_mask = family_subidx == int(sub_id)
                    if int(sub_mask.sum().item()) <= 0:
                        continue
                    residual[sub_mask] = sub_head(family_latent[sub_mask])
                family_out = family_out + residual
            out[family_mask] = family_out
        return out


class _HybridActionLayout:
    def __init__(
        self,
        *,
        name: str,
        action_dim: int,
        continuous_indices: tuple[int, ...],
        binary_indices: tuple[int, ...],
        event_action_index: int | None = None,
        categorical_indices: tuple[tuple[int, int], ...],
    ) -> None:
        self.name = str(name)
        self.action_dim = int(action_dim)
        self.continuous_indices = tuple(int(i) for i in continuous_indices)
        self.binary_indices = tuple(int(i) for i in binary_indices)
        self.event_action_index = None if event_action_index is None else int(event_action_index)
        self.categorical_indices = tuple((int(i), int(n)) for i, n in categorical_indices)
        self.continuous_count = int(len(self.continuous_indices))
        self.binary_count = int(len(self.binary_indices))
        self.event_logit_count = 1 if self.event_action_index is not None else 0
        if self.event_action_index is not None and self.event_action_index not in self.binary_indices:
            raise ValueError("event_action_index must also appear in binary_indices for flat transport compatibility")
        self.event_binary_position = (
            self.binary_indices.index(self.event_action_index) if self.event_action_index is not None else None
        )
        self.ordinary_binary_positions = tuple(
            idx for idx, action_idx in enumerate(self.binary_indices) if action_idx != self.event_action_index
        )
        self.ordinary_binary_indices = tuple(
            action_idx for action_idx in self.binary_indices if action_idx != self.event_action_index
        )
        self.categorical_logit_count = int(sum(n for _, n in self.categorical_indices))
        self.param_dim = int(
            self.continuous_count + self.binary_count + self.event_logit_count + self.categorical_logit_count
        )

    @property
    def event_fire_param_index(self) -> int | None:
        if self.event_binary_position is None:
            return None
        return int(self.continuous_count) + int(self.event_binary_position)

    @property
    def event_hold_param_index(self) -> int | None:
        if self.event_action_index is None:
            return None
        return int(self.continuous_count) + int(self.binary_count)


def _normalize_hybrid_action_layout(spec: Any, action_space) -> _HybridActionLayout | None:
    if spec is None:
        return None
    if isinstance(spec, str):
        name = spec.strip()
        if name == "" or name.lower() in {"none", "off", "false", "0"}:
            return None
    elif isinstance(spec, dict):
        name = str(spec.get("name", spec.get("mode", ""))).strip()
    else:
        raise TypeError(f"hybrid_action_spec must be a string, dict or None, got {type(spec)}")

    if name != "air_combat_hybrid_v1":
        raise ValueError(f"Unknown hybrid_action_spec: {name!r}")
    action_dim = int(get_action_dim(action_space))
    if action_dim != 12:
        raise ValueError(
            "hybrid_action_spec='air_combat_hybrid_v1' requires a 12D transport action space, "
            f"got {action_dim}D."
        )
    return _HybridActionLayout(
        name=name,
        action_dim=12,
        continuous_indices=(0, 1, 2, 3, 4, 5),
        binary_indices=(6, 7, 8, 9, 10),
        event_action_index=9,
        categorical_indices=((11, 8),),
    )


def _hybrid_fire_event_mask_from_obs(obs: Any, *, batch_size: int, device: th.device) -> th.Tensor | None:
    if not isinstance(obs, dict):
        return None

    explicit_event_mask = obs.get("event_action_mask")
    if explicit_event_mask is not None:
        mask = th.as_tensor(explicit_event_mask, device=device)
        if mask.ndim == 1:
            mask = mask.reshape(1, -1)
        if mask.ndim == 2 and int(mask.shape[1]) >= 2:
            return mask[:, 1].to(dtype=th.bool)

    explicit_fire_mask = obs.get("fire_mask")
    if explicit_fire_mask is not None:
        mask = th.as_tensor(explicit_fire_mask, device=device)
        return mask.reshape(-1).to(dtype=th.bool)

    mission = obs.get("mission")
    if mission is None:
        return None
    mission_tensor = th.as_tensor(mission, device=device)
    if mission_tensor.ndim != 2 or int(mission_tensor.shape[1]) != 20:
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
    if int(fire_mask.shape[0]) != int(batch_size):
        return None
    return fire_mask


class _HybridActionDistribution:
    def __init__(
        self,
        *,
        layout: _HybridActionLayout,
        params: th.Tensor,
        log_std: th.Tensor,
        action_low,
        action_high,
        fire_event_mask: th.Tensor | None = None,
        fire_event_q_values: th.Tensor | None = None,
    ) -> None:
        self.layout = layout
        self.params = params
        self.log_std = log_std
        device = params.device
        dtype = params.dtype
        self.action_low = th.as_tensor(action_low, dtype=dtype, device=device).reshape(-1)
        self.action_high = th.as_tensor(action_high, dtype=dtype, device=device).reshape(-1)
        self.continuous_indices = th.as_tensor(layout.continuous_indices, dtype=th.long, device=device)
        self.binary_indices = th.as_tensor(layout.binary_indices, dtype=th.long, device=device)
        self.ordinary_binary_indices = th.as_tensor(layout.ordinary_binary_indices, dtype=th.long, device=device)
        self.ordinary_binary_positions = th.as_tensor(layout.ordinary_binary_positions, dtype=th.long, device=device)
        self.fire_event_mask = self._normalize_fire_event_mask(fire_event_mask)
        self._fire_event_q_values = self._normalize_fire_event_q_values(fire_event_q_values)
        self._split_params()

    def _split_params(self) -> None:
        offset = 0
        cont_n = self.layout.continuous_count
        bin_n = self.layout.binary_count
        self.continuous_mean = self.params[:, offset : offset + cont_n]
        offset += cont_n
        self.binary_logits = self.params[:, offset : offset + bin_n]
        offset += bin_n
        self.fire_event_hold_logits = None
        if self.layout.event_action_index is not None:
            self.fire_event_hold_logits = self.params[:, offset]
            offset += 1
        self.categorical_logits: list[tuple[int, th.Tensor]] = []
        for action_index, category_count in self.layout.categorical_indices:
            logits = self.params[:, offset : offset + int(category_count)]
            offset += int(category_count)
            self.categorical_logits.append((int(action_index), logits))

    def _normalize_fire_event_mask(self, fire_event_mask: th.Tensor | None) -> th.Tensor | None:
        if self.layout.event_action_index is None:
            return None
        batch = int(self.params.shape[0])
        if fire_event_mask is None:
            fire = th.ones((batch,), dtype=th.bool, device=self.params.device)
        else:
            fire = fire_event_mask.to(device=self.params.device).reshape(-1).to(dtype=th.bool)
            if int(fire.shape[0]) != batch:
                raise ValueError(f"fire_event_mask batch {int(fire.shape[0])} does not match params batch {batch}")
        hold = th.ones_like(fire, dtype=th.bool)
        return th.stack((hold, fire), dim=1)

    def _normalize_fire_event_q_values(self, q_values: th.Tensor | None) -> th.Tensor | None:
        if q_values is None or self.layout.event_action_index is None:
            return None
        values = q_values.to(device=self.params.device, dtype=self.params.dtype)
        if values.ndim != 2 or int(values.shape[1]) != 2:
            raise ValueError("fire_event_q_values must have shape [batch, 2]")
        if int(values.shape[0]) != int(self.params.shape[0]):
            raise ValueError(
                f"fire_event_q_values batch {int(values.shape[0])} does not match params batch {int(self.params.shape[0])}"
            )
        return values

    def _fire_event_logits(self) -> th.Tensor | None:
        logits = self.fire_event_unmasked_logits()
        if logits is None:
            return None
        if self.fire_event_mask is None:
            return logits
        masked_floor = th.full_like(logits, -1.0e8)
        return th.where(self.fire_event_mask, logits, masked_floor)

    def fire_event_unmasked_logits(self) -> th.Tensor | None:
        if self.layout.event_action_index is None or self.fire_event_hold_logits is None:
            return None
        if self.layout.event_binary_position is None:
            return None
        fire_logits = self.binary_logits[:, int(self.layout.event_binary_position)]
        return th.stack((self.fire_event_hold_logits, fire_logits), dim=1)

    def fire_event_logit_delta(self) -> th.Tensor | None:
        logits = self.fire_event_unmasked_logits()
        if logits is None:
            return None
        return logits[:, 1] - logits[:, 0]

    def fire_event_probability(self) -> th.Tensor | None:
        delta = self.fire_event_logit_delta()
        if delta is None:
            return None
        return th.sigmoid(delta)

    def fire_event_q_values(self) -> th.Tensor | None:
        return self._fire_event_q_values

    def fire_event_advantage(self) -> th.Tensor | None:
        values = self.fire_event_q_values()
        if values is None:
            return None
        return values[:, 1] - values[:, 0]

    def _continuous_bounds(self) -> tuple[th.Tensor, th.Tensor, th.Tensor]:
        low = self.action_low[self.continuous_indices].reshape(1, -1)
        high = self.action_high[self.continuous_indices].reshape(1, -1)
        scale = th.clamp((high - low) * 0.5, min=1.0e-6)
        return low, high, scale

    @staticmethod
    def _atanh(x: th.Tensor) -> th.Tensor:
        x = th.clamp(x, -1.0 + 1.0e-6, 1.0 - 1.0e-6)
        return 0.5 * (th.log1p(x) - th.log1p(-x))

    def _transform_continuous(self, raw: th.Tensor) -> th.Tensor:
        low, _high, scale = self._continuous_bounds()
        return low + (th.tanh(raw) + 1.0) * scale

    def _inverse_continuous(self, actions: th.Tensor) -> tuple[th.Tensor, th.Tensor, th.Tensor]:
        low, _high, scale = self._continuous_bounds()
        y = th.clamp((actions - low) / scale - 1.0, -1.0 + 1.0e-6, 1.0 - 1.0e-6)
        return self._atanh(y), y, scale

    def mode(self) -> th.Tensor:
        batch = int(self.params.shape[0])
        actions = self.params.new_zeros((batch, self.layout.action_dim))
        if self.layout.continuous_count > 0:
            actions[:, self.continuous_indices] = self._transform_continuous(self.continuous_mean)
        if int(self.ordinary_binary_positions.numel()) > 0:
            actions[:, self.ordinary_binary_indices] = (
                self.binary_logits[:, self.ordinary_binary_positions] >= 0.0
            ).to(dtype=self.params.dtype)
        event_logits = self._fire_event_logits()
        if event_logits is not None and self.layout.event_action_index is not None:
            actions[:, int(self.layout.event_action_index)] = th.argmax(event_logits, dim=1).to(dtype=self.params.dtype)
        for action_index, logits in self.categorical_logits:
            actions[:, action_index] = th.argmax(logits, dim=1).to(dtype=self.params.dtype)
        return actions

    def get_actions(self, deterministic: bool = False) -> th.Tensor:
        if deterministic:
            return self.mode()
        batch = int(self.params.shape[0])
        actions = self.params.new_zeros((batch, self.layout.action_dim))
        if self.layout.continuous_count > 0:
            std = th.exp(self.log_std).reshape(1, -1).expand_as(self.continuous_mean)
            raw = self.continuous_mean + std * th.randn_like(self.continuous_mean)
            actions[:, self.continuous_indices] = self._transform_continuous(raw)
        if int(self.ordinary_binary_positions.numel()) > 0:
            actions[:, self.ordinary_binary_indices] = Bernoulli(
                logits=self.binary_logits[:, self.ordinary_binary_positions]
            ).sample()
        event_logits = self._fire_event_logits()
        if event_logits is not None and self.layout.event_action_index is not None:
            actions[:, int(self.layout.event_action_index)] = Categorical(logits=event_logits).sample().to(
                dtype=self.params.dtype
            )
        for action_index, logits in self.categorical_logits:
            actions[:, action_index] = Categorical(logits=logits).sample().to(dtype=self.params.dtype)
        return actions

    def log_prob(self, actions: th.Tensor) -> th.Tensor:
        actions = actions.reshape((-1, self.layout.action_dim)).to(device=self.params.device, dtype=self.params.dtype)
        total = self.params.new_zeros((int(actions.shape[0]),))
        if self.layout.continuous_count > 0:
            cont_actions = actions[:, self.continuous_indices]
            raw, y, scale = self._inverse_continuous(cont_actions)
            std = th.exp(self.log_std).reshape(1, -1).expand_as(self.continuous_mean)
            normal = Normal(self.continuous_mean, std)
            correction = th.log(scale) + th.log(th.clamp(1.0 - y.pow(2), min=1.0e-6))
            total = total + (normal.log_prob(raw) - correction).sum(dim=1)
        if int(self.ordinary_binary_positions.numel()) > 0:
            binary_actions = th.clamp(actions[:, self.ordinary_binary_indices], 0.0, 1.0).round()
            total = total + Bernoulli(logits=self.binary_logits[:, self.ordinary_binary_positions]).log_prob(
                binary_actions
            ).sum(dim=1)
        event_logits = self._fire_event_logits()
        if event_logits is not None and self.layout.event_action_index is not None:
            event_action = th.clamp(actions[:, int(self.layout.event_action_index)].round().long(), 0, 1)
            total = total + Categorical(logits=event_logits).log_prob(event_action)
        for action_index, logits in self.categorical_logits:
            categorical_action = th.clamp(actions[:, action_index].round().long(), 0, int(logits.shape[1]) - 1)
            total = total + Categorical(logits=logits).log_prob(categorical_action)
        return total

    def entropy(self):
        total = self.params.new_zeros((int(self.params.shape[0]),))
        if self.layout.continuous_count > 0:
            std = th.exp(self.log_std).reshape(1, -1).expand_as(self.continuous_mean)
            total = total + Normal(self.continuous_mean, std).entropy().sum(dim=1)
        if int(self.ordinary_binary_positions.numel()) > 0:
            total = total + Bernoulli(logits=self.binary_logits[:, self.ordinary_binary_positions]).entropy().sum(dim=1)
        event_logits = self._fire_event_logits()
        if event_logits is not None:
            total = total + Categorical(logits=event_logits).entropy()
        for _action_index, logits in self.categorical_logits:
            total = total + Categorical(logits=logits).entropy()
        return total


@dataclass(frozen=True)
class _HybridEventCreditOutput:
    q_hold: th.Tensor
    q_fire_once: th.Tensor
    event_advantage: th.Tensor


class HierarchicalMoEExecutionPolicy(SquashedMultiInputPolicy):
    """
    Shared-backbone execution policy with explicit hierarchical semantic routing.

    First skeleton only:
    - shared feature extractor
    - shared latent/value trunk
    - actor-side family heads + subexpert residual heads
    - routing from the maintained mission observation vector
    """

    def __init__(
        self,
        observation_space,
        action_space,
        lr_schedule,
        *args: Any,
        family_subexpert_counts: tuple[int, ...] | list[int] = DEFAULT_FAMILY_SUBEXPERT_COUNTS,
        hmoe_residual_scale: float = 0.25,
        hmoe_head_lr_scale: float = 0.35,
        hmoe_residual_warmup_fraction: float = 0.15,
        hmoe_residual_start_factor: float = 0.0,
        hybrid_action_spec: Any | None = None,
        hybrid_event_head_lr_scale: float = 0.0,
        hybrid_event_credit_head_lr_scale: float = 0.0,
        **kwargs: Any,
    ):
        self._hmoe_family_subexpert_counts = tuple(int(max(1, v)) for v in family_subexpert_counts)
        self._hmoe_residual_scale = float(max(0.0, hmoe_residual_scale))
        self._hmoe_head_lr_scale = float(max(0.0, hmoe_head_lr_scale))
        self._hmoe_residual_warmup_fraction = float(min(max(0.0, hmoe_residual_warmup_fraction), 1.0))
        self._hmoe_residual_start_factor = float(min(max(0.0, hmoe_residual_start_factor), 1.0))
        self._hybrid_event_head_lr_scale = float(max(0.0, hybrid_event_head_lr_scale))
        self._hybrid_event_credit_head_lr_scale = float(max(0.0, hybrid_event_credit_head_lr_scale))
        self._hmoe_residual_gate = float(self._hmoe_residual_start_factor)
        self._hmoe_initial_lr = float(lr_schedule(1))
        self._hybrid_log_std_init = float(kwargs.get("log_std_init", 0.0))
        self._hybrid_action_spec_config = hybrid_action_spec
        self._hybrid_action_layout: _HybridActionLayout | None = None
        self.hybrid_event_head: nn.Linear | None = None
        self.hybrid_event_credit_head: nn.Linear | None = None
        if hybrid_action_spec is not None:
            kwargs["squash_output"] = False
        super().__init__(observation_space, action_space, lr_schedule, *args, **kwargs)
        if not isinstance(self.action_space, spaces.Box):
            raise TypeError(
                f"HierarchicalMoEExecutionPolicy only supports Box action spaces, got {type(self.action_space)}"
            )
        self._hybrid_action_layout = _normalize_hybrid_action_layout(hybrid_action_spec, self.action_space)
        hmoe_output_dim = int(get_action_dim(self.action_space))
        if self._hybrid_action_layout is not None:
            hmoe_output_dim = int(self._hybrid_action_layout.param_dim)
            self.action_net = nn.Linear(int(self.mlp_extractor.latent_dim_pi), hmoe_output_dim).to(self.device)
            self.log_std = nn.Parameter(
                th.full(
                    (int(self._hybrid_action_layout.continuous_count),),
                    float(self._hybrid_log_std_init),
                    device=self.device,
                )
            )
            self._squash_output = False
            if self._hybrid_event_head_lr_scale > 0.0:
                self.hybrid_event_head = nn.Linear(int(self.mlp_extractor.latent_dim_pi), 2).to(self.device)
                nn.init.zeros_(self.hybrid_event_head.weight)
                nn.init.zeros_(self.hybrid_event_head.bias)
            if self._hybrid_event_credit_head_lr_scale > 0.0:
                self.hybrid_event_credit_head = nn.Linear(int(self.mlp_extractor.latent_dim_pi), 2).to(self.device)
                nn.init.zeros_(self.hybrid_event_credit_head.weight)
                nn.init.zeros_(self.hybrid_event_credit_head.bias)
        self.hmoe_head_bank = _HMoEHeadBank(
            latent_dim=int(self.mlp_extractor.latent_dim_pi),
            action_dim=hmoe_output_dim,
            family_subexpert_counts=self._hmoe_family_subexpert_counts,
        ).to(self.device)
        # SB3 builds the optimizer inside `super().__init__()`. Rebuild it once the HMoE heads
        # exist so the expert parameters are actually trainable.
        self.optimizer = self._build_optimizer()
        self.apply_optimizer_learning_rate(self._hmoe_initial_lr, lr_mult=1.0)
        self._last_hmoe_route_stats: dict[str, float] = {}

    def _get_constructor_parameters(self) -> dict[str, Any]:
        data = super()._get_constructor_parameters()
        data["family_subexpert_counts"] = list(self._hmoe_family_subexpert_counts)
        data["hmoe_residual_scale"] = float(self._hmoe_residual_scale)
        data["hmoe_head_lr_scale"] = float(self._hmoe_head_lr_scale)
        data["hmoe_residual_warmup_fraction"] = float(self._hmoe_residual_warmup_fraction)
        data["hmoe_residual_start_factor"] = float(self._hmoe_residual_start_factor)
        data["hybrid_action_spec"] = self._hybrid_action_spec_config
        data["hybrid_event_head_lr_scale"] = float(self._hybrid_event_head_lr_scale)
        data["hybrid_event_credit_head_lr_scale"] = float(self._hybrid_event_credit_head_lr_scale)
        return data

    def initialize_hmoe_from_shared_action_head(self) -> None:
        """
        Bootstrap routed heads for residual-style startup.

        Why:
        - The first HMoE line is intentionally a residual/specialization extension of the
          shared execution policy, not a from-scratch independent expert bank.
        - The shared action head remains the initial policy mean.
        - Routed heads should start neutral and only learn residual corrections on top of
          the shared mean, otherwise bootstrap would amplify the shared action prior.
        """
        shared_head = getattr(self, "action_net", None)
        if shared_head is None:
            return
        with th.no_grad():
            for family_head in self.hmoe_head_bank.family_heads:
                family_head.weight.zero_()
                if getattr(family_head, "bias", None) is not None:
                    family_head.bias.zero_()
            for family_subheads in self.hmoe_head_bank.subexpert_heads:
                for sub_head in family_subheads:
                    sub_head.weight.zero_()
                    if getattr(sub_head, "bias", None) is not None:
                        sub_head.bias.zero_()
            if self.hybrid_event_head is not None:
                self.hybrid_event_head.weight.zero_()
                if getattr(self.hybrid_event_head, "bias", None) is not None:
                    self.hybrid_event_head.bias.zero_()
            if self.hybrid_event_credit_head is not None:
                self.hybrid_event_credit_head.weight.zero_()
                if getattr(self.hybrid_event_credit_head, "bias", None) is not None:
                    self.hybrid_event_credit_head.bias.zero_()

    def get_hmoe_parameter_stats(self) -> dict[str, float]:
        stats: dict[str, float] = {}

        def _record_group(prefix: str, modules: list[nn.Linear]) -> None:
            if not modules:
                stats[f"{prefix}/count"] = 0.0
                return
            weight_norms: list[float] = []
            bias_norms: list[float] = []
            abs_means: list[float] = []
            nonzero_count = 0
            max_abs = 0.0
            for module in modules:
                weight = module.weight.detach()
                bias = module.bias.detach() if getattr(module, "bias", None) is not None else None
                weight_norms.append(float(weight.norm().item()))
                abs_means.append(float(weight.abs().mean().item()))
                max_abs = max(max_abs, float(weight.abs().max().item()))
                if bias is not None:
                    bias_norms.append(float(bias.norm().item()))
                    max_abs = max(max_abs, float(bias.abs().max().item()))
                if float(weight.abs().sum().item()) > 0.0:
                    nonzero_count += 1
            stats[f"{prefix}/count"] = float(len(modules))
            stats[f"{prefix}/nonzero_frac"] = float(nonzero_count) / float(len(modules))
            stats[f"{prefix}/weight_norm_mean"] = float(sum(weight_norms) / len(weight_norms))
            stats[f"{prefix}/weight_abs_mean"] = float(sum(abs_means) / len(abs_means))
            stats[f"{prefix}/max_abs"] = float(max_abs)
            if bias_norms:
                stats[f"{prefix}/bias_norm_mean"] = float(sum(bias_norms) / len(bias_norms))

        family_modules = [head for head in self.hmoe_head_bank.family_heads]
        sub_modules = [head for family_subheads in self.hmoe_head_bank.subexpert_heads for head in family_subheads]
        _record_group("hmoe_params/family", family_modules)
        _record_group("hmoe_params/sub", sub_modules)
        if self.hybrid_event_head is None:
            stats["a6/event_head_params/enabled"] = 0.0
            stats["a6/event_head_params/lr_scale"] = float(self._hybrid_event_head_lr_scale)
        else:
            stats["a6/event_head_params/enabled"] = 1.0
            stats["a6/event_head_params/lr_scale"] = float(self._hybrid_event_head_lr_scale)
            weight = self.hybrid_event_head.weight.detach()
            bias = self.hybrid_event_head.bias.detach()
            stats["a6/event_head_params/weight_norm"] = float(weight.norm().item())
            stats["a6/event_head_params/bias_norm"] = float(bias.norm().item())
            stats["a6/event_head_params/max_abs"] = float(max(weight.abs().max().item(), bias.abs().max().item()))
        if self.hybrid_event_credit_head is None:
            stats["a7/event_credit_head_params/enabled"] = 0.0
            stats["a7/event_credit_head_params/lr_scale"] = float(self._hybrid_event_credit_head_lr_scale)
        else:
            stats["a7/event_credit_head_params/enabled"] = 1.0
            stats["a7/event_credit_head_params/lr_scale"] = float(self._hybrid_event_credit_head_lr_scale)
            weight = self.hybrid_event_credit_head.weight.detach()
            bias = self.hybrid_event_credit_head.bias.detach()
            stats["a7/event_credit_head_params/weight_norm"] = float(weight.norm().item())
            stats["a7/event_credit_head_params/bias_norm"] = float(bias.norm().item())
            stats["a7/event_credit_head_params/max_abs"] = float(
                max(weight.abs().max().item(), bias.abs().max().item())
            )
        return stats

    def _build_optimizer(self):
        hmoe_params = list(self.hmoe_head_bank.parameters())
        event_params = list(self.hybrid_event_head.parameters()) if self.hybrid_event_head is not None else []
        credit_params = (
            list(self.hybrid_event_credit_head.parameters())
            if self.hybrid_event_credit_head is not None
            else []
        )
        hmoe_param_ids = {id(param) for param in hmoe_params}
        event_param_ids = {id(param) for param in event_params}
        credit_param_ids = {id(param) for param in credit_params}
        routed_param_ids = hmoe_param_ids | event_param_ids | credit_param_ids
        shared_params = [param for param in self.parameters() if id(param) not in routed_param_ids]
        param_groups: list[dict[str, Any]] = [
            {
                "params": shared_params,
                "lr_scale": 1.0,
                "name": "shared",
            }
        ]
        if event_params:
            param_groups.append(
                {
                    "params": event_params,
                    "lr_scale": float(self._hybrid_event_head_lr_scale),
                    "name": "hybrid_event_head",
                }
            )
        if credit_params:
            param_groups.append(
                {
                    "params": credit_params,
                    "lr_scale": float(self._hybrid_event_credit_head_lr_scale),
                    "name": "hybrid_event_credit_head",
                }
            )
        if hmoe_params:
            param_groups.append(
                {
                    "params": hmoe_params,
                    "lr_scale": float(self._hmoe_head_lr_scale),
                    "name": "hmoe",
                }
            )
        return self.optimizer_class(
            param_groups,
            lr=self._hmoe_initial_lr,
            **self.optimizer_kwargs,
        )

    def apply_optimizer_learning_rate(self, base_lr: float, *, lr_mult: float = 1.0) -> None:
        if self.optimizer is None:
            return
        for group in self.optimizer.param_groups:
            scale = float(max(0.0, group.get("lr_scale", 1.0)))
            group["lr"] = float(base_lr) * float(lr_mult) * scale

    def set_hmoe_training_progress(self, progress_remaining: float) -> None:
        progress = float(min(max(progress_remaining, 0.0), 1.0))
        warmup_fraction = float(self._hmoe_residual_warmup_fraction)
        if warmup_fraction <= 0.0:
            self._hmoe_residual_gate = 1.0
            return
        completed = 1.0 - progress
        ramp = min(max(completed / warmup_fraction, 0.0), 1.0)
        start = float(self._hmoe_residual_start_factor)
        self._hmoe_residual_gate = start + (1.0 - start) * ramp

    def _route_indices(self, obs: Any, latent_pi: th.Tensor) -> tuple[th.Tensor, th.Tensor]:
        mission = obs.get("mission") if isinstance(obs, dict) else None
        instruments = obs.get("instruments") if isinstance(obs, dict) else None
        route = route_from_mission_observation(
            mission,
            instruments=instruments,
            batch_size=int(latent_pi.shape[0]),
            device=latent_pi.device,
        )
        return route.family_index, route.subexpert_index

    def _update_route_stats(self, family_index: th.Tensor, subexpert_index: th.Tensor) -> None:
        batch = int(family_index.shape[0])
        if batch <= 0:
            self._last_hmoe_route_stats = {}
            return
        stats: dict[str, float] = {"hmoe/batch_size": float(batch)}

        family_log_names = {
            "takeoff_ground": "tkof",
            "departure_nav": "nav",
            "formation_cooperative": "form",
            "recovery_landing": "land",
            "combat_weapons": "combat",
        }
        subexpert_log_names = {
            "single_ship": "single",
            "interval": "interval",
            "wing": "wing",
            "vector": "vector",
            "route": "route",
            "generic": "generic",
            "element_lead": "lead",
            "wingman": "wingman",
            "weapons_hold": "hold",
            "authorized_first_shot": "first_shot",
            "post_launch_assess": "assess",
        }

        family_cpu = family_index.detach().to(device="cpu", dtype=th.long)
        subexpert_cpu = subexpert_index.detach().to(device="cpu", dtype=th.long)
        unique_families = th.unique(family_cpu, sorted=True)
        for family_id_tensor in unique_families:
            family_id = int(family_id_tensor.item())
            family_label = family_name(family_id)
            family_log = family_log_names.get(family_label, family_label)
            family_mask = family_cpu == family_id
            family_count = int(family_mask.sum().item())
            stats[f"hmoe/fam/{family_log}"] = float(family_count) / float(batch)
            family_sub = subexpert_cpu[family_mask]
            unique_sub = th.unique(family_sub, sorted=True)
            for sub_id_tensor in unique_sub:
                sub_id = int(sub_id_tensor.item())
                sub_label = subexpert_name(family_id, sub_id)
                sub_log = subexpert_log_names.get(sub_label, sub_label)
                sub_count = int((family_sub == sub_id).sum().item())
                stats[f"hmoe/sub/{family_log}/{sub_log}"] = float(sub_count) / float(batch)
        self._last_hmoe_route_stats = stats

    def get_hmoe_route_stats(self) -> dict[str, float]:
        return dict(self._last_hmoe_route_stats)

    def _apply_hybrid_event_head(self, mean_actions: th.Tensor, latent_pi: th.Tensor) -> th.Tensor:
        layout = self._hybrid_action_layout
        event_head = self.hybrid_event_head
        if layout is None or event_head is None:
            self._last_hmoe_route_stats["a6/event_head_enabled"] = 0.0
            self._last_hmoe_route_stats["a6/event_head_lr_scale"] = float(self._hybrid_event_head_lr_scale)
            return mean_actions
        hold_index = layout.event_hold_param_index
        fire_index = layout.event_fire_param_index
        if hold_index is None or fire_index is None:
            self._last_hmoe_route_stats["a6/event_head_enabled"] = 0.0
            self._last_hmoe_route_stats["a6/event_head_lr_scale"] = float(self._hybrid_event_head_lr_scale)
            return mean_actions

        event_delta = event_head(latent_pi)
        adjusted = mean_actions.clone()
        adjusted[:, int(hold_index)] = adjusted[:, int(hold_index)] + event_delta[:, 0]
        adjusted[:, int(fire_index)] = adjusted[:, int(fire_index)] + event_delta[:, 1]

        event_delta_detached = event_delta.detach()
        self._last_hmoe_route_stats["a6/event_head_enabled"] = 1.0
        self._last_hmoe_route_stats["a6/event_head_lr_scale"] = float(self._hybrid_event_head_lr_scale)
        self._last_hmoe_route_stats["a6/event_head_delta_abs_mean"] = float(
            event_delta_detached.abs().mean().item()
        )
        self._last_hmoe_route_stats["a6/event_head_delta_hold_mean"] = float(
            event_delta_detached[:, 0].mean().item()
        )
        self._last_hmoe_route_stats["a6/event_head_delta_fire_mean"] = float(
            event_delta_detached[:, 1].mean().item()
        )
        return adjusted

    def _compute_hybrid_event_credit_values(self, latent_pi: th.Tensor) -> th.Tensor | None:
        layout = self._hybrid_action_layout
        credit_head = self.hybrid_event_credit_head
        if layout is None or credit_head is None or layout.event_action_index is None:
            self._last_hmoe_route_stats["a7/event_credit_head_enabled"] = 0.0
            self._last_hmoe_route_stats["a7/event_credit_head_lr_scale"] = float(
                self._hybrid_event_credit_head_lr_scale
            )
            return None

        values = credit_head(latent_pi)
        values_detached = values.detach()
        advantage = values_detached[:, 1] - values_detached[:, 0]
        self._last_hmoe_route_stats["a7/event_credit_head_enabled"] = 1.0
        self._last_hmoe_route_stats["a7/event_credit_head_lr_scale"] = float(
            self._hybrid_event_credit_head_lr_scale
        )
        self._last_hmoe_route_stats["a7/event_credit_q_hold_mean"] = float(
            values_detached[:, 0].mean().item()
        )
        self._last_hmoe_route_stats["a7/event_credit_q_fire_mean"] = float(
            values_detached[:, 1].mean().item()
        )
        self._last_hmoe_route_stats["a7/event_credit_advantage_mean"] = float(advantage.mean().item())
        self._last_hmoe_route_stats["a7/event_credit_advantage_abs_mean"] = float(advantage.abs().mean().item())
        return values

    def get_hybrid_event_credit(self, obs) -> _HybridEventCreditOutput | None:
        distribution = self.get_distribution(obs)
        values_getter = getattr(distribution, "fire_event_q_values", None)
        if not callable(values_getter):
            return None
        values = values_getter()
        if values is None:
            return None
        return _HybridEventCreditOutput(
            q_hold=values[:, 0],
            q_fire_once=values[:, 1],
            event_advantage=values[:, 1] - values[:, 0],
        )

    def get_distribution(self, obs):
        features = super().extract_features(obs, self.pi_features_extractor)
        latent_pi = self.mlp_extractor.forward_actor(features)
        return self._get_action_dist_from_latent(latent_pi, obs=obs)

    def _get_action_dist_from_latent(self, latent_pi: th.Tensor, obs: Any | None = None):
        if obs is None:
            batch_size = int(latent_pi.shape[0])
            family_index = th.full(
                (batch_size,),
                FAMILY_DEPARTURE_NAV,
                dtype=th.long,
                device=latent_pi.device,
            )
            subexpert_index = th.zeros((batch_size,), dtype=th.long, device=latent_pi.device)
        else:
            family_index, subexpert_index = self._route_indices(obs, latent_pi)
        self._update_route_stats(family_index, subexpert_index)

        shared_mean_actions = self.action_net(latent_pi)
        expert_residual = self.hmoe_head_bank(latent_pi, family_index, subexpert_index)
        effective_scale = float(self._hmoe_residual_scale) * float(self._hmoe_residual_gate)
        mean_actions = shared_mean_actions + effective_scale * expert_residual
        self._last_hmoe_route_stats["hmoe/resid_abs_mean"] = float(expert_residual.detach().abs().mean().item())
        self._last_hmoe_route_stats["hmoe/resid_gate"] = float(self._hmoe_residual_gate)
        self._last_hmoe_route_stats["hmoe/resid_effective_scale"] = float(effective_scale)

        if self._hybrid_action_layout is not None:
            mean_actions = self._apply_hybrid_event_head(mean_actions, latent_pi)
            fire_event_q_values = self._compute_hybrid_event_credit_values(latent_pi)
            fire_event_mask = _hybrid_fire_event_mask_from_obs(
                obs,
                batch_size=int(mean_actions.shape[0]),
                device=mean_actions.device,
            )
            return _HybridActionDistribution(
                layout=self._hybrid_action_layout,
                params=mean_actions,
                log_std=self.log_std,
                action_low=self.action_space.low,
                action_high=self.action_space.high,
                fire_event_mask=fire_event_mask,
                fire_event_q_values=fire_event_q_values,
            )
        if isinstance(self.action_dist, SquashedDiagGaussianDistribution):
            return self.action_dist.proba_distribution(mean_actions, self.log_std)
        return super()._get_action_dist_from_latent(latent_pi)

    def forward(self, obs, deterministic: bool = False):
        features = self.extract_features(obs)
        if self.share_features_extractor:
            latent_pi, latent_vf = self.mlp_extractor(features)
        else:
            pi_features, vf_features = features
            latent_pi = self.mlp_extractor.forward_actor(pi_features)
            latent_vf = self.mlp_extractor.forward_critic(vf_features)
        values = self.value_net(latent_vf)
        distribution = self._get_action_dist_from_latent(latent_pi, obs=obs)
        actions = distribution.get_actions(deterministic=deterministic)
        log_prob = distribution.log_prob(actions)
        actions = actions.reshape((-1, *self.action_space.shape))
        return actions, values, log_prob

    def evaluate_actions(self, obs, actions: th.Tensor):
        features = self.extract_features(obs)
        if self.share_features_extractor:
            latent_pi, latent_vf = self.mlp_extractor(features)
        else:
            pi_features, vf_features = features
            latent_pi = self.mlp_extractor.forward_actor(pi_features)
            latent_vf = self.mlp_extractor.forward_critic(vf_features)
        distribution = self._get_action_dist_from_latent(latent_pi, obs=obs)
        log_prob = distribution.log_prob(actions)
        values = self.value_net(latent_vf)
        entropy = distribution.entropy()
        return values, log_prob, entropy
