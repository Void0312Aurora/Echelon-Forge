"""Conservative post-launch assessment for the independent scripted Air line."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Mapping

from .contracts import AirAssessmentInput


AIR_ASSESSMENT_IDLE = "idle"
AIR_ASSESSMENT_IN_FLIGHT = "in_flight"
AIR_ASSESSMENT_TERMINAL_OBSERVED = "terminal_observed"
AIR_ASSESSMENT_REATTACK_READY = "reattack_ready"
AIR_ASSESSMENT_TRACK_LOST = "track_lost"
AIR_ASSESSMENT_TRACK_UNAVAILABLE = "track_unavailable"


def _nonnegative(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return number if isfinite(number) and number >= 0.0 else 0.0


@dataclass(frozen=True)
class AirPostLaunchAssessmentReport:
    """Auditable result of one post-launch observation cycle."""

    state: str
    outcome: str
    confidence: float
    allow_reattack: bool
    blocks_fire: bool
    release_executed: bool
    pending_assessment: bool
    target_contact_present: bool
    own_missiles_in_flight_count: float
    target_track_age_s: float
    reason_codes: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "outcome": self.outcome,
            "confidence": self.confidence,
            "allow_reattack": self.allow_reattack,
            "blocks_fire": self.blocks_fire,
            "release_executed": self.release_executed,
            "pending_assessment": self.pending_assessment,
            "target_contact_present": self.target_contact_present,
            "own_missiles_in_flight_count": self.own_missiles_in_flight_count,
            "target_track_age_s": self.target_track_age_s,
            "reason_codes": list(self.reason_codes),
        }


class AirPostLaunchAssessment:
    """Track release evidence without inventing terminal or kill evidence.

    An explicit ``target_effect_observed`` or ``target_mission_killed`` event
    is required for ``terminal_observed``. A missing contact is never treated
    as a hit. ``reattack_ready`` is intentionally an inconclusive state: it
    only means the declared assessment gate is clear and another shot may be
    requested if authority and budget also permit it.
    """

    def __init__(self, *, max_track_age_s: float = 5.0) -> None:
        if not isfinite(float(max_track_age_s)) or float(max_track_age_s) <= 0.0:
            raise ValueError("max_track_age_s must be finite and positive")
        self.max_track_age_s = float(max_track_age_s)
        self.reset()

    def reset(self) -> None:
        self._release_seen = False
        self._state = AIR_ASSESSMENT_IDLE
        self._last_report = AirPostLaunchAssessmentReport(
            state=AIR_ASSESSMENT_IDLE,
            outcome="none",
            confidence=0.0,
            allow_reattack=False,
            blocks_fire=False,
            release_executed=False,
            pending_assessment=False,
            target_contact_present=False,
            own_missiles_in_flight_count=0.0,
            target_track_age_s=0.0,
            reason_codes=(),
        )

    @property
    def last_report(self) -> AirPostLaunchAssessmentReport:
        return self._last_report

    def assess(self, *, inputs: AirAssessmentInput) -> AirPostLaunchAssessmentReport:
        """Assess typed evidence without exposing the legacy event mapping."""

        event_info = {
            "release_executed": inputs.release_executed,
            "target_effect_observed": inputs.target_effect_observed,
            "target_mission_killed": inputs.target_mission_killed,
            "target_destroyed": inputs.target_destroyed,
        }
        return self.observe(
            event_info=event_info,
            pending_assessment=inputs.pending_assessment,
            target_contact_present=inputs.target_contact_present,
            own_missiles_in_flight_count=inputs.own_missiles_in_flight_count,
            shot_budget_remaining=inputs.shot_budget_remaining,
            target_track_age_s=inputs.target_track_age_s,
            dt_s=inputs.dt_s,
        )

    def observe_input(self, *, inputs: AirAssessmentInput) -> AirPostLaunchAssessmentReport:
        """Compatibility alias for assessor protocol implementations."""

        return self.assess(inputs=inputs)

    def observe(
        self,
        *,
        event_info: Mapping[str, Any] | None = None,
        pending_assessment: bool,
        target_contact_present: bool,
        own_missiles_in_flight_count: float = 0.0,
        shot_budget_remaining: float = 0.0,
        target_track_age_s: float = 0.0,
        dt_s: float = 0.0,
    ) -> AirPostLaunchAssessmentReport:
        info = event_info if isinstance(event_info, Mapping) else {}
        release_executed = bool(info.get("release_executed", False))
        explicit_effect = bool(
            info.get("target_effect_observed", False)
            or info.get("target_mission_killed", False)
            or info.get("target_destroyed", False)
        )
        pending = bool(pending_assessment)
        contact = bool(target_contact_present)
        in_flight = _nonnegative(own_missiles_in_flight_count)
        track_age = _nonnegative(target_track_age_s)
        budget = _nonnegative(shot_budget_remaining)
        if release_executed:
            self._release_seen = True
        if not self._release_seen:
            return self._record(
                state=AIR_ASSESSMENT_IDLE,
                outcome="none",
                confidence=0.0,
                allow_reattack=False,
                blocks_fire=False,
                release_executed=release_executed,
                pending_assessment=pending,
                target_contact_present=contact,
                own_missiles_in_flight_count=in_flight,
                target_track_age_s=track_age,
                reason_codes=(),
            )
        if explicit_effect:
            return self._record(
                state=AIR_ASSESSMENT_TERMINAL_OBSERVED,
                outcome="hit_evidence",
                confidence=1.0,
                allow_reattack=False,
                blocks_fire=True,
                release_executed=release_executed,
                pending_assessment=pending,
                target_contact_present=contact,
                own_missiles_in_flight_count=in_flight,
                target_track_age_s=track_age,
                reason_codes=("explicit_target_effect",),
            )
        if pending or in_flight > 0.5:
            return self._record(
                state=AIR_ASSESSMENT_IN_FLIGHT,
                outcome="pending",
                confidence=0.0,
                allow_reattack=False,
                blocks_fire=True,
                release_executed=release_executed,
                pending_assessment=pending,
                target_contact_present=contact,
                own_missiles_in_flight_count=in_flight,
                target_track_age_s=track_age,
                reason_codes=("assessment_pending" if pending else "missile_in_flight",),
            )
        if not contact:
            return self._record(
                state=AIR_ASSESSMENT_TRACK_LOST,
                outcome="inconclusive",
                confidence=0.0,
                allow_reattack=False,
                blocks_fire=True,
                release_executed=release_executed,
                pending_assessment=pending,
                target_contact_present=contact,
                own_missiles_in_flight_count=in_flight,
                target_track_age_s=track_age,
                reason_codes=("target_contact_lost", "no_terminal_effect_evidence"),
            )
        if track_age > self.max_track_age_s:
            return self._record(
                state=AIR_ASSESSMENT_TRACK_UNAVAILABLE,
                outcome="inconclusive",
                confidence=0.0,
                allow_reattack=False,
                blocks_fire=True,
                release_executed=release_executed,
                pending_assessment=pending,
                target_contact_present=contact,
                own_missiles_in_flight_count=in_flight,
                target_track_age_s=track_age,
                reason_codes=("target_track_stale", "no_terminal_effect_evidence"),
            )
        allow_reattack = budget > 0.5
        reasons = ["no_terminal_effect_evidence"]
        if not allow_reattack:
            reasons.append("shot_budget_exhausted")
        return self._record(
            state=AIR_ASSESSMENT_REATTACK_READY,
            outcome="inconclusive",
            confidence=0.0,
            allow_reattack=allow_reattack,
            blocks_fire=False,
            release_executed=release_executed,
            pending_assessment=pending,
            target_contact_present=contact,
            own_missiles_in_flight_count=in_flight,
            target_track_age_s=track_age,
            reason_codes=tuple(reasons),
        )

    def _record(self, **values: Any) -> AirPostLaunchAssessmentReport:
        report = AirPostLaunchAssessmentReport(**values)
        self._state = report.state
        self._last_report = report
        return report


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
