from __future__ import annotations

from typing import Any

import numpy as np

from python.tasking_contracts.air_scripted_execution import (
    AIR_SCRIPTED_EXECUTION_MODEL_ID,
    AIR_SCRIPTED_MODEL_REGISTRY,
)


class ScriptedExecutiveController:
    def __init__(
        self,
        env: Any,
        *,
        transition_alt_agl_m: float = 140.0,
        model_id: str = AIR_SCRIPTED_EXECUTION_MODEL_ID,
    ):
        self.env = env
        self.transition_alt_agl_m = float(transition_alt_agl_m)
        self.model_id = str(model_id).strip() or AIR_SCRIPTED_EXECUTION_MODEL_ID
        self._model = None

    @property
    def active_mode(self) -> str:
        return "takeoff" if self._model is None else self._model.active_mode

    @property
    def takeoff_ctrl(self):
        return None if self._model is None else self._model.takeoff_ctrl

    @property
    def stable_ctrl(self):
        return None if self._model is None else self._model.stable_ctrl

    @property
    def landing_ctrl(self):
        return None if self._model is None else self._model.landing_ctrl

    @property
    def action_dim(self) -> int:
        return int(self.env.action_space.shape[0])

    def reset(self, obs: dict) -> None:
        dt = 0.05
        try:
            dt = float(getattr(self.env.unwrapped.sim, "get_time_step", lambda: 0.05)())
        except Exception:
            dt = 0.05
        self._model = AIR_SCRIPTED_MODEL_REGISTRY.create_for(
            domain="air",
            role_id="autopilot_controller",
            model_id=self.model_id,
            action_dim=self.action_dim,
            dt=dt,
            transition_alt_agl_m=self.transition_alt_agl_m,
        )
        self._model.reset_observation(obs, phase_name=self._phase_name())

    def _phase_name(self) -> str:
        loader = getattr(self.env.unwrapped, "loader", None)
        return "" if loader is None else str(getattr(loader, "mission_phase_name", ""))

    def predict(self, obs: dict) -> np.ndarray:
        if self._model is None:
            self.reset(obs)
        assert self._model is not None
        return self._model.step(obs, phase_name=self._phase_name())
