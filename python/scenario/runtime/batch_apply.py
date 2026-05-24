from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

import ef_py
import numpy as np

from python.scenario_compiler import (
    CompiledScenario,
    _clone_runtime_mission_command,
    materialize_runtime_waypoint_cache,
)

from .geometry import apply_runtime_world_yaw_inplace, rotate_xy_clockwise
from .kernel_apply import build_compiled_world_layout
from .models import (
    AppliedScenarioWorld,
    BatchWorldApplyBuffer,
    PreparedScenarioWorldContext,
    ScenarioWorldLayout,
    _SIDE_MAP,
)
from .randomization import _apply_spawn_randomization
from .roster import _attach_active_roster_to_applied_world
from .world_setup import apply_world_setup_payload_maintained


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
    facade_setup_target,
    compiled_scenario: CompiledScenario,
    *,
    normalized_seeds: list[int],
    randomization_overrides: dict[str, Any] | None = None,
    apply_buffer: BatchWorldApplyBuffer | None = None,
    setup_payload_apply: Callable[..., list[int]] | None = None,
) -> list[AppliedScenarioWorld]:
    runtime_metadata = getattr(compiled_scenario, "runtime_metadata", None)
    if runtime_metadata is None:
        raise ValueError("compiled_scenario.runtime_metadata is required for direct batch materialization")

    compiled_template = runtime_metadata.layout_template
    world_count = int(facade_setup_target.world_count())
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
            req.ammo_override_enabled = bool(template.ammo_override_enabled)
            req.missiles_remaining = int(template.missiles_remaining)
            req.max_missiles = int(template.max_missiles)
            req.weapon_cooldown_override_enabled = bool(template.weapon_cooldown_override_enabled)
            req.weapon_cooldown_s = float(template.weapon_cooldown_s)
            req.weapon_last_fire_time = float(template.weapon_last_fire_time)
            world_spawn_meta.append((str(template.entity_name), bool(template.is_agent)))
        spawn_meta_by_world.append(world_spawn_meta)

    time_step_items = [
        0.0 if ts is None else float(ts)
        for ts in time_steps
    ]
    entity_ids = _apply_world_setup_request(
        facade_setup_target,
        seeds=normalized_seeds,
        terrain_assignments=terrain_items,
        wind_assignments=wind_items,
        zones=zone_items[:zone_cursor],
        spawn_requests=spawn_items[:spawn_cursor],
        time_steps=time_step_items,
        setup_payload_apply=setup_payload_apply,
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
        applied.append(
            _attach_active_roster_to_applied_world(
                AppliedScenarioWorld(layout=context, entities=entities, agent_id=agent_id),
                world_index=world_index,
            )
        )
    return applied


def _load_compiled_scenario_for_setup_target(
    facade_setup_target,
    compiled_scenario: CompiledScenario,
    *,
    seeds: list[int] | tuple[int, ...] | np.ndarray,
    randomization_overrides: dict[str, Any] | None = None,
    apply_buffer: BatchWorldApplyBuffer | None = None,
    setup_payload_apply: Callable[..., list[int]] | None = None,
) -> list[AppliedScenarioWorld]:
    if not isinstance(compiled_scenario, CompiledScenario):
        raise TypeError("compiled_scenario must be a CompiledScenario")

    world_count = int(facade_setup_target.world_count())
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
            facade_setup_target,
            compiled_scenario,
            normalized_seeds=normalized_seeds,
            randomization_overrides=randomization_overrides,
            apply_buffer=apply_buffer,
            setup_payload_apply=setup_payload_apply,
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

    return _apply_world_layouts_to_setup_target(
        facade_setup_target,
        layouts,
        apply_buffer=apply_buffer,
        setup_payload_apply=setup_payload_apply,
    )


def load_compiled_scenario_for_setup_target(
    facade_setup_target,
    compiled_scenario: CompiledScenario,
    *,
    seeds: list[int] | tuple[int, ...] | np.ndarray,
    randomization_overrides: dict[str, Any] | None = None,
    apply_buffer: BatchWorldApplyBuffer | None = None,
) -> list[AppliedScenarioWorld]:
    return _load_compiled_scenario_for_setup_target(
        facade_setup_target,
        compiled_scenario,
        seeds=seeds,
        randomization_overrides=randomization_overrides,
        apply_buffer=apply_buffer,
    )


def _apply_world_layouts_to_setup_target(
    facade_setup_target,
    layouts: list[ScenarioWorldLayout],
    *,
    apply_buffer: BatchWorldApplyBuffer | None = None,
    setup_payload_apply: Callable[..., list[int]] | None = None,
) -> list[AppliedScenarioWorld]:
    world_count = int(facade_setup_target.world_count())
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
        facade_setup_target,
        seeds=normalized_seeds,
        terrain_assignments=terrain_assignments,
        wind_assignments=wind_assignments,
        zones=zone_defs,
        spawn_requests=spawn_requests,
        time_steps=time_step_items,
        setup_payload_apply=setup_payload_apply,
    )

    applied: list[AppliedScenarioWorld] = []
    entity_cursor = 0
    for world_index, layout in enumerate(layouts):
        entities: dict[str, int] = {}
        agent_id: int | None = None
        for spawn in layout.spawns:
            entity_id = int(entity_ids[entity_cursor])
            entity_cursor += 1
            entities[spawn.entity_name] = entity_id
            if spawn.is_agent and agent_id is None:
                agent_id = entity_id
        applied.append(
            _attach_active_roster_to_applied_world(
                AppliedScenarioWorld(layout=layout, entities=entities, agent_id=agent_id),
                world_index=world_index,
            )
        )
    return applied


def apply_world_layouts_to_setup_target(
    facade_setup_target,
    layouts: list[ScenarioWorldLayout],
    *,
    apply_buffer: BatchWorldApplyBuffer | None = None,
) -> list[AppliedScenarioWorld]:
    return _apply_world_layouts_to_setup_target(
        facade_setup_target,
        layouts,
        apply_buffer=apply_buffer,
    )


def _apply_world_setup_request(
    facade_setup_target,
    *,
    seeds: list[int],
    terrain_assignments: list[Any],
    wind_assignments: list[Any],
    zones: list[Any],
    spawn_requests: list[Any],
    time_steps: list[float],
    setup_payload_apply: Callable[..., list[int]] | None = None,
) -> list[int]:
    if setup_payload_apply is None:
        return apply_world_setup_payload_maintained(
            facade_setup_target,
            seeds=seeds,
            terrain_assignments=terrain_assignments,
            wind_assignments=wind_assignments,
            zones=zones,
            spawn_requests=spawn_requests,
            time_steps=time_steps,
        )
    return setup_payload_apply(
        facade_setup_target,
        seeds=seeds,
        terrain_assignments=terrain_assignments,
        wind_assignments=wind_assignments,
        zones=zones,
        spawn_requests=spawn_requests,
        time_steps=time_steps,
    )


__all__ = [
    "apply_world_layouts_to_setup_target",
    "load_compiled_scenario_for_setup_target",
]
