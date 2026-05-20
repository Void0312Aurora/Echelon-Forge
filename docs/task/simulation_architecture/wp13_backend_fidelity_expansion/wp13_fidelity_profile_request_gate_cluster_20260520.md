# WP13-D Fidelity Profile Request Gate

Status: `2026-05-21` complete / accepted.

Language:

- English canonical: `wp13_fidelity_profile_request_gate_cluster_20260520.md`
- Chinese companion:
  [wp13_fidelity_profile_request_gate_cluster_20260520.zh.md](wp13_fidelity_profile_request_gate_cluster_20260520.zh.md)

Inputs:

- [WP13 backend fidelity expansion](backend_fidelity_expansion_wp13_20260520.md)
- [WP13-B backend profile registry gate](wp13_backend_profile_registry_gate_cluster_20260520.md)
- [WP13-C parity budget evidence gate](wp13_parity_budget_evidence_gate_cluster_20260520.md)
- [WP7 multi-fidelity entry conditions](../wp7_backend_capability_materialization/wp7_multifidelity_entry_conditions_cluster_20260519.md)
- [WP8 SCAL learning face](../wp8_learning_face/learning_face_wp8_20260520.md)
- [WP10 causal runtime foundation](../wp10_causal_runtime_foundation/causal_runtime_foundation_wp10_20260520.md)
- [WP11 facade vertical slice and provenance](../wp11_facade_vertical_slice_provenance/facade_vertical_slice_provenance_wp11_20260520.md)

## 1. Purpose

`WP13-D` makes fidelity profiles admissible as requests, not as support claims.
A fidelity label such as `fast_training` or `sensor_heavy` should be accepted
only when it binds a maintained backend profile, accepted parity or tolerance
budget, model-family scope, validation gate, and facade-visible evidence.

The first implementation should support a maintained baseline request, for
example `exact_evaluation` on `cpu_exact.reference`, and reject unsupported
multi-fidelity, adaptive, approximate, resident-state, or learned-provider
requests with stable reasons.

## 2. Scope

In scope:

- define a fidelity profile request DTO/helper or admission function;
- support request labels from WP7-D as labels only;
- require backend profile id, budget ref, model-family scope, validation gate,
  and evidence fields;
- accept a conservative CPU exact baseline request when B/C gates pass;
- reject unsupported `fast_training`, `sensor_heavy`, adaptive scheduling,
  learned provider, exact GPU, resident-state, and shadow-backed claims unless
  their gates are present.

Out of scope:

- adaptive fidelity scheduling;
- backend selection;
- learned `ModelProvider` runtime interface;
- approximate execution;
- changing runtime capability support booleans to true.

## 3. Candidate Implementation Seams

Inspect before editing:

- `src/runtime/contracts/runtime_dto_contracts.h`
- `src/runtime/contracts/world_batch_contracts.h`
- `src/runtime/contracts/policy_contracts.h`
- any new backend profile or parity budget helper from `WP13-B` / `WP13-C`
- `src/interfaces/python/bindings_runtime.cpp`
- `tests/runtime/bindings/test_bindings_runtime_dto_surface.py`
- `tests/runtime/facade/test_runtime_facade.py`

Preferred approach:

- keep fidelity request admission as a pure validator/helper in the first
  slice;
- avoid wiring it into execution dispatch until a later WP explicitly owns
  scheduling or backend selection;
- preserve request/evidence fields that `WP13-E` can expose through bindings;
- use stable rejection reasons such as `fidelity_profile_requires_maintained_backend_profile`,
  `fidelity_profile_requires_accepted_budget`, and
  `adaptive_fidelity_scheduling_not_implemented`.

## 4. Gate Rules

| Boundary | Required behavior |
|----------|-------------------|
| Request label | A label is descriptive and never implies support by itself. |
| Backend binding | Accepted requests must cite a maintained backend profile. |
| Budget binding | Accepted requests must cite an accepted parity or tolerance budget. |
| Model scope | Request must name lifecycle stages or model families it covers. |
| Evidence | Request must carry facade-visible evidence ids or required evidence fields. |
| Unsupported paths | Adaptive, learned, approximate, exact GPU, resident-state, and shadow-backed requests fail closed. |

## 5. Acceptance Tests

Minimum tests:

- baseline `exact_evaluation` request using `cpu_exact.reference` and
  `parity_budget.cpu_exact.reference.v1` passes admission;
- missing backend profile id rejects;
- missing or non-accepted budget rejects;
- `fast_training` and `sensor_heavy` do not imply maintained multi-fidelity
  support without accepted gates;
- adaptive scheduling and learned provider requests reject with stable reasons;
- exact GPU, resident-state, and shadow-backed fidelity requests reject until
  B/C gates report maintained evidence.

Suggested commands:

```bash
git diff --check
cmake --build build-workshop -j4
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py tests/runtime/facade/test_runtime_facade.py
```

## 6. Handoff Contract

Return:

- request DTO/helper files touched;
- fidelity labels and admission helper names;
- accepted baseline request fixture;
- rejection reason vocabulary;
- tests added or updated;
- exact commands run and outcomes;
- blockers for `WP13-E` binding/facade proof;
- residuals for later adaptive fidelity or `ModelProvider` work.
