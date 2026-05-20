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
4. 空军、海军、武器和未来领域应通过阶段局部的模型族、capability bundle 与 stage-node contract 扩展该生命周期。
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
13. 当本子项目被拆分给多个 subagent 或 worker 时，应遵循
    [Subagent 使用规范](../../standards/governance/subagent_usage_policy.zh.md)：
    保持写入范围互不重叠、保留一个 integration owner，并且不要让多个并行作者
    拆写同一张规范性表格。

## 工作包

| 工作包 | 状态 | 目标 | 产出 |
|--------|------|------|------|
| `WP0 Architecture Baseline` | complete | 明确 SCAL 定位、语义生命周期、因果-时序执行投影与扩展规则 | 架构设计文档、任务子项目入口 |
| `WP1 Pipeline Inventory` | complete | 把当前代码、system、model、test 映射到 `P0-P10` 与当前耦合热点 | [管线盘点](wp1_pipeline_inventory/pipeline_inventory_wp1_20260519.zh.md) |
| `WP2 Contract Freeze` | complete | 识别需要显式 ownership 的 packet 族、stage-node contract 与跨层 policy/orchestration contract | [契约冻结](wp2_contract_freeze/contract_freeze_wp2_20260519.zh.md) |
| `WP2.5 Scheduler Semantics Freeze` | complete | 冻结 event ordering、state versioning、barrier visibility、clock-domain merge policy、replay contract 与 stage-node manifest schema | [调度语义冻结](wp25_scheduler_semantics/scheduler_semantics_wp25_20260519.zh.md)、[验收审查](../review/wp25_scheduler_semantics_acceptance_review_20260519.zh.md) |
| `WP3 Engagement Pilot` | complete | 以武器/交战作为第一条跨领域验证切片 | [交战试点任务族](wp3_engagement_pilot/engagement_pilot_wp3_20260519.zh.md) |
| `WP4 Facade Alignment` | complete | 确保试点行为可通过 facade-shaped API 访问，并避免 raw runtime access | [facade 对齐任务族](wp4_facade_alignment/facade_alignment_wp4_20260519.zh.md)、[最终验收](../review/wp4_facade_alignment_acceptance_review_20260519.zh.md) |
| `WP5 Validation Harness` | complete | 添加证明共享生命周期和图边界的 smoke、architecture、trace、boundary、information-leakage 与 replay/evidence 测试 | [验证套件任务族](wp5_validation_harness/validation_harness_wp5_20260519.zh.md)、[最终验收](../review/wp5_validation_harness_acceptance_review_20260519.zh.md) |
| `WP6 Backend Profile Policy` | complete | 冻结 backend profile taxonomy、parity budgets、resident-state 边界与 backend capability 暴露规则 | [后端配置文件策略](wp6_backend_profile_policy/backend_profile_policy_wp6_20260519.zh.md)、[profile 注册表](wp6_backend_profile_policy/wp6_backend_profile_registry_20260519.zh.md)、[parity budget 注册表](wp6_backend_profile_policy/wp6_parity_budget_registry_20260519.zh.md)、[resident-state 边界规则](wp6_backend_profile_policy/wp6_resident_state_boundary_rules_20260519.zh.md)、[验收审查](../review/wp6_backend_profile_policy_acceptance_review_20260519.zh.md) |
| `WP7 Backend Capability Materialization` | complete / accepted | 把已验收的 WP6 policy 物化为可机器检查 registry、runtime capability projection、promotion evidence gates 与 multi-fidelity entry conditions，但不晋级候选能力 | [后端能力物化](wp7_backend_capability_materialization/backend_capability_materialization_wp7_20260519.zh.md)、[registry materialization](wp7_backend_capability_materialization/wp7_registry_materialization_cluster_20260519.zh.md)、[runtime capability projection](wp7_backend_capability_materialization/wp7_runtime_capability_projection_cluster_20260519.zh.md)、[promotion evidence gates](wp7_backend_capability_materialization/wp7_promotion_evidence_gates_cluster_20260519.zh.md)、[multi-fidelity entry conditions](wp7_backend_capability_materialization/wp7_multifidelity_entry_conditions_cluster_20260519.zh.md)、[验收审查](../review/wp7_backend_capability_materialization_acceptance_review_20260519.zh.md) |
| `WP7.5 训练路径 facade 桥接` | complete / accepted | 在 `WP8` 依赖之前，把维护中的 batch 训练路径从 `RuntimeFacade.runtime()` 与 raw `WorldBatchRuntime` stepping 迁到 facade-shaped execution / observation API | [训练路径 facade 桥接](wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.zh.md)、[验收审查](../review/wp75_training_path_facade_bridge_acceptance_review_20260520.zh.md) |
| `WP8 SCAL Learning Face` | planned | 把课程、评估、能力画像、场景生成与学习证据收敛为显式架构和任务词汇，但不重新打开仿真闭合 | [学习面任务族](wp8_learning_face/learning_face_wp8_20260520.zh.md) |

