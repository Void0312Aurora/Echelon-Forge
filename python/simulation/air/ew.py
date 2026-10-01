"""Simulation-side composition of the neutral scripted Air EW action model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np

from python.tasking_contracts.air.ew.model import (
    AIR_EW_HYBRID_ACTION_DIM,
    AIR_EW_HYBRID_V2_ACTION_DIM,
    AirScriptedEWActionModel,
    AirScriptedEWIntent,
)

from .action import build_pilot_action
from .observation import build_air_scripted_observation


@dataclass(frozen=True)
class AirEWDecision:
    """Neutral EW action plus its native PilotAction projection."""

    action: np.ndarray
    pilot_action: Any
    intent: AirScriptedEWIntent


class AirScriptedEWController:
    """Adapt native RWR state to the replaceable scripted EW model."""

    def __init__(self, *, model: AirScriptedEWActionModel | None = None, dt: float = 0.05) -> None:
        self.model = model or AirScriptedEWActionModel(dt=dt)
        self.action_mode = (
            "air_ew_hybrid_v2"
            if int(getattr(self.model, "action_dim", AIR_EW_HYBRID_ACTION_DIM)) == AIR_EW_HYBRID_V2_ACTION_DIM
            else "air_ew_hybrid_v1"
        )
        self._closed = False

    def reset(
        self,
        *,
        observation: Any,
        instruments: Any,
        command: Any = None,
        phase_name: str = "stable_flight",
        doctrine: str = "observe_only",
        jammer_doctrine: str = "hold",
    ) -> None:
        scripted_observation = build_air_scripted_observation(observation, instruments, command)
        self.model.reset(
            context={
                "observation": scripted_observation,
                "phase_name": phase_name,
                "response_doctrine": doctrine,
                "jammer_doctrine": jammer_doctrine,
            }
        )
        self._closed = False

    def decide(
        self,
        *,
        observation: Any,
        instruments: Any,
        command: Any = None,
        phase_name: str = "stable_flight",
        doctrine: str = "observe_only",
        jammer_doctrine: str = "hold",
        observation_version: str = "",
        dt: float | None = None,
    ) -> AirEWDecision:
        if self._closed:
            raise RuntimeError("Air scripted EW controller is closed")
        scripted_observation = build_air_scripted_observation(observation, instruments, command)
        context: Mapping[str, Any] = {
            "phase_name": phase_name,
            "response_doctrine": doctrine,
            "jammer_doctrine": jammer_doctrine,
            "observation_version": observation_version,
        }
        action = np.asarray(
            self.model.decide(
                observation=scripted_observation,
                context=context,
                dt=float(dt if dt is not None else self.model.dt),
            ),
            dtype=np.float32,
        ).reshape(-1)
        intent = self.model.last_intent
        if intent is None:
            raise RuntimeError("Air scripted EW action model did not retain its decision intent")
        return AirEWDecision(
            action=action,
            pilot_action=build_pilot_action(
                action,
                action_mode=self.action_mode,
                instrument_state=instruments,
            ),
            intent=intent,
        )

    def close(self) -> None:
        self.model.close()
        self._closed = True


__all__ = ["AIR_EW_HYBRID_ACTION_DIM", "AirEWDecision", "AirScriptedEWController"]
