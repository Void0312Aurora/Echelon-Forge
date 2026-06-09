# WP13-A Runtime Capability Query And Rejection Surface

Status: `2026-05-21` complete / accepted.

Language:

- English canonical: `wp13_runtime_capability_query_cluster_20260520.md`
- Chinese companion:
  [wp13_runtime_capability_query_cluster_20260520.zh.md](wp13_runtime_capability_query_cluster_20260520.zh.md)

Inputs:

- [WP13 backend fidelity expansion](backend_fidelity_expansion_wp13_20260520.md)
- [WP7 runtime capability projection](../wp7_backend_capability_materialization/wp7_runtime_capability_projection_cluster_20260519.md)
- [WP6 backend profile registry](../wp6_backend_profile_policy/wp6_backend_profile_registry_20260519.md)
- [WP6 resident-state boundary rules](../wp6_backend_profile_policy/wp6_resident_state_boundary_rules_20260519.md)
- Current `src/runtime/facade/runtime_facade_types.h`
- Current `src/runtime/facade/runtime_facade.cpp`
- Current `src/interfaces/python/bindings_runtime.cpp`
- Current `tests/runtime/facade/test_runtime_facade.py`
- Current `tests/test_gpu_runtime_bindings.py`
- Current `tests/architecture/runtime_facade/test_layering.py`

## 1. Purpose

`WP13-A` makes capability answers inspectable without making new capability
claims. A caller should be able to ask what backend/fidelity capability is
maintained, which profile or budget supports it, and why unsupported claims are
rejected.

The first accepted result should still keep:

```yaml
supports_device_observation_view: false
supports_resident_state: false
supports_exact_gpu_backend: false
supports_shadow_compare: false
```

The change is query/rejection evidence, not support promotion.

## 2. Scope

In scope:

- add conservative query metadata next to or inside `RuntimeCapabilities`;
- expose maintained baseline profile and budget references where available;
- expose unsupported/rejected reasons for exact GPU, resident-state, device
  observation, shadow, and multi-fidelity claims;
- keep GPU helper/probe availability as deployment fact or diagnostics only;
- update Python binding/tests for any new fields or helper DTOs.

Out of scope:

- changing unsupported support booleans to true;
- backend selection;
- adaptive fidelity scheduling;
- direct GPU helper/probe calls from facade/core capability projection;
- profile registry row ownership, unless coordinating a tiny shared DTO name
  with `WP13-B`.

## 3. Candidate Implementation Seams

Inspect before editing:

- `src/runtime/facade/runtime_facade_types.h`
- `src/runtime/facade/runtime_facade.cpp`
- `src/interfaces/python/bindings_runtime.cpp`
- `tests/runtime/facade/test_runtime_facade.py`
- `tests/test_gpu_runtime_bindings.py`
- `tests/architecture/runtime_facade/test_layering.py`

Preferred approach:

- keep existing boolean support fields stable for compatibility;
- add explicit metadata fields such as `maintained_backend_profile_id`,
  `maintained_parity_budget_ref`, or `*_rejection_reason` only when tests prove
  their default values;
- keep rejection reasons stable string constants or enum-like values suitable
  for Python tests;
- keep facade/core independent from `src/gpu` helper or probe implementation.

## 4. Gate Rules

| Boundary | Required behavior |
|----------|-------------------|
| Conservative support | Existing unsupported backend/fidelity booleans remain false. |
| Queryability | Maintained baseline and unsupported reason metadata are visible through maintained facade/binding surfaces. |
| Probe separation | GPU helper/probe bindings may exist, but they cannot influence maintained support claims. |
| Rejection evidence | Unsupported exact GPU, resident-state, shadow, device-observation, and multi-fidelity claims produce stable reasons. |

## 5. Acceptance Tests

Minimum tests:

- `RuntimeFacade.capabilities()` exposes any new metadata fields with stable
  conservative defaults;
- Python bindings expose the same fields or helper DTOs;
- GPU helper/probe binding availability does not flip exact GPU, resident-state,
  device-observation, or shadow support;
- architecture layering test still rejects facade/core dependency on GPU helper
  implementation;
- unsupported reason values cite missing maintained profile, missing budget, or
  blocked candidate status rather than generic failure.

Suggested commands:

```bash
git diff --check
cmake --build build-workshop -j4
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/facade/test_runtime_facade.py tests/test_gpu_runtime_bindings.py
CMO_BUILD_DIR=build-workshop pytest -q tests/architecture/runtime_facade/test_layering.py
```

## 6. Handoff Contract

Return:

- DTO/projection files touched;
- new capability metadata fields or helper names;
- rejection reason vocabulary;
- tests added or updated;
- exact commands run and outcomes;
- blockers and residuals for `WP13-E`;
- integration notes for `WP13-B` / `WP13-C` if shared struct names changed.
