from __future__ import annotations

from typing import Any
import time

import ef_py
import numpy as np

from gym_envs.universal_env import (
    build_pilot_action,
    is_air_combat_hybrid_action_mode,
    normalize_action,
)
from python.rl.tasking.bridge import resolve_loader_time_step

from .runtime_support import compute_loader_step_outcome
from ._vec_env_support import (
    _execution_instrument_vector,
    _post_launch_reward_from_breakdown,
    _scenario_stage,
)

_compute_loader_step_outcome = compute_loader_step_outcome


class _WorldBatchVecEnvAirCombatPostLaunchMixin:
    def _air_combat_post_launch_assessment_limit_steps(self, env_idx: int) -> int:
        handle = self._handles[int(env_idx)]
        dt = float(resolve_loader_time_step(handle.loader, default=self._world_time_step(env_idx)))
        limits: list[int] = []
        if self.air_combat_post_launch_assessment_max_steps > 0:
            limits.append(int(self.air_combat_post_launch_assessment_max_steps))
        if self.air_combat_post_launch_assessment_timeout_s > 0.0 and dt > 1.0e-9:
            limits.append(max(1, int(np.ceil(self.air_combat_post_launch_assessment_timeout_s / dt))))
        remaining = max(0, int(handle.max_steps) - int(handle.steps))
        if remaining > 0:
            limits.append(int(remaining))
        if not limits:
            return 0
        return max(0, min(limits))

    def _air_combat_post_launch_assessment_should_run(
        self,
        env_idx: int,
        *,
        terminated: bool,
        truncated: bool,
    ) -> bool:
        if not self.air_combat_post_launch_assessment_enabled:
            return False
        if self.execution_episode_controller_mainline:
            return False
        if not is_air_combat_hybrid_action_mode(self.action_mode):
            return False
        if bool(terminated or truncated):
            return False
        handle = self._handles[int(env_idx)]
        stage = _scenario_stage(handle.loader)
        if self.air_combat_post_launch_assessment_stages and stage not in self.air_combat_post_launch_assessment_stages:
            return False
        event_info = getattr(handle.loader, "_last_air_combat_event_action_info", None)
        if not (isinstance(event_info, dict) and bool(event_info.get("release_executed", False))):
            return False
        return self._air_combat_post_launch_assessment_limit_steps(env_idx) > 0

    def _air_combat_post_launch_assessment_action(self) -> np.ndarray:
        action = np.zeros(tuple(self.action_space.shape), dtype=np.float32)
        if action.size > 3:
            action[3] = float(self.air_combat_post_launch_assessment_blue_throttle)
        if is_air_combat_hybrid_action_mode(self.action_mode):
            if action.size > 6:
                action[6] = 1.0
            if action.size > 8:
                action[8] = 0.0
            if action.size > 9:
                action[9] = 0.0
            if action.size > 10:
                action[10] = 0.0
            if action.size > 11:
                action[11] = 0.0
        elif self.action_mode == "full":
            if action.size > 9:
                action[9] = 1.0
            if action.size > 13:
                action[13] = 0.0
            if action.size > 14:
                action[14] = 0.0
            if action.size > 15:
                action[15] = 0.0
            if action.size > 16:
                action[16] = 0.0
        return normalize_action(action, action_space=self.action_space, action_mode=self.action_mode)

    def _run_air_combat_post_launch_assessment(
        self,
        env_idx: int,
        *,
        obs: dict[str, np.ndarray],
        reward: float,
        terminated: bool,
        truncated: bool,
        mission_status: Any,
    ) -> tuple[dict[str, np.ndarray], float, bool, bool, Any, dict[str, Any]]:
        handle = self._handles[int(env_idx)]
        limit_steps = self._air_combat_post_launch_assessment_limit_steps(env_idx)
        if limit_steps <= 0:
            return obs, float(reward), bool(terminated), bool(truncated), mission_status, {}

        managed_action = self._air_combat_post_launch_assessment_action()
        gamma = float(self.air_combat_post_launch_assessment_gamma)
        discount = gamma
        discounted_extra_reward = 0.0
        undiscounted_extra_reward = 0.0
        steps_run = 0
        last_reason = ""
        final_status = mission_status
        final_terminated = bool(terminated)
        final_truncated = bool(truncated)
        final_obs = obs
        assessment_t0 = time.perf_counter()

        for _ in range(int(limit_steps)):
            if final_terminated or final_truncated:
                break

            inst_now = handle.last_inst if self.action_mode != "full" else None
            assignment = ef_py.WorldPilotActionAssignment()
            assignment.world_index = int(env_idx)
            assignment.entity_id = int(handle.agent_id)
            assignment.action = build_pilot_action(
                managed_action,
                action_mode=self.action_mode,
                inst_now=inst_now,
            )
            handle.last_action = managed_action.astype(np.float32, copy=True)
            handle.loader._last_action_mode = str(self.action_mode)
            handle.loader._last_effective_action = handle.last_action.astype(np.float32, copy=True)

            self._set_pilot_actions_batch([assignment])
            self._step_runtime_worlds([int(env_idx)])

            _target_indices, truth_list, inst_list = self._read_truth_and_inst_batch([int(env_idx)])
            if not truth_list or not inst_list:
                break
            handle.steps += 1
            handle.loader.steps = int(handle.steps)
            handle.last_truth = truth_list[0]
            handle.last_inst = inst_list[0]

            sim_time = float(handle.steps) * float(
                resolve_loader_time_step(handle.loader, default=self._world_time_step(env_idx))
            )
            handle.loader.update_behaviors(
                sim_time,
                truth=handle.last_truth,
                inst=handle.last_inst,
                sync_to_kernel=False,
            )
            self._sync_command_chain_batch([int(env_idx)])

            inst_vec = _execution_instrument_vector(
                handle.loader,
                handle.last_truth,
                handle.last_inst,
                max_contacts=int(self.max_contacts),
                max_rwr=int(self.max_rwr),
                own_ship_field_reader=self._observation_own_ship_field_reader,
                observation_view_spec=self._runtime_adapter.typed_observation_view_spec,
            )
            reward_obs = {"instruments": inst_vec}
            step_reward, step_terminated, step_truncated, step_status = _compute_loader_step_outcome(
                handle.loader,
                obs=reward_obs,
                steps=handle.steps,
                max_steps=handle.max_steps,
                truth=handle.last_truth,
                inst_state=handle.last_inst,
                step_evaluation=None,
            )
            consequence_reward = _post_launch_reward_from_breakdown(
                getattr(handle.loader, "last_reward_breakdown", None)
            )
            undiscounted_extra_reward += float(consequence_reward)
            discounted_extra_reward += float(discount) * float(consequence_reward)
            discount *= gamma
            steps_run += 1
            final_status = step_status
            final_terminated = bool(step_terminated)
            final_truncated = bool(step_truncated)
            last_reason = str(getattr(handle.loader, "last_termination_reason", "") or "")

        if not bool(final_terminated or final_truncated):
            final_terminated = True
            final_truncated = False
            last_reason = "post_launch_assessment_timeout"

        final_obs = self._build_observation_from_cached_state(int(env_idx))
        elapsed_s = float(steps_run) * float(
            resolve_loader_time_step(handle.loader, default=self._world_time_step(env_idx))
        )
        info = {
            "post_launch_assessment": True,
            "post_launch_assessment_steps": int(steps_run),
            "post_launch_assessment_sim_time_s": float(elapsed_s),
            "post_launch_assessment_discounted_reward": float(discounted_extra_reward),
            "post_launch_assessment_undiscounted_reward": float(undiscounted_extra_reward),
            "post_launch_assessment_gamma": float(gamma),
            "post_launch_assessment_reward_mode": "combat_consequence_terms",
            "post_launch_assessment_wall_time_ms": float((time.perf_counter() - assessment_t0) * 1000.0),
        }
        if last_reason:
            info["post_launch_assessment_terminal_reason"] = str(last_reason)
        return (
            final_obs,
            float(reward) + float(discounted_extra_reward),
            bool(final_terminated),
            bool(final_truncated),
            final_status,
            info,
        )



__all__ = ["_WorldBatchVecEnvAirCombatPostLaunchMixin"]
