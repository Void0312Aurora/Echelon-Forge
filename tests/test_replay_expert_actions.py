import tempfile

import numpy as np

import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from python.world_model.replay import DatasetSpec, Episode, EpisodeDataset, EpisodeStore


def _make_episode(*, T: int, obs_dim: int, act_dim: int, include_expert: bool) -> Episode:
    rng = np.random.default_rng(0)
    obs_vec = rng.standard_normal((T + 1, obs_dim), dtype=np.float32)
    actions = rng.standard_normal((T, act_dim), dtype=np.float32)
    rewards = rng.standard_normal((T,), dtype=np.float32)
    dones = np.zeros((T,), dtype=np.bool_)
    dones[-1] = True
    expert_actions = actions + 0.123 if include_expert else None
    return Episode(obs_vec=obs_vec, actions=actions, rewards=rewards, dones=dones, expert_actions=expert_actions)


def test_episode_store_roundtrip_expert_actions():
    with tempfile.TemporaryDirectory() as td:
        spec = DatasetSpec(
            action_dim=3,
            obs_vec_dim=4,
            action_low=-np.ones((3,), dtype=np.float32),
            action_high=np.ones((3,), dtype=np.float32),
        )
        store = EpisodeStore(td, spec)
        ep = _make_episode(T=8, obs_dim=4, act_dim=3, include_expert=True)
        store.add(ep, seed=123)

        ds = EpisodeDataset(td)
        loaded = ds.get_episode(0)
        assert loaded.expert_actions is not None
        np.testing.assert_allclose(loaded.expert_actions, ep.expert_actions)

        batch = ds.sample_batch(batch_size=2, seq_len=5, rng=np.random.default_rng(1))
        assert "expert_actions" in batch
        assert batch["expert_actions"].shape == batch["actions"].shape


def test_sample_batch_fallback_when_missing_expert_actions():
    with tempfile.TemporaryDirectory() as td:
        spec = DatasetSpec(
            action_dim=2,
            obs_vec_dim=3,
            action_low=-np.ones((2,), dtype=np.float32),
            action_high=np.ones((2,), dtype=np.float32),
        )
        store = EpisodeStore(td, spec)
        ep = _make_episode(T=6, obs_dim=3, act_dim=2, include_expert=False)
        store.add(ep)

        ds = EpisodeDataset(td)
        batch = ds.sample_batch(batch_size=1, seq_len=6, rng=np.random.default_rng(2))
        np.testing.assert_allclose(batch["expert_actions"], batch["actions"])


if __name__ == "__main__":
    test_episode_store_roundtrip_expert_actions()
    test_sample_batch_fallback_when_missing_expert_actions()
    print("OK")
