"""Compatibility shell for the canonical Air strategy planning layer."""

from __future__ import annotations

from .air.strategy.planning import (
    AirEngagementPlan,
    AirEngagementPlanner,
    AirEngagementPlannerConfig,
)
from .air.strategy.weapons import AirWeaponEnvelope
from .air.strategy.contracts import AirPlanningContext, AirTacticalDecision

__all__ = [
    "AirWeaponEnvelope",
    "AirEngagementPlan",
    "AirEngagementPlanner",
    "AirEngagementPlannerConfig",
    "AirPlanningContext",
    "AirTacticalDecision",
]
