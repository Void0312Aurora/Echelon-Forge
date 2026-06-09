# WP12-D Intent Injection Authority Guard

Status: `2026-05-20` accepted / implementation mergeable.

Language:

- English canonical: `wp12_intent_injection_authority_guard_cluster_20260520.md`
- Chinese companion:
  [wp12_intent_injection_authority_guard_cluster_20260520.zh.md](wp12_intent_injection_authority_guard_cluster_20260520.zh.md)

Inputs:

- [WP12 information and agency enforcement](information_agency_enforcement_wp12_20260520.md)
- [WP12-A Law 14 read-side enforcement](wp12_law14_read_side_enforcement_cluster_20260520.md)
- [WP12-B agency role authority boundary](wp12_agency_role_authority_cluster_20260520.md)
- [WP12-C information transformation surface](wp12_information_transformation_surface_cluster_20260520.md)
- [WP10 causal runtime foundation](../wp10_causal_runtime_foundation/causal_runtime_foundation_wp10_20260520.md)
- [WP11 facade vertical slice and provenance](../wp11_facade_vertical_slice_provenance/facade_vertical_slice_provenance_wp11_20260520.md)

## 1. Purpose

`WP12-D` integrates the read-side, role-authority, and transformation surfaces
into the first maintained decision-to-intent guard. A maintained
`DecisionBelief` may produce an `ActionIntentPacket` or
`CoordinationIntentPacket` only when the path carries provenance, source ids,
role authority, valid timing metadata, and uses the facade-compatible injection
seam.

## 2. Scope

In scope:

- guard the focused `DecisionBelief -> ActionIntentPacket` path;
- optionally cover `DecisionBelief -> CoordinationIntentPacket` if the same
  validator surface makes it low-risk;
- require provenance labels, transformation step, source id, role authority,
  action interface, `effective_time`, `valid_until`, and `merge_policy` where
  the packet family already owns those fields;
- reject unlabeled, unauthorized, expired, or raw-runtime-injected maintained
  intents;
- add integration tests over the WP10/WP11 facade seam.

Out of scope:

- broad command/tasking runtime rewrite;
- full policy/control/physics cadence;
- global Agency Graph dispatcher;
- new raw command/control injection path;
- backend/fidelity, capability composition, or counterfactual work.

## 3. Candidate Implementation Seams

Inspect before editing:

- `src/runtime/contracts/policy_contracts.h`
- `src/runtime/facade/runtime_facade_types.h`
- `src/runtime/facade/runtime_facade.cpp`
- `src/interfaces/python/bindings_runtime.cpp`
- `python/rl/runtime/agent_shim.py`
- `tests/runtime/facade/test_runtime_facade_window_loop_injection.py`
- `tests/runtime/bindings/test_bindings_runtime_dto_surface.py`
- `tests/architecture/policy_execution/test_belief_and_read_side_boundaries.py`

Preferred approach:

- compose validators from `WP12-A`, `WP12-B`, and `WP12-C` instead of
  duplicating their logic;
- route accepted intents through the existing WP10 cross-layer request/injection
  seam;
- keep invalid intent evidence visible in tests without silently dropping the
  reason.

## 4. Gate Rules

| Boundary | Required behavior |
|----------|-------------------|
| Authorized maintained intent | Carries valid belief provenance, legal transformation step, source id, role authority, action interface, timing metadata, and merge policy. |
| Missing provenance | Rejected. |
| Invalid or missing role authority | Rejected. |
| Illegal transformation shortcut | Rejected unless diagnostics-only and not injected as maintained action. |
| Raw runtime injection | Rejected for maintained action/coordination paths. |
| Expired or future-invalid timing | Rejected or queued according to existing cross-layer request rules, with test evidence. |

## 5. Acceptance Tests

Minimum tests:

- valid maintained belief-to-intent path is accepted through facade-compatible
  injection;
- missing provenance fails;
- invalid role authority fails;
- illegal transformation shortcut fails;
- raw runtime injection bypass fails;
- timing/validity metadata behavior is tested or explicitly blocked with a
  named residual;
- no claim is made for full policy/control/physics cadence.

## 6. Handoff Contract

Return:

- validators and facade/injection glue touched;
- accepted and rejected packet fixtures;
- tests added or updated;
- exact commands run and outcomes;
- blockers and residuals for broader intent families;
- integration notes for `WP12-E`.
