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
from .models import RuntimeWorldLayoutRequestCompat, RuntimeWorldLayoutResultCompat


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


def build_runtime_world_layout_request(
    *,
    world_index: int,
    seed: int,
    terrain_type: str,
    wind_speed_mps: float,
    wind_dir_from_deg: float,
    wind_shear_mps_per_km: float,
    maritime_configured: bool,
    sea_state: float,
    wave_heading_deg: float,
    wave_period_s: float,
    zones: list[Any],
    spawn_requests: list[Any],
    time_steps: list[float],
):
    if hasattr(ef_py, "RuntimeWorldLayoutRequest"):
        request = ef_py.RuntimeWorldLayoutRequest()
    else:
        request = RuntimeWorldLayoutRequestCompat()
    request.world_index = int(world_index)
    request.seed = int(seed) & 0xFFFFFFFF
    request.terrain_type = str(terrain_type)
    request.wind_speed_mps = float(wind_speed_mps)
    request.wind_dir_from_deg = float(wind_dir_from_deg)
    request.wind_shear_mps_per_km = float(wind_shear_mps_per_km)
    request.maritime_configured = bool(maritime_configured)
    request.sea_state = float(sea_state)
    request.wave_heading_deg = float(wave_heading_deg)
    request.wave_period_s = float(wave_period_s)
    request.zones = list(zones)
    request.spawn_requests = list(spawn_requests)
    request.time_steps = [float(value) for value in list(time_steps)]
    return request


def extract_runtime_world_layout_entity_ids(result: Any) -> list[int]:
    entity_ids = getattr(result, "entity_ids", result)
    return [int(entity_id) for entity_id in list(entity_ids)]


def _maintained_setup_target_required_message(surface: str) -> str:
    return f"{surface} requires a maintained facade setup target; raw runtime setup is outside this contract."


def apply_runtime_world_layout_request_maintained(setup_target: Any, request: Any) -> Any:
    if (
        hasattr(setup_target, "world_compatibility_quarantine")
        or hasattr(setup_target, "world")
        or not hasattr(setup_target, "apply_world_layout")
    ):
        raise RuntimeError(
            _maintained_setup_target_required_message(
                "apply_runtime_world_layout_request_maintained"
            )
        )
    result = setup_target.apply_world_layout(request)
    if hasattr(result, "entity_ids") and hasattr(result, "world_index"):
        return result
    maintained_result = RuntimeWorldLayoutResultCompat()
    maintained_result.world_index = int(getattr(request, "world_index", 0))
    maintained_result.entity_ids = extract_runtime_world_layout_entity_ids(result)
    return maintained_result


def apply_world_setup_request_maintained(setup_target: Any, request: Any) -> list[int]:
    raw_runtime_shaped = (
        hasattr(setup_target, "world_compatibility_quarantine")
        or hasattr(setup_target, "world")
    ) and not hasattr(setup_target, "facade")
    if request is None or raw_runtime_shaped or not hasattr(setup_target, "apply_world_setup"):
        raise RuntimeError(
            _maintained_setup_target_required_message("apply_world_setup_request_maintained")
        )
    return extract_batch_world_setup_entity_ids(setup_target.apply_world_setup(request))


def apply_world_setup_payload_maintained(
    setup_target: Any,
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
    return apply_world_setup_request_maintained(setup_target, request)


__all__ = [
    "apply_runtime_world_layout_request_maintained",
    "apply_world_setup_payload_maintained",
    "apply_world_setup_request_maintained",
    "build_batch_world_setup_request",
    "build_runtime_world_layout_request",
    "extract_batch_world_setup_entity_ids",
    "extract_runtime_world_layout_entity_ids",
    "normalize_world_setup_terrain_assignments",
]
