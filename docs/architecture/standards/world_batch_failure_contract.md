# WorldBatch failure contract

Language:
- English canonical: `world_batch_failure_contract.md`
- Chinese companion: [world_batch_failure_contract.zh.md](world_batch_failure_contract.zh.md)

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/architecture/standards/world_batch_failure_contract.md`
Owner: `architecture/runtime-workflow`
Last verified: `2026-10-11`

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

This local integration ports PR #230's #210 owner implementation from
`7989800d284484c76ccd0aed77cca32300fb2dda` to current main. It preserves current
maintained command interfaces and broadphase types. The newer composition
diagnostics export and resize operation also reject an unhealthy generation.
The port is carried on the qualification branch; #210 remains open upstream
and this branch does not establish delivery to main.
