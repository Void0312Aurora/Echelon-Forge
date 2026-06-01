# Simulation Architecture

Status: active subproject opened on `2026-05-19`.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

This subproject turns the strict simulation architecture baseline into scoped
work packages. It should be used before starting broad implementation across
weapons, naval runtime, sensor/track, command/tasking, facade, or backend
acceleration.

Architecture authority:

- [simulation system architecture design](../../plan/architecture/simulation_system_architecture_design.md)
- [system layering and engine encapsulation plan](../../plan/architecture/system_layering_and_engine_encapsulation_plan.md)
- [architecture and performance follow-up](../../plan/architecture/architecture_and_performance_research_followup.md)

## Current Position

The active design conclusion is:

1. The project should be treated as a SCAL system: semantic, causal, agentic,
   and learning-facing, with `WP0-WP5` building the verified runtime kernel,
   `WP6` closing backend profile policy for acceleration and resident-state
   work, and `WP7` materializing that policy into registry, projection,
   evidence, and multi-fidelity entry tasks.
2. The project should follow one canonical semantic lifecycle.
3. Real execution should use a causal-temporal execution model. The temporal
   DAG is the scheduling projection, with feedback crossing explicit
   state-store or event-queue boundaries.
4. Air, naval, ground, weapon, and future platform/domain families should
   extend that lifecycle through stage-local model families, capability
   bundles, and stage-node contracts.
5. Runtime facade and typed request/result contracts should become the long-term
   frontend dependency.
6. Policy computation and test/orchestration should be modeled as explicit
   producers and consumers of facade contracts, not as hidden owners of
   simulation state.
7. Information-state boundaries must distinguish `World Truth`,
   `ObservationPacket`, and `DecisionBelief`.
8. Local work on this machine should focus on build/import/smoke, architecture
   docs, contract design, and simulation assembly rather than RL training.
9. Backend acceleration and resident-state work should be routed through
   explicit backend profiles and parity budgets behind contracts, not through
   a second semantic path.
10. Backend capability implementation should start from the accepted WP6
    registry and parity records, then add machine-checkable materialization and
    evidence gates before any exact GPU, resident-state, shadow, or
    multi-fidelity capability can become maintained.
11. The maintained training-path bridge between accepted facade contracts and
    future learning-facing consumers should be routed through a separate
    `WP7.5` line that migrates batch training paths away from
    `RuntimeFacade.runtime()`.
12. Learning-face work should be routed through a separate `WP8` task family
    focused on curriculum, evaluation, capability profiling, scenario
    generation, and learning evidence; it should not reopen the simulation
    closure or assume local RL training availability.
13. Deferred contract and infrastructure closure should be routed through
    `WP9`, which promotes accepted DTO vocabulary and closes small residual
    infrastructure/guard items without reopening `WP0-WP8`.
14. Post-WP9 work should follow the
    [post-WP9 architecture route plan](archive/post_wp9_architecture_route_plan_20260520.md):
    causal runtime foundation first, facade vertical slice second, then
    information/agency enforcement, backend/fidelity, capability composition,
    and counterfactual/experiment generation. Phases 1-5 are now accepted as
    `WP10`, `WP11`, `WP12`, `WP13`, and `WP14`; Phase 6 is now accepted as
    `WP15`.
15. After the post-WP9 route, the next architecture-optimization phase is
    `WP16 Runtime Spine Consolidation`: turn the accepted boundaries from
    `WP10-WP15` into the maintained default runtime path, close remaining
    bypasses, and promote `GAP-9` clock-domain enforcement from deferred
    advisory status into the selected runtime-spine slice.
16. After WP16, the Stage 3 final refactor phase is opened as
    `WP17 Stage 3 Runtime Materialization And Cleanup`: reconcile the Stage 3
    plan with current code facts, migrate maintained business paths away from
    compatibility-only runtime access, and split multi-rate, fidelity-provider,
    capability-spawn, and counterfactual runtime materialization into bounded
    implementation streams.
17. After WP17 acceptance, the remaining mainline was frozen as four stages:
    `WP18` runtime ownership and C++ hot-path consolidation, `WP19` CUDA /
    resident-state mainline alignment, `WP20` public capability-platform
    composition, and `WP21` full counterfactual / experiment runtime. `WP18`,
    `WP19`, and `WP20` remain accepted. WP21's claimed closure was rejected by
    the owner on `2026-05-22`; it must not be treated as final route closure.
18. The post-WP21
    [architecture refactoring audit](../review/architecture_refactoring_audit_20260522.md)
    is a new architecture-level fact: several compatibility layers and old
    implementation surfaces still act as default or maintained paths. This
    invalidated the WP21 acceptance claim and opened `WP22 Legacy Compatibility
    Retirement And Architecture Hardening`, but WP22's continuation stream was
    stopped by the owner on `2026-05-23` after uncontrolled follow-up waves,
    partial evidence reuse, and quarantine/dual-representation drift made the
    plan unacceptable.
19. The latest legacy-retirement recovery record is `WP23 Legacy Retirement
    Recovery And Reset`: it froze WP22, classified current dirty work, forced
    delete-or-block decisions, resolved single-representation tasking/public-API
    exits as blocked, skipped implementation, and closed as `blocked` on
    `2026-05-24`.
20. `TM01 Architecture Closure Remediation` is closed for the audited
    implementation slice only: `TM01-A`, `TM01-C`, and `TM01-D` passed for the
    focused maintained path, while the `TM01-B` launch bridge was recorded as a
    source-backed residual for later architecture ownership.
21. When this subproject is split across subagents or workers, follow the
    [Subagent Usage Policy](../../standards/governance/subagent_usage_policy.md):
    keep write scopes disjoint, keep one integration owner, and do not split
    the same normative table across concurrent authors.
22. Commit messages for implementation closure should use capability/result
    language and avoid internal work-package labels such as `WP13` or `WP14`.
23. `TM03 Launch Bridge Boundary` closed the TM01-B source-backed
    `systems -> SimulationKernel` weapon-release residual for the two explicit
    release helpers by introducing `IWeaponReleaseService`; it does not claim
    broader P7 launch/fire-control redesign, raw-runtime retirement, or general
    compatibility cleanup.

## Work Packages

