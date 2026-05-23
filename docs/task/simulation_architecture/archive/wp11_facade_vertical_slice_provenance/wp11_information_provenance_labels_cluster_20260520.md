# WP11-B Information Provenance Labels

Status: `2026-05-20` planned WP11 dispatch sheet.

Language:

- English canonical: `wp11_information_provenance_labels_cluster_20260520.md`
- Chinese companion:
  [wp11_information_provenance_labels_cluster_20260520.zh.md](wp11_information_provenance_labels_cluster_20260520.zh.md)

Inputs:

- [WP11 facade vertical slice and provenance](facade_vertical_slice_provenance_wp11_20260520.md)
- [WP10 causal runtime foundation](../wp10_causal_runtime_foundation/causal_runtime_foundation_wp10_20260520.md)
- [Post-WP9 gap analysis](../../review/post_wp9_gap_analysis_20260520.md)

## 1. Purpose

`WP11-B` adds stable information-state provenance labels to maintained
facade-visible packets and beliefs. These labels are the vocabulary later Law 14
and Agency Graph enforcement will consume.

## 2. Scope

In scope:

- define or reuse one canonical provenance DTO/vocabulary;
- label maintained `ObservationBatchPacket`, engagement/facade export metadata,
  and `DecisionBelief` surfaces where applicable;
- distinguish `WorldTruth`, `SensedState`, `TrackState`,
  `SharedTacticalPicture`, `AgentObservation`, and `DecisionBelief`;
- preserve `maintained`, `diagnostics_only`, and `compatibility_adapter`
  status labels;
- add Python/binding-visible tests for provenance survival.

Out of scope:

- full Law 14 enforcement;
- field masking for every observation view;
- Agency Graph authority checks;
- broad data-link or shared tactical picture runtime implementation.

## 3. Provenance Rules

Maintained facade exports must not be unlabeled.

| Label | Maintained use |
|-------|----------------|
| `WorldTruth` | Diagnostics-only unless a later accepted gate declares a transformation. |
| `SensedState` | Maintained when sampled through declared sensor/facade metadata. |
| `TrackState` | Maintained when track ids, source snapshot/version, and confidence metadata are present. |
| `SharedTacticalPicture` | Reserved unless link/roster constraints are implemented or explicitly compatibility-only. |
| `AgentObservation` | Maintained facade-facing observation input. |
| `DecisionBelief` | Maintained only when derived from declared observation, memory, estimator, or decision-model inputs. |

## 4. Acceptance Tests

Minimum tests:

- maintained facade observation packets carry a non-empty provenance label;
- maintained diagnostics/engagement traces preserve source snapshot and
  information-state label where relevant;
- maintained `DecisionBelief` cannot silently claim truth/raw-ECS ancestry;
- binding tests prove labels survive Python-facing DTOs;
- diagnostics-only truth paths remain allowed only when explicitly labeled.

## 5. Handoff Contract

Return:

- provenance vocabulary and DTO/helper paths;
- packet or belief fields added/updated;
- tests added or updated;
- commands run and outcomes;
- any labels reserved but not yet runtime-populated;
- integration notes for `WP11-C/D/E`.
