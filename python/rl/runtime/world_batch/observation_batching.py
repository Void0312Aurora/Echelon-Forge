from __future__ import annotations

from collections.abc import Callable
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any
import time

import ef_py
import numpy as np

from python.mission_obs_taxonomy import mission_observation_compiled_fallback_mode
from .typed_observation_view import admit_typed_observation_view_spec


# G4 information-state declaration (architecture design doc §3/§15; facility in
# python/architecture/information_layer.py). This module is the C3 world-batch
# execution-observation assembler: it consumes cached truth/instrument objects,
# obtains the two own-ship ILS coordinates through the high-level injected
# observation-view reader, and passes the opaque truth object unchanged to the
# compiled ``ef_py`` batch kernel. Per the I32 batch-step stage contracts
# (python/rl/runtime/world_batch/core.py), this is the ``observation_build``
# closure at P10 ObservationExport. The I87 typed-view spec is structural-only:
# empty required/optional lists do not filter or wildcard fields. The default-
# off path performs no facade describe call or spec admission.
INFORMATION_LAYER_CONSUMED = ("World Truth",)
INFORMATION_LAYER_PRODUCED = ("Agent Observation",)
SEMANTIC_STAGE = ("P10 ObservationExport",)


@dataclass
class ExecutionObservationBatch:
    inst_batch: list[Any]
    truth_batch: list[Any]
    mission_inputs_batch: list[Any]
    ils_batch: np.ndarray
    inst_out: np.ndarray
    contacts_out: np.ndarray
    rwr_out: np.ndarray
    mission_out: np.ndarray
    device_view: Any = None
    timing: dict[str, float] = field(default_factory=dict)


def compute_execution_observation_batch(
    *,
    states: Sequence[Any],
    mission_obs_mode: str | None,
    max_contacts: int,
    max_rwr: int,
    backend: str,
    allow_device_export: bool = False,
    torch_bridge_enabled: bool = False,
    observation_view_spec: Any = None,
    own_ship_field_reader: Callable[[Any, str], Any],
) -> ExecutionObservationBatch:
    inst_batch: list[Any] = []
    truth_batch: list[Any] = []
    mission_inputs_batch: list[Any] = []
    ils_batch = np.zeros((len(states), 4), dtype=np.float32)

    if observation_view_spec is not None:
        admit_typed_observation_view_spec(observation_view_spec)

    mission_mode_for_compiled = str(mission_obs_mode or "basic")
    python_owned_mission = False
    if states:
        first_loader = states[0].loader
        mode_check = getattr(first_loader, "_python_owned_mission_observation_mode", None)
        if callable(mode_check):
            python_owned_mission = bool(mode_check(mission_obs_mode))
    if python_owned_mission:
        mission_mode_for_compiled = str(mission_observation_compiled_fallback_mode(mission_obs_mode) or "basic")
        allow_device_export = False

    mission_input_t0 = time.perf_counter()
    for state_index, state in enumerate(states):
        if state.last_inst is None or state.last_truth is None:
            raise RuntimeError(f"world-batch state {state_index} has no cached state for observation build")
        loader = state.loader
        if hasattr(loader, "reset_runtime_eval_cache"):
            try:
                loader.reset_runtime_eval_cache()
            except Exception:
                pass
        inst = state.last_inst
        truth = state.last_truth
        inst_batch.append(inst)
        truth_batch.append(truth)
        mission_inputs_batch.append(
            loader._build_mission_observation_runtime_inputs(
                mission_obs_mode,
                truth=truth,
                inst=inst,
            )
            if not python_owned_mission
            else loader._build_mission_observation_runtime_inputs(
                mission_mode_for_compiled,
                truth=truth,
                inst=inst,
            )
        )
        own_x = float(own_ship_field_reader(truth, "x"))
        own_y = float(own_ship_field_reader(truth, "y"))
        ils_vec = loader.get_ils_observation(own_x, own_y, float(inst.alt_baro))
        ils_batch[state_index, :] = np.asarray(ils_vec[:4], dtype=np.float32)
    mission_input_build_ms = (time.perf_counter() - mission_input_t0) * 1000.0

    execution_obs_t0 = time.perf_counter()
    if (
        backend == "gpu_host"
        and allow_device_export
        and torch_bridge_enabled
        and hasattr(ef_py, "compute_execution_observation_batch_export")
    ):
        inst_out, contacts_out, rwr_out, mission_out, device_view = ef_py.compute_execution_observation_batch_export(
            inst_batch,
            truth_batch,
            mission_inputs_batch,
            ils_batch,
            int(max_contacts),
            int(max_rwr),
            True,
        )
    else:
        inst_out, contacts_out, rwr_out, mission_out = ef_py.compute_execution_observation_batch_numpy(
            inst_batch,
            truth_batch,
            mission_inputs_batch,
            ils_batch,
            int(max_contacts),
            int(max_rwr),
            backend == "gpu_host",
        )
        device_view = None
    execution_observation_batch_ms = (time.perf_counter() - execution_obs_t0) * 1000.0

    return ExecutionObservationBatch(
        inst_batch=inst_batch,
        truth_batch=truth_batch,
        mission_inputs_batch=mission_inputs_batch,
        ils_batch=ils_batch,
        inst_out=np.asarray(inst_out, dtype=np.float32),
        contacts_out=np.asarray(contacts_out, dtype=np.float32),
        rwr_out=np.asarray(rwr_out, dtype=np.float32),
        mission_out=np.asarray(mission_out, dtype=np.float32),
        device_view=device_view,
        timing={
            "mission_input_build_ms": float(mission_input_build_ms),
            "execution_observation_batch_ms": float(execution_observation_batch_ms),
        },
    )


