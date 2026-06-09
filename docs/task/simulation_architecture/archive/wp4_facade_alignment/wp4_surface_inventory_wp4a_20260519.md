# WP4-A Surface Inventory Draft

Status: `2026-05-19` first inventory draft.

Language:

- English canonical: `wp4_surface_inventory_wp4a_20260519.md`
- Chinese companion: [wp4_surface_inventory_wp4a_20260519.zh.md](wp4_surface_inventory_wp4a_20260519.zh.md)

Inputs:

- [WP4-A facade surface inventory dispatch](wp4_surface_inventory_cluster_20260519.md)
- [WP4 facade alignment](facade_alignment_wp4_20260519.md)
- [WP4 facade alignment plan review](../review/wp4_facade_alignment_plan_review_20260519.md)
- [Temp-02 SCAL architecture vision review](../review/temp-02_review_20260519.md)
- Current facade headers in `src/runtime/facade/*` and Python bindings in
  `src/interfaces/python/bindings_runtime.cpp`

This draft is documentation-only. It does not implement facade methods, split
`RuntimeFacade`, or add runtime scheduler/replay behavior.

## 1. Purpose

WP4-A establishes the surface vocabulary that later WP4 workers should use
before changing facade, policy, binding, diagnostics, or validation code.

The inventory has three goals:

1. classify each surface as `maintained`, `compatibility_adapter`,
   `diagnostics_only`, or `deferred`;
2. state the metadata required by the WP4-A dispatch sheet for each surface;
3. preserve the Temp-02 information/agency/evidence boundaries:
   `World Truth`, `ObservationPacket`, `DecisionBelief`, `AgentRole`, and
   `DiagnosticsTrace` are not interchangeable.

## 2. Classification Rules

| Classification | Meaning | Maintained truth status |
|----------------|---------|-------------------------|
| `maintained` | Canonical surface or contract concept that later implementation may rely on. | May define facade, policy, replay, or validation truth according to its owner. |
| `compatibility_adapter` | Existing or migration-period path that may remain available but is not the preferred maintained path. | Must not become the mainline path without reclassification. |
| `diagnostics_only` | Evidence, debug, oracle, or inspection surface. | Must not define scheduler truth, policy/training truth, or world truth. |
| `deferred` | Named surface candidate that is intentionally not implemented or promoted in WP4-A. | No maintained behavior until a later WP4/WP5/backend task promotes it. |

Consumer groups use the WP4-A vocabulary: `frontend`, `policy`,
`orchestration`, `test`, `diagnostics`, `binding`, or `backend`.

Information-state layers use the WP4-A vocabulary: `WorldTruth`,
`SensedState`, `TrackState`, `SharedTacticalPicture`, `AgentObservation`,
`DecisionBelief`, or `not_applicable`.

## 3. Surface Inventory

