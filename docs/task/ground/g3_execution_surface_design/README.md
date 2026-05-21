# G3 Execution Surface Design

Status: `2026-05-21` ready for design preflight after accepted G1-G2 evidence.

Language:

- English canonical: `README.md`
- Chinese companion: not required yet; this is a high-churn task slice.

Inputs:

- [G1 contract skeleton](../g1_contract_skeleton/README.md)
- [G2 content and test seed](../g2_content_test_seed/README.md)
- [Ground standards overview](../../../standards/ground/README.md)
- [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)

## Purpose

Design the first ground execution surface before runtime behavior is written.

## Output

- [G3 execution surface preflight cluster](g3_execution_surface_preflight_cluster_20260521.md)

## Scope

In scope:

- decide whether the first runtime slice is tasking-only or includes a tiny
  command surface
- define stage coverage beyond G1
- name consumed and produced packets
- define observation/reporting surface candidates
- map terrain/environment dependencies and explicit deferrals

Out of scope:

- implementing movement, sensing, fire-control, or observation export
- large `MissionCommand` expansion
- terrain realism implementation

## Gate

G3 is mergeable when it names one safe G4 runtime slice and records all
deferred surfaces honestly.

Current release condition: design preflight only. G4 remains held until G3
selects one bounded runtime candidate, write scope, and focused test plan.
