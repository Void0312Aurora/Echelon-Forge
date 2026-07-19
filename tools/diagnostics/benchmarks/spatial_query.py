#!/usr/bin/env python3
from __future__ import annotations

import argparse
import cProfile
import io
import json
import math
import os
import pstats
import sys
import tempfile
import time
from typing import Any

import numpy as np

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT_HINT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", "..", ".."))
if _REPO_ROOT_HINT not in sys.path:
    sys.path.insert(0, _REPO_ROOT_HINT)

from python.angles import bearing_deg, wrap_signed_deg
from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path

REPO_ROOT = ensure_repo_imports()
os.chdir(REPO_ROOT)

import ef_py  # noqa: E402
from gym_envs.scenario_loader import ScenarioLoader  # noqa: E402


DATABASE_PATH = resolve_repo_path("examples", "config", "database")
DEFAULT_ROUTE_CONTRACT = resolve_repo_path(
    "tests", "archive", "contracts", "env_regression", "waypoint", "waypoint_track_reward_regression.json"
)
DEFAULT_LANDING_CONTRACT = resolve_repo_path(
    "tests", "archive", "contracts", "env_regression", "landing", "ils_threshold_crossing_height_regression.json"
)


# Local names preserved as thin aliases; semantics owned by python.angles.
_bearing_to_deg = bearing_deg
_wrap_angle_deg = wrap_signed_deg


def _turn_lead_distance_m(turn_angle_deg: float, speed_mps: float, bank_limit_deg: float) -> float:
    turn_abs_deg = abs(float(turn_angle_deg))
    if turn_abs_deg <= 1.0e-6:
        return 0.0
    bank_lim = float(np.clip(bank_limit_deg, 5.0, 70.0))
    tanb = math.tan(math.radians(bank_lim))
    if abs(tanb) <= 1.0e-6:
        return 0.0
    v = max(30.0, float(speed_mps))
    r_turn = (v * v) / (9.80665 * abs(tanb))
    turn_half_rad = 0.5 * min(math.pi - 1.0e-3, math.radians(turn_abs_deg))
    return max(0.0, float(r_turn * math.tan(turn_half_rad)))


