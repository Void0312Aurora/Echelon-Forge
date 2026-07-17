"""Shared component load/response projections for kill-chain diagnostics."""

from __future__ import annotations

import math
from typing import Any

from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.schema import (
    _finite_float,
)


COMPONENT_DETAIL_SCHEMA_VERSION = "a2.kill_chain_expectation_component_detail.v1"


def _finite_or_none(value: Any) -> float | None:
    out = _finite_float(value, float("nan"))
    return out if math.isfinite(out) else None


def _safe_ratio(numerator: Any, denominator: Any) -> float | None:
    top = _finite_or_none(numerator)
    bottom = _finite_or_none(denominator)
    if top is None or bottom is None or abs(bottom) <= 1.0e-12:
        return None
    return float(top) / float(bottom)


def _component_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("component_name", "") or ""),
        str(row.get("component_system", "") or ""),
        str(row.get("component_redundancy_group_id", "") or ""),
    )


def _component_load_rows(runtime_facade: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in list(
            dict(runtime_facade.get("warhead_load_field", {}) or {}).get(
                "component_loads",
                [],
            )
            or []
        )
        if isinstance(row, dict)
    ]


def _component_response_rows(runtime_facade: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in list(runtime_facade.get("component_responses", []) or [])
        if isinstance(row, dict)
    ]


def component_load_metrics(runtime_facade: dict[str, Any]) -> dict[str, Any]:
    loads = _component_load_rows(runtime_facade)
    effect_scales = [
        float(value)
        for value in (_finite_or_none(row.get("effect_scale")) for row in loads)
        if value is not None
    ]
    return {
        "component_load_row_count": len(loads),
        "strongest_component_effect_scale": max(effect_scales) if effect_scales else None,
        "weakest_component_effect_scale": min(effect_scales) if effect_scales else None,
    }


def component_response_metrics(runtime_facade: dict[str, Any]) -> dict[str, Any]:
    rows = _component_response_rows(runtime_facade)
    probabilities = [
        float(value)
        for value in (_finite_or_none(row.get("failure_probability")) for row in rows)
        if value is not None
    ]
    integrity_deltas = [
        float(value)
        for value in (_finite_or_none(row.get("integrity_delta")) for row in rows)
        if value is not None
    ]
    sampled_failure_count = 0
    max_probability_row: dict[str, Any] | None = None
    for row in rows:
        probability = _finite_or_none(row.get("failure_probability"))
        sample = _finite_or_none(row.get("failure_sample"))
        if probability is not None and sample is not None and sample <= probability:
            sampled_failure_count += 1
        if probability is not None and (
            max_probability_row is None
            or probability > float(max_probability_row.get("failure_probability", -1.0))
        ):
            max_probability_row = row
    if not rows:
        response_band = "no_response_rows"
    elif sampled_failure_count > 0:
        response_band = "sampled_failure_observed"
    elif probabilities:
        response_band = "observed_probability_only"
    else:
        response_band = "unclassified_component_response"
    return {
        "component_response_row_count": len(rows),
        "max_failure_probability": max(probabilities) if probabilities else None,
        "sampled_failure_count": int(sampled_failure_count),
        "min_integrity_delta": min(integrity_deltas) if integrity_deltas else None,
        "primary_failure_mode": (
            str(max_probability_row.get("failure_mode", "") or "")
            if max_probability_row is not None
            else ""
        ),
        "component_response_band": response_band,
    }


def _component_response_by_key(
    runtime_facade: dict[str, Any],
) -> dict[tuple[str, str, str], dict[str, Any]]:
    out: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in _component_response_rows(runtime_facade):
        out[_component_key(row)] = row
    return out


