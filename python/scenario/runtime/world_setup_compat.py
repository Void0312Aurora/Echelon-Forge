from __future__ import annotations

from typing import Any

import ef_py


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
    request = ef_py.BatchWorldSetupRequest()
    request.seeds = [int(seed) & 0xFFFFFFFF for seed in seeds]
    request.terrain_assignments = list(terrain_assignments)
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
    request = build_batch_world_setup_request(
        seeds=seeds,
        terrain_assignments=terrain_assignments,
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
            list(terrain_assignments),
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
]
