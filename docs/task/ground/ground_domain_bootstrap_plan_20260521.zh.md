# Ground 域启动计划

状态：`2026-05-24` G0-G4 封存基线；G5 tasking smoke 已验收；G6
开启第一批 realism-gradient MVP 场景。

输入：

- [仿真系统架构设计](../../plan/architecture/simulation_system_architecture_design.md)
- [美国陆军画像](../../standards/services/army.zh.md)
- [通用空海军](../common_air_naval/README.zh.md)
- [Stage 3 平台扩展主线计划](../review/stage3_platform_expansion_mainline_plan_20260521.md)
- [Ground 域启动计划 review](../review/ground_domain_bootstrap_plan_review_20260521.md)

## 1. 目标

本计划为仓库第三域建立专门的任务入口：ground/land 执行特化。

眼下目标不是马上展开大规模实现，而是先冻结：

1. 命名，
2. 分层边界，
3. 最小语义范围，
4. 首阶段验收标准，
5. 新增一个域时必须一并补上的横向面，
6. `G1 合同骨架` 开始前必须明确的 G0 架构承诺。

## 2. 架构定位

维护中的边界建议如下：

- `services/army` 继续作为军种画像层。
- `ground/` 作为执行特化层的规划入口。
- 后续代码/runtime 工作应通过 capability composition、common-core
  contract 与 stage-local model family 接入共享生命周期。
- 不应新增一条独立的 `army runtime stack`。

理由：

- `Army` 是 service profile，不适合作为执行语义的长期命名。
- `ground` 能承接以 Army 为主的陆上建模，同时不把未来所有陆上工作都绑死在军种标签上。
- 这与现有 `services/navy` 和 `naval/` 的分层一致，也符合 standards 中“未来 land execution 应落在 dedicated ground specialization”这一原则。

## 3. 当前仓库位置

截至 `2026-05-21`，仓库已经具备：

- 权威的 Army service-profile 文档
- tasking/command DTO 层的 `common + air + naval` 拆分
- `air` 与 `naval` 的 Python tasking-profile 分发
- “新域通过 capability 实现接入，而非新增 runtime path”的架构法则

当前仓库尚未具备：

- 维护中的 `ground/` standards 特化层
- Python 分发中的 ground tasking profile
- ground 专用 DTO 落点
- ground 场景、内容样例与 runtime-contract 测试
- 第一版可达成共识的机动 / 火力 / 观测语义面

## 4. 建议阶段

| 阶段 | 范围 | 目标产物 | 非目标 |
|------|------|----------|--------|
| `G0 边界冻结` | 命名、层次模型、起步范围 | 当前任务线、子项目 README、规划基线、必要架构声明、待确认清单 | 不做代码/runtime 行为 |
| `G1 合同骨架` | 最小 profile 分发与 DTO 落点 | `ground` profile 识别、starter common-core defaults、空或极小的 ground DTO 壳、架构测试 | 不做机动模型，不做火力 runtime |
| `G2 内容与测试种子` | 第一批样例与兼容性证明 | 一到两个 content fixture、scenario/task spec、roundtrip/mapping test、contract-shape test | 不铺开场景目录 |
| `G3 执行面设计` | 有界执行语义 | 第一版 ground command/task/observation 设计说明、stage coverage、capability map | 不做完整物理或战斗实现 |
| `G4 runtime 切片` | 第一条维护中的行为切片 | 一个通过共享生命周期跑通的 ground 端到端切片 | 不新增 ground-only 并行管线 |
| `G5 MVP 场景` | 第一版规范 ground 场景壳 | 一个维护中的 `scenarios/ground/` smoke fixture，用于证明 loader 与 tasking status chain | 不声明真实 ground platform schema、movement、terrain、sensing、fires 或 combat |
| `G6 Realism Gradient MVP Scenarios` | 第一批受梯度约束的场景 | G1 static occupy 与 support relationship fixture，并为后续 G2+ work 设置 gate | 不声明 movement、terrain、sensing、fires、damage 或 native ground platform |

关键规则是：`G1-G4` 必须复用现有的
`common + specialization + profile bridge` 模式，而不是再发明一套新的
tasking/mission/runtime 链路。

G5 将这条规则延伸到 scenario content：第一版 ground MVP 场景必须复用共享
`ScenarioLoader` 与已验收的 G4 tasking lifecycle，不得创建私有 ground scenario
loader 或 runtime path。