### WP2.5 工作流地图

WP2.5 虽然是冻结文档，但后续工作已经拆成有边界的流：

- 先做 `WP2.5-F StageNodeManifest Schema`：
  [manifest/event 任务簇](wp25_scheduler_semantics/wp25_manifest_event_cluster_20260519.zh.md)。
- 在 manifest 词汇稳定后，并行推进 `WP2.5-A Event Ordering and ID Rules`、
  `WP2.5-B State Shard Versioning`、`WP2.5-C Barrier Visibility`：
  [state/barrier 任务簇](wp25_scheduler_semantics/wp25_state_barrier_cluster_20260519.zh.md)。
- 语义规则稳定后，再做 `WP2.5-D Clock-Domain Merge`。
- 调度语义完全冻结后，再做 `WP2.5-E Deterministic Replay Contract`：
  [clock/replay 任务簇](wp25_scheduler_semantics/wp25_clock_replay_cluster_20260519.zh.md)。
- 最后做 `WP2.5-G Integration and Index Sync`，作为串行发布步骤。

`WP2.5-D` 和 `WP2.5-E` 是思考预算最高的两个工作流。

## WP7.5 训练路径 facade 桥接

产出：

- [WP7.5 训练路径 facade 桥接](wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.zh.md)

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

- [WP8 SCAL Learning Face 任务族](wp8_learning_face/learning_face_wp8_20260520.zh.md)

WP8 为延后的 SCAL learning face 提供有边界的任务族。它不引入第二条运行时生命周期，而是把课程、评估、能力画像、场景生成与学习证据转成显式的实验与规划契约，并保持它们与权威仿真层分离。

WP8 工作流地图：

- `WP8-A Curriculum And Scenario Generation` 定义场景、seed、课程阶段与生成请求如何选择和版本化。
- `WP8-B Evaluation And Capability Profiling` 定义基准协议、画像 schema、分数归因与能力证据。
- `WP8-C World-Model Interface And Learning Evidence` 定义学习面如何消费 facade-shaped observation，并在不成为 truth source 的前提下记录证据。
- `WP8-D Integration And Index Sync` 负责串行更新任务/审查索引、交叉引用与双语对齐。

`WP8-B` 和 `WP8-C` 是思考预算最高的工作流，因为它们必须让学习输出保持可比较，同时避免滑向隐藏的 truth ownership。

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

- [WP1 管线盘点](wp1_pipeline_inventory/pipeline_inventory_wp1_20260519.zh.md)

产出：

- [WP2 契约冻结](wp2_contract_freeze/contract_freeze_wp2_20260519.zh.md)

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

- [WP3 交战试点任务族](wp3_engagement_pilot/engagement_pilot_wp3_20260519.zh.md)

第一条实现试点应选择交战生命周期，因为它横跨最多架构边界，并且天然涉及多个 clock domain：

