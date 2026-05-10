from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import ef_py
import numpy as np

from python.scenario_compiler import (
    CompiledScenario,
    CompiledWorldLayoutTemplate,
    _clone_runtime_mission_command,
    materialize_runtime_waypoint_cache,
)


_SURFACE_TYPE_MAP = {
    "Concrete": 0,
    "Asphalt": 1,
    "HardPacked": 2,
    "SoftDirt": 3,
    "Water": 4,
    "Obstacle": 5,
}

_SIDE_MAP = {
    "Blue": ef_py.Side.Blue,
    "Red": ef_py.Side.Red,
    "Neutral": ef_py.Side.Neutral,
}


@dataclass
class ScenarioZoneLayout:
    name: str
    x: float
    y: float
    width: float
    length: float
    heading: float
    surface_type: int


@dataclass
class ScenarioSpawnLayout:
    entity_name: str
    side: Any
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


@dataclass
class ScenarioWorldLayout:
    scenario_data: dict[str, Any]
    seed: int
    rotate_mission_heading_with_world: bool
    world_yaw_deg: float
    world_yaw_origin_x: float
    world_yaw_origin_y: float
    time_step_s: float | None
    terrain_type: str
    wind_speed_mps: float
    wind_dir_from_deg: float
    wind_shear_mps_per_km: float
    zones: list[ScenarioZoneLayout]
    spawns: list[ScenarioSpawnLayout]


@dataclass
class PreparedScenarioWorldContext:
    scenario_data: dict[str, Any]
    seed: int
    rotate_mission_heading_with_world: bool
    world_yaw_deg: float
    world_yaw_origin_x: float
    world_yaw_origin_y: float


@dataclass
class AppliedScenarioWorld:
    layout: ScenarioWorldLayout | PreparedScenarioWorldContext
    entities: dict[str, int]
    agent_id: int | None


@dataclass
class BatchWorldApplyBuffer:
    world_count: int
    terrain_assignments: list[Any] | None = None
    wind_assignments: list[Any] | None = None
    zone_defs: list[Any] | None = None
    spawn_requests: list[Any] | None = None

    def __post_init__(self) -> None:
        self.world_count = max(0, int(self.world_count))
        self.terrain_assignments = [] if self.terrain_assignments is None else list(self.terrain_assignments)
        self.wind_assignments = [] if self.wind_assignments is None else list(self.wind_assignments)
        self.zone_defs = [] if self.zone_defs is None else list(self.zone_defs)
        self.spawn_requests = [] if self.spawn_requests is None else list(self.spawn_requests)

    @staticmethod
    def _ensure_size(items: list[Any], target_size: int, factory) -> list[Any]:
        if len(items) < target_size:
            items.extend(factory() for _ in range(target_size - len(items)))
        elif len(items) > target_size:
            del items[target_size:]
        return items

    def prepare(self, layouts: list[ScenarioWorldLayout]) -> tuple[list[Any], list[Any], list[Any], list[Any]]:
        if len(layouts) != int(self.world_count):
            raise ValueError(f"expected {self.world_count} layouts, got {len(layouts)}")

        terrain_items = self._ensure_size(self.terrain_assignments, len(layouts), ef_py.WorldTerrainAssignment)
        wind_items = self._ensure_size(self.wind_assignments, len(layouts), ef_py.WorldWindAssignment)
        total_zone_count = sum(len(layout.zones) for layout in layouts)
        total_spawn_count = sum(len(layout.spawns) for layout in layouts)
        zone_items = self._ensure_size(self.zone_defs, total_zone_count, ef_py.WorldZoneDefinition)
        spawn_items = self._ensure_size(self.spawn_requests, total_spawn_count, ef_py.WorldSpawnRequest)

        zone_cursor = 0
        spawn_cursor = 0
        for world_index, layout in enumerate(layouts):
            terrain = terrain_items[world_index]
            terrain.world_index = int(world_index)
            terrain.terrain_type = str(layout.terrain_type)

            wind = wind_items[world_index]
            wind.world_index = int(world_index)
            wind.speed_mps = float(layout.wind_speed_mps)
            wind.dir_from_deg = float(layout.wind_dir_from_deg)
            wind.shear_mps_per_km = float(layout.wind_shear_mps_per_km)

            for zone in layout.zones:
                zone_def = zone_items[zone_cursor]
                zone_cursor += 1
                zone_def.world_index = int(world_index)
                zone_def.name = str(zone.name)
                zone_def.x = float(zone.x)
                zone_def.y = float(zone.y)
                zone_def.width = float(zone.width)
                zone_def.length = float(zone.length)
                zone_def.heading = float(zone.heading)
                zone_def.surface_type = int(zone.surface_type)

            for spawn in layout.spawns:
                req = spawn_items[spawn_cursor]
                spawn_cursor += 1
                req.world_index = int(world_index)
                req.side = spawn.side
                req.type_name = str(spawn.type_name)
                req.entity_name = str(spawn.entity_name)
                req.is_agent = bool(spawn.is_agent)
                req.x = float(spawn.x)
                req.y = float(spawn.y)
                req.z = float(spawn.z)
                req.heading = float(spawn.heading)
                req.pitch = float(spawn.pitch)
                req.roll = float(spawn.roll)
                req.vx = float(spawn.vx)
                req.vy = float(spawn.vy)
                req.vz = float(spawn.vz)

        return terrain_items, wind_items, zone_items, spawn_items

    def prepare_direct(self, *, total_zone_count: int, total_spawn_count: int) -> tuple[list[Any], list[Any], list[Any], list[Any]]:
        terrain_items = self._ensure_size(self.terrain_assignments, int(self.world_count), ef_py.WorldTerrainAssignment)
        wind_items = self._ensure_size(self.wind_assignments, int(self.world_count), ef_py.WorldWindAssignment)
        zone_items = self._ensure_size(self.zone_defs, int(total_zone_count), ef_py.WorldZoneDefinition)
        spawn_items = self._ensure_size(self.spawn_requests, int(total_spawn_count), ef_py.WorldSpawnRequest)
        return terrain_items, wind_items, zone_items, spawn_items


