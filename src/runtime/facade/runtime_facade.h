#pragma once

#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "runtime/facade/runtime_facade_types.h"

class IWorldBatchBackend;
struct WorldBatchVisualBindingCompatibilityScene;
struct RecentEngagementEvents;

namespace runtime::counterfactual {
struct MaintainedReplayEnvelopeResult;
} // namespace runtime::counterfactual

class RuntimeFacade {
  public:
    explicit RuntimeFacade(std::size_t world_count = 0);
    explicit RuntimeFacade(const RuntimeBatchConfig &config);
    RuntimeFacade(RuntimeFacade &&) noexcept;
    RuntimeFacade &operator=(RuntimeFacade &&) noexcept;
    RuntimeFacade(const RuntimeFacade &) = delete;
    RuntimeFacade &operator=(const RuntimeFacade &) = delete;
    ~RuntimeFacade();

    void configure_batch(const RuntimeBatchConfig &config);
    RuntimeBatchConfig batch_config() const noexcept;
    RuntimeCapabilities capabilities() const noexcept;
    [[nodiscard]] RuntimeCompositionEvidenceResult export_composition_evidence() const;
    [[nodiscard]] RuntimeCompositionEvidenceComparison
    compare_composition_evidence(const RuntimeCompositionEvidence &expected) const;
    RuntimeBackendAdmission admit_backend_request(const RuntimeBackendRequest &request) const;
    RuntimeFidelityAdmission admit_fidelity_request(const RuntimeFidelityRequest &request) const;
    RuntimeCounterfactualSnapshot snapshot_counterfactual_entity(
        const WorldEntityRef &ref, const RuntimeFidelityAdmission &fidelity_admission,
        const std::string &cadence_reason, const std::vector<std::string> &evidence_refs);
    RuntimeCounterfactualRestoreResult
    restore_counterfactual_snapshot(const RuntimeCounterfactualRestoreRequest &request);
    RuntimeCounterfactualBranchResult
    run_counterfactual_branch(const RuntimeCounterfactualBranchRequest &request);
    RuntimeExperimentResult run_counterfactual_experiment(const RuntimeExperimentRequest &request);

    std::size_t world_count() const noexcept;
    void resize(std::size_t world_count);
    void set_worker_threads(std::size_t worker_threads) noexcept;
    std::size_t worker_threads() const noexcept;
    std::size_t effective_worker_threads() const noexcept;

    bool load_database(const std::string &path);
    bool load_unit_definitions(const std::string &path, std::string *error = nullptr);

    void reset_batch(const BatchResetRequest &request = {});
    std::vector<uint64_t>
    apply_world_setup_batch(const std::vector<uint32_t> &seeds,
                            const std::vector<WorldTerrainAssignment> &terrain_assignments,
                            const std::vector<WorldWindAssignment> &wind_assignments,
                            const std::vector<WorldZoneDefinition> &zones,
                            const std::vector<WorldSpawnRequest> &requests,
                            const std::vector<double> &time_steps = {},
                            const std::vector<WorldSunAssignment> &sun_assignments = {});
    BatchWorldSetupResult apply_world_setup(const BatchWorldSetupRequest &request);
    RuntimeWorldLayoutResult apply_world_layout(const RuntimeWorldLayoutRequest &request);
    double world_time_step(std::size_t world_index) const;
    std::vector<std::vector<std::uint64_t>>
    get_sensor_candidate_ids_batch(const std::vector<WorldEntityRef> &refs,
                                   bool use_gpu = false) const;
    std::vector<std::vector<std::uint64_t>>
    get_visual_candidate_ids_batch(const std::vector<WorldEntityRef> &refs,
                                   double range_m = 25000.0, bool use_gpu = false) const;
    std::vector<std::vector<std::uint64_t>>
    get_comm_candidate_ids_batch(const std::vector<WorldEntityRef> &refs,
                                 bool use_gpu = false) const;
    // Maintained facade-owned wrapper. Candidate-id assembly stays at the
    // facade boundary while raw scene assembly remains in a named compatibility
    // helper beneath the runtime quarantine surface.
    std::vector<WorldBatchVisualBindingCompatibilityScene>
    collect_visual_binding_compatibility_scenes_batch(const std::vector<WorldEntityRef> &refs,
                                                      int downsample, bool use_gpu = false) const;
    void set_pilot_actions_batch(const std::vector<WorldPilotActionAssignment> &assignments);
    std::vector<LaunchEvent>
    apply_launch_requests_batch(const std::vector<LaunchRequest> &requests);
    void set_mission_commands_maintained_batch(
        const std::vector<WorldMissionCommandMaintainedAssignment> &assignments);
    void set_task_orders_maintained_batch(
        const std::vector<WorldTaskOrderMaintainedAssignment> &assignments);
    std::vector<TaskOrderMaintainedBatchContract>
    get_task_orders_maintained_batch(const std::vector<WorldEntityRef> &refs) const;
    void set_leader_intents_maintained_batch(
        const std::vector<WorldLeaderIntentMaintainedAssignment> &assignments);
    void set_pilot_reports_maintained_batch(
        const std::vector<WorldPilotReportMaintainedAssignment> &assignments);
    void step_batch();
    void clear_execution_episode_batch() noexcept;
    void prime_execution_episode_batch(const std::vector<WorldEntityRef> &refs,
                                       const std::vector<ExecutionEpisodeState> &states);
    bool execution_episode_ready(std::size_t world_index) const noexcept;
    std::vector<ExecutionEpisodeState>
    export_execution_episode_states(const std::vector<WorldEntityRef> &refs) const;

