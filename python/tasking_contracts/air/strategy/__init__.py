"""Replaceable Air scripted strategy implementations and typed contracts."""

from __future__ import annotations

from .assessment import (
    AIR_ASSESSMENT_IDLE,
    AIR_ASSESSMENT_IN_FLIGHT,
    AIR_ASSESSMENT_REATTACK_READY,
    AIR_ASSESSMENT_TERMINAL_OBSERVED,
    AIR_ASSESSMENT_TRACK_LOST,
    AIR_ASSESSMENT_TRACK_UNAVAILABLE,
    AirPostLaunchAssessment,
    AirPostLaunchAssessmentReport,
)
from .contracts import (
    AirAssessmentInput,
    AirPlanningContext,
    AirPostLaunchAssessor,
    AirTacticalDecision,
    AirTacticalPlanner,
)
from .planning import (
    AirEngagementPlan,
    AirEngagementPlanner,
    AirEngagementPlannerConfig,
)
from .weapons import AirWeaponEnvelope, load_air_weapon_envelope

__all__ = [
    "AIR_ASSESSMENT_IDLE",
    "AIR_ASSESSMENT_IN_FLIGHT",
    "AIR_ASSESSMENT_REATTACK_READY",
    "AIR_ASSESSMENT_TERMINAL_OBSERVED",
    "AIR_ASSESSMENT_TRACK_LOST",
    "AIR_ASSESSMENT_TRACK_UNAVAILABLE",
    "AirAssessmentInput",
    "AirEngagementPlan",
    "AirEngagementPlanner",
    "AirEngagementPlannerConfig",
    "AirPlanningContext",
    "AirPostLaunchAssessment",
    "AirPostLaunchAssessmentReport",
    "AirPostLaunchAssessor",
    "AirTacticalDecision",
    "AirTacticalPlanner",
    "AirWeaponEnvelope",
    "load_air_weapon_envelope",
]