def _sample_uniform(rng: np.random.RandomState, value: Any, default: float) -> float:
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        try:
            return float(rng.uniform(float(value[0]), float(value[1])))
        except Exception:
            return float(default)
    try:
        return float(value)
    except Exception:
        return float(default)


def _apply_spawn_randomization(
    rng: np.random.RandomState,
    pos: list[float],
    vel: list[float],
    heading: float,
    pitch: float,
    roll: float,
    rand_cfg: dict[str, Any] | None,
) -> tuple[list[float], list[float], float, float, float]:
    if not isinstance(rand_cfg, dict):
        return pos, vel, float(heading), float(pitch), float(roll)

    heading += _sample_uniform(rng, rand_cfg.get("heading_offset_deg_range", [0.0, 0.0]), 0.0)
    pitch += _sample_uniform(rng, rand_cfg.get("pitch_offset_deg_range", [0.0, 0.0]), 0.0)
    roll += _sample_uniform(rng, rand_cfg.get("roll_offset_deg_range", [0.0, 0.0]), 0.0)

    h_rad = math.radians(float(heading))
    fwd_x = math.sin(h_rad)
    fwd_y = math.cos(h_rad)
    right_x = math.cos(h_rad)
    right_y = -math.sin(h_rad)

    along_off = _sample_uniform(rng, rand_cfg.get("along_body_m_range", [0.0, 0.0]), 0.0)
    cross_off = _sample_uniform(rng, rand_cfg.get("cross_body_m_range", [0.0, 0.0]), 0.0)
    alt_off = _sample_uniform(rng, rand_cfg.get("altitude_offset_m_range", [0.0, 0.0]), 0.0)

    try:
        pos[0] = float(pos[0]) + along_off * fwd_x + cross_off * right_x
        pos[1] = float(pos[1]) + along_off * fwd_y + cross_off * right_y
        pos[2] = float(pos[2]) + alt_off
    except Exception:
        pass

    try:
        base_horiz_speed = math.sqrt(float(vel[0]) * float(vel[0]) + float(vel[1]) * float(vel[1]))
    except Exception:
        base_horiz_speed = 0.0
    speed_scale = _sample_uniform(rng, rand_cfg.get("speed_scale_range", [1.0, 1.0]), 1.0)
    speed_off = _sample_uniform(rng, rand_cfg.get("speed_offset_mps_range", [0.0, 0.0]), 0.0)
    horiz_speed = max(0.0, float(base_horiz_speed) * float(speed_scale) + float(speed_off))
    sink_default = float(vel[2]) if len(vel) > 2 else 0.0
    sink_rate = _sample_uniform(
        rng,
        rand_cfg.get("sink_rate_mps_range", [sink_default, sink_default]),
        sink_default,
    )

    if len(vel) < 3:
        vel = [0.0, 0.0, 0.0]
    vel[0] = float(horiz_speed * fwd_x)
    vel[1] = float(horiz_speed * fwd_y)
    vel[2] = float(sink_rate)

    return pos, vel, float(heading), float(pitch), float(roll)


