from __future__ import annotations

import json
import math
import os
import shutil
import tempfile
import unittest

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py # noqa: E402


_DB_PATH = resolve_repo_path("examples", "config", "database")


def _make_kernel() -> ef_py.SimulationKernel:
  sim = ef_py.SimulationKernel()
  if not sim.load_database(_DB_PATH):
    raise AssertionError("failed to load runtime database")
  sim.set_time_step(1.0 / 60.0)
  tuning = ef_py.MissileTuning()
  tuning.sensor_scan_period = 1.0e9
  tuning.sensor_track_memory_s = 0.0
  tuning.sensor_detection_prob = 0.0
  tuning.seeker_fov_deg = 180.0
  tuning.seeker_lock_range = 1.0e6
  tuning.max_speed = 950.0
  tuning.turn_rate = 35.0
  tuning.nav_gain = 3.0
  tuning.track_break_time_s = 0.75
  tuning.boost_time_s = 3.0
  tuning.sustain_time_s = 0.0
  tuning.reference_area_m2 = 0.02
  sim.set_missile_tuning(tuning)
  return sim


def _spawn_pair(sim: ef_py.SimulationKernel) -> tuple[int, int]:
  blue_id = int(
    sim.spawn_unit(
      ef_py.Side.Blue,
      "F-16C_Block50",
      0.0,
      0.0,
      5000.0,
      0.0,
      0.0,
      0.0,
      0.0,
      250.0,
      0.0,
    )
  )
  red_id = int(
    sim.spawn_unit(
      ef_py.Side.Red,
      "Aircraft",
      0.0,
      100000.0,
      5000.0,
      180.0,
      0.0,
      0.0,
      0.0,
      -250.0,
      0.0,
    )
  )
  sim.set_unit_ammo(blue_id, 4, 4)
  sim.set_weapon_cooldown(blue_id, 0.0, -1.0)
  return blue_id, red_id


def _make_detection(
  target_id: int,
  *,
  range_m: float,
  bearing_deg: float,
  elevation_deg: float = 0.0,
  closing_speed_mps: float = 350.0,
  signal_strength: float = 1.0,
  local_sensor_hit: bool = True,
  timestamp: float = 0.0,
) -> ef_py.Detection:
  det = ef_py.Detection()
  det.target_id = int(target_id)
  det.range = float(range_m)
  det.bearing = float(bearing_deg)
  det.elevation = float(elevation_deg)
  det.closing_speed = float(closing_speed_mps)
  det.signal_strength = float(signal_strength)
  det.local_sensor_hit = bool(local_sensor_hit)
  det.timestamp = float(timestamp)
  return det


def _set_contacts(sim: ef_py.SimulationKernel, entity_id: int, contacts: list[ef_py.Detection]) -> None:
  sim.set_contact_list(int(entity_id), contacts)


def _velocity_speed(sim: ef_py.SimulationKernel, entity_id: int) -> float:
  vx, vy, vz = sim.get_unit_velocity(int(entity_id))
  return math.sqrt(vx * vx + vy * vy + vz * vz)


def _missile_runtime(sim: ef_py.SimulationKernel, entity_id: int) -> dict:
  return sim.debug_get_missile_runtime_state(int(entity_id))


def _heading_from_velocity(sim: ef_py.SimulationKernel, entity_id: int) -> float:
  vx, vy, _ = sim.get_unit_velocity(int(entity_id))
  if abs(vx) + abs(vy) < 1.0e-9:
    return 0.0
  deg = math.degrees(math.atan2(vx, vy))
  while deg < 0.0:
    deg += 360.0
  while deg >= 360.0:
    deg -= 360.0
  return deg


def _relative_detection_from_truth(
  sim: ef_py.SimulationKernel,
  observer_id: int,
  target_id: int,
  *,
  timestamp: float,
  signal_strength: float = 1.0,
  local_sensor_hit: bool = True,
) -> ef_py.Detection:
  ox, oy, oz = (float(value) for value in sim.get_unit_position(int(observer_id)))
  tx, ty, tz = (float(value) for value in sim.get_unit_position(int(target_id)))
  ovx, ovy, ovz = (float(value) for value in sim.get_unit_velocity(int(observer_id)))
  tvx, tvy, tvz = (float(value) for value in sim.get_unit_velocity(int(target_id)))
  dx = tx - ox
  dy = ty - oy
  dz = tz - oz
  horizontal = math.hypot(dx, dy)
  distance = math.sqrt(dx * dx + dy * dy + dz * dz)
  bearing_nav = math.degrees(math.atan2(dx, dy))
  heading = float(sim.get_unit_heading(int(observer_id)))
  relative_bearing = bearing_nav - heading
  while relative_bearing > 180.0:
    relative_bearing -= 360.0
  while relative_bearing < -180.0:
    relative_bearing += 360.0
  elevation = math.degrees(math.atan2(dz, horizontal)) if horizontal > 1.0e-9 else 0.0
  closing = 0.0
  if distance > 1.0e-9:
    ux = dx / distance
    uy = dy / distance
    uz = dz / distance
    rel_vx = tvx - ovx
    rel_vy = tvy - ovy
    rel_vz = tvz - ovz
    closing = -(rel_vx * ux + rel_vy * uy + rel_vz * uz)
  return _make_detection(
    int(target_id),
    range_m=distance,
    bearing_deg=relative_bearing,
    elevation_deg=elevation,
    closing_speed_mps=closing,
    signal_strength=signal_strength,
    local_sensor_hit=local_sensor_hit,
    timestamp=timestamp,
  )


