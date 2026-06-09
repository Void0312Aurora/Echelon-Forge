# WP12-A Law 14 Read-Side Enforcement

Status: `2026-05-20` accepted / implementation mergeable.

Language:

- English canonical: `wp12_law14_read_side_enforcement_cluster_20260520.md`
- Chinese companion:
  [wp12_law14_read_side_enforcement_cluster_20260520.zh.md](wp12_law14_read_side_enforcement_cluster_20260520.zh.md)

Inputs:

- [WP12 information and agency enforcement](information_agency_enforcement_wp12_20260520.md)
- [WP11-D consumer boundary pre-gates](../wp11_facade_vertical_slice_provenance/wp11_consumer_boundary_pregates_cluster_20260520.md)
- [WP11 acceptance review](../../review/wp11_facade_vertical_slice_provenance_acceptance_review_20260520.md)
- [Post-WP9 gap analysis](../../review/post_wp9_gap_analysis_20260520.md)

## 1. Purpose

`WP12-A` turns the WP11 maintained-vs-diagnostics consumer pre-gates into a
focused Architecture Law 14 read-side enforcement slice.

Architecture Law 14 says maintained decision paths consume `ObservationPacket`
and, when needed, `DecisionBelief`; they must not consume `World Truth` unless
the path is diagnostics-only.

## 2. Scope

In scope:

- enforce the focused maintained consumer path through provenance-labeled
  packet or belief inputs;
- fail closed when a maintained fixture consumes unlabeled truth, raw ECS, or
  privileged traces;
- preserve diagnostics-only and compatibility-only truth/raw-runtime fixtures
  through explicit labels or allowlists;
- add tests that prove both rejected and allowed paths;
- record residuals for repository-wide Law 14 coverage.

Out of scope:

- global ban on all raw ECS reads;
- full static analysis for every Python and C++ policy path;
- Agency Graph authority validation;
- decision-model dispatch;
- backend/fidelity or learning-face changes.

## 3. Candidate Implementation Seams

Inspect before editing:

- `python/rl/runtime/agent_shim.py`
- `tests/runtime/test_agent_shim.py`
- `tests/architecture/policy_execution/test_belief_and_read_side_boundaries.py`
- `src/runtime/contracts/policy_contracts.h`
- `src/runtime/facade/runtime_facade_types.h`
- `src/interfaces/python/bindings_runtime.cpp`

Preferred approach:

- extend the existing WP11 pre-gate helpers instead of creating a second guard
  framework;
- keep raw-truth diagnostics explicitly labeled;
- use a narrow failing fixture to prove maintained paths cannot silently bypass
  `ObservationPacket` / `DecisionBelief`.

## 4. Gate Rules

| Boundary | Required behavior |
|----------|-------------------|
| Maintained consumer | Must consume provenance-labeled packet or belief input in the focused slice. |
| Diagnostics-only consumer | May consume truth/raw ECS only when explicitly labeled or allowlisted. |
| Compatibility adapter | May remain only when labeled compatibility-only and not used as maintained decision evidence. |
| Unknown source | Fails closed in focused guard tests. |

## 5. Acceptance Tests

Minimum tests:

- maintained consumer fixture passes with labeled `ObservationPacket` or
  `DecisionBelief`;
- maintained consumer fixture fails with `WorldTruth`, raw ECS, privileged
  trace, or unlabeled input;
- diagnostics-only fixture using truth/raw ECS remains explicit and allowed;
- architecture test documents the exact allowlist and does not claim global
  repository-wide enforcement;
- no new raw runtime escape hatch is introduced.

## 6. Handoff Contract

Return:

- guard files and allowlists touched;
- maintained and diagnostics-only fixture paths;
- tests added or updated;
- exact commands run and outcomes;
- blockers and residuals for wider Law 14 coverage;
- integration notes for `WP12-D` and `WP12-E`.