    std::vector<ExecutionEpisodeRuntimeProducts>
    evaluate_execution_batch(const std::vector<WorldExecutionEpisodeStepRequest> &requests) const;
    std::vector<ExecutionEpisodeRuntimeProducts>
    step_execution_products_batch(const std::vector<WorldExecutionEpisodeStepRequest> &requests);
    ExecutionBatchStepResult step_execution_batch(const ExecutionBatchStepRequest &request);
    std::vector<AgentObservation>
    get_agent_observations_batch(const std::vector<WorldEntityRef> &refs) const;
    std::vector<InstrumentState>
    get_instrument_states_batch(const std::vector<WorldEntityRef> &refs) const;
    std::vector<MissionCommandMaintainedBatchContract>
    get_mission_commands_maintained_batch(const std::vector<WorldEntityRef> &refs) const;
    std::vector<LeaderIntentMaintainedBatchContract>
    get_leader_intents_maintained_batch(const std::vector<WorldEntityRef> &refs) const;
    std::vector<PilotReportMaintainedBatchContract>
    get_pilot_reports_maintained_batch(const std::vector<WorldEntityRef> &refs) const;
    ObservationBatchPacket export_observation_packet(const std::vector<WorldEntityRef> &refs) const;
    ObservationBatchPacket export_observation_packet(const ObservationBatchRequest &request) const;
    TaskingBatchPacket export_tasking_packet(const TaskingBatchRequest &request) const;
    EngagementEventPacket
    export_engagement_event_packet(const EngagementBatchRequest &request) const;
    std::vector<DiagnosticsTrace>
    export_diagnostics_traces(const EngagementBatchRequest &request) const;
    RuntimeWindowResult run_window(const RuntimeWindowRequest &request);