def _component_detail_rows(
    *,
    runtime_facade: dict[str, Any],
    r_effect_m: float | None,
) -> list[dict[str, Any]]:
    response_by_key = _component_response_by_key(runtime_facade)
    rows: list[dict[str, Any]] = []
    for load in _component_load_rows(runtime_facade):
        response = response_by_key.get(_component_key(load), {})
        failure_probability = _finite_or_none(response.get("failure_probability"))
        failure_sample = _finite_or_none(response.get("failure_sample"))
        sampled_failure = (
            failure_probability is not None
            and failure_sample is not None
            and failure_sample <= failure_probability
        )
        distance_m = _finite_or_none(load.get("distance_m"))
        rows.append(
            {
                "source_row_index": int(load.get("source_row_index", len(rows)) or 0),
                "component_name": str(load.get("component_name", "") or ""),
                "component_system": str(load.get("component_system", "") or ""),
                "component_redundancy_group_id": str(
                    load.get("component_redundancy_group_id", "") or ""
                ),
                "load_owner_stage": str(load.get("owner_stage", "") or ""),
                "response_owner_stage": str(response.get("owner_stage", "") or ""),
                "distance_m": distance_m,
                "rho_effect_component": _safe_ratio(distance_m, r_effect_m),
                "effect_scale": _finite_or_none(load.get("effect_scale")),
                "spatial_intersection_fraction": _finite_or_none(
                    load.get("spatial_intersection_fraction")
                ),
                "pattern_weight": _finite_or_none(load.get("pattern_weight")),
                "orientation_weight": _finite_or_none(load.get("orientation_weight")),
                "receiver_exposure_fraction": _finite_or_none(
                    load.get("receiver_exposure_fraction")
                ),
                "armor_transmission": _finite_or_none(load.get("armor_transmission")),
                "sampling_confidence": _finite_or_none(load.get("sampling_confidence")),
                "load_intensity_scale": _finite_or_none(
                    load.get("load_intensity_scale")
                ),
                "fragment_energy_j": _finite_or_none(load.get("fragment_energy_j")),
                "fragment_areal_density_per_m2": _finite_or_none(
                    load.get("fragment_areal_density_per_m2")
                ),
                "penetration_margin": _finite_or_none(load.get("penetration_margin")),
                "blast_overpressure_kpa": _finite_or_none(
                    load.get("blast_overpressure_kpa")
                ),
                "blast_impulse_kpa_ms": _finite_or_none(
                    load.get("blast_impulse_kpa_ms")
                ),
                "blast_scaled_distance_m_kg13": _finite_or_none(
                    load.get("blast_scaled_distance_m_kg13")
                ),
                "rod_cut_margin": _finite_or_none(load.get("rod_cut_margin")),
                "surface_incidence_cos": _finite_or_none(
                    load.get("surface_incidence_cos")
                ),
                "component_threshold_scale": _finite_or_none(
                    response.get("component_threshold_scale")
                ),
                "failure_probability": failure_probability,
                "failure_sample": failure_sample,
                "sampled_failure": bool(sampled_failure),
                "failure_probability_source": str(
                    response.get("failure_probability_source", "") or ""
                ),
                "failure_probability_calibrated": bool(
                    response.get("failure_probability_calibrated")
                ),
                "failure_mode": str(response.get("failure_mode", "") or ""),
                "failure_severity": _finite_or_none(response.get("failure_severity")),
                "integrity_before": _finite_or_none(response.get("integrity_before")),
                "integrity_after": _finite_or_none(response.get("integrity_after")),
                "integrity_delta": _finite_or_none(response.get("integrity_delta")),
                "owner_boundary_status": str(
                    response.get("owner_boundary_status", "") or ""
                ),
            }
        )
    return rows


def _component_detail_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    effect_rows = [
        row for row in rows if _finite_or_none(row.get("effect_scale")) is not None
    ]
    probability_rows = [
        row
        for row in rows
        if _finite_or_none(row.get("failure_probability")) is not None
    ]
    sampled_rows = [row for row in rows if bool(row.get("sampled_failure"))]
    strongest_load = max(
        effect_rows,
        key=lambda row: float(row.get("effect_scale") or 0.0),
        default=None,
    )
    strongest_response = max(
        probability_rows,
        key=lambda row: float(row.get("failure_probability") or 0.0),
        default=None,
    )
    return {
        "schema_version": COMPONENT_DETAIL_SCHEMA_VERSION,
        "projection_source": "runtime_facade_component_load_and_response_rows",
        "component_detail_row_count": len(rows),
        "matched_component_response_row_count": len(probability_rows),
        "sampled_failure_detail_count": len(sampled_rows),
        "strongest_load_component": (
            {
                "component_name": str(strongest_load.get("component_name", "") or ""),
                "component_system": str(strongest_load.get("component_system", "") or ""),
                "effect_scale": _finite_or_none(strongest_load.get("effect_scale")),
                "rho_effect_component": _finite_or_none(
                    strongest_load.get("rho_effect_component")
                ),
            }
            if strongest_load is not None
            else None
        ),
        "max_probability_component": (
            {
                "component_name": str(
                    strongest_response.get("component_name", "") or ""
                ),
                "component_system": str(
                    strongest_response.get("component_system", "") or ""
                ),
                "failure_probability": _finite_or_none(
                    strongest_response.get("failure_probability")
                ),
                "effect_scale": _finite_or_none(strongest_response.get("effect_scale")),
                "sampled_failure": bool(strongest_response.get("sampled_failure")),
            }
            if strongest_response is not None
            else None
        ),
    }


def empty_component_detail(
    *,
    r_effect_variant: str,
    r_effect_m: float | None,
) -> dict[str, Any]:
    return {
        "schema_version": COMPONENT_DETAIL_SCHEMA_VERSION,
        "R_effect_variant": str(r_effect_variant),
        "R_effect_m": r_effect_m,
        "summary": _component_detail_summary([]),
        "component_rows": [],
    }


def component_detail_from_runtime_facade(
    *,
    runtime_facade: dict[str, Any],
    r_effect_variant: str,
    r_effect_m: float | None,
) -> dict[str, Any]:
    rows = _component_detail_rows(
        runtime_facade=runtime_facade,
        r_effect_m=r_effect_m,
    )
    return {
        "schema_version": COMPONENT_DETAIL_SCHEMA_VERSION,
        "R_effect_variant": str(r_effect_variant),
        "R_effect_m": r_effect_m,
        "summary": _component_detail_summary(rows),
        "component_rows": rows,
    }
