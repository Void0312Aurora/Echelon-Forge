from __future__ import annotations

from collections import OrderedDict
from collections.abc import Sequence
from copy import deepcopy
from typing import Any
import os
import time
import warnings

import ef_py
import gymnasium as gym
import numpy as np

try:
    import torch
except Exception:  # pragma: no cover - training envs are expected to have torch
    torch = None

from gym_envs.scenario_loader import (
    ScenarioLoader,
    normalize_execution_step_runtime_mode,
)
from gym_envs.universal_env import (
    add_air_combat_event_action_info,
    air_combat_hybrid_effective_action,
    apply_air_combat_event_action_gate,
    apply_naval_station_action,
    bind_naval_station_eval_reference,
    build_pilot_action,
    build_step_info_minimal,
    finalize_air_combat_event_action_info,
    is_air_combat_hybrid_action_mode,
    is_naval_station_action_mode,
    make_action_space,
    make_observation_space,
    make_temporal_history_buffer,
    naval_station_action_command,
    normalize_action,
    reset_air_combat_event_action_state,
    reset_naval_station_action_state,
    validate_naval_action_mode_for_loader,
)
from python.rl.control.wrappers import MultiTimescaleActionController
from python.rl.support.sb3_vec_env_compat import (
    VecEnv,
    VecEnvIndices,
    VecEnvObs,
    VecEnvStepReturn,
    obs_space_info,
)
from python.rl.tasking.bridge import build_kernel_mission_command, resolve_loader_time_step
from python.scenario.runtime import (
    BatchWorldApplyBuffer,
    build_compiled_world_layout,
    load_compiled_scenario_for_setup_target,
)
from python.scenario.compiler import ScenarioCompiler

from .adapter import RuntimeFacadeAdapter
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
from .common import (
    copy_obs,
    parse_reward_terms_json,
    step_info_products_to_info_fields,
)
from .normalize import (
    normalize_batch_observation_backend,
    normalize_batch_visual_backend,
    normalize_flight_shaping_backend,
    normalize_observation_return_mode,
)
from .runtime_support import build_loader_step_info, compute_loader_step_outcome
from .state import BatchWorldHandle
from ._air_combat_post_launch_mixin import _WorldBatchVecEnvAirCombatPostLaunchMixin
from ._execution_episode_mixin import _WorldBatchVecEnvExecutionEpisodeMixin
from ._observation_mixin import _WorldBatchVecEnvObservationMixin
from ._vec_env_support import (
    _as_stage_set,
    _execution_instrument_vector,
    _float32_view,
    _post_launch_reward_from_breakdown,
    _scenario_stage,
)
from ._visual_backend_mixin import _WorldBatchVecEnvVisualBackendMixin

_copy_obs = copy_obs
_parse_reward_terms_json = parse_reward_terms_json
_step_info_products_to_info_fields = step_info_products_to_info_fields
_normalize_batch_observation_backend = normalize_batch_observation_backend
_normalize_batch_visual_backend = normalize_batch_visual_backend
_normalize_flight_shaping_backend = normalize_flight_shaping_backend
_normalize_observation_return_mode = normalize_observation_return_mode
_BatchWorldHandle = BatchWorldHandle
_RuntimeFacadeAdapter = RuntimeFacadeAdapter
_build_loader_step_info = build_loader_step_info
_compute_loader_step_outcome = compute_loader_step_outcome


