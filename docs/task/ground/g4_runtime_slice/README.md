# G4 Runtime Slice

Status: `2026-05-21` planned / held until G3 selects a slice.

Language:

- English canonical: `README.md`
- Chinese companion: not required yet; this is a high-churn task slice.

Inputs:

- [G3 execution surface design](../g3_execution_surface_design/README.md)
- [Ground standards overview](../../../standards/ground/README.md)
- [Ground minimal task structure](../../../standards/ground/minimal_task_structure.md)
- [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)

## Purpose

Implement one selected, maintained ground behavior slice through the shared
simulation lifecycle.

## Output

- [G4 selected runtime slice cluster](g4_selected_runtime_slice_cluster_20260521.md)

## Scope

In scope:

- one G3-selected runtime behavior
- focused tests proving shared lifecycle participation
- compatibility guards proving no private ground runtime path
- validation rollup and residual map

Out of scope:

- broad ground movement model
- direct-fire or indirect-fire runtime
- full terrain, logistics, or damage model
- public schema expansion beyond the selected slice

## Gate

G4 is mergeable when one ground behavior is exercised through maintained shared
entry points and tests prove air/naval compatibility is preserved.