| Work package | Status | Goal | Output |
|--------------|--------|------|--------|
| `WP0 Architecture Baseline` | complete | Make the SCAL framing, semantic lifecycle, causal-temporal execution projection, and extension rules explicit | architecture design doc, task subproject entry |
| `WP1 Pipeline Inventory` | complete | Map current code, systems, models, and tests onto `P0-P10` and current coupling hotspots | [pipeline inventory](archive/wp1_pipeline_inventory/pipeline_inventory_wp1_20260519.md) |
| `WP2 Contract Freeze` | complete | Identify packet families, stage-node contracts, and cross-layer policy/orchestration contracts that need explicit ownership | [contract freeze](archive/wp2_contract_freeze/contract_freeze_wp2_20260519.md) |
| `WP2.5 Scheduler Semantics Freeze` | complete | Freeze event ordering, state versioning, barrier visibility, clock-domain merge policy, replay contract, and stage-node manifest schema | [scheduler semantics freeze](archive/wp25_scheduler_semantics/scheduler_semantics_wp25_20260519.md), [acceptance review](../review/archive/wp-acceptance/wp25_scheduler_semantics_acceptance_review_20260519.md) |
| `WP3 Engagement Pilot` | complete | Use weapon/engagement as the first cross-domain validation slice | [engagement pilot task family](archive/wp3_engagement_pilot/engagement_pilot_wp3_20260519.md) |
| `WP4 Facade Alignment` | complete | Ensure pilot behavior is reachable through facade-shaped APIs without raw runtime access | [facade alignment task family](archive/wp4_facade_alignment/facade_alignment_wp4_20260519.md), [final acceptance](../review/archive/wp-acceptance/wp4_facade_alignment_acceptance_review_20260519.md) |
| `WP5 Validation Harness` | complete | Add smoke, architecture, trace, boundary, information-leakage, and replay/evidence tests that prove the shared lifecycle and graph boundaries | [validation harness task family](archive/wp5_validation_harness/validation_harness_wp5_20260519.md), [final acceptance](../review/archive/wp-acceptance/wp5_validation_harness_acceptance_review_20260519.md) |
| `WP6 Backend Profile Policy` | complete | Freeze backend profile taxonomy, parity budgets, resident-state boundaries, and backend capability exposure rules | [backend profile policy](archive/wp6_backend_profile_policy/backend_profile_policy_wp6_20260519.md), [profile registry](archive/wp6_backend_profile_policy/wp6_backend_profile_registry_20260519.md), [parity budget registry](archive/wp6_backend_profile_policy/wp6_parity_budget_registry_20260519.md), [resident-state boundary rules](archive/wp6_backend_profile_policy/wp6_resident_state_boundary_rules_20260519.md), [acceptance review](../review/archive/wp-acceptance/wp6_backend_profile_policy_acceptance_review_20260519.md) |
| `WP7 Backend Capability Materialization` | complete / accepted | Materialize accepted WP6 policy into machine-checkable registry, runtime capability projection, promotion evidence gates, and multi-fidelity entry conditions without promoting candidates | [backend capability materialization](archive/wp7_backend_capability_materialization/backend_capability_materialization_wp7_20260519.md), [registry materialization](archive/wp7_backend_capability_materialization/wp7_registry_materialization_cluster_20260519.md), [runtime capability projection](archive/wp7_backend_capability_materialization/wp7_runtime_capability_projection_cluster_20260519.md), [promotion evidence gates](archive/wp7_backend_capability_materialization/wp7_promotion_evidence_gates_cluster_20260519.md), [multi-fidelity entry conditions](archive/wp7_backend_capability_materialization/wp7_multifidelity_entry_conditions_cluster_20260519.md), [acceptance review](../review/archive/wp-acceptance/wp7_backend_capability_materialization_acceptance_review_20260519.md) |
| `WP7.5 Training Path Facade Bridge` | complete / accepted | Migrate maintained batch training paths from `RuntimeFacade.runtime()` and raw `WorldBatchRuntime` stepping to facade-shaped execution and observation APIs before `WP8` depends on them | [training path facade bridge](archive/wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.md), [acceptance review](../review/archive/wp-acceptance/wp75_training_path_facade_bridge_acceptance_review_20260520.md) |
| `WP8 SCAL Learning Face` | complete / accepted | Define curriculum, evaluation, capability profiling, scenario generation, and learning evidence as explicit architecture and task vocabulary without reopening the simulation closure | [learning face task family](archive/wp8_learning_face/learning_face_wp8_20260520.md), [acceptance review](../review/archive/wp-acceptance/wp8_learning_face_acceptance_review_20260520.md) |
| `WP9 Contract And Infrastructure Closure` | complete / accepted | Promote deferred DTO contracts, close small infrastructure residuals, add guard allowlists, and publish final index/acceptance evidence | [contract and infrastructure closure](archive/wp9_contract_infrastructure_closure/contract_infrastructure_closure_wp9_20260520.md), [DTO batch 1](archive/wp9_contract_infrastructure_closure/wp9_dto_promotion_batch1_cluster_20260520.md), [DTO batch 2](archive/wp9_contract_infrastructure_closure/wp9_dto_promotion_batch2_cluster_20260520.md), [infrastructure closure](archive/wp9_contract_infrastructure_closure/wp9_infrastructure_closure_cluster_20260520.md), [guard enforcement](archive/wp9_contract_infrastructure_closure/wp9_guard_enforcement_cluster_20260520.md), [integration sync](archive/wp9_contract_infrastructure_closure/wp9_integration_and_index_sync_cluster_20260520.md), [acceptance review](../review/archive/wp-acceptance/wp9_contract_infrastructure_closure_acceptance_review_20260520.md) |
| `Post-WP9 Architecture Route` | route selected | Establish the implementation order and anchor Phase 1 as WP10: causal runtime foundation, facade vertical slice, information/agency enforcement, backend/fidelity, capability composition, counterfactual/experiment generation | [post-WP9 architecture route plan](archive/post_wp9_architecture_route_plan_20260520.md) |
| `WP10 Causal Runtime Foundation` | complete / accepted | Implement Phase 1 of the post-WP9 route: manifest registry seed, minimal scheduling-window loop, request injection, same-window validation, event/snapshot evidence, and integration handoff | [causal runtime foundation](archive/wp10_causal_runtime_foundation/causal_runtime_foundation_wp10_20260520.md), [manifest registry](archive/wp10_causal_runtime_foundation/wp10_manifest_registry_cluster_20260520.md), [window loop / injection](archive/wp10_causal_runtime_foundation/wp10_window_loop_injection_cluster_20260520.md), [same-window validation](archive/wp10_causal_runtime_foundation/wp10_same_window_validation_cluster_20260520.md), [event/snapshot evidence](archive/wp10_causal_runtime_foundation/wp10_event_snapshot_evidence_cluster_20260520.md), [integration handoff](archive/wp10_causal_runtime_foundation/wp10_integration_acceptance_cluster_20260520.md), [acceptance review](../review/archive/wp-acceptance/wp10_causal_runtime_foundation_acceptance_review_20260520.md) |
| `WP11 Facade Vertical Slice And Provenance` | complete / accepted | Implement Phase 2 of the post-WP9 route: `ActionHoldPolicy`, information-state provenance labels, a WP10-seam facade/binding proof, consumer boundary pre-gates, and integration handoff | [facade vertical slice and provenance](archive/wp11_facade_vertical_slice_provenance/facade_vertical_slice_provenance_wp11_20260520.md), [ActionHoldPolicy](archive/wp11_facade_vertical_slice_provenance/wp11_action_hold_policy_cluster_20260520.md), [information provenance](archive/wp11_facade_vertical_slice_provenance/wp11_information_provenance_labels_cluster_20260520.md), [vertical slice proof](archive/wp11_facade_vertical_slice_provenance/wp11_facade_vertical_slice_proof_cluster_20260520.md), [consumer boundary pre-gates](archive/wp11_facade_vertical_slice_provenance/wp11_consumer_boundary_pregates_cluster_20260520.md), [integration handoff](archive/wp11_facade_vertical_slice_provenance/wp11_integration_acceptance_cluster_20260520.md), [acceptance review](../review/archive/wp-acceptance/wp11_facade_vertical_slice_provenance_acceptance_review_20260520.md) |
| `WP12 Information And Agency Enforcement` | complete / accepted | Implement Phase 3 of the post-WP9 route: Law 14 read-side enforcement, `AgentRole` authority validation, information-transformation evidence, authorized intent injection, and integration handoff | [information and agency enforcement](archive/wp12_information_agency_enforcement/information_agency_enforcement_wp12_20260520.md), [Law 14 read-side enforcement](archive/wp12_information_agency_enforcement/wp12_law14_read_side_enforcement_cluster_20260520.md), [agency role authority](archive/wp12_information_agency_enforcement/wp12_agency_role_authority_cluster_20260520.md), [information transformation surface](archive/wp12_information_agency_enforcement/wp12_information_transformation_surface_cluster_20260520.md), [intent injection authority guard](archive/wp12_information_agency_enforcement/wp12_intent_injection_authority_guard_cluster_20260520.md), [integration handoff](archive/wp12_information_agency_enforcement/wp12_integration_acceptance_cluster_20260520.md), [acceptance review](../review/archive/wp-acceptance/wp12_information_agency_enforcement_acceptance_review_20260520.md) |
| `WP13 Backend Fidelity Expansion` | complete / accepted | Implement Phase 4 of the post-WP9 route: make runtime capabilities, backend profiles, parity budgets, and fidelity profile requests queryable, rejectable, and evidence-backed without promoting unsupported backend claims | [backend fidelity expansion](archive/wp13_backend_fidelity_expansion/backend_fidelity_expansion_wp13_20260520.md), [capability query](archive/wp13_backend_fidelity_expansion/wp13_runtime_capability_query_cluster_20260520.md), [backend profile registry gate](archive/wp13_backend_fidelity_expansion/wp13_backend_profile_registry_gate_cluster_20260520.md), [parity budget evidence gate](archive/wp13_backend_fidelity_expansion/wp13_parity_budget_evidence_gate_cluster_20260520.md), [fidelity request gate](archive/wp13_backend_fidelity_expansion/wp13_fidelity_profile_request_gate_cluster_20260520.md), [facade/binding proof](archive/wp13_backend_fidelity_expansion/wp13_facade_binding_proof_cluster_20260520.md), [integration handoff](archive/wp13_backend_fidelity_expansion/wp13_integration_acceptance_cluster_20260520.md), [acceptance review](../review/archive/wp-acceptance/wp13_backend_fidelity_expansion_acceptance_review_20260520.md) |
| `WP14 Capability Composition` | complete / accepted | Implement Phase 5 of the post-WP9 route: move existing type-name setup toward typed `Capability` / `CapabilityBundle` composition through compatibility-preserving resolved spawn plans, additive facade/setup DTOs, and strict implementation gates without a big-bang spawn rewrite | [capability composition](archive/wp14_capability_composition/capability_composition_wp14_20260521.md), [capability bundle contract](archive/wp14_capability_composition/wp14_capability_bundle_contract_cluster_20260521.md), [content definition lowering](archive/wp14_capability_composition/wp14_content_definition_lowering_cluster_20260521.md), [spawn resolution bridge](archive/wp14_capability_composition/wp14_spawn_resolution_bridge_cluster_20260521.md), [additive facade setup DTO](archive/wp14_capability_composition/wp14_additive_facade_setup_dto_cluster_20260521.md), [capability effects materialization](archive/wp14_capability_composition/wp14_capability_effects_materialization_cluster_20260521.md), [compatibility validation](archive/wp14_capability_composition/wp14_compatibility_validation_acceptance_cluster_20260521.md), [acceptance review](../review/archive/wp-acceptance/wp14_capability_composition_acceptance_review_20260521.md) |
| `WP15 Counterfactual Experiment Generation` | complete / accepted | Implement Phase 6 of the post-WP9 route: add replay envelopes, branch point and worldline metadata, counterfactual admission, scenario/adversary generation request surfaces, and experiment evidence ancestry without claiming full snapshot/restore or maintained rollout execution | [counterfactual experiment generation](archive/wp15_counterfactual_experiment_generation/counterfactual_experiment_generation_wp15_20260521.md), [replay envelope and branch point](archive/wp15_counterfactual_experiment_generation/wp15_replay_envelope_branch_point_cluster_20260521.md), [worldline branch metadata](archive/wp15_counterfactual_experiment_generation/wp15_worldline_branch_metadata_gate_cluster_20260521.md), [counterfactual admission](archive/wp15_counterfactual_experiment_generation/wp15_counterfactual_admission_cluster_20260521.md), [scenario/adversary generation](archive/wp15_counterfactual_experiment_generation/wp15_scenario_adversary_generation_surface_cluster_20260521.md), [experiment evidence bridge](archive/wp15_counterfactual_experiment_generation/wp15_experiment_evidence_bridge_cluster_20260521.md), [integration handoff](archive/wp15_counterfactual_experiment_generation/wp15_integration_acceptance_cluster_20260521.md), [acceptance review](../review/archive/wp-acceptance/wp15_counterfactual_experiment_generation_acceptance_review_20260521.md) |
| `WP16 Runtime Spine Consolidation` | complete / accepted | Complete the post-WP15 architecture optimization phase: inventory bypasses, define the maintained runtime spine, enforce the first strict `GAP-9` clock-domain cadence slice, migrate facade/batch consumers, classify legacy paths, and reduce documentation-sync drag through generated closure summaries while preserving the recorded residuals | [runtime spine consolidation](archive/wp16_runtime_spine_consolidation/runtime_spine_consolidation_wp16_20260521.md), [runtime spine inventory](archive/wp16_runtime_spine_consolidation/wp16_runtime_spine_inventory_cluster_20260521.md), [clock-domain enforcement](archive/wp16_runtime_spine_consolidation/wp16_clock_domain_enforcement_cluster_20260521.md), [facade/batch migration](archive/wp16_runtime_spine_consolidation/wp16_facade_batch_spine_migration_cluster_20260521.md), [legacy compatibility](archive/wp16_runtime_spine_consolidation/wp16_legacy_deprecation_compatibility_cluster_20260521.md), [documentation automation](archive/wp16_runtime_spine_consolidation/wp16_generated_documentation_automation_cluster_20260521.md), [integration handoff](archive/wp16_runtime_spine_consolidation/wp16_integration_acceptance_cluster_20260521.md), [acceptance review](../review/archive/wp-acceptance/wp16_runtime_spine_consolidation_acceptance_review_20260521.md) |
| `WP17 Stage 3 Runtime Materialization And Cleanup` | complete / accepted | Materialize the final Stage 3 selected runtime slices: facade-shaped batch reads, runnable cadence evidence, reference CPU fidelity admission, capability-gated spawn, and explicit-setup selected-entity counterfactual branch/compare while preserving legacy compatibility and full-worldline residuals | [stage3 runtime materialization and cleanup](archive/wp17_stage3_runtime_materialization_cleanup/stage3_runtime_materialization_cleanup_wp17_20260521.md), [fact ledger](archive/wp17_stage3_runtime_materialization_cleanup/wp17_fact_ledger_and_boundary_freeze_cluster_20260521.md), [business migration](archive/wp17_stage3_runtime_materialization_cleanup/wp17_facade_business_migration_cleanup_cluster_20260521.md), [multi-rate runtime](archive/wp17_stage3_runtime_materialization_cleanup/wp17_multirate_runtime_example_cluster_20260521.md), [fidelity provider runtime](archive/wp17_stage3_runtime_materialization_cleanup/wp17_fidelity_provider_runtime_cluster_20260521.md), [capability spawn runtime](archive/wp17_stage3_runtime_materialization_cleanup/wp17_capability_spawn_runtime_cluster_20260521.md), [counterfactual runtime closure](archive/wp17_stage3_runtime_materialization_cleanup/wp17_counterfactual_runtime_closure_cluster_20260521.md), [dispatch queue](archive/wp17_stage3_runtime_materialization_cleanup/wp17_subagent_dispatch_queue_20260521.md), [acceptance review](../review/archive/wp-acceptance/wp17_stage3_runtime_materialization_cleanup_acceptance_review_20260521.md) |
| `WP18 Runtime Ownership And C++ Hot Path Consolidation` | complete / accepted | Consolidate runtime ownership after WP17 by moving maintained execution truths and high-frequency Python paths toward C++/facade-owned surfaces while keeping compatibility APIs bounded | [runtime ownership and C++ hot path consolidation](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/runtime_ownership_cxx_hot_path_consolidation_wp18_20260521.md), [ownership fact ledger](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_ownership_fact_ledger_hot_path_map_cluster_20260521.md), [execution episode ownership sink](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_execution_episode_ownership_sink_cluster_20260521.md), [ScenarioLoader adapter split](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_scenario_loader_adapter_split_cluster_20260521.md), [facade contract hardening](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_facade_contract_hardening_cluster_20260521.md), [C++ hot path matrix](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_cxx_hot_path_migration_matrix_cluster_20260521.md), [integration handoff](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_integration_handoff_cluster_20260521.md), [dispatch queue](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_subagent_dispatch_queue_20260521.md), [acceptance review](../review/archive/wp-acceptance/wp18_runtime_ownership_cxx_hot_path_consolidation_acceptance_review_20260521.md) |
| `WP19 CUDA And Resident-State Mainline Alignment` | complete / accepted | Align existing CUDA helpers, device-resident output contracts, diagnostics boundaries, and resident-state sync/shard vocabulary without promoting exact GPU or maintained resident-state support by default | [CUDA and resident-state mainline alignment](archive/wp19_cuda_resident_state_alignment/cuda_resident_state_alignment_wp19_20260521.md), [fact ledger](archive/wp19_cuda_resident_state_alignment/wp19_cuda_resident_state_fact_ledger_cluster_20260521.md), [device output contract](archive/wp19_cuda_resident_state_alignment/wp19_device_resident_output_contract_cluster_20260521.md), [GPU helper diagnostics boundary](archive/wp19_cuda_resident_state_alignment/wp19_gpu_helper_diagnostics_boundary_cluster_20260521.md), [resident-state sync and shard contract](archive/wp19_cuda_resident_state_alignment/wp19_resident_state_sync_shard_contract_cluster_20260521.md), [first CUDA alignment slice](archive/wp19_cuda_resident_state_alignment/wp19_first_cuda_alignment_slice_cluster_20260521.md), [integration handoff](archive/wp19_cuda_resident_state_alignment/wp19_integration_handoff_cluster_20260521.md), [dispatch queue](archive/wp19_cuda_resident_state_alignment/wp19_subagent_dispatch_queue_20260521.md), [acceptance review](../review/archive/wp-acceptance/wp19_cuda_resident_state_alignment_acceptance_review_20260521.md) |
| `WP20 Public Capability-Platform Composition` | complete / accepted | Publicize the typed capability-platform setup path through validation-first admission/result contracts and compatibility-preserving materialization while keeping type-name spawning and scenario schema stable | [public capability-platform composition](archive/wp20_public_capability_platform_composition/public_capability_platform_composition_wp20_20260521.md), [fact ledger](archive/wp20_public_capability_platform_composition/wp20_public_capability_fact_ledger_cluster_20260521.md), [public typed spawn contract](archive/wp20_public_capability_platform_composition/wp20_public_typed_platform_spawn_contract_cluster_20260521.md), [runtime setup consume bridge](archive/wp20_public_capability_platform_composition/wp20_runtime_setup_consume_bridge_cluster_20260521.md), [facade/binding surface](archive/wp20_public_capability_platform_composition/wp20_facade_binding_public_surface_cluster_20260521.md), [compatibility/schema guard](archive/wp20_public_capability_platform_composition/wp20_compatibility_schema_guard_cluster_20260521.md), [integration handoff](archive/wp20_public_capability_platform_composition/wp20_integration_handoff_cluster_20260521.md), [dispatch queue](archive/wp20_public_capability_platform_composition/wp20_subagent_dispatch_queue_20260521.md), [acceptance review](../review/archive/wp-acceptance/wp20_public_capability_platform_composition_acceptance_review_20260521.md) |
| `WP21 Full Counterfactual Experiment Runtime` | owner-rejected / superseded by WP22 | Claimed closure attempted to turn accepted counterfactual contracts and selected runtime slices into maintained facade-owned experiment execution, scenario generation, evidence collection, and legacy cleanup, but owner rejected the closure because compatibility layers and incomplete subagent work remained. | [full counterfactual experiment runtime](archive/wp21_full_counterfactual_experiment_runtime/full_counterfactual_experiment_runtime_wp21_20260521.md), [fact ledger](archive/wp21_full_counterfactual_experiment_runtime/wp21_fact_ledger_residual_freeze_cluster_20260521.md), [snapshot/restore boundary](archive/wp21_full_counterfactual_experiment_runtime/wp21_snapshot_restore_worldline_boundary_cluster_20260521.md), [counterfactual rollout](archive/wp21_full_counterfactual_experiment_runtime/wp21_counterfactual_rollout_causal_difference_cluster_20260521.md), [scenario generation runtime](archive/wp21_full_counterfactual_experiment_runtime/wp21_scenario_intervention_generation_cluster_20260521.md), [experiment facade/evidence](archive/wp21_full_counterfactual_experiment_runtime/wp21_experiment_facade_evidence_cluster_20260521.md), [final cleanup](archive/wp21_full_counterfactual_experiment_runtime/wp21_final_cleanup_acceptance_cluster_20260521.md), [dispatch queue](archive/wp21_full_counterfactual_experiment_runtime/wp21_subagent_dispatch_queue_20260521.md), [disputed acceptance record](../review/archive/wp-acceptance/wp21_full_counterfactual_experiment_runtime_acceptance_review_20260522.md) |
| `WP22 Legacy Compatibility Retirement And Architecture Hardening` | owner-rejected / frozen; superseded by WP23 | Attempted to force-retire post-WP21 compatibility layers, but the owner stopped the stream after uncontrolled follow-up waves and partial/quarantine evidence drift. Its queue is historical only and must not be dispatched. | [legacy compatibility retirement](wp22_legacy_compatibility_retirement/legacy_compatibility_retirement_wp22_20260522.md), [remaining task clusters](wp22_legacy_compatibility_retirement/wp22_remaining_task_clusters_20260523.md), [dispatch queue](wp22_legacy_compatibility_retirement/wp22_subagent_dispatch_queue_20260522.md) |
| `WP23 Legacy Retirement Recovery And Reset` | closed / blocked | Froze WP22, classified current dirty work, forced delete-or-block decisions, recorded TaskOrder and public API exits as blocked, skipped implementation because no deletion-ready surface was identified, and closed as controlled blocked recovery. | [legacy retirement recovery](wp23_legacy_retirement_recovery/legacy_retirement_recovery_wp23_20260523.md) |
| `WP24 TaskOrder Maintained Business Migration` | closed / accepted | Replacement-backed TaskOrder business migration after WP23: maintained contract/export/Python business paths are integrated, the old public TaskOrder whole-shell compatibility surfaces are removed, and the canonical acceptance review is published. | [taskorder maintained business migration](wp24_taskorder_maintained_business_migration/taskorder_maintained_business_migration_wp24_20260524.md), [integration assessment and cleanup close-out](wp24_taskorder_maintained_business_migration/wp24_integration_assessment_and_next_dispatch_20260524.md), [acceptance review](../review/archive/wp-acceptance/wp24_taskorder_maintained_business_migration_acceptance_review_20260525.md) |
| `TM01 Architecture Closure Remediation` | audited-slice closed / residual handed off | Focused remediation after the implementation-level closure audit: `TM01-A`, `TM01-C`, and `TM01-D` are complete for the audited maintained-path slice; `TM01-B` recorded the launch-bridge residual that was later closed by TM03, while broader architecture, P7/raw-runtime, and WP24 canonical acceptance closure remain out of scope. | [TM01 entry](tm01_architecture_closure_remediation/README.md), [task clusters](tm01_architecture_closure_remediation/tm01_architecture_closure_task_clusters_20260524.md) |
| `TM02 WP24 Acceptance Closure` | temporary / closed | Closure lane that published WP24 canonical acceptance review and index sync without reopening implementation scope. | [TM02 entry](tm02_wp24_acceptance_closure/README.md), [acceptance review](../review/archive/wp-acceptance/wp24_taskorder_maintained_business_migration_acceptance_review_20260525.md) |
| `TM03 Launch Bridge Boundary` | temporary / closed | Bounded architecture lane that closed the two `systems -> SimulationKernel` weapon-release bridges recorded by TM01-B through a narrow `IWeaponReleaseService` seam. | [TM03 entry](tm03_launch_bridge_boundary/README.md), [task clusters](tm03_launch_bridge_boundary/tm03_launch_bridge_boundary_task_clusters_20260525.md) |

