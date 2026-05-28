from __future__ import annotations

import json
import math
import os
import shutil
import tempfile
import unittest

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402


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
    target_side: ef_py.Side = ef_py.Side.Red,
    altitude_m: float = 5000.0,
) -> tuple[int, int]:
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


def _make_warhead_profile(family: str, *, damage: float = 90.0, radius: float = 25.0) -> ef_py.WarheadProfile:
    profile = ef_py.WarheadProfile()
    profile.family = str(family)
    profile.mass_kg = 12.0
    profile.lethal_radius_m = float(radius)
    profile.damage_scalar = float(damage)
    profile.synthetic = False
    profile.damage_scalar_synthetic = False
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
    names = (
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
        "structural_overstress",
        "flutter_exposure",
        "forced_landing",
        "flight_control_kill",
        "propulsion_kill",
        "crew_kill",
    )
    if len(values) != len(names):
        raise AssertionError(f"expected aircraft damage overlay with {len(names)} fields, got {values!r}")
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


class WeaponGuidanceRealismGuardTests(unittest.TestCase):
    def test_definition_missile_tuning_flows_into_launch_runtime(self) -> None:
        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(_DB_PATH))
        sim.set_time_step(1.0 / 60.0)

        _, _, aim120_id = _spawn_and_fire_with_station(sim, 1, range_m=22000.0, bearing_deg=5.0)
        aim120 = _missile_runtime(sim, aim120_id)
        self.assertAlmostEqual(float(aim120["mass_total_kg"]), 152.0, delta=1.0e-6)
        self.assertAlmostEqual(float(aim120["max_speed_mps"]), 1372.0, delta=1.0e-6)
        self.assertAlmostEqual(float(aim120["turn_rate_deg_s"]), 30.0, delta=1.0e-6)
        self.assertAlmostEqual(float(aim120["guidance_max_lateral_g"]), 35.0, delta=1.0e-6)
        self.assertAlmostEqual(float(aim120["fuse_distance_m"]), 15.0, delta=1.0e-6)
        self.assertEqual(str(aim120["warhead_family"]), "blast_fragmentation")
        self.assertAlmostEqual(float(aim120["warhead_mass_kg"]), 20.0, delta=1.0e-6)
        self.assertAlmostEqual(float(aim120["warhead_lethal_radius_m"]), 15.0, delta=1.0e-6)
        self.assertAlmostEqual(float(aim120["warhead_damage_scalar"]), 180.0, delta=1.0e-6)
        self.assertFalse(bool(aim120["warhead_profile_synthetic"]))
        self.assertTrue(bool(aim120["warhead_damage_scalar_synthetic"]))
        self.assertEqual(str(aim120["fuze_type"]), "radar_proximity")
        self.assertAlmostEqual(float(aim120["fuze_trigger_radius_m"]), 15.0, delta=1.0e-6)
        self.assertAlmostEqual(float(aim120["fuze_delay_s"]), 0.015, delta=1.0e-6)
        self.assertAlmostEqual(float(aim120["fuze_reliability"]), 0.94, delta=1.0e-6)
        self.assertFalse(bool(aim120["fuze_profile_synthetic"]))
        self.assertAlmostEqual(float(aim120["sensor_max_range_m"]), 16000.0, delta=1.0e-6)
        self.assertEqual(int(aim120["sensor_type"]), int(ef_py.SensorType.Radar))

        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(_DB_PATH))
        sim.set_time_step(1.0 / 60.0)

        _, _, aim9x_id = _spawn_and_fire_with_station(sim, 2, range_m=9000.0, bearing_deg=20.0)
        aim9x = _missile_runtime(sim, aim9x_id)
        self.assertAlmostEqual(float(aim9x["mass_total_kg"]), 85.0, delta=1.0e-6)
        self.assertAlmostEqual(float(aim9x["max_speed_mps"]), 850.0, delta=1.0e-6)
        self.assertAlmostEqual(float(aim9x["turn_rate_deg_s"]), 60.0, delta=1.0e-6)
        self.assertAlmostEqual(float(aim9x["guidance_max_lateral_g"]), 60.0, delta=1.0e-6)
        self.assertAlmostEqual(float(aim9x["fuse_distance_m"]), 8.0, delta=1.0e-6)
        self.assertEqual(str(aim9x["warhead_family"]), "blast_fragmentation")
        self.assertAlmostEqual(float(aim9x["warhead_mass_kg"]), 9.4, delta=1.0e-6)
        self.assertAlmostEqual(float(aim9x["warhead_lethal_radius_m"]), 8.0, delta=1.0e-6)
        self.assertAlmostEqual(float(aim9x["warhead_damage_scalar"]), 84.6, delta=1.0e-6)
        self.assertFalse(bool(aim9x["warhead_profile_synthetic"]))
        self.assertTrue(bool(aim9x["warhead_damage_scalar_synthetic"]))
        self.assertEqual(str(aim9x["fuze_type"]), "laser_proximity")
        self.assertAlmostEqual(float(aim9x["fuze_trigger_radius_m"]), 8.0, delta=1.0e-6)
        self.assertAlmostEqual(float(aim9x["fuze_delay_s"]), 0.008, delta=1.0e-6)
        self.assertAlmostEqual(float(aim9x["fuze_reliability"]), 0.92, delta=1.0e-6)
        self.assertFalse(bool(aim9x["fuze_profile_synthetic"]))
        self.assertEqual(int(aim9x["sensor_type"]), int(ef_py.SensorType.Infrared))

    def test_global_missile_tuning_can_override_definition_baseline(self) -> None:
        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(_DB_PATH))
        sim.set_time_step(1.0 / 60.0)

        tuning = ef_py.MissileTuning()
        tuning.max_speed = 910.0
        tuning.turn_rate = 44.0
        tuning.fuse_distance = 21.0
        tuning.sensor_max_range = 12345.0
        tuning.sensor_scan_period = 0.25
        tuning.sensor_track_memory_s = 3.0
        tuning.seeker_type = int(ef_py.SensorType.Radar)
        tuning.propellant_mass_kg = 33.0
        tuning.reference_area_m2 = 0.041
        tuning.boost_time_s = 1.7
        tuning.sustain_time_s = 0.3
        tuning.max_lateral_g = 47.0
        sim.set_missile_tuning(tuning)

        _, _, missile_id = _spawn_and_fire_with_station(sim, 2, range_m=9000.0, bearing_deg=15.0)
        runtime = _missile_runtime(sim, missile_id)
        self.assertAlmostEqual(float(runtime["mass_total_kg"]), 85.0, delta=1.0e-6)
        self.assertAlmostEqual(float(runtime["mass_fuel_kg"]), 33.0, delta=1.0e-6)
        self.assertAlmostEqual(float(runtime["reference_area_m2"]), 0.041, delta=1.0e-6)
        self.assertAlmostEqual(float(runtime["max_speed_mps"]), 910.0, delta=1.0e-6)
        self.assertAlmostEqual(float(runtime["turn_rate_deg_s"]), 44.0, delta=1.0e-6)
        self.assertAlmostEqual(float(runtime["fuse_distance_m"]), 21.0, delta=1.0e-6)
        self.assertAlmostEqual(float(runtime["sensor_max_range_m"]), 12345.0, delta=1.0e-6)
        self.assertAlmostEqual(float(runtime["sensor_scan_period_s"]), 0.25, delta=1.0e-6)
        self.assertAlmostEqual(float(runtime["sensor_track_memory_s"]), 3.0, delta=1.0e-6)
        self.assertAlmostEqual(float(runtime["guidance_max_lateral_g"]), 47.0, delta=1.0e-6)
        self.assertEqual(int(runtime["sensor_type"]), int(ef_py.SensorType.Radar))

    def test_global_fuze_profile_override_flows_into_runtime_and_effects_event(self) -> None:
        sim = _make_baseline_kernel()

        profile = ef_py.FuzeProfile()
        profile.type = "laser_proximity"
        profile.trigger_radius_m = 35.0
        profile.delay_s = 0.02
        profile.reliability = 0.88
        profile.synthetic = False
        profile.provenance = "test_authored_fuze_profile"

        tuning = sim.get_missile_tuning()
        tuning.fuze_profile = profile
        tuning.has_fuze_profile = True
        sim.set_missile_tuning(tuning)

        blue_id, red_id = _spawn_geometry_pair(
            sim,
            red_x=13000.0,
            red_y=9000.0,
            red_heading=270.0,
            red_vx=-260.0,
            red_vy=0.0,
        )
        missile_id = int(sim.fire_missile(blue_id, red_id))
        self.assertGreater(missile_id, 0)
        runtime = _missile_runtime(sim, missile_id)
        self.assertAlmostEqual(float(runtime["fuse_distance_m"]), 35.0, delta=1.0e-6)
        self.assertEqual(str(runtime["fuze_type"]), "laser_proximity")
        self.assertAlmostEqual(float(runtime["fuze_trigger_radius_m"]), 35.0, delta=1.0e-6)
        self.assertAlmostEqual(float(runtime["fuze_delay_s"]), 0.02, delta=1.0e-6)
        self.assertAlmostEqual(float(runtime["fuze_reliability"]), 0.88, delta=1.0e-6)
        self.assertFalse(bool(runtime["fuze_profile_synthetic"]))

        for step_idx in range(3600):
            if not sim.is_unit_active(missile_id):
                break
            _set_contacts(
                sim,
                missile_id,
                [
                    _relative_detection_from_truth(
                        sim,
                        missile_id,
                        red_id,
                        timestamp=step_idx * sim.get_time_step(),
                        local_sensor_hit=True,
                    )
                ],
            )
            sim.step()

        events = sim.export_recent_engagement_events()
        self.assertGreaterEqual(len(events.effects_events), 1)
        effects = events.effects_events[-1]
        self.assertEqual(str(effects.fuze_type), "laser_proximity")
        self.assertAlmostEqual(float(effects.fuze_trigger_radius_m), 35.0, delta=1.0e-6)
        self.assertAlmostEqual(float(effects.fuze_delay_s), 0.02, delta=1.0e-6)
        self.assertAlmostEqual(float(effects.fuze_reliability), 0.88, delta=1.0e-6)
        self.assertFalse(bool(effects.fuze_profile_synthetic))
        self.assertEqual(str(effects.fuze_signature_source), "target_projected_geometry")
        self.assertGreater(float(effects.fuze_target_signature), 1.0)
        self.assertGreater(float(effects.fuze_signature_scale), 0.0)
        self.assertLessEqual(float(effects.fuze_signature_scale), 1.15)
        self.assertAlmostEqual(
            float(effects.fuze_effective_reliability),
            min(1.0, 0.88 * float(effects.fuze_signature_scale)),
            delta=1.0e-6,
        )

    def test_fuze_delay_schedules_detonation_after_nearest_approach(self) -> None:
        sim = _make_baseline_kernel()
        sim.set_time_step(0.02)

        profile = ef_py.FuzeProfile()
        profile.type = "radar_proximity"
        profile.trigger_radius_m = 35.0
        profile.delay_s = 0.08
        profile.reliability = 1.0
        profile.synthetic = False
        profile.provenance = "test_delay_fuze_profile"

        tuning = sim.get_missile_tuning()
        tuning.fuze_profile = profile
        tuning.has_fuze_profile = True
        sim.set_missile_tuning(tuning)

        blue_id, red_id = _spawn_geometry_pair(
            sim,
            red_x=13000.0,
            red_y=9000.0,
            red_heading=270.0,
            red_vx=-260.0,
            red_vy=0.0,
        )
        missile_id = int(sim.fire_missile(blue_id, red_id))
        self.assertGreater(missile_id, 0)

        armed_seen = False
        for step_idx in range(3600):
            if not sim.is_unit_active(missile_id):
                break
            _set_contacts(
                sim,
                missile_id,
                [
                    _relative_detection_from_truth(
                        sim,
                        missile_id,
                        red_id,
                        timestamp=step_idx * sim.get_time_step(),
                        local_sensor_hit=True,
                    )
                ],
            )
            sim.step()
            if sim.is_unit_active(missile_id):
                runtime = _missile_runtime(sim, missile_id)
                if bool(runtime["fuze_delay_armed"]):
                    armed_seen = True
                    self.assertTrue(math.isfinite(float(runtime["fuze_nearest_approach_time_s"])))
                    self.assertEqual(str(runtime["fuze_signature_source"]), "target_rcs_aspect")
                    self.assertGreater(float(runtime["fuze_target_signature"]), 0.0)
                    self.assertGreater(float(runtime["fuze_signature_scale"]), 0.0)
                    self.assertLessEqual(float(runtime["fuze_effective_reliability"]), 1.0)
                    self.assertAlmostEqual(
                        float(runtime["fuze_detonation_time_s"]) -
                        float(runtime["fuze_nearest_approach_time_s"]),
                        0.08,
                        delta=sim.get_time_step() + 1.0e-6,
                    )
                    self.assertGreater(float(runtime["fuze_hit_probability"]), 0.0)

        self.assertTrue(armed_seen)
        events = sim.export_recent_engagement_events()
        self.assertGreaterEqual(len(events.effects_events), 1)
        effects = events.effects_events[-1]
        self.assertEqual(str(effects.fuze_type), "radar_proximity")
        self.assertAlmostEqual(float(effects.fuze_delay_s), 0.08, delta=1.0e-6)
        self.assertEqual(str(effects.fuze_signature_source), "target_rcs_aspect")
        self.assertGreater(float(effects.fuze_target_signature), 0.0)
        self.assertGreater(float(effects.fuze_signature_scale), 0.0)
        self.assertLessEqual(float(effects.fuze_effective_reliability), 1.0)
        self.assertGreater(float(effects.detonation_time_s), float(effects.nearest_approach_time_s))
        self.assertAlmostEqual(
            float(effects.detonation_time_s) - float(effects.nearest_approach_time_s),
            0.08,
            delta=sim.get_time_step() + 1.0e-6,
        )

    def test_fuze_event_records_detonation_attitude_evidence(self) -> None:
        sim = _make_baseline_kernel()
        sim.set_time_step(0.02)

        profile = ef_py.FuzeProfile()
        profile.type = "radar_proximity"
        profile.trigger_radius_m = 35.0
        profile.delay_s = 0.08
        profile.reliability = 1.0
        profile.synthetic = False
        profile.provenance = "test_detonation_attitude_evidence"

        tuning = sim.get_missile_tuning()
        tuning.fuze_profile = profile
        tuning.has_fuze_profile = True
        sim.set_missile_tuning(tuning)

        blue_id, red_id = _spawn_geometry_pair(
            sim,
            red_x=13000.0,
            red_y=9000.0,
            red_heading=270.0,
            red_vx=-260.0,
            red_vy=0.0,
        )
        missile_id = int(sim.fire_missile(blue_id, red_id))
        self.assertGreater(missile_id, 0)

        armed_attitude: tuple[float, float, float] | None = None
        for step_idx in range(3600):
            if not sim.is_unit_active(missile_id):
                break
            _set_contacts(
                sim,
                missile_id,
                [
                    _relative_detection_from_truth(
                        sim,
                        missile_id,
                        red_id,
                        timestamp=step_idx * sim.get_time_step(),
                        local_sensor_hit=True,
                    )
                ],
            )
            sim.step()
            if sim.is_unit_active(missile_id):
                runtime = _missile_runtime(sim, missile_id)
                if bool(runtime["fuze_delay_armed"]):
                    armed_attitude = (
                        float(runtime["fuze_detonation_heading_deg"]),
                        float(runtime["fuze_detonation_pitch_deg"]),
                        float(runtime["fuze_detonation_roll_deg"]),
                    )
                    self.assertTrue(all(math.isfinite(value) for value in armed_attitude))
                    break

        self.assertIsNotNone(armed_attitude)
        while sim.is_unit_active(missile_id):
            sim.step()

        events = sim.export_recent_engagement_events()
        self.assertGreaterEqual(len(events.effects_events), 1)
        effects = events.effects_events[-1]
        assert armed_attitude is not None
        self.assertAlmostEqual(float(effects.detonation_heading_deg), armed_attitude[0], delta=1.0e-6)
        self.assertAlmostEqual(float(effects.detonation_pitch_deg), armed_attitude[1], delta=1.0e-6)
        self.assertAlmostEqual(float(effects.detonation_roll_deg), armed_attitude[2], delta=1.0e-6)
        self.assertEqual(str(effects.fuze_type), "radar_proximity")

    def test_contact_fuze_does_not_trigger_from_near_miss_radius(self) -> None:
        def run_with_fuze(fuze_type: str) -> tuple[dict[str, float | bool], object]:
            sim = _make_baseline_kernel()
            sim.set_time_step(0.02)

            profile = ef_py.FuzeProfile()
            profile.type = fuze_type
            profile.trigger_radius_m = 35.0
            profile.delay_s = 0.0
            profile.reliability = 1.0
            profile.synthetic = False
            profile.provenance = "test_fuze_type_trigger_semantics"

            tuning = sim.get_missile_tuning()
            tuning.fuze_profile = profile
            tuning.has_fuze_profile = True
            sim.set_missile_tuning(tuning)

            blue_id, red_id = _spawn_geometry_pair(
                sim,
                red_x=0.0,
                red_y=22000.0,
                red_heading=180.0,
                red_vx=0.0,
                red_vy=-250.0,
            )
            missile_id = int(sim.fire_missile(blue_id, red_id))
            self.assertGreater(missile_id, 0)

            result = _drive_missile_with_truth_track(
                sim,
                missile_id,
                red_id,
                max_steps=3600,
            )
            return result, sim.export_recent_engagement_events()

        proximity_result, proximity_events = run_with_fuze("radar_proximity")
        self.assertFalse(bool(proximity_result["missile_active"]))
        self.assertLess(float(proximity_result["truth_min_dist_m"]), 35.0)
        self.assertGreaterEqual(len(proximity_events.effects_events), 1)
        proximity_effect = proximity_events.effects_events[-1]
        self.assertEqual(str(proximity_effect.trigger_type), "proximity_fuze")
        self.assertEqual(str(proximity_effect.fuze_type), "radar_proximity")
        self.assertFalse(bool(proximity_effect.direct_hitbox_intersection))
        self.assertGreater(int(proximity_effect.projected_hitbox_count), 0)

        contact_result, contact_events = run_with_fuze("contact")
        self.assertFalse(bool(contact_result["missile_active"]))
        self.assertLess(float(contact_result["truth_min_dist_m"]), 35.0)
        self.assertEqual(len(contact_events.effects_events), 0)
        self.assertEqual(len(contact_events.damage_reports), 0)

    def test_contact_fuze_records_surface_and_penetration_evidence(self) -> None:
        sim = _make_baseline_kernel()
        sim.set_time_step(0.02)

        profile = ef_py.FuzeProfile()
        profile.type = "impact"
        profile.trigger_radius_m = 0.25
        profile.delay_s = 0.0
        profile.reliability = 1.0
        profile.synthetic = False
        profile.provenance = "test_contact_penetration_evidence"

        tuning = sim.get_missile_tuning()
        tuning.fuze_profile = profile
        tuning.has_fuze_profile = True
        sim.set_missile_tuning(tuning)

        blue_id, red_id = _spawn_geometry_pair(
            sim,
            red_x=13000.0,
            red_y=9000.0,
            red_heading=270.0,
            red_vx=-260.0,
            red_vy=0.0,
        )
        missile_id = int(sim.fire_missile(blue_id, red_id))
        self.assertGreater(missile_id, 0)

        armed_seen = False
        for step_idx in range(3600):
            if not sim.is_unit_active(missile_id):
                break
            _set_contacts(
                sim,
                missile_id,
                [
                    _relative_detection_from_truth(
                        sim,
                        missile_id,
                        red_id,
                        timestamp=step_idx * sim.get_time_step(),
                        local_sensor_hit=True,
                    )
                ],
            )
            sim.step()
            if sim.is_unit_active(missile_id):
                runtime = _missile_runtime(sim, missile_id)
                if bool(runtime["fuze_delay_armed"]):
                    armed_seen = True
                    self.assertEqual(str(runtime["fuze_signature_source"]), "contact_surface")
                    self.assertAlmostEqual(
                        float(runtime["fuze_contact_surface_tolerance_m"]),
                        0.25,
                        delta=1.0e-6,
                    )
                    self.assertLessEqual(
                        float(runtime["fuze_contact_surface_distance_m"]),
                        float(runtime["fuze_contact_surface_tolerance_m"]) + 1.0e-6,
                    )
                    self.assertTrue(bool(runtime["fuze_contact_inside_hitbox"]))
                    self.assertGreater(float(runtime["fuze_contact_penetration_depth_m"]), 0.0)

        self.assertTrue(armed_seen)
        events = sim.export_recent_engagement_events()
        self.assertGreaterEqual(len(events.effects_events), 1)
        effects = events.effects_events[-1]
        self.assertEqual(str(effects.trigger_type), "contact_fuze")
        self.assertEqual(str(effects.fuze_type), "impact")
        self.assertEqual(str(effects.fuze_signature_source), "contact_surface")
        self.assertAlmostEqual(float(effects.fuze_contact_surface_tolerance_m), 0.25, delta=1.0e-6)
        self.assertLessEqual(
            float(effects.fuze_contact_surface_distance_m),
            float(effects.fuze_contact_surface_tolerance_m) + 1.0e-6,
        )
        self.assertTrue(bool(effects.fuze_contact_inside_hitbox))
        self.assertGreater(float(effects.fuze_contact_penetration_depth_m), 0.0)
        self.assertAlmostEqual(float(effects.fuze_target_signature), 0.0, delta=1.0e-6)
        self.assertAlmostEqual(float(effects.fuze_signature_scale), 1.0, delta=1.0e-6)
        self.assertAlmostEqual(float(effects.fuze_effective_reliability), 1.0, delta=1.0e-6)

    def test_timed_fuze_detonates_on_delay_without_proximity_gate(self) -> None:
        sim = _make_baseline_kernel()
        sim.set_time_step(0.02)

        profile = ef_py.FuzeProfile()
        profile.type = "timed"
        profile.trigger_radius_m = 35.0
        profile.delay_s = 0.10
        profile.reliability = 1.0
        profile.synthetic = False
        profile.provenance = "test_timed_fuze_independent_trigger"

        tuning = sim.get_missile_tuning()
        tuning.fuze_profile = profile
        tuning.has_fuze_profile = True
        sim.set_missile_tuning(tuning)

        blue_id, red_id = _spawn_geometry_pair(
            sim,
            red_x=0.0,
            red_y=26000.0,
            red_heading=180.0,
            red_vx=0.0,
            red_vy=-250.0,
        )
        missile_id = int(sim.fire_missile(blue_id, red_id))
        self.assertGreater(missile_id, 0)

        launch_time = 0.0
        for step_idx in range(60):
            if not sim.is_unit_active(missile_id):
                break
            _set_contacts(
                sim,
                missile_id,
                [
                    _relative_detection_from_truth(
                        sim,
                        missile_id,
                        red_id,
                        timestamp=step_idx * sim.get_time_step(),
                        local_sensor_hit=True,
                    )
                ],
            )
            sim.step()

        self.assertFalse(sim.is_unit_active(missile_id))
        events = sim.export_recent_engagement_events()
        self.assertEqual(len(events.effects_events), 1)
        self.assertEqual(len(events.damage_reports), 1)

        effects = events.effects_events[-1]
        report = events.damage_reports[-1]
        self.assertEqual(str(effects.trigger_type), "timed_fuze")
        self.assertEqual(str(effects.fuze_type), "timed")
        self.assertEqual(str(effects.outcome_state), "detonated_no_effect")
        self.assertGreater(float(effects.miss_distance_m), 1000.0)
        self.assertFalse(bool(effects.direct_hitbox_intersection))
        self.assertEqual(int(effects.projected_hitbox_count), 0)
        self.assertAlmostEqual(float(effects.fuze_delay_s), 0.10, delta=1.0e-6)
        self.assertAlmostEqual(
            float(effects.detonation_time_s) - launch_time,
            0.10,
            delta=(2.0 * sim.get_time_step()) + 1.0e-6,
        )
        self.assertAlmostEqual(float(report.system_health_delta), 0.0, delta=1.0e-6)
        self.assertFalse(bool(report.destroyed))

    def test_global_warhead_profile_override_flows_into_runtime_and_effects_event(self) -> None:
        sim = _make_baseline_kernel()

        profile = ef_py.WarheadProfile()
        profile.family = "continuous_rod"
        profile.mass_kg = 12.5
        profile.lethal_radius_m = 35.0
        profile.damage_scalar = 77.0
        profile.synthetic = False
        profile.damage_scalar_synthetic = False
        profile.provenance = "test_authored_profile"

        tuning = sim.get_missile_tuning()
        tuning.warhead_profile = profile
        tuning.has_warhead_profile = True
        sim.set_missile_tuning(tuning)

        blue_id, red_id = _spawn_geometry_pair(
            sim,
            red_x=13000.0,
            red_y=9000.0,
            red_heading=270.0,
            red_vx=-260.0,
            red_vy=0.0,
        )
        missile_id = int(sim.fire_missile(blue_id, red_id))
        self.assertGreater(missile_id, 0)
        runtime = _missile_runtime(sim, missile_id)
        self.assertAlmostEqual(float(runtime["fuse_distance_m"]), 35.0, delta=1.0e-6)
        self.assertAlmostEqual(float(runtime["damage"]), 77.0, delta=1.0e-6)
        self.assertEqual(str(runtime["warhead_family"]), "continuous_rod")
        self.assertAlmostEqual(float(runtime["warhead_mass_kg"]), 12.5, delta=1.0e-6)
        self.assertFalse(bool(runtime["warhead_profile_synthetic"]))
        self.assertFalse(bool(runtime["warhead_damage_scalar_synthetic"]))

        for step_idx in range(3600):
            if not sim.is_unit_active(missile_id):
                break
            _set_contacts(
                sim,
                missile_id,
                [
                    _relative_detection_from_truth(
                        sim,
                        missile_id,
                        red_id,
                        timestamp=step_idx * sim.get_time_step(),
                        local_sensor_hit=True,
                    )
                ],
            )
            sim.step()

        events = sim.export_recent_engagement_events()
        self.assertGreaterEqual(len(events.effects_events), 1)
        effects = events.effects_events[-1]
        self.assertEqual(str(effects.effect_family), "continuous_rod")
        self.assertAlmostEqual(float(effects.warhead_mass_kg), 12.5, delta=1.0e-6)
        self.assertAlmostEqual(float(effects.warhead_lethal_radius_m), 35.0, delta=1.0e-6)
        self.assertFalse(bool(effects.warhead_profile_synthetic))
        self.assertFalse(bool(effects.damage_scalar_synthetic))
        self.assertEqual(str(effects.fuze_type), "proximity")
        self.assertAlmostEqual(float(effects.fuze_trigger_radius_m), 35.0, delta=1.0e-6)
        self.assertTrue(bool(effects.fuze_profile_synthetic))

    def test_min_launch_range_rejects_without_consuming_ammo_or_cooldown(self) -> None:
        sim = _make_kernel()
        tuning = sim.get_missile_tuning()
        tuning.min_launch_range_m = 15000.0
        sim.set_missile_tuning(tuning)

        blue_id, red_id = _spawn_pair(sim)
        sim.set_weapon_cooldown(blue_id, 10.0, -1.0)
        _set_contacts(
            sim,
            blue_id,
            [_make_detection(red_id, range_m=12000.0, bearing_deg=0.0, local_sensor_hit=True)],
        )

        blocked_id = int(sim.fire_missile(blue_id, red_id))
        self.assertEqual(blocked_id, 0)
        blocked_obs = sim.get_agent_observation(blue_id)
        self.assertEqual(int(getattr(blocked_obs, "missiles_remaining", -1)), 4)
        self.assertTrue(bool(getattr(blocked_obs, "can_fire", False)))

        _set_contacts(
            sim,
            blue_id,
            [_make_detection(red_id, range_m=22000.0, bearing_deg=0.0, local_sensor_hit=True)],
        )
        fired_id = int(sim.fire_missile(blue_id, red_id))
        self.assertGreater(fired_id, 0)
        post_fire = sim.get_agent_observation(blue_id)
        self.assertEqual(int(getattr(post_fire, "missiles_remaining", -1)), 3)
        self.assertFalse(bool(getattr(post_fire, "can_fire", True)))

    def test_off_boresight_cap_rejects_without_consuming_ammo_or_cooldown(self) -> None:
        sim = _make_kernel()
        tuning = sim.get_missile_tuning()
        tuning.max_launch_off_boresight_deg = 10.0
        sim.set_missile_tuning(tuning)

        blue_id, red_id = _spawn_pair(sim)
        sim.set_weapon_cooldown(blue_id, 10.0, -1.0)
        _set_contacts(
            sim,
            blue_id,
            [_make_detection(red_id, range_m=22000.0, bearing_deg=25.0, local_sensor_hit=True)],
        )

        blocked_id = int(sim.fire_missile(blue_id, red_id))
        self.assertEqual(blocked_id, 0)
        blocked_obs = sim.get_agent_observation(blue_id)
        self.assertEqual(int(getattr(blocked_obs, "missiles_remaining", -1)), 4)
        self.assertTrue(bool(getattr(blocked_obs, "can_fire", False)))

        _set_contacts(
            sim,
            blue_id,
            [_make_detection(red_id, range_m=22000.0, bearing_deg=5.0, local_sensor_hit=True)],
        )
        fired_id = int(sim.fire_missile(blue_id, red_id))
        self.assertGreater(fired_id, 0)
        post_fire = sim.get_agent_observation(blue_id)
        self.assertEqual(int(getattr(post_fire, "missiles_remaining", -1)), 3)
        self.assertFalse(bool(getattr(post_fire, "can_fire", True)))

    def test_lobl_requirement_rejects_nonlocal_track_without_consuming_ammo_or_cooldown(self) -> None:
        sim = _make_kernel()
        tuning = sim.get_missile_tuning()
        tuning.lobl_required = True
        sim.set_missile_tuning(tuning)

        blue_id, red_id = _spawn_pair(sim)
        sim.set_weapon_cooldown(blue_id, 10.0, -1.0)
        _set_contacts(
            sim,
            blue_id,
            [_make_detection(red_id, range_m=22000.0, bearing_deg=0.0, local_sensor_hit=False)],
        )

        blocked_id = int(sim.fire_missile(blue_id, red_id))
        self.assertEqual(blocked_id, 0)
        blocked_obs = sim.get_agent_observation(blue_id)
        self.assertEqual(int(getattr(blocked_obs, "missiles_remaining", -1)), 4)
        self.assertTrue(bool(getattr(blocked_obs, "can_fire", False)))

        _set_contacts(
            sim,
            blue_id,
            [_make_detection(red_id, range_m=22000.0, bearing_deg=0.0, local_sensor_hit=True)],
        )
        fired_id = int(sim.fire_missile(blue_id, red_id))
        self.assertGreater(fired_id, 0)
        post_fire = sim.get_agent_observation(blue_id)
        self.assertEqual(int(getattr(post_fire, "missiles_remaining", -1)), 3)
        self.assertFalse(bool(getattr(post_fire, "can_fire", True)))

    def test_missile_tuning_roundtrip_shared_api(self) -> None:
        sim = _make_kernel()

        tuning = ef_py.MissileTuning()
        tuning.max_speed = 1234.0
        tuning.turn_rate = 27.5
        tuning.nav_gain = 4.2
        tuning.seeker_type = int(ef_py.SensorType.Radar)
        tuning.bearing_filter_tau_s = 0.07
        tuning.elevation_filter_tau_s = 0.11
        tuning.range_filter_tau_s = 0.19
        tuning.track_break_time_s = 1.35
        tuning.boost_time_s = 2.8
        tuning.sustain_time_s = 1.1
        tuning.boost_thrust_n = 21000.0
        tuning.sustain_thrust_n = 7200.0
        tuning.reference_area_m2 = 0.031
        tuning.cd0_subsonic = 0.24
        tuning.cd0_supersonic = 0.68
        tuning.induced_drag_k = 7.5
        tuning.propellant_mass_kg = 24.0
        tuning.max_lateral_g = 28.0
        tuning.autopilot_tau_s = 0.16
        tuning.max_accel_response_g_per_s = 95.0
        tuning.lobl_required = True
        tuning.midcourse_datalink_supported = True
        sim.set_missile_tuning(tuning)

        got = sim.get_missile_tuning()
        self.assertEqual(got.seeker_type, int(ef_py.SensorType.Radar))
        self.assertAlmostEqual(got.max_speed, 1234.0)
        self.assertAlmostEqual(got.turn_rate, 27.5)
        self.assertAlmostEqual(got.nav_gain, 4.2)
        self.assertAlmostEqual(got.bearing_filter_tau_s, 0.07)
        self.assertAlmostEqual(got.elevation_filter_tau_s, 0.11)
        self.assertAlmostEqual(got.range_filter_tau_s, 0.19)
        self.assertAlmostEqual(got.track_break_time_s, 1.35)
        self.assertAlmostEqual(got.boost_time_s, 2.8)
        self.assertAlmostEqual(got.sustain_time_s, 1.1)
        self.assertAlmostEqual(got.boost_thrust_n, 21000.0)
        self.assertAlmostEqual(got.sustain_thrust_n, 7200.0)
        self.assertAlmostEqual(got.reference_area_m2, 0.031)
        self.assertAlmostEqual(got.cd0_subsonic, 0.24)
        self.assertAlmostEqual(got.cd0_supersonic, 0.68)
        self.assertAlmostEqual(got.induced_drag_k, 7.5)
        self.assertAlmostEqual(got.propellant_mass_kg, 24.0)
        self.assertAlmostEqual(got.max_lateral_g, 28.0)
        self.assertAlmostEqual(got.autopilot_tau_s, 0.16)
        self.assertAlmostEqual(got.max_accel_response_g_per_s, 95.0)
        self.assertTrue(got.lobl_required)
        self.assertTrue(got.midcourse_datalink_supported)

    def test_seeker_activation_range_requires_local_terminal_contact(self) -> None:
        sim = _make_kernel()
        tuning = sim.get_missile_tuning()
        tuning.seeker_activation_range_m = 8000.0
        tuning.midcourse_datalink_supported = True
        tuning.track_break_time_s = 0.3
        tuning.range_filter_tau_s = 0.0
        sim.set_missile_tuning(tuning)

        blue_id, red_id = _spawn_pair(sim)
        _set_contacts(
            sim,
            blue_id,
            [_make_detection(red_id, range_m=30000.0, bearing_deg=0.0, local_sensor_hit=True)],
        )
        missile_id = int(sim.fire_missile(blue_id, red_id))
        self.assertGreater(missile_id, 0)

        runtime = _missile_runtime(sim, missile_id)
        self.assertFalse(bool(runtime["terminal_seeker_active"]))
        self.assertTrue(bool(runtime["midcourse_datalink_supported"]))
        self.assertAlmostEqual(float(runtime["seeker_activation_range_m"]), 8000.0, delta=1.0e-6)

        for step_idx in range(12):
            t_s = step_idx * sim.get_time_step()
            _set_contacts(
                sim,
                missile_id,
                [_make_detection(red_id, range_m=25000.0, bearing_deg=12.0, local_sensor_hit=False, timestamp=t_s)],
            )
            sim.step()

        midcourse_runtime = _missile_runtime(sim, missile_id)
        self.assertTrue(bool(midcourse_runtime["seeker_has_valid_track"]))
        self.assertEqual(int(midcourse_runtime["seeker_mode"]), 0)
        self.assertFalse(bool(midcourse_runtime["terminal_seeker_active"]))
        self.assertGreater(float(midcourse_runtime["filtered_range_m"]), 8000.0)

        _set_contacts(
            sim,
            missile_id,
            [_make_detection(red_id, range_m=6000.0, bearing_deg=6.0, local_sensor_hit=False, timestamp=1.0)],
        )
        sim.step()
        activated_runtime = _missile_runtime(sim, missile_id)
        self.assertTrue(bool(activated_runtime["terminal_seeker_active"]))
        self.assertLess(float(activated_runtime["filtered_range_m"]), 8000.0)

        _set_contacts(sim, missile_id, [])
        for _ in range(30):
            sim.step()

        no_local_terminal_runtime = _missile_runtime(sim, missile_id)
        self.assertFalse(bool(no_local_terminal_runtime["seeker_has_valid_track"]))
        self.assertEqual(int(no_local_terminal_runtime["seeker_mode"]), 2)
        self.assertTrue(bool(no_local_terminal_runtime["terminal_seeker_active"]))

        _set_contacts(
            sim,
            missile_id,
            [_make_detection(red_id, range_m=5500.0, bearing_deg=3.0, local_sensor_hit=True, timestamp=2.0)],
        )
        sim.step()
        local_terminal_runtime = _missile_runtime(sim, missile_id)
        self.assertTrue(bool(local_terminal_runtime["seeker_has_valid_track"]))
        self.assertEqual(int(local_terminal_runtime["seeker_mode"]), 0)
        self.assertTrue(bool(local_terminal_runtime["terminal_seeker_active"]))
        self.assertLess(float(local_terminal_runtime["filtered_range_m"]), 8000.0)

    def test_without_midcourse_datalink_nonlocal_updates_do_not_drive_track(self) -> None:
        sim = _make_kernel()
        tuning = sim.get_missile_tuning()
        tuning.seeker_activation_range_m = 8000.0
        tuning.midcourse_datalink_supported = False
        tuning.track_break_time_s = 0.1
        sim.set_missile_tuning(tuning)

        blue_id, red_id = _spawn_pair(sim)
        _set_contacts(
            sim,
            blue_id,
            [_make_detection(red_id, range_m=30000.0, bearing_deg=0.0, local_sensor_hit=True)],
        )
        missile_id = int(sim.fire_missile(blue_id, red_id))
        self.assertGreater(missile_id, 0)

        for step_idx in range(20):
            t_s = step_idx * sim.get_time_step()
            _set_contacts(
                sim,
                missile_id,
                [_make_detection(red_id, range_m=22000.0, bearing_deg=15.0, local_sensor_hit=False, timestamp=t_s)],
            )
            sim.step()

        runtime = _missile_runtime(sim, missile_id)
        self.assertFalse(bool(runtime["midcourse_datalink_supported"]))
        self.assertFalse(bool(runtime["terminal_seeker_active"]))
        self.assertFalse(bool(runtime["seeker_has_valid_track"]))
        self.assertEqual(int(runtime["seeker_mode"]), 2)

    def test_guidance_keeps_assigned_target_even_if_stronger_nonassigned_contact_appears(self) -> None:
        sim = _make_kernel()
        blue_id, red_id = _spawn_pair(sim)
        intruder_id = int(
            sim.spawn_unit(
                ef_py.Side.Red,
                "Aircraft",
                5000.0,
                26000.0,
                5000.0,
                180.0,
                0.0,
                0.0,
                0.0,
                -250.0,
                0.0,
            )
        )

        _set_contacts(
            sim,
            blue_id,
            [_make_detection(red_id, range_m=30000.0, bearing_deg=0.0, signal_strength=1.0)],
        )
        missile_id = int(sim.fire_missile(blue_id, red_id))
        self.assertGreater(missile_id, 0)

        for step_idx in range(6):
            t_s = step_idx * sim.get_time_step()
            _set_contacts(
                sim,
                missile_id,
                [_make_detection(red_id, range_m=25000.0, bearing_deg=4.0, signal_strength=0.6, timestamp=t_s)],
            )
            sim.step()

        for step_idx in range(6, 12):
            t_s = step_idx * sim.get_time_step()
            _set_contacts(
                sim,
                missile_id,
                [_make_detection(intruder_id, range_m=18000.0, bearing_deg=20.0, signal_strength=4.0, timestamp=t_s)],
            )
            sim.step()

        runtime = _missile_runtime(sim, missile_id)
        self.assertTrue(bool(runtime["seeker_has_valid_track"]))
        self.assertEqual(int(runtime["seeker_mode"]), 1)

    def test_terminal_seeker_activation_latches_after_entry(self) -> None:
        sim = _make_kernel()
        tuning = sim.get_missile_tuning()
        tuning.seeker_activation_range_m = 8000.0
        tuning.midcourse_datalink_supported = True
        tuning.track_break_time_s = 0.5
        tuning.range_filter_tau_s = 0.0
        sim.set_missile_tuning(tuning)

        blue_id, red_id = _spawn_pair(sim)
        _set_contacts(
            sim,
            blue_id,
            [_make_detection(red_id, range_m=30000.0, bearing_deg=0.0, local_sensor_hit=True)],
        )
        missile_id = int(sim.fire_missile(blue_id, red_id))
        self.assertGreater(missile_id, 0)

        _set_contacts(
            sim,
            missile_id,
            [_make_detection(red_id, range_m=6000.0, bearing_deg=2.0, local_sensor_hit=True, timestamp=0.0)],
        )
        sim.step()
        activated_runtime = _missile_runtime(sim, missile_id)
        self.assertTrue(bool(activated_runtime["terminal_seeker_active"]))
        self.assertLess(float(activated_runtime["filtered_range_m"]), 8000.0)

        _set_contacts(
            sim,
            missile_id,
            [_make_detection(red_id, range_m=12000.0, bearing_deg=2.5, local_sensor_hit=False, timestamp=sim.get_time_step())],
        )
        sim.step()
        post_expand_runtime = _missile_runtime(sim, missile_id)
        self.assertTrue(bool(post_expand_runtime["terminal_seeker_active"]))
        self.assertTrue(bool(post_expand_runtime["seeker_has_valid_track"]))
        self.assertEqual(int(post_expand_runtime["seeker_mode"]), 1)
        self.assertLess(float(post_expand_runtime["filtered_range_m"]), 8000.0)

        _set_contacts(sim, missile_id, [])
        for _ in range(40):
            sim.step()

        decayed_runtime = _missile_runtime(sim, missile_id)
        self.assertTrue(bool(decayed_runtime["terminal_seeker_active"]))
        self.assertFalse(bool(decayed_runtime["seeker_has_valid_track"]))
        self.assertEqual(int(decayed_runtime["seeker_mode"]), 2)

    def test_terminal_proximity_fuze_does_not_resolve_hit_after_terminal_track_fully_decays(self) -> None:
        sim = _make_kernel()
        tuning = sim.get_missile_tuning()
        tuning.seeker_activation_range_m = 8000.0
        tuning.midcourse_datalink_supported = True
        tuning.track_break_time_s = 0.12
        tuning.range_filter_tau_s = 0.0
        tuning.max_speed = 120.0
        tuning.boost_time_s = 0.0
        tuning.sustain_time_s = 0.0
        tuning.reference_area_m2 = 0.01
        tuning.fuse_distance = 50.0
        sim.set_missile_tuning(tuning)

        blue_id, red_id = _spawn_pair(sim)
        _set_contacts(
            sim,
            blue_id,
            [_make_detection(red_id, range_m=9000.0, bearing_deg=0.0, local_sensor_hit=True)],
        )
        missile_id = int(sim.fire_missile(blue_id, red_id))
        self.assertGreater(missile_id, 0)

        target_health_before = list(sim.get_unit_health(red_id))

        for step_idx in range(6):
            t_s = step_idx * sim.get_time_step()
            _set_contacts(
                sim,
                missile_id,
                [_make_detection(red_id, range_m=40.0, bearing_deg=0.0, local_sensor_hit=True, timestamp=t_s)],
            )
            sim.step()

        activated_runtime = _missile_runtime(sim, missile_id)
        self.assertTrue(bool(activated_runtime["terminal_seeker_active"]))
        self.assertTrue(bool(activated_runtime["seeker_has_valid_track"]))

        for _ in range(20):
            _set_contacts(sim, missile_id, [])
            sim.step()
            if not sim.is_unit_active(missile_id):
                break

        self.assertTrue(sim.is_unit_active(red_id))
        self.assertEqual(list(sim.get_unit_health(red_id)), target_health_before)

    def test_structured_air_target_uses_damage_state_instead_of_hp_first_kill(self) -> None:
        sim = ef_py.SimulationKernel()
        sim.reset(20260526)
        self.assertTrue(sim.load_database(_DB_PATH))

        attacker_id, target_id = _spawn_structured_f16_pair(sim)

        health_before = [float(value) for value in sim.get_unit_health(target_id)]
        damage_before = [float(value) for value in sim.get_unit_damage_state(target_id)]
        self.assertEqual(health_before, [100.0, 100.0])
        self.assertEqual(damage_before, [1.0, 1.0, 1.0, 1.0])

        self.assertTrue(bool(sim.debug_apply_proximity_hit(attacker_id, target_id, 240.0, 80.0)))

        health_after = [float(value) for value in sim.get_unit_health(target_id)]
        damage_after = [float(value) for value in sim.get_unit_damage_state(target_id)]
        self.assertTrue(sim.is_unit_active(target_id))
        self.assertEqual(health_after, health_before)
        self.assertLess(min(damage_after), min(damage_before))
        self.assertGreater(float(damage_after[3]), 0.0)

        events = sim.export_recent_engagement_events()
        self.assertEqual(len(events.effects_events), 1)
        self.assertEqual(len(events.damage_reports), 1)
        effect = events.effects_events[0]
        report = events.damage_reports[0]
        self.assertAlmostEqual(float(effect.miss_distance_m), 0.0, delta=1.0e-6)
        self.assertAlmostEqual(float(effect.detonation_local_forward_m), 0.0, delta=1.0e-6)
        self.assertAlmostEqual(float(effect.detonation_local_right_m), 0.0, delta=1.0e-6)
        self.assertAlmostEqual(float(effect.detonation_local_up_m), 0.0, delta=1.0e-6)
        self.assertAlmostEqual(float(report.hp_delta), 0.0, delta=1.0e-6)
        self.assertLess(float(report.system_health_delta), 0.0)
        self.assertFalse(bool(report.destroyed))
        self.assertNotEqual(str(report.loss_state_to), "lost")

    def test_structured_air_damage_does_not_write_rl_score_from_physical_effects(self) -> None:
        sim = ef_py.SimulationKernel()
        sim.reset(20260526)
        self.assertTrue(sim.load_database(_DB_PATH))
        attacker_id, target_id = _spawn_structured_f16_pair(sim)

        attacker_reward_before = float(sim.get_agent_observation(attacker_id).total_reward)
        target_health_before = [float(value) for value in sim.get_unit_health(target_id)]

        self.assertTrue(
            bool(
                sim.debug_apply_local_proximity_hit(
                    attacker_id,
                    target_id,
                    -0.753,
                    4.0,
                    0.0,
                    240.0,
                    80.0,
                )
            )
        )

        attacker_reward_after = float(sim.get_agent_observation(attacker_id).total_reward)
        events = sim.export_recent_engagement_events()
        self.assertEqual([float(value) for value in sim.get_unit_health(target_id)], target_health_before)
        self.assertEqual(len(events.damage_reports), 1)
        self.assertLess(float(events.damage_reports[0].system_health_delta), 0.0)
        self.assertAlmostEqual(attacker_reward_after, attacker_reward_before, delta=1.0e-6)

    def test_phase2_aircraft_hitboxes_produce_distinct_subsystem_effects(self) -> None:
        cases = {
            "nose_radar": {
                "local": (6.024, 0.0, 0.0),
                "expect_sensor_drop": True,
                "expect_thrust_drop": False,
                "expect_fuel_leak": False,
                "expect_structure_drop": True,
                "expect_flight_control_drop": True,
            },
            "fuselage_engine_fuel": {
                "local": (0.0, 0.0, 0.3),
                "expect_sensor_drop": False,
                "expect_thrust_drop": True,
                "expect_fuel_leak": True,
                "expect_structure_drop": True,
                "expect_flight_control_drop": False,
            },
            "wing_flight_control": {
                "local": (-0.753, 4.0, 0.0),
                "expect_sensor_drop": False,
                "expect_thrust_drop": False,
                "expect_fuel_leak": False,
                "expect_structure_drop": True,
                "expect_flight_control_drop": True,
            },
        }

        for name, case in cases.items():
            with self.subTest(hitbox=name):
                sim = ef_py.SimulationKernel()
                sim.reset(20260526)
                self.assertTrue(sim.load_database(_DB_PATH))
                attacker_id, target_id = _spawn_structured_f16_pair(sim)

                sensor_before = sim.get_sensor_debug_view(target_id)
                flight_before = sim.get_flight_dynamics_debug_view(target_id)
                damage_before = [float(value) for value in sim.get_unit_damage_state(target_id)]
                local_forward, local_right, local_up = case["local"]

                self.assertTrue(
                    bool(
                        sim.debug_apply_local_proximity_hit(
                            attacker_id,
                            target_id,
                            float(local_forward),
                            float(local_right),
                            float(local_up),
                            240.0,
                            80.0,
                        )
                    )
                )

                sensor_after = sim.get_sensor_debug_view(target_id)
                damage_after = [float(value) for value in sim.get_unit_damage_state(target_id)]
                sim.step()
                flight_after = sim.get_flight_dynamics_debug_view(target_id)
                self.assertTrue(sim.is_unit_active(target_id))
                self.assertEqual([float(value) for value in sim.get_unit_health(target_id)], [100.0, 100.0])
                self.assertLess(min(damage_after), min(damage_before))

                if case["expect_sensor_drop"]:
                    self.assertLess(float(sensor_after.max_range), float(sensor_before.max_range))
                    self.assertLess(float(damage_after[2]), float(damage_before[2]))
                else:
                    self.assertAlmostEqual(float(sensor_after.max_range), float(sensor_before.max_range), delta=1.0e-6)

                if case["expect_thrust_drop"]:
                    self.assertLess(float(flight_after.mil_thrust_n), float(flight_before.mil_thrust_n))
                    self.assertLess(float(flight_after.ab_thrust_n), float(flight_before.ab_thrust_n))
                else:
                    self.assertAlmostEqual(float(flight_after.mil_thrust_n), float(flight_before.mil_thrust_n), delta=1.0e-6)
                    self.assertAlmostEqual(float(flight_after.ab_thrust_n), float(flight_before.ab_thrust_n), delta=1.0e-6)

                if case["expect_fuel_leak"]:
                    self.assertGreater(float(flight_after.fuel_leak_rate_kg_s), float(flight_before.fuel_leak_rate_kg_s))
                else:
                    self.assertAlmostEqual(
                        float(flight_after.fuel_leak_rate_kg_s),
                        float(flight_before.fuel_leak_rate_kg_s),
                        delta=1.0e-6,
                    )

                if case["expect_flight_control_drop"]:
                    self.assertLess(float(flight_after.max_turn_rate), float(flight_before.max_turn_rate))
                else:
                    self.assertLessEqual(
                        float(flight_after.max_turn_rate),
                        float(flight_before.max_turn_rate),
                    )
                if case["expect_structure_drop"]:
                    self.assertLess(float(flight_after.max_g), float(flight_before.max_g))
                else:
                    self.assertAlmostEqual(float(flight_after.max_g), float(flight_before.max_g), delta=1.0e-6)

    def test_phase2_aircraft_damage_overlay_tracks_air_specific_subsystems(self) -> None:
        cases = {
            "nose_crew_avionics": {
                "local": (6.024, 0.0, 0.0),
                "drops": ("crew", "avionics", "structure", "flight_control"),
                "stable": ("propulsion", "fuel", "hydraulic"),
                "rises": ("fire",),
            },
            "fuselage_propulsion_fuel": {
                "local": (0.0, 0.0, 0.3),
                "drops": ("propulsion", "fuel", "avionics", "structure"),
                "stable": ("crew", "flight_control", "hydraulic"),
                "rises": ("fire", "fuel_leak"),
            },
            "wing_flight_control_hydraulic": {
                "local": (-0.753, 4.0, 0.0),
                "drops": ("flight_control", "hydraulic", "structure"),
                "stable": ("crew", "avionics", "fuel"),
                "rises": (),
            },
        }

        for name, case in cases.items():
            with self.subTest(hitbox=name):
                sim = ef_py.SimulationKernel()
                sim.reset(20260526)
                self.assertTrue(sim.load_database(_DB_PATH))
                attacker_id, target_id = _spawn_structured_f16_pair(sim)

                overlay_before = _aircraft_damage_overlay(sim, target_id)
                platform_before = [float(value) for value in sim.get_unit_damage_state(target_id)]
                flight_before = sim.get_flight_dynamics_debug_view(target_id)
                self.assertEqual(overlay_before["forced_landing"], 0.0)
                self.assertEqual(overlay_before["flight_control_kill"], 0.0)
                self.assertEqual(overlay_before["propulsion_kill"], 0.0)
                self.assertEqual(overlay_before["crew_kill"], 0.0)

                self.assertTrue(
                    bool(
                        sim.debug_apply_local_proximity_hit(
                            attacker_id,
                            target_id,
                            float(case["local"][0]),
                            float(case["local"][1]),
                            float(case["local"][2]),
                            240.0,
                            80.0,
                        )
                    )
                )

                overlay_after = _aircraft_damage_overlay(sim, target_id)
                platform_after = [float(value) for value in sim.get_unit_damage_state(target_id)]
                sim.step()
                flight_after_update = sim.get_flight_dynamics_debug_view(target_id)
                self.assertTrue(sim.is_unit_active(target_id))
                self.assertLess(min(platform_after), min(platform_before))

                for field in case["drops"]:
                    self.assertLess(overlay_after[field], overlay_before[field], field)
                for field in case["stable"]:
                    self.assertAlmostEqual(overlay_after[field], overlay_before[field], delta=1.0e-6, msg=field)
                for field in case["rises"]:
                    self.assertGreater(overlay_after[field], overlay_before[field], field)

                if "flight_control" in case["drops"]:
                    self.assertLess(platform_after[1], platform_before[1])
                    self.assertLess(float(flight_after_update.max_turn_rate), float(flight_before.max_turn_rate))
                    self.assertLess(float(flight_after_update.max_accel), float(flight_before.max_accel))
                if "avionics" in case["drops"] or "crew" in case["drops"]:
                    self.assertLess(platform_after[0], platform_before[0])
                if "structure" in case["drops"]:
                    self.assertLess(float(flight_after_update.max_g), float(flight_before.max_g))
                if "propulsion" in case["drops"]:
                    self.assertLess(float(flight_after_update.mil_thrust_n), float(flight_before.mil_thrust_n))
                    self.assertLess(float(flight_after_update.ab_thrust_n), float(flight_before.ab_thrust_n))
                if "fuel_leak" in case["rises"]:
                    self.assertGreater(
                        float(flight_after_update.fuel_leak_rate_kg_s),
                        float(flight_before.fuel_leak_rate_kg_s),
                    )

    def test_phase2_aileron_component_damage_derives_roll_axis_authority(self) -> None:
        sim = ef_py.SimulationKernel()
        sim.reset(20260526)
        self.assertTrue(sim.load_database(_DB_PATH))
        attacker_id, target_id = _spawn_structured_f16_pair(sim)

        overlay_before = _aircraft_damage_overlay(sim, target_id)
        flight_before = sim.get_flight_dynamics_debug_view(target_id)

        self.assertTrue(
            bool(
                sim.debug_apply_local_proximity_hit(
                    attacker_id,
                    target_id,
                    -0.8,
                    4.1,
                    0.0,
                    240.0,
                    80.0,
                )
            )
        )

        overlay_after = _aircraft_damage_overlay(sim, target_id)
        self.assertLess(overlay_after["roll_control"], overlay_before["roll_control"])
        self.assertGreater(overlay_after["control_asymmetry"], overlay_before["control_asymmetry"])
        self.assertAlmostEqual(
            overlay_after["pitch_control"],
            overlay_before["pitch_control"],
            delta=1.0e-6,
        )
        self.assertAlmostEqual(
            overlay_after["yaw_control"],
            overlay_before["yaw_control"],
            delta=1.0e-6,
        )

        sim.step()
        flight_after = sim.get_flight_dynamics_debug_view(target_id)
        self.assertTrue(sim.is_unit_active(target_id))
        self.assertLess(float(flight_after.max_turn_rate), float(flight_before.max_turn_rate))

    def test_phase2_named_control_components_derive_axis_specific_authority(
        self,
    ) -> None:
        cases = [
            (
                "F-16C_Block50",
                (-6.7, 0.0, 0.45),
                "rudder_actuator",
                {"yaw_control"},
                set(),
                set(),
            ),
            (
                "F-16C_Block50",
                (-0.2, 1.6, 0.0),
                "right_leading_edge_flap_actuator",
                {"roll_control", "pitch_control"},
                set(),
                {"control_asymmetry"},
            ),
            (
                "Su-35S_Flanker-E",
                (-9.2, 1.4, -0.15),
                "right_thrust_vector_actuator",
                {"pitch_control", "yaw_control"},
                set(),
                {"control_asymmetry"},
            ),
            (
                "MH-60R_MVP",
                (-1.0, 3.2, 2.5),
                "right_cyclic_servo",
                {"roll_control", "pitch_control"},
                set(),
                {"control_asymmetry"},
            ),
            (
                "MH-60R_MVP",
                (-1.0, 0.0, 2.5),
                "collective_servo",
                {"pitch_control"},
                {"roll_control", "yaw_control"},
                set(),
            ),
            (
                "MQ-9_Reaper",
                (-0.2, 2.8, 0.0),
                "right_inboard_flap_servo",
                {"roll_control", "pitch_control"},
                set(),
                {"control_asymmetry"},
            ),
        ]

        for target_type, local_impact, expected_component, drops, unchanged, rises in cases:
            with self.subTest(target_type=target_type, component=expected_component):
                overlay, _, event = _profiled_local_hit_overlay_for_target(
                    target_type,
                    "blast_fragmentation",
                    local_impact,
                    damage=120.0,
                    radius=35.0,
                )

                self.assertTrue(bool(event.direct_hitbox_intersection))
                self.assertEqual(str(event.component_primary_name), expected_component)
                self.assertEqual(str(event.component_primary_system), "flight_control")
                for field in drops:
                    self.assertLess(overlay[field], 1.0, field)
                for field in unchanged:
                    self.assertAlmostEqual(overlay[field], 1.0, delta=1.0e-6, msg=field)
                for field in rises:
                    self.assertGreater(overlay[field], 0.0, field)

    def test_phase2_avionics_and_crew_damage_derives_sensor_performance(self) -> None:
        cases = {
            "nose_cockpit_avionics": {
                "local": (6.024, 0.0, 0.0),
                "expect_sensor_degradation": True,
            },
            "wing_flight_control": {
                "local": (-0.753, 4.0, 0.0),
                "expect_sensor_degradation": False,
            },
        }

        for name, case in cases.items():
            with self.subTest(hitbox=name):
                sim = ef_py.SimulationKernel()
                sim.reset(20260526)
                self.assertTrue(sim.load_database(_DB_PATH))
                attacker_id, target_id = _spawn_structured_f16_pair(sim)

                sensor_before = sim.get_sensor_debug_view(target_id)
                overlay_before = _aircraft_damage_overlay(sim, target_id)
                self.assertGreater(float(sensor_before.max_range), 0.0)
                self.assertGreater(float(sensor_before.detection_prob), 0.0)

                self.assertTrue(
                    bool(
                        sim.debug_apply_local_proximity_hit(
                            attacker_id,
                            target_id,
                            float(case["local"][0]),
                            float(case["local"][1]),
                            float(case["local"][2]),
                            240.0,
                            80.0,
                        )
                    )
                )
                sim.step()

                overlay_after = _aircraft_damage_overlay(sim, target_id)
                sensor_after = sim.get_sensor_debug_view(target_id)
                self.assertTrue(sim.is_unit_active(target_id))

                if case["expect_sensor_degradation"]:
                    self.assertLess(overlay_after["avionics"], overlay_before["avionics"])
                    self.assertLess(overlay_after["crew"], overlay_before["crew"])
                    self.assertLess(float(sensor_after.max_range), float(sensor_before.max_range))
                    self.assertLess(float(sensor_after.detection_prob), float(sensor_before.detection_prob))
                    self.assertGreater(float(sensor_after.bearing_noise_std), float(sensor_before.bearing_noise_std))
                    self.assertGreater(float(sensor_after.range_noise_std), float(sensor_before.range_noise_std))
                    self.assertLess(float(sensor_after.track_memory_s), float(sensor_before.track_memory_s))
                else:
                    self.assertGreaterEqual(
                        overlay_after["avionics"],
                        overlay_before["avionics"] - 5.0e-4,
                    )
                    self.assertGreaterEqual(
                        overlay_after["crew"],
                        overlay_before["crew"] - 5.0e-4,
                    )
                    self.assertGreater(
                        float(sensor_after.max_range),
                        float(sensor_before.max_range) * 0.99,
                    )
                    self.assertGreater(
                        float(sensor_after.detection_prob),
                        float(sensor_before.detection_prob) * 0.99,
                    )

    def test_phase2_crew_consequences_distinguish_pilot_mission_and_command_roles(self) -> None:
        cases = [
            (
                "F-16C_Block50",
                (5.15, 0.0, 0.1),
                "cockpit_crew_station",
                "pilot",
                {"pilot", "crew", "flight_control"},
                {"mission_crew", "command_navigation"},
            ),
            (
                "E-3_Sentry_AWACS",
                (1.0, 1.8, 3.0),
                "mission_operator_consoles",
                "mission_crew",
                {"mission_crew", "crew", "avionics"},
                {"pilot", "command_navigation"},
            ),
            (
                "E-3_Sentry_AWACS",
                (15.5, 0.0, 0.0),
                "command_navigation_suite",
                "command_navigation",
                {"command_navigation", "crew", "avionics"},
                {"pilot", "mission_crew"},
            ),
        ]

        for target_type, local, expected_component, primary_role, drops, stable in cases:
            with self.subTest(target_type=target_type, component=expected_component):
                sim = _kernel_with_unit_overrides([])
                attacker_id, target_id = _spawn_attacker_and_named_target(sim, target_type)
                overlay_before = _aircraft_damage_overlay(sim, target_id)
                platform_before = [float(value) for value in sim.get_unit_damage_state(target_id)]
                flight_before = sim.get_flight_dynamics_debug_view(target_id)
                sensor_before = sim.get_sensor_debug_view(target_id)

                ok = sim.debug_apply_profiled_local_proximity_hit(
                    attacker_id,
                    target_id,
                    float(local[0]),
                    float(local[1]),
                    float(local[2]),
                    _make_warhead_profile("blast_fragmentation", damage=120.0, radius=35.0),
                )
                self.assertTrue(bool(ok))

                overlay, _, event = (
                    _aircraft_damage_overlay(sim, target_id),
                    [float(value) for value in sim.get_unit_damage_state(target_id)],
                    sim.export_recent_engagement_events().effects_events[0],
                )
                self.assertEqual(str(event.component_primary_name), expected_component)
                self.assertLess(overlay[primary_role], overlay_before[primary_role])
                for field in drops:
                    self.assertLess(overlay[field], overlay_before[field], field)
                for field in stable:
                    self.assertAlmostEqual(
                        overlay[field],
                        overlay_before[field],
                        delta=1.0e-6,
                        msg=field,
                    )

                sim.step()
                platform_after = [float(value) for value in sim.get_unit_damage_state(target_id)]
                flight_after = sim.get_flight_dynamics_debug_view(target_id)
                sensor_after = sim.get_sensor_debug_view(target_id)
                if primary_role == "pilot":
                    self.assertLess(platform_after[1], platform_before[1])
                    self.assertLess(float(flight_after.max_turn_rate), float(flight_before.max_turn_rate))
                else:
                    self.assertLess(platform_after[0], platform_before[0])
                    self.assertLess(float(sensor_after.max_range), float(sensor_before.max_range))
                    self.assertLess(float(sensor_after.detection_prob), float(sensor_before.detection_prob))

    def test_phase2_aircraft_fire_fuel_and_hydraulic_damage_cascade_over_time(self) -> None:
        sim = ef_py.SimulationKernel()
        sim.reset(20260526)
        self.assertTrue(sim.load_database(_DB_PATH))
        sim.set_time_step(0.5)
        attacker_id, target_id = _spawn_structured_f16_pair(sim)

        self.assertTrue(
            bool(
                sim.debug_apply_local_proximity_hit(
                    attacker_id,
                    target_id,
                    -0.8,
                    2.8,
                    0.0,
                    180.0,
                    80.0,
                )
            )
        )
        self.assertTrue(
            bool(
                sim.debug_apply_local_proximity_hit(
                    attacker_id,
                    target_id,
                    -0.8,
                    4.1,
                    0.0,
                    180.0,
                    80.0,
                )
            )
        )

        overlay_initial = _aircraft_damage_overlay(sim, target_id)
        fuel_initial = [float(value) for value in sim.get_unit_fuel(target_id)]
        mass_initial = [float(value) for value in sim.debug_get_mass_state(target_id)]
        platform_initial = [float(value) for value in sim.get_unit_damage_state(target_id)]
        flight_initial = sim.get_flight_dynamics_debug_view(target_id)
        self.assertGreater(overlay_initial["fuel_leak"], 0.0)
        self.assertGreater(overlay_initial["fire"], 0.0)

        for _ in range(40):
            sim.step()

        overlay_after = _aircraft_damage_overlay(sim, target_id)
        fuel_after = [float(value) for value in sim.get_unit_fuel(target_id)]
        mass_after = [float(value) for value in sim.debug_get_mass_state(target_id)]
        platform_after = [float(value) for value in sim.get_unit_damage_state(target_id)]
        flight_after = sim.get_flight_dynamics_debug_view(target_id)

        self.assertTrue(sim.is_unit_active(target_id))
        self.assertLess(fuel_after[0] + fuel_after[2], fuel_initial[0] + fuel_initial[2])
        self.assertLess(mass_after[1], mass_initial[1])
        self.assertGreater(overlay_after["fire"], overlay_initial["fire"])
        self.assertLess(overlay_after["hydraulic"], overlay_initial["hydraulic"])
        self.assertLess(overlay_after["flight_control"], overlay_initial["flight_control"])
        self.assertLess(overlay_after["structure"], overlay_initial["structure"])
        self.assertLess(platform_after[1], platform_initial[1])
        self.assertLess(platform_after[3], platform_initial[3])
        self.assertLess(float(flight_after.max_turn_rate), float(flight_initial.max_turn_rate))

    def test_phase2_damaged_airframe_high_speed_envelope_accumulates_structural_damage(self) -> None:
        cases = {
            "moderate": {
                "vx": 0.0,
                "vy": 260.0,
                "expect_degradation": False,
            },
            "high_dynamic_pressure": {
                "vx": 0.0,
                "vy": 430.0,
                "expect_degradation": True,
            },
        }

        for name, case in cases.items():
            with self.subTest(profile=name):
                sim = ef_py.SimulationKernel()
                sim.reset(20260526)
                self.assertTrue(sim.load_database(_DB_PATH))
                sim.set_time_step(0.25)
                target_id = int(
                    sim.spawn_unit(
                        ef_py.Side.Red,
                        "F-16C_Block50",
                        0.0,
                        0.0,
                        1200.0,
                        0.0,
                        0.0,
                        0.0,
                        float(case["vx"]),
                        float(case["vy"]),
                        0.0,
                    )
                )
                attacker_id = int(
                    sim.spawn_unit(
                        ef_py.Side.Blue,
                        "F-16C_Block50",
                        0.0,
                        -5000.0,
                        1200.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        250.0,
                        0.0,
                    )
                )

                self.assertTrue(
                    bool(
                        sim.debug_apply_local_proximity_hit(
                            attacker_id,
                            target_id,
                            -0.753,
                            4.0,
                            0.0,
                            240.0,
                            80.0,
                        )
                    )
                )
                sim.step()
                overlay_before = _aircraft_damage_overlay(sim, target_id)
                flight_before = sim.get_flight_dynamics_debug_view(target_id)

                for _ in range(80):
                    sim.step()

                overlay_after = _aircraft_damage_overlay(sim, target_id)
                flight_after = sim.get_flight_dynamics_debug_view(target_id)
                self.assertTrue(sim.is_unit_active(target_id))
                self.assertLess(overlay_before["structure"], 1.0)

                if case["expect_degradation"]:
                    self.assertLess(overlay_after["structure"], overlay_before["structure"])
                    self.assertGreater(overlay_after["flutter_exposure"], overlay_before["flutter_exposure"])
                    self.assertGreater(overlay_after["structural_overstress"], overlay_before["structural_overstress"])
                    self.assertLess(float(flight_after.max_g), float(flight_before.max_g))
                else:
                    self.assertLess(
                        overlay_after["structure"],
                        overlay_before["structure"],
                    )
                    self.assertAlmostEqual(
                        overlay_after["flutter_exposure"],
                        overlay_before["flutter_exposure"],
                        delta=1.0e-6,
                    )

    def test_phase3_warhead_family_changes_structured_air_effect_distribution(self) -> None:
        fuselage = (0.0, 0.0, 0.3)
        wing = (-0.753, 4.0, 0.0)
        nose = (6.024, 0.0, 0.0)

        blast_fragmentation_fuselage, baseline_event = _profiled_local_hit_damage_state(
            "blast_fragmentation",
            fuselage,
        )
        blast_fuselage, blast_event = _profiled_local_hit_damage_state("blast", fuselage)
        self.assertEqual(str(baseline_event.effect_family), "blast_fragmentation")
        self.assertEqual(str(blast_event.effect_family), "blast")
        self.assertFalse(bool(blast_event.warhead_profile_synthetic))
        self.assertFalse(bool(blast_event.damage_scalar_synthetic))
        self.assertGreater(float(blast_event.component_threshold_scale), 1.0)
        self.assertLess(blast_fuselage[3], blast_fragmentation_fuselage[3])

        blast_fragmentation_wing, _ = _profiled_local_hit_damage_state(
            "blast_fragmentation",
            wing,
        )
        continuous_rod_wing, continuous_event = _profiled_local_hit_damage_state(
            "continuous_rod",
            wing,
        )
        self.assertEqual(str(continuous_event.effect_family), "continuous_rod")
        self.assertGreater(float(continuous_event.component_threshold_scale), 1.0)
        self.assertLess(continuous_rod_wing[1], blast_fragmentation_wing[1])

        blast_fragmentation_nose, _ = _profiled_local_hit_damage_state(
            "blast_fragmentation",
            nose,
            damage=60.0,
        )
        hit_to_kill_nose, hit_to_kill_event = _profiled_local_hit_damage_state(
            "hit_to_kill",
            nose,
            damage=60.0,
        )
        self.assertEqual(str(hit_to_kill_event.effect_family), "hit_to_kill")
        self.assertGreater(float(hit_to_kill_event.component_threshold_scale), 1.0)
        self.assertLess(hit_to_kill_nose[0], blast_fragmentation_nose[0])
        self.assertLess(hit_to_kill_nose[2], blast_fragmentation_nose[2])

    def test_phase3_proximity_field_projects_near_miss_onto_nearest_air_hitbox(self) -> None:
        direct_wing_overlay, direct_damage, _ = _profiled_local_hit_overlay(
            "blast_fragmentation",
            (-0.753, 4.0, 0.0),
            damage=90.0,
            radius=25.0,
        )
        near_wing_overlay, near_damage, near_event = _profiled_local_hit_overlay(
            "blast_fragmentation",
            (-0.753, 7.1, 0.0),
            damage=90.0,
            radius=25.0,
        )
        far_overlay, far_damage, far_event = _profiled_local_hit_overlay(
            "blast_fragmentation",
            (-0.753, 20.0, 0.0),
            damage=90.0,
            radius=25.0,
        )

        self.assertEqual(str(near_event.effect_family), "blast_fragmentation")
        self.assertAlmostEqual(float(near_event.miss_distance_m), math.hypot(-0.753, 7.1), delta=1.0e-6)
        self.assertAlmostEqual(float(near_event.detonation_local_forward_m), -0.753, delta=1.0e-6)
        self.assertAlmostEqual(float(near_event.detonation_local_right_m), 7.1, delta=1.0e-6)
        self.assertAlmostEqual(float(near_event.detonation_local_up_m), 0.0, delta=1.0e-6)
        self.assertFalse(bool(near_event.direct_hitbox_intersection))
        self.assertGreater(int(near_event.projected_hitbox_count), 0)
        self.assertGreater(float(near_event.spatial_effect_scale), 0.0)
        self.assertLess(float(near_event.spatial_effect_scale), 1.0)
        self.assertGreater(float(near_event.mechanism_effect_scale), 0.0)
        self.assertLessEqual(float(near_event.mechanism_effect_scale), 1.10)
        self.assertGreater(int(near_event.warhead_spatial_sample_count), 100)
        self.assertGreater(float(near_event.warhead_spatial_hit_estimate), 0.0)
        self.assertGreater(float(near_event.warhead_spatial_energy_scale), 0.0)
        self.assertLess(near_wing_overlay["structure"], 1.0)
        self.assertLess(near_wing_overlay["flight_control"], 1.0)
        self.assertLess(near_wing_overlay["hydraulic"], 1.0)
        self.assertLess(near_wing_overlay["fuel"], 1.0)
        self.assertGreater(near_wing_overlay["fuel_leak"], 0.0)
        self.assertGreater(min(far_damage), 0.99)
        self.assertAlmostEqual(far_overlay["structure"], 1.0, delta=1.0e-6)
        self.assertAlmostEqual(far_overlay["flight_control"], 1.0, delta=1.0e-6)
        self.assertAlmostEqual(far_overlay["fuel"], 1.0, delta=1.0e-6)
        self.assertEqual(str(far_event.effect_family), "blast_fragmentation")

        self.assertGreater(near_wing_overlay["structure"], direct_wing_overlay["structure"])
        self.assertGreater(near_wing_overlay["flight_control"], direct_wing_overlay["flight_control"])
        self.assertGreater(near_damage[1], direct_damage[1])

    def test_phase3_spatial_projection_respects_warhead_family_footprint(self) -> None:
        near_wing = (-0.753, 7.1, 0.0)
        blast_fragmentation_overlay, _, blast_fragmentation_event = _profiled_local_hit_overlay(
            "blast_fragmentation",
            near_wing,
            damage=90.0,
            radius=35.0,
        )
        hit_to_kill_overlay, _, hit_to_kill_event = _profiled_local_hit_overlay(
            "hit_to_kill",
            near_wing,
            damage=90.0,
            radius=35.0,
        )

        self.assertEqual(str(blast_fragmentation_event.effect_family), "blast_fragmentation")
        self.assertEqual(str(hit_to_kill_event.effect_family), "hit_to_kill")
        self.assertFalse(bool(blast_fragmentation_event.direct_hitbox_intersection))
        self.assertEqual(int(blast_fragmentation_event.projected_hitbox_count), 3)
        self.assertFalse(bool(hit_to_kill_event.direct_hitbox_intersection))
        self.assertEqual(int(hit_to_kill_event.projected_hitbox_count), 1)

        self.assertLess(blast_fragmentation_overlay["flight_control"], 1.0)
        self.assertLess(blast_fragmentation_overlay["hydraulic"], 1.0)
        self.assertLess(blast_fragmentation_overlay["fuel"], 1.0)
        self.assertLess(blast_fragmentation_overlay["propulsion"], 1.0)
        self.assertLess(blast_fragmentation_overlay["avionics"], 1.0)
        self.assertAlmostEqual(blast_fragmentation_overlay["crew"], 1.0, delta=1.0e-6)

        self.assertLess(hit_to_kill_overlay["flight_control"], 1.0)
        self.assertLess(hit_to_kill_overlay["hydraulic"], 1.0)
        self.assertAlmostEqual(hit_to_kill_overlay["fuel"], 1.0, delta=1.0e-6)
        self.assertAlmostEqual(hit_to_kill_overlay["propulsion"], 1.0, delta=1.0e-6)
        self.assertAlmostEqual(hit_to_kill_overlay["avionics"], 1.0, delta=1.0e-6)
        self.assertAlmostEqual(hit_to_kill_overlay["crew"], 1.0, delta=1.0e-6)

    def test_phase3_warhead_mechanism_sampling_consumes_hitbox_armor(self) -> None:
        low_armor_name = "F-16C_A2_LowArmor_Test"
        high_armor_name = "F-16C_A2_HighArmor_Test"
        overrides = [
            _make_f16_armor_override(low_armor_name, wing_armor_mm=1.0),
            _make_f16_armor_override(high_armor_name, wing_armor_mm=80.0),
        ]

        low_armor_overlay, low_armor_damage, low_event = _profiled_local_hit_overlay_for_target(
            low_armor_name,
            "blast_fragmentation",
            (-0.753, 4.0, 0.0),
            damage=90.0,
            radius=35.0,
            overrides=overrides,
        )
        high_armor_overlay, high_armor_damage, high_event = _profiled_local_hit_overlay_for_target(
            high_armor_name,
            "blast_fragmentation",
            (-0.753, 4.0, 0.0),
            damage=90.0,
            radius=35.0,
            overrides=overrides,
        )

        self.assertEqual(str(low_event.effect_family), "blast_fragmentation")
        self.assertEqual(str(high_event.effect_family), "blast_fragmentation")
        self.assertAlmostEqual(float(low_event.miss_distance_m), float(high_event.miss_distance_m), delta=1.0e-6)
        self.assertTrue(bool(low_event.direct_hitbox_intersection))
        self.assertTrue(bool(high_event.direct_hitbox_intersection))
        self.assertGreater(
            float(low_event.mechanism_armor_scale),
            float(high_event.mechanism_armor_scale),
        )
        self.assertGreater(
            float(low_event.mechanism_effect_scale),
            float(high_event.mechanism_effect_scale),
        )
        self.assertLess(low_armor_overlay["flight_control"], high_armor_overlay["flight_control"])
        self.assertLess(low_armor_overlay["hydraulic"], high_armor_overlay["hydraulic"])
        self.assertLess(low_armor_overlay["structure"], high_armor_overlay["structure"])
        self.assertLess(low_armor_damage[1], high_armor_damage[1])

    def test_phase3_componentized_hitbox_localizes_damage_within_wing(self) -> None:
        target_name = "F-16C_A2_ComponentWing_Test"
        overrides = [_make_f16_componentized_wing_override(target_name)]

        fuel_overlay, _, fuel_event = _profiled_local_hit_overlay_for_target(
            target_name,
            "blast_fragmentation",
            (-0.8, -2.8, 0.0),
            damage=90.0,
            radius=35.0,
            overrides=overrides,
        )
        control_overlay, _, control_event = _profiled_local_hit_overlay_for_target(
            target_name,
            "blast_fragmentation",
            (-0.8, 2.8, 0.0),
            damage=90.0,
            radius=35.0,
            overrides=overrides,
        )

        self.assertTrue(bool(fuel_event.direct_hitbox_intersection))
        self.assertTrue(bool(control_event.direct_hitbox_intersection))
        self.assertGreater(float(fuel_event.component_threshold_scale), 1.0)
        self.assertGreater(float(control_event.component_threshold_scale), 1.0)

        self.assertLess(fuel_overlay["fuel"], control_overlay["fuel"])
        self.assertGreater(fuel_overlay["fuel_leak"], control_overlay["fuel_leak"])
        self.assertAlmostEqual(fuel_overlay["flight_control"], 1.0, delta=1.0e-6)
        self.assertAlmostEqual(fuel_overlay["hydraulic"], 1.0, delta=1.0e-6)

        self.assertLess(control_overlay["flight_control"], fuel_overlay["flight_control"])
        self.assertLess(control_overlay["hydraulic"], fuel_overlay["hydraulic"])
        self.assertAlmostEqual(control_overlay["fuel"], 1.0, delta=1.0e-6)
        self.assertAlmostEqual(control_overlay["fuel_leak"], 0.0, delta=1.0e-6)

    def test_phase3_database_f16_component_geometry_reports_primary_component(self) -> None:
        fuel_overlay, _, fuel_event = _profiled_local_hit_overlay_for_target(
            "F-16C_Block50",
            "blast_fragmentation",
            (-0.8, -2.8, 0.0),
            damage=90.0,
            radius=35.0,
        )
        control_overlay, _, control_event = _profiled_local_hit_overlay_for_target(
            "F-16C_Block50",
            "blast_fragmentation",
            (-0.8, 4.1, 0.0),
            damage=90.0,
            radius=35.0,
        )

        self.assertTrue(bool(fuel_event.direct_hitbox_intersection))
        self.assertGreaterEqual(int(fuel_event.component_hit_count), 1)
        self.assertEqual(str(fuel_event.component_primary_name), "left_wing_fuel_cell")
        self.assertEqual(str(fuel_event.component_primary_system), "fuel")
        self.assertAlmostEqual(float(fuel_event.component_primary_redundancy_group), 1.0, delta=1.0e-6)
        self.assertEqual(str(fuel_event.component_primary_redundancy_group_id), "wing_fuel_cells")
        self.assertTrue(bool(fuel_event.component_primary_critical))
        self.assertLess(float(fuel_event.component_primary_integrity), 1.0)
        self.assertGreater(float(fuel_event.component_redundancy_group_availability), 0.0)
        self.assertEqual(int(fuel_event.component_redundancy_group_member_count), 2)
        self.assertLess(fuel_overlay["fuel"], 1.0)
        self.assertGreater(fuel_overlay["fuel_leak"], 0.0)
        self.assertAlmostEqual(fuel_overlay["flight_control"], 1.0, delta=1.0e-6)

        self.assertTrue(bool(control_event.direct_hitbox_intersection))
        self.assertEqual(int(control_event.component_hit_count), 1)
        self.assertEqual(str(control_event.component_primary_name), "right_aileron_actuator")
        self.assertEqual(str(control_event.component_primary_system), "flight_control")
        self.assertAlmostEqual(float(control_event.component_primary_redundancy_group), 2.0, delta=1.0e-6)
        self.assertEqual(
            str(control_event.component_primary_redundancy_group_id),
            "lateral_flight_control_actuators",
        )
        self.assertFalse(bool(control_event.component_primary_critical))
        self.assertLess(float(control_event.component_primary_integrity), 1.0)
        self.assertEqual(int(control_event.component_redundancy_group_member_count), 2)
        self.assertLess(control_overlay["flight_control"], 1.0)
        self.assertLess(control_overlay["hydraulic"], 1.0)
        self.assertAlmostEqual(control_overlay["fuel"], 1.0, delta=1.0e-6)

    def test_phase3_database_su35_component_geometry_reports_primary_component(self) -> None:
        fuel_overlay, _, fuel_event = _profiled_local_hit_overlay_for_target(
            "Su-35S_Flanker-E",
            "blast_fragmentation",
            (-2.0, -4.4, 0.0),
            damage=90.0,
            radius=35.0,
        )
        control_overlay, _, control_event = _profiled_local_hit_overlay_for_target(
            "Su-35S_Flanker-E",
            "blast_fragmentation",
            (-2.0, 6.2, 0.0),
            damage=90.0,
            radius=35.0,
        )

        self.assertTrue(bool(fuel_event.direct_hitbox_intersection))
        self.assertGreaterEqual(int(fuel_event.component_hit_count), 1)
        self.assertEqual(str(fuel_event.component_primary_name), "left_wing_fuel_cell")
        self.assertEqual(str(fuel_event.component_primary_system), "fuel")
        self.assertAlmostEqual(float(fuel_event.component_primary_redundancy_group), 1.0, delta=1.0e-6)
        self.assertEqual(str(fuel_event.component_primary_redundancy_group_id), "wing_fuel_cells")
        self.assertTrue(bool(fuel_event.component_primary_critical))
        self.assertLess(fuel_overlay["fuel"], 1.0)
        self.assertGreater(fuel_overlay["fuel_leak"], 0.0)
        self.assertAlmostEqual(fuel_overlay["flight_control"], 1.0, delta=1.0e-6)

        self.assertTrue(bool(control_event.direct_hitbox_intersection))
        self.assertEqual(int(control_event.component_hit_count), 1)
        self.assertEqual(str(control_event.component_primary_name), "right_elevon_actuator")
        self.assertEqual(str(control_event.component_primary_system), "flight_control")
        self.assertAlmostEqual(float(control_event.component_primary_redundancy_group), 2.0, delta=1.0e-6)
        self.assertEqual(
            str(control_event.component_primary_redundancy_group_id),
            "lateral_flight_control_actuators",
        )
        self.assertFalse(bool(control_event.component_primary_critical))
        self.assertLess(control_overlay["flight_control"], 1.0)
        self.assertLess(control_overlay["hydraulic"], 1.0)
        self.assertAlmostEqual(control_overlay["fuel"], 1.0, delta=1.0e-6)

    def test_phase3_fighter_component_geometry_covers_nose_avionics_and_engine_runtime_identity(
        self,
    ) -> None:
        cases = [
            ("F-16C_Block50", (6.6, 0.0, 0.0), "apg68_radar_array", "radar", "avionics"),
            ("F-16C_Block50", (1.5, 0.0, 0.25), "mission_computer", "avionics", "avionics"),
            ("F-16C_Block50", (-5.8, 0.0, 0.0), "engine_core", "engine", "propulsion"),
            ("Su-35S_Flanker-E", (9.2, 0.0, 0.0), "irbis_radar_array", "radar", "avionics"),
            ("Su-35S_Flanker-E", (1.8, 0.0, 0.25), "mission_computer", "avionics", "avionics"),
            ("Su-35S_Flanker-E", (-7.5, -1.4, -0.4), "left_engine_core", "engine_left", "propulsion"),
            ("Su-35S_Flanker-E", (-7.5, 1.4, -0.4), "right_engine_core", "engine_right", "propulsion"),
        ]

        for target_type, local, expected_component, expected_system, affected_overlay in cases:
            with self.subTest(target=target_type, component=expected_component):
                overlay, _, event = _profiled_local_hit_overlay_for_target(
                    target_type,
                    "blast_fragmentation",
                    local,
                    damage=90.0,
                    radius=35.0,
                )

                self.assertTrue(bool(event.direct_hitbox_intersection))
                self.assertEqual(int(event.component_hit_count), 1)
                self.assertEqual(str(event.component_primary_name), expected_component)
                self.assertEqual(str(event.component_primary_system), expected_system)
                self.assertLess(float(event.component_primary_integrity), 1.0)
                self.assertGreater(float(event.component_threshold_scale), 1.0)
                self.assertLess(overlay[affected_overlay], 1.0)

    def test_phase3_representative_aircraft_database_components_cover_uav_helo_c2(self) -> None:
        cases = {
            "mq9_reaper.json": {
                "eo_ir_sensor_turret",
                "synthetic_aperture_radar",
                "satcom_antenna_array",
                "mission_payload_processor",
                "power_distribution_unit",
                "data_link_transceiver",
                "rear_engine_block",
                "engine_fuel_control_unit",
                "starter_generator",
                "pusher_propeller_hub",
                "left_wing_fuel_cell",
                "right_aileron_servo",
                "left_inboard_flap_servo",
                "right_outboard_wing_spar",
            },
            "mh60r_mvp.json": {
                "cockpit_crew_station",
                "surface_search_radar",
                "forward_flir_turret",
                "tactical_navigation_unit",
                "fuel_bladders",
                "dipping_sonar_processor",
                "esm_receiver_rack",
                "power_distribution_panel",
                "left_engine_module",
                "main_gearbox",
                "hydraulic_pump_module",
                "main_rotor_hub",
                "collective_servo",
                "tail_drive_shaft",
                "right_tail_rudder_servo",
            },
            "e3_sentry.json": {
                "flight_deck_crew_station",
                "iff_transponder_suite",
                "rotodome_radar_array",
                "mission_processing_racks",
                "radar_signal_processor",
                "mission_operator_consoles",
                "center_fuselage_fuel_cell",
                "navigation_reference_unit",
                "power_distribution_bus",
                "auxiliary_power_unit",
                "left_engine_pod",
                "right_engine_pod",
                "left_engine_fire_bottle",
                "right_engine_fire_bottle",
                "right_aileron_actuator",
                "right_spoiler_actuator",
            },
        }

        for filename, expected_names in cases.items():
            with self.subTest(filename=filename):
                with open(
                    resolve_repo_path("examples", "config", "database", "aircraft", "units", filename),
                    "r",
                    encoding="utf-8",
                ) as handle:
                    unit = json.load(handle)
                components = [
                    component
                    for hitbox in unit["damage_model"]["hitboxes"]
                    for component in hitbox.get("components", [])
                ]
                component_names = {str(component.get("name", "")) for component in components}

                self.assertGreaterEqual(len(components), 20)
                self.assertTrue(expected_names.issubset(component_names))
                for component in components:
                    self.assertTrue(str(component.get("name", "")))
                    self.assertTrue(str(component.get("system", "")))
                    self.assertTrue(str(component.get("redundancy_group_id", "")))
                    self.assertGreater(float(component.get("threshold_scale", 0.0)), 0.0)

    def test_phase3_fighter_components_author_mechanism_specific_thresholds(self) -> None:
        cases = [
            (
                "f16c_block50.json",
                {
                    "apg68_radar_array",
                    "cockpit_crew_station",
                    "nose_avionics_bay",
                    "iff_interrogator",
                    "center_fuselage_fuel_cell",
                    "mission_computer",
                    "data_link_terminal",
                    "flight_control_computer",
                    "inertial_navigation_unit",
                    "electrical_power_bus",
                    "engine_core",
                    "afterburner_nozzle",
                    "tail_hydraulic_pump",
                    "engine_fuel_control_unit",
                    "rudder_actuator",
                    "left_wing_fuel_cell",
                    "right_wing_fuel_cell",
                    "left_aileron_actuator",
                    "right_aileron_actuator",
                    "wing_spar_center",
                    "left_leading_edge_flap_actuator",
                    "right_leading_edge_flap_actuator",
                },
                {
                    "radar",
                    "cockpit",
                    "avionics",
                    "navigation",
                    "data_link",
                    "engine",
                    "hydraulic",
                    "flight_control",
                    "fuel",
                    "wings",
                },
            ),
            (
                "su35s_flanker_e.json",
                {
                    "irbis_radar_array",
                    "cockpit_crew_station",
                    "nose_avionics_bay",
                    "irst_sensor",
                    "center_fuselage_fuel_cell",
                    "mission_computer",
                    "data_link_terminal",
                    "flight_control_computer",
                    "inertial_navigation_unit",
                    "electrical_power_bus",
                    "left_engine_core",
                    "left_engine_fuel_feed",
                    "left_thrust_vector_actuator",
                    "right_engine_core",
                    "right_engine_fuel_feed",
                    "right_thrust_vector_actuator",
                    "left_wing_fuel_cell",
                    "right_wing_fuel_cell",
                    "left_elevon_actuator",
                    "right_elevon_actuator",
                    "wing_spar_center",
                    "left_leading_edge_flap_actuator",
                    "right_leading_edge_flap_actuator",
                },
                {
                    "radar",
                    "cockpit",
                    "avionics",
                    "sensor_payload",
                    "navigation",
                    "data_link",
                    "engine_left",
                    "engine_right",
                    "flight_control",
                    "fuel",
                    "wings",
                },
            ),
        ]
        required_families = {"blast", "fragmentation", "blast_fragmentation", "continuous_rod", "hit_to_kill"}

        for filename, expected_components, expected_systems in cases:
            with self.subTest(filename=filename):
                with open(
                    resolve_repo_path("examples", "config", "database", "aircraft", "units", filename),
                    "r",
                    encoding="utf-8",
                ) as handle:
                    unit = json.load(handle)
                components = {
                    str(component.get("name", "")): component
                    for hitbox in unit["damage_model"]["hitboxes"]
                    for component in hitbox.get("components", [])
                }
                self.assertGreaterEqual(len(components), 20)
                self.assertTrue(expected_components.issubset(set(components)))
                self.assertTrue(expected_systems.issubset({str(c.get("system", "")) for c in components.values()}))
                for component_name in expected_components:
                    thresholds = components[component_name].get("mechanism_thresholds", {})
                    self.assertTrue(required_families.issubset(set(thresholds)))
                    self.assertGreater(len({float(value) for value in thresholds.values()}), 1)

    def test_phase3_component_mechanism_thresholds_drive_failure_probability(self) -> None:
        low_target = "F-16C_A2_LowRodThreshold_Test"
        high_target = "F-16C_A2_HighRodThreshold_Test"
        low_override = _make_f16_component_mechanism_threshold_override(
            low_target,
            continuous_rod_scale=0.60,
        )
        high_override = _make_f16_component_mechanism_threshold_override(
            high_target,
            continuous_rod_scale=1.00,
        )

        _low_overlay, _, low_event = _profiled_local_hit_overlay_for_target(
            low_target,
            "continuous_rod",
            (-0.8, 4.1, 0.0),
            damage=90.0,
            radius=35.0,
            overrides=[low_override],
        )
        _high_overlay, _, high_event = _profiled_local_hit_overlay_for_target(
            high_target,
            "continuous_rod",
            (-0.8, 4.1, 0.0),
            damage=90.0,
            radius=35.0,
            overrides=[high_override],
        )

        self.assertEqual(str(low_event.component_primary_name), "right_aileron_actuator")
        self.assertEqual(str(high_event.component_primary_name), "right_aileron_actuator")
        self.assertAlmostEqual(
            float(low_event.component_failure_sample),
            float(high_event.component_failure_sample),
            delta=1.0e-9,
        )
        self.assertLess(
            float(low_event.component_threshold_scale),
            float(high_event.component_threshold_scale),
        )
        self.assertLess(
            float(low_event.component_failure_probability),
            float(high_event.component_failure_probability),
        )

    def test_phase3_representative_aircraft_components_author_mechanism_thresholds(
        self,
    ) -> None:
        filenames = [
            "f16c_block50.json",
            "su35s_flanker_e.json",
            "mq9_reaper.json",
            "mh60r_mvp.json",
            "e3_sentry.json",
        ]
        required_families = {"blast", "fragmentation", "blast_fragmentation", "continuous_rod", "hit_to_kill"}

        for filename in filenames:
            with self.subTest(filename=filename):
                with open(
                    resolve_repo_path("examples", "config", "database", "aircraft", "units", filename),
                    "r",
                    encoding="utf-8",
                ) as handle:
                    unit = json.load(handle)
                components = [
                    component
                    for hitbox in unit["damage_model"]["hitboxes"]
                    for component in hitbox.get("components", [])
                ]
                self.assertGreaterEqual(len(components), 20)
                for component in components:
                    thresholds = component.get("mechanism_thresholds", {})
                    self.assertTrue(required_families.issubset(set(thresholds)))
                    for family in required_families:
                        self.assertGreater(float(thresholds[family]), 0.0)
                    self.assertGreater(len({float(value) for value in thresholds.values()}), 1)

    def test_phase3_current_aircraft_unit_database_has_20_plus_component_models(
        self,
    ) -> None:
        units_dir = resolve_repo_path("examples", "config", "database", "aircraft", "units")
        required_families = {"blast", "fragmentation", "blast_fragmentation", "continuous_rod", "hit_to_kill"}
        filenames = sorted(
            filename
            for filename in os.listdir(units_dir)
            if filename.endswith(".json")
        )

        self.assertGreater(len(filenames), 0)
        for filename in filenames:
            with self.subTest(filename=filename):
                with open(os.path.join(units_dir, filename), "r", encoding="utf-8") as handle:
                    unit = json.load(handle)
                hitboxes = unit.get("damage_model", {}).get("hitboxes", [])
                components = [
                    component
                    for hitbox in hitboxes
                    for component in hitbox.get("components", [])
                ]
                self.assertGreater(len(hitboxes), 0)
                self.assertGreaterEqual(len(components), 20)
                self.assertEqual(
                    len({str(component.get("name", "")) for component in components}),
                    len(components),
                )
                for component in components:
                    self.assertTrue(str(component.get("name", "")))
                    self.assertTrue(str(component.get("system", "")))
                    self.assertTrue(str(component.get("redundancy_group_id", "")))
                    self.assertGreater(float(component.get("threshold_scale", 0.0)), 0.0)
                    thresholds = component.get("mechanism_thresholds", {})
                    self.assertTrue(required_families.issubset(set(thresholds)))
                    for family in required_families:
                        self.assertGreater(float(thresholds[family]), 0.0)
                    self.assertGreater(len({float(value) for value in thresholds.values()}), 1)

    def test_phase3_current_aircraft_unit_component_centers_stay_inside_parent_hitboxes(
        self,
    ) -> None:
        units_dir = resolve_repo_path("examples", "config", "database", "aircraft", "units")
        filenames = sorted(
            filename
            for filename in os.listdir(units_dir)
            if filename.endswith(".json")
        )

        for filename in filenames:
            with self.subTest(filename=filename):
                with open(os.path.join(units_dir, filename), "r", encoding="utf-8") as handle:
                    unit = json.load(handle)
                for hitbox in unit.get("damage_model", {}).get("hitboxes", []):
                    hitbox_offset = [float(value) for value in hitbox["offset"]]
                    hitbox_size = [float(value) for value in hitbox["size"]]
                    hitbox_min = [
                        hitbox_offset[index] - 0.5 * hitbox_size[index]
                        for index in range(3)
                    ]
                    hitbox_max = [
                        hitbox_offset[index] + 0.5 * hitbox_size[index]
                        for index in range(3)
                    ]
                    for component in hitbox.get("components", []):
                        component_offset = [float(value) for value in component["offset"]]
                        for axis in range(3):
                            self.assertGreaterEqual(
                                component_offset[axis],
                                hitbox_min[axis] - 1.0e-9,
                                str(component.get("name", "")),
                            )
                            self.assertLessEqual(
                                component_offset[axis],
                                hitbox_max[axis] + 1.0e-9,
                                str(component.get("name", "")),
                            )

    def test_phase3_component_dependencies_are_authored_for_representative_control_and_mission_components(
        self,
    ) -> None:
        cases = [
            ("f16c_block50.json", "right_aileron_actuator", {"hydraulic", "flight_control"}),
            ("su35s_flanker_e.json", "right_elevon_actuator", {"hydraulic", "flight_control"}),
            ("mq9_reaper.json", "right_aileron_servo", {"hydraulic", "flight_control"}),
            ("mh60r_mvp.json", "right_tail_rudder_servo", {"hydraulic", "flight_control"}),
            ("e3_sentry.json", "rotodome_radar_array", {"avionics", "mission_systems"}),
        ]

        for filename, component_name, expected_dependencies in cases:
            with self.subTest(filename=filename, component=component_name):
                with open(
                    resolve_repo_path("examples", "config", "database", "aircraft", "units", filename),
                    "r",
                    encoding="utf-8",
                ) as handle:
                    unit = json.load(handle)
                components = [
                    component
                    for hitbox in unit["damage_model"]["hitboxes"]
                    for component in hitbox.get("components", [])
                    if str(component.get("name", "")) == component_name
                ]
                self.assertEqual(len(components), 1)
                dependency_systems = {
                    str(dependency.get("system", ""))
                    for dependency in components[0].get("dependencies", [])
                }
                self.assertTrue(expected_dependencies.issubset(dependency_systems))

    def test_phase3_current_aircraft_units_author_mission_power_and_link_dependencies(
        self,
    ) -> None:
        units_dir = resolve_repo_path("examples", "config", "database", "aircraft", "units")
        cases = [
            ("f16c_block50.json", "electrical_power_bus", {"flight_control", "data_link", "mission_systems"}),
            ("f16c_block50.json", "data_link_terminal", {"avionics", "mission_systems"}),
            ("su35s_flanker_e.json", "electrical_power_bus", {"flight_control", "data_link", "mission_systems"}),
            ("su35s_flanker_e.json", "data_link_terminal", {"avionics", "mission_systems"}),
            ("mq9_reaper.json", "power_distribution_unit", {"flight_control", "data_link", "mission_systems"}),
            ("mq9_reaper.json", "data_link_transceiver", {"avionics", "mission_systems"}),
            ("mh60r_mvp.json", "power_distribution_panel", {"flight_control", "data_link", "mission_systems"}),
            ("mh60r_mvp.json", "data_link_terminal", {"avionics", "mission_systems"}),
            ("e3_sentry.json", "power_distribution_bus", {"flight_control", "data_link", "mission_systems"}),
            ("e3_sentry.json", "wideband_data_link_array", {"avionics", "mission_systems"}),
        ]

        for filename, component_name, expected_dependencies in cases:
            with self.subTest(filename=filename, component=component_name):
                with open(os.path.join(units_dir, filename), "r", encoding="utf-8") as handle:
                    unit = json.load(handle)
                matches = [
                    component
                    for hitbox in unit["damage_model"]["hitboxes"]
                    for component in hitbox.get("components", [])
                    if str(component.get("name", "")) == component_name
                ]
                self.assertEqual(len(matches), 1)
                dependency_systems = {
                    str(dependency.get("system", ""))
                    for dependency in matches[0].get("dependencies", [])
                }
                self.assertTrue(expected_dependencies.issubset(dependency_systems))

    def test_phase3_representative_aircraft_components_report_runtime_identity(self) -> None:
        cases = [
            (
                "MQ-9_Reaper",
                (4.8, 0.0, -0.25),
                "eo_ir_sensor_turret",
                "sensor_payload",
                "mission_sensor_payload",
                1,
                "avionics",
                None,
            ),
            (
                "MQ-9_Reaper",
                (-0.4, 8.0, 0.0),
                "right_aileron_servo",
                "flight_control",
                "lateral_flight_control_actuators",
                2,
                "flight_control",
                "roll_control",
            ),
            (
                "MH-60R_MVP",
                (4.6, 0.0, -0.5),
                "surface_search_radar",
                "sensor_payload",
                "helo_sensor_payload",
                1,
                "avionics",
                None,
            ),
            (
                "MH-60R_MVP",
                (-8.5, 0.35, 0.2),
                "right_tail_rudder_servo",
                "flight_control",
                "yaw_control_servos",
                2,
                "flight_control",
                "yaw_control",
            ),
            (
                "E-3_Sentry_AWACS",
                (5.0, 0.0, 4.4),
                "rotodome_radar_array",
                "radar",
                "awacs_primary_radar",
                1,
                "avionics",
                None,
            ),
            (
                "E-3_Sentry_AWACS",
                (-2.0, 19.0, 0.0),
                "right_aileron_actuator",
                "flight_control",
                "lateral_flight_control_actuators",
                2,
                "flight_control",
                "roll_control",
            ),
        ]

        for (
            target_type,
            local_impact,
            expected_component,
            expected_system,
            expected_group,
            expected_group_members,
            expected_overlay_drop,
            expected_axis_drop,
        ) in cases:
            with self.subTest(target_type=target_type, component=expected_component):
                overlay, _, event = _profiled_local_hit_overlay_for_target(
                    target_type,
                    "blast_fragmentation",
                    local_impact,
                    damage=90.0,
                    radius=35.0,
                )

                self.assertTrue(bool(event.direct_hitbox_intersection))
                self.assertGreaterEqual(int(event.component_hit_count), 1)
                self.assertEqual(str(event.component_primary_name), expected_component)
                self.assertEqual(str(event.component_primary_system), expected_system)
                self.assertEqual(str(event.component_primary_redundancy_group_id), expected_group)
                self.assertEqual(
                    int(event.component_redundancy_group_member_count),
                    expected_group_members,
                )
                self.assertLess(float(event.component_primary_integrity), 1.0)
                self.assertGreater(float(event.component_redundancy_group_availability), 0.0)
                self.assertLess(overlay[expected_overlay_drop], 1.0)
                if expected_axis_drop is not None:
                    self.assertLess(overlay[expected_axis_drop], 1.0)

    def test_phase3_component_dependency_damage_propagates_to_related_aircraft_systems(self) -> None:
        sim = ef_py.SimulationKernel()
        sim.reset(20260526)
        self.assertTrue(sim.load_database(_DB_PATH))
        attacker_id, target_id = _spawn_attacker_and_named_target(sim, "F-16C_Block50")
        profile = _make_warhead_profile("continuous_rod", damage=160.0, radius=35.0)

        before = _aircraft_damage_overlay(sim, target_id)
        self.assertAlmostEqual(before["hydraulic"], 1.0, delta=1.0e-6)
        self.assertAlmostEqual(before["flight_control"], 1.0, delta=1.0e-6)

        self.assertTrue(
            bool(
                sim.debug_apply_profiled_local_proximity_hit(
                    attacker_id,
                    target_id,
                    -0.8,
                    4.1,
                    0.0,
                    profile,
                )
            )
        )

        event = sim.export_recent_engagement_events().effects_events[-1]
        after = _aircraft_damage_overlay(sim, target_id)

        self.assertEqual(str(event.component_primary_name), "right_aileron_actuator")
        self.assertEqual(
            str(event.component_primary_redundancy_group_id),
            "lateral_flight_control_actuators",
        )
        self.assertLess(float(event.component_redundancy_group_availability), 1.0)
        self.assertLess(after["hydraulic"], before["hydraulic"])
        self.assertLess(after["flight_control"], before["flight_control"])
        self.assertLess(after["roll_control"], before["roll_control"])

    def test_phase3_mission_component_dependency_damage_propagates_to_avionics_overlay(self) -> None:
        overlay, _, event = _profiled_local_hit_overlay_for_target(
            "E-3_Sentry_AWACS",
            "blast_fragmentation",
            (5.0, 0.0, 4.4),
            damage=90.0,
            radius=35.0,
        )

        self.assertEqual(str(event.component_primary_name), "rotodome_radar_array")
        self.assertEqual(str(event.component_primary_system), "radar")
        self.assertEqual(str(event.component_primary_redundancy_group_id), "awacs_primary_radar")
        self.assertLess(float(event.component_primary_integrity), 1.0)
        self.assertLess(overlay["avionics"], 1.0)

    def test_phase3_power_and_data_link_dependencies_propagate_to_aircraft_overlay(self) -> None:
        cases = [
            (
                "F-16C_Block50",
                (-2.8, 0.45, 0.05),
                "electrical_power_bus",
                {"avionics": 1.0, "flight_control": 1.0},
            ),
            (
                "MQ-9_Reaper",
                (-1.8, 0.0, 0.2),
                "power_distribution_unit",
                {"avionics": 1.0, "flight_control": 1.0},
            ),
            (
                "MH-60R_MVP",
                (-2.0, 0.0, 0.35),
                "power_distribution_panel",
                {"avionics": 1.0, "flight_control": 1.0},
            ),
            (
                "E-3_Sentry_AWACS",
                (-8.0, 0.0, 0.0),
                "power_distribution_bus",
                {"avionics": 1.0, "flight_control": 1.0},
            ),
            (
                "MQ-9_Reaper",
                (1.0, 0.0, 0.2),
                "data_link_transceiver",
                {"avionics": 1.0},
            ),
            (
                "E-3_Sentry_AWACS",
                (7.0, 0.0, 3.2),
                "wideband_data_link_array",
                {"avionics": 1.0},
            ),
        ]

        for target_type, local_impact, expected_component, expected_drops in cases:
            with self.subTest(target_type=target_type, component=expected_component):
                overlay, _, event = _profiled_local_hit_overlay_for_target(
                    target_type,
                    "blast_fragmentation",
                    local_impact,
                    damage=120.0,
                    radius=35.0,
                )

                self.assertEqual(str(event.component_primary_name), expected_component)
                self.assertLess(float(event.component_primary_integrity), 1.0)
                for overlay_name, baseline in expected_drops.items():
                    self.assertLess(overlay[overlay_name], baseline)

    def test_phase3_component_redundancy_reduces_failure_probability(self) -> None:
        single_name = "F-16C_A2_SingleCriticalActuator_Test"
        redundant_name = "F-16C_A2_RedundantActuator_Test"
        overrides = [
            _make_f16_component_redundancy_override(
                single_name,
                redundancy_group=0.0,
                critical=True,
            ),
            _make_f16_component_redundancy_override(
                redundant_name,
                redundancy_group=2.0,
                critical=False,
            ),
        ]

        _, _, single_event = _profiled_local_hit_overlay_for_target(
            single_name,
            "continuous_rod",
            (-0.8, 4.1, 0.0),
            damage=140.0,
            radius=35.0,
            overrides=overrides,
        )
        _, _, redundant_event = _profiled_local_hit_overlay_for_target(
            redundant_name,
            "continuous_rod",
            (-0.8, 4.1, 0.0),
            damage=140.0,
            radius=35.0,
            overrides=overrides,
        )

        self.assertEqual(str(single_event.component_primary_name), "right_aileron_actuator")
        self.assertEqual(str(redundant_event.component_primary_name), "right_aileron_actuator")
        self.assertTrue(bool(single_event.component_primary_critical))
        self.assertFalse(bool(redundant_event.component_primary_critical))
        self.assertAlmostEqual(float(single_event.component_primary_redundancy_group), 0.0, delta=1.0e-6)
        self.assertAlmostEqual(float(redundant_event.component_primary_redundancy_group), 2.0, delta=1.0e-6)
        self.assertGreater(
            float(single_event.component_failure_probability),
            float(redundant_event.component_failure_probability),
        )

    def test_phase3_component_redundancy_group_tracks_cumulative_integrity(self) -> None:
        sim = ef_py.SimulationKernel()
        sim.reset(20260526)
        self.assertTrue(sim.load_database(_DB_PATH))
        attacker_id, target_id = _spawn_attacker_and_named_target(sim, "F-16C_Block50")
        profile = _make_warhead_profile("continuous_rod", damage=160.0, radius=35.0)

        self.assertTrue(
            bool(
                sim.debug_apply_profiled_local_proximity_hit(
                    attacker_id,
                    target_id,
                    -0.8,
                    4.1,
                    0.0,
                    profile,
                )
            )
        )
        first_event = sim.export_recent_engagement_events().effects_events[-1]
        first_integrity = float(first_event.component_primary_integrity)
        first_group_availability = float(first_event.component_redundancy_group_availability)

        self.assertEqual(str(first_event.component_primary_name), "right_aileron_actuator")
        self.assertEqual(
            str(first_event.component_primary_redundancy_group_id),
            "lateral_flight_control_actuators",
        )
        self.assertEqual(int(first_event.component_redundancy_group_member_count), 2)
        self.assertEqual(int(first_event.component_redundancy_group_failed_count), 0)
        self.assertLess(first_integrity, 1.0)
        self.assertGreater(first_group_availability, first_integrity)

        self.assertTrue(
            bool(
                sim.debug_apply_profiled_local_proximity_hit(
                    attacker_id,
                    target_id,
                    -0.8,
                    4.1,
                    0.0,
                    profile,
                )
            )
        )
        second_event = sim.export_recent_engagement_events().effects_events[-1]
        second_integrity = float(second_event.component_primary_integrity)
        second_group_availability = float(second_event.component_redundancy_group_availability)

        self.assertLess(second_integrity, first_integrity)
        self.assertLess(second_group_availability, first_group_availability)
        self.assertGreater(second_group_availability, second_integrity)

    def test_phase3_component_failure_probability_is_sampled_and_reported(self) -> None:
        wing = (-0.753, 4.0, 0.0)

        low_energy_overlay, _, low_event = _profiled_local_hit_overlay(
            "continuous_rod",
            wing,
            damage=35.0,
            radius=35.0,
        )
        high_energy_overlay, _, high_event = _profiled_local_hit_overlay(
            "continuous_rod",
            wing,
            damage=180.0,
            radius=35.0,
        )

        self.assertTrue(bool(high_event.direct_hitbox_intersection))
        self.assertGreater(float(high_event.component_failure_probability), 0.0)
        self.assertLessEqual(float(high_event.component_failure_probability), 1.0)
        self.assertGreaterEqual(float(high_event.component_failure_sample), 0.0)
        self.assertLessEqual(float(high_event.component_failure_sample), 1.0)
        self.assertGreater(
            float(high_event.component_failure_probability),
            float(low_event.component_failure_probability),
        )
        self.assertGreater(int(high_event.component_failure_count), 0)
        self.assertLess(
            high_energy_overlay["flight_control"],
            low_energy_overlay["flight_control"],
        )
        self.assertLess(
            high_energy_overlay["hydraulic"],
            low_energy_overlay["hydraulic"],
        )

    def test_phase3_component_failure_probability_consumes_mechanism_load_evidence(self) -> None:
        wing = (-0.753, 4.0, 0.0)

        _low_overlay, low_event = _profiled_local_hit_overlay_and_event_with_velocity(
            "continuous_rod",
            wing,
            (0.0, -220.0, 0.0),
            damage=90.0,
            radius=35.0,
        )
        _high_overlay, high_event = _profiled_local_hit_overlay_and_event_with_velocity(
            "continuous_rod",
            wing,
            (900.0, -250.0, 0.0),
            damage=90.0,
            radius=35.0,
        )

        self.assertEqual(str(low_event.component_failure_probability_source), "synthetic_sigmoid")
        self.assertEqual(str(high_event.component_failure_probability_source), "synthetic_sigmoid")
        self.assertFalse(bool(low_event.component_failure_probability_calibrated))
        self.assertFalse(bool(high_event.component_failure_probability_calibrated))
        self.assertAlmostEqual(
            float(low_event.component_failure_sample),
            float(high_event.component_failure_sample),
            delta=1.0e-9,
        )
        self.assertGreater(float(high_event.closure_mps), float(low_event.closure_mps))
        self.assertGreater(
            float(high_event.mechanism_rod_cut_margin),
            float(low_event.mechanism_rod_cut_margin),
        )
        self.assertGreater(
            float(high_event.mechanism_penetration_margin),
            float(low_event.mechanism_penetration_margin),
        )
        self.assertGreater(
            float(high_event.component_failure_probability),
            float(low_event.component_failure_probability),
        )

    def test_phase5_aircraft_vulnerability_profile_modulates_structured_damage(self) -> None:
        beam_high_closure = _profiled_local_hit_overlay_with_velocity(
            "continuous_rod",
            (-0.753, 4.0, 0.0),
            (900.0, -250.0, 0.0),
            damage=90.0,
            radius=35.0,
        )
        tail_low_closure = _profiled_local_hit_overlay_with_velocity(
            "continuous_rod",
            (-6.0, 0.0, 0.0),
            (0.0, -210.0, 0.0),
            damage=90.0,
            radius=35.0,
        )
        direct_wing = _profiled_local_hit_overlay_with_velocity(
            "continuous_rod",
            (-0.753, 4.0, 0.0),
            (900.0, -250.0, 0.0),
            damage=90.0,
            radius=35.0,
        )
        near_wing = _profiled_local_hit_overlay_with_velocity(
            "continuous_rod",
            (-0.753, 7.1, 0.0),
            (900.0, -250.0, 0.0),
            damage=90.0,
            radius=35.0,
        )

        self.assertLess(beam_high_closure["flight_control"], tail_low_closure["flight_control"])
        self.assertLess(beam_high_closure["hydraulic"], tail_low_closure["hydraulic"])
        self.assertLess(direct_wing["flight_control"], near_wing["flight_control"])
        self.assertLess(direct_wing["structure"], near_wing["structure"])

    def test_phase5_vulnerability_adjustment_is_recorded_on_effects_event(self) -> None:
        _overlay, event = _profiled_local_hit_overlay_and_event_with_velocity(
            "continuous_rod",
            (-0.753, 4.0, 0.0),
            (900.0, -250.0, 0.0),
            damage=90.0,
            radius=35.0,
        )

        self.assertTrue(bool(event.vulnerability_profile_present))
        self.assertTrue(bool(event.vulnerability_profile_synthetic))
        self.assertFalse(bool(event.vulnerability_calibrated_evidence))
        self.assertFalse(bool(event.vulnerability_pk_authority))
        self.assertFalse(bool(event.vulnerability_deterministic_fuze_authority))
        self.assertFalse(bool(event.vulnerability_evidence_dataset_valid))
        self.assertEqual(str(event.vulnerability_evidence_dataset_ref), "")
        self.assertEqual(str(event.vulnerability_calibration_status), "unvalidated")
        self.assertIn("synthetic fighter vulnerability scaffold", str(event.vulnerability_provenance))
        self.assertEqual(str(event.vulnerability_aspect_bucket), "beam")
        self.assertAlmostEqual(float(event.vulnerability_family_scale), 1.18, delta=1.0e-6)
        self.assertAlmostEqual(float(event.vulnerability_aspect_scale), 1.18, delta=1.0e-6)
        expected_closure_mps = 900.0 * 4.0 / math.hypot(4.0, 0.753)
        self.assertAlmostEqual(
            float(event.vulnerability_closure_mps),
            expected_closure_mps,
            delta=1.0e-6,
        )
        self.assertAlmostEqual(float(event.vulnerability_closure_scale), 1.10, delta=1.0e-6)
        self.assertAlmostEqual(float(event.vulnerability_miss_distance_scale), 1.0, delta=1.0e-6)
        self.assertAlmostEqual(float(event.vulnerability_effect_scale), 1.25, delta=1.0e-6)

    def test_phase5_synthetic_vulnerability_profile_is_not_pk_or_fuze_authority(self) -> None:
        sim = ef_py.SimulationKernel()
        sim.reset(20260526)
        self.assertTrue(sim.load_database(_DB_PATH))
        _attacker_id, target_id = _spawn_structured_f16_pair(sim)

        evidence = [
            float(value)
            for value in sim.debug_get_aircraft_vulnerability_evidence_state(target_id)
        ]
        self.assertEqual(evidence, [1.0, 1.0, 0.0, 0.0, 0.0, 0.0])

    def test_phase5_representative_aircraft_vulnerability_scaffolds_are_non_authoritative(
        self,
    ) -> None:
        cases = (
            "F-16C_Block50",
            "Su-35S_Flanker-E",
            "MQ-9_Reaper",
            "MH-60R_MVP",
            "E-3_Sentry_AWACS",
        )

        for target_type in cases:
            with self.subTest(target_type=target_type):
                sim = ef_py.SimulationKernel()
                sim.reset(20260526)
                self.assertTrue(sim.load_database(_DB_PATH))
                target_id = int(
                    sim.spawn_unit(
                        ef_py.Side.Red,
                        target_type,
                        0.0,
                        1000.0,
                        5000.0,
                        180.0,
                        0.0,
                        0.0,
                        0.0,
                        -200.0,
                        0.0,
                    )
                )

                evidence = [
                    float(value)
                    for value in sim.debug_get_aircraft_vulnerability_evidence_state(target_id)
                ]
                self.assertEqual(evidence, [1.0, 1.0, 0.0, 0.0, 0.0, 0.0])

    def test_phase5_calibrated_vulnerability_claim_requires_dataset_descriptor(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cmo_a2_vuln_missing_descriptor_") as tmpdir:
            db_dir = _copy_database_with_f16_vulnerability(
                tmpdir,
                {
                    "synthetic": False,
                    "calibrated": True,
                    "pk_authority": True,
                    "deterministic_fuze_authority": True,
                    "evidence_dataset_ref": "missing_external_dataset",
                    "calibration_status": "calibrated",
                    "provenance": "unit-test forged calibrated claim without descriptor",
                },
            )

            sim = ef_py.SimulationKernel()
            sim.reset(20260526)
            self.assertTrue(sim.load_database(db_dir))
            _attacker_id, target_id = _spawn_structured_f16_pair(sim)

            evidence = [
                float(value)
                for value in sim.debug_get_aircraft_vulnerability_evidence_state(target_id)
            ]
            self.assertEqual(evidence, [1.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    def test_phase5_synthetic_descriptor_cannot_grant_vulnerability_authority(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cmo_a2_vuln_synthetic_descriptor_") as tmpdir:
            db_dir = _copy_database_with_f16_vulnerability(
                tmpdir,
                {
                    "synthetic": False,
                    "calibrated": True,
                    "pk_authority": True,
                    "deterministic_fuze_authority": True,
                    "evidence_dataset_ref": "a2_synthetic_f16_aim120_placeholder",
                    "calibration_status": "calibrated",
                    "provenance": "unit-test calibrated claim pointed at synthetic descriptor",
                },
                descriptor_patch={
                    "calibration_status": "calibrated",
                    "pk_authority": True,
                    "deterministic_fuze_authority": True,
                },
            )

            sim = ef_py.SimulationKernel()
            sim.reset(20260526)
            self.assertTrue(sim.load_database(db_dir))
            _attacker_id, target_id = _spawn_structured_f16_pair(sim)

            evidence = [
                float(value)
                for value in sim.debug_get_aircraft_vulnerability_evidence_state(target_id)
            ]
            self.assertEqual(evidence, [1.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    def test_phase5_calibrated_descriptor_grants_only_requested_authority(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cmo_a2_vuln_pk_descriptor_") as tmpdir:
            db_dir = _copy_database_with_f16_vulnerability(
                tmpdir,
                {
                    "synthetic": False,
                    "calibrated": True,
                    "pk_authority": True,
                    "deterministic_fuze_authority": True,
                    "evidence_dataset_ref": "unit_test_calibrated_f16_frag_pk",
                    "calibration_status": "calibrated",
                    "provenance": "unit-test calibrated descriptor gate; synthetic fixture, not project data",
                },
                descriptor={
                    "dataset_id": "unit_test_calibrated_f16_frag_pk",
                    "target_type": "F-16C_Block50",
                    "weapon_family": "blast_fragmentation",
                    "aspect_bucket": "beam",
                    "closure_bucket": "high",
                    "miss_distance_bucket": "near_miss_0_35m",
                    "source_kind": "external_calibration_dataset",
                    "calibration_status": "calibrated",
                    "pk_authority": True,
                    "deterministic_fuze_authority": False,
                    "provenance": "unit-test descriptor proving authority gating mechanics only",
                },
            )

            sim = ef_py.SimulationKernel()
            sim.reset(20260526)
            self.assertTrue(sim.load_database(db_dir))
            _attacker_id, target_id = _spawn_structured_f16_pair(sim)

            evidence = [
                float(value)
                for value in sim.debug_get_aircraft_vulnerability_evidence_state(target_id)
            ]
            self.assertEqual(evidence, [1.0, 0.0, 1.0, 1.0, 0.0, 1.0])

    def test_phase5_calibrated_descriptor_requires_evidence_axes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cmo_a2_vuln_axis_descriptor_") as tmpdir:
            db_dir = _copy_database_with_f16_vulnerability(
                tmpdir,
                {
                    "synthetic": False,
                    "calibrated": True,
                    "pk_authority": True,
                    "deterministic_fuze_authority": True,
                    "evidence_dataset_ref": "unit_test_calibrated_f16_axis_missing",
                    "calibration_status": "calibrated",
                    "provenance": "unit-test calibrated descriptor missing evidence axes",
                },
                descriptor={
                    "dataset_id": "unit_test_calibrated_f16_axis_missing",
                    "target_type": "F-16C_Block50",
                    "weapon_family": "blast_fragmentation",
                    "source_kind": "external_calibration_dataset",
                    "calibration_status": "calibrated",
                    "pk_authority": True,
                    "deterministic_fuze_authority": True,
                    "provenance": "unit-test descriptor missing aspect/closure/miss-distance axes",
                },
            )

            sim = ef_py.SimulationKernel()
            sim.reset(20260526)
            self.assertTrue(sim.load_database(db_dir))
            _attacker_id, target_id = _spawn_structured_f16_pair(sim)

            evidence = [
                float(value)
                for value in sim.debug_get_aircraft_vulnerability_evidence_state(target_id)
            ]
            self.assertEqual(evidence, [1.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    def test_phase5_calibrated_descriptor_requires_schema_and_source_ref(self) -> None:
        cases = (
            ("missing_schema_version", {"schema_version": ""}),
            ("unknown_schema_version", {"schema_version": "a2.vulnerability_evidence.v0"}),
            ("missing_source_ref", {"source_ref": ""}),
        )
        for label, descriptor_patch in cases:
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory(prefix="cmo_a2_vuln_source_ref_") as tmpdir:
                    dataset_id = f"unit_test_calibrated_f16_{label}"
                    db_dir = _copy_database_with_f16_vulnerability(
                        tmpdir,
                        {
                            "synthetic": False,
                            "calibrated": True,
                            "pk_authority": True,
                            "deterministic_fuze_authority": True,
                            "evidence_dataset_ref": dataset_id,
                            "calibration_status": "calibrated",
                            "provenance": "unit-test descriptor schema/source-ref gate",
                        },
                        descriptor={
                            "dataset_id": dataset_id,
                            "target_type": "F-16C_Block50",
                            "weapon_family": "blast_fragmentation",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "near_miss_0_35m",
                            "source_kind": "external_calibration_dataset",
                            "calibration_status": "calibrated",
                            "pk_authority": True,
                            "deterministic_fuze_authority": True,
                            "provenance": "unit-test descriptor must declare schema and source ref",
                            **descriptor_patch,
                        },
                    )

                    sim = ef_py.SimulationKernel()
                    sim.reset(20260526)
                    self.assertTrue(sim.load_database(db_dir))
                    _attacker_id, target_id = _spawn_structured_f16_pair(sim)

                    evidence = [
                        float(value)
                        for value in sim.debug_get_aircraft_vulnerability_evidence_state(target_id)
                    ]
                    self.assertEqual(evidence, [1.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    def test_phase5_descriptor_requires_authoritative_source_kind(self) -> None:
        for source_kind, validation_artifact_ref, extra_descriptor in (
            (
                "engineering_surrogate",
                "fixture://unvalidated-engineering-surrogate",
                _validated_surrogate_manifest_patch(),
            ),
            ("validated_physics_surrogate", "", {}),
        ):
            with self.subTest(source_kind=source_kind):
                with tempfile.TemporaryDirectory(prefix="cmo_a2_vuln_source_kind_") as tmpdir:
                    db_dir = _copy_database_with_f16_vulnerability(
                        tmpdir,
                        {
                            "synthetic": False,
                            "calibrated": True,
                            "pk_authority": True,
                            "deterministic_fuze_authority": True,
                            "evidence_dataset_ref": f"unit_test_{source_kind}",
                            "calibration_status": "calibrated",
                            "provenance": "unit-test descriptor source-kind gate",
                        },
                        descriptor={
                            "dataset_id": f"unit_test_{source_kind}",
                            "target_type": "F-16C_Block50",
                            "weapon_family": "blast_fragmentation",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "near_miss_0_35m",
                            "source_kind": source_kind,
                            "validation_artifact_ref": validation_artifact_ref,
                            "calibration_status": "calibrated",
                            "pk_authority": True,
                            "deterministic_fuze_authority": True,
                            "provenance": "unit-test descriptor must not grant authority without accepted source kind",
                            **extra_descriptor,
                        },
                    )

                    sim = ef_py.SimulationKernel()
                    sim.reset(20260526)
                    self.assertTrue(sim.load_database(db_dir))
                    _attacker_id, target_id = _spawn_structured_f16_pair(sim)

                    evidence = [
                        float(value)
                        for value in sim.debug_get_aircraft_vulnerability_evidence_state(target_id)
                    ]
                    self.assertEqual(evidence, [1.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    def test_phase5_validated_physics_surrogate_requires_auditable_manifest(
        self,
    ) -> None:
        cases = (
            ("artifact_only", {}),
            (
                "missing_digest",
                {
                    "validation_manifest": {
                        **_validated_surrogate_manifest_patch()["validation_manifest"],
                        "validation_artifact_sha256": "",
                    }
                },
            ),
            (
                "failed_status",
                _validated_surrogate_manifest_patch(validation_status="failed"),
            ),
            (
                "scope_mismatch",
                _validated_surrogate_manifest_patch(aspect_bucket="tail"),
            ),
        )
        for label, manifest_patch in cases:
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory(prefix="cmo_a2_vuln_validated_surrogate_denied_") as tmpdir:
                    dataset_id = f"unit_test_validated_physics_surrogate_{label}"
                    db_dir = _copy_database_with_f16_vulnerability(
                        tmpdir,
                        {
                            "synthetic": False,
                            "calibrated": True,
                            "pk_authority": True,
                            "deterministic_fuze_authority": False,
                            "evidence_dataset_ref": dataset_id,
                            "calibration_status": "calibrated",
                            "provenance": "unit-test validated physics surrogate manifest gate",
                        },
                        descriptor={
                            "dataset_id": dataset_id,
                            "target_type": "F-16C_Block50",
                            "weapon_family": "blast_fragmentation",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "near_miss_0_35m",
                            "source_kind": "validated_physics_surrogate",
                            "validation_artifact_ref": "fixture://validated-physics-surrogate-report",
                            "calibration_status": "calibrated",
                            "pk_authority": True,
                            "deterministic_fuze_authority": False,
                            "provenance": "unit-test descriptor must carry audited surrogate manifest",
                            **manifest_patch,
                        },
                    )

                    sim = ef_py.SimulationKernel()
                    sim.reset(20260526)
                    self.assertTrue(sim.load_database(db_dir))
                    _attacker_id, target_id = _spawn_structured_f16_pair(sim)

                    evidence = [
                        float(value)
                        for value in sim.debug_get_aircraft_vulnerability_evidence_state(target_id)
                    ]
                    self.assertEqual(evidence, [1.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    def test_phase5_validated_physics_surrogate_exports_manifest_metadata(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="cmo_a2_vuln_validated_surrogate_accepted_") as tmpdir:
            db_dir = _copy_database_with_f16_vulnerability(
                tmpdir,
                {
                    "synthetic": False,
                    "calibrated": True,
                    "pk_authority": True,
                    "deterministic_fuze_authority": False,
                    "evidence_dataset_ref": "unit_test_validated_physics_surrogate_manifest",
                    "calibration_status": "calibrated",
                    "provenance": "unit-test validated physics surrogate manifest gate",
                },
                descriptor={
                    "dataset_id": "unit_test_validated_physics_surrogate_manifest",
                    "target_type": "F-16C_Block50",
                    "weapon_family": "continuous_rod",
                    "aspect_bucket": "beam",
                    "closure_bucket": "high",
                    "miss_distance_bucket": "direct_hit",
                    "source_kind": "validated_physics_surrogate",
                    "validation_artifact_ref": "fixture://validated-physics-surrogate-report",
                    "calibration_status": "calibrated",
                    "effect_scale_authority": True,
                    "pk_authority": True,
                    "deterministic_fuze_authority": False,
                    "provenance": "unit-test descriptor proving audited surrogate manifest mechanics only",
                    **_validated_surrogate_manifest_patch(
                        weapon_family="continuous_rod",
                        miss_distance_bucket="direct_hit",
                    ),
                    "rows": [
                        {
                            "row_id": "surrogate-manifest-effect-row",
                            "source_ref": "fixture://surrogate/effect-row",
                            "provenance": "unit-test validated surrogate row fixture",
                            "weapon_family": "continuous_rod",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "direct_hit",
                            "effect_scale": 1.19,
                        }
                    ],
                },
            )

            _overlay, event = _profiled_local_hit_overlay_and_event_with_velocity(
                "continuous_rod",
                (-0.753, 4.0, 0.0),
                (900.0, -250.0, 0.0),
                damage=90.0,
                radius=35.0,
                database_path=db_dir,
            )

            self.assertTrue(bool(event.vulnerability_evidence_dataset_valid))
            self.assertTrue(bool(event.vulnerability_pk_authority))
            self.assertFalse(bool(event.vulnerability_deterministic_fuze_authority))
            self.assertEqual(
                str(event.vulnerability_evidence_validation_manifest_schema_version),
                "a2.vulnerability_surrogate_validation.v1",
            )
            self.assertEqual(str(event.vulnerability_evidence_validation_status), "validated")
            self.assertEqual(
                str(event.vulnerability_evidence_validation_artifact_sha256),
                "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            )
            self.assertEqual(
                str(event.vulnerability_evidence_validated_surrogate_model_ref),
                "fixture://surrogate/model/f16-aim120-v1",
            )
            self.assertEqual(
                str(event.vulnerability_evidence_validation_benchmark_ref),
                "fixture://surrogate/benchmark/f16-aim120-v1",
            )
            self.assertEqual(
                str(event.vulnerability_evidence_validation_metrics_ref),
                "fixture://surrogate/metrics/f16-aim120-v1",
            )
            self.assertEqual(
                str(event.vulnerability_evidence_validation_acceptance_criteria_ref),
                "fixture://surrogate/acceptance/f16-aim120-v1",
            )
            self.assertEqual(str(event.vulnerability_effect_scale_source), "vulnerability_evidence_row")
            self.assertAlmostEqual(float(event.vulnerability_effect_scale), 1.19, delta=1.0e-6)

    def test_phase5_calibrated_descriptor_can_grant_pk_but_deterministic_fuze_remains_deferred(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="cmo_a2_vuln_full_descriptor_") as tmpdir:
            db_dir = _copy_database_with_f16_vulnerability(
                tmpdir,
                {
                    "synthetic": False,
                    "calibrated": True,
                    "pk_authority": True,
                    "deterministic_fuze_authority": True,
                    "evidence_dataset_ref": "unit_test_calibrated_f16_frag_full",
                    "calibration_status": "calibrated",
                    "provenance": "unit-test calibrated descriptor gate; synthetic fixture, not project data",
                },
                descriptor={
                    "dataset_id": "unit_test_calibrated_f16_frag_full",
                    "target_type": "F-16C_Block50",
                    "weapon_family": "blast_fragmentation",
                    "aspect_bucket": "beam",
                    "closure_bucket": "high",
                    "miss_distance_bucket": "near_miss_0_35m",
                    "source_kind": "external_calibration_dataset",
                    "calibration_status": "calibrated",
                    "pk_authority": True,
                    "deterministic_fuze_authority": True,
                    "provenance": "unit-test descriptor proving authority gating mechanics only",
                },
            )

            sim = ef_py.SimulationKernel()
            sim.reset(20260526)
            self.assertTrue(sim.load_database(db_dir))
            _attacker_id, target_id = _spawn_structured_f16_pair(sim)

            evidence = [
                float(value)
                for value in sim.debug_get_aircraft_vulnerability_evidence_state(target_id)
            ]
            self.assertEqual(evidence, [1.0, 0.0, 1.0, 1.0, 0.0, 1.0])

    def test_phase5_authorized_vulnerability_rows_drive_effects_event_scales(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cmo_a2_vuln_rows_descriptor_") as tmpdir:
            db_dir = _copy_database_with_f16_vulnerability(
                tmpdir,
                {
                    "synthetic": False,
                    "calibrated": True,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "evidence_dataset_ref": "unit_test_calibrated_f16_rod_rows",
                    "calibration_status": "calibrated",
                    "provenance": "unit-test calibrated rows gate; synthetic fixture, not project data",
                    "continuous_rod_scale": 0.91,
                    "beam_aspect_scale": 0.92,
                    "high_closure_scale": 0.93,
                    "direct_hit_scale": 0.94,
                },
                descriptor={
                    "dataset_id": "unit_test_calibrated_f16_rod_rows",
                    "schema_version": "a2.vulnerability_evidence.v1",
                    "target_type": "F-16C_Block50",
                    "weapon_family": "continuous_rod",
                    "aspect_bucket": "beam",
                    "closure_bucket": "high",
                    "miss_distance_bucket": "direct_hit",
                    "source_kind": "external_calibration_dataset",
                    "source_ref": "fixture://descriptor/unit-test-calibrated-f16-rod-rows",
                    "validation_artifact_ref": "fixture://validation/effect-scale-rows-report",
                    "calibration_status": "calibrated",
                    "effect_scale_authority": True,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "provenance": "unit-test descriptor proving row consumption mechanics only",
                    "rows": [
                        {
                            "row_id": "effect-scale-continuous-rod-beam-high",
                            "source_ref": "fixture://effect-scale/continuous-rod-beam-high",
                            "provenance": "unit-test effect-scale row fixture",
                            "weapon_family": "continuous_rod",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "direct_hit",
                            "family_scale": 1.31,
                            "aspect_scale": 1.17,
                            "closure_scale": 1.09,
                            "miss_distance_scale": 1.03,
                            "effect_scale": 1.42,
                        },
                        {
                            "weapon_family": "blast",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "direct_hit",
                            "effect_scale": 0.66,
                        },
                    ],
                },
            )

            _overlay, event = _profiled_local_hit_overlay_and_event_with_velocity(
                "continuous_rod",
                (-0.753, 4.0, 0.0),
                (900.0, -250.0, 0.0),
                damage=90.0,
                radius=35.0,
                database_path=db_dir,
            )

            self.assertTrue(bool(event.vulnerability_profile_present))
            self.assertFalse(bool(event.vulnerability_profile_synthetic))
            self.assertTrue(bool(event.vulnerability_calibrated_evidence))
            self.assertTrue(bool(event.vulnerability_evidence_dataset_valid))
            self.assertFalse(bool(event.vulnerability_pk_authority))
            self.assertFalse(bool(event.vulnerability_deterministic_fuze_authority))
            self.assertEqual(str(event.vulnerability_evidence_dataset_ref), "unit_test_calibrated_f16_rod_rows")
            self.assertEqual(str(event.vulnerability_calibration_status), "calibrated")
            self.assertEqual(
                str(event.vulnerability_evidence_schema_version),
                "a2.vulnerability_evidence.v1",
            )
            self.assertEqual(str(event.vulnerability_evidence_source_kind), "external_calibration_dataset")
            self.assertEqual(
                str(event.vulnerability_evidence_source_ref),
                "fixture://descriptor/unit-test-calibrated-f16-rod-rows",
            )
            self.assertEqual(
                str(event.vulnerability_evidence_validation_artifact_ref),
                "fixture://validation/effect-scale-rows-report",
            )
            self.assertEqual(str(event.vulnerability_aspect_bucket), "beam")
            self.assertAlmostEqual(float(event.vulnerability_family_scale), 1.31, delta=1.0e-6)
            self.assertAlmostEqual(float(event.vulnerability_aspect_scale), 1.17, delta=1.0e-6)
            self.assertAlmostEqual(float(event.vulnerability_closure_scale), 1.09, delta=1.0e-6)
            self.assertAlmostEqual(float(event.vulnerability_miss_distance_scale), 1.03, delta=1.0e-6)
            self.assertAlmostEqual(float(event.vulnerability_effect_scale), 1.42, delta=1.0e-6)
            self.assertEqual(str(event.vulnerability_effect_scale_source), "vulnerability_evidence_row")
            self.assertEqual(
                str(event.vulnerability_effect_scale_evidence_row_id),
                "effect-scale-continuous-rod-beam-high",
            )
            self.assertEqual(
                str(event.vulnerability_effect_scale_evidence_source_ref),
                "fixture://effect-scale/continuous-rod-beam-high",
            )
            self.assertEqual(
                str(event.vulnerability_effect_scale_evidence_provenance),
                "unit-test effect-scale row fixture",
            )

    def test_phase5_vulnerability_rows_require_effect_scale_authority(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cmo_a2_vuln_rows_denied_") as tmpdir:
            db_dir = _copy_database_with_f16_vulnerability(
                tmpdir,
                {
                    "synthetic": False,
                    "calibrated": True,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "evidence_dataset_ref": "unit_test_calibrated_f16_rows_denied",
                    "calibration_status": "calibrated",
                    "provenance": "unit-test rows denied fixture, not project data",
                    "continuous_rod_scale": 0.91,
                    "beam_aspect_scale": 0.92,
                    "high_closure_scale": 0.93,
                    "direct_hit_scale": 0.94,
                },
                descriptor={
                    "dataset_id": "unit_test_calibrated_f16_rows_denied",
                    "target_type": "F-16C_Block50",
                    "weapon_family": "continuous_rod",
                    "aspect_bucket": "beam",
                    "closure_bucket": "high",
                    "miss_distance_bucket": "direct_hit",
                    "source_kind": "external_calibration_dataset",
                    "calibration_status": "calibrated",
                    "effect_scale_authority": False,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "provenance": "unit-test descriptor proving row authority is explicit",
                    "rows": [
                        {
                            "row_id": "global-component-failure-probability",
                            "source_ref": "fixture://component-probability/global",
                            "provenance": "unit-test component probability row fixture",
                            "weapon_family": "continuous_rod",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "direct_hit",
                            "family_scale": 1.31,
                            "aspect_scale": 1.17,
                            "closure_scale": 1.09,
                            "miss_distance_scale": 1.03,
                            "effect_scale": 1.42,
                        }
                    ],
                },
            )

            _overlay, event = _profiled_local_hit_overlay_and_event_with_velocity(
                "continuous_rod",
                (-0.753, 4.0, 0.0),
                (900.0, -250.0, 0.0),
                damage=90.0,
                radius=35.0,
                database_path=db_dir,
            )

            self.assertTrue(bool(event.vulnerability_calibrated_evidence))
            self.assertTrue(bool(event.vulnerability_evidence_dataset_valid))
            self.assertAlmostEqual(float(event.vulnerability_family_scale), 0.91, delta=1.0e-6)
            self.assertAlmostEqual(float(event.vulnerability_aspect_scale), 0.92, delta=1.0e-6)
            self.assertAlmostEqual(float(event.vulnerability_closure_scale), 0.93, delta=1.0e-6)
            self.assertAlmostEqual(float(event.vulnerability_miss_distance_scale), 0.94, delta=1.0e-6)
            self.assertAlmostEqual(
                float(event.vulnerability_effect_scale),
                0.91 * 0.92 * 0.93 * 0.94,
                delta=1.0e-6,
            )
            self.assertEqual(str(event.vulnerability_effect_scale_source), "profile_scale")
            self.assertEqual(str(event.vulnerability_effect_scale_evidence_row_id), "")

    def test_phase5_effect_scale_rows_respect_mechanism_load_gate(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cmo_a2_vuln_effect_mechanism_gate_") as tmpdir:
            db_dir = _copy_database_with_f16_vulnerability(
                tmpdir,
                {
                    "synthetic": False,
                    "calibrated": True,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "evidence_dataset_ref": "unit_test_effect_scale_mechanism_gate",
                    "calibration_status": "calibrated",
                    "provenance": "unit-test effect-scale mechanism-load gate fixture, not project data",
                    "continuous_rod_scale": 0.91,
                    "beam_aspect_scale": 0.92,
                    "high_closure_scale": 0.93,
                    "direct_hit_scale": 0.94,
                },
                descriptor={
                    "dataset_id": "unit_test_effect_scale_mechanism_gate",
                    "target_type": "F-16C_Block50",
                    "weapon_family": "continuous_rod",
                    "aspect_bucket": "beam",
                    "closure_bucket": "high",
                    "miss_distance_bucket": "direct_hit",
                    "source_kind": "external_calibration_dataset",
                    "calibration_status": "calibrated",
                    "effect_scale_authority": True,
                    "component_failure_probability_authority": False,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "provenance": "unit-test descriptor proving effect-scale rows consume mechanism gates",
                    "rows": [
                        {
                            "row_id": "unreachable-effect-scale-high-rod-margin",
                            "source_ref": "fixture://effect-scale-mechanism/unreachable-high-rod",
                            "provenance": "unit-test unreachable effect-scale row fixture",
                            "weapon_family": "continuous_rod",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "direct_hit",
                            "min_rod_cut_margin": 9.0,
                            "effect_scale": 1.55,
                        },
                        {
                            "row_id": "reachable-effect-scale-fallback",
                            "source_ref": "fixture://effect-scale-mechanism/reachable-fallback",
                            "provenance": "unit-test reachable effect-scale row fixture",
                            "weapon_family": "continuous_rod",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "direct_hit",
                            "effect_scale": 1.18,
                        },
                    ],
                },
            )

            _overlay, event = _profiled_local_hit_overlay_and_event_with_velocity(
                "continuous_rod",
                (-0.8, 4.1, 0.0),
                (900.0, -250.0, 0.0),
                damage=90.0,
                radius=35.0,
                database_path=db_dir,
            )

            self.assertTrue(bool(event.vulnerability_calibrated_evidence))
            self.assertTrue(bool(event.vulnerability_evidence_dataset_valid))
            self.assertLess(float(event.component_primary_mechanism_rod_cut_margin), 9.0)
            self.assertAlmostEqual(float(event.vulnerability_effect_scale), 1.18, delta=1.0e-6)
            self.assertEqual(str(event.vulnerability_effect_scale_source), "vulnerability_evidence_row")
            self.assertEqual(
                str(event.vulnerability_effect_scale_evidence_row_id),
                "reachable-effect-scale-fallback",
            )
            self.assertEqual(
                str(event.vulnerability_effect_scale_evidence_source_ref),
                "fixture://effect-scale-mechanism/reachable-fallback",
            )
            self.assertEqual(
                str(event.vulnerability_effect_scale_evidence_provenance),
                "unit-test reachable effect-scale row fixture",
            )

    def test_phase5_effect_scale_rows_can_use_blast_scaled_distance_gate(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cmo_a2_vuln_blast_scaled_gate_") as tmpdir:
            db_dir = _copy_database_with_f16_vulnerability(
                tmpdir,
                {
                    "synthetic": False,
                    "calibrated": True,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "evidence_dataset_ref": "unit_test_blast_scaled_distance_gate",
                    "calibration_status": "calibrated",
                    "provenance": "unit-test blast scaled-distance gate fixture, not project data",
                    "blast_scale": 0.91,
                    "beam_aspect_scale": 0.92,
                    "high_closure_scale": 0.93,
                    "near_miss_scale": 0.94,
                },
                descriptor={
                    "dataset_id": "unit_test_blast_scaled_distance_gate",
                    "target_type": "F-16C_Block50",
                    "weapon_family": "blast",
                    "aspect_bucket": "beam",
                    "closure_bucket": "high",
                    "miss_distance_bucket": "near_miss",
                    "source_kind": "external_calibration_dataset",
                    "calibration_status": "calibrated",
                    "effect_scale_authority": True,
                    "component_failure_probability_authority": False,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "provenance": "unit-test descriptor proving blast scaled-distance row gates",
                    "rows": [
                        {
                            "row_id": "blast-close-scaled-distance",
                            "source_ref": "fixture://blast-scaled-distance/close",
                            "provenance": "unit-test close blast scaled-distance row fixture",
                            "weapon_family": "blast",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "near_miss",
                            "max_blast_scaled_distance_m_kg13": 2.0,
                            "effect_scale": 1.36,
                        },
                        {
                            "row_id": "blast-far-scaled-distance",
                            "source_ref": "fixture://blast-scaled-distance/far",
                            "provenance": "unit-test far blast scaled-distance row fixture",
                            "weapon_family": "blast",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "near_miss",
                            "min_blast_scaled_distance_m_kg13": 2.0,
                            "effect_scale": 0.82,
                        },
                    ],
                },
            )

            _close_overlay, close_event = _profiled_local_hit_overlay_and_event_with_velocity(
                "blast",
                (-0.753, 6.0, 0.0),
                (900.0, -250.0, 0.0),
                damage=90.0,
                radius=35.0,
                database_path=db_dir,
            )
            _far_overlay, far_event = _profiled_local_hit_overlay_and_event_with_velocity(
                "blast",
                (-0.753, 10.0, 0.0),
                (900.0, -250.0, 0.0),
                damage=90.0,
                radius=35.0,
                database_path=db_dir,
            )

            self.assertLess(float(close_event.mechanism_blast_scaled_distance_m_kg13), 2.0)
            self.assertGreater(float(far_event.mechanism_blast_scaled_distance_m_kg13), 2.0)
            self.assertGreater(
                float(close_event.vulnerability_effect_scale),
                float(far_event.vulnerability_effect_scale),
            )
            self.assertEqual(
                str(close_event.vulnerability_effect_scale_evidence_row_id),
                "blast-close-scaled-distance",
            )
            self.assertEqual(
                str(far_event.vulnerability_effect_scale_evidence_row_id),
                "blast-far-scaled-distance",
            )

    def test_phase5_effect_scale_rows_can_use_fragment_areal_density_gate(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cmo_a2_vuln_frag_density_gate_") as tmpdir:
            db_dir = _copy_database_with_f16_vulnerability(
                tmpdir,
                {
                    "synthetic": False,
                    "calibrated": True,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "evidence_dataset_ref": "unit_test_fragment_areal_density_gate",
                    "calibration_status": "calibrated",
                    "provenance": "unit-test fragment areal-density gate fixture, not project data",
                    "fragmentation_scale": 0.91,
                    "beam_aspect_scale": 0.92,
                    "high_closure_scale": 0.93,
                    "near_miss_scale": 0.94,
                },
                descriptor={
                    "dataset_id": "unit_test_fragment_areal_density_gate",
                    "target_type": "F-16C_Block50",
                    "weapon_family": "blast_fragmentation",
                    "aspect_bucket": "beam",
                    "closure_bucket": "high",
                    "miss_distance_bucket": "near_miss",
                    "source_kind": "external_calibration_dataset",
                    "calibration_status": "calibrated",
                    "effect_scale_authority": True,
                    "component_failure_probability_authority": False,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "provenance": "unit-test descriptor proving fragment areal-density row gates",
                    "rows": [
                        {
                            "row_id": "fragment-high-areal-density",
                            "source_ref": "fixture://fragment-density/high",
                            "provenance": "unit-test high fragment areal-density row fixture",
                            "weapon_family": "blast_fragmentation",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "near_miss",
                            "min_fragment_areal_density_per_m2": 2.0,
                            "effect_scale": 1.31,
                        },
                        {
                            "row_id": "fragment-low-areal-density",
                            "source_ref": "fixture://fragment-density/low",
                            "provenance": "unit-test low fragment areal-density row fixture",
                            "weapon_family": "blast_fragmentation",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "near_miss",
                            "max_fragment_areal_density_per_m2": 2.0,
                            "effect_scale": 0.79,
                        },
                    ],
                },
            )

            _close_overlay, close_event = _profiled_local_hit_overlay_and_event_with_velocity(
                "blast_fragmentation",
                (-0.753, 6.0, 0.0),
                (900.0, -250.0, 0.0),
                damage=90.0,
                radius=35.0,
                database_path=db_dir,
            )
            _far_overlay, far_event = _profiled_local_hit_overlay_and_event_with_velocity(
                "blast_fragmentation",
                (-0.753, 10.0, 0.0),
                (900.0, -250.0, 0.0),
                damage=90.0,
                radius=35.0,
                database_path=db_dir,
            )

            self.assertGreater(float(close_event.mechanism_fragment_areal_density_per_m2), 2.0)
            self.assertLess(float(far_event.mechanism_fragment_areal_density_per_m2), 2.0)
            self.assertEqual(
                str(close_event.vulnerability_effect_scale_evidence_row_id),
                "fragment-high-areal-density",
            )
            self.assertEqual(
                str(far_event.vulnerability_effect_scale_evidence_row_id),
                "fragment-low-areal-density",
            )

    def test_phase5_effect_scale_rows_can_use_surface_incidence_gate(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cmo_a2_vuln_surface_incidence_gate_") as tmpdir:
            db_dir = _copy_database_with_f16_vulnerability(
                tmpdir,
                {
                    "synthetic": False,
                    "calibrated": True,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "evidence_dataset_ref": "unit_test_surface_incidence_gate",
                    "calibration_status": "calibrated",
                    "provenance": "unit-test surface-incidence gate fixture, not project data",
                    "continuous_rod_scale": 0.91,
                    "beam_aspect_scale": 0.92,
                    "high_closure_scale": 0.93,
                    "direct_hit_scale": 0.94,
                },
                descriptor={
                    "dataset_id": "unit_test_surface_incidence_gate",
                    "target_type": "F-16C_Block50",
                    "weapon_family": "continuous_rod",
                    "aspect_bucket": "beam",
                    "closure_bucket": "high",
                    "miss_distance_bucket": "direct_hit",
                    "source_kind": "external_calibration_dataset",
                    "calibration_status": "calibrated",
                    "effect_scale_authority": True,
                    "component_failure_probability_authority": False,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "provenance": "unit-test descriptor proving surface-incidence row gates",
                    "rows": [
                        {
                            "row_id": "surface-normal-incidence",
                            "source_ref": "fixture://surface-incidence/normal",
                            "provenance": "unit-test normal-incidence row fixture",
                            "weapon_family": "continuous_rod",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "direct_hit",
                            "min_surface_incidence_cos": 0.5,
                            "effect_scale": 1.32,
                        },
                        {
                            "row_id": "surface-oblique-incidence",
                            "source_ref": "fixture://surface-incidence/oblique",
                            "provenance": "unit-test oblique-incidence row fixture",
                            "weapon_family": "continuous_rod",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "direct_hit",
                            "max_surface_incidence_cos": 0.5,
                            "effect_scale": 0.72,
                        },
                    ],
                },
            )

            _normal_overlay, normal_event = _profiled_local_hit_overlay_and_event_with_velocity(
                "continuous_rod",
                (-0.8, 4.49, 0.0),
                (900.0, 0.0, 0.0),
                damage=90.0,
                radius=35.0,
                database_path=db_dir,
            )
            _oblique_overlay, oblique_event = _profiled_local_hit_overlay_and_event_with_velocity(
                "continuous_rod",
                (-0.36, 4.1, 0.0),
                (900.0, 0.0, 0.0),
                damage=90.0,
                radius=35.0,
                database_path=db_dir,
            )

            self.assertGreater(float(normal_event.mechanism_surface_incidence_cos), 0.5)
            self.assertLess(float(oblique_event.mechanism_surface_incidence_cos), 0.5)
            self.assertAlmostEqual(float(normal_event.vulnerability_effect_scale), 1.32, delta=1.0e-6)
            self.assertAlmostEqual(float(oblique_event.vulnerability_effect_scale), 0.72, delta=1.0e-6)
            self.assertEqual(
                str(normal_event.vulnerability_effect_scale_evidence_row_id),
                "surface-normal-incidence",
            )
            self.assertEqual(
                str(oblique_event.vulnerability_effect_scale_evidence_row_id),
                "surface-oblique-incidence",
            )

    def test_phase5_authorized_rows_drive_component_failure_probability(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cmo_a2_vuln_component_pk_") as tmpdir:
            db_dir = _copy_database_with_f16_vulnerability(
                tmpdir,
                {
                    "synthetic": False,
                    "calibrated": True,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "evidence_dataset_ref": "unit_test_calibrated_f16_component_failure",
                    "calibration_status": "calibrated",
                    "provenance": "unit-test component failure row gate; synthetic fixture, not project data",
                },
                descriptor={
                    "dataset_id": "unit_test_calibrated_f16_component_failure",
                    "target_type": "F-16C_Block50",
                    "weapon_family": "continuous_rod",
                    "aspect_bucket": "beam",
                    "closure_bucket": "high",
                    "miss_distance_bucket": "direct_hit",
                    "source_kind": "external_calibration_dataset",
                    "calibration_status": "calibrated",
                    "effect_scale_authority": False,
                    "component_failure_probability_authority": True,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "provenance": "unit-test descriptor proving component probability row mechanics only",
                    "rows": [
                        {
                            "row_id": "global-component-failure-probability",
                            "source_ref": "fixture://component-probability/global",
                            "provenance": "unit-test component probability row fixture",
                            "weapon_family": "continuous_rod",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "direct_hit",
                            "component_failure_probability": 0.37,
                        }
                    ],
                },
            )

            _overlay, event = _profiled_local_hit_overlay_and_event_with_velocity(
                "continuous_rod",
                (-0.753, 4.0, 0.0),
                (900.0, -250.0, 0.0),
                damage=90.0,
                radius=35.0,
                database_path=db_dir,
            )

            self.assertTrue(bool(event.vulnerability_calibrated_evidence))
            self.assertTrue(bool(event.vulnerability_evidence_dataset_valid))
            self.assertFalse(bool(event.vulnerability_pk_authority))
            self.assertAlmostEqual(float(event.component_failure_probability), 0.37, delta=1.0e-6)
            self.assertEqual(str(event.component_failure_probability_source), "vulnerability_evidence_row")
            self.assertTrue(bool(event.component_failure_probability_calibrated))
            self.assertEqual(
                str(event.component_failure_probability_evidence_dataset_ref),
                "unit_test_calibrated_f16_component_failure",
            )
            self.assertEqual(
                str(event.component_failure_probability_evidence_row_id),
                "global-component-failure-probability",
            )
            self.assertEqual(
                str(event.component_failure_probability_evidence_source_ref),
                "fixture://component-probability/global",
            )
            self.assertEqual(
                str(event.component_failure_probability_evidence_provenance),
                "unit-test component probability row fixture",
            )
            component_rows = list(event.component_mechanism_load_rows)
            self.assertGreater(len(component_rows), 0)
            for row in component_rows:
                self.assertAlmostEqual(float(row.component_failure_probability), 0.37, delta=1.0e-6)
                self.assertEqual(
                    str(row.component_failure_probability_source),
                    "vulnerability_evidence_row",
                )
                self.assertTrue(bool(row.component_failure_probability_calibrated))
                self.assertEqual(
                    str(row.component_failure_probability_evidence_dataset_ref),
                    "unit_test_calibrated_f16_component_failure",
                )
                self.assertEqual(
                    str(row.component_failure_probability_evidence_row_id),
                    "global-component-failure-probability",
                )
                self.assertTrue(bool(row.component_failure_probability_authority))
                self.assertEqual(str(row.component_failure_probability_weapon_family), "continuous_rod")
                self.assertEqual(str(row.component_failure_probability_aspect_bucket), "beam")
                self.assertEqual(str(row.component_failure_probability_closure_bucket), "high")
                self.assertEqual(
                    str(row.component_failure_probability_miss_distance_bucket),
                    "direct_hit",
                )

    def test_phase5_component_failure_rows_require_probability_authority(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cmo_a2_vuln_component_pk_denied_") as tmpdir:
            db_dir = _copy_database_with_f16_vulnerability(
                tmpdir,
                {
                    "synthetic": False,
                    "calibrated": True,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "evidence_dataset_ref": "unit_test_calibrated_f16_component_failure_denied",
                    "calibration_status": "calibrated",
                    "provenance": "unit-test component failure row denied fixture, not project data",
                },
                descriptor={
                    "dataset_id": "unit_test_calibrated_f16_component_failure_denied",
                    "target_type": "F-16C_Block50",
                    "weapon_family": "continuous_rod",
                    "aspect_bucket": "beam",
                    "closure_bucket": "high",
                    "miss_distance_bucket": "direct_hit",
                    "source_kind": "external_calibration_dataset",
                    "calibration_status": "calibrated",
                    "effect_scale_authority": False,
                    "component_failure_probability_authority": False,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "provenance": "unit-test descriptor proving component probability authority is explicit",
                    "rows": [
                        {
                            "weapon_family": "continuous_rod",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "direct_hit",
                            "component_failure_probability": 0.37,
                        }
                    ],
                },
            )

            _overlay, event = _profiled_local_hit_overlay_and_event_with_velocity(
                "continuous_rod",
                (-0.753, 4.0, 0.0),
                (900.0, -250.0, 0.0),
                damage=90.0,
                radius=35.0,
                database_path=db_dir,
            )

            self.assertTrue(bool(event.vulnerability_calibrated_evidence))
            self.assertTrue(bool(event.vulnerability_evidence_dataset_valid))
            self.assertNotAlmostEqual(
                float(event.component_failure_probability),
                0.37,
                delta=1.0e-6,
            )
            self.assertEqual(str(event.component_failure_probability_source), "synthetic_sigmoid")
            self.assertFalse(bool(event.component_failure_probability_calibrated))
            self.assertEqual(str(event.component_failure_probability_evidence_dataset_ref), "")
            component_rows = list(event.component_mechanism_load_rows)
            self.assertGreater(len(component_rows), 0)
            for row in component_rows:
                self.assertNotAlmostEqual(
                    float(row.component_failure_probability),
                    0.37,
                    delta=1.0e-6,
                )
                self.assertEqual(
                    str(row.component_failure_probability_source),
                    "synthetic_sigmoid",
                )
                self.assertFalse(bool(row.component_failure_probability_calibrated))
                self.assertEqual(
                    str(row.component_failure_probability_evidence_dataset_ref),
                    "",
                )
                self.assertFalse(bool(row.component_failure_probability_authority))
                self.assertEqual(str(row.component_failure_probability_weapon_family), "continuous_rod")
                self.assertEqual(str(row.component_failure_probability_aspect_bucket), "beam")
                self.assertEqual(str(row.component_failure_probability_closure_bucket), "high")
                self.assertEqual(
                    str(row.component_failure_probability_miss_distance_bucket),
                    "direct_hit",
                )

    def test_phase5_authorized_rows_require_row_provenance_metadata(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cmo_a2_vuln_row_metadata_denied_") as tmpdir:
            db_dir = _copy_database_with_f16_vulnerability(
                tmpdir,
                {
                    "synthetic": False,
                    "calibrated": True,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "evidence_dataset_ref": "unit_test_row_metadata_required",
                    "calibration_status": "calibrated",
                    "provenance": "unit-test row provenance metadata gate, not project data",
                    "continuous_rod_scale": 0.91,
                    "beam_aspect_scale": 0.92,
                    "high_closure_scale": 0.93,
                    "direct_hit_scale": 0.94,
                },
                descriptor={
                    "dataset_id": "unit_test_row_metadata_required",
                    "target_type": "F-16C_Block50",
                    "weapon_family": "continuous_rod",
                    "aspect_bucket": "beam",
                    "closure_bucket": "high",
                    "miss_distance_bucket": "direct_hit",
                    "source_kind": "external_calibration_dataset",
                    "calibration_status": "calibrated",
                    "effect_scale_authority": True,
                    "component_failure_probability_authority": True,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "provenance": "unit-test descriptor proving row metadata is mandatory",
                    "rows": [
                        {
                            "weapon_family": "continuous_rod",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "direct_hit",
                            "effect_scale": 1.42,
                            "component_failure_probability": 0.81,
                        }
                    ],
                },
            )

            _overlay, event = _profiled_local_hit_overlay_and_event_with_velocity(
                "continuous_rod",
                (-0.753, 4.0, 0.0),
                (900.0, -250.0, 0.0),
                damage=90.0,
                radius=35.0,
                database_path=db_dir,
            )

            self.assertTrue(bool(event.vulnerability_calibrated_evidence))
            self.assertTrue(bool(event.vulnerability_evidence_dataset_valid))
            self.assertAlmostEqual(float(event.vulnerability_family_scale), 0.91, delta=1.0e-6)
            self.assertAlmostEqual(float(event.vulnerability_aspect_scale), 0.92, delta=1.0e-6)
            self.assertAlmostEqual(float(event.vulnerability_closure_scale), 0.93, delta=1.0e-6)
            self.assertAlmostEqual(float(event.vulnerability_miss_distance_scale), 0.94, delta=1.0e-6)
            self.assertNotAlmostEqual(float(event.vulnerability_effect_scale), 1.42, delta=1.0e-6)
            self.assertEqual(str(event.vulnerability_effect_scale_source), "profile_scale")
            self.assertEqual(str(event.vulnerability_effect_scale_evidence_row_id), "")
            self.assertEqual(str(event.component_failure_probability_source), "synthetic_sigmoid")
            self.assertFalse(bool(event.component_failure_probability_calibrated))
            self.assertEqual(str(event.component_failure_probability_evidence_row_id), "")
            component_rows = list(event.component_mechanism_load_rows)
            self.assertGreater(len(component_rows), 0)
            for row in component_rows:
                self.assertEqual(str(row.component_failure_probability_source), "synthetic_sigmoid")
                self.assertFalse(bool(row.component_failure_probability_authority))
                self.assertEqual(str(row.component_failure_probability_evidence_row_id), "")

    def test_phase5_component_specific_probability_rows_override_global_rows(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cmo_a2_vuln_component_specific_") as tmpdir:
            db_dir = _copy_database_with_f16_vulnerability(
                tmpdir,
                {
                    "synthetic": False,
                    "calibrated": True,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "evidence_dataset_ref": "unit_test_component_specific_probability_rows",
                    "calibration_status": "calibrated",
                    "provenance": "unit-test component-specific probability row fixture, not project data",
                },
                descriptor={
                    "dataset_id": "unit_test_component_specific_probability_rows",
                    "target_type": "F-16C_Block50",
                    "weapon_family": "continuous_rod",
                    "aspect_bucket": "beam",
                    "closure_bucket": "high",
                    "miss_distance_bucket": "direct_hit",
                    "source_kind": "external_calibration_dataset",
                    "calibration_status": "calibrated",
                    "effect_scale_authority": False,
                    "component_failure_probability_authority": True,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "provenance": "unit-test descriptor proving component-specific row precedence only",
                    "rows": [
                        {
                            "weapon_family": "continuous_rod",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "direct_hit",
                            "component_failure_probability": 0.21,
                        },
                        {
                            "row_id": "right-aileron-actuator-specific",
                            "source_ref": "fixture://component-specific/right-aileron-actuator-specific",
                            "provenance": "unit-test component-specific row fixture",
                            "weapon_family": "continuous_rod",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "direct_hit",
                            "component_name": "right_aileron_actuator",
                            "component_system": "flight_control",
                            "component_redundancy_group_id": "lateral_flight_control_actuators",
                            "component_failure_probability": 0.73,
                        },
                    ],
                },
            )

            _overlay, event = _profiled_local_hit_overlay_and_event_with_velocity(
                "continuous_rod",
                (-0.8, 4.1, 0.0),
                (900.0, -250.0, 0.0),
                damage=90.0,
                radius=35.0,
                database_path=db_dir,
            )

            self.assertTrue(bool(event.vulnerability_calibrated_evidence))
            self.assertEqual(str(event.component_primary_name), "right_aileron_actuator")
            self.assertAlmostEqual(float(event.component_failure_probability), 0.73, delta=1.0e-6)
            self.assertEqual(str(event.component_failure_probability_source), "vulnerability_evidence_row")
            self.assertEqual(
                str(event.component_failure_probability_evidence_row_id),
                "right-aileron-actuator-specific",
            )
            self.assertEqual(
                str(event.component_failure_probability_evidence_source_ref),
                "fixture://component-specific/right-aileron-actuator-specific",
            )
            self.assertEqual(
                str(event.component_failure_probability_evidence_provenance),
                "unit-test component-specific row fixture",
            )
            component_rows = list(event.component_mechanism_load_rows)
            matching_rows = [
                row for row in component_rows
                if str(row.component_name) == "right_aileron_actuator"
            ]
            self.assertEqual(len(matching_rows), 1)
            row = matching_rows[0]
            self.assertTrue(bool(row.component_failure_probability_component_specific))
            self.assertAlmostEqual(float(row.component_failure_probability), 0.73, delta=1.0e-6)
            self.assertEqual(
                str(row.component_failure_probability_evidence_component_name),
                "right_aileron_actuator",
            )
            self.assertEqual(
                str(row.component_failure_probability_evidence_component_system),
                "flight_control",
            )
            self.assertEqual(
                str(row.component_failure_probability_evidence_component_redundancy_group_id),
                "lateral_flight_control_actuators",
            )
            self.assertEqual(
                str(row.component_failure_probability_evidence_row_id),
                "right-aileron-actuator-specific",
            )
            self.assertEqual(
                str(row.component_failure_probability_evidence_source_ref),
                "fixture://component-specific/right-aileron-actuator-specific",
            )
            self.assertEqual(
                str(row.component_failure_probability_evidence_provenance),
                "unit-test component-specific row fixture",
            )

    def test_phase5_component_failure_rows_require_mechanism_load_gate(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cmo_a2_vuln_mechanism_gate_") as tmpdir:
            db_dir = _copy_database_with_f16_vulnerability(
                tmpdir,
                {
                    "synthetic": False,
                    "calibrated": True,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "evidence_dataset_ref": "unit_test_component_probability_mechanism_gate",
                    "calibration_status": "calibrated",
                    "provenance": "unit-test mechanism-load row gate fixture, not project data",
                },
                descriptor={
                    "dataset_id": "unit_test_component_probability_mechanism_gate",
                    "target_type": "F-16C_Block50",
                    "weapon_family": "continuous_rod",
                    "aspect_bucket": "beam",
                    "closure_bucket": "high",
                    "miss_distance_bucket": "direct_hit",
                    "source_kind": "external_calibration_dataset",
                    "calibration_status": "calibrated",
                    "effect_scale_authority": False,
                    "component_failure_probability_authority": True,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "provenance": "unit-test descriptor proving mechanism-load gates only",
                    "rows": [
                        {
                            "row_id": "unreachable-high-rod-margin",
                            "source_ref": "fixture://mechanism-gate/unreachable-high-rod-margin",
                            "provenance": "unit-test unreachable mechanism-load row fixture",
                            "weapon_family": "continuous_rod",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "direct_hit",
                            "min_rod_cut_margin": 9.0,
                            "component_failure_probability": 0.97,
                        },
                        {
                            "row_id": "reachable-fallback-rod-margin",
                            "source_ref": "fixture://mechanism-gate/reachable-fallback-rod-margin",
                            "provenance": "unit-test reachable fallback row fixture",
                            "weapon_family": "continuous_rod",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "direct_hit",
                            "component_failure_probability": 0.33,
                        },
                    ],
                },
            )

            _overlay, event = _profiled_local_hit_overlay_and_event_with_velocity(
                "continuous_rod",
                (-0.8, 4.1, 0.0),
                (900.0, -250.0, 0.0),
                damage=90.0,
                radius=35.0,
                database_path=db_dir,
            )

            self.assertTrue(bool(event.vulnerability_calibrated_evidence))
            self.assertTrue(bool(event.vulnerability_evidence_dataset_valid))
            self.assertLess(float(event.component_primary_mechanism_rod_cut_margin), 9.0)
            self.assertEqual(str(event.component_failure_probability_source), "vulnerability_evidence_row")
            self.assertAlmostEqual(float(event.component_failure_probability), 0.33, delta=1.0e-6)
            self.assertEqual(
                str(event.component_failure_probability_evidence_row_id),
                "reachable-fallback-rod-margin",
            )
            component_rows = list(event.component_mechanism_load_rows)
            self.assertGreater(len(component_rows), 0)
            for row in component_rows:
                self.assertLess(float(row.mechanism_rod_cut_margin), 9.0)
                self.assertAlmostEqual(float(row.component_failure_probability), 0.33, delta=1.0e-6)
                self.assertEqual(
                    str(row.component_failure_probability_source),
                    "vulnerability_evidence_row",
                )
                self.assertEqual(
                    str(row.component_failure_probability_evidence_row_id),
                    "reachable-fallback-rod-margin",
                )
                self.assertFalse(bool(row.component_failure_probability_component_specific))

    def test_phase5_component_failure_rows_can_use_fragment_areal_density_gate(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cmo_a2_vuln_frag_density_component_gate_") as tmpdir:
            db_dir = _copy_database_with_f16_vulnerability(
                tmpdir,
                {
                    "synthetic": False,
                    "calibrated": True,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "evidence_dataset_ref": "unit_test_component_probability_fragment_density",
                    "calibration_status": "calibrated",
                    "provenance": "unit-test fragment-density component gate fixture, not project data",
                },
                descriptor={
                    "dataset_id": "unit_test_component_probability_fragment_density",
                    "target_type": "F-16C_Block50",
                    "weapon_family": "blast_fragmentation",
                    "aspect_bucket": "beam",
                    "closure_bucket": "high",
                    "miss_distance_bucket": "near_miss",
                    "source_kind": "external_calibration_dataset",
                    "calibration_status": "calibrated",
                    "effect_scale_authority": False,
                    "component_failure_probability_authority": True,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "provenance": "unit-test descriptor proving fragment-density gates component rows",
                    "rows": [
                        {
                            "row_id": "component-high-fragment-density",
                            "source_ref": "fixture://fragment-density-component/high",
                            "provenance": "unit-test high fragment-density component row fixture",
                            "weapon_family": "blast_fragmentation",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "near_miss",
                            "min_fragment_areal_density_per_m2": 2.0,
                            "component_failure_probability": 0.62,
                        },
                        {
                            "row_id": "component-low-fragment-density",
                            "source_ref": "fixture://fragment-density-component/low",
                            "provenance": "unit-test low fragment-density component row fixture",
                            "weapon_family": "blast_fragmentation",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "near_miss",
                            "max_fragment_areal_density_per_m2": 2.0,
                            "component_failure_probability": 0.18,
                        },
                    ],
                },
            )

            _close_overlay, close_event = _profiled_local_hit_overlay_and_event_with_velocity(
                "blast_fragmentation",
                (-0.753, 6.0, 0.0),
                (900.0, -250.0, 0.0),
                damage=90.0,
                radius=35.0,
                database_path=db_dir,
            )
            _far_overlay, far_event = _profiled_local_hit_overlay_and_event_with_velocity(
                "blast_fragmentation",
                (-0.753, 10.0, 0.0),
                (900.0, -250.0, 0.0),
                damage=90.0,
                radius=35.0,
                database_path=db_dir,
            )

            self.assertGreater(float(close_event.mechanism_fragment_areal_density_per_m2), 2.0)
            self.assertLess(float(far_event.mechanism_fragment_areal_density_per_m2), 2.0)
            self.assertAlmostEqual(float(close_event.component_failure_probability), 0.62, delta=1.0e-6)
            self.assertAlmostEqual(float(far_event.component_failure_probability), 0.18, delta=1.0e-6)
            self.assertEqual(
                str(close_event.component_failure_probability_evidence_row_id),
                "component-high-fragment-density",
            )
            self.assertEqual(
                str(far_event.component_failure_probability_evidence_row_id),
                "component-low-fragment-density",
            )

    def test_phase5_component_failure_rows_can_use_surface_incidence_gate(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cmo_a2_vuln_surface_incidence_component_gate_") as tmpdir:
            db_dir = _copy_database_with_f16_vulnerability(
                tmpdir,
                {
                    "synthetic": False,
                    "calibrated": True,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "evidence_dataset_ref": "unit_test_component_probability_surface_incidence",
                    "calibration_status": "calibrated",
                    "provenance": "unit-test surface-incidence component gate fixture, not project data",
                },
                descriptor={
                    "dataset_id": "unit_test_component_probability_surface_incidence",
                    "target_type": "F-16C_Block50",
                    "weapon_family": "continuous_rod",
                    "aspect_bucket": "beam",
                    "closure_bucket": "high",
                    "miss_distance_bucket": "direct_hit",
                    "source_kind": "external_calibration_dataset",
                    "calibration_status": "calibrated",
                    "effect_scale_authority": False,
                    "component_failure_probability_authority": True,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "provenance": "unit-test descriptor proving surface-incidence gates component rows",
                    "rows": [
                        {
                            "row_id": "component-normal-surface-incidence",
                            "source_ref": "fixture://surface-incidence-component/normal",
                            "provenance": "unit-test normal surface-incidence component row fixture",
                            "weapon_family": "continuous_rod",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "direct_hit",
                            "min_surface_incidence_cos": 0.5,
                            "component_failure_probability": 0.61,
                        },
                        {
                            "row_id": "component-oblique-surface-incidence",
                            "source_ref": "fixture://surface-incidence-component/oblique",
                            "provenance": "unit-test oblique surface-incidence component row fixture",
                            "weapon_family": "continuous_rod",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "direct_hit",
                            "max_surface_incidence_cos": 0.5,
                            "component_failure_probability": 0.19,
                        },
                    ],
                },
            )

            _normal_overlay, normal_event = _profiled_local_hit_overlay_and_event_with_velocity(
                "continuous_rod",
                (-0.8, 4.49, 0.0),
                (900.0, 0.0, 0.0),
                damage=90.0,
                radius=35.0,
                database_path=db_dir,
            )
            _oblique_overlay, oblique_event = _profiled_local_hit_overlay_and_event_with_velocity(
                "continuous_rod",
                (-0.36, 4.1, 0.0),
                (900.0, 0.0, 0.0),
                damage=90.0,
                radius=35.0,
                database_path=db_dir,
            )

            self.assertGreater(float(normal_event.mechanism_surface_incidence_cos), 0.5)
            self.assertLess(float(oblique_event.mechanism_surface_incidence_cos), 0.5)
            self.assertAlmostEqual(float(normal_event.component_failure_probability), 0.61, delta=1.0e-6)
            self.assertAlmostEqual(float(oblique_event.component_failure_probability), 0.19, delta=1.0e-6)
            self.assertEqual(str(normal_event.component_failure_probability_source), "vulnerability_evidence_row")
            self.assertEqual(str(oblique_event.component_failure_probability_source), "vulnerability_evidence_row")
            self.assertTrue(bool(normal_event.component_failure_probability_calibrated))
            self.assertTrue(bool(oblique_event.component_failure_probability_calibrated))
            self.assertEqual(
                str(normal_event.component_failure_probability_evidence_row_id),
                "component-normal-surface-incidence",
            )
            self.assertEqual(
                str(normal_event.component_failure_probability_evidence_source_ref),
                "fixture://surface-incidence-component/normal",
            )
            self.assertEqual(
                str(oblique_event.component_failure_probability_evidence_row_id),
                "component-oblique-surface-incidence",
            )
            self.assertEqual(
                str(oblique_event.component_failure_probability_evidence_source_ref),
                "fixture://surface-incidence-component/oblique",
            )

    def test_phase5_component_failure_rows_select_mechanism_load_bucket(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cmo_a2_vuln_mechanism_bucket_") as tmpdir:
            db_dir = _copy_database_with_f16_vulnerability(
                tmpdir,
                {
                    "synthetic": False,
                    "calibrated": True,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "evidence_dataset_ref": "unit_test_component_probability_mechanism_bucket",
                    "calibration_status": "calibrated",
                    "provenance": "unit-test mechanism-load bucket fixture, not project data",
                },
                descriptor={
                    "dataset_id": "unit_test_component_probability_mechanism_bucket",
                    "target_type": "F-16C_Block50",
                    "weapon_family": "continuous_rod",
                    "aspect_bucket": "beam",
                    "closure_bucket": "high",
                    "miss_distance_bucket": "direct_hit",
                    "source_kind": "external_calibration_dataset",
                    "calibration_status": "calibrated",
                    "effect_scale_authority": False,
                    "component_failure_probability_authority": True,
                    "pk_authority": False,
                    "deterministic_fuze_authority": False,
                    "provenance": "unit-test descriptor proving row buckets consume mechanism loads",
                    "rows": [
                        {
                            "row_id": "low-rod-cut-margin",
                            "source_ref": "fixture://mechanism-bucket/low-rod-cut-margin",
                            "provenance": "unit-test low rod-load bucket fixture",
                            "weapon_family": "continuous_rod",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "direct_hit",
                            "max_rod_cut_margin": 2.24,
                            "component_failure_probability": 0.24,
                        },
                        {
                            "row_id": "high-rod-cut-margin",
                            "source_ref": "fixture://mechanism-bucket/high-rod-cut-margin",
                            "provenance": "unit-test high rod-load bucket fixture",
                            "weapon_family": "continuous_rod",
                            "aspect_bucket": "beam",
                            "closure_bucket": "high",
                            "miss_distance_bucket": "direct_hit",
                            "min_rod_cut_margin": 2.24,
                            "component_failure_probability": 0.64,
                        },
                    ],
                },
            )

            _low_overlay, low_event = _profiled_local_hit_overlay_and_event_with_velocity(
                "continuous_rod",
                (-0.8, 4.1, 0.0),
                (750.0, -250.0, 0.0),
                damage=90.0,
                radius=35.0,
                database_path=db_dir,
            )
            _high_overlay, high_event = _profiled_local_hit_overlay_and_event_with_velocity(
                "continuous_rod",
                (-0.8, 4.1, 0.0),
                (900.0, -250.0, 0.0),
                damage=90.0,
                radius=35.0,
                database_path=db_dir,
            )

            self.assertGreaterEqual(float(low_event.closure_mps), 700.0)
            self.assertLess(float(low_event.component_primary_mechanism_rod_cut_margin), 2.24)
            self.assertGreater(float(high_event.component_primary_mechanism_rod_cut_margin), 2.24)
            self.assertAlmostEqual(float(low_event.component_failure_probability), 0.24, delta=1.0e-6)
            self.assertAlmostEqual(float(high_event.component_failure_probability), 0.64, delta=1.0e-6)
            self.assertEqual(str(low_event.component_failure_probability_source), "vulnerability_evidence_row")
            self.assertEqual(str(high_event.component_failure_probability_source), "vulnerability_evidence_row")
            self.assertTrue(bool(low_event.component_failure_probability_calibrated))
            self.assertTrue(bool(high_event.component_failure_probability_calibrated))
            self.assertEqual(
                str(low_event.component_failure_probability_evidence_row_id),
                "low-rod-cut-margin",
            )
            self.assertEqual(
                str(high_event.component_failure_probability_evidence_row_id),
                "high-rod-cut-margin",
            )

    def test_phase3_continuous_rod_near_miss_uses_relative_velocity_axis(self) -> None:
        near_wing = (-0.753, 7.1, 0.0)
        broadside_sweep = _profiled_local_hit_overlay_with_velocity(
            "continuous_rod",
            near_wing,
            (0.0, -900.0, 0.0),
            damage=90.0,
            radius=35.0,
        )
        axial_pass = _profiled_local_hit_overlay_with_velocity(
            "continuous_rod",
            near_wing,
            (-900.0, 0.0, 0.0),
            damage=90.0,
            radius=35.0,
        )
        blast_fragmentation_broadside = _profiled_local_hit_overlay_with_velocity(
            "blast_fragmentation",
            near_wing,
            (0.0, -900.0, 0.0),
            damage=90.0,
            radius=35.0,
        )
        blast_fragmentation_axial = _profiled_local_hit_overlay_with_velocity(
            "blast_fragmentation",
            near_wing,
            (-900.0, 0.0, 0.0),
            damage=90.0,
            radius=35.0,
        )

        self.assertLess(broadside_sweep["flight_control"], axial_pass["flight_control"])
        self.assertLess(broadside_sweep["hydraulic"], axial_pass["hydraulic"])
        self.assertLess(broadside_sweep["structure"], axial_pass["structure"])
        self.assertLess(
            abs(blast_fragmentation_broadside["flight_control"] - blast_fragmentation_axial["flight_control"]),
            abs(broadside_sweep["flight_control"] - axial_pass["flight_control"]),
        )

    def test_phase3_surface_incidence_cos_reports_obliquity_evidence(self) -> None:
        normal_side = (-0.8, 4.49, 0.0)
        oblique_side = (-0.36, 4.1, 0.0)
        _normal_overlay, normal_event = _profiled_local_hit_overlay_and_event_with_velocity(
            "continuous_rod",
            normal_side,
            (900.0, 0.0, 0.0),
            damage=90.0,
            radius=35.0,
        )
        _oblique_overlay, oblique_event = _profiled_local_hit_overlay_and_event_with_velocity(
            "continuous_rod",
            oblique_side,
            (900.0, 0.0, 0.0),
            damage=90.0,
            radius=35.0,
        )
        _invalid_overlay, invalid_event = _profiled_local_hit_overlay_and_event_with_velocity(
            "continuous_rod",
            normal_side,
            (0.0, 0.0, 0.0),
            damage=90.0,
            radius=35.0,
        )

        self.assertGreater(float(normal_event.mechanism_surface_incidence_cos), 0.5)
        self.assertLess(float(oblique_event.mechanism_surface_incidence_cos), 0.5)
        self.assertAlmostEqual(float(invalid_event.mechanism_surface_incidence_cos), 0.0, delta=1.0e-6)
        self.assertAlmostEqual(
            float(normal_event.component_primary_mechanism_surface_incidence_cos),
            float(normal_event.mechanism_surface_incidence_cos),
            delta=1.0e-6,
        )
        normal_rows = list(normal_event.component_mechanism_load_rows)
        self.assertGreater(len(normal_rows), 0)
        self.assertGreaterEqual(
            min(float(row.mechanism_surface_incidence_cos) for row in normal_rows),
            0.0,
        )
        self.assertLessEqual(
            max(float(row.mechanism_surface_incidence_cos) for row in normal_rows),
            1.0,
        )

    def test_phase3_warhead_spatial_sampling_reports_fragment_and_rod_evidence(self) -> None:
        near_wing = (-0.753, 7.1, 0.0)
        _blast_overlay, _, blast_event = _profiled_local_hit_overlay(
            "blast_fragmentation",
            near_wing,
            damage=90.0,
            radius=35.0,
        )

        self.assertEqual(str(blast_event.effect_family), "blast_fragmentation")
        self.assertGreater(int(blast_event.warhead_spatial_sample_count), 100)
        self.assertGreater(float(blast_event.warhead_spatial_hit_estimate), 0.0)
        self.assertLess(float(blast_event.warhead_spatial_hit_fraction), 0.10)
        self.assertGreater(float(blast_event.warhead_spatial_energy_scale), 0.0)
        self.assertGreater(float(blast_event.mechanism_fragment_energy_j), 0.0)
        self.assertGreater(float(blast_event.mechanism_penetration_margin), 0.0)
        self.assertGreater(float(blast_event.mechanism_blast_overpressure_kpa), 0.0)
        self.assertGreater(float(blast_event.mechanism_blast_impulse_kpa_ms), 0.0)

        sim = ef_py.SimulationKernel()
        sim.reset(20260526)
        self.assertTrue(sim.load_database(_DB_PATH))
        attacker_id, target_id = _spawn_structured_f16_pair(sim)
        rod_profile = _make_warhead_profile("continuous_rod", damage=90.0, radius=35.0)

        self.assertTrue(
            bool(
                sim.debug_apply_profiled_local_proximity_hit_with_velocity(
                    attacker_id,
                    target_id,
                    near_wing[0],
                    near_wing[1],
                    near_wing[2],
                    rod_profile,
                    0.0,
                    -900.0,
                    0.0,
                )
            )
        )
        broadside_event = sim.export_recent_engagement_events().effects_events[-1]

        self.assertTrue(
            bool(
                sim.debug_apply_profiled_local_proximity_hit_with_velocity(
                    attacker_id,
                    target_id,
                    near_wing[0],
                    near_wing[1],
                    near_wing[2],
                    rod_profile,
                    -900.0,
                    0.0,
                    0.0,
                )
            )
        )
        axial_event = sim.export_recent_engagement_events().effects_events[-1]

        self.assertEqual(str(broadside_event.effect_family), "continuous_rod")
        self.assertGreater(int(broadside_event.warhead_spatial_sample_count), 20)
        self.assertGreater(
            float(broadside_event.warhead_spatial_pattern_scale),
            float(axial_event.warhead_spatial_pattern_scale),
        )
        self.assertGreater(
            float(broadside_event.warhead_spatial_hit_estimate),
            float(axial_event.warhead_spatial_hit_estimate),
        )
        self.assertGreater(float(broadside_event.mechanism_rod_cut_margin), 0.0)
        self.assertGreater(
            float(broadside_event.mechanism_rod_cut_margin),
            float(axial_event.mechanism_rod_cut_margin),
        )

    def test_phase3_warhead_mechanism_load_evidence_tracks_mechanism_family(self) -> None:
        direct_wing = (-0.8, 4.1, 0.0)
        _blast_overlay, blast_event = _profiled_local_hit_overlay_and_event_with_velocity(
            "blast",
            direct_wing,
            (900.0, -250.0, 0.0),
            damage=90.0,
            radius=35.0,
        )
        _frag_overlay, frag_event = _profiled_local_hit_overlay_and_event_with_velocity(
            "blast_fragmentation",
            direct_wing,
            (900.0, -250.0, 0.0),
            damage=90.0,
            radius=35.0,
        )
        _rod_overlay, rod_event = _profiled_local_hit_overlay_and_event_with_velocity(
            "continuous_rod",
            direct_wing,
            (900.0, -250.0, 0.0),
            damage=90.0,
            radius=35.0,
        )

        self.assertEqual(str(blast_event.effect_family), "blast")
        self.assertGreater(float(blast_event.mechanism_blast_overpressure_kpa), 0.0)
        self.assertGreater(float(blast_event.mechanism_blast_impulse_kpa_ms), 0.0)
        self.assertGreater(float(blast_event.mechanism_blast_scaled_distance_m_kg13), 0.0)
        self.assertAlmostEqual(float(blast_event.mechanism_fragment_energy_j), 0.0, delta=1.0e-6)
        self.assertAlmostEqual(float(blast_event.mechanism_rod_cut_margin), 0.0, delta=1.0e-6)

        self.assertEqual(str(frag_event.effect_family), "blast_fragmentation")
        self.assertGreater(float(frag_event.mechanism_fragment_energy_j), 0.0)
        self.assertGreater(float(frag_event.mechanism_fragment_areal_density_per_m2), 0.0)
        self.assertGreater(float(frag_event.mechanism_penetration_margin), 0.0)
        self.assertGreater(float(frag_event.mechanism_blast_overpressure_kpa), 0.0)
        self.assertGreater(float(frag_event.mechanism_blast_scaled_distance_m_kg13), 0.0)

        self.assertEqual(str(rod_event.effect_family), "continuous_rod")
        self.assertGreater(float(rod_event.mechanism_rod_cut_margin), 0.0)
        self.assertGreater(float(rod_event.mechanism_penetration_margin), 0.0)
        self.assertAlmostEqual(float(rod_event.mechanism_blast_overpressure_kpa), 0.0, delta=1.0e-6)

    def test_phase3_blast_scaled_distance_tracks_standoff_and_pressure(self) -> None:
        near_wing = (-0.753, 6.0, 0.0)
        far_wing = (-0.753, 10.0, 0.0)
        _near_overlay, near_event = _profiled_local_hit_overlay_and_event_with_velocity(
            "blast",
            near_wing,
            (900.0, -250.0, 0.0),
            damage=90.0,
            radius=35.0,
        )
        _far_overlay, far_event = _profiled_local_hit_overlay_and_event_with_velocity(
            "blast",
            far_wing,
            (900.0, -250.0, 0.0),
            damage=90.0,
            radius=35.0,
        )

        self.assertGreater(float(near_event.mechanism_blast_scaled_distance_m_kg13), 0.0)
        self.assertGreater(
            float(far_event.mechanism_blast_scaled_distance_m_kg13),
            float(near_event.mechanism_blast_scaled_distance_m_kg13),
        )
        self.assertLess(
            float(far_event.mechanism_blast_overpressure_kpa),
            float(near_event.mechanism_blast_overpressure_kpa),
        )
        self.assertLess(
            float(far_event.mechanism_blast_impulse_kpa_ms),
            float(near_event.mechanism_blast_impulse_kpa_ms),
        )

    def test_phase3_fragment_areal_density_tracks_standoff(self) -> None:
        near_wing = (-0.753, 6.0, 0.0)
        far_wing = (-0.753, 10.0, 0.0)
        _near_overlay, near_event = _profiled_local_hit_overlay_and_event_with_velocity(
            "blast_fragmentation",
            near_wing,
            (900.0, -250.0, 0.0),
            damage=90.0,
            radius=35.0,
        )
        _far_overlay, far_event = _profiled_local_hit_overlay_and_event_with_velocity(
            "blast_fragmentation",
            far_wing,
            (900.0, -250.0, 0.0),
            damage=90.0,
            radius=35.0,
        )

        self.assertGreater(float(near_event.mechanism_fragment_areal_density_per_m2), 0.0)
        self.assertLess(
            float(far_event.mechanism_fragment_areal_density_per_m2),
            float(near_event.mechanism_fragment_areal_density_per_m2),
        )
        self.assertLess(
            float(far_event.warhead_spatial_hit_estimate),
            float(near_event.warhead_spatial_hit_estimate),
        )

    def test_phase3_primary_component_reports_mechanism_load_vector(self) -> None:
        direct_wing = (-0.8, 4.1, 0.0)
        _frag_overlay, frag_event = _profiled_local_hit_overlay_and_event_with_velocity(
            "blast_fragmentation",
            direct_wing,
            (900.0, -250.0, 0.0),
            damage=90.0,
            radius=35.0,
        )
        _rod_overlay, rod_event = _profiled_local_hit_overlay_and_event_with_velocity(
            "continuous_rod",
            direct_wing,
            (900.0, -250.0, 0.0),
            damage=90.0,
            radius=35.0,
        )

        self.assertEqual(str(frag_event.component_primary_name), "right_aileron_actuator")
        self.assertEqual(str(frag_event.component_primary_system), "flight_control")
        frag_rows = list(frag_event.component_mechanism_load_rows)
        self.assertEqual(len(frag_rows), int(frag_event.component_hit_count))
        frag_primary_row = next(
            (
                row
                for row in frag_rows
                if str(row.component_name) == str(frag_event.component_primary_name)
            ),
            None,
        )
        self.assertIsNotNone(frag_primary_row)
        assert frag_primary_row is not None
        self.assertEqual(str(frag_primary_row.component_system), "flight_control")
        self.assertEqual(
            str(frag_primary_row.component_redundancy_group_id),
            str(frag_event.component_primary_redundancy_group_id),
        )
        self.assertTrue(bool(frag_primary_row.direct_hit))
        self.assertAlmostEqual(float(frag_primary_row.distance_m), 0.0, delta=1.0e-6)
        self.assertGreater(float(frag_primary_row.effect_scale), 0.0)
        self.assertGreater(float(frag_primary_row.component_threshold_scale), 0.0)
        self.assertGreater(float(frag_primary_row.component_failure_probability), 0.0)
        self.assertEqual(
            str(frag_primary_row.component_failure_probability_source),
            "synthetic_sigmoid",
        )
        self.assertFalse(bool(frag_primary_row.component_failure_probability_calibrated))
        self.assertEqual(
            str(frag_primary_row.component_failure_probability_evidence_dataset_ref),
            "",
        )
        self.assertGreaterEqual(float(frag_primary_row.component_failure_sample), 0.0)
        self.assertLessEqual(float(frag_primary_row.component_failure_sample), 1.0)
        self.assertFalse(bool(frag_primary_row.component_failure_probability_authority))
        self.assertEqual(
            str(frag_primary_row.component_failure_probability_weapon_family),
            "blast_fragmentation",
        )
        self.assertEqual(str(frag_primary_row.component_failure_probability_aspect_bucket), "beam")
        self.assertEqual(str(frag_primary_row.component_failure_probability_closure_bucket), "high")
        self.assertEqual(
            str(frag_primary_row.component_failure_probability_miss_distance_bucket),
            "direct_hit",
        )
        self.assertGreater(float(frag_event.component_primary_mechanism_fragment_energy_j), 0.0)
        self.assertGreater(
            float(frag_event.component_primary_mechanism_fragment_areal_density_per_m2),
            0.0,
        )
        self.assertGreater(float(frag_event.component_primary_mechanism_penetration_margin), 0.0)
        self.assertGreater(
            float(frag_event.component_primary_mechanism_blast_overpressure_kpa),
            0.0,
        )
        self.assertGreater(
            float(frag_event.component_primary_mechanism_blast_impulse_kpa_ms),
            0.0,
        )
        self.assertGreater(
            float(frag_event.component_primary_mechanism_blast_scaled_distance_m_kg13),
            0.0,
        )
        self.assertAlmostEqual(
            float(frag_event.component_primary_mechanism_rod_cut_margin),
            0.0,
            delta=1.0e-6,
        )
        self.assertAlmostEqual(
            float(frag_primary_row.mechanism_fragment_energy_j),
            float(frag_event.component_primary_mechanism_fragment_energy_j),
            delta=1.0e-6,
        )
        self.assertAlmostEqual(
            float(frag_primary_row.mechanism_fragment_areal_density_per_m2),
            float(frag_event.component_primary_mechanism_fragment_areal_density_per_m2),
            delta=1.0e-6,
        )
        self.assertAlmostEqual(
            float(frag_primary_row.mechanism_penetration_margin),
            float(frag_event.component_primary_mechanism_penetration_margin),
            delta=1.0e-6,
        )
        self.assertAlmostEqual(
            float(frag_primary_row.mechanism_blast_overpressure_kpa),
            float(frag_event.component_primary_mechanism_blast_overpressure_kpa),
            delta=1.0e-6,
        )
        self.assertAlmostEqual(
            float(frag_primary_row.mechanism_blast_impulse_kpa_ms),
            float(frag_event.component_primary_mechanism_blast_impulse_kpa_ms),
            delta=1.0e-6,
        )
        self.assertAlmostEqual(
            float(frag_primary_row.mechanism_blast_scaled_distance_m_kg13),
            float(frag_event.component_primary_mechanism_blast_scaled_distance_m_kg13),
            delta=1.0e-6,
        )
        self.assertAlmostEqual(
            float(frag_primary_row.mechanism_rod_cut_margin),
            float(frag_event.component_primary_mechanism_rod_cut_margin),
            delta=1.0e-6,
        )

        self.assertEqual(str(rod_event.component_primary_name), "right_aileron_actuator")
        rod_rows = list(rod_event.component_mechanism_load_rows)
        self.assertEqual(len(rod_rows), int(rod_event.component_hit_count))
        rod_primary_row = next(
            (
                row
                for row in rod_rows
                if str(row.component_name) == str(rod_event.component_primary_name)
            ),
            None,
        )
        self.assertIsNotNone(rod_primary_row)
        assert rod_primary_row is not None
        self.assertGreater(float(rod_event.component_primary_mechanism_rod_cut_margin), 0.0)
        self.assertGreater(float(rod_event.component_primary_mechanism_penetration_margin), 0.0)
        self.assertAlmostEqual(
            float(rod_event.component_primary_mechanism_blast_overpressure_kpa),
            0.0,
            delta=1.0e-6,
        )
        self.assertGreater(float(rod_primary_row.mechanism_rod_cut_margin), 0.0)
        self.assertAlmostEqual(
            float(rod_primary_row.mechanism_rod_cut_margin),
            float(rod_event.component_primary_mechanism_rod_cut_margin),
            delta=1.0e-6,
        )
        self.assertAlmostEqual(
            float(rod_primary_row.mechanism_blast_overpressure_kpa),
            0.0,
            delta=1.0e-6,
        )

    def test_phase3_warhead_orientation_axis_modulates_rod_pattern_evidence(self) -> None:
        near_wing = (-0.753, 7.1, 0.0)
        missile_velocity = (0.0, -900.0, 0.0)
        broadside_overlay, broadside_event = (
            _profiled_local_hit_overlay_and_event_with_velocity_and_attitude(
                "continuous_rod",
                near_wing,
                missile_velocity,
                (0.0, 0.0, 0.0),
                damage=90.0,
                radius=35.0,
            )
        )
        axial_overlay, axial_event = (
            _profiled_local_hit_overlay_and_event_with_velocity_and_attitude(
                "continuous_rod",
                near_wing,
                missile_velocity,
                (90.0, 0.0, 0.0),
                damage=90.0,
                radius=35.0,
            )
        )

        self.assertEqual(str(broadside_event.effect_family), "continuous_rod")
        self.assertAlmostEqual(abs(float(broadside_event.warhead_orientation_axis_forward)), 1.0, delta=1.0e-6)
        self.assertAlmostEqual(abs(float(axial_event.warhead_orientation_axis_right)), 1.0, delta=1.0e-6)
        self.assertGreater(
            float(broadside_event.warhead_orientation_pattern_scale),
            float(axial_event.warhead_orientation_pattern_scale),
        )
        self.assertGreater(
            float(broadside_event.warhead_spatial_pattern_scale),
            float(axial_event.warhead_spatial_pattern_scale),
        )
        self.assertGreater(
            float(broadside_event.warhead_spatial_hit_estimate),
            float(axial_event.warhead_spatial_hit_estimate),
        )
        self.assertLess(
            broadside_overlay["flight_control"],
            axial_overlay["flight_control"],
        )

    def test_phase3_local_hit_geometry_respects_target_pitch_and_roll(self) -> None:
        local_aileron = (-0.8, 4.1, 0.0)
        overlay, event = _profiled_local_hit_overlay_and_event_with_target_attitude(
            "continuous_rod",
            local_aileron,
            (12.0, 25.0),
            damage=90.0,
            radius=35.0,
        )

        self.assertAlmostEqual(float(event.detonation_local_forward_m), local_aileron[0], delta=1.0e-5)
        self.assertAlmostEqual(float(event.detonation_local_right_m), local_aileron[1], delta=1.0e-5)
        self.assertAlmostEqual(float(event.detonation_local_up_m), local_aileron[2], delta=1.0e-5)
        self.assertTrue(bool(event.direct_hitbox_intersection))
        self.assertEqual(str(event.component_primary_name), "right_aileron_actuator")
        self.assertEqual(str(event.component_primary_system), "flight_control")
        self.assertLess(overlay["flight_control"], 1.0)
        self.assertLess(overlay["roll_control"], 1.0)

    def test_e3_sentry_c2node_uses_authored_structured_damage_model(self) -> None:
        sim = ef_py.SimulationKernel()
        sim.reset(20260526)
        self.assertTrue(sim.load_database(_DB_PATH))
        attacker_id, target_id = _spawn_attacker_and_e3_target(sim)

        health_before = [float(value) for value in sim.get_unit_health(target_id)]
        damage_before = [float(value) for value in sim.get_unit_damage_state(target_id)]
        sensor_before = sim.get_sensor_debug_view(target_id)
        self.assertEqual(health_before, [500.0, 500.0])
        self.assertEqual(damage_before, [1.0, 1.0, 1.0, 1.0])

        self.assertTrue(
            bool(
                sim.debug_apply_local_proximity_hit(
                    attacker_id,
                    target_id,
                    5.0,
                    0.0,
                    3.8,
                    240.0,
                    80.0,
                )
            )
        )

        health_after = [float(value) for value in sim.get_unit_health(target_id)]
        damage_after = [float(value) for value in sim.get_unit_damage_state(target_id)]
        sensor_after = sim.get_sensor_debug_view(target_id)
        self.assertTrue(sim.is_unit_active(target_id))
        self.assertEqual(health_after, health_before)
        self.assertLess(float(damage_after[0]), float(damage_before[0]))
        self.assertLess(float(damage_after[2]), float(damage_before[2]))
        self.assertLess(float(sensor_after.max_range), float(sensor_before.max_range))

        events = sim.export_recent_engagement_events()
        self.assertEqual(len(events.effects_events), 1)
        self.assertEqual(len(events.damage_reports), 1)
        report = events.damage_reports[0]
        self.assertAlmostEqual(float(report.hp_delta), 0.0, delta=1.0e-6)
        self.assertLess(float(report.system_health_delta), 0.0)
        self.assertFalse(bool(report.destroyed))
        self.assertNotEqual(str(report.loss_state_to), "lost")

    def test_aircraft_database_units_have_authored_structured_damage_models(self) -> None:
        cases = {
            "F-16C_Block50": (0.0, 0.0, 0.0),
            "Su-35S_Flanker-E": (0.0, 0.0, 0.0),
            "MQ-9_Reaper": (0.0, 0.0, 0.0),
            "MH-60R_MVP": (0.0, 0.0, 0.0),
            "E-3_Sentry_AWACS": (5.0, 0.0, 3.8),
        }

        for target_type, local_impact in cases.items():
            with self.subTest(target_type=target_type):
                sim = ef_py.SimulationKernel()
                sim.reset(20260526)
                self.assertTrue(sim.load_database(_DB_PATH))
                attacker_id, target_id = _spawn_attacker_and_named_target(sim, target_type)

                health_before = [float(value) for value in sim.get_unit_health(target_id)]
                damage_before = [float(value) for value in sim.get_unit_damage_state(target_id)]
                self.assertGreater(health_before[0], 0.0)
                self.assertEqual(damage_before, [1.0, 1.0, 1.0, 1.0])

                self.assertTrue(
                    bool(
                        sim.debug_apply_local_proximity_hit(
                            attacker_id,
                            target_id,
                            float(local_impact[0]),
                            float(local_impact[1]),
                            float(local_impact[2]),
                            240.0,
                            80.0,
                        )
                    )
                )

                health_after = [float(value) for value in sim.get_unit_health(target_id)]
                damage_after = [float(value) for value in sim.get_unit_damage_state(target_id)]
                self.assertTrue(sim.is_unit_active(target_id))
                self.assertEqual(health_after, health_before)
                self.assertLess(min(damage_after), min(damage_before))

                events = sim.export_recent_engagement_events()
                self.assertEqual(len(events.effects_events), 1)
                self.assertEqual(len(events.damage_reports), 1)
                report = events.damage_reports[0]
                self.assertAlmostEqual(float(report.hp_delta), 0.0, delta=1.0e-6)
                self.assertLess(float(report.system_health_delta), 0.0)
                self.assertFalse(bool(report.destroyed))
                self.assertNotEqual(str(report.loss_state_to), "lost")

    def test_live_missile_hit_records_structured_air_damage_without_hp_first_kill(self) -> None:
        sim = _make_baseline_kernel()
        blue_id, red_id = _spawn_geometry_pair(
            sim,
            red_x=13000.0,
            red_y=9000.0,
            red_heading=270.0,
            red_vx=-260.0,
            red_vy=0.0,
        )
        missile_id = int(sim.fire_missile(blue_id, red_id))
        self.assertGreater(missile_id, 0)

        health_before = [float(value) for value in sim.get_unit_health(red_id)]
        damage_before = [float(value) for value in sim.get_unit_damage_state(red_id)]

        for step_idx in range(3600):
            if not sim.is_unit_active(missile_id):
                break
            _set_contacts(
                sim,
                missile_id,
                [
                    _relative_detection_from_truth(
                        sim,
                        missile_id,
                        red_id,
                        timestamp=step_idx * sim.get_time_step(),
                        local_sensor_hit=True,
                    )
                ],
            )
            sim.step()

        self.assertFalse(sim.is_unit_active(missile_id))
        self.assertTrue(sim.is_unit_active(red_id))
        self.assertEqual([float(value) for value in sim.get_unit_health(red_id)], health_before)
        damage_after = [float(value) for value in sim.get_unit_damage_state(red_id)]
        self.assertLess(min(damage_after), min(damage_before))

        events = sim.export_recent_engagement_events()
        self.assertEqual(len(events.launch_events), 1)
        self.assertEqual(len(events.effects_events), 1)
        self.assertEqual(len(events.damage_reports), 1)
        effect = events.effects_events[0]
        report = events.damage_reports[0]
        self.assertEqual(int(effect.munition.entity_id), missile_id)
        self.assertEqual(int(effect.target.entity_id), red_id)
        self.assertEqual(str(effect.trigger_type), "proximity_fuze")
        self.assertEqual(str(effect.outcome_state), "damage_applied")
        self.assertTrue(math.isfinite(float(effect.miss_distance_m)))
        self.assertGreaterEqual(float(effect.miss_distance_m), 0.0)
        self.assertLess(float(effect.miss_distance_m), 35.0)
        self.assertAlmostEqual(float(effect.warhead_lethal_radius_m), 35.0, delta=1.0e-6)
        self.assertTrue(math.isfinite(float(effect.closure_mps)))
        self.assertGreaterEqual(float(effect.closure_mps), 0.0)
        missile_axis_norm = math.sqrt(
            float(effect.missile_axis_forward) ** 2 +
            float(effect.missile_axis_right) ** 2 +
            float(effect.missile_axis_up) ** 2
        )
        self.assertAlmostEqual(missile_axis_norm, 1.0, delta=1.0e-3)
        self.assertAlmostEqual(float(report.hp_delta), 0.0, delta=1.0e-6)
        self.assertLess(float(report.system_health_delta), 0.0)
        self.assertFalse(bool(report.destroyed))
        self.assertNotEqual(str(report.loss_state_to), "lost")

    def test_debug_runtime_exposes_proximity_fuze_miss_distance_state(self) -> None:
        sim = _make_baseline_kernel()
        blue_id, red_id = _spawn_geometry_pair(
            sim,
            red_x=0.0,
            red_y=22000.0,
            red_heading=180.0,
            red_vx=0.0,
            red_vy=-250.0,
        )
        missile_id = int(sim.fire_missile(blue_id, red_id))
        self.assertGreater(missile_id, 0)

        initial_runtime = _missile_runtime(sim, missile_id)
        self.assertTrue(math.isinf(float(initial_runtime["proximity_min_dist_m"])))
        self.assertTrue(math.isinf(float(initial_runtime["proximity_last_dist_m"])))
        self.assertFalse(bool(initial_runtime["proximity_engaged"]))

        for step_idx in range(3):
            _set_contacts(
                sim,
                missile_id,
                [_relative_detection_from_truth(sim, missile_id, red_id, timestamp=step_idx * sim.get_time_step())],
            )
            sim.step()

        runtime = _missile_runtime(sim, missile_id)
        self.assertTrue(math.isfinite(float(runtime["proximity_min_dist_m"])))
        self.assertTrue(math.isfinite(float(runtime["proximity_last_dist_m"])))
        self.assertGreater(float(runtime["proximity_min_dist_m"]), 0.0)
        self.assertGreater(float(runtime["proximity_last_dist_m"]), 0.0)

    def test_phase0_pn_miss_distance_baseline_matrix_tracks_engagement_geometries(self) -> None:
        cases = {
            "head_on": _run_miss_distance_case(
                red_x=0.0,
                red_y=26000.0,
                red_heading=180.0,
                red_vx=0.0,
                red_vy=-250.0,
            ),
            "tail_chase": _run_miss_distance_case(
                red_x=0.0,
                red_y=18000.0,
                red_heading=0.0,
                red_vx=0.0,
                red_vy=290.0,
            ),
            "beam": _run_miss_distance_case(
                red_x=-9000.0,
                red_y=15000.0,
                red_heading=90.0,
                red_vx=300.0,
                red_vy=0.0,
            ),
            "high_off_boresight": _run_miss_distance_case(
                red_x=13000.0,
                red_y=9000.0,
                red_heading=270.0,
                red_vx=-260.0,
                red_vy=0.0,
            ),
        }

        for name, result in cases.items():
            with self.subTest(geometry=name):
                self.assertFalse(bool(result["missile_active"]))
                self.assertTrue(math.isfinite(float(result["truth_min_dist_m"])))
                self.assertTrue(math.isfinite(float(result["proximity_min_dist_m"])))
                self.assertGreaterEqual(float(result["proximity_min_dist_m"]), 0.0)
                self.assertLess(
                    abs(float(result["truth_min_dist_m"]) - float(result["proximity_min_dist_m"])),
                    500.0,
                )
                self.assertTrue(bool(result["proximity_engaged"]))
                self.assertTrue(bool(result["terminal_seeker_active"]))

        self.assertLess(float(cases["head_on"]["proximity_min_dist_m"]), 50.0)
        self.assertGreater(float(cases["tail_chase"]["proximity_min_dist_m"]), 5000.0)
        self.assertGreater(float(cases["beam"]["proximity_min_dist_m"]), 250.0)
        self.assertLess(float(cases["beam"]["proximity_min_dist_m"]), 1000.0)
        self.assertLess(float(cases["high_off_boresight"]["proximity_min_dist_m"]), 5.0)
        self.assertGreater(
            float(cases["head_on"]["max_achieved_lateral_accel_mps2"]),
            float(cases["tail_chase"]["max_achieved_lateral_accel_mps2"]) + 100.0,
        )

    def test_launch_initializes_mass_and_runtime_state(self) -> None:
        sim = _make_kernel()
        tuning = sim.get_missile_tuning()
        tuning.propellant_mass_kg = 22.0
        tuning.track_break_time_s = 1.4
        tuning.boost_time_s = 2.5
        tuning.sustain_time_s = 0.7
        sim.set_missile_tuning(tuning)

        blue_id, red_id = _spawn_pair(sim)
        _set_contacts(sim, blue_id, [_make_detection(red_id, range_m=30000.0, bearing_deg=8.0)])

        missile_id = int(sim.fire_missile(blue_id, red_id))
        self.assertGreater(missile_id, 0)

        mass_state = sim.debug_get_mass_state(missile_id)
        self.assertEqual(len(mass_state), 6)
        self.assertAlmostEqual(float(mass_state[0]), 58.0, delta=1.0e-6)
        self.assertAlmostEqual(float(mass_state[1]), 22.0, delta=1.0e-6)
        self.assertAlmostEqual(float(mass_state[3]), 80.0, delta=1.0e-6)
        self.assertAlmostEqual(float(mass_state[4]), 58.0, delta=1.0e-6)
        self.assertAlmostEqual(float(mass_state[5]), 80.0, delta=1.0e-6)

        runtime = sim.debug_get_missile_runtime_state(missile_id)
        self.assertTrue(bool(runtime["p0_runtime_initialized"]))
        self.assertTrue(bool(runtime["seeker_has_valid_track"]))
        self.assertTrue(bool(runtime["seeker_has_range"]))
        self.assertEqual(int(runtime["seeker_mode"]), 0)
        self.assertAlmostEqual(float(runtime["track_memory_timeout_s"]), 1.4, delta=1.0e-6)
        self.assertAlmostEqual(float(runtime["filtered_bearing_deg"]), 8.0, delta=1.0e-6)
        self.assertAlmostEqual(float(runtime["filtered_range_m"]), 30000.0, delta=1.0e-6)
        self.assertAlmostEqual(float(runtime["current_speed_mps"]), 250.0, delta=1.0e-6)
        self.assertAlmostEqual(float(runtime["burnout_time_s"]), 3.2, delta=1.0e-6)

    def test_shared_burn_window_changes_guidance_speed_profile(self) -> None:
        short_sim = _make_kernel()
        short_tuning = short_sim.get_missile_tuning()
        short_tuning.boost_time_s = 0.6
        short_tuning.sustain_time_s = 0.0
        short_sim.set_missile_tuning(short_tuning)

        long_sim = _make_kernel()
        long_tuning = long_sim.get_missile_tuning()
        long_tuning.boost_time_s = 4.0
        long_tuning.sustain_time_s = 0.0
        long_sim.set_missile_tuning(long_tuning)

        short_blue, short_red = _spawn_pair(short_sim)
        long_blue, long_red = _spawn_pair(long_sim)
        _set_contacts(short_sim, short_blue, [_make_detection(short_red, range_m=28000.0, bearing_deg=0.0)])
        _set_contacts(long_sim, long_blue, [_make_detection(long_red, range_m=28000.0, bearing_deg=0.0)])

        short_id = int(short_sim.fire_missile(short_blue, short_red))
        long_id = int(long_sim.fire_missile(long_blue, long_red))
        self.assertGreater(short_id, 0)
        self.assertGreater(long_id, 0)

        sample_short = 0.0
        sample_long = 0.0
        for step_idx in range(180):
            t_short = step_idx * short_sim.get_time_step()
            t_long = step_idx * long_sim.get_time_step()
            _set_contacts(short_sim, short_id, [_make_detection(short_red, range_m=max(2000.0, 28000.0 - 350.0 * t_short), bearing_deg=0.0, timestamp=t_short)])
            _set_contacts(long_sim, long_id, [_make_detection(long_red, range_m=max(2000.0, 28000.0 - 350.0 * t_long), bearing_deg=0.0, timestamp=t_long)])
            short_sim.step()
            long_sim.step()
            if step_idx == 120:
                sample_short = _velocity_speed(short_sim, short_id)
                sample_long = _velocity_speed(long_sim, long_id)

        self.assertGreater(sample_long, sample_short + 40.0)

    def test_shared_reference_area_changes_drag_cost(self) -> None:
        clean_sim = _make_kernel()
        clean_tuning = clean_sim.get_missile_tuning()
        clean_tuning.reference_area_m2 = 0.015
        clean_sim.set_missile_tuning(clean_tuning)

        draggy_sim = _make_kernel()
        draggy_tuning = draggy_sim.get_missile_tuning()
        draggy_tuning.reference_area_m2 = 0.060
        draggy_sim.set_missile_tuning(draggy_tuning)

        clean_blue, clean_red = _spawn_pair(clean_sim)
        draggy_blue, draggy_red = _spawn_pair(draggy_sim)
        _set_contacts(clean_sim, clean_blue, [_make_detection(clean_red, range_m=30000.0, bearing_deg=0.0)])
        _set_contacts(draggy_sim, draggy_blue, [_make_detection(draggy_red, range_m=30000.0, bearing_deg=0.0)])

        clean_id = int(clean_sim.fire_missile(clean_blue, clean_red))
        draggy_id = int(draggy_sim.fire_missile(draggy_blue, draggy_red))
        self.assertGreater(clean_id, 0)
        self.assertGreater(draggy_id, 0)

        for step_idx in range(240):
            t_clean = step_idx * clean_sim.get_time_step()
            t_draggy = step_idx * draggy_sim.get_time_step()
            _set_contacts(clean_sim, clean_id, [_make_detection(clean_red, range_m=max(3000.0, 30000.0 - 350.0 * t_clean), bearing_deg=0.0, timestamp=t_clean)])
            _set_contacts(draggy_sim, draggy_id, [_make_detection(draggy_red, range_m=max(3000.0, 30000.0 - 350.0 * t_draggy), bearing_deg=0.0, timestamp=t_draggy)])
            clean_sim.step()
            draggy_sim.step()

        clean_speed = _velocity_speed(clean_sim, clean_id)
        draggy_speed = _velocity_speed(draggy_sim, draggy_id)
        self.assertGreater(clean_speed, draggy_speed + 20.0)

    def test_shared_cd0_subsonic_changes_low_speed_drag_cost(self) -> None:
        clean_sim = _make_kernel()
        clean_tuning = clean_sim.get_missile_tuning()
        clean_tuning.boost_time_s = 0.0
        clean_tuning.sustain_time_s = 0.0
        clean_tuning.max_speed = 320.0
        clean_tuning.reference_area_m2 = 0.050
        clean_tuning.cd0_subsonic = 0.12
        clean_tuning.cd0_supersonic = 0.12
        clean_sim.set_missile_tuning(clean_tuning)

        draggy_sim = _make_kernel()
        draggy_tuning = draggy_sim.get_missile_tuning()
        draggy_tuning.boost_time_s = 0.0
        draggy_tuning.sustain_time_s = 0.0
        draggy_tuning.max_speed = 320.0
        draggy_tuning.reference_area_m2 = 0.050
        draggy_tuning.cd0_subsonic = 0.80
        draggy_tuning.cd0_supersonic = 0.80
        draggy_sim.set_missile_tuning(draggy_tuning)

        _, clean_red, clean_id = _spawn_and_fire(clean_sim, range_m=30000.0, bearing_deg=0.0)
        _, draggy_red, draggy_id = _spawn_and_fire(draggy_sim, range_m=30000.0, bearing_deg=0.0)

        for step_idx in range(180):
            t_clean = step_idx * clean_sim.get_time_step()
            t_draggy = step_idx * draggy_sim.get_time_step()
            _set_contacts(
                clean_sim,
                clean_id,
                [_make_detection(clean_red, range_m=max(6000.0, 30000.0 - 250.0 * t_clean), bearing_deg=0.0, timestamp=t_clean)],
            )
            _set_contacts(
                draggy_sim,
                draggy_id,
                [_make_detection(draggy_red, range_m=max(6000.0, 30000.0 - 250.0 * t_draggy), bearing_deg=0.0, timestamp=t_draggy)],
            )
            clean_sim.step()
            draggy_sim.step()

        clean_speed = _velocity_speed(clean_sim, clean_id)
        draggy_speed = _velocity_speed(draggy_sim, draggy_id)
        self.assertGreater(clean_speed, draggy_speed + 20.0)

    def test_shared_cd0_supersonic_changes_high_speed_drag_cost(self) -> None:
        clean_sim = _make_kernel()
        clean_tuning = clean_sim.get_missile_tuning()
        clean_tuning.max_speed = 1800.0
        clean_tuning.propellant_mass_kg = 24.0
        clean_tuning.reference_area_m2 = 0.030
        clean_tuning.boost_time_s = 1.2
        clean_tuning.sustain_time_s = 1.2
        clean_tuning.boost_thrust_n = 28000.0
        clean_tuning.sustain_thrust_n = 12000.0
        clean_tuning.cd0_subsonic = 0.20
        clean_tuning.cd0_supersonic = 0.28
        clean_sim.set_missile_tuning(clean_tuning)

        draggy_sim = _make_kernel()
        draggy_tuning = draggy_sim.get_missile_tuning()
        draggy_tuning.max_speed = 1800.0
        draggy_tuning.propellant_mass_kg = 24.0
        draggy_tuning.reference_area_m2 = 0.030
        draggy_tuning.boost_time_s = 1.2
        draggy_tuning.sustain_time_s = 1.2
        draggy_tuning.boost_thrust_n = 28000.0
        draggy_tuning.sustain_thrust_n = 12000.0
        draggy_tuning.cd0_subsonic = 0.20
        draggy_tuning.cd0_supersonic = 1.10
        draggy_sim.set_missile_tuning(draggy_tuning)

        _, clean_red, clean_id = _spawn_and_fire(clean_sim, range_m=26000.0, bearing_deg=0.0)
        _, draggy_red, draggy_id = _spawn_and_fire(draggy_sim, range_m=26000.0, bearing_deg=0.0)

        sample_clean = 0.0
        sample_draggy = 0.0
        for step_idx in range(144):
            t_clean = step_idx * clean_sim.get_time_step()
            t_draggy = step_idx * draggy_sim.get_time_step()
            _set_contacts(
                clean_sim,
                clean_id,
                [_make_detection(clean_red, range_m=max(4000.0, 26000.0 - 350.0 * t_clean), bearing_deg=0.0, timestamp=t_clean)],
            )
            _set_contacts(
                draggy_sim,
                draggy_id,
                [_make_detection(draggy_red, range_m=max(4000.0, 26000.0 - 350.0 * t_draggy), bearing_deg=0.0, timestamp=t_draggy)],
            )
            clean_sim.step()
            draggy_sim.step()
            if step_idx == 100:
                sample_clean = _velocity_speed(clean_sim, clean_id)
                sample_draggy = _velocity_speed(draggy_sim, draggy_id)

        self.assertGreater(sample_clean, sample_draggy + 35.0)

    def test_shared_induced_drag_changes_turn_energy_loss(self) -> None:
        clean_sim = _make_kernel()
        clean_tuning = clean_sim.get_missile_tuning()
        clean_tuning.nav_gain = 10.0
        clean_tuning.max_lateral_g = 24.0
        clean_tuning.autopilot_tau_s = 0.03
        clean_tuning.max_accel_response_g_per_s = 400.0
        clean_tuning.reference_area_m2 = 0.020
        clean_tuning.induced_drag_k = 1.5
        clean_sim.set_missile_tuning(clean_tuning)

        draggy_sim = _make_kernel()
        draggy_tuning = draggy_sim.get_missile_tuning()
        draggy_tuning.nav_gain = 10.0
        draggy_tuning.max_lateral_g = 24.0
        draggy_tuning.autopilot_tau_s = 0.03
        draggy_tuning.max_accel_response_g_per_s = 400.0
        draggy_tuning.reference_area_m2 = 0.020
        draggy_tuning.induced_drag_k = 18.0
        draggy_sim.set_missile_tuning(draggy_tuning)

        _, clean_red, clean_id = _spawn_and_fire(clean_sim, range_m=6000.0, bearing_deg=85.0)
        _, draggy_red, draggy_id = _spawn_and_fire(draggy_sim, range_m=6000.0, bearing_deg=85.0)

        clean_speed = 0.0
        draggy_speed = 0.0
        for step_idx in range(120):
            t_clean = step_idx * clean_sim.get_time_step()
            t_draggy = step_idx * draggy_sim.get_time_step()
            _set_contacts(
                clean_sim,
                clean_id,
                [_make_detection(clean_red, range_m=6000.0, bearing_deg=85.0, timestamp=t_clean)],
            )
            _set_contacts(
                draggy_sim,
                draggy_id,
                [_make_detection(draggy_red, range_m=6000.0, bearing_deg=85.0, timestamp=t_draggy)],
            )
            clean_sim.step()
            draggy_sim.step()
            if step_idx == 100:
                clean_speed = _velocity_speed(clean_sim, clean_id)
                draggy_speed = _velocity_speed(draggy_sim, draggy_id)

        self.assertGreater(clean_speed, draggy_speed + 25.0)

    def test_shared_boost_and_sustain_thrust_change_speed_profile(self) -> None:
        low_sim = _make_kernel()
        low_tuning = low_sim.get_missile_tuning()
        low_tuning.max_speed = 1800.0
        low_tuning.propellant_mass_kg = 24.0
        low_tuning.reference_area_m2 = 0.015
        low_tuning.boost_time_s = 0.8
        low_tuning.sustain_time_s = 1.6
        low_tuning.boost_thrust_n = 14000.0
        low_tuning.sustain_thrust_n = 3500.0
        low_sim.set_missile_tuning(low_tuning)

        high_sim = _make_kernel()
        high_tuning = high_sim.get_missile_tuning()
        high_tuning.max_speed = 1800.0
        high_tuning.propellant_mass_kg = 24.0
        high_tuning.reference_area_m2 = 0.015
        high_tuning.boost_time_s = 0.8
        high_tuning.sustain_time_s = 1.6
        high_tuning.boost_thrust_n = 26000.0
        high_tuning.sustain_thrust_n = 9000.0
        high_sim.set_missile_tuning(high_tuning)

        _, low_red, low_id = _spawn_and_fire(low_sim, range_m=26000.0, bearing_deg=0.0)
        _, high_red, high_id = _spawn_and_fire(high_sim, range_m=26000.0, bearing_deg=0.0)

        boost_low = 0.0
        boost_high = 0.0
        sustain_low = 0.0
        sustain_high = 0.0
        for step_idx in range(120):
            t_low = step_idx * low_sim.get_time_step()
            t_high = step_idx * high_sim.get_time_step()
            _set_contacts(
                low_sim,
                low_id,
                [_make_detection(low_red, range_m=max(4000.0, 26000.0 - 350.0 * t_low), bearing_deg=0.0, timestamp=t_low)],
            )
            _set_contacts(
                high_sim,
                high_id,
                [_make_detection(high_red, range_m=max(4000.0, 26000.0 - 350.0 * t_high), bearing_deg=0.0, timestamp=t_high)],
            )
            low_sim.step()
            high_sim.step()
            if step_idx == 24:
                boost_low = _velocity_speed(low_sim, low_id)
                boost_high = _velocity_speed(high_sim, high_id)
            if step_idx == 84:
                sustain_low = _velocity_speed(low_sim, low_id)
                sustain_high = _velocity_speed(high_sim, high_id)

        self.assertGreater(boost_high, boost_low + 35.0)
        self.assertGreater(sustain_high, sustain_low + 45.0)

    def test_boost_then_decay_speed_profile(self) -> None:
        sim = _make_kernel()
        blue_id, red_id = _spawn_pair(sim)
        _set_contacts(sim, blue_id, [_make_detection(red_id, range_m=30000.0, bearing_deg=0.0)])

        missile_id = int(sim.fire_missile(blue_id, red_id))
        self.assertGreater(missile_id, 0)

        speeds: list[float] = []
        time_s = 0.0
        for _ in range(420):
            _set_contacts(
                sim,
                missile_id,
                [_make_detection(red_id, range_m=max(2000.0, 30000.0 - 350.0 * time_s), bearing_deg=0.0, timestamp=time_s)],
            )
            sim.step()
            time_s += sim.get_time_step()
            if not sim.is_unit_active(missile_id):
                break
            speeds.append(_velocity_speed(sim, missile_id))

        self.assertGreater(len(speeds), 120)
        peak_speed = max(speeds)
        self.assertGreater(peak_speed, speeds[5] + 80.0)
        self.assertLess(speeds[-1], peak_speed - 40.0)

    def test_shared_bearing_filter_tau_changes_track_response(self) -> None:
        fast_sim = _make_kernel()
        fast_tuning = fast_sim.get_missile_tuning()
        fast_tuning.bearing_filter_tau_s = 0.02
        fast_tuning.elevation_filter_tau_s = 0.02
        fast_tuning.range_filter_tau_s = 0.02
        fast_sim.set_missile_tuning(fast_tuning)

        slow_sim = _make_kernel()
        slow_tuning = slow_sim.get_missile_tuning()
        slow_tuning.bearing_filter_tau_s = 1.0
        slow_tuning.elevation_filter_tau_s = 1.0
        slow_tuning.range_filter_tau_s = 1.0
        slow_sim.set_missile_tuning(slow_tuning)

        _, fast_red, fast_id = _spawn_and_fire(fast_sim, range_m=24000.0, bearing_deg=0.0)
        _, slow_red, slow_id = _spawn_and_fire(slow_sim, range_m=24000.0, bearing_deg=0.0)

        for step_idx in range(10):
            t_fast = step_idx * fast_sim.get_time_step()
            t_slow = step_idx * slow_sim.get_time_step()
            _set_contacts(
                fast_sim,
                fast_id,
                [_make_detection(fast_red, range_m=22000.0, bearing_deg=60.0, timestamp=t_fast)],
            )
            _set_contacts(
                slow_sim,
                slow_id,
                [_make_detection(slow_red, range_m=22000.0, bearing_deg=60.0, timestamp=t_slow)],
            )
            fast_sim.step()
            slow_sim.step()

        fast_runtime = _missile_runtime(fast_sim, fast_id)
        slow_runtime = _missile_runtime(slow_sim, slow_id)
        fast_bearing = float(fast_runtime["filtered_bearing_deg"])
        slow_bearing = float(slow_runtime["filtered_bearing_deg"])
        self.assertGreater(fast_bearing, 55.0)
        self.assertLess(slow_bearing, 12.0)
        self.assertGreater(fast_bearing, slow_bearing + 35.0)

    def test_mass_depletion_during_propulsion(self) -> None:
        sim = _make_kernel()
        blue_id, red_id = _spawn_pair(sim)
        _set_contacts(sim, blue_id, [_make_detection(red_id, range_m=30000.0, bearing_deg=0.0)])

        missile_id = int(sim.fire_missile(blue_id, red_id))
        self.assertGreater(missile_id, 0)

        masses: list[float] = []
        time_s = 0.0
        for _ in range(300):
            _set_contacts(
                sim,
                missile_id,
                [_make_detection(red_id, range_m=max(2000.0, 30000.0 - 350.0 * time_s), bearing_deg=0.0, timestamp=time_s)],
            )
            sim.step()
            time_s += sim.get_time_step()
            state = sim.debug_get_mass_state(missile_id)
            self.assertTrue(len(state) >= 6)
            masses.append(float(state[3]))

        self.assertGreater(masses[0], masses[60])
        self.assertGreater(masses[60], masses[120])
        self.assertAlmostEqual(masses[-1], masses[-30], delta=0.5)

    def test_shared_autopilot_tau_changes_response_buildup(self) -> None:
        fast_sim = _make_kernel()
        fast_tuning = fast_sim.get_missile_tuning()
        fast_tuning.nav_gain = 10.0
        fast_tuning.max_lateral_g = 28.0
        fast_tuning.max_accel_response_g_per_s = 400.0
        fast_tuning.autopilot_tau_s = 0.03
        fast_sim.set_missile_tuning(fast_tuning)

        slow_sim = _make_kernel()
        slow_tuning = slow_sim.get_missile_tuning()
        slow_tuning.nav_gain = 10.0
        slow_tuning.max_lateral_g = 28.0
        slow_tuning.max_accel_response_g_per_s = 400.0
        slow_tuning.autopilot_tau_s = 0.75
        slow_sim.set_missile_tuning(slow_tuning)

        _, fast_red, fast_id = _spawn_and_fire(fast_sim, range_m=4000.0, bearing_deg=88.0)
        _, slow_red, slow_id = _spawn_and_fire(slow_sim, range_m=4000.0, bearing_deg=88.0)

        fast_achieved = 0.0
        slow_achieved = 0.0
        for step_idx in range(8):
            t_fast = step_idx * fast_sim.get_time_step()
            t_slow = step_idx * slow_sim.get_time_step()
            _set_contacts(
                fast_sim,
                fast_id,
                [_make_detection(fast_red, range_m=4000.0, bearing_deg=88.0, timestamp=t_fast)],
            )
            _set_contacts(
                slow_sim,
                slow_id,
                [_make_detection(slow_red, range_m=4000.0, bearing_deg=88.0, timestamp=t_slow)],
            )
            fast_sim.step()
            slow_sim.step()
            if step_idx == 5:
                fast_achieved = float(_missile_runtime(fast_sim, fast_id)["achieved_lateral_accel_mps2"])
                slow_achieved = float(_missile_runtime(slow_sim, slow_id)["achieved_lateral_accel_mps2"])

        self.assertGreater(fast_achieved, slow_achieved + 80.0)

    def test_shared_max_lateral_g_changes_guidance_cap(self) -> None:
        low_sim = _make_kernel()
        low_tuning = low_sim.get_missile_tuning()
        low_tuning.nav_gain = 10.0
        low_tuning.max_lateral_g = 8.0
        low_tuning.autopilot_tau_s = 0.03
        low_tuning.max_accel_response_g_per_s = 400.0
        low_sim.set_missile_tuning(low_tuning)

        high_sim = _make_kernel()
        high_tuning = high_sim.get_missile_tuning()
        high_tuning.nav_gain = 10.0
        high_tuning.max_lateral_g = 26.0
        high_tuning.autopilot_tau_s = 0.03
        high_tuning.max_accel_response_g_per_s = 400.0
        high_sim.set_missile_tuning(high_tuning)

        _, low_red, low_id = _spawn_and_fire(low_sim, range_m=4000.0, bearing_deg=88.0)
        _, high_red, high_id = _spawn_and_fire(high_sim, range_m=4000.0, bearing_deg=88.0)

        low_peak_g = 0.0
        high_peak_g = 0.0
        for step_idx in range(100):
            t_low = step_idx * low_sim.get_time_step()
            t_high = step_idx * high_sim.get_time_step()
            _set_contacts(
                low_sim,
                low_id,
                [_make_detection(low_red, range_m=4000.0, bearing_deg=88.0, timestamp=t_low)],
            )
            _set_contacts(
                high_sim,
                high_id,
                [_make_detection(high_red, range_m=4000.0, bearing_deg=88.0, timestamp=t_high)],
            )
            low_sim.step()
            high_sim.step()
            low_peak_g = max(
                low_peak_g,
                float(_missile_runtime(low_sim, low_id)["achieved_lateral_accel_mps2"]) / 9.80665,
            )
            high_peak_g = max(
                high_peak_g,
                float(_missile_runtime(high_sim, high_id)["achieved_lateral_accel_mps2"]) / 9.80665,
            )

        self.assertLess(low_peak_g, 9.5)
        self.assertGreater(high_peak_g, low_peak_g + 12.0)

    def test_bounded_lateral_accel_and_response_lag(self) -> None:
        sim = _make_kernel()
        blue_id, red_id = _spawn_pair(sim)
        _set_contacts(sim, blue_id, [_make_detection(red_id, range_m=25000.0, bearing_deg=85.0)])

        missile_id = int(sim.fire_missile(blue_id, red_id))
        self.assertGreater(missile_id, 0)

        dt = sim.get_time_step()
        headings: list[float] = []
        speeds: list[float] = []
        for step_idx in range(120):
            bearing = 85.0 if step_idx < 80 else -70.0
            _set_contacts(
                sim,
                missile_id,
                [_make_detection(red_id, range_m=25000.0, bearing_deg=bearing, timestamp=step_idx * dt)],
            )
            sim.step()
            if not sim.is_unit_active(missile_id):
                break
            headings.append(_heading_from_velocity(sim, missile_id))
            speeds.append(_velocity_speed(sim, missile_id))

        self.assertGreater(len(headings), 30)
        first_delta = abs(headings[1] - headings[0])
        if first_delta > 180.0:
            first_delta = 360.0 - first_delta
        self.assertLess(first_delta, 3.0)

        max_lateral_g_est = 0.0
        for idx in range(1, len(headings)):
            delta = abs(headings[idx] - headings[idx - 1])
            if delta > 180.0:
                delta = 360.0 - delta
            yaw_rate = math.radians(delta) / dt
            lat_accel = speeds[idx] * yaw_rate
            max_lateral_g_est = max(max_lateral_g_est, lat_accel / 9.80665)

        self.assertLess(max_lateral_g_est, 45.0)

    def test_large_turn_costs_speed(self) -> None:
        sim = _make_kernel()
        blue_id, red_id = _spawn_pair(sim)
        sim.set_unit_ammo(blue_id, 4, 4)

        _set_contacts(sim, blue_id, [_make_detection(red_id, range_m=30000.0, bearing_deg=0.0)])
        straight_id = int(sim.fire_missile(blue_id, red_id))
        self.assertGreater(straight_id, 0)

        turning_bearing_deg = 85.0
        _set_contacts(sim, blue_id, [_make_detection(red_id, range_m=30000.0, bearing_deg=turning_bearing_deg)])
        turning_id = int(sim.fire_missile(blue_id, red_id))
        self.assertGreater(turning_id, 0)

        time_s = 0.0
        for _ in range(240):
            _set_contacts(
                sim,
                straight_id,
                [_make_detection(red_id, range_m=max(5000.0, 30000.0 - 350.0 * time_s), bearing_deg=0.0, timestamp=time_s)],
            )
            _set_contacts(
                sim,
                turning_id,
                [_make_detection(red_id, range_m=max(5000.0, 30000.0 - 350.0 * time_s), bearing_deg=turning_bearing_deg, timestamp=time_s)],
            )
            sim.step()
            time_s += sim.get_time_step()
            if not sim.is_unit_active(straight_id) or not sim.is_unit_active(turning_id):
                break

        straight_speed = _velocity_speed(sim, straight_id)
        turning_speed = _velocity_speed(sim, turning_id)
        self.assertGreater(straight_speed, turning_speed + 15.0)

    def test_track_memory_timeout(self) -> None:
        sim = _make_kernel()
        blue_id, red_id = _spawn_pair(sim)
        _set_contacts(sim, blue_id, [_make_detection(red_id, range_m=30000.0, bearing_deg=0.0)])

        missile_id = int(sim.fire_missile(blue_id, red_id))
        self.assertGreater(missile_id, 0)

        dt = sim.get_time_step()
        headings: list[float] = []
        time_s = 0.0
        for step_idx in range(170):
            if step_idx < 30:
                bearing = 5.0 + 0.7 * step_idx
                contacts = [_make_detection(red_id, range_m=22000.0, bearing_deg=bearing, timestamp=time_s)]
            else:
                contacts = []
            _set_contacts(sim, missile_id, contacts)
            sim.step()
            time_s += dt
            if not sim.is_unit_active(missile_id):
                break
            headings.append(_heading_from_velocity(sim, missile_id))

        self.assertGreater(len(headings), 120)

        early_memory_delta = abs(headings[55] - headings[30])
        if early_memory_delta > 180.0:
            early_memory_delta = 360.0 - early_memory_delta

        late_delta = abs(headings[150] - headings[120])
        if late_delta > 180.0:
            late_delta = 360.0 - late_delta

        self.assertGreater(early_memory_delta, 2.0)
        self.assertLess(late_delta, early_memory_delta * 0.5)


if __name__ == "__main__":
    unittest.main()
