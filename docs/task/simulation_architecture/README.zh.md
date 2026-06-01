# 仿真架构

状态：`2026-05-19` 开启活跃子项目。

语言版本：

- 英文主文：[README.md](README.md)
- 中文辅文：`README.zh.md`

本子项目负责把严格仿真架构基线转化为有边界的工作包。凡是准备跨武器、海军 runtime、传感器/航迹、command/tasking、facade 或后端加速展开大范围实现前，都应先从这里收敛任务。

架构权威：

- [仿真系统架构设计](../../plan/architecture/simulation_system_architecture_design.zh.md)
- [系统分层与引擎封装方案](../../plan/architecture/system_layering_and_engine_encapsulation_plan.zh.md)
- [架构与性能路线进一步调研](../../plan/architecture/architecture_and_performance_research_followup.zh.md)

## 当前定位

当前活跃设计结论是：

1. 项目应被视为 SCAL 系统：semantic、causal、agentic 与 learning-facing，
   `WP0-WP5` 构建经验证运行时内核，`WP6` 收口后端加速与 resident-state
   工作所需的 backend profile policy，`WP7` 把该 policy 物化为 registry、
   projection、evidence 与 multi-fidelity entry 任务。
2. 项目应遵循一条规范化语义生命周期。
3. 真实执行应使用因果-时序执行模型。temporal DAG 是调度投影，反馈跨越显式 state-store 或 event-queue 边界。
4. 空军、海军、地面、武器和未来平台/领域族应通过阶段局部的模型族、capability bundle 与 stage-node contract 扩展该生命周期。
5. runtime facade 与 typed request/result 契约应成为前端长期依赖面。
6. 策略计算层与测试/编排层应被建模为 facade contract 的显式 producer / consumer，而不是仿真状态的隐藏 owner。
7. 信息状态边界必须区分 `World Truth`、`ObservationPacket` 与 `DecisionBelief`。
8. 本机工作应聚焦 build/import/smoke、架构文档、契约设计和仿真系统组建，而不是 RL 训练。
9. 后端加速与 resident-state 工作应通过契约后的显式 backend profiles 和 parity budgets 来收口，而不是走第二条语义路径。
10. backend capability implementation 应从已验收的 WP6 registry 与 parity
    记录出发，先补可机器检查的 materialization 与 evidence gate，再让任何
    exact GPU、resident-state、shadow 或 multi-fidelity capability 进入维护态。
11. 已验收 facade contracts 与未来 learning-facing consumer 之间的维护中训练路径
    桥接，应通过独立的 `WP7.5` 线展开，把 batch 训练路径从
    `RuntimeFacade.runtime()` 迁走。
12. 学习面工作应通过独立的 `WP8` 任务族来展开，聚焦课程、评估、能力画像、
    场景生成与学习证据；它不应重新打开仿真闭合，也不应默认本机具备完整 RL
    训练条件。
13. 延后的 contract 与 infrastructure closure 应通过 `WP9` 收口；它负责晋升已验收
    DTO 词汇并关闭小型 residual infrastructure / guard 项目，而不重新打开
    `WP0-WP8`。
14. post-WP9 工作应遵循
    [post-WP9 architecture route plan](archive/post_wp9_architecture_route_plan_20260520.zh.md)：
    先做 causal runtime foundation，再做 facade vertical slice，随后推进
    information/agency enforcement、backend/fidelity、capability composition 与
    counterfactual/experiment generation。Phase 1-5 现已验收为 `WP10`、`WP11`、
    `WP12`、`WP13` 与 `WP14`；Phase 6 现已验收为 `WP15`。
15. post-WP9 路线完成后，下一步架构优化阶段是 `WP16 Runtime Spine
    Consolidation`：把 `WP10-WP15` 已验收边界转成 maintained default runtime
    path，关闭 remaining bypasses，并把 `GAP-9` clock-domain enforcement 从延后
    的 advisory 状态推进到 selected runtime-spine slice。
16. WP16 之后，Stage 3 最后重构阶段开启为 `WP17 Stage 3 Runtime
    Materialization And Cleanup`：按当前代码事实校正 Stage 3 计划，把维护中的业务路径
    从 compatibility-only runtime access 迁出，并把 multi-rate、
    fidelity-provider、capability-spawn 与 counterfactual runtime materialization
    拆成有边界的实现流。
17. WP17 验收后，剩余主线曾冻结为四个阶段：`WP18` runtime ownership 与 C++ hot-path
    consolidation，`WP19` CUDA / resident-state mainline alignment，`WP20`
    public capability-platform composition，以及 `WP21` full counterfactual /
    experiment runtime。`WP18`、`WP19` 与 `WP20` 仍保持已验收；WP21 的 claimed
    closure 已在 `2026-05-22` 被 owner 否决，不得再视为最终路线闭合。
18. post-WP21 的
    [architecture refactoring audit](../review/architecture_refactoring_audit_20260522.zh.md)
    是新的架构级事实：若干 compatibility layers 与旧实现面仍作为默认或
    maintained paths 存在。这使 WP21 的验收主张失效，并打开 `WP22 Legacy
    Compatibility Retirement And Architecture Hardening`；但 WP22 continuation
    stream 已在 `2026-05-23` 被 owner 终止，因为 uncontrolled follow-up waves、
    partial evidence reuse 与 quarantine/dual-representation drift 使该计划不可接受。
19. 最新 legacy-retirement recovery 记录是 `WP23 Legacy Retirement Recovery And
    Reset`：它冻结 WP22，分类当前 dirty work，强制 delete-or-block 判定，将
    single-representation tasking/public-API exits 判定为 blocked，跳过
    implementation，并于 `2026-05-24` 以 `blocked` 关闭。
20. `TM01 Architecture Closure Remediation` 仅就已审计的实现切片关闭：`TM01-A`、
    `TM01-C` 与 `TM01-D` 已完成并验证，而 `TM01-B` 的 launch bridge 已作为有
    源码锚点的 residual 记录，并交由后续架构工作负责。
21. 当本子项目被拆分给多个 subagent 或 worker 时，应遵循
    [Subagent 使用规范](../../standards/governance/subagent_usage_policy.zh.md)：
    保持写入范围互不重叠、保留一个 integration owner，并且不要让多个并行作者
    拆写同一张规范性表格。
22. 实现收口的 commit message 应使用 capability/result language，避免 `WP13`
    或 `WP14` 这类 internal work-package labels。
23. `TM03 Launch Bridge Boundary` 已关闭 TM01-B 记录的
    `systems -> SimulationKernel` weapon-release residual：两个显式 release
    helper 改为经由 `IWeaponReleaseService` 窄接口；这不声明更广泛的 P7
    launch/fire-control 重设、raw-runtime 退场或通用 compatibility cleanup。

## 工作包

已闭合、已冻结、blocked 或已替代的 package 仍保留在下表中用于路线追溯，但其任务
packet 已移入 [archive/](archive/README.zh.md)，不再作为顶层 active 子项目目录裸露。

