from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from python.experiment.contracts import ContractError
from python.experiment.runtime_facade_learner_admission import (
    LEARNER_CONSUMERS,
    admit_runtime_facade_learner_sidecar,
)
from python.experiment.runtime_facade_training_export import (
    AIR_TAKEOFF_RUNTIME_FACADE_SURFACE,
    export_runtime_facade_training_sidecar,
)
from tests.experiment.test_numeric_observation_adapter import _action, _projection, _reward, _sources


def _sidecar(tmp_path: Path, *, surface_id: str | None = None):
    projection = _projection()
    all_sources = _sources(projection)
    key = next(iter(all_sources))
    receipt = export_runtime_facade_training_sidecar(
        projection,
        {key: all_sources[key]},
        agent_id="pilot",
        selected_branch_digests=[key[1]],
        seed=11,
        split="training",
        action_encoder=_action,
        reward_encoder=_reward,
        root_dir=str(tmp_path / "dataset"),
        **({"surface_id": surface_id} if surface_id is not None else {}),
    )
    return projection, key, receipt


@pytest.mark.parametrize("consumer", LEARNER_CONSUMERS)
def test_three_consumers_round_trip_one_admitted_sidecar(tmp_path, consumer: str) -> None:
    projection, key, receipt = _sidecar(tmp_path)
    batches = admit_runtime_facade_learner_sidecar(
        receipt.root_dir,
        consumer=consumer,
        projection_digest=projection.digest,
        agent_id="pilot",
        seed=11,
        split="training",
        branch_digests=[key[1]],
    )

    assert len(batches) == 1
    batch = batches[0]
    assert batch.consumer == consumer
    assert batch.observations.shape[0] == batch.actions.shape[0]
    assert batch.observations.shape[0] == batch.rewards.shape[0] == batch.dones.shape[0]
    assert batch.observations.shape[1] == 2
    assert batch.actions.shape[1] == 1
    if consumer == "world_model":
        assert batch.next_observations is not None
        assert batch.next_observations.shape == batch.observations.shape
    else:
        assert batch.next_observations is None
    if consumer == "bc":
        assert batch.targets is not None
        assert batch.targets.shape == batch.actions.shape
    else:
        assert batch.targets is None


@pytest.mark.parametrize("consumer", LEARNER_CONSUMERS)
def test_takeoff_surface_round_trips_for_all_learner_consumers(tmp_path, consumer: str) -> None:
    projection, key, receipt = _sidecar(
        tmp_path,
        surface_id=AIR_TAKEOFF_RUNTIME_FACADE_SURFACE,
    )
    batches = admit_runtime_facade_learner_sidecar(
        receipt.root_dir,
        consumer=consumer,
        projection_digest=projection.digest,
        agent_id="pilot",
        seed=11,
        split="training",
        branch_digests=[key[1]],
        surface_id=AIR_TAKEOFF_RUNTIME_FACADE_SURFACE,
    )
    assert len(batches) == 1
    assert batches[0].consumer == consumer


def test_admission_rejects_unknown_consumer_and_identity_drift(tmp_path) -> None:
    projection, key, receipt = _sidecar(tmp_path)
    kwargs = dict(
        root_dir=receipt.root_dir,
        projection_digest=projection.digest,
        agent_id="pilot",
        seed=11,
        split="training",
        branch_digests=[key[1]],
    )
    with pytest.raises(ContractError, match="consumer"):
        admit_runtime_facade_learner_sidecar(consumer="evaluation", **kwargs)
    with pytest.raises(ContractError, match="projection digest"):
        admit_runtime_facade_learner_sidecar(consumer="ppo", projection_digest="0" * 64, **{k: v for k, v in kwargs.items() if k != "projection_digest"})
    with pytest.raises(ContractError, match="fixed identity"):
        admit_runtime_facade_learner_sidecar(consumer="bc", seed=17, **{k: v for k, v in kwargs.items() if k != "seed"})


def test_admission_rejects_episode_shape_drift(tmp_path) -> None:
    projection, key, receipt = _sidecar(tmp_path)
    episode_path = next((tmp_path / "dataset" / "episodes").glob("episode_*.npz"))
    np.savez_compressed(
        episode_path,
        obs_vec=np.zeros((2, 99), dtype=np.float32),
        actions=np.zeros((1, 1), dtype=np.float32),
        rewards=np.zeros((1,), dtype=np.float32),
        dones=np.zeros((1,), dtype=np.bool_),
    )
    with pytest.raises(ContractError, match="observation shape"):
        admit_runtime_facade_learner_sidecar(
            receipt.root_dir,
            consumer="world_model",
            projection_digest=projection.digest,
            agent_id="pilot",
            seed=11,
            split="training",
            branch_digests=[key[1]],
        )


def test_consumer_contract_is_explicit_and_minimal() -> None:
    assert LEARNER_CONSUMERS == ("ppo", "bc", "world_model")