def _sample_entity_spawn(
    rng: np.random.RandomState,
    ent_cfg: dict[str, Any],
) -> tuple[list[float], list[float], float, float, float]:
    pos = list(ent_cfg.get("pos", [0.0, 0.0, 0.0]))
    vel = list(ent_cfg.get("vel", [0.0, 0.0, 0.0]))
    heading = float(ent_cfg.get("heading", 0.0))
    pitch = float(ent_cfg.get("pitch", 0.0))
    roll = float(ent_cfg.get("roll", 0.0))
    return _apply_spawn_randomization(
        rng,
        pos,
        vel,
        heading,
        pitch,
        roll,
        ent_cfg.get("randomization", None),
    )


def rotate_xy_clockwise(x: float, y: float, origin_x: float, origin_y: float, yaw_deg: float) -> tuple[float, float]:
    rad = -math.radians(float(yaw_deg))
    c = math.cos(rad)
    s = math.sin(rad)
    dx = float(x) - float(origin_x)
    dy = float(y) - float(origin_y)
    rx = float(origin_x) + c * dx - s * dy
    ry = float(origin_y) + s * dx + c * dy
    return rx, ry


def _rotate_waypoint_list_inplace(
    waypoints: list[Any] | tuple[Any, ...] | None,
    *,
    origin_x: float,
    origin_y: float,
    yaw_deg: float,
) -> None:
    if not isinstance(waypoints, (list, tuple)):
        return
    for wp in waypoints:
        if isinstance(wp, dict):
            if "pos" in wp and isinstance(wp.get("pos"), list) and len(wp["pos"]) >= 2:
                pos_x, pos_y = rotate_xy_clockwise(
                    wp["pos"][0],
                    wp["pos"][1],
                    origin_x,
                    origin_y,
                    yaw_deg,
                )
                wp["pos"][0] = pos_x
                wp["pos"][1] = pos_y
            elif "x" in wp and "y" in wp:
                pos_x, pos_y = rotate_xy_clockwise(
                    wp.get("x", 0.0),
                    wp.get("y", 0.0),
                    origin_x,
                    origin_y,
                    yaw_deg,
                )
                wp["x"] = pos_x
                wp["y"] = pos_y
        elif isinstance(wp, list) and len(wp) >= 2:
            pos_x, pos_y = rotate_xy_clockwise(wp[0], wp[1], origin_x, origin_y, yaw_deg)
            wp[0] = pos_x
            wp[1] = pos_y


