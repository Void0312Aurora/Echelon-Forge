from __future__ import annotations

import multiprocessing as mp
import warnings
from collections import OrderedDict
from collections.abc import Sequence
from multiprocessing import shared_memory
from typing import Any, Callable, Optional

import gymnasium as gym
import numpy as np
from stable_baselines3.common.vec_env.base_vec_env import (
    CloudpickleWrapper,
    VecEnv,
    VecEnvIndices,
    VecEnvObs,
    VecEnvStepReturn,
)
from stable_baselines3.common.vec_env.patch_gym import _patch_env
from stable_baselines3.common.vec_env.util import dict_to_obs, obs_space_info


def _copy_obs(obs: Any) -> Any:
    if isinstance(obs, dict):
        return {key: _copy_obs(value) for key, value in obs.items()}
    if isinstance(obs, tuple):
        return tuple(_copy_obs(value) for value in obs)
    return np.array(obs, copy=True)


def _open_shared_memory(*, name: str | None = None, create: bool, size: int = 0) -> shared_memory.SharedMemory:
    try:
        return shared_memory.SharedMemory(name=name, create=create, size=size, track=False)
    except TypeError:  # pragma: no cover
        return shared_memory.SharedMemory(name=name, create=create, size=size)


def _write_obs(
    obs: VecEnvObs,
    *,
    env_idx: int,
    keys: list[Any],
    shared_obs: dict[Any, np.ndarray],
) -> None:
    for key in keys:
        if key is None:
            shared_obs[key][env_idx] = np.asarray(obs)
        else:
            shared_obs[key][env_idx] = np.asarray(obs[key])  # type: ignore[index]


def _shared_array_from_spec(spec: dict[str, Any]) -> tuple[shared_memory.SharedMemory, np.ndarray]:
    shm = _open_shared_memory(name=str(spec["name"]), create=False)
    array = np.ndarray(tuple(spec["shape"]), dtype=np.dtype(spec["dtype"]), buffer=shm.buf)
    return shm, array


def _worker(  # noqa: C901
    remote: mp.connection.Connection,
    parent_remote: mp.connection.Connection,
    env_fn_wrapper: CloudpickleWrapper,
    env_idx: int,
) -> None:
    from stable_baselines3.common.env_util import is_wrapped

    parent_remote.close()
    env = _patch_env(env_fn_wrapper.var())
    reset_info: Optional[dict[str, Any]] = {}
    keys: list[Any] = []
    shared_blocks: dict[Any, shared_memory.SharedMemory] = {}
    shared_obs: dict[Any, np.ndarray] = {}

    def _close_shared_blocks() -> None:
        shared_obs.clear()
        for block in shared_blocks.values():
            try:
                block.close()
            except FileNotFoundError:
                pass
            except BufferError:
                pass
        shared_blocks.clear()

    while True:
        try:
            cmd, data = remote.recv()
            if cmd == "set_shared_buffers":
                _close_shared_blocks()
                keys = list(data["keys"])
                for key in keys:
                    block, array = _shared_array_from_spec(data["specs"][key])
                    shared_blocks[key] = block
                    shared_obs[key] = array
                remote.send(True)
            elif cmd == "step":
                observation, reward, terminated, truncated, info = env.step(data)
                done = terminated or truncated
                info["TimeLimit.truncated"] = truncated and not terminated
                if done:
                    info["terminal_observation"] = _copy_obs(observation)
                    observation, reset_info = env.reset()
                _write_obs(observation, env_idx=env_idx, keys=keys, shared_obs=shared_obs)
                remote.send((reward, done, info, reset_info))
            elif cmd == "reset":
                maybe_options = {"options": data[1]} if data[1] else {}
                observation, reset_info = env.reset(seed=data[0], **maybe_options)
                _write_obs(observation, env_idx=env_idx, keys=keys, shared_obs=shared_obs)
                remote.send(reset_info)
            elif cmd == "render":
                remote.send(env.render())
            elif cmd == "close":
                env.close()
                _close_shared_blocks()
                remote.close()
                break
            elif cmd == "get_spaces":
                remote.send((env.observation_space, env.action_space))
            elif cmd == "env_method":
                method = env.get_wrapper_attr(data[0])
                remote.send(method(*data[1], **data[2]))
            elif cmd == "get_attr":
                remote.send(env.get_wrapper_attr(data))
            elif cmd == "has_attr":
                try:
                    env.get_wrapper_attr(data)
                    remote.send(True)
                except AttributeError:
                    remote.send(False)
            elif cmd == "set_attr":
                remote.send(setattr(env, data[0], data[1]))  # type: ignore[func-returns-value]
            elif cmd == "is_wrapped":
                remote.send(is_wrapped(env, data))
            else:
                raise NotImplementedError(f"`{cmd}` is not implemented in the worker")
        except EOFError:
            break
        except KeyboardInterrupt:
            break
    _close_shared_blocks()


