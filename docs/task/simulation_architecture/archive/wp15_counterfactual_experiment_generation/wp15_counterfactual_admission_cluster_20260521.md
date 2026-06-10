# WP15-C Counterfactual Request Admission

Status: `2026-05-21` mergeable / first slice complete.

Language:

- English canonical: `wp15_counterfactual_admission_cluster_20260521.md`
- Chinese companion:
  [wp15_counterfactual_admission_cluster_20260521.zh.md](wp15_counterfactual_admission_cluster_20260521.zh.md)

Inputs:

- [WP15 counterfactual experiment generation](counterfactual_experiment_generation_wp15_20260521.md)
- [WP15-A replay envelope and branch point](wp15_replay_envelope_branch_point_cluster_20260521.md)
- [WP15-B worldline branch metadata](wp15_worldline_branch_metadata_gate_cluster_20260521.md)
- [WP12 information and agency enforcement](../wp12_information_agency_enforcement/information_agency_enforcement_wp12_20260520.md)
- [WP13 backend fidelity expansion](../wp13_backend_fidelity_expansion/backend_fidelity_expansion_wp13_20260520.md)
- [WP14 capability composition](../wp14_capability_composition/capability_composition_wp14_20260521.md)

## 1. Purpose

`WP15-C` turns replay and worldline metadata into a fail-closed admission gate
for counterfactual experiment requests. A request may be accepted as metadata,
rejected, or blocked by unsupported restore/runtime capability, but it must not
silently mutate authoritative simulation state.

## 2. Scope

In scope:

- `CounterfactualExperimentRequest` and admission result vocabulary;
- baseline worldline, branch point, replay envelope, intervention kind, source,
  authority, backend/fidelity, capability, and evidence refs;
- stable allowed intervention/source labels;
- fail-closed rejection reasons for missing ancestry, unsupported intervention,
  missing authority, unsupported backend/fidelity/capability refs, and raw state
  mutation;
- facade/binding proof if a public runtime surface is added.

Out of scope:

- executing a counterfactual branch;
- broad experiment orchestration;
- public generator runtime;
- promoting capability or backend support from experiment results.

## 3. Candidate Implementation Seams

Inspect before editing:

- output from `WP15-A` and `WP15-B`;
- `src/runtime/contracts/backend_profile_contracts.h`;
- `src/runtime/contracts/fidelity_profile_contracts.h`;
- `src/runtime/contracts/platform_capability_contracts.h`;
- `src/runtime/facade/runtime_facade_types.h`;
- `src/interfaces/python/bindings_runtime.cpp` if bindings are exposed.

Preferred approach:

- keep admission in contract/helpers first;
- expose through facade/bindings only if the DTO can be proven additive and
  fail-closed;
- require explicit evidence refs rather than inferring support from profiles or
  capabilities;
- keep unsupported restore visible in the admission result.

## 4. Gate Rules

| Boundary | Required behavior |
|----------|-------------------|
| Ancestry required | Request must reference replay envelope, branch point, and worldline metadata. |
| Authority required | Request must name a source and authority/provenance evidence consistent with WP12. |
| Backend/capability guarded | Backend/fidelity/capability refs are evidence constraints, not support promotion. |
| Raw mutation rejected | Requests that ask for raw authoritative state mutation fail closed. |

## 5. Acceptance Tests

Minimum tests:

- valid admission fixture accepts metadata-only counterfactual request;
- missing replay envelope, branch point, worldline id, intervention, source,
  authority, or evidence refs rejects with stable reasons;
- unsupported restore blocks executable branch claims while preserving
  diagnostics;
- raw state mutation request is rejected.

Suggested commands:

```bash
git diff --check
python -m pytest -q tests/architecture/causal_runtime/test_counterfactual_admission.py
python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "counterfactual or replay or experiment"
```

## 6. Handoff Contract

Return:

- admission files touched;
- request/result field names;
- rejection reason vocabulary;
- tests added or updated;
- exact commands run and outcomes;
- blockers for `WP15-E`.
