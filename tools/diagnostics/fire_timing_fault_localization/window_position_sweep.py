#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from collections import Counter
from types import SimpleNamespace
from typing import Any

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from python.testing.runtime import ensure_repo_imports, resolve_repo_path

ensure_repo_imports()

from tools.diagnostics import air_combat_weapon_employment_process_probe as process_probe  # noqa: E402
from tools.diagnostics import lethality_chain_contract as chain_contract  # noqa: E402


DEFAULT_SCENARIO = resolve_repo_path(
    "scenarios",
    "air_combat",
    "1v1",
    "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json",
)
DEFAULT_TRAIN_CONFIG = resolve_repo_path(
    "examples",
    "config",
    "training",
    "active",
    "air_combat",
    "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s1_grouped_stopping_state_completed_world_batch_probe_v1.json",
)
DEFAULT_OUTPUT_DIR = resolve_repo_path(
    "docs",
    "task",
    "model",
    "fire_timing_window_position_effect",
)


def _finite_float(value: Any, default: float = float("nan")) -> float:
    try:
        out = float(value)
    except Exception:
        return float(default)
    return out if math.isfinite(out) else float(default)


def _parse_delays(value: str) -> list[int]:
    delays: list[int] = []
    for item in str(value or "").split(","):
        item = item.strip()
        if not item:
            continue
        delay = max(0, int(item))
        if delay not in delays:
            delays.append(delay)
    return delays or [0]


def _mean(values: list[float]) -> float:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    if not finite:
        return float("nan")
    return float(sum(finite) / len(finite))


def _spread(values: list[float]) -> float:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    if not finite:
        return 0.0
    return float(max(finite) - min(finite))


def _count_true(records: list[dict[str, Any]], key: str) -> int:
    return int(sum(1 for record in records if bool(record.get(key, False))))


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value or "").strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off", ""}:
        return False
    return False


def _json_string_list(value: Any) -> list[str]:
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if str(item)]
    text = str(value or "").strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except Exception:
        parsed = None
    if isinstance(parsed, list):
        return [str(item) for item in parsed if str(item)]
    return [item.strip() for item in text.split(",") if item.strip()]


def _effective_detonation_observed(*, fuze_triggered: bool, stages_json: Any) -> bool:
    if fuze_triggered:
        return True
    stages = set(_json_string_list(stages_json))
    return bool(stages & chain_contract.EFFECTIVE_DETONATION_STAGES)


def _effective_system_consequence_observed(
    *,
    system_delta: float,
    mission_kill: bool,
    mobility_kill: bool,
    sensor_kill: bool,
    destroyed: bool,
    loss_state: str,
) -> bool:
    if mission_kill or mobility_kill or sensor_kill or destroyed:
        return True
    if loss_state and loss_state != "combat_capable":
        return True
    return math.isfinite(system_delta) and abs(system_delta) > 1.0e-9


def _probe_namespace(args: argparse.Namespace, *, delay: int, seed: int) -> SimpleNamespace:
    return SimpleNamespace(
        scenario=str(args.scenario),
        train_config=str(args.train_config),
        mode="legal_mask_fire",
        fire_range_m=float(args.fire_range_m),
        fire_delay_steps=int(delay),
        legal_fire_range_m=float(args.legal_fire_range_m),
        model="",
        algo="auto",
        device="auto",
        episodes=1,
        seed=int(seed),
        max_steps=int(args.max_steps),
        stochastic=False,
        csv_out="",
        chain_csv_out="",
        json_out="",
        plot_out="",
        diagnostic_dcr_bridge=bool(args.diagnostic_dcr_bridge),
        diagnostic_dcr_bridge_target_reward=float(args.diagnostic_dcr_bridge_target_reward),
        diagnostic_dcr_bridge_self_reward=float(args.diagnostic_dcr_bridge_self_reward),
    )