    // --- Dedicated run-global evidence producers ---------------------------
    //
    // Additive snapshot-version and trace-id producers. They are built
    // "producer first": no existing export path calls them, so every existing
    // serialized value (packet snapshot_version,
    // trace_id, barrier metadata, replay envelopes) is byte-for-byte unchanged.
    // Wiring these into the maintained run requires an explicit adapter opt-in.
    //
    // Run-global boundary adjudication (from the run/episode/reset lifecycle):
    //   A "run" == the lifetime of a single RuntimeFacade instance. Both
    //   counters mint monotonically increasing std::uint64_t values (first
    //   minted value is 1) for the whole life of the facade object and are
    //   deliberately NOT reset by any in-run operation, specifically:
    //     * export_* calls (values stay monotone across exports),
    //     * step_batch / step_execution_batch,
    //     * reset_batch (episode re-seed) and clear_execution_episode_batch,
    //     * resize / configure_batch,
    //     * kernel-side clear() / event-clock rewind.
    //   The last item is structural, not incidental: the pre-existing kernel
    //   trace-id allocator (SimulationKernelEngagementEventStore::
    //   next_engagement_event_id_) is per-world state beneath WorldBatchRuntime
    //   and is reset to 1 by clear() and by an event-clock rewind. These
    //   facade-owned counters live above that layer and cannot be reached by
    //   it, which satisfies the requirement for a dedicated allocator that
    //   does not share the resettable engagement-event id space. Only
    //   constructing a fresh RuntimeFacade restarts the sequences at 1.
    //
    // Move semantics: moving a RuntimeFacade transfers the run
    //   identity, including both allocator cursors, to the destination, which
    //   continues the sequences exactly where the source stopped. The
    //   moved-from facade's cursors are exchanged to the invalidated sentinel
    //   (kInvalidatedEvidenceCursor = 0, a value the allocators never mint);
    //   its allocate_*/peek_next_* then fail fast with std::logic_error
    //   instead of silently minting ids that duplicate -- or, via move
    //   assignment, rewind -- the destination's run. Defaulted moves would
    //   copy the uint64 cursors and permit exactly that, so the move
    //   constructor/assignment are user-defined in runtime_facade.cpp.
    //
    // Exhaustion boundary: the cursors are plain uint64
    //   post-increments with no dedicated overflow guard. Minting the final
    //   id UINT64_MAX wraps the cursor to 0, which is exactly the invalidated
    //   sentinel above, so every later allocate_*/peek_next_* on that counter
    //   fails fast (std::logic_error) permanently: the sequence collapses
    //   into the invalidated state instead of wrapping around and repeating
    //   ids. Exhaustion and moved-from deliberately share that single
    //   invalidated representation (no separate exhausted state; the
    //   fail-fast message names both entry paths). Practical reachability:
    //   minting once per nanosecond would take roughly 584 years to exhaust
    //   the space.
    //
    // allocate_* mint-and-advance (post-increment); peek_next_* report the
    // value the next allocate_* would return without advancing. All four
    // throw std::logic_error once the counter is invalidated -- by move or
    // by exhaustion (see the two paragraphs above).
    std::uint64_t allocate_run_snapshot_version(); // Run-global snapshot sequence.
    std::uint64_t peek_next_run_snapshot_version() const;
    std::uint64_t allocate_trace_id(); // Run-global trace sequence.
    std::uint64_t peek_next_trace_id() const;

