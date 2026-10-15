# WorldBatch failure contract

Language:
- English canonical: `world_batch_failure_contract.md`
- Chinese companion: [world_batch_failure_contract.zh.md](world_batch_failure_contract.zh.md)

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/architecture/standards/world_batch_failure_contract.md`
Owner: `architecture/runtime-workflow`
Last verified: `2026-10-12`

`WorldBatchRuntime` does not promise transactional rollback when a state-mutating
operation fails. A worker may have advanced or otherwise changed one world before
another world reports an exception.

This page describes the maintained owner contract exercised by the qualification
branch. The upstream `main` line has not yet received the local #210 port described
below, so branch evidence must not be reported as a production guarantee until the
owner repair is delivered and verified on mainline ancestry.

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

The native qualification test injects first/later worker-launch failures through
a private test accessor on actual 3/4-world batches. It verifies that already
started workers are joined before the exception reaches the caller, exports and
retry are fenced, a recovery launch failure keeps the fence, and a successful
reset restores operation. Clock observations remain diagnostics; the aggregate
Python projection still reports unknown per-world commit status.

This local integration ports PR #230's #210 owner implementation from
`7989800d284484c76ccd0aed77cca32300fb2dda` to the qualification branch's
`de19c3dbd69e9feb330b1291e84a210c53bfd09f` interface baseline. It preserves current
maintained command interfaces and broadphase types. The newer composition
diagnostics export and resize operation also reject an unhealthy generation.
The port is carried on the qualification branch; #210 remains open upstream
and this branch does not establish delivery to main.