def _drive_missile_with_truth_track(
  sim: ef_py.SimulationKernel,
  missile_id: int,
  target_id: int,
  *,
  max_steps: int = 3600,
) -> dict[str, float | bool]:
  dt = float(sim.get_time_step())
  last_runtime: dict = _missile_runtime(sim, missile_id)
  min_truth_distance = math.inf
  max_achieved_lateral_accel = float(last_runtime["achieved_lateral_accel_mps2"])
  time_s = 0.0
  for step_idx in range(max_steps):
    if not sim.is_unit_active(missile_id):
      break
    mx, my, mz = (float(value) for value in sim.get_unit_position(int(missile_id)))
    tx, ty, tz = (float(value) for value in sim.get_unit_position(int(target_id)))
    min_truth_distance = min(min_truth_distance, math.dist((mx, my, mz), (tx, ty, tz)))
    _set_contacts(
      sim,
      missile_id,
      [
        _relative_detection_from_truth(
          sim,
          missile_id,
          target_id,
          timestamp=step_idx * dt,
          local_sensor_hit=True,
        )
      ],
    )
    sim.step()
    time_s += dt
    if sim.is_unit_active(missile_id):
      last_runtime = _missile_runtime(sim, missile_id)
      max_achieved_lateral_accel = max(
        max_achieved_lateral_accel,
        float(last_runtime["achieved_lateral_accel_mps2"]),
      )

  target_active = bool(sim.is_unit_active(target_id))
  missile_active = bool(sim.is_unit_active(missile_id))
  if missile_active:
    last_runtime = _missile_runtime(sim, missile_id)
  return {
    "missile_active": missile_active,
    "target_active": target_active,
    "time_s": time_s,
    "truth_min_dist_m": float(min_truth_distance),
    "proximity_min_dist_m": float(last_runtime["proximity_min_dist_m"]),
    "proximity_last_dist_m": float(last_runtime["proximity_last_dist_m"]),
    "proximity_engaged": bool(last_runtime["proximity_engaged"]),
    "seeker_has_valid_track": bool(last_runtime["seeker_has_valid_track"]),
    "terminal_seeker_active": bool(last_runtime["terminal_seeker_active"]),
    "achieved_lateral_accel_mps2": float(last_runtime["achieved_lateral_accel_mps2"]),
    "max_achieved_lateral_accel_mps2": max_achieved_lateral_accel,
  }


def _make_baseline_kernel() -> ef_py.SimulationKernel:
  sim = _make_kernel()
  tuning = sim.get_missile_tuning()
  tuning.sensor_scan_period = 1.0e9
  tuning.sensor_detection_prob = 0.0
  tuning.sensor_track_memory_s = 0.0
  tuning.seeker_fov_deg = 180.0
  tuning.seeker_lock_range = 1.0e6
  tuning.max_speed = 1100.0
  tuning.turn_rate = 45.0
  tuning.max_lateral_g = 35.0
  tuning.autopilot_tau_s = 0.04
  tuning.max_accel_response_g_per_s = 500.0
  tuning.nav_gain = 4.0
  tuning.fuse_distance = 35.0
  tuning.damage = 1.0
  tuning.max_flight_time_s = 45.0
  tuning.guidance_delay_s = 0.0
  tuning.guidance_update_period_s = 0.0
  tuning.bearing_filter_tau_s = 0.0
  tuning.elevation_filter_tau_s = 0.0
  tuning.range_filter_tau_s = 0.0
  tuning.track_break_time_s = 0.4
  tuning.boost_time_s = 3.0
  tuning.sustain_time_s = 1.5
  tuning.reference_area_m2 = 0.025
  sim.set_missile_tuning(tuning)
  return sim


def _spawn_geometry_pair(
  sim: ef_py.SimulationKernel,
  *,
  red_x: float,
  red_y: float,
  red_heading: float,
  red_vx: float,
  red_vy: float,
  red_vz: float = 0.0,
  blue_heading: float = 0.0,
  blue_vx: float = 0.0,
  blue_vy: float = 250.0,
  blue_z: float = 5000.0,
  red_z: float = 5000.0,
) -> tuple[int, int]:
  blue_id = int(
    sim.spawn_unit(
      ef_py.Side.Blue,
      "F-16C_Block50",
      0.0,
      0.0,
      blue_z,
      blue_heading,
      0.0,
      0.0,
      blue_vx,
      blue_vy,
      0.0,
    )
  )
  red_id = int(
    sim.spawn_unit(
      ef_py.Side.Red,
      "F-16C_Block50",
      red_x,
      red_y,
      red_z,
      red_heading,
      0.0,
      0.0,
      red_vx,
      red_vy,
      red_vz,
    )
  )
  sim.set_unit_ammo(blue_id, 4, 4)
  sim.set_weapon_cooldown(blue_id, 0.0, -1.0)
  initial_detection = _relative_detection_from_truth(sim, blue_id, red_id, timestamp=0.0)
  _set_contacts(sim, blue_id, [initial_detection])
  return blue_id, red_id