    // --- Maintained-run replay-envelope producer ---------------------------
    //
    // This additive read-only producer assembles a
    // runtime::counterfactual::ReplayEnvelope from a maintained run's REAL
    // window products -- the RuntimeWindowResult returned by run_window --
    // instead of the synthetic request/snapshot fields the two existing
    // envelope assemblies use (replay_envelope_from_experiment_request and
    // runtime_counterfactual_restore_boundary_for_snapshot, both file-local to
    // runtime_facade_counterfactual.cpp, which both remain untouched).
    //
    // Real-evidence field sources (fail-closed when absent):
    //   * snapshot_ref.snapshot_version_ref / facade_provenance_ref.packet_ref
    //     copy the run-produced provenance strings on the exported observation
    //     packet ("global:{snapshot_version}" / "obs:{snapshot_version}",
    //     apply_observation_packet_provenance) -- the packet's real
    //     snapshot_version embedding, not a re-derived constant.
    //   * facade_provenance_ref.information_state_source copies the observation
    //     packet's own provenance struct (the run-produced information-state
    //     label and id lists).
    //   * barrier_ref copies the window's real "window_commit" barrier record
    //     (barrier_id + sequence from RuntimeWindowResult.barrier_trace) plus
    //     the engagement packet's real barrier_detail.
    //   * event_order_ref anchors on the engagement packet's trace_ids tail --
    //     which the facade-evidence opt-in adapter path stamps from the
    //     allocate_trace_id producer -- as "event:trace:{id}", with the
    //     packet's real producer_node_id.
    //   * source_time_s echoes the window's real context.source_time_s.
    //   * run_id / episode_id / deterministic_seed are the caller-owned run
    //     identity (the run orchestrator owns them; the facade cannot mint a
    //     more-real run identity), validated non-blank.
    //
    // Opt-in truth linkage: the producer first REQUIRES the window result
    // to carry the opaque identity attached by THIS facade's run_window seam.
    // A hand-built result and a result returned by another facade fail closed
    // before numeric evidence admission, even when both allocators overlap.
    // The window's trace ids must then have been minted by THIS facade's
    // allocator (every id must be < peek_next_trace_id()); the default
    // maintained path's placeholder trace_ids = [1] against an untouched
    // allocator (peek == 1) fails closed with a named reason. A meaningful
    // envelope therefore requires the RuntimeFacadeAdapter(
    // use_facade_evidence_producers=True) opt-in path (or an equivalent caller
    // that stamps allocator-minted ids).
    //
    // Envelope id namespace: "replay:maintained:{run_id}:trace:{trace_id}".
    // Existing id spaces stay untouched and disjoint: "replay:facade:*" is the
    // snapshot-derived restore-boundary space and remaining spaces are
    // caller-authored; "replay:maintained:*" is verified unused at this
    // baseline and is reserved for this producer.
    //
    // Restore claim: the maintained window path registers no counterfactual
    // worldline snapshot, so the envelope honestly claims
    // snapshot_restore_supported = false with the
    // restore_unsupported_until_snapshot_restore_proof boundary (accepted by
    // validate_replay_envelope; restore proof stays with the counterfactual
    // restore path).
    //
    // Zero-wiring: nothing in the maintained runtime calls this method; it
    // only READS the allocator cursors (peek) and mints nothing, so calling it
    // is idempotent and every existing serialized value is byte-for-byte
    // unchanged. The assembled envelope is validated with
    // validate_replay_envelope before it is returned; rejection reasons are
    // stable named strings (see runtime_facade_internal.h
    // kMaintainedReplayEnvelope* constants).
    // Snapshot identity is opt-in and additive: by DEFAULT
    // (`run_snapshot_version == 0`, the allocator's invalid sentinel)
    // snapshot_ref.snapshot_version_ref is exactly the observation packet's own
    // run-produced provenance string ("global:{packet.snapshot_version}").
    // That value is real, but packet.snapshot_version is the PER-EXPORT
    // sequence (next_snapshot_version(index) = index + 1, reset every export),
    // which the contract calls out explicitly: it is not run-globally unique,
    // so two
    // exports of one run carry the same "global:1" and the envelope's snapshot
    // identity does not distinguish them.
    //
    // Passing a non-zero `run_snapshot_version` qualifies the ref with the
    // run-global monotone version returned by allocate_run_snapshot_version,
    // yielding
    // "global:{packet_version}:run_snapshot:{run_global_version}" -- additive by
    // construction: the existing per-export substring keeps its exact meaning
    // and position as the prefix, and nothing is renamed, retyped, or dropped.
    // The value must have been minted by THIS facade's run-snapshot allocator
    // AND
    // recorded by this exact run_window result; allocation without a matching
    // window anchor is insufficient. Otherwise the producer fails closed with
    // kMaintainedReplayEnvelopeRunSnapshotNotRunMinted. The maintained run
    // recovers its own recorded value from the window's real
    // RuntimeWindowNodeExecutionRecord.source_snapshot_version ("snapshot:{n}",
    // stamped by the facade-evidence opt-in path), so this stays run-produced
    // evidence rather than a caller-invented number.
    //
    // Because qualifying changes a serialized string, it follows the explicit
    // opt-in discipline: default off (this parameter defaults to 0), reached only
    // through an explicit adapter opt-in, with a named fail-closed rejection.
    runtime::counterfactual::MaintainedReplayEnvelopeResult
    build_maintained_replay_envelope(const RuntimeWindowResult &window_result,
                                     const std::string &run_id, const std::string &episode_id,
                                     std::uint64_t deterministic_seed,
                                     std::uint64_t run_snapshot_version = 0) const;

