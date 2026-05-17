from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from .clone import _clone_scenario_value
from .common import _coerce_nonnegative_int, _SURFACE_TYPE_MAP


def _extract_ils_beacons(env_cfg: dict[str, Any] | None) -> list[dict[str, Any]]:
    env_cfg = env_cfg if isinstance(env_cfg, dict) else {}
    beacons: list[dict[str, Any]] = []
    zones = env_cfg.get("zones", [])
    if not isinstance(zones, list):
        return beacons
    for idx, zone in enumerate(zones):
        if not isinstance(zone, dict):
            continue
        name = str(zone.get("name", ""))
        surface = str(zone.get("surface", ""))
        ils_cfg = zone.get("ils", {})
        if not isinstance(ils_cfg, dict):
            ils_cfg = {}
        enabled = bool(ils_cfg.get("enabled", False))
        if not enabled:
            if ("runway" in name.lower()) and surface in ("Concrete", "Asphalt"):
                enabled = True
            else:
                continue
        try:
            cx = float(zone.get("x", 0.0))
            cy = float(zone.get("y", 0.0))
            width = float(zone.get("width", 0.0))
            length = float(zone.get("length", 0.0))
            heading = float(zone.get("heading", 0.0)) % 360.0
        except Exception:
            continue
        if length <= 1.0:
            continue
        if width <= 1.0:
            width = float(ils_cfg.get("width_m", 60.0))
        glide_slope_deg = float(ils_cfg.get("glide_slope_deg", 3.0))
        loc_max_deg = float(ils_cfg.get("loc_max_deg", 2.5))
        gs_max_deg = float(ils_cfg.get("gs_max_deg", 0.7))
        range_m = float(ils_cfg.get("range_m", 25000.0))
        elev_m = float(ils_cfg.get("elev_m", 0.0))
        h_rad = math.radians(heading)
        fwd_x = math.sin(h_rad)
        fwd_y = math.cos(h_rad)
        thr_x = cx - fwd_x * (length * 0.5)
        thr_y = cy - fwd_y * (length * 0.5)
        beacons.append(
            {
                "runway_id": int(zone.get("runway_id", idx)),
                "name": name,
                "cx": cx,
                "cy": cy,
                "thr_x": thr_x,
                "thr_y": thr_y,
                "heading": heading,
                "length": length,
                "width": width,
                "elev_m": elev_m,
                "glide_slope_deg": glide_slope_deg,
                "loc_max_deg": max(0.1, loc_max_deg),
                "gs_max_deg": max(0.1, gs_max_deg),
                "range_m": max(100.0, range_m),
            }
        )
    return beacons


def rotate_ils_beacon_templates(
    templates: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None,
    *,
    yaw_deg: float,
    origin_x: float = 0.0,
    origin_y: float = 0.0,
) -> list[dict[str, Any]]:
    if not templates:
        return []

    rad = -math.radians(float(yaw_deg))
    c = math.cos(rad)
    s = math.sin(rad)

    def _rot(x: float, y: float) -> tuple[float, float]:
        dx = float(x) - float(origin_x)
        dy = float(y) - float(origin_y)
        rx = float(origin_x) + c * dx - s * dy
        ry = float(origin_y) + s * dx + c * dy
        return rx, ry

    rotated = []
    for beacon in templates:
        if not isinstance(beacon, dict):
            continue
        item = dict(beacon)
        item["cx"], item["cy"] = _rot(float(beacon.get("cx", 0.0)), float(beacon.get("cy", 0.0)))
        item["thr_x"], item["thr_y"] = _rot(float(beacon.get("thr_x", 0.0)), float(beacon.get("thr_y", 0.0)))
        item["heading"] = (float(beacon.get("heading", 0.0)) + float(yaw_deg)) % 360.0
        rotated.append(item)
    return rotated


def _primary_runway_heading_deg(env_cfg: dict[str, Any] | None) -> float | None:
    env_cfg = env_cfg if isinstance(env_cfg, dict) else {}
    zones = env_cfg.get("zones", [])
    if not isinstance(zones, list):
        return None
    best_heading = None
    best_priority = -1
    for zone in zones:
        if not isinstance(zone, dict):
            continue
        name = str(zone.get("name", "")).lower()
        surface = str(zone.get("surface", ""))
        ils_cfg = zone.get("ils", {})
        if not isinstance(ils_cfg, dict):
            ils_cfg = {}
        ils_enabled = bool(ils_cfg.get("enabled", False))
        is_runway = "runway" in name
        priority = 0
        if ils_enabled and is_runway:
            priority = 3
        elif ils_enabled:
            priority = 2
        elif is_runway and surface in ("Concrete", "Asphalt"):
            priority = 1
        if priority <= best_priority:
            continue
        try:
            best_heading = float(zone.get("heading", 0.0)) % 360.0
        except Exception:
            continue
        best_priority = priority
    return best_heading


