#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT_HINT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", "..", ".."))
if _REPO_ROOT_HINT not in sys.path:
    sys.path.insert(0, _REPO_ROOT_HINT)

from python.angles import wrap_signed_deg
from python.runtime_bootstrap import ensure_repo_imports

REPO_ROOT = ensure_repo_imports()
os.chdir(REPO_ROOT)

import ef_py  # noqa: E402


# Local name preserved as a thin alias; semantics owned by python.angles.
_wrap_angle_deg = wrap_signed_deg


def _build_route_result() -> tuple[ef_py.SpatialRouteQueryResult, ef_py.MissionNavInputs]:
    geom = ef_py.CompiledScenarioGeometry()
    geom.set_route_leg_origin(0.0, 0.0)

    wp1 = ef_py.SpatialRouteWaypoint()
    wp1.x_m = 10000.0
    wp1.y_m = 0.0
    wp1.z_m = 1200.0
    wp1.altitude_m = 1200.0
    wp1.radius_m = 1000.0
    wp1.speed_mps = 210.0
    wp1.waypoint_mode = "flyover"
    geom.add_route_waypoint(wp1)

    wp2 = ef_py.SpatialRouteWaypoint()
    wp2.x_m = 20000.0
    wp2.y_m = 10000.0
    wp2.z_m = 1200.0
    wp2.altitude_m = 1200.0
    wp2.radius_m = 1000.0
    wp2.speed_mps = 210.0
    wp2.waypoint_mode = "flyby"
    geom.add_route_waypoint(wp2)

    opts = ef_py.SpatialRouteQueryOptions()
    opts.waypoint_index = 0
    opts.own_x_m = 0.0
    opts.own_y_m = 0.0
    opts.own_speed_mps = 210.0
    opts.base_lookahead_m = 1500.0
    opts.lnav_max_intercept_deg = 25.0
    opts.lnav_capture_max_intercept_deg = 45.0
    opts.lnav_capture_xtrack_m = 0.0
    opts.lnav_capture_course_error_deg = 45.0
    opts.lnav_direct_to_final_fix = True
    opts.lnav_bank_limit_deg = 30.0
    opts.lnav_sequence_gate_scale = 0.35
    route_result = geom.query_route_guidance(opts)

    inputs = ef_py.MissionNavInputs()
    inputs.own_altitude_m = 1200.0
    inputs.truth_heading_deg = 90.0
    inputs.truth_speed_mps = 210.0
    inputs.inst_heading_deg = 90.0
    inputs.inst_ground_track_deg = 90.0
    inputs.inst_ias_mps = 210.0
    inputs.waypoint_altitude_m = 1200.0
    inputs.cdi_full_scale_m = 1000.0
    return route_result, inputs


def _legacy_waypoint_nav(route_result: ef_py.SpatialRouteQueryResult, inputs: ef_py.MissionNavInputs) -> dict[str, float]:
    own_heading_deg = float(inputs.truth_heading_deg)
    ground_track_deg = own_heading_deg
    true_airspeed_mps = float(inputs.truth_speed_mps)
    if math.isfinite(float(inputs.inst_heading_deg)):
        own_heading_deg = float(inputs.inst_heading_deg)
    if math.isfinite(float(inputs.inst_ground_track_deg)):
        ground_track_deg = float(inputs.inst_ground_track_deg)
    if math.isfinite(float(inputs.inst_ias_mps)) and float(inputs.inst_ias_mps) > 1.0:
        true_airspeed_mps = float(inputs.inst_ias_mps)
    if abs(_wrap_angle_deg(ground_track_deg - own_heading_deg)) > 85.0 and true_airspeed_mps > 80.0:
        ground_track_deg = own_heading_deg

    dist_m = float(route_result.dist_m)
    direct_bearing_deg = float(route_result.direct_to_track_deg)
    desired_leg_track_deg = float(route_result.reward_desired_track_deg)
    xtk_m = float(route_result.reward_xtk_m)
    dtg_m = float(route_result.reward_dtg_m)
    return {
        "selected_steerpoint": float(route_result.idx + 1),
        "steerpoint_mode_code": 1.0 if str(route_result.waypoint_mode) == "flyover" else 0.0,
        "dist_m": dist_m,
        "bearing_rel_deg": float(_wrap_angle_deg(direct_bearing_deg - own_heading_deg)),
        "altitude_delta_m": float(inputs.waypoint_altitude_m - inputs.own_altitude_m),
        "cdi_norm": float(max(-1.0, min(1.0, xtk_m / max(1.0, float(inputs.cdi_full_scale_m))))),
        "track_angle_error_deg": float(_wrap_angle_deg(desired_leg_track_deg - ground_track_deg)),
        "dtg_m": dtg_m,
        "next_turn_deg": float(route_result.next_turn_deg),
        "distance_to_turn_m": float(route_result.distance_to_turn_m),
    }


