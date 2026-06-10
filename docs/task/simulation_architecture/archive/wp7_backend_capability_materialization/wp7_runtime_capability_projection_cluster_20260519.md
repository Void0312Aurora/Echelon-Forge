# WP7-B Runtime Capability Projection

Status: `2026-05-19` implementation-ready WP7 second-wave preparation.

Language:

- English canonical: `wp7_runtime_capability_projection_cluster_20260519.md`
- Chinese companion:
  [wp7_runtime_capability_projection_cluster_20260519.zh.md](wp7_runtime_capability_projection_cluster_20260519.zh.md)
- Implementation notes:
  [wp7_runtime_capability_projection_notes_20260519.md](wp7_runtime_capability_projection_notes_20260519.md)

Inputs:

- [WP7 backend capability materialization](backend_capability_materialization_wp7_20260519.md)
- [WP7-A registry materialization](wp7_registry_materialization_cluster_20260519.md)
- [WP7-A registry materialization notes](wp7_registry_materialization_notes_20260519.md)
- [WP6-C1 resident-state boundary rules](wp6_resident_state_boundary_rules_20260519.md)
- Current `src/runtime/facade/runtime_facade_types.h`
- Current `tests/runtime/facade/test_runtime_facade.py`
- Current `tests/test_gpu_runtime_bindings.py`
- Current `tests/architecture/runtime_facade`

## 1. Purpose

WP7-B defines the implementation route for making `RuntimeCapabilities` a
projection of declared backend profile metadata plus probeable deployment
facts. It must preserve the WP6 rule that GPU helper/probe availability cannot
promote exact GPU, resident-state, device observation, or shadow support.

This is the new post-WP6 `WP7-B` line. It must not reuse the older historical
alias where `WP7` meant backend profile policy; that policy is closed as `WP6`.

The implementation notes are the normative handoff for the second wave. They
define the current projection matrix, the deployment facts separation rule, and
the layering guard that keeps facade/core independent from GPU helper or probe
implementation details.

## 2. Required Work Items

| Stream | Required output | Write scope | Budget |
|--------|-----------------|-------------|--------|
| `WP7-B1 Projection Source Boundary` | Document or implement where registry metadata enters the runtime facade projection path. | runtime/facade docs, optional C++ projection helper. | High. |
| `WP7-B2 Deployment Fact Separation` | Keep GPU helper/probe data separate from maintained capability claims. | tests and docs; avoid facade/core GPU linkage. | High. |
| `WP7-B3 Capability Default Guard` | Preserve current false defaults for exact GPU, device observation, resident-state, and shadow support. | `tests/runtime/facade/`, `tests/test_gpu_runtime_bindings.py`. | Medium-high. |
| `WP7-B4 Layering Guard` | Ensure facade/core does not call or link GPU helper/probe implementation for capability projection. | `tests/architecture/runtime_facade`. | Medium-high. |

## 3. Projection Rules

The runtime projection path must obey:

1. Maintained capability claims require a maintained profile row.
   Projection must first consume `maintained_status` and
   `projection_eligibility` from the WP7-A materialized registry shape.
2. Deployment facts may explain availability or unavailability, but they cannot
   override profile class, parity budget, sync policy, or validation gate.
3. Diagnostics-only rows may project report-only affordances, not maintained
   truth.
4. Candidate rows project false support until promotion evidence passes.
5. The facade/core layer must not depend on GPU helper or probe implementation
   details because `ef_gpu_experiments` already depends on `ef_core`.

The planned projection adapter may combine registry metadata with deployment
facts only after the registry gate has produced conservative capability truth.
GPU helper/probe binding presence is a deployment fact, not promotion evidence.

## 4. Current Required Projection

The current maintained projection remains:

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

These values are current required support claims, not a prediction about future
promotion. They stay false until a future maintained profile revision and gate
explicitly update `maintained_status`, `projection_eligibility`,
`validation_gate`, and the paired parity budget `acceptance_gate`.

## 5. Implementation Notes Handoff

See
[wp7_runtime_capability_projection_notes_20260519.md](wp7_runtime_capability_projection_notes_20260519.md)
for the implementation-ready contract. The notes require the runtime projection
to:

1. Use `maintained_status` plus `projection_eligibility` as the capability
   source boundary.
2. Layer deployment facts on top only as availability or diagnostics
   explanation.
3. Keep GPU helper/probe bindings report-only for current support claims.
4. Preserve facade/core layering by avoiding any dependency on GPU helper
   implementation symbols.
5. Add only narrow guards if tests change, and avoid failing because the future
   hand-maintained YAML seed is not present yet.

## 6. Non-Goals

- Do not enable exact GPU, resident-state, device observation, or shadow support.
- Do not add backend selection.
- Do not make `RuntimeCapabilities` the source of truth.
- Do not link facade/core against GPU helper code.
- Do not remove diagnostics helper bindings.

## 7. Acceptance Gates

This cluster is accepted when:

1. Projection can be explained from registry metadata plus deployment facts.
2. Current false capability claims remain false in tests.
3. GPU helper/probe bindings can exist without promoting maintained support.
4. Facade/core layering tests prevent GPU helper dependency inversion.
5. Any new projection fields cite their registry source and validation gate.
6. English and Chinese WP7-B cluster and notes documents are reciprocally
   linked and structurally aligned.

## 8. Validation Commands

```bash
git diff --check
rg -n "RuntimeCapabilities|maintained_status|projection_eligibility|deployment facts|supports_exact_gpu_backend|supports_resident_state|supports_shadow_compare|GPU helper|probe" docs/task/simulation_architecture/wp7_runtime_capability_projection*20260519*.md
```

If tests change, run the narrow affected pytest targets. If tests do not
change, the existing guards remain the planned coverage:
`tests/runtime/facade/test_runtime_facade.py`,
`tests/test_gpu_runtime_bindings.py`, and
`tests/architecture/runtime_facade`.