def _infer_wind_ref_alt_m(merged_scenario_data: dict[str, Any]) -> float:
    try:
        for ent in merged_scenario_data.get("entities", []):
            if isinstance(ent, dict) and bool(ent.get("is_agent", False)):
                pos = ent.get("pos", None)
                if isinstance(pos, list) and len(pos) >= 3:
                    return float(pos[2])
    except Exception:
        return 0.0
    try:
        entities = merged_scenario_data.get("entities", [])
        if isinstance(entities, list) and entities:
            pos = entities[0].get("pos", None) if isinstance(entities[0], dict) else None
            if isinstance(pos, list) and len(pos) >= 3:
                return float(pos[2])
    except Exception:
        return 0.0
    return 0.0


@dataclass(frozen=True)
class CompiledZoneLayoutTemplate:
    name: str
    x: float
    y: float
    width: float
    length: float
    heading: float
    surface_type: int


@dataclass(frozen=True)
class CompiledSpawnLayoutTemplate:
    entity_name: str
    side_name: str
    type_name: str
    is_agent: bool
    x: float
    y: float
    z: float
    heading: float
    pitch: float
    roll: float
    vx: float
    vy: float
    vz: float
    randomization: dict[str, Any]
    ammo_override_enabled: bool
    missiles_remaining: int
    max_missiles: int
    weapon_cooldown_override_enabled: bool
    weapon_cooldown_s: float
    weapon_last_fire_time: float


@dataclass(frozen=True)
class CompiledWorldLayoutTemplate:
    time_step_s: float | None
    terrain_type: str
    wind_speed_mps: float
    wind_dir_from_deg: float
    wind_shear_mps_per_km: float
    maritime_configured: bool
    sea_state: float
    wave_heading_deg: float
    wave_period_s: float
    env_randomization: dict[str, Any]
    primary_runway_heading_deg: float | None
    wind_ref_alt_m: float
    zones: tuple[CompiledZoneLayoutTemplate, ...]
    spawns: tuple[CompiledSpawnLayoutTemplate, ...]