| Surface | classification | consumer_group | request/result DTO | source_layer | snapshot_semantics | scheduler_dependency | information_state_layer | compatibility_rule | deprecation_rule | validation_gate |
|---------|----------------|----------------|--------------------|--------------|--------------------|----------------------|-------------------------|--------------------|------------------|-----------------|
| `BatchWorldSetupRequest` / `BatchWorldSetupResult`; `BatchResetRequest` | `maintained` | frontend, test, orchestration, binding | request: `BatchWorldSetupRequest` or `BatchResetRequest`; result: `BatchWorldSetupResult` or reset side effect | facade plus simulation setup | setup/reset commit creates or resets the `setup` shard and initial `SnapshotVersion` ancestry | `state_shard_version`, `barrier_visibility`, `replay_metadata` | `WorldTruth` | legacy setup through raw runtime is allowed only as compatibility diagnostics | remove raw setup dependence when facade setup covers current tests and bindings | facade setup/reset tests plus architecture raw-runtime layering gate |
| `ObservationViewSpec` | `maintained` | policy, test, binding | request: none in current C++ facade; result/concept: `ObservationViewSpec` | policy/test owns schema; facade owns export binding | names schema version, required fields, optional fields, include flags, source snapshot requirement, encoding/normalization owner | `state_shard_version`, `barrier_visibility`, `replay_metadata` | `AgentObservation` | direct Python observation assembly remains compatibility until it can name an equivalent view spec and source snapshot | deprecate direct assembly when `ObservationBatchRequest` or adapter metadata carries view-spec parity | WP5 information/belief leakage gate and observation schema compatibility gate |
| `ObservationPacket` / `ObservationBatchRequest` / `ObservationBatchPacket` | `maintained` | frontend, policy, test, binding | request: `ObservationBatchRequest`; result: `ObservationBatchPacket` | facade export over simulation state | must name committed source `SnapshotVersion`, source time, export barrier, and observation packet version once runtime metadata exists | `state_shard_version`, `barrier_visibility`, `replay_metadata` | `AgentObservation` | direct getters such as `get_agent_observations_batch` are compatibility helpers when they bypass packet provenance | narrow direct getters after packet export carries required provenance and tests use packet path | facade observation tests plus WP5 information/belief leakage gate |
| `DecisionBelief` | `maintained` | policy, orchestration, test | request: consumed `ObservationPacket` or memory/estimator input; result/concept: `DecisionBelief` | policy/agent side | must declare consumed observation packet ids, observation snapshot versions, memory/estimator state, model reference, and uncertainty/confidence shape | `replay_metadata`, `state_shard_version`, `barrier_visibility` | `DecisionBelief` | truth-derived oracle beliefs are `diagnostics_only` and must carry an oracle label | deprecate oracle fallback for maintained adapters once belief metadata is available | WP5 information/belief leakage gate distinguishing declared belief from `WorldTruth` |
| `EngagementBatchRequest` / `EngagementEventPacket` | `maintained` | frontend, test, diagnostics, binding | request: `EngagementBatchRequest`; result: `EngagementEventPacket` | facade export over engagement evidence | track, launch, lifecycle, effects, damage, and diagnostics payloads must preserve world-safe refs and event/report ancestry | `event_order`, `state_shard_version`, `barrier_visibility`, `replay_metadata` | `TrackState` | unused packet slots may stay placeholders only if documented as compatibility gaps | remove placeholder ambiguity when producer coverage is documented by WP4-B/WP5 trace gates | engagement facade tests and trace conformance tests |
| `ExecutionBatchStepRequest` / `ExecutionBatchStepResult` | `maintained` | frontend, policy, orchestration, test, binding | request: `ExecutionBatchStepRequest`; result: `ExecutionBatchStepResult` | facade execution step over compiled runtime products | step result should carry observation snapshot, reward fact/shaping ancestry, termination source, and mirrored status provenance | `barrier_visibility`, `clock_domain`, `state_shard_version`, `replay_metadata` | `AgentObservation` | Python step assembly fallback is compatibility until facade result carries all ownership metadata | deprecate fallback when reward, termination, observation, and lifecycle provenance are facade-visible | facade step tests plus WP4-C lifecycle alignment gates |
| `ActionIntentPacket` / `ActionHoldPolicy` | `deferred` | policy, orchestration, test | request: future `ActionIntentPacket`; result: accepted/rejected intent or translated command/control packet | policy/orchestration through facade-compatible adapter | requires `source_id`, `input_snapshot_version`, `effective_time`, `valid_until`, `merge_policy`, and hold/expiry metadata | `clock_domain`, `barrier_visibility`, `replay_metadata`, `event_order` | `DecisionBelief` | current direct action assignment paths are compatibility adapters and must not be treated as maintained policy truth | promote after WP4-D defines adapter path and WP5 can test cadence/replay metadata | WP4-D action bridge plus WP5 boundary/replay gates |
| `CoordinationIntentPacket` | `deferred` | policy, orchestration, frontend, test | request: future `CoordinationIntentPacket`; result: accepted/rejected tasking or coordination report | policy/orchestration/human producer through facade-compatible adapter | requires source type/id, roster, target refs, update clock, `effective_time`, `merge_policy`, produced tasking fields | `event_order`, `barrier_visibility`, `clock_domain`, `replay_metadata` | `SharedTacticalPicture` | current cooperative director writes are compatibility until they cross a declared facade-compatible injection path | promote after WP4-D defines coordination adapter and raw tasking writes are no longer mainline | WP4-D coordination bridge and architecture raw-mutation gate |
| `AgentRole` | `deferred` | policy, orchestration, test, binding | request: none in WP4-A; result/concept: `AgentRole` | policy/agent boundary | must name role id/type, authority scope, information-state source, decision model reference, and action interface before maintained use | `replay_metadata`, `clock_domain` when actions are emitted | `DecisionBelief` | ad hoc policy identity remains compatibility until mapped to an `AgentRole` | promote after WP4-D contract sketch connects current adapters to role metadata | WP4-D AgentRole gate and WP5 information/agency gate |
| `RewardSpec` / `RewardReport` | `maintained` | policy, test, orchestration, binding | request: reward spec may be external/configured; result: reward fields in `ExecutionBatchStepResult` and future `RewardReport` | split simulation facts and policy/test shaping | fact terms must name source `SnapshotVersion`; shaping terms must name owner/source and consumed observation/belief when applicable | `state_shard_version`, `barrier_visibility`, `replay_metadata` | `not_applicable` | Python reward fallback remains compatibility when it labels fact/shaping ownership and source versions | deprecate unlabelled fallback after WP4-C exposes fact/shaping attribution | WP4-C reward attribution tests |
| `TerminationSpec` / `EpisodeStatus` | `maintained` | frontend, policy, orchestration, test, binding | request: orchestration truncation/reset request when present; result: termination/status fields in `ExecutionBatchStepResult` and future `EpisodeStatus` | simulation owns semantic termination; orchestration owns truncation | terminated/truncated reason must carry reason source, source time, snapshot version, and mirrored phase status | `state_shard_version`, `barrier_visibility`, `replay_metadata` | `not_applicable` | Gymnasium-style adapter mirrors are compatibility unless they preserve authoritative source | deprecate private adapter phase machines after facade lifecycle source is explicit | WP4-C termination/lifecycle tests |
| `EpisodeLifecycleContract` | `maintained` | frontend, policy, orchestration, test, binding | request: reset/step lifecycle requests; result: phase, step count, reset transition id, mirrored status | compiled runtime/facade authority with adapter mirrors | facade state is authoritative; adapters may mirror phase but not advance private truth | `barrier_visibility`, `replay_metadata` | `not_applicable` | adapter-local lifecycle state is compatibility mirror only | remove authoritative adapter phase mutation when facade phase covers use cases | architecture lifecycle authority gate and WP4-C tests |
| `DiagnosticsTrace` | `diagnostics_only` | diagnostics, test, frontend, binding | request: currently piggybacks on `EngagementBatchRequest`; result: `DiagnosticsTrace` inside `EngagementEventPacket` | core/engine evidence exported through facade | trace links request, event, report, snapshot/export version, and observation packet version where available | `event_order`, `state_shard_version`, `barrier_visibility`, `replay_metadata` | `not_applicable` | WP4 may keep trace piggyback on engagement export; no dedicated diagnostics facade is required in WP4-A | promote to dedicated diagnostics query/export surface when WP5 trace conformance needs cross-surface queries | WP5 trace and replay/evidence conformance gates |
| Direct observation getters: `get_agent_observations_batch`, `get_instrument_states_batch`, `get_mission_commands_batch`, `get_task_orders_batch`, `get_leader_intents_batch`, `get_pilot_reports_batch` | `compatibility_adapter` | frontend, test, binding | request: `WorldEntityRef` list; result: per-field vectors | facade helper over simulation state | may lack unified packet provenance and view-spec schema metadata | `state_shard_version`, `barrier_visibility` | varies; usually `AgentObservation` or `not_applicable` | allowed while tests and bindings migrate to `ObservationBatchPacket` | narrow or mark diagnostics when packet path has parity and provenance | facade observation parity tests |
| `RuntimeFacade::runtime()` / raw `WorldBatchRuntime` | `compatibility_adapter` | test, diagnostics, backend | request: raw runtime access; result: raw runtime handle | facade escape hatch to simulation internals | not a facade snapshot contract | none for maintained truth; may inspect scheduler artifacts for diagnostics | `WorldTruth` | allowed only for legacy tests, migration debugging, and low-level capability verification | remove from maintained frontend paths; keep only explicit diagnostics/legacy use | `tests/architecture/runtime_facade/test_layering.py` |
| `RuntimeCapabilities` / backend capability query | `deferred` | backend, frontend, diagnostics, test | request: `capabilities()`; result: `RuntimeCapabilities` | facade/backend capability boundary | current struct documents capability flags but does not define backend profile parity or resident-state semantics | future `clock_domain`, `state_shard_version`, `replay_metadata`, parity budget | `not_applicable` | existing empty/simple query may be documented but must not imply backend parity | promote in backend profile work after parity budget and device-resident state policy exist | deferred backend profile validation; not WP4-A implementation |
| `ef_py` mirror | `maintained` | binding, policy, test, frontend | request/result: mirrors stable C++ facade DTOs | Python binding adapter | must preserve DTO names and field semantics; no independent snapshot truth | same as mirrored surface | same as mirrored surface | Python helpers that bypass facade DTOs are compatibility-only | remove helper-only maintained docs when binding mirror covers stable DTOs | binding field-presence tests and raw-runtime exposure checks |

