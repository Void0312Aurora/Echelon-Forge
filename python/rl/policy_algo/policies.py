from __future__ import annotations

from typing import Any, Optional

import torch as th
import torch.nn as nn
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
        **kwargs: Any,
    ):
        self._hmoe_family_subexpert_counts = tuple(int(max(1, v)) for v in family_subexpert_counts)
        self._hmoe_residual_scale = float(max(0.0, hmoe_residual_scale))
        self._hmoe_head_lr_scale = float(max(0.0, hmoe_head_lr_scale))
        self._hmoe_residual_warmup_fraction = float(min(max(0.0, hmoe_residual_warmup_fraction), 1.0))
        self._hmoe_residual_start_factor = float(min(max(0.0, hmoe_residual_start_factor), 1.0))
        self._hmoe_residual_gate = 1.0
        self._hmoe_initial_lr = float(lr_schedule(1))
        super().__init__(observation_space, action_space, lr_schedule, *args, **kwargs)
        if not isinstance(self.action_space, spaces.Box):
            raise TypeError(
                f"HierarchicalMoEExecutionPolicy only supports Box action spaces, got {type(self.action_space)}"
            )
        self.hmoe_head_bank = _HMoEHeadBank(
            latent_dim=int(self.mlp_extractor.latent_dim_pi),
            action_dim=int(get_action_dim(self.action_space)),
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
        return data

    def initialize_hmoe_from_shared_action_head(self) -> None:
        """
        Bootstrap routed heads from the current shared action head.

        Why:
        - The first HMoE line is intentionally a residual/specialization extension of the
          shared execution policy, not a from-scratch independent expert bank.
        - Copying the shared head into routed heads gives each expert a meaningful initial
          policy prior while still allowing subsequent specialization.
        """
        shared_head = getattr(self, "action_net", None)
        if shared_head is None:
            return
        shared_weight = getattr(shared_head, "weight", None)
        shared_bias = getattr(shared_head, "bias", None)
        if shared_weight is None:
            return
        with th.no_grad():
            for family_head in self.hmoe_head_bank.family_heads:
                family_head.weight.copy_(shared_weight)
                if shared_bias is not None and getattr(family_head, "bias", None) is not None:
                    family_head.bias.copy_(shared_bias)
            for family_subheads in self.hmoe_head_bank.subexpert_heads:
                for sub_head in family_subheads:
                    sub_head.weight.zero_()
                    if getattr(sub_head, "bias", None) is not None:
                        sub_head.bias.zero_()

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
        return stats

    def _build_optimizer(self):
        hmoe_params = list(self.hmoe_head_bank.parameters())
        hmoe_param_ids = {id(param) for param in hmoe_params}
        shared_params = [param for param in self.parameters() if id(param) not in hmoe_param_ids]
        param_groups: list[dict[str, Any]] = [
            {
                "params": shared_params,
                "lr_scale": 1.0,
                "name": "shared",
            }
        ]
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
