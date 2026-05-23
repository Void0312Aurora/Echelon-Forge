from __future__ import annotations

import math
from typing import Any

import ef_py
import numpy as np

from python.scenario_compiler import (
    CompiledScenario,
    CompiledWorldLayoutTemplate,
    DEFAULT_TERRAIN_TYPE,
    _clone_runtime_mission_command,
    materialize_runtime_waypoint_cache,
    resolve_environment_terrain_config,
)

from .geometry import _primary_runway_heading_deg, apply_world_yaw_inplace, rotate_xy_clockwise
from .models import (
    AppliedScenarioWorld,
    ScenarioSpawnLayout,
    ScenarioWorldLayout,
    ScenarioZoneLayout,
    _SIDE_MAP,
    _SURFACE_TYPE_MAP,
)
from .randomization import (
    _apply_spawn_randomization,
    _normalize_spawn_ammo_override,
    _normalize_spawn_weapon_cooldown_override,
    _sample_entity_spawn,
)
from .roster import _attach_active_roster_to_applied_world


def prepare_scenario_world_layout(
    scenario_data: dict[str, Any],
    *,
    seed: int,
    rng: np.random.RandomState,
    randomization_overrides: dict[str, Any] | None = None,
    compiled_template: CompiledWorldLayoutTemplate | None = None,
) -> ScenarioWorldLayout:
    rotate_mission_heading_with_world = False
    world_yaw_deg = 0.0
    world_yaw_origin_x = 0.0
    world_yaw_origin_y = 0.0
    time_step_s: float | None = None
    terrain_type = DEFAULT_TERRAIN_TYPE
    terrain_type_source = "default_mainline"
    wind_speed = 10.0
    wind_dir_from = 270.0
    wind_shear = 4.0
    maritime_configured = False
    sea_state = 0.0
    wave_heading_deg = 0.0
    wave_period_s = 8.0
    zones: list[ScenarioZoneLayout] = []
    spawns: list[ScenarioSpawnLayout] = []

    env_cfg = scenario_data.get("environment", {})
    if not isinstance(env_cfg, dict):
        env_cfg = {}

    if compiled_template is not None:
        env_rand = dict(compiled_template.env_randomization)
        time_step_s = compiled_template.time_step_s
        terrain_type = str(compiled_template.terrain_type)
        terrain_type_source = str(compiled_template.terrain_type_source)
        wind_speed = float(compiled_template.wind_speed_mps)
        wind_dir_from = float(compiled_template.wind_dir_from_deg)
        wind_shear = float(compiled_template.wind_shear_mps_per_km)
        maritime_configured = bool(compiled_template.maritime_configured)
        sea_state = float(compiled_template.sea_state)
        wave_heading_deg = float(compiled_template.wave_heading_deg)
        wave_period_s = float(compiled_template.wave_period_s)
        runway_heading_deg_template = compiled_template.primary_runway_heading_deg
        compiled_wind_ref_alt_m = float(compiled_template.wind_ref_alt_m)
    else:
        env_rand = env_cfg.get("randomization", {}) if isinstance(env_cfg.get("randomization", {}), dict) else {}
        if "time_step" in env_cfg:
            time_step_s = float(env_cfg["time_step"])
        terrain_type, terrain_type_source = resolve_environment_terrain_config(
            env_cfg,
            default=DEFAULT_TERRAIN_TYPE,
        )
        wind_cfg = env_cfg.get("wind", {}) if isinstance(env_cfg.get("wind", {}), dict) else {}
        wind_speed = float(wind_cfg.get("speed_mps", 10.0))
        wind_dir_from = float(wind_cfg.get("dir_from_deg", 270.0))
        wind_shear = float(wind_cfg.get("shear_mps_per_km", 4.0))
        maritime_configured = isinstance(env_cfg.get("maritime", None), dict)
        maritime_cfg = env_cfg.get("maritime", {}) if maritime_configured else {}
        sea_state = float(maritime_cfg.get("sea_state", 0.0))
        wave_heading_deg = float(maritime_cfg.get("wave_heading_deg", 0.0))
        wave_period_s = float(maritime_cfg.get("wave_period_s", 8.0))
        runway_heading_deg_template = None
        compiled_wind_ref_alt_m = None

    if isinstance(randomization_overrides, dict) and randomization_overrides:
        env_rand = dict(env_rand)
        env_rand.update(randomization_overrides)

    rotate_mission_heading_with_world = bool(env_rand.get("rotate_mission_heading_with_world", False))
    if "world_yaw_range" in env_rand:
        yaw_range = env_rand["world_yaw_range"]
        world_yaw_deg = float(rng.uniform(yaw_range[0], yaw_range[1]))
        origin = env_rand.get("world_yaw_origin", [0.0, 0.0])
        try:
            world_yaw_origin_x = float(origin[0])
            world_yaw_origin_y = float(origin[1])
        except Exception:
            world_yaw_origin_x = 0.0
            world_yaw_origin_y = 0.0
        apply_world_yaw_inplace(
            scenario_data,
            world_yaw_deg,
            world_yaw_origin_x,
            world_yaw_origin_y,
        )

    used_runway_relative_wind = False
    if "wind_headwind_range" in env_rand or "wind_crosswind_range" in env_rand:
        headwind_range = env_rand.get("wind_headwind_range", [0.0, 0.0])
        crosswind_range = env_rand.get("wind_crosswind_range", [0.0, 0.0])
        try:
            headwind = float(rng.uniform(float(headwind_range[0]), float(headwind_range[1])))
        except Exception:
            headwind = 0.0
        try:
            crosswind = float(rng.uniform(float(crosswind_range[0]), float(crosswind_range[1])))
        except Exception:
            crosswind = 0.0
        tailwind_limit = env_rand.get("wind_tailwind_max_mps", env_rand.get("wind_tailwind_max", None))
        if tailwind_limit is not None:
            try:
                headwind = max(headwind, -abs(float(tailwind_limit)))
            except Exception:
                pass
        runway_heading_deg = runway_heading_deg_template
        if runway_heading_deg is None:
            runway_heading_deg = _primary_runway_heading_deg(env_cfg)
        if runway_heading_deg is not None and abs(float(world_yaw_deg)) > 1.0e-9:
            runway_heading_deg = (float(runway_heading_deg) + float(world_yaw_deg)) % 360.0
        if runway_heading_deg is not None:
            heading_rad = math.radians(float(runway_heading_deg))
            fwd_x = math.sin(heading_rad)
            fwd_y = math.cos(heading_rad)
            right_x = math.cos(heading_rad)
            right_y = -math.sin(heading_rad)
            wx = headwind * fwd_x + crosswind * right_x
            wy = headwind * fwd_y + crosswind * right_y
            wind_speed = float(math.sqrt(wx * wx + wy * wy))
            wind_dir_from = float((math.degrees(math.atan2(wx, wy)) + 360.0) % 360.0)
            used_runway_relative_wind = True

    if not used_runway_relative_wind:
        if "wind_speed_range" in env_rand:
            speed_range = env_rand["wind_speed_range"]
            wind_speed = float(rng.uniform(speed_range[0], speed_range[1]))
        if "wind_dir_from_range" in env_rand:
            dir_range = env_rand["wind_dir_from_range"]
            wind_dir_from = float(rng.uniform(dir_range[0], dir_range[1]))
    if "wind_shear_range" in env_rand:
        shear_range = env_rand["wind_shear_range"]
        wind_shear = float(rng.uniform(shear_range[0], shear_range[1]))

    mission_cmd = scenario_data.get("mission_command", None)
    if isinstance(mission_cmd, dict) and (
        abs(float(world_yaw_deg)) > 1.0e-9 or not isinstance(mission_cmd.get("_normalized_waypoints"), list)
    ):
        materialize_runtime_waypoint_cache(mission_cmd)

    if abs(float(wind_shear)) > 1.0e-9:
        wind_ref_alt_m = env_rand.get("wind_ref_alt_m", compiled_wind_ref_alt_m)
        if wind_ref_alt_m is None and compiled_template is None:
            try:
                for ent in scenario_data.get("entities", []):
                    if isinstance(ent, dict) and bool(ent.get("is_agent", False)):
                        pos = ent.get("pos", None)
                        if isinstance(pos, list) and len(pos) >= 3:
                            wind_ref_alt_m = float(pos[2])
                            break
            except Exception:
                wind_ref_alt_m = None
        if wind_ref_alt_m is None and compiled_template is None:
            try:
                entities = scenario_data.get("entities", [])
                if isinstance(entities, list) and entities:
                    pos = entities[0].get("pos", None) if isinstance(entities[0], dict) else None
                    if isinstance(pos, list) and len(pos) >= 3:
                        wind_ref_alt_m = float(pos[2])
            except Exception:
                wind_ref_alt_m = None
        if wind_ref_alt_m is None:
            wind_ref_alt_m = 0.0
        wind_speed = max(0.0, float(wind_speed) - float(wind_shear) * (max(0.0, float(wind_ref_alt_m)) / 1000.0))

    if compiled_template is not None:
        yaw_active = abs(float(world_yaw_deg)) > 1.0e-9
        origin_x = float(world_yaw_origin_x)
        origin_y = float(world_yaw_origin_y)
        yaw_deg = float(world_yaw_deg)
        for template in compiled_template.zones:
            x = template.x
            y = template.y
            heading = template.heading
            if yaw_active:
                x, y = rotate_xy_clockwise(x, y, origin_x, origin_y, yaw_deg)
                heading = (heading + yaw_deg) % 360.0
            zones.append(
                ScenarioZoneLayout(
                    name=template.name,
                    x=x,
                    y=y,
                    width=template.width,
                    length=template.length,
                    heading=heading,
                    surface_type=template.surface_type,
                )
            )
        for template in compiled_template.spawns:
            pos = [template.x, template.y, template.z]
            vel = [template.vx, template.vy, template.vz]
            heading = template.heading
            pitch = template.pitch
            roll = template.roll
            if yaw_active:
                pos[0], pos[1] = rotate_xy_clockwise(pos[0], pos[1], origin_x, origin_y, yaw_deg)
                vel[0], vel[1] = rotate_xy_clockwise(vel[0], vel[1], 0.0, 0.0, yaw_deg)
                heading = (heading + yaw_deg) % 360.0
            pos, vel, heading, pitch, roll = _apply_spawn_randomization(
                rng,
                pos,
                vel,
                heading,
                pitch,
                roll,
                template.randomization,
            )
            spawns.append(
                ScenarioSpawnLayout(
                    entity_name=template.entity_name,
                    side=_SIDE_MAP.get(template.side_name, ef_py.Side.Neutral),
                    type_name=template.type_name,
                    is_agent=template.is_agent,
                    x=pos[0],
                    y=pos[1],
                    z=pos[2],
                    heading=heading,
                    pitch=pitch,
                    roll=roll,
                    vx=vel[0],
                    vy=vel[1],
                    vz=vel[2],
                    ammo_override_enabled=bool(template.ammo_override_enabled),
                    missiles_remaining=int(template.missiles_remaining),
                    max_missiles=int(template.max_missiles),
                    weapon_cooldown_override_enabled=bool(template.weapon_cooldown_override_enabled),
                    weapon_cooldown_s=float(template.weapon_cooldown_s),
                    weapon_last_fire_time=float(template.weapon_last_fire_time),
                )
            )
    else:
        zone_defs = env_cfg.get("zones", [])
        if isinstance(zone_defs, list):
            for zone in zone_defs:
                if not isinstance(zone, dict):
                    continue
                zones.append(
                    ScenarioZoneLayout(
                        name=str(zone.get("name", "Zone")),
                        x=float(zone.get("x", 0.0)),
                        y=float(zone.get("y", 0.0)),
                        width=float(zone.get("width", 1000.0)),
                        length=float(zone.get("length", 1000.0)),
                        heading=float(zone.get("heading", 0.0)),
                        surface_type=int(_SURFACE_TYPE_MAP.get(zone.get("surface", "SoftDirt"), 3)),
                    )
                )

        entities = scenario_data.get("entities", [])
        if isinstance(entities, list):
            for ent_cfg in entities:
                if not isinstance(ent_cfg, dict):
                    continue
                pos, vel, heading, pitch, roll = _sample_entity_spawn(rng, ent_cfg)
                ammo_override_enabled, missiles_remaining, max_missiles = _normalize_spawn_ammo_override(ent_cfg)
                (
                    weapon_cooldown_override_enabled,
                    weapon_cooldown_s,
                    weapon_last_fire_time,
                ) = _normalize_spawn_weapon_cooldown_override(ent_cfg)
                spawns.append(
                    ScenarioSpawnLayout(
                        entity_name=str(ent_cfg.get("name", "")),
                        side=_SIDE_MAP.get(str(ent_cfg.get("side", "Neutral")), ef_py.Side.Neutral),
                        type_name=str(ent_cfg.get("type", "")),
                        is_agent=bool(ent_cfg.get("is_agent", False)),
                        x=float(pos[0]),
                        y=float(pos[1]),
                        z=float(pos[2]),
                        heading=float(heading),
                        pitch=float(pitch),
                        roll=float(roll),
                        vx=float(vel[0]),
                        vy=float(vel[1]),
                        vz=float(vel[2]),
                        ammo_override_enabled=bool(ammo_override_enabled),
                        missiles_remaining=int(missiles_remaining),
                        max_missiles=int(max_missiles),
                        weapon_cooldown_override_enabled=bool(weapon_cooldown_override_enabled),
                        weapon_cooldown_s=float(weapon_cooldown_s),
                        weapon_last_fire_time=float(weapon_last_fire_time),
                    )
                )

    return ScenarioWorldLayout(
        scenario_data=scenario_data,
        seed=int(seed) & 0xFFFFFFFF,
        rotate_mission_heading_with_world=rotate_mission_heading_with_world,
        world_yaw_deg=float(world_yaw_deg),
        world_yaw_origin_x=float(world_yaw_origin_x),
        world_yaw_origin_y=float(world_yaw_origin_y),
        time_step_s=time_step_s,
        terrain_type=terrain_type,
        terrain_type_source=terrain_type_source,
        wind_speed_mps=float(wind_speed),
        wind_dir_from_deg=float(wind_dir_from),
        wind_shear_mps_per_km=float(wind_shear),
        maritime_configured=bool(maritime_configured),
        sea_state=float(sea_state),
        wave_heading_deg=float(wave_heading_deg),
        wave_period_s=float(wave_period_s),
        zones=zones,
        spawns=spawns,
    )