def _record_from_episode_summary(
    *,
    delay: int,
    payload: dict[str, Any],
    episode_summary: dict[str, Any],
) -> dict[str, Any]:
    release_count = int(episode_summary.get("release_count", 0) or 0)
    payload_seed = int(payload.get("seed", 0) or 0)
    episode = int(episode_summary.get("episode", 0) or 0)
    chain_stages_json = str(episode_summary.get("lethality_chain_stages_json", "") or "")
    fuze_triggered = _bool_value(episode_summary.get("lethality_chain_fuze_triggered", False))
    component_damage_count = int(
        episode_summary.get("lethality_chain_component_damage_count", 0) or 0
    )
    system_health_delta = _finite_float(
        episode_summary.get("lethality_chain_system_health_delta", float("nan"))
    )
    mission_kill = _bool_value(episode_summary.get("lethality_chain_mission_kill", False))
    mobility_kill = _bool_value(episode_summary.get("lethality_chain_mobility_kill", False))
    sensor_kill = _bool_value(episode_summary.get("lethality_chain_sensor_kill", False))
    destroyed = _bool_value(episode_summary.get("lethality_chain_destroyed", False))
    loss_state = str(episode_summary.get("lethality_chain_loss_state", "") or "")
    effective_detonation = _effective_detonation_observed(
        fuze_triggered=fuze_triggered,
        stages_json=chain_stages_json,
    )
    effective_component_damage = component_damage_count > 0
    effective_system_consequence = _effective_system_consequence_observed(
        system_delta=system_health_delta,
        mission_kill=mission_kill,
        mobility_kill=mobility_kill,
        sensor_kill=sensor_kill,
        destroyed=destroyed,
        loss_state=loss_state,
    )
    fuze_failure_reason = str(
        episode_summary.get("lethality_chain_fuze_failure_reason", "") or ""
    )
    return {
        "delay_steps": int(delay),
        "episode": episode,
        "episode_seed": int(payload_seed + episode),
        "released": bool(release_count > 0),
        "release_count": release_count,
        "first_release_step": episode_summary.get("first_release_step"),
        "first_release_sim_time_s": _finite_float(
            episode_summary.get("first_release_sim_time_s", float("nan"))
        ),
        "first_release_target_range_geom_m": _finite_float(
            episode_summary.get("first_release_target_range_geom_m", float("nan"))
        ),
        "first_release_target_range_track_m": _finite_float(
            episode_summary.get("first_release_target_range_track_m", float("nan"))
        ),
        "first_release_target_track_age_s": _finite_float(
            episode_summary.get("first_release_target_track_age_s", float("nan"))
        ),
        "first_release_legal_window_age_steps": int(
            episode_summary.get("first_release_legal_window_age_steps", 0) or 0
        ),
        "first_release_engagement_state": str(
            episode_summary.get("first_release_engagement_state", "") or ""
        ),
        "total_reward": _finite_float(episode_summary.get("total_reward", float("nan"))),
        "final_target_health": _finite_float(
            episode_summary.get("final_target_health", float("nan"))
        ),
        "target_health_delta_from_release": (
            _finite_float(episode_summary.get("final_target_health", float("nan")))
            - _finite_float(episode_summary.get("first_release_target_health", float("nan")))
        ),
        "effects_event_count": int(episode_summary.get("effects_event_count", 0) or 0),
        "damage_report_count": int(episode_summary.get("damage_report_count", 0) or 0),
        "first_effects_event_step": episode_summary.get("first_effects_event_step"),
        "first_damage_report_step": episode_summary.get("first_damage_report_step"),
        "first_damage_consequence_reward_step": episode_summary.get(
            "first_damage_consequence_reward_step"
        ),
        "damage_consequence_reward_total": _finite_float(
            episode_summary.get("damage_consequence_reward_total", 0.0),
            0.0,
        ),
        "target_damage_consequence_reward_total": _finite_float(
            episode_summary.get("target_damage_consequence_reward_total", 0.0),
            0.0,
        ),
        "lethality_chain_miss_distance_m": _finite_float(
            episode_summary.get("lethality_chain_miss_distance_m", float("nan"))
        ),
        "lethality_chain_closure_mps": _finite_float(
            episode_summary.get("lethality_chain_closure_mps", float("nan"))
        ),
        "lethality_chain_aspect_bucket": str(
            episode_summary.get("lethality_chain_aspect_bucket", "") or ""
        ),
        "lethality_chain_row_count": int(
            episode_summary.get("lethality_chain_row_count", 0) or 0
        ),
        "lethality_chain_chain_count": int(
            episode_summary.get("lethality_chain_chain_count", 0) or 0
        ),
        "lethality_chain_stages_json": chain_stages_json,
        "lethality_chain_fuze_triggered": fuze_triggered,
        "lethality_chain_fuze_failure_reason": fuze_failure_reason,
        "lethality_chain_fuze_expected_detonation_probability": _finite_float(
            episode_summary.get(
                "lethality_chain_fuze_expected_detonation_probability",
                float("nan"),
            )
        ),
        "lethality_chain_fuze_sampled_outcome": _bool_value(
            episode_summary.get("lethality_chain_fuze_sampled_outcome", False)
        ),
        "lethality_chain_projected_hitbox_count": int(
            episode_summary.get("lethality_chain_projected_hitbox_count", 0) or 0
        ),
        "lethality_chain_component_hit_count": int(
            episode_summary.get("lethality_chain_component_hit_count", 0) or 0
        ),
        "effective_detonation": bool(effective_detonation),
        "effective_component_damage": bool(effective_component_damage),
        "effective_system_consequence": bool(effective_system_consequence),
        "terminal_negative_reason": (
            fuze_failure_reason if not effective_detonation and fuze_failure_reason else ""
        ),
        "lethality_chain_component_name": str(
            episode_summary.get("lethality_chain_component_name", "") or ""
        ),
        "lethality_chain_component_system": str(
            episode_summary.get("lethality_chain_component_system", "") or ""
        ),
        "lethality_chain_component_damage_count": int(
            episode_summary.get("lethality_chain_component_damage_count", 0) or 0
        ),
        "lethality_chain_component_damage_name": str(
            episode_summary.get("lethality_chain_component_damage_name", "") or ""
        ),
        "lethality_chain_component_damage_system": str(
            episode_summary.get("lethality_chain_component_damage_system", "") or ""
        ),
        "lethality_chain_component_failure_mode": str(
            episode_summary.get("lethality_chain_component_failure_mode", "") or ""
        ),
        "lethality_chain_component_failure_severity": _finite_float(
            episode_summary.get("lethality_chain_component_failure_severity", float("nan"))
        ),
        "lethality_chain_component_failure_probability": _finite_float(
            episode_summary.get(
                "lethality_chain_component_failure_probability",
                float("nan"),
            )
        ),
        "lethality_chain_component_failure_sample": _finite_float(
            episode_summary.get("lethality_chain_component_failure_sample", float("nan"))
        ),
        "lethality_chain_component_integrity_before": _finite_float(
            episode_summary.get("lethality_chain_component_integrity_before", float("nan"))
        ),
        "lethality_chain_component_integrity_after": _finite_float(
            episode_summary.get("lethality_chain_component_integrity_after", float("nan"))
        ),
        "lethality_chain_system_health_delta": _finite_float(
            episode_summary.get("lethality_chain_system_health_delta", float("nan"))
        ),
        "lethality_chain_mission_capability_before": _finite_float(
            episode_summary.get("lethality_chain_mission_capability_before", float("nan"))
        ),
        "lethality_chain_mission_capability_after": _finite_float(
            episode_summary.get("lethality_chain_mission_capability_after", float("nan"))
        ),
        "lethality_chain_mission_capability_delta": _finite_float(
            episode_summary.get("lethality_chain_mission_capability_delta", float("nan"))
        ),
        "lethality_chain_mobility_capability_before": _finite_float(
            episode_summary.get("lethality_chain_mobility_capability_before", float("nan"))
        ),
        "lethality_chain_mobility_capability_after": _finite_float(
            episode_summary.get("lethality_chain_mobility_capability_after", float("nan"))
        ),
        "lethality_chain_mobility_capability_delta": _finite_float(
            episode_summary.get("lethality_chain_mobility_capability_delta", float("nan"))
        ),
        "lethality_chain_sensor_capability_before": _finite_float(
            episode_summary.get("lethality_chain_sensor_capability_before", float("nan"))
        ),
        "lethality_chain_sensor_capability_after": _finite_float(
            episode_summary.get("lethality_chain_sensor_capability_after", float("nan"))
        ),
        "lethality_chain_sensor_capability_delta": _finite_float(
            episode_summary.get("lethality_chain_sensor_capability_delta", float("nan"))
        ),
        "lethality_chain_survivability_margin_before": _finite_float(
            episode_summary.get("lethality_chain_survivability_margin_before", float("nan"))
        ),
        "lethality_chain_survivability_margin_after": _finite_float(
            episode_summary.get("lethality_chain_survivability_margin_after", float("nan"))
        ),
        "lethality_chain_survivability_margin_delta": _finite_float(
            episode_summary.get("lethality_chain_survivability_margin_delta", float("nan"))
        ),
        "lethality_chain_control_delta": _finite_float(
            episode_summary.get("lethality_chain_control_delta", float("nan"))
        ),
        "lethality_chain_engine_delta": _finite_float(
            episode_summary.get("lethality_chain_engine_delta", float("nan"))
        ),
        "lethality_chain_fuel_leak_delta": _finite_float(
            episode_summary.get("lethality_chain_fuel_leak_delta", float("nan"))
        ),
        "lethality_chain_fire_state": str(
            episode_summary.get("lethality_chain_fire_state", "") or ""
        ),
        "lethality_chain_aircraft_damage_state_before": str(
            episode_summary.get("lethality_chain_aircraft_damage_state_before", "") or ""
        ),
        "lethality_chain_aircraft_damage_state_after": str(
            episode_summary.get("lethality_chain_aircraft_damage_state_after", "") or ""
        ),
        "lethality_chain_aircraft_damage_state_delta": str(
            episode_summary.get("lethality_chain_aircraft_damage_state_delta", "") or ""
        ),
        "lethality_chain_air_system_hit_flags": str(
            episode_summary.get("lethality_chain_air_system_hit_flags", "") or ""
        ),
        "lethality_chain_air_system_spatial_scales": str(
            episode_summary.get("lethality_chain_air_system_spatial_scales", "") or ""
        ),
        "lethality_chain_vulnerability_scale_trace": str(
            episode_summary.get("lethality_chain_vulnerability_scale_trace", "") or ""
        ),
        "lethality_chain_loss_state": str(
            loss_state
        ),
        "lethality_chain_mission_kill": mission_kill,
        "lethality_chain_mobility_kill": mobility_kill,
        "lethality_chain_sensor_kill": sensor_kill,
        "lethality_chain_destroyed": destroyed,
        "termination_reason": str(episode_summary.get("termination_reason", "") or ""),
        "payload_mode": str(payload.get("mode", "") or ""),
        "payload_seed": payload_seed,
    }