## TM03 Launch Bridge Boundary

Output:

- [TM03 Launch Bridge Boundary](tm03_launch_bridge_boundary/README.md)
- [TM03 Launch Bridge Boundary Task Clusters](tm03_launch_bridge_boundary/tm03_launch_bridge_boundary_task_clusters_20260525.md)

TM03 owned only the narrow launch-bridge residual recorded by TM01-B. It closed
that residual by adding `IWeaponReleaseService`, removing direct
`SimulationKernel` dependencies from the two release helper headers, and
recording focused architecture and weapon-release validation. Broader P7
launch/fire-control redesign and raw-runtime retirement remain outside TM03.

## TM02 WP24 Acceptance Closure

Output:

- [TM02 WP24 Acceptance Closure](tm02_wp24_acceptance_closure/README.md)
- [WP24 TaskOrder Maintained Business Migration Acceptance Review](../review/archive/wp-acceptance/wp24_taskorder_maintained_business_migration_acceptance_review_20260525.md)

TM02 is the serial closure lane for WP24. It published the canonical acceptance
review and index synchronization after focused validation, while keeping ground
runtime expansion and public raw-runtime retirement outside WP24. The TM01-B
launch bridge was still outside WP24 and was closed separately by TM03.

## TM01 Architecture Closure Remediation

Output:

- [TM01 Architecture Closure Remediation](tm01_architecture_closure_remediation/README.md)
- [TM01 Architecture Closure Task Clusters](tm01_architecture_closure_remediation/tm01_architecture_closure_task_clusters_20260524.md)

TM01 is closed for the audited implementation slice only; it is not a new
architecture WP and does not create canonical WP24 acceptance. `TM01-A` restored
the focused ground tasking-shell validation path, `TM01-C` synchronized WP24
provenance wording to the maintained `agent_shim.py` defaults, and `TM01-D`
published the focused validation and close/block recommendation.

Post-TM01 closure lanes have since closed two ledgered gaps without reopening
TM01: `TM02` published the WP24 canonical acceptance review, and `TM03` closed
the ledgered `systems -> SimulationKernel` launch-helper residual through
`IWeaponReleaseService`. Broader architecture closure, P7 launch/fire-control
contract redesign beyond that helper seam, public raw-runtime or compatibility
retirement, and ground runtime completion remain explicitly unclosed.

## WP24 TaskOrder Maintained Business Migration