def _run_miss_distance_case(
  *,
  red_x: float,
  red_y: float,
  red_heading: float,
  red_vx: float,
  red_vy: float,
  red_vz: float = 0.0,
  blue_heading: float = 0.0,
  blue_vx: float = 0.0,
  blue_vy: float = 250.0,
  max_steps: int = 3600,
) -> dict[str, float | bool]:
  sim = _make_baseline_kernel()
  blue_id, red_id = _spawn_geometry_pair(
    sim,
    red_x=red_x,
    red_y=red_y,
    red_heading=red_heading,
    red_vx=red_vx,
    red_vy=red_vy,
    red_vz=red_vz,
    blue_heading=blue_heading,
    blue_vx=blue_vx,
    blue_vy=blue_vy,
  )
  missile_id = int(sim.fire_missile(blue_id, red_id))
  if missile_id <= 0:
    raise AssertionError("expected missile launch to succeed for miss-distance baseline")
  return _drive_missile_with_truth_track(sim, missile_id, red_id, max_steps=max_steps)


def _spawn_structured_f16_pair(sim: ef_py.SimulationKernel) -> tuple[int, int]:
  attacker_id = int(
    sim.spawn_unit(
      ef_py.Side.Blue,
      "F-16C_Block50",
      0.0,
      0.0,
      5000.0,
      0.0,
      0.0,
      0.0,
      0.0,
      250.0,
      0.0,
    )
  )
  target_id = int(
    sim.spawn_unit(
      ef_py.Side.Red,
      "F-16C_Block50",
      0.0,
      500.0,
      5000.0,
      180.0,
      0.0,
      0.0,
      0.0,
      -250.0,
      0.0,
    )
  )
  return attacker_id, target_id


def _spawn_structured_f16_pair_with_target_attitude(
  sim: ef_py.SimulationKernel,
  *,
  target_pitch_deg: float,
  target_roll_deg: float,
) -> tuple[int, int]:
  attacker_id = int(
    sim.spawn_unit(
      ef_py.Side.Blue,
      "F-16C_Block50",
      0.0,
      0.0,
      5000.0,
      0.0,
      0.0,
      0.0,
      0.0,
      250.0,
      0.0,
    )
  )
  target_id = int(
    sim.spawn_unit(
      ef_py.Side.Red,
      "F-16C_Block50",
      0.0,
      500.0,
      5000.0,
      180.0,
      float(target_pitch_deg),
      float(target_roll_deg),
      0.0,
      -250.0,
      0.0,
    )
  )
  return attacker_id, target_id


def _spawn_attacker_and_e3_target(sim: ef_py.SimulationKernel) -> tuple[int, int]:
  attacker_id = int(
    sim.spawn_unit(
      ef_py.Side.Blue,
      "F-16C_Block50",
      0.0,
      0.0,
      9000.0,
      0.0,
      0.0,
      0.0,
      0.0,
      250.0,
      0.0,
    )
  )
  target_id = int(
    sim.spawn_unit(
      ef_py.Side.Red,
      "E-3_Sentry_AWACS",
      0.0,
      1000.0,
      9000.0,
      180.0,
      0.0,
      0.0,
      0.0,
      200.0,
      0.0,
    )
  )
  return attacker_id, target_id


def _spawn_attacker_and_named_target(
  sim: ef_py.SimulationKernel,
  target_type: str,
  *,
  target_side: ef_py.Side | None = None,
  altitude_m: float = 5000.0,
) -> tuple[int, int]:
  if target_side is None:
    target_side = ef_py.Side.Red
  attacker_id = int(
    sim.spawn_unit(
      ef_py.Side.Blue,
      "F-16C_Block50",
      0.0,
      0.0,
      altitude_m,
      0.0,
      0.0,
      0.0,
      0.0,
      250.0,
      0.0,
    )
  )
  target_id = int(
    sim.spawn_unit(
      target_side,
      target_type,
      0.0,
      1000.0,
      altitude_m,
      180.0,
      0.0,
      0.0,
      0.0,
      -200.0,
      0.0,
    )
  )
  return attacker_id, target_id