def refresh_visual_cache_batch(
    *,
    adapter: Any,
    indexed_states: Sequence[tuple[int, Any]],
    visual_downsample: int,
    visual_update_interval: int,
    arb_height: int,
    arb_width: int,
    arb_channels: int,
    arb_height_native: int,
    arb_width_native: int,
    backend: str,
    allow_device_export: bool = False,
) -> tuple[bool, Any]:
    _ = (
        int(arb_height),
        int(arb_width),
        int(arb_channels),
        int(arb_height_native),
        int(arb_width_native),
    )
    refresh_indices: list[int] = []
    refresh_states: list[Any] = []
    refs: list[Any] = []
    for item_index, state in indexed_states:
        need_refresh = (
            state.visual_cache is None
            or visual_update_interval <= 1
            or state.steps <= 0
            or (int(state.steps) - int(state.visual_cache_step)) >= visual_update_interval
        )
        if not need_refresh:
            continue
        refresh_indices.append(int(item_index))
        refresh_states.append(state)
        ref = ef_py.WorldEntityRef()
        ref.world_index = int(state.world_index)
        ref.entity_id = int(state.entity_id)
        refs.append(ref)

    if not refresh_states:
        return False, None

    if backend == "legacy":
        raise ValueError("batch_visual_backend='legacy' has been removed from maintained VecEnv paths")
    if not hasattr(ef_py, "compute_world_batch_visual_observation_batch_numpy"):
        raise RuntimeError("maintained visual batching requires compute_world_batch_visual_observation_batch_numpy")

    if (
        backend == "gpu_host"
        and allow_device_export
        and len(refresh_states) == len(indexed_states)
        and hasattr(ef_py, "compute_world_batch_visual_observation_batch_export")
    ):
        visuals, device_view = adapter.compute_visual_observation_batch_export(
            refs,
            int(visual_downsample),
            True,
        )
    else:
        visuals = adapter.compute_visual_observation_batch_numpy(
            refs,
            int(visual_downsample),
            backend == "gpu_host",
        )
        device_view = None

    visuals = np.asarray(visuals, dtype=np.float32)
    for batch_idx, state in enumerate(refresh_states):
        state.visual_cache = np.asarray(visuals[batch_idx], dtype=np.float32)
        state.visual_cache_step = int(state.steps)
    return True, device_view


__all__ = [
    "ExecutionObservationBatch",
    "compute_execution_observation_batch",
    "refresh_visual_cache_batch",
]
