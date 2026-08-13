from __future__ import annotations

from collections import OrderedDict
from collections.abc import Sequence
from copy import deepcopy
from typing import Any

import ef_py
import numpy as np
import time

from gym_envs.universal_env import (
    append_temporal_history,
    attach_temporal_history,
    make_temporal_history_buffer,
    naval_policy_instruments,
    temporal_history_enabled,
)
from python.rl.support.sb3_vec_env_compat import VecEnvObs, dict_to_obs
from python.rl.tasking.bridge import resolve_tasking_profile, tasking_profile_for_loader

from .common import observation_timing_snapshot
from .observation_batching import ExecutionObservationBatch, compute_execution_observation_batch
from ._vec_env_support import _float32_view
from ._shared_ops import assemble_observation_dict


class _WorldBatchVecEnvObservationMixin:
    def _prepare_step_evaluations_batch(
        self,
        target_indices: list[int],
        truth_batch: list,
        inst_batch: list,
        inst_out: np.ndarray,
        ils_batch: np.ndarray,
        mission_inputs_batch: list | None = None,
    ) -> list[dict] | None:
        """Batch preparation of step evaluations using C++ API."""
        if not target_indices:
            return None

        # Check if all loaders support batch mode
        first_loader = self._handles[target_indices[0]].loader
        if not hasattr(first_loader, "_build_step_evaluation_batch_env_state"):
            return None

        config = ef_py.StepEvaluationBatchConfig()
        config.target_altitude_m = float(first_loader.mission_cmd.get("target_altitude", 0.0))
        config.target_speed_mps = float(first_loader.mission_cmd.get("target_speed", 0.0))
        config.target_heading_deg = float(first_loader.mission_cmd.get("target_heading", 0.0))
        config.time_step_s = self._runtime_adapter.get_time_step(target_indices[0])

        # Build env states
        env_states = []
        prepared_entries: list[dict[str, Any] | None] = []
        for batch_idx, env_idx in enumerate(target_indices):
            handle = self._handles[env_idx]
            truth = truth_batch[batch_idx]
            inst_vec = inst_out[batch_idx]
            mission_inputs = mission_inputs_batch[batch_idx] if mission_inputs_batch is not None and batch_idx < len(mission_inputs_batch) else None
            state, prepared = handle.loader._build_step_evaluation_batch_env_state(
                truth=truth,
                inst_obj=inst_batch[batch_idx],
                inst_vec=inst_vec,
                ils_vec=np.asarray(ils_batch[batch_idx], dtype=np.float32),
                steps=int(handle.steps),
                max_steps=int(handle.max_steps),
                mission_obs_mode=self.mission_obs_mode,
                mission_observation_inputs=mission_inputs,
                return_prepared=True,
            )
            env_states.append(state)
            prepared_entries.append(prepared if isinstance(prepared, dict) else None)

        # Call C++ batch API
        runtime_inputs_batch = ef_py.prepare_step_evaluations_batch(config, env_states)

        # Compute execution episode runtime batch
        if hasattr(ef_py, "compute_execution_episode_runtime_batch"):
            frame_products_batch = ef_py.compute_execution_episode_runtime_batch(runtime_inputs_batch)
        else:
            return None

        # Format results
        results = []
        for batch_idx, frame_products in enumerate(frame_products_batch):
            handle = self._handles[target_indices[batch_idx]]
            prepared = prepared_entries[batch_idx] if batch_idx < len(prepared_entries) else None
            result = {
                "frame_products": frame_products,
            }
            if isinstance(prepared, dict):
                result = {
                    "truth_obj": truth_batch[batch_idx],
                    "inst_obj": inst_batch[batch_idx],
                    "steps": int(handle.steps),
                    "max_steps": int(handle.max_steps),
                    "mission_obs_mode": "" if self.mission_obs_mode is None else str(self.mission_obs_mode),
                    "frame_products": frame_products,
                    **prepared,
                }
                cache = getattr(handle.loader, "_runtime_eval_cache", None)
                if isinstance(cache, dict):
                    cache["step_evaluation"] = result
            results.append(result)

        return results

    def _build_observations_from_cached_state(
        self,
        indices: Sequence[int] | None = None,
    ) -> list[dict[str, np.ndarray]]:
        target_indices = list(range(self.num_envs)) if indices is None else [int(i) for i in indices]
        if not target_indices:
            return []
        if self.include_visual:
            self._refresh_visual_batch(target_indices)
        backend = self._batch_observation_backend_mode()
        if not self._batch_observation_runtime_available():
            raise RuntimeError("maintained observation batching requires compute_execution_observation_batch_numpy")

        allow_execution_device_export = self._execution_observation_device_export_allowed(target_indices)
        typed_view_spec = self._runtime_adapter.typed_observation_view_spec
        obs_batch_data: ExecutionObservationBatch = compute_execution_observation_batch(
            states=[self._handles[env_idx] for env_idx in target_indices],
            mission_obs_mode=self.mission_obs_mode,
            max_contacts=int(self.max_contacts),
            max_rwr=int(self.max_rwr),
            backend=backend,
            allow_device_export=bool(allow_execution_device_export),
            torch_bridge_enabled=bool(self._policy_torch_bridge_enabled),
            observation_view_spec=typed_view_spec,
            own_ship_field_reader=self._observation_own_ship_field_reader,
        )
        inst_batch = obs_batch_data.inst_batch
        truth_batch = obs_batch_data.truth_batch
        mission_inputs_batch = obs_batch_data.mission_inputs_batch
        ils_batch = obs_batch_data.ils_batch
        inst_out = obs_batch_data.inst_out
        contacts_out = obs_batch_data.contacts_out
        rwr_out = obs_batch_data.rwr_out
        mission_out = obs_batch_data.mission_out
        self._policy_execution_device_view = obs_batch_data.device_view if allow_execution_device_export else None

        # Try batch step evaluation preparation if available
        step_eval_batch = None
        step_eval_prepare_ms = 0.0
        if self.execution_step_batch_prepare and hasattr(ef_py, "prepare_step_evaluations_batch") and len(target_indices) > 0:
            try:
                prep_t0 = time.perf_counter()
                step_eval_batch = self._prepare_step_evaluations_batch(
                    target_indices, truth_batch, inst_batch, inst_out, ils_batch, mission_inputs_batch
                )
                step_eval_prepare_ms = (time.perf_counter() - prep_t0) * 1000.0
            except Exception:
                step_eval_batch = None
        self.last_observation_build_timing = {
            **dict(obs_batch_data.timing),
            "step_eval_prepare_ms": float(step_eval_prepare_ms),
        }

        obs_batch = []
        for batch_idx, env_idx in enumerate(target_indices):
            handle = self._handles[env_idx]
            inst_vec = _float32_view(inst_out[batch_idx])
            contacts = _float32_view(contacts_out[batch_idx]).reshape(int(self.max_contacts), 5)
            rwr = _float32_view(rwr_out[batch_idx]).reshape(int(self.max_rwr), 4)
            if handle.loader._python_owned_mission_observation_mode(self.mission_obs_mode):
                miss_vec = _float32_view(
                    handle.loader.get_mission_observation(
                        self.mission_obs_mode,
                        truth=truth_batch[batch_idx],
                        inst=inst_batch[batch_idx],
                    )
                )
            else:
                miss_vec = _float32_view(mission_out[batch_idx])

            # Use batch result if available, otherwise fall back to per-env
            step_eval = None
            if step_eval_batch is not None and batch_idx < len(step_eval_batch):
                step_eval = step_eval_batch[batch_idx]
            elif hasattr(handle.loader, "_prepare_step_evaluation"):
                try:
                    step_eval = handle.loader._prepare_step_evaluation(
                        truth=truth_batch[batch_idx],
                        inst_obj=inst_batch[batch_idx],
                        inst_vec=inst_vec,
                        ils_vec=_float32_view(ils_batch[batch_idx]),
                        steps=int(handle.steps),
                        max_steps=int(handle.max_steps),
                        mission_obs_mode=self.mission_obs_mode,
                    )
                except Exception:
                    step_eval = None
            if isinstance(step_eval, dict):
                frame_products = step_eval.get("frame_products")
                if (
                    not handle.loader._python_owned_mission_observation_mode(self.mission_obs_mode)
                    and frame_products is not None
                    and bool(getattr(frame_products, "mission_observation_evaluated", False))
                ):
                    miss_vec = _float32_view(frame_products.mission_observation.values)

            policy_inst_vec = (
                naval_policy_instruments(inst_vec)
                if tasking_profile_for_loader(handle.loader) is resolve_tasking_profile("naval")
                else inst_vec
            )
            obs = assemble_observation_dict(
                inst_vec=policy_inst_vec,
                contacts=contacts,
                rwr=rwr,
                miss_vec=miss_vec,
                max_contacts=int(self.max_contacts),
                max_rwr=int(self.max_rwr),
                include_proprio=self.include_proprio,
                last_action=handle.last_action,
                action_dim=int(self.action_space.shape[0]),
            )
            obs_batch.append(self._attach_temporal_history(env_idx, self._attach_visual_observation(env_idx, obs)))
        return obs_batch

    def _observation_timing_snapshot(self) -> dict[str, float]:
        return observation_timing_snapshot(getattr(self, "last_observation_build_timing", None))

    def _attach_visual_observation(self, env_idx: int, obs: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
        if not self.include_visual:
            return obs
        handle = self._handles[env_idx]
        if handle.visual_cache is None:
            self._refresh_visual_batch([env_idx])
        obs["visual"] = np.asarray(handle.visual_cache, dtype=np.float32)
        return obs

    def _attach_temporal_history(self, env_idx: int, obs: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
        if not temporal_history_enabled(self.temporal_history_len):
            return obs
        handle = self._handles[int(env_idx)]
        if handle.temporal_history is None:
            handle.temporal_history = make_temporal_history_buffer(self.temporal_history_len)
        append_temporal_history(
            handle.temporal_history,
            obs,
            history_len=self.temporal_history_len,
            action_dim=int(self.action_space.shape[0]),
        )
        return attach_temporal_history(
            obs,
            handle.temporal_history,
            history_len=self.temporal_history_len,
            action_dim=int(self.action_space.shape[0]),
        )

    def _build_observation_from_cached_state(self, env_idx: int) -> dict[str, np.ndarray]:
        return self._build_observations_from_cached_state([env_idx])[0]

    def _refresh_mission_observation_batch(
        self,
        obs_batch: Sequence[dict[str, np.ndarray]],
        indices: Sequence[int] | None = None,
    ) -> None:
        target_indices = list(range(self.num_envs)) if indices is None else [int(i) for i in indices]
        for env_idx in target_indices:
            handle = self._handles[env_idx]
            if hasattr(handle.loader, "reset_runtime_eval_cache"):
                try:
                    handle.loader.reset_runtime_eval_cache()
                except Exception:
                    pass
            obs_batch[env_idx]["mission"] = np.asarray(
                handle.loader.get_mission_observation(
                    self.mission_obs_mode,
                    truth=handle.last_truth,
                    inst=handle.last_inst,
                ),
                dtype=np.float32,
            )

    def _obs_from_buf(self) -> VecEnvObs:
        if self.observation_return_mode == "view":
            obs_dict = OrderedDict((key, value) for key, value in self.buf_obs.items())
            return dict_to_obs(self.observation_space, obs_dict)
        return dict_to_obs(self.observation_space, deepcopy(self.buf_obs))



__all__ = ["_WorldBatchVecEnvObservationMixin"]
