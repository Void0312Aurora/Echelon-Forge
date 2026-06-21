"""Decoupled lethality-chain stage abstractions for process diagnostics."""

from __future__ import annotations

import math
from collections import Counter
from typing import Any

from tools.diagnostics import lethality_chain_contract as chain_contract
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.schema import (
    _finite_float,
)


ABSTRACTION_SCHEMA_VERSION = "kill_chain_stage_abstraction.v1"

ABSTRACTION_APPROACH = "approach"
ABSTRACTION_FUZE_DECISION = "fuze_decision"
ABSTRACTION_WARHEAD_LOAD_FIELD = "warhead_load_field"
ABSTRACTION_COMPONENT_RESPONSE = "component_response"
ABSTRACTION_CONSEQUENCE_PROJECTION = "consequence_projection"

ABSTRACTION_STAGES = (
    ABSTRACTION_APPROACH,
    ABSTRACTION_FUZE_DECISION,
    ABSTRACTION_WARHEAD_LOAD_FIELD,
    ABSTRACTION_COMPONENT_RESPONSE,
    ABSTRACTION_CONSEQUENCE_PROJECTION,
)


def _stage_present(row: dict[str, Any] | None) -> bool:
    return bool(row) and str(row.get("status", "") or "") != "missing"


def _finite_or_none(value: Any) -> float | None:
    out = _finite_float(value, float("nan"))
    return out if math.isfinite(out) else None


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except Exception:
        return None


def _nonempty_or_none(value: Any) -> str | None:
    text = str(value or "")
    return text if text else None


def _put_if_finite(out: dict[str, Any], key: str, value: Any) -> None:
    number = _finite_or_none(value)
    if number is not None:
        out[key] = number


def _put_if_int(out: dict[str, Any], key: str, value: Any) -> None:
    number = _int_or_none(value)
    if number is not None:
        out[key] = number


def _put_if_text(out: dict[str, Any], key: str, value: Any) -> None:
    text = _nonempty_or_none(value)
    if text is not None:
        out[key] = text


def _latest_row(rows: list[dict[str, Any]], stage: str) -> dict[str, Any] | None:
    matches = [row for row in rows if str(row.get("stage", "") or "") == str(stage)]
    return matches[-1] if matches else None


def _rows_for_stages(rows: list[dict[str, Any]], stages: tuple[str, ...]) -> list[dict[str, Any]]:
    stage_set = set(stages)
    return [row for row in rows if str(row.get("stage", "") or "") in stage_set]


def _source_stages(rows: list[dict[str, Any]]) -> list[str]:
    return sorted({str(row.get("stage", "") or "") for row in rows if row.get("stage")})


def _source_event_kinds(rows: list[dict[str, Any]]) -> list[str]:
    return sorted(
        {
            str(row.get("source_event_kind", "") or "")
            for row in rows
            if row.get("source_event_kind")
        }
    )


