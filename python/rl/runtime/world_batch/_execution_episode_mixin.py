from __future__ import annotations

from collections.abc import Sequence
from typing import Any
import time

import ef_py
import numpy as np

from gym_envs.scenario_loader import ScenarioLoader

from .common import parse_reward_terms_json, step_info_products_to_info_fields
from ._vec_env_support import _execution_instrument_vector

_parse_reward_terms_json = parse_reward_terms_json
_step_info_products_to_info_fields = step_info_products_to_info_fields


class _WorldBatchVecEnvExecutionEpisodeMixin:
    def execution_episode_ready(self, world_index: int) -> bool:
        return bool(self._runtime_adapter.execution_episode_ready(int(world_index)))

    def export_execution_episode_states(self, refs: Sequence[Any]) -> list[Any]:
        return self._runtime_adapter.export_execution_episode_states(refs)

    def export_execution_episode_state(self, env_idx: int) -> Any:
        _target_indices, refs = self._build_refs([int(env_idx)])
        return self.export_execution_episode_states(refs)[0]

    @staticmethod
    def _execution_episode_shadow_state_summary(state) -> dict[str, Any]:
        return {
            "step_count": int(getattr(state, "step_count", 0)),
            "waypoint_index": int(getattr(state, "waypoint_index", 0)),
            "has_waypoint_prev_dist_m": bool(getattr(state, "has_waypoint_prev_dist_m", False)),
            "waypoint_prev_dist_m": float(getattr(state, "waypoint_prev_dist_m", 0.0)),
            "prev_altitude_m": float(getattr(state, "prev_altitude_m", 0.0)),
            "prev_ias_mps": float(getattr(state, "prev_ias_mps", 0.0)),
            "liftoff_awarded": bool(getattr(state, "liftoff_awarded", False)),
            "gear_bonus_awarded": bool(getattr(state, "gear_bonus_awarded", False)),
            "off_runway_steps": int(getattr(state, "off_runway_steps", 0)),
            "has_approach_prev_dme_m": bool(getattr(state, "has_approach_prev_dme_m", False)),
            "approach_prev_dme_m": float(getattr(state, "approach_prev_dme_m", 0.0)),
            "has_approach_prev_loc_abs": bool(getattr(state, "has_approach_prev_loc_abs", False)),
            "approach_prev_loc_abs": float(getattr(state, "approach_prev_loc_abs", 0.0)),
            "has_approach_prev_gs_abs": bool(getattr(state, "has_approach_prev_gs_abs", False)),
            "approach_prev_gs_abs": float(getattr(state, "approach_prev_gs_abs", 0.0)),
            "last_termination_reason": str(getattr(state, "last_termination_reason", "")),
            "last_reward_total": float(getattr(state, "last_reward_total", 0.0)),
        }

    def _execution_episode_controller_runtime_ready(self, env_idx: int) -> bool:
        return self.execution_episode_ready(env_idx)

    def _set_pilot_actions_batch(self, assignments: Sequence[Any]) -> None:
        self._runtime_adapter.set_pilot_actions_batch(assignments)

    def _step_runtime_batch(self) -> None:
        self._runtime_adapter.step_batch()

    def _prime_execution_episode_controller_runtime_batch(
        self,
        refs: Sequence[Any],
        states: Sequence[Any],
    ) -> None:
        self._runtime_adapter.prime_execution_episode_batch(refs, states)

    def _step_execution_episode_controller_mainline_requests(self, requests: Sequence[Any]) -> Any:
        batch_request = ef_py.ExecutionBatchStepRequest()
        batch_request.step_requests = list(requests)
        batch_request.include_agent_observations = True
        batch_request.include_instrument_states = True
        return self._runtime_adapter.step_execution_batch(batch_request)

    def _consume_execution_episode_controller_mainline_observation_packet(
        self,
        step_batch_result: Any,
        result_env_indices: Sequence[int],
    ) -> bool:
        packet = getattr(step_batch_result, "observation_packet", None)
        if packet is None:
            return False
        refs = list(getattr(packet, "refs", []) or [])
        truth_list = list(getattr(packet, "agent_observations", []) or [])
        inst_list = list(getattr(packet, "instrument_states", []) or [])
        if (
            len(refs) != len(result_env_indices)
            or len(truth_list) != len(result_env_indices)
            or len(inst_list) != len(result_env_indices)
        ):
            return False
        for batch_idx, env_idx in enumerate(result_env_indices):
            handle = self._handles[int(env_idx)]
            agent_id = getattr(handle, "agent_id", None)
            ref = refs[batch_idx]
            try:
                ref_world_index = int(getattr(ref, "world_index"))
                ref_entity_id = int(getattr(ref, "entity_id"))
            except Exception:
                return False
            if agent_id is None or ref_world_index != int(env_idx) or ref_entity_id != int(agent_id):
                return False
        for batch_idx, env_idx in enumerate(result_env_indices):
            handle = self._handles[int(env_idx)]
            handle.last_truth = truth_list[batch_idx]
            handle.last_inst = inst_list[batch_idx]
        return True

    def _step_execution_episode_controller_shadow_requests(self, requests: Sequence[Any]) -> list[Any]:
        return self._runtime_adapter.step_execution_products_batch(requests)

    def _export_execution_episode_controller_states(self, refs: Sequence[Any]) -> list[Any]:
        return self.export_execution_episode_states(refs)

    def _sync_execution_episode_controller_runtime_state(self, env_idx: int) -> None:
        if not (self.execution_episode_controller_shadow_compare or self.execution_episode_controller_mainline):
            return
        handle = self._handles[env_idx]
        handle.loader.steps = int(handle.steps)
        _target_indices, refs = self._build_refs([env_idx])
        self._prime_execution_episode_controller_runtime_batch(
            refs,
            [handle.loader.build_execution_episode_state()],
        )
        handle.execution_episode_controller_config = handle.loader._build_execution_episode_controller_shadow_config()

    def _compare_execution_episode_controller_shadow_batch(
        self,
        obs_batch: Sequence[dict[str, np.ndarray]],
    ) -> list[dict[str, Any] | None]:
        if not self.execution_episode_controller_shadow_compare:
            return [None] * self.num_envs

        for env_idx in range(self.num_envs):
            if not self._execution_episode_controller_runtime_ready(env_idx):
                self._sync_execution_episode_controller_runtime_state(env_idx)

        _target_indices, refs = self._build_refs()

        requests: list[Any] = []
        request_refs: list[Any] = []
        request_metadata: list[tuple[int, ScenarioLoader, dict[str, Any] | None, Any]] = []
        reports: list[dict[str, Any] | None] = [None] * self.num_envs

        for env_idx, _obs in enumerate(obs_batch):
            handle = self._handles[env_idx]
            loader = handle.loader
            cache = getattr(loader, "_runtime_eval_cache", None)
            step_eval = cache.get("step_evaluation") if isinstance(cache, dict) else None
            inst_vec = _execution_instrument_vector(
                loader,
                handle.last_truth,
                handle.last_inst,
                max_contacts=self.max_contacts,
                max_rwr=self.max_rwr,
                own_ship_field_reader=self._observation_own_ship_field_reader,
                observation_view_spec=self._runtime_adapter.typed_observation_view_spec,
            )
            ils_vec = (
                np.asarray(inst_vec[-4:], dtype=np.float32)
                if inst_vec.size >= 4
                else np.zeros((4,), dtype=np.float32)
            )
            if not isinstance(step_eval, dict):
                step_eval = loader._prepare_step_evaluation(
                    truth=handle.last_truth,
                    inst_obj=handle.last_inst,
                    inst_vec=inst_vec,
                    ils_vec=ils_vec,
                    steps=int(handle.steps),
                    max_steps=int(handle.max_steps),
                    mission_obs_mode=self.mission_obs_mode,
                )

            reference_products = step_eval.get("frame_products") if isinstance(step_eval, dict) else None
            if reference_products is None:
                continue

            mission_inputs = step_eval.get("mission_observation_inputs") if isinstance(step_eval, dict) else None
            if isinstance(step_eval, dict):
                ils_vec = np.asarray(
                    [
                        float(step_eval.get("ils_valid", ils_vec[0] if ils_vec.size > 0 else 0.0)),
                        float(step_eval.get("ils_loc", ils_vec[1] if ils_vec.size > 1 else 0.0)),
                        float(step_eval.get("ils_gs", ils_vec[2] if ils_vec.size > 2 else 0.0)),
                        float(step_eval.get("ils_dme", ils_vec[3] if ils_vec.size > 3 else 0.0)),
                    ],
                    dtype=np.float32,
                )

            batch_state = loader._build_step_evaluation_batch_env_state(
                truth=handle.last_truth,
                inst_obj=handle.last_inst,
                inst_vec=inst_vec,
                ils_vec=ils_vec,
                steps=int(handle.steps),
                max_steps=int(handle.max_steps),
                mission_obs_mode=self.mission_obs_mode,
                mission_observation_inputs=mission_inputs,
            )
            batch_state.has_episode_state = False

            config = handle.execution_episode_controller_config
            if config is None:
                config = loader._build_execution_episode_controller_shadow_config()
                handle.execution_episode_controller_config = config

            request = ef_py.WorldExecutionEpisodeStepRequest()
            request.world_index = int(env_idx)
            request.entity_id = int(handle.agent_id)
            request.config = config
            request.env_state = batch_state
            requests.append(request)
            request_refs.append(refs[env_idx])
            request_metadata.append((env_idx, loader, cache if isinstance(cache, dict) else None, reference_products))

        if not requests:
            return reports

        shadow_products_batch = self._step_execution_episode_controller_shadow_requests(requests)
        post_step_states = self._export_execution_episode_controller_states(request_refs)
        for (env_idx, loader, cache, reference_products), shadow_products, shadow_state in zip(
            request_metadata,
            shadow_products_batch,
            post_step_states,
            strict=True,
        ):
            full_report = {
                "reference_frame_products": reference_products,
                "shadow_frame_products": shadow_products,
                "shadow_state": shadow_state,
                "advance_state": True,
                "comparison": loader._compare_execution_episode_runtime_products(
                    reference_products,
                    shadow_products,
                ),
            }
            report = {
                "advance_state": True,
                "comparison": dict(full_report["comparison"]),
                "shadow_state": self._execution_episode_shadow_state_summary(shadow_state),
                "shadow_reward_total": float(getattr(shadow_products, "compiled_reward_total", 0.0)),
                "shadow_terminated": bool(getattr(shadow_products, "terminated", False)),
                "shadow_reason_code": str(getattr(shadow_products, "final_reason_code", "")),
            }
            if isinstance(cache, dict):
                cache["execution_episode_controller_shadow"] = full_report
                cache["execution_episode_controller_shadow_summary"] = report
            reports[env_idx] = report
        return reports

    def _step_execution_episode_controller_mainline_batch(
        self,
        obs_batch: Sequence[dict[str, np.ndarray]],
    ) -> list[dict[str, Any] | None]:
        if not self.execution_episode_controller_mainline:
            self._execution_episode_controller_mainline_timing = {}
            return [None] * self.num_envs

        timing_enabled = self.collect_step_timing
        for env_idx in range(self.num_envs):
            if not self._execution_episode_controller_runtime_ready(env_idx):
                self._sync_execution_episode_controller_runtime_state(env_idx)

        request_build_t0 = time.perf_counter() if timing_enabled else 0.0
        requests: list[Any] = []
        request_metadata: list[tuple[int, Any]] = []
        results: list[dict[str, Any] | None] = [None] * self.num_envs

        for env_idx, _obs in enumerate(obs_batch):
            handle = self._handles[env_idx]
            loader = handle.loader
            inst_vec = _execution_instrument_vector(
                loader,
                handle.last_truth,
                handle.last_inst,
                max_contacts=self.max_contacts,
                max_rwr=self.max_rwr,
                own_ship_field_reader=self._observation_own_ship_field_reader,
                observation_view_spec=self._runtime_adapter.typed_observation_view_spec,
            )
            ils_vec = np.asarray(inst_vec[-4:], dtype=np.float32) if inst_vec.size >= 4 else np.zeros((4,), dtype=np.float32)
            cache = getattr(loader, "_runtime_eval_cache", None)
            cached_step_eval = cache.get("step_evaluation") if isinstance(cache, dict) else None
            batch_state, prepared = loader._build_step_evaluation_batch_env_state(
                truth=handle.last_truth,
                inst_obj=handle.last_inst,
                inst_vec=inst_vec,
                ils_vec=ils_vec,
                steps=int(handle.steps),
                max_steps=int(handle.max_steps),
                mission_obs_mode=None,
                mission_observation_inputs=None,
                include_episode_state=False,
                return_prepared=True,
                prepared_entry=cached_step_eval if isinstance(cached_step_eval, dict) else None,
            )
            step_eval = prepared if isinstance(prepared, dict) else {}
            try:
                control_mission_inputs = loader._build_mission_observation_runtime_inputs(
                    "nav_v2",
                    truth=handle.last_truth,
                    inst=handle.last_inst,
                )
                batch_state.has_mission_observation = True
                batch_state.mission_observation = control_mission_inputs
            except Exception:
                pass
            batch_state.has_episode_state = False

            config = handle.execution_episode_controller_config
            if config is None:
                config = loader._build_execution_episode_controller_shadow_config()
                handle.execution_episode_controller_config = config

            request = ef_py.WorldExecutionEpisodeStepRequest()
            request.world_index = int(env_idx)
            request.entity_id = int(handle.agent_id)
            request.config = config
            request.env_state = batch_state
            requests.append(request)
            request_metadata.append((env_idx, step_eval))

        request_build_ms = (time.perf_counter() - request_build_t0) * 1000.0 if timing_enabled else 0.0

        if not requests:
            self._execution_episode_controller_mainline_timing = {}
            return results

        runtime_step_t0 = time.perf_counter() if timing_enabled else 0.0
        step_batch_result = self._step_execution_episode_controller_mainline_requests(requests)
        runtime_step_ms = (time.perf_counter() - runtime_step_t0) * 1000.0 if timing_enabled else 0.0
        self._consume_execution_episode_controller_mainline_observation_packet(
            step_batch_result,
            [env_idx for env_idx, _step_eval in request_metadata],
        )
        step_results_batch = list(getattr(step_batch_result, "step_results", []))
        execution_episode_states_batch = list(
            getattr(step_batch_result, "execution_episode_states", [])
        )
        rewards_batch = list(getattr(step_batch_result, "rewards", []))
        terminated_batch = list(getattr(step_batch_result, "terminated", []))
        truncated_batch = list(getattr(step_batch_result, "truncated", []))
        status_vectors_batch = list(getattr(step_batch_result, "status_vectors", []))
        termination_reasons_batch = list(getattr(step_batch_result, "termination_reasons", []))
        reward_breakdown_jsons_batch = list(getattr(step_batch_result, "reward_breakdown_jsons", []))
        step_infos_batch = list(getattr(step_batch_result, "step_infos", []))
        step_info_valid_flags = list(getattr(step_batch_result, "step_info_valid_flags", []))
        controller_state_changed_flags = list(
            getattr(step_batch_result, "controller_state_changed_flags", [])
        )
        mirror_ms = 0.0
        for result_idx, ((env_idx, _step_eval), step_result) in enumerate(zip(
            request_metadata,
            step_results_batch,
            strict=True,
        )):
            handle = self._handles[env_idx]
            mirror_t0 = time.perf_counter() if timing_enabled else 0.0
            controller_state = (
                execution_episode_states_batch[result_idx]
                if result_idx < len(execution_episode_states_batch)
                else step_result.controller_state
            )
            structural_state_changed = (
                bool(controller_state_changed_flags[result_idx])
                if result_idx < len(controller_state_changed_flags)
                else bool(getattr(step_result, "structural_state_changed", False))
            )
            if structural_state_changed:
                handle.loader.apply_execution_episode_state(controller_state)
            else:
                handle.loader.apply_execution_episode_runtime_fields(
                    controller_state,
                    include_navigation_state=True,
                    include_navigation_structure=False,
                )
            if timing_enabled:
                mirror_ms += (time.perf_counter() - mirror_t0) * 1000.0
            status_vector = (
                status_vectors_batch[result_idx]
                if result_idx < len(status_vectors_batch)
                else [
                    float(getattr(step_result, "status0", 0.0)),
                    float(getattr(step_result, "status1", 0.0)),
                    float(getattr(step_result, "status2", 0.0)),
                    float(getattr(step_result, "status3", 0.0)),
                ]
            )
            results[env_idx] = {
                "reward": float(rewards_batch[result_idx]) if result_idx < len(rewards_batch) else float(getattr(step_result, "reward_total", 0.0)),
                "terminated": bool(terminated_batch[result_idx]) if result_idx < len(terminated_batch) else bool(getattr(step_result, "terminated", False)),
                "truncated": bool(truncated_batch[result_idx]) if result_idx < len(truncated_batch) else bool(getattr(step_result, "truncated", False)),
                "mission_status": [float(value) for value in status_vector],
                "termination_reason": (
                    str(termination_reasons_batch[result_idx])
                    if result_idx < len(termination_reasons_batch)
                    else str(getattr(controller_state, "last_termination_reason", "") or "")
                ),
                "reward_terms": (
                    _parse_reward_terms_json(reward_breakdown_jsons_batch[result_idx])
                    if result_idx < len(reward_breakdown_jsons_batch)
                    else _parse_reward_terms_json(
                        str(getattr(controller_state, "last_reward_breakdown_json", "") or "")
                    )
                ),
                "step_info_fields": (
                    _step_info_products_to_info_fields(step_infos_batch[result_idx], loader=handle.loader)
                    if (
                        result_idx < len(step_infos_batch)
                        and result_idx < len(step_info_valid_flags)
                        and bool(step_info_valid_flags[result_idx])
                    )
                    else {}
                ),
            }
        if timing_enabled:
            self._execution_episode_controller_mainline_timing = {
                "execution_episode_controller_mainline_pre_export_ms": 0.0,
                "execution_episode_controller_mainline_request_build_ms": float(request_build_ms),
                "execution_episode_controller_mainline_runtime_step_ms": float(runtime_step_ms),
                "execution_episode_controller_mainline_post_export_ms": 0.0,
                "execution_episode_controller_mainline_loader_consume_ms": float(mirror_ms),
                "execution_episode_controller_mainline_loader_mirror_ms": float(mirror_ms),
                "execution_episode_controller_mainline_reprime_ms": 0.0,
            }
        else:
            self._execution_episode_controller_mainline_timing = {}
        return results



__all__ = ["_WorldBatchVecEnvExecutionEpisodeMixin"]