Output:

- [WP24 TaskOrder Maintained Business Migration](wp24_taskorder_maintained_business_migration/taskorder_maintained_business_migration_wp24_20260524.md)

WP24 is the accepted replacement-backed implementation package opened after WP23
closed as `blocked`. It is not another recovery wave. The maintained
contract/export/Python business migration is integrated, the cleanup close-out
removes the old public TaskOrder whole-shell compatibility surfaces instead of
accepting them as residuals, and the canonical acceptance review is published.

## WP23 Legacy Retirement Recovery And Reset

Output:

- [WP23 Legacy Retirement Recovery And Reset](wp23_legacy_retirement_recovery/legacy_retirement_recovery_wp23_20260523.md)

WP23 is a reset, not a continuation wave. It froze WP22 queue entries as
historical evidence and stayed within the strict documentation budget: only the
canonical WP23 plan plus its Chinese companion were used. It audited the dirty
worktree, classified every legacy/compatibility surface, and closed as
`blocked` when deletion or migration proved unsafe inside the bounded
implementation window.

WP23 close-out map:

- `WP23-A Freeze And Salvage Audit` completed the dirty-work classification.
- `WP23-B Delete-Or-Block Table` completed the source-backed blocked/delete
  decision baseline.
- `WP23-C Tasking Single Representation` closed as `blocked` because TaskOrder
  maintained-batch work still coexists with public whole-shell read/write and
  observation exports.
- `WP23-D Public API Exit` closed as `blocked public API` for runtime/world/batch
  escape hatches, TaskOrder whole-shell APIs, observation tasking exports, and
  raw GPU/visual overloads.
- `WP23-E Minimal Implementation Batch` was skipped because no deletion-ready
  implementation surface was identified.
- `WP23-F Close-Out` completed with controlled `blocked` recovery, not legacy
  retirement acceptance.

## WP22 Legacy Compatibility Retirement And Architecture Hardening

Output:

- [WP22 Legacy Compatibility Retirement And Architecture Hardening](wp22_legacy_compatibility_retirement/legacy_compatibility_retirement_wp22_20260522.md)
- [WP22-A Retirement Fact Ledger And Kill List](wp22_legacy_compatibility_retirement/wp22_retirement_fact_ledger_cluster_20260522.md)
- [WP22-B Python Business Bypass Retirement](wp22_legacy_compatibility_retirement/wp22_python_business_bypass_retirement_cluster_20260522.md)
- [WP22-C Runtime Escape-Hatch And Legacy Mode Closure](wp22_legacy_compatibility_retirement/wp22_runtime_escape_hatch_closure_cluster_20260522.md)
- [WP22-D Command DTO And Legacy Surface Retirement](wp22_legacy_compatibility_retirement/wp22_command_dto_legacy_surface_retirement_cluster_20260522.md)
- [WP22-E Structural God-File Decomposition](wp22_legacy_compatibility_retirement/wp22_structural_god_file_decomposition_cluster_20260522.md)
- [WP22-F Guardrail And Acceptance Closure](wp22_legacy_compatibility_retirement/wp22_guard_acceptance_closure_cluster_20260522.md)
- [WP22 Subagent Dispatch Queue](wp22_legacy_compatibility_retirement/wp22_subagent_dispatch_queue_20260522.md)

WP22 is frozen and superseded by WP23. It was opened by the post-WP21
architecture refactoring audit, but its continuation stream failed the owner's
process bar after too many ad-hoc waves and partial/quarantine evidence loops.
These files remain useful provenance, not an active dispatch queue.

WP22 planned map:

- `WP22-A Retirement Fact Ledger And Kill List` starts first and corrects audit
  facts before implementation work depends on them.
- `WP22-B Python Business Bypass Retirement` owns tasking/profile/mission-command
  migration away from raw loader/runtime access.
- `WP22-C Runtime Escape-Hatch And Legacy Mode Closure` owns raw runtime,
  batch-runtime, loader-sim, and silent legacy-mode quarantine.
- `WP22-D Command DTO And Legacy Surface Retirement` owns C++ command, DTO, and
  setup legacy-surface retirement.
- `WP22-E Structural God-File Decomposition` owns behavior-preserving splits of
  monolithic contract/facade/window/factory files.
- `WP22-F Guardrail And Acceptance Closure` is serial and must fail closure if
  any unowned default legacy path remains.

## WP21 Full Counterfactual Experiment Runtime

Output:

- [WP21 Full Counterfactual Experiment Runtime](archive/wp21_full_counterfactual_experiment_runtime/full_counterfactual_experiment_runtime_wp21_20260521.md)
- [WP21-A Fact Ledger And Residual Freeze](archive/wp21_full_counterfactual_experiment_runtime/wp21_fact_ledger_residual_freeze_cluster_20260521.md)
- [WP21-B Snapshot Restore And Worldline Boundary](archive/wp21_full_counterfactual_experiment_runtime/wp21_snapshot_restore_worldline_boundary_cluster_20260521.md)
- [WP21-C Counterfactual Rollout And Causal Difference](archive/wp21_full_counterfactual_experiment_runtime/wp21_counterfactual_rollout_causal_difference_cluster_20260521.md)
- [WP21-D Scenario Intervention Generation Runtime](archive/wp21_full_counterfactual_experiment_runtime/wp21_scenario_intervention_generation_cluster_20260521.md)
- [WP21-E Experiment Facade And Evidence Collection](archive/wp21_full_counterfactual_experiment_runtime/wp21_experiment_facade_evidence_cluster_20260521.md)
- [WP21-F Final Cleanup And Acceptance Handoff](archive/wp21_full_counterfactual_experiment_runtime/wp21_final_cleanup_acceptance_cluster_20260521.md)
- [WP21 Subagent Dispatch Queue](archive/wp21_full_counterfactual_experiment_runtime/wp21_subagent_dispatch_queue_20260521.md)
- [Disputed WP21 Acceptance Record](../review/archive/wp-acceptance/wp21_full_counterfactual_experiment_runtime_acceptance_review_20260522.md)

WP21 is the disputed final planned refactor stage. It consumed WP15 contracts,
WP17's selected runtime branch/compare slice, WP18 ownership residuals, WP19
host-visible state boundaries, and WP20 typed setup evidence, but its claimed
closure was rejected by the owner on `2026-05-22`. It must not be used as proof
that legacy compatibility layers have retired.

WP21 disputed map:

- `WP21-A Fact Ledger And Residual Freeze` starts first and freezes source facts.
- `WP21-B Snapshot Restore And Worldline Boundary` owns bounded host-owned
  snapshot/restore and worldline identity.
- `WP21-D Scenario Intervention Generation Runtime` can run in parallel with B
  after A and owns deterministic generated artifacts plus loader boundary guards.
- `WP21-C Counterfactual Rollout And Causal Difference` waits for B and owns
  parent/branch rollout.
- `WP21-E Experiment Facade And Evidence Collection` waits for C/D and owns the
  public orchestration/evidence surface.
- `WP21-F Final Cleanup And Acceptance Handoff` failed the owner-acceptance bar;
  the archived acceptance review is historical only and superseded by WP22.

## WP20 Public Capability-Platform Composition

Output:

- [WP20 Public Capability-Platform Composition](archive/wp20_public_capability_platform_composition/public_capability_platform_composition_wp20_20260521.md)
- [WP20-A Public Capability Fact Ledger](archive/wp20_public_capability_platform_composition/wp20_public_capability_fact_ledger_cluster_20260521.md)
- [WP20-B Public Typed Platform Spawn Contract](archive/wp20_public_capability_platform_composition/wp20_public_typed_platform_spawn_contract_cluster_20260521.md)
- [WP20-C Runtime Setup Consume Bridge](archive/wp20_public_capability_platform_composition/wp20_runtime_setup_consume_bridge_cluster_20260521.md)
- [WP20-D Facade And Binding Public Surface](archive/wp20_public_capability_platform_composition/wp20_facade_binding_public_surface_cluster_20260521.md)
- [WP20-E Compatibility And Schema Guard](archive/wp20_public_capability_platform_composition/wp20_compatibility_schema_guard_cluster_20260521.md)
- [WP20-F Integration And Handoff](archive/wp20_public_capability_platform_composition/wp20_integration_handoff_cluster_20260521.md)
- [WP20 Subagent Dispatch Queue](archive/wp20_public_capability_platform_composition/wp20_subagent_dispatch_queue_20260521.md)
- [WP20 Acceptance Review](../review/archive/wp-acceptance/wp20_public_capability_platform_composition_acceptance_review_20260521.md)

WP20 is the accepted third frozen post-WP17 stage. It consumes WP14's capability
composition vocabulary and WP17's internal resolved-plan spawn path, then
publicizes typed platform setup through validation-first admission/result
evidence. It must preserve `spawn_unit(type_name)`,
`WorldSpawnRequest.type_name`, legacy scenario setup, and backend
`RuntimeCapabilities` separation.

WP20 current map:

- `WP20-A Public Capability Fact Ledger` freezes source-backed facts before
  implementation.
- `WP20-B Public Typed Platform Spawn Contract` owns admission/result DTO shape
  and ordering rules.
- `WP20-E Compatibility And Schema Guard` updates WP14 additive-only guards into
  WP20 validation-first publicization guards.
- `WP20-C Runtime Setup Consume Bridge` has returned and passed focused
  validation.
- `WP20-D Facade And Binding Public Surface` has returned and passed focused
  validation.
- `WP20-F Integration And Handoff` has closed as the serial closure lane.

## WP19 CUDA And Resident-State Mainline Alignment

Output:

- [WP19 CUDA And Resident-State Mainline Alignment](archive/wp19_cuda_resident_state_alignment/cuda_resident_state_alignment_wp19_20260521.md)
- [WP19-A CUDA / Resident-State Fact Ledger](archive/wp19_cuda_resident_state_alignment/wp19_cuda_resident_state_fact_ledger_cluster_20260521.md)
- [WP19-B Device-Resident Output Contract Pre-Gate](archive/wp19_cuda_resident_state_alignment/wp19_device_resident_output_contract_cluster_20260521.md)
- [WP19-C GPU Helper Diagnostics Boundary](archive/wp19_cuda_resident_state_alignment/wp19_gpu_helper_diagnostics_boundary_cluster_20260521.md)
- [WP19-D Resident-State Sync And Shard Contract](archive/wp19_cuda_resident_state_alignment/wp19_resident_state_sync_shard_contract_cluster_20260521.md)
- [WP19-E First CUDA Alignment Slice](archive/wp19_cuda_resident_state_alignment/wp19_first_cuda_alignment_slice_cluster_20260521.md)
- [WP19-F Integration And Handoff](archive/wp19_cuda_resident_state_alignment/wp19_integration_handoff_cluster_20260521.md)
- [WP19 Subagent Dispatch Queue](archive/wp19_cuda_resident_state_alignment/wp19_subagent_dispatch_queue_20260521.md)
- [WP19 Acceptance Review](../review/archive/wp-acceptance/wp19_cuda_resident_state_alignment_acceptance_review_20260521.md)

