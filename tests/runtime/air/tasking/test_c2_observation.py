from __future__ import annotations

from types import SimpleNamespace

from python.tasking_contracts.air.tasking.c2_observation import (
    C2RecoveryReadinessInput,
    C2ReportTypeCodes,
    C2StationMetrics,
    assess_c2_report,
    compute_station_metrics,
    recovery_window_ready,
)


def _task(**overrides):
    values = {
        "anchor_x_m": 1000.0,
        "anchor_y_m": 0.0,
        "station_radius_m": 1000.0,
        "altitude_block_min_m": 900.0,
        "altitude_block_max_m": 1100.0,
        "speed_min_mps": 90.0,
        "speed_max_mps": 110.0,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _report(report_type: int, *, active: bool = True):
    return SimpleNamespace(active=active, report_type=report_type)


def test_station_assessment_is_a_pure_projection() -> None:
    result = compute_station_metrics(
        truth=SimpleNamespace(x=1000.0, y=0.0),
        inst=SimpleNamespace(alt_baro=1000.0, ias=100.0),
        task=_task(),
        radius_scale=1.25,
        altitude_slack_m=10.0,
        speed_slack_mps=5.0,
    )

    assert result == C2StationMetrics(True, 0.0, True, True)


def test_report_assessment_keeps_invalid_bingo_and_station_reports_distinct() -> None:
    codes = C2ReportTypeCodes(none=0, on_station=1, rtb=2, bingo=3, unable=4, wilco=5)
    outside = C2StationMetrics(False, 2000.0, True, True)

    station = assess_c2_report(
        _report(codes.on_station),
        report_codes=codes,
        station_metrics=outside,
        fuel_margin_fraction=1.0,
    )
    bingo = assess_c2_report(
        _report(codes.bingo),
        report_codes=codes,
        station_metrics=outside,
        fuel_margin_fraction=0.25,
    )

    assert station.valid is False
    assert station.reason == "station_not_reached"
    assert bingo.valid is False
    assert bingo.reason == "fuel_not_bingo"


def test_recovery_gate_requires_declared_geometry() -> None:
    base = dict(
        ils_valid=True,
        localizer_abs=0.1,
        glide_slope_abs=0.1,
        dme_m=10000.0,
        altitude_agl_m=500.0,
        runway_frame_valid=True,
        runway_along_m=0.0,
        runway_cross_m=0.0,
        runway_heading_error_deg=5.0,
        max_dme_m=18000.0,
        max_altitude_agl_m=1800.0,
        max_localizer_abs=0.8,
        max_glide_slope_abs=1.5,
        require_runway_frame=True,
        min_runway_along_m=-1000.0,
        max_runway_cross_abs_m=3500.0,
        max_runway_heading_error_deg=85.0,
    )

    assert recovery_window_ready(C2RecoveryReadinessInput(**base)) is True
    assert recovery_window_ready(
        C2RecoveryReadinessInput(**{**base, "runway_cross_m": 4000.0})
    ) is False