    // --- Maintained engagement-packet ancestry producer --------------------
    //
    // This producer sets parent_trace_id from the run-global allocator and
    // records reference lineage for the engagement-event packet family.
    //
    // Assembles a MaintainedPacketAncestryResult from the REAL products of one
    // maintained window, linking the window's exported DiagnosticsTrace family
    // to the previous window's run-minted trace anchor. Like the replay-envelope
    // producer it is read-only (peeks the allocator cursor, mints
    // nothing) and returns COPIES: the window products, the default export
    // path, and every existing serialized value stay byte-for-byte unchanged.
    // Nothing in the maintained runtime calls this method; the only Python
    // reach is the RuntimeFacadeAdapter.build_maintained_packet_ancestry seam,
    // which requires the use_facade_evidence_producers=True opt-in.
    //
    // Gates (fail-closed, named reasons in runtime_facade_internal.h):
    //
    //   1. The window must carry the opaque association minted by THIS
    //      facade's run_window seam; foreign and synthetic results fail before
    //      numeric evidence admission.
    //   2. The window must yield an ADMITTED maintained replay envelope: this
    //      producer internally runs build_maintained_replay_envelope (default
    //      run-snapshot qualification off) and propagates its rejection reasons
    //      verbatim, so the replay-envelope gates -- including the run-global
    //      trace-id admission that rejects the default placeholder [1] -- plus
    //      validate_replay_envelope guard this surface too.
    //      The admitted envelope id becomes ancestry.replay_envelope_ref, so
    //      an ancestry record always names a validator-accepted envelope.
    //   3. parent_trace_id (when non-zero) must have been minted by THIS
    //      facade's trace-id allocator and recorded by an earlier genuine
    //      window --
    //      kMaintainedPacketAncestryParentNotRunMinted otherwise. Allocation
    //      without a window anchor and foreign-facade linkage both fail closed.
    //      A numeric anchor remains usable while its RuntimeWindowResult is
    //      retained by the caller or while it is in the facade's bounded
    //      recent-window retention (64 windows); callers that need an older
    //      anchor must retain the source window result instead of relying on an
    //      unbounded numeric history.
    //   4. parent_trace_id (when non-zero) must be strictly below every one of
    //      the window's own trace tags (ancestry points backwards; no self or
    //      forward links, hence no cycles) --
    //      kMaintainedPacketAncestryParentNotBeforeWindow otherwise.
    //   5. The window must carry exported diagnostics traces, at least one of
    //      which is tagged with one of the packet's (already-admitted)
    //      run-minted trace ids; kernel-space traces alone cannot anchor an
    //      ancestry (the two uint64 id spaces are value-indistinguishable, so
    //      tag-set membership is the only honest discriminator).
    //
    // parent_trace_id = 0 declares a root window: ancestral trace copies keep
    // parent_trace_id = 0, byte-identical to the existing default, so a root
    // ancestry asserts lineage without inventing a parent.
    MaintainedPacketAncestryResult
    build_maintained_packet_ancestry(const RuntimeWindowResult &window_result,
                                     const std::string &run_id, const std::string &episode_id,
                                     std::uint64_t deterministic_seed,
                                     std::uint64_t parent_trace_id = 0) const;

