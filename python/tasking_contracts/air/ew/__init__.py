"""Air electronic-warfare scripted adapters."""

from __future__ import annotations

from .formation import AirFormationEWRuntime, AirFormationEWRoleOrder
from .model import (
    AirScriptedEWActionModel,
    AirScriptedEWIntent,
    AirScriptedEWModel,
    make_air_scripted_ew_action_model,
    make_air_scripted_ew_model,
)

__all__ = [
    "AirFormationEWRuntime",
    "AirFormationEWRoleOrder",
    "AirScriptedEWActionModel",
    "AirScriptedEWIntent",
    "AirScriptedEWModel",
    "make_air_scripted_ew_action_model",
    "make_air_scripted_ew_model",
]