## 4. Information-State Boundaries

`ObservationViewSpec` is a maintained policy/test-owned surface concept. It
owns schema version, required fields, optional fields, feature encoding,
normalization, masking, stacking, and checkpoint compatibility behavior. It
does not own authoritative simulation state.

`ObservationPacket` is the facade-exported data product. The current C++ DTO is
`ObservationBatchPacket`. It is maintained only when it is sampled from a
declared source snapshot, barrier, and view specification. It is not a belief
state and must not silently include `WorldTruth` fields outside the declared
view.

`DecisionBelief` is the policy/agent-side belief layer. A maintained
`DecisionBelief` must name the `ObservationPacket` versions, memory/estimator
state, model reference, and uncertainty/confidence shape it consumed.
Truth-derived oracle beliefs are `diagnostics_only`.

`AgentRole` is the agency boundary: role plus authority plus information-state
source plus decision model plus action interface. WP4-A records the name and
boundary, but WP4-D owns the contract sketch and adapter mapping.

`DiagnosticsTrace` is the evidence boundary. It may cite truth, events, reports,
snapshots, and exports to explain what happened, but it must not become a
policy observation or maintained scheduler truth. In WP4-A it remains a
`diagnostics_only` surface piggybacking on engagement export until a later
diagnostics facade is promoted.

