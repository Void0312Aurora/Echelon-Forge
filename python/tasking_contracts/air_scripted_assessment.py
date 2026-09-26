"""Compatibility shell for the canonical Air strategy assessment layer."""

from __future__ import annotations

from .air.strategy.assessment import (
    AIR_ASSESSMENT_IDLE,
    AIR_ASSESSMENT_IN_FLIGHT,
    AIR_ASSESSMENT_REATTACK_READY,
    AIR_ASSESSMENT_TERMINAL_OBSERVED,
    AIR_ASSESSMENT_TRACK_LOST,
    AIR_ASSESSMENT_TRACK_UNAVAILABLE,
    AirPostLaunchAssessment,
    AirPostLaunchAssessmentReport,
)

__all__ = [
    "AIR_ASSESSMENT_IDLE",
    "AIR_ASSESSMENT_IN_FLIGHT",
    "AIR_ASSESSMENT_REATTACK_READY",
    "AIR_ASSESSMENT_TERMINAL_OBSERVED",
    "AIR_ASSESSMENT_TRACK_LOST",
    "AIR_ASSESSMENT_TRACK_UNAVAILABLE",
    "AirPostLaunchAssessment",
    "AirPostLaunchAssessmentReport",
]
