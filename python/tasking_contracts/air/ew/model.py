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

from ..execution.model import AirScriptedExecutionModel

AIR_SCRIPTED_EW_MODEL_ID = "air.ew.rwr_response_scripted"
AIR_SCRIPTED_EW_ACTION_MODEL_ID = "air.ew.rwr_action_scripted"
AIR_EW_HYBRID_ACTION_DIM = 14
AIR_EW_HYBRID_V2_ACTION_DIM = 16
# First EW tail index; [0:12] is the shared ``air_combat_hybrid_v1`` prefix.
AIR_EW_ACTION_TAIL_START = 12
# Jammer doctrines. ``hold`` never transmits. ``self_protect_on_lock`` keys the
# pod while a hostile radar holds a lock or a launch is warned, and returns it
# to standby when the threat clears (emission control otherwise).
AIR_EW_JAMMER_DOCTRINES = ("hold", "self_protect_on_lock")
# Technique codes shared with the native JammingType (0 barrage, 1 spot, 2 DRFM).
AIR_EW_JAMMER_TECHNIQUE_CODES = {"noise_barrage": 0, "noise_spot": 1, "deception_drfm": 2}
# Countermeasure dispense programs. ``continuous`` requests a release on every
# warned frame (the native release interval meters it). ``burst`` requests a
# release only for ``dispense_burst_s`` seconds after each launch-warning
# onset or each newly warned threat bearing (outside
# ``dispense_bearing_gate_deg`` of every previously warned bearing), then holds
# while the same threat set persists. Both are doctrine (tactics) settings the
# scenario must declare; they are not physical constants and have no default.
AIR_EW_DISPENSE_PROGRAMS = ("continuous", "burst")


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
    jammer_transmit: bool = False
    jammer_technique_code: int = 0


def air_ew_action_tail(intent: AirScriptedEWIntent, *, action_dim: int) -> np.ndarray:
    """Project an EW intent onto the versioned action tail after index 11.

    The tail is ``[chaff, flare]`` for ``air_ew_hybrid_v1`` and adds
    ``[jammer_transmit, technique_code]`` for ``air_ew_hybrid_v2``. It never
    covers the shared 12-element combat prefix.
    """

    dim = int(action_dim)
    if dim not in (AIR_EW_HYBRID_ACTION_DIM, AIR_EW_HYBRID_V2_ACTION_DIM):
        raise ValueError(f"Air EW action_dim must be 14 or 16, got {action_dim}")
    tail = np.zeros((dim - AIR_EW_ACTION_TAIL_START,), dtype=np.float32)
    tail[0] = 1.0 if intent.countermeasure_plan in {"request_chaff", "request_chaff_and_flare"} else 0.0
    tail[1] = 1.0 if intent.countermeasure_plan in {"request_flare", "request_chaff_and_flare"} else 0.0
    if dim == AIR_EW_HYBRID_V2_ACTION_DIM:
        tail[2] = 1.0 if intent.jammer_transmit else 0.0
        tail[3] = float(intent.jammer_technique_code)
    return tail


