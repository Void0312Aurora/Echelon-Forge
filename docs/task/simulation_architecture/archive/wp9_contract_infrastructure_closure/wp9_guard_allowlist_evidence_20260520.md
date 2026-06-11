# WP9 Guard Allowlist Evidence

Status: `2026-05-20` evidence note for `WP9-D Guard Enforcement`.

This note records the explicitly labeled direct `sim` access families that the
architecture guard accepts for the current closure pass. The guard is
intentionally narrow: it covers compatibility bridges, diagnostics fixtures,
and test-only surfaces, and it does not try to ban legacy runtime usage that
already has an owned label elsewhere in the repository.

## Allowed Labels

| Label | Meaning |
|-------|---------|
| `compatibility_only` | A maintained bridge that centralizes legacy simulation access behind a named adapter or runtime wrapper. |
| `diagnostics_only` | Evidence, oracle, or inspection code that reads privileged runtime state without becoming maintained policy truth. |
| `test_only` | Fixtures and tests that exercise binding or surface behavior only. |

## Allowed File Families

| Label | File family evidence |
|-------|----------------------|
| `compatibility_only` | `python/rl/control/wrappers.py`, `python/rl/runtime/cooperative_world_batch_vec_env.py`, `python/rl/runtime/leader_world_batch_runtime.py`, `python/rl/runtime/single_world_batch_runtime.py`, `python/rl/runtime/world_batch/cooperative_director.py`, `python/rl/runtime/world_batch/runtime_access.py`, `python/rl/runtime/world_batch_vec_env.py`, `python/rl/tasking/leader_tasking.py`, `python/scenario/runtime/kernel_apply.py` |
| `compatibility_only` | `gym_envs/` plus the compatibility bridge files above |
| `diagnostics_only` | `python/testing/contracts/`, `examples/viz/runtime/`, `tools/diagnostics/`, `tools/eval/`, `tools/maintenance/damage_model_candidate_artifacts.py runtime-authority-exercise`, and `world_model_train.py` |
| `test_only` | `tests/` |

## Guard Note

The guard checks for explicit labels rather than a blanket repository-wide ban.
That preserves documented compatibility adapters and keeps diagnostics and test
fixtures visible during migration.