def _load_inline_contract(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    scenario = payload.get("scenario_inline", None)
    if not isinstance(scenario, dict):
        raise ValueError(f"{path} does not contain scenario_inline")
    return scenario


def _write_temp_scenario(scenario: dict[str, Any], *, stem: str) -> str:
    fd, tmp_path = tempfile.mkstemp(prefix=f"{stem}_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(scenario, f, ensure_ascii=True)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    return tmp_path


def _make_loader(scenario_path: str, seed: int) -> tuple[ef_py.SimulationKernel, ScenarioLoader]:
    sim = ef_py.SimulationKernel()
    sim.load_database(DATABASE_PATH)
    loader = ScenarioLoader(sim)
    loader.load_scenario(scenario_path, seed=seed)
    return sim, loader


def _nearest_beacon(loader: ScenarioLoader, x_m: float, y_m: float) -> dict[str, Any] | None:
    best = None
    best_d2 = float("inf")
    for beacon in loader.ils_beacons:
        dx = float(x_m) - float(beacon.get("cx", 0.0))
        dy = float(y_m) - float(beacon.get("cy", 0.0))
        d2 = dx * dx + dy * dy
        if d2 < best_d2:
            best_d2 = d2
            best = beacon
    return best


def _legacy_runway_local_frame(loader: ScenarioLoader, x_m: float, y_m: float) -> tuple[bool, float, float, float, float]:
    beacon = _nearest_beacon(loader, x_m, y_m)
    if beacon is None:
        return False, 0.0, 0.0, 0.0, 0.0
    h_rad = math.radians(float(beacon.get("heading", 0.0)))
    fwd_x = math.sin(h_rad)
    fwd_y = math.cos(h_rad)
    right_x = math.cos(h_rad)
    right_y = -math.sin(h_rad)
    dx = float(x_m) - float(beacon.get("cx", 0.0))
    dy = float(y_m) - float(beacon.get("cy", 0.0))
    along = dx * fwd_x + dy * fwd_y
    cross = dx * right_x + dy * right_y
    length = float(beacon.get("length", 0.0))
    width = float(beacon.get("width", 0.0))
    valid = bool(length > 1.0 and width > 1.0)
    return valid, float(along), float(cross), float(length), float(width)


def _legacy_ils_observation(
    loader: ScenarioLoader,
    x_m: float,
    y_m: float,
    alt_m: float,
    threshold_crossing_height_m: float,
) -> tuple[float, float, float, float]:
    beacon = _nearest_beacon(loader, x_m, y_m)
    if beacon is None:
        return 0.0, 0.0, 0.0, 0.0

    h_rad = math.radians(float(beacon["heading"]))
    fwd_x = math.sin(h_rad)
    fwd_y = math.cos(h_rad)
    right_x = math.cos(h_rad)
    right_y = -math.sin(h_rad)

    cx = float(beacon["cx"])
    cy = float(beacon["cy"])
    length = float(beacon.get("length", 0.0))
    loc_x = cx + fwd_x * (0.5 * length)
    loc_y = cy + fwd_y * (0.5 * length)

    dx = float(x_m) - loc_x
    dy = float(y_m) - loc_y
    along = -(dx * fwd_x + dy * fwd_y)
    cross = dx * right_x + dy * right_y

    along_abs = max(abs(along), 1.0)
    loc_angle_deg = math.degrees(math.atan2(cross, along_abs))
    loc_dev = float(np.clip(loc_angle_deg / float(beacon["loc_max_deg"]), -1.0, 1.0))

    thr_dx = float(x_m) - float(beacon["thr_x"])
    thr_dy = float(y_m) - float(beacon["thr_y"])
    approach_dist_m = -(thr_dx * fwd_x + thr_dy * fwd_y)
    dme = float(math.sqrt(thr_dx * thr_dx + thr_dy * thr_dy + (float(alt_m) - float(beacon["elev_m"])) ** 2))

    glide_slope_deg = float(beacon["glide_slope_deg"])
    gs_max_deg = float(beacon["gs_max_deg"])
    gs_ref_alt_m = float(beacon["elev_m"]) + max(0.0, float(threshold_crossing_height_m))
    if approach_dist_m <= 1.0:
        gs_dev = 0.0
    else:
        gs_angle_deg = math.degrees(math.atan2(float(alt_m) - gs_ref_alt_m, approach_dist_m))
        gs_dev = float(np.clip((gs_angle_deg - glide_slope_deg) / gs_max_deg, -1.0, 1.0))

    valid = 1.0 if dme <= float(beacon["range_m"]) else 0.0
    return float(valid), float(loc_dev), float(gs_dev), float(dme)


def _make_route_options(loader: ScenarioLoader, *, waypoint_index: int, own_x_m: float, own_y_m: float, own_speed_mps: float):
    opts = ef_py.SpatialRouteQueryOptions()
    opts.waypoint_index = int(np.clip(int(waypoint_index), 0, max(0, len(loader.waypoints) - 1)))
    opts.own_x_m = float(own_x_m)
    opts.own_y_m = float(own_y_m)
    opts.own_speed_mps = float(own_speed_mps)
    opts.base_lookahead_m = float(loader.mission_cmd.get("lnav_lookahead_m", 1500.0))
    opts.lnav_max_intercept_deg = float(loader.mission_cmd.get("lnav_max_intercept_deg", 25.0))
    opts.lnav_capture_max_intercept_deg = float(
        loader.mission_cmd.get("lnav_capture_max_intercept_deg", max(opts.lnav_max_intercept_deg, 45.0))
    )
    capture_xtrack = loader.mission_cmd.get("lnav_capture_xtrack_m", None)
    opts.lnav_capture_xtrack_m = 0.0 if capture_xtrack is None else float(capture_xtrack)
    opts.lnav_capture_course_error_deg = float(loader.mission_cmd.get("lnav_capture_course_error_deg", 45.0))
    opts.lnav_direct_to_final_fix = bool(loader.mission_cmd.get("lnav_direct_to_final_fix", True))
    flyover_capture_window = loader.mission_cmd.get("lnav_flyover_capture_window_m", None)
    opts.lnav_flyover_capture_window_m = 0.0 if flyover_capture_window is None else float(flyover_capture_window)
    opts.lnav_bank_limit_deg = float(loader.mission_cmd.get("lnav_bank_limit_deg", 30.0))
    opts.lnav_sequence_gate_scale = float(loader.mission_cmd.get("lnav_sequence_gate_scale", 0.35))
    seq_gate_min = loader.mission_cmd.get("lnav_sequence_gate_min_m", None)
    seq_gate_max = loader.mission_cmd.get("lnav_sequence_gate_max_m", None)
    opts.lnav_sequence_gate_min_m = 0.0 if seq_gate_min is None else float(seq_gate_min)
    opts.lnav_sequence_gate_max_m = 0.0 if seq_gate_max is None else float(seq_gate_max)
    return opts


def _legacy_route_guidance(
    loader: ScenarioLoader,
    *,
    waypoint_index: int,
    own_x_m: float,
    own_y_m: float,
    own_speed_mps: float,
) -> dict[str, float | bool | str]:
    idx = int(np.clip(int(waypoint_index), 0, max(0, len(loader.waypoints) - 1)))
    wp = loader.waypoints[idx]
    waypoint_mode = loader._normalize_waypoint_mode(wp.get("waypoint_mode", loader.mission_cmd.get("waypoint_mode", "flyby")))

    if idx <= 0:
        sx = float(getattr(loader, "_waypoint_leg_origin_x", own_x_m))
        sy = float(getattr(loader, "_waypoint_leg_origin_y", own_y_m))
    else:
        prev = loader.waypoints[idx - 1]
        sx = float(prev.get("x", 0.0))
        sy = float(prev.get("y", 0.0))

    ex = float(wp.get("x", 0.0))
    ey = float(wp.get("y", 0.0))
    lx = ex - sx
    ly = ey - sy
    leg_len = float(math.hypot(lx, ly))

    dx = ex - float(own_x_m)
    dy = ey - float(own_y_m)
    dist_m = float(math.hypot(dx, dy))
    direct_to_track_deg = float(_bearing_to_deg(dx, dy))

    desired_track_deg = direct_to_track_deg
    xtk_m = 0.0
    along_m = 0.0
    dtg_m = dist_m
    if leg_len > 1.0e-6:
        desired_track_deg = float(_bearing_to_deg(lx, ly))
        ux = lx / leg_len
        uy = ly / leg_len
        rx = uy
        ry = -ux
        px = float(own_x_m) - sx
        py = float(own_y_m) - sy
        xtk_m = float(px * rx + py * ry)
        along_m = float(px * ux + py * uy)
        dtg_m = max(0.0, float(leg_len - along_m))

    lookahead_m = float(loader.mission_cmd.get("lnav_lookahead_m", 1500.0))
    spd = float(own_speed_mps)
    if math.isfinite(spd) and spd > 1.0:
        lookahead_m = max(500.0, min(5000.0, spd * 8.0))
    lookahead_m = max(200.0, float(lookahead_m))

    max_int = float(loader.mission_cmd.get("lnav_max_intercept_deg", 25.0))
    capture_max_int = float(loader.mission_cmd.get("lnav_capture_max_intercept_deg", max(max_int, 45.0)))
    capture_max_int = max(max_int, capture_max_int)
    waypoint_radius_m = max(1.0, float(wp.get("radius_m", loader.mission_cmd.get("waypoint_radius_m", 1000.0))))
    capture_xtrack_m = float(
        loader.mission_cmd.get(
            "lnav_capture_xtrack_m",
            max(2.0 * waypoint_radius_m, min(8000.0, 0.35 * max(1.0, leg_len))),
        )
    )
    capture_xtrack_m = max(waypoint_radius_m, capture_xtrack_m)
    capture_course_err_deg = float(loader.mission_cmd.get("lnav_capture_course_error_deg", 45.0))
    direct_to_final_fix = bool(loader.mission_cmd.get("lnav_direct_to_final_fix", True))
    flyover_capture_window_m = float(
        loader.mission_cmd.get(
            "lnav_flyover_capture_window_m",
            max(2.0 * waypoint_radius_m, min(5000.0, 0.30 * max(1.0, leg_len))),
        )
    )
    flyover_capture_window_m = max(waypoint_radius_m, flyover_capture_window_m)
    before_leg = along_m < -0.25 * lookahead_m
    far_off_course = abs(xtk_m) > capture_xtrack_m
    large_to_from_angle = abs(_wrap_angle_deg(direct_to_track_deg - desired_track_deg)) > capture_course_err_deg
    final_leg = idx >= (len(loader.waypoints) - 1)
    passed_fix = along_m >= leg_len
    near_flyover_terminal = (
        waypoint_mode == "flyover"
        and (dist_m <= flyover_capture_window_m or along_m >= max(0.0, leg_len - flyover_capture_window_m))
    )
    missed_flyby_recovery = bool(waypoint_mode == "flyby" and passed_fix)
    use_direct_to = bool(
        (final_leg and direct_to_final_fix)
        or before_leg
        or (far_off_course and large_to_from_angle)
        or near_flyover_terminal
        or (waypoint_mode == "flyover" and passed_fix)
        or missed_flyby_recovery
    )
    direct_to_fix_guidance = bool(
        use_direct_to and ((final_leg and direct_to_final_fix) or waypoint_mode == "flyover" or missed_flyby_recovery)
    )

    cmd_track_deg = desired_track_deg
    if use_direct_to:
        if direct_to_fix_guidance:
            cmd_track_deg = direct_to_track_deg
        else:
            capture_delta_deg = float(_wrap_angle_deg(direct_to_track_deg - desired_track_deg))
            capture_delta_deg = float(np.clip(capture_delta_deg, -capture_max_int, capture_max_int))
            cmd_track_deg = float((desired_track_deg + capture_delta_deg + 360.0) % 360.0)
    else:
        intercept_rad = math.atan2(-xtk_m, lookahead_m)
        intercept_deg = float(math.degrees(intercept_rad))
        if max_int > 0.0:
            intercept_deg = float(np.clip(intercept_deg, -max_int, max_int))
        cmd_track_deg = float((desired_track_deg + intercept_deg + 360.0) % 360.0)

    reward_desired_track_deg = float(direct_to_track_deg if direct_to_fix_guidance else desired_track_deg)
    reward_xtk_m = float(0.0 if direct_to_fix_guidance else xtk_m)
    reward_dtg_m = float(dist_m if direct_to_fix_guidance else dtg_m)

    next_turn_deg = 0.0
    next_turn_abs_deg = 0.0
    prev_turn_abs_deg = 0.0
    lead_turn_m = 0.0
    distance_to_turn_m = float(dist_m if direct_to_fix_guidance else dtg_m)
    dist_to_next_turn_start_m = float(distance_to_turn_m)
    distance_from_prev_turn_m = max(0.0, float(along_m))
    sequence_gate_scale = float(loader.mission_cmd.get("lnav_sequence_gate_scale", 0.35))
    sequence_gate_min_m = float(loader.mission_cmd.get("lnav_sequence_gate_min_m", waypoint_radius_m))
    sequence_gate_max_m = float(
        loader.mission_cmd.get("lnav_sequence_gate_max_m", max(2.5 * waypoint_radius_m, waypoint_radius_m + 1500.0))
    )
    sequence_gate_m = waypoint_radius_m

    if idx < len(loader.waypoints) - 1:
        next_wp = loader.waypoints[idx + 1]
        next_dx = float(next_wp.get("x", 0.0)) - ex
        next_dy = float(next_wp.get("y", 0.0)) - ey
        if (next_dx * next_dx + next_dy * next_dy) > 1.0e-9:
            cur_track_deg = float(_bearing_to_deg(lx, ly))
            next_track_deg = float(_bearing_to_deg(next_dx, next_dy))
            next_turn_deg = float(_wrap_angle_deg(next_track_deg - desired_track_deg))
            next_turn_abs_deg = abs(float(_wrap_angle_deg(next_track_deg - cur_track_deg)))
            lead_turn_m = _turn_lead_distance_m(
                next_turn_abs_deg,
                max(30.0, float(own_speed_mps)),
                float(loader.mission_cmd.get("lnav_bank_limit_deg", 30.0)),
            )
            sequence_gate_m = max(
                sequence_gate_min_m,
                min(sequence_gate_max_m, waypoint_radius_m + sequence_gate_scale * max(0.0, lead_turn_m)),
            )
            dist_to_next_turn_start_m = max(0.0, float(dtg_m - lead_turn_m))
            if not direct_to_fix_guidance:
                distance_to_turn_m = float(dist_to_next_turn_start_m)

    if idx > 0:
        if idx == 1:
            psx = float(getattr(loader, "_waypoint_leg_origin_x", sx))
            psy = float(getattr(loader, "_waypoint_leg_origin_y", sy))
        else:
            prevprev = loader.waypoints[idx - 2]
            psx = float(prevprev.get("x", 0.0))
            psy = float(prevprev.get("y", 0.0))
        prev_lx = sx - psx
        prev_ly = sy - psy
        if (prev_lx * prev_lx + prev_ly * prev_ly) > 1.0e-9 and (lx * lx + ly * ly) > 1.0e-9:
            prev_trk = float(_bearing_to_deg(prev_lx, prev_ly))
            cur_trk = float(_bearing_to_deg(lx, ly))
            prev_turn_abs_deg = abs(float(_wrap_angle_deg(cur_trk - prev_trk)))

    return {
        "idx": int(idx),
        "count": int(len(loader.waypoints)),
        "waypoint_mode": str(waypoint_mode),
        "dist_m": float(dist_m),
        "direct_to_track_deg": float(direct_to_track_deg),
        "desired_track_deg": float(desired_track_deg),
        "reward_desired_track_deg": float(reward_desired_track_deg),
        "xtk_m": float(xtk_m),
        "reward_xtk_m": float(reward_xtk_m),
        "along_m": float(along_m),
        "dtg_m": float(dtg_m),
        "reward_dtg_m": float(reward_dtg_m),
        "leg_len_m": float(leg_len),
        "waypoint_radius_m": float(waypoint_radius_m),
        "cmd_track_deg": float(cmd_track_deg),
        "next_turn_deg": float(next_turn_deg),
        "next_turn_abs_deg": float(next_turn_abs_deg),
        "prev_turn_abs_deg": float(prev_turn_abs_deg),
        "lead_turn_m": float(lead_turn_m),
        "sequence_gate_m": float(sequence_gate_m),
        "distance_to_turn_m": float(distance_to_turn_m),
        "dist_to_next_turn_start_m": float(dist_to_next_turn_start_m),
        "distance_from_prev_turn_m": float(distance_from_prev_turn_m),
        "use_direct_to": bool(use_direct_to),
        "direct_to_fix_guidance": bool(direct_to_fix_guidance),
        "final_leg": bool(final_leg),
        "passed_fix": bool(passed_fix),
    }


def _compiled_nav_v2_products(loader: ScenarioLoader, truth, inst) -> dict[str, float] | None:
    gstate = loader._compute_waypoint_guidance_state(truth=truth, inst=inst)
    if gstate is None:
        return None

    idx = int(gstate["idx"])
    n = int(gstate["count"])
    wp = gstate["wp"]
    waypoint_mode = str(gstate["waypoint_mode"])

    own_z = float(getattr(truth, "z", 0.0))
    own_heading_deg = float(getattr(truth, "heading", 0.0))
    ground_track_deg = own_heading_deg
    true_airspeed_mps = float(getattr(truth, "speed", 0.0))
    if inst is not None:
        try:
            hdg = float(getattr(inst, "heading", own_heading_deg))
            if math.isfinite(hdg):
                own_heading_deg = hdg
        except Exception:
            pass
        try:
            trk = float(getattr(inst, "ground_track", own_heading_deg))
            if math.isfinite(trk):
                ground_track_deg = trk
        except Exception:
            pass
        try:
            ias = float(getattr(inst, "ias", true_airspeed_mps))
            if math.isfinite(ias) and ias > 1.0:
                true_airspeed_mps = ias
        except Exception:
            pass
    if abs(_wrap_angle_deg(ground_track_deg - own_heading_deg)) > 85.0 and true_airspeed_mps > 80.0:
        ground_track_deg = own_heading_deg

    dist_m = float(gstate["dist_m"])
    direct_bearing_deg = float(gstate["direct_to_track_deg"])
    bearing_rel_deg = float(_wrap_angle_deg(direct_bearing_deg - own_heading_deg))
    altitude_delta_m = float(wp.get("altitude_m", wp.get("z", 0.0)) - own_z)
    desired_leg_track_deg = float(gstate["reward_desired_track_deg"])
    xtk_m = float(gstate["reward_xtk_m"])
    dtg_m = float(gstate["reward_dtg_m"])

    cdi_full_scale_m = 1500.0
    try:
        cdi_full_scale_m = float(
            loader.mission_cmd.get(
                "nav_course_dev_full_scale_m",
                loader.mission_cmd.get(
                    "course_dev_full_scale_m",
                    max(1000.0, float(loader.mission_cmd.get("waypoint_radius_m", 1000.0))),
                ),
            )
        )
    except Exception:
        cdi_full_scale_m = 1500.0
    cdi_norm = float(np.clip(xtk_m / max(1.0, cdi_full_scale_m), -1.0, 1.0))
    track_angle_error_deg = float(_wrap_angle_deg(desired_leg_track_deg - ground_track_deg))

    return {
        "selected_steerpoint": float(idx + 1),
        "steerpoint_mode_code": 1.0 if waypoint_mode == "flyover" else 0.0,
        "dist_m": float(dist_m),
        "bearing_rel_deg": float(bearing_rel_deg),
        "altitude_delta_m": float(altitude_delta_m),
        "cdi_norm": float(cdi_norm),
        "track_angle_error_deg": float(track_angle_error_deg),
        "dtg_m": float(dtg_m),
        "next_turn_deg": float(gstate.get("next_turn_deg", 0.0)),
        "distance_to_turn_m": float(gstate.get("distance_to_turn_m", dtg_m)),
    }


def _legacy_nav_v2_products(loader: ScenarioLoader, truth, inst) -> dict[str, float]:
    idx = int(np.clip(int(getattr(loader, "waypoint_idx", 0)), 0, max(0, len(loader.waypoints) - 1)))
    own_speed_mps = float(getattr(truth, "speed", 0.0))
    if inst is not None:
        try:
            ias = float(getattr(inst, "ias", own_speed_mps))
            if math.isfinite(ias) and ias > 1.0:
                own_speed_mps = ias
        except Exception:
            pass
    gstate = _legacy_route_guidance(
        loader,
        waypoint_index=idx,
        own_x_m=float(getattr(truth, "x", 0.0)),
        own_y_m=float(getattr(truth, "y", 0.0)),
        own_speed_mps=float(own_speed_mps),
    )
    wp = loader.waypoints[idx]
    waypoint_mode = str(gstate["waypoint_mode"])

    own_z = float(getattr(truth, "z", 0.0))
    own_heading_deg = float(getattr(truth, "heading", 0.0))
    ground_track_deg = own_heading_deg
    true_airspeed_mps = float(getattr(truth, "speed", 0.0))
    if inst is not None:
        try:
            hdg = float(getattr(inst, "heading", own_heading_deg))
            if math.isfinite(hdg):
                own_heading_deg = hdg
        except Exception:
            pass
        try:
            trk = float(getattr(inst, "ground_track", own_heading_deg))
            if math.isfinite(trk):
                ground_track_deg = trk
        except Exception:
            pass
        try:
            ias = float(getattr(inst, "ias", true_airspeed_mps))
            if math.isfinite(ias) and ias > 1.0:
                true_airspeed_mps = ias
        except Exception:
            pass
    if abs(_wrap_angle_deg(ground_track_deg - own_heading_deg)) > 85.0 and true_airspeed_mps > 80.0:
        ground_track_deg = own_heading_deg

    dist_m = float(gstate["dist_m"])
    direct_bearing_deg = float(gstate["direct_to_track_deg"])
    bearing_rel_deg = float(_wrap_angle_deg(direct_bearing_deg - own_heading_deg))
    altitude_delta_m = float(wp.get("altitude_m", wp.get("z", 0.0)) - own_z)
    desired_leg_track_deg = float(gstate["reward_desired_track_deg"])
    xtk_m = float(gstate["reward_xtk_m"])
    dtg_m = float(gstate["reward_dtg_m"])

    cdi_full_scale_m = 1500.0
    try:
        cdi_full_scale_m = float(
            loader.mission_cmd.get(
                "nav_course_dev_full_scale_m",
                loader.mission_cmd.get(
                    "course_dev_full_scale_m",
                    max(1000.0, float(loader.mission_cmd.get("waypoint_radius_m", 1000.0))),
                ),
            )
        )
    except Exception:
        cdi_full_scale_m = 1500.0
    cdi_norm = float(np.clip(xtk_m / max(1.0, cdi_full_scale_m), -1.0, 1.0))
    track_angle_error_deg = float(_wrap_angle_deg(desired_leg_track_deg - ground_track_deg))

    return {
        "selected_steerpoint": float(idx + 1),
        "steerpoint_mode_code": 1.0 if waypoint_mode == "flyover" else 0.0,
        "dist_m": float(dist_m),
        "bearing_rel_deg": float(bearing_rel_deg),
        "altitude_delta_m": float(altitude_delta_m),
        "cdi_norm": float(cdi_norm),
        "track_angle_error_deg": float(track_angle_error_deg),
        "dtg_m": float(dtg_m),
        "next_turn_deg": float(gstate["next_turn_deg"]),
        "distance_to_turn_m": float(gstate["distance_to_turn_m"]),
    }


def _compiled_route_projection(loader: ScenarioLoader, sample: dict[str, float]) -> dict[str, float | bool | str]:
    result = loader._spatial_geometry.query_route_guidance(
        _make_route_options(
            loader,
            waypoint_index=int(sample["waypoint_index"]),
            own_x_m=sample["own_x_m"],
            own_y_m=sample["own_y_m"],
            own_speed_mps=sample["own_speed_mps"],
        )
    )
    return {
        "idx": int(result.idx),
        "count": int(result.count),
        "waypoint_mode": str(result.waypoint_mode),
        "dist_m": float(result.dist_m),
        "direct_to_track_deg": float(result.direct_to_track_deg),
        "desired_track_deg": float(result.desired_track_deg),
        "reward_desired_track_deg": float(result.reward_desired_track_deg),
        "xtk_m": float(result.xtk_m),
        "reward_xtk_m": float(result.reward_xtk_m),
        "along_m": float(result.along_m),
        "dtg_m": float(result.dtg_m),
        "reward_dtg_m": float(result.reward_dtg_m),
        "leg_len_m": float(result.leg_len_m),
        "waypoint_radius_m": float(result.waypoint_radius_m),
        "cmd_track_deg": float(result.cmd_track_deg),
        "next_turn_deg": float(result.next_turn_deg),
        "next_turn_abs_deg": float(result.next_turn_abs_deg),
        "prev_turn_abs_deg": float(result.prev_turn_abs_deg),
        "lead_turn_m": float(result.lead_turn_m),
        "sequence_gate_m": float(result.sequence_gate_m),
        "distance_to_turn_m": float(result.distance_to_turn_m),
        "dist_to_next_turn_start_m": float(result.dist_to_next_turn_start_m),
        "distance_from_prev_turn_m": float(result.distance_from_prev_turn_m),
        "use_direct_to": bool(result.use_direct_to),
        "direct_to_fix_guidance": bool(result.direct_to_fix_guidance),
        "final_leg": bool(result.final_leg),
        "passed_fix": bool(result.passed_fix),
    }


def _compiled_ils_projection(loader: ScenarioLoader, sample: dict[str, float]) -> tuple[float, float, float, float]:
    result = loader._spatial_geometry.query_ils(
        sample["x_m"],
        sample["y_m"],
        sample["alt_m"],
        sample["threshold_crossing_height_m"],
    )
    return float(result.valid), float(result.loc_dev), float(result.gs_dev), float(result.dme_m)


def _compiled_runway_projection(loader: ScenarioLoader, sample: dict[str, float]) -> tuple[float, float, float, float, float]:
    result = loader._spatial_geometry.query_runway_local_frame(sample["x_m"], sample["y_m"])
    return (
        float(result.valid),
        float(result.along_m),
        float(result.cross_m),
        float(result.length_m),
        float(result.width_m),
    )


def _profile_callable(fn, *, iters: int) -> dict[str, Any]:
    profiler = cProfile.Profile()
    profiler.enable()
    for _ in range(max(1, int(iters))):
        fn()
    profiler.disable()
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream).sort_stats("cumulative")
    stats.print_stats(10)
    total_calls = 0
    total_time_s = 0.0
    for func_data in stats.stats.values():
        ccalls, _ncalls, tt, _ct, _callers = func_data
        total_calls += int(ccalls)
        total_time_s += float(tt)
    return {
        "total_python_time_s": float(total_time_s),
        "top": stream.getvalue().strip().splitlines()[:18],
        "total_calls": int(total_calls),
    }


def _sample_route_queries(loader: ScenarioLoader, *, samples_per_leg: int, cross_tracks_m: list[float]) -> list[dict[str, float]]:
    samples: list[dict[str, float]] = []
    if not loader.waypoints:
        return samples
    for idx, wp in enumerate(loader.waypoints):
        if idx <= 0:
            sx = float(getattr(loader, "_waypoint_leg_origin_x", 0.0))
            sy = float(getattr(loader, "_waypoint_leg_origin_y", 0.0))
        else:
            prev = loader.waypoints[idx - 1]
            sx = float(prev.get("x", 0.0))
            sy = float(prev.get("y", 0.0))
        ex = float(wp.get("x", 0.0))
        ey = float(wp.get("y", 0.0))
        lx = ex - sx
        ly = ey - sy
        leg_len = float(math.hypot(lx, ly))
        if leg_len <= 1.0e-6:
            continue
        ux = lx / leg_len
        uy = ly / leg_len
        rx = uy
        ry = -ux
        own_speed = float(wp.get("speed_mps", loader.mission_cmd.get("target_speed", 210.0)))
        for along in np.linspace(-0.15 * leg_len, 1.10 * leg_len, max(4, int(samples_per_leg))):
            for cross in cross_tracks_m:
                own_x = sx + along * ux + cross * rx
                own_y = sy + along * uy + cross * ry
                samples.append(
                    {
                        "waypoint_index": float(idx),
                        "own_x_m": float(own_x),
                        "own_y_m": float(own_y),
                        "own_speed_mps": float(own_speed),
                    }
                )
    return samples


def _sample_ils_queries(loader: ScenarioLoader, *, approach_dists_m: list[float], cross_tracks_m: list[float]) -> list[dict[str, float]]:
    samples: list[dict[str, float]] = []
    if not loader.ils_beacons:
        return samples
    beacon = loader.ils_beacons[0]
    h_rad = math.radians(float(beacon["heading"]))
    fwd_x = math.sin(h_rad)
    fwd_y = math.cos(h_rad)
    right_x = math.cos(h_rad)
    right_y = -math.sin(h_rad)
    threshold_crossing_height_m = float(loader.mission_cmd.get("threshold_crossing_height_m", 15.0))
    for dist in approach_dists_m:
        alt = float(beacon["elev_m"]) + threshold_crossing_height_m + math.tan(
            math.radians(float(beacon["glide_slope_deg"]))
        ) * float(dist)
        for cross in cross_tracks_m:
            x = float(beacon["thr_x"]) - float(dist) * fwd_x + float(cross) * right_x
            y = float(beacon["thr_y"]) - float(dist) * fwd_y + float(cross) * right_y
            samples.append(
                {
                    "x_m": float(x),
                    "y_m": float(y),
                    "alt_m": float(alt),
                    "threshold_crossing_height_m": float(threshold_crossing_height_m),
                }
            )
    return samples


def _sample_runway_queries(loader: ScenarioLoader, *, alongs_m: list[float], crosses_m: list[float]) -> list[dict[str, float]]:
    samples: list[dict[str, float]] = []
    if not loader.ils_beacons:
        return samples
    beacon = loader.ils_beacons[0]
    h_rad = math.radians(float(beacon["heading"]))
    fwd_x = math.sin(h_rad)
    fwd_y = math.cos(h_rad)
    right_x = math.cos(h_rad)
    right_y = -math.sin(h_rad)
    cx = float(beacon["cx"])
    cy = float(beacon["cy"])
    for along in alongs_m:
        for cross in crosses_m:
            x = cx + float(along) * fwd_x + float(cross) * right_x
            y = cy + float(along) * fwd_y + float(cross) * right_y
            samples.append({"x_m": float(x), "y_m": float(y)})
    return samples


def _numeric_projection(value: Any) -> list[float]:
    if isinstance(value, tuple):
        return [float(v) for v in value]
    if isinstance(value, dict):
        return [float(value[k]) for k in sorted(value.keys()) if isinstance(value[k], (int, float, bool))]
    attrs = []
    for name in dir(value):
        if name.startswith("_"):
            continue
        try:
            attr = getattr(value, name)
        except Exception:
            continue
        if callable(attr):
            continue
        if isinstance(attr, (int, float, bool)):
            attrs.append((name, float(attr)))
    attrs.sort(key=lambda item: item[0])
    return [item[1] for item in attrs]


def _benchmark_query_pair(compiled_fn, legacy_fn, samples: list[dict[str, float]], *, warmup: int, iters: int) -> dict[str, Any]:
    if not samples:
        return {
            "samples": 0,
            "compiled_ms_per_call": None,
            "legacy_ms_per_call": None,
            "speedup_vs_legacy": None,
            "max_abs_diff": None,
        }

    max_abs_diff = 0.0
    for sample in samples[: min(64, len(samples))]:
        compiled = compiled_fn(sample)
        legacy = legacy_fn(sample)
        compiled_vals = _numeric_projection(compiled)
        legacy_vals = _numeric_projection(legacy)
        for lhs, rhs in zip(compiled_vals, legacy_vals):
            max_abs_diff = max(max_abs_diff, abs(lhs - rhs))

    for _ in range(max(1, int(warmup))):
        for sample in samples:
            compiled_fn(sample)
        for sample in samples:
            legacy_fn(sample)

    start = time.perf_counter()
    for _ in range(max(1, int(iters))):
        for sample in samples:
            compiled_fn(sample)
    compiled_elapsed = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(max(1, int(iters))):
        for sample in samples:
            legacy_fn(sample)
    legacy_elapsed = time.perf_counter() - start

    compiled_calls = max(1, len(samples) * max(1, int(iters)))
    legacy_calls = max(1, len(samples) * max(1, int(iters)))
    compiled_ms = 1000.0 * compiled_elapsed / compiled_calls
    legacy_ms = 1000.0 * legacy_elapsed / legacy_calls
    return {
        "samples": int(len(samples)),
        "compiled_ms_per_call": float(compiled_ms),
        "legacy_ms_per_call": float(legacy_ms),
        "speedup_vs_legacy": float(legacy_ms / max(compiled_ms, 1.0e-12)),
        "max_abs_diff": float(max_abs_diff),
    }


def _print_summary(results: dict[str, Any]) -> None:
    print("Spatial Query Phase 1 Benchmark")
    print("=" * 34)
    for name in ("runway_frame", "ils_sample", "route_guidance"):
        row = results["query_benchmarks"][name]
        print(
            f"{name:>16}: compiled={row['compiled_ms_per_call']:.6f} ms  "
            f"legacy={row['legacy_ms_per_call']:.6f} ms  "
            f"speedup={row['speedup_vs_legacy']:.2f}x  "
            f"max_abs_diff={row['max_abs_diff']:.3e}"
        )
    nav = results["nav_v2_profile"]
    print(
        f"{'nav_v2 profile':>16}: compiled_total={nav['compiled']['total_python_time_s']:.4f}s  "
        f"legacy_total={nav['legacy']['total_python_time_s']:.4f}s  "
        f"speedup={nav['legacy']['total_python_time_s'] / max(nav['compiled']['total_python_time_s'], 1.0e-12):.2f}x"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 1 spatial-query benchmark and profile harness.")
    parser.add_argument("--route-contract", default=DEFAULT_ROUTE_CONTRACT, help="Waypoint contract containing scenario_inline.")
    parser.add_argument("--landing-contract", default=DEFAULT_LANDING_CONTRACT, help="Landing contract containing scenario_inline.")
    parser.add_argument("--seed", type=int, default=0, help="Scenario seed.")
    parser.add_argument("--warmup", type=int, default=8, help="Warmup iterations for microbenchmarks.")
    parser.add_argument("--iters", type=int, default=128, help="Measured iterations for microbenchmarks.")
    parser.add_argument("--samples-per-leg", type=int, default=24, help="Route samples along each active leg.")
    parser.add_argument("--profile-iters", type=int, default=2000, help="Profiler iterations for nav_v2 helpers.")
    parser.add_argument("--json-out", default="", help="Optional path to write JSON results.")
    args = parser.parse_args()

    route_scenario_path = ""
    landing_scenario_path = ""
    route_sim = None
    landing_sim = None
    try:
        route_scenario_path = _write_temp_scenario(_load_inline_contract(os.path.abspath(args.route_contract)), stem="phase1_route")
        landing_scenario_path = _write_temp_scenario(
            _load_inline_contract(os.path.abspath(args.landing_contract)),
            stem="phase1_landing",
        )

        route_sim, route_loader = _make_loader(route_scenario_path, seed=int(args.seed))
        landing_sim, landing_loader = _make_loader(landing_scenario_path, seed=int(args.seed))

        route_samples = _sample_route_queries(
            route_loader,
            samples_per_leg=max(4, int(args.samples_per_leg)),
            cross_tracks_m=[-1500.0, -600.0, 0.0, 600.0, 1500.0],
        )
        ils_samples = _sample_ils_queries(
            landing_loader,
            approach_dists_m=[250.0, 750.0, 1500.0, 3000.0, 5000.0],
            cross_tracks_m=[-120.0, -40.0, 0.0, 40.0, 120.0],
        )
        runway_samples = _sample_runway_queries(
            landing_loader,
            alongs_m=[-800.0, -400.0, 0.0, 400.0, 800.0],
            crosses_m=[-80.0, -30.0, 0.0, 30.0, 80.0],
        )

        route_bench = _benchmark_query_pair(
            lambda sample: _compiled_route_projection(route_loader, sample),
            lambda sample: _legacy_route_guidance(
                route_loader,
                waypoint_index=int(sample["waypoint_index"]),
                own_x_m=sample["own_x_m"],
                own_y_m=sample["own_y_m"],
                own_speed_mps=sample["own_speed_mps"],
            ),
            route_samples,
            warmup=int(args.warmup),
            iters=int(args.iters),
        )
        ils_bench = _benchmark_query_pair(
            lambda sample: _compiled_ils_projection(landing_loader, sample),
            lambda sample: _legacy_ils_observation(
                landing_loader,
                sample["x_m"],
                sample["y_m"],
                sample["alt_m"],
                sample["threshold_crossing_height_m"],
            ),
            ils_samples,
            warmup=int(args.warmup),
            iters=int(args.iters),
        )
        runway_bench = _benchmark_query_pair(
            lambda sample: _compiled_runway_projection(landing_loader, sample),
            lambda sample: _legacy_runway_local_frame(landing_loader, sample["x_m"], sample["y_m"]),
            runway_samples,
            warmup=int(args.warmup),
            iters=int(args.iters),
        )

        route_truth = route_sim.get_agent_observation(route_loader.agent_id)
        route_inst = route_sim.get_instrument_state(route_loader.agent_id)
        nav_compiled_profile = _profile_callable(
            lambda: _compiled_nav_v2_products(route_loader, route_truth, route_inst),
            iters=int(args.profile_iters),
        )
        nav_legacy_profile = _profile_callable(
            lambda: _legacy_nav_v2_products(route_loader, route_truth, route_inst),
            iters=int(args.profile_iters),
        )

        results = {
            "route_contract": os.path.abspath(args.route_contract),
            "landing_contract": os.path.abspath(args.landing_contract),
            "query_benchmarks": {
                "runway_frame": runway_bench,
                "ils_sample": ils_bench,
                "route_guidance": route_bench,
            },
            "nav_v2_profile": {
                "compiled": nav_compiled_profile,
                "legacy": nav_legacy_profile,
            },
        }

        _print_summary(results)
        if args.json_out:
            with open(os.path.abspath(args.json_out), "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=True)
        return 0
    finally:
        for path in (route_scenario_path, landing_scenario_path):
            if path:
                try:
                    os.unlink(path)
                except OSError:
                    pass


if __name__ == "__main__":
    raise SystemExit(main())
