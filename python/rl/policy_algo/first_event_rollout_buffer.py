from __future__ import annotations

from collections import namedtuple
from collections.abc import Generator
from typing import Optional

import numpy as np
import torch as th

from stable_baselines3.common.buffers import DictRolloutBuffer
from stable_baselines3.common.type_aliases import DictRolloutBufferSamples
from stable_baselines3.common.vec_env import VecNormalize

from .device_dict_rollout_buffer import DeviceDictRolloutBuffer
from .first_event_hazard import (
    A6_FIRST_EVENT_FIELD_ACTIVE,
    A6_FIRST_EVENT_FIELD_HAD_ACCEPTED,
    A6_FIRST_EVENT_FIELD_NAMES,
    A6_FIRST_EVENT_FIELD_SOURCE,
    A6_FIRST_EVENT_FIELD_TARGET,
    A6_FIRST_EVENT_FIELD_WEIGHT,
    A6_FIRST_EVENT_FIELD_WINDOW_AGE,
    A6_FIRST_EVENT_FIELD_WINDOW_ID,
    FirstEventHazardLabels,
)


A6FirstEventDictRolloutBufferSamples = namedtuple(
    "A6FirstEventDictRolloutBufferSamples",
    (*DictRolloutBufferSamples._fields, *A6_FIRST_EVENT_FIELD_NAMES),
)


class A6FirstEventDictRolloutBuffer(DictRolloutBuffer):
    """
    Dict rollout buffer that carries A6 first-event labels outside policy observations.

    The labels are generated after a rollout window has been collected, then are
    shuffled with the same minibatch indices as the PPO samples.
    """

    supports_a6_first_event_labels = True

    def reset(self) -> None:
        super().reset()
        self._reset_a6_first_event_fields()

    def _reset_a6_first_event_fields(self) -> None:
        shape = (self.buffer_size, self.n_envs)
        self.a6_first_event_active = np.zeros(shape, dtype=np.float32)
        self.a6_first_event_target = np.zeros(shape, dtype=np.float32)
        self.a6_first_event_weight = np.zeros(shape, dtype=np.float32)
        self.a6_first_event_source = np.zeros(shape, dtype=np.int64)
        self.a6_first_event_window_age = np.zeros(shape, dtype=np.float32)
        self.a6_first_event_window_id = np.full(shape, -1, dtype=np.int64)
        self.a6_first_event_had_accepted = np.zeros(shape, dtype=np.float32)

    def set_a6_first_event_labels(self, labels: FirstEventHazardLabels) -> None:
        shape = (self.buffer_size, self.n_envs)
        expected = int(self.buffer_size * self.n_envs)
        if int(labels.active.numel()) != expected:
            raise ValueError("A6 first-event labels must match rollout buffer size")
        self.a6_first_event_active = labels.active.detach().cpu().numpy().astype(np.float32).reshape(shape)
        self.a6_first_event_target = labels.target.detach().cpu().numpy().astype(np.float32).reshape(shape)
        self.a6_first_event_weight = labels.weight.detach().cpu().numpy().astype(np.float32).reshape(shape)
        self.a6_first_event_source = labels.source.detach().cpu().numpy().astype(np.int64).reshape(shape)
        self.a6_first_event_window_age = labels.window_age.detach().cpu().numpy().astype(np.float32).reshape(shape)
        self.a6_first_event_window_id = labels.window_id.detach().cpu().numpy().astype(np.int64).reshape(shape)
        self.a6_first_event_had_accepted = (
            labels.had_accepted.detach().cpu().numpy().astype(np.float32).reshape(shape)
        )

    def get(  # type: ignore[override]
        self,
        batch_size: Optional[int] = None,
    ) -> Generator[A6FirstEventDictRolloutBufferSamples, None, None]:
        if not self.generator_ready:
            for field in A6_FIRST_EVENT_FIELD_NAMES:
                self.__dict__[field] = self.swap_and_flatten(self.__dict__[field])
        yield from super().get(batch_size)

    def _get_samples(  # type: ignore[override]
        self,
        batch_inds: np.ndarray,
        env: Optional[VecNormalize] = None,
    ) -> A6FirstEventDictRolloutBufferSamples:
        base = super()._get_samples(batch_inds, env)
        return A6FirstEventDictRolloutBufferSamples(
            *base,
            self.to_torch(self.a6_first_event_active[batch_inds]).flatten(),
            self.to_torch(self.a6_first_event_target[batch_inds]).flatten(),
            self.to_torch(self.a6_first_event_weight[batch_inds]).flatten(),
            self.to_torch(self.a6_first_event_source[batch_inds]).flatten().long(),
            self.to_torch(self.a6_first_event_window_age[batch_inds]).flatten(),
            self.to_torch(self.a6_first_event_window_id[batch_inds]).flatten().long(),
            self.to_torch(self.a6_first_event_had_accepted[batch_inds]).flatten(),
        )