`tasking -> command delivery -> sensor/track -> fire control -> launcher -> munition -> seeker/guidance/fuze -> effects -> damage -> observation`

该试点必须涉及至少两个平台族，例如：

- 航空挂架发射，
- 舰载挂载发射。

试点应避免创建独立的 `air weapon` 和 `naval weapon` 运行时路径。差异应出现在 launcher、munition、seeker、guidance、fuze、effects、doctrine 族和 clock-domain policy 中。

第一波实现应拆分为 contract DTO scaffold、facade packet shell、Python binding exposure、air launch adapter、naval launch adapter、munition/damage export、diagnostics trace 和 stage-aligned non-RL smoke harness。Air 与 naval worker 只有在不编辑同一个共享 kernel 文件时才适合并行。

## WP4 Facade 对齐

产出：

- [WP4 facade 对齐任务族](wp4_facade_alignment/facade_alignment_wp4_20260519.zh.md)

WP4 把已验收的交战试点转成维护中的前端形态。它应引用 WP2.5 的调度语义，并引用 Temp-02 的 information/agency 边界：

- `ObservationPacket` 是智能体被允许看见的内容。
- `DecisionBelief` 是智能体在 inference、memory、doctrine 或 learned state 作用后认为真实的内容。
- `AgentRole` 是 role + authority + information-state source + decision-model reference + action interface。

WP4 不应创建新的仿真语义。它应让现有行为通过 facade-shaped API 或已记录 compatibility adapter 到达。

WP4 分发任务簇：

- 先做 `WP4-A Surface Inventory`：
  [surface inventory 任务簇](wp4_facade_alignment/wp4_surface_inventory_cluster_20260519.zh.md)。
- 初始 surface 词汇稳定后，再做 `WP4-B/C Engagement, Step, And Lifecycle Alignment`：
  [engagement/step 任务簇](wp4_facade_alignment/wp4_engagement_step_cluster_20260519.zh.md)。
- action、coordination、observation、belief 与 agent-role 名称稳定后，再做 `WP4-D/E Policy, AgentRole, And Python Mirror`：
  [policy/binding 任务簇](wp4_facade_alignment/wp4_policy_binding_cluster_20260519.zh.md)。
- `WP4-F Integration And Docs` 保持串行，由主线程或专门 integration worker 在任务簇返回后处理。

`WP4-A`、`WP4-C` 与 `WP4-D` 是思考预算最高的工作流，因为它们触及跨层语义、belief 边界或 adapter ownership。

WP4 第一波产物已作为 discovery 输入验收：

- [WP4 第一波验收审查](../review/wp4_first_wave_acceptance_review_20260519.zh.md)
- [WP4-A surface inventory 初稿](wp4_facade_alignment/wp4_surface_inventory_wp4a_20260519.zh.md)
- [WP4-B/C engagement-step 对齐笔记](wp4_facade_alignment/wp4_engagement_step_alignment_notes_20260519.zh.md)
- [WP4-D/E policy-binding 对齐笔记](wp4_facade_alignment/wp4_policy_binding_alignment_notes_20260519.zh.md)

WP4 第二波任务簇：

- `WP4-G Facade Evidence Gates`：
  [facade evidence 任务簇](wp4_facade_alignment/wp4_facade_evidence_cluster_20260519.zh.md)。
- `WP4-H Information And Agent Shim`：
  [agent shim 任务簇](wp4_facade_alignment/wp4_agent_shim_cluster_20260519.zh.md)。
- `WP4-I Compatibility Guard And Integration`：
  [compat guard 任务簇](wp4_facade_alignment/wp4_compat_guard_cluster_20260519.zh.md)。

WP4 第二波与集成产物：

- [WP4 第二波验收审查](../review/wp4_second_wave_acceptance_review_20260519.zh.md)
- [WP4-I compatibility guard 笔记](wp4_facade_alignment/wp4_compat_guard_notes_20260519.zh.md)
- [WP4-F 集成交接](wp4_facade_alignment/wp4_integration_handoff_20260519.zh.md)
- [WP4 最终验收审查](../review/wp4_facade_alignment_acceptance_review_20260519.zh.md)

