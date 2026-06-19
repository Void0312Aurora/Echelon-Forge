# MLF-9 Pk Statistical Trends

Status: `2026-06-19` accepted / archived for bounded Pk/statistical trend
projection. This subproject closes the simulation-trend slice after MLF-8
acceptance and before any calibration-gate work.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Parent A2 index: [../../README.md](../../README.md)
- MLF-5 component-failure evidence:
  [../missile_lethality_component_failure/README.md](../missile_lethality_component_failure/README.md)
- MLF-6 structural-failure evidence:
  [../missile_lethality_structural_failure/README.md](../missile_lethality_structural_failure/README.md)
- MLF-7 consequence bridge:
  [../missile_lethality_secondary_consequence_coupling/README.md](../missile_lethality_secondary_consequence_coupling/README.md)
- MLF-8 debris/wreck lifecycle:
  [../missile_lethality_debris_wreck_lifecycle/README.md](../missile_lethality_debris_wreck_lifecycle/README.md)
- Damage consequence reward surface:
  [../../damage_consequence_reward_surface/README.md](../../damage_consequence_reward_surface/README.md)
- Realism authority boundary:
  [../../../../../standards/foundation/realism_authority_boundary.zh.md](../../../../../standards/foundation/realism_authority_boundary.zh.md)

## Purpose

MLF-9 turns the replayable missile-lethality chain into bounded statistical
trend evidence. It should answer questions such as "do closer detonations trend
toward more severe simulated outcomes?" and "do chains with structural breakup
trend toward terminal loss more often than chains without it?".

It must not answer "what is the real AIM-120C probability of kill against a
real F-16 or MQ-9?". Real-world calibration, source admission, weapon-specific
truth, and validation against selected public outcomes remain held for MLF-10 or
later work.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Upstream chain facts | accepted inputs | Archived MLF-5 through MLF-8 evidence surfaces | Inputs are replayable simulation facts, not calibrated real-world data |
| Statistical authority | accepted / archived | This README, inventory, metric contract, trend/report integration results, validation record, acceptance record, and focused diagnostics/tests | No calibrated Pk value is accepted |
| Reward / training surface | retained adjacent work | Damage consequence reward surface remains separate | MLF-9 does not create reward authority or training success claims |
| Calibration | held | MLF-10 is reserved for calibration gates | No stock weapon or target-specific truth |

## Scope

In scope:

- Define the MLF-9 metric contract for replay rows, event joins, outcome
  buckets, trend summaries, and uncertainty fields.
- Build or extend diagnostics/replay tooling only when the contract is explicit.
- Keep outputs as synthetic simulation trend reports unless a later calibration
  gate promotes them.
- Test monotonic and consistency properties on controlled fixtures rather than
  claiming real-world probabilities.
- Record residuals where upstream fields are insufficient for honest trend
  projection.

Out of scope:

- No real weapon-specific Pk, target-specific lethality, or stock AIM-120C
  effectiveness claim.
- No MLF-10 calibration gate, public-outcome fitting, or source-admission
  promotion.
- No reward shaping, entity deletion, direct crash rule, or debris physics.
- No edits inside archived MLF-1 through MLF-9 packages except link-only
  maintenance if a link is broken.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Open the subproject and freeze non-claims. | MLF-8 accepted / archived. | Parent index links this project and task clusters exist. | pass |
| `P1 Evidence Inventory` | Map replayable upstream fields and missing joins. | P0 docs exist. | Inventory names accepted inputs, missing fields, and safe write sets. | pass |
| `P2 Metric Contract` | Define rows, denominators, buckets, and uncertainty labels. | P1 complete. | Contract can be implemented without implying calibration. | initial pass |
| `P3 Trend Harness` | Produce deterministic replay/statistical summaries. | P2 contract available. | Focused tests cover controlled fixture trends. | initial pass |
| `P4 Integration` | Expose reports through diagnostics or retained artifacts. | P3 trend harness available. | Reports are consumable without reward/training leakage. | initial pass |
| `P5 Validation` | Run focused and smoke validation. | P4 report integration available. | Validation separates trend evidence from real Pk. | pass |
| `P6 Closure` | Accept, hold, or re-scope MLF-9 and sync indexes. | P5 evidence exists. | README/status/acceptance, pointer path, and archive registry agree. | pass |

## Task Clusters

- Task cluster plan:
  [missile_lethality_pk_statistical_trends_task_clusters_20260619.md](missile_lethality_pk_statistical_trends_task_clusters_20260619.md)
- Dispatch queue:
  [missile_lethality_pk_statistical_trends_dispatch_queue_20260619.md](missile_lethality_pk_statistical_trends_dispatch_queue_20260619.md)
- Evidence inventory:
  [missile_lethality_pk_statistical_trends_inventory_20260619.md](missile_lethality_pk_statistical_trends_inventory_20260619.md)
- Metric contract:
  [missile_lethality_pk_statistical_trends_metric_contract_20260619.md](missile_lethality_pk_statistical_trends_metric_contract_20260619.md)
- Trend harness result:
  [missile_lethality_pk_statistical_trends_trend_harness_20260619.md](missile_lethality_pk_statistical_trends_trend_harness_20260619.md)
- Report integration result:
  [missile_lethality_pk_statistical_trends_report_integration_20260619.md](missile_lethality_pk_statistical_trends_report_integration_20260619.md)
- Focused validation:
  [missile_lethality_pk_statistical_trends_validation_20260619.md](missile_lethality_pk_statistical_trends_validation_20260619.md)
- Acceptance record:
  [missile_lethality_pk_statistical_trends_acceptance_20260619.md](missile_lethality_pk_statistical_trends_acceptance_20260619.md)

## Outputs And Evidence

- Planning surface and parent index entry for MLF-9.
- P1 evidence inventory over MLF-5 through MLF-8 inputs and diagnostics outputs.
- P2 initial metric contract for replay rows, denominators, outcome buckets, and
  uncertainty labels.
- Diagnostics process-probe row-surface update exposing `structural_breakup`
  rows and snapshot fields.
- Deterministic MLF-9 trend harness over explicit row fixtures:
  `tools/diagnostics/mlf9_statistical_trends.py` and
  `tests/tools/test_mlf9_statistical_trends.py`.
- Process-probe retained report integration through `mlf9_statistical_trends`
  payloads and optional `--mlf9_report_json_out`.
- P5 focused validation reports `53 passed`, clean diff whitespace, and 0
  missing local Markdown links over the MLF-9/A2 docs set.
- P6 acceptance record marks the deterministic simulation-trend/report slice
  accepted / archived and leaves real-world Pk/calibration held.

## Acceptance Gate

This subproject can be marked accepted only when:

- MLF-9 reports are generated from explicit replay rows or controlled fixtures.
- Tests show that trend summaries are deterministic, bounded, and do not leak
  into reward, entity deletion, or calibration authority.
- Documentation states the denominator, sample source, uncertainty labels, and
  non-claims for every reported trend.
- Real weapon-specific Pk and calibration claims remain refused.

## Residuals And Next Steps

- Immediate: no further MLF-9 implementation is required for the accepted
  simulation-trend/report slice.
- Deferred: MLF-10 calibration gates, public-source outcome admission, and
  selected weapon/target calibration.

## Archive

MLF-9 has been physically archived under the parent A2 local archive. The old
active path now contains only a lightweight compatibility pointer.
