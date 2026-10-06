"""RL-independent scripted Air combat model with an EW self-protection tail.

Composition rule: the model owns one ``AirScriptedEngagementModel`` (12-element
``air_combat_hybrid_v1`` action) and one ``AirScriptedEWModel``. Its action is
the engagement action unchanged in ``[0:12]`` followed by the versioned EW tail
(``[12:14]`` chaff/flare for ``air_ew_hybrid_v1``; ``[14:16]`` jammer transmit
and technique for ``air_ew_hybrid_v2``). The EW intent never writes the
engagement prefix: it does not override flight control, radar, or the weapon
request, so the engagement model alone shapes the fire request and the
environment's Air combat event gate alone decides whether a release is
accepted. Both sub-models read only the declared observation (C2/ROE mission
rows and RWR rows); neither touches native EW or weapon state.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping

import numpy as np

from ..engagement.model import AIR_COMBAT_HYBRID_ACTION_DIM, AirScriptedEngagementModel
from ..ew.model import (
    AIR_EW_ACTION_TAIL_START,
    AIR_EW_HYBRID_ACTION_DIM,
    AIR_EW_HYBRID_V2_ACTION_DIM,
    AirScriptedEWIntent,
    AirScriptedEWModel,
    air_ew_action_tail,
)

AIR_SCRIPTED_COMBAT_EW_MODEL_ID = "air.combat_ew.c2_roe_ew_scripted"
AIR_COMBAT_EW_ROLE_ID = "air_combat_ew_controller"

if AIR_EW_ACTION_TAIL_START != AIR_COMBAT_HYBRID_ACTION_DIM:
    raise RuntimeError("Air EW action tail must start right after the combat-hybrid prefix")


class AirScriptedCombatEWModel:
    """Engagement prefix plus EW tail; see the module docstring for the rule."""

    model_kind = "scripted"

    def __init__(
        self,
        *,
        action_dim: int = AIR_EW_HYBRID_ACTION_DIM,
        max_rwr: int = 4,
        **engagement_kwargs: Any,
    ) -> None:
        if int(action_dim) not in (AIR_EW_HYBRID_ACTION_DIM, AIR_EW_HYBRID_V2_ACTION_DIM):
            raise ValueError(
                "Air scripted combat-EW action_dim must be "
                f"{AIR_EW_HYBRID_ACTION_DIM} (air_ew_hybrid_v1) or "
                f"{AIR_EW_HYBRID_V2_ACTION_DIM} (air_ew_hybrid_v2), got {action_dim}"
            )
        self.action_dim = int(action_dim)
        self.engagement_model = AirScriptedEngagementModel(
            action_dim=AIR_COMBAT_HYBRID_ACTION_DIM,
            **engagement_kwargs,
        )
        self.ew_model = AirScriptedEWModel(max_rwr=max_rwr)
        self.last_intent: AirScriptedEWIntent | None = None
        self._closed = False

    @property
    def last_engagement_decision_info(self) -> dict[str, Any]:
        return self.engagement_model.last_decision_info

    @property
    def last_decision_info(self) -> dict[str, Any]:
        """Report the last engagement decision and the last EW intent together."""

        return {
            "role": AIR_COMBAT_EW_ROLE_ID,
            "engagement": dict(self.engagement_model.last_decision_info),
            "ew_intent": None if self.last_intent is None else asdict(self.last_intent),
        }

    def reset(self, *, context: Any) -> None:
        if not isinstance(context, Mapping):
            raise TypeError("Air scripted combat-EW reset requires a mapping context")
        self.engagement_model.reset(context=dict(context))
        self.ew_model.reset(context=context)
        self.last_intent = None
        self._closed = False

    def decide(self, *, observation: Any, context: Any, dt: float) -> np.ndarray:
        if self._closed:
            raise RuntimeError("Air scripted combat-EW model is closed")
        model_context = dict(context) if isinstance(context, Mapping) else {}
        prefix = np.asarray(
            self.engagement_model.decide(observation=observation, context=model_context, dt=dt),
            dtype=np.float32,
        ).reshape(-1)
        if prefix.size != AIR_COMBAT_HYBRID_ACTION_DIM:
            raise RuntimeError(
                f"Air engagement model returned {prefix.size} values, expected {AIR_COMBAT_HYBRID_ACTION_DIM}"
            )
        intent = self.ew_model.decide(observation=observation, context=model_context, dt=dt)
        self.last_intent = intent
        tail = air_ew_action_tail(intent, action_dim=self.action_dim)
        return np.concatenate((prefix, tail)).astype(np.float32, copy=False)

    def close(self) -> None:
        self.engagement_model.close()
        self.ew_model.close()
        self._closed = True


def make_air_scripted_combat_ew_model(**kwargs: Any) -> AirScriptedCombatEWModel:
    return AirScriptedCombatEWModel(**kwargs)


__all__ = [
    "AIR_COMBAT_EW_ROLE_ID",
    "AIR_SCRIPTED_COMBAT_EW_MODEL_ID",
    "AirScriptedCombatEWModel",
    "make_air_scripted_combat_ew_model",
]
