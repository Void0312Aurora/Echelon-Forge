"""Lethality-chain row projection for the process probe."""

from __future__ import annotations

from typing import Any

from tools.diagnostics import lethality_chain_contract as chain_contract
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.schema import (
    LETHALITY_CHAIN_SCHEMA_VERSION,
    _entity_id,
    _event_id,
    _finite_float,
    _stable_json,
)
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.lethality_rows import (
    _lethality_base_row,
    _lethality_header_base_kwargs,
)


def _effects_event_has_warhead_load(effect: Any) -> bool:
    outcome = str(getattr(effect, "outcome_state", "") or "")
    if outcome in {
        "fuze_no_detonation",
        "fuze_no_terminal_track",
        "outside_sensor_window",
        "target_not_detected",
        "no_detonation",
    }:
        return False
    if int(getattr(effect, "component_hit_count", 0) or 0) > 0:
        return True
    if list(getattr(effect, "component_mechanism_load_rows", []) or []):
        return True
    load_fields = (
        "mechanism_fragment_energy_j",
        "mechanism_fragment_areal_density_per_m2",
        "mechanism_penetration_margin",
        "mechanism_blast_overpressure_kpa",
        "mechanism_blast_impulse_kpa_ms",
        "mechanism_blast_scaled_distance_m_kg13",
        "mechanism_rod_cut_margin",
        "mechanism_surface_incidence_cos",
        "warhead_spatial_hit_estimate",
    )
    return any(_finite_float(getattr(effect, field, 0.0), 0.0) > 0.0 for field in load_fields)


def _parse_platform_damage_state_delta(value: Any) -> dict[str, float]:
    deltas = {
        "mission_capability_delta": float("nan"),
        "mobility_capability_delta": float("nan"),
        "sensor_capability_delta": float("nan"),
        "survivability_margin_delta": float("nan"),
    }
    text = str(value or "")
    key_map = {
        "mission": "mission_capability_delta",
        "mobility": "mobility_capability_delta",
        "sensor": "sensor_capability_delta",
        "survivability": "survivability_margin_delta",
    }
    for item in text.split(","):
        if "=" not in item:
            continue
        key, raw = item.split("=", 1)
        out_key = key_map.get(str(key).strip())
        if out_key is None:
            continue
        deltas[out_key] = _finite_float(raw.strip(), float("nan"))
    return deltas


def _lethality_evidence_level(effect: Any | None) -> str:
    if effect is None:
        return "training_synthetic"
    if (
        bool(getattr(effect, "fuze_profile_synthetic", False))
        or bool(getattr(effect, "warhead_profile_synthetic", False))
        or bool(getattr(effect, "damage_scalar_synthetic", False))
    ):
        return "training_synthetic"
    if bool(getattr(effect, "vulnerability_calibrated_evidence", False)):
        return "engineering_assumption"
    return "uncalibrated"


def _lethality_trace_indexes(engagement_events: Any) -> tuple[dict[int, Any], dict[int, Any]]:
    trace_by_effect: dict[int, Any] = {}
    trace_by_damage: dict[int, Any] = {}
    for trace in list(getattr(engagement_events, "diagnostics_traces", []) or []):
        effects_event_id = _event_id(trace, "effects_event_id")
        damage_report_id = _event_id(trace, "damage_report_id")
        if effects_event_id > 0:
            trace_by_effect[effects_event_id] = trace
        if damage_report_id > 0:
            trace_by_damage[damage_report_id] = trace
    return trace_by_effect, trace_by_damage