def _make_warhead_profile(
  family: str,
  *,
  damage: float = 90.0,
  radius: float = 25.0,
  mass_kg: float = 12.0,
  damage_scalar_synthetic: bool = False,
) -> ef_py.WarheadProfile:
  profile = ef_py.WarheadProfile()
  profile.family = str(family)
  profile.mass_kg = float(mass_kg)
  profile.lethal_radius_m = float(radius)
  profile.damage_scalar = float(damage)
  profile.synthetic = False
  profile.damage_scalar_synthetic = bool(damage_scalar_synthetic)
  profile.provenance = f"test_{family}_profile"
  return profile


def _make_f16_armor_override(name: str, *, wing_armor_mm: float) -> dict:
  with open(
    resolve_repo_path("examples", "config", "database", "aircraft", "units", "f16c_block50.json"),
    "r",
    encoding="utf-8",
  ) as handle:
    unit = json.load(handle)
  unit["name"] = name
  damage_model = unit["damage_model"]
  damage_model.pop("vulnerability", None)
  for hitbox in damage_model["hitboxes"]:
    systems = set(str(system) for system in hitbox.get("systems", []))
    if "wings" in systems and "flight_control" in systems:
      hitbox["armor"] = float(wing_armor_mm)
      for component in hitbox.get("components", []):
        component["armor"] = float(wing_armor_mm)
  return unit


def _make_f16_componentized_wing_override(name: str) -> dict:
  with open(
    resolve_repo_path("examples", "config", "database", "aircraft", "units", "f16c_block50.json"),
    "r",
    encoding="utf-8",
  ) as handle:
    unit = json.load(handle)
  unit["name"] = name
  damage_model = unit["damage_model"]
  damage_model.pop("vulnerability", None)
  for hitbox in damage_model["hitboxes"]:
    systems = set(str(system) for system in hitbox.get("systems", []))
    if "wings" in systems and "flight_control" in systems:
      hitbox["components"] = [
        {
          "name": "left_wing_fuel_cell",
          "system": "fuel",
          "offset": [-0.8, -2.8, 0.0],
          "size": [1.2, 1.2, 0.25],
          "armor": 2.0,
          "threshold_scale": 1.25,
          "redundancy_group_id": "wing_fuel_cells",
          "redundancy_group": 1.0,
          "redundancy_weight": 1.0,
          "critical": True,
        },
        {
          "name": "right_aileron_actuator",
          "system": "flight_control",
          "offset": [-0.8, 2.8, 0.0],
          "size": [1.0, 1.1, 0.22],
          "armor": 3.0,
          "threshold_scale": 1.35,
          "redundancy_group_id": "lateral_flight_control_actuators",
          "redundancy_group": 2.0,
          "redundancy_weight": 1.0,
          "critical": False,
        },
      ]
  return unit


def _make_f16_wing_geometry_override(name: str, *, wing_width_m: float) -> dict:
  with open(
    resolve_repo_path("examples", "config", "database", "aircraft", "units", "f16c_block50.json"),
    "r",
    encoding="utf-8",
  ) as handle:
    unit = json.load(handle)
  unit["name"] = name
  damage_model = unit["damage_model"]
  damage_model.pop("vulnerability", None)
  for hitbox in damage_model["hitboxes"]:
    systems = set(str(system) for system in hitbox.get("systems", []))
    if "wings" in systems and "flight_control" in systems:
      old_width = float(hitbox["size"][1])
      width_ratio = float(wing_width_m) / max(1.0e-6, old_width)
      hitbox["size"][1] = float(wing_width_m)
      for component in hitbox.get("components", []):
        offset = [float(value) for value in component.get("offset", [0.0, 0.0, 0.0])]
        size = [float(value) for value in component.get("size", [0.5, 0.5, 0.2])]
        if len(offset) >= 2:
          offset[1] *= width_ratio
        if len(size) >= 2:
          size[1] = max(0.12, size[1] * width_ratio)
        component["offset"] = offset
        component["size"] = size
  return unit


def _make_f16_wing_only_geometry_override(name: str, *, wing_width_m: float) -> dict:
  unit = _make_f16_wing_geometry_override(name, wing_width_m=wing_width_m)
  damage_model = unit["damage_model"]
  filtered_hitboxes = []
  for hitbox in damage_model["hitboxes"]:
    systems = set(str(system) for system in hitbox.get("systems", []))
    if "wings" in systems and "flight_control" in systems:
      filtered_hitboxes.append(hitbox)
  damage_model["hitboxes"] = filtered_hitboxes
  return unit


def _make_f16_component_redundancy_override(
  name: str,
  *,
  redundancy_group: float,
  critical: bool,
) -> dict:
  with open(
    resolve_repo_path("examples", "config", "database", "aircraft", "units", "f16c_block50.json"),
    "r",
    encoding="utf-8",
  ) as handle:
    unit = json.load(handle)
  unit["name"] = name
  damage_model = unit["damage_model"]
  damage_model.pop("vulnerability", None)
  for hitbox in damage_model["hitboxes"]:
    for component in hitbox.get("components", []):
      if str(component.get("name", "")) == "right_aileron_actuator":
        component["redundancy_group"] = float(redundancy_group)
        component["redundancy_group_id"] = (
          "lateral_flight_control_actuators"
          if redundancy_group > 0.0
          else "single_right_aileron_actuator"
        )
        component["critical"] = bool(critical)
        component["threshold_scale"] = 1.35
  return unit