## WP5 验证套件

产出：

- [WP5 验证套件任务族](wp5_validation_harness/validation_harness_wp5_20260519.zh.md)

WP5 把架构与 facade 工作转化为维护中的证据。验证套件应覆盖五个验证层级：

- design conformance，
- trace conformance，
- boundary conformance，
- information/belief leakage，
- replay/evidence conformance。

WP5 从已验收的 WP4 facade label 启动。它不应从 raw runtime inspection 出发；重点是证明 facade-shaped artifact、diagnostics 与 replay metadata 足以验证共享架构。

WP5 第一波任务簇：

- `WP5-A Harness Inventory`：
  [harness inventory 任务簇](wp5_validation_harness/wp5_harness_inventory_cluster_20260519.zh.md)。
- `WP5-B Design And Boundary Gates`：
  [design/boundary 任务簇](wp5_validation_harness/wp5_design_boundary_cluster_20260519.zh.md)。
- `WP5-C Trace And Replay Gates`：
  [trace/replay 任务簇](wp5_validation_harness/wp5_trace_replay_cluster_20260519.zh.md)。

`WP5-C` 是第一波中推理预算最高的流，因为 trace ancestry 与 replay metadata
测试如果假设了 WP4 明确推迟的 runtime metadata，就会变得脆弱。

WP5 第一波产物已验收：

- [WP5 第一波验收审查](../review/wp5_first_wave_acceptance_review_20260519.zh.md)
- [WP5-A harness inventory 笔记](wp5_validation_harness/wp5_harness_inventory_notes_20260519.zh.md)
- [WP5-B design/boundary 笔记](wp5_validation_harness/wp5_design_boundary_notes_20260519.zh.md)
- [WP5-C trace/replay gates 笔记](wp5_validation_harness/wp5_trace_replay_gates_notes_20260519.zh.md)

WP5 第二波任务簇：

- `WP5-D Information And Belief Gates`：
  [information/belief 任务簇](wp5_validation_harness/wp5_information_belief_cluster_20260519.zh.md)。
- `WP5-E Smoke Promotion And Docs`：
  [smoke promotion 任务簇](wp5_validation_harness/wp5_smoke_promotion_cluster_20260519.zh.md)。

WP5 第二波与最终产物已验收：

- [WP5-D information/belief 验收审查](../review/wp5_information_belief_acceptance_review_20260519.zh.md)
- [WP5-D information/belief 笔记](wp5_validation_harness/wp5_information_belief_notes_20260519.zh.md)
- [WP5-E smoke promotion 笔记](wp5_validation_harness/wp5_smoke_promotion_notes_20260519.zh.md)
- [WP5 validation harness 验收审查](../review/wp5_validation_harness_acceptance_review_20260519.zh.md)

## WP6 后端配置文件策略

产出：

- [WP6 后端配置文件策略](wp6_backend_profile_policy/backend_profile_policy_wp6_20260519.zh.md)
- [WP6-A 后端配置文件分类分发单](wp6_backend_profile_policy/wp6_backend_profile_taxonomy_cluster_20260519.zh.md)
- [WP6-A 后端配置文件注册表](wp6_backend_profile_policy/wp6_backend_profile_registry_20260519.zh.md)
- [WP6-B parity budget 分发单](wp6_backend_profile_policy/wp6_parity_budget_cluster_20260519.zh.md)
- [WP6-B parity budget 注册表](wp6_backend_profile_policy/wp6_parity_budget_registry_20260519.zh.md)
- [WP6-C + WP6-D 集成交接](wp6_backend_profile_policy/wp6_integration_and_index_sync_20260519.zh.md)
- [WP6-C1 resident-state 边界规则](wp6_backend_profile_policy/wp6_resident_state_boundary_rules_20260519.zh.md)
- [WP6 后端配置文件策略验收审查](../review/wp6_backend_profile_policy_acceptance_review_20260519.zh.md)

