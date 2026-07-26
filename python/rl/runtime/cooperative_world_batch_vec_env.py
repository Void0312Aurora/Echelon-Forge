from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from typing import Any
import os
import time
import warnings

import numpy as np

try:
    import gymnasium as gym
except ModuleNotFoundError:  # pragma: no cover
    gym = None

import ef_py

from gym_envs.scenario_loader import (
    ScenarioLoader,
    normalize_execution_step_runtime_mode,
)
from gym_envs.universal_env import (
    build_step_info_minimal,
    is_air_combat_hybrid_action_mode,
    make_action_space,
    make_observation_space,
    naval_policy_instruments,
    naval_station_action_command,
    normalize_action,
)
from gym_envs.universal_env_parts import (
    append_temporal_history,
    apply_naval_station_action,
    attach_temporal_history,
    bind_naval_station_eval_reference,
    is_naval_station_action_mode,
    make_temporal_history_buffer,
    temporal_history_enabled,
    validate_naval_action_mode_for_loader,
)
from python.env_config import VALID_FLIGHT_SHAPING_BACKENDS, VALID_STEP_INFO_MODES
from python.rl.runtime.multi_agent_runtime import MultiAgentControlSlot, MultiAgentWorldRuntimeView
from python.rl.support.sb3_vec_env_compat import (
    VecEnv,
    VecEnvIndices,
    VecEnvObs,
    VecEnvStepReturn,
    dict_to_obs,
    obs_space_info,
)
from python.rl.runtime.world_batch import (
    build_loader_step_info,
    compute_loader_step_outcome,
    CooperativeSlotState,
    CooperativeWorldState,
    RuntimeFacadeAdapter,
    ScriptedCooperativeCoordinationDirector,
    clone_small_dict,
    compute_execution_observation_batch,
    copy_obs,
    count_control_slots,
    mission_status_success_flag,
    normalize_batch_observation_backend,
    normalize_batch_visual_backend,
    normalize_flight_shaping_backend,
    observation_timing_snapshot,
    refresh_visual_cache_batch,
)
from python.rl.runtime.world_batch.core import CooperativePlugin, resolve_execution_mode
from python.rl.runtime.world_batch._shared_ops import (
    batch_observation_runtime_base_check,
    diff_single_entity_command_chain,
    normalize_seed as _shared_normalize_seed,
    resolve_batch_observation_backend_mode,
    resolve_batch_visual_backend_mode,
    save_obs_to_buffer,
    submit_command_chain_assignments,
    assemble_observation_dict,
)
from python.rl.control.wrappers import MultiTimescaleActionController
from python.rl.tasking.bridge import resolve_loader_time_step, resolve_tasking_profile, tasking_profile_for_loader
from python.scenario.compiler import ScenarioCompiler
from python.scenario.runtime import build_compiled_world_layout


_copy_obs = copy_obs
_CooperativeWorldState = CooperativeWorldState
_CooperativeSlotState = CooperativeSlotState
_RuntimeFacadeAdapter = RuntimeFacadeAdapter
_clone_small_dict = clone_small_dict
_count_control_slots = count_control_slots
_mission_status_success_flag = mission_status_success_flag
_normalize_batch_observation_backend = normalize_batch_observation_backend
_normalize_batch_visual_backend = normalize_batch_visual_backend
_build_loader_step_info = build_loader_step_info
_compute_loader_step_outcome = compute_loader_step_outcome


def _float32_view(value: Any) -> np.ndarray:
    return np.asarray(value, dtype=np.float32)


