import ef_py

from ..common import OBJECTIVE_DYNAMIC_TARGET_MAP, OBJECTIVE_OP_MAP, OBJECTIVE_PROPERTY_MAP


def _combat_target_snapshot(loader, truth):
    target_id = int(getattr(loader, "primary_target_id", 0) or 0)
    if target_id <= 0:
        return {
            "target_id": 0,
            "target_active": False,
            "target_health": 0.0,
            "target_range_m": None,
            "self_active": True,
            "self_health": float(getattr(truth, "health", 100.0)),
            "missiles_remaining": float(getattr(truth, "missiles_remaining", 0.0)),
        }

    sim = getattr(loader, "sim", None)
    target_active = False
    target_health = 0.0
    target_range_m = None
    if sim is not None and hasattr(sim, "is_unit_active"):
        try:
            target_active = bool(sim.is_unit_active(int(target_id)))
        except Exception:
            target_active = False
    if sim is not None and hasattr(sim, "get_unit_health"):
        try:
            health = sim.get_unit_health(int(target_id))
            if isinstance(health, list) and health:
                target_health = float(health[0])
        except Exception:
            target_health = 0.0
    for track in getattr(truth, "contacts", []) or []:
        try:
            if int(getattr(track, "id", 0)) != int(target_id):
                continue
            target_range_m = float(getattr(track, "range", 0.0))
            break
        except Exception:
            continue

    return {
        "target_id": int(target_id),
        "target_active": bool(target_active),
        "target_health": float(target_health),
        "target_range_m": target_range_m,
        "self_active": True,
        "self_health": float(getattr(truth, "health", 100.0)),
        "missiles_remaining": float(getattr(truth, "missiles_remaining", 0.0)),
    }


def build_approach_reward_inputs(
    loader,
    cfg: dict,
    *,
    ils_valid: float,
    ils_loc: float,
    ils_gs: float,
    ils_dme: float,
    curr_alt_agl: float,
    sink_rate_mps: float,
):
    inputs = ef_py.ApproachRewardInputs()
    _ = cfg
    approach_cfg = loader._approach_reward_cfg
    inputs.valid = True
    inputs.ils_valid = bool(ils_valid > 0.5)
    inputs.ils_loc_dev = float(ils_loc)
    inputs.ils_gs_dev = float(ils_gs)
    inputs.ils_dme_m = float(ils_dme)
    inputs.has_prev_loc = loader._approach_prev_loc_abs is not None
    inputs.prev_loc_abs = 0.0 if loader._approach_prev_loc_abs is None else float(loader._approach_prev_loc_abs)
    inputs.has_prev_gs = loader._approach_prev_gs_abs is not None
    inputs.prev_gs_abs = 0.0 if loader._approach_prev_gs_abs is None else float(loader._approach_prev_gs_abs)
    inputs.has_prev_dme = loader._approach_prev_dme_m is not None
    inputs.prev_dme_m = 0.0 if loader._approach_prev_dme_m is None else float(loader._approach_prev_dme_m)

    inputs.localizer_weight = float(approach_cfg.localizer_weight)
    inputs.localizer_deadband = float(approach_cfg.localizer_deadband)
    inputs.localizer_norm = float(approach_cfg.localizer_norm)
    inputs.localizer_power = float(approach_cfg.localizer_power)
    inputs.localizer_clip = float(approach_cfg.localizer_clip)
    inputs.localizer_improve_weight = float(approach_cfg.localizer_improve_weight)

    inputs.glideslope_weight = float(approach_cfg.glideslope_weight)
    inputs.glideslope_deadband = float(approach_cfg.glideslope_deadband)
    inputs.glideslope_norm = float(approach_cfg.glideslope_norm)
    inputs.glideslope_power = float(approach_cfg.glideslope_power)
    inputs.glideslope_clip = float(approach_cfg.glideslope_clip)
    inputs.glideslope_improve_weight = float(approach_cfg.glideslope_improve_weight)

    inputs.dme_progress_weight = float(approach_cfg.dme_progress_weight)
    inputs.dme_progress_localizer_band = float(approach_cfg.dme_progress_localizer_band)
    inputs.dme_progress_glideslope_band = float(approach_cfg.dme_progress_glideslope_band)
    inputs.dme_progress_quality_power = float(approach_cfg.dme_progress_quality_power)

    inputs.capture_bonus = float(approach_cfg.capture_bonus)
    inputs.capture_localizer_band = float(approach_cfg.capture_localizer_band)
    inputs.capture_glideslope_band = float(approach_cfg.capture_glideslope_band)

    inputs.sink_rate_weight = float(approach_cfg.sink_rate_weight)
    inputs.flare_agl_m = float(approach_cfg.flare_agl_m)
    inputs.curr_alt_agl_m = float(curr_alt_agl)
    inputs.sink_rate_mps = float(sink_rate_mps)
    inputs.sink_rate_deadband_mps = float(approach_cfg.sink_rate_deadband_mps)
    inputs.sink_rate_norm_mps = float(approach_cfg.sink_rate_norm_mps)
    inputs.sink_rate_power = float(approach_cfg.sink_rate_power)
    inputs.sink_rate_clip = float(approach_cfg.sink_rate_clip)
    return inputs


