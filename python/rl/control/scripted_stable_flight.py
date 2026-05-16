from __future__ import annotations

import numpy as np
from .base_scripted_controller import BaseScriptedController, wrap_deg


class ScriptedStableFlightController(BaseScriptedController):
    """
    Realism-first scripted stable-flight controller.

    Uses only pilot-observable signals (instruments + mission command vector).
    Intended for:
      - collecting healthy offline datasets for world-model training
      - sanity-checking physics stability (airborne start)
    """

    def __init__(self, *, action_dim: int, dt: float = 0.05):
        super().__init__(action_dim=action_dim, dt=dt)
        self._alt_int = 0.0
        self._thr = 0.6
        self._alt_ref = None
        self._ias_ref = None
        self._hdg_ref = None
        self._cmd_code = 0

    def reset(self, obs: dict) -> None:
        inst, mission = self.instrument_and_mission(obs)
        if mission.size >= 4:
            self._cmd_code = int(mission[0])
            self._hdg_ref = float(mission[1])
            self._alt_ref = float(mission[2])
            self._ias_ref = float(mission[3])
        else:
            self._cmd_code = 0
            self._hdg_ref = float(inst[9]) if inst.size > 9 else 0.0
            self._alt_ref = float(inst[2]) if inst.size > 2 else 1000.0
            self._ias_ref = float(inst[0]) if inst.size > 0 else 200.0
        self._alt_int = 0.0
        self._thr = 0.6

    def step(self, obs: dict) -> np.ndarray:
        if self._alt_ref is None or self._ias_ref is None or self._hdg_ref is None:
            self.reset(obs)

        inst, mission = self.instrument_and_mission(obs)
        if mission.size >= 4:
            self._cmd_code = int(mission[0])
            self._hdg_ref = float(mission[1])
            self._alt_ref = float(mission[2])
            self._ias_ref = float(mission[3])

        ias = float(inst[0]) if inst.size > 0 else 0.0
        alt = float(inst[2]) if inst.size > 2 else 0.0
        vvi = float(inst[4]) if inst.size > 4 else 0.0
        beta = float(inst[6]) if inst.size > 6 else 0.0
        pitch = float(inst[7]) if inst.size > 7 else 0.0
        roll = float(inst[8]) if inst.size > 8 else 0.0
        hdg = float(inst[9]) if inst.size > 9 else 0.0
        gtrk = float(inst[30]) if inst.size > 30 else hdg
        p_rate = float(inst[12]) if inst.size > 12 else 0.0
        q_rate = float(inst[13]) if inst.size > 13 else 0.0
        r_rate = float(inst[14]) if inst.size > 14 else 0.0

        dt = self.effective_dt()

        # --- Lateral guidance ---
        # Default: heading hold toward the mission heading bug.
        #
        # For waypoint navigation (command_code==3), treat mission[1] as the desired *ground track*
        # (bearing-to-waypoint) and close the loop on ground track rather than heading. This avoids
        # systematic drift in wind and matches typical NAV/LNAV guidance behavior.
        cmd_code = int(getattr(self, "_cmd_code", 0) or 0)
        if cmd_code == 3:
            trk_err = wrap_deg(float(self._hdg_ref) - gtrk)
            bank_cmd = float(np.clip(0.80 * trk_err, -35.0, 35.0))
            stick_roll = float(np.clip(0.06 * (bank_cmd - roll) - 0.03 * p_rate, -0.9, 0.9))
            # PilotAction.rudder uses "positive = nose right". Positive beta / positive yaw rate in this sim
            # need a positive pedal command for damping; the previous sign created a positive-feedback yaw loop.
            rudder = float(np.clip(0.25 * beta + 0.06 * r_rate, -0.6, 0.6))
        else:
            hdg_err = wrap_deg(float(self._hdg_ref) - hdg)
            bank_cmd = float(np.clip(0.60 * hdg_err, -35.0, 35.0))
            stick_roll = float(np.clip(0.05 * (bank_cmd - roll) - 0.02 * p_rate, -0.8, 0.8))
            rudder = float(np.clip(0.20 * beta + 0.05 * r_rate, -0.5, 0.5))

        # --- Altitude hold -> pitch target (deg) ---
        # The sim uses a relatively high cruise speed by default; tighten altitude holding with
        # stronger PI terms and a bit more VVI damping.
        alt_err = float(self._alt_ref) - alt
        self._alt_int = float(np.clip(self._alt_int + alt_err * dt, -2000.0, 2000.0))
        pitch_tgt = float(np.clip(0.05 * alt_err + 0.0015 * self._alt_int - 0.08 * vvi, -20.0, 20.0))
        stick_pitch = float(np.clip(0.10 * (pitch_tgt - pitch) - 0.02 * q_rate, -1.0, 1.0))

        # Airspeed hold via throttle (slow integrator).
        spd_err = float(self._ias_ref) - ias
        self._thr = float(np.clip(self._thr + 0.0025 * spd_err, 0.0, 1.0))

        a = self.action_zeros()
        if self.action_dim == 2:
            a[0] = stick_pitch
            a[1] = self._thr
            return a

        if self.action_dim >= 4:
            a[0] = stick_pitch
            a[1] = stick_roll
            a[2] = rudder
            a[3] = self._thr

        # Full 17-dim action space: keep config/avionics in a safe, realistic baseline.
        if self.action_dim >= 5:
            a[4] = 0.0  # gear up
        if self.action_dim >= 6:
            a[5] = 0.5  # neutral (half_to_unit -> 0)
        if self.action_dim >= 7:
            overspeed_mps = float(ias - float(self._ias_ref))
            # Mixed takeoff-cruise-landing tasks can hand the stable-flight controller a jet that is still
            # carrying a large post-takeoff energy surplus. A small speedbrake schedule keeps turn radii
            # realistic enough for multileg LNAV recovery without affecting normal on-speed cruise behavior.
            if overspeed_mps > 40.0:
                a[6] = 1.0
            elif overspeed_mps > 20.0:
                a[6] = 0.75
            else:
                a[6] = 0.0
        if self.action_dim >= 9:
            a[7] = 0.0  # brakes off
            a[8] = 0.0

        return a


def scripted_stable_flight_action(obs: dict, *, action_dim: int) -> np.ndarray:
    """
    Stateless helper for compatibility with older call-sites.

    Prefer using ScriptedStableFlightController when you need consistent behavior over time.
    """
    ctrl = ScriptedStableFlightController(action_dim=int(action_dim))
    ctrl.reset(obs)
    return ctrl.step(obs)
