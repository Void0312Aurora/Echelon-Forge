from __future__ import annotations

from collections import OrderedDict
from collections.abc import Sequence
from copy import deepcopy
from typing import Any
import json
import os
import time
import warnings

import gymnasium as gym
import numpy as np

try:
    import torch
except Exception:  # pragma: no cover - training envs are expected to have torch
    torch = None

import ef_py

from gym_envs.scenario_loader import (
    ScenarioLoader,
    normalize_execution_step_runtime_mode,
)
from gym_envs.universal_env import (
    add_air_combat_event_action_info,
    append_temporal_history,
    air_combat_hybrid_effective_action,
    apply_air_combat_event_action_gate,
    apply_naval_station_action,
    attach_temporal_history,
    bind_naval_station_eval_reference,
    build_pilot_action,
    build_step_info_minimal,
    build_universal_observation,
    make_action_space,
    make_observation_space,
    make_temporal_history_buffer,
    naval_policy_instruments,
    naval_station_action_command,
    normalize_action,
    reset_naval_station_action_state,
    finalize_air_combat_event_action_info,
    is_air_combat_hybrid_action_mode,
    is_naval_station_action_mode,
    temporal_history_enabled,
    validate_naval_action_mode_for_loader,
)
from python.rl.tasking.bridge import build_kernel_mission_command
from python.rl.runtime.world_batch.command_chain_cache import (
    project_world_leader_intent_maintained_assignment,
    project_world_mission_command_maintained_assignment,
    project_world_pilot_report_maintained_assignment,
    project_world_task_order_maintained_assignment,
)
from python.rl.support.sb3_vec_env_compat import (
    VecEnv,
    VecEnvIndices,
    VecEnvObs,
    VecEnvStepReturn,
    dict_to_obs,
    obs_space_info,
)
from python.rl.control.wrappers import MultiTimescaleActionController
from python.rl.runtime.world_batch import (
    BatchWorldHandle,
    build_loader_step_info,
    compute_loader_step_outcome,
    ExecutionObservationBatch,
    RuntimeFacadeAdapter,
    compute_execution_observation_batch,
    copy_obs,
    leader_intent_snapshot,
    mission_command_snapshot,
    normalize_batch_observation_backend,
    normalize_batch_visual_backend,
    normalize_flight_shaping_backend,
    normalize_observation_return_mode,
    normalize_runtime_compatibility_enabled,
    observation_timing_snapshot,
    parse_reward_terms_json,
    pilot_report_snapshot,
    refresh_visual_cache_batch,
    snapshot_changed,
    step_info_products_to_info_fields,
    task_order_snapshot,
)
from python.rl.tasking.bridge import resolve_loader_time_step, resolve_tasking_profile, tasking_profile_for_loader
from python.scenario_compiler import ScenarioCompiler
from python.scenario.runtime import (
    BatchWorldApplyBuffer,
    build_compiled_world_layout,
    load_compiled_scenario_for_setup_target,
)

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

_POST_LAUNCH_ASSESSMENT_REWARD_KEYS = {
    "combat_win_bonus",
    "combat_loss_penalty",
    "combat_draw_reward",
}
_POST_LAUNCH_ASSESSMENT_REWARD_PREFIXES = (
    "air_combat_target_",
    "air_combat_self_",
)
_POST_LAUNCH_ASSESSMENT_DEFAULT_STAGES = {"A1-S1", "A1-S2"}


def _float32_view(value: Any) -> np.ndarray:
    return np.asarray(value, dtype=np.float32)


def _execution_instrument_vector(loader: ScenarioLoader, truth: Any, inst: Any, *, max_contacts: int, max_rwr: int) -> np.ndarray:
    ils_vec = loader.get_ils_observation(float(truth.x), float(truth.y), float(inst.alt_baro))
    inst_vec, _contacts, _rwr = ef_py.compute_execution_observation_runtime_numpy(
        inst,
        truth,
        float(ils_vec[0]) if len(ils_vec) > 0 else 0.0,
        float(ils_vec[1]) if len(ils_vec) > 1 else 0.0,
        float(ils_vec[2]) if len(ils_vec) > 2 else 0.0,
        float(ils_vec[3]) if len(ils_vec) > 3 else 0.0,
        int(max_contacts),
        int(max_rwr),
    )
    return np.asarray(inst_vec, dtype=np.float32)