def _time_call(fn, *, iters: int) -> float:
    start = time.perf_counter()
    for _ in range(max(1, int(iters))):
        fn()
    elapsed = time.perf_counter() - start
    return 1000.0 * elapsed / max(1, int(iters))


def _legacy_waypoint_reward(inputs: ef_py.WaypointRewardInputs) -> dict[str, float]:
    out = {
        "waypoint_progress": 0.0,
        "waypoint_distance": 0.0,
        "waypoint_cross_track": 0.0,
        "waypoint_proximity": 0.0,
    }
    if float(inputs.progress_weight) != 0.0 and bool(inputs.has_prev_dist):
        delta = float(inputs.prev_dist_m) - float(inputs.dist_m)
        if delta < 0.0:
            delta *= max(0.0, float(inputs.progress_negative_scale))
        out["waypoint_progress"] = delta * float(inputs.progress_weight)

    if float(inputs.distance_weight) != 0.0:
        dist_term_m = float(inputs.dist_m)
        clip_m = float(inputs.distance_clip_m)
        if clip_m > 0.0:
            dist_term_m = min(dist_term_m, clip_m)
        scale = 1.0
        if bool(inputs.distance_scale_by_route):
            route_len_m = float(inputs.route_length_m)
            route_ref_m = float(inputs.distance_route_ref_m)
            if route_len_m > 1.0e-6 and route_ref_m > 1.0e-6:
                scale = route_ref_m / route_len_m
                lo = float(inputs.distance_route_scale_min)
                hi = float(inputs.distance_route_scale_max)
                if hi < lo:
                    lo, hi = hi, lo
                scale = max(lo, min(hi, scale))
        out["waypoint_distance"] = dist_term_m * float(inputs.distance_weight) * scale

    if float(inputs.cross_track_weight) != 0.0 and bool(inputs.has_guidance):
        dead_m = max(0.0, float(inputs.cross_track_deadband_m))
        norm_m = float(inputs.cross_track_norm_m)
        if norm_m <= 1.0e-6:
            norm_m = 1000.0
        p = min(8.0, max(1.0, float(inputs.cross_track_power)))
        err = abs(float(inputs.xtk_m)) - dead_m
        if err > 0.0:
            x = err / norm_m
            clip_x = float(inputs.cross_track_clip)
            if clip_x > 0.0:
                x = min(x, clip_x)
            turn_relief_max = max(0.0, min(0.95, float(inputs.turn_relief_max)))
            scale = 1.0 - turn_relief_max * float(inputs.turn_relief_activation)
            out["waypoint_cross_track"] = float(inputs.cross_track_weight) * (x ** p) * scale

    if float(inputs.proximity_weight) != 0.0:
        ref_m = float(inputs.proximity_ref_m)
        if ref_m > 1.0e-6:
            p = min(8.0, max(1.0, float(inputs.proximity_power)))
            prox_x = 1.0 - min(float(inputs.dist_m), ref_m) / ref_m
            if prox_x > 0.0:
                out["waypoint_proximity"] = float(inputs.proximity_weight) * (prox_x ** p)
    return out


