from __future__ import annotations

import math

import numpy as np
from .base_scripted_controller import BaseScriptedController, wrap_deg


class ScriptedTakeoffController(BaseScriptedController):
    """
    Realism-first scripted takeoff controller (stateful).

    Key properties:
      - Uses only pilot-observable signals (ILS localizer, air data, inertial rates, EGI wind).
      - No privileged runway geometry/heading is exposed to the agent.
      - Includes a small integral term to learn a steady bias under crosswind (prevents one-sided drift).
    """

    def __init__(self, *, action_dim: int, dt: float = 0.05):
        super().__init__(action_dim=action_dim, dt=dt)
        self._loc_int = 0.0
        self._dep_trk_int = 0.0
        self._target_track_deg: float | None = None
        self._mission_track_deg: float | None = None
        self._takeoff_clearance_code: int = 0

    def reset(self, obs: dict | None = None) -> None:
        self._loc_int = 0.0
        self._dep_trk_int = 0.0
        self._target_track_deg = None
        self._mission_track_deg = None
        self._takeoff_clearance_code = 0
        if obs is not None:
            try:
                inst = self.obs_array(obs, "instruments")
                if inst.size >= 10:
                    # At runway lineup the aircraft heading matches runway direction. Storing this is not
                    # "god info" (it is pilot-observable) and helps enforce a straight ground track under wind.
                    self._target_track_deg = float(inst[9])
            except Exception:
                self._target_track_deg = None
            try:
                mission = self.obs_array(obs, "mission")
                if mission.size >= 2:
                    self._mission_track_deg = float(mission[1])
                if mission.size >= 16:
                    self._takeoff_clearance_code = int(round(float(mission[15])))
            except Exception:
                self._mission_track_deg = None

    def step(self, obs: dict) -> np.ndarray:
        inst, mission = self.instrument_and_mission(obs)
        ias = float(inst[0]) if inst.size >= 1 else 0.0
        alt_radar = float(inst[3]) if inst.size >= 4 else 0.0
        if mission.size >= 2:
            try:
                self._mission_track_deg = float(mission[1])
            except Exception:
                pass
        if mission.size >= 16:
            try:
                self._takeoff_clearance_code = int(round(float(mission[15])))
            except Exception:
                pass

        dt = self.effective_dt()

        # Initialize the runway/desired track the first time we see a valid heading, while clearly on ground.
        if self._target_track_deg is None and inst.size >= 10 and alt_radar < 5.0 and ias < 25.0:
            self._target_track_deg = float(inst[9])
        desired_track_deg = self._mission_track_deg
        if desired_track_deg is None:
            desired_track_deg = self._target_track_deg

        a = self.action_zeros()

        # Primary controls
        clearance_code = int(self._takeoff_clearance_code)
        cleared_for_roll = clearance_code in (0, 3, 4, 5)
        if self.action_dim == 2:
            a[1] = 1.0 if cleared_for_roll else 0.0
        elif self.action_dim >= 4:
            a[3] = 1.0 if cleared_for_roll else 0.0

        # Configuration (only available in the full 17-dim action space)
        if self.action_dim >= 6:
            # Takeoff flaps (mild): UniversalEnv maps via half_to_unit(), so 0.6 -> ~0.2 actual.
            a[5] = 0.6
        if self.action_dim >= 7:
            a[6] = 0.0  # speedbrake stowed
        if self.action_dim >= 9:
            brake_hold = 1.0 if not cleared_for_roll else 0.0
            a[7] = brake_hold
            a[8] = brake_hold
        if self.action_dim >= 5:
            # Gear: keep down on ground; retract after liftoff.
            a[4] = 1.0 if alt_radar < 20.0 else 0.0

        # Runway centerline assist via ILS localizer.
        # ILS is derived from scenario geometry (a real instrument), and does not leak runway heading directly.
        if self.action_dim >= 3 and inst.size >= 4:
            ils_valid = float(inst[-4])
            loc_dev = float(inst[-3])

            # Yaw rate (deg/s) is part of the instrument vector (p,q,r at indices 12,13,14).
            # Note: in this sim, +rudder increases heading, but yaw-rate `r` is negative for a right turn
            # (matches the internal dynamics sign). Keep this in mind when damping yaw.
            r_deg_s = float(inst[14]) if inst.size >= 15 else 0.0

            # Wind (EGI): used only for a small feed-forward aileron bias on the ground.
            wind_speed = float(inst[31]) if inst.size >= 33 else 0.0
            wind_from = float(inst[32]) if inst.size >= 33 else 0.0
            hdg = float(inst[9]) if inst.size >= 10 else 0.0
            ref_hdg = float(self._target_track_deg) if self._target_track_deg is not None else hdg
            rel = wrap_deg(wind_from - ref_hdg)
            cross_sign = float(math.sin(math.radians(rel)))  # +1 => wind from right of nose

            # Ground track hold:
            # Keep the *trajectory* aligned with the runway direction even under crosswind.
            # This matches real takeoff technique: the jet may crab (heading into wind) while the ground
            # track stays straight down the runway.
            trk_deg = float(inst[30]) if inst.size >= 31 else hdg
            # At (near) standstill, `ground_track` is often undefined and may read as 0.0,
            # which would produce a huge spurious error and saturate rudder/NWS.
            # Use heading as the proxy until the aircraft is clearly moving.
            if ias < 25.0:
                trk_deg = hdg
            trk_err = 0.0
            if self._target_track_deg is not None:
                trk_err = float(wrap_deg(trk_deg - float(self._target_track_deg)))

            # Only use ILS for *ground-run centerline tracking*.
            # After liftoff, pilots typically keep runway heading/track and do not chase the localizer needle
            # at very low altitude; in the sim this also prevents unrealistic post-liftoff rudder saturation.
            preliftoff = alt_radar < 5.0
            if ils_valid > 0.5 and preliftoff:
                # Leaky integral: only a small bias term; keep it tightly bounded to avoid overshoot.
                leak = 1.0  # 1/s
                self._loc_int = float(self._loc_int) * max(0.0, 1.0 - leak * dt) + float(loc_dev) * dt
                self._loc_int = float(np.clip(self._loc_int, -0.5, 0.5))

                # Primary: keep ground track aligned (responds early to weathercocking).
                if ias < 20.0:
                    k_trk = 0.075
                elif ias < 60.0:
                    k_trk = 0.065
                else:
                    k_trk = 0.055

                # Secondary: localizer for cross-track cleanup.
                k_loc = 1.4
                k_i = 0.4

                # Yaw-rate damping (deg/s -> rudder). r>0 is left yaw, so add +rudder to oppose it.
                k_r = 0.020

                # Wind feed-forward (very small): counter weathercocking.
                # cross_sign > 0 means wind from right, which tends to yaw right -> need left rudder.
                ff = -0.12 * cross_sign * float(np.clip(wind_speed / 12.0, -1.0, 1.0))

                rud_cmd = (-k_trk * trk_err) + (-k_loc * loc_dev) + (-k_i * self._loc_int) + (k_r * r_deg_s) + ff
                rud_lim = 1.0
                a[2] = float(np.clip(rud_cmd, -rud_lim, rud_lim))

                # Aileron into wind (common crosswind technique). Keep it mild.
                if self.action_dim >= 2 and alt_radar < 8.0:
                    roll_w = 0.15 * cross_sign * float(np.clip(wind_speed / 12.0, -1.0, 1.0))
                    roll_loc = float(np.clip(-0.25 * loc_dev, -0.25, 0.25))
                    a[1] = float(np.clip(roll_w + roll_loc, -0.30, 0.30))
            else:
                # If ILS is invalid or we're well airborne, bleed off integrator.
                self._loc_int *= max(0.0, 1.0 - 2.0 * dt)

            # Departure hold after liftoff: keep the runway/departure ground track until a safe climb height.
            if desired_track_deg is not None and 5.0 <= alt_radar < 150.0:
                trk_deg = float(inst[30]) if inst.size >= 31 else (float(inst[9]) if inst.size >= 10 else 0.0)
                if not np.isfinite(trk_deg):
                    trk_deg = float(inst[9]) if inst.size >= 10 else 0.0
                roll_deg = float(inst[8]) if inst.size >= 9 else 0.0
                hdg_deg = float(inst[9]) if inst.size >= 10 else trk_deg
                beta = float(inst[6]) if inst.size >= 7 else 0.0
                p_deg_s = float(inst[12]) if inst.size >= 13 else 0.0
                r_deg_s = float(inst[14]) if inst.size >= 15 else 0.0
                trk_err_air = float(wrap_deg(float(desired_track_deg) - trk_deg))
                hdg_err_air = float(wrap_deg(float(desired_track_deg) - hdg_deg))

                # Keep a bounded integral on track error to learn the crab bias required under crosswind/shear.
                leak = 0.35  # 1/s
                self._dep_trk_int = float(self._dep_trk_int) * max(0.0, 1.0 - leak * dt) + trk_err_air * dt
                self._dep_trk_int = float(np.clip(self._dep_trk_int, -12.0, 12.0))

                # Build a gentle bank command rather than trying to yaw the aircraft onto track.
                if alt_radar < 30.0:
                    bank_limit = 10.0
                elif alt_radar < 80.0:
                    bank_limit = 14.0
                else:
                    bank_limit = 18.0
                bank_cmd = float(
                    np.clip(
                        0.95 * trk_err_air + 0.10 * self._dep_trk_int + 0.08 * hdg_err_air,
                        -bank_limit,
                        bank_limit,
                    )
                )
                stick_roll = float(np.clip(0.065 * (bank_cmd - roll_deg) - 0.028 * p_deg_s, -0.40, 0.40))

                # Keep rudder mostly as coordination/yaw damping, with only a small track-error feedforward.
                rud_ff = 0.016 * trk_err_air + 0.006 * hdg_err_air + 0.010 * self._dep_trk_int
                rud_cmd = float(np.clip(rud_ff + 0.12 * beta + 0.08 * r_deg_s, -0.35, 0.35))

                if self.action_dim >= 4:
                    a[1] = stick_roll
                if self.action_dim >= 3:
                    a[2] = rud_cmd
            else:
                self._dep_trk_int *= max(0.0, 1.0 - 1.5 * dt)

        # Rotate/climb schedule (stick pitch)
        if self.action_dim >= 1:
            if not cleared_for_roll:
                a[0] = 0.0
                return a
            # Realistic rotation: begin pitching near Vr and aim to reach a higher AoA
            # (fighters typically rotate to ~10-13 deg AoA) rather than waiting for excessive speed.
            aoa = float(inst[5]) if inst.size >= 6 else 0.0
            if alt_radar > 25.0:
                a[0] = 0.10
            elif alt_radar > 5.0:
                # Early climb-out: reduce pitch to avoid ballooning while still building speed.
                a[0] = 0.14
            else:
                # Ground rotation schedule (smooth ramp around Vr).
                if ias < 65.0:
                    pitch_cmd = 0.0
                elif ias < 70.0:
                    pitch_cmd = 0.10
                elif ias < 80.0:
                    # Ramp to a stronger command for timely rotation.
                    t = (ias - 70.0) / 10.0
                    pitch_cmd = 0.10 + t * (0.35 - 0.10)
                else:
                    pitch_cmd = 0.35

                # AoA soft-cap (pilot-observable): avoid over-rotation / tailstrike-like behavior.
                if aoa > 12.0:
                    pitch_cmd = min(pitch_cmd, 0.10)
                if aoa > 14.0:
                    pitch_cmd = min(pitch_cmd, 0.05)

                a[0] = float(np.clip(pitch_cmd, 0.0, 0.45))

        return a


def scripted_takeoff_action(obs: dict, *, action_dim: int) -> np.ndarray:
    """
    Stateless helper for compatibility with older call-sites.

    For curriculum/DAgger collection you should prefer the stateful ScriptedTakeoffController.
    """
    ctrl = ScriptedTakeoffController(action_dim=int(action_dim))
    ctrl.reset(obs)
    return ctrl.step(obs)