class WorldBatchVecEnv(
    _WorldBatchVecEnvExecutionEpisodeMixin,
    _WorldBatchVecEnvAirCombatPostLaunchMixin,
    _WorldBatchVecEnvObservationMixin,
    _WorldBatchVecEnvVisualBackendMixin,
    VecEnv,
):
    """
    Single-process execution-layer VecEnv backed by `ef_py.RuntimeFacade`.

    This is the maintained execution-layer batch adapter for the runtime facade.
    It keeps execution policy rollouts on one process and uses facade-shaped
    C++ batch stepping/reads across worlds. Temporary low-level runtime access is
    centralized in `_RuntimeFacadeAdapter` for compatibility-only paths.
    """

    def __init__(
        self,
        *,
        scenario_path: str,
        n_envs: int,
        render_mode: str | None = None,
        include_visual: bool = False,
        include_proprio: bool = False,
        action_mode: str = "full",
        mission_obs_mode: str = "basic",
        visual_downsample: int = 1,
        visual_update_interval: int = 1,
        temporal_history_len: int = 1,
        step_info_mode: str = "full",
        execution_step_runtime_mode: str | None = None,
        flight_shaping_backend: str | None = None,
        database_path: str | None = None,
        worker_threads: int | None = None,
        collect_step_timing: bool = False,
        batch_observation_backend: str | None = "auto",
        batch_visual_backend: str | None = "auto",
        execution_step_batch_prepare: bool = False,
        execution_episode_controller_shadow_compare: bool = False,
        execution_episode_controller_mainline: bool = False,
        policy_observation_torch_bridge: bool = True,
        observation_return_mode: str = "copy",
        action_wrapper_kwargs: dict[str, Any] | None = None,
        air_combat_post_launch_assessment_enabled: bool = False,
        air_combat_post_launch_assessment_stages: Sequence[str] | str | None = None,
        air_combat_post_launch_assessment_max_steps: int = 0,
        air_combat_post_launch_assessment_timeout_s: float = 0.0,
        air_combat_post_launch_assessment_gamma: float = 0.999,
        air_combat_post_launch_assessment_blue_throttle: float = 0.65,
    ):
        if render_mode not in (None,):
            raise ValueError("WorldBatchVecEnv currently only supports render_mode=None.")
        self.scenario_path = os.path.abspath(str(scenario_path))
        self.n_envs = max(1, int(n_envs))
        self.include_visual = bool(include_visual)
        self.include_proprio = bool(include_proprio)
        self.action_mode = str(action_mode)
        self.mission_obs_mode = str(mission_obs_mode).strip().lower()
        self.visual_downsample = max(1, int(visual_downsample))
        self.visual_update_interval = max(1, int(visual_update_interval))
        self.temporal_history_len = max(1, int(temporal_history_len))
        self.step_info_mode = str(step_info_mode).strip().lower()
        self.execution_step_runtime_mode = (
            normalize_execution_step_runtime_mode(execution_step_runtime_mode)
            if execution_step_runtime_mode is not None
            else None
        )
        self.flight_shaping_backend = _normalize_flight_shaping_backend(flight_shaping_backend)
        if self.execution_step_runtime_mode == "legacy":
            raise ValueError("execution_step_runtime_mode='legacy' has been removed from maintained VecEnv paths")
        if self.execution_step_runtime_mode not in (None, "compiled"):
            raise ValueError(f"Unknown execution_step_runtime_mode: {execution_step_runtime_mode!r}")
        if self.step_info_mode not in ("full", "terminal", "off"):
            raise ValueError(f"Unknown step_info_mode: {step_info_mode!r}")
        self.collect_step_timing = bool(collect_step_timing)
        self.batch_observation_backend = _normalize_batch_observation_backend(batch_observation_backend)
        self.batch_visual_backend = _normalize_batch_visual_backend(batch_visual_backend)
        self.execution_step_batch_prepare = bool(execution_step_batch_prepare)
        self.execution_episode_controller_shadow_compare = bool(execution_episode_controller_shadow_compare)
        self.execution_episode_controller_mainline = bool(execution_episode_controller_mainline)
        self.policy_observation_torch_bridge = bool(policy_observation_torch_bridge)
        self.observation_return_mode = _normalize_observation_return_mode(observation_return_mode)
        self._action_wrapper_kwargs = dict(action_wrapper_kwargs or {})
        self.air_combat_post_launch_assessment_enabled = bool(air_combat_post_launch_assessment_enabled)
        self.air_combat_post_launch_assessment_stages = _as_stage_set(
            air_combat_post_launch_assessment_stages
        )
        self.air_combat_post_launch_assessment_max_steps = max(
            0,
            int(air_combat_post_launch_assessment_max_steps),
        )
        try:
            self.air_combat_post_launch_assessment_timeout_s = max(
                0.0,
                float(air_combat_post_launch_assessment_timeout_s),
            )
        except Exception:
            self.air_combat_post_launch_assessment_timeout_s = 0.0
        try:
            self.air_combat_post_launch_assessment_gamma = float(
                air_combat_post_launch_assessment_gamma
            )
        except Exception:
            self.air_combat_post_launch_assessment_gamma = 0.999
        if not np.isfinite(self.air_combat_post_launch_assessment_gamma):
            self.air_combat_post_launch_assessment_gamma = 0.999
        self.air_combat_post_launch_assessment_gamma = float(
            np.clip(self.air_combat_post_launch_assessment_gamma, 0.0, 1.0)
        )
        try:
            self.air_combat_post_launch_assessment_blue_throttle = float(
                air_combat_post_launch_assessment_blue_throttle
            )
        except Exception:
            self.air_combat_post_launch_assessment_blue_throttle = 0.65
        self.air_combat_post_launch_assessment_blue_throttle = float(
            np.clip(self.air_combat_post_launch_assessment_blue_throttle, 0.0, 1.0)
        )
        self.last_step_timing: dict[str, float] = {}
        self.last_reset_timing: dict[str, float] = {}
        self.last_observation_build_timing: dict[str, float] = {}
        self._execution_episode_controller_mainline_timing: dict[str, float] = {}
        self.last_execution_episode_controller_shadow_compare: list[dict[str, Any] | None] = [
            None for _ in range(self.n_envs)
        ]
        if self.execution_episode_controller_shadow_compare or self.execution_episode_controller_mainline:
            missing_runtime_attrs = []
            required_names = [
                "WorldExecutionEpisodeStepRequest",
                "RuntimeFacade",
                "ExecutionBatchStepRequest",
                "ExecutionBatchStepResult",
            ]
            for name in required_names:
                if not hasattr(ef_py, name):
                    missing_runtime_attrs.append(name)
            if missing_runtime_attrs:
                raise RuntimeError(
                    "execution episode controller runtime features require runtime-owned episode controller APIs: "
                    + ", ".join(missing_runtime_attrs)
                )
        if self.execution_episode_controller_mainline and self.execution_episode_controller_shadow_compare:
            raise RuntimeError(
                "execution_episode_controller_mainline is not compatible with "
                "execution_episode_controller_shadow_compare"
            )
        self._db_path = (
            os.path.abspath(database_path)
            if database_path
            else os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "examples", "config", "database")
            )
        )
        self._compiled_scenario = ScenarioCompiler.compile_path(self.scenario_path)
        self._runtime_adapter = _RuntimeFacadeAdapter(self.n_envs)
        self._batch_apply_buffer = BatchWorldApplyBuffer(self.n_envs)
        self._worker_threads = None if worker_threads is None else max(0, int(worker_threads))
        if self._worker_threads is not None:
            self._runtime_adapter.set_worker_threads(int(self._worker_threads))
        if not bool(self._runtime_adapter.load_database(self._db_path)):
            raise RuntimeError(f"failed to load database into RuntimeFacade: {self._db_path}")

        self.action_space = make_action_space(self.action_mode)
        self.max_contacts = 10
        self.max_rwr = 4
        self.obs_size = 42
        self.arb_height_native = 48
        self.arb_width_native = 96
        self.arb_channels = 10
        if self.arb_height_native % self.visual_downsample != 0 or self.arb_width_native % self.visual_downsample != 0:
            raise ValueError(
                f"visual_downsample={self.visual_downsample} must divide {self.arb_height_native}x{self.arb_width_native}"
            )
        self.arb_height = self.arb_height_native // self.visual_downsample
        self.arb_width = self.arb_width_native // self.visual_downsample
        self.observation_space = make_observation_space(
            action_space=self.action_space,
            mission_obs_mode=self.mission_obs_mode,
            include_visual=self.include_visual,
            include_proprio=self.include_proprio,
            arb_height=self.arb_height,
            arb_width=self.arb_width,
            arb_channels=self.arb_channels,
            temporal_history_len=self.temporal_history_len,
            obs_size=self.obs_size,
            max_contacts=self.max_contacts,
            max_rwr=self.max_rwr,
        )

        self._handles = [
            _BatchWorldHandle(
                env_idx=env_idx,
                loader=self._runtime_adapter.make_scenario_loader(env_idx),
                scenario_path=self.scenario_path,
                render_mode=render_mode,
                include_visual=self.include_visual,
                include_proprio=self.include_proprio,
                action_mode=self.action_mode,
                mission_obs_mode=self.mission_obs_mode,
            )
            for env_idx in range(self.n_envs)
        ]
        for handle in self._handles:
            handle.loader._compiled_scenario = self._compiled_scenario
            handle.loader._compiled_runtime_metadata = self._compiled_scenario.runtime_metadata
            handle.loader._scenario_source_path = self.scenario_path
            if self.execution_step_runtime_mode is not None:
                handle.loader.set_execution_step_runtime_mode(self.execution_step_runtime_mode)
            handle.loader.set_flight_shaping_backend(self.flight_shaping_backend)
            if self.execution_episode_controller_mainline and handle.loader._flight_shaping_backend_mode() != "compiled":
                raise RuntimeError(
                    "execution_episode_controller_mainline currently requires the compiled flight-shaping backend"
                )
            if self._action_wrapper_kwargs:
                handle.action_controller = MultiTimescaleActionController(
                    action_space=self.action_space,
                    loader_getter=lambda handle=handle: handle.loader,
                    dt_getter=lambda handle=handle: self._runtime_adapter.get_time_step(handle.env_idx),
                    **self._action_wrapper_kwargs,
                )
            handle.temporal_history = make_temporal_history_buffer(self.temporal_history_len)
        self.envs = list(self._handles)
        self._actions: np.ndarray | None = None
        self._closed = False
        self._t_start = time.time()

        super().__init__(self.n_envs, self.observation_space, self.action_space)

        self.keys, shapes, dtypes = obs_space_info(self.observation_space)
        self.buf_obs = OrderedDict(
            [(key, np.zeros((self.num_envs, *tuple(shapes[key])), dtype=dtypes[key])) for key in self.keys]
        )
        self.buf_dones = np.zeros((self.num_envs,), dtype=bool)
        self.buf_rews = np.zeros((self.num_envs,), dtype=np.float32)
        self.buf_infos: list[dict[str, Any]] = [{} for _ in range(self.num_envs)]
        self._policy_execution_device_view = None
        self._policy_visual_device_view = None
        self._policy_torch_bridge_enabled = bool(
            self.policy_observation_torch_bridge and torch is not None and hasattr(torch, "from_dlpack")
        )

    @property
    def runtime_facade(self):
        return self._runtime_adapter.facade

    @property
    def last_runtime_window_evidence(self):
        return self._runtime_adapter.last_window_evidence

    def _normalize_seed(self, seed: int | None) -> int:
        if seed is None:
            seed = int(np.random.randint(0, np.iinfo(np.uint32).max, dtype=np.uint32))
        return int(seed) & 0xFFFFFFFF

    def _build_refs(self, indices: Sequence[int] | None = None):
        target_indices = list(range(self.num_envs)) if indices is None else [int(i) for i in indices]
        refs = []
        for env_idx in target_indices:
            handle = self._handles[env_idx]
            if handle.agent_id is None:
                raise RuntimeError(f"world {env_idx} has no active agent_id")
            ref = ef_py.WorldEntityRef()
            ref.world_index = int(env_idx)
            ref.entity_id = int(handle.agent_id)
            refs.append(ref)
        return target_indices, refs

    def _read_truth_and_inst_batch(
        self,
        indices: Sequence[int] | None = None,
    ) -> tuple[list[int], list[Any], list[Any]]:
        target_indices, refs = self._build_refs(indices)
        packet = self._runtime_adapter.read_observation_packet(
            refs,
            include_agent_observations=True,
            include_instrument_states=True,
        )
        truth_list = list(getattr(packet, "agent_observations", []) or [])
        inst_list = list(getattr(packet, "instrument_states", []) or [])
        return target_indices, truth_list, inst_list

    def _read_truth_and_inst_by_refs(
        self,
        refs: Sequence[Any],
    ) -> tuple[list[Any], list[Any]]:
        packet = self._runtime_adapter.read_observation_packet(
            refs,
            include_agent_observations=True,
            include_instrument_states=True,
        )
        return (
            list(getattr(packet, "agent_observations", []) or []),
            list(getattr(packet, "instrument_states", []) or []),
        )

    def _get_instrument_states_batch(self, refs: Sequence[Any]) -> list[Any]:
        return self._runtime_adapter.get_instrument_states_batch(refs)

    def _get_agent_observations_batch(self, refs: Sequence[Any]) -> list[Any]:
        return self._runtime_adapter.get_agent_observations_batch(refs)

    def _world_time_step(self, env_idx: int) -> float:
        return self._runtime_adapter.get_time_step(int(env_idx))

    def _step_runtime_worlds(self, world_indices: Sequence[int]) -> None:
        self._runtime_adapter.step_worlds(world_indices)

    def _sync_command_chain_batch(self, indices: Sequence[int] | None = None) -> None:
        target_indices = list(range(self.num_envs)) if indices is None else [int(i) for i in indices]
        mission_assignments = []
        task_assignments = []
        intent_assignments = []
        report_assignments = []
        for env_idx in target_indices:
            handle = self._handles[env_idx]
            if handle.agent_id is None:
                continue
            if not self._command_chain_entity_active(handle):
                continue

            mission_command = build_kernel_mission_command(handle.loader)
            mission_snapshot = mission_command_snapshot(mission_command)
            if snapshot_changed(handle.last_mission_command_snapshot, mission_snapshot):
                mission_assign = ef_py.WorldMissionCommandMaintainedAssignment()
                project_world_mission_command_maintained_assignment(
                    mission_assign,
                    world_index=int(env_idx),
                    entity_id=int(handle.agent_id),
                    compatibility_mission_command_shell=mission_command,
                )
                mission_assignments.append(mission_assign)
                handle.last_mission_command_snapshot = mission_snapshot

            task_snapshot = task_order_snapshot(getattr(handle.loader, "task_order", None))
            if task_snapshot is not None and snapshot_changed(handle.last_task_order_snapshot, task_snapshot):
                task_assign = ef_py.WorldTaskOrderMaintainedAssignment()
                project_world_task_order_maintained_assignment(
                    task_assign,
                    world_index=int(env_idx),
                    entity_id=int(handle.agent_id),
                    compatibility_task_order_shell=handle.loader.task_order,
                )
                task_assignments.append(task_assign)
                handle.last_task_order_snapshot = task_snapshot

            intent_snapshot = leader_intent_snapshot(getattr(handle.loader, "leader_intent", None))
            if intent_snapshot is not None and snapshot_changed(handle.last_leader_intent_snapshot, intent_snapshot):
                intent_assign = ef_py.WorldLeaderIntentMaintainedAssignment()
                project_world_leader_intent_maintained_assignment(
                    intent_assign,
                    world_index=int(env_idx),
                    entity_id=int(handle.agent_id),
                    compatibility_intent_shell=handle.loader.leader_intent,
                )
                intent_assignments.append(intent_assign)
                handle.last_leader_intent_snapshot = intent_snapshot

            report_snapshot = pilot_report_snapshot(getattr(handle.loader, "pilot_report", None))
            if report_snapshot is not None and snapshot_changed(handle.last_pilot_report_snapshot, report_snapshot):
                report_assign = ef_py.WorldPilotReportMaintainedAssignment()
                project_world_pilot_report_maintained_assignment(
                    report_assign,
                    world_index=int(env_idx),
                    entity_id=int(handle.agent_id),
                    compatibility_report_shell=handle.loader.pilot_report,
                )
                report_assignments.append(report_assign)
                handle.last_pilot_report_snapshot = report_snapshot

        if mission_assignments:
            self._runtime_adapter.set_mission_commands_maintained_batch(mission_assignments)
        if task_assignments:
            self._runtime_adapter.set_task_orders_maintained_batch(task_assignments)
        if intent_assignments:
            self._runtime_adapter.set_leader_intents_maintained_batch(intent_assignments)
        if report_assignments:
            self._runtime_adapter.set_pilot_reports_maintained_batch(report_assignments)

    @staticmethod
    def _command_chain_entity_active(handle: _BatchWorldHandle) -> bool:
        truth = getattr(handle, "last_truth", None)
        if truth is None:
            return True
        try:
            return float(getattr(truth, "health", 1.0) or 0.0) > 0.0
        except Exception:
            return True

    def _save_obs(self, env_idx: int, obs: VecEnvObs) -> None:
        for key in self.keys:
            if key is None:
                self.buf_obs[key][env_idx] = obs
            else:
                self.buf_obs[key][env_idx] = obs[key]  # type: ignore[index]





    def _activate_applied_world(
        self,
        env_idx: int,
        applied_world,
        *,
        seed: int,
        initial_truth=None,
        initial_inst=None,
        sync_to_kernel: bool = True,
    ) -> None:
        handle = self._handles[env_idx]
        handle.loader._compiled_scenario = self._compiled_scenario
        handle.loader._compiled_runtime_metadata = self._compiled_scenario.runtime_metadata
        handle.loader._scenario_source_path = self.scenario_path
        handle.agent_id = handle.loader.load_prepared_world(
            applied_world,
            seed=seed,
            initial_truth=initial_truth,
            initial_inst=initial_inst,
            sync_to_kernel=sync_to_kernel,
        )
        validate_naval_action_mode_for_loader(handle.loader, self.action_mode)
        handle.max_steps = int(handle.loader.get_max_steps())
        handle.steps = 0
        handle.loader.steps = 0
        handle.last_mission_command_snapshot = None
        handle.last_task_order_snapshot = None
        handle.last_leader_intent_snapshot = None
        handle.last_pilot_report_snapshot = None
        handle.last_action = None
        handle.last_policy_action_intent = None
        reset_naval_station_action_state(handle.loader)
        reset_air_combat_event_action_state(handle.loader)
        bind_naval_station_eval_reference(handle.loader)
        handle.last_inst = initial_inst
        handle.last_truth = initial_truth
        if handle.temporal_history is None:
            handle.temporal_history = make_temporal_history_buffer(self.temporal_history_len)
        else:
            handle.temporal_history.clear()
        handle.episode_return = 0.0
        handle.episode_length = 0
        handle.visual_cache = None
        handle.visual_cache_step = -1
        if self.execution_episode_controller_shadow_compare or self.execution_episode_controller_mainline:
            self._sync_execution_episode_controller_runtime_state(env_idx)
        self.last_execution_episode_controller_shadow_compare[env_idx] = None
        self._clear_policy_observation_device_cache()

    def _shared_randomization_overrides(self) -> dict[str, Any] | None:
        base = dict(self._handles[0].randomization_overrides)
        for handle in self._handles[1:]:
            if dict(handle.randomization_overrides) != base:
                return None
        return base

    def _reset_single_world(self, env_idx: int, seed: int | None) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
        total_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        seed_i = self._normalize_seed(seed)
        handle = self._handles[env_idx]
        layout_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        layout = build_compiled_world_layout(
            self._compiled_scenario,
            seed=seed_i,
            randomization_overrides=dict(handle.randomization_overrides) or None,
        )
        layout_build_ms = (time.perf_counter() - layout_t0) * 1000.0 if self.collect_step_timing else 0.0
        apply_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        applied_world = self._runtime_adapter.apply_world_layout(int(env_idx), layout)
        kernel_apply_ms = (time.perf_counter() - apply_t0) * 1000.0 if self.collect_step_timing else 0.0
        initial_truth = None
        initial_inst = None
        if applied_world.agent_id is not None:
            try:
                ref = ef_py.WorldEntityRef()
                ref.world_index = int(env_idx)
                ref.entity_id = int(applied_world.agent_id)
                truth_list, inst_list = self._read_truth_and_inst_by_refs([ref])
                initial_truth = truth_list[0]
                initial_inst = inst_list[0]
            except Exception:
                initial_truth = None
                initial_inst = None
        activate_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        self._activate_applied_world(
            env_idx,
            applied_world,
            seed=seed_i,
            initial_truth=initial_truth,
            initial_inst=initial_inst,
            sync_to_kernel=True,
        )
        activation_ms = (time.perf_counter() - activate_t0) * 1000.0 if self.collect_step_timing else 0.0
        sync_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        self._sync_command_chain_batch([env_idx])
        command_sync_ms = (time.perf_counter() - sync_t0) * 1000.0 if self.collect_step_timing else 0.0
        obs_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        obs = self._build_observation_from_cached_state(env_idx)
        if handle.action_controller is not None:
            handle.action_controller.reset_state(_copy_obs(obs))
        obs_build_ms = (time.perf_counter() - obs_t0) * 1000.0 if self.collect_step_timing else 0.0
        reset_info: dict[str, Any] = {}
        if self.collect_step_timing:
            timing = {
                "layout_build_ms": float(layout_build_ms),
                "kernel_apply_ms": float(kernel_apply_ms),
                "activation_ms": float(activation_ms),
                "command_sync_ms": float(command_sync_ms),
                "obs_build_ms": float(obs_build_ms),
                "total_ms": float((time.perf_counter() - total_t0) * 1000.0),
            }
            timing.update(self._observation_timing_snapshot())
            reset_info["timing"] = timing
            self.last_reset_timing = dict(timing)
        self.reset_infos[env_idx] = reset_info
        self._save_obs(env_idx, obs)
        return obs, reset_info

    def step_async(self, actions: np.ndarray) -> None:
        action_arr = np.asarray(actions, dtype=np.float32)
        if self.num_envs == 1 and action_arr.ndim == 1:
            action_arr = action_arr.reshape(1, -1)
        self._actions = action_arr

    def step_wait(self) -> VecEnvStepReturn:
        if self._actions is None:
            raise RuntimeError("step_async() must be called before step_wait().")

        self._clear_policy_observation_device_cache()
        total_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        prepare_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        _, refs = self._build_refs()
        inst_now_list = None
        if self.action_mode != "full":
            inst_now_list = self._get_instrument_states_batch(refs)

        assignments = []
        prepared_actions: list[Any | None] = [None] * self.num_envs
        air_combat_truth_before: list[Any | None] = [None] * self.num_envs
        naval_action_sync_indices: list[int] = []
        for env_idx, handle in enumerate(self._handles):
            if handle.agent_id is None:
                raise RuntimeError(f"world {env_idx} is not initialized; call reset() before step().")
            effective_action = self._actions[env_idx]
            if handle.action_controller is not None:
                prepared = handle.action_controller.prepare_action(effective_action)
                prepared_actions[env_idx] = prepared
                effective_action = prepared.action
            action = normalize_action(effective_action, action_space=self.action_space, action_mode=self.action_mode)
            if is_naval_station_action_mode(self.action_mode):
                action = naval_station_action_command(action)
                handle.last_action = action.astype(np.float32, copy=True)
                if apply_naval_station_action(handle.loader, action):
                    naval_action_sync_indices.append(env_idx)
            elif is_air_combat_hybrid_action_mode(self.action_mode):
                policy_intent = action.astype(np.float32, copy=True)
                action = air_combat_hybrid_effective_action(
                    action,
                    previous_intent=handle.last_policy_action_intent,
                )
                handle.last_policy_action_intent = policy_intent
                air_combat_truth_before[env_idx] = handle.last_truth
                action, _ = apply_air_combat_event_action_gate(
                    handle.loader,
                    action,
                    agent_id=int(handle.agent_id),
                    truth_before=handle.last_truth,
                )
                handle.last_action = action.astype(np.float32, copy=True)
            else:
                handle.last_action = action.astype(np.float32, copy=True)
            handle.loader._last_action_mode = str(self.action_mode)
            handle.loader._last_effective_action = handle.last_action.astype(np.float32, copy=True)
            assign = ef_py.WorldPilotActionAssignment()
            assign.world_index = int(env_idx)
            assign.entity_id = int(handle.agent_id)
            assign.action = build_pilot_action(
                action,
                action_mode=self.action_mode,
                inst_now=None if inst_now_list is None else inst_now_list[env_idx],
            )
            assignments.append(assign)
        action_prepare_ms = (time.perf_counter() - prepare_t0) * 1000.0 if self.collect_step_timing else 0.0

        step_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        if naval_action_sync_indices:
            self._sync_command_chain_batch(naval_action_sync_indices)
        self._set_pilot_actions_batch(assignments)
        self._step_runtime_batch()
        batch_step_ms = (time.perf_counter() - step_t0) * 1000.0 if self.collect_step_timing else 0.0

        read_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        _target_indices, truth_list, inst_list = self._read_truth_and_inst_batch()
        state_read_ms = (time.perf_counter() - read_t0) * 1000.0 if self.collect_step_timing else 0.0
        behavior_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        for env_idx, handle in enumerate(self._handles):
            handle.steps += 1
            handle.loader.steps = int(handle.steps)
            handle.last_truth = truth_list[env_idx]
            handle.last_inst = inst_list[env_idx]
            if is_air_combat_hybrid_action_mode(self.action_mode):
                finalize_air_combat_event_action_info(
                    handle.loader,
                    truth_before=air_combat_truth_before[env_idx],
                    truth_after=handle.last_truth,
                )
            sim_time = float(handle.steps) * float(
                resolve_loader_time_step(handle.loader, default=self._world_time_step(env_idx))
            )
            if self.execution_episode_controller_mainline:
                handle.loader.update_command_chain_only(
                    sim_time,
                    truth=handle.last_truth,
                    inst=handle.last_inst,
                    sync_to_kernel=False,
                )
            else:
                handle.loader.update_behaviors(
                    sim_time,
                    truth=handle.last_truth,
                    inst=handle.last_inst,
                    sync_to_kernel=False,
                )
        behavior_update_ms = (time.perf_counter() - behavior_t0) * 1000.0 if self.collect_step_timing else 0.0
        sync_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        if not self.execution_episode_controller_mainline:
            self._sync_command_chain_batch()
        command_sync_ms = (time.perf_counter() - sync_t0) * 1000.0 if self.collect_step_timing else 0.0

        obs_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        obs_batch = self._build_observations_from_cached_state()
        obs_build_ms = (time.perf_counter() - obs_t0) * 1000.0 if self.collect_step_timing else 0.0
        shaping_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        self._prepare_batch_flight_shaping_overrides()
        flight_shaping_batch_ms = (time.perf_counter() - shaping_t0) * 1000.0 if self.collect_step_timing else 0.0
        reward_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        any_done = False
        shadow_reports: list[dict[str, Any] | None] = [None] * self.num_envs
        mainline_results: list[dict[str, Any] | None] = [None] * self.num_envs
        if self.execution_episode_controller_shadow_compare:
            shadow_reports = self._compare_execution_episode_controller_shadow_batch(obs_batch)
        if self.execution_episode_controller_mainline:
            mainline_results = self._step_execution_episode_controller_mainline_batch(obs_batch)
            sync_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            self._sync_command_chain_batch()
            command_sync_ms = (time.perf_counter() - sync_t0) * 1000.0 if self.collect_step_timing else 0.0
            mission_refresh_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            self._refresh_mission_observation_batch(obs_batch)
            if self.collect_step_timing:
                obs_build_ms += (time.perf_counter() - mission_refresh_t0) * 1000.0
        for env_idx in range(self.num_envs):
            obs = obs_batch[env_idx]
            handle = self._handles[env_idx]
            mainline_result = mainline_results[env_idx]
            if mainline_result is not None:
                reward = float(mainline_result["reward"])
                terminated = bool(mainline_result["terminated"])
                truncated = bool(mainline_result["truncated"])
                mission_status = list(mainline_result["mission_status"])
            else:
                cache = getattr(handle.loader, "_runtime_eval_cache", None)
                cached_step_eval = cache.get("step_evaluation") if isinstance(cache, dict) else None
                reward, terminated, truncated, mission_status = _compute_loader_step_outcome(
                    handle.loader,
                    obs=obs,
                    steps=handle.steps,
                    max_steps=handle.max_steps,
                    truth=handle.last_truth,
                    inst_state=handle.last_inst,
                    step_evaluation=cached_step_eval if isinstance(cached_step_eval, dict) else None,
                )
            post_launch_assessment_info: dict[str, Any] = {}
            if self._air_combat_post_launch_assessment_should_run(
                env_idx,
                terminated=bool(terminated),
                truncated=bool(truncated),
            ):
                (
                    obs,
                    reward,
                    terminated,
                    truncated,
                    mission_status,
                    post_launch_assessment_info,
                ) = self._run_air_combat_post_launch_assessment(
                    env_idx,
                    obs=obs,
                    reward=float(reward),
                    terminated=bool(terminated),
                    truncated=bool(truncated),
                    mission_status=mission_status,
                )
            include_full_step_info = not (
                self.step_info_mode == "off"
                or (self.step_info_mode == "terminal" and not bool(terminated or truncated))
            )
            mainline_step_info_fields: dict[str, float] | None = None
            if mainline_result is not None:
                step_info_fields = mainline_result.get("step_info_fields")
                if isinstance(step_info_fields, dict) and step_info_fields:
                    mainline_step_info_fields = {}
                    for key, value in step_info_fields.items():
                        try:
                            mainline_step_info_fields[str(key)] = float(value)
                        except Exception:
                            continue
                    if not mainline_step_info_fields:
                        mainline_step_info_fields = None
            if include_full_step_info and mainline_step_info_fields is None:
                info = _build_loader_step_info(
                    handle.loader,
                    entity_id=int(handle.agent_id),
                    mission_status=mission_status,
                    terminated=terminated,
                    truncated=truncated,
                    inst_now=handle.last_inst,
                    truth_now=handle.last_truth,
                )
            else:
                info = build_step_info_minimal(
                    handle.loader,
                    mission_status=mission_status,
                    terminated=terminated,
                    truncated=truncated,
                )
                if include_full_step_info and mainline_step_info_fields is not None:
                    info.update(mainline_step_info_fields)
            if mainline_result is not None:
                termination_reason = str(mainline_result.get("termination_reason", "") or "")
                if termination_reason:
                    info["termination_reason"] = termination_reason
                reward_terms = mainline_result.get("reward_terms")
                if isinstance(reward_terms, dict) and reward_terms:
                    info["reward_terms"] = {str(key): float(value) for key, value in reward_terms.items()}
            prepared = prepared_actions[env_idx]
            if prepared is not None and handle.action_controller is not None:
                obs, reward, info = handle.action_controller.finalize_step_result(obs, reward, info, prepared)
            if is_air_combat_hybrid_action_mode(self.action_mode):
                add_air_combat_event_action_info(info, handle.loader)
            if post_launch_assessment_info:
                info.update(post_launch_assessment_info)
                reason_before = str(info.get("termination_reason", "") or "").strip().lower()
                if reason_before in {"", "running"} and isinstance(
                    post_launch_assessment_info.get("post_launch_assessment_terminal_reason"), str
                ):
                    info["termination_reason"] = str(
                        post_launch_assessment_info["post_launch_assessment_terminal_reason"]
                    )
            if shadow_reports[env_idx] is not None:
                info["execution_episode_controller_shadow_compare"] = shadow_reports[env_idx]
            handle.episode_return += float(reward)
            handle.episode_length += 1
            done = bool(terminated or truncated)
            any_done = any_done or done
            self.buf_rews[env_idx] = float(reward)
            self.buf_dones[env_idx] = done
            info["TimeLimit.truncated"] = bool(truncated and not terminated)

            if done:
                info["episode"] = {
                    "r": round(float(handle.episode_return), 6),
                    "l": int(handle.episode_length),
                    "t": round(time.time() - self._t_start, 6),
                }
                info["terminal_observation"] = _copy_obs(obs)
                obs, self.reset_infos[env_idx] = self._reset_single_world(env_idx, seed=None)
            self.buf_infos[env_idx] = info
            self._save_obs(env_idx, obs)
        reward_info_ms = (time.perf_counter() - reward_t0) * 1000.0 if self.collect_step_timing else 0.0
        if any_done:
            self._clear_policy_observation_device_cache()
        self.last_execution_episode_controller_shadow_compare = list(shadow_reports)

        if self.collect_step_timing:
            autoreset_ms = 0.0
            for reset_info in self.reset_infos:
                if isinstance(reset_info, dict):
                    timing = reset_info.get("timing")
                    if isinstance(timing, dict):
                        try:
                            autoreset_ms += float(timing.get("total_ms", 0.0))
                        except Exception:
                            pass
            self.last_step_timing = {
                "action_prepare_ms": float(action_prepare_ms),
                "batch_step_ms": float(batch_step_ms),
                "state_read_ms": float(state_read_ms),
                "behavior_update_ms": float(behavior_update_ms),
                "command_sync_ms": float(command_sync_ms),
                "obs_build_ms": float(obs_build_ms),
                "flight_shaping_batch_ms": float(flight_shaping_batch_ms),
                "reward_info_ms": float(reward_info_ms),
                "autoreset_ms": float(autoreset_ms),
                "total_ms": float((time.perf_counter() - total_t0) * 1000.0),
            }
            self.last_step_timing.update(self._observation_timing_snapshot())
            self.last_step_timing.update(self._execution_episode_controller_mainline_timing)
            for info in self.buf_infos:
                if isinstance(info, dict):
                    info["timing"] = dict(self.last_step_timing)
        else:
            self.last_step_timing = {}
            self._execution_episode_controller_mainline_timing = {}

        self._actions = None
        return self._obs_from_buf(), np.copy(self.buf_rews), np.copy(self.buf_dones), deepcopy(self.buf_infos)

    def reset(self) -> VecEnvObs:
        self._clear_policy_observation_device_cache()
        total_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        seeds = [self._normalize_seed(self._seeds[env_idx]) for env_idx in range(self.num_envs)]
        shared_overrides = self._shared_randomization_overrides()
        if shared_overrides is not None:
            batch_setup_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            applied_worlds = load_compiled_scenario_for_setup_target(
                self._runtime_adapter,
                self._compiled_scenario,
                seeds=seeds,
                randomization_overrides=shared_overrides or None,
                apply_buffer=self._batch_apply_buffer,
            )
            batch_setup_ms = (time.perf_counter() - batch_setup_t0) * 1000.0 if self.collect_step_timing else 0.0
            refs = []
            for env_idx, applied_world in enumerate(applied_worlds):
                if applied_world.agent_id is None:
                    raise RuntimeError(f"world {env_idx} has no agent after batch scenario load")
                ref = ef_py.WorldEntityRef()
                ref.world_index = int(env_idx)
                ref.entity_id = int(applied_world.agent_id)
                refs.append(ref)
            read_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            truth_list, inst_list = self._read_truth_and_inst_by_refs(refs)
            state_read_ms = (time.perf_counter() - read_t0) * 1000.0 if self.collect_step_timing else 0.0
            activate_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            for env_idx, applied_world in enumerate(applied_worlds):
                self._activate_applied_world(
                    env_idx,
                    applied_world,
                    seed=seeds[env_idx],
                    initial_truth=truth_list[env_idx],
                    initial_inst=inst_list[env_idx],
                    sync_to_kernel=False,
                )
            activation_ms = (time.perf_counter() - activate_t0) * 1000.0 if self.collect_step_timing else 0.0
            sync_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            self._sync_command_chain_batch()
            command_sync_ms = (time.perf_counter() - sync_t0) * 1000.0 if self.collect_step_timing else 0.0
            obs_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            obs_batch = self._build_observations_from_cached_state()
            for env_idx, obs in enumerate(obs_batch):
                handle = self._handles[env_idx]
                if handle.action_controller is not None:
                    handle.action_controller.reset_state(_copy_obs(obs))
                self.reset_infos[env_idx] = {}
                self._save_obs(env_idx, obs)
            obs_build_ms = (time.perf_counter() - obs_t0) * 1000.0 if self.collect_step_timing else 0.0
            if self.collect_step_timing:
                self.last_reset_timing = {
                    "batch_setup_ms": float(batch_setup_ms),
                    "state_read_ms": float(state_read_ms),
                    "activation_ms": float(activation_ms),
                    "command_sync_ms": float(command_sync_ms),
                    "obs_build_ms": float(obs_build_ms),
                    "total_ms": float((time.perf_counter() - total_t0) * 1000.0),
                }
                self.last_reset_timing.update(self._observation_timing_snapshot())
                for env_idx in range(self.num_envs):
                    self.reset_infos[env_idx] = {"timing": dict(self.last_reset_timing)}
        else:
            for env_idx in range(self.num_envs):
                self._reset_single_world(env_idx, seed=seeds[env_idx])
            if self.collect_step_timing:
                total_ms = float((time.perf_counter() - total_t0) * 1000.0)
                self.last_reset_timing = {"total_ms": total_ms}
        if not self.collect_step_timing:
            self.last_reset_timing = {}
        self.last_execution_episode_controller_shadow_compare = [None for _ in range(self.num_envs)]
        self._reset_seeds()
        self._reset_options()
        return self._obs_from_buf()

    def close(self) -> None:
        self._clear_policy_observation_device_cache()
        self._actions = None
        self._closed = True

    def get_images(self) -> Sequence[np.ndarray | None]:
        if self.render_mode != "rgb_array":
            warnings.warn(
                f"The render mode is {self.render_mode}, but this method assumes it is `rgb_array` to obtain images."
            )
        return [None for _ in range(self.num_envs)]

    def get_attr(self, attr_name: str, indices: VecEnvIndices = None) -> list[Any]:
        target_handles = self._get_target_handles(indices)
        values = []
        for handle in target_handles:
            if hasattr(handle, attr_name):
                values.append(getattr(handle, attr_name))
            elif hasattr(handle.loader, attr_name):
                values.append(getattr(handle.loader, attr_name))
            else:
                raise AttributeError(attr_name)
        return values

    def set_attr(self, attr_name: str, value: Any, indices: VecEnvIndices = None) -> None:
        for handle in self._get_target_handles(indices):
            if hasattr(handle, attr_name):
                setattr(handle, attr_name, value)
            elif hasattr(handle.loader, attr_name):
                setattr(handle.loader, attr_name, value)
            else:
                raise AttributeError(attr_name)

    def env_method(self, method_name: str, *method_args, indices: VecEnvIndices = None, **method_kwargs) -> list[Any]:
        results = []
        for handle in self._get_target_handles(indices):
            if hasattr(handle, method_name):
                method = getattr(handle, method_name)
            elif hasattr(handle.loader, method_name):
                method = getattr(handle.loader, method_name)
            else:
                raise AttributeError(method_name)
            results.append(method(*method_args, **method_kwargs))
        return results

    def env_is_wrapped(self, wrapper_class: type[gym.Wrapper], indices: VecEnvIndices = None) -> list[bool]:
        _ = wrapper_class
        return [False for _ in self._get_indices(indices)]

    def _get_target_handles(self, indices: VecEnvIndices) -> list[_BatchWorldHandle]:
        return [self._handles[i] for i in self._get_indices(indices)]


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
]