def _summarize_delay(delay: int, records: list[dict[str, Any]]) -> dict[str, Any]:
    released_records = [record for record in records if bool(record.get("released", False))]
    episode_count = int(len(records))
    effects_count = _count_true(records, "effects_event_count")
    damage_count = _count_true(records, "damage_report_count")
    effective_detonation_count = _count_true(records, "effective_detonation")
    effective_component_damage_count = _count_true(records, "effective_component_damage")
    effective_system_consequence_count = _count_true(records, "effective_system_consequence")
    mission_kill_count = _count_true(records, "lethality_chain_mission_kill")
    destroyed_count = _count_true(records, "lethality_chain_destroyed")

    def rate(count: int) -> float:
        return float(count / episode_count) if episode_count > 0 else float("nan")

    def released_rate(key: str) -> float:
        if not released_records:
            return float("nan")
        count = _count_true(released_records, key)
        return float(count / len(released_records))

    return {
        "delay_steps": int(delay),
        "episodes": episode_count,
        "release_episode_count": int(len(released_records)),
        "release_rate": rate(len(released_records)),
        "effects_episode_count": effects_count,
        "effects_rate": rate(effects_count),
        "effects_given_release_rate": released_rate("effects_event_count"),
        "damage_episode_count": damage_count,
        "damage_rate": rate(damage_count),
        "damage_given_release_rate": released_rate("damage_report_count"),
        "effective_detonation_episode_count": effective_detonation_count,
        "effective_detonation_rate": rate(effective_detonation_count),
        "effective_detonation_given_release_rate": released_rate("effective_detonation"),
        "effective_component_damage_episode_count": effective_component_damage_count,
        "effective_component_damage_rate": rate(effective_component_damage_count),
        "effective_component_damage_given_release_rate": released_rate(
            "effective_component_damage"
        ),
        "effective_system_consequence_episode_count": effective_system_consequence_count,
        "effective_system_consequence_rate": rate(effective_system_consequence_count),
        "effective_system_consequence_given_release_rate": released_rate(
            "effective_system_consequence"
        ),
        "mission_kill_episode_count": mission_kill_count,
        "mission_kill_rate": rate(mission_kill_count),
        "mission_kill_given_release_rate": released_rate("lethality_chain_mission_kill"),
        "destroyed_episode_count": destroyed_count,
        "destroyed_rate": rate(destroyed_count),
        "destroyed_given_release_rate": released_rate("lethality_chain_destroyed"),
        "mean_first_release_step": _mean(
            [_finite_float(record.get("first_release_step", float("nan"))) for record in released_records]
        ),
        "mean_release_range_geom_m": _mean(
            [float(record["first_release_target_range_geom_m"]) for record in released_records]
        ),
        "mean_release_range_track_m": _mean(
            [float(record["first_release_target_range_track_m"]) for record in released_records]
        ),
        "mean_release_window_age_steps": _mean(
            [
                _finite_float(record.get("first_release_legal_window_age_steps", float("nan")))
                for record in released_records
            ]
        ),
        "mean_total_reward": _mean([float(record["total_reward"]) for record in records]),
        "mean_final_target_health": _mean(
            [float(record["final_target_health"]) for record in records]
        ),
        "mean_target_health_delta_from_release": _mean(
            [float(record["target_health_delta_from_release"]) for record in released_records]
        ),
        "mean_damage_consequence_reward_total": _mean(
            [float(record["damage_consequence_reward_total"]) for record in records]
        ),
        "mean_target_damage_consequence_reward_total": _mean(
            [float(record["target_damage_consequence_reward_total"]) for record in records]
        ),
        "mean_miss_distance_m": _mean(
            [float(record["lethality_chain_miss_distance_m"]) for record in records]
        ),
        "mean_fuze_expected_detonation_probability": _mean(
            [
                _finite_float(
                    record.get(
                        "lethality_chain_fuze_expected_detonation_probability",
                        float("nan"),
                    )
                )
                for record in records
            ]
        ),
        "mean_lethality_chain_row_count": _mean(
            [_finite_float(record.get("lethality_chain_row_count", float("nan"))) for record in records]
        ),
        "mean_closure_mps": _mean(
            [float(record["lethality_chain_closure_mps"]) for record in records]
        ),
        "mean_component_failure_probability": _mean(
            [
                float(record["lethality_chain_component_failure_probability"])
                for record in records
            ]
        ),
        "mean_component_failure_sample": _mean(
            [float(record["lethality_chain_component_failure_sample"]) for record in records]
        ),
        "mean_component_damage_count": _mean(
            [_finite_float(record.get("lethality_chain_component_damage_count", float("nan"))) for record in records]
        ),
        "mean_component_integrity_delta": _mean(
            [
                float(record["lethality_chain_component_integrity_after"])
                - float(record["lethality_chain_component_integrity_before"])
                for record in records
            ]
        ),
        "mean_system_health_delta": _mean(
            [float(record["lethality_chain_system_health_delta"]) for record in records]
        ),
        "mean_mission_capability_before": _mean(
            [float(record["lethality_chain_mission_capability_before"]) for record in records]
        ),
        "mean_mission_capability_after": _mean(
            [float(record["lethality_chain_mission_capability_after"]) for record in records]
        ),
        "mean_mission_capability_delta": _mean(
            [float(record["lethality_chain_mission_capability_delta"]) for record in records]
        ),
        "mean_mobility_capability_before": _mean(
            [float(record["lethality_chain_mobility_capability_before"]) for record in records]
        ),
        "mean_mobility_capability_after": _mean(
            [float(record["lethality_chain_mobility_capability_after"]) for record in records]
        ),
        "mean_mobility_capability_delta": _mean(
            [float(record["lethality_chain_mobility_capability_delta"]) for record in records]
        ),
        "mean_sensor_capability_before": _mean(
            [float(record["lethality_chain_sensor_capability_before"]) for record in records]
        ),
        "mean_sensor_capability_after": _mean(
            [float(record["lethality_chain_sensor_capability_after"]) for record in records]
        ),
        "mean_sensor_capability_delta": _mean(
            [float(record["lethality_chain_sensor_capability_delta"]) for record in records]
        ),
        "mean_survivability_margin_before": _mean(
            [float(record["lethality_chain_survivability_margin_before"]) for record in records]
        ),
        "mean_survivability_margin_after": _mean(
            [float(record["lethality_chain_survivability_margin_after"]) for record in records]
        ),
        "mean_survivability_margin_delta": _mean(
            [float(record["lethality_chain_survivability_margin_delta"]) for record in records]
        ),
        "mean_control_delta": _mean(
            [float(record["lethality_chain_control_delta"]) for record in records]
        ),
        "mean_engine_delta": _mean(
            [float(record["lethality_chain_engine_delta"]) for record in records]
        ),
        "mean_fuel_leak_delta": _mean(
            [float(record["lethality_chain_fuel_leak_delta"]) for record in records]
        ),
        "loss_state_counts": dict(
            sorted(Counter(str(record.get("lethality_chain_loss_state", "") or "") for record in records).items())
        ),
        "fire_state_counts": dict(
            sorted(Counter(str(record.get("lethality_chain_fire_state", "") or "") for record in records).items())
        ),
        "fuze_failure_reason_counts": dict(
            sorted(
                Counter(
                    str(record.get("lethality_chain_fuze_failure_reason", "") or "")
                    for record in records
                ).items()
            )
        ),
        "terminal_negative_reason_counts": dict(
            sorted(
                Counter(
                    str(record.get("terminal_negative_reason", "") or "")
                    for record in records
                ).items()
            )
        ),
        "lethality_chain_stages_counts": dict(
            sorted(
                Counter(
                    str(record.get("lethality_chain_stages_json", "") or "")
                    for record in records
                ).items()
            )
        ),
        "aircraft_damage_state_delta_counts": dict(
            sorted(
                Counter(
                    str(record.get("lethality_chain_aircraft_damage_state_delta", "") or "")
                    for record in records
                ).items()
            )
        ),
        "air_system_hit_flags_counts": dict(
            sorted(
                Counter(
                    str(record.get("lethality_chain_air_system_hit_flags", "") or "")
                    for record in records
                ).items()
            )
        ),
        "vulnerability_scale_trace_counts": dict(
            sorted(
                Counter(
                    str(record.get("lethality_chain_vulnerability_scale_trace", "") or "")
                    for record in records
                ).items()
            )
        ),
        "component_name_counts": dict(
            sorted(Counter(str(record.get("lethality_chain_component_name", "") or "") for record in records).items())
        ),
        "component_damage_name_counts": dict(
            sorted(
                Counter(
                    str(record.get("lethality_chain_component_damage_name", "") or "")
                    for record in records
                ).items()
            )
        ),
        "termination_reason_counts": dict(
            sorted(Counter(str(record.get("termination_reason", "") or "") for record in records).items())
        ),
    }


