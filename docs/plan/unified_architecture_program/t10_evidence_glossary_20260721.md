# T10 Evidence Glossary (2026-07-21)

Language:
- English canonical: `t10_evidence_glossary_20260721.md`
- Chinese companion: [t10_evidence_glossary_20260721.zh.md](t10_evidence_glossary_20260721.zh.md)

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/plan/unified_architecture_program/t10_evidence_glossary_20260721.md`
Owner: `unified architecture program workline`
Last verified: `2026-07-21`
Baseline commit: `1d25c4d1`

Status: T10 second-slice additive evidence glossary for the
[Unified Architecture Program](README.md), executing slice 2 of the order
recorded in the
[T10 Evidence Spine Census](t10_evidence_spine_census_20260721.md) (section 3:
"Additive evidence glossary. A schema-sourced id/version glossary (VA-1, VA-2,
VA-3) mapping the `uint64` and `string` id spaces and the two version
concepts — documentation + schema metadata, no field changes"). This document
is a descriptive `reference` register, not an independent review: it is the
authoritative field-by-field vocabulary for the evidence id spaces and the two
version concepts, each fact re-verified against source at baseline `1d25c4d1`
(the census was verified at `8bd21d86`; the surface is unchanged and each row
carries its own `file:line` pointer). It changes no behavior, no field, and no
`src/**`/`python/**` code. Vocabulary follows the SCAL Evidence Graph face in
[Simulation System Architecture Design](../architecture/simulation_system_architecture_design.md)
(section 2, Evidence Graph: "Trace ids, packet ancestry, snapshot versions,
event order, and validation verdicts").

## 0. Method And Scope

- Re-read the maintained surface (`src/**` read-only, `python/**`,
  `tools/maintenance/dto_schema/**`, `tests/**`) at baseline `1d25c4d1`. Every
  glossary row below cites the `file:line` it was verified against; where a
  fact is a producer behavior (not a declaration) the producer `file:line` is
  cited too. Declaration line numbers were re-extracted mechanically from the
  checked-in sources (not transcribed by hand) and spot-checked.
- The schema-single-sourced DTO field lists live in X-macro `.inc` fragments
  under `src/runtime/contracts/detail/` and `src/runtime/facade/detail/`,
  generated from `tools/maintenance/dto_schema/schemas/*.py`. Line numbers for
  those fields refer to the checked-in `.inc` fragment (the ABI/serialization
  surface). The counterfactual/replay contract types in
  `src/runtime/contracts/counterfactual_replay_contract_types.h` are
  hand-written structs; line numbers refer to that header.
- **Value-provenance legend (applies to every table).** Two distinctions are
  kept explicit throughout: (a) the *declared default* (what the `.inc`/header
  declaration initializes, i.e. what a default-constructed DTO carries) versus
  the *production-path value* (what the kernel/facade actually writes on
  export/experiment paths) — several fields differ between the two; and
  (b) *caller-constructible* (the DTO is a contract type that callers and WP15
  test fixtures may fill directly) versus *facade/kernel-produced* (a
  production code path assigns the field). "Producer" columns list the
  production-path assignments and mark caller-constructible surfaces
  explicitly.
- This glossary maps VA-1 (id-type split), VA-2 (snapshot-version name/type,
  no monotone counter today), and VA-3 (version-concept conflation) from the
  census. VA-4/VA-5/VA-6/VA-7/VA-8 are referenced where an id/version field
  participates in them, but their alignment work stays with the census's later
  slices.
- Zero code change. The optional schema-metadata sub-task was assessed and
  declined; the reason (no semantically fitting existing channel; extending
  the model is a generator code change outside this slice's red line) is
  recorded in section 6.

## 1. Evidence Id Spaces

The evidence surface carries identity in two disjoint representations that no
single typed field bridges today (VA-1): a `std::uint64_t` space on the
trace/engagement/packet surface, and a `std::string` space on the
worldline/replay/experiment surface. (No typed conversion exists; the
crossings are textual embeddings of numbers into strings — non-exhaustive
examples: the worldline-id default embeds `world_index`/`entity_id` digits,
the restore-boundary `snapshot_version_ref` embeds the `uint64`
`snapshot_version`, the adapter's `input_snapshot_version` default embeds
`world_index`/`entity_id` (`python/rl/runtime/world_batch/adapter.py:448`),
and the packet-provenance id/version strings embed the numeric
`snapshot_version` (`runtime_facade_packet.cpp:204-211`, `:317-320`,
`:331-334`); see section 3.)

### 1.1 `uint64` identity fields

Semantics legend: **epoch-monotone** = increases within a single
event-store epoch but resets to `1` on `clear()` / event-clock rewind;
**batch-local** = assigned within one export/batch and not stable across
exports; **copy/ref** = copied from or referencing another field's value.

| Field | DTO — `file:line` | Type | Producer (`file:line`) | Consumer / test pin | Semantics | VA |
|-------|-------------------|------|------------------------|---------------------|-----------|----|
| `trace_id` | `DiagnosticsTrace` — `diagnostics_trace.inc:6` | `std::uint64_t` | Kernel store mints `trace.trace_id = next_engagement_event_id_++` (`simulation_kernel_engagement_event_store.cpp:364` launch, `:750` effects); facade observation-export traces instead carry the caller tag cycled from `request.trace_ids` (`runtime_facade_packet.cpp:734`, `:828-831`) into `diagnostics_trace_from_track_packet` (`:368`) | `test_trace_replay_gates.py:196` (`trace_id > 0`, replay-sortable) | Kernel-minted values are epoch-monotone in the shared engagement-event id space; observation-export values are caller tags (maintained adapter placeholder `[1]`), so not unique | VA-1, VA-8 |
| `parent_trace_id` | `DiagnosticsTrace` — `diagnostics_trace.inc:7` | `std::uint64_t` | Hardcoded `0` on the facade observation-export literal (`runtime_facade_packet.cpp:369`); kernel store paths leave the declared default `0` | `test_diagnostics_trace_contract.py:202` (`parent_trace_id == 0`) | Always `0` today, so trace ancestry is single-level | VA-8 |
| `chain_id` | `DiagnosticsTrace` — `diagnostics_trace.inc:8` | `std::uint64_t` | Kernel launch: `= event_id` (`simulation_kernel_engagement_event_store.cpp:365`); kernel effects: `= launch_event_id`, falling back to `effects_event_id` (`:761`); observation export: `= trace_id`, i.e. the same caller tag (`runtime_facade_packet.cpp:370`) | `test_trace_replay_gates.py:197` (`chain_id == launch.event_id`) | Groups a trace to its originating event on kernel paths; equals the request tag on observation export | VA-1, VA-8 |
| `track_id` | `DiagnosticsTrace` — `diagnostics_trace.inc:9` | `std::uint64_t` | Observation export copies `= track.track_id` (`runtime_facade_packet.cpp:371`); the kernel launch-path trace leaves the declared default `0` (`simulation_kernel_engagement_event_store.cpp:363-368` sets no `track_id`) | — | Copy of the `TrackPacket` identity where present | copy/ref |
| `launch_request_id` | `DiagnosticsTrace` — `diagnostics_trace.inc:10` | `std::uint64_t` | `= event.request_id` (`simulation_kernel_engagement_event_store.cpp:366`); on the legacy launch path `request_id` itself is a copy of the minted `event_id` (`:348`) | `test_trace_replay_gates.py:198` | References a `LaunchEvent.request_id` (event-store id space) | copy/ref |
| `launch_event_id` | `DiagnosticsTrace` — `diagnostics_trace.inc:11` | `std::uint64_t` | `= event_id` (`simulation_kernel_engagement_event_store.cpp:367`) | `test_trace_replay_gates.py:194` (linkage) | References a `LaunchEvent.event_id` (event-store id space) | copy/ref |
| `effects_event_id` | `DiagnosticsTrace` — `diagnostics_trace.inc:13` | `std::uint64_t` | `next_engagement_event_id_++` (`simulation_kernel_engagement_event_store.cpp:747`) | — | Effects id from the event-store allocator | VA-8 |
| `damage_report_id` | `DiagnosticsTrace` — `diagnostics_trace.inc:14` | `std::uint64_t` | `next_engagement_event_id_++` (`simulation_kernel_engagement_event_store.cpp:748`) | — | Damage-report id from the event-store allocator | VA-8 |
| `track_id` | `TrackPacket` — `track_packet.inc:6` | `std::uint64_t` | `= contact.id` in `track_packet_from_observation_contact` (`runtime_facade_packet.cpp:343`) — the observation contact's entity id, **not** the event-store allocator | `test_trace_replay_gates.py:202` (`track_id > 0`) | Sensor-contact identity from the observation path | VA-1 |
| `entity_id` | `RuntimeCounterfactualSnapshot` — `runtime_counterfactual_snapshot.inc:11` | `std::uint64_t` | `= ref.entity_id` in `counterfactual_snapshot_from_runtime` (`runtime_facade_counterfactual.cpp:83`); seeds the worldline-id default string (`:460-461`) and the `deterministic_seed` default (`:466-467`) | `test_runtime_facade_counterfactual.py` | ECS entity id; the `uint64` whose digits are embedded into the string worldline-id space | VA-1 |
| `trace_ids` | `EngagementEventPacket` — `engagement_event_packet.inc:15` | `std::vector<std::uint64_t>` | Caller-supplied on the request; window coordinator defaults an empty list to `[index + 1]` (`runtime_window_coordinator_selection_helpers.h:89-93`); facade copies the request list onto the packet (`runtime_facade_packet.cpp:778`) and cycles it to tag traces (`:734`, `:828-831`); maintained adapter sets `[1]` (`python/rl/runtime/world_batch/adapter.py:436`) | `test_trace_replay_gates.py` (window path) | Request-side tagging list; placeholder `[1]` on the maintained path | VA-8 |
| `barrier_sequence` | `EngagementEventPacket` — `engagement_event_packet.inc:8` | `std::uint64_t` | Declared default `0`; the export paths write the constant `kExportBarrierSequence = 1` (`runtime_facade_internal.h:55`; applied in `apply_export_packet_metadata` `runtime_facade_packet.cpp:198` and `export_engagement_event_packet` `:780`) | `test_trace_replay_gates.py:241` pins the default-constructed `0` only | Declared default `0` vs production-path value `1`; a fixed export constant, independent of any allocator | VA-7 |
| `barrier_sequence` | `ReplayBarrierRef` — `counterfactual_replay_contract_types.h:19` | `std::uint64_t` | Caller-constructible (WP15 fixtures); experiment envelope sets `1` (`runtime_facade_counterfactual.cpp:127`); restore boundary sets `= snapshot.snapshot_version` (`:381`) | `test_replay_envelope_contracts.py` (WP15) | Replay barrier sequence number | VA-7 |

**Allocator scope.** The `next_engagement_event_id_` counter belongs to the
kernel engagement event store: it starts at `1`
(`simulation_kernel_engagement_event_store.h:63`), is reset to `1` by
`clear()` (`:1073`), and `clear()` is re-invoked by
`reset_if_event_clock_rewound` when the frame count regresses (`:274-279`).
It mints the event id for **every** kernel event family the store records:
launch (`simulation_kernel_engagement_event_store.cpp:345`; `request_id`
copied from it at `:348`), nearest-approach (`:385`), fuze-evaluation
(`:441`), warhead-mechanism (`:508`), spatial-coverage (`:531`),
component-load (`:554`), component-damage (`:576`), structural-breakup
(`:599`), platform-consequence (`:640`), and lifecycle-transition (`:705`) —
the lethality-chain families land these ids in
`LethalityChainHeader.event_id` (`lethality_chain_header.inc:8`, e.g. `:399`)
— plus the store-minted launch-trace `trace_id` (`:364`) and the
effects-damage path's `effects_event_id`/`damage_report_id`/
`platform_consequence_event_id`/`trace_id` quadruple minted consecutively at
`:747-750`. All of these share the one resettable counter and can collide
across resets. Outside the store: `TrackPacket.track_id` comes from the
observation contact (`contact.id`), packet `trace_ids` are caller tags
(window default `[index + 1]`), and `barrier_sequence` is a fixed export
constant — none of them draw from the event-store allocator.

### 1.2 `string` identity fields

| Field | DTO — `file:line` | Type | Producer (`file:line`) | Consumer / test pin | Semantics | VA |
|-------|-------------------|------|------------------------|---------------------|-----------|----|
| `source_node_id` | `DiagnosticsTrace` — `diagnostics_trace.inc:20` | `std::string` | Kernel store leaves the declared default `{}`; observation-export literal sets `kObservationExportNodeId` = `"observation_export.v1"` (`runtime_facade_packet.cpp:377`; constant `runtime_facade_internal.h:50`); recent/kernel traces get the matched stage node via `apply_export_trace_metadata` (`:225-227`, manifest-gated), called with launch/effects/observation node ids (`:497`, `:514-515`, `:520-521`, `:266-306`) | `test_trace_replay_gates.py:232` (field present) | Stage-node label (registered node id), not a run-unique identity | VA-1 |
| `export_node_id` | `DiagnosticsTrace` — `diagnostics_trace.inc:21` | `std::string` | Kernel store leaves `{}`; observation-export literal sets `"observation_export.v1"` (`runtime_facade_packet.cpp:378`); `apply_export_trace_metadata` sets it to `kObservationExportNodeId` (manifest-gated, `:228-230`) | `test_trace_replay_gates.py:233` (field present) | Export stage-node label | VA-1 |
| `worldline_id` | `RuntimeCounterfactualSnapshot` — `runtime_counterfactual_snapshot.inc:7` | `std::string` | Facade default `"worldline:runtime:<world_index>:<entity_id>"` when blank (`runtime_facade_counterfactual.cpp:460-461`); experiment path defaults `"worldline:baseline"`/`"worldline:branch"` (`:645`, `:656`); else caller-authored | `test_runtime_facade_counterfactual.py` | Facade-generated when blank; no cross-run scheme | VA-1 |
| `parent_worldline_id` | `RuntimeCounterfactualSnapshot` — `runtime_counterfactual_snapshot.inc:8` | `std::string` | Defaults to `worldline_id` when empty (`runtime_facade_counterfactual.cpp:463`) | `test_runtime_facade_counterfactual.py` | Single-level lineage by default | VA-1 |
| `fidelity_profile_id` | `RuntimeCounterfactualSnapshot` — `runtime_counterfactual_snapshot.inc:23` | `std::string` | `= fidelity_admission.backend_profile_id` (`runtime_facade_counterfactual.cpp:95`) — note it is filled from the admission's **backend** profile id | `test_runtime_facade_counterfactual.py` | Fidelity/backend profile label on the snapshot | VA-1 |
| `selected_stage_node_id` | `RuntimeCounterfactualSnapshot` — `runtime_counterfactual_snapshot.inc:25` | `std::string` | `= fidelity_admission.selected_stage_node_id` (`runtime_facade_counterfactual.cpp:97`); reused as the restore-boundary event-order `producer_node_id` when non-empty (`:390-392`) | `test_runtime_facade_counterfactual.py` | Stage-node label chosen by fidelity admission | VA-1 |
| `comparison_id` | `RuntimeWorldlineComparison` — `runtime_worldline_comparison.inc:8` | `std::string` | `"counterfactual:selected_slice"` or `":<branch_point_id>"` suffix (`runtime_facade_counterfactual.cpp:334-336`) | `test_runtime_facade_counterfactual.py` | Generated per branch call | VA-1 |
| `parent_worldline_id` | `RuntimeWorldlineComparison` — `runtime_worldline_comparison.inc:9` | `std::string` | `= parent.worldline_id` (`runtime_facade_counterfactual.cpp:337`) | — | Copy of the snapshot id | copy/ref |
| `branch_worldline_id` | `RuntimeWorldlineComparison` — `runtime_worldline_comparison.inc:10` | `std::string` | `= branch.worldline_id` (`runtime_facade_counterfactual.cpp:338`) | — | Copy of the snapshot id | copy/ref |
| `replay_envelope_id` | `ReplayEnvelope` — `counterfactual_replay_contract_types.h:38` | `std::string` | Caller-constructible; experiment envelope passes through `branch_request.replay_envelope_id` (`runtime_facade_counterfactual.cpp:109`); restore boundary synthesizes `"replay:facade:<worldline_id>"` (`:365-367`) | `test_replay_envelope_contracts.py` (WP15) | Caller-authored or facade-synthesized; not built from a real run | VA-1 |
| `run_id` | `ReplayEnvelope` — `counterfactual_replay_contract_types.h:39` | `std::string` | Caller-constructible; experiment envelope: `request.experiment_run_id` or default `"run:counterfactual_experiment"` (`runtime_facade_counterfactual.cpp:110-111`); restore boundary: `snapshot.worldline_id` or `"run:facade"` (`:368`) | `test_replay_envelope_contracts.py` | Run identity string | VA-1 |
| `episode_id` | `ReplayEnvelope` — `counterfactual_replay_contract_types.h:40` | `std::string` | Caller-constructible; experiment envelope: `request.setup_ref` or default `"episode:counterfactual_experiment"` (`runtime_facade_counterfactual.cpp:112-113`); restore boundary: `snapshot.barrier_id` or `"episode:facade"` (`:369`) | `test_replay_envelope_contracts.py` | Episode identity string | VA-1 |
| `event_id` | `ReplayEventOrderRef` — `counterfactual_replay_contract_types.h:25` | `std::string` | Caller-constructible; experiment envelope sets `= branch_request.branch_point_id` (`runtime_facade_counterfactual.cpp:135`); restore boundary sets `"event:<worldline_id>"` or `"event:facade"` (`:388-389`) | `test_replay_envelope_contracts.py` | **`event_id` is `std::string` here vs `std::uint64_t` in the kernel**; on the experiment path it actually carries a branch-point id | VA-1 |
| `producer_node_id` | `ReplayEventOrderRef` — `counterfactual_replay_contract_types.h:26` | `std::string` | Caller-constructible; experiment envelope sets the fixed `"observation_export.v1"` (`runtime_facade_counterfactual.cpp:136`); restore boundary sets `snapshot.selected_stage_node_id` or that same default (`:390-392`) | `test_replay_envelope_contracts.py` | Producer-node label | VA-1 |
| `branch_point_id` | `BranchPoint` — `counterfactual_replay_contract_types.h:54` | `std::string` | Caller-supplied on requests (e.g. `"replay:wp17f:0001"`); experiment branch-point builder copies `request.branch_request.branch_point_id` (`runtime_facade_counterfactual.cpp:152`); admission derives its `request_id` from it (`:246-248`) | `test_replay_envelope_contracts.py` (`make_branch_point_identity`) | Caller-authored; string-equality identity | VA-1, VA-5 |
| `replay_envelope_id` | `BranchPoint` — `counterfactual_replay_contract_types.h:55` | `std::string` | Caller-constructible; experiment builder copies `branch_request.replay_envelope_id` (`runtime_facade_counterfactual.cpp:153`) | `test_replay_envelope_contracts.py` | Cross-ref to a `ReplayEnvelope.replay_envelope_id` (string-equality) | VA-1, VA-5 |
| `baseline_worldline_id` | `WorldlineBranchMetadata` — `counterfactual_replay_contract_types.h:65` | `std::string` | Caller-constructible only; `src/**` has validators but no facade producer for this struct | `test_worldline_branch_metadata.py` | Metadata-only branch record | VA-1 |
| `parent_worldline_id` | `WorldlineBranchMetadata` — `counterfactual_replay_contract_types.h:66` | `std::string` | Caller-constructible only (validators, no facade producer) | `test_worldline_branch_metadata.py` | Metadata-only branch record | VA-1 |
| `child_worldline_id` | `WorldlineBranchMetadata` — `counterfactual_replay_contract_types.h:67` | `std::string` | Caller-constructible only (validators, no facade producer) | `test_worldline_branch_metadata.py` | Metadata-only branch record | VA-1 |
| `request_id` | `CounterfactualExperimentRequest` — `counterfactual_replay_contract_types.h:87` | `std::string` | Caller-constructible only; the facade experiment path takes `RuntimeExperimentRequest` and builds the admission directly (`runtime_facade_counterfactual.cpp:240-270`) | `test_counterfactual_admission.py` | Experiment-request identity | VA-1 |
| `baseline_worldline_id` | `CounterfactualExperimentRequest` — `counterfactual_replay_contract_types.h:88` | `std::string` | Caller-constructible only (see previous row); the admission's baseline comes from `branch_request.parent_worldline_id` (`runtime_facade_counterfactual.cpp:249`) | `test_counterfactual_admission.py` | Experiment baseline identity | VA-1 |
| `experiment_run_id` | `ExperimentEvidenceBridgeRecord` — `counterfactual_replay_contract_types.h:215` | `std::string` | Produced by `make_experiment_evidence_bridge_record` (`counterfactual_replay_experiment_validation.h:641`); the facade passes `request.experiment_run_id` or default `"experiment_run:runtime_facade.counterfactual"` (`runtime_facade_counterfactual.cpp:857-858`); also caller-constructible | `test_experiment_evidence_bridge.py` | Bridge experiment-run identity | VA-1 |
| `comparison_id` | `ExperimentEvidenceBridgeRecord` — `counterfactual_replay_contract_types.h:216` | `std::string` | Produced at `counterfactual_replay_experiment_validation.h:642`; facade passes `request.comparison_id` or the branch comparison's id (`runtime_facade_counterfactual.cpp:859-860`) | `test_experiment_evidence_bridge.py` | Cross-ref to a `RuntimeWorldlineComparison.comparison_id` | VA-1 |
| `replay_run_id` | `ExperimentEvidenceBridgeRecord` — `counterfactual_replay_contract_types.h:217` | `std::string` | `= replay_envelope.run_id` (`counterfactual_replay_experiment_validation.h:643`) | `test_experiment_evidence_bridge.py` | Bridge replay-run identity | VA-1 |
| `baseline_worldline_id` | `ExperimentEvidenceBridgeRecord` — `counterfactual_replay_contract_types.h:218` | `std::string` | `= admission.baseline_worldline_id` (`counterfactual_replay_experiment_validation.h:644`), which the facade fills from `branch_request.parent_worldline_id` (`runtime_facade_counterfactual.cpp:249`) | `test_experiment_evidence_bridge.py` | Bridge baseline identity | VA-1 |
| `variant_worldline_id` | `ExperimentEvidenceBridgeRecord` — `counterfactual_replay_contract_types.h:219` | `std::string` | `= admission.child_worldline_id` (`counterfactual_replay_experiment_validation.h:645`), filled from `branch_request.branch_worldline_id` (`runtime_facade_counterfactual.cpp:250`) | `test_experiment_evidence_bridge.py` | Bridge variant identity | VA-1 |
| `request_id` | `ScenarioGenerationRequestMetadata` — `counterfactual_replay_contract_types.h:183` | `std::string` | Produced by the facade experiment path: `generated_input_ref`/`generation_ref` or default `"scenario-gen:runtime_facade.counterfactual"` (`runtime_facade_counterfactual.cpp:187-191`); also caller-constructible (parallel Python surface `python/scenario/compiler/generation_request.py`) | `python/scenario/compiler/generation_request.py` | Generation-request identity | VA-1, VA-6 |

### 1.3 Untyped ancestry references (`*_ref`)

`RuntimeExperimentAncestry`
(`src/runtime/facade/detail/runtime_experiment_ancestry.inc`) carries all
lineage as free `std::string` refs with no typed link to the `_id` they name
(matching is string-equality). These are the serialization form and are listed
here so a later slice can add a "ref → id-kind" registry (VA-5) additively.

| Field | `file:line` | Type | Names id-kind | VA |
|-------|-------------|------|---------------|----|
| `counterfactual_request_ref` | `runtime_experiment_ancestry.inc:11` | `std::string` | `CounterfactualExperimentRequest.request_id` | VA-5 |
| `counterfactual_admission_ref` | `runtime_experiment_ancestry.inc:12` | `std::string` | `CounterfactualAdmissionResult.request_id` | VA-5 |
| `setup_ref` | `runtime_experiment_ancestry.inc:13` | `std::string` | setup identity | VA-5 |
| `generation_ref` | `runtime_experiment_ancestry.inc:14` | `std::string` | generation identity | VA-5 |
| `replay_envelope_ref` | `runtime_experiment_ancestry.inc:15` | `std::string` | `ReplayEnvelope.replay_envelope_id` | VA-5 |
| `branch_point_ref` | `runtime_experiment_ancestry.inc:16` | `std::string` | `BranchPoint.branch_point_id` | VA-5 |
| `generated_input_ref` | `runtime_experiment_ancestry.inc:17` | `std::string` | generated-input identity | VA-5 |
| `backend_profile_ref` | `runtime_experiment_ancestry.inc:18` | `std::string` | backend-profile identity | VA-5 |
| `fidelity_profile_ref` | `runtime_experiment_ancestry.inc:19` | `std::string` | fidelity-profile identity | VA-5 |

## 2. Version Concepts

Two distinct concepts both use the `version` suffix (VA-3): a **state-slice
version** (which slice of produced state a packet/trace corresponds to) and a
**format/schema version** (which contract/format the payload conforms to). They
must not be conflated.

### 2.1 State-slice version fields (VA-2)

Producer note: `next_snapshot_version(index)` returns `index + 1` as a pure
function (`runtime_facade_packet.cpp:574`, `runtime_facade_execution.cpp:27`).
It is used for the observation/tasking packet top-level version
(`= next_snapshot_version(refs.size() - 1) = refs.size()`;
`runtime_facade_packet.cpp:865`, `:896`) and the per-step version
(`= next_snapshot_version(step_index)`; `runtime_facade_execution.cpp:164`).
The per-`TrackPacket` version comes from a **separate local counter** that
starts at `1` and increments per ref within one export
(`runtime_facade_packet.cpp:728-732`, `:817-821`). **No run-global monotone
snapshot counter exists today.**

| Field | DTO — `file:line` | Type | Producer / value | Uniqueness / monotonicity | VA |
|-------|-------------------|------|------------------|---------------------------|----|
| `snapshot_version` | `TrackPacket` — `track_packet.inc:19` | `std::uint64_t` | Local per-ref counter from `1` (`runtime_facade_packet.cpp:732`, `:821`); declared default `0` | Batch-local; resets to `1` each export; not monotone | VA-2 |
| `snapshot_version` | `ObservationBatchPacket` — `observation_batch_packet.inc:7` | `std::uint64_t` | `= refs.size()` (`runtime_facade_packet.cpp:865`); declared default `0` | Equals the batch ref count; not monotone | VA-2 |
| `snapshot_version` | `EngagementEventPacket` — `engagement_event_packet.inc:6` | `std::uint64_t` | `resolve_engagement_snapshot_version` = max of track/trace versions, else `refs.size()` (`runtime_facade_packet.cpp:641-654`; applied via `apply_export_packet_metadata` `:196`, callers `:808-809`, `:840-841`) | Derived per export; not monotone | VA-2 |
| `snapshot_version` | `RuntimeCounterfactualSnapshot` — `runtime_counterfactual_snapshot.inc:21` | `std::uint64_t` | Fixed constant `kRuntimeCounterfactualSelectedSliceSnapshotVersion = 1` (`runtime_facade_internal.h:89`; applied `runtime_facade_counterfactual.cpp:93`); declared default `0` | Always `1` on the production path | VA-2 |
| `snapshot_version` | `TerminationSpec` — `termination_spec.inc:8` | `std::uint64_t` | `termination_spec_from_step_result` sets it (`runtime_facade_execution.cpp:104`) from the per-step `next_snapshot_version(step_index)` (`:164`, used `:176`) | Per-step slice tag; resets with step indexing | VA-2 |
| `observation_packet_version` | `DiagnosticsTrace` — `diagnostics_trace.inc:15` | `std::uint64_t` | Passed as the per-ref snapshot version into the export-trace literal (`runtime_facade_packet.cpp:372`) | Batch-local | VA-2 |
| `source_snapshot_version` | `DiagnosticsTrace` — `diagnostics_trace.inc:16` | `std::uint64_t` | `= track.snapshot_version` on observation export (`runtime_facade_packet.cpp:373`); `apply_export_trace_metadata` re-stamps it (`:221`) on recent/kernel traces | Batch-local | VA-2 |
| `source_snapshot_version` | `RuntimeWindowNodeExecutionRecord` — `runtime_window_node_execution_record.inc:17` | `std::string` | Window coordinator copies the action request's `clock_domain_metadata.source_snapshot_version`, falling back to its `input_snapshot_version` (`runtime_window_coordinator_helpers.h:87-93`; applied e.g. `runtime_window_coordinator_execution_helpers.h:77-78`); the export record uses `runtime_window_export_snapshot_evidence` (`runtime_window_coordinator.h:345`) | **Type split: `std::string` here vs `std::uint64_t` in `DiagnosticsTrace`** | VA-2 |
| `fact_snapshot_version` | `RewardReport` — `reward_report.inc:8` | `std::uint64_t` | `reward_report_from_step_result` sets it (`runtime_facade_execution.cpp:46`) from the per-step version (`:164`, used `:180`) | Per-step reward slice tag | VA-2 |
| `snapshot_version_ref` | `ReplaySnapshotRef` — `counterfactual_replay_contract_types.h:14` | `std::string` | Caller-constructible; experiment envelope: `request.setup_ref` or `"snapshot:counterfactual_experiment"` (`runtime_facade_counterfactual.cpp:120-122`); restore boundary: `"snapshot:" + std::to_string(snapshot.snapshot_version)` (`:376`) — embedding the fixed `uint64` `1` | String ref; not bound to any produced `uint64` version by type | VA-2, VA-5 |
| `snapshot_version_ref` | `BranchPoint` — `counterfactual_replay_contract_types.h:56` | `std::string` | Caller-constructible; experiment branch-point builder copies the envelope's ref (`runtime_facade_counterfactual.cpp:154`) | String ref; not bound to any produced `uint64` version by type | VA-2, VA-5 |
| `input_snapshot_version` | `RuntimeWindowActionRequest` — `runtime_facade_types.h:192` (Python param `python/rl/runtime/world_batch/adapter.py:322`, `:400`) | `std::string` / `str` | Adapter default `"obs:{world}:{entity}"` (`adapter.py:448`); flows to `source_observation_versions = [str(...)]` (`:361`) and into window records via `runtime_window_input_source_snapshot_version` (`runtime_window_coordinator_helpers.h:87-93`) | Synthetic string; not a produced version | VA-2 |

### 2.2 Format / schema version fields (VA-3)

| Field | DTO / owner — `file:line` | Type | Value | VA |
|-------|---------------------------|------|-------|----|
| `schema_version` | `ObservationViewSpec` — `observation_view_spec.inc:7` | `std::string` | `"1.0"`; parsed as `major.minor` by `parse_observation_schema_version` (`runtime_dto_contracts.h:40`) | VA-3 |
| `schema_version` | `LethalityChainHeader` — `lethality_chain_header.inc:6` | `std::uint32_t` | Default `kLethalityChainContractSchemaVersion` = `1` (constant at `engagement_contracts.h:10`) | VA-3 |
| `schema_version` | `KillChainRuntimeFacade` — `kill_chain_runtime_facade.inc:7` | `std::uint32_t` | Default `1` | VA-3 |
| `vulnerability_evidence_schema_version` | `EffectsEvent` — `effects_event_fields.inc:127`; same-named field on `EffectsResult` — `effects_model.h:77` | `std::string` | Copied from the sampled `VulnerabilityAdjustment.evidence_schema_version` (`default_effects_result_detail.inc:195-196`) | VA-3 |
| `evidence_schema_version` | `AircraftVulnerabilityProfile` — `damage_air.h:72`; `VulnerabilityAdjustment` — `default_effects_warhead_detail.inc:104` | `std::string` | Loader fills the profile from the content descriptor's `schema_version` (`unit_definition_loader.cpp:754`); copied profile → adjustment (`default_effects_warhead_detail.inc:1063`) → result (`default_effects_result_detail.inc:195-196`) | VA-3 |
| `request_version` | `ScenarioGenerationRequestMetadata` — `counterfactual_replay_contract_types.h:184` | `std::string` | `"1"` (declared; facade experiment path also writes `"1"`, `runtime_facade_counterfactual.cpp:192`) | VA-3 |
| `contract_version` | `ScenarioGenerationRequestMetadata` — `counterfactual_replay_contract_types.h:185` | `std::string` | `kScenarioGenerationContractVersionRequestV1` (declared; re-stamped by the facade, `runtime_facade_counterfactual.cpp:193`) | VA-3 |
| `envelope_schema_version` | report envelope — `python/experiment/report_envelope.py:45` (`ENVELOPE_SCHEMA_VERSION`), emitted `:113` | `str` | `"1"` | VA-3 |

### 2.3 Concept → representation mapping (VA-2, VA-3)

| Concept | Representations (name @ type) | Monotone today? | Notes |
|---------|-------------------------------|-----------------|-------|
| State-slice version (which produced slice) | `snapshot_version` @ `uint64`; `observation_packet_version` @ `uint64`; `source_snapshot_version` @ `uint64` (`DiagnosticsTrace`) / `std::string` (`RuntimeWindowNodeExecutionRecord`); `fact_snapshot_version` @ `uint64`; `snapshot_version_ref` @ `string`; `input_snapshot_version` @ `string` | No | ≥5 names, 2 types; per-export/batch-local or fixed `1`; no run-global monotone counter |
| Format / schema version (which contract/format) | `schema_version` @ `string` `"1.0"` (`ObservationViewSpec`) / `uint32` (`LethalityChainHeader`, `KillChainRuntimeFacade`); `evidence_schema_version`/`vulnerability_evidence_schema_version` @ `string`; `request_version`/`contract_version` @ `string`; `envelope_schema_version` @ `str` | n/a | Discrete contract labels; `*_schema_version`/`*_contract_version` = format, `*_snapshot_version`/`*_packet_version` = state-slice |

## 3. Id-Space Coexistence And Collision Risk (VA-1, VA-3)

- **Two disjoint representations, no typed bridge field.** "Identity for
  replay/diagnostics" is `std::uint64_t` on the trace/engagement/packet surface
  (section 1.1) and `std::string` on the worldline/replay/experiment surface
  (section 1.2). No typed field converts between them; the crossings are
  textual number-into-string embeddings at several points, for example: the
  worldline-id default embeds `world_index`/`entity_id`
  (`runtime_facade_counterfactual.cpp:460-461`), the restore-boundary
  `snapshot_version_ref` embeds `snapshot_version` (`:376`), the adapter's
  `input_snapshot_version` default embeds `world_index`/`entity_id`
  (`python/rl/runtime/world_batch/adapter.py:448`), and the packet-provenance
  `observation_packet_ids`/`source_observation_versions` strings embed the
  numeric `snapshot_version` (`runtime_facade_packet.cpp:204-211` engagement,
  `:317-320` observation, `:331-334` tasking). SCAL names one
  `source_id` ("stable producer id for replay and diagnostics") that no single
  type realizes. A later slice may declare a bridging ref field or an id-kind
  registry additively (VA-1, VA-5); this glossary only documents the split.
- **Same name, different type.** `event_id` is `std::uint64_t` in the kernel
  (`LaunchEvent`/`EffectsEvent`, referenced by `DiagnosticsTrace.launch_event_id`
  / `effects_event_id`) but `std::string` in `ReplayEventOrderRef`
  (`counterfactual_replay_contract_types.h:25`) — where the experiment path
  actually stores a branch-point id (`runtime_facade_counterfactual.cpp:135`).
  `source_snapshot_version` is `std::uint64_t` in `DiagnosticsTrace` but
  `std::string` in `RuntimeWindowNodeExecutionRecord`. Cross-surface joins on
  these names are therefore not type-safe.
- **The kernel event-store ids share one resettable allocator.** Within the
  store-minted set (section 1.1: the event ids of all recorded kernel event
  families — launch, nearest-approach, fuze-evaluation, warhead-mechanism,
  spatial-coverage, component-load/damage, structural-breakup,
  platform-consequence, lifecycle-transition, effects/damage — and the
  store-minted trace ids), all values are drawn from
  `next_engagement_event_id_`, which resets to `1` on `clear()` / clock rewind.
  Two runs (or one run after a rewind) can mint identical values, so these ids
  are not stable across resets and must not be treated as globally unique.
  Collision risk is even more direct for the caller-tag ids: the maintained
  adapter tags every observation-export trace with `[1]`.
- **String ids are facade-generated or caller-authored.** Worldline/comparison
  ids and the restore-boundary refs are facade-generated within one raw-facade
  call (section 1.2); the experiment-path envelope mostly passes caller fields
  through with fixed fallbacks (`run:counterfactual_experiment`,
  `episode:counterfactual_experiment`); `branch_point_id`, the request
  `replay_envelope_id`, and the branch-metadata worldline ids remain
  caller-authored strings. There is no cross-run stable id scheme, so
  string-space uniqueness is only per-call/per-author.

## 4. Barrier-Id Vocabulary (VA-7)

`barrier_id` is consistently `std::string` but its defaults differ by DTO; the
census attributes `"window_commit"` to `barrier_id`, but at baseline `1d25c4d1`
it is the **`barrier_detail`** default of `ReplayBarrierRef` — `barrier_id`
there has no default (see section 5 census discrepancies). The declared
defaults and the production-path writes agree on the export surface (the
constants `kExportBarrierId`/`kExportBarrierDetail` repeat the declared
defaults, `runtime_facade_internal.h:53-54`).

| Field | DTO — `file:line` | Declared default | Production-path write |
|-------|-------------------|------------------|-----------------------|
| `barrier_id` | `DiagnosticsTrace` — `diagnostics_trace.inc:17` | `"export"` | `kExportBarrierId` = `"export"` (`runtime_facade_packet.cpp:222`, `:374`) |
| `barrier_id` | `ObservationBatchPacket` — `observation_batch_packet.inc:8` | `"export"` | `"export"` (`runtime_facade_packet.cpp:852`) |
| `barrier_id` | `EngagementEventPacket` — `engagement_event_packet.inc:7` | `"export"` | `kExportBarrierId` (`runtime_facade_packet.cpp:197`, `:779`) |
| `barrier_id` | `RuntimeCounterfactualSnapshot` — `runtime_counterfactual_snapshot.inc:22` | `"counterfactual_selected_slice"` | `kRuntimeCounterfactualSelectedSliceBarrierId` (`runtime_facade_internal.h:87-88`; applied `runtime_facade_counterfactual.cpp:94`) |
| `barrier_id` | `RuntimeWorldlineComparison` — `runtime_worldline_comparison.inc:11` | `"counterfactual_selected_slice"` | Same constant (`runtime_facade_counterfactual.cpp:339`) |
| `barrier_id` | `ReplayBarrierRef` — `counterfactual_replay_contract_types.h:18` | none (empty) | Experiment: `branch_request.restore_barrier_id` (`runtime_facade_counterfactual.cpp:126`); restore boundary: `snapshot.barrier_id` (`:380`) |
| `barrier_detail` | `ReplayBarrierRef` — `counterfactual_replay_contract_types.h:20` | `"window_commit"` | Experiment: `cadence_reason` or `"maintained_facade_export"` (`runtime_facade_counterfactual.cpp:128-130`); restore boundary similar (`:382-383`) |
| `barrier_detail` | `DiagnosticsTrace` / `EngagementEventPacket` — `diagnostics_trace.inc:18` / `engagement_event_packet.inc:9` | `"maintained_facade_export"` | `kExportBarrierDetail` (`runtime_facade_packet.cpp:223` / `:199`, `:781`) |

## 5. Census Discrepancies (for coordinator)

The census (`t10_evidence_spine_census_20260721.md`) is retained as an
immutable historical record; this glossary does not edit it. Two minor
imprecisions were found while re-verifying and are recorded here for the
coordinator to adjudicate:

1. **`RuntimeExperimentAncestry` field names.** Census §1(ii) writes the
   evidence-bridge fields as `evidence_bridge_valid`/`fail_closed`/
   `rejection_reason`/`errors`. The actual field names carry the
   `evidence_bridge_` prefix: `evidence_bridge_valid`
   (`runtime_experiment_ancestry.inc:7`), `evidence_bridge_fail_closed` (`:8`),
   `evidence_bridge_rejection_reason` (`:9`), `evidence_bridge_errors` (`:10`).
2. **`ReplayBarrierRef` `"window_commit"`.** Census §2 VA-7 attributes the
   `"window_commit"` default to `barrier_id`. At `1d25c4d1` `ReplayBarrierRef.barrier_id`
   has no default; `"window_commit"` is the default of `barrier_detail`
   (`counterfactual_replay_contract_types.h:20`).

Neither affects the census's conclusions; both are documented correctly in this
glossary (sections 1.2, 4).

## 6. Non-Goals

- **Zero code change; zero field change.** This slice is documentation only. It
  adds no field, renames nothing, retypes nothing, and touches no `src/**`,
  `python/**`, `examples/**`, or existing test.
- **Optional schema-metadata sub-task declined.** The census slice permits an
  optional documentation-only schema annotation. It was assessed and declined
  on scope grounds: the current `Field` model
  (`tools/maintenance/dto_schema/model.py:19-31`, a `frozen=True, slots=True`
  dataclass) has no semantically fitting existing channel for evidence
  vocabulary — the free-text `comment` is rendered into the generated `.inc`
  output (`tools/maintenance/dto_schema/generate.py:58-63`) and so would change
  checked-in artifacts, while the reserved keys are binding/serialization
  metadata (`readonly` changes the generated Python builder,
  `python_builder.py:100-102`; `python_name`/`hidden`/`json_key` carry
  binding/codec semantics). Adding a new dedicated annotation attribute (for
  example `evidence_role`) could be made output-neutral, but it requires
  editing the model/generator code (the fixed dataclass attribute set rejects
  unknown keywords with `TypeError`), which is a generator code change outside
  this slice's zero-code-change red line. The sub-task therefore ships as
  documentation only; a later slice may add the attribute together with its
  freshness-gate evidence.
- **Additive-only red line** (copied from census §3, unchanged):
  - No existing evidence field may be renamed, retyped, removed, or reordered.
    Member order is ABI; JSON codec aliases and retained-artifact hashes pin the
    serialized shape; the tests in the census section 1 pin the surface.
  - New evidence arrives as new fields / DTOs / producers with regeneration
    freshness gates (`tools/maintenance/dto_schema/generate.py --check`) and
    embedded-reference parity where behavior could drift; compatibility shells
    are retained until the T7 final residual audit retires them deliberately.
  - Vocabulary alignment is delivered as documentation plus new additive
    fields, never as in-place edits to the pinned surfaces.

## 7. Coverage Totals

- `uint64` identity fields: 13 (section 1.1).
- `string` identity fields: 27 (section 1.2).
- Untyped ancestry refs: 9 (section 1.3).
- State-slice version fields: 12 (section 2.1).
- Format/schema version fields: 8 (section 2.2).
- **Total documented id/ref/version fields: 69.**

## Related Authority

- [Unified Architecture Program](README.md) (T10 track definition and risk)
- [T10 Evidence Spine Census (2026-07-21)](t10_evidence_spine_census_20260721.md) (slice 1; VA-1..VA-8 and the additive red line)
- [Simulation System Architecture Design](../architecture/simulation_system_architecture_design.md) (SCAL Evidence Graph face)
- [SCAL Conformance Census (2026-07-20)](scal_conformance_census_20260720.md) (census format precedent)
- [T6 Residual Ledger (2026-07-20)](t6_residual_ledger.md)
- [Repository Consolidation Plan](../repository_consolidation/README.md) (iteration ledger and protocol)
