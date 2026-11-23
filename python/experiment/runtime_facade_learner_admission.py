"""Explicit PPO/BC/world-model admission over a RuntimeFacade learner sidecar.

The module is a consumer-only boundary. It reads an already-qualified Air
RuntimeFacade sidecar and its EpisodeStore files, validates identity and array
shape, then exposes one stable learner batch contract. It does not create
runtime evidence, receipts, input locks, or production admission.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from python.experiment.contracts import ContractError, content_digest
from python.experiment.runtime_facade_training_export import (
    AIR_RUNTIME_FACADE_SURFACE,
    load_runtime_facade_training_sidecar,
)


LEARNER_CONSUMERS = ("ppo", "bc", "world_model")
_NUMERIC_SIDECAR = "trace_projection_export.json"


@dataclass(frozen=True)
class LearnerConsumerBatch:
    """One EpisodeStore episode projected for one explicit learner consumer."""

    consumer: str
    observations: np.ndarray
    actions: np.ndarray
    rewards: np.ndarray
    dones: np.ndarray
    next_observations: np.ndarray | None
    targets: np.ndarray | None
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        if self.consumer not in LEARNER_CONSUMERS:
            raise ContractError(f"consumer must be one of {LEARNER_CONSUMERS}")
        observations = np.asarray(self.observations, dtype=np.float32)
        actions = np.asarray(self.actions, dtype=np.float32)
        rewards = np.asarray(self.rewards, dtype=np.float32)
        dones = np.asarray(self.dones, dtype=np.bool_)
        if observations.ndim != 2 or actions.ndim != 2 or rewards.ndim != 1 or dones.ndim != 1:
            raise ContractError("learner batch arrays have invalid rank")
        transitions = actions.shape[0]
        if observations.shape[0] != transitions or rewards.shape[0] != transitions or dones.shape[0] != transitions:
            raise ContractError("learner batch arrays have mismatched transition count")
        if transitions == 0 or observations.shape[1] == 0 or actions.shape[1] == 0:
            raise ContractError("learner batch arrays must be non-empty")
        for name, array in (("observations", observations), ("actions", actions), ("rewards", rewards)):
            if not bool(np.all(np.isfinite(array))):
                raise ContractError(f"{name} contains non-finite values")
            array.setflags(write=False)
        dones.setflags(write=False)
        object.__setattr__(self, "observations", observations)
        object.__setattr__(self, "actions", actions)
        object.__setattr__(self, "rewards", rewards)
        object.__setattr__(self, "dones", dones)
        if self.next_observations is not None:
            next_observations = np.asarray(self.next_observations, dtype=np.float32)
            if next_observations.shape != observations.shape or not bool(np.all(np.isfinite(next_observations))):
                raise ContractError("next_observations shape or values are invalid")
            next_observations.setflags(write=False)
            object.__setattr__(self, "next_observations", next_observations)
        if self.targets is not None:
            targets = np.asarray(self.targets, dtype=np.float32)
            if targets.shape != actions.shape or not bool(np.all(np.isfinite(targets))):
                raise ContractError("targets shape or values are invalid")
            targets.setflags(write=False)
            object.__setattr__(self, "targets", targets)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"learner sidecar is unreadable: {path}") from exc
    if not isinstance(value, dict):
        raise ContractError("learner sidecar must contain an object")
    return value


def _numeric_sidecar(root: Path, expected: Mapping[str, Any], payload: Mapping[str, Any]) -> dict[str, Any]:
    numeric = _read_json(root / _NUMERIC_SIDECAR)
    metadata_digest = numeric.get("metadata_digest")
    if not isinstance(metadata_digest, str):
        raise ContractError("numeric metadata digest is missing")
    without_digest = dict(numeric)
    without_digest.pop("metadata_digest", None)
    if content_digest("experiment.numeric-export", without_digest) != metadata_digest:
        raise ContractError("numeric metadata digest mismatch")
    if payload.get("numeric_metadata_digest") != metadata_digest:
        raise ContractError("learner sidecar numeric digest mismatch")
    if numeric.get("episodes") != payload.get("episodes"):
        raise ContractError("learner and numeric episode metadata differ")
    if numeric.get("projection_digest") != expected["projection_digest"]:
        raise ContractError("numeric projection digest mismatch")
    return numeric


def _episode_path(root: Path, relative: object) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ContractError("episode path must be a relative path")
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ContractError("episode path escapes the sidecar root") from exc
    return path


def _batch_from_episode(
    root: Path,
    episode_meta: Mapping[str, Any],
    *,
    consumer: str,
) -> LearnerConsumerBatch:
    path = _episode_path(root, episode_meta.get("path"))
    try:
        data = np.load(path, allow_pickle=False)
    except (OSError, ValueError) as exc:
        raise ContractError(f"episode file is unreadable: {path}") from exc
    try:
        required = {"obs_vec", "actions", "rewards", "dones"}
        if not required.issubset(data.files):
            raise ContractError("episode file is missing learner arrays")
        observations_full = np.asarray(data["obs_vec"], dtype=np.float32)
        actions = np.asarray(data["actions"], dtype=np.float32)
        rewards = np.asarray(data["rewards"], dtype=np.float32)
        dones = np.asarray(data["dones"], dtype=np.bool_)
    finally:
        data.close()
    if observations_full.ndim != 2 or actions.ndim != 2 or rewards.ndim != 1 or dones.ndim != 1:
        raise ContractError("episode observation shape is invalid")
    if observations_full.shape[0] != actions.shape[0] + 1:
        raise ContractError("episode observation shape must be T+1")
    if rewards.shape[0] != actions.shape[0] or dones.shape[0] != actions.shape[0]:
        raise ContractError("episode transition shape is inconsistent")
    if episode_meta.get("observation_dim") != int(observations_full.shape[1]):
        raise ContractError("episode observation shape metadata mismatch")
    if episode_meta.get("action_dim") != int(actions.shape[1]):
        raise ContractError("episode action shape metadata mismatch")
    if episode_meta.get("transition_count") != int(actions.shape[0]):
        raise ContractError("episode transition metadata mismatch")
    observations = observations_full[:-1]
    next_observations = observations_full[1:] if consumer == "world_model" else None
    targets = actions.copy() if consumer == "bc" else None
    metadata = dict(episode_meta)
    metadata["consumer"] = consumer
    return LearnerConsumerBatch(
        consumer=consumer,
        observations=observations,
        actions=actions,
        rewards=rewards,
        dones=dones,
        next_observations=next_observations,
        targets=targets,
        metadata=metadata,
    )


def admit_runtime_facade_learner_sidecar(
    root_dir: str,
    *,
    consumer: str,
    projection_digest: str,
    agent_id: str,
    seed: int,
    split: str,
    branch_digests: list[str] | tuple[str, ...],
    surface_id: str = AIR_RUNTIME_FACADE_SURFACE,
) -> tuple[LearnerConsumerBatch, ...]:
    """Admit one qualified sidecar for PPO, BC, or world-model consumers."""

    if consumer not in LEARNER_CONSUMERS:
        raise ContractError(f"consumer must be one of {LEARNER_CONSUMERS}")
    payload = load_runtime_facade_training_sidecar(
        root_dir,
        projection_digest=projection_digest,
        agent_id=agent_id,
        seed=seed,
        split=split,
        branch_digests=branch_digests,
        surface_id=surface_id,
    )
    root = Path(root_dir).resolve()
    expected = {
        "projection_digest": projection_digest,
        "agent_id": agent_id,
        "seed": seed,
        "split": split,
    }
    _numeric_sidecar(root, expected, payload)
    episodes = payload.get("episodes")
    if not isinstance(episodes, list) or not episodes:
        raise ContractError("learner sidecar episodes must be non-empty")
    batches = tuple(
        _batch_from_episode(root, episode, consumer=consumer)
        for episode in episodes
        if isinstance(episode, Mapping)
    )
    if len(batches) != len(episodes):
        raise ContractError("learner sidecar episode metadata is invalid")
    return batches


__all__ = [
    "LEARNER_CONSUMERS",
    "LearnerConsumerBatch",
    "admit_runtime_facade_learner_sidecar",
]