WP19 is the accepted second frozen post-WP17 stage. It consumes the accepted
WP18 runtime-ownership boundary and aligns existing CUDA helpers,
device-resident output metadata, and resident-state sync vocabulary with the
maintained facade/backend profile model. It does not promote exact GPU
world-step or maintained resident-state support by default.

WP19 workstream map:

- `WP19-A CUDA / Resident-State Fact Ledger` freezes current source/test facts
  before implementation.
- `WP19-B Device-Resident Output Contract Pre-Gate` defines fail-closed output
  metadata and DTO placement.
- `WP19-C GPU Helper Diagnostics Boundary` prevents helper/probe availability
  from becoming accidental maintained capability evidence.
- `WP19-D Resident-State Sync And Shard Contract` maps state ownership, shard,
  sync, stale-read, and export rules to runtime evidence.
- `WP19-E First CUDA Alignment Slice` is held until A-D identify one safe
  bounded helper/output path.
- `WP19-F Integration And Handoff` remains serial closure after evidence streams
  return.
- [WP19 Acceptance Review](../review/archive/wp-acceptance/wp19_cuda_resident_state_alignment_acceptance_review_20260521.md)

## WP18 Runtime Ownership And C++ Hot Path Consolidation

Output:

- [WP18 Runtime Ownership And C++ Hot Path Consolidation](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/runtime_ownership_cxx_hot_path_consolidation_wp18_20260521.md)
- [WP18-A Ownership Fact Ledger And Hot-Path Map](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_ownership_fact_ledger_hot_path_map_cluster_20260521.md)
- [WP18-B Execution Episode Ownership Sink](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_execution_episode_ownership_sink_cluster_20260521.md)
- [WP18-C ScenarioLoader Adapter Split](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_scenario_loader_adapter_split_cluster_20260521.md)
- [WP18-D Facade Contract Hardening](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_facade_contract_hardening_cluster_20260521.md)
- [WP18-E C++ Hot Path Migration Matrix](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_cxx_hot_path_migration_matrix_cluster_20260521.md)
- [WP18-F Integration And Handoff](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_integration_handoff_cluster_20260521.md)
- [WP18 Subagent Dispatch Queue](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_subagent_dispatch_queue_20260521.md)
- [WP18 Acceptance Review](../review/archive/wp-acceptance/wp18_runtime_ownership_cxx_hot_path_consolidation_acceptance_review_20260521.md)

WP18 is the accepted first frozen post-WP17 stage. It focuses on runtime
ownership and C++ hot-path consolidation. CUDA/resident-state alignment, public
capability-platform composition, and full counterfactual runtime work remain
routed to WP19, WP20, and WP21 rather than claimed here.

WP18 workstream map:

- `WP18-A Ownership Fact Ledger And Hot-Path Map` freezes current source/test
  facts before implementation.
- `WP18-B Execution Episode Ownership Sink` moves one maintained
  execution-episode slice behind C++/facade-owned evidence.
- `WP18-C ScenarioLoader Adapter Split` separates scenario/content adaptation
  from runtime ownership and frontend helper responsibilities.
- `WP18-D Facade Contract Hardening` prevents maintained callers from
  regressing to raw runtime/world-handle reads.
- `WP18-E C++ Hot Path Migration Matrix` ranks reward/termination,
  route/approach, request build/consume, and related hot paths, then implements
  one bounded first slice if safe.
- `WP18-F Integration And Handoff` remains serial closure after implementation
  streams return.

## WP17 Stage 3 Runtime Materialization And Cleanup

Output:

- [WP17 Stage 3 Runtime Materialization And Cleanup](archive/wp17_stage3_runtime_materialization_cleanup/stage3_runtime_materialization_cleanup_wp17_20260521.md)
- [WP17-A Fact Ledger And Boundary Freeze](archive/wp17_stage3_runtime_materialization_cleanup/wp17_fact_ledger_and_boundary_freeze_cluster_20260521.md)
- [WP17-B Facade Business Migration And Compatibility Cleanup](archive/wp17_stage3_runtime_materialization_cleanup/wp17_facade_business_migration_cleanup_cluster_20260521.md)
- [WP17-C Multi-Rate Runtime Example](archive/wp17_stage3_runtime_materialization_cleanup/wp17_multirate_runtime_example_cluster_20260521.md)
- [WP17-D Fidelity Provider Runtime](archive/wp17_stage3_runtime_materialization_cleanup/wp17_fidelity_provider_runtime_cluster_20260521.md)
- [WP17-E Capability Spawn Runtime Promotion](archive/wp17_stage3_runtime_materialization_cleanup/wp17_capability_spawn_runtime_cluster_20260521.md)
- [WP17-F Counterfactual Runtime Slice And Closure](archive/wp17_stage3_runtime_materialization_cleanup/wp17_counterfactual_runtime_closure_cluster_20260521.md)
- [WP17 Subagent Dispatch Queue](archive/wp17_stage3_runtime_materialization_cleanup/wp17_subagent_dispatch_queue_20260521.md)
- [WP17 Acceptance Review](../review/archive/wp-acceptance/wp17_stage3_runtime_materialization_cleanup_acceptance_review_20260521.md)

WP17 is the accepted final Stage 3 runtime-materialization and cleanup task
family. It uses current code facts to split the remaining runtime work into bounded
selected-slice streams, then keeps the residuals honest where full-worldline or
full-provider support is still absent.

WP17 workstream map:

- `WP17-A Fact Ledger And Boundary Freeze` locked current code facts and
  residual boundaries before runtime edits.
- `WP17-B Facade Business Migration And Compatibility Cleanup` moved maintained
  training/batch reads to facade-shaped env/adapter methods and guards direct
  `batch_runtime` reads as compatibility-only.
- `WP17-C Multi-Rate Runtime Example` materialized the selected architecture §8
  cadence slice with hold/expiry/barrier evidence.
- `WP17-D Fidelity Provider Runtime` added conservative facade-owned reference
  CPU fidelity admission and fail-closed provider rejection.
- `WP17-E Capability Spawn Runtime Promotion` promotes the internal capability
  resolution chain while preserving type-name compatibility.
- `WP17-F Counterfactual Runtime Slice And Closure` implements explicit-setup
  selected-entity branch/compare; arbitrary live-world clone and full
  counterfactual orchestration remain residuals.

## WP16 Runtime Spine Consolidation

Output:

- [WP16 Runtime Spine Consolidation](archive/wp16_runtime_spine_consolidation/runtime_spine_consolidation_wp16_20260521.md)
- [WP16-A Runtime Spine Inventory And Bypass Map](archive/wp16_runtime_spine_consolidation/wp16_runtime_spine_inventory_cluster_20260521.md)
- [WP16-B Clock-Domain Enforcement And Merge Trace](archive/wp16_runtime_spine_consolidation/wp16_clock_domain_enforcement_cluster_20260521.md)
- [WP16-C Facade And Batch Path Spine Migration](archive/wp16_runtime_spine_consolidation/wp16_facade_batch_spine_migration_cluster_20260521.md)
- [WP16-D Legacy Path Deprecation And Compatibility Gates](archive/wp16_runtime_spine_consolidation/wp16_legacy_deprecation_compatibility_cluster_20260521.md)
- [WP16-E Generated Documentation And Closure Automation](archive/wp16_runtime_spine_consolidation/wp16_generated_documentation_automation_cluster_20260521.md)
- [WP16-F Integration And Acceptance Handoff](archive/wp16_runtime_spine_consolidation/wp16_integration_acceptance_cluster_20260521.md)

WP16 opens the architecture-optimization phase after the post-WP9 route is
complete. It consumes WP10-WP15 boundaries and turns them into a maintained
runtime spine. WP16 is accepted as the selected-slice runtime-spine
consolidation increment, and the residual register is preserved in the WP16
acceptance review:

```text
setup/admission request
  -> scheduling-window input injection
  -> clock-domain trigger and skip decision
  -> manifest-derived node execution
  -> barrier and event evidence
  -> observation/facade export
  -> training, scenario, and experiment consumer
```

WP16 workstream map:

- `WP16-A Runtime Spine Inventory And Bypass Map` inventories maintained,
  compatibility, diagnostics-only, deprecated, blocked, and unknown runtime
  paths before code migration starts.
- `WP16-B Clock-Domain Enforcement And Merge Trace` promotes `GAP-9` into the
  selected runtime-spine slice so non-triggered clock domains skip, defer, or
  reject with evidence instead of executing silently.
- `WP16-C Facade And Batch Path Spine Migration` routes maintained facade,
  batch, training, scenario, and experiment consumers toward the accepted
  runtime-window evidence spine.
- `WP16-D Legacy Path Deprecation And Compatibility Gates` classifies raw
  runtime, direct state, legacy spawn, diagnostics, and compatibility paths with
  guard tests and replacement evidence.
- `WP16-E Generated Documentation And Closure Automation` reduces manual
  README/review/index synchronization by adding machine-readable status and
  generated closure-summary hints without replacing acceptance authority.
- `WP16-F Integration And Acceptance Handoff` is the serial validation,
  residual, acceptance-review, README/route, and bilingual closure lane after
  A-E become mergeable.

WP16 is complete / accepted. The implementation boundary remains narrow:
global scheduler rewrite, full multi-rate support, public legacy API deletion,
and maintained independent-domain merge success are still out of scope.

## WP15 Counterfactual Experiment Generation

Output:

- [WP15 Counterfactual Experiment Generation](archive/wp15_counterfactual_experiment_generation/counterfactual_experiment_generation_wp15_20260521.md)
- [WP15-A Replay Envelope And Branch Point Contract](archive/wp15_counterfactual_experiment_generation/wp15_replay_envelope_branch_point_cluster_20260521.md)
- [WP15-B Worldline Branch Metadata Gate](archive/wp15_counterfactual_experiment_generation/wp15_worldline_branch_metadata_gate_cluster_20260521.md)
- [WP15-C Counterfactual Request Admission](archive/wp15_counterfactual_experiment_generation/wp15_counterfactual_admission_cluster_20260521.md)
- [WP15-D Scenario And Adversary Generation Request Surface](archive/wp15_counterfactual_experiment_generation/wp15_scenario_adversary_generation_surface_cluster_20260521.md)
- [WP15-E Experiment Evidence And Capability Profiling Bridge](archive/wp15_counterfactual_experiment_generation/wp15_experiment_evidence_bridge_cluster_20260521.md)
- [WP15-F Integration And Acceptance Handoff](archive/wp15_counterfactual_experiment_generation/wp15_integration_acceptance_cluster_20260521.md)

WP15 accepts Phase 6 of the post-WP9 route. It consumes WP8 learning-face
vocabulary and the accepted WP10-WP14 causal, facade, agency, backend/fidelity,
and capability evidence. The first target is not full counterfactual rollout;
it is the evidence boundary that makes replay envelopes, branch points,
worldline metadata, generation requests, and experiment evidence ancestry
machine-checkable before any branch can mutate authoritative runtime state.

WP15 workstream map:

- `WP15-A Replay Envelope And Branch Point Contract` defines deterministic
  replay envelope and branch point vocabulary with seed, snapshot, barrier,
  event-order, and facade provenance evidence.
- `WP15-B Worldline Branch Metadata Gate` names parent/child worldline metadata,
  mutation intent, provenance, and unsupported-restore boundaries.
