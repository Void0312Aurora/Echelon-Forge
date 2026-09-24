"""Aggregate registry for maintained and bounded Air scripted models."""

from __future__ import annotations

from .air_scripted_engagement import (
    AIR_SCRIPTED_ENGAGEMENT_MODEL_ID,
    make_air_scripted_engagement_model,
)
from .air_scripted_ew import (
    AIR_SCRIPTED_EW_ACTION_MODEL_ID,
    AIR_SCRIPTED_EW_MODEL_ID,
    make_air_scripted_ew_action_model,
    make_air_scripted_ew_model,
)
from .air_scripted_execution import (
    AIR_SCRIPTED_EXECUTION_MODEL_ID,
    make_air_scripted_execution_model,
)
from .scripted_registry import ScriptedModelRegistration, ScriptedModelRegistry


AIR_SCRIPTED_MODEL_REGISTRY = ScriptedModelRegistry(
    (
        ScriptedModelRegistration(
            model_id=AIR_SCRIPTED_EXECUTION_MODEL_ID,
            domain="air",
            role_ids=("autopilot_controller",),
            factory=make_air_scripted_execution_model,
            status="maintained",
            note="Composed takeoff, stable-flight, and landing execution model.",
        ),
        ScriptedModelRegistration(
            model_id=AIR_SCRIPTED_ENGAGEMENT_MODEL_ID,
            domain="air",
            role_ids=("air_tactical_engagement_controller",),
            factory=make_air_scripted_engagement_model,
            status="adapter",
            note=(
                "C2/ROE-derived tactical event overlay composed with the neutral "
                "Air phase execution model; direct scenario admission remains open."
            ),
        ),
        ScriptedModelRegistration(
            model_id=AIR_SCRIPTED_EW_MODEL_ID,
            domain="air",
            role_ids=("air_ew_controller",),
            factory=make_air_scripted_ew_model,
            status="adapter",
            note=(
                "RWR-derived EW response intent; countermeasure and jammer "
                "native action ownership remains open."
            ),
        ),
        ScriptedModelRegistration(
            model_id=AIR_SCRIPTED_EW_ACTION_MODEL_ID,
            domain="air",
            role_ids=("air_ew_action_controller",),
            factory=make_air_scripted_ew_action_model,
            status="adapter",
            note=(
                "Versioned 14-element EW action extension; native acceptance "
                "and replay/roster gates remain open."
            ),
        ),
    )
)


__all__ = ["AIR_SCRIPTED_MODEL_REGISTRY"]