| 工作包 | 状态 | 目标 | 产出 |
|--------|------|------|------|
| `WP0 Architecture Baseline` | complete | 明确 SCAL 定位、语义生命周期、因果-时序执行投影与扩展规则 | 架构设计文档、任务子项目入口 |
| `WP1 Pipeline Inventory` | complete | 把当前代码、system、model、test 映射到 `P0-P10` 与当前耦合热点 | [管线盘点](archive/wp1_pipeline_inventory/pipeline_inventory_wp1_20260519.zh.md) |
| `WP2 Contract Freeze` | complete | 识别需要显式 ownership 的 packet 族、stage-node contract 与跨层 policy/orchestration contract | [契约冻结](archive/wp2_contract_freeze/contract_freeze_wp2_20260519.zh.md) |
| `WP2.5 Scheduler Semantics Freeze` | complete | 冻结 event ordering、state versioning、barrier visibility、clock-domain merge policy、replay contract 与 stage-node manifest schema | [调度语义冻结](archive/wp25_scheduler_semantics/scheduler_semantics_wp25_20260519.zh.md)、[验收审查](../review/archive/wp-acceptance/wp25_scheduler_semantics_acceptance_review_20260519.zh.md) |
| `WP3 Engagement Pilot` | complete | 以武器/交战作为第一条跨领域验证切片 | [交战试点任务族](archive/wp3_engagement_pilot/engagement_pilot_wp3_20260519.zh.md) |
| `WP4 Facade Alignment` | complete | 确保试点行为可通过 facade-shaped API 访问，并避免 raw runtime access | [facade 对齐任务族](archive/wp4_facade_alignment/facade_alignment_wp4_20260519.zh.md)、[最终验收](../review/archive/wp-acceptance/wp4_facade_alignment_acceptance_review_20260519.zh.md) |
| `WP5 Validation Harness` | complete | 添加证明共享生命周期和图边界的 smoke、architecture、trace、boundary、information-leakage 与 replay/evidence 测试 | [验证套件任务族](archive/wp5_validation_harness/validation_harness_wp5_20260519.zh.md)、[最终验收](../review/archive/wp-acceptance/wp5_validation_harness_acceptance_review_20260519.zh.md) |
| `WP6 Backend Profile Policy` | complete | 冻结 backend profile taxonomy、parity budgets、resident-state 边界与 backend capability 暴露规则 | [后端配置文件策略](archive/wp6_backend_profile_policy/backend_profile_policy_wp6_20260519.zh.md)、[profile 注册表](archive/wp6_backend_profile_policy/wp6_backend_profile_registry_20260519.zh.md)、[parity budget 注册表](archive/wp6_backend_profile_policy/wp6_parity_budget_registry_20260519.zh.md)、[resident-state 边界规则](archive/wp6_backend_profile_policy/wp6_resident_state_boundary_rules_20260519.zh.md)、[验收审查](../review/archive/wp-acceptance/wp6_backend_profile_policy_acceptance_review_20260519.zh.md) |
| `WP7 Backend Capability Materialization` | complete / accepted | 把已验收的 WP6 policy 物化为可机器检查 registry、runtime capability projection、promotion evidence gates 与 multi-fidelity entry conditions，但不晋级候选能力 | [后端能力物化](archive/wp7_backend_capability_materialization/backend_capability_materialization_wp7_20260519.zh.md)、[registry materialization](archive/wp7_backend_capability_materialization/wp7_registry_materialization_cluster_20260519.zh.md)、[runtime capability projection](archive/wp7_backend_capability_materialization/wp7_runtime_capability_projection_cluster_20260519.zh.md)、[promotion evidence gates](archive/wp7_backend_capability_materialization/wp7_promotion_evidence_gates_cluster_20260519.zh.md)、[multi-fidelity entry conditions](archive/wp7_backend_capability_materialization/wp7_multifidelity_entry_conditions_cluster_20260519.zh.md)、[验收审查](../review/archive/wp-acceptance/wp7_backend_capability_materialization_acceptance_review_20260519.zh.md) |
| `WP7.5 训练路径 facade 桥接` | complete / accepted | 在 `WP8` 依赖之前，把维护中的 batch 训练路径从 `RuntimeFacade.runtime()` 与 raw `WorldBatchRuntime` stepping 迁到 facade-shaped execution / observation API | [训练路径 facade 桥接](archive/wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.zh.md)、[验收审查](../review/archive/wp-acceptance/wp75_training_path_facade_bridge_acceptance_review_20260520.zh.md) |
| `WP8 SCAL Learning Face` | complete / accepted | 把课程、评估、能力画像、场景生成与学习证据收敛为显式架构和任务词汇，但不重新打开仿真闭合 | [学习面任务族](archive/wp8_learning_face/learning_face_wp8_20260520.zh.md)、[验收审查](../review/archive/wp-acceptance/wp8_learning_face_acceptance_review_20260520.zh.md) |
| `WP9 Contract And Infrastructure Closure` | complete / accepted | 晋升延后的 DTO 契约，关闭小型 infrastructure residual，添加 guard allowlists，并发布最终索引/验收证据 | [contract and infrastructure closure](archive/wp9_contract_infrastructure_closure/contract_infrastructure_closure_wp9_20260520.zh.md)、[DTO batch 1](archive/wp9_contract_infrastructure_closure/wp9_dto_promotion_batch1_cluster_20260520.zh.md)、[DTO batch 2](archive/wp9_contract_infrastructure_closure/wp9_dto_promotion_batch2_cluster_20260520.zh.md)、[infrastructure closure](archive/wp9_contract_infrastructure_closure/wp9_infrastructure_closure_cluster_20260520.zh.md)、[guard enforcement](archive/wp9_contract_infrastructure_closure/wp9_guard_enforcement_cluster_20260520.zh.md)、[integration sync](archive/wp9_contract_infrastructure_closure/wp9_integration_and_index_sync_cluster_20260520.zh.md)、[验收审查](../review/archive/wp-acceptance/wp9_contract_infrastructure_closure_acceptance_review_20260520.zh.md) |
| `Post-WP9 Architecture Route` | route selected | 确定实现顺序并把 Phase 1 锚定为 WP10：causal runtime foundation、facade vertical slice、information/agency enforcement、backend/fidelity、capability composition、counterfactual/experiment generation | [post-WP9 architecture route plan](archive/post_wp9_architecture_route_plan_20260520.zh.md) |
| `WP10 Causal Runtime Foundation` | complete / accepted | 实现 post-WP9 路线 Phase 1：manifest registry seed、minimal scheduling-window loop、request injection、same-window validation、event/snapshot evidence 与 integration handoff | [causal runtime foundation](archive/wp10_causal_runtime_foundation/causal_runtime_foundation_wp10_20260520.zh.md)、[manifest registry](archive/wp10_causal_runtime_foundation/wp10_manifest_registry_cluster_20260520.zh.md)、[window loop / injection](archive/wp10_causal_runtime_foundation/wp10_window_loop_injection_cluster_20260520.zh.md)、[same-window validation](archive/wp10_causal_runtime_foundation/wp10_same_window_validation_cluster_20260520.zh.md)、[event/snapshot evidence](archive/wp10_causal_runtime_foundation/wp10_event_snapshot_evidence_cluster_20260520.zh.md)、[integration handoff](archive/wp10_causal_runtime_foundation/wp10_integration_acceptance_cluster_20260520.zh.md)、[验收审查](../review/archive/wp-acceptance/wp10_causal_runtime_foundation_acceptance_review_20260520.zh.md) |
| `WP11 Facade Vertical Slice And Provenance` | complete / accepted | 实现 post-WP9 路线 Phase 2：`ActionHoldPolicy`、information-state provenance labels、基于 WP10 seam 的 facade/binding proof、consumer boundary pre-gates 与 integration handoff | [facade vertical slice and provenance](archive/wp11_facade_vertical_slice_provenance/facade_vertical_slice_provenance_wp11_20260520.zh.md)、[ActionHoldPolicy](archive/wp11_facade_vertical_slice_provenance/wp11_action_hold_policy_cluster_20260520.zh.md)、[information provenance](archive/wp11_facade_vertical_slice_provenance/wp11_information_provenance_labels_cluster_20260520.zh.md)、[vertical slice proof](archive/wp11_facade_vertical_slice_provenance/wp11_facade_vertical_slice_proof_cluster_20260520.zh.md)、[consumer boundary pre-gates](archive/wp11_facade_vertical_slice_provenance/wp11_consumer_boundary_pregates_cluster_20260520.zh.md)、[integration handoff](archive/wp11_facade_vertical_slice_provenance/wp11_integration_acceptance_cluster_20260520.zh.md)、[验收审查](../review/archive/wp-acceptance/wp11_facade_vertical_slice_provenance_acceptance_review_20260520.zh.md) |
| `WP12 Information And Agency Enforcement` | complete / accepted | 实现 post-WP9 路线 Phase 3：Law 14 read-side enforcement、`AgentRole` authority validation、information-transformation evidence、authorized intent injection 与 integration handoff | [information and agency enforcement](archive/wp12_information_agency_enforcement/information_agency_enforcement_wp12_20260520.zh.md)、[Law 14 read-side enforcement](archive/wp12_information_agency_enforcement/wp12_law14_read_side_enforcement_cluster_20260520.zh.md)、[agency role authority](archive/wp12_information_agency_enforcement/wp12_agency_role_authority_cluster_20260520.zh.md)、[information transformation surface](archive/wp12_information_agency_enforcement/wp12_information_transformation_surface_cluster_20260520.zh.md)、[intent injection authority guard](archive/wp12_information_agency_enforcement/wp12_intent_injection_authority_guard_cluster_20260520.zh.md)、[integration handoff](archive/wp12_information_agency_enforcement/wp12_integration_acceptance_cluster_20260520.zh.md)、[验收审查](../review/archive/wp-acceptance/wp12_information_agency_enforcement_acceptance_review_20260520.zh.md) |
| `WP13 Backend Fidelity Expansion` | complete / accepted | 实现 post-WP9 路线 Phase 4：让 runtime capabilities、backend profiles、parity budgets 与 fidelity profile requests 可查询、可拒绝、可证据化，同时不晋级 unsupported backend claims | [backend fidelity expansion](archive/wp13_backend_fidelity_expansion/backend_fidelity_expansion_wp13_20260520.zh.md)、[capability query](archive/wp13_backend_fidelity_expansion/wp13_runtime_capability_query_cluster_20260520.zh.md)、[backend profile registry gate](archive/wp13_backend_fidelity_expansion/wp13_backend_profile_registry_gate_cluster_20260520.zh.md)、[parity budget evidence gate](archive/wp13_backend_fidelity_expansion/wp13_parity_budget_evidence_gate_cluster_20260520.zh.md)、[fidelity request gate](archive/wp13_backend_fidelity_expansion/wp13_fidelity_profile_request_gate_cluster_20260520.zh.md)、[facade/binding proof](archive/wp13_backend_fidelity_expansion/wp13_facade_binding_proof_cluster_20260520.zh.md)、[integration handoff](archive/wp13_backend_fidelity_expansion/wp13_integration_acceptance_cluster_20260520.zh.md)、[验收审查](../review/archive/wp-acceptance/wp13_backend_fidelity_expansion_acceptance_review_20260520.zh.md) |
| `WP14 Capability Composition` | complete / accepted | 实现 post-WP9 路线 Phase 5：在保持 type-name 兼容的前提下，通过 resolved spawn plans、additive facade/setup DTO 与严格实现 gate，把现有 setup 推向 typed `Capability` / `CapabilityBundle` composition，避免 big-bang spawn rewrite | [capability composition](archive/wp14_capability_composition/capability_composition_wp14_20260521.zh.md)、[capability bundle contract](archive/wp14_capability_composition/wp14_capability_bundle_contract_cluster_20260521.zh.md)、[content definition lowering](archive/wp14_capability_composition/wp14_content_definition_lowering_cluster_20260521.zh.md)、[spawn resolution bridge](archive/wp14_capability_composition/wp14_spawn_resolution_bridge_cluster_20260521.zh.md)、[additive facade setup DTO](archive/wp14_capability_composition/wp14_additive_facade_setup_dto_cluster_20260521.zh.md)、[capability effects materialization](archive/wp14_capability_composition/wp14_capability_effects_materialization_cluster_20260521.zh.md)、[compatibility validation](archive/wp14_capability_composition/wp14_compatibility_validation_acceptance_cluster_20260521.zh.md)、[验收审查](../review/archive/wp-acceptance/wp14_capability_composition_acceptance_review_20260521.zh.md) |
| `WP15 Counterfactual Experiment Generation` | complete / accepted | 实现 post-WP9 路线 Phase 6：添加 replay envelopes、branch point 与 worldline metadata、counterfactual admission、scenario/adversary generation request surfaces 与 experiment evidence ancestry，同时不声明 full snapshot/restore 或 maintained rollout execution | [counterfactual experiment generation](archive/wp15_counterfactual_experiment_generation/counterfactual_experiment_generation_wp15_20260521.zh.md)、[replay envelope and branch point](archive/wp15_counterfactual_experiment_generation/wp15_replay_envelope_branch_point_cluster_20260521.zh.md)、[worldline branch metadata](archive/wp15_counterfactual_experiment_generation/wp15_worldline_branch_metadata_gate_cluster_20260521.zh.md)、[counterfactual admission](archive/wp15_counterfactual_experiment_generation/wp15_counterfactual_admission_cluster_20260521.zh.md)、[scenario/adversary generation](archive/wp15_counterfactual_experiment_generation/wp15_scenario_adversary_generation_surface_cluster_20260521.zh.md)、[experiment evidence bridge](archive/wp15_counterfactual_experiment_generation/wp15_experiment_evidence_bridge_cluster_20260521.zh.md)、[integration handoff](archive/wp15_counterfactual_experiment_generation/wp15_integration_acceptance_cluster_20260521.zh.md)、[验收审查](../review/archive/wp-acceptance/wp15_counterfactual_experiment_generation_acceptance_review_20260521.zh.md) |
| `WP16 Runtime Spine Consolidation` | complete / accepted | 完成 post-WP15 架构优化阶段：盘点 bypasses、定义 maintained runtime spine、执行第一条严格 `GAP-9` clock-domain cadence slice、迁移 facade/batch consumers、分类 legacy paths，并通过 generated closure summaries 降低文档同步拖拽，同时保留记录下来的 residuals | [runtime spine consolidation](archive/wp16_runtime_spine_consolidation/runtime_spine_consolidation_wp16_20260521.zh.md)、[runtime spine inventory](archive/wp16_runtime_spine_consolidation/wp16_runtime_spine_inventory_cluster_20260521.zh.md)、[clock-domain enforcement](archive/wp16_runtime_spine_consolidation/wp16_clock_domain_enforcement_cluster_20260521.zh.md)、[facade/batch migration](archive/wp16_runtime_spine_consolidation/wp16_facade_batch_spine_migration_cluster_20260521.zh.md)、[legacy compatibility](archive/wp16_runtime_spine_consolidation/wp16_legacy_deprecation_compatibility_cluster_20260521.zh.md)、[documentation automation](archive/wp16_runtime_spine_consolidation/wp16_generated_documentation_automation_cluster_20260521.zh.md)、[integration handoff](archive/wp16_runtime_spine_consolidation/wp16_integration_acceptance_cluster_20260521.zh.md)、[验收审查](../review/archive/wp-acceptance/wp16_runtime_spine_consolidation_acceptance_review_20260521.zh.md) |
| `WP17 Stage 3 Runtime Materialization And Cleanup` | complete / accepted | 物化 Stage 3 最后一组 selected runtime slices：facade-shaped batch reads、可运行 cadence evidence、reference CPU fidelity admission、capability-gated spawn，以及 explicit-setup selected-entity counterfactual branch/compare，同时保留 legacy compatibility 与 full-worldline residuals | [stage3 runtime materialization and cleanup](archive/wp17_stage3_runtime_materialization_cleanup/stage3_runtime_materialization_cleanup_wp17_20260521.zh.md)、[fact ledger](archive/wp17_stage3_runtime_materialization_cleanup/wp17_fact_ledger_and_boundary_freeze_cluster_20260521.md)、[business migration](archive/wp17_stage3_runtime_materialization_cleanup/wp17_facade_business_migration_cleanup_cluster_20260521.md)、[multi-rate runtime](archive/wp17_stage3_runtime_materialization_cleanup/wp17_multirate_runtime_example_cluster_20260521.md)、[fidelity provider runtime](archive/wp17_stage3_runtime_materialization_cleanup/wp17_fidelity_provider_runtime_cluster_20260521.md)、[capability spawn runtime](archive/wp17_stage3_runtime_materialization_cleanup/wp17_capability_spawn_runtime_cluster_20260521.md)、[counterfactual runtime closure](archive/wp17_stage3_runtime_materialization_cleanup/wp17_counterfactual_runtime_closure_cluster_20260521.md)、[dispatch queue](archive/wp17_stage3_runtime_materialization_cleanup/wp17_subagent_dispatch_queue_20260521.md)、[验收审查](../review/archive/wp-acceptance/wp17_stage3_runtime_materialization_cleanup_acceptance_review_20260521.zh.md) |
| `WP18 Runtime Ownership And C++ Hot Path Consolidation` | complete / accepted | 在 WP17 后收紧 runtime ownership，把维护中的 execution truths 与高频 Python paths 推向 C++/facade-owned surfaces，同时让 compatibility APIs 保持有边界 | [runtime ownership and C++ hot path consolidation](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/runtime_ownership_cxx_hot_path_consolidation_wp18_20260521.zh.md)、[ownership fact ledger](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_ownership_fact_ledger_hot_path_map_cluster_20260521.zh.md)、[execution episode ownership sink](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_execution_episode_ownership_sink_cluster_20260521.zh.md)、[ScenarioLoader adapter split](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_scenario_loader_adapter_split_cluster_20260521.zh.md)、[facade contract hardening](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_facade_contract_hardening_cluster_20260521.zh.md)、[C++ hot path matrix](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_cxx_hot_path_migration_matrix_cluster_20260521.zh.md)、[integration handoff](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_integration_handoff_cluster_20260521.zh.md)、[dispatch queue](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_subagent_dispatch_queue_20260521.zh.md)、[验收审查](../review/archive/wp-acceptance/wp18_runtime_ownership_cxx_hot_path_consolidation_acceptance_review_20260521.zh.md) |
| `WP19 CUDA And Resident-State Mainline Alignment` | complete / accepted | 对齐现有 CUDA helpers、device-resident output contracts、diagnostics boundaries 与 resident-state sync/shard vocabulary，同时默认不晋级 exact GPU 或 maintained resident-state support | [CUDA and resident-state mainline alignment](archive/wp19_cuda_resident_state_alignment/cuda_resident_state_alignment_wp19_20260521.zh.md)、[fact ledger](archive/wp19_cuda_resident_state_alignment/wp19_cuda_resident_state_fact_ledger_cluster_20260521.zh.md)、[device output contract](archive/wp19_cuda_resident_state_alignment/wp19_device_resident_output_contract_cluster_20260521.zh.md)、[GPU helper diagnostics boundary](archive/wp19_cuda_resident_state_alignment/wp19_gpu_helper_diagnostics_boundary_cluster_20260521.zh.md)、[resident-state sync and shard contract](archive/wp19_cuda_resident_state_alignment/wp19_resident_state_sync_shard_contract_cluster_20260521.zh.md)、[first CUDA alignment slice](archive/wp19_cuda_resident_state_alignment/wp19_first_cuda_alignment_slice_cluster_20260521.zh.md)、[integration handoff](archive/wp19_cuda_resident_state_alignment/wp19_integration_handoff_cluster_20260521.zh.md)、[dispatch queue](archive/wp19_cuda_resident_state_alignment/wp19_subagent_dispatch_queue_20260521.zh.md)、[验收审查](../review/archive/wp-acceptance/wp19_cuda_resident_state_alignment_acceptance_review_20260521.zh.md) |
| `WP20 Public Capability-Platform Composition` | complete / accepted | 通过 validation-first admission/result contracts 与 compatibility-preserving materialization 公开 typed capability-platform setup path，同时保持 type-name spawning 与 scenario schema 稳定 | [public capability-platform composition](archive/wp20_public_capability_platform_composition/public_capability_platform_composition_wp20_20260521.zh.md)、[fact ledger](archive/wp20_public_capability_platform_composition/wp20_public_capability_fact_ledger_cluster_20260521.zh.md)、[public typed spawn contract](archive/wp20_public_capability_platform_composition/wp20_public_typed_platform_spawn_contract_cluster_20260521.zh.md)、[runtime setup consume bridge](archive/wp20_public_capability_platform_composition/wp20_runtime_setup_consume_bridge_cluster_20260521.zh.md)、[facade/binding surface](archive/wp20_public_capability_platform_composition/wp20_facade_binding_public_surface_cluster_20260521.zh.md)、[compatibility/schema guard](archive/wp20_public_capability_platform_composition/wp20_compatibility_schema_guard_cluster_20260521.zh.md)、[integration handoff](archive/wp20_public_capability_platform_composition/wp20_integration_handoff_cluster_20260521.zh.md)、[dispatch queue](archive/wp20_public_capability_platform_composition/wp20_subagent_dispatch_queue_20260521.zh.md)、[验收审查](../review/archive/wp-acceptance/wp20_public_capability_platform_composition_acceptance_review_20260521.zh.md) |
| `WP21 Full Counterfactual Experiment Runtime` | owner-rejected / superseded by WP22 | claimed closure 试图将已验收 counterfactual contracts 与 selected runtime slices 转为 maintained facade-owned experiment execution、scenario generation、evidence collection 与 legacy cleanup，但 owner 因 compatibility layers 与未闭合 subagent work 仍残留而否决该收口。 | [full counterfactual experiment runtime](archive/wp21_full_counterfactual_experiment_runtime/full_counterfactual_experiment_runtime_wp21_20260521.zh.md)、[fact ledger](archive/wp21_full_counterfactual_experiment_runtime/wp21_fact_ledger_residual_freeze_cluster_20260521.zh.md)、[snapshot/restore boundary](archive/wp21_full_counterfactual_experiment_runtime/wp21_snapshot_restore_worldline_boundary_cluster_20260521.zh.md)、[counterfactual rollout](archive/wp21_full_counterfactual_experiment_runtime/wp21_counterfactual_rollout_causal_difference_cluster_20260521.zh.md)、[scenario generation runtime](archive/wp21_full_counterfactual_experiment_runtime/wp21_scenario_intervention_generation_cluster_20260521.zh.md)、[experiment facade/evidence](archive/wp21_full_counterfactual_experiment_runtime/wp21_experiment_facade_evidence_cluster_20260521.zh.md)、[final cleanup](archive/wp21_full_counterfactual_experiment_runtime/wp21_final_cleanup_acceptance_cluster_20260521.zh.md)、[dispatch queue](archive/wp21_full_counterfactual_experiment_runtime/wp21_subagent_dispatch_queue_20260521.zh.md)、[已争议验收记录](../review/archive/wp-acceptance/wp21_full_counterfactual_experiment_runtime_acceptance_review_20260522.zh.md) |
| `WP22 Legacy Compatibility Retirement And Architecture Hardening` | owner-rejected / frozen；由 WP23 取代 | 曾试图强制退场 post-WP21 compatibility layers，但 owner 因 uncontrolled follow-up waves 与 partial/quarantine evidence drift 终止该流。其 queue 只作历史记录，不得再派发。 | [legacy compatibility retirement](archive/wp22_legacy_compatibility_retirement/legacy_compatibility_retirement_wp22_20260522.zh.md)、[remaining task clusters](archive/wp22_legacy_compatibility_retirement/wp22_remaining_task_clusters_20260523.zh.md)、[dispatch queue](archive/wp22_legacy_compatibility_retirement/wp22_subagent_dispatch_queue_20260522.zh.md) |
| `WP23 Legacy Retirement Recovery And Reset` | closed / blocked | 冻结 WP22，分类当前 dirty work，强制 delete-or-block decisions，将 TaskOrder 与 public API exits 记录为 blocked；因没有 deletion-ready surface 而跳过 implementation，并以受控 blocked recovery 收口。 | [legacy retirement recovery](archive/wp23_legacy_retirement_recovery/legacy_retirement_recovery_wp23_20260523.zh.md) |
| `WP24 TaskOrder Maintained Business Migration` | closed / accepted | WP23 后的 replacement-backed TaskOrder 业务迁移：maintained contract/export/Python business paths 已集成，旧 public TaskOrder whole-shell compatibility surfaces 已删除，canonical acceptance review 已发布。 | [taskorder maintained business migration](archive/wp24_taskorder_maintained_business_migration/taskorder_maintained_business_migration_wp24_20260524.zh.md)、[集成评估与清理收口](archive/wp24_taskorder_maintained_business_migration/wp24_integration_assessment_and_next_dispatch_20260524.zh.md)、[验收审查](../review/archive/wp-acceptance/wp24_taskorder_maintained_business_migration_acceptance_review_20260525.zh.md) |
| `TM01 Architecture Closure Remediation` | audited-slice closed / residual handed off | 审计后的有边界整改线：`TM01-A`、`TM01-C`、`TM01-D` 已完成并覆盖本次 maintained-path 切片；`TM01-B` 记录的 launch-bridge residual 已由 TM03 关闭，且更广泛的架构、P7/raw-runtime 与 WP24 canonical acceptance 闭合仍未完成。 | [TM01 entry](archive/tm01_architecture_closure_remediation/README.md)、[task clusters](archive/tm01_architecture_closure_remediation/tm01_architecture_closure_task_clusters_20260524.md) |
| `TM02 WP24 Acceptance Closure` | temporary / closed | 已发布 WP24 canonical acceptance review 并同步索引的 closure lane；未重开 implementation scope。 | [TM02 entry](archive/tm02_wp24_acceptance_closure/README.md)、[验收审查](../review/archive/wp-acceptance/wp24_taskorder_maintained_business_migration_acceptance_review_20260525.zh.md) |
| `TM03 Launch Bridge Boundary` | temporary / closed | 通过 `IWeaponReleaseService` 窄接口关闭 TM01-B 记录的两个 `systems -> SimulationKernel` weapon-release bridge 的有边界架构 lane。 | [TM03 entry](archive/tm03_launch_bridge_boundary/README.md)、[task clusters](archive/tm03_launch_bridge_boundary/tm03_launch_bridge_boundary_task_clusters_20260525.md) |

