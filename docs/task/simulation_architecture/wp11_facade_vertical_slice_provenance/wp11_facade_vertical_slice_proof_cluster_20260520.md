# WP11-C Facade Vertical Slice Proof

Status: `2026-05-20` planned WP11 dispatch sheet.

Language:

- English canonical: `wp11_facade_vertical_slice_proof_cluster_20260520.md`
- Chinese companion:
  [wp11_facade_vertical_slice_proof_cluster_20260520.zh.md](wp11_facade_vertical_slice_proof_cluster_20260520.zh.md)

Inputs:

- [WP11 facade vertical slice and provenance](facade_vertical_slice_provenance_wp11_20260520.md)
- [WP11-A ActionHoldPolicy contract](wp11_action_hold_policy_cluster_20260520.md)
- [WP11-B information provenance labels](wp11_information_provenance_labels_cluster_20260520.md)
- [WP10 acceptance review](../../review/wp10_causal_runtime_foundation_acceptance_review_20260520.md)

## 1. Purpose

`WP11-C` proves one maintained chain over the accepted WP10 seam. The chain must
be visible from runtime evidence through facade export and into a Python binding
or maintained consumer smoke test.

## 2. Scope

In scope:

- use WP10 node ids and barrier ids without redefining them;
- prove event/snapshot/barrier/provenance metadata in one facade-visible chain;
- include `ActionHoldPolicy` as a contract-visible prerequisite without running
  a full cadence loop;
- prove Python/binding visibility for the selected chain;
- add one end-to-end or tightly coupled focused test.

Out of scope:

- broad facade API rewrite;
- full scheduler replacement;
- new backend/fidelity behavior;
- hidden raw runtime access as the maintained proof path.

## 3. Required Chain

The proof should reference the same identifiers across layers:

```text
p7.fire_control_launch.v1 / p9.effects_damage.v1 / p10.observation_export.v1
  -> input_injection / window_commit / export barrier evidence
  -> LaunchEvent / EffectsEvent / DamageReport / DiagnosticsTrace ancestry
  -> ObservationBatchPacket or EngagementEventPacket provenance
  -> Python binding or maintained consumer smoke
```

## 4. Acceptance Tests

Minimum tests:

- end-to-end proof references WP10 node ids and export barrier ids;
- facade export carries event/snapshot/barrier/source-time/provenance metadata;
- Python-facing object exposes the same evidence fields;
- the test does not rely on undocumented insertion order or wall-clock time;
- any raw runtime setup path is diagnostics-only and allowlisted explicitly.

## 5. Handoff Contract

Return:

- vertical-slice test paths and runtime/facade files touched;
- exact identifiers proved across the chain;
- commands run and outcomes;
- raw runtime escape hatches added or changed, if any;
- integration notes for `WP11-D/E`.
