from __future__ import annotations

from typing import Any

import numpy as np

from python.rl.control.mission_defs import (
    COMMAND_CODE_LANDING,
    normalize_phase_name,
    scripted_mode_for_phase_name,
)
from python.rl.control.scripted_landing import ScriptedLandingController
from python.rl.control.scripted_stable_flight import ScriptedStableFlightController
from python.rl.control.scripted_takeoff import ScriptedTakeoffController


class ScriptedExecutiveController:
    def __init__(self, env: Any, *, transition_alt_agl_m: float = 140.0):
        self.env = env
        self.transition_alt_agl_m = float(transition_alt_agl_m)
        self.takeoff_ctrl: ScriptedTakeoffController | None = None
        self.stable_ctrl: ScriptedStableFlightController | None = None
        self.landing_ctrl: ScriptedLandingController | None = None
        self.active_mode = "takeoff"

    @property
    def action_dim(self) -> int:
        return int(self.env.action_space.shape[0])

    def reset(self, obs: dict) -> None:
        dt = 0.05
        try:
            dt = float(getattr(self.env.unwrapped.sim, "get_time_step", lambda: 0.05)())
        except Exception:
            dt = 0.05
        self.takeoff_ctrl = ScriptedTakeoffController(action_dim=self.action_dim, dt=dt)
        self.stable_ctrl = ScriptedStableFlightController(action_dim=self.action_dim, dt=dt)
        self.landing_ctrl = ScriptedLandingController(action_dim=self.action_dim, dt=dt)
        self.active_mode = "takeoff"
        self.takeoff_ctrl.reset(obs)
        self.stable_ctrl.reset(obs)
        self.landing_ctrl.reset(obs)

    def _infer_mode(self, obs: dict) -> str:
        loader = getattr(self.env.unwrapped, "loader", None)
        phase_name = normalize_phase_name(getattr(loader, "mission_phase_name", ""))
        if phase_name == "departure":
            try:
                inst = np.asarray(obs.get("instruments", []), dtype=np.float32).reshape(-1)
                if inst.size >= 4 and float(inst[3]) >= self.transition_alt_agl_m:
                    return "stable_flight"
            except Exception:
                pass
            return "takeoff"
        mode = scripted_mode_for_phase_name(phase_name)
        if mode:
            return mode

        try:
            mission = np.asarray(obs.get("mission", []), dtype=np.float32).reshape(-1)
            if mission.size >= 1 and int(round(float(mission[0]))) >= COMMAND_CODE_LANDING:
                return "landing_ils"
        except Exception:
            pass
        try:
            inst = np.asarray(obs.get("instruments", []), dtype=np.float32).reshape(-1)
            if inst.size >= 4 and float(inst[3]) < self.transition_alt_agl_m:
                return "takeoff"
        except Exception:
            pass
        return "stable_flight"

    def predict(self, obs: dict) -> np.ndarray:
        mode = self._infer_mode(obs)
        if mode != self.active_mode:
            ctrl = self._controller_for_mode(mode)
            if ctrl is not None:
                ctrl.reset(obs)
            self.active_mode = mode
        ctrl = self._controller_for_mode(mode)
        if ctrl is None:
            return np.zeros((self.action_dim,), dtype=np.float32)
        return np.asarray(ctrl.step(obs), dtype=np.float32).reshape(-1)

    def _controller_for_mode(self, mode: str):
        if mode == "landing_ils":
            return self.landing_ctrl
        if mode == "stable_flight":
            return self.stable_ctrl
        return self.takeoff_ctrl
