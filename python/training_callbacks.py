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
        actions = self.locals.get("clipped_actions", self.locals.get("actions"))
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
                brake_raw = np.maximum(a[:, 7], a[:, 8])
                brake_amt = np.clip((brake_raw - 0.5) * 2.0, 0.0, 1.0)
                self.logger.record("diag/action_brake_amt_mean", float(brake_amt.mean()))

        if isinstance(infos, (list, tuple)) and infos:
            on_runway = [info.get("on_runway") for info in infos if isinstance(info, dict) and "on_runway" in info]
            if on_runway:
                self.logger.record("diag/on_runway_frac", float(np.asarray(on_runway, dtype=np.float32).mean()))

            on_runway_geom = [
                info.get("on_runway_geom") for info in infos if isinstance(info, dict) and "on_runway_geom" in info
            ]
            if on_runway_geom:
                self.logger.record(
                    "diag/on_runway_geom_frac", float(np.asarray(on_runway_geom, dtype=np.float32).mean())
                )

            runway_cross = [
                info.get("runway_cross_m") for info in infos if isinstance(info, dict) and "runway_cross_m" in info
            ]
            if runway_cross:
                rc = np.asarray(runway_cross, dtype=np.float32)
                self.logger.record("diag/runway_cross_abs_mean_m", float(np.abs(rc).mean()))
                abs_rc = np.abs(rc)
                # Robust tail metrics help catch "edge-hugging" even when mean looks OK.
                try:
                    self.logger.record("diag/runway_cross_abs_p95_m", float(np.percentile(abs_rc, 95.0)))
                except Exception:
                    pass
                self.logger.record("diag/runway_cross_abs_max_m", float(abs_rc.max(initial=0.0)))

            gear_collapsed = [
                info.get("gear_collapsed") for info in infos if isinstance(info, dict) and "gear_collapsed" in info
            ]
            if gear_collapsed:
                self.logger.record("diag/gear_collapsed_frac", float(np.asarray(gear_collapsed, dtype=np.float32).mean()))

            gear_stress = [info.get("gear_stress") for info in infos if isinstance(info, dict) and "gear_stress" in info]
            if gear_stress:
                self.logger.record("diag/gear_stress_mean", float(np.asarray(gear_stress, dtype=np.float32).mean()))

        return True


class ScenarioCurriculumCallback(BaseCallback):
    """
    Time-based curriculum for scenario randomization.

    Applies `ScenarioLoader.set_randomization_overrides()` (via `env_method`) according to staged schedule:
      stages = [{"until_timesteps": 200000, "randomization": {...}}, {..., "until_timesteps": null, ...}]
    """

    def __init__(self, stages: list[dict[str, Any]], check_freq: int = 10_000, verbose: int = 0):
        super().__init__(verbose=verbose)
        if not isinstance(stages, list) or not stages:
            raise ValueError("ScenarioCurriculumCallback requires a non-empty `stages` list")
        self.stages = stages
        self.check_freq = int(check_freq)
        self._next_check = 0
        self._active_stage_idx: int | None = None

    def _select_stage(self, t: int) -> int:
        for idx, st in enumerate(self.stages):
            until = st.get("until_timesteps", None)
            if until is None:
                return idx
            if t < int(until):
                return idx
        return len(self.stages) - 1

    def _apply_stage(self, idx: int) -> None:
        st = self.stages[idx]
        overrides = st.get("randomization_overrides", st.get("randomization", {}))
        if overrides is None:
            overrides = {}
        if not isinstance(overrides, dict):
            raise TypeError(f"curriculum stage randomization overrides must be a dict, got {type(overrides)}")

        # Broadcast to all parallel envs (works for DummyVecEnv/SubprocVecEnv).
        try:
            self.training_env.env_method("set_randomization_overrides", overrides)  # type: ignore[union-attr]
        except Exception:
            return

        self._active_stage_idx = int(idx)
        self.logger.record("curriculum/stage", int(idx))

    def _on_training_start(self) -> None:
        self._next_check = 0
        self._active_stage_idx = None
        self._apply_stage(self._select_stage(int(self.num_timesteps)))

    def _on_step(self) -> bool:
        if self.check_freq <= 0:
            return True
        if self.num_timesteps < self._next_check:
            return True
        self._next_check = int(self.num_timesteps) + int(self.check_freq)

        idx = self._select_stage(int(self.num_timesteps))
        if self._active_stage_idx != idx:
            self._apply_stage(idx)
        return True