WP6 用契约把 backend profile 与 parity budget 的空档收口。它冻结 profile
词汇、budget 记录、resident-state 边界与 capability projection 规则，让
accelerated、resident-state、approximate 与 diagnostics-only 路径在进入维护态前有明确约束。

WP6 工作流地图：

- `WP6-A Backend Profile Taxonomy`：
  [taxonomy 分发单](wp6_backend_profile_policy/wp6_backend_profile_taxonomy_cluster_20260519.zh.md) 与
  [profile 注册表](wp6_backend_profile_policy/wp6_backend_profile_registry_20260519.zh.md)。
- `WP6-B Parity Budget And Comparison Rules`：
  [parity budget 分发单](wp6_backend_profile_policy/wp6_parity_budget_cluster_20260519.zh.md) 与
  [parity budget 注册表](wp6_backend_profile_policy/wp6_parity_budget_registry_20260519.zh.md)。
- `WP6-C Resident-State And Backend Capability Alignment`：
  [resident-state 边界规则](wp6_backend_profile_policy/wp6_resident_state_boundary_rules_20260519.zh.md)，以及
  [runtime facade layering 测试](../../../tests/architecture/test_runtime_facade_layering.py)、
  [runtime facade 测试](../../../tests/runtime/facade/test_runtime_facade.py) 和
  [GPU runtime binding 测试](../../../tests/test_gpu_runtime_bindings.py) 中的 capability-projection guard。
- `WP6-D Integration And Index Sync`：
  [集成交接](wp6_backend_profile_policy/wp6_integration_and_index_sync_20260519.zh.md) 与
  [验收审查](../review/wp6_backend_profile_policy_acceptance_review_20260519.zh.md)。

## WP7 后端能力物化

产出：

- [WP7 后端能力物化](wp7_backend_capability_materialization/backend_capability_materialization_wp7_20260519.zh.md)
- [WP7-A registry materialization 任务簇](wp7_backend_capability_materialization/wp7_registry_materialization_cluster_20260519.zh.md)
- [WP7-A registry materialization 笔记](wp7_backend_capability_materialization/wp7_registry_materialization_notes_20260519.zh.md)
- [WP7-B runtime capability projection 任务簇](wp7_backend_capability_materialization/wp7_runtime_capability_projection_cluster_20260519.zh.md)
- [WP7-B runtime capability projection 笔记](wp7_backend_capability_materialization/wp7_runtime_capability_projection_notes_20260519.zh.md)
- [WP7-C promotion evidence gates 任务簇](wp7_backend_capability_materialization/wp7_promotion_evidence_gates_cluster_20260519.zh.md)
- [WP7-C promotion evidence gates 笔记](wp7_backend_capability_materialization/wp7_promotion_evidence_gates_notes_20260519.zh.md)
- [WP7-D multi-fidelity entry conditions 任务簇](wp7_backend_capability_materialization/wp7_multifidelity_entry_conditions_cluster_20260519.zh.md)
- [WP7-D multi-fidelity entry conditions 笔记](wp7_backend_capability_materialization/wp7_multifidelity_entry_conditions_notes_20260519.zh.md)
- [WP7-E integration and index sync 任务簇](wp7_backend_capability_materialization/wp7_integration_and_index_sync_cluster_20260519.zh.md)
- [WP7 后端能力物化验收审查](../review/wp7_backend_capability_materialization_acceptance_review_20260519.zh.md)

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

## 非目标

- 在本地 Windows 机器上完成完整 RL 训练。
- 立即替换为 exact GPU world-step。
- 把 Rust 作为近期后端引入。
- 在 contract freeze 前重写所有既有 command/tasking DTO。
- 在 WP0/WP1 阶段移动所有现有文件到新目录。