## TM03 Launch Bridge Boundary

产出：

- [TM03 Launch Bridge Boundary](archive/tm03_launch_bridge_boundary/README.md)
- [TM03 Launch Bridge Boundary Task Clusters](archive/tm03_launch_bridge_boundary/tm03_launch_bridge_boundary_task_clusters_20260525.md)

TM03 只负责 TM01-B 记录下来的窄 launch-bridge residual。它已通过
`IWeaponReleaseService` 移除两个 release helper header 对 `SimulationKernel` 的直接依赖，
并记录聚焦架构与 weapon-release 验证。更广泛的 P7 launch/fire-control 重设与
raw-runtime 退场仍在 TM03 范围之外。

## TM02 WP24 Acceptance Closure

产出：

- [TM02 WP24 Acceptance Closure](archive/tm02_wp24_acceptance_closure/README.md)
- [WP24 TaskOrder Maintained Business Migration 验收审查](../review/archive/wp-acceptance/wp24_taskorder_maintained_business_migration_acceptance_review_20260525.zh.md)

TM02 是 WP24 的串行 closure lane。它已在 focused validation 后发布 canonical acceptance
review 并同步索引，同时把 ground runtime expansion 与 public raw-runtime retirement
保持在 WP24 之外。TM01-B launch bridge 仍不属于 WP24，后续由 TM03 单独关闭。

## TM01 Architecture Closure Remediation

产出：

- [TM01 Architecture Closure Remediation](archive/tm01_architecture_closure_remediation/README.md)
- [TM01 Architecture Closure Task Clusters](archive/tm01_architecture_closure_remediation/tm01_architecture_closure_task_clusters_20260524.md)

TM01 仅对已审计的实现切片关闭；它不是新的 architecture WP，也不会创建 canonical
WP24 acceptance。`TM01-A` 已恢复聚焦的 ground tasking-shell 验证路径，`TM01-C`
已把 WP24 provenance wording 同步到 maintained `agent_shim.py` 默认值，`TM01-D`
已发布聚焦验证结果与 close/block 建议。

