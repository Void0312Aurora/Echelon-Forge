# WorldBatch failure contract

Language:
- English canonical: `world_batch_failure_contract.md`
- Chinese companion: [world_batch_failure_contract.zh.md](world_batch_failure_contract.zh.md)

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/architecture/standards/world_batch_failure_contract.md`
Owner: `architecture/runtime-workflow`
Last verified: `2026-10-15`

`WorldBatchRuntime` does not promise transactional rollback when a state-mutating
operation fails. A worker may have advanced or otherwise changed one world before
another world reports an exception.

This page describes the maintained owner contract now integrated into `main` by PR
#278 (merge `9edcb14dacd1127442efe0504bfee7c487a53628`) and re-verified on the
final RFC stack at `main@ed9e476be4b57831001e0ef8e42d500989933e0e`. The
implementation is a bounded native fail-closed behavior. It does not by itself
make the proposed #251 ADR accepted or establish production supervisor isolation,
per-world commit truth, rollback, or transactional semantics.

The maintained contract is fail-closed:

1. the first runtime exception is joined and rethrown to the caller;
2. the affected `WorldBatchRuntime` generation is marked unhealthy;
3. every maintained batch operation rejects a retry while that generation is unhealthy;
4. callers may inspect the failure through `batch_healthy()` and
   `batch_failure_reason()` and `batch_requires_host_recreate()`; reset is allowed
   only when native pipeline scopes are complete, otherwise retire the host process;
5. only a successful reset clears the unhealthy state and permits another batch operation.

The maintained `RuntimeFacade` exposes the same native-owned snapshot through
`batch_failure_status()`.  Its `healthy`, `generation`, `failure_reason`, and
`requires_host_recreate` fields are a projection of the active backend; the
facade and Python bindings do not reconstruct recovery state from exceptions or
clock observations.  The CPU exact backend is the production implementation of
this contract.  Candidate backends may report only the failure information they
own and must not be treated as proof of CPU or host parity.

`reset_batch()` is a recovery boundary, not a rollback. It reinitializes all worlds
using the requested seeds. Raw `world_raw_quarantine()` access remains a diagnostic
escape hatch and is not a synchronized recovery API. Callers must not continue a
failed batch or retry it as though all worlds had completed.

A C++ exception inside a Flecs callback can leave its readonly/defer and iterator
scopes unfinished. Episode reset cannot repair those internals. Reset and raw
step reject that state before mutation; failed reset keeps the batch unhealthy
and its generation unchanged. The native recovery diagnostic remains readable
through the fence, and Python projects `terminate_generation` when the native
owner requires host recreation. This does not certify in-process world teardown.
The test-only `ef_native_system_fault_probe` verifies this path, fatal/nontermination
bounds and fresh process startup; it does not deploy a production supervisor.

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

The implementation originated in PR #230's #210 owner repair at
`7989800d284484c76ccd0aed77cca32300fb2dda` and was adapted during qualification
from the historical `de19c3dbd69e9feb330b1291e84a210c53bfd09f` interface baseline.
That historical branch and SHA remain in the record for provenance; the maintained
owner repair is now present on `main`. #210 remains open for the broader contract
and acceptance work. The newer composition diagnostics export and resize operation
also reject an unhealthy generation.
