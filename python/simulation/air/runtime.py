"""Common decision-runtime adapter for the compiled Air engagement line.

The neutral runtime owns scheduling, hold/expiry, provenance, and roster
routing.  This adapter owns only the translation between that opaque runtime
payload and the maintained Air engagement controller.  A learned or human
provider can occupy the same ``DecisionRuntimeAgent`` slot without changing
the simulation backend or the Air-native observation/action contracts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .engagement import AirEngagementFacts, AirEngagementDecision, AirScriptedEngagementController


@dataclass(frozen=True)
class AirEngagementRuntimeInput:
    """Domain-owned input packet passed opaquely through the common runtime."""

    native_observation: Any
    instruments: Any
    command: Any
    facts: AirEngagementFacts
    phase_name: str = "stable_flight"
    last_event_info: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.facts, AirEngagementFacts):
            raise TypeError("Air engagement runtime input requires AirEngagementFacts")
        phase_name = str(self.phase_name).strip() or "stable_flight"
        object.__setattr__(self, "phase_name", phase_name)
        object.__setattr__(self, "last_event_info", dict(self.last_event_info))


class AirScriptedEngagementRuntimeModel:
    """Expose the Air controller through the neutral DecisionModel lifecycle."""

    def __init__(
        self,
        *,
        controller: AirScriptedEngagementController | None = None,
        **controller_kwargs: Any,
    ) -> None:
        if controller is not None and controller_kwargs:
            raise ValueError("provide controller or controller_kwargs, not both")
        self.controller = controller or AirScriptedEngagementController(**controller_kwargs)
        self._closed = False

    def reset(self, *, context: Any) -> None:
        if not isinstance(context, Mapping):
            raise TypeError("Air engagement runtime reset requires a mapping context")
        packet = _require_input(context.get("observation"))
        self.controller.reset(
            observation=packet.native_observation,
            instruments=packet.instruments,
            command=packet.command,
            facts=packet.facts,
            phase_name=packet.phase_name,
        )
        self._closed = False

    def decide(self, *, observation: Any, context: Any, dt: float) -> AirEngagementDecision:
        if self._closed:
            raise RuntimeError("Air engagement runtime model is closed")
        packet = _require_input(observation)
        model_context = context if isinstance(context, Mapping) else {}
        phase_name = str(model_context.get("phase_name", packet.phase_name)).strip() or packet.phase_name
        event_info = model_context.get("last_event_info", packet.last_event_info)
        if not isinstance(event_info, Mapping):
            raise TypeError("Air engagement runtime last_event_info must be a mapping")
        return self.controller.decide(
            observation=packet.native_observation,
            instruments=packet.instruments,
            command=packet.command,
            facts=packet.facts,
            phase_name=phase_name,
            dt=float(dt),
            last_event_info=event_info,
        )

    def close(self) -> None:
        if not self._closed:
            self.controller.close()
            self._closed = True


def _require_input(value: Any) -> AirEngagementRuntimeInput:
    if not isinstance(value, AirEngagementRuntimeInput):
        raise TypeError("Air engagement runtime requires AirEngagementRuntimeInput")
    return value


__all__ = ["AirEngagementRuntimeInput", "AirScriptedEngagementRuntimeModel"]
