# WP11-E Integration And Acceptance Handoff

Status: `2026-05-20` planned WP11 dispatch sheet.

Language:

- English canonical: `wp11_integration_acceptance_cluster_20260520.md`
- Chinese companion:
  [wp11_integration_acceptance_cluster_20260520.zh.md](wp11_integration_acceptance_cluster_20260520.zh.md)

Inputs:

- [WP11 facade vertical slice and provenance](facade_vertical_slice_provenance_wp11_20260520.md)
- [WP11-A ActionHoldPolicy contract](wp11_action_hold_policy_cluster_20260520.md)
- [WP11-B information provenance labels](wp11_information_provenance_labels_cluster_20260520.md)
- [WP11-C facade vertical slice proof](wp11_facade_vertical_slice_proof_cluster_20260520.md)
- [WP11-D consumer boundary pre-gates](wp11_consumer_boundary_pregates_cluster_20260520.md)
- [WP closure lane policy](../../../standards/governance/wp_closure_lane_policy.md)

## 1. Purpose

`WP11-E` is the serial integration and acceptance-handoff stream. It reconciles
shared glue after implementation streams reach `Mergeable`, records residuals,
and prepares acceptance evidence without turning README/archive/bilingual chores
into the main implementation bottleneck.

## 2. Scope

In scope:

- verify that A-D evidence references the same WP10 node ids, barrier ids,
  provenance labels, and consumer surfaces;
- run and record focused validation commands;
- create or prepare the WP11 acceptance review;
- run the WP closure audit and hand off non-blocking closure chores;
- list residuals for Law 14, Agency Graph, backend/fidelity, and cadence work.

Out of scope:

- implementing new runtime semantics after A-D close;
- claiming full Law 14 enforcement;
- claiming maintained multi-rate cadence;
- blocking code/test mergeability on optional archive or bilingual polish.

## 3. Integration Checklist

| Check | Required result |
|-------|-----------------|
| Contract consistency | `ActionHoldPolicy` is typed and binding-visible if bindings are touched. |
| Provenance consistency | Maintained facade packets and beliefs use the same label vocabulary. |
| WP10 seam consistency | Vertical proof references accepted WP10 node ids and barrier ids. |
| Consumer boundary | Maintained consumers avoid unlabeled truth/raw-ECS inputs in focused fixtures. |
| Residual register | Full cadence, Law 14, Agency Graph, backend/fidelity, and counterfactual work remain named later work. |
| Closure lane | README/index/archive/bilingual chores are routed to closure lane unless they expose broken links or contradictory status. |

## 4. Acceptance Review Skeleton

The final acceptance review should contain:

- gate-by-gate verdicts for `WP11-A` through `WP11-E`;
- exact changed runtime/test/docs paths;
- exact validation commands and outcomes;
- blockers with exact command and next environment;
- residuals mapped to later phases;
- closure-lane checklist and owner.

## 5. Validation Commands

Minimum final check set:

```bash
git diff --check
cmake --build build-workshop -j4
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/bindings tests/runtime/facade tests/runtime/engagement
CMO_BUILD_DIR=build-workshop pytest -q tests/architecture
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP11
```

The integrator may narrow or expand the test set based on actual files touched,
but the acceptance review must explain the choice.

## 6. Handoff Contract

Return:

- final integrated file list;
- validation commands and outcomes;
- acceptance review path if created;
- unresolved blockers;
- residuals for later phases;
- closure-lane warnings that should not block implementation mergeability.
