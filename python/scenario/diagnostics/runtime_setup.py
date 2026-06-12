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
    raise AttributeError("runtime diagnostics require world_time_step or adapter-supplied fallback_time_step_s")


def apply_runtime_world_layout_request_diagnostics(runtime: Any, request: Any) -> Any:
    return apply_runtime_world_layout_request_maintained(runtime, request)


def apply_world_setup_request_diagnostics(runtime: Any, request: Any) -> list[int]:
    return apply_world_setup_request_maintained(runtime, request)


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
    return apply_world_setup_request_diagnostics(runtime, request)


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