G6 继续把该规则扩展为梯度边界：每个新 ground 场景都必须声明进入的
realism grade，证明该 grade 的最低临界点，并显式延后更高复杂度声明。

### 4.1 阶段子项目与任务簇

每个阶段都作为独立 task 子项目维护，便于单独分发、review 和关闭，而不把整个 ground bootstrap 任务线一次性放大。

| 阶段 | 子项目 | 分发任务簇 | 释放状态 |
|------|--------|------------|----------|
| `G0 边界冻结` | [g0_boundary_freeze/](g0_boundary_freeze/README.md) | [G0 standards alignment cluster](g0_boundary_freeze/g0_standards_alignment_cluster_20260521.md) | accepted |
| `G1 合同骨架` | [g1_contract_skeleton/](g1_contract_skeleton/README.md) | [G1 profile and DTO contract cluster](g1_contract_skeleton/g1_profile_dto_contract_cluster_20260521.md) | accepted for Python-profile-only slice |
| `G2 内容与测试种子` | [g2_content_test_seed/](g2_content_test_seed/README.md) | [G2 content fixture and test cluster](g2_content_test_seed/g2_content_fixture_test_cluster_20260521.md) | accepted |
| `G3 执行面设计` | [g3_execution_surface_design/](g3_execution_surface_design/README.md) | [G3 execution surface preflight cluster](g3_execution_surface_preflight_cluster_20260521.md) | accepted |
| `G4 runtime 切片` | [g4_runtime_slice/](g4_runtime_slice/README.md) | [G4 selected runtime slice cluster](g4_runtime_slice/g4_selected_runtime_slice_cluster_20260521.md) | 已验收并封存为有边界的 tasking-only lifecycle proof |
| `G5 MVP 场景` | [g5_mvp_scenario/](g5_mvp_scenario/README.md) | [G5 MVP scenario cluster](g5_mvp_scenario/g5_mvp_scenario_cluster_20260522.md) | 已验收 tasking smoke scenario |
| `G6 Realism Gradient MVP Scenarios` | [g6_realism_gradient_mvp_scenarios/](g6_realism_gradient_mvp_scenarios/README.md) | [G6 realism-gradient MVP scenario cluster](g6_realism_gradient_mvp_scenarios/g6_realism_gradient_mvp_scenario_cluster_20260524.md) | 已验收 G1 static occupy 与 G1 support relationship compatibility-shell fixtures |

当前分发队列是
[ground_subagent_dispatch_queue_20260521.md](ground_subagent_dispatch_queue_20260521.md)。
该队列遵循仓库的
[Subagent 使用规范](../../standards/governance/subagent_usage_policy.zh.md)：
限定写入范围、禁止多个 worker 同时拆同一张规范表、由 main thread 负责最终集成，并要求 worker 在释放后续依赖阶段前返回标准 return packet。

## 5. 第一波最小语义范围

第一波应保持很窄，只冻结能叠加在现有 common core 之上的最小 ground
语义集合。

起步语义目标：

- 维护中的执行特化名默认使用 `ground`
- `tasking_profile` 应接受 `army`、`ground`、`land`，并统一归一到
  `ground`
- 第一批 tight-loop 战术单元默认使用 `platoon`
- squad/section 与 company/troop/battery 仍可作为 scenario/tasking 语境，但第一批可执行粒度围绕 platoon
- 第一任务族默认使用 `move / occupy / support`
- 通过 `authority_scope`、`command_relationship`、`supported_node_id`、
  `supporting_node_id` 等共享字段表达 command/support 关系
- 一组无需新增物理假设即可映射的第一批 ground task
- 为后续 maneuver、fires、sustainment 与 mobility-control 扩展留出口

起步非目标：

- brigade/division/corps 进入 tight-loop runtime
- 完整 direct-fire / indirect-fire 执行语义
- terrain、cover、concealment、breaching、logistics、route-clearance 真实度
- 在 tasking/core 边界未稳前就大幅扩张 `MissionCommand`

## 6. G0 架构承诺

G0 现在冻结进入 G1 前必须明确的最小架构声明。这些是规划和合同形状承诺，不表示 runtime 行为已经存在。

### 6.1 Stage 覆盖

第一批 ground 切片在共享生命周期中的参与方式如下：

