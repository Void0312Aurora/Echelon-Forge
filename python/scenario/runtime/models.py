from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import ef_py


_SURFACE_TYPE_MAP = {
    "Concrete": 0,
    "Asphalt": 1,
    "HardPacked": 2,
    "SoftDirt": 3,
    "Water": 4,
    "Obstacle": 5,
}

_SIDE_MAP = {
    "Blue": "Blue",
    "Red": "Red",
    "Neutral": "Neutral",
}


def resolve_scenario_side(side_name: Any):
    member_name = _SIDE_MAP.get(str(side_name), "Neutral")
    return getattr(ef_py.Side, member_name)


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
    ammo_override_enabled: bool = False
    missiles_remaining: int = 0
    max_missiles: int = 0
    weapon_cooldown_override_enabled: bool = False
    weapon_cooldown_s: float = 2.0
    weapon_last_fire_time: float = -1.0


@dataclass
class ScenarioRosterMemberLayout:
    entity_name: str
    is_agent: bool
    team_id: int | None = None
    element_id: int | None = None
    role_code: int | None = None
    formation_role_id: str | None = None
    relative_slot_code: int | None = None
    policy_route: str | None = None
    reference_entity_name: str | None = None
    reference_entity_id: int | None = None
    mission_command_overrides: dict[str, Any] | None = None
    task_order_overrides: dict[str, Any] | None = None


@dataclass
class AppliedScenarioRosterMember:
    world_index: int | None
    entity_name: str
    entity_id: int
    is_agent: bool
    team_id: int | None = None
    element_id: int | None = None
    role_code: int | None = None
    formation_role_id: str | None = None
    relative_slot_code: int | None = None
    policy_route: str | None = None
    reference_entity_name: str | None = None
    reference_entity_id: int | None = None
    mission_command_overrides: dict[str, Any] | None = None
    task_order_overrides: dict[str, Any] | None = None

    def key(self) -> tuple[int | None, int]:
        return (None if self.world_index is None else int(self.world_index), int(self.entity_id))


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
    terrain_type_source: str
    wind_speed_mps: float
    wind_dir_from_deg: float
    wind_shear_mps_per_km: float
    # False: leave ships on platform fallback maritime params.
    # True: environment maritime fields fully override per-platform defaults.
    maritime_configured: bool
    sea_state: float
    wave_heading_deg: float
    wave_period_s: float
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
    active_roster: list[AppliedScenarioRosterMember] = field(default_factory=list)


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
                req.ammo_override_enabled = bool(spawn.ammo_override_enabled)
                req.missiles_remaining = int(spawn.missiles_remaining)
                req.max_missiles = int(spawn.max_missiles)
                req.weapon_cooldown_override_enabled = bool(spawn.weapon_cooldown_override_enabled)
                req.weapon_cooldown_s = float(spawn.weapon_cooldown_s)
                req.weapon_last_fire_time = float(spawn.weapon_last_fire_time)

        return terrain_items, wind_items, zone_items, spawn_items

    def prepare_direct(self, *, total_zone_count: int, total_spawn_count: int) -> tuple[list[Any], list[Any], list[Any], list[Any]]:
        terrain_items = self._ensure_size(self.terrain_assignments, int(self.world_count), ef_py.WorldTerrainAssignment)
        wind_items = self._ensure_size(self.wind_assignments, int(self.world_count), ef_py.WorldWindAssignment)
        zone_items = self._ensure_size(self.zone_defs, int(total_zone_count), ef_py.WorldZoneDefinition)
        spawn_items = self._ensure_size(self.spawn_requests, int(total_spawn_count), ef_py.WorldSpawnRequest)
        return terrain_items, wind_items, zone_items, spawn_items


__all__ = [
    "AppliedScenarioRosterMember",
    "AppliedScenarioWorld",
    "BatchWorldApplyBuffer",
    "PreparedScenarioWorldContext",
    "ScenarioRosterMemberLayout",
    "ScenarioSpawnLayout",
    "ScenarioWorldLayout",
    "ScenarioZoneLayout",
]