def _make_f16_typed_dependency_override(name: str, dependencies: list[dict]) -> dict:
  with open(
    resolve_repo_path("examples", "config", "database", "aircraft", "units", "f16c_block50.json"),
    "r",
    encoding="utf-8",
  ) as handle:
    unit = json.load(handle)
  unit["name"] = name
  damage_model = unit["damage_model"]
  damage_model.pop("vulnerability", None)
  for hitbox in damage_model["hitboxes"]:
    systems = set(str(system) for system in hitbox.get("systems", []))
    if "wings" in systems and "flight_control" in systems:
      hitbox["components"] = [
        {
          "name": "typed_dependency_source",
          "system": "auxiliary_dependency_source",
          "offset": [-0.8, 2.8, 0.0],
          "size": [1.0, 1.1, 0.22],
          "armor": 2.0,
          "threshold_scale": 1.0,
          "redundancy_group_id": "typed_dependency_source",
          "redundancy_group": 0.0,
          "redundancy_weight": 1.0,
          "dependencies": dependencies,
          "critical": False,
        },
      ]
  return unit


def _make_f16_component_mechanism_threshold_override(
  name: str,
  *,
  continuous_rod_scale: float,
) -> dict:
  with open(
    resolve_repo_path("examples", "config", "database", "aircraft", "units", "f16c_block50.json"),
    "r",
    encoding="utf-8",
  ) as handle:
    unit = json.load(handle)
  unit["name"] = name
  unit["damage_model"].pop("vulnerability", None)
  for hitbox in unit["damage_model"]["hitboxes"]:
    for component in hitbox.get("components", []):
      if str(component.get("name", "")) == "right_aileron_actuator":
        component["mechanism_thresholds"] = {
          "blast_fragmentation": 1.0,
          "continuous_rod": float(continuous_rod_scale),
        }
  return unit


def _make_f16_projection_priority_override(name: str) -> dict:
  with open(
    resolve_repo_path("examples", "config", "database", "aircraft", "units", "f16c_block50.json"),
    "r",
    encoding="utf-8",
  ) as handle:
    unit = json.load(handle)
  unit["name"] = name
  damage_model = unit["damage_model"]
  damage_model.pop("vulnerability", None)
  for hitbox in damage_model["hitboxes"]:
    systems = set(str(system) for system in hitbox.get("systems", []))
    if "wings" in systems and "flight_control" in systems:
      hitbox["components"] = [
        {
          "name": "near_resistant_wing_structure",
          "system": "wing_structure",
          "offset": [-0.8, 4.1, 0.0],
          "size": [0.9, 0.8, 0.22],
          "armor": 12.0,
          "threshold_scale": 0.35,
          "mechanism_thresholds": {
            "blast": 0.45,
            "fragmentation": 0.40,
            "blast_fragmentation": 0.40,
            "continuous_rod": 0.40,
            "hit_to_kill": 0.50,
          },
          "redundancy_group_id": "projection_priority_structure",
          "redundancy_group": 1.0,
          "redundancy_weight": 1.5,
          "critical": False,
        },
        {
          "name": "far_vulnerable_flight_servo",
          "system": "flight_control",
          "offset": [-0.8, 2.8, 0.0],
          "size": [1.2, 1.0, 0.25],
          "armor": 0.2,
          "threshold_scale": 2.2,
          "mechanism_thresholds": {
            "blast": 1.10,
            "fragmentation": 1.70,
            "blast_fragmentation": 1.80,
            "continuous_rod": 1.75,
            "hit_to_kill": 1.40,
          },
          "redundancy_group_id": "projection_priority_servo",
          "redundancy_group": 0.0,
          "redundancy_weight": 0.8,
          "dependencies": [
            {
              "target_system": "hydraulic",
              "edge_type": "hydraulic_power",
              "scale": 1.0,
              "threshold": 1.0,
            }
          ],
          "critical": True,
        },
      ]
  return unit