TM01 关闭后的两个 ledgered gap 已由后续 closure lane 处理：`TM02` 发布 WP24
canonical acceptance review，`TM03` 通过 `IWeaponReleaseService` 关闭
`systems -> SimulationKernel` launch-helper residual。更广泛的架构闭合、超出该
helper seam 的 P7 launch/fire-control contract 重设、public raw-runtime 或
compatibility 退场、以及完整 ground runtime 仍显式未闭合。

## WP24 TaskOrder Maintained Business Migration

产出：

- [WP24 TaskOrder Maintained Business Migration](archive/wp24_taskorder_maintained_business_migration/taskorder_maintained_business_migration_wp24_20260524.zh.md)

WP24 是 WP23 以 `blocked` 关闭后打开并已验收的 replacement-backed implementation
package，不是另一轮 recovery wave。maintained contract/export/Python business
migration 已集成；cleanup close-out 删除旧 public TaskOrder whole-shell compatibility
surfaces，而不是把它们作为 residual 接受；canonical acceptance review 已发布。

## WP23 Legacy Retirement Recovery And Reset

产出：

- [WP23 Legacy Retirement Recovery And Reset](archive/wp23_legacy_retirement_recovery/legacy_retirement_recovery_wp23_20260523.zh.md)

WP23 是 reset，不是 continuation wave。它把 WP22 queue entries 冻结为历史证据，并保持
严格文档预算：只使用 canonical WP23 plan 与中文 companion。它审计 dirty worktree，
分类每个 legacy/compatibility surface，并在有边界实现窗口内无法安全删除或迁移时以
`blocked` close-out。

WP23 收口地图：

- `WP23-A Freeze And Salvage Audit` 已完成 dirty-work 分类。
- `WP23-B Delete-Or-Block Table` 已完成 source-backed blocked/delete 判定基线。
- `WP23-C Tasking Single Representation` 以 `blocked` 收口，因为 TaskOrder
  maintained-batch work 仍与 public whole-shell read/write 和 observation exports 共存。
- `WP23-D Public API Exit` 对 runtime/world/batch escape hatches、TaskOrder
  whole-shell APIs、observation tasking exports 与 raw GPU/visual overloads 作出
  `blocked public API` 判定。
- `WP23-E Minimal Implementation Batch` 因没有识别出 deletion-ready implementation
  surface 而跳过。
- `WP23-F Close-Out` 完成受控 `blocked` recovery，不代表 legacy retirement acceptance。

## WP22 Legacy Compatibility Retirement And Architecture Hardening

产出：

- [WP22 Legacy Compatibility Retirement And Architecture Hardening](archive/wp22_legacy_compatibility_retirement/legacy_compatibility_retirement_wp22_20260522.zh.md)
- [WP22-A Retirement Fact Ledger And Kill List](archive/wp22_legacy_compatibility_retirement/wp22_retirement_fact_ledger_cluster_20260522.zh.md)
- [WP22-B Python Business Bypass Retirement](archive/wp22_legacy_compatibility_retirement/wp22_python_business_bypass_retirement_cluster_20260522.zh.md)
- [WP22-C Runtime Escape-Hatch And Legacy Mode Closure](archive/wp22_legacy_compatibility_retirement/wp22_runtime_escape_hatch_closure_cluster_20260522.zh.md)
- [WP22-D Command DTO And Legacy Surface Retirement](archive/wp22_legacy_compatibility_retirement/wp22_command_dto_legacy_surface_retirement_cluster_20260522.zh.md)
- [WP22-E Structural God-File Decomposition](archive/wp22_legacy_compatibility_retirement/wp22_structural_god_file_decomposition_cluster_20260522.zh.md)
- [WP22-F Guardrail And Acceptance Closure](archive/wp22_legacy_compatibility_retirement/wp22_guard_acceptance_closure_cluster_20260522.zh.md)
- [WP22 Subagent Dispatch Queue](archive/wp22_legacy_compatibility_retirement/wp22_subagent_dispatch_queue_20260522.zh.md)

WP22 已冻结并由 WP23 取代。它由 post-WP21 architecture refactoring audit 打开，但
continuation stream 因过多 ad-hoc waves 与 partial/quarantine evidence loops 未达到
owner 的过程标准。这些文件只保留为 provenance，不再是 active dispatch queue。

WP22 计划地图：

- `WP22-A Retirement Fact Ledger And Kill List` 先启动，在实现依赖前修正审计事实。
- `WP22-B Python Business Bypass Retirement` 拥有 tasking/profile/mission-command
  从 raw loader/runtime access 迁出的工作。
- `WP22-C Runtime Escape-Hatch And Legacy Mode Closure` 拥有 raw runtime、
  batch-runtime、loader-sim 与 silent legacy-mode quarantine。
- `WP22-D Command DTO And Legacy Surface Retirement` 拥有 C++ command、DTO 与
  setup legacy-surface retirement。
- `WP22-E Structural God-File Decomposition` 拥有 monolithic
  contract/facade/window/factory 文件的 behavior-preserving splits。
- `WP22-F Guardrail And Acceptance Closure` 串行执行；若仍有 unowned default
  legacy path，则必须使 closure 失败。

## WP21 Full Counterfactual Experiment Runtime

产出：

- [WP21 Full Counterfactual Experiment Runtime](archive/wp21_full_counterfactual_experiment_runtime/full_counterfactual_experiment_runtime_wp21_20260521.zh.md)
- [WP21-A Fact Ledger And Residual Freeze](archive/wp21_full_counterfactual_experiment_runtime/wp21_fact_ledger_residual_freeze_cluster_20260521.zh.md)
- [WP21-B Snapshot Restore And Worldline Boundary](archive/wp21_full_counterfactual_experiment_runtime/wp21_snapshot_restore_worldline_boundary_cluster_20260521.zh.md)
- [WP21-C Counterfactual Rollout And Causal Difference](archive/wp21_full_counterfactual_experiment_runtime/wp21_counterfactual_rollout_causal_difference_cluster_20260521.zh.md)
- [WP21-D Scenario Intervention Generation Runtime](archive/wp21_full_counterfactual_experiment_runtime/wp21_scenario_intervention_generation_cluster_20260521.zh.md)
- [WP21-E Experiment Facade And Evidence Collection](archive/wp21_full_counterfactual_experiment_runtime/wp21_experiment_facade_evidence_cluster_20260521.zh.md)
- [WP21-F Final Cleanup And Acceptance Handoff](archive/wp21_full_counterfactual_experiment_runtime/wp21_final_cleanup_acceptance_cluster_20260521.zh.md)
- [WP21 Subagent Dispatch Queue](archive/wp21_full_counterfactual_experiment_runtime/wp21_subagent_dispatch_queue_20260521.zh.md)
- [已争议的 WP21 验收记录](../review/archive/wp-acceptance/wp21_full_counterfactual_experiment_runtime_acceptance_review_20260522.zh.md)

WP21 是存在争议的最后一个计划中 refactor stage。它消费 WP15 contracts、WP17 的
selected runtime branch/compare slice、WP18 ownership residuals、WP19
host-visible state boundaries 与 WP20 typed setup evidence，但 claimed closure 已在
`2026-05-22` 被 owner 否决。它不得再作为 legacy compatibility layers 已退场的证明。

WP21 争议地图：

- `WP21-A Fact Ledger And Residual Freeze` 先启动并冻结 source facts。
- `WP21-B Snapshot Restore And Worldline Boundary` 拥有 bounded host-owned
  snapshot/restore 与 worldline identity。
- `WP21-D Scenario Intervention Generation Runtime` 可在 A 后与 B 并行，并拥有
  deterministic generated artifacts 与 loader boundary guards。
- `WP21-C Counterfactual Rollout And Causal Difference` 等待 B，并拥有
  parent/branch rollout。
- `WP21-E Experiment Facade And Evidence Collection` 等待 C/D，并拥有 public
  orchestration/evidence surface。
- `WP21-F Final Cleanup And Acceptance Handoff` 未达到 owner acceptance bar；
  归档的 acceptance review 仅保留为历史记录，并由 WP22 取代。

## WP20 Public Capability-Platform Composition

产出：

- [WP20 Public Capability-Platform Composition](archive/wp20_public_capability_platform_composition/public_capability_platform_composition_wp20_20260521.zh.md)
- [WP20-A Public Capability Fact Ledger](archive/wp20_public_capability_platform_composition/wp20_public_capability_fact_ledger_cluster_20260521.zh.md)
- [WP20-B Public Typed Platform Spawn Contract](archive/wp20_public_capability_platform_composition/wp20_public_typed_platform_spawn_contract_cluster_20260521.zh.md)
- [WP20-C Runtime Setup Consume Bridge](archive/wp20_public_capability_platform_composition/wp20_runtime_setup_consume_bridge_cluster_20260521.zh.md)
- [WP20-D Facade And Binding Public Surface](archive/wp20_public_capability_platform_composition/wp20_facade_binding_public_surface_cluster_20260521.zh.md)
- [WP20-E Compatibility And Schema Guard](archive/wp20_public_capability_platform_composition/wp20_compatibility_schema_guard_cluster_20260521.zh.md)
- [WP20-F Integration And Handoff](archive/wp20_public_capability_platform_composition/wp20_integration_handoff_cluster_20260521.zh.md)
- [WP20 Subagent Dispatch Queue](archive/wp20_public_capability_platform_composition/wp20_subagent_dispatch_queue_20260521.zh.md)
- [WP20 验收审查](../review/archive/wp-acceptance/wp20_public_capability_platform_composition_acceptance_review_20260521.zh.md)

WP20 是已验收的第三个冻结 post-WP17 阶段。它消费 WP14 的 capability composition
vocabulary 与 WP17 的 internal resolved-plan spawn path，通过 validation-first
admission/result evidence 公开 typed platform setup。它必须保留
`spawn_unit(type_name)`、`WorldSpawnRequest.type_name`、legacy scenario setup
以及 backend `RuntimeCapabilities` 分离。

WP20 当前地图：

- `WP20-A Public Capability Fact Ledger` 在实现前冻结 source-backed facts。
- `WP20-B Public Typed Platform Spawn Contract` 拥有 admission/result DTO shape
  与 ordering rules。
- `WP20-E Compatibility And Schema Guard` 把 WP14 additive-only guards 更新为
  WP20 validation-first publicization guards。
- `WP20-C Runtime Setup Consume Bridge` 已返回并通过 focused validation。
- `WP20-D Facade And Binding Public Surface` 已返回并通过 focused validation。
- `WP20-F Integration And Handoff` 已关闭为串行 closure lane。

## WP19 CUDA And Resident-State Mainline Alignment

产出：

- [WP19 CUDA And Resident-State Mainline Alignment](archive/wp19_cuda_resident_state_alignment/cuda_resident_state_alignment_wp19_20260521.zh.md)
- [WP19-A CUDA / Resident-State Fact Ledger](archive/wp19_cuda_resident_state_alignment/wp19_cuda_resident_state_fact_ledger_cluster_20260521.zh.md)
- [WP19-B Device-Resident Output Contract Pre-Gate](archive/wp19_cuda_resident_state_alignment/wp19_device_resident_output_contract_cluster_20260521.zh.md)
- [WP19-C GPU Helper Diagnostics Boundary](archive/wp19_cuda_resident_state_alignment/wp19_gpu_helper_diagnostics_boundary_cluster_20260521.zh.md)
- [WP19-D Resident-State Sync And Shard Contract](archive/wp19_cuda_resident_state_alignment/wp19_resident_state_sync_shard_contract_cluster_20260521.zh.md)
- [WP19-E First CUDA Alignment Slice](archive/wp19_cuda_resident_state_alignment/wp19_first_cuda_alignment_slice_cluster_20260521.zh.md)
- [WP19-F Integration And Handoff](archive/wp19_cuda_resident_state_alignment/wp19_integration_handoff_cluster_20260521.zh.md)
- [WP19 Subagent Dispatch Queue](archive/wp19_cuda_resident_state_alignment/wp19_subagent_dispatch_queue_20260521.zh.md)
- [WP19 验收审查](../review/archive/wp-acceptance/wp19_cuda_resident_state_alignment_acceptance_review_20260521.zh.md)

