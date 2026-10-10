# WorldBatch failure contract

`WorldBatchRuntime` does not promise transactional rollback when a state-mutating
operation fails. A worker may have advanced or otherwise changed one world before
another world reports an exception.

The maintained contract is fail-closed:

1. the first runtime exception is joined and rethrown to the caller;
2. the affected `WorldBatchRuntime` generation is marked unhealthy;
3. every maintained batch operation rejects a retry while that generation is unhealthy;
4. callers may inspect the failure through `batch_healthy()` and
   `batch_failure_reason()`, then recover by calling `reset_batch()`;
5. only a successful reset clears the unhealthy state and permits another batch operation.

`reset_batch()` is a recovery boundary, not a rollback. It reinitializes all worlds
using the requested seeds. Raw `world_raw_quarantine()` access remains a diagnostic
escape hatch and is not a synchronized recovery API. Callers must not continue a
failed batch or retry it as though all worlds had completed.

Input validation that fails before any world operation, such as an invalid seed
vector or timestep vector, does not poison the batch. Runtime task failures and
worker-launch failures do poison it. Read-only batch exports use the same guard so
maintained callers cannot consume a failed generation as a successful synchronized
step.