def _copy_database_with_f16_vulnerability(
  tmpdir: str,
  vulnerability_patch: dict,
  *,
  descriptor: dict | None = None,
  descriptor_patch: dict | None = None,
) -> str:
  db_dir = os.path.join(tmpdir, "database")
  shutil.copytree(_DB_PATH, db_dir)

  unit_path = os.path.join(db_dir, "aircraft", "units", "f16c_block50.json")
  with open(unit_path, "r", encoding="utf-8") as handle:
    unit = json.load(handle)
  vulnerability = dict(unit["damage_model"].get("vulnerability", {}))
  vulnerability.update(vulnerability_patch)
  unit["damage_model"]["vulnerability"] = vulnerability
  with open(unit_path, "w", encoding="utf-8") as handle:
    json.dump(unit, handle)

  if descriptor is not None or descriptor_patch is not None:
    evidence_dir = os.path.join(db_dir, "damage", "vulnerability_evidence")
    os.makedirs(evidence_dir, exist_ok=True)
    descriptor_data = dict(descriptor) if descriptor is not None else {}
    if descriptor_patch is not None:
      placeholder_path = os.path.join(
        evidence_dir,
        "a2_synthetic_f16_aim120_placeholder.json",
      )
      if os.path.exists(placeholder_path):
        with open(placeholder_path, "r", encoding="utf-8") as handle:
          descriptor_data = json.load(handle)
      descriptor_data.update(descriptor_patch)
    dataset_id = str(descriptor_data["dataset_id"])
    if descriptor_data.get("calibration_status") == "calibrated":
      descriptor_data.setdefault("schema_version", "a2.vulnerability_evidence.v1")
      descriptor_data.setdefault("source_ref", f"fixture://descriptor/{dataset_id}")
    with open(
      os.path.join(evidence_dir, f"{dataset_id}.json"),
      "w",
      encoding="utf-8",
    ) as handle:
      json.dump(descriptor_data, handle)

  return db_dir


def _validated_surrogate_manifest_patch(
  *,
  target_type: str = "F-16C_Block50",
  weapon_family: str = "blast_fragmentation",
  aspect_bucket: str = "beam",
  closure_bucket: str = "high",
  miss_distance_bucket: str = "near_miss_0_35m",
  validation_status: str = "validated",
) -> dict:
  return {
    "validation_manifest": {
      "schema_version": "a2.vulnerability_surrogate_validation.v1",
      "validation_status": validation_status,
      "validation_artifact_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
      "validated_surrogate_model_ref": "fixture://surrogate/model/f16-aim120-v1",
      "validation_benchmark_ref": "fixture://surrogate/benchmark/f16-aim120-v1",
      "validation_metrics_ref": "fixture://surrogate/metrics/f16-aim120-v1",
      "validation_acceptance_criteria_ref": "fixture://surrogate/acceptance/f16-aim120-v1",
      "validation_scope": {
        "target_type": target_type,
        "weapon_family": weapon_family,
        "aspect_bucket": aspect_bucket,
        "closure_bucket": closure_bucket,
        "miss_distance_bucket": miss_distance_bucket,
      },
    }
  }


def _kernel_with_unit_overrides(overrides: list[dict]) -> ef_py.SimulationKernel:
  sim = ef_py.SimulationKernel()
  sim.reset(20260526 + len(overrides))
  if not sim.load_database(_DB_PATH):
    raise AssertionError("failed to load runtime database")
  with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
    json.dump({"units": overrides}, handle)
    override_path = handle.name
  if not sim.load_unit_definitions(override_path):
    raise AssertionError(f"failed to load unit overrides from {override_path}")
  return sim


def _profiled_local_hit_overlay_for_target(
  target_type: str,
  family: str,
  local: tuple[float, float, float],
  *,
  damage: float = 90.0,
  radius: float = 25.0,
  overrides: list[dict] | None = None,
) -> tuple[dict[str, float], list[float], object]:
  sim = _kernel_with_unit_overrides(overrides or [])
  attacker_id, target_id = _spawn_attacker_and_named_target(sim, target_type)
  profile = _make_warhead_profile(family, damage=damage, radius=radius)
  ok = sim.debug_apply_profiled_local_proximity_hit(
    attacker_id,
    target_id,
    float(local[0]),
    float(local[1]),
    float(local[2]),
    profile,
  )
  if not ok:
    raise AssertionError(f"profiled local hit failed for {family} against {target_type}")
  if not sim.is_unit_active(target_id):
    raise AssertionError(f"profiled local hit destroyed target unexpectedly for {target_type}")
  events = sim.export_recent_engagement_events()
  if len(events.effects_events) != 1:
    raise AssertionError(f"expected one effects event for {target_type}")
  return (
    _aircraft_damage_overlay(sim, target_id),
    [float(value) for value in sim.get_unit_damage_state(target_id)],
    events.effects_events[0],
  )


def _profiled_local_hit_damage_state(
  family: str,
  local: tuple[float, float, float],
  *,
  damage: float = 90.0,
) -> tuple[list[float], object]:
  sim = ef_py.SimulationKernel()
  sim.reset(20260526)
  if not sim.load_database(_DB_PATH):
    raise AssertionError("failed to load runtime database")
  attacker_id, target_id = _spawn_structured_f16_pair(sim)
  profile = _make_warhead_profile(family, damage=damage)
  ok = sim.debug_apply_profiled_local_proximity_hit(
    attacker_id,
    target_id,
    float(local[0]),
    float(local[1]),
    float(local[2]),
    profile,
  )
  if not ok:
    raise AssertionError(f"profiled local hit failed for {family}")
  if not sim.is_unit_active(target_id):
    raise AssertionError(f"profiled local hit destroyed target unexpectedly for {family}")
  events = sim.export_recent_engagement_events()
  if len(events.effects_events) != 1:
    raise AssertionError(f"expected one effects event for {family}")
  return [float(value) for value in sim.get_unit_damage_state(target_id)], events.effects_events[0]