class SharedMemorySubprocVecEnv(VecEnv):
    """
    Subprocess VecEnv that stores observations in parent-owned shared memory.

    Worker processes only send rewards/dones/infos over the pipe. This removes
    the large per-step pickle/stack cost for Dict observations, which is the main
    overhead when visual tensors are enabled.
    """

    def __init__(self, env_fns: list[Callable[[], gym.Env]], start_method: Optional[str] = None):
        self.waiting = False
        self.closed = False
        n_envs = len(env_fns)

        available_start_methods = mp.get_all_start_methods()
        if start_method is None:
            start_method = "forkserver" if "forkserver" in available_start_methods else "spawn"
        elif start_method not in available_start_methods:
            fallback_start_method = "forkserver" if "forkserver" in available_start_methods else "spawn"
            warnings.warn(
                f"multiprocessing start_method={start_method!r} is unavailable on this platform; "
                f"using {fallback_start_method!r}.",
                RuntimeWarning,
                stacklevel=2,
            )
            start_method = fallback_start_method
        ctx = mp.get_context(start_method)

        self.remotes, self.work_remotes = zip(*[ctx.Pipe() for _ in range(n_envs)])
        self.processes = []
        for env_idx, (work_remote, remote, env_fn) in enumerate(zip(self.work_remotes, self.remotes, env_fns)):
            args = (work_remote, remote, CloudpickleWrapper(env_fn), env_idx)
            process = ctx.Process(target=_worker, args=args, daemon=True)  # type: ignore[attr-defined]
            process.start()
            self.processes.append(process)
            work_remote.close()

        self.remotes[0].send(("get_spaces", None))
        observation_space, action_space = self.remotes[0].recv()

        self.keys, self.shapes, self.dtypes = obs_space_info(observation_space)
        self._obs_shms: dict[Any, shared_memory.SharedMemory] = {}
        self.buf_obs = OrderedDict()
        self._shared_specs: dict[Any, dict[str, Any]] = {}
        for key in self.keys:
            shape = (n_envs, *tuple(self.shapes[key]))
            dtype = np.dtype(self.dtypes[key])
            shm = _open_shared_memory(
                create=True,
                size=int(np.prod(shape, dtype=np.int64)) * int(dtype.itemsize),
            )
            array = np.ndarray(shape, dtype=dtype, buffer=shm.buf)
            array.fill(0)
            self._obs_shms[key] = shm
            self.buf_obs[key] = array
            self._shared_specs[key] = {
                "name": shm.name,
                "shape": shape,
                "dtype": dtype.str,
            }

        for remote in self.remotes:
            remote.send(("set_shared_buffers", {"keys": self.keys, "specs": self._shared_specs}))
        for remote in self.remotes:
            remote.recv()

        super().__init__(len(env_fns), observation_space, action_space)
        self.buf_dones = np.zeros((self.num_envs,), dtype=bool)
        self.buf_rews = np.zeros((self.num_envs,), dtype=np.float32)
        self.buf_infos: list[dict[str, Any]] = [{} for _ in range(self.num_envs)]

    def step_async(self, actions: np.ndarray) -> None:
        for remote, action in zip(self.remotes, actions):
            remote.send(("step", action))
        self.waiting = True

    def step_wait(self) -> VecEnvStepReturn:
        results = [remote.recv() for remote in self.remotes]
        self.waiting = False
        rews, dones, infos, self.reset_infos = zip(*results)  # type: ignore[assignment]
        self.buf_rews[:] = np.asarray(rews, dtype=np.float32)
        self.buf_dones[:] = np.asarray(dones, dtype=bool)
        self.buf_infos = list(infos)
        return self._obs_from_buf(), np.copy(self.buf_rews), np.copy(self.buf_dones), self.buf_infos

    def reset(self) -> VecEnvObs:
        for env_idx, remote in enumerate(self.remotes):
            remote.send(("reset", (self._seeds[env_idx], self._options[env_idx])))
        self.reset_infos = [remote.recv() for remote in self.remotes]
        self._reset_seeds()
        self._reset_options()
        return self._obs_from_buf()

    def close(self) -> None:
        if self.closed:
            return
        if self.waiting:
            for remote in self.remotes:
                remote.recv()
        for remote in self.remotes:
            remote.send(("close", None))
        for process in self.processes:
            process.join()
        self.buf_obs.clear()
        for shm in self._obs_shms.values():
            try:
                shm.close()
            except FileNotFoundError:
                pass
            except BufferError:
                pass
            try:
                shm.unlink()
            except FileNotFoundError:
                pass
        self.closed = True

    def get_images(self) -> Sequence[Optional[np.ndarray]]:
        if self.render_mode != "rgb_array":
            warnings.warn(
                f"The render mode is {self.render_mode}, but this method assumes it is `rgb_array` to obtain images."
            )
            return [None for _ in self.remotes]
        for pipe in self.remotes:
            pipe.send(("render", None))
        return [pipe.recv() for pipe in self.remotes]

    def has_attr(self, attr_name: str) -> bool:
        target_remotes = self._get_target_remotes(indices=None)
        for remote in target_remotes:
            remote.send(("has_attr", attr_name))
        return all(remote.recv() for remote in target_remotes)

    def get_attr(self, attr_name: str, indices: VecEnvIndices = None) -> list[Any]:
        target_remotes = self._get_target_remotes(indices)
        for remote in target_remotes:
            remote.send(("get_attr", attr_name))
        return [remote.recv() for remote in target_remotes]

    def set_attr(self, attr_name: str, value: Any, indices: VecEnvIndices = None) -> None:
        target_remotes = self._get_target_remotes(indices)
        for remote in target_remotes:
            remote.send(("set_attr", (attr_name, value)))
        for remote in target_remotes:
            remote.recv()

    def env_method(self, method_name: str, *method_args, indices: VecEnvIndices = None, **method_kwargs) -> list[Any]:
        target_remotes = self._get_target_remotes(indices)
        for remote in target_remotes:
            remote.send(("env_method", (method_name, method_args, method_kwargs)))
        return [remote.recv() for remote in target_remotes]

    def env_is_wrapped(self, wrapper_class: type[gym.Wrapper], indices: VecEnvIndices = None) -> list[bool]:
        target_remotes = self._get_target_remotes(indices)
        for remote in target_remotes:
            remote.send(("is_wrapped", wrapper_class))
        return [remote.recv() for remote in target_remotes]

    def _get_target_remotes(self, indices: VecEnvIndices) -> list[Any]:
        indices = self._get_indices(indices)
        return [self.remotes[i] for i in indices]

    def _obs_from_buf(self) -> VecEnvObs:
        obs_dict = OrderedDict((key, value) for key, value in self.buf_obs.items())
        return dict_to_obs(self.observation_space, obs_dict)
