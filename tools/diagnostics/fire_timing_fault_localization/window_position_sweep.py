#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from collections import Counter
from statistics import NormalDist
from types import SimpleNamespace
from typing import Any

_REPO_ROOT_HINT = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT_HINT = os.path.dirname(_REPO_ROOT_HINT)
_REPO_ROOT_HINT = os.path.dirname(_REPO_ROOT_HINT)
_REPO_ROOT_HINT = os.path.dirname(_REPO_ROOT_HINT)
if _REPO_ROOT_HINT not in sys.path:
    sys.path.insert(0, _REPO_ROOT_HINT)
from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path

ensure_repo_imports()

from tools.diagnostics.common import (
    add_json_out_arg,
    add_model_load_args,
    add_probe_run_args,
    finite_float,
    mean_finite,
    write_json_output,
)
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
    "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_grouped_stopping_state_completed_world_batch_probe_v1.json",
)
DEFAULT_OUTPUT_DIR = resolve_repo_path(
    "docs",
    "systems",
    "effects",
    "reviews",
    "fire_timing_window_position_effect_20260615",
)

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

def _finite_values(values: list[Any]) -> list[float]:
    return [
        value
        for value in (finite_float(item, float("nan")) for item in values)
        if math.isfinite(value)
    ]

def _confidence_z(confidence_level: float) -> float:
    level = min(0.999, max(0.5, float(confidence_level)))
    return float(NormalDist().inv_cdf(0.5 + level / 2.0))

def _sample_std(values: list[float]) -> float:
    finite = _finite_values(values)
    if len(finite) < 2:
        return float("nan")
    mean = sum(finite) / len(finite)
    variance = sum((value - mean) ** 2 for value in finite) / (len(finite) - 1)
    return float(math.sqrt(max(0.0, variance)))

def _numeric_confidence_fields(
    prefix: str,
    values: list[Any],
    *,
    z_score: float,
) -> dict[str, Any]:
    finite = _finite_values(values)
    if not finite:
        return {
            f"{prefix}_sample_count": 0,
            f"{prefix}_std": float("nan"),
            f"{prefix}_sem": float("nan"),
            f"{prefix}_ci_low": float("nan"),
            f"{prefix}_ci_high": float("nan"),
            f"{prefix}_ci_width": float("nan"),
        }
    std = _sample_std(finite)
    sem = std / math.sqrt(len(finite)) if math.isfinite(std) else float("nan")
    mean = sum(finite) / len(finite)
    ci_low = mean - z_score * sem if math.isfinite(sem) else float("nan")
    ci_high = mean + z_score * sem if math.isfinite(sem) else float("nan")
    return {
        f"{prefix}_sample_count": int(len(finite)),
        f"{prefix}_std": float(std),
        f"{prefix}_sem": float(sem),
        f"{prefix}_ci_low": float(ci_low),
        f"{prefix}_ci_high": float(ci_high),
        f"{prefix}_ci_width": (
            float(ci_high - ci_low)
            if math.isfinite(ci_low) and math.isfinite(ci_high)
            else float("nan")
        ),
    }

def _wilson_interval(success_count: int, sample_count: int, *, z_score: float) -> tuple[float, float]:
    if sample_count <= 0:
        return (float("nan"), float("nan"))
    n = float(sample_count)
    p = float(success_count) / n
    z2 = z_score * z_score
    denom = 1.0 + z2 / n
    center = (p + z2 / (2.0 * n)) / denom
    margin = (
        z_score
        * math.sqrt(max(0.0, (p * (1.0 - p) / n) + (z2 / (4.0 * n * n))))
        / denom
    )
    return (float(max(0.0, center - margin)), float(min(1.0, center + margin)))

def _binary_confidence_fields(
    prefix: str,
    *,
    success_count: int,
    sample_count: int,
    z_score: float,
) -> dict[str, Any]:
    if sample_count <= 0:
        return {
            f"{prefix}_sample_count": 0,
            f"{prefix}_success_count": int(success_count),
            f"{prefix}_std": float("nan"),
            f"{prefix}_sem": float("nan"),
            f"{prefix}_ci_low": float("nan"),
            f"{prefix}_ci_high": float("nan"),
            f"{prefix}_ci_width": float("nan"),
        }
    p = float(success_count) / float(sample_count)
    std = (
        math.sqrt(p * (1.0 - p) * sample_count / (sample_count - 1))
        if sample_count > 1
        else float("nan")
    )
    sem = math.sqrt(p * (1.0 - p) / sample_count)
    ci_low, ci_high = _wilson_interval(success_count, sample_count, z_score=z_score)
    return {
        f"{prefix}_sample_count": int(sample_count),
        f"{prefix}_success_count": int(success_count),
        f"{prefix}_std": float(std),
        f"{prefix}_sem": float(sem),
        f"{prefix}_ci_low": float(ci_low),
        f"{prefix}_ci_high": float(ci_high),
        f"{prefix}_ci_width": float(ci_high - ci_low),
    }

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

def _bounded_probability(value: float) -> float:
    if not math.isfinite(value):
        return float("nan")
    return float(min(1.0, max(0.0, value)))

def _delta_from_before_after(explicit_delta: Any, before: float, after: float) -> float:
    delta = finite_float(explicit_delta, float("nan"))
    if math.isfinite(delta):
        return delta
    if math.isfinite(before) and math.isfinite(after):
        return float(after - before)
    return float("nan")

def _component_sample_gate(probability: float, sample: float) -> str:
    bounded = _bounded_probability(probability)
    if not math.isfinite(bounded):
        return "no_component_probability"
    if not math.isfinite(sample):
        return "no_component_sample"
    if sample <= bounded:
        return "sample_passed"
    return "sample_rejected"

def _fuze_trigger_distance_ratio(miss_distance_m: float, trigger_radius_m: float) -> float:
    if not math.isfinite(miss_distance_m) or not math.isfinite(trigger_radius_m):
        return float("nan")
    if trigger_radius_m <= 0.0:
        return float("nan")
    return float(miss_distance_m / trigger_radius_m)

def _fuze_trigger_quality(miss_distance_m: float, trigger_radius_m: float) -> float:
    ratio = _fuze_trigger_distance_ratio(miss_distance_m, trigger_radius_m)
    if not math.isfinite(ratio):
        return float("nan")
    return _bounded_probability(1.0 - ratio)

def _fuze_sample_gate(probability: float, sample: float) -> str:
    bounded = _bounded_probability(probability)
    if not math.isfinite(bounded):
        return "no_fuze_probability"
    if not math.isfinite(sample):
        return "no_fuze_sample"
    if sample <= bounded:
        return "sample_passed"
    return "sample_rejected"

