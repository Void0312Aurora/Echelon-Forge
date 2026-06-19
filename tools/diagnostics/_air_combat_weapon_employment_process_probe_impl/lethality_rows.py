"""Low-level lethality-chain row projection helpers."""

from __future__ import annotations

from typing import Any

from tools.diagnostics import lethality_chain_contract as chain_contract
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.schema import (
    LETHALITY_CHAIN_SCHEMA_VERSION,
    _entity_id,
    _event_id,
    _finite_float,
)


def _lethality_base_row(
    *,
    episode: int,
    step: int,
    sim_time_s: float,
    chain_id: int,
    event_id: int,
    parent_event_id: int,
    stage: str,
    source_event_kind: str,
    source_event_id: int,
    munition_id: int,
    target_id: int,
    evidence_level: str,
    reason: str,
    observation_mode: str = chain_contract.OBSERVATION_MODE_SAMPLED_RUNTIME,
    consumer_visibility: str = chain_contract.CONSUMER_VISIBILITY_DIAGNOSTICS_AND_TRAINING,
    status: str = "projected",
) -> dict[str, Any]:
    row = {
        "schema_version": int(LETHALITY_CHAIN_SCHEMA_VERSION),
        "episode": int(episode),
        "step": int(step),
        "sim_time_s": float(sim_time_s),
        "chain_id": int(chain_id),
        "event_id": int(event_id),
        "parent_event_id": int(parent_event_id),
        "stage": str(stage),
        "status": str(status),
        "reason": str(reason),
        "source_event_kind": str(source_event_kind),
        "source_event_id": int(source_event_id),
        "munition_id": int(munition_id),
        "target_id": int(target_id),
        "evidence_level": str(evidence_level),
        "observation_mode": str(observation_mode),
        "consumer_visibility": str(consumer_visibility),
        "miss_distance_m": float("nan"),
        "nearest_approach_time_s": float("nan"),
        "local_forward_m": float("nan"),
        "local_right_m": float("nan"),
        "local_up_m": float("nan"),
        "closure_mps": float("nan"),
        "aspect_bucket": "",
        "fuze_type": "",
        "fuze_armed": 0,
        "fuze_triggered": 0,
        "fuze_failure_reason": "",
        "fuze_delay_s": float("nan"),
        "fuze_reliability": float("nan"),
        "fuze_sample": float("nan"),
        "fuze_expected_detonation_probability": float("nan"),
        "fuze_sampled_outcome": 0,
        "fuze_trigger_radius_m": float("nan"),
        "fuze_sensor_opportunity_source": "",
        "fuze_sensor_opportunity_score": float("nan"),
        "fuze_terminal_track_valid": 0,
        "fuze_target_detected": 0,
        "fuze_target_detection_source": "",
        "fuze_target_detection_confidence": float("nan"),
        "fuze_target_detection_threshold": float("nan"),
        "detonation_point_source": "",
        "fuze_mechanism_coverage_score": float("nan"),
        "contact_surface_distance_m": float("nan"),
        "contact_penetration_depth_m": float("nan"),
        "contact_surface_tolerance_m": float("nan"),
        "contact_inside_hitbox": 0,
        "direct_hitbox_intersection": 0,
        "mechanism_family": "",
        "warhead_mass_kg": float("nan"),
        "lethal_radius_m": float("nan"),
        "fragment_energy_j": float("nan"),
        "fragment_density_per_m2": float("nan"),
        "blast_overpressure_kpa": float("nan"),
        "blast_impulse_kpa_ms": float("nan"),
        "blast_scaled_distance_m_kg13": float("nan"),
        "rod_cut_margin": float("nan"),
        "penetration_margin": float("nan"),
        "surface_incidence_cos": float("nan"),
        "projected_hitbox_count": 0,
        "spatial_sample_count": 0,
        "spatial_hit_estimate": float("nan"),
        "spatial_hit_fraction": float("nan"),
        "spatial_energy_scale": float("nan"),
        "spatial_pattern_scale": float("nan"),
        "component_hit_count": 0,
        "component_name": "",
        "component_system": "",
        "component_direct_hit": 0,
        "component_distance_m": float("nan"),
        "component_effect_scale": float("nan"),
        "component_load_source": "",
        "component_integrity_before": float("nan"),
        "component_integrity_after": float("nan"),
        "component_failure_mode": "",
        "component_failure_severity": float("nan"),
        "component_failure_probability": float("nan"),
        "component_failure_sample": float("nan"),
        "breakup_state": "",
        "break_mode": "",
        "detached_part_ref": "",
        "detached_part_count": 0,
        "airframe_breakup": 0,
        "cause_event_id": 0,
        "damage_report_id": 0,
        "mission_capability_before": float("nan"),
        "mission_capability_after": float("nan"),
        "mobility_capability_before": float("nan"),
        "mobility_capability_after": float("nan"),
        "sensor_capability_before": float("nan"),
        "sensor_capability_after": float("nan"),
        "survivability_margin_before": float("nan"),
        "survivability_margin_after": float("nan"),
        "system_health_delta": float("nan"),
        "mission_capability_delta": float("nan"),
        "mobility_capability_delta": float("nan"),
        "sensor_capability_delta": float("nan"),
        "survivability_margin_delta": float("nan"),
        "control_delta": float("nan"),
        "engine_delta": float("nan"),
        "fuel_leak_delta": float("nan"),
        "fire_state": "",
        "aircraft_damage_state_before": "",
        "aircraft_damage_state_after": "",
        "aircraft_damage_state_delta": "",
        "air_system_hit_flags": "",
        "air_system_spatial_scales": "",
        "vulnerability_scale_trace": "",
        "mission_kill": 0,
        "mobility_kill": 0,
        "sensor_kill": 0,
        "destroyed": 0,
        "loss_state": "",
        "lifecycle_from": "",
        "lifecycle_to": "",
        "ground_lifecycle": "",
        "wreck_entity_id": 0,
        "debris_count": 0,
        "lifecycle_terminal": 0,
        "terminal_projection_id": 0,
    }
    return row


