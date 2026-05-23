from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import ef_py

from .common import (
    _normalize_waypoint_mode,
    _OBJECTIVE_DYNAMIC_TARGET_MAP,
    _OBJECTIVE_OP_MAP,
    _OBJECTIVE_PROPERTY_MAP,
)
from .layout_template import CompiledWorldLayoutTemplate


def _compile_conditional_objectives(objectives: Any) -> tuple[Any, ...]:
    compiled = []
    if not isinstance(objectives, list):
        return tuple(compiled)
    for obj in objectives:
        if not isinstance(obj, dict):
            continue
        if str(obj.get("type", "")).strip().lower() != "conditional":
            continue
        spec = ef_py.ConditionalObjectiveSpec()
        spec.reward_bonus = float(obj.get("reward", 1000.0))
        conds = []
        for cond in obj.get("conditions", []):
            if not isinstance(cond, dict):
                continue
            compiled_cond = ef_py.ConditionalObjectiveCondition()
            prop_key = str(cond.get("property", "")).strip()
            compiled_cond.property_code = _OBJECTIVE_PROPERTY_MAP.get(
                prop_key,
                ef_py.ConditionalObjectiveProperty.Unknown,
            )
            compiled_cond.op_code = _OBJECTIVE_OP_MAP.get(
                str(cond.get("op", ">=")).strip(),
                ef_py.ConditionalObjectiveOp.GreaterEqual,
            )
            compiled_cond.target_kind = ef_py.ConditionalObjectiveTargetKind.Literal
            compiled_cond.target_scale = 1.0
            tgt = cond.get("value", 0.0)
            if isinstance(tgt, str):
                target_info = _OBJECTIVE_DYNAMIC_TARGET_MAP.get(tgt.strip().upper())
                if target_info is not None:
                    compiled_cond.target_kind = target_info[0]
                    compiled_cond.target_scale = float(cond.get("scale", target_info[1]))
                    compiled_cond.target_value = 0.0
                else:
                    try:
                        compiled_cond.target_value = float(tgt)
                    except Exception:
                        compiled_cond.target_value = 0.0
            else:
                try:
                    compiled_cond.target_value = float(tgt)
                except Exception:
                    compiled_cond.target_value = 0.0
            conds.append(compiled_cond)
        spec.conditions = conds
        compiled.append(spec)
    return tuple(compiled)


def _objective_shaping_binding_error(exc: Exception) -> RuntimeError:
    return RuntimeError(
        "conditional objective reward shaping requires ef_py.ObjectiveShapingConfig(), "
        "but that binding is unavailable. Rebuild or install the matching runtime bindings "
        "before using conditional objectives."
    ).with_traceback(exc.__traceback__)


def _build_objective_shaping_config(
    cfg: dict[str, Any] | None,
    *,
    required: bool = False,
) -> Any:
    cfg = cfg if isinstance(cfg, dict) else {}
    if not cfg and not required:
        return None
    try:
        shaping = ef_py.ObjectiveShapingConfig()
    except Exception as exc:
        raise _objective_shaping_binding_error(exc) from exc
    shaping.runway_cross_penalty_weight = float(cfg.get("success_runway_cross_penalty_weight", 0.0))
    shaping.runway_cross_deadband_m = float(cfg.get("success_runway_cross_deadband_m", 0.0))
    shaping.runway_cross_norm_m = float(cfg.get("success_runway_cross_norm_m", 20.0))
    shaping.runway_cross_power = float(cfg.get("success_runway_cross_power", 2.0))
    shaping.runway_cross_clip = float(cfg.get("success_runway_cross_clip", 0.0))
    shaping.ground_track_penalty_weight = float(cfg.get("success_ground_track_error_penalty_weight", 0.0))
    shaping.ground_track_deadband_deg = float(cfg.get("success_ground_track_error_deadband_deg", 0.0))
    shaping.ground_track_norm_deg = float(cfg.get("success_ground_track_error_norm_deg", 10.0))
    shaping.ground_track_power = float(cfg.get("success_ground_track_error_power", 2.0))
    shaping.ground_track_clip = float(cfg.get("success_ground_track_error_clip", 0.0))
    return shaping


@dataclass(frozen=True)
class WaypointModeRewardConfig:
    progress_weight: float = 0.0
    progress_negative_scale: float = 1.0
    distance_weight: float = 0.0
    distance_clip_m: float = 0.0
    distance_scale_by_route: bool = False
    distance_route_ref_m: float = 55000.0
    distance_route_scale_min: float = 0.5
    distance_route_scale_max: float = 1.0
    cross_track_weight: float = 0.0
    cross_track_deadband_m: float = 0.0
    cross_track_norm_m: float = 1000.0
    cross_track_power: float = 1.0
    cross_track_clip: float = 0.0
    turn_relief_max: float = 0.0
    proximity_weight: float = 0.0
    proximity_ref_m: float = 1500.0
    proximity_power: float = 1.0
    reached_bonus: float = 0.0
    heading_relief_max: float = 0.0
    turn_relief_window_m: float = 3000.0
    turn_relief_min_turn_deg: float = 15.0
    turn_relief_angle_ref_deg: float = 90.0
    turn_relief_power: float = 1.0


