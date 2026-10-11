from __future__ import annotations

import numpy as np

from tools.diagnostics.benchmarks.world_batch_thread_matrix import (
    _build_actions,
    _effective_action_seed,
)


def test_action_seed_is_shared_across_thread_matrix_cells() -> None:
    configured_threads = (1, 2, 4, 8, 0)
    seeds = {
        worker_threads: _effective_action_seed(experiment_seed=123, n_envs=8)
        for worker_threads in configured_threads
    }
    assert set(seeds.values()) == {8123}

    action_streams = {
        _configured_threads: _build_actions(
            steps=4,
            n_envs=8,
            action_dim=3,
            seed=seed,
        )
        for _configured_threads, seed in seeds.items()
    }
    reference = action_streams[configured_threads[0]]
    for stream in action_streams.values():
        assert len(stream) == len(reference)
        for actual, expected in zip(stream, reference):
            np.testing.assert_array_equal(actual, expected)