def _first_present(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    for row in rows:
        if row:
            return row
    return None


def _base_abstraction(
    *,
    chain_rows: list[dict[str, Any]],
    abstraction_stage: str,
    owner: str,
    source_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    source = _first_present(source_rows) or _first_present(chain_rows) or {}
    return {
        "schema_version": ABSTRACTION_SCHEMA_VERSION,
        "episode": int(source.get("episode", 0) or 0),
        "chain_id": int(source.get("chain_id", 0) or 0),
        "target_id": int(source.get("target_id", 0) or 0),
        "munition_id": int(source.get("munition_id", 0) or 0),
        "abstraction_stage": abstraction_stage,
        "owner": owner,
        "present": int(bool(source_rows)),
        "status": "observed" if source_rows else "missing",
        "reason": str(source.get("reason", "") or ""),
        "source_stages": _source_stages(source_rows),
        "source_event_kinds": _source_event_kinds(source_rows),
        "observed": {},
        "coupling_flags": [],
    }


def _append_flag(out: dict[str, Any], flag: str) -> None:
    flags = out.setdefault("coupling_flags", [])
    if flag not in flags:
        flags.append(flag)


def _approach_abstraction(chain_rows: list[dict[str, Any]]) -> dict[str, Any]:
    row = _latest_row(chain_rows, chain_contract.STAGE_NEAREST_APPROACH)
    out = _base_abstraction(
        chain_rows=chain_rows,
        abstraction_stage=ABSTRACTION_APPROACH,
        owner="guidance_kinematics",
        source_rows=[row] if row else [],
    )
    observed = out["observed"]
    if row:
        _put_if_finite(observed, "miss_distance_m", row.get("miss_distance_m"))
        _put_if_finite(
            observed, "nearest_approach_time_s", row.get("nearest_approach_time_s")
        )
        _put_if_finite(observed, "local_forward_m", row.get("local_forward_m"))
        _put_if_finite(observed, "local_right_m", row.get("local_right_m"))
        _put_if_finite(observed, "local_up_m", row.get("local_up_m"))
        _put_if_finite(observed, "closure_mps", row.get("closure_mps"))
        _put_if_text(observed, "aspect_bucket", row.get("aspect_bucket"))
    return out


def _fuze_abstraction(chain_rows: list[dict[str, Any]]) -> dict[str, Any]:
    row = _latest_row(chain_rows, chain_contract.STAGE_FUZE)
    out = _base_abstraction(
        chain_rows=chain_rows,
        abstraction_stage=ABSTRACTION_FUZE_DECISION,
        owner="fuze_decision",
        source_rows=[row] if row else [],
    )
    observed = out["observed"]
    if row:
        _put_if_text(observed, "fuze_type", row.get("fuze_type"))
        _put_if_int(observed, "armed", row.get("fuze_armed"))
        _put_if_int(observed, "triggered", row.get("fuze_triggered"))
        _put_if_text(observed, "failure_reason", row.get("fuze_failure_reason"))
        _put_if_finite(
            observed,
            "detonation_probability",
            row.get("fuze_expected_detonation_probability"),
        )
        _put_if_finite(observed, "detonation_sample", row.get("fuze_sample"))
        _put_if_finite(observed, "reliability", row.get("fuze_reliability"))
        _put_if_finite(observed, "trigger_radius_m", row.get("fuze_trigger_radius_m"))
        _put_if_finite(
            observed, "sensor_opportunity_score", row.get("fuze_sensor_opportunity_score")
        )
        _put_if_int(observed, "terminal_track_valid", row.get("fuze_terminal_track_valid"))
        _put_if_int(observed, "target_detected", row.get("fuze_target_detected"))
        _put_if_finite(
            observed,
            "target_detection_confidence",
            row.get("fuze_target_detection_confidence"),
        )
        _put_if_finite(
            observed,
            "target_detection_threshold",
            row.get("fuze_target_detection_threshold"),
        )
        _put_if_text(observed, "detonation_point_source", row.get("detonation_point_source"))
        if _finite_or_none(row.get("fuze_mechanism_coverage_score")) is not None:
            observed["mechanism_coverage_score"] = _finite_float(
                row.get("fuze_mechanism_coverage_score"), float("nan")
            )
            _append_flag(out, "fuze_stage_contains_mechanism_coverage_score")
    return out


def _load_abstraction(chain_rows: list[dict[str, Any]]) -> dict[str, Any]:
    load_rows = _rows_for_stages(
        chain_rows,
        (
            chain_contract.STAGE_WARHEAD_MECHANISM,
            chain_contract.STAGE_SPATIAL_COVERAGE,
            chain_contract.STAGE_COMPONENT_LOAD,
        ),
    )
    warhead = _latest_row(chain_rows, chain_contract.STAGE_WARHEAD_MECHANISM)
    spatial = _latest_row(chain_rows, chain_contract.STAGE_SPATIAL_COVERAGE)
    component = _latest_row(chain_rows, chain_contract.STAGE_COMPONENT_LOAD)
    out = _base_abstraction(
        chain_rows=chain_rows,
        abstraction_stage=ABSTRACTION_WARHEAD_LOAD_FIELD,
        owner="warhead_load_field",
        source_rows=load_rows,
    )
    observed = out["observed"]
    if warhead:
        _put_if_text(observed, "mechanism_family", warhead.get("mechanism_family"))
        _put_if_finite(observed, "warhead_mass_kg", warhead.get("warhead_mass_kg"))
        _put_if_finite(observed, "lethal_radius_m", warhead.get("lethal_radius_m"))
        _put_if_finite(observed, "fragment_energy_j", warhead.get("fragment_energy_j"))
        _put_if_finite(
            observed, "fragment_density_per_m2", warhead.get("fragment_density_per_m2")
        )
        _put_if_finite(observed, "blast_overpressure_kpa", warhead.get("blast_overpressure_kpa"))
        _put_if_finite(observed, "blast_impulse_kpa_ms", warhead.get("blast_impulse_kpa_ms"))
        _put_if_finite(
            observed,
            "blast_scaled_distance_m_kg13",
            warhead.get("blast_scaled_distance_m_kg13"),
        )
        _put_if_finite(observed, "rod_cut_margin", warhead.get("rod_cut_margin"))
        _put_if_finite(observed, "penetration_margin", warhead.get("penetration_margin"))
        _put_if_finite(observed, "surface_incidence_cos", warhead.get("surface_incidence_cos"))
    if spatial:
        _put_if_int(observed, "projected_hitbox_count", spatial.get("projected_hitbox_count"))
        _put_if_int(observed, "spatial_sample_count", spatial.get("spatial_sample_count"))
        _put_if_finite(observed, "spatial_hit_estimate", spatial.get("spatial_hit_estimate"))
        _put_if_finite(observed, "spatial_hit_fraction", spatial.get("spatial_hit_fraction"))
        _put_if_finite(observed, "spatial_energy_scale", spatial.get("spatial_energy_scale"))
        _put_if_finite(observed, "spatial_pattern_scale", spatial.get("spatial_pattern_scale"))
    if component:
        _put_if_text(observed, "component_name", component.get("component_name"))
        _put_if_text(observed, "component_system", component.get("component_system"))
        _put_if_text(observed, "component_load_source", component.get("component_load_source"))
        _put_if_finite(observed, "component_distance_m", component.get("component_distance_m"))
        _put_if_finite(
            observed, "component_effect_scale", component.get("component_effect_scale")
        )
        if _finite_or_none(component.get("component_effect_scale")) is not None:
            _append_flag(out, "component_load_uses_composite_effect_scale")
    return out


def _component_response_abstraction(chain_rows: list[dict[str, Any]]) -> dict[str, Any]:
    damage = _latest_row(chain_rows, chain_contract.STAGE_COMPONENT_DAMAGE)
    source_rows = [damage] if damage is not None else []
    out = _base_abstraction(
        chain_rows=chain_rows,
        abstraction_stage=ABSTRACTION_COMPONENT_RESPONSE,
        owner="component_response",
        source_rows=source_rows,
    )
    source = damage
    observed = out["observed"]
    if source:
        _put_if_text(observed, "component_name", source.get("component_name"))
        _put_if_text(observed, "component_system", source.get("component_system"))
        _put_if_finite(
            observed,
            "failure_probability",
            source.get("component_failure_probability"),
        )
        _put_if_finite(observed, "failure_sample", source.get("component_failure_sample"))
        _put_if_text(observed, "failure_mode", source.get("component_failure_mode"))
        _put_if_finite(
            observed,
            "failure_severity",
            source.get("component_failure_severity"),
        )
        before = _finite_or_none(source.get("component_integrity_before"))
        after = _finite_or_none(source.get("component_integrity_after"))
        if before is not None:
            observed["integrity_before"] = before
        if after is not None:
            observed["integrity_after"] = after
        if before is not None and after is not None:
            observed["integrity_delta"] = after - before
    return out


def _consequence_abstraction(chain_rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_rows = _rows_for_stages(
        chain_rows,
        (
            chain_contract.STAGE_STRUCTURAL_BREAKUP,
            chain_contract.STAGE_PLATFORM_CONSEQUENCE,
            chain_contract.STAGE_LIFECYCLE,
        ),
    )
    structural = _latest_row(chain_rows, chain_contract.STAGE_STRUCTURAL_BREAKUP)
    platform = _latest_row(chain_rows, chain_contract.STAGE_PLATFORM_CONSEQUENCE)
    lifecycle = _latest_row(chain_rows, chain_contract.STAGE_LIFECYCLE)
    out = _base_abstraction(
        chain_rows=chain_rows,
        abstraction_stage=ABSTRACTION_CONSEQUENCE_PROJECTION,
        owner="consequence_projection",
        source_rows=source_rows,
    )
    observed = out["observed"]
    if structural:
        _put_if_text(observed, "breakup_state", structural.get("breakup_state"))
        _put_if_text(observed, "break_mode", structural.get("break_mode"))
        _put_if_int(observed, "airframe_breakup", structural.get("airframe_breakup"))
    if platform:
        _put_if_finite(observed, "system_health_delta", platform.get("system_health_delta"))
        _put_if_finite(
            observed, "mission_capability_delta", platform.get("mission_capability_delta")
        )
        _put_if_finite(
            observed, "mobility_capability_delta", platform.get("mobility_capability_delta")
        )
        _put_if_finite(
            observed, "sensor_capability_delta", platform.get("sensor_capability_delta")
        )
        _put_if_finite(
            observed,
            "survivability_margin_delta",
            platform.get("survivability_margin_delta"),
        )
        _put_if_text(observed, "fire_state", platform.get("fire_state"))
        _put_if_text(observed, "loss_state", platform.get("loss_state"))
        _put_if_int(observed, "mission_kill", platform.get("mission_kill"))
        _put_if_int(observed, "mobility_kill", platform.get("mobility_kill"))
        _put_if_int(observed, "sensor_kill", platform.get("sensor_kill"))
        _put_if_int(observed, "destroyed", platform.get("destroyed"))
        if "effect_scale=" in str(platform.get("vulnerability_scale_trace", "") or ""):
            _append_flag(out, "consequence_trace_contains_vulnerability_effect_scale")
    if lifecycle:
        _put_if_text(observed, "lifecycle_from", lifecycle.get("lifecycle_from"))
        _put_if_text(observed, "lifecycle_to", lifecycle.get("lifecycle_to"))
        _put_if_text(observed, "lifecycle_loss_state", lifecycle.get("loss_state"))
        _put_if_int(observed, "lifecycle_terminal", lifecycle.get("lifecycle_terminal"))
    return out


def _lethality_chain_stage_abstractions(chain_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_chain: dict[tuple[int, int], list[dict[str, Any]]] = {}
    for row in chain_rows:
        chain_id = int(row.get("chain_id", 0) or 0)
        if chain_id <= 0:
            continue
        episode = int(row.get("episode", 0) or 0)
        rows_by_chain.setdefault((episode, chain_id), []).append(row)

    abstractions: list[dict[str, Any]] = []
    for key in sorted(rows_by_chain):
        chain = rows_by_chain[key]
        abstractions.extend(
            (
                _approach_abstraction(chain),
                _fuze_abstraction(chain),
                _load_abstraction(chain),
                _component_response_abstraction(chain),
                _consequence_abstraction(chain),
            )
        )
    return abstractions


def _lethality_chain_decoupling_summary(
    stage_abstractions: list[dict[str, Any]],
) -> dict[str, Any]:
    chains = {
        (int(row.get("episode", 0) or 0), int(row.get("chain_id", 0) or 0))
        for row in stage_abstractions
    }
    present_stage_counts = Counter(
        str(row.get("abstraction_stage", "") or "")
        for row in stage_abstractions
        if int(row.get("present", 0) or 0) > 0
    )
    coupling_flags = Counter(
        flag
        for row in stage_abstractions
        for flag in list(row.get("coupling_flags", []) or [])
    )
    missing_by_chain: dict[str, list[str]] = {}
    for episode, chain_id in sorted(chains):
        chain_rows = [
            row
            for row in stage_abstractions
            if int(row.get("episode", 0) or 0) == episode
            and int(row.get("chain_id", 0) or 0) == chain_id
        ]
        missing = [
            str(row.get("abstraction_stage", "") or "")
            for row in chain_rows
            if int(row.get("present", 0) or 0) <= 0
        ]
        if missing:
            missing_by_chain[f"{episode}:{chain_id}"] = missing

    return {
        "schema_version": ABSTRACTION_SCHEMA_VERSION,
        "chain_count": len(chains),
        "abstraction_count": len(stage_abstractions),
        "canonical_abstraction_stages": list(ABSTRACTION_STAGES),
        "present_stage_counts": dict(sorted(present_stage_counts.items())),
        "coupling_flag_counts": dict(sorted(coupling_flags.items())),
        "missing_stages_by_chain": missing_by_chain,
        "authority_boundary": {
            "runtime_parameter_retuning": False,
            "real_world_pk": False,
            "deterministic_fuze_authority": False,
            "calibration_authority": False,
        },
    }
