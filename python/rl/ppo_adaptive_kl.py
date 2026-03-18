from __future__ import annotations

from typing import Optional

import numpy as np
import torch as th
from gymnasium import spaces
from torch.nn import functional as F

from stable_baselines3 import PPO
from stable_baselines3.common.utils import explained_variance


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
        super().__init__(*args, **kwargs)

    def _apply_lr_multiplier(self) -> None:
        if self.policy is None:
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

    def train(self) -> None:  # noqa: C901 - keep SB3-like structure for clarity
        # Switch to train mode (affects batch norm / dropout)
        self.policy.set_training_mode(True)

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

        explained_var = explained_variance(self.rollout_buffer.values.flatten(), self.rollout_buffer.returns.flatten())

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

        self.logger.record("train/n_updates", int(self._n_updates), exclude="tensorboard")
        self.logger.record("train/clip_range", float(clip_range))
        if clip_range_vf is not None:
            self.logger.record("train/clip_range_vf", float(clip_range_vf))

        # Adaptive KL control logs
        self.logger.record("train/kl_penalty_coef", float(self.kl_penalty_coef))
        self.logger.record("train/kl_lr_mult", float(self._lr_mult))
        self.logger.record("train/kl_clip_mult", float(self._clip_mult))
        self.logger.record("train/kl_low_streak", int(self._low_kl_streak))