def _sweep_verdict(
    delay_summaries: list[dict[str, Any]],
    *,
    reward_epsilon: float,
    health_epsilon: float,
    system_health_delta_epsilon: float,
    component_failure_probability_epsilon: float,
    miss_distance_epsilon_m: float,
    range_epsilon_m: float,
) -> dict[str, Any]:
    released = [
        row
        for row in delay_summaries
        if int(row.get("release_episode_count", 0) or 0) > 0
    ]
    release_range_spread_m = _spread(
        [_finite_float(row.get("mean_release_range_geom_m", float("nan"))) for row in released]
    )
    reward_spread = _spread(
        [_finite_float(row.get("mean_total_reward", float("nan"))) for row in released]
    )
    final_health_spread = _spread(
        [_finite_float(row.get("mean_final_target_health", float("nan"))) for row in released]
    )
    component_probability_spread = _spread(
        [
            _finite_float(row.get("mean_component_failure_probability", float("nan")))
            for row in released
        ]
    )
    system_health_delta_spread = _spread(
        [_finite_float(row.get("mean_system_health_delta", float("nan"))) for row in released]
    )
    miss_distance_spread_m = _spread(
        [_finite_float(row.get("mean_miss_distance_m", float("nan"))) for row in released]
    )
    damage_reward_spread = _spread(
        [
            _finite_float(row.get("mean_damage_consequence_reward_total", float("nan")))
            for row in released
        ]
    )
    mission_kill_rate_spread = _spread(
        [_finite_float(row.get("mission_kill_rate", float("nan"))) for row in released]
    )
    mission_kill_given_release_rate_spread = _spread(
        [
            _finite_float(row.get("mission_kill_given_release_rate", float("nan")))
            for row in released
        ]
    )
    effects_rate_spread = _spread(
        [_finite_float(row.get("effects_rate", float("nan"))) for row in released]
    )
    damage_rate_spread = _spread(
        [_finite_float(row.get("damage_rate", float("nan"))) for row in released]
    )
    effective_detonation_rate_spread = _spread(
        [
            _finite_float(row.get("effective_detonation_rate", float("nan")))
            for row in released
        ]
    )
    effective_component_damage_rate_spread = _spread(
        [
            _finite_float(row.get("effective_component_damage_rate", float("nan")))
            for row in released
        ]
    )
    effective_system_consequence_rate_spread = _spread(
        [
            _finite_float(row.get("effective_system_consequence_rate", float("nan")))
            for row in released
        ]
    )
    categorical_effect_change = len(
        {
            (
                int(row.get("effective_detonation_episode_count", 0) or 0),
                int(row.get("effective_component_damage_episode_count", 0) or 0),
                int(row.get("effective_system_consequence_episode_count", 0) or 0),
                int(row.get("mission_kill_episode_count", 0) or 0),
                int(row.get("destroyed_episode_count", 0) or 0),
            )
            for row in released
        }
    ) > 1
    position_variation_observed = release_range_spread_m > float(range_epsilon_m)
    outcome_variation_observed = bool(
        reward_spread > float(reward_epsilon)
        or final_health_spread > float(health_epsilon)
        or damage_reward_spread > float(reward_epsilon)
        or system_health_delta_spread > float(system_health_delta_epsilon)
        or component_probability_spread > float(component_failure_probability_epsilon)
        or miss_distance_spread_m > float(miss_distance_epsilon_m)
        or mission_kill_rate_spread > 0.0
        or mission_kill_given_release_rate_spread > 0.0
        or effective_detonation_rate_spread > 0.0
        or effective_component_damage_rate_spread > 0.0
        or effective_system_consequence_rate_spread > 0.0
        or categorical_effect_change
    )
    learnability_candidate = bool(position_variation_observed and outcome_variation_observed)
    return {
        "release_position_variation_observed": bool(position_variation_observed),
        "release_range_spread_m": float(release_range_spread_m),
        "outcome_variation_observed": bool(outcome_variation_observed),
        "reward_spread": float(reward_spread),
        "final_target_health_spread": float(final_health_spread),
        "damage_consequence_reward_spread": float(damage_reward_spread),
        "system_health_delta_spread": float(system_health_delta_spread),
        "component_failure_probability_spread": float(component_probability_spread),
        "miss_distance_spread_m": float(miss_distance_spread_m),
        "mission_kill_rate_spread": float(mission_kill_rate_spread),
        "mission_kill_given_release_rate_spread": float(mission_kill_given_release_rate_spread),
        "effects_rate_spread": float(effects_rate_spread),
        "damage_rate_spread": float(damage_rate_spread),
        "effective_detonation_rate_spread": float(effective_detonation_rate_spread),
        "effective_component_damage_rate_spread": float(
            effective_component_damage_rate_spread
        ),
        "effective_system_consequence_rate_spread": float(
            effective_system_consequence_rate_spread
        ),
        "categorical_effect_change": bool(categorical_effect_change),
        "learnability_candidate": bool(learnability_candidate),
        "interpretation": (
            "Window-position changes produce both release-geometry variation and "
            "observable outcome variation under oracle legal-mask firing."
            if learnability_candidate
            else "This bounded sweep did not observe enough coupled geometry/outcome variation."
        ),
    }


