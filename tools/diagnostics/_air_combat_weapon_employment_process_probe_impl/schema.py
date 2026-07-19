"""Shared schema constants and scalar helpers for the process probe."""

from __future__ import annotations

import json
import math
from typing import Any

import numpy as np

from gym_envs.scenario_loader.reward_runtime.air_combat import classify_air_combat_c2_roe_event
from python.runtime_bootstrap import resolve_repo_path
from tools.diagnostics import lethality_chain_contract as chain_contract

DEFAULT_SCENARIO = resolve_repo_path(
    "scenarios",
    "air_combat",
    "1v1",
    "air_combat_1v1_stage0_drone_weapon_employment_v1.json",
)
DEFAULT_TRAIN_CONFIG = resolve_repo_path(
    "examples",
    "config",
    "training",
    "active",
    "air_combat",
    "air_combat_1v1_stage0_drone_weapon_employment_world_batch_probe_v1.json",
)


FULL_ACTION_COLUMNS = {
    "pitch": 0,
    "roll": 1,
    "rudder": 2,
    "throttle": 3,
    "tms_up": 12,
    "radar_active": 9,
    "master_arm": 13,
    "fire_weapon": 14,
    "fire_gun": 15,
    "weapon_select": 16,
}
HYBRID_ACTION_COLUMNS = {
    "pitch": 0,
    "roll": 1,
    "rudder": 2,
    "throttle": 3,
    "radar_active": 6,
    "tms_up": 7,
    "master_arm": 8,
    "fire_weapon": 9,
    "fire_gun": 10,
    "weapon_select": 11,
}
ACTION_SIGNAL_NAMES = tuple(FULL_ACTION_COLUMNS.keys())
HYBRID_BINARY_POLICY_SIGNAL_NAMES = (
    "radar_active",
    "tms_up",
    "master_arm",
    "fire_weapon",
    "fire_gun",
)
FIRE_MASK_COMPONENT_NAMES = (
    "fire_mask_c2_authorized",
    "fire_mask_target_present",
    "fire_mask_shot_budget_available",
    "fire_mask_not_pending_assessment",
    "fire_mask_weapon_ready",
    "fire_mask_ammo_available",
    "fire_mask_reattack_allowed",
)
TARGET_DAMAGE_CONSEQUENCE_REWARD_PREFIX = "air_combat_target_damage_consequence_"
SELF_DAMAGE_CONSEQUENCE_REWARD_PREFIX = "air_combat_self_damage_consequence_"
LETHALITY_CHAIN_CONTRACT_SCHEMA_VERSION = chain_contract.CONTRACT_SCHEMA_VERSION
LETHALITY_CHAIN_SCHEMA_VERSION = chain_contract.DIAGNOSTIC_ROW_SCHEMA_VERSION
LETHALITY_CHAIN_STAGES = chain_contract.DIAGNOSTIC_ROW_STAGES
LETHALITY_CHAIN_ROW_FIELDS = (
    "schema_version",
    "episode",
    "step",
    "sim_time_s",
    "chain_id",
    "event_id",
    "parent_event_id",
    "stage",
    "status",
    "reason",
    "source_event_kind",
    "source_event_id",
    "munition_id",
    "target_id",
    "evidence_level",
    "observation_mode",
    "consumer_visibility",
    "miss_distance_m",
    "nearest_approach_time_s",
    "local_forward_m",
    "local_right_m",
    "local_up_m",
    "closure_mps",
    "aspect_bucket",
    "fuze_type",
    "fuze_armed",
    "fuze_triggered",
    "fuze_failure_reason",
    "fuze_delay_s",
    "fuze_reliability",
    "fuze_sample",
    "fuze_expected_detonation_probability",
    "fuze_sampled_outcome",
    "fuze_trigger_radius_m",
    "fuze_sensor_opportunity_source",
    "fuze_sensor_opportunity_score",
    "fuze_terminal_track_valid",
    "fuze_target_detected",
    "fuze_target_detection_source",
    "fuze_target_detection_confidence",
    "fuze_target_detection_threshold",
    "detonation_point_source",
    "fuze_mechanism_coverage_score",
    "contact_surface_distance_m",
    "contact_penetration_depth_m",
    "contact_surface_tolerance_m",
    "contact_inside_hitbox",
    "direct_hitbox_intersection",
    "mechanism_family",
    "warhead_mass_kg",
    "lethal_radius_m",
    "fragment_energy_j",
    "fragment_density_per_m2",
    "blast_overpressure_kpa",
    "blast_impulse_kpa_ms",
    "blast_scaled_distance_m_kg13",
    "rod_cut_margin",
    "penetration_margin",
    "surface_incidence_cos",
    "projected_hitbox_count",
    "spatial_sample_count",
    "spatial_hit_estimate",
    "spatial_hit_fraction",
    "spatial_energy_scale",
    "spatial_pattern_scale",
    "component_hit_count",
    "component_name",
    "component_system",
    "component_direct_hit",
    "component_distance_m",
    "component_effect_scale",
    "component_spatial_intersection_fraction",
    "component_pattern_weight",
    "component_orientation_weight",
    "component_receiver_exposure_fraction",
    "component_armor_transmission",
    "component_sampling_confidence",
    "component_load_intensity_scale",
    "component_load_source",
    "component_integrity_before",
    "component_integrity_after",
    "component_failure_mode",
    "component_failure_severity",
    "component_failure_probability",
    "component_failure_sample",
    "breakup_state",
    "break_mode",
    "detached_part_ref",
    "detached_part_count",
    "airframe_breakup",
    "cause_event_id",
    "damage_report_id",
    "mission_capability_before",
    "mission_capability_after",
    "mobility_capability_before",
    "mobility_capability_after",
    "sensor_capability_before",
    "sensor_capability_after",
    "survivability_margin_before",
    "survivability_margin_after",
    "system_health_delta",
    "mission_capability_delta",
    "mobility_capability_delta",
    "sensor_capability_delta",
    "survivability_margin_delta",
    "control_delta",
    "engine_delta",
    "fuel_leak_delta",
    "fire_state",
    "aircraft_damage_state_before",
    "aircraft_damage_state_after",
    "aircraft_damage_state_delta",
    "air_system_hit_flags",
    "air_system_spatial_scales",
    "vulnerability_scale_trace",
    "mission_kill",
    "mobility_kill",
    "sensor_kill",
    "destroyed",
    "loss_state",
    "lifecycle_from",
    "lifecycle_to",
    "ground_lifecycle",
    "wreck_entity_id",
    "debris_count",
    "lifecycle_terminal",
    "terminal_projection_id",
)


