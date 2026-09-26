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
    AirActionApplication,
    AirActionAdapter,
    AirAssessmentInput,
    AirPlanningContext,
    AirObservationAdapter,
    AirPostLaunchAssessor,
    AirTacticalActionIntent,
    AirTacticalDecision,
    AirTacticalObservation,
    AirTacticalPlanner,
)
from .action import AIR_COMBAT_HYBRID_ACTION_DIM, AIR_FULL_ACTION_DIM, AirActionLayoutAdapter
from .observation import AirMissionContactObservationAdapter
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
    "AirActionApplication",
    "AirActionAdapter",
    "AirActionLayoutAdapter",
    "AIR_COMBAT_HYBRID_ACTION_DIM",
    "AIR_FULL_ACTION_DIM",
    "AirEngagementPlan",
    "AirEngagementPlanner",
    "AirEngagementPlannerConfig",
    "AirPlanningContext",
    "AirMissionContactObservationAdapter",
    "AirObservationAdapter",
    "AirPostLaunchAssessment",
    "AirPostLaunchAssessmentReport",
    "AirPostLaunchAssessor",
    "AirTacticalActionIntent",
    "AirTacticalDecision",
    "AirTacticalObservation",
    "AirTacticalPlanner",
    "AirWeaponEnvelope",
    "load_air_weapon_envelope",
]
