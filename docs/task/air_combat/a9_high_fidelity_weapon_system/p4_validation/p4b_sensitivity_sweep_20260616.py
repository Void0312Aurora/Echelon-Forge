"""P4-B: A9 parameter sensitivity sweep.

Varies nav_gain, autopilot_tau_s, and fuze trigger_radius across
a single engagement geometry, records miss distance.

Run: PYTHONPATH=build python <this_file>
Output: CSV to p4_validation/ directory.
"""

from __future__ import annotations

import csv, math, os, sys

_repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
_build = os.path.join(_repo, "build")
sys.path.insert(0, _build)
sys.path.insert(0, _repo)

import ef_py
from tests.runtime.air_combat.weapon_guidance_realism.helpers import (
    _make_kernel,
    _spawn_geometry_pair,
    _drive_missile_with_truth_track,
)

SWEEPS = {
    "nav_gain": [2.5, 3.0, 3.5, 4.0, 5.0],
    "autopilot_tau_s": [0.05, 0.08, 0.12, 0.20, 0.30],
    "apn_target_accel_gain": [0.0, 0.25, 0.5, 0.75, 1.0],
}

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "p4b_sensitivity_sweep_20260616.csv")


def _run_one(sim, geom, label):
    blue_id, red_id = _spawn_geometry_pair(sim, **geom)
    mid = int(sim.fire_missile(blue_id, red_id))
    if mid <= 0:
        return {"label": label, "miss_distance_m": float("nan")}
    result = _drive_missile_with_truth_track(sim, mid, red_id)
    return {"label": label, "miss_distance_m": float(result["truth_min_dist_m"])}


def main():
    base_geom = dict(red_x=8000, red_y=2000, red_heading=210, red_vx=-216, red_vy=-125)
    base_tuning = {
        "nav_gain": 3.5, "autopilot_tau_s": 0.10, "apn_target_accel_gain": 0.5,
    }
    rows = []

    for param, values in SWEEPS.items():
        for val in values:
            label = f"{param}={val}"
            sim = _make_kernel()
            t = sim.get_missile_tuning()
            for k, v in base_tuning.items():
                setattr(t, k, v)
            setattr(t, param, val)
            sim.set_missile_tuning(t)
            row = _run_one(sim, base_geom, label)
            row["param"] = param
            row["value"] = val
            rows.append(row)
            print(f"  {label}: miss={row['miss_distance_m']:.2f}m")

    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["label", "param", "value", "miss_distance_m"])
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {len(rows)} rows → {OUT}")

    # Summarize per-parameter range
    for param in SWEEPS:
        vals = [r["miss_distance_m"] for r in rows if r["param"] == param]
        if vals and all(math.isfinite(v) for v in vals):
            print(f"  {param}: range [{min(vals):.1f}, {max(vals):.1f}]m")


if __name__ == "__main__":
    main()
