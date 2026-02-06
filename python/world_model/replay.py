from __future__ import annotations

import os
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any

import numpy as np

from python.world_model.utils import ensure_dir


@dataclass(frozen=True)
class DatasetSpec:
    action_dim: int
    obs_vec_dim: int
    action_low: np.ndarray | None = None
    action_high: np.ndarray | None = None
    visual_shape: tuple[int, int, int] | None = None  # (H, W, C) after downsampling


@dataclass(frozen=True)
class Episode:
    obs_vec: np.ndarray  # (T+1, obs_vec_dim)
    actions: np.ndarray  # (T, action_dim)
    rewards: np.ndarray  # (T,)
    dones: np.ndarray  # (T,) bool
    visual: np.ndarray | None = None  # (T+1, H, W, C)
    # Optional expert labels for imitation/DAgger-style training. When present, this stores the
    # expert/teacher action for each transition, aligned with `actions` length (T, action_dim).
    expert_actions: np.ndarray | None = None  # (T, action_dim)

    def __post_init__(self) -> None:
        if self.obs_vec.ndim != 2:
            raise ValueError(f"obs_vec must be (T+1, D), got {self.obs_vec.shape}")
        if self.actions.ndim != 2:
            raise ValueError(f"actions must be (T, A), got {self.actions.shape}")
        if self.rewards.ndim != 1:
            raise ValueError(f"rewards must be (T,), got {self.rewards.shape}")
        if self.dones.ndim != 1:
            raise ValueError(f"dones must be (T,), got {self.dones.shape}")
        if self.obs_vec.shape[0] != self.actions.shape[0] + 1:
            raise ValueError("obs_vec length must be actions length + 1")
        if self.rewards.shape[0] != self.actions.shape[0]:
            raise ValueError("rewards length must match actions length")
        if self.dones.shape[0] != self.actions.shape[0]:
            raise ValueError("dones length must match actions length")
        if self.visual is not None and self.visual.shape[0] != self.obs_vec.shape[0]:
            raise ValueError("visual length must match obs_vec length")
        if self.expert_actions is not None:
            if self.expert_actions.ndim != 2:
                raise ValueError(f"expert_actions must be (T, A), got {self.expert_actions.shape}")
            if self.expert_actions.shape != self.actions.shape:
                raise ValueError(
                    f"expert_actions shape must match actions shape, got expert_actions={self.expert_actions.shape} "
                    f"actions={self.actions.shape}"
                )


class EpisodeStore:
    def __init__(self, root_dir: str, spec: DatasetSpec):
        self.root_dir = os.path.abspath(root_dir)
        self.episodes_dir = os.path.join(self.root_dir, "episodes")
        ensure_dir(self.episodes_dir)
        self.spec = spec
        self._counter = self._scan_next_index()

        spec_path = os.path.join(self.root_dir, "spec.npz")
        if not os.path.exists(spec_path):
            action_low = spec.action_low
            action_high = spec.action_high
            if action_low is None:
                action_low = -np.ones((spec.action_dim,), dtype=np.float32)
            if action_high is None:
                action_high = np.ones((spec.action_dim,), dtype=np.float32)
            np.savez_compressed(
                spec_path,
                action_dim=np.asarray([spec.action_dim], dtype=np.int32),
                obs_vec_dim=np.asarray([spec.obs_vec_dim], dtype=np.int32),
                action_low=np.asarray(action_low, dtype=np.float32),
                action_high=np.asarray(action_high, dtype=np.float32),
                visual_shape=np.asarray(spec.visual_shape if spec.visual_shape is not None else (-1, -1, -1), dtype=np.int32),
            )

    def _scan_next_index(self) -> int:
        if not os.path.isdir(self.episodes_dir):
            return 0
        max_idx = -1
        for fname in os.listdir(self.episodes_dir):
            if not fname.startswith("episode_") or not fname.endswith(".npz"):
                continue
            try:
                idx = int(fname[len("episode_") : -len(".npz")])
                max_idx = max(max_idx, idx)
            except ValueError:
                continue
        return max_idx + 1

    def add(self, episode: Episode, seed: int | None = None) -> str:
        idx = self._counter
        self._counter += 1
        path = os.path.join(self.episodes_dir, f"episode_{idx:06d}.npz")

        payload: dict[str, Any] = {
            "obs_vec": episode.obs_vec.astype(np.float32, copy=False),
            "actions": episode.actions.astype(np.float32, copy=False),
            "rewards": episode.rewards.astype(np.float32, copy=False),
            "dones": episode.dones.astype(np.bool_, copy=False),
        }
        if episode.visual is not None:
            payload["visual"] = episode.visual
        if episode.expert_actions is not None:
            payload["expert_actions"] = episode.expert_actions.astype(np.float32, copy=False)
        if seed is not None:
            payload["seed"] = np.asarray([seed], dtype=np.int64)

        np.savez_compressed(path, **payload)
        return path


