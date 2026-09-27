"""Neutral air execution model built from the maintained flight controllers.

The model is the first concrete consumer of ``ScriptedModelRegistry``. It owns
air phase-to-controller selection and keeps environment-specific phase lookup in
the ``gym_envs`` adapter. It does not load scenarios, access a kernel, or
depend on RL.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from .air_scripted_registry import AIR_SCRIPTED_MODEL_REGISTRY

from .mission_defs import (
    COMMAND_CODE_LANDING,
    normalize_phase_name,
    scripted_mode_for_phase_name,
)
from .scripted_landing import ScriptedLandingController
from .scripted_registry import (
    ScriptedDecisionModel,
)
from .scripted_stable_flight import ScriptedStableFlightController
from .scripted_takeoff import ScriptedTakeoffController


AIR_SCRIPTED_EXECUTION_MODEL_ID = "air.execution.phase_scripted"

if TYPE_CHECKING:
    from .air_scripted_registry import AIR_SCRIPTED_MODEL_REGISTRY


class AirScriptedExecutionModel:
    """Compose the existing air takeoff, cruise, and landing controllers.

    ``step`` is the environment-adapter convenience method. ``reset`` and
    ``decide`` implement the neutral scripted-model lifecycle and accept an
    opaque context dictionary with optional ``observation`` and ``phase_name``
    keys. The model never reads a world kernel directly.
    """

    def __init__(
        self,
        *,
        action_dim: int,
        dt: float = 0.05,
        transition_alt_agl_m: float = 140.0,
        runway_length_m: float = 0.0,
    ) -> None:
        self.action_dim = int(action_dim)
        self.dt = float(dt) if float(dt) > 1.0e-6 else 0.05
        self.transition_alt_agl_m = float(transition_alt_agl_m)
        self.runway_length_m = max(0.0, float(runway_length_m))
        self.takeoff_ctrl: ScriptedTakeoffController | None = None
        self.stable_ctrl: ScriptedStableFlightController | None = None
        self.landing_ctrl: ScriptedLandingController | None = None
        self.active_mode = "takeoff"
        self._closed = False

    def reset_observation(self, obs: dict[str, Any], *, phase_name: str = "") -> None:
        self.takeoff_ctrl = ScriptedTakeoffController(action_dim=self.action_dim, dt=self.dt)
        self.stable_ctrl = ScriptedStableFlightController(action_dim=self.action_dim, dt=self.dt)
        self.landing_ctrl = ScriptedLandingController(
            action_dim=self.action_dim,
            dt=self.dt,
            runway_length_m=self.runway_length_m,
        )
        self.active_mode = "takeoff"
        self._closed = False
        self.takeoff_ctrl.reset(obs)
        self.stable_ctrl.reset(obs)
        self.landing_ctrl.reset(obs)

    def reset(self, *, context: Any) -> None:
        obs, phase_name = self._context_values(context)
        if not isinstance(obs, dict):
            raise TypeError("air scripted execution reset requires context['observation'] dict")
        self.reset_observation(obs, phase_name=phase_name)

    def decide(self, *, observation: Any, context: Any, dt: float) -> np.ndarray:
        if not isinstance(observation, dict):
            raise TypeError("air scripted execution observation must be a dict")
        if float(dt) > 1.0e-6 and abs(float(dt) - self.dt) > 1.0e-12:
            self.dt = float(dt)
            for controller in (self.takeoff_ctrl, self.stable_ctrl, self.landing_ctrl):
                if controller is not None:
                    controller.dt = self.dt
        phase_name = self._context_phase(context)
        return self.step(observation, phase_name=phase_name)

    def step(self, obs: dict[str, Any], *, phase_name: str = "") -> np.ndarray:
        if self._closed:
            raise RuntimeError("air scripted execution model is closed")
        if self.takeoff_ctrl is None or self.stable_ctrl is None or self.landing_ctrl is None:
            self.reset_observation(obs, phase_name=phase_name)
        mode = self._infer_mode(obs, phase_name)
        self._set_mode(mode, obs)
        controller = self._controller_for_mode(self.active_mode)
        if controller is None:
            return np.zeros((self.action_dim,), dtype=np.float32)
        return np.asarray(controller.step(obs), dtype=np.float32).reshape(-1)

    def close(self) -> None:
        self.takeoff_ctrl = None
        self.stable_ctrl = None
        self.landing_ctrl = None
        self._closed = True

    def _set_mode(self, mode: str, obs: dict[str, Any]) -> None:
        normalized = str(mode or "takeoff")
        if normalized == self.active_mode:
            return
        controller = self._controller_for_mode(normalized)
        if controller is not None:
            controller.reset(obs)
        self.active_mode = normalized

    def _infer_mode(self, obs: dict[str, Any], phase_name: str) -> str:
        normalized_phase = normalize_phase_name(phase_name)
        if normalized_phase == "departure":
            instruments = np.asarray(obs.get("instruments", []), dtype=np.float32).reshape(-1)
            if instruments.size >= 4 and float(instruments[3]) >= self.transition_alt_agl_m:
                return "stable_flight"
            return "takeoff"

        mode = scripted_mode_for_phase_name(normalized_phase)
        if mode:
            return mode

        mission = np.asarray(obs.get("mission", []), dtype=np.float32).reshape(-1)
        if mission.size >= 1 and int(round(float(mission[0]))) >= COMMAND_CODE_LANDING:
            return "landing_ils"

        instruments = np.asarray(obs.get("instruments", []), dtype=np.float32).reshape(-1)
        if instruments.size >= 4 and float(instruments[3]) < self.transition_alt_agl_m:
            return "takeoff"
        return "stable_flight"

    def _controller_for_mode(self, mode: str) -> Any:
        if mode == "landing_ils":
            return self.landing_ctrl
        if mode == "stable_flight":
            return self.stable_ctrl
        return self.takeoff_ctrl

    @staticmethod
    def _context_values(context: Any) -> tuple[Any, str]:
        if not isinstance(context, dict):
            return None, ""
        return context.get("observation"), str(context.get("phase_name", ""))

    @staticmethod
    def _context_phase(context: Any) -> str:
        return "" if not isinstance(context, dict) else str(context.get("phase_name", ""))


def make_air_scripted_execution_model(**kwargs: Any) -> AirScriptedExecutionModel:
    return AirScriptedExecutionModel(**kwargs)


def __getattr__(name: str) -> Any:
    """Preserve the historical registry import without a second registry.

    The aggregate registry lives in ``air_scripted_registry`` so Air models
    can be registered together without import-time mutation.  A module-level
    lazy attribute keeps existing callers of
    ``air_scripted_execution.AIR_SCRIPTED_MODEL_REGISTRY`` source-compatible.
    """

    if name == "AIR_SCRIPTED_MODEL_REGISTRY":
        from .air_scripted_registry import AIR_SCRIPTED_MODEL_REGISTRY

        return AIR_SCRIPTED_MODEL_REGISTRY
    raise AttributeError(name)

__all__ = [
    "AIR_SCRIPTED_EXECUTION_MODEL_ID",
    "AIR_SCRIPTED_MODEL_REGISTRY",
    "AirScriptedExecutionModel",
    "make_air_scripted_execution_model",
]