def _as_stage_set(value: Any) -> set[str]:
    if value is None:
        return set(_POST_LAUNCH_ASSESSMENT_DEFAULT_STAGES)
    if isinstance(value, str):
        parts = [part.strip() for part in value.replace(";", ",").split(",")]
        return {part for part in parts if part}
    try:
        return {str(part).strip() for part in value if str(part).strip()}
    except TypeError:
        return {str(value).strip()} if str(value).strip() else set()


def _scenario_stage(loader: ScenarioLoader) -> str:
    scenario = getattr(loader, "scenario_data", {})
    scenario = scenario if isinstance(scenario, dict) else {}
    realism = scenario.get("realism_gradient", {})
    realism = realism if isinstance(realism, dict) else {}
    stage = str(realism.get("stage", "") or "").strip()
    if stage:
        return stage
    source_path = str(getattr(loader, "_scenario_source_path", "") or "").lower()
    if "stage1" in source_path or "a1-s1" in source_path:
        return "A1-S1"
    if "stage2" in source_path or "a1-s2" in source_path:
        return "A1-S2"
    return ""


def _post_launch_reward_from_breakdown(breakdown: Any) -> float:
    if not isinstance(breakdown, dict):
        return 0.0
    total = 0.0
    for key, value in breakdown.items():
        key_s = str(key)
        if key_s in _POST_LAUNCH_ASSESSMENT_REWARD_KEYS or key_s.startswith(
            _POST_LAUNCH_ASSESSMENT_REWARD_PREFIXES
        ):
            try:
                total += float(value)
            except Exception:
                continue
    return float(total)


