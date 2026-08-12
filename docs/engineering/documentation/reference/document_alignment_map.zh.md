# 文档对齐映射

Language:
- English canonical: `docs/engineering/documentation/reference/document_alignment_map.md`
- Chinese companion: [document_alignment_map.zh.md](document_alignment_map.zh.md)

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/engineering/documentation/reference/document_alignment_map.md`
Owner: `engineering/documentation-governance`
Last verified: `2026-08-08`

状态：`2026-08-08`，文档归属与分层的迁移期权威映射。

本文档用于明确：

- 哪些标准文档是当前主依据
- 哪些文档属于特化补充
- 活跃任务/工作流文档应如何映射回分布式 owner standards

本文档是路由图，不是技术 standard。

## 当前主依据

### 联合 / 通用核心

当前联合层主依据：

- [联合标准总览](../../../domains/joint/README.zh.md)
- [联合指挥与建模基线](../../../domains/joint/standards/command_and_modeling_baseline.zh.md)
- [联合命令链与汇报基线](../../../domains/joint/standards/command_link_and_reporting_baseline.zh.md)
- [仿真约定](../../../architecture/standards/simulation_conventions.zh.md)
- [梯度真实性原则](../../../systems/standards/gradient_realism_principles.zh.md)
- [运行时工作流与合同基线](../../../architecture/standards/runtime_workflow_and_contract_baseline.zh.md)

它们负责定义：

- 指挥关系与授权边界
- 共享任务下达、命令和汇报工作流边界
- `ScenarioLoader` 编排层与 C++ mission/runtime 纯计算层的阶段归属
- 引擎中立的坐标、角度、时间和观测约定
- 让场景声明与已实现领域机制保持一致，并约束“高真实度 / candidate /
  non-authoritative / authority release”等口径的梯度真实性门槛

### 军种画像

当前军种画像主依据：

- [军种画像总览](../../../domains/joint/service_profiles/README.zh.md)
- [美国空军画像](../../../domains/joint/service_profiles/standards/air_force_profile.zh.md)
- [美国陆军画像](../../../domains/joint/service_profiles/standards/army_profile.zh.md)
- [美国海军画像](../../../domains/joint/service_profiles/standards/navy_profile.zh.md)
- [美国海军陆战队画像](../../../domains/joint/service_profiles/standards/marine_corps_profile.zh.md)

它们负责定义：

- 哪些层级是有效的 tight-loop runtime 单位
- 哪些概念在进入平台特化前仍应保留为军种特有概念
- common core 在各军种中的解释口径

### Runtime 与编写路由

当前维护中的跨 owner 路由是：

- [场景配置指南](../../../operations/howto/scenario_configuration_guide.zh.md)
- [运行时工作流与合同基线](../../../architecture/standards/runtime_workflow_and_contract_baseline.zh.md)

它们不重新定义 doctrine，而是说明当前仓库中的输入、工作流阶段和 DTO
如何对齐到分布式 owner standards。

### 模型架构

当前维护中的模型架构依据：

- [模型架构标准总览](../../../learning/README.zh.md)
- [策略执行架构基线](../../../learning/standards/policy_execution_architecture.zh.md)

它们负责定义：

- executable policy branches、auxiliary heads、runtime action adapters、losses、
  rewards、rollout labels 与 probes 之间的模型/策略组件 ownership
- runtime support constraint 与 learned stopping/timing mechanism 的区别
- owner-local learning 工作与 reviews 如何回映到稳定架构词汇，而不是把工作状态当成标准

## 当前有效的特化补充

### 空中特化

以下文档仍有效，但不属于全项目 common core：

- [空中平台标准总览](../../../domains/air/README.zh.md)
- [飞行员观测空间标准](../../../domains/air/standards/pilot_observation_contract.zh.md)
- [飞行员操作空间标准](../../../domains/air/standards/pilot_action_contract.zh.md)
- [空中任务命令标准](../../../domains/air/standards/mission_command_and_tasking_contract.zh.md)
- [飞行员汇报标准](../../../domains/air/standards/pilot_reporting_contract.zh.md)
- [空空杀伤链期望包络](../../../domains/air/work/issues/kill_chain_expectation_envelope.md)
  - active planning supplement，不是当前 runtime contract

它们负责：

- runway、approach、ILS、takeoff、recovery、sortie phase 等 air semantics
- air mission observation 与 execution-command 的特化
- `wingman`、`element`、`flight` 等空中编组语义
- 校准工作前用于 review 诊断分布的空空杀伤链期望包络 labels

### 海军特化

当前维护中的海军特化入口：

- [海军标准总览](../../../domains/naval/README.zh.md)
- [海军最小任务结构](../../../domains/naval/standards/minimal_task_structure.zh.md)
- [舰艇单位参考](../../../domains/naval/reference/ship_unit_references.zh.md)
- [海军观测合同](../../../domains/naval/standards/observation_contract.zh.md)

它们负责：

- maritime task / station / screen / support / recovery 语义
- ship 与 task-group 层的 naval role 解释
- 第一批海军建模数据/来源边界，其中
  [舰艇单位参考](../../../domains/naval/reference/ship_unit_references.zh.md) 当前承担 reference 基准角色
- `naval_screen_station_v1` mission-observation 的归属与字段顺序

它们不负责跨军种授权关系或 generic tasking DTO 边界。

### Ground 特化

当前维护中的 ground 特化入口：

- [Ground 标准总览](../../../domains/ground/README.zh.md)
- [Ground 特化基线](../../../domains/ground/standards/specialization_baseline.zh.md)
- [Ground 最小任务结构](../../../domains/ground/standards/minimal_task_structure.zh.md)

它们负责：

- 以 platoon 为中心的起步 tasking 默认值
- `TASK_MOVE`、`TASK_OCCUPY` 与 `TASK_SUPPORT` 的 ground 语义
- ground agency role 默认值
- terrain-masked sensing 与 radio-range-constrained shared-picture 假设
- 第一波 ground platform 的 capability-composition 预期

它们不负责跨军种 authority 定义、Army service-profile 解释，也不负责完整的
terrain/mobility/fires/runtime 行为。

路由规则：`docs/domains/joint/service_profiles/standards/army_profile.md` 负责
Army profile 解释，`docs/domains/ground/` 负责维护中的 ground 特化。已接受的
`army` 与 `land` 别名会规范化为 `ground`，不得被写成单独的
`army runtime stack`。

## 开放架构问题

以下 draft 记录尚未解决的 architecture residual；它不是当前 runtime contract，也不
授权实施：

- [模块化规划](../../../architecture/work/issues/modularization_plan.md)

它记录当前 domain roots、已落地 extension interfaces 和剩余依赖边界问题。它不能
被当作每个拟议模块边界或 domain runtime owner 已实现、已验收的证据。

## 已归档文档

以下文档仅保留作历史参考：

- `docs/Archive/air_first_standards/com/*.md`
- `docs/Archive/air_first_standards/com/two_ship/*.md`
- `docs/Archive/architecture/*.md`
- `docs/Archive/architecture/layers/*.md`

这些文档之所以归档，是因为它们描述了已被替代的执行路径、早期 air-first 泛化路线，
或只作为任务历史快照存在，不再充当当前标准。

## common concepts 的归属规则

以下概念应尽量上提到 common core：

- `command_relationship`
- `authority_scope`
- `service_profile`
- `task_family`
- `tactical_unit_type`
- `coordination_mode`
- `role_code`
- `task_group_id`
- `supported_node_id`
- `supporting_node_id`
- `recovery_site_id`

归属规则：

- `docs/domains/joint/` 负责命名、最小语义和禁止混淆项
- `docs/domains/joint/service_profiles/` 负责各军种解释
- bridge 文档负责说明当前 runtime 如何表达这些对象
- 特化文档不得把它们重新写成 air-only 或 naval-only 的 core

## air-specific concepts 的归属规则

以下概念在出现更好的跨军种抽象前，应继续留在 air specialization：

- `CAP`
- `route CAP`
- `runway`
- `approach_type`
- `takeoff_procedure`
- `takeoff_clearance`
- `LeaderPhase`
- `wingman`
- `element`
- `flight`

这些概念可以继续存在于代码、测试和场景中，但不能被描述成全项目 common-core 默认语汇。

## naval-specific concepts 的归属规则

以下概念属于 Navy profile 或 naval specialization，而不是 common core：

- `warfare_role_code`
- `officer_in_tactical_command`
- `task force / task group / task unit` 的海军组织语义
- `screen`
- `support`
- `station`
- `replenishment`
- ship/section recovery semantics

`joint/common core` 可以保留 `task_group_id` 或 `coordination_mode`
这类挂点，但它们在海上场景中的语义由 Navy profile 和 naval specialization 解释。

## ground-specific concepts 的归属规则

以下概念属于 Army profile 或 ground specialization，而不是 common core：

- `platoon` 作为第一 tight-loop ground tasking 边界
- `move`、`occupy` 与 land `support` 任务语义
- `ground_squad_leader`
- `ground_platoon_commander`
- `ground_company_commander`
- terrain-masked sensing
- radio-range-constrained shared tactical picture
- ground mobility、direct-fire、indirect-fire、sustainment 与 land reporting extension

`joint/common core` 可以保留 `tactical_unit_type`、`parent_node_id`、
`supported_node_id`、`supporting_node_id` 与 `coordination_mode` 这类挂点，
但这些挂点在陆上场景中的语义由 Army profile 和 ground specialization 解释。

## 将历史 flight_dynamics 工作流映射回标准树

原 flight-dynamics task 树现在只保留归档。其冻结分析是 provenance，不是维护中的
真实性入口。当前缺口分别路由到 physics、sensing、command/tasking、weapons、Naval
与 Air owner。

建议按下面方式回映：

- `c2_command_chain/`
  - 主要对齐到 `docs/domains/joint/`
  - 涉及 ship authority/report 时，次级对齐到 Navy service profile 与
    `docs/domains/naval/`
- `naval/`
  - 对齐到 Navy service profile 与 `docs/domains/naval/`
- `ground/` 或未来 land-domain task work
  - 对齐到 Army service profile 的军种画像解释，以及 `docs/domains/ground/`
    的特化语义
  - 不得新增一条单独的 `army runtime stack`
- `sensor_situation/`
  - 当前主要对齐到 architecture workflow standard，以及后续共享的 `track / IFF / report` 标准
- `weapon_guidance/`
  - 当前主要对齐到 architecture workflow standard，以及未来的 weapon specialization
- `flight/`
  - 对齐到 air specialization 与 runtime workflow 约束

已归档任务目录可以提供有效历史分析，但不负责决定稳定共享合同最终落在哪里。

## 维护规则

新增一份维护中的标准文档时：

1. 跨军种共通关系放 `docs/domains/joint/standards/`
2. 军种组织与控制解释放
   `docs/domains/joint/service_profiles/standards/`
3. Air、Ground 或 Naval 特化放到对应 owner-local `standards/` 表面
4. 新的跨域 runtime/workflow 合同放到 `docs/architecture/standards/`，
   不得重建共享 `bridge/` 根
5. 模型/策略架构词汇放到 `docs/learning/standards/`
6. 过时工作依照文档生命周期政策退役；标准迁移不得改写既有 archive
