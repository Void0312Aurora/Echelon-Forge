# WP10-D Event And Snapshot Evidence

Status: `2026-05-20` planned WP10 dispatch sheet.

Language:

- English canonical: `wp10_event_snapshot_evidence_cluster_20260520.md`
- Chinese companion:
  [wp10_event_snapshot_evidence_cluster_20260520.zh.md](wp10_event_snapshot_evidence_cluster_20260520.zh.md)

Inputs:

- [WP10 causal runtime foundation](causal_runtime_foundation_wp10_20260520.md)
- [WP10-A manifest registry](wp10_manifest_registry_cluster_20260520.md)
- [WP10-B window loop and injection](wp10_window_loop_injection_cluster_20260520.md)
- [WP10-C same-window validation](wp10_same_window_validation_cluster_20260520.md)
- [WP5 validation harness](../wp5_validation_harness/validation_harness_wp5_20260519.md)
- [WP9 contract and infrastructure closure](../wp9_contract_infrastructure_closure/contract_infrastructure_closure_wp9_20260520.md)

## 1. Purpose

`WP10-D` proves that the selected runtime seam is visible through maintained
evidence, not just internal code structure. The facade-visible path must expose
or assert deterministic event ordering, snapshot version, barrier id, source
time, and diagnostics ancestry.

## 2. Scope

In scope:

- bind events to manifest node ids or maintained source ids;
- preserve deterministic event ordering by `(timestamp, priority, event_id)`;
- expose or assert `SnapshotVersion` / source shard ancestry where the facade
  already returns packets;
- preserve `barrier_id`, barrier sequence/detail, and simulated source time;
- tie diagnostics traces to event ancestry;
- add facade-visible or binding-visible tests for the selected slice.

Out of scope:

- replay engine rewrite;
- snapshot/restore implementation;
- counterfactual branching;
- broad DTO redesign;
- treating diagnostics-only truth as maintained policy or training truth.

## 3. Evidence Fields

The selected slice should preserve these field groups.

| Field group | Required evidence |
|-------------|-------------------|
| Event identity | `event_id`, `event_family`, `timestamp`, `priority`, producing `node_id` or maintained `source_id`. |
| Event ordering | Stable sort by `(timestamp, priority, event_id)` with deterministic tie-breakers. |
| Snapshot ancestry | `world_id`, `SnapshotVersion` or source shard versions, `global_version` where available. |
| Barrier ancestry | `barrier_id`, `barrier_sequence`, optional `barrier_detail`. |
| Source time | Simulated `source_time_s`; wall-clock time must not define ordering. |
| Diagnostics ancestry | Diagnostics trace id/ref plus source request/event refs needed to explain the exported packet. |
| Facade/binding visibility | Runtime facade or Python-visible packet/test proving the metadata survives the consumer boundary. |

## 4. Acceptance Tests

Minimum tests:

- repeated runs produce the same event ordering for the selected fixture;
- facade-visible recent engagement events or observation exports carry source
  snapshot/barrier/source-time metadata;
- diagnostics trace can name the event ancestry;
- Python binding smoke either proves the metadata is visible or records the
  exact import/build blocker;
- tests reject insertion-order-only event ordering.

## 5. Handoff Contract

Return:

- metadata fields added or asserted;
- facade/binding tests added or updated;
- deterministic ordering fixture details;
- commands run and outcomes;
- any Python binding blockers;
- residuals for Phase 2 provenance-label work.
