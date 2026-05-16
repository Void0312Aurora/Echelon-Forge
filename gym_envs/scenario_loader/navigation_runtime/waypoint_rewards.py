import math

import ef_py

from python.scenario_compiler import WaypointModeRewardConfig

from .guidance import (
    cfg_value_for_waypoint_mode,
    compute_waypoint_guidance_state,
    normalize_waypoint_mode,
    route_reference_xy,
)


def build_waypoint_step_state(loader, cfg: dict, *, truth=None, inst=None, turn_relief_activation: float = 0.0):
    try:
        cmd_code = int(loader.mission_cmd.get("command_code", 0))
    except Exception:
        cmd_code = 0
    if cmd_code != 3 or not loader.waypoints:
        return None

    idx = int(getattr(loader, "waypoint_idx", 0))
    if idx < 0:
        idx = 0
    count = int(len(loader.waypoints))
    if idx >= count:
        return None

    gstate = compute_waypoint_guidance_state(loader, truth=truth, inst=inst)
    wp = loader.waypoints[idx]
    dist_m = float(
        math.hypot(
            float(wp.get("x", 0.0)) - float(getattr(truth, "x", 0.0)),
            float(wp.get("y", 0.0)) - float(getattr(truth, "y", 0.0)),
        )
    )
    mode = normalize_waypoint_mode(wp.get("waypoint_mode", loader.mission_cmd.get("waypoint_mode", "flyby")))
    leg_len = 0.0
    xtk = None
    dtg = dist_m
    rad = max(1.0, float(wp.get("radius_m", loader.mission_cmd.get("waypoint_radius_m", 500.0))))
    lead = 0.0
    seq_gate_m = float(rad)
    passed_fix = False
    if isinstance(gstate, dict) and int(gstate.get("idx", -1)) == idx:
        wp = gstate["wp"]
        mode = str(gstate.get("waypoint_mode", mode))
        dist_m = float(gstate.get("dist_m", dist_m))
        leg_len = float(gstate.get("leg_len_m", 0.0))
        if str(mode) == "flyby" and bool(gstate.get("final_leg", False)):
            xtk = float(gstate.get("xtk_m", gstate.get("reward_xtk_m", 0.0)))
        else:
            xtk = float(gstate.get("reward_xtk_m", 0.0))
        dtg = float(gstate.get("reward_dtg_m", dist_m))
        rad = max(1.0, float(gstate.get("waypoint_radius_m", rad)))
        lead = float(gstate.get("lead_turn_m", 0.0))
        seq_gate_m = float(gstate.get("sequence_gate_m", rad))
        passed_fix = bool(gstate.get("passed_fix", False))
    else:
        ref_x, ref_y = route_reference_xy(
            loader,
            float(getattr(truth, "x", 0.0)),
            float(getattr(truth, "y", 0.0)),
            int(idx),
        )
        dist_m = float(
            math.hypot(
                float(wp.get("x", 0.0)) - ref_x,
                float(wp.get("y", 0.0)) - ref_y,
            )
        )

    waypoint_inputs = build_waypoint_reward_inputs(
        loader,
        cfg,
        idx=int(idx),
        count=int(count),
        mode=str(mode),
        dist_m=float(dist_m),
        leg_len_m=float(leg_len),
        xtk_m=xtk,
        dtg_m=dtg,
        waypoint_radius_m=float(rad),
        lead_turn_m=float(lead),
        sequence_gate_m=float(seq_gate_m),
        passed_fix=bool(passed_fix),
        turn_relief_activation=float(turn_relief_activation),
    )
    return {
        "idx": int(idx),
        "count": int(count),
        "dist_m": float(dist_m),
        "inputs": waypoint_inputs,
        "episode_success": bool(
            (idx + 1) >= count
            and not (isinstance(loader.post_waypoint_transition, dict) and loader.post_waypoint_transition)
        ),
    }


