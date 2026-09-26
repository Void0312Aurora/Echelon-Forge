"""Deterministic, RL-independent Air tactical engagement planning.

This module owns the first deliberative layer above the maintained flight
controllers.  It evaluates a small, explicit set of kinematic posture
candidates from the declared Air track/mission view, filters candidates by
the C2/ROE and track-freshness constraints, and selects the highest-scoring
candidate with a weighted utility function.  It is deliberately a bounded
receding-horizon proxy: it does not read world truth, call the simulator, or
claim a calibrated weapon envelope.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Mapping

import numpy as np

from .weapons import AirWeaponEnvelope
from .contracts import AirPlanningContext, AirTacticalDecision


def _finite(value: float, *, name: str, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return float(default)
    return number if isfinite(number) else float(default)


def _clip(value: float, low: float, high: float) -> float:
    return float(np.clip(float(value), float(low), float(high)))


@dataclass(frozen=True)
class AirEngagementPlannerConfig:
    """Policy parameters for the bounded candidate evaluator.

    The values are policy parameters, not a database weapon model.  A later
    maintained platform profile may replace them with source-backed values.
    """

    preferred_range_m: float = 16000.0
    preferred_range_half_width_m: float = 7000.0
    legal_min_range_m: float = 8000.0
    legal_max_range_m: float = 30000.0
    max_track_age_s: float = 5.0
    desired_closing_speed_mps: float = 250.0
    planning_horizon_s: float = 5.0
    commit_utility_threshold: float = 0.50
    range_weight: float = 0.42
    geometry_weight: float = 0.28
    closure_weight: float = 0.15
    freshness_weight: float = 0.15
    max_bearing_deg: float = 45.0
    max_elevation_deg: float = 20.0
    max_guidance_roll: float = 0.08
    max_guidance_pitch: float = 0.05
    max_guidance_throttle: float = 0.04
    guidance_weight: float = 0.10
    weapon_envelope: AirWeaponEnvelope | None = None

    def __post_init__(self) -> None:
        positive = (
            "preferred_range_m",
            "preferred_range_half_width_m",
            "legal_min_range_m",
            "legal_max_range_m",
            "max_track_age_s",
            "desired_closing_speed_mps",
            "planning_horizon_s",
            "max_bearing_deg",
            "max_elevation_deg",
        )
        for name in positive:
            value = _finite(getattr(self, name), name=name, default=-1.0)
            if value <= 0.0:
                raise ValueError(f"{name} must be finite and positive")
        if self.legal_min_range_m >= self.legal_max_range_m:
            raise ValueError("legal_min_range_m must be lower than legal_max_range_m")
        if not 0.0 < float(self.commit_utility_threshold) <= 1.0:
            raise ValueError("commit_utility_threshold must be in (0, 1]")
        weights = (
            float(self.range_weight),
            float(self.geometry_weight),
            float(self.closure_weight),
            float(self.freshness_weight),
            float(self.guidance_weight),
        )
        if any(weight < 0.0 for weight in weights) or sum(weights) <= 0.0:
            raise ValueError("planner utility weights must be non-negative and non-zero")
        limits = (self.max_guidance_roll, self.max_guidance_pitch, self.max_guidance_throttle)
        if any(float(limit) < 0.0 for limit in limits):
            raise ValueError("guidance limits must be non-negative")


@dataclass(frozen=True)
class AirEngagementPlan:
    """Auditable result of one tactical planning cycle."""

    mode: str
    selected_candidate: str
    fire_recommended: bool
    target_range_m: float
    target_bearing_deg: float
    target_elevation_deg: float
    closing_speed_mps: float
    track_age_s: float
    range_score: float
    geometry_score: float
    closure_score: float
    freshness_score: float
    guidance_score: float
    weapon_envelope_id: str | None
    current_utility: float
    selected_utility: float
    guidance_roll: float
    guidance_pitch: float
    guidance_throttle: float
    reason_codes: tuple[str, ...]
    candidate_utilities: tuple[tuple[str, float], ...]

    def as_tactical_decision(self) -> AirTacticalDecision:
        """Project the rich planner record onto the stable strategy contract."""

        return AirTacticalDecision(
            mode=self.mode,
            selected_candidate=self.selected_candidate,
            fire_recommended=self.fire_recommended,
            guidance_roll=self.guidance_roll,
            guidance_pitch=self.guidance_pitch,
            guidance_throttle=self.guidance_throttle,
            reason_codes=self.reason_codes,
            diagnostics=self.as_dict(),
        )

    def as_dict(self) -> dict[str, Any]:
        result = {
            "mode": self.mode,
            "selected_candidate": self.selected_candidate,
            "fire_recommended": self.fire_recommended,
            "target_range_m": self.target_range_m,
            "target_bearing_deg": self.target_bearing_deg,
            "target_elevation_deg": self.target_elevation_deg,
            "closing_speed_mps": self.closing_speed_mps,
            "track_age_s": self.track_age_s,
            "range_score": self.range_score,
            "geometry_score": self.geometry_score,
            "closure_score": self.closure_score,
            "freshness_score": self.freshness_score,
            "guidance_score": self.guidance_score,
            "weapon_envelope_id": self.weapon_envelope_id,
            "current_utility": self.current_utility,
            "selected_utility": self.selected_utility,
            "guidance_roll": self.guidance_roll,
            "guidance_pitch": self.guidance_pitch,
            "guidance_throttle": self.guidance_throttle,
            "reason_codes": list(self.reason_codes),
            "candidate_utilities": {name: score for name, score in self.candidate_utilities},
        }
        return result


class AirEngagementPlanner:
    """Choose a bounded tactical posture with deterministic receding replans."""

    def __init__(self, config: AirEngagementPlannerConfig | None = None) -> None:
        self.config = config or AirEngagementPlannerConfig()
        self.last_plan: AirEngagementPlan | None = None

    def reset(self) -> None:
        self.last_plan = None

    def decide(self, *, context: AirPlanningContext) -> AirTacticalDecision:
        """Plan from a normalized context and return the stable decision DTO."""

        return self.plan_context(context=context).as_tactical_decision()

    def plan_context(self, *, context: AirPlanningContext) -> AirEngagementPlan:
        return self.plan(
            target_contact_present=context.target_contact_present,
            authorization_to_fire=context.authorization_to_fire,
            fire_mask_open=context.fire_mask_open,
            launch_window_open=context.launch_window_open,
            quality_window_ready=context.quality_window_ready,
            pending_assessment=context.pending_assessment,
            shot_budget_remaining=context.shot_budget_remaining,
            target_range_m=context.target_range_m,
            target_track_age_s=context.target_track_age_s,
            contact_bearing_deg=context.contact_bearing_deg,
            contact_elevation_deg=context.contact_elevation_deg,
            closing_speed_mps=context.closing_speed_mps,
        )

    def plan(
        self,
        *,
        target_contact_present: bool,
        authorization_to_fire: bool,
        fire_mask_open: bool,
        launch_window_open: bool,
        quality_window_ready: bool,
        pending_assessment: bool,
        shot_budget_remaining: float,
        target_range_m: float = 0.0,
        target_track_age_s: float = 0.0,
        contact_bearing_deg: float = 0.0,
        contact_elevation_deg: float = 0.0,
        closing_speed_mps: float = 0.0,
    ) -> AirEngagementPlan:
        cfg = self.config
        distance = max(0.0, _finite(target_range_m, name="target_range_m"))
        bearing = _finite(contact_bearing_deg, name="contact_bearing_deg")
        elevation = _finite(contact_elevation_deg, name="contact_elevation_deg")
        closing = _finite(closing_speed_mps, name="closing_speed_mps")
        age = max(0.0, _finite(target_track_age_s, name="target_track_age_s"))
        range_known = distance > 0.0
        geometry_known = range_known or abs(bearing) > 1.0e-6 or abs(elevation) > 1.0e-6

        legal = bool(
            target_contact_present
            and authorization_to_fire
            and fire_mask_open
            and launch_window_open
            and float(shot_budget_remaining) > 0.5
            and not pending_assessment
        )
        freshness = 0.5 if not range_known and age <= 0.0 else _clip(1.0 - age / cfg.max_track_age_s, 0.0, 1.0)
        range_score = self._range_score(distance) if range_known else 0.5
        geometry_score = self._geometry_score(bearing, elevation) if geometry_known else 0.5
        # Older C2/ROE observations may omit the contact token.  Preserve a
        # neutral closure contribution in that compatibility case; a known
        # non-closing track is scored as zero.
        closure_score = (
            0.5
            if not range_known and abs(closing) <= 1.0e-6
            else _clip(closing / cfg.desired_closing_speed_mps, 0.0, 1.0)
        )
        guidance_score = self._guidance_score(
            distance,
            bearing,
            range_known=range_known,
            geometry_known=geometry_known,
        )
        current_utility = self._utility(range_score, geometry_score, closure_score, freshness, guidance_score)

        candidates = self._candidate_states(
            distance=distance,
            bearing=bearing,
            elevation=elevation,
            closing=closing,
            range_known=range_known,
        )
        scored: list[tuple[str, float, tuple[float, float, float, float]]] = []
        for name, state in candidates.items():
            candidate_range, candidate_bearing, candidate_elevation, candidate_closing = state
            utility = self._utility(
                self._range_score(candidate_range) if range_known else 0.5,
                self._geometry_score(candidate_bearing, candidate_elevation),
                _clip(candidate_closing / cfg.desired_closing_speed_mps, 0.0, 1.0),
                freshness,
                self._guidance_score(
                    candidate_range,
                    candidate_bearing,
                    range_known=range_known,
                    geometry_known=geometry_known,
                ),
            )
            scored.append((name, utility, state))
        scored.sort(key=lambda row: (-row[1], row[0]))
        selected_name, selected_utility, selected_state = scored[0]

        reasons: list[str] = []
        if not target_contact_present:
            mode = "search"
            selected_name = "hold"
            selected_utility = current_utility
            guidance = (0.0, 0.0, 0.0)
            reasons.append("no_target_contact")
        elif not authorization_to_fire:
            mode = "hold_authority"
            guidance = self._guidance_for_state(selected_state, bearing, elevation, closing)
            reasons.append("fire_authority_closed")
        elif pending_assessment:
            mode = "assess"
            selected_name = "hold"
            selected_utility = current_utility
            guidance = (0.0, 0.0, 0.0)
            reasons.append("pending_assessment")
        elif legal and current_utility >= cfg.commit_utility_threshold and (
            cfg.weapon_envelope is None or guidance_score > 0.0
        ):
            mode = "commit"
            selected_name = "hold"
            selected_utility = current_utility
            guidance = (0.0, 0.0, 0.0)
            reasons.append("legal_window_open")
            if quality_window_ready:
                reasons.append("quality_window_ready")
            else:
                # Quality age is an evidence-strength signal, not an
                # additional release gate.  The native fire gate remains the
                # authority for legal and weapon-state acceptance.
                reasons.append("quality_window_not_ready")
        else:
            mode = "reposition"
            guidance = self._guidance_for_state(selected_state, bearing, elevation, closing)
            if not fire_mask_open or not launch_window_open:
                reasons.append("window_closed")
            if current_utility < cfg.commit_utility_threshold:
                reasons.append("utility_below_commit_threshold")
            if not quality_window_ready:
                reasons.append("quality_window_not_ready")

        fire_recommended = bool(mode == "commit" and legal)
        if not range_known:
            reasons.append("range_geometry_unavailable")
        if cfg.weapon_envelope is not None:
            if guidance_score <= 0.0:
                reasons.append("weapon_guidance_opportunity_closed")
            else:
                reasons.append("weapon_guidance_opportunity_available")
        plan = AirEngagementPlan(
            mode=mode,
            selected_candidate=selected_name,
            fire_recommended=fire_recommended,
            target_range_m=distance,
            target_bearing_deg=bearing,
            target_elevation_deg=elevation,
            closing_speed_mps=closing,
            track_age_s=age,
            range_score=float(range_score),
            geometry_score=float(geometry_score),
            closure_score=float(closure_score),
            freshness_score=float(freshness),
            guidance_score=float(guidance_score),
            weapon_envelope_id=None if cfg.weapon_envelope is None else cfg.weapon_envelope.weapon_id,
            current_utility=float(current_utility),
            selected_utility=float(selected_utility),
            guidance_roll=float(guidance[0]),
            guidance_pitch=float(guidance[1]),
            guidance_throttle=float(guidance[2]),
            reason_codes=tuple(reasons),
            candidate_utilities=tuple((name, float(score)) for name, score, _ in scored),
        )
        self.last_plan = plan
        return plan

    def apply_guidance(self, action: np.ndarray, plan: AirEngagementPlan) -> np.ndarray:
        """Apply only bounded low-level biases; transport and fire bits stay separate."""

        result = np.asarray(action, dtype=np.float32).reshape(-1).copy()
        if result.size >= 4 and plan.mode == "reposition":
            result[0] = _clip(result[0] + plan.guidance_pitch, -1.0, 1.0)
            result[1] = _clip(result[1] + plan.guidance_roll, -1.0, 1.0)
            result[3] = _clip(result[3] + plan.guidance_throttle, 0.0, 1.0)
        return result

    def apply_decision_guidance(self, action: np.ndarray, decision: AirTacticalDecision) -> np.ndarray:
        """Apply the bounded guidance carried by the stable decision DTO."""

        result = np.asarray(action, dtype=np.float32).reshape(-1).copy()
        if result.size >= 4 and decision.mode == "reposition":
            result[0] = _clip(result[0] + decision.guidance_pitch, -1.0, 1.0)
            result[1] = _clip(result[1] + decision.guidance_roll, -1.0, 1.0)
            result[3] = _clip(result[3] + decision.guidance_throttle, 0.0, 1.0)
        return result

    def _range_score(self, distance: float) -> float:
        cfg = self.config
        if distance < cfg.legal_min_range_m or distance > cfg.legal_max_range_m:
            return 0.0
        return _clip(1.0 - abs(distance - cfg.preferred_range_m) / cfg.preferred_range_half_width_m, 0.0, 1.0)

    def _geometry_score(self, bearing: float, elevation: float) -> float:
        cfg = self.config
        bearing_score = _clip(1.0 - abs(bearing) / cfg.max_bearing_deg, 0.0, 1.0)
        elevation_score = _clip(1.0 - abs(elevation) / cfg.max_elevation_deg, 0.0, 1.0)
        return 0.7 * bearing_score + 0.3 * elevation_score

    def _utility(
        self,
        range_score: float,
        geometry_score: float,
        closure_score: float,
        freshness: float,
        guidance_score: float,
    ) -> float:
        cfg = self.config
        total = (
            cfg.range_weight
            + cfg.geometry_weight
            + cfg.closure_weight
            + cfg.freshness_weight
            + cfg.guidance_weight
        )
        return float(
            (
                cfg.range_weight * range_score
                + cfg.geometry_weight * geometry_score
                + cfg.closure_weight * closure_score
                + cfg.freshness_weight * freshness
                + cfg.guidance_weight * guidance_score
            )
            / total
        )

    def _guidance_score(
        self,
        distance: float,
        bearing: float,
        *,
        range_known: bool,
        geometry_known: bool,
    ) -> float:
        envelope = self.config.weapon_envelope
        if envelope is None:
            return 0.5
        score = 0.5
        if range_known:
            guidance_range = envelope.guidance_range_m
            if guidance_range is not None:
                score = 1.0 if distance <= guidance_range else 0.0
            if envelope.min_launch_range_m is not None and distance < envelope.min_launch_range_m:
                score = 0.0
        if geometry_known and envelope.max_launch_off_boresight_deg is not None:
            if abs(bearing) > envelope.max_launch_off_boresight_deg:
                score = 0.0
        return float(score)

    def _candidate_states(
        self,
        *,
        distance: float,
        bearing: float,
        elevation: float,
        closing: float,
        range_known: bool,
    ) -> Mapping[str, tuple[float, float, float, float]]:
        cfg = self.config
        horizon = cfg.planning_horizon_s
        if range_known:
            hold_range = distance
            intercept_range = distance - max(0.0, closing) * horizon
            reposition_range = distance + (cfg.preferred_range_m - distance) * 0.35
        else:
            hold_range = cfg.preferred_range_m
            intercept_range = hold_range
            reposition_range = hold_range
        return {
            "hold": (hold_range, bearing, elevation, closing),
            "intercept": (
                max(0.0, intercept_range),
                bearing * 0.45,
                elevation * 0.65,
                max(closing, cfg.desired_closing_speed_mps * 0.85),
            ),
            "reposition": (
                max(0.0, reposition_range),
                bearing * 0.60,
                elevation * 0.75,
                max(closing, cfg.desired_closing_speed_mps * 0.65),
            ),
        }

    def _guidance_for_state(
        self,
        state: tuple[float, float, float, float],
        current_bearing: float,
        current_elevation: float,
        current_closing: float,
    ) -> tuple[float, float, float]:
        _, desired_bearing, desired_elevation, desired_closing = state
        cfg = self.config
        roll = _clip(desired_bearing / cfg.max_bearing_deg, -1.0, 1.0) * cfg.max_guidance_roll
        pitch = _clip(desired_elevation / cfg.max_elevation_deg, -1.0, 1.0) * cfg.max_guidance_pitch
        throttle = _clip(
            (desired_closing - current_closing) / cfg.desired_closing_speed_mps,
            -1.0,
            1.0,
        ) * cfg.max_guidance_throttle
        return roll, pitch, throttle


__all__ = [
    "AirWeaponEnvelope",
    "AirEngagementPlan",
    "AirEngagementPlanner",
    "AirEngagementPlannerConfig",
    "AirPlanningContext",
    "AirTacticalDecision",
]
