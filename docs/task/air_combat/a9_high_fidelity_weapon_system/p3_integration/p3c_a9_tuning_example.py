"""P3-C: A9 High-Fidelity Weapon System — tuning round-trip example.

Verifies all A9-specific MissileTuning fields survive
set_missile_tuning → get_missile_tuning round-trip.

Run: PYTHONPATH=build python <this_file>
"""

from __future__ import annotations

import os, sys

_repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
_build = os.path.join(_repo, "build")
sys.path.insert(0, _build)
sys.path.insert(0, _repo)

import ef_py

A9_FIELDS = {
    # G1 — APN Guidance
    "apn_target_accel_gain": 0.5,
    # G2 — Kalman Filter Seeker
    "use_kalman_seeker": True,
    # G3 — Three-Loop Autopilot
    "autopilot_order": 3,
    "autopilot_damping": 0.7,
    # G5 — Mach-Dependent Aerodynamics
    "mach_transonic_start": 0.80,
    "mach_transonic_end": 1.40,
    "cd0_power_on_ratio": 0.88,
}


def main():
    sim = ef_py.SimulationKernel()
    sim.reset(20260616)

    # Write A9 fields
    t = sim.get_missile_tuning()
    for field, value in A9_FIELDS.items():
        setattr(t, field, value)
    sim.set_missile_tuning(t)

    # Read back
    t2 = sim.get_missile_tuning()
    passed = 0
    for field, expected in A9_FIELDS.items():
        got = getattr(t2, field)
        ok = got == expected
        print(f"  {'✓' if ok else '✗'} {field}: set={expected} → got={got}")
        if ok:
            passed += 1

    print(f"\nP3-C: {passed}/{len(A9_FIELDS)} A9 fields round-trip {'PASS' if passed == len(A9_FIELDS) else 'PARTIAL'}")


if __name__ == "__main__":
    main()
