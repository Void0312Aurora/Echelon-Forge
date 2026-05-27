from __future__ import annotations

import numpy as np

from python.rl.tasking.bridge import resolve_tasking_profile, tasking_profile_for_loader

from .common import ef_py

_NAVAL_INSTRUMENT_KEEP_INDICES = (
    8,   # roll/orientation sanity.
    9,   # heading.
    21,  # commanded heading.
    23,  # commanded speed.
    26,  # north velocity.
    27,  # east velocity.
    29,  # ground speed.
    30,  # ground track.
    31,  # wind speed.
    32,  # wind direction.
    34,  # GPS available.
    35,  # position uncertainty.
    36,  # threat/warning activity.
    37,  # abstract store count.
)


def naval_policy_instruments(inst_vec: np.ndarray) -> np.ndarray:
    flat = np.asarray(inst_vec, dtype=np.float32).reshape(-1)
    out = np.zeros_like(flat)
    for idx in _NAVAL_INSTRUMENT_KEEP_INDICES:
        if idx < flat.size:
            out[idx] = flat[idx]
    return out.reshape(np.asarray(inst_vec).shape)


def downsample_visual_mean(visual: np.ndarray, factor: int) -> np.ndarray:
    if factor <= 1:
        return visual.astype(np.float32, copy=False)
    h, w, c = visual.shape
    if h % factor != 0 or w % factor != 0:
        raise ValueError(f"visual shape {visual.shape} not divisible by downsample factor {factor}")
    nh, nw = h // factor, w // factor
    out = visual.reshape(nh, factor, nw, factor, c).mean(axis=(1, 3))
    return out.astype(np.float32, copy=False)


def build_universal_observation(
    loader,
    inst,
    truth,
    *,
    mission_obs_mode: str,
    max_contacts: int,
    max_rwr: int,
    include_proprio: bool,
    last_action,
    action_space,
    steps: int | None = None,
    max_steps: int | None = None,
):
    if hasattr(loader, "reset_runtime_eval_cache"):
        try:
            loader.reset_runtime_eval_cache()
        except Exception:
            pass
    ils_vec = loader.get_ils_observation(float(truth.x), float(truth.y), float(inst.alt_baro))
    compiled_obs_enabled = bool(getattr(loader, "use_compiled_execution_step_runtime", True)) and hasattr(
        ef_py, "compute_execution_observation_runtime_numpy"
    )
    if compiled_obs_enabled:
        inst_vec, contacts, rwr = ef_py.compute_execution_observation_runtime_numpy(
            inst,
            truth,
            float(ils_vec[0]) if len(ils_vec) > 0 else 0.0,
            float(ils_vec[1]) if len(ils_vec) > 1 else 0.0,
            float(ils_vec[2]) if len(ils_vec) > 2 else 0.0,
            float(ils_vec[3]) if len(ils_vec) > 3 else 0.0,
            int(max_contacts),
            int(max_rwr),
        )
        inst_vec = np.asarray(inst_vec, dtype=np.float32)
        contacts = np.asarray(contacts, dtype=np.float32).reshape(int(max_contacts), 5)
        rwr = np.asarray(rwr, dtype=np.float32).reshape(int(max_rwr), 4)
    else:
        inst_vec = np.array(
            [
                inst.ias,
                inst.mach,
                inst.alt_baro,
                inst.alt_radar,
                inst.vvi,
                inst.aoa,
                inst.beta,
                inst.pitch,
                inst.roll,
                inst.heading,
                inst.g_load,
                inst.g_load_axial,
                inst.p,
                inst.q,
                inst.r,
                inst.engine_rpm,
                inst.fuel_internal + inst.fuel_external,
                inst.fuel_flow,
                inst.gear_pos,
                inst.flaps_pos,
                inst.speedbrake_pos,
                inst.cmd_heading,
                inst.cmd_alt,
                inst.cmd_speed,
                getattr(inst, "lat", 0.0),
                getattr(inst, "lon", 0.0),
                getattr(inst, "vn", 0.0),
                getattr(inst, "ve", 0.0),
                getattr(inst, "vd", 0.0),
                getattr(inst, "ground_speed", 0.0),
                getattr(inst, "ground_track", 0.0),
                getattr(inst, "wind_speed", 0.0),
                getattr(inst, "wind_dir", 0.0),
                getattr(inst, "oat", 15.0),
                float(getattr(inst, "gps_available", True)),
                getattr(inst, "position_uncertainty", 10.0),
                float(getattr(inst, "rwr_active", False)),
                float(getattr(inst, "missiles_remaining", 0)),
            ],
            dtype=np.float64,
        )

        contacts = np.zeros((int(max_contacts), 5), dtype=np.float32)
        for i, track in enumerate(getattr(truth, "contacts", [])):
            if i >= int(max_contacts):
                break
            contacts[i] = [track.range, track.azimuth, track.elevation, track.closing_speed, track.time_since_update]

        rwr = np.zeros((int(max_rwr), 4), dtype=np.float32)
        for i, warning in enumerate(getattr(truth, "rwr_warnings", [])):
            if i >= int(max_rwr):
                break
            rwr[i] = [
                warning.bearing,
                warning.signal_strength,
                1.0 if warning.is_lock else 0.0,
                1.0 if warning.is_launch else 0.0,
            ]

        inst_vec = np.concatenate([inst_vec, ils_vec.astype(np.float64, copy=False)], axis=0)
        inst_vec = np.nan_to_num(inst_vec, nan=0.0, posinf=0.0, neginf=0.0)
        inst_vec = np.clip(inst_vec, -1.0e6, 1.0e6).astype(np.float32, copy=False)
    step_eval = None
    if steps is not None and max_steps is not None and hasattr(loader, "_prepare_step_evaluation"):
        try:
            step_eval = loader._prepare_step_evaluation(
                truth=truth,
                inst_obj=inst,
                inst_vec=inst_vec,
                ils_vec=np.asarray(ils_vec, dtype=np.float32),
                steps=int(steps),
                max_steps=int(max_steps),
                mission_obs_mode=mission_obs_mode,
            )
        except Exception:
            step_eval = None
    if isinstance(step_eval, dict):
        frame_products = step_eval.get("frame_products")
        if (
            not loader._python_owned_mission_observation_mode(mission_obs_mode)
            and frame_products is not None
            and bool(getattr(frame_products, "mission_observation_evaluated", False))
        ):
            miss_vec = np.asarray(frame_products.mission_observation.values, dtype=np.float32)
        else:
            miss_vec = loader.get_mission_observation(mission_obs_mode, truth=truth, inst=inst)
    else:
        miss_vec = loader.get_mission_observation(mission_obs_mode, truth=truth, inst=inst)

    policy_inst_vec = (
        naval_policy_instruments(inst_vec)
        if tasking_profile_for_loader(loader) is resolve_tasking_profile("naval")
        else inst_vec
    )
    obs = {
        "instruments": policy_inst_vec,
        "contacts": contacts,
        "rwr": rwr,
        "mission": miss_vec,
    }
    if include_proprio:
        if last_action is None:
            proprio = np.zeros((int(action_space.shape[0]),), dtype=np.float32)
        else:
            proprio = np.asarray(last_action, dtype=np.float32).reshape(-1)
        obs["proprio"] = proprio
    return obs


__all__ = ["build_universal_observation", "downsample_visual_mean", "naval_policy_instruments"]