def apply_runtime_world_yaw_inplace(
    scenario_data: dict[str, Any],
    yaw_deg: float,
    origin_x: float = 0.0,
    origin_y: float = 0.0,
) -> None:
    if abs(float(yaw_deg)) <= 1.0e-9:
        return

    mission_cmd = scenario_data.get("mission_command", None)
    if isinstance(mission_cmd, dict):
        _rotate_waypoint_list_inplace(
            mission_cmd.get("waypoints", None),
            origin_x=origin_x,
            origin_y=origin_y,
            yaw_deg=yaw_deg,
        )
        cached_waypoints = mission_cmd.get("_normalized_waypoints", None)
        if isinstance(cached_waypoints, list):
            _rotate_waypoint_list_inplace(
                cached_waypoints,
                origin_x=origin_x,
                origin_y=origin_y,
                yaw_deg=yaw_deg,
            )

    task_order = scenario_data.get("task_order", None)
    if isinstance(task_order, dict):
        if "anchor_x_m" in task_order and "anchor_y_m" in task_order:
            try:
                pos_x, pos_y = rotate_xy_clockwise(
                    float(task_order.get("anchor_x_m", 0.0)),
                    float(task_order.get("anchor_y_m", 0.0)),
                    origin_x,
                    origin_y,
                    yaw_deg,
                )
                task_order["anchor_x_m"] = pos_x
                task_order["anchor_y_m"] = pos_y
            except Exception:
                pass
        if "station_heading_deg" in task_order:
            try:
                task_order["station_heading_deg"] = (
                    float(task_order.get("station_heading_deg", 0.0)) + float(yaw_deg)
                ) % 360.0
            except Exception:
                pass

    entities = scenario_data.get("entities", [])
    if not isinstance(entities, list) or not entities:
        return

    candidate_indices = [idx for idx, ent in enumerate(entities) if isinstance(ent, dict) and bool(ent.get("is_agent", False))]
    if not candidate_indices:
        for idx, ent in enumerate(entities):
            if isinstance(ent, dict):
                candidate_indices.append(idx)
                break

    for idx in candidate_indices:
        ent = entities[idx]
        if not isinstance(ent, dict):
            continue
        pos = ent.get("pos", None)
        vel = ent.get("vel", None)
        if isinstance(pos, list) and len(pos) >= 2:
            pos_x, pos_y = rotate_xy_clockwise(pos[0], pos[1], origin_x, origin_y, yaw_deg)
            pos[0] = pos_x
            pos[1] = pos_y
        if isinstance(vel, list) and len(vel) >= 2:
            vel_x, vel_y = rotate_xy_clockwise(vel[0], vel[1], 0.0, 0.0, yaw_deg)
            vel[0] = vel_x
            vel[1] = vel_y
        if "heading" in ent:
            try:
                ent["heading"] = (float(ent.get("heading", 0.0)) + float(yaw_deg)) % 360.0
            except Exception:
                pass


