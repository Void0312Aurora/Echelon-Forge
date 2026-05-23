# WP7-E Dispatch Sheet: Integration And Index Sync

Status: `2026-05-19` accepted serial WP7 publication handoff.

Language:

- English canonical: `wp7_integration_and_index_sync_cluster_20260519.md`
- Chinese companion:
  [wp7_integration_and_index_sync_cluster_20260519.zh.md](wp7_integration_and_index_sync_cluster_20260519.zh.md)

Inputs:

- [WP7 backend capability materialization](backend_capability_materialization_wp7_20260519.md)
- [WP7-A registry materialization](wp7_registry_materialization_cluster_20260519.md)
- [WP7-B runtime capability projection](wp7_runtime_capability_projection_cluster_20260519.md)
- [WP7-C promotion evidence gates](wp7_promotion_evidence_gates_cluster_20260519.md)
- [WP7-D multi-fidelity entry conditions](wp7_multifidelity_entry_conditions_cluster_20260519.md)

## 1. Purpose

WP7-E is the serial publication pass. It should run after WP7-A through WP7-D
are stable enough to reference. Its job is to publish one coherent WP7 line and
prevent older `WP7` naming from reopening the already accepted WP6 policy line.

## 2. Required Work Items

| Stream | Required output | Write scope | Budget |
|--------|-----------------|-------------|--------|
| `WP7-E1 Task README Sync` | Add WP7 outputs and workstream map to the simulation architecture README pair. | `docs/task/simulation_architecture/README*.md`. | Medium. |
| `WP7-E2 Architecture Relation Sync` | Add WP7 relation notes to architecture README and strict architecture baseline. | `docs/plan/architecture/README*.md`, architecture design pair. | Medium. |
| `WP7-E3 Review Index Sync` | Add future WP7 acceptance review links only after review files exist; otherwise record pending review scope in WP7 docs. | `docs/task/review/README*.md` or deferred note. | Medium. |
| `WP7-E4 Final Handoff` | Record final validation commands, reviewed outputs, and deferred follow-up. | WP7 handoff or acceptance review. | Medium-high. |

## 3. Publication Rules

1. The WP7 task line starts after accepted WP6 policy.
2. `WP6` remains the name for backend profile policy.
3. `WP7` is the name for backend capability materialization and multi-fidelity
   entry conditions.
4. Indexes should cite stable WP7 documents, not draft fragments.
5. Review indexes should not link acceptance reviews before those files exist.

## 4. Non-Goals

- Do not rewrite WP6 accepted outputs.
- Do not create acceptance-review files before A-D evidence exists.
- Do not mark WP7 complete during initial document creation.
- Do not promote candidate capabilities in publication prose.

## 5. Acceptance Gates

This cluster is accepted when:

1. Task README files list WP7 and link all stable WP7 cluster docs.
2. Architecture README and baseline relation sections identify WP7 as the
   post-WP6 materialization line.
3. No active doc treats old pre-WP6 `WP7` naming as the current policy line.
4. Review index state matches actual review files.
5. Final validation commands are recorded.

## 6. Validation Commands

```bash
git diff --check
rg -n "WP7|backend_capability_materialization_wp7|wp7_registry_materialization|wp7_runtime_capability_projection|wp7_promotion_evidence|wp7_multifidelity|wp7_integration" docs/task/simulation_architecture docs/plan/architecture docs/task/review
```

## 7. Publication Handoff Result

WP7-E completed the serial publication pass after WP7-A through WP7-D produced
stable implementation-preparation notes. The published WP7 line is now accepted
as documentation and implementation readiness, not as capability promotion.

Accepted outputs:

- [WP7-A registry materialization notes](wp7_registry_materialization_notes_20260519.md):
  hand-maintained YAML seed shape, schema/provenance requirements,
  `maintained_status`, `projection_eligibility`, and drift detection plan.
- [WP7-B runtime capability projection notes](wp7_runtime_capability_projection_notes_20260519.md):
  `RuntimeCapabilities` projection from maintained metadata, with deployment
  facts kept diagnostics/availability-only.
- [WP7-C promotion evidence gates notes](wp7_promotion_evidence_gates_notes_20260519.md):
  exact GPU, resident-state, and shadow promotion gates mapped to WP5 evidence
  tiers and acceptance review.
- [WP7-D multi-fidelity entry conditions notes](wp7_multifidelity_entry_conditions_notes_20260519.md):
  fidelity profile requests and entry gates, with request labels not treated as
  support claims.
- [WP7 backend capability materialization acceptance review](../review/wp7_backend_capability_materialization_acceptance_review_20260519.md):
  accepts the WP7 documentation/implementation-prep line and keeps current
  exact GPU, resident-state, shadow, device observation, and multi-fidelity
  support false.

Indexes updated:

- Simulation architecture README pair now lists WP7 as complete/accepted and
  links A-D clusters, A-D notes, WP7-E, and the acceptance review.
- Architecture README pair and strict architecture baseline pair now identify
  WP7 as the post-WP6 materialization plan and link the acceptance review.
- Review README pair now lists the WP7 acceptance review.

Deferred follow-up:

1. Add the hand-maintained WP7 registry seed.
2. Add doc/schema tests for seed fields, provenance, pairing, projection
   eligibility, and drift detection.
3. Implement the runtime projection adapter from normalized registry metadata.
4. Run future promotion packets before any exact GPU, resident-state, shadow,
   device observation, or multi-fidelity support field can become true.

Final validation commands for this handoff:

```bash
git diff --check
rg -n "WP7|backend capability materialization|acceptance review|RuntimeCapabilities|maintained_status|projection_eligibility|multi-fidelity|promotion gate" docs/task/simulation_architecture docs/plan/architecture docs/task/review
python -m pytest tests/runtime/facade/test_runtime_facade.py tests/test_gpu_runtime_bindings.py tests/architecture/test_runtime_facade_layering.py -q
```
