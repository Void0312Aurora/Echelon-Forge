"""Shared batch-step operations for execution and cooperative modes.

Extracted from verbatim and parameterized-isomorphic duplicates between
``WorldBatchVecEnv`` and ``CooperativeWorldBatchVecEnv``.  Every function
is resolved once at call-site scope; hot-path bodies contain no imports,
no registry lookups, and no exception-based control flow (pinned by the
disassembly tests that cover the callers).

Dependency surface: this module imports ``ef_py``, ``numpy``,
``python.rl.tasking.bridge`` (``build_kernel_mission_command`` — an
existing dependency direction inherited from the pre-extraction inline
code in both vec-envs), and the sibling ``command_chain_cache`` module.
It must NOT import ``gym_envs`` at any scope (AST-pinned by the core
test suite); unlike ``core.py`` it is not a zero-domain-import substrate
node.
"""

from __future__ import annotations

from typing import Any

import ef_py
import numpy as np

from python.rl.tasking.bridge import build_kernel_mission_command

from .command_chain_cache import (
    leader_intent_snapshot,
    mission_command_snapshot,
    pilot_report_snapshot,
    project_world_leader_intent_maintained_assignment,
    project_world_mission_command_maintained_assignment,
    project_world_pilot_report_maintained_assignment,
    project_world_task_order_maintained_assignment,
    snapshot_changed,
    task_order_snapshot,
)


# ---------------------------------------------------------------------------
# Verbatim-shared: seed normalisation
# ---------------------------------------------------------------------------

def normalize_seed(seed: int | None) -> int:
    """Normalise an optional seed to a reproducible uint32."""
    if seed is None:
        seed = int(np.random.randint(0, np.iinfo(np.uint32).max, dtype=np.uint32))
    return int(seed) & 0xFFFFFFFF


# ---------------------------------------------------------------------------
# Verbatim-shared: buffer observation store
# ---------------------------------------------------------------------------

def save_obs_to_buffer(
    buf_obs: dict[str | None, np.ndarray],
    keys: list[str | None],
    env_idx: int,
    obs: Any,
) -> None:
    """Write a single observation into the VecEnv buffer arrays."""
    for key in keys:
        if key is None:
            buf_obs[key][env_idx] = obs
        else:
            buf_obs[key][env_idx] = obs[key]


# ---------------------------------------------------------------------------
# Parameterised-shared: backend mode resolution
# ---------------------------------------------------------------------------

def resolve_batch_observation_backend_mode(
    backend_setting: str,
    runtime_available: bool,
) -> str:
    """Resolve the effective observation batching backend."""
    if backend_setting == "auto":
        if runtime_available:
            return "compiled"
        raise RuntimeError(
            "maintained observation batching requires "
            "compute_execution_observation_batch_numpy"
        )
    return backend_setting


def batch_observation_runtime_base_check() -> bool:
    """Core ef_py attribute gate shared by all modes."""
    return hasattr(ef_py, "compute_execution_observation_batch_numpy")


def resolve_batch_visual_backend_mode(backend_setting: str) -> str:
    """Resolve the effective visual batching backend."""
    if backend_setting == "auto":
        if hasattr(ef_py, "compute_world_batch_visual_observation_batch_numpy"):
            return "compiled"
        raise RuntimeError(
            "maintained visual batching requires "
            "compute_world_batch_visual_observation_batch_numpy"
        )
    return backend_setting


# ---------------------------------------------------------------------------
# Parameterised-shared: per-entity command chain diff
# ---------------------------------------------------------------------------