def apply_world_yaw_inplace(
    scenario_data: dict[str, Any],
    yaw_deg: float,
    origin_x: float = 0.0,
    origin_y: float = 0.0,
) -> None:
    env = scenario_data.get("environment", {})
    zones = env.get("zones", [])
    if isinstance(zones, list):
        for zone in zones:
            if not isinstance(zone, dict):
                continue
            if "x" in zone and "y" in zone:
                zone_x, zone_y = rotate_xy_clockwise(
                    zone.get("x", 0.0),
                    zone.get("y", 0.0),
                    origin_x,
                    origin_y,
                    yaw_deg,
                )
                zone["x"] = zone_x
                zone["y"] = zone_y
            if "heading" in zone:
                try:
                    zone["heading"] = (float(zone.get("heading", 0.0)) + float(yaw_deg)) % 360.0
                except Exception:
                    pass

    entities = scenario_data.get("entities", [])
    if isinstance(entities, list):
        for ent in entities:
            if not isinstance(ent, dict):
                continue
            pos = ent.get("pos", None)
            vel = ent.get("vel", None)
            if isinstance(pos, list) and len(pos) >= 2:
                pos_x, pos_y = rotate_xy_clockwise(pos[0], pos[1], origin_x, origin_y, yaw_deg)
                pos[0] = pos_x
                pos[1] = pos_y
            if isinstance(vel, list) and len(vel) >= 2:
                vel_x, vel_y = rotate_xy_clockwise(vel[0], vel[1], 0.0, 0.0, yaw_deg)
                vel[0] = vel_x
                vel[1] = vel_y
            if "heading" in ent:
                try:
                    ent["heading"] = (float(ent.get("heading", 0.0)) + float(yaw_deg)) % 360.0
                except Exception:
                    pass

    mission_cmd = scenario_data.get("mission_command", None)
    if isinstance(mission_cmd, dict):
        waypoints = mission_cmd.get("waypoints", None)
        if isinstance(waypoints, list):
            for wp in waypoints:
                if isinstance(wp, dict):
                    if "pos" in wp and isinstance(wp.get("pos"), list) and len(wp["pos"]) >= 2:
                        pos_x, pos_y = rotate_xy_clockwise(
                            wp["pos"][0],
                            wp["pos"][1],
                            origin_x,
                            origin_y,
                            yaw_deg,
                        )
                        wp["pos"][0] = pos_x
                        wp["pos"][1] = pos_y
                    elif "x" in wp and "y" in wp:
                        pos_x, pos_y = rotate_xy_clockwise(
                            wp.get("x", 0.0),
                            wp.get("y", 0.0),
                            origin_x,
                            origin_y,
                            yaw_deg,
                        )
                        wp["x"] = pos_x
                        wp["y"] = pos_y
                elif isinstance(wp, list) and len(wp) >= 2:
                    pos_x, pos_y = rotate_xy_clockwise(wp[0], wp[1], origin_x, origin_y, yaw_deg)
                    wp[0] = pos_x
                    wp[1] = pos_y

    task_order = scenario_data.get("task_order", None)
    if isinstance(task_order, dict):
        if "anchor_x_m" in task_order and "anchor_y_m" in task_order:
            try:
                pos_x, pos_y = rotate_xy_clockwise(
                    float(task_order.get("anchor_x_m", 0.0)),
                    float(task_order.get("anchor_y_m", 0.0)),
                    origin_x,
                    origin_y,
                    yaw_deg,
                )
                task_order["anchor_x_m"] = pos_x
                task_order["anchor_y_m"] = pos_y
            except Exception:
                pass
        if "station_heading_deg" in task_order:
            try:
                task_order["station_heading_deg"] = (
                    float(task_order.get("station_heading_deg", 0.0)) + float(yaw_deg)
                ) % 360.0
            except Exception:
                pass


def _primary_runway_heading_deg(env_cfg: dict[str, Any]) -> float | None:
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


def _prepare_compiled_batch_world_context(
    compiled_scenario: CompiledScenario,
    *,
    seed: int,
    randomization_overrides: dict[str, Any] | None = None,
) -> tuple[PreparedScenarioWorldContext, float | None, str, float, float, float, np.random.RandomState]:
    runtime_metadata = getattr(compiled_scenario, "runtime_metadata", None)
    if runtime_metadata is None:
        raise ValueError("compiled_scenario.runtime_metadata is required for direct batch materialization")

    compiled_template = runtime_metadata.layout_template
    scenario_data = compiled_scenario.instantiate_runtime_context()
    scenario_data["mission_command"] = _clone_runtime_mission_command(runtime_metadata.mission_command_template)
    rng = np.random.RandomState(int(seed) & 0xFFFFFFFF)

    env_rand = dict(compiled_template.env_randomization)
    if isinstance(randomization_overrides, dict) and randomization_overrides:
        env_rand.update(randomization_overrides)

    rotate_mission_heading_with_world = bool(env_rand.get("rotate_mission_heading_with_world", False))
    world_yaw_deg = 0.0
    world_yaw_origin_x = 0.0
    world_yaw_origin_y = 0.0
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
        apply_runtime_world_yaw_inplace(
            scenario_data,
            world_yaw_deg,
            world_yaw_origin_x,
            world_yaw_origin_y,
        )

    terrain_type = str(compiled_template.terrain_type)
    wind_speed = float(compiled_template.wind_speed_mps)
    wind_dir_from = float(compiled_template.wind_dir_from_deg)
    wind_shear = float(compiled_template.wind_shear_mps_per_km)
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
        runway_heading_deg = compiled_template.primary_runway_heading_deg
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
        wind_ref_alt_m = env_rand.get("wind_ref_alt_m", float(compiled_template.wind_ref_alt_m))
        if wind_ref_alt_m is None:
            wind_ref_alt_m = 0.0
        wind_speed = max(0.0, float(wind_speed) - float(wind_shear) * (max(0.0, float(wind_ref_alt_m)) / 1000.0))

    context = PreparedScenarioWorldContext(
        scenario_data=scenario_data,
        seed=int(seed) & 0xFFFFFFFF,
        rotate_mission_heading_with_world=rotate_mission_heading_with_world,
        world_yaw_deg=float(world_yaw_deg),
        world_yaw_origin_x=float(world_yaw_origin_x),
        world_yaw_origin_y=float(world_yaw_origin_y),
    )
    return (
        context,
        compiled_template.time_step_s,
        terrain_type,
        float(wind_speed),
        float(wind_dir_from),
        float(wind_shear),
        rng,
    )