- `WP15-C Counterfactual Request Admission` admits or rejects counterfactual
  requests behind replay, branch, authority, backend/fidelity, and capability
  evidence.
- `WP15-D Scenario And Adversary Generation Request Surface` adds deterministic
  generation request schemas and non-mutation guards for scenario/adversary
  inputs.
- `WP15-E Experiment Evidence And Capability Profiling Bridge` links experiment
  runs, comparisons, generated inputs, capability profiles, backend profiles,
  and capability evidence without score-to-truth promotion.
- `WP15-F Integration And Acceptance Handoff` is the serial validation,
  residual, acceptance-review, README/route, and bilingual closure lane.

`WP15-A` through `WP15-E` first slices are accepted. `WP15-F` completed the
closure lane for validation, residuals, acceptance review, README/route sync,
and bilingual handoff.

## WP14 Capability Composition

Output:

- [WP14 Capability Composition](archive/wp14_capability_composition/capability_composition_wp14_20260521.md)
- [WP14-A Capability Bundle Contract](archive/wp14_capability_composition/wp14_capability_bundle_contract_cluster_20260521.md)
- [WP14-B Content Definition Lowering](archive/wp14_capability_composition/wp14_content_definition_lowering_cluster_20260521.md)
- [WP14-C Spawn Resolution Bridge](archive/wp14_capability_composition/wp14_spawn_resolution_bridge_cluster_20260521.md)
- [WP14-D Additive Facade Setup DTO](archive/wp14_capability_composition/wp14_additive_facade_setup_dto_cluster_20260521.md)
- [WP14-E Capability Effects Materialization](archive/wp14_capability_composition/wp14_capability_effects_materialization_cluster_20260521.md)
- [WP14-F Compatibility Validation And Acceptance Handoff](archive/wp14_capability_composition/wp14_compatibility_validation_acceptance_cluster_20260521.md)
- [WP14 acceptance review](../review/archive/wp-acceptance/wp14_capability_composition_acceptance_review_20260521.md)

WP14 accepts Phase 5 of the post-WP9 route. It consumes WP2/WP9 contract
vocabulary and WP10-WP13 runtime, facade, agency, and backend evidence, then
turns implicit platform composition into bounded, testable implementation
streams. The first slice preserves `spawn_unit(type_name)` and
`WorldSpawnRequest.type_name` compatibility while introducing
`type_name -> CapabilityBundle template -> ResolvedPlatformSpawnPlan` resolution
before materialization.

WP14 workstream map:

- `WP14-A Capability Bundle Contract` defines platform-semantic `Capability`,
  `CapabilityBundle`, capability-family vocabulary, and resolved-plan evidence
  without colliding with backend `RuntimeCapabilities`.
- `WP14-B Content Definition Lowering` maps existing content/factory evidence
  into deterministic capability templates and resolved spawn plans.
- `WP14-C Spawn Resolution Bridge` routes existing spawn paths through
  resolution before materialization while preserving public compatibility.
- `WP14-D Additive Facade Setup DTO` prepares future typed platform spawn
  requests as additive setup vocabulary, not a mandatory replacement.
- `WP14-E Capability Effects Materialization` binds capability families to
  existing ECS/component materialization evidence and unsupported-effect
  reasons without adding new tactical behavior.
- `WP14-F Compatibility Validation And Acceptance Handoff` is the serial
  validation, residual, acceptance-review, README/route, and bilingual closure
  lane after A-E are mergeable.

`WP14-A` through `WP14-F` are accepted. The accepted boundary is a
compatibility bridge: type-name setup remains maintained, typed platform spawn
DTOs are additive, and public `spawn_platform({capabilities...})`,
scenario-schema migration, backend/fidelity promotion, and broad spawn rewrites
remain future gated work.

## WP13 Backend Fidelity Expansion

Output:

- [WP13 Backend Fidelity Expansion](archive/wp13_backend_fidelity_expansion/backend_fidelity_expansion_wp13_20260520.md)
- [WP13-A Runtime Capability Query And Rejection Surface](archive/wp13_backend_fidelity_expansion/wp13_runtime_capability_query_cluster_20260520.md)
- [WP13-B Backend Profile Registry Runtime Gate](archive/wp13_backend_fidelity_expansion/wp13_backend_profile_registry_gate_cluster_20260520.md)
- [WP13-C Parity Budget Evidence Gate](archive/wp13_backend_fidelity_expansion/wp13_parity_budget_evidence_gate_cluster_20260520.md)
- [WP13-D Fidelity Profile Request Gate](archive/wp13_backend_fidelity_expansion/wp13_fidelity_profile_request_gate_cluster_20260520.md)
- [WP13-E Facade And Binding Proof](archive/wp13_backend_fidelity_expansion/wp13_facade_binding_proof_cluster_20260520.md)
- [WP13-F Integration And Acceptance Handoff](archive/wp13_backend_fidelity_expansion/wp13_integration_acceptance_cluster_20260520.md)
- [WP13 acceptance review](../review/archive/wp-acceptance/wp13_backend_fidelity_expansion_acceptance_review_20260520.md)

WP13 accepts Phase 4 of the post-WP9 route. It consumes WP6/WP7 backend profile
policy/materialization and WP10-WP12 causal, provenance, and agency evidence,
then turns backend/fidelity support into queryable, rejectable, test-backed
runtime facts without promoting exact GPU, resident-state, shadow, or
multi-fidelity support.

WP13 workstream map:

- `WP13-A Runtime Capability Query And Rejection Surface` adds conservative
  capability metadata and stable unsupported reasons while preserving false
  support defaults.
- `WP13-B Backend Profile Registry Runtime Gate` makes the accepted backend
  profile seed records code-owned and validates maintained/candidate/diagnostics
  boundaries.
- `WP13-C Parity Budget Evidence Gate` makes profile-owned parity budget
  records and missing/incompatible budget rejection machine-checkable.
- `WP13-D Fidelity Profile Request Gate` admits fidelity labels as requests
  bound to profile, budget, model scope, validation, and evidence, not support
  claims.
- `WP13-E Facade And Binding Proof` proves query and rejection behavior through
  maintained facade and Python binding surfaces.
- `WP13-F Integration And Acceptance Handoff` is the serial validation,
  residual, acceptance-review, README/index, and bilingual closure lane.

`WP13-A` through `WP13-F` are accepted. The accepted baseline admits only CPU
exact reference fidelity requests and keeps exact GPU, resident-state, shadow,
adaptive fidelity, learned provider runtime, and maintained multi-fidelity
support out of scope.

Commit messages for this phase should use capability/result language, not
internal work-package labels.

## WP12 Information And Agency Enforcement

Output:

- [WP12 Information And Agency Enforcement](archive/wp12_information_agency_enforcement/information_agency_enforcement_wp12_20260520.md)
- [WP12-A Law 14 Read-Side Enforcement](archive/wp12_information_agency_enforcement/wp12_law14_read_side_enforcement_cluster_20260520.md)
- [WP12-B Agency Role Authority Boundary](archive/wp12_information_agency_enforcement/wp12_agency_role_authority_cluster_20260520.md)
- [WP12-C Information Transformation Surface](archive/wp12_information_agency_enforcement/wp12_information_transformation_surface_cluster_20260520.md)
- [WP12-D Intent Injection Authority Guard](archive/wp12_information_agency_enforcement/wp12_intent_injection_authority_guard_cluster_20260520.md)
- [WP12-E Integration And Acceptance Handoff](archive/wp12_information_agency_enforcement/wp12_integration_acceptance_cluster_20260520.md)

WP12 accepts Phase 3 of the post-WP9 route. It consumes WP10 causal evidence and
WP11 provenance/pre-gates, then turns `GAP-5`, `GAP-6`, and `GAP-7` into
test-backed read-side, role/authority, and information-transformation gates.

WP12 workstream map:

- `WP12-A Law 14 Read-Side Enforcement` promotes maintained consumer pre-gates
  into focused packet/belief read-side enforcement while preserving explicit
  diagnostics-only truth paths.
- `WP12-B Agency Role Authority Boundary` validates `AgentRole` authority scope,
  information source, decision-model reference, and action interface before
  maintained outputs are authorized.
- `WP12-C Information Transformation Surface` makes the selected information
  transformation chain machine-checkable without rewriting every producer.
- `WP12-D Intent Injection Authority Guard` integrates A-C so maintained
  `DecisionBelief -> ActionIntentPacket` / `CoordinationIntentPacket` paths use
  provenance, authority metadata, timing metadata, and facade-compatible
  injection.
- `WP12-E Integration And Acceptance Handoff` is the serial validation,
  residual, acceptance-review, README/index, and bilingual closure lane.

`WP12-B`, `WP12-C`, and `WP12-D` are the highest-reasoning streams. `WP12-A`,
`WP12-B`, and `WP12-C` may start in parallel with disjoint write scopes; `WP12-D`
should wait for their validator/vocabulary surfaces; `WP12-E` runs last.

### WP2.5 Workstream Map

WP2.5 is a freeze document, but the follow-on work is split into bounded
streams:

- `WP2.5-F StageNodeManifest Schema` first:
  [manifest/event cluster](archive/wp25_scheduler_semantics/wp25_manifest_event_cluster_20260519.md).
- `WP2.5-A Event Ordering and ID Rules`, `WP2.5-B State Shard Versioning`, and
  `WP2.5-C Barrier Visibility` in parallel after the manifest vocabulary is
  stable:
  [state/barrier cluster](archive/wp25_scheduler_semantics/wp25_state_barrier_cluster_20260519.md).
- `WP2.5-D Clock-Domain Merge` after those semantic rules are stable.
- `WP2.5-E Deterministic Replay Contract` after the scheduler semantics are
  frozen:
  [clock/replay cluster](archive/wp25_scheduler_semantics/wp25_clock_replay_cluster_20260519.md).
- `WP2.5-G Integration and Index Sync` last, as the serial publication pass.

`WP2.5-D` and `WP2.5-E` are the highest-reasoning streams.

## WP7.5 Training Path Facade Bridge

Output:

- [WP7.5 Training Path Facade Bridge](archive/wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.md)

`WP7.5` is the missing bridge between accepted simulation-side facade
contracts and planned learning-facing contract vocabulary. It does not replace
`WP8`; instead, it migrates the maintained training mainline away from the
`RuntimeFacade.runtime()` escape hatch and toward
`RuntimeFacade.step_execution_batch()` plus
`RuntimeFacade.export_observation_packet()`.

`WP7.5` workstream map:

- `WP7.5-A Step Execution Mainline` migrates maintained batch stepping onto
  `ExecutionBatchStepRequest` / `ExecutionBatchStepResult`.
- `WP7.5-B Observation Packet Mainline` migrates maintained observation reads
  onto `ObservationBatchRequest` / `ObservationBatchPacket`.
- `WP7.5-C Compatibility Escape Hatch Reduction` narrows raw runtime access to
  explicit compatibility or diagnostics seams.
- `WP7.5-D Validation And Integration Sync` is serial and publishes the bridge
  line into README, review, and `WP8` references.