def run_sweep(args: argparse.Namespace) -> dict[str, Any]:
    delays = _parse_delays(str(args.delays))
    records: list[dict[str, Any]] = []
    delay_payloads: list[dict[str, Any]] = []
    for delay in delays:
        delay_payload: dict[str, Any] = {
            "delay_steps": int(delay),
            "probe_args": {
                "mode": "legal_mask_fire",
                "fire_delay_steps": int(delay),
                "samples": int(args.episodes),
                "seed_start": int(args.seed),
                "max_steps": int(args.max_steps),
                "legal_fire_range_m": float(args.legal_fire_range_m),
            },
            "sample_summaries": [],
        }
        for sample_index in range(int(args.episodes)):
            seed = int(args.seed) + int(sample_index)
            probe_args = _probe_namespace(args, delay=int(delay), seed=seed)
            payload = process_probe.run_probe(probe_args)
            for summary in payload.get("episode_summaries", []):
                if not isinstance(summary, dict):
                    continue
                record = _record_from_episode_summary(
                    delay=int(delay),
                    payload=payload,
                    episode_summary=summary,
                )
                record["sample_index"] = int(sample_index)
                records.append(record)
                delay_payload["sample_summaries"].append(summary)
        delay_payloads.append(delay_payload)
    delay_summaries = [
        _summarize_delay(
            int(delay),
            [record for record in records if int(record["delay_steps"]) == int(delay)],
        )
        for delay in delays
    ]
    return {
        "schema_version": "fire_timing.window_position_sweep.v2",
        "scenario": os.path.abspath(args.scenario),
        "train_config": os.path.abspath(args.train_config),
        "seed": int(args.seed),
        "episodes": int(args.episodes),
        "sampling_mode": "independent_seed_process_probe_episodes_1",
        "max_steps": int(args.max_steps),
        "delays": delays,
        "legal_fire_range_m": float(args.legal_fire_range_m),
        "diagnostic_dcr_bridge": bool(args.diagnostic_dcr_bridge),
        "independent_variables": [
            "fire_delay_steps",
            "first_release_step",
            "first_release_target_range_geom_m",
            "first_release_legal_window_age_steps",
        ],
        "dependent_variables": [
            "total_reward",
            "final_target_health",
            "effects_event_count",
            "damage_report_count",
            "effective_detonation",
            "effective_component_damage",
            "effective_system_consequence",
            "terminal_negative_reason",
            "lethality_chain_fuze_triggered",
            "lethality_chain_fuze_failure_reason",
            "lethality_chain_fuze_expected_detonation_probability",
            "lethality_chain_fuze_sampled_outcome",
            "lethality_chain_stages_json",
            "lethality_chain_component_name",
            "lethality_chain_component_damage_count",
            "lethality_chain_component_failure_probability",
            "lethality_chain_component_failure_sample",
            "lethality_chain_system_health_delta",
            "lethality_chain_mission_capability_before",
            "lethality_chain_mission_capability_after",
            "lethality_chain_mission_capability_delta",
            "lethality_chain_mobility_capability_before",
            "lethality_chain_mobility_capability_after",
            "lethality_chain_sensor_capability_before",
            "lethality_chain_sensor_capability_after",
            "lethality_chain_survivability_margin_before",
            "lethality_chain_survivability_margin_after",
            "lethality_chain_aircraft_damage_state_delta",
            "lethality_chain_air_system_hit_flags",
            "lethality_chain_air_system_spatial_scales",
            "lethality_chain_vulnerability_scale_trace",
            "lethality_chain_loss_state",
        ],
        "records": records,
        "delay_summaries": delay_summaries,
        "verdict": _sweep_verdict(
            delay_summaries,
            reward_epsilon=float(args.reward_epsilon),
            health_epsilon=float(args.health_epsilon),
            system_health_delta_epsilon=float(args.system_health_delta_epsilon),
            component_failure_probability_epsilon=float(
                args.component_failure_probability_epsilon
            ),
            miss_distance_epsilon_m=float(args.miss_distance_epsilon_m),
            range_epsilon_m=float(args.range_epsilon_m),
        ),
        "cases": delay_payloads if bool(args.include_cases) else [],
    }