def _load_compiled_scenario_batch_direct(
    batch_runtime,
    compiled_scenario: CompiledScenario,
    *,
    normalized_seeds: list[int],
    randomization_overrides: dict[str, Any] | None = None,
    apply_buffer: BatchWorldApplyBuffer | None = None,
) -> list[AppliedScenarioWorld]:
    runtime_metadata = getattr(compiled_scenario, "runtime_metadata", None)
    if runtime_metadata is None:
        raise ValueError("compiled_scenario.runtime_metadata is required for direct batch materialization")

    compiled_template = runtime_metadata.layout_template
    world_count = int(batch_runtime.world_count())
    if apply_buffer is None:
        apply_buffer = BatchWorldApplyBuffer(world_count)

    terrain_items, wind_items, zone_items, spawn_items = apply_buffer.prepare_direct(
        total_zone_count=len(compiled_template.zones) * world_count,
        total_spawn_count=len(compiled_template.spawns) * world_count,
    )

    contexts: list[PreparedScenarioWorldContext] = []
    spawn_meta_by_world: list[list[tuple[str, bool]]] = []
    time_steps: list[float | None] = []
    zone_cursor = 0
    spawn_cursor = 0

    for world_index, seed in enumerate(normalized_seeds):
        context, time_step_s, terrain_type, wind_speed, wind_dir_from, wind_shear, rng = _prepare_compiled_batch_world_context(
            compiled_scenario,
            seed=int(seed),
            randomization_overrides=randomization_overrides,
        )
        contexts.append(context)
        time_steps.append(None if time_step_s is None else float(time_step_s))

        terrain = terrain_items[world_index]
        terrain.world_index = int(world_index)
        terrain.terrain_type = str(terrain_type)

        wind = wind_items[world_index]
        wind.world_index = int(world_index)
        wind.speed_mps = float(wind_speed)
        wind.dir_from_deg = float(wind_dir_from)
        wind.shear_mps_per_km = float(wind_shear)

        yaw_active = abs(float(context.world_yaw_deg)) > 1.0e-9
        yaw_deg = float(context.world_yaw_deg)
        origin_x = float(context.world_yaw_origin_x)
        origin_y = float(context.world_yaw_origin_y)

        for template in compiled_template.zones:
            x = float(template.x)
            y = float(template.y)
            heading = float(template.heading)
            if yaw_active:
                x, y = rotate_xy_clockwise(x, y, origin_x, origin_y, yaw_deg)
                heading = (heading + yaw_deg) % 360.0
            zone_def = zone_items[zone_cursor]
            zone_cursor += 1
            zone_def.world_index = int(world_index)
            zone_def.name = str(template.name)
            zone_def.x = float(x)
            zone_def.y = float(y)
            zone_def.width = float(template.width)
            zone_def.length = float(template.length)
            zone_def.heading = float(heading)
            zone_def.surface_type = int(template.surface_type)

        world_spawn_meta: list[tuple[str, bool]] = []
        for template in compiled_template.spawns:
            pos = [float(template.x), float(template.y), float(template.z)]
            vel = [float(template.vx), float(template.vy), float(template.vz)]
            heading = float(template.heading)
            pitch = float(template.pitch)
            roll = float(template.roll)
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
            req = spawn_items[spawn_cursor]
            spawn_cursor += 1
            req.world_index = int(world_index)
            req.side = _SIDE_MAP.get(str(template.side_name), ef_py.Side.Neutral)
            req.type_name = str(template.type_name)
            req.entity_name = str(template.entity_name)
            req.is_agent = bool(template.is_agent)
            req.x = float(pos[0])
            req.y = float(pos[1])
            req.z = float(pos[2])
            req.heading = float(heading)
            req.pitch = float(pitch)
            req.roll = float(roll)
            req.vx = float(vel[0])
            req.vy = float(vel[1])
            req.vz = float(vel[2])
            world_spawn_meta.append((str(template.entity_name), bool(template.is_agent)))
        spawn_meta_by_world.append(world_spawn_meta)

    time_step_items = [
        0.0 if ts is None else float(ts)
        for ts in time_steps
    ]
    entity_ids = _apply_world_setup_request(
        batch_runtime,
        seeds=normalized_seeds,
        terrain_assignments=terrain_items,
        wind_assignments=wind_items,
        zones=zone_items[:zone_cursor],
        spawn_requests=spawn_items[:spawn_cursor],
        time_steps=time_step_items,
    )

    applied: list[AppliedScenarioWorld] = []
    entity_cursor = 0
    for world_index, context in enumerate(contexts):
        entities: dict[str, int] = {}
        agent_id: int | None = None
        for entity_name, is_agent in spawn_meta_by_world[world_index]:
            entity_id = int(entity_ids[entity_cursor])
            entity_cursor += 1
            entities[entity_name] = entity_id
            if is_agent and agent_id is None:
                agent_id = entity_id
        applied.append(AppliedScenarioWorld(layout=context, entities=entities, agent_id=agent_id))
    return applied


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
    terrain_type = "legacy"
    wind_speed = 10.0
    wind_dir_from = 270.0
    wind_shear = 4.0
    zones: list[ScenarioZoneLayout] = []
    spawns: list[ScenarioSpawnLayout] = []

    env_cfg = scenario_data.get("environment", {})
    if not isinstance(env_cfg, dict):
        env_cfg = {}

    if compiled_template is not None:
        env_rand = dict(compiled_template.env_randomization)
        time_step_s = compiled_template.time_step_s
        terrain_type = str(compiled_template.terrain_type)
        wind_speed = float(compiled_template.wind_speed_mps)
        wind_dir_from = float(compiled_template.wind_dir_from_deg)
        wind_shear = float(compiled_template.wind_shear_mps_per_km)
        runway_heading_deg_template = compiled_template.primary_runway_heading_deg
        compiled_wind_ref_alt_m = float(compiled_template.wind_ref_alt_m)
    else:
        env_rand = env_cfg.get("randomization", {}) if isinstance(env_cfg.get("randomization", {}), dict) else {}
        if "time_step" in env_cfg:
            time_step_s = float(env_cfg["time_step"])
        terrain_type = str(env_cfg.get("terrain_type", "legacy")).strip() or "legacy"
        wind_cfg = env_cfg.get("wind", {}) if isinstance(env_cfg.get("wind", {}), dict) else {}
        wind_speed = float(wind_cfg.get("speed_mps", 10.0))
        wind_dir_from = float(wind_cfg.get("dir_from_deg", 270.0))
        wind_shear = float(wind_cfg.get("shear_mps_per_km", 4.0))
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
        wind_speed_mps=float(wind_speed),
        wind_dir_from_deg=float(wind_dir_from),
        wind_shear_mps_per_km=float(wind_shear),
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
        entities[spawn.entity_name] = entity_id
        if spawn.is_agent and agent_id is None:
            agent_id = entity_id
    return AppliedScenarioWorld(layout=layout, entities=entities, agent_id=agent_id)


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