| Stage | G0 声明 |
|-------|---------|
| `P0 ContentCompile` | ground 平台定义应作为 capability bundle 下沉，而不是新增 hardcoded type-name 路径。 |
| `P2 TaskingIntent` | G1 负责 ground task order、leader intent、梯队元数据、command relationship 与 support relationship。 |
| `P3 CommandDelivery` | 延后到 G3，除非 G1 明确接纳一个最小 ground command surface。 |
| `P6 SenseTrackLink` | 延后；ground sensing 成为 maintained 前必须考虑 terrain masking、line-of-sight、radio range 与 relay topology。 |
| `P10 ObservationExport` | formal `ObservationPacket` export 延后；status/report 合同测试可以先于 runtime observation export。 |

read/write set、facade visibility、详细 capability interface 与 parity test
保留到 G3+，因为它们依赖最终选定的执行面。

### 6.2 Packet 词汇

G1 合同骨架应优先使用既有 packet family。

Consumed：

- `TaskingPacket` / common tasking-core 等价对象
- `AgentRole`，用于 ground squad/platoon/company 角色

Produced：

- 带 ground task-family 语义的 `TaskOrder`
- 带 ground command hierarchy 与 support relationship 的 `LeaderIntent`
- `PilotReport` 作为兼容 status/report 壳，直到引入更合适的 ground-neutral report 名称

Deferred：

- `CommandPacket`
- `ObservationPacket`
- `TrackPacket`

### 6.3 Capability Composition 路径

ground 平台必须定义为 capability bundle。G1 不应新增一条 canonical 的
hardcoded `spawn_unit(type_name)` dispatch 分支。

第一波 capability family 声明：

| Family | 第一波声明 |
|--------|------------|
| `PlatformFamily` | `dismounted_unit`、`ground_vehicle_section` |
| `MotionFamily` | `ground_mobility`，后续包含 wheeled、tracked、dismounted 变体 |
| `SensorFamily` | `ground_visual`、`ground_acoustic`；延后到 G3+ |
| `LauncherFamily` | `direct_fire_platform`、`indirect_fire_battery`；延后到 G3+ |
| `DoctrineFamily` | `land_tactics`，覆盖 move、occupy、support，后续扩展 screen/secure |
| `EffectsFamily` | 延后到 G3+ |

兼容行为：现有 `spawn_unit(type_name)` 风格创建可以继续作为 wrapper，但
ground 的规划目标是 capability-bundle lowering。

### 6.4 Clock Domain 假设

ground tasking 不应默认继承 air/naval 的高频运动假设。

G0 时钟假设：

- 基础战术评估节奏：`1 Hz`
- motion update：低频或 event-driven，延后到 G3+
- sensing update：受 terrain masking 与 line-of-sight 约束，延后到 G3+
- scheduler integration：所有 ground cadence 都必须汇入共享 causal-temporal scheduler 和 evidence model，而不是形成私有 ground loop

### 6.5 Agency Graph 影响

第一批 ground 角色应声明架构基线要求的五元素 schema：`role`、
`authority_scope`、`information_state_source`、`decision_model_ref`、
`action_interface`。

| Role | Authority scope | Information state source | Decision model ref | Action interface |
|------|-----------------|--------------------------|--------------------|------------------|
| `ground_squad_leader` | squad | sensed + agent observation | scripted land-task execution，后续可接 learned policy | task-order execution |
| `ground_platoon_commander` | platoon | shared tactical picture + agent observation | scripted platoon tasking，后续可接 doctrine profile | leader intent 与 task-order delegation |
| `ground_company_commander` | company | shared tactical picture | company coordination doctrine；延后到 G3+ | coordination intent；延后到 G3+ |

### 6.6 Information-State 边界

ground information state 遵循六层架构模型。

| Layer | G0 ground 承诺 |
|-------|----------------|
| `World Truth` | 权威 terrain、entity 与 tasking truth 仍留在 runtime 内部。 |
| `Sensed State` | ground sensing 默认受 terrain masking 与 line-of-sight 约束，不按自由空间 radar propagation 假设处理。 |
| `Track State` | ground contact 可使用 visual/acoustic correlation；maintained track fusion 延后。 |
| `Shared Tactical Picture` | ground sharing 受 radio range、relay topology、latency 与 permission 约束。 |
| `Agent Observation` | policy 或 scripted agent 消费 view-spec-shaped observation，而不是 world truth。 |
| `Decision Belief` | ground decision model 必须声明 belief 来自哪些 observation 或 shared-picture 输入。 |

这些规则在 G3+ 实现前仍是 placeholder，但该边界属于 G0 架构冻结内容。

## 7. 建议的首阶段改动包络

