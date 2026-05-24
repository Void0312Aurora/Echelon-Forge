# TM01 Architecture Closure Remediation

Status: opened on `2026-05-24` as a temporary remediation project.

TM01 records the finite remediation work that follows the implementation-level
architecture closure audit. It is intentionally a `TM` project instead of a new
`WP25`: the historical `WP2.5 / WP25 Scheduler Semantics Freeze` already exists
in archive, and this slice is a bounded repair lane rather than a new
architecture expansion package.

Governance:

- Follow the [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)
  for any delegated worker or integration pass.
- Use the task-cluster packet as the only active dispatch surface for this
  temporary project.
- Do not dispatch work that is not mapped to a named TM01 cluster.
- Stop and re-scope if a cluster exceeds its planned repair-round cap.

Planning surface:

- [TM01 Architecture Closure Task Clusters](tm01_architecture_closure_task_clusters_20260524.md)

## Closure Threshold

TM01 only covers findings that satisfy at least one of these conditions:

- The path is already declared maintained, accepted, or current close-out
  evidence.
- A current focused test fails on a declared maintained or accepted path.
- A maintained path bypasses the runtime facade or consumes raw runtime state.
- A source dependency contradicts an explicit architecture boundary and is narrow
  enough to record or repair without reopening a broad refactor.

Explicit non-goals:

- Do not implement full ground movement, sensing, fires, damage, or observation
  export.
- Do not redesign all P7 launch/fire-control semantics.
- Do not delete every raw `SimulationKernel`, `WorldBatchRuntime`, diagnostics,
  or compatibility API.
- Do not rewrite all historical WP24 documents.
- Do not run broad full-suite closure unless a focused validation gate fails in a
  way that makes focused evidence inconclusive.

## Current Finding Map

| Finding | TM01 classification | Current owner |
|---------|---------------------|---------------|
| Ground MVP tasking shell load fails because `recovery_approach_type` assignment can pass an incompatible value to the binding enum. | implementation blocker | `TM01-A` |
| `systems/combat` and `systems/naval` weapon release systems depend directly on `SimulationKernel&`. | architecture residual / source-backed ledger | `TM01-B` |
| WP24-L prose still describes compatibility defaults while current `agent_shim.py` defaults are maintained. | documentation/governance mismatch | `TM01-C` |
| WP24 implementation is green in focused runtime/facade tests but has no canonical acceptance review. | governance closure gap | `TM01-C` / `TM01-D` |
| Raw runtime and compatibility APIs remain for diagnostics/tests/compatibility. | controlled residual, not TM01 implementation work | deferred |

## Exit State

TM01 may close only when:

- `TM01-A` is either fixed and validated, or explicitly marked blocked with a
  named owner and failing command.
- `TM01-B` records the launch-bridge residual without expanding into a P7
  redesign.
- `TM01-C` resolves the WP24 provenance-default documentation mismatch and states
  whether canonical acceptance review is in or out of the current lane.
- `TM01-D` publishes focused validation outcomes and residual ownership.

TM01 must not claim that ground runtime, P7 launch contracts, or public escape
hatch retirement are complete.
