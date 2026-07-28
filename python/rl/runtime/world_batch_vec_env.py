"""Compatibility-only re-export shell for the historical ``world_batch_vec_env`` module path.

The implementation lives in :mod:`python.rl.runtime.world_batch.vec_env` (plus its
``_observation_mixin`` collaborator for ``compute_execution_observation_batch``). All
maintained callers under ``python/``, ``gym_envs/``, ``tools/`` (non-archive), and
``tests/`` (non-archive) import the canonical modules directly; see
``tests/architecture/runtime_facade/test_world_batch_owner_imports.py``.

This module is retained only so external/legacy scripts that still spell
``python.rl.runtime.world_batch_vec_env`` keep working. It intentionally does not
override module attribute assignment to forward monkeypatches anymore: the
maintained test suite now patches the owning implementation modules directly, so
the historical mutable-forwarding compat-module machinery has no remaining
consumer and has been removed.
"""

from __future__ import annotations

from python.rl.runtime.world_batch._observation_mixin import compute_execution_observation_batch
from python.rl.runtime.world_batch.command_chain_cache import (
    project_world_leader_intent_maintained_assignment,
    project_world_mission_command_maintained_assignment,
    project_world_pilot_report_maintained_assignment,
    project_world_task_order_maintained_assignment,
)
from python.rl.runtime.world_batch.vec_env import (
    WorldBatchVecEnv,
    _BatchWorldHandle,
    _RuntimeFacadeAdapter,
    _as_stage_set,
    _build_loader_step_info,
    _compute_loader_step_outcome,
    _copy_obs,
    _execution_instrument_vector,
    _float32_view,
    _normalize_batch_observation_backend,
    _normalize_batch_visual_backend,
    _normalize_flight_shaping_backend,
    _normalize_observation_return_mode,
    _parse_reward_terms_json,
    _post_launch_reward_from_breakdown,
    _scenario_stage,
    _step_info_products_to_info_fields,
    build_compiled_world_layout,
)

__all__ = [
    "WorldBatchVecEnv",
    "_BatchWorldHandle",
    "_RuntimeFacadeAdapter",
    "_as_stage_set",
    "_copy_obs",
    "_execution_instrument_vector",
    "_float32_view",
    "_normalize_batch_observation_backend",
    "_normalize_batch_visual_backend",
    "_normalize_flight_shaping_backend",
    "_normalize_observation_return_mode",
    "_parse_reward_terms_json",
    "_post_launch_reward_from_breakdown",
    "_scenario_stage",
    "_step_info_products_to_info_fields",
    "_build_loader_step_info",
    "_compute_loader_step_outcome",
    "build_compiled_world_layout",
    "compute_execution_observation_batch",
    "project_world_leader_intent_maintained_assignment",
    "project_world_mission_command_maintained_assignment",
    "project_world_pilot_report_maintained_assignment",
    "project_world_task_order_maintained_assignment",
]