@dataclass(frozen=True)
class ApproachRewardConfig:
    localizer_weight: float = 0.0
    localizer_deadband: float = 0.0
    localizer_norm: float = 1.0
    localizer_power: float = 2.0
    localizer_clip: float = 0.0
    localizer_improve_weight: float = 0.0
    glideslope_weight: float = 0.0
    glideslope_deadband: float = 0.0
    glideslope_norm: float = 1.0
    glideslope_power: float = 2.0
    glideslope_clip: float = 0.0
    glideslope_improve_weight: float = 0.0
    dme_progress_weight: float = 0.0
    dme_progress_localizer_band: float = 0.0
    dme_progress_glideslope_band: float = 0.0
    dme_progress_quality_power: float = 1.0
    capture_bonus: float = 0.0
    capture_localizer_band: float = 0.20
    capture_glideslope_band: float = 0.20
    sink_rate_weight: float = 0.0
    flare_agl_m: float = 20.0
    sink_rate_deadband_mps: float = 0.0
    sink_rate_norm_mps: float = 2.0
    sink_rate_power: float = 2.0
    sink_rate_clip: float = 0.0
    active: bool = False


@dataclass(frozen=True)
class SafetyRewardConfig:
    crash_penalty: float = -1000.0
    survival_reward: float = 0.01
    stall_threshold_deg: float = 15.0
    stall_penalty_weight: float = -1.0
    stall_penalty_clip: float = 0.0
    overload_g_threshold: float = 6.0
    overload_penalty_weight: float = -1.0
    overload_penalty_clip: float = 0.0
    overload_min_alt_agl_m: float = 5.0
    failfast_penalty: float = -50.0
    gear_collapse_penalty: float = -500.0
    gear_stress_penalty_weight: float = -10.0
    off_runway_penalty: float = -1.0
    off_runway_terminate_speed: float = 0.0
    off_runway_terminate_grace_s: float = 0.0
    off_runway_terminate_penalty: float = -200.0
    on_ground_alt_threshold: float = 2.5
    airborne_alt_threshold: float = 5.0
    runway_width_margin_m: float = 2.0
    runway_length_margin_m: float = 0.0
    waypoint_mission_success_bonus: float = 1000.0


@dataclass(frozen=True)
class LNavRuntimeConfig:
    cdi_full_scale_m: float = 1500.0
    lookahead_m: float = 1500.0
    max_intercept_deg: float = 25.0
    capture_max_intercept_deg: float = 45.0
    capture_xtrack_m: float = 0.0
    capture_course_error_deg: float = 45.0
    direct_to_final_fix: bool = True
    flyover_capture_window_m: float | None = None
    bank_limit_deg: float = 30.0
    sequence_gate_scale: float = 0.35
    sequence_gate_min_m: float | None = None
    sequence_gate_max_m: float | None = None


@dataclass(frozen=True)
class CompiledScenarioRuntimeMetadata:
    mission_command_template: dict[str, Any]
    rewards_config: dict[str, Any]
    meta_config: dict[str, Any]
    normalized_route_waypoints: tuple[dict[str, Any], ...]
    normalized_waypoint_templates: tuple[tuple[dict[str, Any], ...], ...]
    waypoint_template_route_ref_ids: tuple[int, ...]
    compiled_conditional_objectives: tuple[Any, ...]
    objective_shaping_cfg: Any
    ils_beacon_templates: tuple[dict[str, Any], ...]
    waypoint_mode_configs: dict[str, WaypointModeRewardConfig]
    approach_reward_config: ApproachRewardConfig
    safety_reward_config: SafetyRewardConfig
    lnav_config: LNavRuntimeConfig
    layout_template: CompiledWorldLayoutTemplate


def _cfg_value_for_waypoint_mode(cfg: dict[str, Any], key: str, mode_value: Any, default: Any = None) -> Any:
    mode = _normalize_waypoint_mode(mode_value)
    mode_key = f"{key}_{mode}"
    if mode_key in cfg:
        return cfg.get(mode_key)
    if key in cfg:
        return cfg.get(key)
    return default