class WorldBatchVecEnv(VecEnv):
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
        runtime_compatibility_enabled: bool = False,
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
        self.runtime_compatibility_enabled = normalize_runtime_compatibility_enabled(runtime_compatibility_enabled)
        self.execution_step_runtime_mode = (
            normalize_execution_step_runtime_mode(execution_step_runtime_mode)
            if execution_step_runtime_mode is not None
            else None
        )
        self.flight_shaping_backend = _normalize_flight_shaping_backend(flight_shaping_backend)
        if self.execution_step_runtime_mode not in (None, "compiled", "legacy"):
            raise ValueError(f"Unknown execution_step_runtime_mode: {execution_step_runtime_mode!r}")
        if self.execution_step_runtime_mode == "legacy" and not self.runtime_compatibility_enabled:
            raise RuntimeError(
                "execution_step_runtime_mode='legacy' is quarantined; pass "
                "runtime_compatibility_enabled=True to opt in explicitly."
            )
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
        if self.execution_episode_controller_mainline and self.execution_step_runtime_mode == "legacy":
            raise RuntimeError("execution_episode_controller_mainline requires compiled execution_step_runtime_mode")
        self._db_path = (
            os.path.abspath(database_path)
            if database_path
            else os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "examples", "config", "database")
            )
        )
        self._compiled_scenario = ScenarioCompiler.compile_path(self.scenario_path)
        self._runtime_adapter = _RuntimeFacadeAdapter(
            self.n_envs,
            runtime_compatibility_enabled=self.runtime_compatibility_enabled,
        )
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

    def execution_episode_ready(self, world_index: int) -> bool:
        return bool(self._runtime_adapter.execution_episode_ready(int(world_index)))

    def export_execution_episode_states(self, refs: Sequence[Any]) -> list[Any]:
        return self._runtime_adapter.export_execution_episode_states(refs)

    def export_execution_episode_state(self, env_idx: int) -> Any:
        _target_indices, refs = self._build_refs([int(env_idx)])
        return self.export_execution_episode_states(refs)[0]

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

    def _collect_observations(self, indices: Sequence[int] | None = None) -> list[dict[str, np.ndarray]]:
        target_indices, truth_list, inst_list = self._read_truth_and_inst_batch(indices)
        for batch_idx, env_idx in enumerate(target_indices):
            handle = self._handles[env_idx]
            handle.last_inst = inst_list[batch_idx]
            handle.last_truth = truth_list[batch_idx]
        return self._build_observations_from_cached_state(target_indices)

    def _batch_observation_backend_mode(self) -> str:
        if self.batch_observation_backend == "auto":
            return "compiled" if self._batch_observation_runtime_available() else "legacy"
        return self.batch_observation_backend

    def _batch_observation_runtime_available(self) -> bool:
        if not hasattr(ef_py, "compute_execution_observation_batch_numpy"):
            return False
        if self.execution_step_runtime_mode == "legacy":
            return False
        for handle in self._handles:
            if not bool(getattr(handle.loader, "use_compiled_execution_step_runtime", True)):
                return False
        return True

    def _batch_visual_backend_mode(self) -> str:
        if self.batch_visual_backend == "auto":
            if self._batch_visual_runtime_available():
                return "compiled"
            raise RuntimeError("maintained visual batching requires compute_world_batch_visual_observation_batch_numpy")
        return self.batch_visual_backend

    def _batch_visual_runtime_available(self) -> bool:
        return hasattr(ef_py, "compute_world_batch_visual_observation_batch_numpy")

    def _flight_shaping_backend_mode(self) -> str:
        modes = {
            str(handle.loader._flight_shaping_backend_mode())
            for handle in self._handles
        }
        if len(modes) == 1:
            return next(iter(modes))
        return "mixed"

    def _clear_policy_observation_device_cache(self) -> None:
        self._policy_execution_device_view = None
        self._policy_visual_device_view = None

    def _is_full_batch_indices(self, indices: Sequence[int]) -> bool:
        return len(indices) == self.num_envs and all(int(env_idx) == idx for idx, env_idx in enumerate(indices))

    def _execution_observation_device_export_allowed(self, indices: Sequence[int]) -> bool:
        if not self._is_full_batch_indices(indices):
            return False
        naval_profile = resolve_tasking_profile("naval")
        for env_idx in indices:
            if tasking_profile_for_loader(self._handles[int(env_idx)].loader) is naval_profile:
                return False
        return True

    def _refresh_visual_batch(self, indices: Sequence[int] | None = None) -> None:
        if not self.include_visual:
            return
        target_indices = list(range(self.num_envs)) if indices is None else [int(i) for i in indices]
        full_refresh = self._is_full_batch_indices(target_indices)
        refreshed, device_view = refresh_visual_cache_batch(
            adapter=self._runtime_adapter,
            indexed_states=[(env_idx, self._handles[env_idx]) for env_idx in target_indices],
            visual_downsample=int(self.visual_downsample),
            visual_update_interval=int(self.visual_update_interval),
            arb_height=int(self.arb_height),
            arb_width=int(self.arb_width),
            arb_channels=int(self.arb_channels),
            arb_height_native=int(self.arb_height_native),
            arb_width_native=int(self.arb_width_native),
            backend=self._batch_visual_backend_mode(),
            allow_device_export=bool(full_refresh and self._policy_torch_bridge_enabled),
        )
        if not refreshed:
            return
        self._policy_visual_device_view = device_view if full_refresh else None

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
        if backend == "legacy" or not self._batch_observation_runtime_available():
            self.last_observation_build_timing = {
                "mission_input_build_ms": 0.0,
                "execution_observation_batch_ms": 0.0,
                "step_eval_prepare_ms": 0.0,
            }
            self._policy_execution_device_view = None
            obs_batch: list[dict[str, np.ndarray]] = []
            for env_idx in target_indices:
                handle = self._handles[env_idx]
                if handle.last_inst is None or handle.last_truth is None:
                    raise RuntimeError(f"world {env_idx} has no cached state for observation build")
                obs = build_universal_observation(
                    handle.loader,
                    handle.last_inst,
                    handle.last_truth,
                    mission_obs_mode=self.mission_obs_mode,
                    max_contacts=self.max_contacts,
                    max_rwr=self.max_rwr,
                    include_proprio=self.include_proprio,
                    last_action=handle.last_action,
                    action_space=self.action_space,
                    steps=int(handle.steps),
                    max_steps=int(handle.max_steps),
                )
                obs_batch.append(self._attach_temporal_history(env_idx, self._attach_visual_observation(env_idx, obs)))
            return obs_batch

        allow_execution_device_export = self._execution_observation_device_export_allowed(target_indices)
        obs_batch_data: ExecutionObservationBatch = compute_execution_observation_batch(
            states=[self._handles[env_idx] for env_idx in target_indices],
            mission_obs_mode=self.mission_obs_mode,
            max_contacts=int(self.max_contacts),
            max_rwr=int(self.max_rwr),
            backend=backend,
            allow_device_export=bool(allow_execution_device_export),
            torch_bridge_enabled=bool(self._policy_torch_bridge_enabled),
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
            obs = {
                "instruments": policy_inst_vec,
                "contacts": contacts,
                "rwr": rwr,
                "mission": miss_vec,
            }
            if self.include_proprio:
                if handle.last_action is None:
                    proprio = np.zeros((int(self.action_space.shape[0]),), dtype=np.float32)
                else:
                    proprio = _float32_view(handle.last_action).reshape(-1)
                obs["proprio"] = proprio
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
        obs["visual"] = np.asarray(handle.visual_cache, dtype=np.float32, copy=False)
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

    @staticmethod
    def _execution_episode_controller_state_requires_reprime(runtime_state, loader_state) -> bool:
        def _canonicalize_runtime_json(raw: Any) -> str:
            if not isinstance(raw, str) or not raw.strip():
                return str(raw or "")
            try:
                parsed = json.loads(raw)
            except Exception:
                return str(raw)

            def _strip_internal_cache_fields(value: Any) -> Any:
                if isinstance(value, dict):
                    return {
                        str(key): _strip_internal_cache_fields(item)
                        for key, item in value.items()
                        if not str(key).startswith("_")
                    }
                if isinstance(value, list):
                    return [_strip_internal_cache_fields(item) for item in value]
                return value

            return json.dumps(_strip_internal_cache_fields(parsed), ensure_ascii=True, sort_keys=True)

        def _route_digest(state: Any) -> list[tuple[float, float, float, float, float, float, str]]:
            route = []
            for waypoint in list(getattr(state, "route_waypoints", [])):
                route.append(
                    (
                        float(getattr(waypoint, "x_m", 0.0)),
                        float(getattr(waypoint, "y_m", 0.0)),
                        float(getattr(waypoint, "z_m", 0.0)),
                        float(getattr(waypoint, "radius_m", 0.0)),
                        float(getattr(waypoint, "altitude_m", 0.0)),
                        float(getattr(waypoint, "speed_mps", 0.0)),
                        str(getattr(waypoint, "waypoint_mode", "")),
                    )
                )
            return route

        runtime_digest = {
            "has_mission_command_json": bool(getattr(runtime_state, "has_mission_command_json", False)),
            "mission_command_json": _canonicalize_runtime_json(str(getattr(runtime_state, "mission_command_json", ""))),
            "route_waypoints": _route_digest(runtime_state),
            "has_post_waypoint_transition_json": bool(getattr(runtime_state, "has_post_waypoint_transition_json", False)),
            "post_waypoint_transition_json": _canonicalize_runtime_json(
                str(getattr(runtime_state, "post_waypoint_transition_json", ""))
            ),
            "mission_phase_name": str(getattr(runtime_state, "mission_phase_name", "")),
            "has_cached_route_ref_id": bool(getattr(runtime_state, "has_cached_route_ref_id", False)),
            "cached_route_ref_id": int(getattr(runtime_state, "cached_route_ref_id", 0)),
        }
        loader_digest = {
            "has_mission_command_json": bool(getattr(loader_state, "has_mission_command_json", False)),
            "mission_command_json": _canonicalize_runtime_json(str(getattr(loader_state, "mission_command_json", ""))),
            "route_waypoints": _route_digest(loader_state),
            "has_post_waypoint_transition_json": bool(getattr(loader_state, "has_post_waypoint_transition_json", False)),
            "post_waypoint_transition_json": _canonicalize_runtime_json(
                str(getattr(loader_state, "post_waypoint_transition_json", ""))
            ),
            "mission_phase_name": str(getattr(loader_state, "mission_phase_name", "")),
            "has_cached_route_ref_id": bool(getattr(loader_state, "has_cached_route_ref_id", False)),
            "cached_route_ref_id": int(getattr(loader_state, "cached_route_ref_id", 0)),
        }
        return runtime_digest != loader_digest

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

    def get_policy_observation_torch(self, device: Any | None = None) -> dict[str, Any] | None:
        if torch is None or not self._policy_torch_bridge_enabled:
            return None

        target_device = torch.device(device) if device is not None else torch.device("cuda")
        if target_device.type != "cuda":
            return None

        obs_torch: dict[str, Any] = {}
        flat = None
        if self._policy_execution_device_view is not None:
            flat = torch.from_dlpack(self._policy_execution_device_view)
            if flat.device != target_device:
                flat = flat.to(target_device)
            inst_width = int(self.obs_size)
            contacts_width = int(self.max_contacts) * 5
            rwr_width = int(self.max_rwr) * 4
            obs_torch["instruments"] = flat[:, :inst_width]
            obs_torch["contacts"] = flat[:, inst_width : inst_width + contacts_width].reshape(
                self.num_envs,
                int(self.max_contacts),
                5,
            )
            obs_torch["rwr"] = flat[
                :,
                inst_width + contacts_width : inst_width + contacts_width + rwr_width,
            ].reshape(
                self.num_envs,
                int(self.max_rwr),
                4,
            )
            obs_torch["mission"] = flat[:, inst_width + contacts_width + rwr_width :]

        for key in ("instruments", "contacts", "rwr", "mission"):
            if key not in obs_torch:
                obs_torch[key] = torch.as_tensor(self.buf_obs[key], device=target_device)

        if self.include_proprio:
            obs_torch["proprio"] = torch.as_tensor(self.buf_obs["proprio"], device=target_device)

        if self.include_visual:
            if self._policy_visual_device_view is not None:
                visual = torch.from_dlpack(self._policy_visual_device_view)
                if visual.device != target_device:
                    visual = visual.to(target_device)
                obs_torch["visual"] = visual
            else:
                obs_torch["visual"] = torch.as_tensor(self.buf_obs["visual"], device=target_device)

        if temporal_history_enabled(self.temporal_history_len):
            for key in (
                "instruments_history",
                "contacts_history",
                "rwr_history",
                "mission_history",
                "proprio_history",
            ):
                if key in self.buf_obs:
                    obs_torch[key] = torch.as_tensor(self.buf_obs[key], device=target_device)

        return obs_torch

    def _prepare_batch_flight_shaping_overrides(self) -> None:
        if self.flight_shaping_backend != "gpu_host" or not hasattr(ef_py, "compute_flight_shaping_batch"):
            return
        target_indices: list[int] = []
        inputs_batch = []
        for env_idx, handle in enumerate(self._handles):
            cache = getattr(handle.loader, "_runtime_eval_cache", None)
            if not isinstance(cache, dict):
                continue
            step_eval = cache.get("step_evaluation")
            if not isinstance(step_eval, dict):
                continue
            if step_eval.get("flight_shaping_products_override") is not None:
                continue
            shaping_inputs = step_eval.get("shaping_inputs")
            if shaping_inputs is None:
                continue
            target_indices.append(env_idx)
            inputs_batch.append(shaping_inputs)
        if not inputs_batch:
            return
        try:
            products_batch = ef_py.compute_flight_shaping_batch(inputs_batch, True)
        except Exception:
            return
        if len(products_batch) != len(target_indices):
            return
        for batch_idx, env_idx in enumerate(target_indices):
            cache = getattr(self._handles[env_idx].loader, "_runtime_eval_cache", None)
            if not isinstance(cache, dict):
                continue
            step_eval = cache.get("step_evaluation")
            if not isinstance(step_eval, dict):
                continue
            step_eval["flight_shaping_products_override"] = products_batch[batch_idx]

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

    def _obs_from_buf(self) -> VecEnvObs:
        if self.observation_return_mode == "view":
            obs_dict = OrderedDict((key, value) for key, value in self.buf_obs.items())
            return dict_to_obs(self.observation_space, obs_dict)
        return dict_to_obs(self.observation_space, deepcopy(self.buf_obs))

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
