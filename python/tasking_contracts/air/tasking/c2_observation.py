"""Pure information assessment helpers for the scripted Air C2 line.

The functions in this module consume declared object attributes and scalar
measurements supplied by an adapter. They do not read a loader, import an RL
runtime, resolve compiled enums, or mutate tasking DTOs. This keeps the
decision algorithms replaceable while the runtime adapter remains responsible
for obtaining observations and projecting the result into the simulation.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any


@dataclass(frozen=True)
class C2StationMetrics:
    """Normalized station-entry assessment."""

    near_station: bool
    anchor_dist_m: float
    altitude_in_block: bool
    speed_in_block: bool


def compute_station_metrics(
    *,
    truth: Any,
    inst: Any,
    task: Any,
    radius_scale: float,
    altitude_slack_m: float,
    speed_slack_mps: float,
) -> C2StationMetrics:
    """Evaluate whether an aircraft is inside the declared station gate."""

    if truth is None or inst is None:
        return C2StationMetrics(False, float("inf"), False, False)

    anchor_x = float(getattr(task, "anchor_x_m", 0.0) if task is not None else 0.0)
    anchor_y = float(getattr(task, "anchor_y_m", 0.0) if task is not None else 0.0)
    dx = anchor_x - float(getattr(truth, "x", 0.0))
    dy = anchor_y - float(getattr(truth, "y", 0.0))
    anchor_dist_m = float(math.hypot(dx, dy))
    station_radius_m = float(
        max(1000.0, getattr(task, "station_radius_m", 12000.0) if task is not None else 12000.0)
    )
    radius_gate = anchor_dist_m <= station_radius_m * max(1.0, float(radius_scale))

    altitude_in_block = True
    speed_in_block = True
    if task is not None:
        alt_baro = float(getattr(inst, "alt_baro", 0.0))
        ias = float(getattr(inst, "ias", 0.0))
        alt_lo = float(getattr(task, "altitude_block_min_m", 0.0))
        alt_hi = float(getattr(task, "altitude_block_max_m", 0.0))
        spd_lo = float(getattr(task, "speed_min_mps", 0.0))
        spd_hi = float(getattr(task, "speed_max_mps", 0.0))
        if alt_hi > alt_lo + 1.0:
            altitude_in_block = (alt_lo - float(altitude_slack_m)) <= alt_baro <= (
                alt_hi + float(altitude_slack_m)
            )
        if spd_hi > spd_lo + 1.0:
            speed_in_block = (spd_lo - float(speed_slack_mps)) <= ias <= (
                spd_hi + float(speed_slack_mps)
            )

    return C2StationMetrics(
        near_station=bool(radius_gate and altitude_in_block and speed_in_block),
        anchor_dist_m=anchor_dist_m,
        altitude_in_block=bool(altitude_in_block),
        speed_in_block=bool(speed_in_block),
    )


@dataclass(frozen=True)
class C2ReportTypeCodes:
    """Domain enum values supplied by the runtime adapter."""

    none: int
    on_station: int
    rtb: int
    bingo: int
    unable: int
    wilco: int


@dataclass(frozen=True)
class C2ReportAssessment:
    valid: bool
    reason: str


def assess_c2_report(
    report: Any,
    *,
    report_codes: C2ReportTypeCodes,
    station_metrics: C2StationMetrics,
    fuel_margin_fraction: float,
) -> C2ReportAssessment:
    """Assess one pilot report using only declared state projections."""

    if report is None or not bool(getattr(report, "active", False)):
        return C2ReportAssessment(False, "no_report")

    report_type = int(getattr(report, "report_type", report_codes.none))
    if report_type == int(report_codes.on_station):
        return C2ReportAssessment(
            bool(station_metrics.near_station),
            "on_station" if station_metrics.near_station else "station_not_reached",
        )
    if report_type == int(report_codes.rtb):
        return C2ReportAssessment(True, "rtb_report")
    if report_type == int(report_codes.bingo):
        margin = float(fuel_margin_fraction)
        return C2ReportAssessment(bool(margin <= 0.15), "bingo_report" if margin <= 0.15 else "fuel_not_bingo")
    if report_type == int(report_codes.unable):
        return C2ReportAssessment(True, "unable_report")
    if report_type == int(report_codes.wilco):
        return C2ReportAssessment(True, "wilco_report")
    return C2ReportAssessment(False, "unsupported_report")


@dataclass(frozen=True)
class C2RecoveryReadinessInput:
    """Declared geometry and threshold values needed by the recovery gate."""

    ils_valid: bool
    localizer_abs: float
    glide_slope_abs: float
    dme_m: float
    altitude_agl_m: float
    runway_frame_valid: bool
    runway_along_m: float
    runway_cross_m: float
    runway_heading_error_deg: float
    max_dme_m: float
    max_altitude_agl_m: float
    max_localizer_abs: float
    max_glide_slope_abs: float
    require_runway_frame: bool
    min_runway_along_m: float
    max_runway_cross_abs_m: float
    max_runway_heading_error_deg: float


def recovery_window_ready(state: C2RecoveryReadinessInput) -> bool:
    """Return whether the declared recovery geometry satisfies all gates."""

    if state.require_runway_frame and not state.runway_frame_valid:
        return False
    if state.runway_frame_valid:
        if state.runway_along_m < state.min_runway_along_m:
            return False
        if abs(state.runway_cross_m) > state.max_runway_cross_abs_m:
            return False
    return bool(
        state.ils_valid
        and state.dme_m <= state.max_dme_m
        and state.altitude_agl_m <= state.max_altitude_agl_m
        and state.localizer_abs <= state.max_localizer_abs
        and state.glide_slope_abs <= state.max_glide_slope_abs
        and state.runway_heading_error_deg <= state.max_runway_heading_error_deg
    )


__all__ = [
    "C2RecoveryReadinessInput",
    "C2ReportAssessment",
    "C2ReportTypeCodes",
    "C2StationMetrics",
    "assess_c2_report",
    "compute_station_metrics",
    "recovery_window_ready",
]
