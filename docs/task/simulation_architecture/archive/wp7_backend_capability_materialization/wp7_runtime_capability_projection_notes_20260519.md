# WP7-B Runtime Capability Projection Implementation Notes

Status: `2026-05-19` implementation-ready notes for the WP7-B second wave.

Language:

- English canonical: `wp7_runtime_capability_projection_notes_20260519.md`
- Chinese companion:
  [wp7_runtime_capability_projection_notes_20260519.zh.md](wp7_runtime_capability_projection_notes_20260519.zh.md)
- Parent cluster:
  [wp7_runtime_capability_projection_cluster_20260519.md](wp7_runtime_capability_projection_cluster_20260519.md)

Inputs:

- [WP7 backend capability materialization](backend_capability_materialization_wp7_20260519.md)
- [WP7-A registry materialization](wp7_registry_materialization_cluster_20260519.md)
- [WP7-A registry materialization notes](wp7_registry_materialization_notes_20260519.md)
- [WP6-A backend profile registry](wp6_backend_profile_registry_20260519.md)
- [WP6-B parity budget registry](wp6_parity_budget_registry_20260519.md)
- [WP6-C1 resident-state boundary rules](wp6_resident_state_boundary_rules_20260519.md)
- Current `src/runtime/facade/runtime_facade_types.h`
- Current `src/runtime/facade/runtime_facade.cpp`
- Current `tests/runtime/facade/test_runtime_facade.py`
- Current `tests/test_gpu_runtime_bindings.py`
- Current `tests/architecture/runtime_facade`

## 1. Projection Thesis

`RuntimeCapabilities` is a projection of accepted backend metadata plus
probeable deployment facts. It is not the source of truth and it must not infer
support from helper code, build flags, imports, device probes, or runtime
experiments.

The projection order is:

1. Read a profile row and its paired parity budget row from the WP7-A
   hand-maintained YAML seed shape once that seed exists.
2. Gate maintained claims on explicit `maintained_status` and
   `projection_eligibility`.
3. Require the profile `validation_gate` and parity budget `acceptance_gate` to
   agree with any maintained claim.
4. Layer deployment facts only after the registry gate, and only as
   availability or diagnostics explanation.

Until the seed lands, tests must use narrow source/document guards or current
runtime expectations. They must not fail merely because the future YAML seed is
not present yet.

## 2. Source Boundary

The future projection adapter should consume normalized registry rows, not
direct WP6 markdown tables. WP7-A defines the first-wave seed vocabulary:
`maintained_status`, `projection_eligibility`, `source_doc_provenance`,
profile `validation_gate`, and parity budget `acceptance_gate`.

The adapter may compute maintained support only from this metadata:

| Input field | Projection use |
|-------------|----------------|
| `maintained_status` | Distinguishes `maintained_exact_baseline`, `diagnostics_only`, and `unmaintained_candidate`. |
| `projection_eligibility.maintained_cpu_exact_baseline` | Allows the CPU exact reference baseline only for `cpu_exact.reference`. |
| `projection_eligibility.exact_gpu_supported` | Controls `supports_exact_gpu_backend`; currently false for all WP6 rows. |
| `projection_eligibility.resident_state_supported` | Controls `supports_resident_state`; currently false for all WP6 rows. |
| `projection_eligibility.shadow_supported` | Controls `supports_shadow_compare`; currently false for all WP6 rows. |
| `projection_eligibility.diagnostics_allowed` | Allows report-only diagnostics surfaces without changing support claims. |
| `validation_gate` and `acceptance_gate` | Must be maintained/accepted before a true maintained support claim can project. |

`RuntimeCapabilities` may mirror the result, but it must not create new
capability truth. If registry metadata is absent or incomplete, the safe output
for candidate or diagnostics-only claims is false support plus diagnostics text.

## 3. Current Required Projection Matrix

The current required `RuntimeCapabilities` support matrix is:

```yaml
supports_batch_runtime: true
supports_compiled_episode_controller: true
supports_compiled_execution_step: true
supports_gpu_visual: false
supports_gpu_observation: false
supports_gpu_flight_shaping: false
supports_device_observation_view: false
supports_resident_state: false
supports_exact_gpu_backend: false
supports_shadow_compare: false
```

The three true values are current facade/runtime surfaces. The seven false
values remain false unless a future maintained profile revision and promotion
gate update the registry, the parity budget, and the projection test contract.

Mapping from current WP6/WP7-A rows:

| Profile row | `maintained_status` | Relevant `projection_eligibility` | Required projection |
|-------------|---------------------|-----------------------------------|---------------------|
| `cpu_exact.reference` | `maintained_exact_baseline` | `maintained_cpu_exact_baseline: true` | May explain the true CPU-backed facade surfaces; does not imply GPU, resident-state, device view, or shadow support. |
| `gpu_helpers.diagnostics_only` | `diagnostics_only` | `diagnostics_allowed: true`; all maintained support booleans false | GPU helper/probe diagnostics may be available, but support fields remain false. |
| `gpu_exact.unmaintained_candidate` | `unmaintained_candidate` | `exact_gpu_supported: false` | `supports_exact_gpu_backend: false`; helper/probe availability cannot promote it. |
| `resident_state.unmaintained_candidate` | `unmaintained_candidate` | `resident_state_supported: false` | `supports_resident_state: false`; unsynced backend-local state stays diagnostics-only. |
| `shadow_compare.unmaintained_candidate` | `unmaintained_candidate` | `shadow_supported: false` | `supports_shadow_compare: false`; shadow reports cannot affect committed state or fallback control flow. |

