from __future__ import annotations

import json
import math
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
                },
                {
                    "name": "right_aileron_actuator",
                    "system": "flight_control",
                    "offset": [-0.8, 2.8, 0.0],
                    "size": [1.0, 1.1, 0.22],
                    "armor": 3.0,
                    "threshold_scale": 1.35,
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
                component["critical"] = bool(critical)
                component["threshold_scale"] = 1.35
    return unit


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
    sim = ef_py.SimulationKernel()
    sim.reset(20260526)
    if not sim.load_database(_DB_PATH):
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
    return _aircraft_damage_overlay(sim, target_id)


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
        self.assertGreater(float(effects.detonation_time_s), float(effects.nearest_approach_time_s))
        self.assertAlmostEqual(
            float(effects.detonation_time_s) - float(effects.nearest_approach_time_s),
            0.08,
            delta=sim.get_time_step() + 1.0e-6,
        )

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
                    240.0,
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
                    240.0,
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
        self.assertTrue(bool(fuel_event.component_primary_critical))
        self.assertLess(fuel_overlay["fuel"], 1.0)
        self.assertGreater(fuel_overlay["fuel_leak"], 0.0)
        self.assertAlmostEqual(fuel_overlay["flight_control"], 1.0, delta=1.0e-6)

        self.assertTrue(bool(control_event.direct_hitbox_intersection))
        self.assertEqual(int(control_event.component_hit_count), 1)
        self.assertEqual(str(control_event.component_primary_name), "right_aileron_actuator")
        self.assertEqual(str(control_event.component_primary_system), "flight_control")
        self.assertAlmostEqual(float(control_event.component_primary_redundancy_group), 2.0, delta=1.0e-6)
        self.assertFalse(bool(control_event.component_primary_critical))
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
        self.assertTrue(bool(fuel_event.component_primary_critical))
        self.assertLess(fuel_overlay["fuel"], 1.0)
        self.assertGreater(fuel_overlay["fuel_leak"], 0.0)
        self.assertAlmostEqual(fuel_overlay["flight_control"], 1.0, delta=1.0e-6)

        self.assertTrue(bool(control_event.direct_hitbox_intersection))
        self.assertEqual(int(control_event.component_hit_count), 1)
        self.assertEqual(str(control_event.component_primary_name), "right_elevon_actuator")
        self.assertEqual(str(control_event.component_primary_system), "flight_control")
        self.assertAlmostEqual(float(control_event.component_primary_redundancy_group), 2.0, delta=1.0e-6)
        self.assertFalse(bool(control_event.component_primary_critical))
        self.assertLess(control_overlay["flight_control"], 1.0)
        self.assertLess(control_overlay["hydraulic"], 1.0)
        self.assertAlmostEqual(control_overlay["fuel"], 1.0, delta=1.0e-6)

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

    def test_phase5_aircraft_vulnerability_profile_modulates_structured_damage(self) -> None:
        beam_high_closure = _profiled_local_hit_overlay_with_velocity(
            "continuous_rod",
            (-0.753, 4.0, 0.0),
            (0.0, -900.0, 0.0),
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
            (0.0, -900.0, 0.0),
            damage=90.0,
            radius=35.0,
        )
        near_wing = _profiled_local_hit_overlay_with_velocity(
            "continuous_rod",
            (-0.753, 7.1, 0.0),
            (0.0, -900.0, 0.0),
            damage=90.0,
            radius=35.0,
        )

        self.assertLess(beam_high_closure["flight_control"], tail_low_closure["flight_control"])
        self.assertLess(beam_high_closure["hydraulic"], tail_low_closure["hydraulic"])
        self.assertLess(direct_wing["flight_control"], near_wing["flight_control"])
        self.assertLess(direct_wing["structure"], near_wing["structure"])

    def test_phase5_synthetic_vulnerability_profile_is_not_pk_or_fuze_authority(self) -> None:
        sim = ef_py.SimulationKernel()
        sim.reset(20260526)
        self.assertTrue(sim.load_database(_DB_PATH))
        _attacker_id, target_id = _spawn_structured_f16_pair(sim)

        evidence = [
            float(value)
            for value in sim.debug_get_aircraft_vulnerability_evidence_state(target_id)
        ]
        self.assertEqual(evidence, [1.0, 1.0, 0.0, 0.0, 0.0])

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
