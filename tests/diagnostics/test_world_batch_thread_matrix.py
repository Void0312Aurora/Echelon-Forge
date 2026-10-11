from __future__ import annotations

from tools.diagnostics.benchmarks.world_batch_thread_matrix import _effective_action_seed


def test_action_seed_is_shared_across_thread_matrix_cells() -> None:
    seeds = {
        _effective_action_seed(experiment_seed=123, n_envs=8)
        for _configured_threads in (1, 2, 4, 8, 0)
    }
    assert seeds == {8123}
