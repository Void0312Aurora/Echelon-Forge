# Ground 标准

Language:
- 英文主文：`README.md`
- 中文辅文：[README.zh.md](README.zh.md)

状态：`2026-05-22` G0-G4 封存特化基线，并补充 G5 MVP 场景边界。

本目录收纳专门的 `ground` specialization 标准文档。

这里是第三域 G0 工作的标准入口。它的职责是把 `joint/common core`、
`services/army` 与 `ground` 清楚分层，让后续 tasking、content、profile
与 runtime 工作可以推进，同时避免引入 air 或 naval 的执行假设。

在这个边界内，`army` 是 service profile 和可接受的 tasking-profile
alias，`land` 是可接受的描述性 alias；二者都会归一到维护中的 `ground`
execution specialization。`army` 和 `land` 都不命名独立的 ground runtime
stack。

## 1. 分层模型

### `joint/common core`

共享层保持跨军种合同稳定。

它负责这些字段形状：

- `service_profile`
- `task_family`
- `tactical_unit_type`
- `command_relationship`
- `authority_scope`
- `coordination_mode`
- `role_code`
- `supported_node_id / supporting_node_id`
- `task_group_id`
- `recovery_site_id`

这些都是军种无关的形状，不是 ground 执行语义。

### `services/army`

Army service profile 负责说明共享合同在陆军地面力量语境下应如何阅读。

它负责这些解释：

- 梯队化组织
- command 与 support 关系
- 哪些层级可能成为 tactical runtime unit
- 哪些层级应保留为 scenario、operational 或 campaign metadata
- maneuver、fires、sustainment 与 support 在成为执行语义前的 Army profile 解释

### `ground`

`ground` specialization 负责 service profile 刻意不定义的 tight-loop 陆上执行语义：

- 以 platoon 为中心的起步 tasking
- move、occupy、support 任务语义
- ground command/support 执行词汇
- ground agency role 与 authority scope
- 受 terrain masking 约束的信息状态假设
- 后续 ground mobility、sensing、direct-fire、indirect-fire、sustainment 与 reporting 扩展

## 2. G0 基线决策

G0 基线为第一批 ground-domain 工作冻结这些默认值：

- 维护中的特化名：`ground`
- 接受的 tasking-profile 别名：`army`、`ground`、`land`（`army` 仍是
  service profile，`land` 仍是 alias）
- 归一后的 tasking-profile 名：`ground`
- 第一批 tight-loop 战术单元：`platoon`
- 第一任务词汇：`move / occupy / support`
- 第一 tasking cadence 假设：`1 Hz` tactical evaluation

这些默认值在 G0 中冻结。后续工作只有通过 accepted standards update 才能改变它们；
如果某个 worker 需要不同默认值，必须停止，而不是直接改写这些 canonical terms。

## 3. 最小语义合同

当前被视为一等术语的最小 ground 语义集是：

- `ground`
- `platoon`
- `move`
- `occupy`
- `support`
- `ground_squad_leader`
- `ground_platoon_commander`
- `ground_company_commander`
- terrain-masked sensing
- radio-range-constrained shared tactical picture

这些术语足以让第三域任务计划具备明确语义，同时不必套用 air sortie 或 maritime station 语言。

## 4. Stage 覆盖规则

第一批 ground 切片通过以下声明阶段进入共享生命周期：

这些声明是面向 planning 与 contract shape 的 architecture commitments，不表示
maintained ground runtime behavior 已经存在。

| Stage | Ground 基线 |
|-------|-------------|
| `P0 ContentCompile` | ground 平台定义应通过 capability bundle 下沉。 |
| `P2 TaskingIntent` | ground task order、leader intent、梯队元数据、command relationship 与 support relationship。 |
| `P3 CommandDelivery` | 延后到最小 ground command surface 被接受之后。 |
| `P6 SenseTrackLink` | 延后到 terrain masking、line-of-sight、radio range 与 relay topology 明确之后。 |
| `P10 ObservationExport` | formal observation export 延后；status/report 合同测试可以先行。 |

任何触及更多阶段的 ground 实现，都必须先更新本标准或派生的 accepted standards 文档。

Clock-domain default：`1 Hz` 是 ground tasking 的 tactical evaluation 基线。
motion 与 sensing update 保持 low-rate、event-driven 或延后到后续 accepted
execution design；任何 cadence 都必须并入 shared causal-temporal scheduler，而不是
private ground loop。

## 5. Capability Composition 规则

ground 平台必须通过 capability composition 定义，而不是新增 canonical hardcoded
type-name dispatch 路径。

第一波 capability-family 声明：