def _fuze_gate_summary(
    *,
    fuze_type: str,
    failure_reason: str,
    miss_distance_m: float,
    trigger_radius_m: float,
    trigger_quality: float,
    probability: float,
    sample: float,
    sample_gate: str,
) -> str:
    if not fuze_type and not failure_reason and not math.isfinite(miss_distance_m):
        return "no fuze observation"
    type_text = fuze_type or "unknown_fuze"
    if math.isfinite(miss_distance_m) and math.isfinite(trigger_radius_m):
        ratio = _fuze_trigger_distance_ratio(miss_distance_m, trigger_radius_m)
        distance_text = (
            f"miss {_format_float(miss_distance_m)}m / "
            f"trigger {_format_float(trigger_radius_m)}m = {_format_float(ratio)}"
        )
    else:
        distance_text = "miss/trigger n/a"
    if sample_gate in {"sample_passed", "sample_rejected"}:
        comparator = "<=" if sample_gate == "sample_passed" else ">"
        sample_text = (
            f"sample {_format_float(sample)}{comparator}"
            f"{_format_float(_bounded_probability(probability))}"
        )
    else:
        sample_text = sample_gate
    reason_text = f"; reason {failure_reason}" if failure_reason else ""
    return (
        f"{type_text}; {distance_text}; quality {_format_float(trigger_quality)}; "
        f"{sample_text}{reason_text}"
    )

def _primary_damage_channel(
    *,
    component_damage_system: str,
    component_system: str,
    effective_system_consequence: bool,
) -> str:
    if component_damage_system:
        return component_damage_system
    if component_system:
        return component_system
    if effective_system_consequence:
        return "platform_consequence"
    return "none"

def _capability_attribution(
    *,
    mission_delta: float,
    mobility_delta: float,
    sensor_delta: float,
    survivability_delta: float,
) -> str:
    candidates = {
        "mission_capability": mission_delta,
        "mobility_capability": mobility_delta,
        "sensor_capability": sensor_delta,
        "survivability_margin": survivability_delta,
    }
    finite_negative = [
        (name, value)
        for name, value in candidates.items()
        if math.isfinite(value) and value < -1.0e-9
    ]
    if not finite_negative:
        return "none"
    return min(finite_negative, key=lambda item: item[1])[0]

def _damage_chain_outcome(
    *,
    released: bool,
    effects_event_count: int,
    effective_detonation: bool,
    effective_component_damage: bool,
    effective_system_consequence: bool,
    fuze_failure_reason: str,
    projected_hitbox_count: int,
    component_hit_count: int,
    component_name: str,
    component_sample_gate: str,
    mission_kill: bool,
    mobility_kill: bool,
    sensor_kill: bool,
    destroyed: bool,
) -> str:
    if not released:
        return "no_release"
    if effects_event_count <= 0:
        return "release_no_effects_event"
    if not effective_detonation:
        return fuze_failure_reason or "no_effective_detonation"
    if projected_hitbox_count <= 0 and component_hit_count <= 0 and not component_name:
        return "detonation_no_spatial_coverage"
    if component_hit_count <= 0 and not component_name:
        return "detonation_no_component_load"
    if component_sample_gate == "sample_rejected" and not effective_component_damage:
        if effective_system_consequence:
            return "component_sample_rejected_but_system_consequence"
        return "component_sample_rejected_no_consequence"
    if not effective_component_damage and not effective_system_consequence:
        return "component_load_no_damage"
    if effective_component_damage and not effective_system_consequence:
        return "component_damage_no_platform_consequence"
    if destroyed:
        return "destroyed"
    if mobility_kill:
        return "mobility_kill"
    if sensor_kill:
        return "sensor_kill"
    if mission_kill:
        return "mission_kill"
    if effective_system_consequence:
        return "system_consequence_below_kill_threshold"
    if effective_component_damage:
        return "component_damage_below_platform_threshold"
    return "detonation_no_effective_damage"

def _damage_chain_blocker(outcome: str) -> str:
    if outcome in {"destroyed", "mobility_kill", "sensor_kill", "mission_kill"}:
        return "kill_observed"
    return outcome

def _format_float(value: float) -> str:
    return f"{value:.3f}" if math.isfinite(value) else "n/a"

