# 地面任务域

语言：[英文规范页](README.md)；本页为中文配套。

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/domains/ground/README.md`
Owner: `domains/ground`
Last verified: `2026-08-08`

Ground owner 定义陆上领域特化语义，但不把 Army 军种条令变成一条私有 runtime
栈。它拥有 Ground 专属平台身份和静态 task/status 词汇。Joint 关系、Army
service-profile 解释以及跨域 runtime 架构仍由各自 owner 负责。

## 当前权威

- [Ground 特化基线](standards/specialization_baseline.zh.md)：规范 Ground 身份、
  owner 边界、已接受实现表面和仍保持 held 的 runtime 声明。
- [Ground 最小任务结构](standards/minimal_task_structure.zh.md)：维护中的
  `TASK_MOVE`、`TASK_OCCUPY` 和 `TASK_SUPPORT` 静态 task/status 合同。

## 当前已实现表面

- `army`、`ground`、`land` 和 `ServiceProfile.Army` 均路由到维护中的
  `ground` tasking profile。
- `Ground_Platoon_MVP` 是 runtime 可加载的原生 `UnitType::Ground` 内容定义，
  用于静态 schema 与 scenario-loader 证据。
- Ground 自有 component slice 通过 `TaskOrder`、`LeaderIntent`、`PilotReport`
  和 `MissionCommand` 兼容 shell 传递静态 command/task/status 字段。
- 维护中的 tasking cadence 基线是 `1 Hz`。
- 当前不存在 `src/systems/domains/ground/` runtime-system owner。Route
  movement、terrain interaction、sensing、fires、effects、damage、suppression、
  logistics 和 Ground observation export 仍保持 held。

目录位置不会扩大上述声明。当前证据证明的是原生身份和静态 task/status 链，
而不是完整 land-combat runtime。

## 当前工作入口

- [Ground 任务区](../../task/ground/README.zh.md)：当前实现状态、剩余 held
  边界和执行规划。

任务文档可以报告成熟度和证据，但不得重新定义以上标准。

## 相关 Owner

- [Joint 任务域](../joint/README.zh.md)：共享授权与 common-core command
  relationship。
- [美国陆军 service profile](../joint/service_profiles/standards/army_profile.zh.md)：
  Army 组织和军种级解释。
- [Runtime workflow 与合同基线](../../standards/bridge/runtime_workflow_and_contract_baseline.zh.md)：
  共享 stage 与 runtime 边界，等待其独立 owner 迁移。
