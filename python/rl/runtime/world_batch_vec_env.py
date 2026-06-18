from __future__ import annotations

import sys
import types

import python.rl.runtime.world_batch._observation_mixin as _observation_mixin_impl
import python.rl.runtime.world_batch.vec_env as _vec_env_impl
from python.rl.runtime.world_batch.vec_env import (
    WorldBatchVecEnv,
    _BatchWorldHandle,
    _RuntimeFacadeAdapter,
    _as_stage_set,
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
    project_world_leader_intent_maintained_assignment,
    project_world_mission_command_maintained_assignment,
    project_world_pilot_report_maintained_assignment,
    project_world_task_order_maintained_assignment,
)

_build_loader_step_info = _vec_env_impl._build_loader_step_info
_compute_loader_step_outcome = _vec_env_impl._compute_loader_step_outcome
compute_execution_observation_batch = _observation_mixin_impl.compute_execution_observation_batch

_FORWARDED_MUTABLE_EXPORTS = {
    "_build_loader_step_info": _vec_env_impl,
    "_compute_loader_step_outcome": _vec_env_impl,
    "compute_execution_observation_batch": _observation_mixin_impl,
    "project_world_leader_intent_maintained_assignment": _vec_env_impl,
    "project_world_mission_command_maintained_assignment": _vec_env_impl,
    "project_world_pilot_report_maintained_assignment": _vec_env_impl,
    "project_world_task_order_maintained_assignment": _vec_env_impl,
}


class _WorldBatchVecEnvCompatModule(types.ModuleType):
    def __setattr__(self, name: str, value):
        target = _FORWARDED_MUTABLE_EXPORTS.get(name)
        if target is not None:
            setattr(target, name, value)
        super().__setattr__(name, value)


sys.modules[__name__].__class__ = _WorldBatchVecEnvCompatModule

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
