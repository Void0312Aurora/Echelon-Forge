# WP10-E Integration And Acceptance Handoff

Status: `2026-05-20` planned WP10 dispatch sheet.

Language:

- English canonical: `wp10_integration_acceptance_cluster_20260520.md`
- Chinese companion:
  [wp10_integration_acceptance_cluster_20260520.zh.md](wp10_integration_acceptance_cluster_20260520.zh.md)

Inputs:

- [WP10 causal runtime foundation](causal_runtime_foundation_wp10_20260520.md)
- [WP10-A manifest registry](wp10_manifest_registry_cluster_20260520.md)
- [WP10-B window loop and injection](wp10_window_loop_injection_cluster_20260520.md)
- [WP10-C same-window validation](wp10_same_window_validation_cluster_20260520.md)
- [WP10-D event and snapshot evidence](wp10_event_snapshot_evidence_cluster_20260520.md)
- [WP closure lane policy](../../../standards/governance/wp_closure_lane_policy.md)

## 1. Purpose

`WP10-E` is the serial integration and acceptance-handoff stream. It reconciles
shared glue after implementation streams reach `Mergeable`, records residuals,
and prepares acceptance evidence without turning README/archive/bilingual chores
into the main implementation bottleneck.

## 2. Scope

In scope:

- integrate shared files touched by A-D;
- verify that A-D evidence refers to the same node ids, barrier ids, event ids,
  and snapshot metadata;
- run and record focused validation commands;
- create or prepare the WP10 acceptance review;
- run the WP closure audit and hand off non-blocking closure chores;
- list residuals for Phase 2 and later phases.

Out of scope:

- implementing new runtime semantics after A-D close;
- reopening Phase 2 `ActionHoldPolicy` or provenance-label work;
- claiming accepted status before the review packet exists;
- blocking code/test mergeability on optional archive or bilingual polish.

## 3. Integration Checklist

| Check | Required result |
|-------|-----------------|
| Registry consistency | All runtime evidence references node ids from `WP10-A`. |
| Barrier consistency | Loop, tests, and facade evidence use the same barrier vocabulary. |
| Edge validation | Same-window validation runs before the selected schedule executes. |
| Event evidence | Event order does not depend on insertion order or wall-clock time. |
| Facade/binding proof | At least one consumer-visible path proves or explicitly blocks metadata visibility. |
| Residual register | Strict clock-domain enforcement, `ActionHoldPolicy`, provenance labels, Law 14, and Agency Graph runtime remain named later work. |
| Closure lane | README/index/archive/bilingual chores are routed to closure lane unless they expose broken links or contradictory status. |

## 4. Acceptance Review Skeleton

The final acceptance review should contain:

- gate-by-gate verdicts for `WP10-A` through `WP10-E`;
- exact changed runtime/test/docs paths;
- exact validation commands and outcomes;
- blockers with exact command and next environment;
- residuals mapped to Phase 2 or later phases;
- closure-lane checklist and owner.

## 5. Validation Commands

Minimum final check set:

```bash
git diff --check
pytest -q tests/architecture/runtime_facade/test_layering.py tests/architecture/governance/test_infrastructure_closure_docs.py
pytest -q tests/runtime/engagement tests/runtime/facade tests/runtime/bindings
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP10
```

The integrator may narrow or expand the test set based on actual files touched,
but the acceptance review must explain the choice.

## 6. Handoff Contract

Return:

- final integrated file list;
- validation commands and outcomes;
- acceptance review path if created;
- unresolved blockers;
- residuals for Phase 2 and later phases;
- closure-lane warnings that should not block implementation mergeability.
