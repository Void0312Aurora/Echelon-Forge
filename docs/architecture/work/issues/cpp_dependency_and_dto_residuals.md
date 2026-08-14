# C++ Dependency And DTO Residuals

Language:
- English canonical: `cpp_dependency_and_dto_residuals.md`
- Chinese companion: not maintained (English-only work surface).

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/architecture/work/issues/cpp_dependency_and_dto_residuals.md`
Owner: `architecture/cpp-boundaries`
Last verified: `2026-08-13`
Content status: owner-local extraction from the completed T6 ledger; held
edges are design questions, not permission to edit include direction.

## Scope

This issue owns the residual C++ dependency edges and DTO ownership decisions
that require a measured architecture or schema migration. It excludes
calibration behavior and test-environment defects.

## Held Dependency Edges

The execution-controller retirement closed the engine-to-mission controller
edge and the runtime-contracts-to-mission step-request edge. Three GPU/engine
edges remain:

1. `core/engine/world_batch_runtime.cpp` → GPU interaction-broadphase types;
2. `core/engine/world_batch_visual_binding_compatibility_types.h` → GPU visual
   runtime;
3. the world-batch visual compatibility helper → GPU visual runtime.

These require a GPU/engine integration seam; editing only the include spelling
would not resolve ownership.

## Related Held DTOs

`RecentEngagementEvents` remains a future candidate outside the completed
ledger's write set. The retired `ExecutionBatchStepResult` is no longer a DTO
residual.

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
