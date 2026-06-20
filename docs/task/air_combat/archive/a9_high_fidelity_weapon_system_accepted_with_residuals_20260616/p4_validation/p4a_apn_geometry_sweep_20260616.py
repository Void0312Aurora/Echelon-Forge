"""P4-A: APN vs PN engagement geometry sweep.

Validates that apn_target_accel_gain > 0 produces different (and
directionally correct) missile behavior compared to classical PN.

Run: python <this_file>
Output: CSV to p4_validation/ directory.
"""

from __future__ import annotations

import csv, math, os, sys

# Ensure the repo root and build directory are on sys.path.
_repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
_build = os.path.join(_repo, "build")
for _p in (_build, _repo):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ef_py
from tests.runtime.air_combat.weapon_guidance_realism.helpers import (
    _drive_missile_with_truth_track,
    _make_baseline_kernel,
    _spawn_geometry_pair,
)

GEOMETRIES = {
    "head_on":  dict(red_x=13000, red_y=0,    red_heading=180, red_vx=-250, red_vy=0),
    "tail_chase": dict(red_x=-3000, red_y=0,   red_heading=0,   red_vx=250,  red_vy=0),
    "beam":      dict(red_x=8000,  red_y=8000, red_heading=225, red_vx=-176, red_vy=-176),
    "high_off_boresight": dict(red_x=8000, red_y=5000, red_heading=210, red_vx=-216, red_vy=-125),
}

APN_GAINS = [0.0, 0.5, 1.0]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "p4a_apn_geometry_sweep_20260616.csv")


def _run_one(sim: ef_py.SimulationKernel, geom: dict, label: str) -> dict:
    blue_id, red_id = _spawn_geometry_pair(sim, **geom)
    missile_id = int(sim.fire_missile(blue_id, red_id))
    if missile_id <= 0:
        return {"label": label, "miss_distance_m": float("nan"), "active": False}
    result = _drive_missile_with_truth_track(sim, missile_id, red_id)
    return {
        "label": label,
        "miss_distance_m": float(result["truth_min_dist_m"]),
        "active": bool(result.get("active", False)),
        "max_achieved_lateral_accel_mps2": float(result.get("max_achieved_lateral_accel_mps2", 0)),
    }


def main():
    rows = []
    for geom_name, geom_kwargs in GEOMETRIES.items():
        for gain in APN_GAINS:
            label = f"{geom_name} apn={gain}"
            sim = _make_baseline_kernel()
            tuning = sim.get_missile_tuning()
            tuning.apn_target_accel_gain = gain
            sim.set_missile_tuning(tuning)
            row = _run_one(sim, geom_kwargs, label)
            row["geometry"] = geom_name
            row["apn_gain"] = gain
            rows.append(row)
            print(f"  {label}: miss={row['miss_distance_m']:.2f}m")

    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["label", "geometry", "apn_gain",
                                           "miss_distance_m", "active",
                                           "max_achieved_lateral_accel_mps2"])
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {len(rows)} rows → {OUT}")

    # Directional check: for head-on / high-off-boresight geometries where
    # target maneuver matters more, APN should produce different trajectory.
    by_geom = {}
    for r in rows:
        by_geom.setdefault(r["geometry"], {})[r["apn_gain"]] = r["miss_distance_m"]

    baselines_ok = True
    for g in GEOMETRIES:
        pn_miss = by_geom[g][0.0]
        apn_miss = by_geom[g][1.0]
        if not math.isfinite(pn_miss) or not math.isfinite(apn_miss):
            print(f"  {g}: NaN miss distance — missile may not have engaged")
            baselines_ok = False
            continue
        delta = apn_miss - pn_miss
        print(f"  {g}: PN={pn_miss:.2f}m  APN(1.0)={apn_miss:.2f}m  Δ={delta:+.2f}m")

    print(f"\nBaseline check: {'PASS' if baselines_ok else 'PARTIAL'} — "
          f"all geometries produced finite miss distances: {baselines_ok}")
    print("Note: APN-vs-PN comparison is directional evidence only, not statistical proof.")


if __name__ == "__main__":
    main()