def apply_world_layout_to_kernel(sim, layout: ScenarioWorldLayout) -> AppliedScenarioWorld:
    if layout.time_step_s is not None:
        sim.set_time_step(layout.time_step_s)
    if hasattr(sim, "set_terrain_type"):
        try:
            sim.set_terrain_type(layout.terrain_type)
        except Exception:
            pass
    if hasattr(sim, "set_wind"):
        try:
            sim.set_wind(
                layout.wind_speed_mps,
                layout.wind_dir_from_deg,
                layout.wind_shear_mps_per_km,
            )
        except Exception:
            pass
    if layout.maritime_configured and hasattr(sim, "set_maritime_state"):
        try:
            sim.set_maritime_state(
                layout.sea_state,
                layout.wave_heading_deg,
                layout.wave_period_s,
            )
        except Exception:
            pass
    elif hasattr(sim, "clear_maritime_state"):
        try:
            sim.clear_maritime_state()
        except Exception:
            pass
    if hasattr(sim, "clear_zones"):
        sim.clear_zones()
        for zone in layout.zones:
            sim.add_zone(
                zone.name,
                zone.x,
                zone.y,
                zone.width,
                zone.length,
                zone.heading,
                zone.surface_type,
            )

    sim.reset(layout.seed)

    entities: dict[str, int] = {}
    agent_id: int | None = None
    for spawn in layout.spawns:
        entity_id = int(
            sim.spawn_unit(
                spawn.side,
                spawn.type_name,
                spawn.x,
                spawn.y,
                spawn.z,
                spawn.heading,
                spawn.pitch,
                spawn.roll,
                spawn.vx,
                spawn.vy,
                spawn.vz,
            )
        )
        if bool(spawn.ammo_override_enabled) and hasattr(sim, "set_unit_ammo"):
            sim.set_unit_ammo(
                int(entity_id),
                int(spawn.missiles_remaining),
                int(spawn.max_missiles),
            )
        if bool(spawn.weapon_cooldown_override_enabled) and hasattr(sim, "set_weapon_cooldown"):
            sim.set_weapon_cooldown(
                int(entity_id),
                float(spawn.weapon_cooldown_s),
                float(spawn.weapon_last_fire_time),
            )
        entities[spawn.entity_name] = entity_id
        if spawn.is_agent and agent_id is None:
            agent_id = entity_id
    return _attach_active_roster_to_applied_world(
        AppliedScenarioWorld(layout=layout, entities=entities, agent_id=agent_id),
        world_index=None,
    )


def build_compiled_world_layout(
    compiled_scenario: CompiledScenario,
    *,
    seed: int,
    randomization_overrides: dict[str, Any] | None = None,
    use_compiled_template: bool = False,
) -> ScenarioWorldLayout:
    scenario_data = compiled_scenario.instantiate_runtime()
    runtime_metadata = getattr(compiled_scenario, "runtime_metadata", None)
    compiled_template = None
    if runtime_metadata is not None:
        scenario_data["mission_command"] = _clone_runtime_mission_command(runtime_metadata.mission_command_template)
        if bool(use_compiled_template):
            compiled_template = runtime_metadata.layout_template
    rng = np.random.RandomState(int(seed) & 0xFFFFFFFF)
    return prepare_scenario_world_layout(
        scenario_data,
        seed=int(seed),
        rng=rng,
        randomization_overrides=randomization_overrides,
        compiled_template=compiled_template,
    )


__all__ = [
    "apply_world_layout_to_kernel",
    "build_compiled_world_layout",
    "prepare_scenario_world_layout",
]