WP19 是已验收的第二个冻结 post-WP17 阶段。它消费已验收的 WP18 runtime-ownership
边界，把现有 CUDA helpers、device-resident output metadata 与 resident-state sync
vocabulary 对齐到 maintained facade/backend profile model。它默认不晋级 exact GPU
world-step 或 maintained resident-state support。

WP19 工作流地图：

- `WP19-A CUDA / Resident-State Fact Ledger` 在实现前冻结当前 source/test facts。
- `WP19-B Device-Resident Output Contract Pre-Gate` 定义 fail-closed output metadata
  与 DTO placement。
- `WP19-C GPU Helper Diagnostics Boundary` 防止 helper/probe availability 意外成为
  maintained capability evidence。
- `WP19-D Resident-State Sync And Shard Contract` 将 state ownership、shard、sync、
  stale-read 与 export rules 映射到 runtime evidence。
- `WP19-E First CUDA Alignment Slice` 等 A-D 识别出安全 bounded helper/output path 后释放。
- `WP19-F Integration And Handoff` 是 evidence streams 返回后的串行 closure。
- [WP19 验收审查](../review/archive/wp-acceptance/wp19_cuda_resident_state_alignment_acceptance_review_20260521.zh.md)

## WP18 Runtime Ownership And C++ Hot Path Consolidation

产出：

- [WP18 Runtime Ownership And C++ Hot Path Consolidation](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/runtime_ownership_cxx_hot_path_consolidation_wp18_20260521.zh.md)
- [WP18-A Ownership Fact Ledger And Hot-Path Map](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_ownership_fact_ledger_hot_path_map_cluster_20260521.zh.md)
- [WP18-B Execution Episode Ownership Sink](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_execution_episode_ownership_sink_cluster_20260521.zh.md)
- [WP18-C ScenarioLoader Adapter Split](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_scenario_loader_adapter_split_cluster_20260521.zh.md)
- [WP18-D Facade Contract Hardening](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_facade_contract_hardening_cluster_20260521.zh.md)
- [WP18-E C++ Hot Path Migration Matrix](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_cxx_hot_path_migration_matrix_cluster_20260521.zh.md)
- [WP18-F Integration And Handoff](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_integration_handoff_cluster_20260521.zh.md)
- [WP18 Subagent Dispatch Queue](archive/wp18_runtime_ownership_cxx_hot_path_consolidation/wp18_subagent_dispatch_queue_20260521.zh.md)
- [WP18 验收审查](../review/archive/wp-acceptance/wp18_runtime_ownership_cxx_hot_path_consolidation_acceptance_review_20260521.zh.md)

WP18 是 WP17 后已验收的第一个冻结阶段。它聚焦 runtime ownership 与 C++
hot-path consolidation；CUDA/resident-state alignment、public
capability-platform composition 与 full counterfactual runtime 继续路由到
WP19、WP20 与 WP21，而不在 WP18 内声明完成。

WP18 工作流地图：

- `WP18-A Ownership Fact Ledger And Hot-Path Map` 在实现前冻结当前 source/test facts。
- `WP18-B Execution Episode Ownership Sink` 将一个 maintained execution-episode slice
  推到 C++/facade-owned evidence 后面。
- `WP18-C ScenarioLoader Adapter Split` 区分 scenario/content adaptation、runtime
  ownership 与 frontend helper responsibilities。
- `WP18-D Facade Contract Hardening` 防止 maintained callers 回退到 raw
  runtime/world-handle reads。
- `WP18-E C++ Hot Path Migration Matrix` 排序 reward/termination、route/approach、
  request build/consume 等 hot paths，并在安全时实现一条 bounded first slice。
- `WP18-F Integration And Handoff` 是实现流回收后的串行 closure。

## WP17 Stage 3 Runtime Materialization And Cleanup

产出：

- [WP17 Stage 3 Runtime Materialization And Cleanup](archive/wp17_stage3_runtime_materialization_cleanup/stage3_runtime_materialization_cleanup_wp17_20260521.zh.md)
- [WP17-A Fact Ledger And Boundary Freeze](archive/wp17_stage3_runtime_materialization_cleanup/wp17_fact_ledger_and_boundary_freeze_cluster_20260521.md)
- [WP17-B Facade Business Migration And Compatibility Cleanup](archive/wp17_stage3_runtime_materialization_cleanup/wp17_facade_business_migration_cleanup_cluster_20260521.md)
- [WP17-C Multi-Rate Runtime Example](archive/wp17_stage3_runtime_materialization_cleanup/wp17_multirate_runtime_example_cluster_20260521.md)
- [WP17-D Fidelity Provider Runtime](archive/wp17_stage3_runtime_materialization_cleanup/wp17_fidelity_provider_runtime_cluster_20260521.md)
- [WP17-E Capability Spawn Runtime Promotion](archive/wp17_stage3_runtime_materialization_cleanup/wp17_capability_spawn_runtime_cluster_20260521.md)
- [WP17-F Counterfactual Runtime Slice And Closure](archive/wp17_stage3_runtime_materialization_cleanup/wp17_counterfactual_runtime_closure_cluster_20260521.md)
- [WP17 Subagent Dispatch Queue](archive/wp17_stage3_runtime_materialization_cleanup/wp17_subagent_dispatch_queue_20260521.md)
- [WP17 验收审查](../review/archive/wp-acceptance/wp17_stage3_runtime_materialization_cleanup_acceptance_review_20260521.zh.md)

WP17 是已验收的 Stage 3 最后 runtime-materialization 与 cleanup 任务族。它按当前代码事实
把剩余 runtime work 拆成有边界的 selected-slice streams，并在 full-worldline 或
full-provider support 尚不存在的地方诚实保留 residuals。

WP17 工作流地图：

- `WP17-A Fact Ledger And Boundary Freeze` 在 runtime edits 前锁定当前代码事实和 residual boundary。
- `WP17-B Facade Business Migration And Compatibility Cleanup` 把维护中的 training/batch reads 迁到 facade-shaped env/adapter 方法，并把直接 `batch_runtime` reads 守成 compatibility-only。
- `WP17-C Multi-Rate Runtime Example` 已物化 selected architecture §8 cadence slice，并提供 hold/expiry/barrier evidence。
- `WP17-D Fidelity Provider Runtime` 已加入 facade-owned reference CPU fidelity admission 和 fail-closed provider rejection。
- `WP17-E Capability Spawn Runtime Promotion` 在保留 type-name 兼容的同时晋级内部 capability resolution chain。
- `WP17-F Counterfactual Runtime Slice And Closure` 已实现 explicit-setup selected-entity branch/compare；arbitrary live-world clone 与 full counterfactual orchestration 仍是 residual。

## WP16 Runtime Spine Consolidation

产出：

- [WP16 Runtime Spine Consolidation](archive/wp16_runtime_spine_consolidation/runtime_spine_consolidation_wp16_20260521.zh.md)
- [WP16-A Runtime Spine Inventory And Bypass Map](archive/wp16_runtime_spine_consolidation/wp16_runtime_spine_inventory_cluster_20260521.zh.md)
- [WP16-B Clock-Domain Enforcement And Merge Trace](archive/wp16_runtime_spine_consolidation/wp16_clock_domain_enforcement_cluster_20260521.zh.md)
- [WP16-C Facade And Batch Path Spine Migration](archive/wp16_runtime_spine_consolidation/wp16_facade_batch_spine_migration_cluster_20260521.zh.md)
- [WP16-D Legacy Path Deprecation And Compatibility Gates](archive/wp16_runtime_spine_consolidation/wp16_legacy_deprecation_compatibility_cluster_20260521.zh.md)
- [WP16-E Generated Documentation And Closure Automation](archive/wp16_runtime_spine_consolidation/wp16_generated_documentation_automation_cluster_20260521.zh.md)
- [WP16-F Integration And Acceptance Handoff](archive/wp16_runtime_spine_consolidation/wp16_integration_acceptance_cluster_20260521.zh.md)

WP16 在 post-WP9 路线完成后开启 architecture-optimization phase。它消费
WP10-WP15 边界，并把它们转成 maintained runtime spine。WP16 现已作为
selected-slice runtime-spine consolidation 增量验收，residual register 记录在
WP16 验收审查中：

```text
setup/admission request
  -> scheduling-window input injection
  -> clock-domain trigger and skip decision
  -> manifest-derived node execution
  -> barrier and event evidence
  -> observation/facade export
  -> training, scenario, and experiment consumer
```

WP16 工作流地图：

- `WP16-A Runtime Spine Inventory And Bypass Map` 在代码迁移前盘点 maintained、
  compatibility、diagnostics-only、deprecated、blocked 与 unknown runtime paths。
- `WP16-B Clock-Domain Enforcement And Merge Trace` 把 `GAP-9` 推进到 selected
  runtime-spine slice，使未触发 clock domain 以 evidence 形式 skip、defer 或 reject，
  而不是静默执行。
- `WP16-C Facade And Batch Path Spine Migration` 将 maintained facade、batch、
  training、scenario 与 experiment consumers 迁向已验收 runtime-window evidence spine。
- `WP16-D Legacy Path Deprecation And Compatibility Gates` 用 guard tests 与
  replacement evidence 分类 raw runtime、direct state、legacy spawn、diagnostics 与
  compatibility paths。
- `WP16-E Generated Documentation And Closure Automation` 通过 machine-readable status
  与 generated closure-summary hints 减少 README/review/index 手工同步，同时不替代
  acceptance authority。
- `WP16-F Integration And Acceptance Handoff` 是 A-E mergeable 后的串行 validation、
  residual、acceptance-review、README/route 与 bilingual closure lane。

WP16 已完成并验收。实现边界保持收窄：global scheduler rewrite、full
multi-rate support、public legacy API 删除，以及 maintained independent-domain
merge success 仍在范围外。

## WP15 Counterfactual Experiment Generation

产出：

- [WP15 Counterfactual Experiment Generation](archive/wp15_counterfactual_experiment_generation/counterfactual_experiment_generation_wp15_20260521.zh.md)
- [WP15-A Replay Envelope And Branch Point Contract](archive/wp15_counterfactual_experiment_generation/wp15_replay_envelope_branch_point_cluster_20260521.zh.md)
- [WP15-B Worldline Branch Metadata Gate](archive/wp15_counterfactual_experiment_generation/wp15_worldline_branch_metadata_gate_cluster_20260521.zh.md)
- [WP15-C Counterfactual Request Admission](archive/wp15_counterfactual_experiment_generation/wp15_counterfactual_admission_cluster_20260521.zh.md)
- [WP15-D Scenario And Adversary Generation Request Surface](archive/wp15_counterfactual_experiment_generation/wp15_scenario_adversary_generation_surface_cluster_20260521.zh.md)
- [WP15-E Experiment Evidence And Capability Profiling Bridge](archive/wp15_counterfactual_experiment_generation/wp15_experiment_evidence_bridge_cluster_20260521.zh.md)
- [WP15-F Integration And Acceptance Handoff](archive/wp15_counterfactual_experiment_generation/wp15_integration_acceptance_cluster_20260521.zh.md)

WP15 验收 post-WP9 路线 Phase 6。它消费 WP8 learning-face vocabulary，以及已验收
WP10-WP14 的 causal、facade、agency、backend/fidelity 与 capability evidence。第一目标
不是 full counterfactual rollout，而是先建立 evidence boundary：让 replay envelopes、
branch points、worldline metadata、generation requests 与 experiment evidence ancestry
在任何 branch 修改 authoritative runtime state 前都可机器检查。

