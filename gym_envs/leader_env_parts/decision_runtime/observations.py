from __future__ import annotations

import math
from typing import Any

import numpy as np

from python.rl.control.mission_defs import COMMAND_CODE_LANDING, normalize_phase_name
from python.rl.tasking.bridge import task_observation_codes

from ..common import wrap_deg
from .commands import fuel_margin_state


def build_observation(env: Any) -> dict[str, np.ndarray]:
    loader = env.unwrapped.loader
    inst, truth = env._current_execution_runtime_state()
    if inst is None or truth is None:
        inst, truth = env._capture_execution_runtime_state()

    mission_nav = np.asarray(
        loader.get_mission_observation("nav_v2", truth=truth, inst=inst),
        dtype=np.float32,
    ).reshape(-1)
    ils = np.asarray(
        loader.get_ils_observation(
            float(getattr(truth, "x", 0.0)),
            float(getattr(truth, "y", 0.0)),
            float(getattr(inst, "alt_baro", 0.0)),
        ),
        dtype=np.float32,
    ).reshape(-1)

    report = getattr(loader, "pilot_report", None)
    task = getattr(loader, "task_order", None)
    phase_name = normalize_phase_name(getattr(loader, "mission_phase_name", ""))
    phase_id = float(getattr(getattr(loader, "leader_intent", None), "phase_id", 0))
    c2_task_id = float(getattr(loader, "c2_task_id", 0))

    valid_rf, along_m, cross_m, _rw_len, _rw_wid = loader.get_runway_local_frame(
        float(getattr(truth, "x", 0.0)),
        float(getattr(truth, "y", 0.0)),
    )
    runway_heading_err = 0.0
    try:
        beacon = loader._nearest_ils_beacon(
            float(getattr(truth, "x", 0.0)),
            float(getattr(truth, "y", 0.0)),
        )
        if beacon is not None:
            runway_heading_err = wrap_deg(
                float(getattr(inst, "heading", 0.0)) - float(beacon.get("heading", 0.0))
            )
    except Exception:
        runway_heading_err = 0.0

    ownship = np.asarray(
        [
            float(getattr(inst, "ias", 0.0)),
            float(getattr(inst, "ground_speed", 0.0)),
            float(getattr(inst, "alt_radar", 0.0)),
            float(getattr(inst, "alt_baro", 0.0)),
            float(getattr(inst, "vvi", 0.0)),
            float(getattr(inst, "heading", 0.0)),
            float(getattr(inst, "ground_track", 0.0)),
            float(getattr(inst, "roll", 0.0)),
            float(getattr(inst, "pitch", 0.0)),
            float(getattr(inst, "beta", 0.0)),
            float(getattr(inst, "r", 0.0)),
            float(getattr(inst, "gear_pos", 0.0)),
        ],
        dtype=np.float32,
    )

    anchor_dx = float(getattr(task, "anchor_x_m", 0.0) if task is not None else 0.0) - float(
        getattr(truth, "x", 0.0)
    )
    anchor_dy = float(getattr(task, "anchor_y_m", 0.0) if task is not None else 0.0) - float(
        getattr(truth, "y", 0.0)
    )
    anchor_dist_m = float(math.hypot(anchor_dx, anchor_dy))
    anchor_bearing_deg = (
        float((math.degrees(math.atan2(anchor_dx, anchor_dy)) + 360.0) % 360.0)
        if anchor_dist_m > 1.0e-6
        else 0.0
    )
    anchor_bearing_rel_deg = float(wrap_deg(anchor_bearing_deg - float(getattr(inst, "heading", 0.0))))

    _fuel_total_kg, fuel_margin_frac = fuel_margin_state(env, task, inst)
    task_primary_code, task_coordination_code, task_unit_code = task_observation_codes(
        task,
        fallback_phase_id=int(phase_id),
        loader=loader,
    )
    task_vec = np.asarray(
        [
            float(c2_task_id),
            float(task_primary_code),
            float(task_coordination_code),
            float(task_unit_code),
            float(loader.mission_cmd.get("target_altitude", 0.0)),
            float(loader.mission_cmd.get("target_speed", 0.0)),
            float(anchor_dist_m),
            float(anchor_bearing_rel_deg),
            float(
                max(
                    0.0,
                    float(getattr(task, "on_station_time_s", 0.0) if task is not None else 0.0)
                    - float(getattr(loader, "c2_on_station_elapsed_s", 0.0)),
                )
            ),
            float(fuel_margin_frac),
        ],
        dtype=np.float32,
    )

    if mission_nav.size >= 14:
        navigation = np.asarray(mission_nav[4:14], dtype=np.float32)
    else:
        navigation = np.asarray(
            np.pad(mission_nav[4:], (0, max(0, 10 - max(0, mission_nav.size - 4)))),
            dtype=np.float32,
        )
    if navigation.size != 10:
        navigation = np.resize(navigation, (10,)).astype(np.float32)

    terminal = np.asarray(
        [
            float(ils[3]) if ils.size >= 4 else 0.0,
            float(ils[1]) if ils.size >= 2 else 0.0,
            float(ils[2]) if ils.size >= 3 else 0.0,
            float(along_m if valid_rf else 0.0),
            float(cross_m if valid_rf else 0.0),
            float(runway_heading_err),
            1.0 if phase_name in {"approach_armed", "landing_final", "rollout"} else 0.0,
            1.0 if float(loader.mission_cmd.get("command_code", 0)) >= COMMAND_CODE_LANDING else 0.0,
        ],
        dtype=np.float32,
    )
    link = np.asarray(
        [
            float(getattr(report, "report_type", 0) if report is not None else 0.0),
            float(getattr(report, "status_value", 0.0) if report is not None else 0.0),
            float(
                max(
                    0.0,
                    getattr(env.unwrapped, "steps", 0) * float(env.unwrapped.sim.get_time_step())
                    - float(getattr(report, "timestamp_s", 0.0)),
                )
                if report is not None
                else 0.0
            ),
            float(fuel_margin_frac),
            float(getattr(inst, "missiles_remaining", 0.0)),
            float(1.0 if getattr(inst, "rwr_active", False) else 0.0),
        ],
        dtype=np.float32,
    )

    return {
        "ownship": np.nan_to_num(ownship, nan=0.0, posinf=0.0, neginf=0.0),
        "task": np.nan_to_num(task_vec, nan=0.0, posinf=0.0, neginf=0.0),
        "navigation": np.nan_to_num(navigation, nan=0.0, posinf=0.0, neginf=0.0),
        "terminal": np.nan_to_num(terminal, nan=0.0, posinf=0.0, neginf=0.0),
        "link": np.nan_to_num(link, nan=0.0, posinf=0.0, neginf=0.0),
    }