def _profiled_local_hit_overlay(
  family: str,
  local: tuple[float, float, float],
  *,
  damage: float = 90.0,
  radius: float = 25.0,
) -> tuple[dict[str, float], list[float], object]:
  sim = ef_py.SimulationKernel()
  sim.reset(20260526)
  if not sim.load_database(_DB_PATH):
    raise AssertionError("failed to load runtime database")
  attacker_id, target_id = _spawn_structured_f16_pair(sim)
  profile = _make_warhead_profile(family, damage=damage, radius=radius)
  ok = sim.debug_apply_profiled_local_proximity_hit(
    attacker_id,
    target_id,
    float(local[0]),
    float(local[1]),
    float(local[2]),
    profile,
  )
  if not ok:
    raise AssertionError(f"profiled local hit failed for {family}")
  if not sim.is_unit_active(target_id):
    raise AssertionError(f"profiled local hit destroyed target unexpectedly for {family}")
  events = sim.export_recent_engagement_events()
  if len(events.effects_events) != 1:
    raise AssertionError(f"expected one effects event for {family}")
  return (
    _aircraft_damage_overlay(sim, target_id),
    [float(value) for value in sim.get_unit_damage_state(target_id)],
    events.effects_events[0],
  )


def _profiled_local_hit_overlay_with_velocity(
  family: str,
  local: tuple[float, float, float],
  missile_velocity: tuple[float, float, float],
  *,
  damage: float = 90.0,
  radius: float = 25.0,
) -> dict[str, float]:
  overlay, _event = _profiled_local_hit_overlay_and_event_with_velocity(
    family,
    local,
    missile_velocity,
    damage=damage,
    radius=radius,
  )
  return overlay


def _profiled_local_hit_overlay_and_event_with_velocity(
  family: str,
  local: tuple[float, float, float],
  missile_velocity: tuple[float, float, float],
  *,
  damage: float = 90.0,
  radius: float = 25.0,
  database_path: str | None = None,
) -> tuple[dict[str, float], object]:
  sim = ef_py.SimulationKernel()
  sim.reset(20260526)
  if not sim.load_database(database_path or _DB_PATH):
    raise AssertionError("failed to load runtime database")
  attacker_id, target_id = _spawn_structured_f16_pair(sim)
  profile = _make_warhead_profile(family, damage=damage, radius=radius)
  ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
    attacker_id,
    target_id,
    float(local[0]),
    float(local[1]),
    float(local[2]),
    profile,
    float(missile_velocity[0]),
    float(missile_velocity[1]),
    float(missile_velocity[2]),
  )
  if not ok:
    raise AssertionError(f"profiled local hit with velocity failed for {family}")
  if not sim.is_unit_active(target_id):
    raise AssertionError(f"profiled local hit destroyed target unexpectedly for {family}")
  events = sim.export_recent_engagement_events()
  if len(events.effects_events) != 1:
    raise AssertionError(f"expected one effects event for {family}")
  return _aircraft_damage_overlay(sim, target_id), events.effects_events[0]


def _profiled_local_hit_overlay_and_event_with_velocity_and_attitude(
  family: str,
  local: tuple[float, float, float],
  missile_velocity: tuple[float, float, float],
  attitude_deg: tuple[float, float, float],
  *,
  damage: float = 90.0,
  radius: float = 25.0,
) -> tuple[dict[str, float], object]:
  sim = ef_py.SimulationKernel()
  sim.reset(20260526)
  if not sim.load_database(_DB_PATH):
    raise AssertionError("failed to load runtime database")
  attacker_id, target_id = _spawn_structured_f16_pair(sim)
  profile = _make_warhead_profile(family, damage=damage, radius=radius)
  ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity_and_attitude(
    attacker_id,
    target_id,
    float(local[0]),
    float(local[1]),
    float(local[2]),
    profile,
    float(missile_velocity[0]),
    float(missile_velocity[1]),
    float(missile_velocity[2]),
    float(attitude_deg[0]),
    float(attitude_deg[1]),
    float(attitude_deg[2]),
  )
  if not ok:
    raise AssertionError(f"profiled local hit with attitude failed for {family}")
  if not sim.is_unit_active(target_id):
    raise AssertionError(f"profiled local hit destroyed target unexpectedly for {family}")
  events = sim.export_recent_engagement_events()
  if len(events.effects_events) != 1:
    raise AssertionError(f"expected one effects event for {family}")
  return _aircraft_damage_overlay(sim, target_id), events.effects_events[0]


