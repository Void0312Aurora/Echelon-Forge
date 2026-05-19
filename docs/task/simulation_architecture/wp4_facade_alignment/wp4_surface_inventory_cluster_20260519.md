# WP4-A Normative Dispatch Sheet: Facade Surface Inventory

Status: `2026-05-19` dispatch sheet; first WP4 wave.

Language:

- English canonical: `wp4_surface_inventory_cluster_20260519.md`
- Chinese companion: [wp4_surface_inventory_cluster_20260519.zh.md](wp4_surface_inventory_cluster_20260519.zh.md)

Inputs:

- [WP4 facade alignment](facade_alignment_wp4_20260519.md)
- [WP4 facade alignment plan review](../review/wp4_facade_alignment_plan_review_20260519.md)
- [WP2.5 scheduler semantics freeze](scheduler_semantics_wp25_20260519.md)
- [Temp-02 SCAL architecture vision review](../review/temp-02_review_20260519.md)
- Current `src/runtime/facade/*` and `src/interfaces/python/bindings_runtime.cpp`

Normative language:

- `MUST` marks required WP4 behavior for maintained documentation and later
  implementation.
- `MUST NOT` marks behavior that cannot become maintained facade truth.
- `SHOULD` marks the default rule; deviations need an explicit review note.
- `MAY` marks an allowed compatibility or documentation path.

## 1. Purpose

This sheet turns `WP4-A Facade Surface Inventory` into a bounded task cluster.
It is the shared vocabulary pass for the rest of WP4.

WP4-A MUST produce a canonical surface map before workers add or reshape facade
behavior. It should absorb the WP4 plan-review findings:

- `ObservationViewSpec` is an independent policy/test-owned surface concept.
- `DecisionBelief` is a policy/agent-side belief layer derived from declared
  observation inputs, not from `World Truth`.
- `DiagnosticsTrace` deserves an explicit facade/evidence surface decision,
  even if the first implementation still piggybacks on engagement export.
- Per-surface dependency on WP2.5 scheduler semantics MUST be declared.
- Facade endpoint governance SHOULD be documented before the public surface
  grows further.

## 2. Dispatch Deliverables

| Stream | Required output | Owner profile | Reasoning budget |
|--------|-----------------|---------------|------------------|
| `WP4-A1 Surface Catalog` | Canonical table of maintained, compatibility-only, diagnostics-only, and deferred facade surfaces. | Facade surface worker. | High. |
| `WP4-A2 Observation And Belief Boundary` | `ObservationViewSpec`, `ObservationPacket`, and `DecisionBelief` provenance rules. | Information-state worker. | High. |
| `WP4-A3 Diagnostics Surface Decision` | Decision whether `DiagnosticsTrace` is a dedicated facade surface now or a documented piggyback until WP5. | Diagnostics worker. | Medium-high. |
| `WP4-A4 Endpoint Governance` | Per-surface metadata fields and split-threshold rule for `RuntimeFacade`. | Integration-minded facade worker. | Medium. |
| Cluster integration | English/Chinese section alignment and `git diff --check`. | Main integration owner. | Medium. |

## 3. Required Surface Metadata

Every maintained WP4 surface entry MUST declare:

| Field | Rule |
|-------|------|
| `surface_name` | Stable C++/Python-facing request, result, packet, or concept name. |
| `classification` | One of `maintained`, `compatibility_adapter`, `diagnostics_only`, `deferred`. |
| `consumer_group` | `frontend`, `policy`, `orchestration`, `test`, `diagnostics`, `binding`, or `backend`. |
| `request_dto` | Request/input DTO name, or `none` for pure query/export concepts. |
| `result_dto` | Result/output DTO name, packet name, or declared concept output. |
| `source_layer` | Simulation, facade, policy, orchestration, adapter, human, or diagnostics. |
| `snapshot_semantics` | Source `SnapshotVersion`, observation version, event ancestry, or `not_applicable`. |
| `scheduler_dependency` | WP2.5 dependency such as `event_order`, `barrier_visibility`, `clock_domain`, `state_shard_version`, `replay_metadata`, or `none`. |
| `information_state_layer` | One of `WorldTruth`, `SensedState`, `TrackState`, `SharedTacticalPicture`, `AgentObservation`, `DecisionBelief`, or `not_applicable`. |
| `compatibility_rule` | Whether legacy/raw access is allowed and what diagnostics label it carries. |
| `deprecation_rule` | Condition for removing or narrowing the compatibility path. |
| `validation_gate` | Test, architecture gate, or WP5 tier that proves the surface is safe. |

