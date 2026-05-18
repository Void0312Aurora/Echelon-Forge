# 军种画像总览

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

状态：`2026-05-18`，军种画像层权威入口。

本目录定义基于美军公开资料整理的军种画像。军种画像不是平台手册，也不是完整编制百科，
它的职责是回答：

- 哪些组织层级适合进入 tight-loop runtime
- 哪些角色应停留在任务/授权/编组元数据层
- `joint/common core` 的共享字段在各军种里如何解释

## 当前纳入的画像

- [美国空军](air_force.md)
- [美国陆军](army.md)
- [美国海军](navy.md)
- [美国海军陆战队](marine_corps.md)

当前建立在军种画像之上的特化目录：

- [空中平台特化](../air/README.md)
- [海军特化](../naval/README.md)

## 军种画像负责什么

军种画像负责解释：

- 哪些战术层级是真正有意义的 runtime 单位
- 哪些角色更适合作为任务/指挥元数据，而不是直接控制面
- `joint/common core` 字段在该军种里的语义口径
- 哪些概念在进入平台/任务特化之前，仍应先保留为军种特有概念

例如：

- `task_package`、`flight`、`element` 先是空军画像概念，然后才进入 air execution semantics。
- `task_group`、`task_unit`、`warfare_role_code`、
  `officer_in_tactical_command` 先是海军画像概念，然后才进入 naval runtime semantics。

## 军种画像不负责什么

军种画像不定义：

- 引擎中立的坐标/单位约定
- 低层 runtime DTO 布局
- 平台专用的传感器页面、runway procedure 或 ship station geometry
- `docs/task/` 下的活跃任务排期细节

这些内容分别应放在：

- [仿真约定](../foundation/conventions.md)
- [运行时工作流与合同基线](../bridge/runtime_workflow_and_contract_baseline.md)
- [air/](../air/README.md)
- [naval/](../naval/README.md)

## 统一结论

四个军种都不支持把“行政编制树”直接塞进 tight-loop RL/runtime 层。

当前维护中的仓库基线是：

- 高层联合/军种层保留为任务发布、授权和兵力包装层
- tight-loop runtime 落在真实的战术单位上
- 由各军种画像来定义“什么算战术单位边界”

## 与当前 runtime 工作的关系

当前代码里已经同时存在几种桥接状态：

- air-first 的 mission semantics，例如 `mission_command`、route、takeoff、runway、formation
- 新出现的 naval semantics，例如 `task_group_id`、ship mission command、authority tests
- joint/common seams，例如 `MissionCommand`、`CommandLink`、`DataLink`、report flow

军种画像层的职责，就是在这些概念被提升到 common core 或下沉到 specialization 之前，
先把它们解释清楚。

## 相关文档

- [联合标准总览](../joint/README.md)
- [文档对齐映射](../overview/document_alignment_map.md)
- [场景配置指南](../bridge/scenario_guide.md)
- [运行时工作流与合同基线](../bridge/runtime_workflow_and_contract_baseline.md)