class AirScriptedEWModel:
    """Interpret RWR rows without accessing truth state or native components."""

    model_kind = "scripted"

    def __init__(self, *, max_rwr: int = 4) -> None:
        if int(max_rwr) <= 0:
            raise ValueError("Air scripted EW max_rwr must be positive")
        self.max_rwr = int(max_rwr)
        self._closed = False
        self._reset_program_state()

    def _reset_program_state(self) -> None:
        self._warned_bearings: tuple[float, ...] = ()
        self._burst_elapsed_s: float | None = None

    def reset(self, *, context: Any) -> None:
        del context
        self._closed = False
        self._reset_program_state()

    def _burst_active(self, *, launch_bearings: tuple[float, ...], context: Mapping[str, Any], dt: float) -> bool:
        # Both program parameters are scenario doctrine; neither has a default.
        burst_s = float(context.get("dispense_burst_s", 0.0))
        if not np.isfinite(burst_s) or burst_s <= 0.0:
            raise ValueError("Air EW burst dispense program requires a positive dispense_burst_s")
        gate_deg = float(context.get("dispense_bearing_gate_deg", 0.0))
        if not np.isfinite(gate_deg) or gate_deg <= 0.0:
            raise ValueError("Air EW burst dispense program requires a positive dispense_bearing_gate_deg")
        # A launch row carries no source id in the declared observation, so a
        # new threat is a launch row whose bearing is outside the association
        # gate of every bearing warned on the previous decision.
        new_threat = any(
            all(abs(((bearing - previous) + 180.0) % 360.0 - 180.0) > gate_deg for previous in self._warned_bearings)
            for bearing in launch_bearings
        )
        if new_threat:
            self._burst_elapsed_s = 0.0
        elif self._burst_elapsed_s is not None:
            self._burst_elapsed_s += max(0.0, float(dt))
        self._warned_bearings = launch_bearings
        # The burst covers [onset, onset + burst_s); the tolerance keeps the
        # boundary decision out despite floating-point accumulation of dt.
        return (
            bool(launch_bearings)
            and self._burst_elapsed_s is not None
            and self._burst_elapsed_s + 1.0e-9 < burst_s
        )

    def decide(self, *, observation: Any, context: Any, dt: float) -> AirScriptedEWIntent:
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
        program = str(context.get("dispense_program", "continuous")) if isinstance(context, Mapping) else "continuous"
        if program not in AIR_EW_DISPENSE_PROGRAMS:
            raise ValueError(f"unknown Air EW dispense program: {program!r}")
        launch_bearings = tuple(float(row[0]) for row in rows if float(row[3]) > 0.5)
        if program == "burst":
            dispense_due = self._burst_active(launch_bearings=launch_bearings, context=context, dt=dt)
        else:
            dispense_due = launch_warning
        if launch_warning and not dispense_due and doctrine != "observe_only":
            countermeasure_plan = "program_hold"
        elif dispense_due and doctrine == "countermeasure_ready":
            countermeasure_plan = "request_chaff_and_flare"
        elif dispense_due and doctrine == "chaff_only":
            countermeasure_plan = "request_chaff"
        elif dispense_due and doctrine == "flare_only":
            countermeasure_plan = "request_flare"
        elif launch_warning:
            countermeasure_plan = "countermeasure_deferred"
        else:
            countermeasure_plan = "hold"
        jammer_doctrine = (
            str(context.get("jammer_doctrine", "hold")) if isinstance(context, Mapping) else "hold"
        )
        if jammer_doctrine not in AIR_EW_JAMMER_DOCTRINES:
            raise ValueError(f"unknown Air EW jammer doctrine: {jammer_doctrine!r}")
        technique = (
            str(context.get("jammer_technique", "noise_barrage"))
            if isinstance(context, Mapping)
            else "noise_barrage"
        )
        if technique not in AIR_EW_JAMMER_TECHNIQUE_CODES:
            raise ValueError(f"unknown Air EW jammer technique: {technique!r}")
        jammer_transmit = jammer_doctrine == "self_protect_on_lock" and (locked or launch_warning)
        if jammer_doctrine == "hold":
            jammer_mode = "unchanged"
        else:
            jammer_mode = technique if jammer_transmit else "standby"
        return AirScriptedEWIntent(
            threat_detected=threat_detected,
            launch_warning=launch_warning,
            track_locked=locked,
            strongest_signal=strongest_signal,
            strongest_bearing_deg=strongest_bearing,
            countermeasure_plan=countermeasure_plan,
            jammer_mode=jammer_mode,
            action_owner_status="native_action_owner_required",
            observation_version=str(context.get("observation_version", "")) if isinstance(context, Mapping) else "",
            jammer_transmit=jammer_transmit,
            jammer_technique_code=AIR_EW_JAMMER_TECHNIQUE_CODES[technique],
        )

    def close(self) -> None:
        self._closed = True


class AirScriptedEWActionModel:
    """Compose flight control with a versioned EW action mode.

    ``action_dim`` 14 is ``air_ew_hybrid_v1`` (countermeasures only); 16 is
    ``air_ew_hybrid_v2``, which appends the jammer transmit switch and the
    technique code.
    """

    model_kind = "scripted"

    def __init__(
        self, *, dt: float = 0.05, max_rwr: int = 4, action_dim: int = AIR_EW_HYBRID_ACTION_DIM
    ) -> None:
        if int(action_dim) not in (AIR_EW_HYBRID_ACTION_DIM, AIR_EW_HYBRID_V2_ACTION_DIM):
            raise ValueError(f"Air scripted EW action_dim must be 14 or 16, got {action_dim}")
        self.action_dim = int(action_dim)
        self.dt = float(dt) if float(dt) > 1.0e-6 else 0.05
        self.flight_model = AirScriptedExecutionModel(action_dim=4, dt=self.dt)
        self.ew_model = AirScriptedEWModel(max_rwr=max_rwr)
        self.last_intent: AirScriptedEWIntent | None = None
        self._closed = False

    def reset(self, *, context: Any) -> None:
        if not isinstance(context, Mapping):
            raise TypeError("Air scripted EW action reset requires a mapping context")
        observation = context.get("observation")
        if not isinstance(observation, Mapping):
            raise TypeError("Air scripted EW action reset requires context['observation']")
        self.flight_model.reset(context={"observation": observation, "phase_name": context.get("phase_name", "")})
        self.ew_model.reset(context=context)
        self.last_intent = None
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
        if flight_action.size != 4:
            raise ValueError(f"Air EW flight model must emit four flight controls, got {flight_action.shape}")
        action = np.zeros((self.action_dim,), dtype=np.float32)
        action[:4] = flight_action
        intent = self.ew_model.decide(observation=observation, context=model_context, dt=dt)
        self.last_intent = intent
        action[AIR_EW_ACTION_TAIL_START:] = air_ew_action_tail(intent, action_dim=self.action_dim)
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
    "AIR_EW_ACTION_TAIL_START",
    "AIR_EW_HYBRID_ACTION_DIM",
    "AIR_EW_HYBRID_V2_ACTION_DIM",
    "AIR_EW_DISPENSE_PROGRAMS",
    "AIR_EW_JAMMER_DOCTRINES",
    "AIR_EW_JAMMER_TECHNIQUE_CODES",
    "AIR_SCRIPTED_EW_ACTION_MODEL_ID",
    "AIR_SCRIPTED_EW_MODEL_ID",
    "AirScriptedEWActionModel",
    "AirScriptedEWIntent",
    "AirScriptedEWModel",
    "air_ew_action_tail",
    "make_air_scripted_ew_action_model",
    "make_air_scripted_ew_model",
]
