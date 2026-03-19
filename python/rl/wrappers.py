from __future__ import annotations

from typing import Iterable, Optional

import numpy as np

import gymnasium as gym
from python.rl.mission_defs import (
    is_route_command_code,
    normalize_command_code,
    scripted_mode_for_command_code,
    scripted_mode_for_phase_name,
)
from python.rl.scripted_landing import ScriptedLandingController
from python.rl.scripted_takeoff import ScriptedTakeoffController
from python.rl.scripted_stable_flight import ScriptedStableFlightController


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
        binary_hysteresis_indices: Optional[Iterable[int]] = None,
        binary_on_threshold: float = 0.75,
        binary_off_threshold: float = 0.25,
        binary_initial_values: Optional[dict[int, float] | dict[str, float]] = None,
        center_deadband_indices: Optional[Iterable[int]] = None,
        center_deadband_center: float = 0.5,
        center_deadband_half_width: float = 0.0,
        scripted_baseline_mode: str | None = None,
        scripted_residual_scale: float = 1.0,
        scripted_residual_alt_breakpoints_m: Optional[Iterable[float]] = None,
        scripted_residual_alt_scales: Optional[Iterable[float]] = None,
        scripted_residual_mode_scales: Optional[dict[str, float]] = None,
        scripted_blend_indices: Optional[Iterable[int]] = None,
        scripted_lock_indices: Optional[Iterable[int]] = None,
        scripted_residual_terminal_waypoint_count: int = 0,
        scripted_residual_terminal_scale: float = 1.0,
        scripted_residual_phaseout_target_speed_max: float | None = None,
        scripted_residual_phaseout_target_altitude_max: float | None = None,
        scripted_residual_phaseout_scale: float = 1.0,
        scripted_transition_alt_agl_m: float = 120.0,
        action_rate_penalty_coef: float = 0.0,
    ):
        super().__init__(env)
        self.hold_steps = int(hold_steps)
        self.low_freq_indices = tuple(sorted(set(int(i) for i in (low_freq_indices or ()))))
        self.snap_binary_indices = tuple(sorted(set(int(i) for i in (snap_binary_indices or ()))))
        self.binary_hysteresis_indices = tuple(sorted(set(int(i) for i in (binary_hysteresis_indices or ()))))
        self.binary_on_threshold = float(binary_on_threshold)
        self.binary_off_threshold = float(binary_off_threshold)
        if self.binary_off_threshold > self.binary_on_threshold:
            self.binary_off_threshold, self.binary_on_threshold = self.binary_on_threshold, self.binary_off_threshold
        self.binary_initial_values = {
            int(k): (1.0 if float(v) > 0.5 else 0.0)
            for k, v in dict(binary_initial_values or {}).items()
        }
        self.center_deadband_indices = tuple(sorted(set(int(i) for i in (center_deadband_indices or ()))))
        self.center_deadband_center = float(center_deadband_center)
        self.center_deadband_half_width = max(0.0, float(center_deadband_half_width))
        self.scripted_baseline_mode = str(scripted_baseline_mode).strip().lower() if scripted_baseline_mode else None
        self.scripted_residual_scale = float(np.clip(float(scripted_residual_scale), 0.0, 1.0))
        bp = [float(x) for x in (scripted_residual_alt_breakpoints_m or ())]
        sv = [float(np.clip(float(x), 0.0, 1.0)) for x in (scripted_residual_alt_scales or ())]
        if len(bp) >= 2 and len(bp) == len(sv):
            order = np.argsort(np.asarray(bp, dtype=np.float32))
            self.scripted_residual_alt_breakpoints_m = tuple(float(bp[i]) for i in order)
            self.scripted_residual_alt_scales = tuple(float(sv[i]) for i in order)
        else:
            self.scripted_residual_alt_breakpoints_m = ()
            self.scripted_residual_alt_scales = ()
        self.scripted_residual_mode_scales = {
            str(k).strip().lower(): float(np.clip(float(v), 0.0, 1.0))
            for k, v in dict(scripted_residual_mode_scales or {}).items()
            if str(k).strip()
        }
        self.scripted_blend_indices = tuple(sorted(set(int(i) for i in (scripted_blend_indices or ()))))
        self.scripted_lock_indices = tuple(sorted(set(int(i) for i in (scripted_lock_indices or ()))))
        self.scripted_residual_terminal_waypoint_count = max(0, int(scripted_residual_terminal_waypoint_count))
        self.scripted_residual_terminal_scale = float(np.clip(float(scripted_residual_terminal_scale), 0.0, 1.0))
        self.scripted_residual_phaseout_target_speed_max = (
            None if scripted_residual_phaseout_target_speed_max is None else float(scripted_residual_phaseout_target_speed_max)
        )
        self.scripted_residual_phaseout_target_altitude_max = (
            None if scripted_residual_phaseout_target_altitude_max is None else float(scripted_residual_phaseout_target_altitude_max)
        )
        self.scripted_residual_phaseout_scale = float(np.clip(float(scripted_residual_phaseout_scale), 0.0, 1.0))
        self.scripted_transition_alt_agl_m = max(0.0, float(scripted_transition_alt_agl_m))
        self.action_rate_penalty_coef = float(action_rate_penalty_coef)

        self._t = 0
        self._held_action: Optional[np.ndarray] = None
        self._binary_state: dict[int, float] = {}
        self._last_obs = None
        self._scripted_ctrl: Optional[object] = None
        self._scripted_takeoff_ctrl: Optional[ScriptedTakeoffController] = None
        self._scripted_stable_ctrl: Optional[ScriptedStableFlightController] = None
        self._scripted_landing_ctrl: Optional[ScriptedLandingController] = None
        self._scripted_active_mode: str | None = None

    def reset(self, **kwargs):
        self._t = 0
        self._held_action = None
        self._binary_state = {int(k): float(v) for k, v in self.binary_initial_values.items()}
        self._scripted_ctrl = None
        self._scripted_takeoff_ctrl = None
        self._scripted_stable_ctrl = None
        self._scripted_landing_ctrl = None
        self._scripted_active_mode = None
        obs, info = self.env.reset(**kwargs)
        self._last_obs = obs
        if self.scripted_baseline_mode in ("stable_flight", "takeoff", "takeoff_then_stable_flight", "landing_ils", "takeoff_cruise_landing"):
            dt = 0.05
            try:
                dt = float(getattr(self.unwrapped.sim, "get_time_step", lambda: 0.05)())
            except Exception:
                dt = 0.05
            if self.scripted_baseline_mode == "takeoff":
                self._scripted_takeoff_ctrl = ScriptedTakeoffController(
                    action_dim=int(self.action_space.shape[0]),
                    dt=dt,
                )
                self._scripted_ctrl = self._scripted_takeoff_ctrl
                self._scripted_active_mode = "takeoff"
            elif self.scripted_baseline_mode == "takeoff_then_stable_flight":
                self._scripted_takeoff_ctrl = ScriptedTakeoffController(
                    action_dim=int(self.action_space.shape[0]),
                    dt=dt,
                )
                self._scripted_stable_ctrl = ScriptedStableFlightController(
                    action_dim=int(self.action_space.shape[0]),
                    dt=dt,
                )
                self._scripted_ctrl = self._scripted_takeoff_ctrl
                self._scripted_active_mode = "takeoff"
            elif self.scripted_baseline_mode == "landing_ils":
                self._scripted_landing_ctrl = ScriptedLandingController(
                    action_dim=int(self.action_space.shape[0]),
                    dt=dt,
                )
                self._scripted_ctrl = self._scripted_landing_ctrl
                self._scripted_active_mode = "landing_ils"
            elif self.scripted_baseline_mode == "takeoff_cruise_landing":
                self._scripted_takeoff_ctrl = ScriptedTakeoffController(
                    action_dim=int(self.action_space.shape[0]),
                    dt=dt,
                )
                self._scripted_stable_ctrl = ScriptedStableFlightController(
                    action_dim=int(self.action_space.shape[0]),
                    dt=dt,
                )
                self._scripted_landing_ctrl = ScriptedLandingController(
                    action_dim=int(self.action_space.shape[0]),
                    dt=dt,
                )
                self._scripted_ctrl = self._scripted_takeoff_ctrl
                self._scripted_active_mode = "takeoff"
            else:
                self._scripted_stable_ctrl = ScriptedStableFlightController(
                    action_dim=int(self.action_space.shape[0]),
                    dt=dt,
                )
                self._scripted_ctrl = self._scripted_stable_ctrl
                self._scripted_active_mode = "stable_flight"
            if isinstance(obs, dict) and self._scripted_ctrl is not None:
                self._scripted_ctrl.reset(obs)
        return obs, info

    def _get_loader(self):
        candidates = [
            getattr(self, "loader", None),
            getattr(self.env, "loader", None),
            getattr(self.unwrapped, "loader", None),
        ]
        for loader in candidates:
            if loader is not None:
                return loader
        return None

    def _obs_alt_agl_m(self, obs) -> float | None:
        try:
            if isinstance(obs, dict):
                inst = np.asarray(obs.get("instruments", []), dtype=np.float32).reshape(-1)
                if inst.size >= 4:
                    return float(inst[3])
        except Exception:
            pass
        return None

    def _scripted_mode_from_command_code(self, command_code, *, alt_agl_m: float | None = None) -> str | None:
        mode = scripted_mode_for_command_code(
            command_code,
            alt_agl_m=alt_agl_m,
            takeoff_transition_alt_agl_m=self.scripted_transition_alt_agl_m,
        )
        code = normalize_command_code(command_code, default=0)
        if (
            mode == "stable_flight"
            and code in (2, 3)
            and alt_agl_m is not None
            and alt_agl_m < self.scripted_transition_alt_agl_m
            and self._scripted_active_mode not in ("stable_flight", "landing_ils")
        ):
            return "takeoff"
        return mode

    @staticmethod
    def _loader_command_code(loader) -> int | None:
        if loader is None:
            return None
        mission_cmd = getattr(loader, "mission_cmd", None)
        if isinstance(mission_cmd, dict):
            return mission_cmd.get("command_code", None)
        return getattr(mission_cmd, "command_code", None)

    def _infer_scripted_mode_from_loader(self) -> str | None:
        loader = self._get_loader()
        if loader is None:
            return None
        alt_agl = self._obs_alt_agl_m(self._last_obs)
        phase_name = str(getattr(loader, "mission_phase_name", "")).strip().lower()
        if phase_name == "departure":
            if alt_agl is not None and alt_agl >= self.scripted_transition_alt_agl_m:
                return "stable_flight"
            return "takeoff"
        mode = scripted_mode_for_phase_name(phase_name)
        if mode is not None:
            return mode
        try:
            intent = getattr(loader, "leader_intent", None)
            if intent is not None:
                phase_name = str(getattr(intent, "phase_id", "")).split(".")[-1].strip().lower()
                if phase_name == "departure":
                    if alt_agl is not None and alt_agl >= self.scripted_transition_alt_agl_m:
                        return "stable_flight"
                    return "takeoff"
                mode = scripted_mode_for_phase_name(phase_name)
                if mode is not None:
                    return mode
                mode = self._scripted_mode_from_command_code(getattr(intent, "command_code", None), alt_agl_m=alt_agl)
                if mode is not None:
                    return mode
        except Exception:
            pass
        return self._scripted_mode_from_command_code(self._loader_command_code(loader), alt_agl_m=alt_agl)

    def _infer_scripted_mode_from_obs_command(self, obs) -> str | None:
        try:
            if isinstance(obs, dict):
                mission = np.asarray(obs.get("mission", []), dtype=np.float32).reshape(-1)
                if mission.size >= 1:
                    return self._scripted_mode_from_command_code(
                        int(round(float(mission[0]))),
                        alt_agl_m=self._obs_alt_agl_m(obs),
                    )
        except Exception:
            pass
        return None

    def _infer_scripted_mode_from_obs(self, obs) -> str | None:
        if self.scripted_baseline_mode == "takeoff":
            return "takeoff"
        if self.scripted_baseline_mode == "stable_flight":
            return "stable_flight"
        if self.scripted_baseline_mode == "landing_ils":
            return "landing_ils"
        if self.scripted_baseline_mode == "takeoff_cruise_landing":
            loader_mode = self._infer_scripted_mode_from_loader()
            if loader_mode is not None:
                return loader_mode
            obs_mode = self._infer_scripted_mode_from_obs_command(obs)
            if obs_mode is not None:
                return obs_mode
            alt_agl = self._obs_alt_agl_m(obs)
            if alt_agl is not None:
                if alt_agl >= self.scripted_transition_alt_agl_m:
                    return "stable_flight"
                if self._scripted_active_mode in ("stable_flight", "landing_ils"):
                    return self._scripted_active_mode
                return "takeoff"
            return self._scripted_active_mode or "takeoff"
        if self.scripted_baseline_mode != "takeoff_then_stable_flight":
            return None
        alt_agl = self._obs_alt_agl_m(obs)
        if alt_agl is not None:
            if alt_agl < self.scripted_transition_alt_agl_m:
                return "takeoff"
            return "stable_flight"
        return self._scripted_active_mode or "takeoff"

    def _get_scripted_controller(self):
        if self.scripted_baseline_mode == "takeoff":
            return self._scripted_takeoff_ctrl or self._scripted_ctrl
        if self.scripted_baseline_mode == "stable_flight":
            return self._scripted_stable_ctrl or self._scripted_ctrl
        if self.scripted_baseline_mode == "landing_ils":
            return self._scripted_landing_ctrl or self._scripted_ctrl
        if self.scripted_baseline_mode == "takeoff_cruise_landing":
            desired_mode = self._infer_scripted_mode_from_obs(self._last_obs)
            if desired_mode == "landing_ils":
                desired_ctrl = self._scripted_landing_ctrl
            elif desired_mode == "stable_flight":
                desired_ctrl = self._scripted_stable_ctrl
            else:
                desired_ctrl = self._scripted_takeoff_ctrl
            if desired_ctrl is None:
                return self._scripted_ctrl
            if desired_mode != self._scripted_active_mode and isinstance(self._last_obs, dict):
                desired_ctrl.reset(self._last_obs)
            self._scripted_active_mode = desired_mode
            self._scripted_ctrl = desired_ctrl
            return desired_ctrl
        if self.scripted_baseline_mode != "takeoff_then_stable_flight":
            return self._scripted_ctrl

        desired_mode = self._infer_scripted_mode_from_obs(self._last_obs)
        desired_ctrl = self._scripted_takeoff_ctrl if desired_mode == "takeoff" else self._scripted_stable_ctrl
        if desired_ctrl is None:
            return self._scripted_ctrl
        if desired_mode != self._scripted_active_mode and isinstance(self._last_obs, dict):
            desired_ctrl.reset(self._last_obs)
        self._scripted_active_mode = desired_mode
        self._scripted_ctrl = desired_ctrl
        return desired_ctrl

    def _current_scripted_residual_scale(self) -> float:
        scale = float(self.scripted_residual_scale)
        if self.scripted_residual_alt_breakpoints_m and self._last_obs is not None:
            try:
                inst = np.asarray(self._last_obs.get("instruments", []), dtype=np.float32).reshape(-1)
                if inst.size >= 4:
                    alt_agl = float(inst[3])
                    scale = float(
                        np.interp(
                            alt_agl,
                            np.asarray(self.scripted_residual_alt_breakpoints_m, dtype=np.float32),
                            np.asarray(self.scripted_residual_alt_scales, dtype=np.float32),
                        )
                    )
            except Exception:
                pass
        mode = str(self._scripted_active_mode or "").strip().lower()
        if mode and mode in self.scripted_residual_mode_scales:
            scale = min(scale, float(self.scripted_residual_mode_scales[mode]))
        if self.scripted_residual_terminal_waypoint_count > 0:
            try:
                loader = self._get_loader()
                waypoints = list(getattr(loader, "waypoints", []) or [])
                wp_idx = int(getattr(loader, "waypoint_idx", 0))
                cmd_code = int(self._loader_command_code(loader) or 0)
                remaining = max(0, len(waypoints) - wp_idx)
                if waypoints and is_route_command_code(cmd_code) and remaining <= self.scripted_residual_terminal_waypoint_count:
                    scale = min(scale, self.scripted_residual_terminal_scale)
            except Exception:
                pass
        if self._last_obs is not None and (
            self.scripted_residual_phaseout_target_speed_max is not None
            or self.scripted_residual_phaseout_target_altitude_max is not None
        ):
            try:
                mission = np.asarray(self._last_obs.get("mission", []), dtype=np.float32).reshape(-1)
                tgt_alt = float(mission[2]) if mission.size >= 3 else None
                tgt_spd = float(mission[3]) if mission.size >= 4 else None
                phaseout = False
                if (
                    self.scripted_residual_phaseout_target_speed_max is not None
                    and tgt_spd is not None
                    and np.isfinite(tgt_spd)
                    and tgt_spd <= float(self.scripted_residual_phaseout_target_speed_max)
                ):
                    phaseout = True
                if (
                    self.scripted_residual_phaseout_target_altitude_max is not None
                    and tgt_alt is not None
                    and np.isfinite(tgt_alt)
                    and tgt_alt <= float(self.scripted_residual_phaseout_target_altitude_max)
                ):
                    phaseout = True
                if phaseout:
                    scale = min(scale, self.scripted_residual_phaseout_scale)
            except Exception:
                pass
        return float(np.clip(scale, 0.0, 1.0))

    def step(self, action):
        a = np.asarray(action, dtype=np.float32).reshape(-1).copy()
        baseline_action = None
        locked_idx: tuple[int, ...] = ()
        scripted_ctrl = None

        if (
            (scripted_ctrl := self._get_scripted_controller()) is not None
            and isinstance(self._last_obs, dict)
            and (self.scripted_blend_indices or self.scripted_lock_indices)
        ):
            try:
                baseline_action = np.asarray(scripted_ctrl.step(self._last_obs), dtype=np.float32).reshape(-1)
            except Exception:
                baseline_action = None
            if baseline_action is not None and baseline_action.size == a.size:
                idx = [i for i in self.scripted_blend_indices if 0 <= i < a.size]
                if idx:
                    s = self._current_scripted_residual_scale()
                    a[idx] = baseline_action[idx] + s * (a[idx] - baseline_action[idx])
                lock_idx = tuple(i for i in self.scripted_lock_indices if 0 <= i < a.size)
                if lock_idx:
                    a[list(lock_idx)] = baseline_action[list(lock_idx)]
                    locked_idx = lock_idx

        if self._held_action is None:
            self._held_action = a.copy()

        # Hold low-frequency dimensions between updates.
        if self.hold_steps > 1 and (self._t % self.hold_steps) != 0 and self.low_freq_indices:
            a[list(self.low_freq_indices)] = self._held_action[list(self.low_freq_indices)]

        # Real cockpit switches are detented and latched, not continuous around 0.5.
        for idx in self.binary_hysteresis_indices:
            if idx in locked_idx or not (0 <= idx < a.size):
                continue
            state = float(self._binary_state.get(idx, self.binary_initial_values.get(idx, 0.0)))
            val = float(a[idx])
            if val >= self.binary_on_threshold:
                state = 1.0
            elif val <= self.binary_off_threshold:
                state = 0.0
            a[idx] = state
            self._binary_state[idx] = state

        # Snap selected dims to {0,1}.
        for idx in self.snap_binary_indices:
            if idx in locked_idx:
                continue
            if 0 <= idx < a.size:
                a[idx] = 1.0 if a[idx] > 0.5 else 0.0

        # Add realistic free-play around center for analog axes that map "stowed/off" to 0.5.
        if self.center_deadband_half_width > 0.0:
            lo = self.center_deadband_center - self.center_deadband_half_width
            hi = self.center_deadband_center + self.center_deadband_half_width
            for idx in self.center_deadband_indices:
                if idx in locked_idx:
                    continue
                if 0 <= idx < a.size and lo <= float(a[idx]) <= hi:
                    a[idx] = self.center_deadband_center

        rate_penalty = 0.0
        if self.action_rate_penalty_coef > 0.0 and self._held_action is not None:
            rate_penalty = float(self.action_rate_penalty_coef) * float(np.mean(np.abs(a - self._held_action)))

        obs, reward, terminated, truncated, info = self.env.step(a)
        self._last_obs = obs

        if isinstance(info, dict):
            info = dict(info)
            info["effective_action"] = a.astype(np.float32, copy=True)
            if baseline_action is not None and baseline_action.size == a.size:
                info["baseline_action"] = baseline_action.astype(np.float32, copy=True)
            if self._scripted_active_mode is not None:
                info["scripted_baseline_mode_active"] = str(self._scripted_active_mode)

        if rate_penalty != 0.0:
            reward = float(reward) - rate_penalty
            if isinstance(info, dict):
                info["action_rate_penalty"] = float(rate_penalty)

        self._held_action = a.copy()
        self._t += 1
        return obs, reward, terminated, truncated, info