def _build_waypoint_mode_reward_config(cfg: dict[str, Any], *, mode: str) -> WaypointModeRewardConfig:
    mode = _normalize_waypoint_mode(mode)
    default_proximity_ref_m = 1500.0
    return WaypointModeRewardConfig(
        progress_weight=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_progress_weight", mode, 0.0)),
        progress_negative_scale=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_progress_negative_scale", mode, 1.0)),
        distance_weight=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_distance_weight", mode, 0.0)),
        distance_clip_m=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_distance_clip_m", mode, 0.0)),
        distance_scale_by_route=bool(_cfg_value_for_waypoint_mode(cfg, "waypoint_distance_scale_by_route", mode, False)),
        distance_route_ref_m=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_distance_route_ref_m", mode, 55000.0)),
        distance_route_scale_min=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_distance_route_scale_min", mode, 0.5)),
        distance_route_scale_max=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_distance_route_scale_max", mode, 1.0)),
        cross_track_weight=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_cross_track_weight", mode, 0.0)),
        cross_track_deadband_m=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_cross_track_deadband_m", mode, 0.0)),
        cross_track_norm_m=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_cross_track_norm_m", mode, 1000.0)),
        cross_track_power=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_cross_track_power", mode, 1.0)),
        cross_track_clip=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_cross_track_clip", mode, 0.0)),
        turn_relief_max=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_turn_relief_max", mode, 0.0)),
        proximity_weight=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_proximity_weight", mode, 0.0)),
        proximity_ref_m=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_proximity_ref_m", mode, default_proximity_ref_m)),
        proximity_power=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_proximity_power", mode, 1.0)),
        reached_bonus=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_reached_bonus", mode, 0.0)),
        heading_relief_max=float(
            _cfg_value_for_waypoint_mode(
                cfg,
                "waypoint_turn_heading_relief_max",
                mode,
                _cfg_value_for_waypoint_mode(cfg, "waypoint_turn_relief_max", mode, 0.0),
            )
        ),
        turn_relief_window_m=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_turn_relief_window_m", mode, 3000.0)),
        turn_relief_min_turn_deg=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_turn_relief_min_turn_deg", mode, 15.0)),
        turn_relief_angle_ref_deg=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_turn_relief_angle_ref_deg", mode, 90.0)),
        turn_relief_power=float(_cfg_value_for_waypoint_mode(cfg, "waypoint_turn_relief_power", mode, 1.0)),
    )


def _build_approach_reward_config(cfg: dict[str, Any]) -> ApproachRewardConfig:
    out = ApproachRewardConfig(
        localizer_weight=float(cfg.get("approach_localizer_weight", 0.0)),
        localizer_deadband=float(cfg.get("approach_localizer_deadband", 0.0)),
        localizer_norm=float(cfg.get("approach_localizer_norm", 1.0)),
        localizer_power=float(cfg.get("approach_localizer_power", 2.0)),
        localizer_clip=float(cfg.get("approach_localizer_clip", 0.0)),
        localizer_improve_weight=float(cfg.get("approach_localizer_improve_weight", 0.0)),
        glideslope_weight=float(cfg.get("approach_glideslope_weight", 0.0)),
        glideslope_deadband=float(cfg.get("approach_glideslope_deadband", 0.0)),
        glideslope_norm=float(cfg.get("approach_glideslope_norm", 1.0)),
        glideslope_power=float(cfg.get("approach_glideslope_power", 2.0)),
        glideslope_clip=float(cfg.get("approach_glideslope_clip", 0.0)),
        glideslope_improve_weight=float(cfg.get("approach_glideslope_improve_weight", 0.0)),
        dme_progress_weight=float(cfg.get("approach_dme_progress_weight", 0.0)),
        dme_progress_localizer_band=float(cfg.get("approach_dme_progress_localizer_band", 0.0)),
        dme_progress_glideslope_band=float(cfg.get("approach_dme_progress_glideslope_band", 0.0)),
        dme_progress_quality_power=float(cfg.get("approach_dme_progress_quality_power", 1.0)),
        capture_bonus=float(cfg.get("approach_capture_bonus", 0.0)),
        capture_localizer_band=float(cfg.get("approach_capture_localizer_band", 0.20)),
        capture_glideslope_band=float(cfg.get("approach_capture_glideslope_band", 0.20)),
        sink_rate_weight=float(cfg.get("landing_sink_rate_penalty_weight", 0.0)),
        flare_agl_m=float(cfg.get("landing_flare_agl_m", 20.0)),
        sink_rate_deadband_mps=float(cfg.get("landing_sink_rate_deadband_mps", 0.0)),
        sink_rate_norm_mps=float(cfg.get("landing_sink_rate_norm_mps", 2.0)),
        sink_rate_power=float(cfg.get("landing_sink_rate_power", 2.0)),
        sink_rate_clip=float(cfg.get("landing_sink_rate_clip", 0.0)),
    )
    active = bool(
        out.localizer_weight != 0.0
        or out.glideslope_weight != 0.0
        or out.dme_progress_weight != 0.0
        or out.capture_bonus != 0.0
        or out.sink_rate_weight != 0.0
    )
    return ApproachRewardConfig(**{**out.__dict__, "active": active})