def diff_single_entity_command_chain(
    world_index: int,
    entity_id: int,
    loader: Any,
    prev_mission_snap: Any,
    prev_task_snap: Any,
    prev_intent_snap: Any,
    prev_report_snap: Any,
    mission_assignments: list,
    task_assignments: list,
    intent_assignments: list,
    report_assignments: list,
) -> tuple[Any, Any, Any, Any]:
    """Diff command chain for one entity, appending to assignment lists.

    Returns ``(new_mission_snap, new_task_snap, new_intent_snap,
    new_report_snap)`` — callers store these in their own data structures
    (handle attrs for execution, per-world dicts for cooperative).
    """
    new_mission = prev_mission_snap
    mission_command = build_kernel_mission_command(loader)
    mission_snap = mission_command_snapshot(mission_command)
    if snapshot_changed(prev_mission_snap, mission_snap):
        assign = ef_py.WorldMissionCommandMaintainedAssignment()
        project_world_mission_command_maintained_assignment(
            assign,
            world_index=int(world_index),
            entity_id=int(entity_id),
            compatibility_mission_command_shell=mission_command,
        )
        mission_assignments.append(assign)
        new_mission = mission_snap

    new_task = prev_task_snap
    task_snap = task_order_snapshot(getattr(loader, "task_order", None))
    if task_snap is not None and snapshot_changed(prev_task_snap, task_snap):
        assign = ef_py.WorldTaskOrderMaintainedAssignment()
        project_world_task_order_maintained_assignment(
            assign,
            world_index=int(world_index),
            entity_id=int(entity_id),
            compatibility_task_order_shell=loader.task_order,
        )
        task_assignments.append(assign)
        new_task = task_snap

    new_intent = prev_intent_snap
    intent_snap = leader_intent_snapshot(getattr(loader, "leader_intent", None))
    if intent_snap is not None and snapshot_changed(prev_intent_snap, intent_snap):
        assign = ef_py.WorldLeaderIntentMaintainedAssignment()
        project_world_leader_intent_maintained_assignment(
            assign,
            world_index=int(world_index),
            entity_id=int(entity_id),
            compatibility_intent_shell=loader.leader_intent,
        )
        intent_assignments.append(assign)
        new_intent = intent_snap

    new_report = prev_report_snap
    report_snap = pilot_report_snapshot(getattr(loader, "pilot_report", None))
    if report_snap is not None and snapshot_changed(prev_report_snap, report_snap):
        assign = ef_py.WorldPilotReportMaintainedAssignment()
        project_world_pilot_report_maintained_assignment(
            assign,
            world_index=int(world_index),
            entity_id=int(entity_id),
            compatibility_report_shell=loader.pilot_report,
        )
        report_assignments.append(assign)
        new_report = report_snap

    return new_mission, new_task, new_intent, new_report


def submit_command_chain_assignments(
    runtime_adapter: Any,
    mission_assignments: list,
    task_assignments: list,
    intent_assignments: list,
    report_assignments: list,
) -> None:
    """Batch-submit accumulated command chain assignments."""
    if mission_assignments:
        runtime_adapter.set_mission_commands_maintained_batch(mission_assignments)
    if task_assignments:
        runtime_adapter.set_task_orders_maintained_batch(task_assignments)
    if intent_assignments:
        runtime_adapter.set_leader_intents_maintained_batch(intent_assignments)
    if report_assignments:
        runtime_adapter.set_pilot_reports_maintained_batch(report_assignments)


# ---------------------------------------------------------------------------
# Parameterised-shared: observation dict assembly
# ---------------------------------------------------------------------------

_float32_view = np.float32


def _as_f32(value: Any) -> np.ndarray:
    return np.asarray(value, dtype=_float32_view)


def assemble_observation_dict(
    *,
    inst_vec: np.ndarray,
    contacts: np.ndarray,
    rwr: np.ndarray,
    miss_vec: np.ndarray,
    max_contacts: int,
    max_rwr: int,
    include_proprio: bool,
    last_action: np.ndarray | None,
    action_dim: int,
) -> dict[str, np.ndarray]:
    """Build the core observation dictionary shared across modes.

    Visual and temporal-history attachment remain caller-owned because
    their state-accessor patterns differ between execution and cooperative.
    """
    obs: dict[str, np.ndarray] = {
        "instruments": inst_vec,
        "contacts": _as_f32(contacts).reshape(int(max_contacts), 5),
        "rwr": _as_f32(rwr).reshape(int(max_rwr), 4),
        "mission": miss_vec,
    }
    if include_proprio:
        if last_action is None:
            obs["proprio"] = np.zeros((int(action_dim),), dtype=np.float32)
        else:
            obs["proprio"] = _as_f32(last_action).reshape(-1)
    return obs


__all__ = [
    "assemble_observation_dict",
    "batch_observation_runtime_base_check",
    "diff_single_entity_command_chain",
    "normalize_seed",
    "resolve_batch_observation_backend_mode",
    "resolve_batch_visual_backend_mode",
    "save_obs_to_buffer",
    "submit_command_chain_assignments",
]