def get_action_wrapper_spec(train_config: dict | None):
    if not isinstance(train_config, dict):
        return None, None
    wrappers_cfg = train_config.get("wrappers", {})
    if not isinstance(wrappers_cfg, dict):
        return None, None
    mts_cfg = wrappers_cfg.get("multi_timescale_action")
    if not (isinstance(mts_cfg, dict) and bool(mts_cfg.get("enabled", False))):
        return None, None
    kwargs = {
        "hold_steps": int(mts_cfg.get("hold_steps", 4)),
        "low_freq_indices": mts_cfg.get(
            "low_freq_indices",
            [4, 5, 6, 9, 12, 13, 14, 15, 16],
        ),
        "snap_binary_indices": mts_cfg.get(
            "snap_binary_indices",
            [4, 9, 12, 13, 14, 15],
        ),
        "binary_hysteresis_indices": mts_cfg.get("binary_hysteresis_indices", []),
        "binary_on_threshold": float(mts_cfg.get("binary_on_threshold", 0.75)),
        "binary_off_threshold": float(mts_cfg.get("binary_off_threshold", 0.25)),
        "binary_initial_values": mts_cfg.get("binary_initial_values", {}),
        "center_deadband_indices": mts_cfg.get("center_deadband_indices", []),
        "center_deadband_center": float(mts_cfg.get("center_deadband_center", 0.5)),
        "center_deadband_half_width": float(mts_cfg.get("center_deadband_half_width", 0.0)),
        "scripted_baseline_mode": mts_cfg.get("scripted_baseline_mode"),
        "scripted_residual_scale": float(mts_cfg.get("scripted_residual_scale", 1.0)),
        "scripted_residual_alt_breakpoints_m": mts_cfg.get("scripted_residual_alt_breakpoints_m", []),
        "scripted_residual_alt_scales": mts_cfg.get("scripted_residual_alt_scales", []),
        "scripted_residual_mode_scales": mts_cfg.get("scripted_residual_mode_scales", {}),
        "scripted_blend_indices": mts_cfg.get("scripted_blend_indices", []),
        "scripted_lock_indices": mts_cfg.get("scripted_lock_indices", []),
        "scripted_residual_terminal_waypoint_count": int(mts_cfg.get("scripted_residual_terminal_waypoint_count", 0)),
        "scripted_residual_terminal_scale": float(mts_cfg.get("scripted_residual_terminal_scale", 1.0)),
        "scripted_residual_phaseout_target_speed_max": mts_cfg.get("scripted_residual_phaseout_target_speed_max"),
        "scripted_residual_phaseout_target_altitude_max": mts_cfg.get("scripted_residual_phaseout_target_altitude_max"),
        "scripted_residual_phaseout_scale": float(mts_cfg.get("scripted_residual_phaseout_scale", 1.0)),
        "scripted_transition_alt_agl_m": float(mts_cfg.get("scripted_transition_alt_agl_m", 120.0)),
        "action_rate_penalty_coef": float(mts_cfg.get("action_rate_penalty_coef", 0.0)),
    }
    return MultiTimescaleActionWrapper, kwargs