    // --- Maintained worldline comparison producer --------------------------
    //
    // This opt-in producer surfaces worldline/counterfactual comparison through
    // the maintained adapter. It joins TWO maintained windows of THIS
    // facade's run -- a baseline worldline and a candidate (counterfactual)
    // worldline -- into an evidence-level comparison, consuming the
    // replay-envelope producer and the packet-ancestry
    // producer for each side. Like both, it is read-only (peeks the allocator
    // cursors via the inner producers, mints nothing, registers no
    // counterfactual worldline snapshot) and additive: nothing in the
    // maintained runtime calls this method; the only Python reach is the
    // RuntimeFacadeAdapter.build_maintained_worldline_comparison seam, which
    // requires the use_facade_evidence_producers=True opt-in.
    //
    // What a "worldline" is here: the evidence chain of one window sequence,
    // named by its window's run-minted trace anchor
    // ("worldline:maintained:{run_id}:trace:{anchor}"). Two worldlines of one
    // facade run are, e.g., two batch worlds set up with the same or different
    // seeds (parallel same-seed/different-seed runs) or two window sequences
    // separated by a counterfactual intervention. Evidence minted by a
    // DIFFERENT facade cannot enter: each side's opaque run_window identity
    // association fail-closes it before the replay-envelope numeric gates.
    //
    // Gates (fail-closed; comparison-level reasons in runtime_facade_internal.h
    // kMaintainedWorldlineComparison*, underlying producer reasons carried in
    // result.errors -- with two windows, verbatim propagation would not say
    // which side failed):
    //
    //   1./2. Each window must yield an ADMITTED maintained replay envelope
    //      (build_maintained_replay_envelope, default qualification off):
    //      all replay-envelope real-evidence gates (beginning with the opaque
    //      window/facade association) plus validate_replay_envelope
    //      -- which requires the deterministic seed and the deterministic
    //      event-order sort key, so "deterministic replay refs present" is
    //      discharged by the validator, per side. Rejection:
    //      *_baseline_envelope_rejected / *_candidate_envelope_rejected.
    //   3./4. Each window must yield an ADMITTED maintained packet ancestry
    //      (build_maintained_packet_ancestry with the side's parent id): the
    //      packet-ancestry parent gates guard the lineage each side contributes.
    //      Rejection: *_baseline_ancestry_rejected /
    //      *_candidate_ancestry_rejected. (Each ancestry call re-runs its
    //      side's envelope build internally; both builds are deterministic
    //      over the same inputs, so ancestry.replay_envelope_ref equals the
    //      gate-1/2 envelope id by construction.)
    //   5. The two anchors must be DISTINCT (a window compared against itself
    //      is not a worldline comparison) --
    //      *_windows_share_the_anchor_trace otherwise.
    //
    // NO TRUTH PROMOTION (the contract boundary; see the DTO comment in
    // runtime_facade_types.h): the result references evidence ids only --
    // envelope ids, ancestry ids, anchor trace ids, event-order refs, snapshot
    // version refs -- never copies of truth state (no kinematic deltas, unlike
    // the raw RuntimeWorldlineComparison). truth_claim/promoted_to_support are
    // structurally always false and claim_scope is always "comparative".
    // Measuring HOW the worldlines diverge stays downstream replay work over
    // the two referenced envelopes; this producer only establishes that both
    // sides are replay-comparable by construction and records their identity.
    //
    // run_id / episode_id are the shared caller-owned run identity (one facade
    // == one run, the facade lifecycle boundary; both windows belong to it).
    // baseline/candidate deterministic seeds are the two worldlines' own
    // caller-owned setup seeds (they differ for a different-seed world pair);
    // deterministic_seed_matched records their equality.
    // baseline/candidate parent_trace_id (default 0 = root) are the sides'
    // packet-ancestry parents.
    //
    // Zero-wiring byte parity: nothing on any existing path calls this method,
    // it only reads, and the default (non-opt-in) adapter path cannot reach it
    // meaningfully (placeholder evidence fails gate 1), so every existing
    // serialized value is byte-for-byte unchanged.
    MaintainedWorldlineComparisonResult build_maintained_worldline_comparison(
        const RuntimeWindowResult &baseline_window_result,
        const RuntimeWindowResult &candidate_window_result, const std::string &run_id,
        const std::string &episode_id, std::uint64_t baseline_deterministic_seed,
        std::uint64_t candidate_deterministic_seed, std::uint64_t baseline_parent_trace_id = 0,
        std::uint64_t candidate_parent_trace_id = 0) const;