def load_compiled_scenario_batch(
    batch_runtime,
    compiled_scenario: CompiledScenario,
    *,
    seeds: list[int] | tuple[int, ...] | np.ndarray,
    randomization_overrides: dict[str, Any] | None = None,
    apply_buffer: BatchWorldApplyBuffer | None = None,
) -> list[AppliedScenarioWorld]:
    if not isinstance(compiled_scenario, CompiledScenario):
        raise TypeError("compiled_scenario must be a CompiledScenario")

    world_count = int(batch_runtime.world_count())
    if world_count <= 0:
        return []

    normalized_seeds = [int(seed) & 0xFFFFFFFF for seed in list(seeds)]
    if len(normalized_seeds) == 1 and world_count > 1:
        base_seed = int(normalized_seeds[0])
        normalized_seeds = [base_seed + idx for idx in range(world_count)]
    if len(normalized_seeds) != world_count:
        raise ValueError(f"expected {world_count} seeds, got {len(normalized_seeds)}")

    runtime_metadata = getattr(compiled_scenario, "runtime_metadata", None)
    if runtime_metadata is not None:
        return _load_compiled_scenario_batch_direct(
            batch_runtime,
            compiled_scenario,
            normalized_seeds=normalized_seeds,
            randomization_overrides=randomization_overrides,
            apply_buffer=apply_buffer,
        )

    layouts: list[ScenarioWorldLayout] = []
    for seed in normalized_seeds:
        layouts.append(
            build_compiled_world_layout(
                compiled_scenario,
                seed=int(seed),
                randomization_overrides=randomization_overrides,
            )
        )

    return apply_world_layouts_to_batch(batch_runtime, layouts, apply_buffer=apply_buffer)


