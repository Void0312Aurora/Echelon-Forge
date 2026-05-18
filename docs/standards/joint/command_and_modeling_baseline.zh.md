# Joint 指挥与建模基线

本文档定义项目中 joint/common core 的边界，用来统一指挥关系、authority scope、intent / order / report，以及可跨空海陆复用的最小数据模型。

## 1. Joint 层在这里意味着什么

这里的 joint 层不是“所有军种共享同一棵完整战术树”，而是一个共享合同，用来回答四个问题：

- 谁可以指挥谁
- 谁可以委托、继承或转移 authority
- 哪些内容属于命令、汇报或数据链转发
- 哪些内容应留在 common core，哪些内容应交给 service profile

因此 joint 层必须小而稳。它不应被写成空军专用词汇，也不应被写成海军或地面专用词汇。

## 2. 共通的指挥关系词汇

以下关系在本项目中属于 joint/common core 概念：

- `COCOM`
- `OPCON`
- `TACON`
- `ADCON`
- `support`
- `coordinating authority`
- `DIRLAUTH`

这些词不是军种专用词。具体哪一种关系生效、谁持有、何时转移，由 service profile 决定。

当前运行时和测试已经把带 authority 的字段视为稳定合同，包括：

- `roe_state`
- `engagement_authority_holder_id`
- `engagement_authority_grantor_id`
- `assigned_target_id`
- `authorization_to_fire`

## 3. Authority Scope

authority scope 解决的是“谁能影响什么，以及影响到哪里”为止。

在 common core 里，authority scope 应该通过少量显式字段和关系表达，而不是写死成某一种军种行为。当前运行时的合同已经体现了这一点：

- `TaskOrder` 和 `LeaderIntent` 承载共享任务意图
- `MissionCommand` 承载可执行命令及其 authority 状态
- `CommandLink` 承载投递时序与顺序
- `DataLink` 承载共享航迹和汇报交换

authority 模型要保持显式，不要把它藏进平台运动参数里。

## 4. Intent / Order / Report

最小共通链路是：

`Intent -> Order -> Execution Command -> Report`

在这个仓库里，对应的实际分层是：

- `TaskOrder` 表达任务式下达
- `LeaderIntent` 表达领导者的战术决策
- `MissionCommand` 表达运行时可消费的执行命令
- `PilotReport` 及相关报告结构表达状态回传

这个链路已经反映在任务编排和 mission runtime 测试中。common 层需要保留这条链路的形状，但不能强迫所有军种使用同一种执行方式。

## 5. 指挥关系与任务组织的边界

joint 层应该保留组织骨架，而不是军种 doctrine 细节。

建议保留在 common core 的字段有：

- `task_family`
- `service_profile`
- `tactical_unit_type`
- `command_relationship`
- `authority_scope`
- `assignee_kind`
- `coordination_mode`
- `parent_node_id`
- `supported_node_id`
- `supporting_node_id`
- `task_group_id`
- `role_code`
- `relative_slot_code`
- `recovery_site_id`

应交给 service profile 的内容包括：

- 空军专用的 `runway`、`takeoff`、`landing`、`CAP` 和编队语义
- 海军专用的 `station`、`screen`、`formation`、参考单元和舰载直升机语义
- 未来地面专用的机动与支援语义

common 层可以描述一个单元被 support 或 supporting，但不应写死它在空、海、陆中的执行方式。

## 6. Common Core 不应优先写什么

设计共享结构时，不要让 common core 被某个军种的执行语言反向塑形。

不应把这些当成首要抽象：

- `wingman_slot_id`
- `recovery_runway_id`
- `task_cap`
- `takeoff_clearance`
- 只用 `station_radius_m` 作为站位模型

应优先采用所有 service profile 都能解释的抽象：

- `task_family`
- `service_profile`
- `tactical_unit_type`
- `relative_slot_code`
- `coordination_mode`
- `authority_scope`
- `recovery_site_id`

## 7. Common Core 与 Service Profile 的边界

边界很简单：

- common core 定义跨军种仍成立的名词和 authority 关系
- service profile 定义这些名词在特定任务域中的解释方式
- platform/task specialization 定义具体几何、时序和控制细节

因此 `docs/standards/joint/*` 应负责命名边界和禁止项，而军种与平台文档应负责具体执行词汇。

## 8. 实现含义

当前代码和测试已经明确朝这个方向收敛：

- `MissionCommand` 是运行时命令承载体
- `CommandLink` 是投递与排序层
- `DataLink` 是共享航迹 / 汇报层
- `ROE` 和交战 authority 是执行命令合同的一部分，不是附属项

后续模块拆分的基线应当是：

1. `joint/common core`
2. `service profile`
3. `platform/task specialization`