def _lethality_header_base_kwargs(
    *,
    episode: int,
    step: int,
    sim_time_s: float,
    event: Any,
    stage: str,
    source_event_kind: str,
) -> dict[str, Any]:
    header = getattr(event, "header", None)
    event_id = _event_id(header, "event_id")
    chain_id = _event_id(header, "chain_id") or event_id
    return {
        "episode": episode,
        "step": step,
        "sim_time_s": sim_time_s,
        "chain_id": chain_id,
        "event_id": event_id,
        "parent_event_id": _event_id(header, "parent_event_id"),
        "stage": stage,
        "source_event_kind": source_event_kind,
        "source_event_id": event_id,
        "munition_id": _entity_id(getattr(header, "munition", None)),
        "target_id": _entity_id(getattr(header, "target", None)),
        "evidence_level": str(getattr(header, "evidence_level", "") or "uncalibrated"),
        "observation_mode": str(
            getattr(header, "observation_mode", "")
            or chain_contract.OBSERVATION_MODE_SAMPLED_RUNTIME
        ),
        "consumer_visibility": str(
            getattr(header, "consumer_visibility", "")
            or chain_contract.CONSUMER_VISIBILITY_DIAGNOSTICS_AND_TRAINING
        ),
        "reason": str(getattr(header, "reason", "") or ""),
        "status": str(getattr(header, "status", "") or "observed"),
    }


def _component_mechanism_row_projection(row: Any) -> dict[str, Any]:
    return {
        "component_integrity_before": _finite_float(
            getattr(row, "component_integrity_before", float("nan"))
        ),
        "component_integrity_after": _finite_float(
            getattr(row, "component_integrity_after", float("nan"))
        ),
        "component_failure_mode": str(getattr(row, "component_failure_primary_mode", "") or ""),
        "component_failure_severity": _finite_float(
            getattr(row, "component_failure_primary_mode_severity", float("nan"))
        ),
        "component_failure_probability": _finite_float(
            getattr(row, "component_failure_probability", float("nan"))
        ),
        "component_failure_sample": _finite_float(
            getattr(row, "component_failure_sample", float("nan"))
        ),
    }


def _component_mechanism_rows_by_effect_id(engagement_events: Any) -> dict[int, list[Any]]:
    rows_by_effect_id: dict[int, list[Any]] = {}
    for effect in list(getattr(engagement_events, "effects_events", []) or []):
        effect_id = _event_id(effect, "event_id")
        if effect_id <= 0:
            continue
        rows_by_effect_id[effect_id] = list(
            getattr(effect, "component_mechanism_load_rows", []) or []
        )
    return rows_by_effect_id


def _match_component_mechanism_row(
    candidates: list[Any],
    *,
    component_name: str,
    component_system: str,
) -> Any | None:
    for row in candidates:
        if (
            str(getattr(row, "component_name", "") or "") == component_name
            and str(getattr(row, "component_system", "") or "") == component_system
        ):
            return row
    return None
