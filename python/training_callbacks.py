from __future__ import annotations

from typing import Any

import numpy as np
from stable_baselines3.common.callbacks import BaseCallback


def _safe_mean(values):
    if values is None:
        return None
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        return None
    return float(arr.mean())


class CMODiagnosticsCallback(BaseCallback):
    """
    Lightweight TensorBoard diagnostics for debugging "no learning / unstable" training runs.

    Logs a few key scalars from observations/actions/infos at a fixed timestep interval.
    """

    def __init__(self, log_every_timesteps: int = 50_000, verbose: int = 0):
        super().__init__(verbose=verbose)
        self.log_every_timesteps = int(log_every_timesteps)
        self._next_log_t = int(log_every_timesteps)

    def _on_step(self) -> bool:
        if self.log_every_timesteps <= 0:
            return True
        if self.num_timesteps < self._next_log_t:
            return True
        self._next_log_t = int(self.num_timesteps) + int(self.log_every_timesteps)

        obs = self.locals.get("new_obs")
        actions = self.locals.get("actions")
        rewards = self.locals.get("rewards")
        infos = self.locals.get("infos")

        if rewards is not None:
            r_mean = _safe_mean(rewards)
            if r_mean is not None:
                self.logger.record("diag/reward_mean", r_mean)

        if isinstance(obs, dict) and "instruments" in obs:
            inst = np.asarray(obs["instruments"], dtype=np.float32)
            if inst.ndim == 2 and inst.shape[1] >= 10:
                self.logger.record("diag/ias_mean", float(inst[:, 0].mean()))
                self.logger.record("diag/alt_baro_mean", float(inst[:, 2].mean()))
                self.logger.record("diag/aoa_mean", float(inst[:, 5].mean()))
                self.logger.record("diag/pitch_mean", float(inst[:, 7].mean()))
                self.logger.record("diag/roll_mean", float(inst[:, 8].mean()))

                if inst.shape[1] >= 42:
                    ils = inst[:, -4:]
                    self.logger.record("diag/ils_valid_frac", float((ils[:, 0] > 0.5).mean()))
                    self.logger.record("diag/ils_loc_abs_mean", float(np.abs(ils[:, 1]).mean()))

        if actions is not None:
            a = np.asarray(actions, dtype=np.float32)
            if a.ndim == 2 and a.shape[1] >= 4:
                self.logger.record("diag/action_pitch_mean", float(a[:, 0].mean()))
                self.logger.record("diag/action_roll_mean", float(a[:, 1].mean()))
                self.logger.record("diag/action_rudder_mean", float(a[:, 2].mean()))
                self.logger.record("diag/action_throttle_mean", float(a[:, 3].mean()))
            if a.ndim == 2 and a.shape[1] >= 9:
                self.logger.record("diag/action_brake_any_frac", float((np.maximum(a[:, 7], a[:, 8]) > 0.5).mean()))

        if isinstance(infos, (list, tuple)) and infos:
            on_runway = [info.get("on_runway") for info in infos if isinstance(info, dict) and "on_runway" in info]
            if on_runway:
                self.logger.record("diag/on_runway_frac", float(np.asarray(on_runway, dtype=np.float32).mean()))

            gear_collapsed = [
                info.get("gear_collapsed") for info in infos if isinstance(info, dict) and "gear_collapsed" in info
            ]
            if gear_collapsed:
                self.logger.record("diag/gear_collapsed_frac", float(np.asarray(gear_collapsed, dtype=np.float32).mean()))

            gear_stress = [info.get("gear_stress") for info in infos if isinstance(info, dict) and "gear_stress" in info]
            if gear_stress:
                self.logger.record("diag/gear_stress_mean", float(np.asarray(gear_stress, dtype=np.float32).mean()))

        return True

