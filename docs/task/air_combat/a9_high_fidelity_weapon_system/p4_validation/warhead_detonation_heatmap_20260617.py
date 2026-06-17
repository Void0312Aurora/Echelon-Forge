"""A9 warhead detonation-point heatmap sweep.

This script compares generic synthetic warhead families across fixed local
detonation points around a structured F-16 target. It is a validation artifact
for directional behavior only: the profile values are not real-weapon
calibration and should not be read as Pk.

Run:
  PYTHONPATH=build python docs/task/air_combat/a9_high_fidelity_weapon_system/p4_validation/warhead_detonation_heatmap_20260617.py

Outputs:
  warhead_detonation_heatmap_20260617.csv
  warhead_detonation_heatmap_damage_horizontal_20260617.png
  warhead_detonation_heatmap_damage_vertical_20260617.png
  warhead_detonation_heatmap_mechanism_horizontal_20260617.png
  warhead_detonation_heatmap_mechanism_vertical_20260617.png
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


_REPO = Path(__file__).resolve().parents[5]
_BUILD = _REPO / "build"
for _path in (str(_BUILD), str(_REPO)):
  if _path not in sys.path:
    sys.path.insert(0, _path)

import ef_py  # noqa: E402
from tests.runtime.air_combat.weapon_guidance_realism.helpers import (  # noqa: E402
  _DB_PATH,
  _spawn_structured_f16_pair,
)


OUT_DIR = Path(__file__).resolve().parent
CSV_OUT = OUT_DIR / "warhead_detonation_heatmap_20260617.csv"
SEED = 20260617
MISSILE_VELOCITY = (900.0, -250.0, 0.0)
WARHEAD_FAMILIES = ("blast", "blast_fragmentation", "continuous_rod")
AXIS_VALUES = (-24.0, -18.0, -12.0, -6.0, 0.0, 6.0, 12.0, 18.0, 24.0)
SLICES = (
  {
    "name": "horizontal",
    "x_label": "local right offset (m)",
    "y_label": "local forward offset (m)",
    "point": lambda x, y: (y, x, 0.0),
    "figure_suffix": "horizontal",
  },
  {
    "name": "vertical",
    "x_label": "local up offset (m)",
    "y_label": "local forward offset (m)",
    "point": lambda x, y: (y, 0.0, x),
    "figure_suffix": "vertical",
  },
)

DAMAGE_METRICS = (
  ("system_damage", "system"),
  ("mission_damage", "mission"),
  ("mobility_damage", "mobility"),
  ("sensor_damage", "sensor"),
  ("survivability_damage", "survivability"),
  ("component_load_count", "loads"),
)
MECHANISM_METRICS = (
  ("mechanism_fragment_areal_density_per_m2", "fragment density /m2"),
  ("mechanism_blast_overpressure_kpa", "blast kPa"),
  ("mechanism_rod_cut_margin", "rod margin"),
  ("component_failure_count", "failures"),
)


def _make_profile(family: str) -> object:
  profile = ef_py.WarheadProfile()
  profile.family = family
  profile.mass_kg = 12.0
  profile.lethal_radius_m = 35.0
  profile.damage_scalar = 90.0
  profile.synthetic = True
  profile.damage_scalar_synthetic = True
  profile.provenance = "a9_heatmap_generic_research"
  return profile


def _parse_damage_delta(report: object) -> dict[str, float]:
  deltas: dict[str, float] = {
    "mission": 0.0,
    "mobility": 0.0,
    "sensor": 0.0,
    "survivability": 0.0,
  }
  for item in str(report.platform_damage_state_delta).split(","):
    if "=" not in item:
      continue
    key, value = item.split("=", 1)
    if key in deltas:
      deltas[key] = float(value)
  return deltas


def _component_keys(rows: list[object]) -> str:
  keys = [
    f"{str(row.component_name)}:{str(row.component_system)}"
    for row in rows
    if str(row.component_name) or str(row.component_system)
  ]
  return ";".join(keys)


def _run_case(
  *,
  family: str,
  slice_name: str,
  x_value: float,
  y_value: float,
  local: tuple[float, float, float],
) -> dict[str, object]:
  sim = ef_py.SimulationKernel()
  sim.reset(SEED)
  if not sim.load_database(_DB_PATH):
    raise RuntimeError(f"failed to load database: {_DB_PATH}")
  attacker_id, target_id = _spawn_structured_f16_pair(sim)

  ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
    attacker_id,
    target_id,
    float(local[0]),
    float(local[1]),
    float(local[2]),
    _make_profile(family),
    float(MISSILE_VELOCITY[0]),
    float(MISSILE_VELOCITY[1]),
    float(MISSILE_VELOCITY[2]),
  )
  if not ok:
    raise RuntimeError(f"debug detonation failed for {family} {slice_name} {local}")

  events = sim.export_recent_engagement_events()
  if len(events.effects_events) != 1 or len(events.damage_reports) != 1:
    raise RuntimeError(f"unexpected event count for {family} {slice_name} {local}")

  effects = events.effects_events[0]
  warhead = events.warhead_mechanism_events[0]
  report = events.damage_reports[0]
  component_loads = list(events.component_load_events)
  component_damages = list(events.component_damage_events)
  deltas = _parse_damage_delta(report)

  return {
    "slice": slice_name,
    "warhead_family": family,
    "x_axis_m": float(x_value),
    "y_axis_m": float(y_value),
    "local_forward_m": float(local[0]),
    "local_right_m": float(local[1]),
    "local_up_m": float(local[2]),
    "miss_distance_m": float(effects.miss_distance_m),
    "direct_hitbox_intersection": bool(effects.direct_hitbox_intersection),
    "projected_hitbox_count": int(effects.projected_hitbox_count),
    "component_hit_count": int(effects.component_hit_count),
    "component_load_count": len(component_loads),
    "component_failure_count": int(effects.component_failure_count),
    "component_damage_event_count": len(component_damages),
    "primary_component_name": str(effects.component_primary_name),
    "primary_component_system": str(effects.component_primary_system),
    "loaded_components": _component_keys(component_loads),
    "damaged_components": _component_keys(component_damages),
    "mechanism_fragment_energy_j": float(warhead.fragment_energy_j),
    "mechanism_fragment_areal_density_per_m2": float(warhead.fragment_density_per_m2),
    "mechanism_blast_overpressure_kpa": float(warhead.blast_overpressure_kpa),
    "mechanism_blast_impulse_kpa_ms": float(warhead.blast_impulse_kpa_ms),
    "mechanism_rod_cut_margin": float(warhead.rod_cut_margin),
    "spatial_energy_scale": float(effects.warhead_spatial_energy_scale),
    "spatial_pattern_scale": float(effects.warhead_spatial_pattern_scale),
    "system_damage": -float(report.system_health_delta),
    "mission_damage": -float(deltas["mission"]),
    "mobility_damage": -float(deltas["mobility"]),
    "sensor_damage": -float(deltas["sensor"]),
    "survivability_damage": -float(deltas["survivability"]),
    "destroyed": bool(report.destroyed),
    "loss_state_to": str(report.loss_state_to),
    "target_active": bool(sim.is_unit_active(target_id)),
  }


def _run_sweep() -> list[dict[str, object]]:
  rows: list[dict[str, object]] = []
  for slice_spec in SLICES:
    for family in WARHEAD_FAMILIES:
      for y_value in AXIS_VALUES:
        for x_value in AXIS_VALUES:
          local = slice_spec["point"](float(x_value), float(y_value))
          rows.append(
            _run_case(
              family=family,
              slice_name=str(slice_spec["name"]),
              x_value=float(x_value),
              y_value=float(y_value),
              local=local,
            )
          )
  return rows


def _write_csv(rows: list[dict[str, object]]) -> None:
  fieldnames = list(rows[0].keys())
  with CSV_OUT.open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)


def _grid(rows: list[dict[str, object]], family: str, slice_name: str, metric: str) -> np.ndarray:
  grid = np.full((len(AXIS_VALUES), len(AXIS_VALUES)), np.nan, dtype=float)
  x_index = {value: index for index, value in enumerate(AXIS_VALUES)}
  y_index = {value: index for index, value in enumerate(AXIS_VALUES)}
  for row in rows:
    if row["warhead_family"] != family or row["slice"] != slice_name:
      continue
    grid[y_index[float(row["y_axis_m"])]][x_index[float(row["x_axis_m"])]] = float(
      row[metric]
    )
  return grid


def _metric_limits(rows: list[dict[str, object]], slice_name: str, metric: str) -> tuple[float, float]:
  values = [
    float(row[metric])
    for row in rows
    if row["slice"] == slice_name and math.isfinite(float(row[metric]))
  ]
  if not values:
    return 0.0, 1.0
  lower = min(values)
  upper = max(values)
  if math.isclose(lower, upper):
    upper = lower + 1.0
  return lower, upper


def _plot_heatmap_group(
  rows: list[dict[str, object]],
  *,
  slice_spec: dict[str, object],
  metrics: tuple[tuple[str, str], ...],
  kind: str,
  cmap: str,
) -> Path:
  slice_name = str(slice_spec["name"])
  fig, axes = plt.subplots(
    len(WARHEAD_FAMILIES),
    len(metrics),
    figsize=(3.0 * len(metrics), 2.7 * len(WARHEAD_FAMILIES)),
    constrained_layout=True,
  )
  extent_step = AXIS_VALUES[1] - AXIS_VALUES[0]
  extent = [
    min(AXIS_VALUES) - extent_step / 2.0,
    max(AXIS_VALUES) + extent_step / 2.0,
    min(AXIS_VALUES) - extent_step / 2.0,
    max(AXIS_VALUES) + extent_step / 2.0,
  ]

  for family_index, family in enumerate(WARHEAD_FAMILIES):
    for metric_index, (metric, title) in enumerate(metrics):
      ax = axes[family_index][metric_index]
      lower, upper = _metric_limits(rows, slice_name, metric)
      image = ax.imshow(
        _grid(rows, family, slice_name, metric),
        cmap=cmap,
        extent=extent,
        origin="lower",
        aspect="equal",
        vmin=lower,
        vmax=upper,
      )
      if family_index == 0:
        ax.set_title(title, fontsize=9)
      if metric_index == 0:
        ax.set_ylabel(f"{family}\n{slice_spec['y_label']}", fontsize=8)
      else:
        ax.set_ylabel("")
      if family_index == len(WARHEAD_FAMILIES) - 1:
        ax.set_xlabel(str(slice_spec["x_label"]), fontsize=8)
      else:
        ax.set_xlabel("")
      ax.tick_params(axis="both", labelsize=7)
      fig.colorbar(image, ax=ax, fraction=0.045, pad=0.02)

  fig.suptitle(
    f"A9 generic synthetic warhead {kind} heatmap ({slice_name} slice)",
    fontsize=12,
  )
  out = OUT_DIR / f"warhead_detonation_heatmap_{kind}_{slice_spec['figure_suffix']}_20260617.png"
  fig.savefig(out, dpi=160)
  plt.close(fig)
  return out


def _print_summary(rows: list[dict[str, object]]) -> None:
  print(f"Wrote {len(rows)} cases to {CSV_OUT}")
  for slice_spec in SLICES:
    slice_name = str(slice_spec["name"])
    print(f"\n{slice_name} slice maxima:")
    for family in WARHEAD_FAMILIES:
      family_rows = [
        row
        for row in rows
        if row["slice"] == slice_name and row["warhead_family"] == family
      ]
      max_damage = max(family_rows, key=lambda row: float(row["system_damage"]))
      max_loads = max(family_rows, key=lambda row: float(row["component_load_count"]))
      print(
        "  "
        f"{family}: max system_damage={float(max_damage['system_damage']):.3f} "
        f"at local=({float(max_damage['local_forward_m']):.1f}, "
        f"{float(max_damage['local_right_m']):.1f}, "
        f"{float(max_damage['local_up_m']):.1f}); "
        f"max loads={int(max_loads['component_load_count'])} "
        f"at local=({float(max_loads['local_forward_m']):.1f}, "
        f"{float(max_loads['local_right_m']):.1f}, "
        f"{float(max_loads['local_up_m']):.1f})"
      )


def main() -> None:
  ef_py.set_log_level("error")
  rows = _run_sweep()
  _write_csv(rows)
  damage_outputs = [
    _plot_heatmap_group(
      rows,
      slice_spec=slice_spec,
      metrics=DAMAGE_METRICS,
      kind="damage",
      cmap="magma",
    )
    for slice_spec in SLICES
  ]
  mechanism_outputs = [
    _plot_heatmap_group(
      rows,
      slice_spec=slice_spec,
      metrics=MECHANISM_METRICS,
      kind="mechanism",
      cmap="viridis",
    )
    for slice_spec in SLICES
  ]
  _print_summary(rows)
  print("\nFigures:")
  for output in damage_outputs + mechanism_outputs:
    print(f"  {output}")


if __name__ == "__main__":
  main()