def _profiled_local_hit_overlay_and_event_with_target_attitude(
  family: str,
  local: tuple[float, float, float],
  target_attitude_deg: tuple[float, float],
  *,
  damage: float = 90.0,
  radius: float = 25.0,
) -> tuple[dict[str, float], object]:
  sim = ef_py.SimulationKernel()
  sim.reset(20260526)
  if not sim.load_database(_DB_PATH):
    raise AssertionError("failed to load runtime database")
  attacker_id, target_id = _spawn_structured_f16_pair_with_target_attitude(
    sim,
    target_pitch_deg=target_attitude_deg[0],
    target_roll_deg=target_attitude_deg[1],
  )
  profile = _make_warhead_profile(family, damage=damage, radius=radius)
  ok = sim.debug_apply_profiled_local_proximity_hit(
    attacker_id,
    target_id,
    float(local[0]),
    float(local[1]),
    float(local[2]),
    profile,
  )
  if not ok:
    raise AssertionError(f"profiled local hit with target attitude failed for {family}")
  if not sim.is_unit_active(target_id):
    raise AssertionError(f"profiled local hit destroyed target unexpectedly for {family}")
  events = sim.export_recent_engagement_events()
  if len(events.effects_events) != 1:
    raise AssertionError(f"expected one effects event for {family}")
  return _aircraft_damage_overlay(sim, target_id), events.effects_events[0]


def _aircraft_damage_overlay(sim: ef_py.SimulationKernel, entity_id: int) -> dict[str, float]:
  values = [float(value) for value in sim.debug_get_aircraft_damage_state(int(entity_id))]
  names_without_pressure = (
    "structure",
    "flight_control",
    "hydraulic",
    "roll_control",
    "pitch_control",
    "yaw_control",
    "control_asymmetry",
    "propulsion",
    "fuel",
    "avionics",
    "crew",
    "pilot",
    "mission_crew",
    "command_navigation",
    "fire",
    "fuel_leak",
    "fuel_imbalance",
    "flammable_fluid",
    "ignition_source",
    "fire_suppression",
    "smoke_heat",
    "engine_fire_zone",
    "wing_fire_zone",
    "fuselage_fire_zone",
    "mission_fire_zone",
    "structural_overstress",
    "flutter_exposure",
    "forced_landing",
    "flight_control_kill",
    "propulsion_kill",
    "crew_kill",
  )
  names_with_pressure = (
    "structure",
    "flight_control",
    "hydraulic",
    "hydraulic_pressure",
    "roll_control",
    "pitch_control",
    "yaw_control",
    "control_asymmetry",
    "propulsion",
    "fuel",
    "avionics",
    "crew",
    "pilot",
    "mission_crew",
    "command_navigation",
    "fire",
    "fuel_leak",
    "fuel_imbalance",
    "flammable_fluid",
    "ignition_source",
    "fire_suppression",
    "smoke_heat",
    "engine_fire_zone",
    "wing_fire_zone",
    "fuselage_fire_zone",
    "mission_fire_zone",
    "structural_overstress",
    "flutter_exposure",
    "forced_landing",
    "flight_control_kill",
    "propulsion_kill",
    "crew_kill",
  )
  if len(values) == len(names_with_pressure):
    names = names_with_pressure
  elif len(values) == len(names_without_pressure):
    names = names_without_pressure
  else:
    raise AssertionError(
      f"unexpected aircraft damage overlay field count: "
      f"expected {len(names_without_pressure)} or {len(names_with_pressure)}, "
      f"got {len(values)} values"
    )
  return dict(zip(names, values))


def _spawn_and_fire(
  sim: ef_py.SimulationKernel,
  *,
  range_m: float = 30000.0,
  bearing_deg: float = 0.0,
  elevation_deg: float = 0.0,
) -> tuple[int, int, int]:
  blue_id, red_id = _spawn_pair(sim)
  _set_contacts(
    sim,
    blue_id,
    [_make_detection(red_id, range_m=range_m, bearing_deg=bearing_deg, elevation_deg=elevation_deg)],
  )
  missile_id = int(sim.fire_missile(blue_id, red_id))
  if missile_id <= 0:
    raise AssertionError("expected missile launch to succeed")
  return blue_id, red_id, missile_id


def _spawn_and_fire_with_station(
  sim: ef_py.SimulationKernel,
  station_id: int,
  *,
  range_m: float = 30000.0,
  bearing_deg: float = 0.0,
  elevation_deg: float = 0.0,
) -> tuple[int, int, int]:
  blue_id, red_id = _spawn_pair(sim)
  pilot = ef_py.PilotAction()
  pilot.active = True
  pilot.weapon_select_id = int(station_id)
  sim.set_pilot_action(blue_id, pilot)
  _set_contacts(
    sim,
    blue_id,
    [_make_detection(red_id, range_m=range_m, bearing_deg=bearing_deg, elevation_deg=elevation_deg)],
  )
  missile_id = int(sim.fire_missile(blue_id, red_id))
  if missile_id <= 0:
    raise AssertionError(f"expected missile launch from station {station_id} to succeed")
  return blue_id, red_id, missile_id


__all__ = [name for name in globals() if not name.startswith("__")]