def _legacy_approach_reward(inputs: ef_py.ApproachRewardInputs) -> dict[str, float]:
    out = {
        "approach_localizer": 0.0,
        "approach_localizer_improve": 0.0,
        "approach_glideslope": 0.0,
        "approach_glideslope_improve": 0.0,
        "approach_dme_progress": 0.0,
        "approach_capture_bonus": 0.0,
        "landing_sink_rate_penalty": 0.0,
    }
    if bool(inputs.ils_valid):
        curr_loc_abs = abs(float(inputs.ils_loc_dev))
        curr_gs_abs = abs(float(inputs.ils_gs_dev))
        if float(inputs.localizer_weight) != 0.0:
            dead = max(0.0, float(inputs.localizer_deadband))
            norm = float(inputs.localizer_norm)
            if norm <= 1.0e-6:
                norm = 1.0
            p = min(8.0, max(1.0, float(inputs.localizer_power)))
            err = curr_loc_abs - dead
            if err > 0.0:
                x = err / norm
                clip = float(inputs.localizer_clip)
                if clip > 0.0:
                    x = min(x, clip)
                out["approach_localizer"] = float(inputs.localizer_weight) * (x ** p)
        if float(inputs.localizer_improve_weight) != 0.0 and bool(inputs.has_prev_loc):
            out["approach_localizer_improve"] = (float(inputs.prev_loc_abs) - curr_loc_abs) * float(inputs.localizer_improve_weight)

        if float(inputs.glideslope_weight) != 0.0:
            dead = max(0.0, float(inputs.glideslope_deadband))
            norm = float(inputs.glideslope_norm)
            if norm <= 1.0e-6:
                norm = 1.0
            p = min(8.0, max(1.0, float(inputs.glideslope_power)))
            err = curr_gs_abs - dead
            if err > 0.0:
                x = err / norm
                clip = float(inputs.glideslope_clip)
                if clip > 0.0:
                    x = min(x, clip)
                out["approach_glideslope"] = float(inputs.glideslope_weight) * (x ** p)
        if float(inputs.glideslope_improve_weight) != 0.0 and bool(inputs.has_prev_gs):
            out["approach_glideslope_improve"] = (float(inputs.prev_gs_abs) - curr_gs_abs) * float(inputs.glideslope_improve_weight)

        if float(inputs.dme_progress_weight) != 0.0 and bool(inputs.has_prev_dme) and math.isfinite(float(inputs.ils_dme_m)):
            quality = 1.0
            loc_band = float(inputs.dme_progress_localizer_band)
            if loc_band > 1.0e-6:
                quality *= max(0.0, 1.0 - curr_loc_abs / loc_band)
            gs_band = float(inputs.dme_progress_glideslope_band)
            if gs_band > 1.0e-6:
                quality *= max(0.0, 1.0 - curr_gs_abs / gs_band)
            quality_power = min(4.0, max(0.5, float(inputs.dme_progress_quality_power)))
            quality = max(0.0, min(1.0, quality)) ** quality_power
            out["approach_dme_progress"] = (float(inputs.prev_dme_m) - float(inputs.ils_dme_m)) * float(inputs.dme_progress_weight) * quality

        if float(inputs.capture_bonus) != 0.0:
            if curr_loc_abs <= max(0.0, float(inputs.capture_localizer_band)) and curr_gs_abs <= max(0.0, float(inputs.capture_glideslope_band)):
                out["approach_capture_bonus"] = float(inputs.capture_bonus)

    if float(inputs.sink_rate_weight) != 0.0 and float(inputs.curr_alt_agl_m) <= max(0.0, float(inputs.flare_agl_m)):
        err = abs(float(inputs.sink_rate_mps)) - max(0.0, float(inputs.sink_rate_deadband_mps))
        if err > 0.0:
            norm = float(inputs.sink_rate_norm_mps)
            if norm <= 1.0e-6:
                norm = 2.0
            p = min(8.0, max(1.0, float(inputs.sink_rate_power)))
            x = err / norm
            clip = float(inputs.sink_rate_clip)
            if clip > 0.0:
                x = min(x, clip)
            out["landing_sink_rate_penalty"] = float(inputs.sink_rate_weight) * (x ** p)
    return out


