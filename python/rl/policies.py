from __future__ import annotations

from typing import Any, Optional

from gymnasium import spaces

from stable_baselines3.common.distributions import SquashedDiagGaussianDistribution
from stable_baselines3.common.preprocessing import get_action_dim
from stable_baselines3.common.policies import MultiInputActorCriticPolicy


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