| Family | Ground 基线 |
|--------|-------------|
| `PlatformFamily` | `dismounted_unit`、`ground_vehicle_section` |
| `MotionFamily` | `ground_mobility`；wheeled、tracked、dismounted 变体保留为后续细节 |
| `SensorFamily` | `ground_visual`、`ground_acoustic`；延后到执行设计 |
| `LauncherFamily` | `direct_fire_platform`、`indirect_fire_battery`；延后到执行设计 |
| `DoctrineFamily` | `land_tactics`，覆盖 move、occupy、support，后续扩展 screen/secure |
| `EffectsFamily` | 延后 |

`spawn_unit(type_name)` 只能继续作为兼容 wrapper，不应成为 ground 的长期
canonical 构造路径。

G5 MVP 场景边界：

- 场景可以使用当前 runtime 可加载的兼容 spawn type，仅用于验证共享
  loader/tasking plumbing
- 场景必须说明该 spawn type 不是 maintained ground platform schema
- ground 语义所有权必须来自 `tasking_profile`、Army service profile 字段与
  common-core tasking 字段
- 兼容 spawn 的使用不得被引用为 ground movement、terrain、sensing、fires、
  effects、damage、observation export 或 formal command delivery 的证据

## 6. Agency 与 Information State

ground role 必须声明：

- `role`
- `authority_scope`
- `information_state_source`
- `decision_model_ref`
- `action_interface`

第一波角色默认值：

| Role | Authority scope | Information source | Decision model ref | Action interface |
|------|-----------------|--------------------|--------------------|------------------|
| `ground_squad_leader` | squad | sensed state plus agent observation | scripted land-task execution；later learned policy | task-order execution |
| `ground_platoon_commander` | platoon | shared tactical picture plus agent observation | scripted platoon tasking；later doctrine profile | leader intent and task-order delegation |
| `ground_company_commander` | company | shared tactical picture | company coordination doctrine，延后 | coordination intent，延后 |

ground information state 遵循六层架构模型：

- `World Truth` 在实现后也必须保持在 shared runtime 内部。
- `Sensed State` 默认受 terrain masking 与 line-of-sight 约束。
- `Track State` 可使用 visual/acoustic correlation；maintained fusion 延后。
- `Shared Tactical Picture` 受 radio range、relay topology、latency 与 permission 约束。
- `Agent Observation` 应为 view-spec-shaped，不得暴露 world truth。
- `Decision Belief` 必须声明由哪些 observation 或 shared-picture 输入生成。

这些 information-state 条目是未来工作的边界和 deferral，不表示 maintained
terrain、sensing、tracking、relay 或 observation-export runtime behavior 已经存在。

## 7. 这里应该写什么

放在这里的文档应描述 ground-specific 语义，例如：

- 以 platoon 为中心的 tasking 默认值
- move、occupy、support、screen、secure 以及后续 fires 任务语义
- ground command/support authority 解释
- terrain-masked sensing 与 radio-constrained information sharing
- ground agency roles
- 后续 ground execution 与 reporting specialization

## 8. 这里不应该写什么

以下内容应继续留在 `joint/`、`services/army` 或 bridge 文档：

- 共享的 `command_relationship`、`authority_scope`、`task_family`、
  `service_profile`、`tactical_unit_type` 与 `coordination_mode` 定义
- 不定义执行语义的 Army service organization 总结
- scenario/runtime adapter 细节或 private ground runtime path
- 实现层 C++ DTO memory layout
- 在相应工作流拥有 accepted task plan 之前，声称完整的 terrain、mobility、
  direct-fire、indirect-fire、damage 或 logistics runtime behavior 已存在

本 overview 只规范 standards placement；它不实现也不授权 ground-only runtime
pipeline。

## 9. 与 Air 和 Naval 的关系

`ground` 不是 air 或 naval 文档改名。

后续 ground 文档应避免默认使用 air 概念，例如：

- `wingman`
- `element lead`
- `runway`
- `takeoff`
- `formation slot`
- `recovery approach`

ground 文档也不应把 `station`、`task group` 或海上 `screen` 等 naval 术语当作默认 land baseline，除非 ground 文档明确重新定义其陆上含义。

## 10. 相关文档

- [Ground 最小任务结构](minimal_task_structure.zh.md)
- [美国陆军画像](../services/army.zh.md)
- [联合指挥与建模基线](../joint/command_and_modeling_baseline.zh.md)
- [运行时工作流与合同基线](../bridge/runtime_workflow_and_contract_baseline.zh.md)
- [Ground 域启动计划](../../task/ground/archive/ground_domain_bootstrap_plan_20260521.zh.md)
