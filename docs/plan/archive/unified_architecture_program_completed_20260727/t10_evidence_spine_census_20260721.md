# T10 Evidence Spine Census (2026-07-21)

Language:
- English canonical: `t10_evidence_spine_census_20260721.md`
- Chinese companion: [t10_evidence_spine_census_20260721.zh.md](t10_evidence_spine_census_20260721.zh.md)

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/plan/archive/unified_architecture_program_completed_20260727/t10_evidence_spine_census_20260721.md`
Owner: `unified architecture program workline`
Last verified: `2026-07-21`
Baseline commit: `8bd21d86`

Status: T10 first-slice evidence-surface census for the
[Unified Architecture Program](README.md). T10's charter is to "unify trace
ids, packet ancestry, snapshot versions, replay gates, and the
worldline/counterfactual surfaces into one evidence architecture generated
from the T1 event schemas", with the primary target that "any maintained run
is replayable and comparable by construction" and the key risk that "evidence
surfaces are pinned by tests and retained artifacts; extension must be
additive". This document is a descriptive census register (`reference`), not
an independent review: it records the verified baseline state and carries no
review verdict. It changes no behavior and no `src/**`/`python/**` code; it
inventories what exists so later T10 slices can extend additively. Vocabulary
follows the SCAL Evidence Graph face in
[Simulation System Architecture Design](../../../architecture/standards/simulation_system_architecture_design.md)
(section 2, Evidence Graph: "Trace ids, packet ancestry, snapshot versions,
event order, and validation verdicts").

## 0. Method And Scope

- Surveyed the maintained surface (`src/**` read-only, `python/**`,
  `tools/maintenance/dto_schema/**`, `tests/**`) at baseline `8bd21d86`.
- The five evidence-relevant DTO families are schema single-sourced under
  `tools/maintenance/dto_schema/schemas/` (T1, I26/I31): `diagnostics_trace`,
  `track_packet`, `observation_batch_packet`, `engagement_event_packet`,
  `runtime_counterfactual_snapshot`, `runtime_worldline_comparison`,
  `runtime_experiment_ancestry`, `runtime_experiment_request/result`,
  `runtime_counterfactual_branch/restore_request/result`, plus the C++
  contract types in `src/runtime/contracts/counterfactual_replay_contract_types.h`.
- The report envelope landed by I44 (`python/experiment/report_envelope.py`)
  deliberately carries only generic metadata (`envelope_schema_version`,
  `tool_id`, `generated_at`, `git_rev`, `experiment_ref`, `payload`) and
  explicitly leaves trace/ancestry mechanics to T10; it is included below as a
  boundary marker, not as an evidence producer.
- Zero behavior change. No optional read-only architecture test was added:
  the five surfaces are already pinned by existing tests (see each row) — most
  smoke-gated, but the packet `snapshot_version`/view-spec facts only by the
  non-smoke `test_runtime_dto_contracts.py` — and a new pin would either
  duplicate them or cement the placeholder state that T10 must replace.
  Decision recorded in section 4.

## 1. Evidence-Surface Census

### (i) Trace ids

| Aspect | Finding |
|--------|---------|
| Existing vocabulary | `DiagnosticsTrace`: `trace_id`, `parent_trace_id`, `chain_id`, `track_id`, `launch_request_id`, `launch_event_id`, `effects_event_id`, `damage_report_id` (all `std::uint64_t`), plus `observation_packet_version`/`source_snapshot_version` (`std::uint64_t`), `barrier_id`/`barrier_detail`, `source_node_id`/`export_node_id`. `EngagementEventPacket.trace_ids` is `std::vector<std::uint64_t>`. `TrackPacket`: `track_id` (`std::uint64_t`), `correlation_policy` (`"unresolved"`), `correlated_entity`/`has_correlated_entity`. |
| Producers | Kernel: `simulation_kernel_engagement_event_store.cpp` mints `trace.trace_id = next_engagement_event_id_++` (monotone within a single event-store epoch only — `next_engagement_event_id_` starts at `1` and is reset to `1` by `clear()` and by `reset_if_event_clock_rewound` on a frame/clock rewind, so it is not globally monotone across resets — and drawn from the *engagement-event* id space). Facade: `runtime_facade_packet.cpp` builds `DiagnosticsTrace{.trace_id = trace_id, .parent_trace_id = 0}` — `parent_trace_id` is hardcoded `0` on the export path — and cycles `request.trace_ids` to tag exported observation traces. `runtime_window_coordinator_selection_helpers.h` defaults empty `trace_ids` to `[index + 1]`. |
| Consumers | Maintained Python path `python/rl/runtime/world_batch/adapter.py` sets `engagement_request.trace_ids = [1]` (placeholder constant) and does not read the produced `trace_id`/`chain_id`. No maintained Python run consumes the trace chain for replay/comparison. |
| Test pinning | `tests/runtime/engagement/test_diagnostics_trace_contract.py` (1 test, trace chain linkage); `tests/runtime/engagement/test_trace_replay_gates.py` (2 tests, replay-sortable ids, `chain_id == event_id`, version metadata explicit/separate) — both smoke-gated. Also `tests/runtime/bindings/test_bindings_engagement_surface.py`, `tests/tools/test_target_geometry_damage_event_trace.py`. |
| Gap vs replayable-by-construction | Kernel produces a `trace_id` that is monotone only within one event-store epoch (reset by `clear()`/clock rewind), but `parent_trace_id` is never populated on the facade export path (always `0`) so trace *ancestry* is single-level (`chain_id == event_id` only); and the maintained Python consumer tags traces with a placeholder `[1]`, so real kernel ids are not wired end-to-end. `trace_id` shares the engagement-event id space and has no link to the string-id worldline/replay surface. |

### (ii) Packet ancestry (`InformationStateSource` / provenance)

| Aspect | Finding |
|--------|---------|
| Existing vocabulary | `InformationStateSource` (in `policy_contracts.h`/`information_transform_contracts.h`), built by `make_information_state_source(information_state, source_label, maintained_status)` over enums `kPolicyInformationState*` (Truth/Sensed/Track/Picture/AgentObservation/DecisionBelief), `kPolicySourceLabel*`, `kPolicyMaintainedStatus*` (Maintained/DiagnosticsOnly/AdapterProjection). The typed provenance field appears under six different names: `ObservationBatchPacket.provenance`, `EngagementEventPacket.packet_provenance` + `diagnostics_provenance`, `ReplayFacadeProvenanceRef.information_state_source`, `WorldlineBranchMetadata.source_information_state`, `CounterfactualExperimentRequest.authority_information_state`. `RuntimeExperimentAncestry` carries all-string `*_ref` lineage (`setup_ref`, `generation_ref`, `replay_envelope_ref`, `branch_point_ref`, `generated_input_ref`, `counterfactual_request_ref`, `counterfactual_admission_ref`, `backend_profile_ref`, `fidelity_profile_ref`) plus `capability_refs`/`profile_observation_refs`/`evidence_refs` and `evidence_bridge_valid`/`fail_closed`/`rejection_reason`/`errors`. |
| Producers | C++ facade: `run_counterfactual_experiment` emits `RuntimeExperimentAncestry`; each packet defaults its provenance via `make_information_state_source`. Python adapter builds `AgentRole.information_state_source` with `source_observation_versions = [str(input_snapshot_version)]` (a synthetic string). |
| Consumers | Provenance is enforced by tests and by the maintained window-authorization path (`run_maintained_window` requires labeled provenance + `AgentRole` authorization). `python/scenario/compiler/generation_request.py` re-implements the lineage vocabulary (`replay_envelope_ref`/`branch_point_ref`/`evidence_refs`/`deterministic_seed`) as a **parallel Python surface**. No maintained run consumes `RuntimeExperimentAncestry`. |
| Test pinning | `tests/architecture/policy_execution/test_belief_and_read_side_boundaries.py` (13 tests, WP11/WP12/WP24 provenance vocabulary + maintained-provenance requirement); `tests/architecture/policy_execution/test_information_transformation_surface.py`; `tests/runtime/engagement/test_facade_engagement_evidence_gates.py` (smoke); `tests/architecture/causal_runtime/test_experiment_evidence_bridge.py` (5 tests); `tests/runtime/facade/test_runtime_facade_counterfactual.py` (ancestry assertions). |
| Gap vs replayable-by-construction | Same type (`InformationStateSource`) has six field names; ancestry references are free `std::string` `*_ref` values with no typed link to the `_id` they name (matching is string-equality); the lineage vocabulary is implemented twice (C++ contract types and Python `generation_request.py`); and no maintained training/eval run produces packet ancestry end-to-end. |

### (iii) Snapshot versions

| Aspect | Finding |
|--------|---------|
| Existing vocabulary (two conflated concepts) | **State-slice version:** `snapshot_version` (`std::uint64_t`) on `TrackPacket`, `ObservationBatchPacket`, `EngagementEventPacket`, `RuntimeCounterfactualSnapshot`; `source_snapshot_version` — `std::uint64_t` in `DiagnosticsTrace` but `std::string` in `RuntimeWindowNodeExecutionRecord`; `observation_packet_version` (`std::uint64_t`, `DiagnosticsTrace`); `snapshot_version_ref` (`std::string`, `ReplaySnapshotRef`/`BranchPoint`); `fact_snapshot_version` (`RewardReport`), `snapshot_version` (`TerminationSpec`); Python adapter `input_snapshot_version` (string, default `"obs:{world}:{entity}"`). **Format/schema version:** `schema_version` = `std::string` `"1.0"` (`ObservationViewSpec`, parsed by `parse_observation_schema_version`) vs `std::uint32_t` (`lethality_chain_header`, `kill_chain_runtime_facade`); `envelope_schema_version` = `"1"` (report envelope); `contract_version`/`request_version` (scenario generation); `evidence_schema_version` (effects vulnerability). |
| Producers | The C++ facade sets packet `snapshot_version` from `next_snapshot_version(index)`, which returns `index + 1` — a per-export-batch sequence number that **resets to `1` on every export** (each export loop restarts a local `next_snapshot_version = 1`; `runtime_facade_execution.cpp` does the same per step index), not a run-global monotone counter; the counterfactual snapshot's `snapshot_version` is the **fixed constant** `kRuntimeCounterfactualSelectedSliceSnapshotVersion = 1`. Python adapter produces a **string** synthetic `input_snapshot_version`. `ObservationViewSpec` compatibility is computed by `evaluate_observation_view_checkpoint_compatibility` over parsed `schema_version`. |
| Consumers | `ObservationViewSpec` checkpoint-compatibility engine (major/minor drift); tests. |
| Test pinning | `tests/architecture/runtime_facade/test_runtime_dto_contracts.py` (versioned view spec + packet `snapshot_version` fields; **not in smoke**); `tests/runtime/engagement/test_trace_replay_gates.py` (track `snapshot_version > 0`, versions kept separate); `tests/architecture/governance/test_dto_schema_freshness.py` (smoke, all schema-owned DTOs regenerate). |
| Gap vs replayable-by-construction | `source_snapshot_version` is `std::uint64_t` in one DTO and `std::string` in another (type inconsistency); the state-slice and format-schema concepts both use the `version` suffix with no naming discipline (`observation_schema_version` vs `observation_packet_version`/`snapshot_version` are easily confused); the string `snapshot_version_ref` in the replay contract is not bound to the `std::uint64_t` `snapshot_version` on packets, so a replay envelope cannot reference an actually-produced packet version by construction. |

### (iv) Replay gates

| Aspect | Finding |
|--------|---------|
| Existing vocabulary | `ReplayEnvelope` (`replay_envelope_id`, `run_id`, `episode_id`, `deterministic_seed` `std::uint64_t`, `source_time_s`, `snapshot_ref`, `barrier_ref`, `event_order_ref`, `facade_provenance_ref`, `snapshot_restore_supported`, `restore_support_boundary`); `ReplaySnapshotRef.snapshot_version_ref`; `ReplayBarrierRef` (`barrier_id`, `barrier_sequence`, `barrier_detail`); `ReplayEventOrderRef` (`sort_key`, `event_id`, `producer_node_id`); `ReplayFacadeProvenanceRef` (`packet_ref`, `packet_kind`, `information_state_source`); `BranchPoint`. Validators: `validate_replay_envelope`, `validate_branch_point`, `validate_branch_point_against_replay_envelope`, `make_branch_point_identity`, `ordered_replay_envelope_evidence_refs`, `validate_replay_envelope_for_snapshot_restore`. Restore boundaries `kReplayRestoreSupportBoundary*` (`Unsupported`, `HostOwnedFacadeStateOnly`); rejection constants `kReplayEnvelopeRejection*`/`kBranchPointRejection*`; sort key `kDeterministicReplayEventOrderSortKey`. |
| Producers | The maintained `RuntimeFacadeAdapter`/live-run path has no `ReplayEnvelope`/`BranchPoint` producer. The raw counterfactual facade **does** construct `ReplayEnvelope`s at two production code points — `replay_envelope_from_experiment_request()` (`runtime_facade_counterfactual.cpp`, from a caller's experiment/branch request) and `runtime_counterfactual_restore_boundary_for_snapshot()` (from a `RuntimeCounterfactualSnapshot`) — but these are **synthetic** envelopes assembled from request/snapshot fields, not built from a maintained run's real packet evidence (packet `snapshot_version` + event order + provenance). Test fixtures also build envelopes with hand-authored string ids. |
| Consumers | C++ validators (fail-closed); `python/scenario/compiler/generation_request.py` requires `replay_envelope_ref` or `branch_point_ref`. No maintained Python run builds or consumes a `ReplayEnvelope`. |
| Test pinning | `tests/architecture/causal_runtime/test_replay_envelope_contracts.py` (7 tests, WP15: required surface, valid-fixture validation, stable `make_branch_point_identity`, restore bounded to `host_owned_facade_state_only`, fail-closed missing fields, invalid provenance/event order); `tests/architecture/causal_runtime/test_counterfactual_admission.py` (6 tests); `tests/architecture/structural_boundaries/test_counterfactual_structure_boundaries.py` (3 tests); `tests/runtime/facade/test_runtime_facade_counterfactual.py` (restore rejection). `tests/runtime/engagement/test_trace_replay_gates.py` and `test_facade_engagement_evidence_gates.py` are smoke-gated; the WP15 causal-runtime C++-snippet tests are not in smoke. |
| Gap vs replayable-by-construction | Replay gates are contract validators (fail-closed); the two raw-facade producers assemble envelopes synthetically from request/snapshot fields, and nothing on the maintained path constructs a `ReplayEnvelope` from a real run, so the gates guard a surface that is not produced from a real run by construction. Determinism is expressed via `deterministic_seed` only; there is no maintained same-seed byte-parity replay gate on the run path. Snapshot restore is three-tiered: the WP15 `WorldlineBranchMetadata` contract is metadata-only (`metadata_only = true`, `snapshot_restore_supported = false`, boundary `unsupported`); the `RuntimeFacade` restore path **does** write host-owned facade kinematics (`restore_counterfactual_entity` calls `try_set_entity_kinematics`), bounded to `host_owned_facade_state_only`; resident-state / exact-GPU / full-clone restore are explicitly rejected. |

### (v) Worldline / counterfactual

| Aspect | Finding |
|--------|---------|
| Existing vocabulary | `RuntimeCounterfactualSnapshot` (`worldline_id`, `parent_worldline_id`, `deterministic_seed`, `world_index`, `entity_id`, physics, `snapshot_version`, `barrier_id` `"counterfactual_selected_slice"`, `fidelity_profile_id`, `provider_family`, `selected_stage_node_id`, `cadence_reason`, `evidence_refs`); `RuntimeWorldlineComparison` (`comparable`, `comparison_id`, `parent_worldline_id`, `branch_worldline_id`, `barrier_id`, deltas, `evidence_refs`); schema DTOs `RuntimeCounterfactualBranch/Restore_Request/Result`, `RuntimeExperiment_Request/Result`, `RuntimeExperimentAncestry`; C++ `WorldlineBranchMetadata`, `CounterfactualExperimentRequest`, `CounterfactualAdmissionResult`, `ExperimentEvidenceBridgeRecord`. |
| Producers | C++ facade: `run_counterfactual_branch`, `restore_counterfactual_snapshot`, `run_counterfactual_experiment`. Several ids are **generated at runtime**: `worldline_id` defaults to `worldline:runtime:<world_index>:<entity_id>` when blank (`snapshot_counterfactual_entity`) and to `worldline:baseline`/`worldline:branch` on the experiment path; `comparison_id` is generated as `counterfactual:selected_slice[:<branch_point_id>]`; and a `replay:facade:<worldline_id>` envelope id plus its run/episode/event/packet refs are derived from the snapshot in `runtime_counterfactual_restore_boundary_for_snapshot`. Only some request fields (`replay_envelope_id`, `branch_point_id`, and `parent_worldline_id`/`branch_worldline_id` when supplied) remain caller-authored strings (e.g. `"worldline:wp17f:baseline"`, `"replay:wp17f:0001"`). |
| Consumers | C++ tests + Python bindings only. In `python/**`, the sole maintained reference is the route label `ROUTE_COUNTERFACTUAL_REPLAY = "counterfactual_replay"` in `python/rl/policy_algo/grouped_stopping.py` (name only) plus the scenario-generation lineage refs. The counterfactual/worldline API is **not** exposed through the maintained `RuntimeFacadeAdapter`; it is on raw `ef_py.RuntimeFacade`. |
| Test pinning | `tests/runtime/facade/test_runtime_facade_counterfactual.py` (branch/restore/experiment, smoke); `tests/architecture/causal_runtime/test_worldline_branch_metadata.py` (5 tests); `test_counterfactual_admission.py` (6 tests); `test_experiment_evidence_bridge.py` (5 tests); `tests/architecture/structural_boundaries/test_counterfactual_structure_boundaries.py` (3 tests); `tests/runtime/facade/test_runtime_facade_core.py`. |
| Gap vs replayable-by-construction | Some ids are facade-generated (`worldline_id` default, `comparison_id`, the snapshot-derived `replay:facade:*` refs), but `branch_point_id` and the request's `replay_envelope_id` remain caller-supplied strings, and there is no cross-run stable id scheme, so comparability by construction holds only for the generated ids within a single raw-facade call. The whole surface is unwired from the maintained Python run path (adapter does not expose it). Restore writes host-owned facade kinematics (not metadata-only) and is bounded to `host_owned_facade_state_only`, with resident/gpu/full-clone rejected. |

## 2. Vocabulary Alignment Checklist (suggestions only; not implemented)

Each item lists an inconsistency across the five surfaces and an **additive**
alignment suggestion. None of these are implemented in this slice; later T10
slices must implement them under the additive-only red line in section 3.

| ID | Inconsistency | Additive alignment suggestion |
|----|---------------|-------------------------------|
| VA-1 | **Id type split.** "Identity for replay/diagnostics" is `std::uint64_t` in the trace/engagement/packet surface (`trace_id`, `parent_trace_id`, `chain_id`, `track_id`, `*_event_id`) but `std::string` in the worldline/replay/experiment surface (`worldline_id`, `replay_envelope_id`, `branch_point_id`, `comparison_id`, `run_id`, `episode_id`, `event_id`). SCAL names one `source_id` ("stable producer id for replay and diagnostics") that no single type realizes. | Declare a schema-sourced evidence-id glossary documenting the two representations and their mapping (or add a bridging ref field). Do **not** retype existing fields. |
| VA-2 | **Snapshot-version name + type (no monotone counter today).** State-slice version is `snapshot_version` (`uint64`) on packets, `source_snapshot_version` (`uint64` in `DiagnosticsTrace`, `std::string` in `RuntimeWindowNodeExecutionRecord`), `observation_packet_version` (`uint64`), and `snapshot_version_ref` (`string`). Same concept, ≥3 names, 2 types. Note **no monotone `snapshot_version` counter exists today**: packet `snapshot_version` is a per-export sequence (`index + 1`, reset each export) and the counterfactual snapshot is fixed at `1`. | First record that no monotone counter exists today; then reserve `snapshot_version` for a (to-be-built) `uint64` monotone counter and `snapshot_version_ref` for the string ref; treat `RuntimeWindowNodeExecutionRecord.source_snapshot_version` as a distinct node-source label or additively add a typed `uint64`. No retyping. |
| VA-3 | **Version concept conflation.** Format/schema version (`schema_version` `"1.0"`/`uint32`, `envelope_schema_version`, `contract_version`) and state-slice version (`snapshot_version`) both use the `version` suffix; `observation_schema_version` (format) vs `observation_packet_version`/`snapshot_version` (state-slice) are confusable. | Document the split: `*_schema_version`/`*_contract_version` for format, `*_snapshot_version`/`*_packet_version` for state-slice. No field changes. |
| VA-4 | **Provenance field name.** `InformationStateSource` is field-named `provenance` / `packet_provenance` / `diagnostics_provenance` / `information_state_source` / `source_information_state` / `authority_information_state`. | Adopt a documented `<role>_provenance` convention for `InformationStateSource`-typed fields; keep existing names, apply the convention to new fields only. |
| VA-5 | **Untyped ancestry refs.** Lineage is carried as free `std::string` `*_ref` fields with no typed link to the `_id` they reference; matching is string-equality (`make_branch_point_identity` composes a string). | Keep string refs (they are the serialization form) but add a schema-declared "ref → id-kind" registry so refs are validated against known id kinds; this new validation must be **versioned or opt-in**, since forcing the new check on existing/old inputs would reject previously-accepted refs and is therefore non-additive. |
| VA-6 | **Parallel lineage vocabularies.** C++ `counterfactual_replay_contract_types.h` (`ScenarioGenerationRequestMetadata`) and Python `generation_request.py` (`ScenarioGenerationRequest`) both implement `replay_envelope_ref`/`branch_point_ref`/`evidence_refs`/`deterministic_seed` lineage. | Make a **shared schema the single owner** and generate **both** the C++ and Python faces from it (via the T1 machinery), rather than hand-maintaining two parallels or making Python a projection of the C++ source; additive, names preserved. |
| VA-7 | **Barrier-id default vocabulary.** `barrier_id` is consistently `std::string` but defaults differ: `"export"` (trace/observation/engagement packets), `"counterfactual_selected_slice"` (counterfactual snapshot/comparison), `"window_commit"` (`ReplayBarrierRef`). | Document a barrier-id enum/registry (`export`/`window_commit`/`counterfactual_selected_slice`/...); no default changes. |
| VA-8 | **`trace_id` shares engagement-event id space; `parent_trace_id` unpopulated.** `trace_id` is minted from `next_engagement_event_id_`, and `parent_trace_id` is hardcoded `0` on facade export. | Document the current sharing; if independent trace ancestry is wanted, add a dedicated trace-id allocator and populate `parent_trace_id` — but note that swapping the allocator or populating `parent_trace_id` **changes serialized values** (retained-artifact hashes and the pinned tests), so it must land through a new producer / versioned path that preserves the existing compatibility surface. |

## 3. Suggested Later-Slice Order And Additive-Only Red Line

Suggested T10 slice order after this census (each consumes the T1 event
schemas; each is additive):

1. **Freeze census + vocabulary (this slice).**
2. **Additive evidence glossary.** A schema-sourced id/version glossary (VA-1,
   VA-2, VA-3) mapping the `uint64` and `string` id spaces and the two version
   concepts — documentation + schema metadata, no field changes.
3. **Build the dedicated producers first (prerequisite for slice 4).** No
   monotone snapshot producer exists today (`next_snapshot_version` returns
   `index + 1` and resets each export; the counterfactual snapshot is fixed at
   `1`) and there is no dedicated trace-id allocator (`trace_id` shares
   `next_engagement_event_id_`, reset by `clear()`/clock rewind, and
   `parent_trace_id` is unpopulated). Add a run-global monotone snapshot-version
   producer (VA-2) and a dedicated trace-id allocator (VA-8) as **new** additive
   producers, keeping the existing fields; because these change serialized
   values, they land behind new producers / versioned paths.
4. **Wire the real trace ids / snapshot versions into the maintained run**
   (depends on slice 3). Replace the adapter placeholder `trace_ids = [1]` and
   synthetic `input_snapshot_version` with the real produced values behind the
   facade, gated by the existing `test_trace_replay_gates.py`.
5. **Replay-envelope producer for the maintained run** (depends on slices 3–4).
   Two synthetic producers exist today
   (`replay_envelope_from_experiment_request`,
   `runtime_counterfactual_restore_boundary_for_snapshot`) but neither builds
   from a real run; build a `ReplayEnvelope` from a maintained run (real packet
   `snapshot_version` + event order + provenance) so `validate_replay_envelope`
   runs on real evidence rather than synthetic/fixture inputs.
6. **Populate packet ancestry end-to-end.** Set `parent_trace_id` (via the
   slice-3 allocator) and the `*_ref` lineage; unify the Python lineage
   vocabulary as a shared-schema projection (VA-4, VA-5, VA-6).
7. **Surface worldline/counterfactual comparison through the maintained
   adapter** (opt-in), consuming the T1 engagement schemas.

**Additive-only red line** (T10 key risk: surfaces are pinned by tests and
retained artifacts):

- No existing evidence field may be renamed, retyped, removed, or reordered.
  Member order is ABI; JSON codec aliases and retained-artifact hashes pin the
  serialized shape; the tests in section 1 pin the surface.
- New evidence arrives as new fields / DTOs / producers with regeneration
  freshness gates (`tools/maintenance/dto_schema/generate.py --check`) and
  embedded-reference parity where behavior could drift; compatibility shells
  are retained until the T7 final residual audit retires them deliberately.
- Vocabulary alignment (section 2) is delivered as documentation plus new
  additive fields, never as in-place edits to the pinned surfaces.

## 4. Read-Only Architecture-Test Decision

The slice budget permits at most one optional read-only architecture test to
pin an otherwise-unguarded evidence surface. None was added, for two reasons:

1. **Already pinned.** Each of the five surfaces has existing pins (section 1),
   including smoke-gated ones (`test_diagnostics_trace_contract.py`,
   `test_trace_replay_gates.py`, `test_facade_engagement_evidence_gates.py`,
   `test_facade_step_evidence_gates.py`, `test_runtime_facade_counterfactual.py`,
   `test_dto_schema_freshness.py`) and the comprehensive but not-smoke-gated
   `test_runtime_dto_contracts.py`.
2. **Avoid cementing placeholders.** The most obviously "unguarded" facts are
   the placeholders T10 must replace (adapter `trace_ids = [1]`, synthetic
   string `input_snapshot_version`, caller-supplied worldline ids). Pinning
   them would obstruct the additive migration rather than protect it.

This keeps the slice pure census + documentation, consistent with the
zero-behavior-change discipline.

## 5. Verification

- Baseline (before this doc) maintained smoke: `446 passed, 45 subtests
  passed` at `8bd21d86`.
- Adding this bilingual doc pair without a `clusters --write` registry refresh
  (deliberately deferred per the slice discipline) makes the smoke-gated
  `tests/architecture/governance/test_document_link_audit.py::test_repository_bilingual_registry_matches_the_maintained_surface`
  mark the new unregistered pair. The registry refresh and iteration-ledger
  registration are out of scope for this document (the SCAL census precedent
  made the same scoping call). The exact before/after smoke numbers are
  reported in the iteration ledger entry.

## Related Authority

- [Unified Architecture Program](README.md) (T10 track definition and risk)
- [Simulation System Architecture Design](../../../architecture/standards/simulation_system_architecture_design.md) (SCAL Evidence Graph face)
- [SCAL Conformance Census (2026-07-20)](scal_conformance_census_20260720.md) (T0 census precedent and format)
- [T6 Residual Ledger (2026-07-20)](t6_residual_ledger.md)
- [Repository Consolidation Plan](../repository_consolidation_completed_20260729/README.md) (iteration ledger and protocol)
