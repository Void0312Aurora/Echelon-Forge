# C++ Dependency And DTO Residuals

Language:
- English canonical: `cpp_dependency_and_dto_residuals.md`
- Chinese companion: not maintained (English-only work surface).

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/architecture/work/issues/cpp_dependency_and_dto_residuals.md`
Owner: `architecture/cpp-boundaries`
Last verified: `2026-08-08`
Content status: owner-local extraction from the completed T6 ledger; held
edges are design questions, not permission to edit include direction.

## Scope

This issue owns the residual C++ dependency edges and DTO ownership decisions
that require a measured architecture or schema migration. It excludes
calibration behavior and test-environment defects.

## Held Dependency Edges

The T6 matrix converged the missile-seeker edge and retained these five edges:

1. `core/engine/world_batch_runtime.cpp` → GPU interaction-broadphase types;
2. `core/engine/world_batch_runtime.h` → execution-episode controller;
3. `core/engine/world_batch_runtime.h` → GPU visual runtime;
4. the world-batch visual compatibility helper → GPU visual runtime;
5. `runtime/contracts/world_batch_contracts.h` → mission episode-batch
   preparation types.

The first four require a GPU/engine or facade/mission seam. The fifth embeds a
large mission-owned nested DTO graph and is a T1-scale schema-ownership
question; relocating one header would either invert the dependency or duplicate
the graph.

## Related Held DTOs

`ExecutionBatchStepResult` remains hand-written because its
`std::vector<std::array<double, 4>>` field is not token-safe for the current
X-macro preprocessor. `RecentEngagementEvents` remains a future candidate
outside the completed ledger's write set. Neither is an implementation task.

## Evidence Boundary And Promotion Gate

The source matrix is retained in the
completed T6 ledger (`git show 77610218:docs/plan/archive/unified_architecture_program_completed_20260727/t6_residual_ledger.md`).
Close an edge only after a consumer census, dependency-direction gate, ABI/
binding parity evidence where applicable, and an independently reviewed
architecture or DTO-family decision. A type move that merely inverts the edge
or creates a second hand-maintained shape does not pass the gate.

## Non-goals

- Do not edit the include-direction allowlist to hide a still-open edge.
- Do not move mission-owned aggregate types into neutral contracts by name
  similarity alone.
- Do not modify archived program records.