def _build_safety_reward_config(cfg: dict[str, Any]) -> SafetyRewardConfig:
    return SafetyRewardConfig(
        crash_penalty=float(cfg.get("crash_penalty", -1000.0)),
        survival_reward=float(cfg.get("survival", 0.01)),
        stall_threshold_deg=float(cfg.get("stall_aoa_threshold", 15.0)),
        stall_penalty_weight=float(cfg.get("stall_penalty", -1.0)),
        stall_penalty_clip=float(cfg.get("stall_penalty_clip", 0.0)),
        overload_g_threshold=float(cfg.get("overload_g_threshold", 6.0)),
        overload_penalty_weight=float(cfg.get("overload_penalty", -1.0)),
        overload_penalty_clip=float(cfg.get("overload_penalty_clip", 0.0)),
        overload_min_alt_agl_m=float(cfg.get("overload_min_alt_agl_m", 5.0)),
        failfast_penalty=float(cfg.get("failfast_penalty", -50.0)),
        gear_collapse_penalty=float(cfg.get("gear_collapse_penalty", -500.0)),
        gear_stress_penalty_weight=float(cfg.get("gear_stress_penalty", -10.0)),
        off_runway_penalty=float(cfg.get("off_runway_penalty", -1.0)),
        off_runway_terminate_speed=float(cfg.get("off_runway_terminate_speed", 0.0)),
        off_runway_terminate_grace_s=float(cfg.get("off_runway_terminate_grace_s", 0.0)),
        off_runway_terminate_penalty=float(cfg.get("off_runway_terminate_penalty", -200.0)),
        on_ground_alt_threshold=float(cfg.get("on_ground_alt_threshold", 2.5)),
        airborne_alt_threshold=float(cfg.get("airborne_alt_threshold", cfg.get("liftoff_alt_threshold", 5.0))),
        runway_width_margin_m=float(cfg.get("runway_width_margin_m", 2.0)),
        runway_length_margin_m=float(cfg.get("runway_length_margin_m", 0.0)),
        waypoint_mission_success_bonus=float(cfg.get("waypoint_mission_success_bonus", 1000.0)),
    )


def _build_lnav_runtime_config(mission_cmd: dict[str, Any]) -> LNavRuntimeConfig:
    cdi_full_scale_m = float(
        mission_cmd.get(
            "nav_course_dev_full_scale_m",
            mission_cmd.get(
                "course_dev_full_scale_m",
                max(1000.0, float(mission_cmd.get("waypoint_radius_m", 1000.0))),
            ),
        )
    )
    capture_xtrack = mission_cmd.get("lnav_capture_xtrack_m", None)
    flyover_capture_window = mission_cmd.get("lnav_flyover_capture_window_m", None)
    seq_gate_min = mission_cmd.get("lnav_sequence_gate_min_m", None)
    seq_gate_max = mission_cmd.get("lnav_sequence_gate_max_m", None)
    max_intercept_deg = float(mission_cmd.get("lnav_max_intercept_deg", 25.0))
    return LNavRuntimeConfig(
        cdi_full_scale_m=float(cdi_full_scale_m),
        lookahead_m=float(mission_cmd.get("lnav_lookahead_m", 1500.0)),
        max_intercept_deg=float(max_intercept_deg),
        capture_max_intercept_deg=float(mission_cmd.get("lnav_capture_max_intercept_deg", max(max_intercept_deg, 45.0))),
        capture_xtrack_m=0.0 if capture_xtrack is None else float(capture_xtrack),
        capture_course_error_deg=float(mission_cmd.get("lnav_capture_course_error_deg", 45.0)),
        direct_to_final_fix=bool(mission_cmd.get("lnav_direct_to_final_fix", True)),
        flyover_capture_window_m=None if flyover_capture_window is None else float(flyover_capture_window),
        bank_limit_deg=float(mission_cmd.get("lnav_bank_limit_deg", 30.0)),
        sequence_gate_scale=float(mission_cmd.get("lnav_sequence_gate_scale", 0.35)),
        sequence_gate_min_m=None if seq_gate_min is None else float(seq_gate_min),
        sequence_gate_max_m=None if seq_gate_max is None else float(seq_gate_max),
    )


__all__ = [
    "WaypointModeRewardConfig",
    "ApproachRewardConfig",
    "SafetyRewardConfig",
    "LNavRuntimeConfig",
    "CompiledScenarioRuntimeMetadata",
    "_compile_conditional_objectives",
    "_build_objective_shaping_config",
    "_cfg_value_for_waypoint_mode",
    "_build_waypoint_mode_reward_config",
    "_build_approach_reward_config",
    "_build_safety_reward_config",
    "_build_lnav_runtime_config",
]
