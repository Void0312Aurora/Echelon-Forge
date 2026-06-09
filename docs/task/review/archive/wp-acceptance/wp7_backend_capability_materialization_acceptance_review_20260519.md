# WP7 Backend Capability Materialization Acceptance Review

Status: `2026-05-19` accepted for documentation and implementation preparation.

Language:

- English canonical: `wp7_backend_capability_materialization_acceptance_review_20260519.md`
- Chinese companion:
  [wp7_backend_capability_materialization_acceptance_review_20260519.zh.md](wp7_backend_capability_materialization_acceptance_review_20260519.zh.md)

Reviewed inputs:

- [WP7 backend capability materialization](../simulation_architecture/backend_capability_materialization_wp7_20260519.md)
- [WP7-A registry materialization notes](../simulation_architecture/wp7_registry_materialization_notes_20260519.md)
- [WP7-B runtime capability projection notes](../simulation_architecture/wp7_runtime_capability_projection_notes_20260519.md)
- [WP7-C promotion evidence gates notes](../simulation_architecture/wp7_promotion_evidence_gates_notes_20260519.md)
- [WP7-D multi-fidelity entry conditions notes](../simulation_architecture/wp7_multifidelity_entry_conditions_notes_20260519.md)
- [WP7-E integration and index sync cluster](../simulation_architecture/wp7_integration_and_index_sync_cluster_20260519.md)

## 1. Review Decision

WP7 Backend Capability Materialization is accepted as a documentation and
implementation-preparation line.

This acceptance does not promote any backend capability. Current maintained
support remains:

```yaml
supports_gpu_visual: false
supports_gpu_observation: false
supports_gpu_flight_shaping: false
supports_device_observation_view: false
supports_resident_state: false
supports_exact_gpu_backend: false
supports_shadow_compare: false
```

The only accepted maintained baseline remains `cpu_exact.reference`, with
existing facade/runtime surfaces such as batch runtime, compiled episode
controller, and compiled execution step still treated separately from GPU,
resident-state, shadow, or multi-fidelity support claims.

## 2. Accepted Outputs

WP7-A is accepted as the registry materialization plan. It chooses a
hand-maintained YAML seed subordinate to WP6 policy, with schema checks,
source-document provenance, explicit `maintained_status`,
`projection_eligibility`, and drift detection. The seed file and doc tests are
not created by this acceptance.

WP7-B is accepted as the runtime capability projection plan.
`RuntimeCapabilities` must project maintained support from
`maintained_status`, `projection_eligibility`, profile `validation_gate`, and
budget `acceptance_gate`. Deployment facts may explain diagnostics or
availability, but cannot promote support.

WP7-C is accepted as the promotion evidence gate plan. Exact GPU,
resident-state, and shadow candidates remain false until a future promotion
packet accepts profile registry revision, parity budget revision,
ownership/sync policy, event/snapshot evidence, mismatch/quarantine policy,
replay evidence, facade/core layering evidence, WP5 mapping, and capability
projection update together.

WP7-D is accepted as the multi-fidelity entry-condition plan. Fidelity profile
labels are requests, not support claims. If a request cannot bind to maintained
backend metadata, budget, model-family scope, validation gate, and
facade-visible evidence, it must be rejected, routed to the maintained
baseline, or reported as diagnostics-only according to mismatch policy.

WP7-E is accepted as the publication handoff. Indexes now point to the WP7
materialization line and this review, while preserving the rule that WP7 does
not itself upgrade exact GPU, resident-state, shadow, device observation, or
multi-fidelity support.

## 3. Deferred Implementation Work

The following work remains deferred and is not implied by this acceptance:

1. Add the hand-maintained WP7 registry seed file.
2. Add doc/schema tests for registry fields, provenance, parity-budget pairing,
   projection eligibility, and drift detection.
3. Implement the runtime projection adapter that consumes normalized registry
   metadata instead of markdown tables or deployment probes.
4. Add promotion-specific review packets, registry revisions, parity budget
   revisions, evidence artifacts, and tests for any exact GPU, resident-state,
   shadow, device observation, or multi-fidelity claim.
5. Implement any adaptive fidelity scheduling, ModelProvider binding, or
   approximate/tolerance budget only after the WP7-D entry gates are satisfied.

## 4. Validation

Required validation for the WP7-E closeout:

```bash
git diff --check
rg -n "WP7|backend capability materialization|acceptance review|RuntimeCapabilities|maintained_status|projection_eligibility|multi-fidelity|promotion gate" docs/task/simulation_architecture docs/plan/architecture docs/task/review
python -m pytest tests/runtime/facade/test_runtime_facade.py tests/test_gpu_runtime_bindings.py tests/architecture/runtime_facade/test_layering.py -q
```

Review expectation: the pytest targets should continue to prove that current
facade projection and GPU helper bindings do not promote unsupported backend
capabilities.

## 5. Residual Risk

The main risk is future implementation drift: a helper, probe, request label,
or deployment fact could be mistaken for support. WP7 mitigates this by making
registry metadata, projection eligibility, promotion gates, and acceptance
review the only route to maintained backend capability support.