def apply_world_layouts_to_batch(
    batch_runtime,
    layouts: list[ScenarioWorldLayout],
    *,
    apply_buffer: BatchWorldApplyBuffer | None = None,
) -> list[AppliedScenarioWorld]:
    world_count = int(batch_runtime.world_count())
    if len(layouts) != world_count:
        raise ValueError(f"expected {world_count} layouts, got {len(layouts)}")

    if apply_buffer is None:
        apply_buffer = BatchWorldApplyBuffer(world_count)
    terrain_assignments, wind_assignments, zone_defs, spawn_requests = apply_buffer.prepare(layouts)

    normalized_seeds = [int(layout.seed) & 0xFFFFFFFF for layout in layouts]
    time_step_items = [
        0.0 if layout.time_step_s is None else float(layout.time_step_s)
        for layout in layouts
    ]
    entity_ids = _apply_world_setup_request(
        batch_runtime,
        seeds=normalized_seeds,
        terrain_assignments=terrain_assignments,
        wind_assignments=wind_assignments,
        zones=zone_defs,
        spawn_requests=spawn_requests,
        time_steps=time_step_items,
    )

    applied: list[AppliedScenarioWorld] = []
    entity_cursor = 0
    for layout in layouts:
        entities: dict[str, int] = {}
        agent_id: int | None = None
        for spawn in layout.spawns:
            entity_id = int(entity_ids[entity_cursor])
            entity_cursor += 1
            entities[spawn.entity_name] = entity_id
            if spawn.is_agent and agent_id is None:
                agent_id = entity_id
        applied.append(AppliedScenarioWorld(layout=layout, entities=entities, agent_id=agent_id))
    return applied


def _apply_world_setup_request(
    runtime,
    *,
    seeds: list[int],
    terrain_assignments: list[Any],
    wind_assignments: list[Any],
    zones: list[Any],
    spawn_requests: list[Any],
    time_steps: list[float],
) -> list[int]:
    if hasattr(runtime, "apply_world_setup") and hasattr(ef_py, "BatchWorldSetupRequest"):
        request = ef_py.BatchWorldSetupRequest()
        request.seeds = [int(seed) & 0xFFFFFFFF for seed in seeds]
        request.terrain_assignments = list(terrain_assignments)
        request.wind_assignments = list(wind_assignments)
        request.zones = list(zones)
        request.spawn_requests = list(spawn_requests)
        request.time_steps = [float(value) for value in time_steps]
        result = runtime.apply_world_setup(request)
        return [int(entity_id) for entity_id in list(result.entity_ids)]

    return [
        int(entity_id)
        for entity_id in runtime.apply_world_setup_batch(
            seeds,
            terrain_assignments,
            wind_assignments,
            zones,
            spawn_requests,
            time_steps,
        )
    ]