`WP7.5-A` and `WP7.5-B` are the highest-reasoning streams because they change
the maintained training mainline while preserving current facade and
information-state rules.

`WP7.5` work should use the project subagent rules in
[Subagent Usage Policy](../../standards/governance/subagent_usage_policy.md)
when it is split across workers.

## WP8 SCAL Learning Face

Output:

- [WP8 SCAL Learning Face task family](archive/wp8_learning_face/learning_face_wp8_20260520.md)
- [WP8-A curriculum and scenario generation cluster](archive/wp8_learning_face/wp8_curriculum_scenario_generation_cluster_20260520.md)
- [WP8-B evaluation and capability profiling cluster](archive/wp8_learning_face/wp8_evaluation_capability_profiling_cluster_20260520.md)
- [WP8-C world-model interface and learning evidence cluster](archive/wp8_learning_face/wp8_world_model_interface_and_learning_evidence_cluster_20260520.md)
- [WP8 learning face acceptance review](../review/archive/wp-acceptance/wp8_learning_face_acceptance_review_20260520.md)

WP8 gives the deferred SCAL learning face an accepted bounded task family. It does not
add a second runtime lifecycle. It turns curriculum, evaluation, capability
profiling, scenario generation, and learning evidence into explicit experiment
and planning contracts that remain separate from the authoritative simulation
layer.

WP8 workstream map:

- `WP8-A Curriculum And Scenario Generation` defines how scenarios, seeds,
  curriculum phases, and generation requests are selected and versioned.
- `WP8-B Evaluation And Capability Profiling` defines benchmark protocols,
  profile schemas, score attribution, and capability evidence.
- `WP8-C World-Model Interface And Learning Evidence` defines how learning
  consumes facade-shaped observations and records evidence without becoming a
  truth source.
- `WP8-D Integration And Index Sync` is serial and updates task/review
  indexes, cross-references, and bilingual alignment.

`WP8-B` and `WP8-C` are the highest-reasoning streams because they have to
keep learning outputs comparable without drifting into hidden truth ownership.

## WP9 Contract And Infrastructure Closure

Output:

- [WP9 Contract And Infrastructure Closure](archive/wp9_contract_infrastructure_closure/contract_infrastructure_closure_wp9_20260520.md)
- [WP9-A DTO Promotion Batch 1](archive/wp9_contract_infrastructure_closure/wp9_dto_promotion_batch1_cluster_20260520.md)
- [WP9-B DTO Promotion Batch 2](archive/wp9_contract_infrastructure_closure/wp9_dto_promotion_batch2_cluster_20260520.md)
- [WP9-C Infrastructure Closure](archive/wp9_contract_infrastructure_closure/wp9_infrastructure_closure_cluster_20260520.md)
- [WP9-D Guard Enforcement](archive/wp9_contract_infrastructure_closure/wp9_guard_enforcement_cluster_20260520.md)
- [WP9-E Integration And Index Sync](archive/wp9_contract_infrastructure_closure/wp9_integration_and_index_sync_cluster_20260520.md)
- [WP9 acceptance review](../review/archive/wp-acceptance/wp9_contract_infrastructure_closure_acceptance_review_20260520.md)

WP9 compresses the deferred items from accepted `WP3-WP8` reviews into one
closure package. It promotes typed DTO surfaces, patches small infrastructure
gaps, adds explicit guard allowlists, and keeps the post-WP9 roadmap separate
from the accepted closure.

WP9 is accepted with one tracked residual: `INF-6` real missile terminal
effects capture remains a later owner task because the current damage system
lacks a narrow maintained recorder seam. The residual is documented in the WP3
task family and WP9 acceptance review.

WP9 workstream map:

- `WP9-A DTO Promotion Batch 1` promotes `RewardReport`, `TerminationSpec`,
  `ObservationBatchPacket` metadata, and `ObservationViewSpec`.
- `WP9-B DTO Promotion Batch 2` promotes `ActionIntentPacket`,
  `CoordinationIntentPacket`, `AgentRole`, and `DecisionBelief`.
- `WP9-C Infrastructure Closure` closes naming, diagnostics, capability
  trigger, manifest registry, facade split, and WP3 event residual items.
- `WP9-D Guard Enforcement` adds the documented guard allowlist and binding
  smoke promotion.
- `WP9-E Integration And Index Sync` is the serial publication and acceptance
  pass.

`WP9-A`, `WP9-B`, `WP9-D`, and `WP9-E` are accepted. `WP9-C` is accepted with
the `INF-6` residual explicitly tracked; all other WP9 infrastructure items are
closed.

## WP0 Scope

WP0 is documentation-only:

- add the strict architecture baseline,
- open this task subproject,
- update navigation entries,
- avoid code changes,
- avoid deciding exact field layouts before WP1/WP2 evidence is collected.

Exit criteria:

1. `docs/plan/architecture` has a clear architecture authority document.
2. `docs/task` has a simulation architecture entry.
3. The task entry explains why weapon work should be treated as a cross-domain
   engagement pilot with multiple clock domains, not a standalone vertical
   stack.

## WP1 Pipeline Inventory

WP1 should inspect the live code and produce a table that maps existing assets
onto the canonical semantic lifecycle:

- `P0 ContentCompile`
- `P1 WorldSetup`
- `P2 TaskingIntent`
- `P3 CommandDelivery`
- `P4 PlatformControl`
- `P5 PhysicsStep`
- `P6 SenseTrackLink`
- `P7 FireControlLaunch`
- `P8 MunitionLifecycle`
- `P9 EffectsDamage`
- `P10 ObservationExport`

Expected evidence:

- relevant `src/components/*` DTOs,
- `src/systems/*` stage behavior,
- `src/models/*` model implementations,
- `src/core/engine/*` orchestration surfaces,
- `src/runtime/facade/*` request/result coverage,
- Python adapter compatibility paths,
- tests that already enforce or violate the intended boundary,
- evidence of clock domains, event queues, state-store feedback, or current
  cross-stage coupling.

WP1 should not implement new code unless a small doc or test fixture is required
to complete the inventory.

## WP2 Contract Freeze

Input:

- [WP1 pipeline inventory](archive/wp1_pipeline_inventory/pipeline_inventory_wp1_20260519.md)

Output:

- [WP2 contract freeze](archive/wp2_contract_freeze/contract_freeze_wp2_20260519.md)

WP2 should turn the inventory into a scoped contract plan. It should decide:

1. which packet families already exist,
2. which are compatibility aggregations,
3. which need new facade-level request/result APIs,
4. which should stay component-only,
5. which stage nodes need explicit read/write sets, clock domains, latency
   policies, and sync policies,
6. which same-window DAG edges are data-derived versus cross-window feedback,
7. which state shards need versioning now or later for partial sync,
8. which event families need deterministic `(timestamp, priority, event_id)`
   ordering,
9. which clock domains can use default nested triggering and which need an
   explicit merge policy,
10. which Python calls need adapter compatibility,
11. which observation schemas are policy/test-owned `ObservationViewSpec`
    variants versus simulation-owned state exports,
12. how policy action cadence maps onto `P3/P4/P5` using `ActionIntentPacket`
    and `ActionHoldPolicy`,
13. how reward is split between simulation facts and experiment shaping using
    the fact/shaping criterion from the architecture baseline,
14. how `terminated` and `truncated` reasons are attributed to simulation,
    policy, or orchestration sources,
15. which side owns authoritative episode phase and which side only mirrors it
    for Gymnasium, batch, replay, or CI APIs,
16. how scripted, learned, and human coordination directors inject tasking or
    command intent without mutating raw ECS state,
17. which `merge_policy` each cross-layer producer uses,
18. which scheduling-window injection semantics each action or coordination
    path expects,
19. which observation schema changes are minor-compatible versus
    major-incompatible.

The expected output is a freeze document, not implementation.

Architecture closure note:

- The architecture framework is closed at the simulation/policy/orchestration
  layer boundary.
- Remaining `B`-level contract semantic details should patch the architecture
  baseline directly.
- `C`-level implementation alignment should be tracked as task plans.
- `D`-level internal design blanks, such as policy-layer internals or
  orchestration-layer internals, should become separate architecture docs and
  should not reopen the simulation-layer framework.

## WP3 Engagement Pilot

Output:

- [WP3 engagement pilot task family](archive/wp3_engagement_pilot/engagement_pilot_wp3_20260519.md)

The first implementation pilot should be the engagement lifecycle because it
crosses the largest number of architecture boundaries and naturally uses
multiple clock domains:

`tasking -> command delivery -> sensor/track -> fire control -> launcher -> munition -> seeker/guidance/fuze -> effects -> damage -> observation`

The pilot must involve at least two platform families, such as:

- aircraft pylon launch,
- naval mount launch.

The pilot should avoid creating separate `air weapon` and `naval weapon`
runtime paths. Differences should appear in launcher, munition, seeker,
guidance, fuze, effects, doctrine families, and clock-domain policies.

The first implementation wave should be split into contract DTO scaffolding,
facade packet shells, Python binding exposure, air launch adapters, naval
launch adapters, munition/damage export, diagnostics trace, and a
stage-aligned non-RL smoke harness. Air and naval workers may run in parallel
only when they do not edit the same shared kernel file.

## WP4 Facade Alignment

Output:

- [WP4 facade alignment task family](archive/wp4_facade_alignment/facade_alignment_wp4_20260519.md)

WP4 turns the accepted engagement pilot into the maintained frontend shape. It
should reference WP2.5 for scheduler semantics and Temp-02 for the
information/agency boundary:

- `ObservationPacket` is what the agent is allowed to see.
- `DecisionBelief` is what the agent thinks is true after inference, memory,
  doctrine, or learned state.
- `AgentRole` is role plus authority plus information-state source plus
  decision-model reference plus action interface.

WP4 should not create new simulation semantics. It should make existing
behavior reachable through facade-shaped APIs or documented compatibility
adapters.

WP4 dispatch clusters:

- `WP4-A Surface Inventory` first:
  [surface inventory cluster](archive/wp4_facade_alignment/wp4_surface_inventory_cluster_20260519.md).
- `WP4-B/C Engagement, Step, And Lifecycle Alignment` after the initial surface
  vocabulary is stable:
  [engagement/step cluster](archive/wp4_facade_alignment/wp4_engagement_step_cluster_20260519.md).
- `WP4-D/E Policy, AgentRole, And Python Mirror` after action, coordination,
  observation, belief, and agent-role names are stable:
  [policy/binding cluster](archive/wp4_facade_alignment/wp4_policy_binding_cluster_20260519.md).
- `WP4-F Integration And Docs` remains serial in the main thread or a dedicated
  integration worker after the clusters return.

`WP4-A`, `WP4-C`, and `WP4-D` are the highest-reasoning streams because they
touch cross-layer semantics, belief boundaries, or adapter ownership.

WP4 first-wave outputs are accepted as discovery inputs:

- [WP4 first-wave acceptance review](../review/archive/wp-superseded/wp4_first_wave_acceptance_review_20260519.md)
- [WP4-A surface inventory draft](archive/wp4_facade_alignment/wp4_surface_inventory_wp4a_20260519.md)
- [WP4-B/C engagement-step alignment notes](archive/wp4_facade_alignment/wp4_engagement_step_alignment_notes_20260519.md)
- [WP4-D/E policy-binding alignment notes](archive/wp4_facade_alignment/wp4_policy_binding_alignment_notes_20260519.md)