## 5. RuntimeFacade Split Threshold

WP4-A records this governance rule but does not implement a split:

```text
If RuntimeFacade exceeds 40 maintained public methods, plan a split into
RuntimeSessionFacade, WorldSetupFacade, ExecutionStepFacade,
ObservationFacade, EngagementFacade, DiagnosticsFacade, and
BackendCapabilityFacade.
```

The threshold is a planning trigger. It does not require an automatic refactor,
and it does not count compatibility-only helpers the same way as maintained
request/result surfaces. A split proposal should first classify which methods
are maintained, compatibility-only, diagnostics-only, or deferred.

## 6. Acceptance Gates

WP4-A inventory is usable when:

1. every surface listed by the WP4-A dispatch sheet has a classification;
2. every row declares consumer group, request/result DTO, source layer,
   snapshot semantics, scheduler dependency, information-state layer,
   compatibility rule, deprecation rule, and validation gate;
3. `ObservationViewSpec`, `ObservationPacket`, `DecisionBelief`, `AgentRole`,
   and `DiagnosticsTrace` have explicit boundaries;
4. compatibility and diagnostics paths cannot be mistaken for maintained
   policy/training truth;
5. later WP4-B/C/D/E workers can cite the surface names without adding new
   vocabulary.

## 7. Open Questions

1. Should `ObservationViewSpec` become an explicit C++ DTO in WP4, or remain a
   documented policy/test-owned concept until WP5 validation needs runtime
   metadata?
2. Should `DiagnosticsTrace` receive a dedicated facade query/export during
   WP4, or is the engagement-piggyback path sufficient until WP5 trace
   conformance work?
3. Should `RuntimeCapabilities` be promoted before WP5, or remain deferred to
   backend profile/parity-budget work?
4. What exact method count should be used as the baseline for the
   `RuntimeFacade` split threshold: maintained request/result methods only, or
   all public methods excluding constructors and accessors?