def build_waypoint_reward_inputs(
    loader,
    cfg: dict,
    *,
    idx: int,
    count: int,
    mode: str,
    dist_m: float,
    leg_len_m: float,
    xtk_m,
    dtg_m,
    waypoint_radius_m: float,
    lead_turn_m: float,
    sequence_gate_m: float,
    passed_fix: bool,
    turn_relief_activation: float,
):
    inputs = ef_py.WaypointRewardInputs()
    mode_cfg = loader._waypoint_mode_reward_cfgs.get(str(mode), loader._waypoint_mode_reward_cfgs.get("flyby", None))
    if mode_cfg is None:
        mode_cfg = WaypointModeRewardConfig(
            progress_weight=float(cfg_value_for_waypoint_mode(loader, cfg, "waypoint_progress_weight", mode, 0.0)),
            progress_negative_scale=float(
                cfg_value_for_waypoint_mode(loader, cfg, "waypoint_progress_negative_scale", mode, 1.0)
            ),
            distance_weight=float(cfg_value_for_waypoint_mode(loader, cfg, "waypoint_distance_weight", mode, 0.0)),
            distance_clip_m=float(cfg_value_for_waypoint_mode(loader, cfg, "waypoint_distance_clip_m", mode, 0.0)),
            distance_scale_by_route=bool(
                cfg_value_for_waypoint_mode(loader, cfg, "waypoint_distance_scale_by_route", mode, False)
            ),
            distance_route_ref_m=float(
                cfg_value_for_waypoint_mode(loader, cfg, "waypoint_distance_route_ref_m", mode, 55000.0)
            ),
            distance_route_scale_min=float(
                cfg_value_for_waypoint_mode(loader, cfg, "waypoint_distance_route_scale_min", mode, 0.5)
            ),
            distance_route_scale_max=float(
                cfg_value_for_waypoint_mode(loader, cfg, "waypoint_distance_route_scale_max", mode, 1.0)
            ),
            cross_track_weight=float(cfg_value_for_waypoint_mode(loader, cfg, "waypoint_cross_track_weight", mode, 0.0)),
            cross_track_deadband_m=float(
                cfg_value_for_waypoint_mode(loader, cfg, "waypoint_cross_track_deadband_m", mode, 0.0)
            ),
            cross_track_norm_m=float(
                cfg_value_for_waypoint_mode(loader, cfg, "waypoint_cross_track_norm_m", mode, 1000.0)
            ),
            cross_track_power=float(cfg_value_for_waypoint_mode(loader, cfg, "waypoint_cross_track_power", mode, 1.0)),
            cross_track_clip=float(cfg_value_for_waypoint_mode(loader, cfg, "waypoint_cross_track_clip", mode, 0.0)),
            turn_relief_max=float(cfg_value_for_waypoint_mode(loader, cfg, "waypoint_turn_relief_max", mode, 0.0)),
            proximity_weight=float(cfg_value_for_waypoint_mode(loader, cfg, "waypoint_proximity_weight", mode, 0.0)),
            proximity_ref_m=float(
                cfg_value_for_waypoint_mode(
                    loader,
                    cfg,
                    "waypoint_proximity_ref_m",
                    mode,
                    max(2.5 * float(waypoint_radius_m), float(waypoint_radius_m) + 1500.0),
                )
            ),
            proximity_power=float(cfg_value_for_waypoint_mode(loader, cfg, "waypoint_proximity_power", mode, 1.0)),
            reached_bonus=float(cfg_value_for_waypoint_mode(loader, cfg, "waypoint_reached_bonus", mode, 0.0)),
        )
    inputs.valid = True
    inputs.waypoint_index = int(idx)
    inputs.waypoint_count = int(count)
    inputs.is_flyover = bool(str(mode) == "flyover")
    inputs.has_guidance = bool(leg_len_m > 1.0e-6 and xtk_m is not None and dtg_m is not None)
    inputs.passed_fix = bool(passed_fix)
    inputs.dist_m = float(dist_m)
    inputs.xtk_m = 0.0 if xtk_m is None else float(xtk_m)
    inputs.dtg_m = float(dist_m if dtg_m is None else dtg_m)
    inputs.waypoint_radius_m = float(waypoint_radius_m)
    inputs.leg_len_m = float(leg_len_m)
    inputs.lead_turn_m = float(lead_turn_m)
    inputs.sequence_gate_m = float(sequence_gate_m)
    inputs.has_prev_dist = loader._waypoint_prev_dist_m is not None
    inputs.prev_dist_m = 0.0 if loader._waypoint_prev_dist_m is None else float(loader._waypoint_prev_dist_m)
    inputs.route_length_m = float(getattr(loader, "waypoint_total_route_length_m", 0.0))
    inputs.turn_relief_activation = float(turn_relief_activation)

    inputs.progress_weight = float(mode_cfg.progress_weight)
    inputs.progress_negative_scale = float(mode_cfg.progress_negative_scale)
    inputs.distance_weight = float(mode_cfg.distance_weight)
    inputs.distance_clip_m = float(mode_cfg.distance_clip_m)
    inputs.distance_scale_by_route = bool(mode_cfg.distance_scale_by_route)
    inputs.distance_route_ref_m = float(mode_cfg.distance_route_ref_m)
    inputs.distance_route_scale_min = float(mode_cfg.distance_route_scale_min)
    inputs.distance_route_scale_max = float(mode_cfg.distance_route_scale_max)
    inputs.cross_track_weight = float(mode_cfg.cross_track_weight)
    inputs.cross_track_deadband_m = float(mode_cfg.cross_track_deadband_m)
    inputs.cross_track_norm_m = float(mode_cfg.cross_track_norm_m)
    inputs.cross_track_power = float(mode_cfg.cross_track_power)
    inputs.cross_track_clip = float(mode_cfg.cross_track_clip)
    inputs.turn_relief_max = float(mode_cfg.turn_relief_max)
    inputs.proximity_weight = float(mode_cfg.proximity_weight)
    inputs.proximity_ref_m = float(
        max(float(mode_cfg.proximity_ref_m), max(2.5 * float(waypoint_radius_m), float(waypoint_radius_m) + 1500.0))
    )
    inputs.proximity_power = float(mode_cfg.proximity_power)
    inputs.reached_bonus = float(mode_cfg.reached_bonus)
    return inputs
