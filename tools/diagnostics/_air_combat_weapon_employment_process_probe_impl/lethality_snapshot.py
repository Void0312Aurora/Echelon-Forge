"""Lethality-chain snapshot aggregation helpers."""

from __future__ import annotations

import math
from typing import Any

from tools.diagnostics import lethality_chain_contract as chain_contract
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.schema import (
    _finite_float,
    _stable_json,
)


def _lethality_chain_snapshot_columns(chain_rows: list[dict[str, Any]]) -> dict[str, Any]:
    def last_stage(stage: str) -> dict[str, Any] | None:
        matches = [row for row in chain_rows if str(row.get("stage", "")) == str(stage)]
        return matches[-1] if matches else None

    nearest = last_stage(chain_contract.STAGE_NEAREST_APPROACH) or {}
    fuze = last_stage(chain_contract.STAGE_FUZE) or {}
    warhead = last_stage(chain_contract.STAGE_WARHEAD_MECHANISM) or {}
    spatial = last_stage(chain_contract.STAGE_SPATIAL_COVERAGE) or {}
    component = last_stage(chain_contract.STAGE_COMPONENT_LOAD) or {}
    component_damage = last_stage(chain_contract.STAGE_COMPONENT_DAMAGE) or {}
    platform = last_stage(chain_contract.STAGE_PLATFORM_CONSEQUENCE) or {}
    lifecycle = last_stage(chain_contract.STAGE_LIFECYCLE) or {}
    component_failure = component_damage or component
    local = (
        _finite_float(nearest.get("local_forward_m", float("nan"))),
        _finite_float(nearest.get("local_right_m", float("nan"))),
        _finite_float(nearest.get("local_up_m", float("nan"))),
    )
    local_norm = (
        math.sqrt(sum(value * value for value in local))
        if all(math.isfinite(value) for value in local)
        else float("nan")
    )
    return {
        "lethality_chain_row_count": int(len(chain_rows)),
        "lethality_chain_chain_count": int(
            len({int(row.get("chain_id", 0) or 0) for row in chain_rows})
        ),
        "lethality_chain_stages_json": _stable_json(
            sorted({str(row.get("stage", "")) for row in chain_rows})
        ),
        "lethality_chain_miss_distance_m": _finite_float(
            nearest.get("miss_distance_m", float("nan"))
        ),
        "lethality_chain_nearest_approach_time_s": _finite_float(
            nearest.get("nearest_approach_time_s", float("nan"))
        ),
        "lethality_chain_local_forward_m": local[0],
        "lethality_chain_local_right_m": local[1],
        "lethality_chain_local_up_m": local[2],
        "lethality_chain_local_norm_m": local_norm,
        "lethality_chain_closure_mps": _finite_float(nearest.get("closure_mps", float("nan"))),
        "lethality_chain_aspect_bucket": str(nearest.get("aspect_bucket", "") or ""),
        "lethality_chain_fuze_type": str(fuze.get("fuze_type", "") or ""),
        "lethality_chain_fuze_armed": int(fuze.get("fuze_armed", 0) or 0),
        "lethality_chain_fuze_triggered": int(fuze.get("fuze_triggered", 0) or 0),
        "lethality_chain_fuze_failure_reason": str(fuze.get("fuze_failure_reason", "") or ""),
        "lethality_chain_fuze_delay_s": _finite_float(fuze.get("fuze_delay_s", float("nan"))),
        "lethality_chain_fuze_reliability": _finite_float(
            fuze.get("fuze_reliability", float("nan"))
        ),
        "lethality_chain_fuze_sample": _finite_float(fuze.get("fuze_sample", float("nan"))),
        "lethality_chain_fuze_expected_detonation_probability": _finite_float(
            fuze.get("fuze_expected_detonation_probability", float("nan"))
        ),
        "lethality_chain_fuze_sampled_outcome": int(fuze.get("fuze_sampled_outcome", 0) or 0),
        "lethality_chain_fuze_trigger_radius_m": _finite_float(
            fuze.get("fuze_trigger_radius_m", float("nan"))
        ),
        "lethality_chain_fuze_sensor_opportunity_source": str(
            fuze.get("fuze_sensor_opportunity_source", "") or ""
        ),
        "lethality_chain_fuze_sensor_opportunity_score": _finite_float(
            fuze.get("fuze_sensor_opportunity_score", float("nan"))
        ),
        "lethality_chain_fuze_terminal_track_valid": int(
            fuze.get("fuze_terminal_track_valid", 0) or 0
        ),
        "lethality_chain_fuze_target_detected": int(fuze.get("fuze_target_detected", 0) or 0),
        "lethality_chain_fuze_target_detection_source": str(
            fuze.get("fuze_target_detection_source", "") or ""
        ),
        "lethality_chain_fuze_target_detection_confidence": _finite_float(
            fuze.get("fuze_target_detection_confidence", float("nan"))
        ),
        "lethality_chain_fuze_target_detection_threshold": _finite_float(
            fuze.get("fuze_target_detection_threshold", float("nan"))
        ),
        "lethality_chain_detonation_point_source": str(
            fuze.get("detonation_point_source", "") or ""
        ),
        "lethality_chain_fuze_mechanism_coverage_score": _finite_float(
            fuze.get("fuze_mechanism_coverage_score", float("nan"))
        ),
        "lethality_chain_direct_hitbox_intersection": int(
            fuze.get("direct_hitbox_intersection", 0) or 0
        ),
        "lethality_chain_mechanism_family": str(warhead.get("mechanism_family", "") or ""),
        "lethality_chain_fragment_energy_j": _finite_float(
            warhead.get("fragment_energy_j", float("nan"))
        ),
        "lethality_chain_fragment_density_per_m2": _finite_float(
            warhead.get("fragment_density_per_m2", float("nan"))
        ),
        "lethality_chain_blast_overpressure_kpa": _finite_float(
            warhead.get("blast_overpressure_kpa", float("nan"))
        ),
        "lethality_chain_rod_cut_margin": _finite_float(
            warhead.get("rod_cut_margin", float("nan"))
        ),
        "lethality_chain_projected_hitbox_count": int(
            spatial.get("projected_hitbox_count", 0) or 0
        ),
        "lethality_chain_component_hit_count": int(component.get("component_hit_count", 0) or 0),
        "lethality_chain_component_name": str(component.get("component_name", "") or ""),
        "lethality_chain_component_system": str(component.get("component_system", "") or ""),
        "lethality_chain_component_load_source": str(
            component.get("component_load_source", "") or ""
        ),
        "lethality_chain_component_rod_cut_margin": _finite_float(
            component.get("rod_cut_margin", float("nan"))
        ),
        "lethality_chain_component_damage_count": int(
            sum(
                1
                for row in chain_rows
                if str(row.get("stage", "")) == chain_contract.STAGE_COMPONENT_DAMAGE
            )
        ),
        "lethality_chain_component_damage_name": str(
            component_damage.get("component_name", "") or ""
        ),
        "lethality_chain_component_damage_system": str(
            component_damage.get("component_system", "") or ""
        ),
        "lethality_chain_component_integrity_before": _finite_float(
            component_failure.get("component_integrity_before", float("nan"))
        ),
        "lethality_chain_component_integrity_after": _finite_float(
            component_failure.get("component_integrity_after", float("nan"))
        ),
        "lethality_chain_component_failure_mode": str(
            component_failure.get("component_failure_mode", "") or ""
        ),
        "lethality_chain_component_failure_severity": _finite_float(
            component_failure.get("component_failure_severity", float("nan"))
        ),
        "lethality_chain_component_failure_probability": _finite_float(
            component_failure.get("component_failure_probability", float("nan"))
        ),
        "lethality_chain_component_failure_sample": _finite_float(
            component_failure.get("component_failure_sample", float("nan"))
        ),
        "lethality_chain_damage_report_id": int(
            platform.get("damage_report_id", lifecycle.get("damage_report_id", 0)) or 0
        ),
        "lethality_chain_system_health_delta": _finite_float(
            platform.get("system_health_delta", float("nan"))
        ),
        "lethality_chain_mission_capability_before": _finite_float(
            platform.get("mission_capability_before", float("nan"))
        ),
        "lethality_chain_mission_capability_after": _finite_float(
            platform.get("mission_capability_after", float("nan"))
        ),
        "lethality_chain_mission_capability_delta": _finite_float(
            platform.get("mission_capability_delta", float("nan"))
        ),
        "lethality_chain_mobility_capability_before": _finite_float(
            platform.get("mobility_capability_before", float("nan"))
        ),
        "lethality_chain_mobility_capability_after": _finite_float(
            platform.get("mobility_capability_after", float("nan"))
        ),
        "lethality_chain_mobility_capability_delta": _finite_float(
            platform.get("mobility_capability_delta", float("nan"))
        ),
        "lethality_chain_sensor_capability_before": _finite_float(
            platform.get("sensor_capability_before", float("nan"))
        ),
        "lethality_chain_sensor_capability_after": _finite_float(
            platform.get("sensor_capability_after", float("nan"))
        ),
        "lethality_chain_sensor_capability_delta": _finite_float(
            platform.get("sensor_capability_delta", float("nan"))
        ),
        "lethality_chain_survivability_margin_before": _finite_float(
            platform.get("survivability_margin_before", float("nan"))
        ),
        "lethality_chain_survivability_margin_after": _finite_float(
            platform.get("survivability_margin_after", float("nan"))
        ),
        "lethality_chain_survivability_margin_delta": _finite_float(
            platform.get("survivability_margin_delta", float("nan"))
        ),
        "lethality_chain_control_delta": _finite_float(platform.get("control_delta", float("nan"))),
        "lethality_chain_engine_delta": _finite_float(platform.get("engine_delta", float("nan"))),
        "lethality_chain_fuel_leak_delta": _finite_float(
            platform.get("fuel_leak_delta", float("nan"))
        ),
        "lethality_chain_fire_state": str(platform.get("fire_state", "") or ""),
        "lethality_chain_aircraft_damage_state_before": str(
            platform.get("aircraft_damage_state_before", "") or ""
        ),
        "lethality_chain_aircraft_damage_state_after": str(
            platform.get("aircraft_damage_state_after", "") or ""
        ),
        "lethality_chain_aircraft_damage_state_delta": str(
            platform.get("aircraft_damage_state_delta", "") or ""
        ),
        "lethality_chain_air_system_hit_flags": str(platform.get("air_system_hit_flags", "") or ""),
        "lethality_chain_air_system_spatial_scales": str(
            platform.get("air_system_spatial_scales", "") or ""
        ),
        "lethality_chain_vulnerability_scale_trace": str(
            platform.get("vulnerability_scale_trace", "") or ""
        ),
        "lethality_chain_mission_kill": int(platform.get("mission_kill", 0) or 0),
        "lethality_chain_mobility_kill": int(platform.get("mobility_kill", 0) or 0),
        "lethality_chain_sensor_kill": int(platform.get("sensor_kill", 0) or 0),
        "lethality_chain_destroyed": int(
            platform.get("destroyed", lifecycle.get("destroyed", 0)) or 0
        ),
        "lethality_chain_loss_state": str(
            platform.get("loss_state", lifecycle.get("loss_state", "")) or ""
        ),
    }