class EpisodeDataset:
    def __init__(self, root_dir: str, cache_size: int = 8):
        self.root_dir = os.path.abspath(root_dir)
        self.episodes_dir = os.path.join(self.root_dir, "episodes")
        if not os.path.isdir(self.episodes_dir):
            raise FileNotFoundError(f"Dataset episodes dir not found: {self.episodes_dir}")

        self.episode_paths = sorted(
            os.path.join(self.episodes_dir, f)
            for f in os.listdir(self.episodes_dir)
            if f.startswith("episode_") and f.endswith(".npz")
        )
        if not self.episode_paths:
            raise FileNotFoundError(f"No episodes found in: {self.episodes_dir}")

        self.cache_size = int(cache_size)
        self._cache: OrderedDict[str, Episode] = OrderedDict()

        self.spec = self._load_spec()
        self._episode_lengths = self._scan_episode_lengths()
        self._episode_probs = None
        self._episode_probs_seq_len: int | None = None

    def _load_spec(self) -> DatasetSpec:
        spec_path = os.path.join(self.root_dir, "spec.npz")
        if not os.path.exists(spec_path):
            first = self._load_episode(self.episode_paths[0])
            vis_shape = None if first.visual is None else tuple(int(x) for x in first.visual.shape[1:])
            return DatasetSpec(action_dim=int(first.actions.shape[1]), obs_vec_dim=int(first.obs_vec.shape[1]), visual_shape=vis_shape)

        data = np.load(spec_path, allow_pickle=False)
        action_dim = int(np.asarray(data["action_dim"]).reshape(-1)[0])
        obs_vec_dim = int(np.asarray(data["obs_vec_dim"]).reshape(-1)[0])
        visual_shape_raw = tuple(int(x) for x in np.asarray(data["visual_shape"]).reshape(-1).tolist())
        visual_shape = None if visual_shape_raw[0] < 0 else visual_shape_raw  # type: ignore[assignment]
        action_low = None
        action_high = None
        if "action_low" in data.files and "action_high" in data.files:
            action_low = np.asarray(data["action_low"], dtype=np.float32).reshape(-1)
            action_high = np.asarray(data["action_high"], dtype=np.float32).reshape(-1)
        return DatasetSpec(
            action_dim=action_dim,
            obs_vec_dim=obs_vec_dim,
            action_low=action_low,
            action_high=action_high,
            visual_shape=visual_shape,
        )

    def _scan_episode_lengths(self) -> np.ndarray:
        lengths: list[int] = []
        for path in self.episode_paths:
            try:
                with np.load(path, allow_pickle=False) as data:
                    if "actions" not in data.files:
                        lengths.append(1)
                        continue
                    actions = np.asarray(data["actions"])
                    lengths.append(int(actions.shape[0]))
            except Exception:
                lengths.append(1)
        arr = np.asarray(lengths, dtype=np.int64)
        return np.maximum(arr, 1)

    def _build_episode_sampling_probs(self, lengths: np.ndarray, seq_len: int) -> np.ndarray | None:
        # Sample episodes roughly proportional to their usable transition counts, but avoid letting
        # extremely long episodes dominate (common in online training when the policy fails and hits
        # max_steps). We use sqrt-weighting as a compromise:
        # - still downweights 1-step junk episodes
        # - but doesn't let 2000-step failures drown out 200-step successes
        lengths = np.asarray(lengths, dtype=np.float64).reshape(-1)
        lengths = np.maximum(lengths, 1.0)
        seq_len = int(seq_len)
        if seq_len > 1 and np.any(lengths >= float(seq_len)):
            usable = np.maximum(lengths - float(seq_len) + 1.0, 1.0)
            usable = np.where(lengths >= float(seq_len), usable, 0.0)
        else:
            usable = lengths
        weights = np.sqrt(np.maximum(usable, 0.0))
        total = float(weights.sum())
        if not np.isfinite(total) or total <= 0.0:
            return None
        probs = weights / total
        probs = probs / probs.sum()
        return probs.astype(np.float64, copy=False)

    def __len__(self) -> int:
        return len(self.episode_paths)

    def refresh(self) -> None:
        """
        Rescan the episodes directory.

        This is used by online training loops that append new episodes while keeping
        the same dataset instance alive.
        """
        new_paths = sorted(
            os.path.join(self.episodes_dir, f)
            for f in os.listdir(self.episodes_dir)
            if f.startswith("episode_") and f.endswith(".npz")
        )
        if not new_paths:
            return

        old_paths = list(self.episode_paths)
        if new_paths == old_paths:
            return

        # Incremental fast-path: new_paths extends old_paths as a prefix.
        if len(new_paths) >= len(old_paths) and new_paths[: len(old_paths)] == old_paths:
            added = new_paths[len(old_paths) :]
            added_lengths = []
            for path in added:
                try:
                    with np.load(path, allow_pickle=False) as data:
                        actions = np.asarray(data["actions"])
                        added_lengths.append(int(actions.shape[0]))
                except Exception:
                    added_lengths.append(1)
            if added_lengths:
                self._episode_lengths = np.concatenate(
                    [self._episode_lengths, np.maximum(np.asarray(added_lengths, dtype=np.int64), 1)], axis=0
                )
        else:
            # Fallback: rebuild lengths from scratch.
            self.episode_paths = new_paths
            self._episode_lengths = self._scan_episode_lengths()

        self.episode_paths = new_paths
        self._episode_probs = None
        self._episode_probs_seq_len = None

        # Purge cache entries that no longer exist.
        valid = set(self.episode_paths)
        for key in list(self._cache.keys()):
            if key not in valid:
                self._cache.pop(key, None)

    def _load_episode(self, path: str) -> Episode:
        data = np.load(path, allow_pickle=False)
        obs_vec = np.asarray(data["obs_vec"], dtype=np.float32)
        actions = np.asarray(data["actions"], dtype=np.float32)
        rewards = np.asarray(data["rewards"], dtype=np.float32)
        dones = np.asarray(data["dones"], dtype=np.bool_)
        expert_actions = None
        if "expert_actions" in data.files:
            expert_actions = np.asarray(data["expert_actions"], dtype=np.float32)
        # Some collectors may stop early without the environment emitting `truncated=True`.
        # For this project the task is episodic; ensure the final transition is marked terminal
        # so the world model learns proper continuation dynamics.
        if dones.size == actions.shape[0] and dones.size > 0 and (not bool(dones[-1])):
            dones = dones.copy()
            dones[-1] = True
        visual = None
        if "visual" in data.files:
            visual = np.asarray(data["visual"])
        return Episode(obs_vec=obs_vec, actions=actions, rewards=rewards, dones=dones, visual=visual, expert_actions=expert_actions)

    def get_episode(self, index: int) -> Episode:
        path = self.episode_paths[int(index)]
        if path in self._cache:
            ep = self._cache.pop(path)
            self._cache[path] = ep
            return ep
        ep = self._load_episode(path)
        self._cache[path] = ep
        while len(self._cache) > self.cache_size:
            self._cache.popitem(last=False)
        return ep

    def sample_batch(
        self,
        batch_size: int,
        seq_len: int,
        rng: np.random.Generator,
        *,
        start_at_zero: bool = False,
        start_at_zero_prob: float | None = None,
    ) -> dict[str, np.ndarray]:
        batch_size = int(batch_size)
        seq_len = int(seq_len)
        if self._episode_probs is None or self._episode_probs_seq_len != seq_len:
            self._episode_probs = self._build_episode_sampling_probs(self._episode_lengths, seq_len)
            self._episode_probs_seq_len = seq_len
        obs_vec_list: list[np.ndarray] = []
        act_list: list[np.ndarray] = []
        expert_act_list: list[np.ndarray] = []
        rew_list: list[np.ndarray] = []
        done_list: list[np.ndarray] = []
        visual_list: list[np.ndarray] = []

        for _ in range(batch_size):
            start_at_zero_i = bool(start_at_zero)
            if start_at_zero_prob is not None:
                try:
                    p = float(start_at_zero_prob)
                except Exception:
                    p = 0.0
                p = float(np.clip(p, 0.0, 1.0))
                start_at_zero_i = bool(rng.random() < p)
            # Prefer sampling from longer episodes to approximate uniform sampling over transitions.
            ep = None
            for attempt in range(20):
                if self._episode_probs is None:
                    ep_idx = int(rng.integers(0, len(self)))
                else:
                    ep_idx = int(rng.choice(len(self), p=self._episode_probs))
                ep = self.get_episode(ep_idx)
                if int(ep.actions.shape[0]) >= seq_len:
                    break
                # If most episodes are short, fall back to padding on the last attempt.
                if attempt == 19:
                    break
            if ep is None:  # pragma: no cover
                raise RuntimeError("Failed to sample episode")
            T = ep.actions.shape[0]
            if T >= seq_len:
                if start_at_zero_i:
                    start = 0
                else:
                    start = int(rng.integers(0, T - seq_len + 1))
                end = start + seq_len
                obs_vec = ep.obs_vec[start : end + 1]
                acts = ep.actions[start:end]
                expert_acts = ep.expert_actions[start:end] if ep.expert_actions is not None else acts
                rews = ep.rewards[start:end]
                dones = ep.dones[start:end]
                vis = ep.visual[start : end + 1] if ep.visual is not None else None
            else:
                # Pad short episodes to a fixed length so batching is stable.
                pad = seq_len - T
                obs_vec = ep.obs_vec
                acts = ep.actions
                expert_acts = ep.expert_actions if ep.expert_actions is not None else acts
                rews = ep.rewards
                dones = ep.dones
                last_obs = obs_vec[-1:]
                obs_vec = np.concatenate([obs_vec, np.repeat(last_obs, pad, axis=0)], axis=0)  # (seq_len+1, D)
                acts = np.concatenate([acts, np.zeros((pad, acts.shape[1]), dtype=acts.dtype)], axis=0)
                expert_acts = np.concatenate(
                    [expert_acts, np.zeros((pad, acts.shape[1]), dtype=acts.dtype)], axis=0
                )
                rews = np.concatenate([rews, np.zeros((pad,), dtype=rews.dtype)], axis=0)
                dones = np.concatenate([dones, np.ones((pad,), dtype=dones.dtype)], axis=0)
                vis = None
                if ep.visual is not None:
                    last_v = ep.visual[-1:]
                    vis = np.concatenate([ep.visual, np.repeat(last_v, pad, axis=0)], axis=0)

            obs_vec_list.append(obs_vec)
            act_list.append(acts)
            expert_act_list.append(expert_acts)
            rew_list.append(rews)
            done_list.append(dones)
            if vis is not None:
                visual_list.append(vis)

        batch: dict[str, np.ndarray] = {
            "obs_vec": np.stack(obs_vec_list, axis=0),
            "actions": np.stack(act_list, axis=0),
            "expert_actions": np.stack(expert_act_list, axis=0),
            "rewards": np.stack(rew_list, axis=0),
            "dones": np.stack(done_list, axis=0),
        }
        if visual_list:
            batch["visual"] = np.stack(visual_list, axis=0)
        return batch
