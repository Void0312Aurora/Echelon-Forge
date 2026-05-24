from __future__ import annotations

from typing import Any

import numpy as np

from python.scenario_compiler import CompiledScenario

from python.scenario.runtime.batch_apply import _apply_world_layouts_to_setup_target
from python.scenario.runtime.batch_apply import _load_compiled_scenario_for_setup_target
from python.scenario.runtime.models import (
    AppliedScenarioWorld,
    BatchWorldApplyBuffer,
    RuntimeWorldLayoutResultCompat,
    ScenarioWorldLayout,
)
from python.scenario.runtime.world_setup import (
    apply_runtime_world_layout_request_maintained,
    apply_world_setup_request_maintained,
    build_batch_world_setup_request,
    build_runtime_world_layout_request,
    extract_batch_world_setup_entity_ids,
    extract_runtime_world_layout_entity_ids,
    normalize_world_setup_terrain_assignments,
)


def read_runtime_world_time_step_diagnostics(
    runtime: Any,
    world_index: int,
    *,
    fallback_time_step_s: float | None = None,
) -> float:
    if hasattr(runtime, "world_time_step"):
        return float(runtime.world_time_step(int(world_index)))
    if fallback_time_step_s is not None:
        return float(fallback_time_step_s)
    world_getter = getattr(runtime, "world_compatibility_quarantine", None)
    if callable(world_getter):
        return float(world_getter(int(world_index)).get_time_step())
    raise AttributeError("runtime does not expose world_time_step or a diagnostics world getter")


def apply_runtime_world_layout_request_diagnostics(runtime: Any, request: Any) -> Any:
    raw_runtime_shaped = hasattr(runtime, "world_compatibility_quarantine") or hasattr(runtime, "world")
    if not raw_runtime_shaped and hasattr(runtime, "apply_world_layout"):
        return apply_runtime_world_layout_request_maintained(runtime, request)
    diagnostics_result = RuntimeWorldLayoutResultCompat()
    diagnostics_result.world_index = int(getattr(request, "world_index", 0))
    diagnostics_result.entity_ids = [
        int(entity_id)
        for entity_id in runtime.apply_world_layout(
            int(request.world_index),
            int(request.seed),
            str(request.terrain_type),
            float(request.wind_speed_mps),
            float(request.wind_dir_from_deg),
            float(request.wind_shear_mps_per_km),
            bool(request.maritime_configured),
            float(request.sea_state),
            float(request.wave_heading_deg),
            float(request.wave_period_s),
            list(request.zones),
            list(request.spawn_requests),
            list(request.time_steps),
        )
    ]
    return diagnostics_result


def apply_world_setup_request_diagnostics(runtime: Any, request: Any) -> list[int]:
    facade_shaped = hasattr(runtime, "apply_world_setup") and not (
        (hasattr(runtime, "world_compatibility_quarantine") or hasattr(runtime, "world"))
        and not hasattr(runtime, "facade")
    )
    if facade_shaped:
        return apply_world_setup_request_maintained(runtime, request)
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


def apply_world_setup_payload_diagnostics(
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
    if request is not None:
        return apply_world_setup_request_diagnostics(runtime, request)
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


def apply_world_layouts_to_batch_diagnostics(
    diagnostics_runtime: Any,
    layouts: list[ScenarioWorldLayout],
    *,
    apply_buffer: BatchWorldApplyBuffer | None = None,
) -> list[AppliedScenarioWorld]:
    return _apply_world_layouts_to_setup_target(
        diagnostics_runtime,
        layouts,
        apply_buffer=apply_buffer,
        setup_payload_apply=apply_world_setup_payload_diagnostics,
    )


def load_compiled_scenario_batch_diagnostics(
    diagnostics_runtime: Any,
    compiled_scenario: CompiledScenario,
    *,
    seeds: list[int] | tuple[int, ...] | np.ndarray,
    randomization_overrides: dict[str, Any] | None = None,
    apply_buffer: BatchWorldApplyBuffer | None = None,
) -> list[AppliedScenarioWorld]:
    return _load_compiled_scenario_for_setup_target(
        diagnostics_runtime,
        compiled_scenario,
        seeds=seeds,
        randomization_overrides=randomization_overrides,
        apply_buffer=apply_buffer,
        setup_payload_apply=apply_world_setup_payload_diagnostics,
    )


__all__ = [
    "apply_runtime_world_layout_request_diagnostics",
    "apply_world_layouts_to_batch_diagnostics",
    "apply_world_setup_payload_diagnostics",
    "apply_world_setup_request_diagnostics",
    "build_batch_world_setup_request",
    "build_runtime_world_layout_request",
    "extract_batch_world_setup_entity_ids",
    "extract_runtime_world_layout_entity_ids",
    "load_compiled_scenario_batch_diagnostics",
    "normalize_world_setup_terrain_assignments",
    "read_runtime_world_time_step_diagnostics",
]
