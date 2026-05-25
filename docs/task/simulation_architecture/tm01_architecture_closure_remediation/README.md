# TM01 Architecture Closure Remediation

Status: closed on `2026-05-25` as a temporary remediation project, with
post-TM02/TM03 status synchronized.

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
| Ground MVP tasking shell load fails because `recovery_approach_type` assignment can pass an incompatible value to the binding enum. | fixed and validated | `TM01-A` |
| `systems/combat` and `systems/naval` weapon release systems depend directly on `SimulationKernel&`. | ledgered by `TM01-B`; closed by `TM03` through `IWeaponReleaseService` | `TM03` close-out |
| WP24-L prose still describes compatibility defaults while current `agent_shim.py` defaults are maintained. | synced to maintained defaults | `TM01-C` |
| WP24 implementation was green in focused runtime/facade tests but initially had no canonical acceptance review. | governance gap recorded by TM01; closed by `TM02` | `TM02` close-out |
| Raw runtime and compatibility APIs remain for diagnostics/tests/compatibility. | controlled residual, not TM01 implementation work | deferred |

## Current Progress

- `TM01-A` is fixed and validated. The leader tasking shell now coerces ground
  recovery-approach values through the binding enum before assigning to
  `TaskOrder` or `LeaderIntent`; compile validation and the focused
  ground/leader pytest set passed on `2026-05-25`.
- `TM01-B` was recorded as a source-backed residual. `TM03 Launch Bridge
  Boundary` later closed the two explicit helper dependencies by introducing
  `IWeaponReleaseService`; TM01 keeps the ledger provenance and does not claim
  broader P7 launch/fire-control redesign.
- `TM01-C` is synced. WP24 docs now describe the maintained `agent_shim.py`
  defaults correctly. No canonical WP24 acceptance review was created in this
  lane; `TM02 WP24 Acceptance Closure` later published the canonical review.
- `TM01-D` completed the final integration pass. It publishes the focused
  validation outcomes, residual register, and close/block recommendation
  without claiming broader architecture closure.

## Final Integration Result

- Focused validation is green. The `py_compile` gate passed for
  `python/rl/tasking/leader_tasking.py`, and the focused ground/leader pytest
  set passed with `27 passed` using the local `build-local-win` `ef_py`
  artifact and explicit Windows DLL directories.
- Residual ownership is still explicit: TM01 ledgered the `TM01-B` launch
  bridge residual, and TM03 later closed that narrow residual for the two helper
  headers. Raw-runtime/compatibility APIs remain controlled residuals for
  diagnostics, tests, and compatibility.
- WP24 canonical acceptance review stayed out of this lane. TM01 created no
  acceptance review; TM02 later published the WP24 canonical acceptance review
  and synchronized indexes.
- Close/block recommendation: focused maintained-path remediation may close for
  the audited slice only. Broader architecture closure, P7 launch contracts
  beyond the TM03 helper seam, ground runtime, and raw-runtime/compatibility
  retirement remain explicitly not closed.

## Exit State

TM01 is closed for the audited slice only. Its post-TM02/TM03 posture is:

- `TM01-A` is fixed and validated.
- `TM01-B` is source-backed and ledgered; its narrow launch-bridge boundary
  residual was later closed by TM03 for the two explicit helper headers.
- `TM01-C` is synced to the maintained `agent_shim.py` defaults, with no
  canonical WP24 acceptance review created by TM01.
- `TM01-D` is complete as the final integration pass and records the audited
  slice close recommendation.
- `TM02` published the WP24 canonical acceptance review outside TM01.
- `TM03` closed the `systems -> SimulationKernel` weapon-release helper
  dependency outside TM01.

TM01 must not claim that broader architecture closure, ground runtime, P7 launch
contract redesign beyond the TM03 helper seam, or compatibility/raw-runtime
residual retirement are complete.