WP15 工作流地图：

- `WP15-A Replay Envelope And Branch Point Contract` 定义 deterministic replay
  envelope 与 branch point vocabulary，并携带 seed、snapshot、barrier、event-order 与
  facade provenance evidence。
- `WP15-B Worldline Branch Metadata Gate` 命名 parent/child worldline metadata、
  mutation intent、provenance 与 unsupported-restore boundaries。
- `WP15-C Counterfactual Request Admission` 在 replay、branch、authority、
  backend/fidelity 与 capability evidence 后接受或拒绝 counterfactual requests。
- `WP15-D Scenario And Adversary Generation Request Surface` 为 scenario/adversary
  inputs 添加 deterministic generation request schemas 与 non-mutation guards。
- `WP15-E Experiment Evidence And Capability Profiling Bridge` 连接 experiment runs、
  comparisons、generated inputs、capability profiles、backend profiles 与 capability
  evidence，同时不做 score-to-truth promotion。
- `WP15-F Integration And Acceptance Handoff` 是串行 validation、residual、
  acceptance-review、README/route 与 bilingual closure lane。

`WP15-A` 到 `WP15-E` 第一切片已经验收。`WP15-F` 已完成 closure lane，负责
validation、residuals、acceptance review、README/route sync 与 bilingual handoff。

## WP14 Capability Composition

产出：

- [WP14 Capability Composition](archive/wp14_capability_composition/capability_composition_wp14_20260521.zh.md)
- [WP14-A Capability Bundle Contract](archive/wp14_capability_composition/wp14_capability_bundle_contract_cluster_20260521.zh.md)
- [WP14-B Content Definition Lowering](archive/wp14_capability_composition/wp14_content_definition_lowering_cluster_20260521.zh.md)
- [WP14-C Spawn Resolution Bridge](archive/wp14_capability_composition/wp14_spawn_resolution_bridge_cluster_20260521.zh.md)
- [WP14-D Additive Facade Setup DTO](archive/wp14_capability_composition/wp14_additive_facade_setup_dto_cluster_20260521.zh.md)
- [WP14-E Capability Effects Materialization](archive/wp14_capability_composition/wp14_capability_effects_materialization_cluster_20260521.zh.md)
- [WP14-F Compatibility Validation And Acceptance Handoff](archive/wp14_capability_composition/wp14_compatibility_validation_acceptance_cluster_20260521.zh.md)
- [WP14 验收审查](../review/archive/wp-acceptance/wp14_capability_composition_acceptance_review_20260521.zh.md)

WP14 验收 post-WP9 路线 Phase 5。它消费 WP2/WP9 contract vocabulary，以及
WP10-WP13 runtime、facade、agency 与 backend evidence，把隐式 platform
composition 转成有边界、可测试的实现流。第一切片保持 `spawn_unit(type_name)` 与
`WorldSpawnRequest.type_name` 兼容，同时在 materialization 前引入
`type_name -> CapabilityBundle template -> ResolvedPlatformSpawnPlan` resolution。

WP14 工作流地图：

- `WP14-A Capability Bundle Contract` 定义 platform-semantic `Capability`、
  `CapabilityBundle`、capability-family vocabulary 与 resolved-plan evidence，
  并避免与 backend `RuntimeCapabilities` 命名域冲突。
- `WP14-B Content Definition Lowering` 把现有 content/factory evidence 映射为
  deterministic capability templates 与 resolved spawn plans。
- `WP14-C Spawn Resolution Bridge` 让既有 spawn 路径在 materialization 前经过
  resolution，同时保持 public compatibility。
- `WP14-D Additive Facade Setup DTO` 为未来 typed platform spawn requests 准备
  additive setup vocabulary，而不是强制替换。
- `WP14-E Capability Effects Materialization` 把 capability families 绑定到现有
  ECS/component materialization evidence 与 unsupported-effect reasons，不添加新战术行为。
- `WP14-F Compatibility Validation And Acceptance Handoff` 是 A-E mergeable 后的
  串行 validation、residual、acceptance-review、README/route 与 bilingual closure lane。

`WP14-A` 到 `WP14-F` 均已验收。已验收边界是 compatibility bridge：type-name
setup 仍为维护中路径，typed platform spawn DTOs 是 additive，public
`spawn_platform({capabilities...})`、scenario-schema migration、backend/fidelity
promotion 与 broad spawn rewrites 仍属于未来 gated work。

## WP13 Backend Fidelity Expansion

产出：

- [WP13 Backend Fidelity Expansion](archive/wp13_backend_fidelity_expansion/backend_fidelity_expansion_wp13_20260520.zh.md)
- [WP13-A Runtime Capability Query And Rejection Surface](archive/wp13_backend_fidelity_expansion/wp13_runtime_capability_query_cluster_20260520.zh.md)
- [WP13-B Backend Profile Registry Runtime Gate](archive/wp13_backend_fidelity_expansion/wp13_backend_profile_registry_gate_cluster_20260520.zh.md)
- [WP13-C Parity Budget Evidence Gate](archive/wp13_backend_fidelity_expansion/wp13_parity_budget_evidence_gate_cluster_20260520.zh.md)
- [WP13-D Fidelity Profile Request Gate](archive/wp13_backend_fidelity_expansion/wp13_fidelity_profile_request_gate_cluster_20260520.zh.md)
- [WP13-E Facade And Binding Proof](archive/wp13_backend_fidelity_expansion/wp13_facade_binding_proof_cluster_20260520.zh.md)
- [WP13-F Integration And Acceptance Handoff](archive/wp13_backend_fidelity_expansion/wp13_integration_acceptance_cluster_20260520.zh.md)
- [WP13 验收审查](../review/archive/wp-acceptance/wp13_backend_fidelity_expansion_acceptance_review_20260520.zh.md)

WP13 验收 post-WP9 路线 Phase 4。它消费 WP6/WP7 backend profile
policy/materialization，以及 WP10-WP12 causal、provenance 与 agency evidence，
把 backend/fidelity support 转成可查询、可拒绝、有测试支撑的 runtime facts，同时不晋级
exact GPU、resident-state、shadow 或 multi-fidelity support。

WP13 工作流地图：

- `WP13-A Runtime Capability Query And Rejection Surface` 添加保守 capability
  metadata 与稳定 unsupported reasons，同时保持 false support defaults。
- `WP13-B Backend Profile Registry Runtime Gate` 让已验收 backend profile seed
  records 进入 code-owned 形态，并校验 maintained/candidate/diagnostics boundaries。
- `WP13-C Parity Budget Evidence Gate` 让 profile-owned parity budget records 以及
  missing/incompatible budget rejection 可机器检查。
- `WP13-D Fidelity Profile Request Gate` 把 fidelity labels 作为绑定 profile、budget、
  model scope、validation 与 evidence 的 requests，而不是 support claims。
- `WP13-E Facade And Binding Proof` 通过 maintained facade 与 Python binding surfaces
  证明 query 与 rejection 行为。
- `WP13-F Integration And Acceptance Handoff` 是串行 validation、residual、
  acceptance-review、README/index 与 bilingual closure lane。

`WP13-A` 到 `WP13-F` 均已验收。已接受 baseline 只 admission CPU exact
reference fidelity requests，并保持 exact GPU、resident-state、shadow、adaptive
fidelity、learned provider runtime 与 maintained multi-fidelity support 不在范围内。

本阶段 commit message 应使用 capability/result language，而不是 internal
work-package labels。

## WP12 Information And Agency Enforcement

产出：

- [WP12 Information And Agency Enforcement](archive/wp12_information_agency_enforcement/information_agency_enforcement_wp12_20260520.zh.md)
- [WP12-A Law 14 Read-Side Enforcement](archive/wp12_information_agency_enforcement/wp12_law14_read_side_enforcement_cluster_20260520.zh.md)
- [WP12-B Agency Role Authority Boundary](archive/wp12_information_agency_enforcement/wp12_agency_role_authority_cluster_20260520.zh.md)
- [WP12-C Information Transformation Surface](archive/wp12_information_agency_enforcement/wp12_information_transformation_surface_cluster_20260520.zh.md)
- [WP12-D Intent Injection Authority Guard](archive/wp12_information_agency_enforcement/wp12_intent_injection_authority_guard_cluster_20260520.zh.md)
- [WP12-E Integration And Acceptance Handoff](archive/wp12_information_agency_enforcement/wp12_integration_acceptance_cluster_20260520.zh.md)

WP12 验收 post-WP9 路线的 Phase 3。它消费 WP10 causal evidence 与 WP11
provenance/pre-gates，并把 `GAP-5`、`GAP-6` 与 `GAP-7` 转成有测试支撑的
read-side、role/authority 与 information-transformation gates。

WP12 工作流地图：

- `WP12-A Law 14 Read-Side Enforcement` 把 maintained consumer pre-gates 晋升为
  focused packet/belief read-side enforcement，同时保留显式 diagnostics-only
  truth paths。
- `WP12-B Agency Role Authority Boundary` 在 maintained outputs 被授权前校验
  `AgentRole` authority scope、information source、decision-model reference 与
  action interface。
- `WP12-C Information Transformation Surface` 让 selected information
  transformation chain 可机器检查，而不重写所有 producer。
- `WP12-D Intent Injection Authority Guard` 整合 A-C，使 maintained
  `DecisionBelief -> ActionIntentPacket` / `CoordinationIntentPacket` 路径使用
  provenance、authority metadata、timing metadata 与 facade-compatible injection。
- `WP12-E Integration And Acceptance Handoff` 是串行 validation、residual、
  acceptance-review、README/index 与 bilingual closure lane。

`WP12-B`、`WP12-C` 与 `WP12-D` 是思考预算最高的 streams。`WP12-A`、`WP12-B`
与 `WP12-C` 可在写入范围分离时并行启动；`WP12-D` 应等待它们的
validator/vocabulary surfaces；`WP12-E` 最后执行。

### WP2.5 工作流地图

WP2.5 虽然是冻结文档，但后续工作已经拆成有边界的流：

- 先做 `WP2.5-F StageNodeManifest Schema`：
  [manifest/event 任务簇](archive/wp25_scheduler_semantics/wp25_manifest_event_cluster_20260519.zh.md)。
- 在 manifest 词汇稳定后，并行推进 `WP2.5-A Event Ordering and ID Rules`、
  `WP2.5-B State Shard Versioning`、`WP2.5-C Barrier Visibility`：
  [state/barrier 任务簇](archive/wp25_scheduler_semantics/wp25_state_barrier_cluster_20260519.zh.md)。
- 语义规则稳定后，再做 `WP2.5-D Clock-Domain Merge`。
- 调度语义完全冻结后，再做 `WP2.5-E Deterministic Replay Contract`：
  [clock/replay 任务簇](archive/wp25_scheduler_semantics/wp25_clock_replay_cluster_20260519.zh.md)。
- 最后做 `WP2.5-G Integration and Index Sync`，作为串行发布步骤。

`WP2.5-D` 和 `WP2.5-E` 是思考预算最高的两个工作流。

## WP7.5 训练路径 facade 桥接

产出：

- [WP7.5 训练路径 facade 桥接](archive/wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.zh.md)

`WP7.5` 是已验收仿真侧 facade contracts 与计划中的 learning-facing contract
vocabulary 之间缺失的桥。它不替代 `WP8`；它负责把维护中的训练主线从
`RuntimeFacade.runtime()` 逃逸口迁到
`RuntimeFacade.step_execution_batch()` 与
`RuntimeFacade.export_observation_packet()`。

`WP7.5` 工作流地图：

- `WP7.5-A Step Execution Mainline` 把维护中的 batch stepping 迁到
  `ExecutionBatchStepRequest` / `ExecutionBatchStepResult`。
