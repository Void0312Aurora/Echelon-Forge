from __future__ import annotations

import copy
import math
import os
from typing import Any

from python.runtime_bootstrap import resolve_repo_path

from ..common import _check_optional_range, _deep_merge, _materialize_scenario_path, _wrap_deg

def _compare_kernel_summary_values(
    expected_value: Any,
    actual_value: Any,
    *,
    key: str,
    abs_tol: float,
    rel_tol: float,
) -> str | None:
    if isinstance(expected_value, bool) or isinstance(actual_value, bool):
        if bool(expected_value) != bool(actual_value):
            return f"{key}: {actual_value!r} != {expected_value!r}"
        return None
    if isinstance(expected_value, (int, float)) and isinstance(actual_value, (int, float)):
        if not math.isclose(float(actual_value), float(expected_value), rel_tol=rel_tol, abs_tol=abs_tol):
            return f"{key}: {actual_value!r} != {expected_value!r}"
        return None
    if actual_value != expected_value:
        return f"{key}: {actual_value!r} != {expected_value!r}"
    return None

def _run_kernel_flight_contract(kernel_spec: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
    import numpy as np
    import ef_py
    from gym_envs.scenario_loader import ScenarioLoader
    from gym_envs.universal_env import half_to_unit

    controller_kind = str(kernel_spec.get("controller_kind", "")).strip().lower()
    scenario_path = resolve_repo_path(str(kernel_spec["scenario"]))
    seed = int(kernel_spec.get("seed", 0))
    checks = dict(kernel_spec.get("checks", {}) or {})

    sim = ef_py.SimulationKernel()
    sim.load_database(resolve_repo_path("examples", "config", "database"))
    loader = ScenarioLoader(sim)
    randomization_overrides = dict(kernel_spec.get("randomization_overrides", {}) or {})
    if randomization_overrides:
        loader.set_randomization_overrides(randomization_overrides)
    agent_id = loader.load_scenario(scenario_path, seed=seed)
    if agent_id is None:
        return False, "scenario did not spawn an agent", {}

    def _finite(x: float) -> bool:
        try:
            return math.isfinite(float(x))
        except Exception:
            return False

    def _base_pilot_action():
        pa = ef_py.PilotAction()
        pa.active = True
        pa.stick_pitch = 0.0
        pa.stick_roll = 0.0
        pa.rudder = 0.0
        pa.throttle = 0.0
        pa.gear_handle = 0.0
        pa.flaps = 0.0
        pa.speedbrake = 0.0
        pa.brake = 0.0
        pa.brake_left = False
        pa.brake_right = False
        pa.radar_active = False
        pa.radar_scan_az = 0.0
        pa.radar_scan_el = 0.0
        pa.tms_up = False
        pa.master_arm = False
        pa.fire_weapon = False
        pa.fire_gun = False
        pa.weapon_select_id = 0
        pa.program_chaff = False
        pa.program_flare = False
        pa.jettison_emergency = False
        return pa

    def _summary(extra: dict[str, Any] | None = None) -> dict[str, Any]:
        inst = sim.get_instrument_state(agent_id)
        truth = sim.get_agent_observation(agent_id)
        pos = sim.get_unit_position(agent_id)
        vel = sim.get_unit_velocity(agent_id)
        out: dict[str, Any] = {
            "controller_kind": controller_kind,
            "seed": seed,
            "alt_baro_m": float(inst.alt_baro),
            "ias_mps": float(inst.ias),
            "vvi_mps": float(inst.vvi),
            "pitch_deg": float(inst.pitch),
            "roll_deg": float(inst.roll),
            "heading_deg": float(inst.heading),
            "aoa_deg": float(inst.aoa),
            "beta_deg": float(inst.beta),
            "q_deg_s": float(inst.q),
            "r_deg_s": float(inst.r),
            "g_load": float(inst.g_load),
            "ground_speed_mps": float(inst.ground_speed),
            "ground_track_deg": float(inst.ground_track),
            "wind_speed_mps": float(inst.wind_speed),
            "wind_dir_deg": float(inst.wind_dir),
            "track_heading_delta_deg": _wrap_deg(float(inst.ground_track) - float(inst.heading)),
            "truth_health": float(truth.health),
            "truth_x_m": float(pos[0]),
            "truth_y_m": float(pos[1]),
            "truth_z_m": float(pos[2]),
            "truth_vx_mps": float(vel[0]),
            "truth_vy_mps": float(vel[1]),
            "truth_vz_mps": float(vel[2]),
        }
        if extra:
            out.update(dict(extra))
        return out

    if controller_kind == "midpoint_env_action":
        action_dim = int(kernel_spec.get("action_dim", 17))
        action = np.zeros((action_dim,), dtype=np.float32)
        for idx in list(kernel_spec.get("midpoint_indices", []) or []):
            if 0 <= int(idx) < action_dim:
                action[int(idx)] = 0.5
        max_steps = int(kernel_spec.get("max_steps", 200))
        for _ in range(max_steps):
            pa = _base_pilot_action()
            pa.stick_pitch = float(action[0])
            pa.stick_roll = float(action[1])
            pa.rudder = float(action[2])
            pa.throttle = float(action[3])
            pa.gear_handle = float(action[4])
            pa.flaps = float(half_to_unit(float(action[5])))
            pa.speedbrake = float(half_to_unit(float(action[6])))
            pa.brake_left = False
            pa.brake_right = False
            pa.brake = float(half_to_unit(float(max(action[7], action[8]))))
            pa.radar_active = bool(action[9] > 0.5)
            pa.radar_scan_az = float(action[10]) * 60.0
            pa.radar_scan_el = float(action[11]) * 30.0
            pa.tms_up = bool(action[12] > 0.5)
            pa.master_arm = bool(action[13] > 0.5)
            pa.fire_weapon = bool(action[14] > 0.5)
            pa.fire_gun = bool(action[15] > 0.5)
            pa.weapon_select_id = int(action[16] * 7)
            sim.set_pilot_action(agent_id, pa)
            sim.step()
        inst = sim.get_instrument_state(agent_id)
        final_ias = float(inst.ias)
        final_ias_min = float(checks.get("final_ias_min", 5.0))
        if final_ias <= final_ias_min:
            return False, f"expected IAS > {final_ias_min:.1f}, got {final_ias:.3f}", _summary({"steps": max_steps})
        return True, f"kernel midpoint ground-roll contract passed with IAS={final_ias:.2f}", _summary({"steps": max_steps})

    if controller_kind == "manual_takeoff":
        target_pitch = float(kernel_spec.get("target_pitch_deg", 15.0))
        success_alt = float(checks.get("success_alt_min", 300.0))
        success_speed = float(checks.get("success_speed_min", 150.0))
        max_steps = int(kernel_spec.get("max_steps", 2000))
        for step in range(max_steps):
            inst = sim.get_instrument_state(agent_id)
            speed = float(inst.ias)
            alt = float(inst.alt_baro)
            pitch = float(inst.pitch)
            pa = _base_pilot_action()
            pa.stick_roll = 0.0
            pa.rudder = 0.0
            pa.throttle = 1.0
            pa.flaps = 0.0
            pa.speedbrake = 0.0
            pa.brake = 0.0
            pa.brake_left = False
            pa.brake_right = False
            if speed < float(kernel_spec.get("rotation_speed_mps", 100.0)):
                pa.stick_pitch = 0.0
            else:
                pa.stick_pitch = float(
                    np.clip(
                        (target_pitch - pitch) * float(kernel_spec.get("pitch_gain", 0.05)),
                        -1.0,
                        1.0,
                    )
                )
            pa.gear_handle = 0.0 if alt > float(kernel_spec.get("gear_up_alt_m", 30.0)) else 1.0
            sim.set_pilot_action(agent_id, pa)
            sim.step()
            if alt > success_alt and speed > success_speed:
                return True, f"kernel manual takeoff contract passed in {step + 1} steps", _summary({"steps": step + 1})
        return False, f"manual takeoff did not reach alt>{success_alt:.1f} and speed>{success_speed:.1f}", _summary({"steps": max_steps})

    if controller_kind == "stable_level_hold":
        dt = float(sim.get_time_step())
        if dt <= 0.0:
            return False, f"invalid sim time step {dt}", {}
        inst0 = sim.get_instrument_state(agent_id)
        alt_ref = float(inst0.alt_baro)
        ias_ref = float(inst0.ias)
        pa = _base_pilot_action()
        pa.rudder = 0.0
        pa.gear_handle = 0.0
        pa.flaps = 0.0
        pa.speedbrake = 0.0
        pa.brake = 0.0
        pa.brake_left = False
        pa.brake_right = False
        thr = float(kernel_spec.get("initial_throttle", 0.6))
        alt_int = 0.0
        min_alt = float("inf")
        max_abs_roll = 0.0
        max_abs_pitch = 0.0
        max_abs_g = 0.0
        steps = int(round(float(kernel_spec.get("duration_s", 200.0)) / dt))
        for _ in range(steps):
            inst = sim.get_instrument_state(agent_id)
            truth = sim.get_agent_observation(agent_id)
            if float(truth.health) <= 0.0:
                return False, "aircraft crashed during level-flight stability test", _summary({"steps": steps})
            alt = float(inst.alt_baro)
            vvi = float(inst.vvi)
            ias = float(inst.ias)
            pitch = float(inst.pitch)
            roll = float(inst.roll)
            p = float(inst.p)
            q = float(inst.q)
            g_load = float(inst.g_load)
            for value in (alt, vvi, ias, pitch, roll, p, q, g_load):
                if not _finite(value):
                    return False, f"non-finite instrument value during stable flight: {value!r}", _summary({"steps": steps})
            min_alt = min(min_alt, alt)
            max_abs_roll = max(max_abs_roll, abs(roll))
            max_abs_pitch = max(max_abs_pitch, abs(pitch))
            max_abs_g = max(max_abs_g, abs(g_load))
            pa.stick_roll = float(np.clip(-0.03 * roll - 0.01 * p, -0.5, 0.5))
            alt_err = alt_ref - alt
            alt_int = float(np.clip(alt_int + alt_err * dt, -2000.0, 2000.0))
            pitch_tgt = float(np.clip(0.02 * alt_err + 0.0005 * alt_int - 0.06 * vvi, -15.0, 15.0))
            pa.stick_pitch = float(np.clip(0.08 * (pitch_tgt - pitch) - 0.015 * q, -1.0, 1.0))
            thr = float(np.clip(thr + 0.003 * (ias_ref - ias), 0.0, 1.0))
            pa.throttle = thr
            sim.set_pilot_action(agent_id, pa)
            sim.step()
        if min_alt <= float(checks.get("min_alt_min", 800.0)):
            return False, f"altitude dipped too low: min_alt={min_alt:.1f}m", _summary({"steps": steps, "min_alt_m": min_alt})
        if max_abs_roll >= float(checks.get("max_abs_roll_max", 10.0)):
            return False, f"excessive roll during level flight: {max_abs_roll:.1f}deg", _summary({"steps": steps, "max_abs_roll_deg": max_abs_roll})
        if max_abs_pitch >= float(checks.get("max_abs_pitch_max", 15.0)):
            return False, f"excessive pitch during level flight: {max_abs_pitch:.1f}deg", _summary({"steps": steps, "max_abs_pitch_deg": max_abs_pitch})
        if max_abs_g >= float(checks.get("max_abs_g_max", 3.0)):
            return False, f"excessive G-load during level flight: {max_abs_g:.2f}", _summary({"steps": steps, "max_abs_g": max_abs_g})
        return True, (
            "kernel stable level-flight contract passed "
            f"(min_alt={min_alt:.1f}, max_roll={max_abs_roll:.1f}, max_pitch={max_abs_pitch:.1f}, max_g={max_abs_g:.2f})"
        ), _summary(
            {
                "steps": steps,
                "min_alt_m": min_alt,
                "max_abs_roll_deg": max_abs_roll,
                "max_abs_pitch_deg": max_abs_pitch,
                "max_abs_g": max_abs_g,
            }
        )

    if controller_kind == "takeoff_then_stable_hold":
        dt = float(sim.get_time_step())
        if dt <= 0.0:
            return False, f"invalid sim time step {dt}", {}
        pa = _base_pilot_action()
        pa.flaps = 0.0
        pa.speedbrake = 0.0
        pa.brake = 0.0
        pa.brake_left = False
        pa.brake_right = False
        stage = "takeoff"
        thr = 1.0
        alt_ref = 0.0
        ias_ref = 0.0
        alt_int = 0.0
        stable_steps = 0
        min_alt_stable = float("inf")
        max_abs_roll = 0.0
        max_abs_pitch = 0.0
        max_steps = int(kernel_spec.get("max_steps", 2000))
        stable_entry_alt_min = float(checks.get("stable_entry_alt_min", 300.0))
        stable_entry_speed_min = float(checks.get("stable_entry_speed_min", 150.0))
        for _ in range(max_steps):
            inst = sim.get_instrument_state(agent_id)
            truth = sim.get_agent_observation(agent_id)
            if float(truth.health) <= 0.0:
                return False, "aircraft crashed during takeoff/stable-flight test", _summary({"steps": max_steps, "stage": stage})
            for value in (
                float(inst.alt_baro),
                float(inst.alt_radar),
                float(inst.ias),
                float(inst.vvi),
                float(inst.pitch),
                float(inst.roll),
                float(inst.p),
                float(inst.q),
                float(inst.g_load),
            ):
                if not _finite(value):
                    return False, f"non-finite instrument value: {value!r}", _summary({"steps": max_steps, "stage": stage})
            if stage == "takeoff":
                pa.throttle = 1.0
                pa.stick_roll = 0.0
                pa.rudder = 0.0
                if float(inst.ias) < float(kernel_spec.get("rotation_speed_mps", 100.0)):
                    pa.stick_pitch = 0.0
                else:
                    pitch_err = float(kernel_spec.get("target_takeoff_pitch_deg", 13.0)) - float(inst.pitch)
                    pa.stick_pitch = float(
                        np.clip(
                            pitch_err * float(kernel_spec.get("takeoff_pitch_gain", 0.05)),
                            -1.0,
                            1.0,
                        )
                    )
                pa.gear_handle = 0.0 if float(inst.alt_baro) > float(kernel_spec.get("gear_up_alt_m", 30.0)) else 1.0
                if float(inst.alt_baro) > stable_entry_alt_min and float(inst.ias) > stable_entry_speed_min:
                    stage = "stable"
                    alt_ref = float(inst.alt_baro)
                    ias_ref = float(inst.ias)
                    thr = float(pa.throttle)
                    alt_int = 0.0
                    stable_steps = 0
                    min_alt_stable = float("inf")
            else:
                stable_steps += 1
                alt = float(inst.alt_baro)
                vvi = float(inst.vvi)
                pitch = float(inst.pitch)
                roll = float(inst.roll)
                p = float(inst.p)
                q = float(inst.q)
                ias = float(inst.ias)
                min_alt_stable = min(min_alt_stable, alt)
                max_abs_roll = max(max_abs_roll, abs(roll))
                max_abs_pitch = max(max_abs_pitch, abs(pitch))
                pa.stick_roll = float(np.clip(-0.03 * roll - 0.01 * p, -0.6, 0.6))
                alt_err = alt_ref - alt
                alt_int = float(np.clip(alt_int + alt_err * dt, -2000.0, 2000.0))
                pitch_tgt = float(np.clip(0.02 * alt_err + 0.0005 * alt_int - 0.06 * vvi, -15.0, 15.0))
                pa.stick_pitch = float(np.clip(0.08 * (pitch_tgt - pitch) - 0.015 * q, -1.0, 1.0))
                thr = float(np.clip(thr + 0.003 * (ias_ref - ias), 0.0, 1.0))
                pa.throttle = thr
                pa.rudder = 0.0
                pa.gear_handle = 0.0
            sim.set_pilot_action(agent_id, pa)
            sim.step()
        if stage != "stable":
            return False, "did not reach stable flight phase within max_steps", _summary({"steps": max_steps, "stage": stage})
        stable_steps_min = int(round(float(checks.get("stable_steps_min_s", 40.0)) / dt))
        if stable_steps < stable_steps_min:
            return False, f"stable phase too short: {stable_steps} steps", _summary({"steps": max_steps, "stable_steps": stable_steps})
        if min_alt_stable <= float(checks.get("min_alt_stable_min", 150.0)):
            return False, (
                f"altitude dipped too low during stable flight: min_alt={min_alt_stable:.1f}m"
            ), _summary({"steps": max_steps, "stable_steps": stable_steps, "min_alt_stable_m": min_alt_stable})
        if max_abs_roll >= float(checks.get("max_abs_roll_max", 20.0)):
            return False, f"excessive roll in stable phase: {max_abs_roll:.1f}deg", _summary({"steps": max_steps, "stable_steps": stable_steps, "max_abs_roll_deg": max_abs_roll})
        if max_abs_pitch >= float(checks.get("max_abs_pitch_max", 20.0)):
            return False, f"excessive pitch in stable phase: {max_abs_pitch:.1f}deg", _summary({"steps": max_steps, "stable_steps": stable_steps, "max_abs_pitch_deg": max_abs_pitch})
        return True, (
            "kernel takeoff-then-stable contract passed "
            f"(stable_steps={stable_steps}, min_alt={min_alt_stable:.1f}, max_roll={max_abs_roll:.1f}, max_pitch={max_abs_pitch:.1f})"
        ), _summary(
            {
                "steps": max_steps,
                "stage": stage,
                "stable_steps": stable_steps,
                "min_alt_stable_m": min_alt_stable,
                "max_abs_roll_deg": max_abs_roll,
                "max_abs_pitch_deg": max_abs_pitch,
            }
        )

    if controller_kind == "pilot_pitch_sign_response":
        response_steps = int(kernel_spec.get("response_steps", 10))
        pa = _base_pilot_action()
        pa.stick_pitch = float(kernel_spec.get("stick_pitch", 0.5))
        pa.throttle = float(kernel_spec.get("throttle", 0.8))
        pa.gear_handle = float(kernel_spec.get("gear_handle", 0.0))
        for _ in range(response_steps):
            sim.set_pilot_action(agent_id, pa)
            sim.step()
        inst = sim.get_instrument_state(agent_id)
        pitch_min = float(checks.get("pitch_min_deg", 0.0))
        q_min = float(checks.get("q_min_deg_s", 0.0))
        aoa_min = float(checks.get("aoa_min_deg", 0.0))
        if float(inst.pitch) <= pitch_min:
            return False, f"expected pitch > {pitch_min:.3f}, got {float(inst.pitch):.6f}", _summary({"steps": response_steps})
        if float(inst.q) <= q_min:
            return False, f"expected q > {q_min:.3f}, got {float(inst.q):.6f}", _summary({"steps": response_steps})
        if float(inst.aoa) <= aoa_min:
            return False, f"expected AoA > {aoa_min:.3f}, got {float(inst.aoa):.6f}", _summary({"steps": response_steps})
        return True, "kernel pilot pitch-sign contract passed", _summary({"steps": response_steps})

    if controller_kind == "pitch_hold":
        dt = float(sim.get_time_step())
        if dt <= 0.0:
            return False, f"invalid sim time step {dt}", {}
        steps = int(kernel_spec.get("max_steps", max(1, int(round(float(kernel_spec.get("duration_s", 6.0)) / dt)))))
        target_pitch = float(kernel_spec.get("target_pitch_deg", 0.0))
        pitch_kp = float(kernel_spec.get("pitch_kp", 0.12))
        pitch_kd = float(kernel_spec.get("pitch_kd", 0.02))
        pa = _base_pilot_action()
        pa.stick_roll = float(kernel_spec.get("stick_roll", 0.0))
        pa.rudder = float(kernel_spec.get("rudder", 0.0))
        pa.throttle = float(kernel_spec.get("throttle", 0.5))
        pa.gear_handle = float(kernel_spec.get("gear_handle", 0.0))
        pa.flaps = float(kernel_spec.get("flaps", 0.0))
        pa.speedbrake = float(kernel_spec.get("speedbrake", 0.0))
        pa.brake = float(kernel_spec.get("brake", 0.0))
        pa.brake_left = bool(kernel_spec.get("brake_left", False))
        pa.brake_right = bool(kernel_spec.get("brake_right", False))
        min_alt = float("inf")
        max_abs_roll = 0.0
        max_abs_pitch_error = 0.0
        for _ in range(steps):
            inst = sim.get_instrument_state(agent_id)
            truth = sim.get_agent_observation(agent_id)
            if float(truth.health) <= 0.0:
                return False, "aircraft crashed during pitch-hold test", _summary({"steps": steps})
            alt = float(inst.alt_baro)
            pitch = float(inst.pitch)
            roll = float(inst.roll)
            q = float(inst.q)
            ias = float(inst.ias)
            vvi = float(inst.vvi)
            aoa = float(inst.aoa)
            for value in (alt, pitch, roll, q, ias, vvi, aoa):
                if not _finite(value):
                    return False, f"non-finite instrument value during pitch-hold test: {value!r}", _summary({"steps": steps})
            min_alt = min(min_alt, alt)
            max_abs_roll = max(max_abs_roll, abs(roll))
            max_abs_pitch_error = max(max_abs_pitch_error, abs(target_pitch - pitch))
            pa.stick_pitch = float(np.clip(pitch_kp * (target_pitch - pitch) - pitch_kd * q, -1.0, 1.0))
            sim.set_pilot_action(agent_id, pa)
            sim.step()
        final_inst = sim.get_instrument_state(agent_id)
        final_pitch_error = abs(target_pitch - float(final_inst.pitch))
        pitch_error_abs_max = checks.get("pitch_error_abs_max", None)
        if pitch_error_abs_max is not None and final_pitch_error > float(pitch_error_abs_max):
            return False, (
                f"pitch-hold final error too large: {final_pitch_error:.3f} > {float(pitch_error_abs_max):.3f}"
            ), _summary(
                {
                    "steps": steps,
                    "target_pitch_deg": target_pitch,
                    "final_pitch_error_deg": final_pitch_error,
                    "max_abs_pitch_error_deg": max_abs_pitch_error,
                    "min_alt_m": min_alt,
                    "max_abs_roll_deg": max_abs_roll,
                }
            )
        min_alt_min = checks.get("min_alt_min", None)
        if min_alt_min is not None and min_alt < float(min_alt_min):
            return False, f"pitch-hold altitude dipped too low: {min_alt:.3f} < {float(min_alt_min):.3f}", _summary(
                {
                    "steps": steps,
                    "target_pitch_deg": target_pitch,
                    "final_pitch_error_deg": final_pitch_error,
                    "max_abs_pitch_error_deg": max_abs_pitch_error,
                    "min_alt_m": min_alt,
                    "max_abs_roll_deg": max_abs_roll,
                }
            )
        max_abs_roll_max = checks.get("max_abs_roll_max", None)
        if max_abs_roll_max is not None and max_abs_roll > float(max_abs_roll_max):
            return False, f"pitch-hold roll excursion too large: {max_abs_roll:.3f} > {float(max_abs_roll_max):.3f}", _summary(
                {
                    "steps": steps,
                    "target_pitch_deg": target_pitch,
                    "final_pitch_error_deg": final_pitch_error,
                    "max_abs_pitch_error_deg": max_abs_pitch_error,
                    "min_alt_m": min_alt,
                    "max_abs_roll_deg": max_abs_roll,
                }
            )
        return True, (
            "kernel pitch-hold contract passed "
            f"(pitch={float(final_inst.pitch):.2f}, vvi={float(final_inst.vvi):.2f}, ias={float(final_inst.ias):.2f})"
        ), _summary(
            {
                "steps": steps,
                "target_pitch_deg": target_pitch,
                "final_pitch_error_deg": final_pitch_error,
                "max_abs_pitch_error_deg": max_abs_pitch_error,
                "min_alt_m": min_alt,
                "max_abs_roll_deg": max_abs_roll,
            }
        )

    if controller_kind == "heading_hold_pitch":
        dt = float(sim.get_time_step())
        if dt <= 0.0:
            return False, f"invalid sim time step {dt}", {}
        steps = int(kernel_spec.get("max_steps", max(1, int(round(float(kernel_spec.get("duration_s", 6.0)) / dt)))))
        inst0 = sim.get_instrument_state(agent_id)
        target_heading = float(kernel_spec.get("target_heading_deg", float(inst0.heading)))
        target_pitch = float(kernel_spec.get("target_pitch_deg", 0.0))
        heading_kp = float(kernel_spec.get("heading_kp", 0.12))
        roll_kp = float(kernel_spec.get("roll_kp", 0.05))
        roll_rate_kd = float(kernel_spec.get("roll_rate_kd", 0.01))
        pitch_kp = float(kernel_spec.get("pitch_kp", 0.16))
        pitch_kd = float(kernel_spec.get("pitch_kd", 0.03))
        max_roll_cmd = float(kernel_spec.get("max_roll_cmd", 0.7))
        pa = _base_pilot_action()
        pa.rudder = float(kernel_spec.get("rudder", 0.0))
        pa.throttle = float(kernel_spec.get("throttle", 0.6))
        pa.gear_handle = float(kernel_spec.get("gear_handle", 0.0))
        pa.flaps = float(kernel_spec.get("flaps", 0.0))
        pa.speedbrake = float(kernel_spec.get("speedbrake", 0.0))
        pa.brake = float(kernel_spec.get("brake", 0.0))
        pa.brake_left = bool(kernel_spec.get("brake_left", False))
        pa.brake_right = bool(kernel_spec.get("brake_right", False))
        max_abs_heading_error = 0.0
        max_abs_pitch_error = 0.0
        max_abs_roll = 0.0
        min_alt = float("inf")
        for _ in range(steps):
            inst = sim.get_instrument_state(agent_id)
            truth = sim.get_agent_observation(agent_id)
            if float(truth.health) <= 0.0:
                return False, "aircraft crashed during heading/pitch-hold test", _summary({"steps": steps})
            alt = float(inst.alt_baro)
            heading = float(inst.heading)
            pitch = float(inst.pitch)
            roll = float(inst.roll)
            p = float(inst.p)
            q = float(inst.q)
            ias = float(inst.ias)
            vvi = float(inst.vvi)
            for value in (alt, heading, pitch, roll, p, q, ias, vvi):
                if not _finite(value):
                    return False, f"non-finite instrument value during heading/pitch-hold test: {value!r}", _summary({"steps": steps})
            heading_error = _wrap_deg(target_heading - heading)
            max_abs_heading_error = max(max_abs_heading_error, abs(heading_error))
            max_abs_pitch_error = max(max_abs_pitch_error, abs(target_pitch - pitch))
            max_abs_roll = max(max_abs_roll, abs(roll))
            min_alt = min(min_alt, alt)
            pa.stick_roll = float(
                np.clip(heading_kp * heading_error - roll_kp * roll - roll_rate_kd * p, -max_roll_cmd, max_roll_cmd)
            )
            pa.stick_pitch = float(np.clip(pitch_kp * (target_pitch - pitch) - pitch_kd * q, -1.0, 1.0))
            sim.set_pilot_action(agent_id, pa)
            sim.step()
        final_inst = sim.get_instrument_state(agent_id)
        final_heading_error = abs(_wrap_deg(target_heading - float(final_inst.heading)))
        final_pitch_error = abs(target_pitch - float(final_inst.pitch))
        heading_error_abs_max = checks.get("heading_error_abs_max", None)
        if heading_error_abs_max is not None and final_heading_error > float(heading_error_abs_max):
            return False, (
                f"heading-hold final error too large: {final_heading_error:.3f} > {float(heading_error_abs_max):.3f}"
            ), _summary(
                {
                    "steps": steps,
                    "target_heading_deg": target_heading,
                    "target_pitch_deg": target_pitch,
                    "final_heading_error_deg": final_heading_error,
                    "final_pitch_error_deg": final_pitch_error,
                    "max_abs_heading_error_deg": max_abs_heading_error,
                    "max_abs_pitch_error_deg": max_abs_pitch_error,
                    "max_abs_roll_deg": max_abs_roll,
                    "min_alt_m": min_alt,
                }
            )
        pitch_error_abs_max = checks.get("pitch_error_abs_max", None)
        if pitch_error_abs_max is not None and final_pitch_error > float(pitch_error_abs_max):
            return False, (
                f"heading-hold pitch error too large: {final_pitch_error:.3f} > {float(pitch_error_abs_max):.3f}"
            ), _summary(
                {
                    "steps": steps,
                    "target_heading_deg": target_heading,
                    "target_pitch_deg": target_pitch,
                    "final_heading_error_deg": final_heading_error,
                    "final_pitch_error_deg": final_pitch_error,
                    "max_abs_heading_error_deg": max_abs_heading_error,
                    "max_abs_pitch_error_deg": max_abs_pitch_error,
                    "max_abs_roll_deg": max_abs_roll,
                    "min_alt_m": min_alt,
                }
            )
        max_abs_roll_max = checks.get("max_abs_roll_max", None)
        if max_abs_roll_max is not None and max_abs_roll > float(max_abs_roll_max):
            return False, (
                f"heading-hold roll excursion too large: {max_abs_roll:.3f} > {float(max_abs_roll_max):.3f}"
            ), _summary(
                {
                    "steps": steps,
                    "target_heading_deg": target_heading,
                    "target_pitch_deg": target_pitch,
                    "final_heading_error_deg": final_heading_error,
                    "final_pitch_error_deg": final_pitch_error,
                    "max_abs_heading_error_deg": max_abs_heading_error,
                    "max_abs_pitch_error_deg": max_abs_pitch_error,
                    "max_abs_roll_deg": max_abs_roll,
                    "min_alt_m": min_alt,
                }
            )
        return True, (
            "kernel heading/pitch-hold contract passed "
            f"(heading={float(final_inst.heading):.2f}, track={float(final_inst.ground_track):.2f}, "
            f"track-heading={_wrap_deg(float(final_inst.ground_track) - float(final_inst.heading)):.2f})"
        ), _summary(
            {
                "steps": steps,
                "target_heading_deg": target_heading,
                "target_pitch_deg": target_pitch,
                "final_heading_error_deg": final_heading_error,
                "final_pitch_error_deg": final_pitch_error,
                "max_abs_heading_error_deg": max_abs_heading_error,
                "max_abs_pitch_error_deg": max_abs_pitch_error,
                "max_abs_roll_deg": max_abs_roll,
                "min_alt_m": min_alt,
            }
        )

    if controller_kind == "free_fall_idle":
        dt = float(sim.get_time_step())
        if dt <= 0.0:
            return False, f"invalid sim time step {dt}", {}
        max_steps = int(kernel_spec.get("max_steps", 20))
        initial_pos = sim.get_unit_position(agent_id)
        initial_vel = sim.get_unit_velocity(agent_id)
        pa = _base_pilot_action()
        pa.throttle = float(kernel_spec.get("throttle", 0.0))
        pa.gear_handle = float(kernel_spec.get("gear_handle", 1.0))
        for _ in range(max_steps):
            sim.set_pilot_action(agent_id, pa)
            sim.step()
        final_pos = sim.get_unit_position(agent_id)
        final_vel = sim.get_unit_velocity(agent_id)
        elapsed_s = max(1.0e-9, max_steps * dt)
        mean_vertical_accel = (float(final_vel[2]) - float(initial_vel[2])) / elapsed_s
        accel_range = list(checks.get("mean_vertical_accel_range", [-10.8, -8.8]))
        if len(accel_range) >= 2:
            accel_lo = float(accel_range[0])
            accel_hi = float(accel_range[1])
            if not (accel_lo <= mean_vertical_accel <= accel_hi):
                return False, (
                    f"mean vertical accel out of range: {mean_vertical_accel:.3f} "
                    f"not in [{accel_lo:.3f}, {accel_hi:.3f}]"
                ), _summary({"steps": max_steps, "mean_vertical_accel_mps2": mean_vertical_accel})
        final_alt_max = checks.get("final_alt_max", None)
        if final_alt_max is not None and float(final_pos[2]) > float(final_alt_max):
            return False, (
                f"expected final altitude <= {float(final_alt_max):.3f}, got {float(final_pos[2]):.6f}"
            ), _summary({"steps": max_steps, "mean_vertical_accel_mps2": mean_vertical_accel})
        final_vz_max = checks.get("final_vz_max", None)
        if final_vz_max is not None and float(final_vel[2]) > float(final_vz_max):
            return False, (
                f"expected final vz <= {float(final_vz_max):.3f}, got {float(final_vel[2]):.6f}"
            ), _summary({"steps": max_steps, "mean_vertical_accel_mps2": mean_vertical_accel})
        return True, "kernel free-fall contract passed", _summary(
            {
                "steps": max_steps,
                "mean_vertical_accel_mps2": mean_vertical_accel,
                "initial_alt_m": float(initial_pos[2]),
                "initial_vz_mps": float(initial_vel[2]),
            }
        )

    raise ValueError(f"Unknown kernel_flight controller_kind: {controller_kind}")


def run_kernel_contract(check_kind: str, spec: dict[str, Any]) -> tuple[bool, str] | None:
    if check_kind == "kernel_flight_regression":
        ok, message, _summary = _run_kernel_flight_contract(spec)
        return ok, message

    if check_kind == "kernel_flight_repeatability":
        repeat_runs = max(2, int(spec.get("repeat_runs", 2)))
        abs_tol = float(spec.get("float_abs_tol", 1.0e-6))
        rel_tol = float(spec.get("float_rel_tol", 1.0e-6))
        compare_keys = [str(x) for x in list(spec.get("compare_keys", []) or [])]
        baseline_summary: dict[str, Any] | None = None
        for run_idx in range(repeat_runs):
            ok, message, summary = _run_kernel_flight_contract(spec)
            if not ok:
                return False, f"repeat run {run_idx + 1} failed: {message}"
            if baseline_summary is None:
                baseline_summary = dict(summary)
                if not compare_keys:
                    compare_keys = sorted(baseline_summary.keys())
                continue
            for key in compare_keys:
                mismatch = _compare_kernel_summary_values(
                    baseline_summary.get(key),
                    summary.get(key),
                    key=key,
                    abs_tol=abs_tol,
                    rel_tol=rel_tol,
                )
                if mismatch is not None:
                    return False, f"repeatability mismatch on run {run_idx + 1}: {mismatch}"
        return True, f"kernel flight repeatability contract passed for {repeat_runs} run(s)"

    if check_kind == "kernel_flight_parameter_scan":
        cases = list(spec.get("cases", []) or [])
        if not cases:
            raise ValueError("kernel_flight_parameter_scan requires non-empty 'cases'")

        def _resolve_case_spec(case_spec: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
            resolved = copy.deepcopy(case_spec)
            cleanup_paths: list[str] = []
            if (
                "scenario" not in resolved
                and ("scenario_base" in resolved or "scenario_inline" in resolved)
            ):
                scenario_path, should_cleanup = _materialize_scenario_path(resolved)
                resolved["scenario"] = scenario_path
                resolved.pop("scenario_base", None)
                resolved.pop("scenario_patch", None)
                resolved.pop("scenario_inline", None)
                if should_cleanup:
                    cleanup_paths.append(scenario_path)
            return resolved, cleanup_paths

        base_case_spec = copy.deepcopy(spec)
        for key in ("cases", "ordered_field_checks", "case_field_checks"):
            base_case_spec.pop(key, None)
        base_case_spec["check_kind"] = "kernel_flight_regression"

        case_summaries: dict[str, dict[str, Any]] = {}
        for idx, raw_case in enumerate(cases):
            if not isinstance(raw_case, dict):
                raise ValueError("kernel_flight_parameter_scan cases must be JSON objects")
            case_name = str(raw_case.get("name", f"case_{idx + 1}"))
            case_overrides = raw_case.get("spec", raw_case.get("overrides", None))
            if case_overrides is None:
                case_overrides = {k: copy.deepcopy(v) for k, v in raw_case.items() if k != "name"}
            if not isinstance(case_overrides, dict):
                raise ValueError(f"kernel_flight_parameter_scan case {case_name!r} overrides must be a JSON object")
            merged_case_spec = _deep_merge(base_case_spec, case_overrides)
            merged_case_spec.pop("name", None)
            run_case_spec, cleanup_paths = _resolve_case_spec(merged_case_spec)
            try:
                ok, message, summary = _run_kernel_flight_contract(run_case_spec)
            finally:
                for cleanup_path in cleanup_paths:
                    try:
                        os.unlink(cleanup_path)
                    except OSError:
                        pass
            if not ok:
                return False, f"scan case {case_name} failed: {message}"
            case_summaries[case_name] = dict(summary)

        for raw_check in list(spec.get("case_field_checks", []) or []):
            if not isinstance(raw_check, dict):
                raise ValueError("kernel_flight_parameter_scan case_field_checks entries must be JSON objects")
            case_name = str(raw_check["case"])
            field_name = str(raw_check["field"])
            if case_name not in case_summaries:
                return False, f"unknown scan case in case_field_checks: {case_name!r}"
            if field_name not in case_summaries[case_name]:
                return False, f"scan case {case_name!r} missing summary field {field_name!r}"
            err = _check_optional_range(
                float(case_summaries[case_name][field_name]),
                raw_check,
                label=f"{case_name}.{field_name}",
            )
            if err is not None:
                return False, err

        for raw_check in list(spec.get("ordered_field_checks", []) or []):
            if not isinstance(raw_check, dict):
                raise ValueError("kernel_flight_parameter_scan ordered_field_checks entries must be JSON objects")
            field_name = str(raw_check["field"])
            case_order = [str(x) for x in list(raw_check.get("case_order", raw_check.get("order", [])) or [])]
            if len(case_order) < 2:
                raise ValueError("ordered_field_checks requires at least two case names")
            direction = str(raw_check.get("direction", "increasing")).strip().lower()
            min_delta = float(raw_check.get("min_delta", 0.0))
            for case_name in case_order:
                if case_name not in case_summaries:
                    return False, f"unknown scan case in ordered_field_checks: {case_name!r}"
                if field_name not in case_summaries[case_name]:
                    return False, f"scan case {case_name!r} missing summary field {field_name!r}"
            for prev_name, curr_name in zip(case_order[:-1], case_order[1:]):
                prev_value = float(case_summaries[prev_name][field_name])
                curr_value = float(case_summaries[curr_name][field_name])
                if direction == "increasing":
                    if (curr_value - prev_value) < min_delta:
                        return False, (
                            f"{field_name} was not increasing enough from {prev_name} to {curr_name}: "
                            f"{curr_value:.3f} - {prev_value:.3f} < {min_delta:.3f}"
                        )
                elif direction == "decreasing":
                    if (prev_value - curr_value) < min_delta:
                        return False, (
                            f"{field_name} was not decreasing enough from {prev_name} to {curr_name}: "
                            f"{prev_value:.3f} - {curr_value:.3f} < {min_delta:.3f}"
                        )
                else:
                    raise ValueError(f"unsupported ordered_field_checks direction: {direction!r}")

        return True, f"kernel flight parameter scan passed for {len(case_summaries)} case(s)"
    return None