`supports_gpu_visual`, `supports_gpu_observation`, `supports_gpu_flight_shaping`,
and `supports_device_observation_view` also remain false in the current
maintained projection. Existing GPU helper outputs are deployment facts or
diagnostics exports, not maintained runtime capability claims.

## 4. Deployment Facts Separation

Deployment facts are observations about the current build or machine. Examples
include whether a GPU helper binding exists, whether `probe_gpu_device()` can be
called, whether CUDA runtime support was built, whether a device count is
reported, or whether an experiment produced timing/debug stats.

Deployment facts may explain:

1. why a diagnostics surface is available or unavailable,
2. why a maintained profile with accepted metadata cannot run in a particular
   deployment,
3. which helper/probe produced a report-only artifact,
4. what availability reason should be shown in diagnostics.

Deployment facts may not:

1. change `maintained_status`,
2. change `projection_eligibility`,
3. satisfy `validation_gate` or `acceptance_gate`,
4. promote exact GPU, resident-state, device observation view, or shadow
   compare support,
5. make helper/probe binding presence a substitute for registry metadata.

This separation is why GPU helper/probe binding existence can coexist with
`supports_exact_gpu_backend: false`, `supports_resident_state: false`, and
`supports_shadow_compare: false`.

## 5. Layering Rule

The facade/core projection path must not link to or call GPU helper/probe
implementation. `ef_gpu_experiments` already depends on `ef_core`, so facade or
core depending back on GPU helper code would invert the dependency direction.

Allowed layering:

1. `RuntimeCapabilities` can expose conservative support booleans from facade
   metadata.
2. GPU helper/probe bindings can remain exported diagnostics helpers.
3. Tests can assert that helper/probe bindings exist and still do not promote
   support.
4. Architecture guards can scan facade/core sources for GPU helper markers.

Forbidden layering:

1. `src/runtime/facade` includes GPU helper headers to compute capabilities.
2. `src/core` calls `probe_gpu_device()` or GPU helper stats to project
   maintained support.
3. A deployment probe flips `supports_exact_gpu_backend`,
   `supports_resident_state`, or `supports_shadow_compare`.
4. Device-resident pointers or helper-local buffers become facade/core truth.

## 6. Test Guard Plan

No new pytest is required for this documentation wave because the current test
set already contains narrow guards:

| Existing target | Guard provided |
|-----------------|----------------|
| `tests/runtime/facade/test_runtime_facade.py` | Facade capability expectations keep current false support fields false. |
| `tests/test_gpu_runtime_bindings.py` | GPU helper/probe bindings can exist while support claims remain false. |
| `tests/architecture/runtime_facade` | Facade/core sources must not include or call GPU helper/probe implementation markers. |

If a test is added later, keep it narrow. It should check one of the contracts
above and should skip or use docs-only expectations when the future
hand-maintained YAML seed does not exist. It should not turn the absence of the
seed into a failure before WP7-A lands it.

## 7. Promotion Requirements

Any future change that turns one of the current false support fields true must
land with all of the following:

1. A maintained profile revision with updated `maintained_status`.
2. Updated `projection_eligibility` for the specific support claim.
3. A maintained parity budget with an accepted `acceptance_gate`.
4. A profile `validation_gate` that names the evidence required for the claim.
5. Source provenance back to the accepted registry and review artifacts.
6. A projection test that proves helper/probe availability alone is still
   insufficient.
7. A layering guard that keeps facade/core independent from GPU helper code.

Without those pieces, `RuntimeCapabilities` must keep the support field false
and may only report diagnostics/availability explanation.

## 8. Acceptance Gates

WP7-B is implementation-ready when:

1. Projection source boundary is documented as `maintained_status` plus
   `projection_eligibility`.
2. Deployment facts are explicitly separated from capability claims.
3. Current required projection keeps GPU visual, GPU observation, GPU flight
   shaping, device observation view, resident state, exact GPU backend, and
   shadow compare support false.
4. GPU helper/probe binding presence remains diagnostics/availability evidence
   only.
5. Facade/core layering excludes GPU helper/probe implementation dependencies.
6. Test guidance avoids failing on a future seed file that has not landed yet.
7. English and Chinese notes are reciprocally linked and structurally aligned.

## 9. Validation Commands

```bash
git diff --check
rg -n "RuntimeCapabilities|maintained_status|projection_eligibility|deployment facts|supports_exact_gpu_backend|supports_resident_state|supports_shadow_compare|GPU helper|probe" docs/task/simulation_architecture/wp7_runtime_capability_projection*20260519*.md
```

No pytest is required when only these WP7-B documents change. If tests are
edited later, run the affected narrow targets.
