# WP13-B Backend Profile Registry Runtime Gate

Status: `2026-05-20` planned / first-wave dispatch candidate.

Language:

- English canonical: `wp13_backend_profile_registry_gate_cluster_20260520.md`
- Chinese companion:
  [wp13_backend_profile_registry_gate_cluster_20260520.zh.md](wp13_backend_profile_registry_gate_cluster_20260520.zh.md)

Inputs:

- [WP13 backend fidelity expansion](backend_fidelity_expansion_wp13_20260520.md)
- [WP6 backend profile policy](../wp6_backend_profile_policy/backend_profile_policy_wp6_20260519.md)
- [WP6 backend profile registry](../wp6_backend_profile_policy/wp6_backend_profile_registry_20260519.md)
- [WP6 resident-state boundary rules](../wp6_backend_profile_policy/wp6_resident_state_boundary_rules_20260519.md)
- [WP7 registry materialization](../wp7_backend_capability_materialization/wp7_registry_materialization_cluster_20260519.md)
- [WP7 promotion evidence gates](../wp7_backend_capability_materialization/wp7_promotion_evidence_gates_cluster_20260519.md)

## 1. Purpose

`WP13-B` turns the accepted backend profile documentation registry into a
minimal code-owned gate. It should make profile records inspectable and
machine-checkable before any runtime capability surface can cite them.

The first runtime registry may be small. It should include the accepted seed
records:

- `cpu_exact.reference`
- `gpu_helpers.diagnostics_only`
- `gpu_exact.unmaintained_candidate`
- `resident_state.unmaintained_candidate`
- `shadow_compare.unmaintained_candidate`

Only `cpu_exact.reference` is maintained in the initial gate.

## 2. Scope

In scope:

- add a C++ contract/header/helper for backend profile records or schema;
- encode required fields for maintained profiles;
- validate maintained, candidate, and diagnostics-only boundaries;
- expose profile lookup and rejection reason helpers for A/C/D consumers;
- add tests proving candidate and diagnostics-only rows do not become
  maintained support.

Out of scope:

- parity budget row implementation beyond `parity_budget_ref`;
- changing `RuntimeCapabilities` support booleans to true;
- GPU helper/probe implementation;
- backend selection or execution dispatch;
- resident-state ownership promotion.

## 3. Candidate Implementation Seams

Inspect before editing:

- `src/runtime/contracts/`
- `src/runtime/facade/runtime_facade_types.h`
- `src/runtime/facade/runtime_facade.cpp`
- `tests/architecture/`
- `tests/runtime/facade/test_runtime_facade.py`
- `tests/test_gpu_runtime_bindings.py`

Preferred approach:

- create a small backend profile contract surface under `src/runtime/contracts/`
  if no suitable owner exists;
- keep row data close to compile-time constants or simple functions;
- provide validators such as `is_maintained_backend_profile(...)` or
  `validate_backend_profile_for_capability(...)`;
- return stable rejection reasons for unmaintained candidates and diagnostics
  rows;
- keep Python exposure for `WP13-E` unless A/E chooses to bind the helper now.

## 4. Required Profile Fields

The gate must preserve the WP6 required metadata:

| Field | Required behavior |
|-------|-------------------|
| `backend_profile_id` | Stable id. |
| `profile_class` | `reference`, `accelerated_exact`, `resident_state`, `approximate`, or `diagnostics_only`. |
| `comparison_reference` | Maintained semantic comparison anchor or explicit non-maintained marker. |
| `host_state_owner` | Host-owned state or output scope. |
| `backend_state_owner` | Backend-owned state or explicit absence. |
| `sync_policy` | Host-owned, backend-owned, partial-sync, observation-only, export-only, or blocked. |
| `state_scope` | Covered state family or candidate scope. |
| `parity_budget_ref` | Profile-owned budget reference. |
| `observability_scope` | Maintained or diagnostics-only export scope. |
| `compatibility_rule` | Legacy/helper projection rule. |
| `deprecation_rule` | Removal, narrowing, or promotion condition. |
| `validation_gate` | Review/test gate required before maintained use. |

## 5. Acceptance Tests

Minimum tests:

- registry exposes all accepted seed profile ids;
- only `cpu_exact.reference` is maintained;
- candidate exact GPU, resident-state, and shadow rows return fail-closed
  rejection reasons;
- diagnostics-only GPU helper row cannot authorize maintained exact GPU,
  resident-state, or shadow support;
- maintained-row validator fails if a required field is missing or empty.

Suggested commands:

```bash
git diff --check
cmake --build build-workshop -j4
CMO_BUILD_DIR=build-workshop pytest -q tests/architecture tests/runtime/facade/test_runtime_facade.py tests/test_gpu_runtime_bindings.py
```

## 6. Handoff Contract

Return:

- registry/contract files touched;
- profile ids and profile classes encoded;
- validation helper names and rejection reason values;
- tests added or updated;
- exact commands run and outcomes;
- blockers for `WP13-C` budget binding or `WP13-A` capability projection;
- residuals where docs remain richer than the first code-owned registry.