def compile_conditional_objectives(loader):
    compiled = []
    for obj in loader.scenario_data.get("objectives", []):
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
            compiled_cond.property_code = OBJECTIVE_PROPERTY_MAP.get(
                prop_key,
                ef_py.ConditionalObjectiveProperty.Unknown,
            )
            compiled_cond.op_code = OBJECTIVE_OP_MAP.get(
                str(cond.get("op", ">=")).strip(),
                ef_py.ConditionalObjectiveOp.GreaterEqual,
            )
            compiled_cond.target_kind = ef_py.ConditionalObjectiveTargetKind.Literal
            compiled_cond.target_scale = 1.0
            tgt = cond.get("value", 0.0)
            if isinstance(tgt, str):
                target_info = OBJECTIVE_DYNAMIC_TARGET_MAP.get(tgt.strip().upper())
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
    return compiled


def build_objective_shaping_config(cfg: dict):
    shaping = ef_py.ObjectiveShapingConfig()
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


def build_conditional_objective_inputs(
    loader,
    truth,
    inst,
    *,
    curr_ias: float,
    curr_ground_speed: float,
    curr_gear: float,
    curr_alt_agl: float,
    heading_error_deg: float,
    ground_track_error_deg: float,
    runway_cross_m,
    runway_from_threshold_m,
    on_runway_geom,
    on_runway_task: bool,
    on_ground: bool,
):
    inputs = ef_py.ConditionalObjectiveInputs()
    inputs.altitude_m = float(getattr(truth, "z", 0.0))
    inputs.altitude_agl_m = float(curr_alt_agl)
    inputs.speed_mps = float(curr_ias)
    inputs.ground_speed_mps = float(curr_ground_speed)
    inputs.gear_fraction = float(curr_gear)
    inputs.heading_error_deg = float(heading_error_deg)
    inputs.command_code = float(int(loader.mission_cmd.get("command_code", 0)))
    inputs.ground_track_error_deg = float(ground_track_error_deg)
    inputs.has_runway_cross_m = runway_cross_m is not None
    inputs.runway_cross_m = 0.0 if runway_cross_m is None else float(runway_cross_m)
    inputs.has_runway_from_threshold_m = runway_from_threshold_m is not None
    inputs.runway_from_threshold_m = 0.0 if runway_from_threshold_m is None else float(runway_from_threshold_m)
    inputs.on_runway_geom = bool(on_runway_geom)
    inputs.on_runway_task = bool(on_runway_task)
    inputs.on_ground = bool(on_ground)
    inputs.sink_rate_abs_mps = abs(loader._instrument_scalar(inst, "vvi", 4, 0.0))
    inputs.ils_localizer_abs = abs(loader._instrument_scalar(inst, "ils_loc", -3, float("inf")))
    inputs.ils_glideslope_abs = abs(loader._instrument_scalar(inst, "ils_gs", -2, float("inf")))
    inputs.dme_m = loader._instrument_scalar(inst, "ils_dme", -1, float("inf"))
    inputs.heading_deg = float(getattr(truth, "heading", 0.0))
    inputs.x_m = float(getattr(truth, "x", 0.0))
    inputs.y_m = float(getattr(truth, "y", 0.0))
    route_target_altitude_m = loader._current_route_target_altitude_m(truth=truth)
    inputs.target_altitude_m = float(
        loader.mission_cmd.get("target_altitude", 0.0)
        if route_target_altitude_m is None
        else route_target_altitude_m
    )
    inputs.target_speed_mps = float(loader.mission_cmd.get("target_speed", 0.0))
    inputs.target_heading_deg = float(loader.mission_cmd.get("target_heading", 0.0))
    combat_snapshot = _combat_target_snapshot(loader, truth)
    inputs.self_active = bool(combat_snapshot["self_active"])
    inputs.target_active = bool(combat_snapshot["target_active"])
    inputs.self_health = float(combat_snapshot["self_health"])
    inputs.target_health = float(combat_snapshot["target_health"])
    inputs.missiles_remaining = float(combat_snapshot["missiles_remaining"])
    target_range_m = combat_snapshot["target_range_m"]
    inputs.has_target_range_m = target_range_m is not None
    inputs.target_range_m = 0.0 if target_range_m is None else float(target_range_m)
    return inputs