class A6FirstEventDeviceDictRolloutBuffer(DeviceDictRolloutBuffer):
    """Device-resident variant of the A6 first-event label buffer."""

    supports_a6_first_event_labels = True

    def reset(self) -> None:
        super().reset()
        self._reset_a6_first_event_fields()

    def _reset_a6_first_event_fields(self) -> None:
        shape = (self.buffer_size, self.n_envs)
        self.a6_first_event_active = th.zeros(shape, dtype=th.float32, device=self.device)
        self.a6_first_event_target = th.zeros(shape, dtype=th.float32, device=self.device)
        self.a6_first_event_weight = th.zeros(shape, dtype=th.float32, device=self.device)
        self.a6_first_event_source = th.zeros(shape, dtype=th.long, device=self.device)
        self.a6_first_event_window_age = th.zeros(shape, dtype=th.float32, device=self.device)
        self.a6_first_event_window_id = th.full(shape, -1, dtype=th.long, device=self.device)
        self.a6_first_event_had_accepted = th.zeros(shape, dtype=th.float32, device=self.device)

    def set_a6_first_event_labels(self, labels: FirstEventHazardLabels) -> None:
        shape = (self.buffer_size, self.n_envs)
        expected = int(self.buffer_size * self.n_envs)
        if int(labels.active.numel()) != expected:
            raise ValueError("A6 first-event labels must match rollout buffer size")
        self.a6_first_event_active.copy_(labels.active.to(device=self.device, dtype=th.float32).reshape(shape))
        self.a6_first_event_target.copy_(labels.target.to(device=self.device, dtype=th.float32).reshape(shape))
        self.a6_first_event_weight.copy_(labels.weight.to(device=self.device, dtype=th.float32).reshape(shape))
        self.a6_first_event_source.copy_(labels.source.to(device=self.device, dtype=th.long).reshape(shape))
        self.a6_first_event_window_age.copy_(labels.window_age.to(device=self.device, dtype=th.float32).reshape(shape))
        self.a6_first_event_window_id.copy_(labels.window_id.to(device=self.device, dtype=th.long).reshape(shape))
        self.a6_first_event_had_accepted.copy_(
            labels.had_accepted.to(device=self.device, dtype=th.float32).reshape(shape)
        )

    def get(  # type: ignore[override]
        self,
        batch_size: Optional[int] = None,
    ) -> Generator[A6FirstEventDictRolloutBufferSamples, None, None]:
        if not self.generator_ready:
            for field in A6_FIRST_EVENT_FIELD_NAMES:
                self.__dict__[field] = self._swap_and_flatten_tensor(self.__dict__[field])
        yield from super().get(batch_size)

    def _get_samples(  # type: ignore[override]
        self,
        batch_inds: np.ndarray,
        env: Optional[VecNormalize] = None,
    ) -> A6FirstEventDictRolloutBufferSamples:
        base = super()._get_samples(batch_inds, env)
        index = th.as_tensor(batch_inds, dtype=th.long, device=self.device)
        return A6FirstEventDictRolloutBufferSamples(
            *base,
            self.a6_first_event_active.index_select(0, index).flatten(),
            self.a6_first_event_target.index_select(0, index).flatten(),
            self.a6_first_event_weight.index_select(0, index).flatten(),
            self.a6_first_event_source.index_select(0, index).flatten().long(),
            self.a6_first_event_window_age.index_select(0, index).flatten(),
            self.a6_first_event_window_id.index_select(0, index).flatten().long(),
            self.a6_first_event_had_accepted.index_select(0, index).flatten(),
        )