第一波实现应刻意保守。

建议范围：

- `docs/standards/` 中面向未来 `ground/` 特化的后续规划
- `docs/task/ground/` 中的规划与收敛记录
- Python `tasking_profile` 对 `Army` / `ground` 的识别
- starter `python/rl/profile/ground_profile.py` 与 adapter 壳
- 仅在最小字段集先达成共识后，再考虑在
  `components/tasking/ground` 与 `components/command/ground` 下增加 C++ DTO 落点
- 聚焦于 resolution、defaults 与 compatibility behavior 的测试

不要从这些开始：

- `systems/ground/` runtime 行为
- `models/ground/` mobility 行为
- 大幅扩张 facade surface
- 大量 scenario-loader 分支
- 在第一版语义合同冻结前先做 ground 的 weapon/damage 特化

## 8. 已冻结默认值与剩余开放议题

架构 review 已将前三个 G0 问题冻结为默认值：

- 维护中的执行特化名：`ground`
- profile resolution 接受别名：`army`、`ground`、`land`
- 第一批 tight-loop 战术运行单元：`platoon`
- 第一任务族：`move / occupy / support`

其余议题应在 `G1 合同骨架` 前或 G1 过程中继续讨论。

### 8.1 第一平台族

- 第一平台是 dismounted unit、ground vehicle section、artillery battery abstraction，还是 logistics/sustainment element？
- 第一切片应优先某一平台族，还是先以 unit-level abstract token 切入？

### 8.2 命令面

- 哪些语义应先放在 `TaskOrder` / `LeaderIntent`，哪些必须延后，不应先塞进 `MissionCommand`？
- 第一波是否需要 ground execution command，还是 tasking-only 的 starter slice 就足够？

### 8.3 观测与回报

- 第一版 ground observation/reporting 在不暴露 world truth 的前提下应长什么样？
- 在能被称为可信之前，哪些 land-specific report type 必须存在？

## 9. 新增一个域必须一并补的横向面

新增域不只是 DTO 或 scenario 的问题。即使是最小启动，也应同时考虑这些横向面：

### 9.1 standards 与 doctrine 落点

- service-profile 解释层
- 未来 ground specialization 的归属
- 哪些术语绝不能借用 air/naval 语义

### 9.2 capability composition 映射

- 第一批 ground slice 需要哪些 `PlatformFamily`、`MotionFamily`、
  `SensorFamily`、`LauncherFamily`、`DoctrineFamily` 与 `EffectsFamily`
- 哪些条目只是 placeholder，哪些会成为 maintained 能力

### 9.3 content 与 database 结构

- `examples/config/database/` 下的第一批内容根目录
- unit/module schema 预期
- 在 public capability composition 更进一步晋升前，
  `spawn_unit(type_name)` 需要怎样的兼容行为

### 9.4 contracts、bindings 与 facade 可见性

- C++ DTO 落点
- 字段进入 maintained 后的 Python binding 暴露
- facade request/result 的可见性规则
- 对现有 caller 的兼容策略

### 9.5 验证与证据

- architecture tests
- runtime-contract tests
- scenario 或 fixture smoke tests
- 证明没有引入“新域私有 runtime path”的证据

### 9.6 information-state 与 agency 边界

- ground unit 的 sensed / observed / believed 信息边界
- land tasking 中的 command/support 关系
- authority ownership 与 delegation 规则

### 9.7 terrain 与 environment 依赖

- terrain、route、obstruction、line-of-sight 的要求
- 第一切片是否可以避免新增 environment-model contract
- 如果 terrain 暂时保持抽象，哪些内容必须明确标注为 deferred

## 10. 下一轮讨论顺序建议

在实现前，建议按以下顺序继续讨论：

1. 确认第一平台族与 fixture 风格
2. 确认 phase one 是 tasking-only，还是要带极小的 execution command surface
3. 确认第一版 observation/reporting surface
4. 确认哪些横向补充项在第一波必须落地，哪些可以明确 deferred
5. 确认用什么证据证明没有引入私有 ground runtime path

## 11. 这条规划线的成功标准

当这条规划线能稳定回答下列问题时，就说明它达到了目的：

- 第三域在层次模型中应落在哪里
- 第一批 maintained scope 是什么
- 为保持架构诚实，哪些内容必须一起实现
- 为了让第一切片保持小而可测，哪些内容必须继续延后
- G1 开始前必须坚持哪些 G0 架构承诺
