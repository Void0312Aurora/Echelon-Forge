# GPU Exact World-Step Mainline Retirement

Date: 2026-04-16

## Decision

The maintained execution baseline has been reset to CPU exact world stepping
plus selected GPU helper paths.

The exact GPU world-step line is retained for archival research only. It is no
longer part of the maintained `p5` execution defaults.

## Keep

- `runtime.world_batch_vec_env` as the maintained execution rollout adapter
- `batch_visual_backend=gpu_host` as the maintained rollout-side GPU helper
- compiled batch observation packing on CPU
- CUDA learner-side bridges and device-resident rollout-buffer work
- compiled CPU execution runtime / episode-controller work under `src/core/mission`

## Retire From Maintained Defaults

- `runtime.exact_world_step_backend` in maintained `p5` configs
- exact-step GPU write-back cadence knobs in maintained configs
- exact-step cached-session promotion experiments as a production candidate
- exact-step parity and trace tooling as a maintained operator workflow

## Why

- the exact-step GPU line still does not clear its CPU-vs-GPU promotion gates
- the maintained repo already has higher-yield GPU helper paths that do not
  require changing exact ECS step semantics
- keeping the CPU exact-step lane as the source of truth reduces operational
  and debugging risk on the current training mainline

## If This Line Is Revived

- treat
  [gpu_exact_world_step_migration_plan.md](/home/void0312/CMO/docs/plan/gpu_exact_world_step_migration_plan.md)
  and
  [gpu_exact_world_step_rearchitecture_plan.md](/home/void0312/CMO/docs/plan/gpu_exact_world_step_rearchitecture_plan.md)
  as design provenance
- rerun
  [benchmark_exact_world_step_first_scope_chain_cached_session.py](/home/void0312/CMO/tools/diagnostics/benchmark_exact_world_step_first_scope_chain_cached_session.py)
  promotion gates before considering any return to maintained defaults
