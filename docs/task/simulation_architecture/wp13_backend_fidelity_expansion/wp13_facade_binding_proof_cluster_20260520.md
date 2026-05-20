# WP13-E Facade And Binding Proof

Status: `2026-05-20` planned / second-wave integration candidate.

Language:

- English canonical: `wp13_facade_binding_proof_cluster_20260520.md`
- Chinese companion:
  [wp13_facade_binding_proof_cluster_20260520.zh.md](wp13_facade_binding_proof_cluster_20260520.zh.md)

Inputs:

- [WP13 backend fidelity expansion](backend_fidelity_expansion_wp13_20260520.md)
- [WP13-A runtime capability query](wp13_runtime_capability_query_cluster_20260520.md)
- [WP13-B backend profile registry gate](wp13_backend_profile_registry_gate_cluster_20260520.md)
- [WP13-C parity budget evidence gate](wp13_parity_budget_evidence_gate_cluster_20260520.md)
- [WP13-D fidelity profile request gate](wp13_fidelity_profile_request_gate_cluster_20260520.md)
- [WP11 facade vertical slice and provenance](../wp11_facade_vertical_slice_provenance/facade_vertical_slice_provenance_wp11_20260520.md)
- [WP12 information and agency enforcement](../wp12_information_agency_enforcement/information_agency_enforcement_wp12_20260520.md)

## 1. Purpose

`WP13-E` proves that backend/fidelity query and rejection behavior is visible
through maintained facade and Python binding surfaces. It is the proof lane, not
the owner of the registry, budget, or fidelity semantics.

The desired evidence is boring in the best way: a caller can inspect supported
baseline metadata, submit or validate unsupported backend/fidelity requests,
and receive stable fail-closed reasons without touching raw runtime or GPU
helper paths.

## 2. Scope

In scope:

- expose the A-D surfaces through `RuntimeFacade` and/or Python bindings;
- add binding smoke tests for new DTOs, fields, or helper functions;
- add facade proof tests for query, rejection, and evidence visibility;
- preserve existing layering guards around GPU helper/probe implementation;
- document residuals if a C++ helper remains intentionally unbound.

Out of scope:

- creating profile or budget records owned by B/C;
- defining new fidelity request semantics owned by D;
- backend selection, execution dispatch, adaptive scheduling, or promotion;
- raw `WorldBatchRuntime` escape hatches.

## 3. Candidate Implementation Seams

Inspect after A-D land:

- `src/runtime/facade/runtime_facade.h`
- `src/runtime/facade/runtime_facade_types.h`
- `src/runtime/facade/runtime_facade.cpp`
- `src/interfaces/python/bindings_runtime.cpp`
- `tests/runtime/facade/test_runtime_facade.py`
- `tests/runtime/bindings/test_bindings_runtime_dto_surface.py`
- `tests/runtime/bindings/test_bindings_policy_surface.py`
- `tests/architecture/test_runtime_facade_layering.py`

Preferred approach:

- bind only stable DTOs/helpers that tests can exercise immediately;
- keep all unsupported capability requests fail-closed;
- ensure binding names match C++ names closely enough for maintenance;
- prefer facade-shaped proof over raw helper invocation.

## 4. Gate Rules

| Boundary | Required behavior |
|----------|-------------------|
| Facade visibility | Query and rejection evidence is accessible through maintained facade APIs or DTOs. |
| Binding visibility | Python callers can inspect the same stable fields or helper results. |
| Layering | Facade/core does not call GPU helper/probe implementation for capability answers. |
| No raw backend path | Proof does not require direct `WorldBatchRuntime` access or GPU helper path. |
| Conservative support | Existing unsupported support booleans remain false. |

## 5. Acceptance Tests

Minimum tests:

- Python binding smoke covers any new capability/profile/budget/fidelity DTO or
  helper;
- facade test proves baseline profile/budget evidence is queryable;
- facade or binding test proves unsupported exact GPU, resident-state, shadow,
  and multi-fidelity/adaptive requests reject with stable reasons;
- existing GPU helper tests still show helper/probe availability does not
  promote support;
- architecture layering test still passes.

Suggested commands:

```bash
git diff --check
cmake --build build-workshop -j4
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/facade/test_runtime_facade.py
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/bindings/test_bindings_policy_surface.py
CMO_BUILD_DIR=build-workshop pytest -q tests/test_gpu_runtime_bindings.py tests/architecture/test_runtime_facade_layering.py
```

## 6. Handoff Contract

Return:

- facade and binding files touched;
- exposed DTOs, fields, and helper names;
- proof tests added or updated;
- exact commands run and outcomes;
- blockers for acceptance closure;
- residuals for unbound helpers or intentionally deferred runtime wiring.
