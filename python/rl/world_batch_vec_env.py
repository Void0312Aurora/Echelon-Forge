from __future__ import annotations

from collections import OrderedDict
from collections.abc import Sequence
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any
import os
import time
import warnings

import gymnasium as gym
import numpy as np
from stable_baselines3.common.vec_env.base_vec_env import VecEnv, VecEnvIndices, VecEnvObs, VecEnvStepReturn
from stable_baselines3.common.vec_env.util import dict_to_obs, obs_space_info

try:
    import torch
except Exception:  # pragma: no cover - training envs are expected to have torch
    torch = None

import ef_py

from gym_envs.scenario_loader import (
    ScenarioLoader,
    normalize_execution_step_runtime_mode,
    normalize_flight_shaping_backend,
)
from gym_envs.universal_env import (
    build_pilot_action,
    build_step_info,
    build_step_info_minimal,
    build_universal_observation,
    downsample_visual_mean,
    make_action_space,
    make_observation_space,
    normalize_action,
)
from python.rl.leader_tasking import build_kernel_mission_command
from python.rl.wrappers import MultiTimescaleActionController
from python.scenario_compiler import ScenarioCompiler
from python.scenario_runtime import (
    BatchWorldApplyBuffer,
    apply_world_layout_to_kernel,
    build_compiled_world_layout,
    load_compiled_scenario_batch,
)


def _copy_obs(obs: Any) -> Any:
    if isinstance(obs, dict):
        return {key: _copy_obs(value) for key, value in obs.items()}
    if isinstance(obs, tuple):
        return tuple(_copy_obs(value) for value in obs)
    return np.array(obs, copy=True)


def _normalize_batch_observation_backend(value: str | None) -> str:
    backend = "auto" if value is None else str(value).strip().lower()
    if backend in ("", "auto"):
        return "auto"
    if backend in ("legacy", "compiled", "gpu_host"):
        return backend
    raise ValueError(f"Unknown batch_observation_backend: {value!r}")


def _normalize_batch_visual_backend(value: str | None) -> str:
    backend = "auto" if value is None else str(value).strip().lower()
    if backend in ("", "auto"):
        return "auto"
    if backend in ("legacy", "compiled", "gpu_host"):
        return backend
    raise ValueError(f"Unknown batch_visual_backend: {value!r}")


def _normalize_flight_shaping_backend(value: str | None) -> str:
    backend = "auto" if value is None else normalize_flight_shaping_backend(value)
    if backend in ("auto", "legacy", "compiled", "gpu_host"):
        return backend
    raise ValueError(f"Unknown flight_shaping_backend: {value!r}")


def _normalize_observation_return_mode(value: str | None) -> str:
    mode = "copy" if value is None else str(value).strip().lower()
    if mode in ("", "copy"):
        return "copy"
    if mode == "view":
        return "view"
    raise ValueError(f"Unknown observation_return_mode: {value!r}")


@dataclass
class _BatchWorldHandle:
    env_idx: int
    loader: ScenarioLoader
    scenario_path: str
    render_mode: str | None
    include_visual: bool
    include_proprio: bool
    action_mode: str
    mission_obs_mode: str
    agent_id: int | None = None
    max_steps: int = 1000
    steps: int = 0
    last_action: np.ndarray | None = None
    last_inst: Any = None
    last_truth: Any = None
    randomization_overrides: dict[str, Any] = field(default_factory=dict)
    episode_return: float = 0.0
    episode_length: int = 0
    visual_cache: np.ndarray | None = None
    visual_cache_step: int = -1
    action_controller: MultiTimescaleActionController | None = None

    def set_randomization_overrides(self, overrides: dict | None) -> None:
        self.loader.set_randomization_overrides(overrides)
        self.randomization_overrides = dict(getattr(self.loader, "randomization_overrides", {}) or {})


