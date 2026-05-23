from __future__ import annotations

from typing import Any

import ef_py

from python.scenario_compiler import (
    DEFAULT_TERRAIN_TYPE,
    TERRAIN_TYPE_SOURCE_COMPATIBILITY,
    TERRAIN_TYPE_SOURCE_DEFAULT,
    TERRAIN_TYPE_SOURCE_EXPLICIT,
    _normalize_terrain_type_value,
)


def normalize_world_setup_terrain_assignments(
    terrain_assignments: list[Any],
    *,
    world_count: int | None = None,
    default: str = DEFAULT_TERRAIN_TYPE,
) -> tuple[list[Any], list[str]]:
    normalized = list(terrain_assignments)
    provided_count = len(normalized)
    normalized_world_count = max(0, int(world_count)) if world_count is not None else None
    if normalized_world_count is not None and len(normalized) < normalized_world_count:
        normalized.extend(ef_py.WorldTerrainAssignment() for _ in range(normalized_world_count - len(normalized)))

    source_by_world: dict[int, str] = {}
    for item_index, item in enumerate(normalized):
        raw_terrain_type = getattr(item, "terrain_type", None)
        terrain_type = _normalize_terrain_type_value(raw_terrain_type, default=default)
        item.terrain_type = terrain_type
        world_index = int(getattr(item, "world_index", 0))
        if item_index >= provided_count or not str(raw_terrain_type).strip():
            source = TERRAIN_TYPE_SOURCE_DEFAULT
        elif str(terrain_type).strip().lower() in {"legacy", "hill", "gaussian_hill", "mountain"}:
            source = TERRAIN_TYPE_SOURCE_COMPATIBILITY
        else:
            source = TERRAIN_TYPE_SOURCE_EXPLICIT
        if source == TERRAIN_TYPE_SOURCE_COMPATIBILITY:
            source_by_world[world_index] = TERRAIN_TYPE_SOURCE_COMPATIBILITY
        elif world_index not in source_by_world:
            source_by_world[world_index] = source

    if normalized_world_count is None:
        normalized_world_count = max(source_by_world.keys(), default=-1) + 1
    sources = []
    for world_index in range(normalized_world_count):
        source = source_by_world.get(world_index)
        if source is None:
            source = TERRAIN_TYPE_SOURCE_DEFAULT
        sources.append(source)
    return normalized, sources


def build_batch_world_setup_request(
    *,
    seeds: list[int],
    terrain_assignments: list[Any],
    wind_assignments: list[Any],
    zones: list[Any],
    spawn_requests: list[Any],
    time_steps: list[float],
):
    if not hasattr(ef_py, "BatchWorldSetupRequest"):
        return None
    normalized_terrain_assignments, _ = normalize_world_setup_terrain_assignments(
        terrain_assignments,
        world_count=len(seeds),
    )
    request = ef_py.BatchWorldSetupRequest()
    request.seeds = [int(seed) & 0xFFFFFFFF for seed in seeds]
    request.terrain_assignments = normalized_terrain_assignments
    request.wind_assignments = list(wind_assignments)
    request.zones = list(zones)
    request.spawn_requests = list(spawn_requests)
    request.time_steps = [float(value) for value in time_steps]
    return request


def extract_batch_world_setup_entity_ids(result: Any) -> list[int]:
    entity_ids = getattr(result, "entity_ids", result)
    return [int(entity_id) for entity_id in list(entity_ids)]


def apply_world_setup_request_compat(runtime: Any, request: Any) -> list[int]:
    if hasattr(runtime, "apply_world_setup"):
        return extract_batch_world_setup_entity_ids(runtime.apply_world_setup(request))
    if not hasattr(runtime, "apply_world_setup_batch"):
        raise AttributeError("runtime does not expose apply_world_setup or apply_world_setup_batch")
    return [
        int(entity_id)
        for entity_id in runtime.apply_world_setup_batch(
            list(request.seeds),
            list(request.terrain_assignments),
            list(request.wind_assignments),
            list(request.zones),
            list(request.spawn_requests),
            list(request.time_steps),
        )
    ]


def apply_world_setup_payload_compat(
    runtime: Any,
    *,
    seeds: list[int],
    terrain_assignments: list[Any],
    wind_assignments: list[Any],
    zones: list[Any],
    spawn_requests: list[Any],
    time_steps: list[float],
) -> list[int]:
    normalized_terrain_assignments, _ = normalize_world_setup_terrain_assignments(
        terrain_assignments,
        world_count=len(seeds),
    )
    request = build_batch_world_setup_request(
        seeds=seeds,
        terrain_assignments=normalized_terrain_assignments,
        wind_assignments=wind_assignments,
        zones=zones,
        spawn_requests=spawn_requests,
        time_steps=time_steps,
    )
    if request is not None and hasattr(runtime, "apply_world_setup"):
        return extract_batch_world_setup_entity_ids(runtime.apply_world_setup(request))
    if not hasattr(runtime, "apply_world_setup_batch"):
        raise AttributeError("runtime does not expose apply_world_setup or apply_world_setup_batch")
    return [
        int(entity_id)
        for entity_id in runtime.apply_world_setup_batch(
            list(seeds),
            list(normalized_terrain_assignments),
            list(wind_assignments),
            list(zones),
            list(spawn_requests),
            list(time_steps),
        )
    ]


__all__ = [
    "apply_world_setup_payload_compat",
    "apply_world_setup_request_compat",
    "build_batch_world_setup_request",
    "extract_batch_world_setup_entity_ids",
    "normalize_world_setup_terrain_assignments",
]