def _legacy_conditional_objective(
    spec: ef_py.ConditionalObjectiveSpec,
    inputs: ef_py.ConditionalObjectiveInputs,
    shaping: ef_py.ObjectiveShapingConfig,
) -> dict[str, float | bool]:
    status = [0.0, 0.0, 0.0]
    matched = True
    unknown_property = False
    for i, cond in enumerate(spec.conditions):
        target_value = float(cond.target_value)
        if cond.target_kind == ef_py.ConditionalObjectiveTargetKind.CommandAltitude:
            target_value = float(inputs.target_altitude_m) * float(cond.target_scale)
        elif cond.target_kind == ef_py.ConditionalObjectiveTargetKind.CommandSpeed:
            target_value = float(inputs.target_speed_mps) * float(cond.target_scale)
        elif cond.target_kind == ef_py.ConditionalObjectiveTargetKind.CommandHeading:
            target_value = float(inputs.target_heading_deg)

        prop = cond.property_code
        if prop == ef_py.ConditionalObjectiveProperty.Altitude:
            value = float(inputs.altitude_m)
        elif prop == ef_py.ConditionalObjectiveProperty.AltitudeAGL:
            value = float(inputs.altitude_agl_m)
        elif prop == ef_py.ConditionalObjectiveProperty.Speed:
            value = float(inputs.speed_mps)
        elif prop == ef_py.ConditionalObjectiveProperty.GroundSpeed:
            value = float(inputs.ground_speed_mps)
        elif prop == ef_py.ConditionalObjectiveProperty.Gear:
            value = float(inputs.gear_fraction)
        elif prop == ef_py.ConditionalObjectiveProperty.HeadingErrorDeg:
            value = float(inputs.heading_error_deg)
        elif prop == ef_py.ConditionalObjectiveProperty.CommandCode:
            value = float(inputs.command_code)
        elif prop == ef_py.ConditionalObjectiveProperty.GroundTrackErrorDeg:
            value = float(inputs.ground_track_error_deg)
        elif prop == ef_py.ConditionalObjectiveProperty.RunwayCrossAbsM:
            value = abs(float(inputs.runway_cross_m)) if bool(inputs.has_runway_cross_m) else float("inf")
        elif prop == ef_py.ConditionalObjectiveProperty.RunwayFromThresholdM:
            value = float(inputs.runway_from_threshold_m) if bool(inputs.has_runway_from_threshold_m) else float("inf")
        elif prop == ef_py.ConditionalObjectiveProperty.OnRunwayGeom:
            value = 1.0 if bool(inputs.on_runway_geom) else 0.0
        elif prop == ef_py.ConditionalObjectiveProperty.OnRunway:
            value = 1.0 if bool(inputs.on_runway_task) else 0.0
        elif prop == ef_py.ConditionalObjectiveProperty.OnGround:
            value = 1.0 if bool(inputs.on_ground) else 0.0
        elif prop == ef_py.ConditionalObjectiveProperty.SinkRateAbsMps:
            value = float(inputs.sink_rate_abs_mps)
        elif prop == ef_py.ConditionalObjectiveProperty.IlsLocalizerAbs:
            value = float(inputs.ils_localizer_abs)
        elif prop == ef_py.ConditionalObjectiveProperty.IlsGlideslopeAbs:
            value = float(inputs.ils_glideslope_abs)
        elif prop == ef_py.ConditionalObjectiveProperty.DmeM:
            value = float(inputs.dme_m)
        elif prop == ef_py.ConditionalObjectiveProperty.Heading:
            value = float(inputs.heading_deg)
        elif prop == ef_py.ConditionalObjectiveProperty.X:
            value = float(inputs.x_m)
        elif prop == ef_py.ConditionalObjectiveProperty.Y:
            value = float(inputs.y_m)
        else:
            unknown_property = True
            matched = False
            break

        if i < 3:
            status[i] = value

        if cond.op_code == ef_py.ConditionalObjectiveOp.GreaterEqual and value < target_value:
            matched = False
        elif cond.op_code == ef_py.ConditionalObjectiveOp.GreaterThan and value <= target_value:
            matched = False
        elif cond.op_code == ef_py.ConditionalObjectiveOp.LessEqual and value > target_value:
            matched = False
        elif cond.op_code == ef_py.ConditionalObjectiveOp.LessThan and value >= target_value:
            matched = False
        if not matched:
            break

    success_runway_cross_penalty = 0.0
    if matched and float(shaping.runway_cross_penalty_weight) != 0.0 and bool(inputs.has_runway_cross_m):
        err = abs(float(inputs.runway_cross_m)) - max(0.0, float(shaping.runway_cross_deadband_m))
        if err > 0.0:
            x = err / max(1.0e-6, float(shaping.runway_cross_norm_m))
            clip = float(shaping.runway_cross_clip)
            if clip > 0.0:
                x = min(x, clip)
            p = min(8.0, max(1.0, float(shaping.runway_cross_power)))
            success_runway_cross_penalty = float(shaping.runway_cross_penalty_weight) * (x ** p)

    success_ground_track_error_penalty = 0.0
    if matched and float(shaping.ground_track_penalty_weight) != 0.0:
        err = float(inputs.ground_track_error_deg) - max(0.0, float(shaping.ground_track_deadband_deg))
        if err > 0.0:
            x = err / max(1.0e-6, float(shaping.ground_track_norm_deg))
            clip = float(shaping.ground_track_clip)
            if clip > 0.0:
                x = min(x, clip)
            p = min(8.0, max(1.0, float(shaping.ground_track_power)))
            success_ground_track_error_penalty = float(shaping.ground_track_penalty_weight) * (x ** p)

    return {
        "matched": matched,
        "unknown_property": unknown_property,
        "status0": status[0],
        "status1": status[1],
        "status2": status[2],
        "success_runway_cross_penalty": success_runway_cross_penalty,
        "success_ground_track_error_penalty": success_ground_track_error_penalty,
        "objective_bonus": float(spec.reward_bonus) if matched else 0.0,
    }


