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

1. 项目应遵循一条规范化语义生命周期。
2. 真实执行应使用多率 temporal DAG，反馈跨越显式 state-store 或 event-queue 边界。
3. 空军、海军、武器和未来领域应通过阶段局部的模型族与 stage-node contract 扩展该生命周期。
4. runtime facade 与 typed request/result 契约应成为前端长期依赖面。
5. 策略计算层与测试/编排层应被建模为 facade contract 的显式 producer / consumer，而不是仿真状态的隐藏 owner。
6. 本机工作应聚焦 build/import/smoke、架构文档、契约设计和仿真系统组建，而不是 RL 训练。

## 工作包

| 工作包 | 状态 | 目标 | 产出 |
|--------|------|------|------|
| `WP0 Architecture Baseline` | complete | 明确语义生命周期、temporal DAG 与扩展规则 | 架构设计文档、任务子项目入口 |
| `WP1 Pipeline Inventory` | complete | 把当前代码、system、model、test 映射到 `P0-P10` 与当前耦合热点 | [管线盘点](pipeline_inventory_wp1_20260519.zh.md) |
| `WP2 Contract Freeze` | active | 识别需要显式 ownership 的 packet 族、stage-node contract 与跨层 policy/orchestration contract | [契约冻结](contract_freeze_wp2_20260519.zh.md) |
| `WP3 Engagement Pilot` | active | 以武器/交战作为第一条跨领域验证切片 | [交战试点任务族](engagement_pilot_wp3_20260519.zh.md) |
| `WP4 Facade Alignment` | planned | 确保试点行为可通过 facade-shaped API 访问 | facade request/result 增补与 adapter 计划 |
| `WP5 Validation Harness` | planned | 添加证明生命周期共享的 smoke 与架构测试 | 聚焦测试与本机 Windows smoke 命令 |

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

- [WP1 管线盘点](pipeline_inventory_wp1_20260519.zh.md)

产出：

- [WP2 契约冻结](contract_freeze_wp2_20260519.zh.md)

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

- [WP3 交战试点任务族](engagement_pilot_wp3_20260519.zh.md)

第一条实现试点应选择交战生命周期，因为它横跨最多架构边界，并且天然涉及多个 clock domain：

`tasking -> command delivery -> sensor/track -> fire control -> launcher -> munition -> seeker/guidance/fuze -> effects -> damage -> observation`

该试点必须涉及至少两个平台族，例如：

- 航空挂架发射，
- 舰载挂载发射。

试点应避免创建独立的 `air weapon` 和 `naval weapon` 运行时路径。差异应出现在 launcher、munition、seeker、guidance、fuze、effects、doctrine 族和 clock-domain policy 中。

第一波实现应拆分为 contract DTO scaffold、facade packet shell、Python binding exposure、air launch adapter、naval launch adapter、munition/damage export、diagnostics trace 和 stage-aligned non-RL smoke harness。Air 与 naval worker 只有在不编辑同一个共享 kernel 文件时才适合并行。

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

## 非目标

- 在本地 Windows 机器上完成完整 RL 训练。
- 立即替换为 exact GPU world-step。
- 把 Rust 作为近期后端引入。
- 在 contract freeze 前重写所有既有 command/tasking DTO。
- 在 WP0/WP1 阶段移动所有现有文件到新目录。