def write_json(path: str, payload: dict[str, Any]) -> None:
    out_path = os.path.abspath(path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(_json_safe(payload), f, indent=2, ensure_ascii=True, allow_nan=False)
        f.write("\n")


def _json_safe(value: Any) -> Any:
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def write_csv(path: str, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    out_path = os.path.abspath(path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def render_plot(path: str, payload: dict[str, Any]) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:
        raise RuntimeError("plotting requires matplotlib") from exc
    summaries = list(payload.get("delay_summaries", []))
    x = list(range(len(summaries)))
    x_labels = [str(int(row["delay_steps"])) for row in summaries]
    release_range_km = [
        _finite_float(row.get("mean_release_range_geom_m", float("nan"))) / 1000.0
        for row in summaries
    ]
    rewards = [_finite_float(row.get("mean_total_reward", float("nan"))) for row in summaries]
    reward_baseline = next((value for value in rewards if math.isfinite(value)), float("nan"))
    reward_delta = [
        value - reward_baseline if math.isfinite(value) and math.isfinite(reward_baseline) else float("nan")
        for value in rewards
    ]
    reward_delta_scaled = [
        value * 100000.0 if math.isfinite(value) else float("nan")
        for value in reward_delta
    ]
    miss_distance = [
        _finite_float(row.get("mean_miss_distance_m", float("nan"))) for row in summaries
    ]
    hit_quality = [
        1.0 / (1.0 + value) if math.isfinite(value) and value >= 0.0 else float("nan")
        for value in miss_distance
    ]
    system_damage_magnitude = [
        max(0.0, -_finite_float(row.get("mean_system_health_delta", float("nan"))))
        for row in summaries
    ]
    mission_damage_magnitude = [
        max(0.0, -_finite_float(row.get("mean_mission_capability_delta", float("nan"))))
        for row in summaries
    ]
    component_prob = [
        _finite_float(row.get("mean_component_failure_probability", float("nan")))
        for row in summaries
    ]
    fuze_expected = [
        _finite_float(row.get("mean_fuze_expected_detonation_probability", float("nan")))
        for row in summaries
    ]
    release = [_finite_float(row.get("release_rate", float("nan"))) for row in summaries]
    detonation = [
        _finite_float(row.get("effective_detonation_given_release_rate", float("nan")))
        for row in summaries
    ]
    component_damage = [
        _finite_float(
            row.get("effective_component_damage_given_release_rate", float("nan"))
        )
        for row in summaries
    ]
    mission_kill = [
        _finite_float(row.get("mission_kill_given_release_rate", float("nan")))
        for row in summaries
    ]
    fig, axes = plt.subplots(
        4,
        1,
        figsize=(11.5, 9.2),
        sharex=True,
        constrained_layout=True,
        gridspec_kw={"height_ratios": [1.0, 1.0, 1.25, 0.9]},
    )
    axes[0].plot(x, release_range_km, marker="o")
    axes[0].set_ylabel("release range\nkm")
    axes[1].bar(x, reward_delta_scaled, color="tab:green", alpha=0.78)
    axes[1].axhline(0.0, color="#111827", linewidth=0.8)
    axes[1].set_ylabel("return delta\nx1e-5")

    def scatter_valid(values: list[float], *, label: str, color: str, marker: str) -> None:
        valid_x = [pos for pos, value in zip(x, values, strict=True) if math.isfinite(value)]
        valid_y = [value for value in values if math.isfinite(value)]
        axes[2].scatter(valid_x, valid_y, label=label, color=color, marker=marker, s=58)

    scatter_valid(
        system_damage_magnitude,
        label="system damage",
        color="tab:red",
        marker="o",
    )
    scatter_valid(
        mission_damage_magnitude,
        label="mission-cap damage",
        color="tab:blue",
        marker="D",
    )
    scatter_valid(
        component_prob,
        label="component P(fail)",
        color="tab:purple",
        marker="s",
    )
    scatter_valid(
        fuze_expected,
        label="fuze E[P(det)]",
        color="tab:cyan",
        marker="x",
    )
    scatter_valid(hit_quality, label="hit quality", color="tab:orange", marker="^")
    axes[2].set_ylabel("auxiliary\nlearning target")
    axes[2].set_ylim(-0.05, 1.05)
    axes[2].legend(loc="upper left", fontsize=8, ncol=3)

    event_matrix = [release, detonation, component_damage, mission_kill]
    axes[3].imshow(event_matrix, aspect="auto", cmap="YlGnBu", vmin=0.0, vmax=1.0)
    axes[3].set_yticks([0, 1, 2, 3])
    axes[3].set_yticklabels(
        ["release", "detonation|rel", "component damage|rel", "mission kill|rel"]
    )
    for row_index, row_values in enumerate(event_matrix):
        for col_index, value in enumerate(row_values):
            finite_value = _finite_float(value, 0.0)
            axes[3].text(
                col_index,
                row_index,
                f"{finite_value:.2f}",
                ha="center",
                va="center",
                fontsize=8,
                color="white" if finite_value >= 0.5 else "#111827",
            )
    axes[3].set_xlabel("legal-window fire delay steps")

    for axis in axes[:3]:
        axis.grid(True, color="#d1d5db", linewidth=0.7, alpha=0.8)
    for axis in axes:
        axis.set_xlim(-0.5, len(x) - 0.5)
    axes[3].set_xticks(x)
    axes[3].set_xticklabels(x_labels, rotation=35, ha="right")
    fig.suptitle("Fire-window learning signals: reward vs auxiliary targets", fontsize=13)
    out_path = os.path.abspath(path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sweep oracle fire delays across launch-window positions.")
    parser.add_argument("--scenario", default=DEFAULT_SCENARIO)
    parser.add_argument("--train_config", default=DEFAULT_TRAIN_CONFIG)
    parser.add_argument(
        "--episodes",
        type=int,
        default=1,
        help="Independent seed samples per delay; each sample invokes the process probe with episodes=1.",
    )
    parser.add_argument("--seed", type=int, default=20260615)
    parser.add_argument("--max_steps", type=int, default=2000)
    parser.add_argument("--delays", default="0,32,64,128,256,512,768,1024,1280,1536,1664")
    parser.add_argument("--fire_range_m", type=float, default=12000.0)
    parser.add_argument("--legal_fire_range_m", type=float, default=0.0)
    parser.add_argument("--reward_epsilon", type=float, default=1.0)
    parser.add_argument("--health_epsilon", type=float, default=1.0)
    parser.add_argument("--system_health_delta_epsilon", type=float, default=0.1)
    parser.add_argument("--component_failure_probability_epsilon", type=float, default=0.05)
    parser.add_argument("--miss_distance_epsilon_m", type=float, default=1.0)
    parser.add_argument("--range_epsilon_m", type=float, default=500.0)
    parser.add_argument("--diagnostic_dcr_bridge", action="store_true")
    parser.add_argument("--diagnostic_dcr_bridge_target_reward", type=float, default=0.0)
    parser.add_argument("--diagnostic_dcr_bridge_self_reward", type=float, default=0.0)
    parser.add_argument("--include_cases", action="store_true")
    parser.add_argument(
        "--output_dir",
        default=DEFAULT_OUTPUT_DIR,
    )
    parser.add_argument("--json_out", default="")
    parser.add_argument("--csv_out", default="")
    parser.add_argument("--plot_out", default="")
    return parser


def _default_output_path(output_dir: str, filename: str) -> str:
    return os.path.join(os.path.abspath(output_dir), filename)


def main() -> int:
    args = build_arg_parser().parse_args()
    payload = run_sweep(args)
    json_out = args.json_out or _default_output_path(
        args.output_dir,
        "fire_timing_window_position_sweep_20260615.json",
    )
    csv_out = args.csv_out or _default_output_path(
        args.output_dir,
        "fire_timing_window_position_sweep_20260615.csv",
    )
    plot_out = args.plot_out or _default_output_path(
        args.output_dir,
        "fire_timing_window_position_sweep_20260615.png",
    )
    write_json(json_out, payload)
    write_csv(csv_out, list(payload.get("delay_summaries", [])))
    render_plot(plot_out, payload)
    payload["json_out"] = os.path.abspath(json_out)
    payload["csv_out"] = os.path.abspath(csv_out)
    payload["plot_out"] = os.path.abspath(plot_out)
    write_json(json_out, payload)
    print(json.dumps(_json_safe(payload), indent=2, ensure_ascii=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