def _action_columns_for_mode(action_mode: str) -> dict[str, int]:
    mode = str(action_mode)
    if mode == "air_combat_hybrid_v1":
        return HYBRID_ACTION_COLUMNS
    return FULL_ACTION_COLUMNS


def _finite_float(value: Any, default: float = float("nan")) -> float:
    try:
        out = float(value)
    except Exception:
        return float(default)
    return out if math.isfinite(out) else float(default)


def _clamp_unit(value: Any) -> float:
    return float(np.clip(_finite_float(value, 0.0), 0.0, 1.0))


def _positive_finite(value: Any) -> bool:
    number = _finite_float(value, float("nan"))
    return math.isfinite(number) and number > 0.0


def _bool_int(value: Any) -> int:
    if isinstance(value, str):
        return int(value.strip().lower() in {"1", "true", "yes", "on"})
    return int(bool(value))


def _stable_json(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    except Exception:
        return ""


def _entity_id(value: Any) -> int:
    try:
        return int(getattr(value, "entity_id", value) or 0)
    except Exception:
        return 0


def _event_id(value: Any, name: str) -> int:
    try:
        return int(getattr(value, name, 0) or 0)
    except Exception:
        return 0


def _reward_terms_prefix_total(reward_terms: Any, prefix: str) -> float:
    if not isinstance(reward_terms, dict):
        return 0.0
    total = 0.0
    for key, value in reward_terms.items():
        if str(key).startswith(prefix):
            total += _finite_float(value, 0.0)
    return float(total)


def _damage_consequence_reward_columns(reward_terms: Any) -> dict[str, float]:
    target_total = _reward_terms_prefix_total(reward_terms, TARGET_DAMAGE_CONSEQUENCE_REWARD_PREFIX)
    self_total = _reward_terms_prefix_total(reward_terms, SELF_DAMAGE_CONSEQUENCE_REWARD_PREFIX)
    return {
        "damage_consequence_reward_total": float(target_total + self_total),
        "target_damage_consequence_reward_total": float(target_total),
        "self_damage_consequence_reward_total": float(self_total),
    }


def _launch_window_config_from_train_config(
    train_config: dict[str, Any] | None,
) -> dict[str, float]:
    hyper = train_config.get("hyperparameters", {}) if isinstance(train_config, dict) else {}
    if not isinstance(hyper, dict):
        hyper = {}
    return {
        "min_range_m": _finite_float(
            hyper.get("first_event_launch_window_min_range_m", 0.0), 0.0
        ),
        "max_range_m": _finite_float(
            hyper.get("first_event_launch_window_max_range_m", 0.0), 0.0
        ),
        "max_track_age_s": _finite_float(
            hyper.get("first_event_launch_window_max_track_age_s", float("inf")),
            float("inf"),
        ),
        "min_window_age_steps": _finite_float(
            hyper.get("first_event_launch_window_min_window_age_steps", 1),
            1.0,
        ),
    }


def _unit_id_set(sim) -> set[int]:
    out: set[int] = set()
    try:
        for unit in sim.get_all_units():
            out.add(int(getattr(unit, "id", 0)))
    except Exception:
        pass
    return out


def _target_track(truth, target_id: int):
    for track in getattr(truth, "contacts", []) or []:
        try:
            if int(getattr(track, "id", 0)) == int(target_id):
                return track
        except Exception:
            continue
    return None


def _distance_m(sim, blue_id: int, target_id: int) -> float:
    try:
        bx, by, bz = sim.get_unit_position(int(blue_id))
        tx, ty, tz = sim.get_unit_position(int(target_id))
        dx = float(tx) - float(bx)
        dy = float(ty) - float(by)
        dz = float(tz) - float(bz)
        return float(math.sqrt(dx * dx + dy * dy + dz * dz))
    except Exception:
        return float("nan")


def _health_current(sim, entity_id: int) -> float:
    try:
        health = sim.get_unit_health(int(entity_id))
        if health:
            return _finite_float(health[0])
    except Exception:
        pass
    return float("nan")


def _weapon_select_id(action: np.ndarray, *, action_mode: str) -> int:
    columns = _action_columns_for_mode(action_mode)
    weapon_select_idx = int(columns["weapon_select"])
    if action.size <= weapon_select_idx:
        return 0
    if str(action_mode) == "air_combat_hybrid_v1":
        return int(np.clip(round(float(action[weapon_select_idx])), 0, 7))
    return int(np.clip(float(action[weapon_select_idx]), 0.0, 1.0) * 7.0)


def _mission_command_dict(loader) -> dict[str, Any]:
    mission_cmd = getattr(loader, "mission_cmd", None)
    return mission_cmd if isinstance(mission_cmd, dict) else {}


def _c2_roe_event_columns(
    state: dict[str, Any],
    *,
    release_delta: int,
    fire_attempted: bool,
    previous_release_count: int,
) -> dict[str, Any]:
    release_delta = max(0, int(release_delta or 0))
    classifications = []
    if release_delta > 0:
        for release_ordinal in range(release_delta):
            classifications.append(
                classify_air_combat_c2_roe_event(
                    state,
                    released=True,
                    fire_attempted=bool(fire_attempted),
                    previous_release_count=int(previous_release_count or 0),
                    release_ordinal=int(release_ordinal),
                )
            )
    else:
        classifications.append(
            classify_air_combat_c2_roe_event(
                state,
                released=False,
                fire_attempted=bool(fire_attempted),
                previous_release_count=int(previous_release_count or 0),
            )
        )

    def count_flag(flag_name: str) -> int:
        return int(sum(1 for item in classifications if bool(item.get(flag_name, False))))

    violation_release_count = count_flag("violation_release")
    bucket = str(classifications[0].get("bucket", "no_fire")) if classifications else "no_fire"
    return {
        "c2_roe_release_bucket": bucket,
        "c2_roe_hold_fire": int(
            any(bool(item.get("hold_fire", False)) for item in classifications)
        ),
        "c2_roe_hold_fire_obeyed": count_flag("hold_fire_obeyed"),
        "c2_roe_hold_fire_violation": count_flag("hold_fire_violation"),
        "c2_roe_unauthorized_shot": count_flag("unauthorized_shot"),
        "c2_roe_unauthorized_release_count": int(
            sum(
                1
                for item in classifications
                if bool(item.get("released", False)) and bool(item.get("unauthorized_shot", False))
            )
        ),
        "c2_roe_authorized_release_count": count_flag("authorized_release"),
        "c2_roe_valid_authorized_release_count": count_flag("valid_authorized_release"),
        "c2_roe_violation_release_count": int(violation_release_count),
        "c2_roe_pending_assessment_violation": count_flag("pending_assessment_violation"),
        "c2_roe_pending_assessment_release_count": int(
            sum(
                1
                for item in classifications
                if bool(item.get("released", False))
                and bool(item.get("pending_assessment_violation", False))
            )
        ),
        "c2_roe_premature_second_shot": count_flag("premature_second_shot"),
        "c2_roe_shot_budget_violation": count_flag("shot_budget_violation"),
        "c2_roe_authorized_salvo_release_count": count_flag("authorized_salvo"),
        "c2_roe_authorized_reattack_release_count": count_flag("authorized_reattack"),
    }


def _event_info_columns(info: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(info, dict):
        return {}
    has_field = any(
        key in info
        for key in (
            "engagement_state",
            "fire_mask",
            "event_action_mask",
            "fire_once_requested",
            "fire_once_accepted",
            "fire_once_rejected_reason",
            "release_executed",
            "post_launch_suppressed",
            "reattack_ready",
            "fire_mask_components",
        )
    )
    if not has_field:
        return {}

    out: dict[str, Any] = {
        "engagement_state": str(info.get("engagement_state", "") or ""),
        "fire_mask": int(_bool_int(info.get("fire_mask", 0))),
        "fire_once_requested": int(_bool_int(info.get("fire_once_requested", False))),
        "fire_once_accepted": int(_bool_int(info.get("fire_once_accepted", False))),
        "fire_once_rejected_reason": str(info.get("fire_once_rejected_reason", "") or ""),
        "release_executed": int(_bool_int(info.get("release_executed", False))),
        "post_launch_suppressed": int(_bool_int(info.get("post_launch_suppressed", False))),
        "reattack_ready": int(_bool_int(info.get("reattack_ready", False))),
    }
    out["fire_once_rejected"] = int(
        out["fire_once_requested"] > 0 and out["fire_once_accepted"] <= 0
    )

    event_mask = info.get("event_action_mask", None)
    if isinstance(event_mask, np.ndarray):
        event_mask_list = event_mask.reshape(-1).tolist()
    elif isinstance(event_mask, (list, tuple)):
        event_mask_list = list(event_mask)
    else:
        event_mask_list = []
    if event_mask_list:
        mask_values = [int(_bool_int(value)) for value in event_mask_list]
        out["event_action_mask_json"] = _stable_json(mask_values)
        out["event_action_mask_hold"] = int(mask_values[0]) if len(mask_values) >= 1 else 1
        out["event_action_mask_fire_once"] = (
            int(mask_values[1]) if len(mask_values) >= 2 else out["fire_mask"]
        )
    else:
        out["event_action_mask_json"] = _stable_json([1, int(out["fire_mask"])])
        out["event_action_mask_hold"] = 1
        out["event_action_mask_fire_once"] = int(out["fire_mask"])

    components = info.get("fire_mask_components", {})
    component_map = components if isinstance(components, dict) else {}
    stable_components = {
        str(key): int(_bool_int(value)) for key, value in sorted(component_map.items())
    }
    out["fire_mask_components_json"] = _stable_json(stable_components)
    for name in FIRE_MASK_COMPONENT_NAMES:
        if name in stable_components:
            out[name] = int(stable_components[name])
    return out
