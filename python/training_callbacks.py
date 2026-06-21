from __future__ import annotations

from typing import Any
import os

import numpy as np
from stable_baselines3.common.callbacks import BaseCallback

from python.training.diagnostics import (
    TrainingEventDiagnosticsWindow,
    action_array_for_diagnostics,
    record_event_info_diagnostics,
    record_first_event_info_diagnostics,
    record_action_diagnostics,
    record_basic_step_diagnostics,
    record_hmoe_policy_diagnostics,
    record_leader_diagnostics,
    record_policy_distribution_diagnostics,
    record_reward_term_diagnostics,
    record_runway_gear_diagnostics,
)


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

    TERMINAL_REWARD_KEYS = (
        "total",
        "crash_penalty",
        "failfast_penalty",
        "off_runway_terminate_penalty",
        "gear_collapse_penalty",
        "overload_penalty",
        "g_deviation_penalty",
        "waypoint_distance",
        "waypoint_cross_track",
        "waypoint_progress",
        "waypoint_success_bonus",
        "objective_bonus",
        "combat_win_bonus",
        "combat_loss_penalty",
        "combat_draw_reward",
    )

    LEADER_REWARD_KEYS = (
        "execution_reward",
        "command_change_penalty",
        "invalid_phase_penalty",
        "premature_approach_penalty",
        "baseline_deviation_penalty",
        "mode_change_penalty",
    )

    STEP_REWARD_KEYS = (
        "total",
        "survival",
        "crash_penalty",
        "stall_penalty",
        "overload_penalty",
        "failfast_penalty",
        "off_runway_penalty",
        "off_runway_terminate_penalty",
        "gear_collapse_penalty",
        "altitude_progress",
        "speed_progress",
        "speed_regress",
        "heading_error_penalty",
        "heading_hold_bonus",
        "altitude_error_penalty",
        "speed_error_penalty",
        "roll_abs_penalty",
        "pitch_abs_penalty",
        "yaw_rate_abs_penalty",
        "beta_abs_penalty",
        "g_deviation_penalty",
        "alignment_reward",
        "waypoint_progress",
        "waypoint_distance",
        "waypoint_reached_bonus",
        "waypoint_success_bonus",
        "objective_bonus",
        "combat_win_bonus",
        "combat_loss_penalty",
        "combat_draw_reward",
        "untracked",
    )

    def __init__(self, log_every_timesteps: int = 50_000, preterm_window_steps: int = 32, verbose: int = 0):
        super().__init__(verbose=verbose)
        self.log_every_timesteps = int(log_every_timesteps)
        self.preterm_window_steps = max(4, int(preterm_window_steps))
        self._next_log_t = int(log_every_timesteps)
        self._event_diagnostics = TrainingEventDiagnosticsWindow(
            terminal_reward_keys=self.TERMINAL_REWARD_KEYS,
            preterm_window_steps=self.preterm_window_steps,
        )
        self._hmoe_param_stats_next_log_t = int(log_every_timesteps)

    def _on_training_start(self) -> None:
        n_envs = int(getattr(self.training_env, "num_envs", 1))
        self._event_diagnostics.reset_for_training(n_envs)
        self._next_log_t = int(self.log_every_timesteps)
        self._hmoe_param_stats_next_log_t = int(self.log_every_timesteps)

    @property
    def _histories(self):
        return self._event_diagnostics.histories

    @_histories.setter
    def _histories(self, value) -> None:
        self._event_diagnostics.histories = value

    def _record_action_diagnostics(self, actions: Any) -> None:
        record_action_diagnostics(logger=self.logger, actions=actions)

    def _record_policy_distribution_diagnostics(self, obs: Any) -> None:
        record_policy_distribution_diagnostics(
            model=getattr(self, "model", None),
            logger=self.logger,
            obs=obs,
        )

    def _record_hmoe_policy_diagnostics(self) -> None:
        self._hmoe_param_stats_next_log_t = record_hmoe_policy_diagnostics(
            model=getattr(self, "model", None),
            logger=self.logger,
            num_timesteps=int(self.num_timesteps),
            next_param_stats_t=int(self._hmoe_param_stats_next_log_t),
            log_every_timesteps=int(self.log_every_timesteps),
        )

    def _record_first_event_info_diagnostics(self, infos: Any) -> None:
        record_first_event_info_diagnostics(
            model=getattr(self, "model", None),
            logger=self.logger,
            infos=infos,
        )

    def _record_event_info_diagnostics(self, infos: Any) -> None:
        record_event_info_diagnostics(logger=self.logger, infos=infos)

    def _record_event_diagnostics(self) -> None:
        self._event_diagnostics.record_and_reset(logger=self.logger)

    def _record_leader_diagnostics(self, obs, infos: list[dict]) -> None:
        record_leader_diagnostics(
            logger=self.logger,
            obs=obs,
            infos=infos,
            reward_keys=self.LEADER_REWARD_KEYS,
        )

    def _record_step_reward_diagnostics(self, infos: list[dict]) -> None:
        record_reward_term_diagnostics(
            logger=self.logger,
            infos=infos,
            reward_keys=self.STEP_REWARD_KEYS,
        )

    def _record_runway_gear_diagnostics(self, infos: Any) -> None:
        record_runway_gear_diagnostics(logger=self.logger, infos=infos)

    def _on_step(self) -> bool:
        obs = self.locals.get("new_obs")
        actions = self.locals.get("clipped_actions", self.locals.get("actions"))
        rewards = self.locals.get("rewards")
        infos = self.locals.get("infos")
        dones = self.locals.get("dones")

        self._event_diagnostics.observe_step(
            obs=obs,
            actions=actions,
            rewards=rewards,
            infos=infos,
            dones=dones,
        )

        if self.log_every_timesteps <= 0:
            return True
        if self.num_timesteps < self._next_log_t:
            return True
        self._next_log_t = int(self.num_timesteps) + int(self.log_every_timesteps)

        record_basic_step_diagnostics(logger=self.logger, obs=obs, rewards=rewards)
        actions_for_log = action_array_for_diagnostics(actions=actions, infos=infos)
        self._record_action_diagnostics(actions_for_log)

        if isinstance(infos, (list, tuple)) and infos:
            self._record_event_info_diagnostics(infos)
            self._record_first_event_info_diagnostics(infos)
            self._record_step_reward_diagnostics(list(infos))
            self._record_runway_gear_diagnostics(infos)

            self._record_leader_diagnostics(obs, list(infos))

        self._record_policy_distribution_diagnostics(obs)
        self._record_hmoe_policy_diagnostics()
        self._record_event_diagnostics()
        return True