- `WP7.5-B Observation Packet Mainline` 把维护中的 observation 读取迁到
  `ObservationBatchRequest` / `ObservationBatchPacket`。
- `WP7.5-C Compatibility Escape Hatch Reduction` 把 raw runtime access 收窄到
  显式的 compatibility / diagnostics seam。
- `WP7.5-D Validation And Integration Sync` 串行执行，把该桥接线发布到
  README、review 与 `WP8` 引用。

`WP7.5-A` 与 `WP7.5-B` 是思考预算最高的工作流，因为它们会改变维护中的训练主线，
同时必须保持现有 facade 与信息状态规则不被破坏。

`WP7.5` 在拆分给多个 worker 时，应使用
[Subagent 使用规范](../../standards/governance/subagent_usage_policy.zh.md)。

## WP8 SCAL Learning Face

产出：

- [WP8 SCAL Learning Face 任务族](archive/wp8_learning_face/learning_face_wp8_20260520.zh.md)
- [WP8-A 课程与场景生成任务簇](archive/wp8_learning_face/wp8_curriculum_scenario_generation_cluster_20260520.zh.md)
- [WP8-B evaluation 与 capability profiling 任务簇](archive/wp8_learning_face/wp8_evaluation_capability_profiling_cluster_20260520.zh.md)
- [WP8-C world-model 接口与学习证据任务簇](archive/wp8_learning_face/wp8_world_model_interface_and_learning_evidence_cluster_20260520.zh.md)
- [WP8 学习面验收审查](../review/archive/wp-acceptance/wp8_learning_face_acceptance_review_20260520.zh.md)

WP8 为延后的 SCAL learning face 提供已验收的有边界任务族。它不引入第二条运行时生命周期，而是把课程、评估、能力画像、场景生成与学习证据转成显式的实验与规划契约，并保持它们与权威仿真层分离。

WP8 工作流地图：

- `WP8-A Curriculum And Scenario Generation` 定义场景、seed、课程阶段与生成请求如何选择和版本化。
- `WP8-B Evaluation And Capability Profiling` 定义基准协议、画像 schema、分数归因与能力证据。
- `WP8-C World-Model Interface And Learning Evidence` 定义学习面如何消费 facade-shaped observation，并在不成为 truth source 的前提下记录证据。
- `WP8-D Integration And Index Sync` 负责串行更新任务/审查索引、交叉引用与双语对齐。

`WP8-B` 和 `WP8-C` 是思考预算最高的工作流，因为它们必须让学习输出保持可比较，同时避免滑向隐藏的 truth ownership。

## WP9 Contract And Infrastructure Closure

产出：

- [WP9 Contract And Infrastructure Closure](archive/wp9_contract_infrastructure_closure/contract_infrastructure_closure_wp9_20260520.zh.md)
- [WP9-A DTO Promotion Batch 1](archive/wp9_contract_infrastructure_closure/wp9_dto_promotion_batch1_cluster_20260520.zh.md)
- [WP9-B DTO Promotion Batch 2](archive/wp9_contract_infrastructure_closure/wp9_dto_promotion_batch2_cluster_20260520.zh.md)
- [WP9-C Infrastructure Closure](archive/wp9_contract_infrastructure_closure/wp9_infrastructure_closure_cluster_20260520.zh.md)
- [WP9-D Guard Enforcement](archive/wp9_contract_infrastructure_closure/wp9_guard_enforcement_cluster_20260520.zh.md)
- [WP9-E Integration And Index Sync](archive/wp9_contract_infrastructure_closure/wp9_integration_and_index_sync_cluster_20260520.zh.md)
- [WP9 验收审查](../review/archive/wp-acceptance/wp9_contract_infrastructure_closure_acceptance_review_20260520.zh.md)

WP9 把已验收 `WP3-WP8` 审查中延后的事项压缩为一个闭合工作包。它晋升 typed DTO surface，修补小型 infrastructure gap，添加显式 guard allowlists，并让 post-WP9 roadmap 与已验收闭合保持分离。

WP9 已验收，但保留一个已跟踪残余项：`INF-6` real missile terminal
effects capture 仍属于后续 owner 任务，因为当前 damage system 缺少窄的
maintained recorder seam。该残余已记录在 WP3 任务族与 WP9 验收审查中。

WP9 工作流地图：

- `WP9-A DTO Promotion Batch 1` 晋升 `RewardReport`、`TerminationSpec`、
  `ObservationBatchPacket` metadata 与 `ObservationViewSpec`。
- `WP9-B DTO Promotion Batch 2` 晋升 `ActionIntentPacket`、
  `CoordinationIntentPacket`、`AgentRole` 与 `DecisionBelief`。
- `WP9-C Infrastructure Closure` 关闭 naming、diagnostics、capability
  trigger、manifest registry、facade split 与 WP3 event residual 项目。
- `WP9-D Guard Enforcement` 添加文档化 guard allowlist 与 binding smoke promotion。
- `WP9-E Integration And Index Sync` 是串行发布与验收步骤。

`WP9-A`、`WP9-B`、`WP9-D` 与 `WP9-E` 已验收。`WP9-C` 带 `INF-6`
残余项验收；其余 WP9 infrastructure 项已经闭合。

## WP0 范围

WP0 仅限文档：

- 新增严格架构基线，
- 开启本任务子项目，
- 更新导航入口，
- 避免代码变更，
- 在 WP1/WP2 证据收集前不决定具体字段布局。

退出标准：

1. `docs/plan/architecture` 有明确的架构权威文档。
2. `docs/task` 有仿真架构入口。
3. 任务入口说明为什么武器工作应被视为带多 clock domain 的跨领域交战试点，而不是独立纵向栈。

## WP1 Pipeline Inventory

WP1 应检查现有代码并产出一张表，把当前资产映射到规范语义生命周期：

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

预期证据：

- 相关 `src/components/*` DTO，
- `src/systems/*` 阶段行为，
- `src/models/*` 模型实现，
- `src/core/engine/*` 编排面，
- `src/runtime/facade/*` request/result 覆盖，
- Python adapter 兼容路径，
- 已经约束或违反目标边界的测试，
- clock domain、event queue、state-store feedback 或当前跨阶段耦合证据。

WP1 不应实现新代码，除非需要少量文档或测试 fixture 才能完成 inventory。

## WP2 Contract Freeze

输入：

- [WP1 管线盘点](archive/wp1_pipeline_inventory/pipeline_inventory_wp1_20260519.zh.md)

产出：

- [WP2 契约冻结](archive/wp2_contract_freeze/contract_freeze_wp2_20260519.zh.md)

WP2 应把 inventory 转化为有范围的契约计划。它应决定：

1. 哪些 packet 族已经存在，
2. 哪些只是兼容性聚合，
3. 哪些需要新的 facade-level request/result API，
4. 哪些应保留为 component-only，
5. 哪些 stage node 需要显式 read/write set、clock domain、latency policy 与 sync policy，
6. 哪些 same-window DAG edge 由数据依赖推导，哪些属于跨窗口反馈，
7. 哪些 state shard 现在或未来 partial sync 时需要版本化，
8. 哪些 event family 需要确定性 `(timestamp, priority, event_id)` 排序，
9. 哪些 clock domain 可以使用默认嵌套触发，哪些需要显式 merge policy，
10. 哪些 Python 调用需要 adapter 兼容，
11. 哪些 observation schema 是策略/测试拥有的 `ObservationViewSpec` 变体，哪些是仿真拥有的 state export，
12. policy action cadence 如何通过 `ActionIntentPacket` 与 `ActionHoldPolicy` 映射到 `P3/P4/P5`，
13. reward 如何依据架构基线中的 fact/shaping 判据拆分为仿真事实与实验 shaping，
14. `terminated` 与 `truncated` reason 如何归因到仿真、策略或编排来源，
15. 哪一侧拥有权威 episode phase，哪一侧只为 Gymnasium、batch、replay 或 CI API 做 mirror，
16. scripted、learned 与 human coordination director 如何在不 raw ECS mutation 的情况下写入 tasking 或 command intent，
17. 每个 cross-layer producer 使用哪种 `merge_policy`，
18. 每条 action 或 coordination 路径期待哪种 scheduling-window injection 语义，
19. 哪些 observation schema 变更属于 minor-compatible，哪些属于 major-incompatible。

预期产出是冻结文档，而不是实现。

架构闭合备注：

- 仿真/策略/编排层边界上的架构框架已经闭合。
- 剩余 `B` 层契约语义细节应直接 patch 架构基线。
- `C` 层实现对齐应进入 task plan 跟踪。
- `D` 层内部设计空白，例如策略层内部或编排层内部架构，应新建独立架构文档，不应重开仿真层框架。

## WP3 Engagement Pilot

产出：

- [WP3 交战试点任务族](archive/wp3_engagement_pilot/engagement_pilot_wp3_20260519.zh.md)

第一条实现试点应选择交战生命周期，因为它横跨最多架构边界，并且天然涉及多个 clock domain：

`tasking -> command delivery -> sensor/track -> fire control -> launcher -> munition -> seeker/guidance/fuze -> effects -> damage -> observation`

该试点必须涉及至少两个平台族，例如：

- 航空挂架发射，
- 舰载挂载发射。

试点应避免创建独立的 `air weapon` 和 `naval weapon` 运行时路径。差异应出现在 launcher、munition、seeker、guidance、fuze、effects、doctrine 族和 clock-domain policy 中。

第一波实现应拆分为 contract DTO scaffold、facade packet shell、Python binding exposure、air launch adapter、naval launch adapter、munition/damage export、diagnostics trace 和 stage-aligned non-RL smoke harness。Air 与 naval worker 只有在不编辑同一个共享 kernel 文件时才适合并行。

## WP4 Facade 对齐

产出：

- [WP4 facade 对齐任务族](archive/wp4_facade_alignment/facade_alignment_wp4_20260519.zh.md)

WP4 把已验收的交战试点转成维护中的前端形态。它应引用 WP2.5 的调度语义，并引用 Temp-02 的 information/agency 边界：

- `ObservationPacket` 是智能体被允许看见的内容。
- `DecisionBelief` 是智能体在 inference、memory、doctrine 或 learned state 作用后认为真实的内容。
- `AgentRole` 是 role + authority + information-state source + decision-model reference + action interface。

WP4 不应创建新的仿真语义。它应让现有行为通过 facade-shaped API 或已记录 compatibility adapter 到达。

WP4 分发任务簇：

- 先做 `WP4-A Surface Inventory`：
  [surface inventory 任务簇](archive/wp4_facade_alignment/wp4_surface_inventory_cluster_20260519.zh.md)。
- 初始 surface 词汇稳定后，再做 `WP4-B/C Engagement, Step, And Lifecycle Alignment`：
  [engagement/step 任务簇](archive/wp4_facade_alignment/wp4_engagement_step_cluster_20260519.zh.md)。
- action、coordination、observation、belief 与 agent-role 名称稳定后，再做 `WP4-D/E Policy, AgentRole, And Python Mirror`：
  [policy/binding 任务簇](archive/wp4_facade_alignment/wp4_policy_binding_cluster_20260519.zh.md)。
- `WP4-F Integration And Docs` 保持串行，由主线程或专门 integration worker 在任务簇返回后处理。

`WP4-A`、`WP4-C` 与 `WP4-D` 是思考预算最高的工作流，因为它们触及跨层语义、belief 边界或 adapter ownership。

WP4 第一波产物已作为 discovery 输入验收：

- [WP4 第一波验收审查](../review/archive/wp-superseded/wp4_first_wave_acceptance_review_20260519.zh.md)
- [WP4-A surface inventory 初稿](archive/wp4_facade_alignment/wp4_surface_inventory_wp4a_20260519.zh.md)
- [WP4-B/C engagement-step 对齐笔记](archive/wp4_facade_alignment/wp4_engagement_step_alignment_notes_20260519.md)
- [WP4-D/E policy-binding 对齐笔记](archive/wp4_facade_alignment/wp4_policy_binding_alignment_notes_20260519.zh.md)

