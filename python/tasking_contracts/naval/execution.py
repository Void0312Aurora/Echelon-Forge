"""Scoped naval scripted adapter for the maintained N4 station baseline.

The scenario loader owns contact, station geometry, recovery, and reward
semantics for this profile.  This adapter only supplies the neutral scripted
model lifecycle and the zero station-order action used by the maintained
baseline gate.  It is deliberately registered as an ``adapter`` rather than
as a general naval combat policy.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ..common.scripted_registry import (
    ScriptedDecisionModel,
    ScriptedModelRegistration,
    ScriptedModelRegistry,
)


NAVAL_STATION_HOLD_MODEL_ID = "naval.station.screen_hold"


class NavalStationHoldScriptedModel:
    """Produce the neutral station-order hold used by the scoped N4 gate."""

    def __init__(self, *, action_dim: int = 3) -> None:
        self.action_dim = int(action_dim)
        if self.action_dim <= 0:
            raise ValueError("naval station scripted action_dim must be positive")
        self._closed = False

    def reset(self, *, context: Any) -> None:
        del context
        self._closed = False

    def decide(self, *, observation: Any, context: Any, dt: float) -> np.ndarray:
        del observation, context, dt
        if self._closed:
            raise RuntimeError("naval station scripted model is closed")
        return np.zeros((self.action_dim,), dtype=np.float32)

    def close(self) -> None:
        self._closed = True


def make_naval_station_hold_model(**kwargs: Any) -> NavalStationHoldScriptedModel:
    return NavalStationHoldScriptedModel(**kwargs)


NAVAL_SCRIPTED_MODEL_REGISTRY = ScriptedModelRegistry(
    (
        ScriptedModelRegistration(
            model_id=NAVAL_STATION_HOLD_MODEL_ID,
            domain="naval",
            role_ids=("naval_warfare_commander",),
            factory=make_naval_station_hold_model,
            status="adapter",
            note=(
                "Scoped N4 station-hold baseline; scenario runtime owns "
                "station geometry, contacts, reports, recovery, and rewards."
            ),
        ),
    )
)


__all__ = [
    "NAVAL_SCRIPTED_MODEL_REGISTRY",
    "NAVAL_STATION_HOLD_MODEL_ID",
    "NavalStationHoldScriptedModel",
    "make_naval_station_hold_model",
]