    // --- Maintained observation-view declaration ---------------------------
    //
    // Additive, read-only declaration export for the maintained
    // observation read seam (scenario_loader/core.py::get_policy_agent_observation).
    // It materializes "what layer the seam produces" as a runtime-queryable
    // ObservationViewSpec instead of a documentation-only fact.
    //
    // The returned spec carries only the STRUCTURAL facts of the maintained
    // observation view -- its schema version, view id, and the produced /
    // consumed information-state layers and semantic stage -- mirrored from
    // the Python-owned single source of truth (gym_envs/observation_view.py and
    // python/architecture/information_layer.py). The detailed observation field
    // list is deliberately left Python-owned (required_fields / optional_fields
    // stay empty here) so there is no dual-source field catalogue to drift; an
    // architecture test gates this C++ export against the Python registry.
    //
    // Zero-wiring: this declaration does not migrate any consumer and nothing
    // in the maintained runtime calls this method, so the observation seam's
    // behavior and every existing serialized value are byte-for-byte unchanged.
    // The method is a pure constant producer (no facade instance state is read
    // or mutated), hence const and callable on any facade including a zero-world
    // one.
    ObservationViewSpec describe_maintained_observation_view() const;

  private:
    bool runtime_window_result_belongs_to_this_facade(
        const RuntimeWindowResult &window_result) const noexcept;
    bool runtime_window_result_evidence_matches_identity(
        const RuntimeWindowResult &window_result) const noexcept;
    RuntimeCompositionEvidenceComparison
    runtime_window_composition_evidence_comparison(const RuntimeWindowResult &window_result) const;
    bool runtime_window_trace_ids_recorded_by_this_window(
        const RuntimeWindowResult &window_result) const noexcept;
    bool runtime_window_snapshot_recorded_by_this_window(
        const RuntimeWindowResult &window_result,
        std::uint64_t run_snapshot_version) const noexcept;
    bool runtime_window_parent_trace_recorded_before_this_window(
        const RuntimeWindowResult &window_result, std::uint64_t parent_trace_id) const noexcept;
    bool counterfactual_world_index_valid(std::uint64_t world_index) const noexcept;
    bool apply_counterfactual_delta(const WorldEntityRef &ref,
                                    const RuntimeCounterfactualBranchRequest &request);
    bool restore_counterfactual_entity(const WorldEntityRef &target_ref,
                                       const RuntimeCounterfactualSnapshot &snapshot);
    RecentEngagementEvents export_recent_engagement_events_for_world(std::size_t world_index) const;
    std::vector<WorldBatchVisualBindingCompatibilityScene>
    collect_visual_binding_compatibility_scenes_from_candidate_ids_batch(
        const std::vector<WorldEntityRef> &refs,
        const std::vector<std::vector<std::uint64_t>> &candidate_ids_batch, int downsample) const;
    ObservationBatchPacket build_observation_packet(const ObservationBatchRequest &request) const;
    TaskingBatchPacket build_tasking_packet(const TaskingBatchRequest &request) const;
    void register_counterfactual_worldline_snapshot(const RuntimeCounterfactualSnapshot &snapshot);

    // Invalidated sentinel for the evidence cursors below: 0 is never minted
    // (sequences start at 1), so a 0 cursor means the counter was invalidated
    // by one of its two entry paths -- the facade was moved-from, or the
    // cursor exhausted its uint64 space (post-increment of UINT64_MAX wraps
    // to 0) -- and the four producer methods above fail fast
    // (std::logic_error).
    static constexpr std::uint64_t kInvalidatedEvidenceCursor = 0;

    struct CounterfactualWorldlineRegistry;
    // Single execution owner. The admitted native provider materializes the
    // maintained implementation behind the internal backend SPI.
    std::unique_ptr<IWorldBatchBackend> runtime_;
    std::unique_ptr<CounterfactualWorldlineRegistry> counterfactual_worldlines_;
    // Opaque run identity used to bind RuntimeWindowResult products to the
    // facade instance that returned them.  It is intentionally not a DTO field
    // and is not exported through Python bindings.
    std::shared_ptr<RuntimeFacadeIdentity> identity_;
    // Run-global evidence allocators (see the public
    // producer declarations above for the run-global boundary adjudication
    // and move semantics). Appended after the existing members; a fresh
    // facade starts both at 1. NOTE: RuntimeFacade's move constructor and
    // move assignment are user-defined (runtime_facade.cpp) and must transfer
    // EVERY member listed here; a sizeof tripwire there fires when this
    // member set changes.
    std::uint64_t next_run_snapshot_version_ = 1;
    std::uint64_t next_trace_id_ = 1;
    std::uint64_t next_window_identity_ = 1;
};
