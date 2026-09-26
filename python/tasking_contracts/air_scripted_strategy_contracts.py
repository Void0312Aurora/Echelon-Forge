"""Compatibility shell for the canonical Air strategy contract layer."""

from __future__ import annotations

from .air.strategy.contracts import (
    AirAssessmentInput,
    AirPlanningContext,
    AirPostLaunchAssessor,
    AirTacticalDecision,
    AirTacticalPlanner,
)

__all__ = [
    "AirAssessmentInput",
    "AirPlanningContext",
    "AirPostLaunchAssessor",
    "AirTacticalDecision",
    "AirTacticalPlanner",
]
