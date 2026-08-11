# Kill-Chain Expectation Standardization Dispatch Queue

Status: `2026-06-23` current-session queue for the integrated P0-P5 docs-only
pass.

Chinese companion:
[kill_chain_expectation_standardization_dispatch_queue_20260621.zh.md](kill_chain_expectation_standardization_dispatch_queue_20260621.zh.md)

Parent task clusters:
[kill_chain_expectation_standardization_task_clusters_20260621.md](kill_chain_expectation_standardization_task_clusters_20260621.md)

## Boundary

This queue only covers expectation standardization. It must not create a new
Codex session thread, modify runtime code, retune descriptors, or claim real
AIM-120C/F-16C/Pk authority.

## Current Packets

| Packet | Cluster | Assignee | Write set | Required output | Status |
| --- | --- | --- | --- | --- | --- |
| `KCES-P0-W1` | `KCES-P0 Project Boundary` | main thread | subproject docs and parent A2 README files | Create the subproject shell and link it from A2. | integrated pass |
| `KCES-P1-W1` | `KCES-P1 Expectation Contract` | main thread | expectation contract docs | Draft the v0 expectation contract with normalized distance and AIM-120C-like seed profile. | integrated pass |
| `KCES-P2-W1` | `KCES-P2 Scenario Matrix` | main thread | scenario matrix docs | Build a range x offset-angle heatmap, classify the nonmaneuvering full grid and maneuver sparse grid as nominal, marginal, or outside-envelope, estimate the recommended main grid / seed budget, and choose the first `R_effect_variant` handoff. | integrated pass |
| `KCES-P3-W1` | `KCES-P3 Metric Mapping` | main thread | metric mapping docs and status surfaces | Map expectation bands, sampling-density tiers, `R_effect_variant` values, and owner guards to stage-report / derived-report fields. | integrated pass |
| `KCES-P4-W1` | `KCES-P4 Calibration Harness Plan` | main thread | harness plan docs and status surfaces | Bind the P3 report row schema to single-layer delta-guard checks, artifact family, and pilot-batch plan without retuning. | integrated pass |
| `KCES-P5-W1` | `KCES-P5 Closure / Promotion Decision` | main thread | P5 decision doc and status surfaces | Decide that P1-P4 pass content remains a task-local docs-only standard and does not promote into `docs/standards` in this batch. | integrated pass |

## Ready Follow-Ups

None. This P0-P5 docs-only queue is closed. Future harness implementation or
standards promotion must enter as a newly named workstream.

## Integration Notes

- P1 is closed with `R_effect` as an independent review variable.
- P2 should not rely on current runtime success or failure as the oracle.
- P2 has selected the first `R_effect_variant` rows and expanded the calibration
  object into a heatmap; the recommended main grid is about `572` signed cases
  per seed; stage-report metric mapping now belongs to P3.
- P3 has mapped heatmap cells, sampling tiers, and `R_effect_variant` values to
  a report row schema.
- P4 has reused the P6 single-layer guard shape in a docs-only harness plan, but
  has not run batch simulation.
- P5 decided that this subproject remains a task-local docs-only standard; this
  batch does not write into `docs/standards` or silently promote runtime
  behavior.

## Worker Packet Contract

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```
