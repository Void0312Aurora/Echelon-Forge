# 美国空军画像

Language:
- English canonical: `air_force.md`
- Chinese companion: [air_force.zh.md](air_force.zh.md)

状态：`2026-05-18`，USAF 军种画像层权威版本。

本文档定义仓库在进入 `air/` 特化之前，如何解释美国空军的组织概念。

它不是完整条令摘要，而是回答三个标准化问题：

- 哪些 USAF 层级应停留在场景与任务包装元数据层
- 哪些战术层级适合进入 tight-loop runtime
- 哪些术语只属于军种画像层，哪些必须通过当前维护中的空中命令、观测、动作与汇报合同来表达

## 现实基础

当前公开的 USAF 条令仍把指挥控制视为一个围绕授权分配展开的 mission-command 问题，
而不是单一 AOC 界面问题。

官方参考：

- [AFDP 3-0.1, Command and Control](https://www.doctrine.af.mil/Operational-Level-Doctrine/AFDP-3-01-Command-and-Control/)
- [AFDP 3-0.1 PDF](https://www.doctrine.af.mil/Portals/61/documents/AFDP_3-0_1/AFDP3-0.1CommandandControl.pdf)

官方页面当前标注 `Last Published: 22 Jan 2025`。该条令与摘要强调：

- 指挥控制以 commander 为中心
- 授权委派是显式结构
- `Centralized Command - Distributed Control - Decentralized Execution`
- AFFOR staff、AOC staff、wing、TACS 等属于更大 C2 system 的组成部分，而不是唯一的 runtime 表面

这已经足以支撑本仓库的标准化结论：高层空中组成与战区管理结构保留在 tight-loop runtime 之上，
而架次级战术组织保留在其下。

## 层级边界

### `joint/common core`

common 层只保留跨军种共享的骨架：

- `service_profile`
- `task_family`
- `tactical_unit_type`
- `authority_scope`
- `command_relationship`
- `coordination_mode`
- `task_group_id`
- `role_code`
- `relative_slot_code`
- `recovery_site_id`

这些字段保持中立，不会因为仓库当前偏 air 而自动变成 USAF 专属术语。

### `services/air_force`

空军画像层负责给这套共享骨架赋予 USAF 口径：

- `mission package` 及类似的上层任务包装
- `flight` 与 `element` 的战术分组含义
- package lead、element lead、wingman、platform 之间的角色差异
- 某个组织层级何时不再只是元数据，而开始成为 runtime 战术单位

这一层定义的是解释权与归属，不负责 runway 几何、动作向量或 mission-observation 数组布局。

### `air`

专门的 `air/` 目录负责当前维护中的空中执行合同：

- `TaskOrderAir`、`LeaderIntentAir`、`PilotReportAir`
- `MissionCommand` 的 air 扩展与当前维护中的 `command_code`
- `route_ref_id`
- `takeoff_*`、`formation_*`、`recovery_*`
- mission-observation modes
- `PilotAction` 映射与报告分类

一个术语只要必须触及 runway、formation、recovery 或 pilot control surface，
它就属于 `air/`，不属于这里。

## Runtime 边界

### 应留在场景/战役元数据层的层级

下列概念真实存在且重要，但在当前仓库里应继续停留在 tight-loop runtime 之上：

- COMAFFOR / JFACC 级授权框架
- AOC 规划与 air-tasking-cycle 编排
- MAJCOM、NAF、wing 等行政或战区管理层
- 战区级兵力呈现与分配决策

这些层级更适合放在：

- 场景编写
- 兵力包装
- 任务授权
- 更高层行动元数据

### 可以进入战术 runtime 的层级

当前仓库应把可执行空战边界放在真实战术单位上，并由 USAF 画像解释：

- mission package
- flight
- element
- aircraft / platform

在代码层面，这通常意味着 common core 只携带 `MissionPackage`、
`TacticalUnit`、`Platform` 这类泛化锚点，而 Air Force profile 解释它们在
架次级单位中的现实含义。

## 对标准树的直接约束

空军画像会对其他标准文档施加几条硬约束。

### 不要把空军专有任务词汇写进 common core

以下术语不应成为 common-core 名词：

- `CAP`
- `BARCAP`
- `TARCAP`
- `runway slot`
- `takeoff clearance`
- `element lead`

这些都属于 Air Force profile 或 `air/` specialization。

### 共享字段只承载骨架，不承载完整空战词汇

共享字段应表达可移植的组织骨架：

- 单位属于哪个军种
- 它是什么战术单位
- 它处于什么支援/协同关系
- 它引用哪个 recovery site 或 task group

这些字段的空军含义，由空军画像层和 `air/` 文档继续叠加解释。

### 航路、编队、起飞、回收继续下沉到 `air/`

即便当前 runtime 对象暴露了 `route_ref_id`、`takeoff_procedure_id`、
`takeoff_clearance_id`、`formation_id` 或 recovery 标识，这些字段也不属于
军种画像层所有权。它们属于已维护的 air specialization 合同。

## 与当前仓库合同的关系

当前仓库已经形成 air-first 的战术桥接：

- common tasking 字段通过 `TaskOrder`、`LeaderIntent`、`PilotReport` 流动
- 可执行命令通过 `MissionCommand` 流动
- 架次级观测与动作合同由 `air/obs.md` 和 `air/act.md` 定义

因此，本文档的作用就是守住边界：

- 上层 USAF 组织继续作为元数据
- 战术分组语义停留在军种画像层
- 执行细节继续由维护中的 `air/` 文档负责

## 相关文档

- [军种画像总览](README.md)
- [空中平台特化](../air/README.md)
- [联合指挥与建模基线](../../domains/joint/standards/command_and_modeling_baseline.zh.md)
- [联合命令链与汇报基线](../../domains/joint/standards/command_link_and_reporting_baseline.zh.md)
- [运行时工作流与合同基线](../bridge/runtime_workflow_and_contract_baseline.md)
