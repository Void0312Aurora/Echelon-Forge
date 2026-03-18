from __future__ import annotations

import numpy as np


def _wrap_deg(x: float) -> float:
    return (float(x) + 180.0) % 360.0 - 180.0


class ScriptedLandingController:
    """
    Simple instrument-style landing controller for straight-in ILS final.

    Uses only policy-observable quantities:
    - instrument state
    - mission command
    - appended ILS cues [ils_valid, loc_dev, gs_dev, dme_m]

    This is intentionally modest rather than "perfect". It is used as a safe
    baseline for residual RL so PPO does not have to rediscover basic approach
    geometry and landing configuration from scratch in the 17D full-action space.
    """

    def __init__(self, *, action_dim: int, dt: float = 0.05):
        self.action_dim = int(action_dim)
        self.dt = float(dt)
        self._thr = 0.45
        self._ias_ref = 82.0
        self._course_ref_deg = 0.0
        self._loc_int = 0.0
        self._prev_loc_dev: float | None = None

    def reset(self, obs: dict) -> None:
        mission = np.asarray(obs.get("mission", []), dtype=np.float32).reshape(-1)
        self._ias_ref = float(mission[3]) if mission.size >= 4 else 82.0
        self._course_ref_deg = float(mission[1]) if mission.size >= 2 else 0.0
        self._thr = 0.45
        self._loc_int = 0.0
        self._prev_loc_dev = None

    def step(self, obs: dict) -> np.ndarray:
        mission = np.asarray(obs.get("mission", []), dtype=np.float32).reshape(-1)
        inst = np.asarray(obs.get("instruments", []), dtype=np.float32).reshape(-1)
        if mission.size >= 4:
            self._ias_ref = float(mission[3])
        if mission.size >= 2:
            self._course_ref_deg = float(mission[1])

        ias = float(inst[0]) if inst.size > 0 else self._ias_ref
        alt_agl = float(inst[3]) if inst.size > 3 else 0.0
        vvi = float(inst[4]) if inst.size > 4 else 0.0
        aoa = float(inst[5]) if inst.size > 5 else 0.0
        beta = float(inst[6]) if inst.size > 6 else 0.0
        pitch = float(inst[7]) if inst.size > 7 else 0.0
        roll = float(inst[8]) if inst.size > 8 else 0.0
        heading = float(inst[9]) if inst.size > 9 else 0.0
        p_rate = float(inst[12]) if inst.size > 12 else 0.0
        q_rate = float(inst[13]) if inst.size > 13 else 0.0
        r_rate = float(inst[14]) if inst.size > 14 else 0.0
        ground_speed = float(inst[29]) if inst.size > 29 else ias
        if not np.isfinite(ground_speed) or ground_speed < 1.0:
            ground_speed = ias
        ground_track = float(inst[30]) if inst.size > 30 else heading
        if not np.isfinite(ground_track) or ias < 35.0:
            ground_track = heading

        ils_valid = float(inst[-4]) if inst.size >= 4 else 0.0
        loc_dev = float(inst[-3]) if inst.size >= 3 else 0.0
        gs_dev = float(inst[-2]) if inst.size >= 2 else 0.0
        dme_m = float(inst[-1]) if inst.size >= 1 else 0.0
        dt = self.dt if self.dt > 1.0e-6 else 0.05
        short_final_mode = bool(
            alt_agl <= 35.0
            or (np.isfinite(dme_m) and alt_agl <= 60.0 and dme_m < 1400.0)
        )
        centerline_hold_mode = bool(
            alt_agl <= 20.0
            or (np.isfinite(dme_m) and alt_agl <= 45.0 and dme_m < 1800.0)
        )
        pre_rollout_mode = bool(
            alt_agl <= 8.0
            or (np.isfinite(dme_m) and alt_agl <= 15.0 and dme_m < 700.0)
        )
        rollout_mode = bool(
            alt_agl <= 3.5
            or (np.isfinite(dme_m) and alt_agl <= 5.0 and dme_m < 420.0)
        )

        course_err = _wrap_deg(float(self._course_ref_deg) - ground_track)
        heading_err = _wrap_deg(float(self._course_ref_deg) - heading)

        # Localizer + course capture -> bank command.
        # We use the mission heading as the inbound course bug, and blend it with localizer
        # cues so the aircraft does not simply "chase the needle" and overshoot through the
        # centerline under wind/randomized initial geometry.
        if ils_valid > 0.5:
            leak = 0.8
            self._loc_int = float(self._loc_int) * max(0.0, 1.0 - leak * dt) + float(loc_dev) * dt
            self._loc_int = float(np.clip(self._loc_int, -0.35, 0.35))
            loc_rate = 0.0 if self._prev_loc_dev is None else (float(loc_dev) - float(self._prev_loc_dev)) / dt
            self._prev_loc_dev = float(loc_dev)

            loc_abs = abs(float(loc_dev))
            course_err_abs = abs(float(course_err))
            if loc_abs > 0.60:
                loc_gain = 24.0
                trk_gain = 0.25
                hdg_gain = 0.05
                bank_limit = 24.0
            elif loc_abs > 0.20:
                loc_gain = 18.0
                trk_gain = 0.45
                hdg_gain = 0.08
                bank_limit = 20.0
            else:
                loc_gain = 10.0
                trk_gain = 0.75
                hdg_gain = 0.10
                bank_limit = 14.0

            # Far from the threshold, the aircraft may already be near the localizer centerline while still
            # carrying a large course-angle error. Use a more assertive intercept so the baseline can rejoin
            # front-course capture during continuous mission handoffs instead of drifting through a shallow turn.
            intercept_mode = bool(np.isfinite(dme_m) and dme_m > 3500.0 and course_err_abs > 20.0)
            if intercept_mode:
                loc_gain = min(loc_gain, 8.0)
                trk_gain = max(trk_gain, 1.10)
                hdg_gain = max(hdg_gain, 0.18)
                bank_limit = max(bank_limit, 20.0 if course_err_abs < 40.0 else 24.0)

            if alt_agl < 120.0:
                bank_limit = min(bank_limit, 16.0 if loc_abs > 0.30 else 12.0)
            if alt_agl < 60.0:
                bank_limit = min(bank_limit, 10.0 if loc_abs < 0.25 else 14.0)
            if np.isfinite(dme_m) and dme_m < 2500.0:
                bank_limit = min(bank_limit, 12.0)
            if np.isfinite(dme_m) and dme_m < 600.0 and alt_agl < 20.0 and loc_abs > 0.08:
                bank_limit = max(bank_limit, 15.0)
            bank_cmd = (
                (-loc_gain * float(loc_dev))
                + (trk_gain * float(course_err))
                + (hdg_gain * float(heading_err))
                + (-4.0 * float(self._loc_int))
                + (-2.5 * float(loc_rate))
                + (-0.08 * float(r_rate))
            )
            if centerline_hold_mode:
                bank_limit = max(bank_limit, 13.0 if loc_abs > 0.08 else 10.0)
                bank_cmd += (-7.5 * float(loc_dev)) + (0.42 * float(course_err)) + (0.12 * float(heading_err))
            if pre_rollout_mode and (not rollout_mode):
                bank_limit = max(bank_limit, 15.0 if loc_abs > 0.10 else 11.5)
                bank_cmd += (-10.0 * float(loc_dev)) + (0.70 * float(course_err)) + (0.18 * float(heading_err))
            bank_cmd = float(np.clip(bank_cmd, -bank_limit, bank_limit))
            if (not intercept_mode) and loc_abs < 0.05 and abs(float(course_err)) < 1.5:
                bank_cmd = 0.0
        else:
            self._loc_int *= max(0.0, 1.0 - 2.0 * dt)
            self._prev_loc_dev = None
            bank_cmd = 0.0
        stick_roll = float(np.clip(0.075 * (bank_cmd - roll) - 0.030 * p_rate, -0.85, 0.85))

        # Glideslope + energy management -> pitch target.
        pitch_tgt = 0.0
        if ils_valid > 0.5:
            pitch_tgt += float(np.clip(-5.5 * gs_dev, -7.0, 7.0))
        pitch_tgt += float(np.clip(-0.10 * vvi, -5.0, 5.0))
        pitch_tgt += float(np.clip(0.14 * (ias - self._ias_ref), -5.0, 5.0))
        if alt_agl < 30.0:
            pitch_tgt += float(np.clip((30.0 - alt_agl) * 0.03, 0.0, 0.6))
        if alt_agl < 18.0:
            pitch_tgt += float(np.clip((18.0 - alt_agl) * 0.10, 0.0, 1.6))
        if alt_agl < 20.0 and ground_speed > 74.0:
            pitch_tgt -= float(np.clip((ground_speed - 74.0) * 0.10, 0.0, 2.8))
        if abs(aoa) > 13.0:
            pitch_tgt -= float(np.clip((abs(aoa) - 13.0) * 0.8, 0.0, 6.0))
        pitch_tgt = float(np.clip(pitch_tgt, -12.0, 10.0))
        stick_pitch = float(np.clip(0.10 * (pitch_tgt - pitch) - 0.02 * q_rate, -1.0, 1.0))

        rudder = float(np.clip(0.22 * beta + 0.06 * r_rate + 0.010 * course_err, -0.50, 0.50))
        if centerline_hold_mode and (not rollout_mode):
            rudder = float(np.clip(rudder + (-0.95 * float(loc_dev)) + 0.026 * course_err + 0.024 * heading_err, -0.95, 0.95))
        if short_final_mode and (not rollout_mode):
            rudder = float(np.clip(rudder + (-1.20 * float(loc_dev)) + 0.034 * heading_err + 0.024 * course_err, -1.0, 1.0))
        if rollout_mode:
            trk_err_rollout = _wrap_deg(float(ground_track) - float(self._course_ref_deg))
            yaw_err_rollout = _wrap_deg(float(heading) - float(self._course_ref_deg))
            bank_cmd_rollout = float(
                np.clip((-20.0 * float(loc_dev)) + (-1.00 * float(trk_err_rollout)) + (-0.20 * float(yaw_err_rollout)), -14.0, 14.0)
            )
            stick_roll = float(np.clip(0.11 * (bank_cmd_rollout - roll) - 0.040 * p_rate, -0.70, 0.70))
            pitch_hold_deg = -2.0 if ground_speed > 28.0 else (-0.8 if ground_speed > 10.0 else 0.0)
            stick_pitch = float(np.clip(0.12 * (pitch_hold_deg - pitch) - 0.035 * q_rate, -0.70, 0.12))
            rudder = float(
                np.clip(
                    (-0.34 * float(trk_err_rollout))
                    + (-0.16 * float(yaw_err_rollout))
                    + (-3.80 * float(loc_dev))
                    + (0.12 * float(r_rate)),
                    -1.0,
                    1.0,
                )
            )

        # Approach thrust law:
        # - keep a non-idle baseline on final
        # - add power when well below glideslope or sinking too fast
        # - still respect the target IAS instead of diving to recover speed
        target_ias = self._ias_ref
        if np.isfinite(dme_m) and dme_m > 5000.0 and alt_agl > 120.0:
            target_ias = max(target_ias, 88.0)
        elif alt_agl > 120.0:
            target_ias = max(target_ias, 84.0)
        elif np.isfinite(dme_m) and dme_m > 2500.0 and alt_agl > 80.0:
            target_ias = max(target_ias, 85.0)
        if np.isfinite(dme_m) and dme_m > 2500.0 and alt_agl > 80.0:
            gs_ref = 72.0 if dme_m > 5000.0 else 68.0
            if ground_speed < gs_ref:
                target_ias += float(np.clip((gs_ref - ground_speed) * 0.35, 0.0, 5.0))
        if short_final_mode:
            target_ias = min(target_ias, max(self._ias_ref, 80.0))
        if alt_agl < 25.0:
            target_ias = min(target_ias, 76.0)
        if pre_rollout_mode:
            target_ias = min(target_ias, 74.0)
        target_sink = 5.0 if alt_agl > 80.0 else (4.0 if alt_agl > 30.0 else 2.5)
        sink_excess = max((-float(vvi)) - target_sink, 0.0)
        gs_low = max(-float(gs_dev), 0.0)
        gs_high = max(float(gs_dev), 0.0)
        throttle_cmd = (
            0.24
            + 0.020 * (target_ias - ias)
            + 0.12 * gs_low
            - 0.06 * gs_high
            + 0.03 * sink_excess
        )
        if short_final_mode:
            throttle_cmd -= 0.05
        if pre_rollout_mode:
            throttle_cmd -= 0.10
        if alt_agl < 20.0:
            throttle_cmd -= 0.04 * min((20.0 - alt_agl) / 20.0, 1.0)
        min_thr = 0.0 if pre_rollout_mode else (0.12 if alt_agl < 20.0 else 0.18)
        throttle_cmd = float(np.clip(throttle_cmd, min_thr, 0.85))
        self._thr = float(np.clip(self._thr + 0.12 * (throttle_cmd - self._thr), min_thr, 0.85))
        if pre_rollout_mode:
            self._thr = 0.0

        a = np.zeros((int(self.action_dim),), dtype=np.float32)
        if self.action_dim >= 4:
            a[0] = stick_pitch
            a[1] = stick_roll
            a[2] = rudder
            a[3] = self._thr
        elif self.action_dim == 2:
            a[0] = stick_pitch
            a[1] = self._thr
            return a

        # Landing configuration.
        if self.action_dim >= 5:
            a[4] = 1.0  # gear down
        if self.action_dim >= 6:
            a[5] = 1.0  # full landing flaps in env action units
        if self.action_dim >= 7:
            a[6] = 1.0 if (short_final_mode or rollout_mode) else 0.0
        if self.action_dim >= 9:
            brake_cmd = 0.0
            if rollout_mode:
                if ground_speed > 4.0:
                    brake_cmd = 1.0
                else:
                    brake_cmd = 0.98
            a[7] = brake_cmd
            a[8] = brake_cmd

        return a


def scripted_landing_action(obs: dict, *, action_dim: int) -> np.ndarray:
    ctrl = ScriptedLandingController(action_dim=int(action_dim))
    ctrl.reset(obs)
    return ctrl.step(obs)