def _legacy_safety_runtime(inputs: ef_py.SafetyRuntimeInputs) -> dict[str, float | bool | str]:
    out = {
        "terminated": False,
        "reason": "running",
        "survival": 0.0,
        "crash_penalty": 0.0,
        "stall_penalty": 0.0,
        "overload_penalty": 0.0,
        "failfast_penalty": 0.0,
        "gear_collapse_penalty": 0.0,
        "off_runway_penalty": 0.0,
        "gear_stress_penalty": 0.0,
        "off_runway_terminate_penalty": 0.0,
    }
    if not bool(inputs.finite_state_valid):
        out["terminated"] = True
        out["reason"] = "nan_guard"
        out["crash_penalty"] = float(inputs.crash_penalty)
        return out
    if float(inputs.health) <= 0.0:
        out["terminated"] = True
        out["reason"] = "crash_health"
        out["crash_penalty"] = float(inputs.crash_penalty)
        return out
    out["survival"] = float(inputs.survival_reward)

    if bool(inputs.airborne) and bool(inputs.aoa_valid) and float(inputs.aoa_abs_deg) > float(inputs.stall_threshold_deg):
        stall_term = float(inputs.stall_penalty_weight) * (float(inputs.aoa_abs_deg) - float(inputs.stall_threshold_deg))
        if float(inputs.stall_penalty_clip) > 0.0 and stall_term < -float(inputs.stall_penalty_clip):
            stall_term = -float(inputs.stall_penalty_clip)
        out["stall_penalty"] = stall_term

    if bool(inputs.airborne) and float(inputs.curr_alt_agl_m) > float(inputs.overload_min_alt_agl_m) and float(inputs.g_abs) > float(inputs.overload_g_threshold):
        overload_term = float(inputs.overload_penalty_weight) * (float(inputs.g_abs) - float(inputs.overload_g_threshold))
        if float(inputs.overload_penalty_clip) > 0.0 and overload_term < -float(inputs.overload_penalty_clip):
            overload_term = -float(inputs.overload_penalty_clip)
        out["overload_penalty"] = overload_term

    if bool(inputs.airborne) and bool(inputs.aoa_valid) and float(inputs.aoa_abs_deg) > 50.0:
        out["terminated"] = True
        out["reason"] = "failfast_deep_stall"
        out["failfast_penalty"] = float(inputs.failfast_penalty)
    elif bool(inputs.airborne) and float(inputs.altitude_m) < 100.0 and float(inputs.roll_abs_deg) > 135.0:
        out["terminated"] = True
        out["reason"] = "failfast_inverted_low_alt"
        out["failfast_penalty"] = float(inputs.failfast_penalty)
    elif bool(inputs.airborne) and float(inputs.pitch_abs_deg) > 85.0:
        out["terminated"] = True
        out["reason"] = "failfast_extreme_pitch"
        out["failfast_penalty"] = float(inputs.failfast_penalty)

    if bool(inputs.gear_collapsed):
        out["terminated"] = True
        out["reason"] = "gear_collapse"
        out["gear_collapse_penalty"] = float(inputs.gear_collapse_penalty)
    elif bool(inputs.runway_surface_phase) and (not bool(inputs.on_runway_task)):
        out["off_runway_penalty"] = float(inputs.off_runway_penalty)
        if float(inputs.gear_stress) > 0.1:
            out["gear_stress_penalty"] = float(inputs.gear_stress) * float(inputs.gear_stress_penalty_weight)
        if float(inputs.off_runway_terminate_speed) > 0.0 and float(inputs.speed_mps) >= float(inputs.off_runway_terminate_speed):
            dt = float(inputs.time_step_s) if float(inputs.time_step_s) > 1.0e-6 else 0.05
            grace_steps = int(max(0.0, float(inputs.off_runway_terminate_grace_s)) / dt)
            if int(inputs.off_runway_steps) > grace_steps:
                out["terminated"] = True
                out["reason"] = "off_runway_terminate"
                out["off_runway_terminate_penalty"] = float(inputs.off_runway_terminate_penalty)

    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 3 mission runtime benchmark.")
    parser.add_argument("--iters", type=int, default=200000, help="Iterations per timing bucket.")
    parser.add_argument("--json-out", default="", help="Optional path to write JSON results.")
    args = parser.parse_args()

    route_result, inputs = _build_route_result()
    legacy_nav = _legacy_waypoint_nav(route_result, inputs)
    runtime_nav = ef_py.compute_waypoint_mission_nav(route_result, inputs)

    waypoint_inputs = ef_py.WaypointRewardInputs()
    waypoint_inputs.valid = True
    waypoint_inputs.waypoint_index = 1
    waypoint_inputs.waypoint_count = 2
    waypoint_inputs.is_flyover = False
    waypoint_inputs.has_guidance = True
    waypoint_inputs.dist_m = 14134.712341288418
    waypoint_inputs.xtk_m = -9989.499135140415
    waypoint_inputs.dtg_m = 14134.712341288418
    waypoint_inputs.waypoint_radius_m = 1000.0
    waypoint_inputs.leg_len_m = 10000.0
    waypoint_inputs.sequence_gate_m = 1000.0
    waypoint_inputs.distance_weight = -0.00004
    waypoint_inputs.distance_clip_m = 6000.0
    waypoint_inputs.cross_track_weight = -0.35
    waypoint_inputs.cross_track_deadband_m = 250.0
    waypoint_inputs.cross_track_norm_m = 1500.0
    waypoint_inputs.cross_track_power = 1.5
    waypoint_inputs.cross_track_clip = 2.0

    approach_inputs = ef_py.ApproachRewardInputs()
    approach_inputs.valid = True
    approach_inputs.ils_valid = True
    approach_inputs.ils_loc_dev = 0.1
    approach_inputs.ils_gs_dev = 0.1
    approach_inputs.ils_dme_m = 9000.0
    approach_inputs.has_prev_loc = True
    approach_inputs.prev_loc_abs = 0.3
    approach_inputs.has_prev_gs = True
    approach_inputs.prev_gs_abs = 0.4
    approach_inputs.has_prev_dme = True
    approach_inputs.prev_dme_m = 9100.0
    approach_inputs.localizer_improve_weight = 2.0
    approach_inputs.glideslope_improve_weight = 2.0
    approach_inputs.dme_progress_weight = 1.0
    approach_inputs.dme_progress_localizer_band = 0.2
    approach_inputs.dme_progress_glideslope_band = 0.2
    approach_inputs.capture_bonus = 5.0
    approach_inputs.capture_localizer_band = 0.2
    approach_inputs.capture_glideslope_band = 0.2

    objective_spec = ef_py.ConditionalObjectiveSpec()
    objective_spec.reward_bonus = 2200.0

    objective_cond0 = ef_py.ConditionalObjectiveCondition()
    objective_cond0.property_code = ef_py.ConditionalObjectiveProperty.OnRunwayGeom
    objective_cond0.op_code = ef_py.ConditionalObjectiveOp.GreaterEqual
    objective_cond0.target_value = 0.5

    objective_cond1 = ef_py.ConditionalObjectiveCondition()
    objective_cond1.property_code = ef_py.ConditionalObjectiveProperty.OnGround
    objective_cond1.op_code = ef_py.ConditionalObjectiveOp.GreaterEqual
    objective_cond1.target_value = 0.5

    objective_cond2 = ef_py.ConditionalObjectiveCondition()
    objective_cond2.property_code = ef_py.ConditionalObjectiveProperty.GroundSpeed
    objective_cond2.op_code = ef_py.ConditionalObjectiveOp.LessEqual
    objective_cond2.target_value = 2.0

    objective_cond3 = ef_py.ConditionalObjectiveCondition()
    objective_cond3.property_code = ef_py.ConditionalObjectiveProperty.CommandCode
    objective_cond3.op_code = ef_py.ConditionalObjectiveOp.GreaterEqual
    objective_cond3.target_value = 4.0

    objective_spec.conditions = [objective_cond0, objective_cond1, objective_cond2, objective_cond3]

    objective_inputs = ef_py.ConditionalObjectiveInputs()
    objective_inputs.on_runway_geom = True
    objective_inputs.on_ground = True
    objective_inputs.ground_speed_mps = 1.2
    objective_inputs.command_code = 4.0
    objective_inputs.has_runway_cross_m = True
    objective_inputs.runway_cross_m = 6.0
    objective_inputs.ground_track_error_deg = 12.0

    objective_shaping = ef_py.ObjectiveShapingConfig()
    objective_shaping.runway_cross_penalty_weight = -0.5
    objective_shaping.runway_cross_deadband_m = 2.0
    objective_shaping.runway_cross_norm_m = 10.0
    objective_shaping.runway_cross_power = 2.0
    objective_shaping.ground_track_penalty_weight = -1.0
    objective_shaping.ground_track_deadband_deg = 5.0
    objective_shaping.ground_track_norm_deg = 10.0
    objective_shaping.ground_track_power = 2.0

    safety_inputs = ef_py.SafetyRuntimeInputs()
    safety_inputs.finite_state_valid = True
    safety_inputs.health = 100.0
    safety_inputs.survival_reward = 0.02
    safety_inputs.airborne = True
    safety_inputs.aoa_valid = True
    safety_inputs.aoa_abs_deg = 18.0
    safety_inputs.stall_threshold_deg = 15.0
    safety_inputs.stall_penalty_weight = -1.0
    safety_inputs.stall_penalty_clip = 10.0
    safety_inputs.g_abs = 7.0
    safety_inputs.overload_g_threshold = 6.0
    safety_inputs.overload_penalty_weight = -2.0
    safety_inputs.overload_penalty_clip = 5.0
    safety_inputs.curr_alt_agl_m = 30.0
    safety_inputs.overload_min_alt_agl_m = 5.0
    safety_inputs.altitude_m = 80.0
    safety_inputs.roll_abs_deg = 140.0
    safety_inputs.pitch_abs_deg = 20.0
    safety_inputs.failfast_penalty = -50.0
    safety_inputs.gear_collapsed = False
    safety_inputs.runway_surface_phase = True
    safety_inputs.on_runway_task = False
    safety_inputs.gear_stress = 0.4
    safety_inputs.gear_stress_penalty_weight = -10.0
    safety_inputs.off_runway_penalty = -1.0
    safety_inputs.speed_mps = 45.0
    safety_inputs.off_runway_steps = 3
    safety_inputs.off_runway_terminate_speed = 40.0
    safety_inputs.off_runway_terminate_grace_s = 0.10
    safety_inputs.time_step_s = 0.05
    safety_inputs.off_runway_terminate_penalty = -200.0

    legacy_nav_ms = _time_call(lambda: _legacy_waypoint_nav(route_result, inputs), iters=int(args.iters))
    runtime_nav_ms = _time_call(lambda: ef_py.compute_waypoint_mission_nav(route_result, inputs), iters=int(args.iters))
    legacy_track_ms = _time_call(
        lambda: abs(_wrap_angle_deg(90.0 - (100.0 if math.isfinite(100.0) else 60.0))),
        iters=int(args.iters),
    )
    runtime_track_ms = _time_call(
        lambda: ef_py.compute_command_tracking_error_deg(90.0, 60.0, 3, 100.0),
        iters=int(args.iters),
    )
    legacy_waypoint_reward_ms = _time_call(lambda: _legacy_waypoint_reward(waypoint_inputs), iters=int(args.iters))
    runtime_waypoint_reward_ms = _time_call(lambda: ef_py.compute_waypoint_reward_terms(waypoint_inputs), iters=int(args.iters))
    legacy_approach_reward_ms = _time_call(lambda: _legacy_approach_reward(approach_inputs), iters=int(args.iters))
    runtime_approach_reward_ms = _time_call(lambda: ef_py.compute_approach_reward_terms(approach_inputs), iters=int(args.iters))
    legacy_objective_ms = _time_call(lambda: _legacy_conditional_objective(objective_spec, objective_inputs, objective_shaping), iters=int(args.iters))
    runtime_objective_ms = _time_call(
        lambda: ef_py.evaluate_conditional_objective(objective_spec, objective_inputs, objective_shaping),
        iters=int(args.iters),
    )
    legacy_safety_ms = _time_call(lambda: _legacy_safety_runtime(safety_inputs), iters=int(args.iters))
    runtime_safety_ms = _time_call(lambda: ef_py.compute_safety_runtime(safety_inputs), iters=int(args.iters))

    results = {
        "iters": int(args.iters),
        "legacy_nav_ms": float(legacy_nav_ms),
        "runtime_nav_ms": float(runtime_nav_ms),
        "nav_speedup": float(legacy_nav_ms / max(runtime_nav_ms, 1.0e-12)),
        "legacy_command_tracking_ms": float(legacy_track_ms),
        "runtime_command_tracking_ms": float(runtime_track_ms),
        "command_tracking_speedup": float(legacy_track_ms / max(runtime_track_ms, 1.0e-12)),
        "legacy_waypoint_reward_ms": float(legacy_waypoint_reward_ms),
        "runtime_waypoint_reward_ms": float(runtime_waypoint_reward_ms),
        "waypoint_reward_speedup": float(legacy_waypoint_reward_ms / max(runtime_waypoint_reward_ms, 1.0e-12)),
        "legacy_approach_reward_ms": float(legacy_approach_reward_ms),
        "runtime_approach_reward_ms": float(runtime_approach_reward_ms),
        "approach_reward_speedup": float(legacy_approach_reward_ms / max(runtime_approach_reward_ms, 1.0e-12)),
        "legacy_objective_ms": float(legacy_objective_ms),
        "runtime_objective_ms": float(runtime_objective_ms),
        "objective_speedup": float(legacy_objective_ms / max(runtime_objective_ms, 1.0e-12)),
        "legacy_safety_ms": float(legacy_safety_ms),
        "runtime_safety_ms": float(runtime_safety_ms),
        "safety_speedup": float(legacy_safety_ms / max(runtime_safety_ms, 1.0e-12)),
        "sample_nav": {
            "legacy": legacy_nav,
            "runtime": {
                "selected_steerpoint": float(runtime_nav.selected_steerpoint),
                "steerpoint_mode_code": float(runtime_nav.steerpoint_mode_code),
                "dist_m": float(runtime_nav.dist_m),
                "bearing_rel_deg": float(runtime_nav.bearing_rel_deg),
                "altitude_delta_m": float(runtime_nav.altitude_delta_m),
                "cdi_norm": float(runtime_nav.cdi_norm),
                "track_angle_error_deg": float(runtime_nav.track_angle_error_deg),
                "dtg_m": float(runtime_nav.dtg_m),
                "next_turn_deg": float(runtime_nav.next_turn_deg),
                "distance_to_turn_m": float(runtime_nav.distance_to_turn_m),
            },
        },
    }

    print("Mission Runtime Phase 3 Benchmark")
    print("=" * 35)
    print(f"legacy nav helper        : {results['legacy_nav_ms']:.6f} ms")
    print(f"runtime nav helper       : {results['runtime_nav_ms']:.6f} ms")
    print(f"nav helper speedup       : {results['nav_speedup']:.2f}x")
    print(f"legacy cmd tracking      : {results['legacy_command_tracking_ms']:.6f} ms")
    print(f"runtime cmd tracking     : {results['runtime_command_tracking_ms']:.6f} ms")
    print(f"cmd tracking speedup     : {results['command_tracking_speedup']:.2f}x")
    print(f"legacy waypoint reward   : {results['legacy_waypoint_reward_ms']:.6f} ms")
    print(f"runtime waypoint reward  : {results['runtime_waypoint_reward_ms']:.6f} ms")
    print(f"waypoint reward speedup  : {results['waypoint_reward_speedup']:.2f}x")
    print(f"legacy approach reward   : {results['legacy_approach_reward_ms']:.6f} ms")
    print(f"runtime approach reward  : {results['runtime_approach_reward_ms']:.6f} ms")
    print(f"approach reward speedup  : {results['approach_reward_speedup']:.2f}x")
    print(f"legacy objective helper  : {results['legacy_objective_ms']:.6f} ms")
    print(f"runtime objective helper : {results['runtime_objective_ms']:.6f} ms")
    print(f"objective helper speedup : {results['objective_speedup']:.2f}x")
    print(f"legacy safety helper     : {results['legacy_safety_ms']:.6f} ms")
    print(f"runtime safety helper    : {results['runtime_safety_ms']:.6f} ms")
    print(f"safety helper speedup    : {results['safety_speedup']:.2f}x")

    if args.json_out:
        with open(os.path.abspath(args.json_out), "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