def _int_value(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _lethality_component_response_rows(
    *,
    episode: int,
    step: int,
    sim_time_s: float,
    engagement_events: Any,
) -> list[dict[str, Any]]:
    trace_by_effect, _trace_by_damage = _lethality_trace_indexes(engagement_events)
    rows: list[dict[str, Any]] = []
    for effect in list(getattr(engagement_events, "effects_events", []) or []):
        response_rows = list(getattr(effect, "component_response_rows", []) or [])
        if not response_rows:
            continue
        effect_id = _event_id(effect, "event_id")
        trace = trace_by_effect.get(effect_id)
        chain_id = _event_id(trace, "chain_id") if trace is not None else effect_id
        munition_id = _entity_id(getattr(trace, "munition", None)) if trace is not None else 0
        if munition_id <= 0:
            munition_id = _entity_id(getattr(effect, "munition", None))
        target_id = _entity_id(getattr(effect, "target", None))
        load_rows = list(getattr(effect, "component_mechanism_load_rows", []) or [])
        for index, response in enumerate(response_rows):
            source_row_index = _int_value(getattr(response, "source_row_index", index), index)
            source_load = (
                load_rows[source_row_index]
                if 0 <= source_row_index < len(load_rows)
                else None
            )
            row = {
                "schema_version": "component_response_fact.v1",
                "episode": int(episode),
                "step": int(step),
                "sim_time_s": float(sim_time_s),
                "chain_id": int(chain_id),
                "event_id": int(effect_id),
                "parent_event_id": (
                    _event_id(trace, "launch_event_id") if trace is not None else 0
                ),
                "stage": "component_response",
                "status": "evaluated",
                "reason": "effects_event_component_response_row",
                "source_event_kind": "ComponentResponseRow",
                "source_event_id": int(effect_id),
                "source_row_index": int(source_row_index),
                "munition_id": int(munition_id),
                "target_id": int(target_id),
                "evidence_level": _lethality_evidence_level(effect),
                "observation_mode": chain_contract.OBSERVATION_MODE_SAMPLED_RUNTIME,
                "consumer_visibility": (
                    chain_contract.CONSUMER_VISIBILITY_DIAGNOSTICS_AND_TRAINING
                ),
                "component_name": str(getattr(response, "component_name", "") or ""),
                "component_system": str(getattr(response, "component_system", "") or ""),
                "component_redundancy_group_id": str(
                    getattr(response, "component_redundancy_group_id", "") or ""
                ),
                "threshold_scale": _finite_float(
                    getattr(response, "threshold_scale", float("nan"))
                ),
                "failure_probability": _finite_float(
                    getattr(response, "failure_probability", float("nan"))
                ),
                "failure_sample": _finite_float(
                    getattr(response, "failure_sample", float("nan"))
                ),
                "failure_probability_source": str(
                    getattr(response, "failure_probability_source", "") or ""
                ),
                "failure_probability_calibrated": int(
                    bool(getattr(response, "failure_probability_calibrated", False))
                ),
                "failure_probability_evidence_dataset_ref": str(
                    getattr(response, "failure_probability_evidence_dataset_ref", "") or ""
                ),
                "failure_probability_evidence_row_id": str(
                    getattr(response, "failure_probability_evidence_row_id", "") or ""
                ),
                "failure_probability_evidence_source_ref": str(
                    getattr(response, "failure_probability_evidence_source_ref", "") or ""
                ),
                "failure_probability_evidence_provenance": str(
                    getattr(response, "failure_probability_evidence_provenance", "") or ""
                ),
                "failure_probability_authority": int(
                    bool(getattr(response, "failure_probability_authority", False))
                ),
                "failure_probability_component_specific": int(
                    bool(getattr(response, "failure_probability_component_specific", False))
                ),
                "failure_probability_weapon_family": str(
                    getattr(response, "failure_probability_weapon_family", "") or ""
                ),
                "failure_probability_aspect_bucket": str(
                    getattr(response, "failure_probability_aspect_bucket", "") or ""
                ),
                "failure_probability_closure_bucket": str(
                    getattr(response, "failure_probability_closure_bucket", "") or ""
                ),
                "failure_probability_miss_distance_bucket": str(
                    getattr(response, "failure_probability_miss_distance_bucket", "") or ""
                ),
                "failure_probability_evidence_component_name": str(
                    getattr(response, "failure_probability_evidence_component_name", "") or ""
                ),
                "failure_probability_evidence_component_system": str(
                    getattr(response, "failure_probability_evidence_component_system", "") or ""
                ),
                "failure_probability_evidence_component_redundancy_group_id": str(
                    getattr(
                        response,
                        "failure_probability_evidence_component_redundancy_group_id",
                        "",
                    )
                    or ""
                ),
                "failure_mode": str(getattr(response, "failure_mode", "") or ""),
                "failure_severity": _finite_float(
                    getattr(response, "failure_severity", float("nan"))
                ),
                "failure_mode_source": str(
                    getattr(response, "failure_mode_source", "") or ""
                ),
                "failure_mode_authority": int(
                    bool(getattr(response, "failure_mode_authority", False))
                ),
                "integrity_before": _finite_float(
                    getattr(response, "integrity_before", float("nan"))
                ),
                "integrity_after": _finite_float(
                    getattr(response, "integrity_after", float("nan"))
                ),
                "redundancy_group_availability_before": _finite_float(
                    getattr(response, "redundancy_group_availability_before", float("nan"))
                ),
                "redundancy_group_availability_after": _finite_float(
                    getattr(response, "redundancy_group_availability_after", float("nan"))
                ),
            }
            if source_load is not None:
                row.update(
                    {
                        "source_load_component_name": str(
                            getattr(source_load, "component_name", "") or ""
                        ),
                        "source_load_component_system": str(
                            getattr(source_load, "component_system", "") or ""
                        ),
                        "source_load_component_redundancy_group_id": str(
                            getattr(source_load, "component_redundancy_group_id", "") or ""
                        ),
                        "source_load_direct_hit": int(
                            bool(getattr(source_load, "direct_hit", False))
                        ),
                        "source_load_distance_m": _finite_float(
                            getattr(source_load, "distance_m", float("nan"))
                        ),
                        "source_load_effect_scale": _finite_float(
                            getattr(source_load, "effect_scale", float("nan"))
                        ),
                    }
                )
            rows.append(row)
    return rows


def _lethality_chain_rows(
    *,
    episode: int,
    step: int,
    sim_time_s: float,
    engagement_events: Any,
) -> list[dict[str, Any]]:
    trace_by_effect, trace_by_damage = _lethality_trace_indexes(engagement_events)
    effect_by_id = {
        _event_id(effect, "event_id"): effect
        for effect in list(getattr(engagement_events, "effects_events", []) or [])
        if _event_id(effect, "event_id") > 0
    }
    rows: list[dict[str, Any]] = []
    standard_nearest_keys: set[tuple[int, int]] = set()
    standard_fuze_keys: set[tuple[int, int]] = set()
    standard_nearest_munition_ids: set[int] = set()
    standard_fuze_munition_ids: set[int] = set()
    standard_warhead_keys: set[tuple[int, int]] = set()
    standard_spatial_keys: set[tuple[int, int]] = set()
    standard_component_keys: set[tuple[int, int]] = set()
    standard_component_damage_keys: set[tuple[int, int]] = set()
    standard_structural_keys: set[tuple[int, int]] = set()
    standard_platform_keys: set[tuple[int, int]] = set()
    standard_lifecycle_keys: set[tuple[int, int]] = set()

    for nearest_event in list(getattr(engagement_events, "nearest_approach_events", []) or []):
        base_kwargs = _lethality_header_base_kwargs(
            episode=episode,
            step=step,
            sim_time_s=sim_time_s,
            event=nearest_event,
            stage=chain_contract.STAGE_NEAREST_APPROACH,
            source_event_kind="NearestApproachEvent",
        )
        row = _lethality_base_row(**base_kwargs)
        row.update(
            {
                "miss_distance_m": _finite_float(
                    getattr(nearest_event, "miss_distance_m", float("nan"))
                ),
                "nearest_approach_time_s": _finite_float(
                    getattr(nearest_event, "nearest_approach_time_s", float("nan"))
                ),
                "local_forward_m": _finite_float(
                    getattr(nearest_event, "local_forward_m", float("nan"))
                ),
                "local_right_m": _finite_float(
                    getattr(nearest_event, "local_right_m", float("nan"))
                ),
                "local_up_m": _finite_float(getattr(nearest_event, "local_up_m", float("nan"))),
                "closure_mps": _finite_float(getattr(nearest_event, "closure_mps", float("nan"))),
                "aspect_bucket": str(getattr(nearest_event, "aspect_bucket", "") or ""),
            }
        )
        rows.append(row)
        standard_nearest_keys.add(
            (int(row.get("chain_id", 0) or 0), int(row.get("munition_id", 0) or 0))
        )
        standard_nearest_munition_ids.add(int(row.get("munition_id", 0) or 0))

    for fuze_event in list(getattr(engagement_events, "fuze_evaluation_events", []) or []):
        base_kwargs = _lethality_header_base_kwargs(
            episode=episode,
            step=step,
            sim_time_s=sim_time_s,
            event=fuze_event,
            stage=chain_contract.STAGE_FUZE,
            source_event_kind="FuzeEvaluationEvent",
        )
        failure_reason = str(getattr(fuze_event, "failure_reason", "") or "")
        if not base_kwargs["reason"]:
            base_kwargs["reason"] = failure_reason
        row = _lethality_base_row(**base_kwargs)
        row.update(
            {
                "fuze_type": str(getattr(fuze_event, "fuze_type", "") or ""),
                "fuze_armed": int(bool(getattr(fuze_event, "armed", False))),
                "fuze_triggered": int(bool(getattr(fuze_event, "triggered", False))),
                "fuze_failure_reason": failure_reason,
                "fuze_delay_s": _finite_float(getattr(fuze_event, "delay_s", float("nan"))),
                "fuze_reliability": _finite_float(getattr(fuze_event, "reliability", float("nan"))),
                "fuze_sample": _finite_float(getattr(fuze_event, "sample", float("nan"))),
                "fuze_expected_detonation_probability": _finite_float(
                    getattr(
                        fuze_event,
                        "expected_detonation_probability",
                        getattr(fuze_event, "reliability", float("nan")),
                    )
                ),
                "fuze_sampled_outcome": int(bool(getattr(fuze_event, "sampled_outcome", True))),
                "fuze_trigger_radius_m": _finite_float(
                    getattr(fuze_event, "trigger_radius_m", float("nan"))
                ),
                "fuze_sensor_opportunity_source": str(
                    getattr(fuze_event, "sensor_opportunity_source", "") or ""
                ),
                "fuze_sensor_opportunity_score": _finite_float(
                    getattr(fuze_event, "sensor_opportunity_score", float("nan"))
                ),
                "fuze_terminal_track_valid": int(
                    bool(getattr(fuze_event, "terminal_track_valid", False))
                ),
                "fuze_target_detected": int(bool(getattr(fuze_event, "target_detected", False))),
                "fuze_target_detection_source": str(
                    getattr(fuze_event, "target_detection_source", "") or ""
                ),
                "fuze_target_detection_confidence": _finite_float(
                    getattr(fuze_event, "target_detection_confidence", float("nan"))
                ),
                "fuze_target_detection_threshold": _finite_float(
                    getattr(fuze_event, "target_detection_threshold", float("nan"))
                ),
                "detonation_point_source": str(
                    getattr(fuze_event, "detonation_point_source", "") or ""
                ),
                "fuze_mechanism_coverage_score": _finite_float(
                    getattr(fuze_event, "mechanism_coverage_score", float("nan"))
                ),
                "contact_surface_distance_m": _finite_float(
                    getattr(fuze_event, "contact_surface_distance_m", float("nan"))
                ),
                "contact_penetration_depth_m": _finite_float(
                    getattr(fuze_event, "contact_penetration_depth_m", float("nan"))
                ),
                "contact_surface_tolerance_m": _finite_float(
                    getattr(fuze_event, "contact_surface_tolerance_m", float("nan"))
                ),
                "contact_inside_hitbox": int(
                    bool(getattr(fuze_event, "contact_inside_hitbox", False))
                ),
                "direct_hitbox_intersection": int(
                    bool(getattr(fuze_event, "direct_hitbox_intersection", False))
                ),
            }
        )
        rows.append(row)
        standard_fuze_keys.add(
            (int(row.get("chain_id", 0) or 0), int(row.get("munition_id", 0) or 0))
        )
        standard_fuze_munition_ids.add(int(row.get("munition_id", 0) or 0))

    for warhead_event in list(getattr(engagement_events, "warhead_mechanism_events", []) or []):
        base_kwargs = _lethality_header_base_kwargs(
            episode=episode,
            step=step,
            sim_time_s=sim_time_s,
            event=warhead_event,
            stage=chain_contract.STAGE_WARHEAD_MECHANISM,
            source_event_kind="WarheadMechanismEvent",
        )
        row = _lethality_base_row(**base_kwargs)
        row.update(
            {
                "mechanism_family": str(getattr(warhead_event, "mechanism_family", "") or ""),
                "warhead_mass_kg": _finite_float(
                    getattr(warhead_event, "warhead_mass_kg", float("nan"))
                ),
                "lethal_radius_m": _finite_float(
                    getattr(warhead_event, "lethal_radius_m", float("nan"))
                ),
                "fragment_energy_j": _finite_float(
                    getattr(warhead_event, "fragment_energy_j", float("nan"))
                ),
                "fragment_density_per_m2": _finite_float(
                    getattr(warhead_event, "fragment_density_per_m2", float("nan"))
                ),
                "blast_overpressure_kpa": _finite_float(
                    getattr(warhead_event, "blast_overpressure_kpa", float("nan"))
                ),
                "blast_impulse_kpa_ms": _finite_float(
                    getattr(warhead_event, "blast_impulse_kpa_ms", float("nan"))
                ),
                "blast_scaled_distance_m_kg13": _finite_float(
                    getattr(warhead_event, "blast_scaled_distance_m_kg13", float("nan"))
                ),
                "rod_cut_margin": _finite_float(
                    getattr(warhead_event, "rod_cut_margin", float("nan"))
                ),
                "penetration_margin": _finite_float(
                    getattr(warhead_event, "penetration_margin", float("nan"))
                ),
                "surface_incidence_cos": _finite_float(
                    getattr(warhead_event, "surface_incidence_cos", float("nan"))
                ),
            }
        )
        rows.append(row)
        standard_warhead_keys.add(
            (int(row.get("chain_id", 0) or 0), int(row.get("munition_id", 0) or 0))
        )

    for spatial_event in list(getattr(engagement_events, "spatial_coverage_events", []) or []):
        base_kwargs = _lethality_header_base_kwargs(
            episode=episode,
            step=step,
            sim_time_s=sim_time_s,
            event=spatial_event,
            stage=chain_contract.STAGE_SPATIAL_COVERAGE,
            source_event_kind="SpatialCoverageEvent",
        )
        row = _lethality_base_row(**base_kwargs)
        row.update(
            {
                "projected_hitbox_count": int(
                    getattr(spatial_event, "projected_hitbox_count", 0) or 0
                ),
                "spatial_sample_count": int(getattr(spatial_event, "sample_count", 0) or 0),
                "spatial_hit_estimate": _finite_float(
                    getattr(spatial_event, "hit_estimate", float("nan"))
                ),
                "spatial_hit_fraction": _finite_float(
                    getattr(spatial_event, "hit_fraction", float("nan"))
                ),
                "spatial_energy_scale": _finite_float(
                    getattr(spatial_event, "energy_scale", float("nan"))
                ),
                "spatial_pattern_scale": _finite_float(
                    getattr(spatial_event, "pattern_scale", float("nan"))
                ),
            }
        )
        rows.append(row)
        standard_spatial_keys.add(
            (int(row.get("chain_id", 0) or 0), int(row.get("munition_id", 0) or 0))
        )

    for component_event in list(getattr(engagement_events, "component_load_events", []) or []):
        base_kwargs = _lethality_header_base_kwargs(
            episode=episode,
            step=step,
            sim_time_s=sim_time_s,
            event=component_event,
            stage=chain_contract.STAGE_COMPONENT_LOAD,
            source_event_kind="ComponentLoadEvent",
        )
        row = _lethality_base_row(**base_kwargs)
        component_name = str(getattr(component_event, "component_name", "") or "")
        component_system = str(getattr(component_event, "component_system", "") or "")
        row.update(
            {
                "component_hit_count": 1,
                "component_name": component_name,
                "component_system": component_system,
                "component_direct_hit": int(bool(getattr(component_event, "direct_hit", False))),
                "component_distance_m": _finite_float(
                    getattr(component_event, "distance_m", float("nan"))
                ),
                "component_effect_scale": _finite_float(
                    getattr(component_event, "effect_scale", float("nan"))
                ),
                "component_spatial_intersection_fraction": _finite_float(
                    getattr(component_event, "spatial_intersection_fraction", float("nan"))
                ),
                "component_pattern_weight": _finite_float(
                    getattr(component_event, "pattern_weight", float("nan"))
                ),
                "component_orientation_weight": _finite_float(
                    getattr(component_event, "orientation_weight", float("nan"))
                ),
                "component_receiver_exposure_fraction": _finite_float(
                    getattr(component_event, "receiver_exposure_fraction", float("nan"))
                ),
                "component_armor_transmission": _finite_float(
                    getattr(component_event, "armor_transmission", float("nan"))
                ),
                "component_sampling_confidence": _finite_float(
                    getattr(component_event, "sampling_confidence", float("nan"))
                ),
                "component_load_intensity_scale": _finite_float(
                    getattr(component_event, "load_intensity_scale", float("nan"))
                ),
                "component_load_source": str(getattr(component_event, "load_source", "") or ""),
                "fragment_energy_j": _finite_float(
                    getattr(component_event, "fragment_energy_j", float("nan"))
                ),
                "fragment_density_per_m2": _finite_float(
                    getattr(component_event, "fragment_density_per_m2", float("nan"))
                ),
                "blast_overpressure_kpa": _finite_float(
                    getattr(component_event, "blast_overpressure_kpa", float("nan"))
                ),
                "blast_impulse_kpa_ms": _finite_float(
                    getattr(component_event, "blast_impulse_kpa_ms", float("nan"))
                ),
                "blast_scaled_distance_m_kg13": _finite_float(
                    getattr(component_event, "blast_scaled_distance_m_kg13", float("nan"))
                ),
                "rod_cut_margin": _finite_float(
                    getattr(component_event, "rod_cut_margin", float("nan"))
                ),
                "penetration_margin": _finite_float(
                    getattr(component_event, "penetration_margin", float("nan"))
                ),
                "surface_incidence_cos": _finite_float(
                    getattr(component_event, "surface_incidence_cos", float("nan"))
                ),
            }
        )
        rows.append(row)
        standard_component_keys.add(
            (int(row.get("chain_id", 0) or 0), int(row.get("munition_id", 0) or 0))
        )

    for damage_event in list(getattr(engagement_events, "component_damage_events", []) or []):
        base_kwargs = _lethality_header_base_kwargs(
            episode=episode,
            step=step,
            sim_time_s=sim_time_s,
            event=damage_event,
            stage=chain_contract.STAGE_COMPONENT_DAMAGE,
            source_event_kind="ComponentDamageEvent",
        )
        row = _lethality_base_row(**base_kwargs)
        row.update(
            {
                "component_hit_count": 1,
                "component_name": str(getattr(damage_event, "component_name", "") or ""),
                "component_system": str(getattr(damage_event, "component_system", "") or ""),
                "component_integrity_before": _finite_float(
                    getattr(damage_event, "integrity_before", float("nan"))
                ),
                "component_integrity_after": _finite_float(
                    getattr(damage_event, "integrity_after", float("nan"))
                ),
                "component_failure_mode": str(getattr(damage_event, "failure_mode", "") or ""),
                "component_failure_severity": _finite_float(
                    getattr(damage_event, "failure_severity", float("nan"))
                ),
                "component_failure_probability": _finite_float(
                    getattr(damage_event, "failure_probability", float("nan"))
                ),
                "component_failure_sample": _finite_float(
                    getattr(damage_event, "failure_sample", float("nan"))
                ),
            }
        )
        rows.append(row)
        standard_component_damage_keys.add(
            (int(row.get("chain_id", 0) or 0), int(row.get("munition_id", 0) or 0))
        )

    for structural_event in list(getattr(engagement_events, "structural_breakup_events", []) or []):
        base_kwargs = _lethality_header_base_kwargs(
            episode=episode,
            step=step,
            sim_time_s=sim_time_s,
            event=structural_event,
            stage=chain_contract.STAGE_STRUCTURAL_BREAKUP,
            source_event_kind="StructuralBreakupEvent",
        )
        row = _lethality_base_row(**base_kwargs)
        row.update(
            {
                "breakup_state": str(getattr(structural_event, "breakup_state", "") or ""),
                "break_mode": str(getattr(structural_event, "break_mode", "") or ""),
                "detached_part_ref": str(
                    getattr(structural_event, "detached_part_ref", "") or ""
                ),
                "detached_part_count": int(
                    getattr(structural_event, "detached_part_count", 0) or 0
                ),
                "airframe_breakup": int(bool(getattr(structural_event, "airframe_breakup", False))),
                "cause_event_id": _event_id(structural_event, "cause_event_id"),
            }
        )
        rows.append(row)
        standard_structural_keys.add(
            (int(row.get("chain_id", 0) or 0), int(row.get("target_id", 0) or 0))
        )

    for platform_event in list(getattr(engagement_events, "platform_consequence_events", []) or []):
        base_kwargs = _lethality_header_base_kwargs(
            episode=episode,
            step=step,
            sim_time_s=sim_time_s,
            event=platform_event,
            stage=chain_contract.STAGE_PLATFORM_CONSEQUENCE,
            source_event_kind="PlatformConsequenceEvent",
        )
        mission_before = _finite_float(
            getattr(platform_event, "mission_capability_before", float("nan"))
        )
        mission_after = _finite_float(
            getattr(platform_event, "mission_capability_after", float("nan"))
        )
        mobility_before = _finite_float(
            getattr(platform_event, "mobility_capability_before", float("nan"))
        )
        mobility_after = _finite_float(
            getattr(platform_event, "mobility_capability_after", float("nan"))
        )
        sensor_before = _finite_float(
            getattr(platform_event, "sensor_capability_before", float("nan"))
        )
        sensor_after = _finite_float(
            getattr(platform_event, "sensor_capability_after", float("nan"))
        )
        survivability_before = _finite_float(
            getattr(platform_event, "survivability_capability_before", float("nan"))
        )
        survivability_after = _finite_float(
            getattr(platform_event, "survivability_capability_after", float("nan"))
        )
        row = _lethality_base_row(**base_kwargs)
        row.update(
            {
                "mission_capability_before": mission_before,
                "mission_capability_after": mission_after,
                "mobility_capability_before": mobility_before,
                "mobility_capability_after": mobility_after,
                "sensor_capability_before": sensor_before,
                "sensor_capability_after": sensor_after,
                "survivability_margin_before": survivability_before,
                "survivability_margin_after": survivability_after,
                "system_health_delta": (
                    min(mission_after, mobility_after, sensor_after, survivability_after)
                    - min(mission_before, mobility_before, sensor_before, survivability_before)
                ),
                "mission_capability_delta": mission_after - mission_before,
                "mobility_capability_delta": mobility_after - mobility_before,
                "sensor_capability_delta": sensor_after - sensor_before,
                "survivability_margin_delta": survivability_after - survivability_before,
                "control_delta": _finite_float(
                    getattr(platform_event, "control_delta", float("nan"))
                ),
                "engine_delta": _finite_float(
                    getattr(platform_event, "engine_delta", float("nan"))
                ),
                "fuel_leak_delta": _finite_float(
                    getattr(platform_event, "fuel_leak_delta", float("nan"))
                ),
                "fire_state": str(getattr(platform_event, "fire_state", "") or ""),
                "aircraft_damage_state_before": str(
                    getattr(platform_event, "aircraft_damage_state_before", "") or ""
                ),
                "aircraft_damage_state_after": str(
                    getattr(platform_event, "aircraft_damage_state_after", "") or ""
                ),
                "aircraft_damage_state_delta": str(
                    getattr(platform_event, "aircraft_damage_state_delta", "") or ""
                ),
                "air_system_hit_flags": str(
                    getattr(platform_event, "air_system_hit_flags", "") or ""
                ),
                "air_system_spatial_scales": str(
                    getattr(platform_event, "air_system_spatial_scales", "") or ""
                ),
                "vulnerability_scale_trace": str(
                    getattr(platform_event, "vulnerability_scale_trace", "") or ""
                ),
                "mission_kill": int(bool(getattr(platform_event, "mission_kill", False))),
                "mobility_kill": int(bool(getattr(platform_event, "mobility_kill", False))),
                "sensor_kill": int(bool(getattr(platform_event, "sensor_kill", False))),
                "destroyed": int(bool(getattr(platform_event, "survivability_kill", False))),
                "loss_state": str(getattr(platform_event, "loss_state_to", "") or ""),
            }
        )
        rows.append(row)
        standard_platform_keys.add(
            (int(row.get("chain_id", 0) or 0), int(row.get("target_id", 0) or 0))
        )

    for lifecycle_event in list(getattr(engagement_events, "lifecycle_transition_events", []) or []):
        base_kwargs = _lethality_header_base_kwargs(
            episode=episode,
            step=step,
            sim_time_s=sim_time_s,
            event=lifecycle_event,
            stage=chain_contract.STAGE_LIFECYCLE,
            source_event_kind="LifecycleTransitionEvent",
        )
        row = _lethality_base_row(**base_kwargs)
        row.update(
            {
                "lifecycle_from": str(getattr(lifecycle_event, "lifecycle_from", "") or ""),
                "lifecycle_to": str(getattr(lifecycle_event, "lifecycle_to", "") or ""),
                "ground_lifecycle": str(getattr(lifecycle_event, "ground_lifecycle", "") or ""),
                "wreck_entity_id": _entity_id(getattr(lifecycle_event, "wreck_entity", None)),
                "debris_count": int(getattr(lifecycle_event, "debris_count", 0) or 0),
                "lifecycle_terminal": int(bool(getattr(lifecycle_event, "terminal", False))),
                "terminal_projection_id": _event_id(
                    lifecycle_event,
                    "terminal_projection_id",
                ),
            }
        )
        rows.append(row)
        standard_lifecycle_keys.add(
            (int(row.get("chain_id", 0) or 0), int(row.get("target_id", 0) or 0))
        )

    for effect in list(getattr(engagement_events, "effects_events", []) or []):
        effect_id = _event_id(effect, "event_id")
        trace = trace_by_effect.get(effect_id)
        chain_id = _event_id(trace, "chain_id") if trace is not None else effect_id
        munition_id = _entity_id(getattr(trace, "munition", None)) if trace is not None else 0
        if munition_id <= 0:
            munition_id = _entity_id(getattr(effect, "munition", None))
        target_id = _entity_id(getattr(effect, "target", None))
        evidence_level = _lethality_evidence_level(effect)
        base_kwargs = {
            "episode": episode,
            "step": step,
            "sim_time_s": sim_time_s,
            "chain_id": chain_id,
            "event_id": effect_id,
            "parent_event_id": _event_id(trace, "launch_event_id") if trace is not None else 0,
            "source_event_kind": "EffectsEvent",
            "source_event_id": effect_id,
            "munition_id": munition_id,
            "target_id": target_id,
            "evidence_level": evidence_level,
            "reason": "transitional_effects_event_projection",
        }
        fallback_key = (int(chain_id), int(munition_id))

        has_standard_nearest = fallback_key in standard_nearest_keys or (
            munition_id > 0 and int(munition_id) in standard_nearest_munition_ids
        )
        if not has_standard_nearest:
            nearest = _lethality_base_row(
                stage=chain_contract.STAGE_NEAREST_APPROACH,
                **base_kwargs,
            )
            nearest.update(
                {
                    "miss_distance_m": _finite_float(
                        getattr(effect, "miss_distance_m", float("nan"))
                    ),
                    "nearest_approach_time_s": _finite_float(
                        getattr(effect, "nearest_approach_time_s", float("nan"))
                    ),
                    "local_forward_m": _finite_float(
                        getattr(effect, "detonation_local_forward_m", float("nan"))
                    ),
                    "local_right_m": _finite_float(
                        getattr(effect, "detonation_local_right_m", float("nan"))
                    ),
                    "local_up_m": _finite_float(
                        getattr(effect, "detonation_local_up_m", float("nan"))
                    ),
                    "closure_mps": _finite_float(getattr(effect, "closure_mps", float("nan"))),
                }
            )
            rows.append(nearest)

        has_standard_fuze = fallback_key in standard_fuze_keys or (
            munition_id > 0 and int(munition_id) in standard_fuze_munition_ids
        )
        if not has_standard_fuze:
            fuze = _lethality_base_row(stage=chain_contract.STAGE_FUZE, **base_kwargs)
            fuze.update(
                {
                    "fuze_type": str(getattr(effect, "fuze_type", "") or ""),
                    "fuze_reliability": _finite_float(
                        getattr(effect, "fuze_effective_reliability", float("nan"))
                    ),
                    "fuze_expected_detonation_probability": _finite_float(
                        getattr(effect, "fuze_effective_reliability", float("nan"))
                    ),
                    "fuze_sampled_outcome": 1,
                    "fuze_trigger_radius_m": _finite_float(
                        getattr(effect, "fuze_trigger_radius_m", float("nan"))
                    ),
                    "fuze_sensor_opportunity_source": str(
                        getattr(effect, "fuze_sensor_opportunity_source", "") or ""
                    ),
                    "fuze_sensor_opportunity_score": _finite_float(
                        getattr(effect, "fuze_sensor_opportunity_score", float("nan"))
                    ),
                    "fuze_terminal_track_valid": int(
                        bool(getattr(effect, "fuze_terminal_track_valid", False))
                    ),
                    "fuze_target_detected": int(
                        bool(getattr(effect, "fuze_target_detected", False))
                    ),
                    "fuze_target_detection_source": str(
                        getattr(effect, "fuze_target_detection_source", "") or ""
                    ),
                    "fuze_target_detection_confidence": _finite_float(
                        getattr(effect, "fuze_target_detection_confidence", float("nan"))
                    ),
                    "fuze_target_detection_threshold": _finite_float(
                        getattr(effect, "fuze_target_detection_threshold", float("nan"))
                    ),
                    "detonation_point_source": str(
                        getattr(effect, "detonation_point_source", "") or ""
                    ),
                    "fuze_mechanism_coverage_score": _finite_float(
                        getattr(effect, "fuze_mechanism_coverage_score", float("nan"))
                    ),
                    "direct_hitbox_intersection": int(
                        bool(getattr(effect, "direct_hitbox_intersection", False))
                    ),
                }
            )
            rows.append(fuze)

        has_warhead_load = _effects_event_has_warhead_load(effect)
        if has_warhead_load and fallback_key not in standard_warhead_keys:
            warhead = _lethality_base_row(
                stage=chain_contract.STAGE_WARHEAD_MECHANISM,
                **base_kwargs,
            )
            warhead.update(
                {
                    "mechanism_family": str(getattr(effect, "effect_family", "") or ""),
                    "warhead_mass_kg": _finite_float(
                        getattr(effect, "warhead_mass_kg", float("nan"))
                    ),
                    "lethal_radius_m": _finite_float(
                        getattr(effect, "warhead_lethal_radius_m", float("nan"))
                    ),
                    "fragment_energy_j": _finite_float(
                        getattr(effect, "mechanism_fragment_energy_j", float("nan"))
                    ),
                    "fragment_density_per_m2": _finite_float(
                        getattr(effect, "mechanism_fragment_areal_density_per_m2", float("nan"))
                    ),
                    "blast_overpressure_kpa": _finite_float(
                        getattr(effect, "mechanism_blast_overpressure_kpa", float("nan"))
                    ),
                    "blast_impulse_kpa_ms": _finite_float(
                        getattr(effect, "mechanism_blast_impulse_kpa_ms", float("nan"))
                    ),
                    "blast_scaled_distance_m_kg13": _finite_float(
                        getattr(effect, "mechanism_blast_scaled_distance_m_kg13", float("nan"))
                    ),
                    "rod_cut_margin": _finite_float(
                        getattr(effect, "mechanism_rod_cut_margin", float("nan"))
                    ),
                    "penetration_margin": _finite_float(
                        getattr(effect, "mechanism_penetration_margin", float("nan"))
                    ),
                    "surface_incidence_cos": _finite_float(
                        getattr(effect, "mechanism_surface_incidence_cos", float("nan"))
                    ),
                }
            )
            rows.append(warhead)

        if has_warhead_load and fallback_key not in standard_spatial_keys:
            spatial = _lethality_base_row(
                stage=chain_contract.STAGE_SPATIAL_COVERAGE,
                **base_kwargs,
            )
            spatial.update(
                {
                    "projected_hitbox_count": int(
                        getattr(effect, "projected_hitbox_count", 0) or 0
                    ),
                    "spatial_sample_count": int(
                        getattr(effect, "warhead_spatial_sample_count", 0) or 0
                    ),
                    "spatial_hit_estimate": _finite_float(
                        getattr(effect, "warhead_spatial_hit_estimate", float("nan"))
                    ),
                    "spatial_hit_fraction": _finite_float(
                        getattr(effect, "warhead_spatial_hit_fraction", float("nan"))
                    ),
                    "spatial_energy_scale": _finite_float(
                        getattr(effect, "warhead_spatial_energy_scale", float("nan"))
                    ),
                    "spatial_pattern_scale": _finite_float(
                        getattr(effect, "warhead_spatial_pattern_scale", float("nan"))
                    ),
                }
            )
            rows.append(spatial)

        if has_warhead_load and fallback_key not in standard_component_keys:
            component = _lethality_base_row(
                stage=chain_contract.STAGE_COMPONENT_LOAD,
                **base_kwargs,
            )
            component_hit_count = int(getattr(effect, "component_hit_count", 0) or 0)
            component_rows = list(getattr(effect, "component_mechanism_load_rows", []) or [])
            if component_hit_count <= 0 and component_rows:
                component_hit_count = int(
                    sum(1 for item in component_rows if bool(getattr(item, "direct_hit", False)))
                )
            component.update({"component_hit_count": int(component_hit_count)})
            rows.append(component)

    for report in list(getattr(engagement_events, "damage_reports", []) or []):
        report_id = _event_id(report, "report_id")
        source_event_id = _event_id(report, "source_event_id")
        trace = trace_by_damage.get(report_id) or trace_by_effect.get(source_event_id)
        source_effect = effect_by_id.get(source_event_id)
        chain_id = (
            _event_id(trace, "chain_id") if trace is not None else source_event_id or report_id
        )
        munition_id = (
            _entity_id(getattr(trace, "munition", None))
            if trace is not None
            else _entity_id(getattr(source_effect, "munition", None))
        )
        target_id = _entity_id(getattr(report, "target", None)) or _entity_id(
            getattr(source_effect, "target", None)
        )
        evidence_level = _lethality_evidence_level(source_effect)
        base_kwargs = {
            "episode": episode,
            "step": step,
            "sim_time_s": sim_time_s,
            "chain_id": chain_id,
            "event_id": report_id,
            "parent_event_id": source_event_id,
            "source_event_kind": "DamageReport",
            "source_event_id": report_id,
            "munition_id": munition_id,
            "target_id": target_id,
            "evidence_level": evidence_level,
            "reason": "transitional_damage_report_projection",
        }

        capability_deltas = _parse_platform_damage_state_delta(
            getattr(report, "platform_damage_state_delta", "")
        )
        platform_key = (int(chain_id), int(target_id))
        if platform_key not in standard_platform_keys:
            platform = _lethality_base_row(
                stage=chain_contract.STAGE_PLATFORM_CONSEQUENCE,
                **base_kwargs,
            )
            platform.update(
                {
                    "damage_report_id": report_id,
                    "system_health_delta": _finite_float(
                        getattr(report, "system_health_delta", float("nan"))
                    ),
                    **capability_deltas,
                    "mission_kill": int(bool(getattr(report, "mission_kill", False))),
                    "mobility_kill": int(bool(getattr(report, "mobility_kill", False))),
                    "sensor_kill": int(bool(getattr(report, "sensor_kill", False))),
                    "destroyed": int(bool(getattr(report, "destroyed", False))),
                    "loss_state": str(getattr(report, "loss_state_to", "") or ""),
                }
            )
            rows.append(platform)

        lifecycle_key = (int(chain_id), int(target_id))
        if lifecycle_key not in standard_lifecycle_keys:
            lifecycle = _lethality_base_row(stage=chain_contract.STAGE_LIFECYCLE, **base_kwargs)
            lifecycle.update(
                {
                    "damage_report_id": report_id,
                    "destroyed": int(bool(getattr(report, "destroyed", False))),
                    "loss_state": str(getattr(report, "loss_state_to", "") or ""),
                }
            )
            rows.append(lifecycle)

    stage_order = {stage: index for index, stage in enumerate(chain_contract.CANONICAL_STAGES)}
    return sorted(
        rows,
        key=lambda row: (
            int(row.get("chain_id", 0) or 0),
            stage_order.get(str(row.get("stage", "") or ""), len(stage_order)),
            int(row.get("event_id", 0) or 0),
            int(row.get("source_event_id", 0) or 0),
        ),
    )


def _append_unique_lethality_chain_rows(
    out: list[dict[str, Any]],
    seen: set[tuple[int, int, int, str, str, int]],
    rows: list[dict[str, Any]],
) -> None:
    standard_source_by_stage = {
        chain_contract.STAGE_NEAREST_APPROACH: "NearestApproachEvent",
        chain_contract.STAGE_FUZE: "FuzeEvaluationEvent",
    }

    def same_episode_munition_stage(lhs: dict[str, Any], rhs: dict[str, Any]) -> bool:
        return (
            int(lhs.get("episode", 0) or 0) == int(rhs.get("episode", 0) or 0)
            and int(lhs.get("munition_id", 0) or 0) == int(rhs.get("munition_id", 0) or 0)
            and str(lhs.get("stage", "") or "") == str(rhs.get("stage", "") or "")
        )

    for row in rows:
        stage = str(row.get("stage", "") or "")
        source_event_kind = str(row.get("source_event_kind", "") or "")
        standard_source = standard_source_by_stage.get(stage)
        if standard_source:
            if source_event_kind == "EffectsEvent" and any(
                same_episode_munition_stage(existing, row)
                and str(existing.get("source_event_kind", "") or "") == standard_source
                for existing in out
            ):
                continue
            if source_event_kind == standard_source:
                out[:] = [
                    existing
                    for existing in out
                    if not (
                        same_episode_munition_stage(existing, row)
                        and str(existing.get("source_event_kind", "") or "") == "EffectsEvent"
                    )
                ]
        key = (
            int(row.get("episode", 0) or 0),
            int(row.get("chain_id", 0) or 0),
            int(row.get("event_id", 0) or 0),
            stage,
            source_event_kind,
            int(row.get("source_event_id", 0) or 0),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(dict(row))


def _append_unique_lethality_component_response_rows(
    out: list[dict[str, Any]],
    seen: set[tuple[int, int, int, int, int]],
    rows: list[dict[str, Any]],
) -> None:
    for row in rows:
        key = (
            int(row.get("episode", 0) or 0),
            int(row.get("chain_id", 0) or 0),
            int(row.get("event_id", 0) or 0),
            int(row.get("source_event_id", 0) or 0),
            int(row.get("source_row_index", 0) or 0),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(dict(row))


def _project_current_lethality_chain_rows(
    *, episode: int, step: int, sim_time_s: float, sim: Any
) -> list[dict[str, Any]]:
    try:
        engagement_events = sim.export_recent_engagement_events()
    except Exception:
        return []
    return _lethality_chain_rows(
        episode=int(episode),
        step=int(step),
        sim_time_s=float(sim_time_s),
        engagement_events=engagement_events,
    )


def _project_current_lethality_component_response_rows(
    *, episode: int, step: int, sim_time_s: float, sim: Any
) -> list[dict[str, Any]]:
    try:
        engagement_events = sim.export_recent_engagement_events()
    except Exception:
        return []
    return _lethality_component_response_rows(
        episode=int(episode),
        step=int(step),
        sim_time_s=float(sim_time_s),
        engagement_events=engagement_events,
    )