WP4 第二波任务簇：

- `WP4-G Facade Evidence Gates`：
  [facade evidence 任务簇](archive/wp4_facade_alignment/wp4_facade_evidence_cluster_20260519.zh.md)。
- `WP4-H Information And Agent Shim`：
  [agent shim 任务簇](archive/wp4_facade_alignment/wp4_agent_shim_cluster_20260519.zh.md)。
- `WP4-I Compatibility Guard And Integration`：
  [compat guard 任务簇](archive/wp4_facade_alignment/wp4_compat_guard_cluster_20260519.zh.md)。

WP4 第二波与集成产物：

- [WP4 第二波验收审查](../review/archive/wp-superseded/wp4_second_wave_acceptance_review_20260519.zh.md)
- [WP4-I compatibility guard 笔记](archive/wp4_facade_alignment/wp4_compat_guard_notes_20260519.zh.md)
- [WP4-F 集成交接](archive/wp4_facade_alignment/wp4_integration_handoff_20260519.zh.md)
- [WP4 最终验收审查](../review/archive/wp-acceptance/wp4_facade_alignment_acceptance_review_20260519.zh.md)

## WP5 验证套件

产出：

- [WP5 验证套件任务族](archive/wp5_validation_harness/validation_harness_wp5_20260519.zh.md)

WP5 把架构与 facade 工作转化为维护中的证据。验证套件应覆盖五个验证层级：

- design conformance，
- trace conformance，
- boundary conformance，
- information/belief leakage，
- replay/evidence conformance。

WP5 从已验收的 WP4 facade label 启动。它不应从 raw runtime inspection 出发；重点是证明 facade-shaped artifact、diagnostics 与 replay metadata 足以验证共享架构。

WP5 第一波任务簇：

- `WP5-A Harness Inventory`：
  [harness inventory 任务簇](archive/wp5_validation_harness/wp5_harness_inventory_cluster_20260519.zh.md)。
- `WP5-B Design And Boundary Gates`：
  [design/boundary 任务簇](archive/wp5_validation_harness/wp5_design_boundary_cluster_20260519.zh.md)。
- `WP5-C Trace And Replay Gates`：
  [trace/replay 任务簇](archive/wp5_validation_harness/wp5_trace_replay_cluster_20260519.zh.md)。

`WP5-C` 是第一波中推理预算最高的流，因为 trace ancestry 与 replay metadata
测试如果假设了 WP4 明确推迟的 runtime metadata，就会变得脆弱。

WP5 第一波产物已验收：

- [WP5 第一波验收审查](../review/archive/wp-superseded/wp5_first_wave_acceptance_review_20260519.zh.md)
- [WP5-A harness inventory 笔记](archive/wp5_validation_harness/wp5_harness_inventory_notes_20260519.zh.md)
- [WP5-B design/boundary 笔记](archive/wp5_validation_harness/wp5_design_boundary_notes_20260519.zh.md)
- [WP5-C trace/replay gates 笔记](archive/wp5_validation_harness/wp5_trace_replay_gates_notes_20260519.zh.md)

WP5 第二波任务簇：

- `WP5-D Information And Belief Gates`：
  [information/belief 任务簇](archive/wp5_validation_harness/wp5_information_belief_cluster_20260519.zh.md)。
- `WP5-E Smoke Promotion And Docs`：
  [smoke promotion 任务簇](archive/wp5_validation_harness/wp5_smoke_promotion_cluster_20260519.zh.md)。

WP5 第二波与最终产物已验收：

- [WP5-D information/belief 验收审查](../review/archive/wp-superseded/wp5_information_belief_acceptance_review_20260519.zh.md)
- [WP5-D information/belief 笔记](archive/wp5_validation_harness/wp5_information_belief_notes_20260519.zh.md)
- [WP5-E smoke promotion 笔记](archive/wp5_validation_harness/wp5_smoke_promotion_notes_20260519.zh.md)
- [WP5 validation harness 验收审查](../review/archive/wp-acceptance/wp5_validation_harness_acceptance_review_20260519.zh.md)

## WP6 后端配置文件策略

产出：

- [WP6 后端配置文件策略](archive/wp6_backend_profile_policy/backend_profile_policy_wp6_20260519.zh.md)
- [WP6-A 后端配置文件分类分发单](archive/wp6_backend_profile_policy/wp6_backend_profile_taxonomy_cluster_20260519.zh.md)
- [WP6-A 后端配置文件注册表](archive/wp6_backend_profile_policy/wp6_backend_profile_registry_20260519.zh.md)
- [WP6-B parity budget 分发单](archive/wp6_backend_profile_policy/wp6_parity_budget_cluster_20260519.zh.md)
- [WP6-B parity budget 注册表](archive/wp6_backend_profile_policy/wp6_parity_budget_registry_20260519.zh.md)
- [WP6-C + WP6-D 集成交接](archive/wp6_backend_profile_policy/wp6_integration_and_index_sync_20260519.zh.md)
- [WP6-C1 resident-state 边界规则](archive/wp6_backend_profile_policy/wp6_resident_state_boundary_rules_20260519.zh.md)
- [WP6 后端配置文件策略验收审查](../review/archive/wp-acceptance/wp6_backend_profile_policy_acceptance_review_20260519.zh.md)

WP6 用契约把 backend profile 与 parity budget 的空档收口。它冻结 profile
词汇、budget 记录、resident-state 边界与 capability projection 规则，让
accelerated、resident-state、approximate 与 diagnostics-only 路径在进入维护态前有明确约束。

WP6 工作流地图：

- `WP6-A Backend Profile Taxonomy`：
  [taxonomy 分发单](archive/wp6_backend_profile_policy/wp6_backend_profile_taxonomy_cluster_20260519.zh.md) 与
  [profile 注册表](archive/wp6_backend_profile_policy/wp6_backend_profile_registry_20260519.zh.md)。
- `WP6-B Parity Budget And Comparison Rules`：
  [parity budget 分发单](archive/wp6_backend_profile_policy/wp6_parity_budget_cluster_20260519.zh.md) 与
  [parity budget 注册表](archive/wp6_backend_profile_policy/wp6_parity_budget_registry_20260519.zh.md)。
- `WP6-C Resident-State And Backend Capability Alignment`：
  [resident-state 边界规则](archive/wp6_backend_profile_policy/wp6_resident_state_boundary_rules_20260519.zh.md)，以及
  [runtime facade layering 测试](../../../tests/architecture/test_runtime_facade_layering.py)、
  [runtime facade 测试](../../../tests/runtime/facade/test_runtime_facade.py) 和
  [GPU runtime binding 测试](../../../tests/test_gpu_runtime_bindings.py) 中的 capability-projection guard。
- `WP6-D Integration And Index Sync`：
  [集成交接](archive/wp6_backend_profile_policy/wp6_integration_and_index_sync_20260519.zh.md) 与
  [验收审查](../review/archive/wp-acceptance/wp6_backend_profile_policy_acceptance_review_20260519.zh.md)。

## WP7 后端能力物化

产出：

- [WP7 后端能力物化](archive/wp7_backend_capability_materialization/backend_capability_materialization_wp7_20260519.zh.md)
- [WP7-A registry materialization 任务簇](archive/wp7_backend_capability_materialization/wp7_registry_materialization_cluster_20260519.zh.md)
- [WP7-A registry materialization 笔记](archive/wp7_backend_capability_materialization/wp7_registry_materialization_notes_20260519.zh.md)
- [WP7-B runtime capability projection 任务簇](archive/wp7_backend_capability_materialization/wp7_runtime_capability_projection_cluster_20260519.zh.md)
- [WP7-B runtime capability projection 笔记](archive/wp7_backend_capability_materialization/wp7_runtime_capability_projection_notes_20260519.zh.md)
- [WP7-C promotion evidence gates 任务簇](archive/wp7_backend_capability_materialization/wp7_promotion_evidence_gates_cluster_20260519.zh.md)
- [WP7-C promotion evidence gates 笔记](archive/wp7_backend_capability_materialization/wp7_promotion_evidence_gates_notes_20260519.zh.md)
- [WP7-D multi-fidelity entry conditions 任务簇](archive/wp7_backend_capability_materialization/wp7_multifidelity_entry_conditions_cluster_20260519.zh.md)
- [WP7-D multi-fidelity entry conditions 笔记](archive/wp7_backend_capability_materialization/wp7_multifidelity_entry_conditions_notes_20260519.zh.md)
- [WP7-E integration and index sync 任务簇](archive/wp7_backend_capability_materialization/wp7_integration_and_index_sync_cluster_20260519.zh.md)
- [WP7 后端能力物化验收审查](../review/archive/wp-acceptance/wp7_backend_capability_materialization_acceptance_review_20260519.zh.md)

WP7 是 WP6 之后已验收的文档与实现准备线。它把已验收的 backend profile policy
转成 materialized registry、runtime projection、promotion evidence 与
multi-fidelity entry conditions。本次验收不晋级 exact GPU、resident-state、
device observation、shadow 或 adaptive fidelity support；当前 support 仍为
false，直到未来 promotion review 同时更新 registry、parity budget、projection
adapter 与 validation evidence。

WP7 工作流地图：

- `WP7-A Registry Materialization` 先启动，负责可机器检查 registry/schema shape。
- `WP7-D Multi-Fidelity Entry Conditions` 可以与 WP7-A 并行，但必须引用
  WP6/WP7-A profile 词汇，不能发明 support claim。
- `WP7-B Runtime Capability Projection` 等 WP7-A 稳定后启动，并保持 projection 保守。
- `WP7-C Promotion Evidence Gates` 消费 WP7-A/D，并把 candidate promotion 映射到
  WP5 validation tiers。
- `WP7-E Integration And Index Sync` 串行执行，应在 A-D 稳定后启动。

## 验收门槛

从本子项目派生的每项实现任务都应满足：

1. stage ownership 已文档化，
2. stage-node read/write set 与 clock domain 已文档化，
3. feedback 跨越 state-store 或 event-queue 边界，
4. facade 或 compatibility-adapter 访问是显式的，
5. CPU exact 行为仍为参考路径，
6. 跨领域行为使用同一生命周期，
7. 本地 smoke test 不要求 RL 依赖，
8. diagnostics 能解释 command、launch、munition、effect 和 damage event，
9. observation schema、action validity、reward composition、termination/truncation source 与 episode lifecycle authority 都被分配到显式层级。
10. 维护中的决策路径消费 `ObservationPacket` 或声明过的 `DecisionBelief`，而不是 `World Truth`。
11. backend capability 声明必须引用维护中的 backend profile 与 parity budget；
    `RuntimeCapabilities` 不能仅凭 helper/probe 存在就推断 exact GPU、resident-state
    或 shadow support。
12. WP7 capability materialization 让 exact GPU、resident-state、device observation、
    shadow 与 multi-fidelity support 保持 false，除非维护中 profile revision、
    parity budget、ownership/sync policy 与 validation gate 明确晋级该 claim。
13. WP8 learning-face 输出必须保持课程、评估、能力画像、场景生成与学习证据显式且可回放，
    不能把它们转成第二条仿真真值路径。
14. WP17 runtime-materialization 工作必须引用当前代码事实，保持 compatibility-only
    runtime access 有边界，并且不得在对应 selected-slice evidence 出现前声明
    global multi-rate、fidelity-provider、capability-spawn 或 counterfactual runtime
    closure。

## 非目标

- 在本地 Windows 机器上完成完整 RL 训练。
- 立即替换为 exact GPU world-step。
- 把 Rust 作为近期后端引入。
- 在 contract freeze 前重写所有既有 command/tasking DTO。
- 在 WP0/WP1 阶段移动所有现有文件到新目录。
