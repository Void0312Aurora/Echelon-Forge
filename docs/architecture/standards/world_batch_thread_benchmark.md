# WorldBatch Thread Matrix Benchmark

`WorldBatchRuntime` defaults to one worker and creates transient workers only
when a caller explicitly selects multiple workers or auto mode. Issue #211 is
therefore a measurement task, not a commitment to introduce a worker pool.

## Reproducible command

Run the maintained benchmark entry point from a checkout that has a local
`ef_py` build:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/diagnostics/benchmark.py \
  --family world_batch_thread_matrix \
  --scenario scenarios/takeoff/takeoff.json \
  --n-envs 1,2,4,8,16,32,64 \
  --worker-threads 1,2,4,8,0 \
  --steps 64 \
  --repeats 5 \
  --warmup-steps 2 \
  --json-out artifacts/world_batch_thread_matrix.json
```

The output records the repository revision, host and Python information,
configured and effective worker counts, all samples, median, p95, and the
maximum for each case. Keep the JSON artifact with the benchmark report; do
not compare results across revisions without recording both revisions and
host configuration.

## Timing boundaries

All times are normalized to milliseconds per environment step. The wall-clock
sample covers the maintained `WorldBatchVecEnv.step()` call. Its stage samples
are collected from the existing runtime timing contract:

- `action_prepare_ms`: action normalization and assignment construction;
- `batch_step_ms`: native action dispatch plus `WorldBatchRuntime.step_batch()`;
- `state_read_ms`: native truth and instrument-state reads;
- `command_sync_ms`, `behavior_update_ms`, `obs_build_ms`, and
  `reward_info_ms`: downstream adapter work.

This separates transient native batch dispatch from Python adapter and
observation work. It does not claim to measure policy inference or a complete
training rollout; add that workload separately before making a production RL
throughput claim.

## Decision rule

Use `worker_threads=1` as the stable baseline. Consider a persistent worker
prototype only when a repeated matrix shows a material, repeatable reduction
in wall-clock and `batch_step_ms` at a maintained workload, while output
determinism and exception/failure contracts remain unchanged. Tiny workloads,
single-world cases, and local CPU utilization alone are insufficient evidence
for changing the default.