class ScenarioCurriculumCallback(BaseCallback):
    """
    Time-based curriculum for scenario randomization.

    Applies `ScenarioLoader.set_randomization_overrides()` (via `env_method`) according to staged schedule:
      stages = [{"until_timesteps": 200000, "randomization": {...}, "leader_env_overrides": {...}}, {..., "until_timesteps": null, ...}]
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
        except Exception as e:
            if self.verbose > 0:
                print(f"[WARN] curriculum stage {idx} apply failed: {e}")

        leader_overrides = st.get("leader_env_overrides", {})
        if leader_overrides is None:
            leader_overrides = {}
        if not isinstance(leader_overrides, dict):
            raise TypeError(
                f"curriculum stage leader_env_overrides must be a dict, got {type(leader_overrides)}"
            )
        if leader_overrides:
            try:
                self.training_env.env_method("set_leader_overrides", leader_overrides)  # type: ignore[union-attr]
            except Exception as e:
                if self.verbose > 0:
                    print(f"[WARN] curriculum leader stage {idx} apply failed: {e}")

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


class RewardPlateauEarlyStopCallback(BaseCallback):
    """
    Stop training when episode-reward EMA no longer improves.

    This remains lightweight and does not require a separate eval env, but it should
    track the same scale as SB3's `rollout/ep_rew_mean` rather than instantaneous
    step rewards.
    """

    def __init__(
        self,
        min_timesteps: int = 200_000,
        check_every_timesteps: int = 20_000,
        patience_checks: int = 6,
        min_improvement: float = 0.5,
        ema_alpha: float = 0.05,
        best_model_path: str | None = None,
        verbose: int = 0,
    ):
        super().__init__(verbose=verbose)
        self.min_timesteps = int(min_timesteps)
        self.check_every_timesteps = int(check_every_timesteps)
        self.patience_checks = int(patience_checks)
        self.min_improvement = float(min_improvement)
        self.ema_alpha = float(ema_alpha)
        self.best_model_path = best_model_path

        self._next_check = 0
        self._ema_reward = None
        self._best_ema = None
        self._stale_checks = 0
        self._best_saved = False

    def _save_best_model(self) -> None:
        if not self.best_model_path:
            return
        try:
            d = os.path.dirname(self.best_model_path)
            if d:
                os.makedirs(d, exist_ok=True)
            self.model.save(self.best_model_path)
            self._best_saved = True
        except Exception:
            pass

    def _on_training_start(self) -> None:
        self._next_check = int(self.check_every_timesteps)
        self._ema_reward = None
        self._best_ema = None
        self._stale_checks = 0
        self._best_saved = False

    def _current_reward_metric(self):
        ep_buf = getattr(self.model, "ep_info_buffer", None)
        if ep_buf:
            vals = []
            for ep in ep_buf:
                if not isinstance(ep, dict):
                    continue
                try:
                    vals.append(float(ep.get("r")))
                except Exception:
                    continue
            if vals:
                return float(np.mean(np.asarray(vals, dtype=np.float32)))

        rewards = self.locals.get("rewards")
        if rewards is not None:
            r_mean = _safe_mean(rewards)
            if r_mean is not None:
                return float(r_mean)
        return None

    def _on_step(self) -> bool:
        if self.num_timesteps < self._next_check:
            return True
        self._next_check = int(self.num_timesteps) + int(self.check_every_timesteps)

        metric = self._current_reward_metric()
        if metric is None:
            return True
        self.logger.record("early_stop/reward_metric", float(metric))

        if self._ema_reward is None:
            self._ema_reward = float(metric)
        else:
            a = self.ema_alpha
            self._ema_reward = float((1.0 - a) * self._ema_reward + a * float(metric))

        self.logger.record("early_stop/ema_reward", float(self._ema_reward))

        if self.num_timesteps < self.min_timesteps:
            if self._best_ema is None or self._ema_reward > self._best_ema:
                self._best_ema = float(self._ema_reward)
                self._save_best_model()
            return True

        if self._best_ema is None:
            self._best_ema = float(self._ema_reward)
            self._save_best_model()
            return True

        improvement = float(self._ema_reward - self._best_ema)
        self.logger.record("early_stop/improvement", improvement)
        self.logger.record("early_stop/stale_checks", int(self._stale_checks))

        if improvement > self.min_improvement:
            self._best_ema = float(self._ema_reward)
            self._stale_checks = 0
            self._save_best_model()
            return True

        self._stale_checks += 1
        if self._stale_checks >= self.patience_checks:
            if self.verbose > 0:
                print(
                    "[EARLY STOP] reward EMA plateau detected: "
                    f"ema={self._ema_reward:.3f}, best={self._best_ema:.3f}, "
                    f"checks={self._stale_checks}/{self.patience_checks}"
                )
            return False

        return True
