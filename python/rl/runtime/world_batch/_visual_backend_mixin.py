from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import ef_py

try:
    import torch
except Exception:  # pragma: no cover - training envs are expected to have torch
    torch = None

from python.rl.tasking.bridge import resolve_tasking_profile, tasking_profile_for_loader
from gym_envs.universal_env import temporal_history_enabled

from .observation_batching import refresh_visual_cache_batch
from ._shared_ops import (
    batch_observation_runtime_base_check,
    resolve_batch_observation_backend_mode,
    resolve_batch_visual_backend_mode,
)


class _WorldBatchVecEnvVisualBackendMixin:
    def _batch_observation_backend_mode(self) -> str:
        return resolve_batch_observation_backend_mode(
            self.batch_observation_backend,
            self._batch_observation_runtime_available(),
        )

    def _batch_observation_runtime_available(self) -> bool:
        if not batch_observation_runtime_base_check():
            return False
        for handle in self._handles:
            if not bool(getattr(handle.loader, "use_compiled_execution_step_runtime", True)):
                return False
        return True

    def _batch_visual_backend_mode(self) -> str:
        return resolve_batch_visual_backend_mode(self.batch_visual_backend)

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



__all__ = ["_WorldBatchVecEnvVisualBackendMixin"]
