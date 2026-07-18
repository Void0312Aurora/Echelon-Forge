from __future__ import annotations

import numpy as np

from python.angles import wrap_signed_deg


def wrap_deg(x: float) -> float:
    # Deliberate variant of python.angles.wrap_signed_deg: values within 1e-9
    # of zero (including negative zero) are snapped to exactly 0.0.
    y = wrap_signed_deg(x)
    return 0.0 if abs(y) < 1.0e-9 else y


class BaseScriptedController:
    def __init__(self, *, action_dim: int, dt: float = 0.05):
        self.action_dim = int(action_dim)
        self.dt = float(dt)

    @staticmethod
    def obs_array(obs: dict, key: str) -> np.ndarray:
        return np.asarray(obs.get(key, []), dtype=np.float32).reshape(-1)

    @classmethod
    def instrument_and_mission(cls, obs: dict) -> tuple[np.ndarray, np.ndarray]:
        return cls.obs_array(obs, "instruments"), cls.obs_array(obs, "mission")

    def action_zeros(self) -> np.ndarray:
        return np.zeros((int(self.action_dim),), dtype=np.float32)

    def effective_dt(self, default: float = 0.05) -> float:
        return self.dt if self.dt > 1.0e-6 else float(default)
