"""Bounded scripted controller for one native Ground infantry soldier.

The model is the Ground entry behind the neutral ``DecisionModelRegistry``. It
moves one soldier toward a task-supplied objective point and then holds there
with an admitted static task mode. Its output is the admitted Ground command
shape: a static task mode plus ``MoveStatic`` heading, speed fraction, and
stance with the fixed ``direct`` route intent.

Boundaries:

- The observation is a typed packet carrying only own position, own
  operational state, and the commander-issued engagement fields already present
  on the mission command (``assigned_target_id`` and the fire-authorization
  flag). Target geometry, contact tracks, terrain truth, and raw kernel state
  are not inputs; Ground sensing and track export remain held.
- A fire request is an input-gated request only. It is emitted when the
  commander has assigned a target and authorized fire; the native
  ``fire_ground_weapon_from_mission_command`` gate remains the release
  authority (holder match, tracked contact, range, ammunition, cooldown). The
  model never writes or grants authority.
- Route planning, passability, line of sight, cover, sensing, indirect fire,
  suppression, logistics, and multi-unit behavior are not represented; a task
  that needs a non-direct route fails closed.

The module is dependency-terminal: it imports neither RL, Gym, NumPy, native
bindings, nor a simulation backend.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping

from ..common.decision_registry import (
    DecisionModelRegistration,
    DecisionModelRegistry,
)


GROUND_INFANTRY_SCRIPTED_MODEL_ID = "ground.infantry.objective_occupy_scripted"
GROUND_INFANTRY_CONTROLLER_ROLE_ID = "ground_infantry_controller"

# Spellings shared with the maintained Ground command projection
# (``python/rl/ground/command.py``) and ``GroundTaskMode``/``GroundStance``.
GROUND_MOVE_TASK_MODE = "move_static"
GROUND_HOLD_TASK_MODES: tuple[str, ...] = ("occupy_static", "support_static")
GROUND_STANCES: tuple[str, ...] = ("stand", "crouch", "prone")
GROUND_DIRECT_ROUTE_INTENT = "direct"

DECISION_REASON_MOVING = "moving_to_objective"
DECISION_REASON_HOLDING = "holding_objective"
DECISION_REASON_NOT_OPERATIONAL = "not_operational"


class GroundScriptedTaskError(ValueError):
    """Raised when a Ground task or observation cannot be represented."""


def _finite(value: Any, *, name: str) -> float:
    if isinstance(value, bool):
        raise GroundScriptedTaskError(f"{name} must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise GroundScriptedTaskError(f"{name} must be numeric") from exc
    if not math.isfinite(number):
        raise GroundScriptedTaskError(f"{name} must be finite")
    return number


def _point(value: Any, *, name: str) -> tuple[float, float]:
    try:
        items = tuple(value)
    except TypeError as exc:
        raise GroundScriptedTaskError(f"{name} must contain two coordinates") from exc
    if len(items) != 2:
        raise GroundScriptedTaskError(f"{name} must contain two coordinates")
    return (_finite(items[0], name=name), _finite(items[1], name=name))


def _wrap_heading_deg(value: float) -> float:
    wrapped = (float(value) + 180.0) % 360.0 - 180.0
    return 0.0 if abs(wrapped) < 1.0e-12 else wrapped


@dataclass(frozen=True)
class GroundInfantryObjectiveTask:
    """Task-supplied objective for one soldier (not World Truth).

    ``objective_radius_m`` is the task's own arrival tolerance and has no
    default: the scenario or commander that issues the task owns it.
    """

    objective_xy_m: tuple[float, float]
    objective_radius_m: float
    hold_task_mode: str = "occupy_static"
    stance: str = "stand"
    speed_fraction: float = 1.0
    route_intent: str = GROUND_DIRECT_ROUTE_INTENT

    def __post_init__(self) -> None:
        object.__setattr__(self, "objective_xy_m", _point(self.objective_xy_m, name="objective_xy_m"))
        radius = _finite(self.objective_radius_m, name="objective_radius_m")
        if radius <= 0.0:
            raise GroundScriptedTaskError("objective_radius_m must be positive")
        object.__setattr__(self, "objective_radius_m", radius)
        hold_mode = str(self.hold_task_mode).strip().lower()
        if hold_mode not in GROUND_HOLD_TASK_MODES:
            raise GroundScriptedTaskError(
                f"hold_task_mode must be one of {GROUND_HOLD_TASK_MODES}"
            )
        object.__setattr__(self, "hold_task_mode", hold_mode)
        stance = str(self.stance).strip().lower()
        if stance not in GROUND_STANCES:
            raise GroundScriptedTaskError(f"stance must be one of {GROUND_STANCES}")
        object.__setattr__(self, "stance", stance)
        fraction = _finite(self.speed_fraction, name="speed_fraction")
        if not 0.0 < fraction <= 1.0:
            raise GroundScriptedTaskError("speed_fraction must be in (0, 1]")
        object.__setattr__(self, "speed_fraction", fraction)
        route_intent = str(self.route_intent).strip().lower()
        if route_intent != GROUND_DIRECT_ROUTE_INTENT:
            raise GroundScriptedTaskError(
                "Ground scripted tasks admit only the direct route intent; "
                "route planning is held"
            )
        object.__setattr__(self, "route_intent", route_intent)


@dataclass(frozen=True)
class GroundInfantryObservation:
    """Admitted own-state observation for the scripted soldier.

    ``assigned_target_id`` and ``authorization_to_fire`` are read back from the
    soldier's own mission command; they are commander-issued fields, not a
    sensor product.
    """

    position_xy_m: tuple[float, float]
    operational: bool
    assigned_target_id: int = 0
    authorization_to_fire: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "position_xy_m", _point(self.position_xy_m, name="position_xy_m"))
        if not isinstance(self.operational, bool):
            raise GroundScriptedTaskError("operational must be a bool")
        if not isinstance(self.authorization_to_fire, bool):
            raise GroundScriptedTaskError("fire authorization must be a bool")
        if isinstance(self.assigned_target_id, bool):
            raise GroundScriptedTaskError("assigned_target_id must be an integer")
        target = int(self.assigned_target_id)
        if target < 0:
            raise GroundScriptedTaskError("assigned_target_id must be non-negative")
        object.__setattr__(self, "assigned_target_id", target)


@dataclass(frozen=True)
class GroundInfantryDecision:
    """Admitted Ground command shape plus an optional input-gated fire request."""

    ground_task_mode: str
    desired_heading_deg: float
    desired_speed_fraction: float
    stance: str
    route_intent: str
    objective_distance_m: float
    objective_reached: bool
    fire_requested: bool
    fire_target_id: int
    reason: str

    def command_action(self) -> dict[str, Any]:
        """Return the movement fields consumed by the Ground command projection."""

        return {
            "ground_task_mode": self.ground_task_mode,
            "desired_heading_deg": self.desired_heading_deg,
            "desired_speed_fraction": self.desired_speed_fraction,
            "stance": self.stance,
            "route_intent": self.route_intent,
        }


class GroundInfantryScriptedModel:
    """Move to the task objective, then hold it with the admitted static mode."""

    model_kind = "scripted"

    def __init__(self) -> None:
        self._task: GroundInfantryObjectiveTask | None = None
        self._objective_reached = False
        self._last_heading_deg = 0.0
        self._closed = False

    def reset(self, *, context: Any) -> None:
        if not isinstance(context, Mapping):
            raise TypeError("Ground scripted reset requires a mapping context")
        task = context.get("task")
        if not isinstance(task, GroundInfantryObjectiveTask):
            raise TypeError("Ground scripted reset requires a GroundInfantryObjectiveTask")
        self._task = task
        self._objective_reached = False
        self._last_heading_deg = 0.0
        self._closed = False

    def decide(self, *, observation: Any, context: Any, dt: float) -> GroundInfantryDecision:
        del context, dt
        if self._closed:
            raise RuntimeError("Ground scripted model is closed")
        if self._task is None:
            raise RuntimeError("Ground scripted model must be reset before deciding")
        if not isinstance(observation, GroundInfantryObservation):
            raise TypeError("Ground scripted model requires GroundInfantryObservation")
        task = self._task
        dx = task.objective_xy_m[0] - observation.position_xy_m[0]
        dy = task.objective_xy_m[1] - observation.position_xy_m[1]
        distance = math.hypot(dx, dy)
        if distance <= task.objective_radius_m:
            # Arrival latches: once reached, the soldier occupies the objective
            # instead of oscillating around the tolerance boundary.
            self._objective_reached = True

        if not observation.operational:
            return self._decision(
                task_mode=task.hold_task_mode,
                speed_fraction=0.0,
                distance=distance,
                fire_target_id=0,
                reason=DECISION_REASON_NOT_OPERATIONAL,
            )

        fire_target_id = (
            observation.assigned_target_id
            if observation.authorization_to_fire and observation.assigned_target_id > 0
            else 0
        )
        if self._objective_reached:
            return self._decision(
                task_mode=task.hold_task_mode,
                speed_fraction=0.0,
                distance=distance,
                fire_target_id=fire_target_id,
                reason=DECISION_REASON_HOLDING,
            )
        self._last_heading_deg = _wrap_heading_deg(math.degrees(math.atan2(dx, dy)))
        return self._decision(
            task_mode=GROUND_MOVE_TASK_MODE,
            speed_fraction=task.speed_fraction,
            distance=distance,
            fire_target_id=fire_target_id,
            reason=DECISION_REASON_MOVING,
        )

    def close(self) -> None:
        self._closed = True

    def _decision(
        self,
        *,
        task_mode: str,
        speed_fraction: float,
        distance: float,
        fire_target_id: int,
        reason: str,
    ) -> GroundInfantryDecision:
        assert self._task is not None
        return GroundInfantryDecision(
            ground_task_mode=task_mode,
            desired_heading_deg=self._last_heading_deg,
            desired_speed_fraction=float(speed_fraction),
            stance=self._task.stance,
            route_intent=self._task.route_intent,
            objective_distance_m=float(distance),
            objective_reached=self._objective_reached,
            fire_requested=fire_target_id > 0,
            fire_target_id=int(fire_target_id),
            reason=reason,
        )


def make_ground_infantry_scripted_model(**kwargs: Any) -> GroundInfantryScriptedModel:
    if kwargs:
        raise TypeError(
            f"Ground scripted model takes its task through reset context, not {sorted(kwargs)!r}"
        )
    return GroundInfantryScriptedModel()


GROUND_SCRIPTED_MODEL_REGISTRY = DecisionModelRegistry(
    (
        DecisionModelRegistration(
            model_id=GROUND_INFANTRY_SCRIPTED_MODEL_ID,
            domain="ground",
            role_ids=(GROUND_INFANTRY_CONTROLLER_ROLE_ID,),
            factory=make_ground_infantry_scripted_model,
            model_kind="scripted",
            status="adapter",
            note=(
                "Single-soldier move-to-objective and static hold over the bounded "
                "native infantry movement slice; fire is an input-gated request to "
                "the native mission-command gate. Route, passability, sensing, "
                "indirect fire, suppression, logistics, and multi-unit remain held."
            ),
        ),
    )
)


__all__ = [
    "DECISION_REASON_HOLDING",
    "DECISION_REASON_MOVING",
    "DECISION_REASON_NOT_OPERATIONAL",
    "GROUND_DIRECT_ROUTE_INTENT",
    "GROUND_HOLD_TASK_MODES",
    "GROUND_INFANTRY_CONTROLLER_ROLE_ID",
    "GROUND_INFANTRY_SCRIPTED_MODEL_ID",
    "GROUND_MOVE_TASK_MODE",
    "GROUND_SCRIPTED_MODEL_REGISTRY",
    "GROUND_STANCES",
    "GroundInfantryDecision",
    "GroundInfantryObjectiveTask",
    "GroundInfantryObservation",
    "GroundInfantryScriptedModel",
    "GroundScriptedTaskError",
    "make_ground_infantry_scripted_model",
]