def _compile_world_layout_template(merged_scenario_data: dict[str, Any]) -> CompiledWorldLayoutTemplate:
    env_cfg = merged_scenario_data.get("environment", {})
    if not isinstance(env_cfg, dict):
        env_cfg = {}
    wind_cfg = env_cfg.get("wind", {})
    if not isinstance(wind_cfg, dict):
        wind_cfg = {}
    maritime_cfg = env_cfg.get("maritime", {})
    if not isinstance(maritime_cfg, dict):
        maritime_cfg = {}

    zones_out: list[CompiledZoneLayoutTemplate] = []
    zone_defs = env_cfg.get("zones", [])
    if isinstance(zone_defs, list):
        for zone in zone_defs:
            if not isinstance(zone, dict):
                continue
            zones_out.append(
                CompiledZoneLayoutTemplate(
                    name=str(zone.get("name", "Zone")),
                    x=float(zone.get("x", 0.0)),
                    y=float(zone.get("y", 0.0)),
                    width=float(zone.get("width", 1000.0)),
                    length=float(zone.get("length", 1000.0)),
                    heading=float(zone.get("heading", 0.0)),
                    surface_type=int(_SURFACE_TYPE_MAP.get(zone.get("surface", "SoftDirt"), 3)),
                )
            )

    spawns_out: list[CompiledSpawnLayoutTemplate] = []
    entities = merged_scenario_data.get("entities", [])
    if isinstance(entities, list):
        for ent_cfg in entities:
            if not isinstance(ent_cfg, dict):
                continue
            pos = ent_cfg.get("pos", [0.0, 0.0, 0.0])
            vel = ent_cfg.get("vel", [0.0, 0.0, 0.0])
            pos_vals = list(pos) if isinstance(pos, (list, tuple)) else [0.0, 0.0, 0.0]
            vel_vals = list(vel) if isinstance(vel, (list, tuple)) else [0.0, 0.0, 0.0]
            while len(pos_vals) < 3:
                pos_vals.append(0.0)
            while len(vel_vals) < 3:
                vel_vals.append(0.0)
            rand_cfg = ent_cfg.get("randomization", {})
            if not isinstance(rand_cfg, dict):
                rand_cfg = {}
            ammo_cfg = ent_cfg.get("ammo", None)
            ammo_override_enabled = isinstance(ammo_cfg, dict)
            missiles_remaining = 0
            max_missiles = 0
            if ammo_override_enabled:
                missiles_remaining = _coerce_nonnegative_int(
                    ammo_cfg.get("missiles_remaining", ammo_cfg.get("count", 0)),
                    0,
                )
                max_missiles = _coerce_nonnegative_int(
                    ammo_cfg.get("max_missiles", ammo_cfg.get("capacity", missiles_remaining)),
                    missiles_remaining,
                )
                if max_missiles < missiles_remaining:
                    max_missiles = missiles_remaining
            cooldown_cfg = ent_cfg.get("weapon_cooldown", None)
            weapon_cooldown_override_enabled = isinstance(cooldown_cfg, dict)
            weapon_cooldown_s = 2.0
            weapon_last_fire_time = -1.0
            if weapon_cooldown_override_enabled:
                try:
                    weapon_cooldown_s = float(cooldown_cfg.get("cooldown_s", 2.0))
                except Exception:
                    weapon_cooldown_s = 2.0
                try:
                    weapon_last_fire_time = float(cooldown_cfg.get("last_fire_time", -1.0))
                except Exception:
                    weapon_last_fire_time = -1.0
            spawns_out.append(
                CompiledSpawnLayoutTemplate(
                    entity_name=str(ent_cfg.get("name", "")),
                    side_name=str(ent_cfg.get("side", "Neutral")),
                    type_name=str(ent_cfg.get("type", "")),
                    is_agent=bool(ent_cfg.get("is_agent", False)),
                    x=float(pos_vals[0]),
                    y=float(pos_vals[1]),
                    z=float(pos_vals[2]),
                    heading=float(ent_cfg.get("heading", 0.0)),
                    pitch=float(ent_cfg.get("pitch", 0.0)),
                    roll=float(ent_cfg.get("roll", 0.0)),
                    vx=float(vel_vals[0]),
                    vy=float(vel_vals[1]),
                    vz=float(vel_vals[2]),
                    randomization=_clone_scenario_value(rand_cfg),
                    ammo_override_enabled=bool(ammo_override_enabled),
                    missiles_remaining=int(missiles_remaining),
                    max_missiles=int(max_missiles),
                    weapon_cooldown_override_enabled=bool(weapon_cooldown_override_enabled),
                    weapon_cooldown_s=float(weapon_cooldown_s),
                    weapon_last_fire_time=float(weapon_last_fire_time),
                )
            )

    return CompiledWorldLayoutTemplate(
        time_step_s=float(env_cfg["time_step"]) if "time_step" in env_cfg else None,
        terrain_type=str(env_cfg.get("terrain_type", "legacy")).strip() or "legacy",
        wind_speed_mps=float(wind_cfg.get("speed_mps", 10.0)),
        wind_dir_from_deg=float(wind_cfg.get("dir_from_deg", 270.0)),
        wind_shear_mps_per_km=float(wind_cfg.get("shear_mps_per_km", 4.0)),
        maritime_configured=isinstance(env_cfg.get("maritime", None), dict),
        sea_state=float(maritime_cfg.get("sea_state", 0.0)),
        wave_heading_deg=float(maritime_cfg.get("wave_heading_deg", 0.0)),
        wave_period_s=float(maritime_cfg.get("wave_period_s", 8.0)),
        env_randomization=_clone_scenario_value(env_cfg.get("randomization", {}))
        if isinstance(env_cfg.get("randomization", {}), dict)
        else {},
        primary_runway_heading_deg=_primary_runway_heading_deg(env_cfg),
        wind_ref_alt_m=float(_infer_wind_ref_alt_m(merged_scenario_data)),
        zones=tuple(zones_out),
        spawns=tuple(spawns_out),
    )


__all__ = [
    "CompiledZoneLayoutTemplate",
    "CompiledSpawnLayoutTemplate",
    "CompiledWorldLayoutTemplate",
    "_extract_ils_beacons",
    "rotate_ils_beacon_templates",
    "_primary_runway_heading_deg",
    "_infer_wind_ref_alt_m",
    "_compile_world_layout_template",
]