def _attribution_summary(
    *,
    outcome: str,
    component_name: str,
    component_system: str,
    component_damage_name: str,
    component_damage_system: str,
    probability: float,
    sample: float,
    sample_gate: str,
    capability_attribution: str,
    mission_before: float,
    mission_after: float,
    mobility_before: float,
    mobility_after: float,
    sensor_before: float,
    sensor_after: float,
    survivability_before: float,
    survivability_after: float,
) -> str:
    if outcome == "no_release":
        return "blocked before release"
    if outcome in chain_contract.TERMINAL_NEGATIVE_REASONS or outcome == "no_effective_detonation":
        return f"blocked at fuze: {outcome}"
    component_label = component_damage_name or component_name or "none"
    system_label = component_damage_system or component_system or "none"
    if sample_gate in {"sample_passed", "sample_rejected"}:
        comparator = "<=" if sample_gate == "sample_passed" else ">"
        sample_text = (
            f"sample {_format_float(sample)}{comparator}"
            f"{_format_float(_bounded_probability(probability))}"
        )
    else:
        sample_text = sample_gate
    capability_pairs = {
        "mission_capability": (mission_before, mission_after),
        "mobility_capability": (mobility_before, mobility_after),
        "sensor_capability": (sensor_before, sensor_after),
        "survivability_margin": (survivability_before, survivability_after),
    }
    before, after = capability_pairs.get(capability_attribution, (float("nan"), float("nan")))
    if capability_attribution != "none":
        capability_text = (
            f"{capability_attribution} {_format_float(before)}->{_format_float(after)}"
        )
    else:
        capability_text = "no capability threshold pressure"
    return f"{outcome} via {component_label}/{system_label}; {sample_text}; {capability_text}"

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
    system_health_delta = finite_float(
        episode_summary.get("lethality_chain_system_health_delta", float("nan"))
    )
    mission_kill = _bool_value(episode_summary.get("lethality_chain_mission_kill", False))
    mobility_kill = _bool_value(episode_summary.get("lethality_chain_mobility_kill", False))
    sensor_kill = _bool_value(episode_summary.get("lethality_chain_sensor_kill", False))
    destroyed = _bool_value(episode_summary.get("lethality_chain_destroyed", False))
    loss_state = str(episode_summary.get("lethality_chain_loss_state", "") or "")
    effects_event_count = int(episode_summary.get("effects_event_count", 0) or 0)
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
    fuze_type = str(episode_summary.get("lethality_chain_fuze_type", "") or "")
    fuze_delay_s = finite_float(
        episode_summary.get("lethality_chain_fuze_delay_s", float("nan"))
    )
    fuze_reliability = finite_float(
        episode_summary.get("lethality_chain_fuze_reliability", float("nan"))
    )
    fuze_sample = finite_float(
        episode_summary.get("lethality_chain_fuze_sample", float("nan"))
    )
    fuze_expected_probability = finite_float(
        episode_summary.get(
            "lethality_chain_fuze_expected_detonation_probability",
            float("nan"),
        )
    )
    fuze_trigger_radius_m = finite_float(
        episode_summary.get("lethality_chain_fuze_trigger_radius_m", float("nan"))
    )
    miss_distance_m = finite_float(
        episode_summary.get("lethality_chain_miss_distance_m", float("nan"))
    )
    fuze_distance_ratio = _fuze_trigger_distance_ratio(
        miss_distance_m,
        fuze_trigger_radius_m,
    )
    fuze_trigger_quality = _fuze_trigger_quality(
        miss_distance_m,
        fuze_trigger_radius_m,
    )
    fuze_sample_gate = _fuze_sample_gate(fuze_expected_probability, fuze_sample)
    fuze_gate_summary = _fuze_gate_summary(
        fuze_type=fuze_type,
        failure_reason=fuze_failure_reason,
        miss_distance_m=miss_distance_m,
        trigger_radius_m=fuze_trigger_radius_m,
        trigger_quality=fuze_trigger_quality,
        probability=fuze_expected_probability,
        sample=fuze_sample,
        sample_gate=fuze_sample_gate,
    )
    projected_hitbox_count = int(
        episode_summary.get("lethality_chain_projected_hitbox_count", 0) or 0
    )
    component_hit_count = int(
        episode_summary.get("lethality_chain_component_hit_count", 0) or 0
    )
    component_name = str(episode_summary.get("lethality_chain_component_name", "") or "")
    component_system = str(episode_summary.get("lethality_chain_component_system", "") or "")
    component_damage_name = str(
        episode_summary.get("lethality_chain_component_damage_name", "") or ""
    )
    component_damage_system = str(
        episode_summary.get("lethality_chain_component_damage_system", "") or ""
    )
    component_failure_probability = finite_float(
        episode_summary.get(
            "lethality_chain_component_failure_probability",
            float("nan"),
        )
    )
    component_failure_sample = finite_float(
        episode_summary.get("lethality_chain_component_failure_sample", float("nan"))
    )
    component_sample_gate = _component_sample_gate(
        component_failure_probability,
        component_failure_sample,
    )
    mission_capability_before = finite_float(
        episode_summary.get("lethality_chain_mission_capability_before", float("nan"))
    )
    mission_capability_after = finite_float(
        episode_summary.get("lethality_chain_mission_capability_after", float("nan"))
    )
    mission_capability_delta = _delta_from_before_after(
        episode_summary.get("lethality_chain_mission_capability_delta", float("nan")),
        mission_capability_before,
        mission_capability_after,
    )
    mobility_capability_before = finite_float(
        episode_summary.get("lethality_chain_mobility_capability_before", float("nan"))
    )
    mobility_capability_after = finite_float(
        episode_summary.get("lethality_chain_mobility_capability_after", float("nan"))
    )
    mobility_capability_delta = _delta_from_before_after(
        episode_summary.get("lethality_chain_mobility_capability_delta", float("nan")),
        mobility_capability_before,
        mobility_capability_after,
    )
    sensor_capability_before = finite_float(
        episode_summary.get("lethality_chain_sensor_capability_before", float("nan"))
    )
    sensor_capability_after = finite_float(
        episode_summary.get("lethality_chain_sensor_capability_after", float("nan"))
    )
    sensor_capability_delta = _delta_from_before_after(
        episode_summary.get("lethality_chain_sensor_capability_delta", float("nan")),
        sensor_capability_before,
        sensor_capability_after,
    )
    survivability_margin_before = finite_float(
        episode_summary.get("lethality_chain_survivability_margin_before", float("nan"))
    )
    survivability_margin_after = finite_float(
        episode_summary.get("lethality_chain_survivability_margin_after", float("nan"))
    )
    survivability_margin_delta = _delta_from_before_after(
        episode_summary.get("lethality_chain_survivability_margin_delta", float("nan")),
        survivability_margin_before,
        survivability_margin_after,
    )
    primary_damage_channel = _primary_damage_channel(
        component_damage_system=component_damage_system,
        component_system=component_system,
        effective_system_consequence=effective_system_consequence,
    )
    capability_attribution = _capability_attribution(
        mission_delta=mission_capability_delta,
        mobility_delta=mobility_capability_delta,
        sensor_delta=sensor_capability_delta,
        survivability_delta=survivability_margin_delta,
    )
    damage_chain_outcome = _damage_chain_outcome(
        released=bool(release_count > 0),
        effects_event_count=effects_event_count,
        effective_detonation=effective_detonation,
        effective_component_damage=effective_component_damage,
        effective_system_consequence=effective_system_consequence,
        fuze_failure_reason=fuze_failure_reason,
        projected_hitbox_count=projected_hitbox_count,
        component_hit_count=component_hit_count,
        component_name=component_name,
        component_sample_gate=component_sample_gate,
        mission_kill=mission_kill,
        mobility_kill=mobility_kill,
        sensor_kill=sensor_kill,
        destroyed=destroyed,
    )
    attribution_summary = _attribution_summary(
        outcome=damage_chain_outcome,
        component_name=component_name,
        component_system=component_system,
        component_damage_name=component_damage_name,
        component_damage_system=component_damage_system,
        probability=component_failure_probability,
        sample=component_failure_sample,
        sample_gate=component_sample_gate,
        capability_attribution=capability_attribution,
        mission_before=mission_capability_before,
        mission_after=mission_capability_after,
        mobility_before=mobility_capability_before,
        mobility_after=mobility_capability_after,
        sensor_before=sensor_capability_before,
        sensor_after=sensor_capability_after,
        survivability_before=survivability_margin_before,
        survivability_after=survivability_margin_after,
    )
    return {
        "delay_steps": int(delay),
        "episode": episode,
        "episode_seed": int(payload_seed + episode),
        "released": bool(release_count > 0),
        "release_count": release_count,
        "first_release_step": episode_summary.get("first_release_step"),
        "first_release_sim_time_s": finite_float(
            episode_summary.get("first_release_sim_time_s", float("nan"))
        ),
        "first_release_target_range_geom_m": finite_float(
            episode_summary.get("first_release_target_range_geom_m", float("nan"))
        ),
        "first_release_target_range_track_m": finite_float(
            episode_summary.get("first_release_target_range_track_m", float("nan"))
        ),
        "first_release_target_track_age_s": finite_float(
            episode_summary.get("first_release_target_track_age_s", float("nan"))
        ),
        "first_release_legal_window_age_steps": int(
            episode_summary.get("first_release_legal_window_age_steps", 0) or 0
        ),
        "first_release_engagement_state": str(
            episode_summary.get("first_release_engagement_state", "") or ""
        ),
        "total_reward": finite_float(episode_summary.get("total_reward", float("nan"))),
        "final_target_health": finite_float(
            episode_summary.get("final_target_health", float("nan"))
        ),
        "target_health_delta_from_release": (
            finite_float(episode_summary.get("final_target_health", float("nan")))
            - finite_float(episode_summary.get("first_release_target_health", float("nan")))
        ),
        "effects_event_count": effects_event_count,
        "damage_report_count": int(episode_summary.get("damage_report_count", 0) or 0),
        "first_effects_event_step": episode_summary.get("first_effects_event_step"),
        "first_damage_report_step": episode_summary.get("first_damage_report_step"),
        "first_damage_consequence_reward_step": episode_summary.get(
            "first_damage_consequence_reward_step"
        ),
        "damage_consequence_reward_total": finite_float(
            episode_summary.get("damage_consequence_reward_total", 0.0),
            0.0,
        ),
        "target_damage_consequence_reward_total": finite_float(
            episode_summary.get("target_damage_consequence_reward_total", 0.0),
            0.0,
        ),
        "lethality_chain_miss_distance_m": miss_distance_m,
        "lethality_chain_closure_mps": finite_float(
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
        "lethality_chain_fuze_type": fuze_type,
        "lethality_chain_fuze_triggered": fuze_triggered,
        "lethality_chain_fuze_failure_reason": fuze_failure_reason,
        "lethality_chain_fuze_delay_s": fuze_delay_s,
        "lethality_chain_fuze_reliability": fuze_reliability,
        "lethality_chain_fuze_sample": fuze_sample,
        "lethality_chain_fuze_expected_detonation_probability": fuze_expected_probability,
        "lethality_chain_fuze_sampled_outcome": _bool_value(
            episode_summary.get("lethality_chain_fuze_sampled_outcome", False)
        ),
        "lethality_chain_fuze_trigger_radius_m": fuze_trigger_radius_m,
        "lethality_chain_fuze_distance_ratio": fuze_distance_ratio,
        "lethality_chain_fuze_trigger_quality": fuze_trigger_quality,
        "lethality_chain_fuze_sample_gate": fuze_sample_gate,
        "lethality_chain_fuze_gate_summary": fuze_gate_summary,
        "lethality_chain_projected_hitbox_count": projected_hitbox_count,
        "lethality_chain_component_hit_count": component_hit_count,
        "effective_detonation": bool(effective_detonation),
        "effective_component_damage": bool(effective_component_damage),
        "effective_system_consequence": bool(effective_system_consequence),
        "terminal_negative_reason": (
            fuze_failure_reason if not effective_detonation and fuze_failure_reason else ""
        ),
        "damage_chain_outcome": damage_chain_outcome,
        "damage_chain_blocker": _damage_chain_blocker(damage_chain_outcome),
        "damage_chain_primary_channel": primary_damage_channel,
        "damage_chain_capability_attribution": capability_attribution,
        "damage_chain_component_sample_gate": component_sample_gate,
        "damage_chain_attribution_summary": attribution_summary,
        "lethality_chain_component_name": component_name,
        "lethality_chain_component_system": component_system,
        "lethality_chain_component_damage_count": int(
            episode_summary.get("lethality_chain_component_damage_count", 0) or 0
        ),
        "lethality_chain_component_damage_name": component_damage_name,
        "lethality_chain_component_damage_system": component_damage_system,
        "lethality_chain_component_failure_mode": str(
            episode_summary.get("lethality_chain_component_failure_mode", "") or ""
        ),
        "lethality_chain_component_failure_severity": finite_float(
            episode_summary.get("lethality_chain_component_failure_severity", float("nan"))
        ),
        "lethality_chain_component_failure_probability": component_failure_probability,
        "lethality_chain_component_failure_sample": component_failure_sample,
        "lethality_chain_component_integrity_before": finite_float(
            episode_summary.get("lethality_chain_component_integrity_before", float("nan"))
        ),
        "lethality_chain_component_integrity_after": finite_float(
            episode_summary.get("lethality_chain_component_integrity_after", float("nan"))
        ),
        "lethality_chain_system_health_delta": finite_float(
            episode_summary.get("lethality_chain_system_health_delta", float("nan"))
        ),
        "lethality_chain_mission_capability_before": mission_capability_before,
        "lethality_chain_mission_capability_after": mission_capability_after,
        "lethality_chain_mission_capability_delta": mission_capability_delta,
        "lethality_chain_mobility_capability_before": mobility_capability_before,
        "lethality_chain_mobility_capability_after": mobility_capability_after,
        "lethality_chain_mobility_capability_delta": mobility_capability_delta,
        "lethality_chain_sensor_capability_before": sensor_capability_before,
        "lethality_chain_sensor_capability_after": sensor_capability_after,
        "lethality_chain_sensor_capability_delta": sensor_capability_delta,
        "lethality_chain_survivability_margin_before": survivability_margin_before,
        "lethality_chain_survivability_margin_after": survivability_margin_after,
        "lethality_chain_survivability_margin_delta": survivability_margin_delta,
        "lethality_chain_control_delta": finite_float(
            episode_summary.get("lethality_chain_control_delta", float("nan"))
        ),
        "lethality_chain_engine_delta": finite_float(
            episode_summary.get("lethality_chain_engine_delta", float("nan"))
        ),
        "lethality_chain_fuel_leak_delta": finite_float(
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

def _summarize_delay(
    delay: int,
    records: list[dict[str, Any]],
    *,
    confidence_level: float = 0.95,
    rate_ci_width_epsilon: float = 0.5,
    outcome_sem_epsilon: float = 0.15,
    range_sem_epsilon_m: float = 500.0,
) -> dict[str, Any]:
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

    z_score = _confidence_z(float(confidence_level))
    confidence_fields: dict[str, Any] = {
        "seed_sample_count": episode_count,
        "seed_confidence_level": float(confidence_level),
        "seed_confidence_z": float(z_score),
    }
    confidence_fields.update(
        _binary_confidence_fields(
            "release_rate",
            success_count=len(released_records),
            sample_count=episode_count,
            z_score=z_score,
        )
    )
    confidence_fields.update(
        _binary_confidence_fields(
            "effects_given_release_rate",
            success_count=_count_true(released_records, "effects_event_count"),
            sample_count=len(released_records),
            z_score=z_score,
        )
    )
    confidence_fields.update(
        _binary_confidence_fields(
            "effective_detonation_given_release_rate",
            success_count=_count_true(released_records, "effective_detonation"),
            sample_count=len(released_records),
            z_score=z_score,
        )
    )
    confidence_fields.update(
        _binary_confidence_fields(
            "fuze_sample_pass_given_release_rate",
            success_count=sum(
                1
                for record in released_records
                if str(record.get("lethality_chain_fuze_sample_gate", ""))
                == "sample_passed"
            ),
            sample_count=len(released_records),
            z_score=z_score,
        )
    )
    confidence_fields.update(
        _binary_confidence_fields(
            "effective_component_damage_given_release_rate",
            success_count=_count_true(released_records, "effective_component_damage"),
            sample_count=len(released_records),
            z_score=z_score,
        )
    )
    confidence_fields.update(
        _binary_confidence_fields(
            "effective_system_consequence_given_release_rate",
            success_count=_count_true(released_records, "effective_system_consequence"),
            sample_count=len(released_records),
            z_score=z_score,
        )
    )
    confidence_fields.update(
        _binary_confidence_fields(
            "mission_kill_given_release_rate",
            success_count=_count_true(released_records, "lethality_chain_mission_kill"),
            sample_count=len(released_records),
            z_score=z_score,
        )
    )
    confidence_fields.update(
        _numeric_confidence_fields(
            "release_range_geom_m",
            [record.get("first_release_target_range_geom_m", float("nan")) for record in released_records],
            z_score=z_score,
        )
    )
    confidence_fields.update(
        _numeric_confidence_fields(
            "miss_distance_m",
            [record.get("lethality_chain_miss_distance_m", float("nan")) for record in records],
            z_score=z_score,
        )
    )
    confidence_fields.update(
        _numeric_confidence_fields(
            "fuze_trigger_radius_m",
            [
                record.get("lethality_chain_fuze_trigger_radius_m", float("nan"))
                for record in records
            ],
            z_score=z_score,
        )
    )
    confidence_fields.update(
        _numeric_confidence_fields(
            "fuze_distance_ratio",
            [
                record.get("lethality_chain_fuze_distance_ratio", float("nan"))
                for record in records
            ],
            z_score=z_score,
        )
    )
    confidence_fields.update(
        _numeric_confidence_fields(
            "fuze_trigger_quality",
            [
                record.get("lethality_chain_fuze_trigger_quality", float("nan"))
                for record in records
            ],
            z_score=z_score,
        )
    )
    confidence_fields.update(
        _numeric_confidence_fields(
            "fuze_sample",
            [record.get("lethality_chain_fuze_sample", float("nan")) for record in records],
            z_score=z_score,
        )
    )
    confidence_fields.update(
        _numeric_confidence_fields(
            "component_failure_probability",
            [
                record.get("lethality_chain_component_failure_probability", float("nan"))
                for record in records
            ],
            z_score=z_score,
        )
    )
    confidence_fields.update(
        _numeric_confidence_fields(
            "system_health_delta",
            [record.get("lethality_chain_system_health_delta", float("nan")) for record in records],
            z_score=z_score,
        )
    )
    confidence_fields.update(
        _numeric_confidence_fields(
            "mission_capability_delta",
            [
                record.get("lethality_chain_mission_capability_delta", float("nan"))
                for record in records
            ],
            z_score=z_score,
        )
    )
    confidence_fields.update(
        _numeric_confidence_fields(
            "total_reward",
            [record.get("total_reward", float("nan")) for record in records],
            z_score=z_score,
        )
    )
    confidence_fields.update(
        _numeric_confidence_fields(
            "fuze_expected_detonation_probability",
            [
                record.get(
                    "lethality_chain_fuze_expected_detonation_probability",
                    float("nan"),
                )
                for record in records
            ],
            z_score=z_score,
        )
    )
    confidence_flags = []
    rate_width_fields = (
        "release_rate_ci_width",
        "effects_given_release_rate_ci_width",
        "effective_detonation_given_release_rate_ci_width",
        "effective_component_damage_given_release_rate_ci_width",
        "effective_system_consequence_given_release_rate_ci_width",
        "mission_kill_given_release_rate_ci_width",
    )
    for field in rate_width_fields:
        if finite_float(confidence_fields.get(field, float("nan"))) > float(rate_ci_width_epsilon):
            confidence_flags.append(f"{field}_wide")
    if finite_float(confidence_fields.get("component_failure_probability_sem", float("nan"))) > float(
        outcome_sem_epsilon
    ):
        confidence_flags.append("component_failure_probability_sem_high")
    if finite_float(confidence_fields.get("system_health_delta_sem", float("nan"))) > float(
        outcome_sem_epsilon
    ):
        confidence_flags.append("system_health_delta_sem_high")
    if finite_float(confidence_fields.get("mission_capability_delta_sem", float("nan"))) > float(
        outcome_sem_epsilon
    ):
        confidence_flags.append("mission_capability_delta_sem_high")
    if finite_float(confidence_fields.get("release_range_geom_m_sem", float("nan"))) > float(
        range_sem_epsilon_m
    ):
        confidence_flags.append("release_range_geom_m_sem_high")
    confidence_fields["seed_confidence_flags"] = confidence_flags
    confidence_fields["seed_high_variance"] = bool(confidence_flags)

    summary = {
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
        "fuze_sample_pass_given_release_rate": (
            float(
                sum(
                    1
                    for record in released_records
                    if str(record.get("lethality_chain_fuze_sample_gate", ""))
                    == "sample_passed"
                )
                / len(released_records)
            )
            if released_records
            else float("nan")
        ),
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
        "mean_first_release_step": mean_finite(
            [finite_float(record.get("first_release_step", float("nan"))) for record in released_records]
        ),
        "mean_release_range_geom_m": mean_finite(
            [float(record["first_release_target_range_geom_m"]) for record in released_records]
        ),
        "mean_release_range_track_m": mean_finite(
            [float(record["first_release_target_range_track_m"]) for record in released_records]
        ),
        "mean_release_window_age_steps": mean_finite(
            [
                finite_float(record.get("first_release_legal_window_age_steps", float("nan")))
                for record in released_records
            ]
        ),
        "mean_total_reward": mean_finite([float(record["total_reward"]) for record in records]),
        "mean_final_target_health": mean_finite(
            [float(record["final_target_health"]) for record in records]
        ),
        "mean_target_health_delta_from_release": mean_finite(
            [float(record["target_health_delta_from_release"]) for record in released_records]
        ),
        "mean_damage_consequence_reward_total": mean_finite(
            [float(record["damage_consequence_reward_total"]) for record in records]
        ),
        "mean_target_damage_consequence_reward_total": mean_finite(
            [float(record["target_damage_consequence_reward_total"]) for record in records]
        ),
        "mean_miss_distance_m": mean_finite(
            [float(record["lethality_chain_miss_distance_m"]) for record in records]
        ),
        "mean_fuze_trigger_radius_m": mean_finite(
            [
                finite_float(record.get("lethality_chain_fuze_trigger_radius_m", float("nan")))
                for record in records
            ]
        ),
        "mean_fuze_distance_ratio": mean_finite(
            [
                finite_float(record.get("lethality_chain_fuze_distance_ratio", float("nan")))
                for record in records
            ]
        ),
        "mean_fuze_trigger_quality": mean_finite(
            [
                finite_float(record.get("lethality_chain_fuze_trigger_quality", float("nan")))
                for record in records
            ]
        ),
        "mean_fuze_sample": mean_finite(
            [
                finite_float(record.get("lethality_chain_fuze_sample", float("nan")))
                for record in records
            ]
        ),
        "mean_fuze_expected_detonation_probability": mean_finite(
            [
                finite_float(
                    record.get(
                        "lethality_chain_fuze_expected_detonation_probability",
                        float("nan"),
                    )
                )
                for record in records
            ]
        ),
        "mean_lethality_chain_row_count": mean_finite(
            [finite_float(record.get("lethality_chain_row_count", float("nan"))) for record in records]
        ),
        "mean_closure_mps": mean_finite(
            [float(record["lethality_chain_closure_mps"]) for record in records]
        ),
        "mean_component_failure_probability": mean_finite(
            [
                float(record["lethality_chain_component_failure_probability"])
                for record in records
            ]
        ),
        "mean_component_failure_sample": mean_finite(
            [float(record["lethality_chain_component_failure_sample"]) for record in records]
        ),
        "mean_component_damage_count": mean_finite(
            [finite_float(record.get("lethality_chain_component_damage_count", float("nan"))) for record in records]
        ),
        "mean_component_integrity_delta": mean_finite(
            [
                float(record["lethality_chain_component_integrity_after"])
                - float(record["lethality_chain_component_integrity_before"])
                for record in records
            ]
        ),
        "mean_system_health_delta": mean_finite(
            [float(record["lethality_chain_system_health_delta"]) for record in records]
        ),
        "mean_mission_capability_before": mean_finite(
            [float(record["lethality_chain_mission_capability_before"]) for record in records]
        ),
        "mean_mission_capability_after": mean_finite(
            [float(record["lethality_chain_mission_capability_after"]) for record in records]
        ),
        "mean_mission_capability_delta": mean_finite(
            [float(record["lethality_chain_mission_capability_delta"]) for record in records]
        ),
        "mean_mobility_capability_before": mean_finite(
            [float(record["lethality_chain_mobility_capability_before"]) for record in records]
        ),
        "mean_mobility_capability_after": mean_finite(
            [float(record["lethality_chain_mobility_capability_after"]) for record in records]
        ),
        "mean_mobility_capability_delta": mean_finite(
            [float(record["lethality_chain_mobility_capability_delta"]) for record in records]
        ),
        "mean_sensor_capability_before": mean_finite(
            [float(record["lethality_chain_sensor_capability_before"]) for record in records]
        ),
        "mean_sensor_capability_after": mean_finite(
            [float(record["lethality_chain_sensor_capability_after"]) for record in records]
        ),
        "mean_sensor_capability_delta": mean_finite(
            [float(record["lethality_chain_sensor_capability_delta"]) for record in records]
        ),
        "mean_survivability_margin_before": mean_finite(
            [float(record["lethality_chain_survivability_margin_before"]) for record in records]
        ),
        "mean_survivability_margin_after": mean_finite(
            [float(record["lethality_chain_survivability_margin_after"]) for record in records]
        ),
        "mean_survivability_margin_delta": mean_finite(
            [float(record["lethality_chain_survivability_margin_delta"]) for record in records]
        ),
        "mean_control_delta": mean_finite(
            [float(record["lethality_chain_control_delta"]) for record in records]
        ),
        "mean_engine_delta": mean_finite(
            [float(record["lethality_chain_engine_delta"]) for record in records]
        ),
        "mean_fuel_leak_delta": mean_finite(
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
        "fuze_sample_gate_counts": dict(
            sorted(
                Counter(
                    str(record.get("lethality_chain_fuze_sample_gate", "") or "")
                    for record in records
                ).items()
            )
        ),
        "fuze_gate_summary_counts": dict(
            sorted(
                Counter(
                    str(record.get("lethality_chain_fuze_gate_summary", "") or "")
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
        "damage_chain_outcome_counts": dict(
            sorted(
                Counter(
                    str(record.get("damage_chain_outcome", "") or "")
                    for record in records
                ).items()
            )
        ),
        "damage_chain_blocker_counts": dict(
            sorted(
                Counter(
                    str(record.get("damage_chain_blocker", "") or "")
                    for record in records
                ).items()
            )
        ),
        "damage_chain_primary_channel_counts": dict(
            sorted(
                Counter(
                    str(record.get("damage_chain_primary_channel", "") or "")
                    for record in records
                ).items()
            )
        ),
        "damage_chain_capability_attribution_counts": dict(
            sorted(
                Counter(
                    str(record.get("damage_chain_capability_attribution", "") or "")
                    for record in records
                ).items()
            )
        ),
        "damage_chain_component_sample_gate_counts": dict(
            sorted(
                Counter(
                    str(record.get("damage_chain_component_sample_gate", "") or "")
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
    summary.update(confidence_fields)
    return summary

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
        [finite_float(row.get("mean_release_range_geom_m", float("nan"))) for row in released]
    )
    reward_spread = _spread(
        [finite_float(row.get("mean_total_reward", float("nan"))) for row in released]
    )
    final_health_spread = _spread(
        [finite_float(row.get("mean_final_target_health", float("nan"))) for row in released]
    )
    component_probability_spread = _spread(
        [
            finite_float(row.get("mean_component_failure_probability", float("nan")))
            for row in released
        ]
    )
    system_health_delta_spread = _spread(
        [finite_float(row.get("mean_system_health_delta", float("nan"))) for row in released]
    )
    miss_distance_spread_m = _spread(
        [finite_float(row.get("mean_miss_distance_m", float("nan"))) for row in released]
    )
    damage_reward_spread = _spread(
        [
            finite_float(row.get("mean_damage_consequence_reward_total", float("nan")))
            for row in released
        ]
    )
    mission_kill_rate_spread = _spread(
        [finite_float(row.get("mission_kill_rate", float("nan"))) for row in released]
    )
    mission_kill_given_release_rate_spread = _spread(
        [
            finite_float(row.get("mission_kill_given_release_rate", float("nan")))
            for row in released
        ]
    )
    effects_rate_spread = _spread(
        [finite_float(row.get("effects_rate", float("nan"))) for row in released]
    )
    damage_rate_spread = _spread(
        [finite_float(row.get("damage_rate", float("nan"))) for row in released]
    )
    effective_detonation_rate_spread = _spread(
        [
            finite_float(row.get("effective_detonation_rate", float("nan")))
            for row in released
        ]
    )
    effective_component_damage_rate_spread = _spread(
        [
            finite_float(row.get("effective_component_damage_rate", float("nan")))
            for row in released
        ]
    )
    effective_system_consequence_rate_spread = _spread(
        [
            finite_float(row.get("effective_system_consequence_rate", float("nan")))
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

def _max_finite(rows: list[dict[str, Any]], key: str) -> float:
    values = [finite_float(row.get(key, float("nan"))) for row in rows]
    finite = [value for value in values if math.isfinite(value)]
    return float(max(finite)) if finite else float("nan")

def _confidence_summary(
    delay_summaries: list[dict[str, Any]],
    *,
    rate_ci_width_epsilon: float,
    outcome_sem_epsilon: float,
    range_sem_epsilon_m: float,
) -> dict[str, Any]:
    high_variance_rows = [
        row
        for row in delay_summaries
        if bool(row.get("seed_high_variance", False))
    ]
    high_variance_delays = [
        int(row.get("delay_steps", 0) or 0)
        for row in high_variance_rows
    ]
    released_rows = [
        row
        for row in delay_summaries
        if int(row.get("release_episode_count", 0) or 0) > 0
    ]
    mission_uncertain = [
        int(row.get("delay_steps", 0) or 0)
        for row in released_rows
        if finite_float(row.get("mission_kill_given_release_rate_ci_width", float("nan")))
        > float(rate_ci_width_epsilon)
    ]
    consequence_uncertain = [
        int(row.get("delay_steps", 0) or 0)
        for row in released_rows
        if (
            finite_float(row.get("system_health_delta_sem", float("nan")))
            > float(outcome_sem_epsilon)
            or finite_float(row.get("mission_capability_delta_sem", float("nan")))
            > float(outcome_sem_epsilon)
        )
    ]
    return {
        "rate_ci_width_epsilon": float(rate_ci_width_epsilon),
        "outcome_sem_epsilon": float(outcome_sem_epsilon),
        "range_sem_epsilon_m": float(range_sem_epsilon_m),
        "high_variance_delay_count": int(len(high_variance_delays)),
        "high_variance_delay_steps": high_variance_delays,
        "mission_kill_uncertain_delay_steps": mission_uncertain,
        "platform_consequence_uncertain_delay_steps": consequence_uncertain,
        "max_release_rate_ci_width": _max_finite(delay_summaries, "release_rate_ci_width"),
        "max_mission_kill_given_release_rate_ci_width": _max_finite(
            delay_summaries,
            "mission_kill_given_release_rate_ci_width",
        ),
        "max_effective_component_damage_given_release_rate_ci_width": _max_finite(
            delay_summaries,
            "effective_component_damage_given_release_rate_ci_width",
        ),
        "max_component_failure_probability_sem": _max_finite(
            delay_summaries,
            "component_failure_probability_sem",
        ),
        "max_system_health_delta_sem": _max_finite(
            delay_summaries,
            "system_health_delta_sem",
        ),
        "max_mission_capability_delta_sem": _max_finite(
            delay_summaries,
            "mission_capability_delta_sem",
        ),
        "interpretation": (
            "Some release-window samples remain seed-sensitive; treat mean "
            "kill-chain outcomes as low-confidence until sample count increases "
            "or the high-variance stages are explained."
            if high_variance_delays
            else "No delay crossed the configured seed-variance warning thresholds."
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
            confidence_level=float(args.confidence_level),
            rate_ci_width_epsilon=float(args.rate_ci_width_epsilon),
            outcome_sem_epsilon=float(args.outcome_sem_epsilon),
            range_sem_epsilon_m=float(args.range_sem_epsilon_m),
        )
        for delay in delays
    ]
    return {
        "schema_version": "fire_timing.window_position_sweep.v5",
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
            "damage_chain_outcome",
            "damage_chain_blocker",
            "damage_chain_primary_channel",
            "damage_chain_capability_attribution",
            "damage_chain_component_sample_gate",
            "damage_chain_attribution_summary",
            "lethality_chain_fuze_type",
            "lethality_chain_fuze_triggered",
            "lethality_chain_fuze_failure_reason",
            "lethality_chain_fuze_delay_s",
            "lethality_chain_fuze_reliability",
            "lethality_chain_fuze_sample",
            "lethality_chain_fuze_expected_detonation_probability",
            "lethality_chain_fuze_sampled_outcome",
            "lethality_chain_fuze_trigger_radius_m",
            "lethality_chain_fuze_distance_ratio",
            "lethality_chain_fuze_trigger_quality",
            "lethality_chain_fuze_sample_gate",
            "lethality_chain_fuze_gate_summary",
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
            "seed_confidence_flags",
            "mission_kill_given_release_rate_ci_width",
            "component_failure_probability_sem",
            "system_health_delta_sem",
        ],
        "records": records,
        "delay_summaries": delay_summaries,
        "confidence_summary": _confidence_summary(
            delay_summaries,
            rate_ci_width_epsilon=float(args.rate_ci_width_epsilon),
            outcome_sem_epsilon=float(args.outcome_sem_epsilon),
            range_sem_epsilon_m=float(args.range_sem_epsilon_m),
        ),
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
    write_json_output(
        path,
        payload,
        allow_nan=False,
        skip_empty_path=False,
        transform=_json_safe,
    )

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
        finite_float(row.get("mean_release_range_geom_m", float("nan"))) / 1000.0
        for row in summaries
    ]
    release_range_sem_km = [
        finite_float(row.get("release_range_geom_m_sem", float("nan"))) / 1000.0
        for row in summaries
    ]
    rewards = [finite_float(row.get("mean_total_reward", float("nan"))) for row in summaries]
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
        finite_float(row.get("mean_miss_distance_m", float("nan"))) for row in summaries
    ]
    hit_quality = [
        finite_float(row.get("mean_fuze_trigger_quality", float("nan")))
        for row in summaries
    ]
    for index, value in enumerate(hit_quality):
        if math.isfinite(value):
            continue
        miss_value = miss_distance[index]
        hit_quality[index] = (
            1.0 / (1.0 + miss_value)
            if math.isfinite(miss_value) and miss_value >= 0.0
            else float("nan")
        )
    system_damage_magnitude = [
        max(0.0, -finite_float(row.get("mean_system_health_delta", float("nan"))))
        for row in summaries
    ]
    system_damage_sem = [
        finite_float(row.get("system_health_delta_sem", float("nan")))
        for row in summaries
    ]
    mission_damage_magnitude = [
        max(0.0, -finite_float(row.get("mean_mission_capability_delta", float("nan"))))
        for row in summaries
    ]
    component_prob = [
        finite_float(row.get("mean_component_failure_probability", float("nan")))
        for row in summaries
    ]
    component_prob_sem = [
        finite_float(row.get("component_failure_probability_sem", float("nan")))
        for row in summaries
    ]
    fuze_expected = [
        finite_float(row.get("mean_fuze_expected_detonation_probability", float("nan")))
        for row in summaries
    ]
    fuze_expected_sem = [
        finite_float(row.get("fuze_expected_detonation_probability_sem", float("nan")))
        for row in summaries
    ]
    fuze_sample = [
        finite_float(row.get("mean_fuze_sample", float("nan"))) for row in summaries
    ]
    release = [finite_float(row.get("release_rate", float("nan"))) for row in summaries]
    fuze_sample_pass = [
        finite_float(row.get("fuze_sample_pass_given_release_rate", float("nan")))
        for row in summaries
    ]
    detonation = [
        finite_float(row.get("effective_detonation_given_release_rate", float("nan")))
        for row in summaries
    ]
    component_damage = [
        finite_float(
            row.get("effective_component_damage_given_release_rate", float("nan"))
        )
        for row in summaries
    ]
    mission_kill = [
        finite_float(row.get("mission_kill_given_release_rate", float("nan")))
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
    axes[0].errorbar(
        x,
        release_range_km,
        yerr=[value if math.isfinite(value) else 0.0 for value in release_range_sem_km],
        marker="o",
        capsize=3,
    )
    axes[0].set_ylabel("release range\nkm")
    axes[1].bar(x, reward_delta_scaled, color="tab:green", alpha=0.78)
    axes[1].axhline(0.0, color="#111827", linewidth=0.8)
    axes[1].set_ylabel("return delta\nx1e-5")

    def scatter_valid(values: list[float], *, label: str, color: str, marker: str) -> None:
        valid_x = [pos for pos, value in zip(x, values, strict=True) if math.isfinite(value)]
        valid_y = [value for value in values if math.isfinite(value)]
        axes[2].scatter(valid_x, valid_y, label=label, color=color, marker=marker, s=58)

    def errorbar_valid(
        values: list[float],
        errors: list[float],
        *,
        label: str,
        color: str,
        marker: str,
    ) -> None:
        valid = [
            (pos, value, err)
            for pos, value, err in zip(x, values, errors, strict=True)
            if math.isfinite(value)
        ]
        if not valid:
            return
        axes[2].errorbar(
            [item[0] for item in valid],
            [item[1] for item in valid],
            yerr=[item[2] if math.isfinite(item[2]) else 0.0 for item in valid],
            label=label,
            color=color,
            marker=marker,
            linestyle="none",
            capsize=3,
            markersize=6,
        )

    errorbar_valid(
        system_damage_magnitude,
        system_damage_sem,
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
    errorbar_valid(
        component_prob,
        component_prob_sem,
        label="component P(fail)",
        color="tab:purple",
        marker="s",
    )
    errorbar_valid(
        fuze_expected,
        fuze_expected_sem,
        label="fuze E[P(det)]",
        color="tab:cyan",
        marker="x",
    )
    scatter_valid(hit_quality, label="fuze quality", color="tab:orange", marker="^")
    scatter_valid(fuze_sample, label="fuze sample", color="tab:brown", marker="v")
    axes[2].set_ylabel("fuze/damage\ntarget")
    axes[2].set_ylim(-0.05, 1.05)
    axes[2].legend(loc="upper left", fontsize=8, ncol=3)

    event_matrix = [release, fuze_sample_pass, detonation, component_damage, mission_kill]
    axes[3].imshow(event_matrix, aspect="auto", cmap="YlGnBu", vmin=0.0, vmax=1.0)
    axes[3].set_yticks([0, 1, 2, 3, 4])
    axes[3].set_yticklabels(
        [
            "release",
            "fuze sample pass|rel",
            "detonation|rel",
            "component damage|rel",
            "mission kill|rel",
        ]
    )
    for row_index, row_values in enumerate(event_matrix):
        for col_index, value in enumerate(row_values):
            finite_value = finite_float(value, 0.0)
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
    fig.suptitle("Fire-window lethality-chain diagnostics", fontsize=13)
    out_path = os.path.abspath(path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sweep oracle fire delays across launch-window positions.")
    add_probe_run_args(parser, include=("scenario",), defaults={"scenario": DEFAULT_SCENARIO})
    add_model_load_args(
        parser,
        include=("train_config",),
        defaults={"train_config": DEFAULT_TRAIN_CONFIG},
    )
    add_probe_run_args(
        parser,
        include=("episodes", "seed", "max_steps"),
        defaults={"episodes": 1, "seed": 20260615, "max_steps": 2000},
        helps={
            "episodes": (
                "Independent seed samples per delay; each sample invokes the process "
                "probe with episodes=1."
            ),
        },
    )
    parser.add_argument("--delays", default="0,32,64,128,256,512,768,1024,1280,1536,1664")
    parser.add_argument("--fire_range_m", type=float, default=12000.0)
    parser.add_argument("--legal_fire_range_m", type=float, default=0.0)
    parser.add_argument("--reward_epsilon", type=float, default=1.0)
    parser.add_argument("--health_epsilon", type=float, default=1.0)
    parser.add_argument("--system_health_delta_epsilon", type=float, default=0.1)
    parser.add_argument("--component_failure_probability_epsilon", type=float, default=0.05)
    parser.add_argument("--miss_distance_epsilon_m", type=float, default=1.0)
    parser.add_argument("--range_epsilon_m", type=float, default=500.0)
    parser.add_argument(
        "--confidence_level",
        type=float,
        default=0.95,
        help="Confidence level for per-delay seed variance intervals.",
    )
    parser.add_argument(
        "--rate_ci_width_epsilon",
        type=float,
        default=0.5,
        help="Flag Bernoulli event rates whose Wilson interval width exceeds this value.",
    )
    parser.add_argument(
        "--outcome_sem_epsilon",
        type=float,
        default=0.15,
        help="Flag normalized outcome metrics whose standard error exceeds this value.",
    )
    parser.add_argument(
        "--range_sem_epsilon_m",
        type=float,
        default=500.0,
        help="Flag release-range estimates whose standard error exceeds this many meters.",
    )
    parser.add_argument("--diagnostic_dcr_bridge", action="store_true")
    parser.add_argument("--diagnostic_dcr_bridge_target_reward", type=float, default=0.0)
    parser.add_argument("--diagnostic_dcr_bridge_self_reward", type=float, default=0.0)
    parser.add_argument("--include_cases", action="store_true")
    parser.add_argument(
        "--output_dir",
        default=DEFAULT_OUTPUT_DIR,
    )
    add_json_out_arg(parser)
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
