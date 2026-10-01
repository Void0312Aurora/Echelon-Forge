"""Bounded Ground scripted adapters."""

from __future__ import annotations

from .execution import (
    GROUND_INFANTRY_CONTROLLER_ROLE_ID,
    GROUND_INFANTRY_SCRIPTED_MODEL_ID,
    GROUND_SCRIPTED_MODEL_REGISTRY,
    GroundInfantryDecision,
    GroundInfantryObjectiveTask,
    GroundInfantryObservation,
    GroundInfantryScriptedModel,
    GroundScriptedTaskError,
    make_ground_infantry_scripted_model,
)

__all__ = [
    "GROUND_INFANTRY_CONTROLLER_ROLE_ID",
    "GROUND_INFANTRY_SCRIPTED_MODEL_ID",
    "GROUND_SCRIPTED_MODEL_REGISTRY",
    "GroundInfantryDecision",
    "GroundInfantryObjectiveTask",
    "GroundInfantryObservation",
    "GroundInfantryScriptedModel",
    "GroundScriptedTaskError",
    "make_ground_infantry_scripted_model",
]