class WorldBatchVecEnv(VecEnv):
    """
    Single-process execution-layer VecEnv backed by `ef_py.WorldBatchRuntime`.

    This is the maintained execution-layer batch adapter for `WorldBatchRuntime`.
    It keeps execution policy rollouts on one process and uses C++ batch
    stepping/reads across worlds. Visual observations can optionally use the
    batched visual helper path instead of per-world kernel readback.
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
        step_info_mode: str = "full",
        execution_step_runtime_mode: str | None = None,
        flight_shaping_backend: str | None = None,
        database_path: str | None = None,
        worker_threads: int | None = None,
        collect_step_timing: bool = False,
        batch_observation_backend: str | None = "auto",
        batch_visual_backend: str | None = "auto",
        policy_observation_torch_bridge: bool = True,
        observation_return_mode: str = "copy",
        action_wrapper_kwargs: dict[str, Any] | None = None,
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
        self.step_info_mode = str(step_info_mode).strip().lower()
        self.execution_step_runtime_mode = (
            normalize_execution_step_runtime_mode(execution_step_runtime_mode)
            if execution_step_runtime_mode is not None
            else None
        )
        self.flight_shaping_backend = _normalize_flight_shaping_backend(flight_shaping_backend)
        if self.execution_step_runtime_mode not in (None, "compiled", "legacy"):
            raise ValueError(f"Unknown execution_step_runtime_mode: {execution_step_runtime_mode!r}")
        if self.step_info_mode not in ("full", "terminal", "off"):
            raise ValueError(f"Unknown step_info_mode: {step_info_mode!r}")
        self.collect_step_timing = bool(collect_step_timing)
        self.batch_observation_backend = _normalize_batch_observation_backend(batch_observation_backend)
        self.batch_visual_backend = _normalize_batch_visual_backend(batch_visual_backend)
        self.policy_observation_torch_bridge = bool(policy_observation_torch_bridge)
        self.observation_return_mode = _normalize_observation_return_mode(observation_return_mode)
        self._action_wrapper_kwargs = dict(action_wrapper_kwargs or {})
        self.last_step_timing: dict[str, float] = {}
        self.last_reset_timing: dict[str, float] = {}
        self._db_path = (
            os.path.abspath(database_path)
            if database_path
            else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "examples", "config", "database"))
        )
        self._compiled_scenario = ScenarioCompiler.compile_path(self.scenario_path)
        self._batch_runtime = ef_py.WorldBatchRuntime(self.n_envs)
        self._batch_apply_buffer = BatchWorldApplyBuffer(self.n_envs)
        self._worker_threads = None if worker_threads is None else max(0, int(worker_threads))
        if self._worker_threads is not None:
            self._batch_runtime.set_worker_threads(int(self._worker_threads))
        if not bool(self._batch_runtime.load_database(self._db_path)):
            raise RuntimeError(f"failed to load database into WorldBatchRuntime: {self._db_path}")

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
            obs_size=self.obs_size,
            max_contacts=self.max_contacts,
            max_rwr=self.max_rwr,
        )

        self._handles = [
            _BatchWorldHandle(
                env_idx=env_idx,
                loader=ScenarioLoader(self._batch_runtime.world(env_idx)),
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
            if self._action_wrapper_kwargs:
                handle.action_controller = MultiTimescaleActionController(
                    action_space=self.action_space,
                    loader_getter=lambda handle=handle: handle.loader,
                    dt_getter=lambda env_idx=handle.env_idx, self=self: float(self._batch_runtime.world(env_idx).get_time_step()),
                    **self._action_wrapper_kwargs,
                )
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
    def batch_runtime(self):
        return self._batch_runtime

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

    def _collect_observations(self, indices: Sequence[int] | None = None) -> list[dict[str, np.ndarray]]:
        target_indices, refs = self._build_refs(indices)
        inst_list = self._batch_runtime.get_instrument_states_batch(refs)
        truth_list = self._batch_runtime.get_agent_observations_batch(refs)
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
            return "compiled" if self._batch_visual_runtime_available() else "legacy"
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

    def _refresh_visual_batch(self, indices: Sequence[int] | None = None) -> None:
        if not self.include_visual:
            return
        target_indices = list(range(self.num_envs)) if indices is None else [int(i) for i in indices]
        refresh_indices = []
        for env_idx in target_indices:
            handle = self._handles[env_idx]
            need_refresh = (
                handle.visual_cache is None
                or self.visual_update_interval <= 1
                or handle.steps <= 0
                or (int(handle.steps) - int(handle.visual_cache_step)) >= self.visual_update_interval
            )
            if need_refresh:
                refresh_indices.append(env_idx)

        if not refresh_indices:
            return

        full_refresh = self._is_full_batch_indices(refresh_indices)

        backend = self._batch_visual_backend_mode()
        if backend == "legacy" or not self._batch_visual_runtime_available():
            if refresh_indices:
                self._policy_visual_device_view = None
            for env_idx in refresh_indices:
                handle = self._handles[env_idx]
                if handle.agent_id is None:
                    raise RuntimeError(f"world {env_idx} has no active agent_id")
                world = self._batch_runtime.world(env_idx)
                if self.visual_downsample > 1 and hasattr(world, "get_visual_observation_downsampled"):
                    visual_raw = world.get_visual_observation_downsampled(int(handle.agent_id), self.visual_downsample)
                    visual = np.asarray(visual_raw, dtype=np.float32)
                    if visual.ndim == 1:
                        visual = visual.reshape(self.arb_height, self.arb_width, self.arb_channels)
                    handle.visual_cache = visual
                else:
                    visual_raw = world.get_visual_observation(int(handle.agent_id))
                    visual = np.asarray(visual_raw, dtype=np.float32)
                    if visual.ndim == 1:
                        visual = visual.reshape(self.arb_height_native, self.arb_width_native, self.arb_channels)
                    handle.visual_cache = downsample_visual_mean(visual, self.visual_downsample)
                handle.visual_cache_step = int(handle.steps)
            return

        _target_indices, refs = self._build_refs(refresh_indices)
        device_view = None
        if (
            backend == "gpu_host"
            and full_refresh
            and self._policy_torch_bridge_enabled
            and hasattr(ef_py, "compute_world_batch_visual_observation_batch_export")
        ):
            visuals, device_view = ef_py.compute_world_batch_visual_observation_batch_export(
                self._batch_runtime,
                refs,
                int(self.visual_downsample),
                True,
            )
        else:
            visuals = ef_py.compute_world_batch_visual_observation_batch_numpy(
                self._batch_runtime,
                refs,
                int(self.visual_downsample),
                backend == "gpu_host",
            )
            device_view = None
        visuals = np.asarray(visuals, dtype=np.float32)
        for batch_idx, env_idx in enumerate(refresh_indices):
            handle = self._handles[env_idx]
            handle.visual_cache = np.asarray(visuals[batch_idx], dtype=np.float32)
            handle.visual_cache_step = int(handle.steps)
        self._policy_visual_device_view = device_view if full_refresh else None

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
                obs_batch.append(self._attach_visual_observation(env_idx, obs))
            return obs_batch

        inst_batch = []
        truth_batch = []
        mission_inputs_batch = []
        ils_batch = np.zeros((len(target_indices), 4), dtype=np.float32)
        for batch_idx, env_idx in enumerate(target_indices):
            handle = self._handles[env_idx]
            if handle.last_inst is None or handle.last_truth is None:
                raise RuntimeError(f"world {env_idx} has no cached state for observation build")
            inst = handle.last_inst
            truth = handle.last_truth
            if hasattr(handle.loader, "reset_runtime_eval_cache"):
                try:
                    handle.loader.reset_runtime_eval_cache()
                except Exception:
                    pass
            inst_batch.append(inst)
            truth_batch.append(truth)
            mission_inputs_batch.append(
                handle.loader._build_mission_observation_runtime_inputs(
                    self.mission_obs_mode,
                    truth=truth,
                    inst=inst,
                )
            )
            ils_vec = handle.loader.get_ils_observation(float(truth.x), float(truth.y), float(inst.alt_baro))
            ils_batch[batch_idx, :] = np.asarray(ils_vec[:4], dtype=np.float32)

        execution_device_view = None
        if (
            backend == "gpu_host"
            and self._is_full_batch_indices(target_indices)
            and self._policy_torch_bridge_enabled
            and hasattr(ef_py, "compute_execution_observation_batch_export")
        ):
            inst_out, contacts_out, rwr_out, mission_out, execution_device_view = (
                ef_py.compute_execution_observation_batch_export(
                    inst_batch,
                    truth_batch,
                    mission_inputs_batch,
                    ils_batch,
                    int(self.max_contacts),
                    int(self.max_rwr),
                    True,
                )
            )
        else:
            inst_out, contacts_out, rwr_out, mission_out = ef_py.compute_execution_observation_batch_numpy(
                inst_batch,
                truth_batch,
                mission_inputs_batch,
                ils_batch,
                int(self.max_contacts),
                int(self.max_rwr),
                backend == "gpu_host",
            )
        self._policy_execution_device_view = execution_device_view if self._is_full_batch_indices(target_indices) else None
        inst_out = np.asarray(inst_out, dtype=np.float32)
        contacts_out = np.asarray(contacts_out, dtype=np.float32)
        rwr_out = np.asarray(rwr_out, dtype=np.float32)
        mission_out = np.asarray(mission_out, dtype=np.float32)

        obs_batch = []
        for batch_idx, env_idx in enumerate(target_indices):
            handle = self._handles[env_idx]
            inst_vec = np.asarray(inst_out[batch_idx], dtype=np.float32)
            contacts = np.asarray(contacts_out[batch_idx], dtype=np.float32).reshape(int(self.max_contacts), 5)
            rwr = np.asarray(rwr_out[batch_idx], dtype=np.float32).reshape(int(self.max_rwr), 4)
            miss_vec = np.asarray(mission_out[batch_idx], dtype=np.float32)
            step_eval = None
            if hasattr(handle.loader, "_prepare_step_evaluation"):
                try:
                    step_eval = handle.loader._prepare_step_evaluation(
                        truth=truth_batch[batch_idx],
                        inst_obj=inst_batch[batch_idx],
                        inst_vec=inst_vec,
                        ils_vec=np.asarray(ils_batch[batch_idx], dtype=np.float32),
                        steps=int(handle.steps),
                        max_steps=int(handle.max_steps),
                        mission_obs_mode=self.mission_obs_mode,
                    )
                except Exception:
                    step_eval = None
            if isinstance(step_eval, dict):
                frame_products = step_eval.get("frame_products")
                if frame_products is not None and bool(getattr(frame_products, "mission_observation_evaluated", False)):
                    miss_vec = np.asarray(frame_products.mission_observation.values, dtype=np.float32)

            obs = {
                "instruments": inst_vec,
                "contacts": contacts,
                "rwr": rwr,
                "mission": miss_vec,
            }
            if self.include_proprio:
                if handle.last_action is None:
                    proprio = np.zeros((int(self.action_space.shape[0]),), dtype=np.float32)
                else:
                    proprio = np.asarray(handle.last_action, dtype=np.float32).reshape(-1)
                obs["proprio"] = proprio
            obs_batch.append(self._attach_visual_observation(env_idx, obs))
        return obs_batch

    def _attach_visual_observation(self, env_idx: int, obs: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
        if not self.include_visual:
            return obs
        self._refresh_visual_batch([env_idx])
        handle = self._handles[env_idx]
        obs["visual"] = np.asarray(handle.visual_cache, dtype=np.float32, copy=False)
        return obs

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

            mission_assign = ef_py.WorldMissionCommandAssignment()
            mission_assign.world_index = int(env_idx)
            mission_assign.entity_id = int(handle.agent_id)
            mission_assign.command = build_kernel_mission_command(handle.loader)
            mission_assignments.append(mission_assign)

            if getattr(handle.loader, "task_order", None) is not None:
                task_assign = ef_py.WorldTaskOrderAssignment()
                task_assign.world_index = int(env_idx)
                task_assign.entity_id = int(handle.agent_id)
                task_assign.order = handle.loader.task_order
                task_assignments.append(task_assign)

            if getattr(handle.loader, "leader_intent", None) is not None:
                intent_assign = ef_py.WorldLeaderIntentAssignment()
                intent_assign.world_index = int(env_idx)
                intent_assign.entity_id = int(handle.agent_id)
                intent_assign.intent = handle.loader.leader_intent
                intent_assignments.append(intent_assign)

            if getattr(handle.loader, "pilot_report", None) is not None:
                report_assign = ef_py.WorldPilotReportAssignment()
                report_assign.world_index = int(env_idx)
                report_assign.entity_id = int(handle.agent_id)
                report_assign.report = handle.loader.pilot_report
                report_assignments.append(report_assign)

        if mission_assignments:
            self._batch_runtime.set_mission_commands_batch(mission_assignments)
        if task_assignments:
            self._batch_runtime.set_task_orders_batch(task_assignments)
        if intent_assignments:
            self._batch_runtime.set_leader_intents_batch(intent_assignments)
        if report_assignments:
            self._batch_runtime.set_pilot_reports_batch(report_assignments)

    def _save_obs(self, env_idx: int, obs: VecEnvObs) -> None:
        for key in self.keys:
            if key is None:
                self.buf_obs[key][env_idx] = obs
            else:
                self.buf_obs[key][env_idx] = obs[key]  # type: ignore[index]

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
        handle.max_steps = int(handle.loader.get_max_steps())
        handle.steps = 0
        handle.last_action = None
        handle.last_inst = initial_inst
        handle.last_truth = initial_truth
        handle.episode_return = 0.0
        handle.episode_length = 0
        handle.visual_cache = None
        handle.visual_cache_step = -1
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
        applied_world = apply_world_layout_to_kernel(self._batch_runtime.world(env_idx), layout)
        kernel_apply_ms = (time.perf_counter() - apply_t0) * 1000.0 if self.collect_step_timing else 0.0
        initial_truth = None
        initial_inst = None
        if applied_world.agent_id is not None:
            try:
                initial_truth = self._batch_runtime.world(env_idx).get_agent_observation(int(applied_world.agent_id))
            except Exception:
                initial_truth = None
            try:
                initial_inst = self._batch_runtime.world(env_idx).get_instrument_state(int(applied_world.agent_id))
            except Exception:
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
                "obs_build_ms": float(obs_build_ms),
                "total_ms": float((time.perf_counter() - total_t0) * 1000.0),
            }
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
            inst_now_list = self._batch_runtime.get_instrument_states_batch(refs)

        assignments = []
        prepared_actions: list[Any | None] = [None] * self.num_envs
        for env_idx, handle in enumerate(self._handles):
            if handle.agent_id is None:
                raise RuntimeError(f"world {env_idx} is not initialized; call reset() before step().")
            effective_action = self._actions[env_idx]
            if handle.action_controller is not None:
                prepared = handle.action_controller.prepare_action(effective_action)
                prepared_actions[env_idx] = prepared
                effective_action = prepared.action
            action = normalize_action(effective_action, action_space=self.action_space, action_mode=self.action_mode)
            handle.last_action = np.asarray(effective_action, dtype=np.float32).reshape(-1).copy()
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
        self._batch_runtime.set_pilot_actions_batch(assignments)
        self._batch_runtime.step_batch()
        batch_step_ms = (time.perf_counter() - step_t0) * 1000.0 if self.collect_step_timing else 0.0

        read_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        truth_list = self._batch_runtime.get_agent_observations_batch(refs)
        inst_list = self._batch_runtime.get_instrument_states_batch(refs)
        state_read_ms = (time.perf_counter() - read_t0) * 1000.0 if self.collect_step_timing else 0.0
        behavior_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        for env_idx, handle in enumerate(self._handles):
            handle.steps += 1
            handle.last_truth = truth_list[env_idx]
            handle.last_inst = inst_list[env_idx]
            sim_time = float(handle.steps) * float(self._batch_runtime.world(env_idx).get_time_step())
            handle.loader.update_behaviors(
                sim_time,
                truth=handle.last_truth,
                inst=handle.last_inst,
                sync_to_kernel=False,
            )
        behavior_update_ms = (time.perf_counter() - behavior_t0) * 1000.0 if self.collect_step_timing else 0.0
        sync_t0 = time.perf_counter() if self.collect_step_timing else 0.0
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
        for env_idx in range(self.num_envs):
            obs = obs_batch[env_idx]
            handle = self._handles[env_idx]
            reward, terminated, truncated, mission_status = handle.loader.compute_full_step(
                obs,
                self._batch_runtime.world(env_idx),
                handle.steps,
                handle.max_steps,
                truth=handle.last_truth,
                inst_state=handle.last_inst,
            )
            info = build_step_info(
                handle.loader,
                self._batch_runtime.world(env_idx),
                int(handle.agent_id),
                mission_status=mission_status,
                terminated=terminated,
                truncated=truncated,
                inst_now=handle.last_inst,
                truth_now=handle.last_truth,
            ) if not (
                self.step_info_mode == "off"
                or (self.step_info_mode == "terminal" and not bool(terminated or truncated))
            ) else build_step_info_minimal(
                handle.loader,
                mission_status=mission_status,
                terminated=terminated,
                truncated=truncated,
            )
            prepared = prepared_actions[env_idx]
            if prepared is not None and handle.action_controller is not None:
                obs, reward, info = handle.action_controller.finalize_step_result(obs, reward, info, prepared)
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
            for info in self.buf_infos:
                if isinstance(info, dict):
                    info["timing"] = dict(self.last_step_timing)
        else:
            self.last_step_timing = {}

        self._actions = None
        return self._obs_from_buf(), np.copy(self.buf_rews), np.copy(self.buf_dones), deepcopy(self.buf_infos)

    def reset(self) -> VecEnvObs:
        self._clear_policy_observation_device_cache()
        total_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        seeds = [self._normalize_seed(self._seeds[env_idx]) for env_idx in range(self.num_envs)]
        shared_overrides = self._shared_randomization_overrides()
        if shared_overrides is not None:
            batch_setup_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            applied_worlds = load_compiled_scenario_batch(
                self._batch_runtime,
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
            truth_list = self._batch_runtime.get_agent_observations_batch(refs)
            inst_list = self._batch_runtime.get_instrument_states_batch(refs)
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