WP4 second-wave clusters:

- `WP4-G Facade Evidence Gates`:
  [facade evidence cluster](archive/wp4_facade_alignment/wp4_facade_evidence_cluster_20260519.md).
- `WP4-H Information And Agent Shim`:
  [agent shim cluster](archive/wp4_facade_alignment/wp4_agent_shim_cluster_20260519.md).
- `WP4-I Compatibility Guard And Integration`:
  [compat guard cluster](archive/wp4_facade_alignment/wp4_compat_guard_cluster_20260519.md).

WP4 second-wave and integration outputs:

- [WP4 second-wave acceptance review](../review/archive/wp-superseded/wp4_second_wave_acceptance_review_20260519.md)
- [WP4-I compatibility guard notes](archive/wp4_facade_alignment/wp4_compat_guard_notes_20260519.md)
- [WP4-F integration handoff](archive/wp4_facade_alignment/wp4_integration_handoff_20260519.md)
- [WP4 final acceptance review](../review/archive/wp-acceptance/wp4_facade_alignment_acceptance_review_20260519.md)

## WP5 Validation Harness

Output:

- [WP5 validation harness task family](archive/wp5_validation_harness/validation_harness_wp5_20260519.md)

WP5 converts the architecture and facade work into maintained evidence. The
harness should cover five validation tiers:

- design conformance,
- trace conformance,
- boundary conformance,
- information/belief leakage,
- replay/evidence conformance.

WP5 starts from the accepted WP4 facade labels. It should not start from raw
runtime inspection; the point is to prove that facade-shaped artifacts,
diagnostics, and replay metadata are enough to validate the shared architecture.

WP5 first-wave clusters:

- `WP5-A Harness Inventory`:
  [harness inventory cluster](archive/wp5_validation_harness/wp5_harness_inventory_cluster_20260519.md).
- `WP5-B Design And Boundary Gates`:
  [design/boundary cluster](archive/wp5_validation_harness/wp5_design_boundary_cluster_20260519.md).
- `WP5-C Trace And Replay Gates`:
  [trace/replay cluster](archive/wp5_validation_harness/wp5_trace_replay_cluster_20260519.md).

`WP5-C` is the highest-reasoning first-wave stream because trace ancestry and
replay metadata tests can become brittle if they assume runtime metadata that
WP4 explicitly deferred.

WP5 first-wave outputs are accepted:

- [WP5 first-wave acceptance review](../review/archive/wp-superseded/wp5_first_wave_acceptance_review_20260519.md)
- [WP5-A harness inventory notes](archive/wp5_validation_harness/wp5_harness_inventory_notes_20260519.md)
- [WP5-B design/boundary notes](archive/wp5_validation_harness/wp5_design_boundary_notes_20260519.md)
- [WP5-C trace/replay gates notes](archive/wp5_validation_harness/wp5_trace_replay_gates_notes_20260519.md)

WP5 second-wave clusters:

- `WP5-D Information And Belief Gates`:
  [information/belief cluster](archive/wp5_validation_harness/wp5_information_belief_cluster_20260519.md).
- `WP5-E Smoke Promotion And Docs`:
  [smoke promotion cluster](archive/wp5_validation_harness/wp5_smoke_promotion_cluster_20260519.md).

WP5 second-wave and final outputs are accepted:

- [WP5-D information/belief acceptance review](../review/archive/wp-superseded/wp5_information_belief_acceptance_review_20260519.md)
- [WP5-D information/belief notes](archive/wp5_validation_harness/wp5_information_belief_notes_20260519.md)
- [WP5-E smoke promotion notes](archive/wp5_validation_harness/wp5_smoke_promotion_notes_20260519.md)
- [WP5 validation harness acceptance review](../review/archive/wp-acceptance/wp5_validation_harness_acceptance_review_20260519.md)

## WP6 Backend Profile Policy

Output:

- [WP6 backend profile policy](archive/wp6_backend_profile_policy/backend_profile_policy_wp6_20260519.md)
- [WP6-A backend profile taxonomy cluster](archive/wp6_backend_profile_policy/wp6_backend_profile_taxonomy_cluster_20260519.md)
- [WP6-A backend profile registry](archive/wp6_backend_profile_policy/wp6_backend_profile_registry_20260519.md)
- [WP6-B parity budget cluster](archive/wp6_backend_profile_policy/wp6_parity_budget_cluster_20260519.md)
- [WP6-B parity budget registry](archive/wp6_backend_profile_policy/wp6_parity_budget_registry_20260519.md)
- [WP6-C + WP6-D integration and index sync](archive/wp6_backend_profile_policy/wp6_integration_and_index_sync_20260519.md)
- [WP6-C1 resident-state boundary rules](archive/wp6_backend_profile_policy/wp6_resident_state_boundary_rules_20260519.md)
- [WP6 backend profile policy acceptance review](../review/archive/wp-acceptance/wp6_backend_profile_policy_acceptance_review_20260519.md)

WP6 closes the backend profile and parity-budget gap behind contracts. It
names the profile vocabulary, budget records, resident-state boundaries, and
capability projection rules that accelerated, resident-state, approximate, and
diagnostics-only paths must obey before those paths can be treated as
maintained.

WP6 workstream map:

- `WP6-A Backend Profile Taxonomy`:
  [taxonomy cluster](archive/wp6_backend_profile_policy/wp6_backend_profile_taxonomy_cluster_20260519.md) and
  [profile registry](archive/wp6_backend_profile_policy/wp6_backend_profile_registry_20260519.md).
- `WP6-B Parity Budget And Comparison Rules`:
  [parity budget cluster](archive/wp6_backend_profile_policy/wp6_parity_budget_cluster_20260519.md) and
  [parity budget registry](archive/wp6_backend_profile_policy/wp6_parity_budget_registry_20260519.md).
- `WP6-C Resident-State And Backend Capability Alignment`:
  [resident-state boundary rules](archive/wp6_backend_profile_policy/wp6_resident_state_boundary_rules_20260519.md)
  plus capability-projection guards in
  [runtime facade layering tests](../../../tests/architecture/test_runtime_facade_layering.py),
  [runtime facade tests](../../../tests/runtime/facade/test_runtime_facade.py),
  and [GPU runtime binding tests](../../../tests/test_gpu_runtime_bindings.py).
- `WP6-D Integration And Index Sync`:
  [integration and index sync](archive/wp6_backend_profile_policy/wp6_integration_and_index_sync_20260519.md) and
  [acceptance review](../review/archive/wp-acceptance/wp6_backend_profile_policy_acceptance_review_20260519.md).

## WP7 Backend Capability Materialization

Output:

- [WP7 backend capability materialization](archive/wp7_backend_capability_materialization/backend_capability_materialization_wp7_20260519.md)
- [WP7-A registry materialization cluster](archive/wp7_backend_capability_materialization/wp7_registry_materialization_cluster_20260519.md)
- [WP7-A registry materialization notes](archive/wp7_backend_capability_materialization/wp7_registry_materialization_notes_20260519.md)
- [WP7-B runtime capability projection cluster](archive/wp7_backend_capability_materialization/wp7_runtime_capability_projection_cluster_20260519.md)
- [WP7-B runtime capability projection notes](archive/wp7_backend_capability_materialization/wp7_runtime_capability_projection_notes_20260519.md)
- [WP7-C promotion evidence gates cluster](archive/wp7_backend_capability_materialization/wp7_promotion_evidence_gates_cluster_20260519.md)
- [WP7-C promotion evidence gates notes](archive/wp7_backend_capability_materialization/wp7_promotion_evidence_gates_notes_20260519.md)
- [WP7-D multi-fidelity entry conditions cluster](archive/wp7_backend_capability_materialization/wp7_multifidelity_entry_conditions_cluster_20260519.md)
- [WP7-D multi-fidelity entry conditions notes](archive/wp7_backend_capability_materialization/wp7_multifidelity_entry_conditions_notes_20260519.md)
- [WP7-E integration and index sync cluster](archive/wp7_backend_capability_materialization/wp7_integration_and_index_sync_cluster_20260519.md)
- [WP7 backend capability materialization acceptance review](../review/archive/wp-acceptance/wp7_backend_capability_materialization_acceptance_review_20260519.md)

WP7 is the accepted post-WP6 documentation and implementation-preparation line.
It turns accepted backend profile policy into materialized registry, runtime
projection, promotion evidence, and multi-fidelity entry conditions. This
acceptance does not promote exact GPU, resident-state, device observation,
shadow, or adaptive fidelity support; current support remains false until a
future promotion review updates the registry, parity budget, projection adapter,
and validation evidence together.

WP7 workstream map:

- `WP7-A Registry Materialization` starts first and owns the machine-checkable
  registry/schema shape.
- `WP7-D Multi-Fidelity Entry Conditions` may run beside WP7-A as long as it
  cites WP6/WP7-A profile vocabulary rather than inventing support claims.
- `WP7-B Runtime Capability Projection` waits for WP7-A and keeps projection
  conservative.
- `WP7-C Promotion Evidence Gates` consumes WP7-A/D and maps candidate
  promotion to WP5 validation tiers.
- `WP7-E Integration And Index Sync` is serial and should run after A-D
  stabilize.

## Acceptance Gates

Every implementation task derived from this subproject should satisfy:

1. stage ownership is documented,
2. stage-node read/write sets and clock domains are documented,
3. feedback crosses state-store or event-queue boundaries,
4. facade or compatibility-adapter access is explicit,
5. CPU exact behavior remains the reference path,
6. cross-domain behavior uses the same lifecycle,
7. local smoke tests run without requiring RL dependencies,
8. diagnostics can explain command, launch, munition, effect, and damage events,
9. observation schema, action validity, reward composition,
   termination/truncation source, and episode lifecycle authority are assigned
   to explicit layers.
10. maintained decision paths consume `ObservationPacket` or declared
    `DecisionBelief`, not `World Truth`.
11. backend capability claims cite a maintained backend profile and parity
    budget; `RuntimeCapabilities` must not infer exact GPU, resident-state, or
    shadow support from helper/probe presence alone.
12. WP7 capability materialization keeps exact GPU, resident-state, device
    observation, shadow, and multi-fidelity support false unless a maintained
    profile revision, parity budget, ownership/sync policy, and validation gate
    explicitly promote the claim.
13. WP8 learning-face outputs keep curriculum, evaluation, capability
    profiling, scenario generation, and learning evidence explicit and
    replayable rather than turning them into a second simulation truth path.
14. WP17 runtime-materialization work must cite current code facts, keep
    compatibility-only runtime access bounded, and avoid claiming global
    multi-rate, fidelity-provider, capability-spawn, or counterfactual runtime
    closure before the corresponding selected-slice evidence exists.

## Non-Goals

- Full RL training on the local Windows machine.
- Immediate exact GPU world-step replacement.
- Introducing Rust as a near-term backend.
- Rewriting all existing command/tasking DTOs before the contract freeze.
- Moving every existing file into new directories during WP0/WP1.
