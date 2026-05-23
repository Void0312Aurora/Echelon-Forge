# WP12-C Information Transformation Surface

Status: `2026-05-20` accepted / implementation mergeable.

Language:

- English canonical: `wp12_information_transformation_surface_cluster_20260520.md`
- Chinese companion:
  [wp12_information_transformation_surface_cluster_20260520.zh.md](wp12_information_transformation_surface_cluster_20260520.zh.md)

Inputs:

- [WP12 information and agency enforcement](information_agency_enforcement_wp12_20260520.md)
- [Post-WP9 gap analysis](../../review/post_wp9_gap_analysis_20260520.md)
- [Simulation system architecture design](../../../plan/architecture/simulation_system_architecture_design.md)

## 1. Purpose

`WP12-C` makes the architecture's information-state transformations
machine-checkable for the first maintained slice. The goal is not to rewrite
every producer; it is to expose a stable transformation vocabulary and evidence
surface that later producers can adopt.

Required transformation chain:

```text
World Truth -> Sensed State
Sensed State -> Track State
Track State -> Shared Tactical Picture
Shared Tactical Picture -> Agent Observation
Agent Observation -> Decision Belief
Decision Belief -> ActionIntentPacket
```

## 2. Scope

In scope:

- add a canonical transformation-name vocabulary or registry;
- associate each transformation with source layer, target layer, and evidence
  requirements;
- require maintained packet/belief fixtures in the selected slice to name their
  transformation step;
- add architecture or runtime tests rejecting missing or illegal
  transformation declarations;
- preserve diagnostics-only truth paths as explicitly diagnostics-only.

Out of scope:

- full sensor model rewrite;
- full track fusion or data-link implementation;
- complete Shared Tactical Picture producer;
- changing all observation schemas at once;
- backend/fidelity or capability-composition work.

## 3. Candidate Implementation Seams

Inspect before editing:

- `src/runtime/contracts/policy_contracts.h`
- `src/runtime/facade/runtime_facade_types.h`
- `src/runtime/facade/runtime_facade.cpp`
- `src/interfaces/python/bindings_runtime.cpp`
- `tests/runtime/facade/test_runtime_facade.py`
- `tests/runtime/bindings/test_bindings_runtime_dto_surface.py`
- `tests/architecture/test_policy_belief_boundaries.py`

Preferred approach:

- reuse `InformationStateSource` and WP11 provenance vocabulary where possible;
- model transformation evidence as contract metadata or helper validation
  rather than a broad runtime rewrite;
- prove at least `Shared Tactical Picture -> Agent Observation` and
  `Agent Observation -> Decision Belief` in the focused maintained path.

## 4. Gate Rules

| Boundary | Required behavior |
|----------|-------------------|
| Known transformation | Declares source layer, target layer, stable name, and evidence requirement. |
| Maintained packet/belief | Names a legal transformation step and source version/provenance. |
| Illegal direct jump | Rejected unless explicitly diagnostics-only. |
| Unknown transformation | Fails closed in focused tests. |
| Diagnostics transformation | Allowed only when labeled diagnostics-only and not used as maintained decision evidence. |

## 5. Acceptance Tests

Minimum tests:

- canonical transformation vocabulary is visible to tests;
- maintained packet or belief names a legal transformation step;
- missing transformation metadata fails;
- illegal `World Truth -> ActionIntentPacket` maintained shortcut fails;
- diagnostics-only shortcut remains explicit;
- tests do not claim every producer has been migrated.

## 6. Handoff Contract

Return:

- transformation vocabulary/registry/helper files touched;
- packet/belief metadata fields or validators touched;
- tests added or updated;
- exact commands run and outcomes;
- blockers and residuals for wider producer adoption;
- integration notes for `WP12-D` and `WP12-E`.
