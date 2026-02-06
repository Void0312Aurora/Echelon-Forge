from __future__ import annotations

from typing import Iterable, Optional

import numpy as np

import gymnasium as gym


class MultiTimescaleActionWrapper(gym.Wrapper):
    """
    Hold "switch-like" action dimensions for multiple sim steps.

    Motivation:
    - Reduces effective action bandwidth for low-frequency cockpit switches
      (gear, flaps, brakes, master arm, weapon trigger), which is closer to reality
      and reduces the RL search space.
    - Optionally adds a small action-rate penalty to discourage jitter.
    """

    def __init__(
        self,
        env: gym.Env,
        hold_steps: int = 4,
        low_freq_indices: Optional[Iterable[int]] = None,
        snap_binary_indices: Optional[Iterable[int]] = None,
        action_rate_penalty_coef: float = 0.0,
    ):
        super().__init__(env)
        self.hold_steps = int(hold_steps)
        self.low_freq_indices = tuple(sorted(set(int(i) for i in (low_freq_indices or ()))))
        self.snap_binary_indices = tuple(sorted(set(int(i) for i in (snap_binary_indices or ()))))
        self.action_rate_penalty_coef = float(action_rate_penalty_coef)

        self._t = 0
        self._held_action: Optional[np.ndarray] = None

    def reset(self, **kwargs):
        self._t = 0
        self._held_action = None
        return self.env.reset(**kwargs)

    def step(self, action):
        a = np.asarray(action, dtype=np.float32).reshape(-1).copy()

        if self._held_action is None:
            self._held_action = a.copy()

        # Hold low-frequency dimensions between updates.
        if self.hold_steps > 1 and (self._t % self.hold_steps) != 0 and self.low_freq_indices:
            a[list(self.low_freq_indices)] = self._held_action[list(self.low_freq_indices)]

        # Snap selected dims to {0,1}.
        for idx in self.snap_binary_indices:
            if 0 <= idx < a.size:
                a[idx] = 1.0 if a[idx] > 0.5 else 0.0

        rate_penalty = 0.0
        if self.action_rate_penalty_coef > 0.0 and self._held_action is not None:
            rate_penalty = float(self.action_rate_penalty_coef) * float(np.mean(np.abs(a - self._held_action)))

        obs, reward, terminated, truncated, info = self.env.step(a)

        if rate_penalty != 0.0:
            reward = float(reward) - rate_penalty
            if isinstance(info, dict):
                info = dict(info)
                info["action_rate_penalty"] = float(rate_penalty)

        self._held_action = a.copy()
        self._t += 1
        return obs, reward, terminated, truncated, info

