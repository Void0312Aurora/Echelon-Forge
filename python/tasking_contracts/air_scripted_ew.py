"""RL-independent scripted Air EW observation/decision adapter.

The adapter interprets only the declared RWR observation rows. It emits an EW
decision envelope for a future native action owner; it never writes
``Countermeasures`` or ``Jammer`` state and therefore remains an ``adapter``
registration until the versioned Air action extension is admitted.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np

from .air_scripted_execution import AirScriptedExecutionModel

AIR_SCRIPTED_EW_MODEL_ID = "air.ew.rwr_response_scripted"
AIR_SCRIPTED_EW_ACTION_MODEL_ID = "air.ew.rwr_action_scripted"
AIR_EW_HYBRID_ACTION_DIM = 14


@dataclass(frozen=True)
class AirScriptedEWIntent:
    """Declared RWR-derived response intent awaiting native command ownership."""

    threat_detected: bool
    launch_warning: bool
    track_locked: bool
    strongest_signal: float
    strongest_bearing_deg: float
    countermeasure_plan: str
    jammer_mode: str
    action_owner_status: str
    observation_version: str


class AirScriptedEWModel:
    """Interpret RWR rows without accessing truth state or native components."""

    def __init__(self, *, max_rwr: int = 4) -> None:
        if int(max_rwr) <= 0:
            raise ValueError("Air scripted EW max_rwr must be positive")
        self.max_rwr = int(max_rwr)
        self._closed = False

    def reset(self, *, context: Any) -> None:
        del context
        self._closed = False

    def decide(self, *, observation: Any, context: Any, dt: float) -> AirScriptedEWIntent:
        del dt
        if self._closed:
            raise RuntimeError("Air scripted EW model is closed")
        if not isinstance(observation, Mapping):
            raise TypeError("Air scripted EW observation must be a mapping")
        rows = np.asarray(observation.get("rwr", []), dtype=np.float32)
        if rows.size == 0:
            rows = np.zeros((0, 4), dtype=np.float32)
        rows = rows.reshape(-1, 4)[: self.max_rwr]
        if rows.shape[0] == 0:
            strongest_signal = 0.0
            strongest_bearing = 0.0
            locked = False
            launch_warning = False
        else:
            strongest_index = int(np.argmax(rows[:, 1]))
            strongest = rows[strongest_index]
            strongest_signal = float(strongest[1])
            strongest_bearing = float(strongest[0])
            locked = bool(np.any(rows[:, 2] > 0.5))
            launch_warning = bool(np.any(rows[:, 3] > 0.5))
        threat_detected = bool(rows.shape[0] and np.any(rows[:, 1] > 0.0))
        doctrine = str(context.get("response_doctrine", "observe_only")) if isinstance(context, Mapping) else "observe_only"
        if launch_warning and doctrine == "countermeasure_ready":
            countermeasure_plan = "request_chaff_and_flare"
        elif launch_warning and doctrine == "chaff_only":
            countermeasure_plan = "request_chaff"
        elif launch_warning and doctrine == "flare_only":
            countermeasure_plan = "request_flare"
        elif launch_warning:
            countermeasure_plan = "countermeasure_deferred"
        else:
            countermeasure_plan = "hold"
        return AirScriptedEWIntent(
            threat_detected=threat_detected,
            launch_warning=launch_warning,
            track_locked=locked,
            strongest_signal=strongest_signal,
            strongest_bearing_deg=strongest_bearing,
            countermeasure_plan=countermeasure_plan,
            jammer_mode="unchanged",
            action_owner_status="native_action_owner_required",
            observation_version=str(context.get("observation_version", "")) if isinstance(context, Mapping) else "",
        )

    def close(self) -> None:
        self._closed = True


class AirScriptedEWActionModel:
    """Compose flight control with the versioned 14-element EW action mode."""

    def __init__(self, *, dt: float = 0.05, max_rwr: int = 4) -> None:
        self.dt = float(dt) if float(dt) > 1.0e-6 else 0.05
        # Flight controllers use the maintained 17D full-action layout.  Their
        # output is projected below before it reaches the 14D EW extension.
        self.flight_model = AirScriptedExecutionModel(action_dim=17, dt=self.dt)
        self.ew_model = AirScriptedEWModel(max_rwr=max_rwr)
        self._closed = False

    def reset(self, *, context: Any) -> None:
        if not isinstance(context, Mapping):
            raise TypeError("Air scripted EW action reset requires a mapping context")
        observation = context.get("observation")
        if not isinstance(observation, Mapping):
            raise TypeError("Air scripted EW action reset requires context['observation']")
        self.flight_model.reset(context={"observation": observation, "phase_name": context.get("phase_name", "")})
        self.ew_model.reset(context=context)
        self._closed = False

    def decide(self, *, observation: Any, context: Any, dt: float) -> np.ndarray:
        if self._closed:
            raise RuntimeError("Air scripted EW action model is closed")
        if not isinstance(observation, Mapping):
            raise TypeError("Air scripted EW action observation must be a mapping")
        model_context = context if isinstance(context, Mapping) else {}
        flight_action = np.asarray(
            self.flight_model.decide(observation=observation, context=model_context, dt=dt),
            dtype=np.float32,
        ).reshape(-1)
        if flight_action.size < 4:
            raise ValueError("Air scripted flight model must emit at least four shared flight axes")
        # The EW extension keeps only the shared flight axes.  Indices 4:12
        # belong to the combat-hybrid prefix and must stay neutral unless a
        # dedicated C2/ROE model owns them; EW owns only 12/13 here.
        action = np.zeros((AIR_EW_HYBRID_ACTION_DIM,), dtype=np.float32)
        action[:4] = flight_action[:4]
        intent = self.ew_model.decide(observation=observation, context=model_context, dt=dt)
        action[12] = 1.0 if intent.countermeasure_plan in {"request_chaff", "request_chaff_and_flare"} else 0.0
        action[13] = 1.0 if intent.countermeasure_plan in {"request_flare", "request_chaff_and_flare"} else 0.0
        return action

    def close(self) -> None:
        self.flight_model.close()
        self.ew_model.close()
        self._closed = True


def make_air_scripted_ew_model(**kwargs: Any) -> AirScriptedEWModel:
    return AirScriptedEWModel(**kwargs)


def make_air_scripted_ew_action_model(**kwargs: Any) -> AirScriptedEWActionModel:
    return AirScriptedEWActionModel(**kwargs)


__all__ = [
    "AIR_EW_HYBRID_ACTION_DIM",
    "AIR_SCRIPTED_EW_ACTION_MODEL_ID",
    "AIR_SCRIPTED_EW_MODEL_ID",
    "AirScriptedEWActionModel",
    "AirScriptedEWIntent",
    "AirScriptedEWModel",
    "make_air_scripted_ew_action_model",
    "make_air_scripted_ew_model",
]