class CooperativeWorldBatchVecEnv(VecEnv):
    """
    Multi-agent execution VecEnv for worlds that expose multiple controllable roster members.

    SB3 still sees a flat VecEnv of execution slots, while each slot actually belongs to a
    shared simulation world. All slots in the same world step together and reset together.
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
        batch_observation_backend: str | None = "auto",
        batch_visual_backend: str | None = "auto",
        step_info_mode: str = "full",
        execution_step_runtime_mode: str | None = None,
        flight_shaping_backend: str | None = None,
        collect_step_timing: bool = False,
        database_path: str | None = None,
        worker_threads: int | None = None,
        action_wrapper_kwargs: dict[str, Any] | None = None,
    ) -> None:
        if gym is None:  # pragma: no cover
            raise ModuleNotFoundError(
                "CooperativeWorldBatchVecEnv requires the optional dependency 'gymnasium'. "
                "Install it (e.g. `pip install gymnasium`) to run RL training."
            )
        if render_mode not in (None,):
            raise ValueError("CooperativeWorldBatchVecEnv currently only supports render_mode=None.")
        self.scenario_path = os.path.abspath(str(scenario_path))
        self.world_count = max(1, int(n_envs))
        self.render_mode = render_mode
        self.include_visual = bool(include_visual)
        self.include_proprio = bool(include_proprio)
        self.action_mode = str(action_mode)
        if is_air_combat_hybrid_action_mode(self.action_mode):
            raise ValueError(
                "CooperativeWorldBatchVecEnv does not implement the air-combat event-action "
                "gate/finalization contract; action_mode='air_combat_hybrid_v1' is rejected "
                "instead of silently bypassing C2/ROE and post-launch gating"
            )
        self.mission_obs_mode = str(mission_obs_mode).strip().lower()
        self.visual_downsample = max(1, int(visual_downsample))
        self.visual_update_interval = max(1, int(visual_update_interval))
        self.temporal_history_len = max(1, int(temporal_history_len))
        self.batch_observation_backend = _normalize_batch_observation_backend(batch_observation_backend)
        self.batch_visual_backend = _normalize_batch_visual_backend(batch_visual_backend)
        self.step_info_mode = str(step_info_mode).strip().lower()
        self.execution_step_runtime_mode = (
            normalize_execution_step_runtime_mode(execution_step_runtime_mode)
            if execution_step_runtime_mode is not None
            else None
        )
        self.flight_shaping_backend = _normalize_flight_shaping_backend(flight_shaping_backend)
        self.collect_step_timing = bool(collect_step_timing)
        self._action_wrapper_kwargs = dict(action_wrapper_kwargs or {})
        if self.execution_step_runtime_mode == "legacy":
            raise ValueError("execution_step_runtime_mode='legacy' has been removed from maintained VecEnv paths")
        if self.step_info_mode not in VALID_STEP_INFO_MODES:
            raise ValueError(f"Unknown step_info_mode: {step_info_mode!r}")

        self._compiled_scenario = ScenarioCompiler.compile_path(self.scenario_path)
        runtime_context = self._compiled_scenario.instantiate_runtime_context()
        self.slots_per_world = int(_count_control_slots(runtime_context))
        if self.slots_per_world <= 0:
            raise RuntimeError(
                "cooperative execution requires at least one controllable roster member in the scenario"
            )

        self.num_slots = int(self.world_count) * int(self.slots_per_world)
        self._db_path = (
            os.path.abspath(database_path)
            if database_path
            else os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "examples", "config", "database")
            )
        )
        self._runtime_adapter = _RuntimeFacadeAdapter(self.world_count)
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

        self._worlds = [
            _CooperativeWorldState(
                world_index=world_index,
                director=ScriptedCooperativeCoordinationDirector(),
            )
            for world_index in range(self.world_count)
        ]
        self._slots: list[_CooperativeSlotState | None] = [None for _ in range(self.num_slots)]
        self._actions: np.ndarray | None = None
        self._closed = False

        self._mode_plugin: CooperativePlugin = resolve_execution_mode("cooperative")

        super().__init__(self.num_slots, self.observation_space, self.action_space)

        self.keys, shapes, dtypes = obs_space_info(self.observation_space)
        self.buf_obs = OrderedDict(
            [(key, np.zeros((self.num_envs, *tuple(shapes[key])), dtype=dtypes[key])) for key in self.keys]
        )
        self.buf_dones = np.zeros((self.num_envs,), dtype=bool)
        self.buf_rews = np.zeros((self.num_envs,), dtype=np.float32)
        self.buf_infos: list[dict[str, Any]] = [{} for _ in range(self.num_envs)]
        self.last_step_timing: dict[str, float] = {}
        self.last_reset_timing: dict[str, float] = {}
        self.last_observation_build_timing: dict[str, float] = {}

    @property
    def runtime_facade(self):
        return self._runtime_adapter.facade

    def set_randomization_overrides(self, overrides: dict | None) -> None:
        for world in self._worlds:
            world.set_randomization_overrides(overrides)

    def set_leader_overrides(self, overrides: dict | None) -> None:
        for world in self._worlds:
            world.set_leader_overrides(overrides)

    def _batch_observation_backend_mode(self) -> str:
        return resolve_batch_observation_backend_mode(
            self.batch_observation_backend,
            self._batch_observation_runtime_available(),
        )

    def _batch_observation_runtime_available(self) -> bool:
        return batch_observation_runtime_base_check()

    def _batch_visual_backend_mode(self) -> str:
        return resolve_batch_visual_backend_mode(self.batch_visual_backend)

    def _slot_refs(self, slot_indices: list[int]) -> list[Any]:
        refs: list[Any] = []
        for slot_index in slot_indices:
            slot_state = self._slots[int(slot_index)]
            if slot_state is None:
                continue
            ref = ef_py.WorldEntityRef()
            ref.world_index = int(slot_state.world_index)
            ref.entity_id = int(slot_state.entity_id)
            refs.append(ref)
        return refs

    def _read_slot_state_batch(
        self,
        slot_indices: list[int],
    ) -> tuple[list[int], list[Any], list[Any]]:
        target_slot_indices = [int(slot_index) for slot_index in slot_indices]
        refs = self._slot_refs(target_slot_indices)
        packet = self._runtime_adapter.read_observation_packet(
            refs,
            include_agent_observations=True,
            include_instrument_states=True,
        )
        truth_list = list(getattr(packet, "agent_observations", []) or [])
        inst_list = list(getattr(packet, "instrument_states", []) or [])
        return target_slot_indices, truth_list, inst_list

    def seed(self, seed: int | None = None) -> list[int]:
        base_seed = int(seed) if seed is not None else int(np.random.randint(0, 2**31 - 1))
        seeds: list[int] = []
        for world_index in range(self.world_count):
            world_seed = int(base_seed + world_index)
            seeds.extend([world_seed] * self.slots_per_world)
        self._seeds = list(seeds)
        return list(seeds)

    def _normalize_seed(self, seed: int | None) -> int:
        return _shared_normalize_seed(seed)

    def _build_slot_loader(self, world_index: int, prepared_world, entity_id: int, seed: int) -> ScenarioLoader:
        loader = self._runtime_adapter.make_scenario_loader(int(world_index))
        loader._compiled_scenario = self._compiled_scenario
        loader._compiled_runtime_metadata = self._compiled_scenario.runtime_metadata
        loader._scenario_source_path = self.scenario_path
        if self.execution_step_runtime_mode is not None:
            loader.set_execution_step_runtime_mode(self.execution_step_runtime_mode)
        loader.set_flight_shaping_backend(self.flight_shaping_backend)
        layout = getattr(prepared_world, "layout", None)
        entities = dict(getattr(prepared_world, "entities", {}) or {})
        active_roster = list(getattr(prepared_world, "active_roster", []) or [])

        loader._prepare_load_seed(seed)
        # Each slot loader must own an isolated runtime scenario copy.
        # Cooperative slots live in the same world and share kernel state, but they should not
        # mutate one another's route randomization / mission-command dictionaries through a shared
        # Python object graph during reset/finalize.
        loader._begin_loaded_world(scenario_data=deepcopy(layout.scenario_data))
        loader.rotate_mission_heading_with_world = bool(getattr(layout, "rotate_mission_heading_with_world", False))
        loader.world_yaw_deg = float(getattr(layout, "world_yaw_deg", 0.0))
        loader.world_yaw_origin_x = float(getattr(layout, "world_yaw_origin_x", 0.0))
        loader.world_yaw_origin_y = float(getattr(layout, "world_yaw_origin_y", 0.0))
        loader.entities = entities
        loader.active_roster = active_roster
        loader.agent_id = int(entity_id)
        loader._finalize_loaded_world(sync_to_kernel=True)
        return loader

    def _build_slot_state(
        self,
        *,
        slot_index: int,
        local_slot_index: int,
        world: _CooperativeWorldState,
        control_slot: MultiAgentControlSlot,
        loader: ScenarioLoader,
    ) -> _CooperativeSlotState:
        slot_state = _CooperativeSlotState(
            slot_index=int(slot_index),
            local_slot_index=int(local_slot_index),
            world=world,
            control_slot=control_slot,
            loader=loader,
            max_steps=int(loader.get_max_steps()),
        )
        if self._action_wrapper_kwargs:
            slot_state.action_controller = MultiTimescaleActionController(
                action_space=self.action_space,
                loader_getter=lambda loader=loader: loader,
                dt_getter=lambda loader=loader: float(resolve_loader_time_step(loader)),
                **self._action_wrapper_kwargs,
            )
        slot_state.temporal_history = make_temporal_history_buffer(self.temporal_history_len)
        return slot_state

    def _refresh_visual_batch(self, indices: list[int] | None = None) -> None:
        if not self.include_visual:
            return
        target_indices = list(range(self.num_slots)) if indices is None else [int(i) for i in indices]
        refresh_visual_cache_batch(
            adapter=self._runtime_adapter,
            indexed_states=[
                (slot_index, slot_state)
                for slot_index in target_indices
                for slot_state in [self._slots[int(slot_index)]]
                if slot_state is not None
            ],
            visual_downsample=int(self.visual_downsample),
            visual_update_interval=int(self.visual_update_interval),
            arb_height=int(self.arb_height),
            arb_width=int(self.arb_width),
            arb_channels=int(self.arb_channels),
            arb_height_native=int(self.arb_height_native),
            arb_width_native=int(self.arb_width_native),
            backend=self._batch_visual_backend_mode(),
            allow_device_export=False,
        )

    def _observation_timing_snapshot(self) -> dict[str, float]:
        return observation_timing_snapshot(getattr(self, "last_observation_build_timing", None))

    def _prepare_step_evaluations_batch(
        self,
        target_indices: list[int],
        truth_batch: list[Any],
        inst_batch: list[Any],
        inst_out: np.ndarray,
        ils_batch: np.ndarray,
        mission_inputs_batch: list[Any],
    ) -> list[dict[str, Any]] | None:
        if (
            not target_indices
            or not hasattr(ef_py, "prepare_step_evaluations_batch")
            or not hasattr(ef_py, "compute_execution_episode_runtime_batch")
        ):
            return None

        first_slot = self._slots[int(target_indices[0])]
        if first_slot is None or not hasattr(first_slot.loader, "_build_step_evaluation_batch_env_state"):
            return None

        def _config_tuple(slot_state: _CooperativeSlotState) -> tuple[float, float, float, float]:
            return (
                float(slot_state.loader.mission_cmd.get("target_altitude", 0.0)),
                float(slot_state.loader.mission_cmd.get("target_speed", 0.0)),
                float(slot_state.loader.mission_cmd.get("target_heading", 0.0)),
                float(resolve_loader_time_step(slot_state.loader)),
            )

        ref_cfg = _config_tuple(first_slot)
        for slot_index in target_indices[1:]:
            slot_state = self._slots[int(slot_index)]
            if slot_state is None or _config_tuple(slot_state) != ref_cfg:
                return None

        config = ef_py.StepEvaluationBatchConfig()
        config.target_altitude_m = float(ref_cfg[0])
        config.target_speed_mps = float(ref_cfg[1])
        config.target_heading_deg = float(ref_cfg[2])
        config.time_step_s = float(ref_cfg[3])

        env_states = []
        prepared_entries: list[dict[str, Any] | None] = []
        for batch_idx, slot_index in enumerate(target_indices):
            slot_state = self._slots[int(slot_index)]
            if slot_state is None:
                return None
            state, prepared = slot_state.loader._build_step_evaluation_batch_env_state(
                truth=truth_batch[batch_idx],
                inst_obj=inst_batch[batch_idx],
                inst_vec=np.asarray(inst_out[batch_idx], dtype=np.float32),
                ils_vec=np.asarray(ils_batch[batch_idx], dtype=np.float32),
                steps=int(slot_state.steps),
                max_steps=int(slot_state.max_steps),
                mission_obs_mode=self.mission_obs_mode,
                mission_observation_inputs=mission_inputs_batch[batch_idx],
                return_prepared=True,
            )
            env_states.append(state)
            prepared_entries.append(prepared if isinstance(prepared, dict) else None)

        runtime_inputs_batch = ef_py.prepare_step_evaluations_batch(config, env_states)
        frame_products_batch = ef_py.compute_execution_episode_runtime_batch(runtime_inputs_batch)

        results: list[dict[str, Any]] = []
        for batch_idx, frame_products in enumerate(frame_products_batch):
            slot_state = self._slots[int(target_indices[batch_idx])]
            if slot_state is None:
                continue
            prepared = prepared_entries[batch_idx] if batch_idx < len(prepared_entries) else None
            result: dict[str, Any]
            if isinstance(prepared, dict):
                result = {
                    "truth_obj": truth_batch[batch_idx],
                    "inst_obj": inst_batch[batch_idx],
                    "steps": int(slot_state.steps),
                    "max_steps": int(slot_state.max_steps),
                    "mission_obs_mode": "" if self.mission_obs_mode is None else str(self.mission_obs_mode),
                    "frame_products": frame_products,
                    **prepared,
                }
                cache = getattr(slot_state.loader, "_runtime_eval_cache", None)
                if isinstance(cache, dict):
                    cache["step_evaluation"] = result
            else:
                result = {"frame_products": frame_products}
            results.append(result)
        return results

    def _build_observations_from_cached_state(self, indices: list[int] | None = None) -> list[dict[str, np.ndarray]]:
        target_indices = list(range(self.num_slots)) if indices is None else [int(i) for i in indices]
        if not target_indices:
            return []
        if self.include_visual:
            self._refresh_visual_batch(target_indices)

        backend = self._batch_observation_backend_mode()
        if not self._batch_observation_runtime_available():
            raise RuntimeError("maintained observation batching requires compute_execution_observation_batch_numpy")

        obs_batch_data = compute_execution_observation_batch(
            states=[
                self._slots[int(slot_index)]
                for slot_index in target_indices
                if self._slots[int(slot_index)] is not None
            ],
            mission_obs_mode=self.mission_obs_mode,
            max_contacts=int(self.max_contacts),
            max_rwr=int(self.max_rwr),
            backend=backend,
            allow_device_export=False,
            torch_bridge_enabled=False,
        )
        inst_batch = obs_batch_data.inst_batch
        truth_batch = obs_batch_data.truth_batch
        mission_inputs_batch = obs_batch_data.mission_inputs_batch
        ils_batch = obs_batch_data.ils_batch
        inst_out = obs_batch_data.inst_out
        contacts_out = obs_batch_data.contacts_out
        rwr_out = obs_batch_data.rwr_out
        mission_out = obs_batch_data.mission_out

        step_eval_prepare_ms = 0.0
        step_eval_batch: list[dict[str, Any]] | None = None
        if len(target_indices) > 0:
            try:
                prep_t0 = time.perf_counter()
                step_eval_batch = self._prepare_step_evaluations_batch(
                    target_indices,
                    truth_batch,
                    inst_batch,
                    inst_out,
                    ils_batch,
                    mission_inputs_batch,
                )
                step_eval_prepare_ms = (time.perf_counter() - prep_t0) * 1000.0
            except Exception:
                step_eval_batch = None
                step_eval_prepare_ms = 0.0
        self.last_observation_build_timing = {
            **dict(obs_batch_data.timing),
            "step_eval_prepare_ms": float(step_eval_prepare_ms),
        }

        obs_batch: list[dict[str, np.ndarray]] = []
        for batch_idx, slot_index in enumerate(target_indices):
            slot_state = self._slots[int(slot_index)]
            if slot_state is None:
                continue
            inst_vec = _float32_view(inst_out[batch_idx])
            if slot_state.loader._python_owned_mission_observation_mode(self.mission_obs_mode):
                miss_vec = _float32_view(
                    slot_state.loader.get_mission_observation(
                        self.mission_obs_mode,
                        truth=truth_batch[batch_idx],
                        inst=inst_batch[batch_idx],
                    )
                )
            else:
                miss_vec = _float32_view(mission_out[batch_idx])
            if step_eval_batch is not None and batch_idx < len(step_eval_batch):
                step_eval = step_eval_batch[batch_idx]
            else:
                try:
                    step_eval = slot_state.loader._prepare_step_evaluation(
                        truth=truth_batch[batch_idx],
                        inst_obj=inst_batch[batch_idx],
                        inst_vec=inst_vec,
                        ils_vec=_float32_view(ils_batch[batch_idx]),
                        steps=int(slot_state.steps),
                        max_steps=int(slot_state.max_steps),
                        mission_obs_mode=self.mission_obs_mode,
                    )
                except Exception:
                    step_eval = None
            if isinstance(step_eval, dict):
                frame_products = step_eval.get("frame_products")
                if (
                    not slot_state.loader._python_owned_mission_observation_mode(self.mission_obs_mode)
                    and frame_products is not None
                    and bool(getattr(frame_products, "mission_observation_evaluated", False))
                ):
                    miss_vec = _float32_view(frame_products.mission_observation.values)
            policy_inst_vec = (
                naval_policy_instruments(inst_vec)
                if tasking_profile_for_loader(slot_state.loader) is resolve_tasking_profile("naval")
                else inst_vec
            )
            obs = assemble_observation_dict(
                inst_vec=policy_inst_vec,
                contacts=contacts_out[batch_idx],
                rwr=rwr_out[batch_idx],
                miss_vec=miss_vec,
                max_contacts=int(self.max_contacts),
                max_rwr=int(self.max_rwr),
                include_proprio=self.include_proprio,
                last_action=slot_state.last_action,
                action_dim=int(self.action_space.shape[0]),
            )
            if self.include_visual:
                obs["visual"] = np.asarray(slot_state.visual_cache, dtype=np.float32, copy=False)
            obs_batch.append(self._attach_temporal_history(slot_state, obs))
        return obs_batch

    def _attach_temporal_history(
        self,
        slot_state: _CooperativeSlotState,
        obs: dict[str, np.ndarray],
    ) -> dict[str, np.ndarray]:
        if not temporal_history_enabled(self.temporal_history_len):
            return obs
        if slot_state.temporal_history is None:
            slot_state.temporal_history = make_temporal_history_buffer(self.temporal_history_len)
        append_temporal_history(
            slot_state.temporal_history,
            obs,
            history_len=self.temporal_history_len,
            action_dim=int(self.action_space.shape[0]),
        )
        return attach_temporal_history(
            obs,
            slot_state.temporal_history,
            history_len=self.temporal_history_len,
            action_dim=int(self.action_space.shape[0]),
        )

    def _world_slot_states(self, world: _CooperativeWorldState) -> list[_CooperativeSlotState]:
        slot_states: list[_CooperativeSlotState] = []
        for slot_index in list(world.slot_indices):
            slot_state = self._slots[slot_index]
            if slot_state is not None:
                slot_states.append(slot_state)
        return slot_states

    def _sync_command_chain_batch(self, world_indices: list[int] | None = None) -> None:
        target_world_indices = list(range(self.world_count)) if world_indices is None else [int(i) for i in world_indices]
        mission_assignments: list = []
        task_assignments: list = []
        intent_assignments: list = []
        report_assignments: list = []
        for world_index in target_world_indices:
            world = self._worlds[world_index]
            for slot_index in world.slot_indices:
                slot_state = self._slots[slot_index]
                if slot_state is None:
                    continue
                eid = int(slot_state.entity_id)
                new_m, new_t, new_i, new_r = diff_single_entity_command_chain(
                    int(world_index),
                    eid,
                    slot_state.loader,
                    world.last_mission_command_snapshots.get(eid),
                    world.last_task_order_snapshots.get(eid),
                    world.last_leader_intent_snapshots.get(eid),
                    world.last_pilot_report_snapshots.get(eid),
                    mission_assignments,
                    task_assignments,
                    intent_assignments,
                    report_assignments,
                )
                world.last_mission_command_snapshots[eid] = new_m
                world.last_task_order_snapshots[eid] = new_t
                world.last_leader_intent_snapshots[eid] = new_i
                world.last_pilot_report_snapshots[eid] = new_r
        submit_command_chain_assignments(
            self._runtime_adapter,
            mission_assignments,
            task_assignments,
            intent_assignments,
            report_assignments,
        )
        for world_index in target_world_indices:
            self._worlds[int(world_index)].command_chain_dirty = False

    def _reset_world(self, world_index: int, seed: int | None) -> list[dict[str, np.ndarray]]:
        total_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        normalized_seed = self._normalize_seed(seed)
        world = self._worlds[int(world_index)]
        layout_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        layout = build_compiled_world_layout(
            self._compiled_scenario,
            seed=normalized_seed,
            randomization_overrides=dict(world.randomization_overrides) or None,
        )
        layout_build_ms = (time.perf_counter() - layout_t0) * 1000.0 if self.collect_step_timing else 0.0
        apply_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        applied_world = self._runtime_adapter.apply_world_layout(int(world_index), layout)
        kernel_apply_ms = (time.perf_counter() - apply_t0) * 1000.0 if self.collect_step_timing else 0.0
        active_roster = list(getattr(applied_world, "active_roster", []) or [])
        control_roster = [
            member
            for member in active_roster
            if bool(getattr(member, "is_agent", True))
        ]
        if len(control_roster) != self.slots_per_world:
            raise RuntimeError(
                f"cooperative world {world_index} control roster size changed from "
                f"{self.slots_per_world} to {len(control_roster)}"
            )

        world.routing_loader = None
        world.view = None
        world.slot_indices = []
        base_slot_index = int(world_index) * int(self.slots_per_world)

        for local_slot_index, member in enumerate(control_roster):
            roster_index = active_roster.index(member)
            loader = self._build_slot_loader(
                int(world_index),
                applied_world,
                int(member.entity_id),
                normalized_seed,
            )
            validate_naval_action_mode_for_loader(loader, self.action_mode)
            control_slot = MultiAgentControlSlot(
                world_index=int(world_index),
                entity_id=int(member.entity_id),
                entity_name=str(member.entity_name),
                roster_index=int(roster_index),
                team_id=None if member.team_id is None else int(member.team_id),
                element_id=None if member.element_id is None else int(member.element_id),
                role_code=None if member.role_code is None else int(member.role_code),
                formation_role_id=None if member.formation_role_id is None else str(member.formation_role_id),
                relative_slot_code=None if member.relative_slot_code is None else int(member.relative_slot_code),
                policy_route=None if member.policy_route is None else str(member.policy_route),
                reference_entity_id=None if member.reference_entity_id is None else int(member.reference_entity_id),
                reference_entity_name=(
                    None if member.reference_entity_name is None else str(member.reference_entity_name)
                ),
                mission_command_overrides=_clone_small_dict(getattr(member, "mission_command_overrides", None)),
                task_order_overrides=_clone_small_dict(getattr(member, "task_order_overrides", None)),
            )
            slot_index = int(base_slot_index + local_slot_index)
            slot_state = self._build_slot_state(
                slot_index=slot_index,
                local_slot_index=local_slot_index,
                world=world,
                control_slot=control_slot,
                loader=loader,
            )
            slot_state.visual_cache = None
            slot_state.visual_cache_step = -1
            bind_naval_station_eval_reference(slot_state.loader)
            self._slots[slot_index] = slot_state
            world.slot_indices.append(slot_index)
            if world.routing_loader is None:
                world.routing_loader = loader

        if world.routing_loader is None:
            raise RuntimeError(f"world {world_index} has no cooperative routing loader")

        world.view = MultiAgentWorldRuntimeView(
            runtime=self._runtime_adapter,
            loader=world.routing_loader,
            world_index=int(world_index),
            action_space=self.action_space,
            action_mode=self.action_mode,
            mission_obs_mode=self.mission_obs_mode,
            include_proprio=self.include_proprio,
            max_contacts=self.max_contacts,
            max_rwr=self.max_rwr,
        )
        world.director_dirty = True
        world.command_chain_dirty = True
        world.last_mission_command_snapshots.clear()
        world.last_task_order_snapshots.clear()
        world.last_leader_intent_snapshots.clear()
        world.last_pilot_report_snapshots.clear()
        slot_indices, truth_list, inst_list = self._read_slot_state_batch(list(world.slot_indices))
        for local_slot_index, slot_index in enumerate(slot_indices):
            slot_state = self._slots[slot_index]
            if slot_state is None:
                continue
            slot_state.last_truth = truth_list[local_slot_index] if local_slot_index < len(truth_list) else None
            slot_state.last_inst = inst_list[local_slot_index] if local_slot_index < len(inst_list) else None
        if world.director is not None:
            world.director.reset(world, self._world_slot_states(world))

        obs_batch: list[dict[str, np.ndarray]] = []
        obs_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        for slot_index in world.slot_indices:
            slot_state = self._slots[slot_index]
            if slot_state is None:
                continue
            slot_state.steps = 0
            slot_state.loader.steps = 0
            slot_state.last_action = None
            if slot_state.temporal_history is None:
                slot_state.temporal_history = make_temporal_history_buffer(self.temporal_history_len)
            else:
                slot_state.temporal_history.clear()
            slot_state.episode_return = 0.0
            slot_state.episode_length = 0
            slot_state.coop_success_latched = False
            slot_state.coop_completion_reason = ""
            slot_state.coop_completion_mission_status = None
            slot_state.coop_completion_info = None
            slot_state.coop_completion_terminal_observation = None
        obs_batch = self._build_observations_from_cached_state(list(world.slot_indices))
        for local_slot_index, slot_index in enumerate(world.slot_indices):
            slot_state = self._slots[slot_index]
            if slot_state is None:
                continue
            obs = obs_batch[local_slot_index]
            slot_state.last_obs = obs
            if slot_state.action_controller is not None:
                slot_state.action_controller.reset_state(_copy_obs(obs))
        if self.collect_step_timing:
            self.last_reset_timing = {
                "layout_build_ms": float(layout_build_ms),
                "kernel_apply_ms": float(kernel_apply_ms),
                "obs_build_ms": float((time.perf_counter() - obs_t0) * 1000.0),
                "total_ms": float((time.perf_counter() - total_t0) * 1000.0),
            }
        return obs_batch

    def reset(self) -> VecEnvObs:
        total_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        for world_index in range(self.world_count):
            world_seed = self._seeds[int(world_index * self.slots_per_world)]
            obs_batch = self._reset_world(world_index, seed=world_seed)
            for local_slot_index, obs in enumerate(obs_batch):
                slot_index = int(world_index * self.slots_per_world + local_slot_index)
                slot_state = self._slots[slot_index]
                if slot_state is None:
                    continue
                self.reset_infos[slot_index] = {
                    "world_index": int(world_index),
                    "entity_id": int(slot_state.entity_id),
                    "entity_name": str(slot_state.entity_name),
                }
                if self.collect_step_timing:
                    self.reset_infos[slot_index]["timing"] = dict(self.last_reset_timing)
                self._save_obs(slot_index, obs)
        if self.collect_step_timing:
            self.last_reset_timing["total_reset_ms"] = float((time.perf_counter() - total_t0) * 1000.0)
        self._reset_seeds()
        self._reset_options()
        return self._obs_from_buf()

    def _prepare_slot_action(
        self,
        slot_state: _CooperativeSlotState,
        action: np.ndarray,
    ) -> tuple[np.ndarray, Any]:
        effective_action = normalize_action(
            action,
            action_space=self.action_space,
            action_mode=self.action_mode,
        )
        prepared = None
        if slot_state.action_controller is not None:
            prepared = slot_state.action_controller.prepare_action(effective_action)
            effective_action = np.asarray(prepared.action, dtype=np.float32).reshape(-1)
        if is_naval_station_action_mode(self.action_mode):
            effective_action = naval_station_action_command(effective_action)
        slot_state.last_action = np.asarray(effective_action, dtype=np.float32, copy=True)
        return slot_state.last_action.astype(np.float32, copy=True), prepared

    def _neutral_hold_action(self, slot_state: _CooperativeSlotState) -> np.ndarray:
        action = np.zeros(self.action_space.shape, dtype=np.float32)
        if self.action_mode == "full":
            inst = slot_state.last_inst
            throttle = 0.0
            gear = 0.0
            flaps = 0.0
            speedbrake = 0.0
            if inst is not None:
                try:
                    throttle = float(np.clip(getattr(inst, "throttle_pos", 0.0), 0.0, 1.0))
                except Exception:
                    throttle = 0.0
                try:
                    gear = float(np.clip(getattr(inst, "gear_pos", 0.0), 0.0, 1.0))
                except Exception:
                    gear = 0.0
                try:
                    flaps = float(np.clip(getattr(inst, "flaps_pos", 0.0), 0.0, 1.0))
                except Exception:
                    flaps = 0.0
                try:
                    speedbrake = float(np.clip(getattr(inst, "speedbrake_pos", 0.0), 0.0, 1.0))
                except Exception:
                    speedbrake = 0.0
            action[3] = throttle
            action[4] = gear
            action[5] = np.clip(0.5 + 0.5 * flaps, 0.0, 1.0)
            action[6] = np.clip(0.5 + 0.5 * speedbrake, 0.0, 1.0)
        return normalize_action(action, action_space=self.action_space, action_mode=self.action_mode)

    def step_async(self, actions: np.ndarray) -> None:
        action_arr = np.asarray(actions, dtype=np.float32)
        if self.num_envs == 1 and action_arr.ndim == 1:
            action_arr = action_arr.reshape(1, -1)
        self._actions = action_arr

    def step_wait(self) -> VecEnvStepReturn:
        if self._actions is None:
            raise RuntimeError("step_async() must be called before step_wait().")

        total_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        dirty_world_indices = [
            int(world.world_index)
            for world in self._worlds
            if bool(world.command_chain_dirty)
        ]
        sync_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        if dirty_world_indices:
            self._sync_command_chain_batch(dirty_world_indices)
        command_sync_ms = (time.perf_counter() - sync_t0) * 1000.0 if self.collect_step_timing else 0.0

        prepared_by_slot: dict[int, Any] = {}
        naval_action_sync_world_indices: set[int] = set()
        action_prepare_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        for world in self._worlds:
            if world.view is None:
                raise RuntimeError(f"world {world.world_index} has not been reset")
            actions_by_entity_id: dict[int, np.ndarray] = {}
            inst_by_entity_id: dict[int, Any] = {}
            for slot_index in world.slot_indices:
                slot_state = self._slots[slot_index]
                if slot_state is None:
                    continue
                if bool(slot_state.coop_success_latched):
                    effective_action = self._neutral_hold_action(slot_state)
                    prepared = None
                    if is_naval_station_action_mode(self.action_mode):
                        effective_action = naval_station_action_command(effective_action)
                    slot_state.last_action = np.asarray(effective_action, dtype=np.float32, copy=True)
                else:
                    effective_action, prepared = self._prepare_slot_action(slot_state, self._actions[slot_index])
                if is_naval_station_action_mode(self.action_mode):
                    if apply_naval_station_action(slot_state.loader, effective_action):
                        naval_action_sync_world_indices.add(int(world.world_index))
                actions_by_entity_id[int(slot_state.entity_id)] = effective_action
                inst_by_entity_id[int(slot_state.entity_id)] = slot_state.last_inst
                prepared_by_slot[int(slot_index)] = prepared
            world.view.apply_actions(actions_by_entity_id, inst_by_entity_id=inst_by_entity_id)
        action_prepare_ms = (time.perf_counter() - action_prepare_t0) * 1000.0 if self.collect_step_timing else 0.0

        step_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        if naval_action_sync_world_indices:
            sync_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            self._sync_command_chain_batch(sorted(naval_action_sync_world_indices))
            if self.collect_step_timing:
                command_sync_ms += (time.perf_counter() - sync_t0) * 1000.0
        self._runtime_adapter.step_worlds(list(range(self.world_count)))
        batch_step_ms = (time.perf_counter() - step_t0) * 1000.0 if self.collect_step_timing else 0.0

        # Refresh per-slot state first, then update the per-slot behavior layers, then sync the
        # command chain back to the kernel for the next world step.
        state_read_ms = 0.0
        behavior_update_ms = 0.0
        active_slot_indices = [
            int(slot_index)
            for world in self._worlds
            if world.view is not None
            for slot_index in world.slot_indices
        ]
        read_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        slot_indices, truth_list, inst_list = self._read_slot_state_batch(active_slot_indices)
        for local_slot_index, slot_index in enumerate(slot_indices):
            slot_state = self._slots[slot_index]
            if slot_state is None:
                continue
            slot_state.last_truth = truth_list[local_slot_index] if local_slot_index < len(truth_list) else None
            slot_state.last_inst = inst_list[local_slot_index] if local_slot_index < len(inst_list) else None
        if self.collect_step_timing:
            state_read_ms = (time.perf_counter() - read_t0) * 1000.0
        for world in self._worlds:
            if world.view is None:
                continue
            behavior_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            for slot_index in world.slot_indices:
                slot_state = self._slots[slot_index]
                if slot_state is None:
                    continue
                slot_state.steps += 1
                slot_state.loader.steps = int(slot_state.steps)
                sim_time = float(slot_state.steps) * float(
                    resolve_loader_time_step(slot_state.loader)
                )
                self._mode_plugin.update_post_step_behavior(
                    slot_state, sim_time, slot_state.last_truth, slot_state.last_inst,
                )
            if world.director is not None:
                world.director.update(world, self._world_slot_states(world), force=True)
            world.command_chain_dirty = True
            if self.collect_step_timing:
                behavior_update_ms += (time.perf_counter() - behavior_t0) * 1000.0
        sync_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        if not self._mode_plugin.skip_post_behavior_command_sync:
            self._sync_command_chain_batch()
        if self.collect_step_timing:
            command_sync_ms += (time.perf_counter() - sync_t0) * 1000.0

        rewards = np.zeros((self.num_envs,), dtype=np.float32)
        dones = np.zeros((self.num_envs,), dtype=bool)
        infos: list[dict[str, Any]] = [{} for _ in range(self.num_envs)]

        obs_build_ms = 0.0
        reward_info_ms = 0.0
        for world in self._worlds:
            world_done = False
            world_success = True
            world_failure = False
            world_timeout = False
            slot_results: list[tuple[int, dict[str, np.ndarray], float, bool, bool, dict[str, Any], float, int]] = []
            obs_by_slot_index: dict[int, dict[str, np.ndarray]] = {}
            obs_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            world_obs_batch = self._build_observations_from_cached_state(list(world.slot_indices))
            if self.collect_step_timing:
                obs_build_ms += (time.perf_counter() - obs_t0) * 1000.0
            for local_slot_index, slot_index in enumerate(world.slot_indices):
                if local_slot_index < len(world_obs_batch):
                    obs_by_slot_index[int(slot_index)] = world_obs_batch[local_slot_index]
            for slot_index in world.slot_indices:
                slot_state = self._slots[slot_index]
                if slot_state is None:
                    continue
                obs = obs_by_slot_index[int(slot_index)]
                reward_t0 = time.perf_counter() if self.collect_step_timing else 0.0
                if bool(slot_state.coop_success_latched) and slot_state.coop_completion_mission_status is not None:
                    reward = 0.0
                    terminated = False
                    truncated = False
                    mission_status = np.asarray(slot_state.coop_completion_mission_status, dtype=np.float32)
                    info = dict(slot_state.coop_completion_info or {})
                else:
                    cache = getattr(slot_state.loader, "_runtime_eval_cache", None)
                    cached_step_eval = cache.get("step_evaluation") if isinstance(cache, dict) else None
                    reward, terminated, truncated, mission_status = _compute_loader_step_outcome(
                        slot_state.loader,
                        obs=obs,
                        steps=slot_state.steps,
                        max_steps=slot_state.max_steps,
                        truth=slot_state.last_truth,
                        inst_state=slot_state.last_inst,
                        step_evaluation=cached_step_eval if isinstance(cached_step_eval, dict) else None,
                    )
                    if self.step_info_mode == "off" or (
                        self.step_info_mode == "terminal" and not bool(terminated or truncated)
                    ):
                        info = build_step_info_minimal(
                            slot_state.loader,
                            mission_status=mission_status,
                            terminated=bool(terminated),
                            truncated=bool(truncated),
                        )
                    else:
                        info = _build_loader_step_info(
                            slot_state.loader,
                            entity_id=int(slot_state.entity_id),
                            mission_status=mission_status,
                            terminated=bool(terminated),
                            truncated=bool(truncated),
                            inst_now=slot_state.last_inst,
                            truth_now=slot_state.last_truth,
                        )
                if self.collect_step_timing:
                    reward_info_ms += (time.perf_counter() - reward_t0) * 1000.0

                prepared = prepared_by_slot.get(int(slot_index))
                if slot_state.action_controller is not None and prepared is not None:
                    obs, reward, info = slot_state.action_controller.finalize_step_result(obs, reward, info, prepared)
                slot_state.last_obs = obs
                slot_state.episode_return += float(reward)
                slot_state.episode_length += 1

                success = _mission_status_success_flag(mission_status)
                truncated = bool(truncated)
                terminated = bool(terminated)
                reason = str(info.get("termination_reason", "") or "").strip().lower()
                failure = bool(terminated and not success)
                timeout = bool(truncated and not terminated)

                if success and not bool(slot_state.coop_success_latched):
                    slot_state.coop_success_latched = True
                    slot_state.coop_completion_reason = str(info.get("termination_reason", "") or "success_waypoint")
                    slot_state.coop_completion_mission_status = np.asarray(mission_status, dtype=np.float32, copy=True)
                    slot_state.coop_completion_info = dict(info)
                    slot_state.coop_completion_terminal_observation = _copy_obs(obs)
                elif bool(slot_state.coop_success_latched):
                    success = True
                    terminated = False
                    truncated = False
                    failure = False
                    timeout = False

                if bool(slot_state.coop_success_latched):
                    info["coop_slot_success_latched"] = 1.0
                    info["coop_slot_complete"] = 1.0
                else:
                    info["coop_slot_success_latched"] = 0.0
                    info["coop_slot_complete"] = 0.0
                info["coop_slot_terminal_success"] = float(success)
                info["coop_slot_terminal_failure"] = float(failure)
                info["coop_slot_terminal_timeout"] = float(timeout)
                if success and slot_state.coop_completion_reason:
                    info["termination_reason"] = slot_state.coop_completion_reason

                world_success = bool(world_success and success)
                world_failure = bool(world_failure or failure)
                world_timeout = bool(world_timeout or timeout)
                slot_results.append(
                    (
                        slot_index,
                        obs,
                        float(reward),
                        bool(terminated),
                        bool(truncated),
                        info,
                        float(slot_state.episode_return),
                        int(slot_state.episode_length),
                    )
                )

            if not slot_results:
                continue

            world_done = bool(world_failure or world_timeout or world_success)
            if world_done:
                terminal_obs = {}
                for slot_index, obs, *_rest in slot_results:
                    slot_state = self._slots[slot_index]
                    if slot_state is not None and slot_state.coop_completion_terminal_observation is not None:
                        terminal_obs[int(slot_index)] = _copy_obs(slot_state.coop_completion_terminal_observation)
                    else:
                        terminal_obs[int(slot_index)] = _copy_obs(obs)
                reset_obs_batch = self._reset_world(world.world_index, seed=None)
                reset_by_local_slot = {
                    int(local_slot_index): obs
                    for local_slot_index, obs in enumerate(reset_obs_batch)
                }

            for slot_index, obs, reward, terminated, truncated, info, episode_return, episode_length in slot_results:
                slot_state = self._slots[slot_index]
                if slot_state is None:
                    continue
                rewards[slot_index] = float(reward)
                infos[slot_index] = dict(info)
                infos[slot_index]["world_index"] = int(slot_state.world_index)
                infos[slot_index]["slot_index"] = int(slot_state.slot_index)
                infos[slot_index]["local_slot_index"] = int(slot_state.local_slot_index)
                infos[slot_index]["slots_per_world"] = int(self.slots_per_world)
                infos[slot_index]["entity_id"] = int(slot_state.entity_id)
                infos[slot_index]["entity_name"] = str(slot_state.entity_name)
                infos[slot_index]["formation_role_id"] = (
                    None
                    if slot_state.control_slot.formation_role_id is None
                    else str(slot_state.control_slot.formation_role_id)
                )
                infos[slot_index]["role_code"] = (
                    None if slot_state.control_slot.role_code is None else int(slot_state.control_slot.role_code)
                )
                infos[slot_index]["relative_slot_code"] = (
                    None
                    if slot_state.control_slot.relative_slot_code is None
                    else int(slot_state.control_slot.relative_slot_code)
                )
                infos[slot_index]["world_done"] = float(bool(world_done))
                infos[slot_index]["world_success"] = float(bool(world_success))
                infos[slot_index]["world_failure"] = float(bool(world_failure))
                infos[slot_index]["world_timeout"] = float(bool(world_timeout))
                slot_completed = bool(float(infos[slot_index].get("coop_slot_complete", 0.0)) > 0.5)
                infos[slot_index]["shared_world_reset"] = float(
                    bool(world_done and not slot_completed and not (world_failure or world_timeout or (terminated or truncated)))
                )
                infos[slot_index]["policy_route"] = (
                    None if slot_state.control_slot.policy_route is None else str(slot_state.control_slot.policy_route)
                )
                if world_done:
                    infos[slot_index]["terminal_observation"] = terminal_obs[int(slot_index)]
                    # A shared-world failure takes precedence over a simultaneous
                    # timeout.  Marking every slot as time-limit truncated in the
                    # mixed case causes value bootstrapping across a true terminal
                    # failure in SB3-compatible consumers.
                    infos[slot_index]["TimeLimit.truncated"] = bool(
                        world_timeout and not world_failure
                    )
                    infos[slot_index]["episode"] = {
                        "r": round(float(episode_return), 6),
                        "l": int(episode_length),
                    }
                    dones[slot_index] = True
                    reset_obs = reset_by_local_slot[int(slot_state.local_slot_index)]
                    self._save_obs(slot_index, reset_obs)
                else:
                    infos[slot_index]["TimeLimit.truncated"] = False
                    dones[slot_index] = False
                    self._save_obs(slot_index, obs)

        if self.collect_step_timing:
            self.last_step_timing = {
                "action_prepare_ms": float(action_prepare_ms),
                "batch_step_ms": float(batch_step_ms),
                "state_read_ms": float(state_read_ms),
                "behavior_update_ms": float(behavior_update_ms),
                "command_sync_ms": float(command_sync_ms),
                "obs_build_ms": float(obs_build_ms),
                "reward_info_ms": float(reward_info_ms),
                "total_ms": float((time.perf_counter() - total_t0) * 1000.0),
            }
            self.last_step_timing.update(self._observation_timing_snapshot())
            for info in infos:
                info["timing"] = dict(self.last_step_timing)
        else:
            self.last_step_timing = {}
        self.buf_rews[:] = rewards
        self.buf_dones[:] = dones
        self.buf_infos = infos
        self._actions = None
        return self._obs_from_buf(), np.copy(self.buf_rews), np.copy(self.buf_dones), list(self.buf_infos)

    def close(self) -> None:
        self._actions = None
        self._closed = True

    def get_images(self) -> list[np.ndarray | None]:
        if self.render_mode != "rgb_array":
            warnings.warn(
                f"The render mode is {self.render_mode}, but this method assumes it is `rgb_array` to obtain images."
            )
        return [None for _ in range(self.num_envs)]

    def get_attr(self, attr_name: str, indices: VecEnvIndices = None) -> list[Any]:
        if attr_name == "render_mode" and any(slot_state is None for slot_state in self._slots):
            return [self.render_mode for _ in self._get_indices(indices)]
        target_slots = self._get_target_slots(indices)
        values = []
        for slot_state in target_slots:
            if hasattr(slot_state, attr_name):
                values.append(getattr(slot_state, attr_name))
            elif hasattr(slot_state.loader, attr_name):
                values.append(getattr(slot_state.loader, attr_name))
            elif hasattr(slot_state.world, attr_name):
                values.append(getattr(slot_state.world, attr_name))
            else:
                raise AttributeError(attr_name)
        return values

    def set_attr(self, attr_name: str, value: Any, indices: VecEnvIndices = None) -> None:
        for slot_state in self._get_target_slots(indices):
            if hasattr(slot_state, attr_name):
                setattr(slot_state, attr_name, value)
            elif hasattr(slot_state.loader, attr_name):
                setattr(slot_state.loader, attr_name, value)
            elif hasattr(slot_state.world, attr_name):
                setattr(slot_state.world, attr_name, value)
            else:
                raise AttributeError(attr_name)

    def env_method(self, method_name: str, *method_args, indices: VecEnvIndices = None, **method_kwargs) -> list[Any]:
        if all(slot_state is None for slot_state in self._slots):
            world_results = []
            for world_index in self._get_indices(indices):
                if world_index < 0 or world_index >= len(self._worlds):
                    continue
                world = self._worlds[int(world_index)]
                if hasattr(world, method_name):
                    method = getattr(world, method_name)
                    world_results.append(method(*method_args, **method_kwargs))
                    continue
                if hasattr(self, method_name):
                    method = getattr(self, method_name)
                    world_results.append(method(*method_args, indices=[int(world_index)], **method_kwargs))
                    continue
                raise RuntimeError(f"cooperative slot {world_index} is not initialized")
            if world_results:
                return world_results
        results = []
        for slot_state in self._get_target_slots(indices):
            if hasattr(slot_state, method_name):
                method = getattr(slot_state, method_name)
            elif hasattr(slot_state.loader, method_name):
                method = getattr(slot_state.loader, method_name)
            elif hasattr(slot_state.world, method_name):
                method = getattr(slot_state.world, method_name)
            else:
                raise AttributeError(method_name)
            results.append(method(*method_args, **method_kwargs))
        return results

    def env_is_wrapped(self, wrapper_class: type[gym.Wrapper], indices: VecEnvIndices = None) -> list[bool]:
        _ = wrapper_class
        return [False for _ in self._get_indices(indices)]

    def _get_target_slots(self, indices: VecEnvIndices) -> list[_CooperativeSlotState]:
        slots: list[_CooperativeSlotState] = []
        for index in self._get_indices(indices):
            slot_state = self._slots[int(index)]
            if slot_state is None:
                raise RuntimeError(f"cooperative slot {index} is not initialized")
            slots.append(slot_state)
        return slots

    def _save_obs(self, env_idx: int, obs: VecEnvObs) -> None:
        save_obs_to_buffer(self.buf_obs, self.keys, env_idx, obs)

    def _obs_from_buf(self) -> VecEnvObs:
        return dict_to_obs(self.observation_space, deepcopy(self.buf_obs))

    def slot_control_slots(self) -> list[MultiAgentControlSlot]:
        out: list[MultiAgentControlSlot] = []
        for slot_state in self._slots:
            if slot_state is not None:
                out.append(slot_state.control_slot)
        return out

    def slot_indices_by_policy_route(self) -> dict[str, list[int]]:
        out: dict[str, list[int]] = {}
        for slot_state in self._slots:
            if slot_state is None:
                continue
            route = str(slot_state.control_slot.policy_route or "default")
            out.setdefault(route, []).append(int(slot_state.slot_index))
        return out


def _normalize_flight_shaping_backend(value: str | None) -> str:
    backend = "auto" if value is None else normalize_flight_shaping_backend(value)
    if backend in VALID_FLIGHT_SHAPING_BACKENDS:
        return backend
    raise ValueError(f"Unknown flight_shaping_backend: {value!r}")