## 4. Surface Decisions To Freeze

WP4-A MUST classify at least these surfaces:

| Surface | Default WP4-A decision |
|---------|------------------------|
| `BatchWorldSetupRequest` / `BatchWorldSetupResult` | Maintained setup/reset surface. |
| `ObservationViewSpec` | Independent policy/test-owned concept with schema version and required/optional field rules. |
| `ObservationBatchRequest` / `ObservationBatchPacket` | Maintained facade export over declared observation provenance. |
| `DecisionBelief` | Maintained only when derived from declared observations or memory/estimator state; truth-derived beliefs are diagnostics-only. |
| `EngagementBatchRequest` / `EngagementEventPacket` | Maintained engagement export; producer coverage must be explicit. |
| `ExecutionBatchStepRequest` / `ExecutionBatchStepResult` | Maintained step/result surface. |
| `ActionIntentPacket` / `ActionHoldPolicy` | Facade-compatible policy action input; scheduler dependency on clock domains and replay metadata. |
| `CoordinationIntentPacket` | Facade-compatible coordination input; scheduler dependency on external injection and merge policy. |
| `AgentRole` | Agent boundary concept: role, authority, information source, decision model, action interface. |
| `RewardSpec` / `RewardReport` | Split simulation facts from shaping terms. |
| `TerminationSpec` / `EpisodeStatus` | Split semantic termination from orchestration truncation. |
| `EpisodeLifecycleContract` | Compiled/facade phase authority with adapter mirrors only. |
| `DiagnosticsTrace` | Either a maintained diagnostics query/export surface or a documented WP4 piggyback with WP5 promotion gate. |
| `RuntimeFacade::runtime()` / raw `WorldBatchRuntime` | Compatibility-only diagnostics escape hatch. |
| `RuntimeCapabilities` / backend capability query | Deferred to backend profile work unless an existing empty surface needs documentation. |

## 5. Observation And Belief Rules

WP4-A MUST state:

1. `ObservationViewSpec` owns schema version, required fields, optional fields,
   feature encoding, normalization, masking, stacking, and checkpoint
   compatibility behavior.
2. `ObservationPacket` owns facade-exported data sampled at a declared barrier
   or snapshot version.
3. `DecisionBelief` is not world truth. It MUST declare consumed observation
   versions or declared memory/estimator state.
4. Truth-derived oracle material MUST be labeled `diagnostics_only`.
5. Any maintained policy or orchestration adapter that uses belief metadata
   MUST be able to name the `AgentRole` that consumed it.

## 6. Facade Split Threshold

WP4 does not split `RuntimeFacade` by default. WP4-A SHOULD document this rule:

```text
If RuntimeFacade exceeds 40 maintained public methods, plan a split into
RuntimeSessionFacade, WorldSetupFacade, ExecutionStepFacade,
ObservationFacade, EngagementFacade, DiagnosticsFacade, and
BackendCapabilityFacade.
```

The threshold is a governance trigger, not an automatic refactor.

## 7. Exit Criteria

This cluster exits when:

1. WP4 has one canonical surface inventory that later workers can cite.
2. `ObservationViewSpec`, `DecisionBelief`, `AgentRole`, and `DiagnosticsTrace`
   have explicit WP4 classification.
3. Every maintained surface names scheduler dependencies or says `none`.
4. Compatibility-only and diagnostics-only paths cannot be confused with
   maintained policy/training truth.
5. The companion Chinese sheet is aligned enough for task dispatch.
