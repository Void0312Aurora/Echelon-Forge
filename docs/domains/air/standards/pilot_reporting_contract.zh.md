# 飞行员汇报合同

Language:
- English canonical: [pilot_reporting_contract.md](pilot_reporting_contract.md)
- Chinese companion: `pilot_reporting_contract.zh.md`

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/domains/air/standards/pilot_reporting_contract.md`
Owner: `domains/air`
Last verified: `2026-08-08`

状态：当前维护中的 air reporting semantics 特化基线。

本文档定义仓库当前维护中的 air reporting contract，它不是完整 brevity-code 手册。

## 范围

当前维护中的 reporting surface 分成三层：

- `PilotReportCore`
- `PilotReportAir`
- 当前 leader/runtime logic 真正赋予稳定语义的 report type 子集

主要依据：

- [src/components/tasking/common/pilot_report_core.h](../../../../src/components/tasking/common/pilot_report_core.h)
- [src/components/domains/air/tasking/pilot_report_air.h](../../../../src/components/domains/air/tasking/pilot_report_air.h)
- [src/components/tasking/pilot_report.h](../../../../src/components/tasking/pilot_report.h)
- [python/rl/tasking/leader_tasking.py](../../../../python/rl/tasking/leader_tasking.py)
- [src/runtime/contracts/world_batch_contracts.h](../../../../src/runtime/contracts/world_batch_contracts.h)
- [tests/runtime/bindings/test_bindings_command_surface.py](../../../../tests/runtime/bindings/test_bindings_command_surface.py)

## Core Report 字段

`PilotReportCore` 提供跨域共享的 report skeleton：

- `report_type`
- `sender_id`
- `task_id`
- `service_profile`
- `task_family`
- `tactical_unit_type`
- `tactical_unit_id`
- `task_group_id`
- `role_code`
- `coordination_mode`
- `timestamp_s`
- `status_value`
- `entity_ref`
- `location_x_m`
- `location_y_m`
- `location_z_m`
- `active`

这些字段属于 common 的 tasking/report ownership，不属于 air 独有语义。

## Air Report 扩展字段

`PilotReportAir` 当前追加：

- `element_id`
- `phase_id`
- `formation_role_id`
- `formation_error_m`
- `bearing_error_deg`
- `closure_mps`
- `separation_m`

这些字段属于编队与空中任务执行上下文中的 air-specific reporting 信息。

## 当前维护中的稳定 Report Type

当前 leader/runtime 闭环明确赋予稳定语义的 report type 是：

- `REP_ON_STATION`
- `REP_RTB`
- `WARN_BINGO`
- `REP_UNABLE`
- `REP_WILCO`

这些 report type 才是当前 runtime logic 真正用来驱动任务推进或 leader assessment 的闭环信号。

## 扩展 Report Surface

更大的 DTO 与 enum surface 仍然可以承载更多 report code，测试里也可能会存储或 roundtrip
额外的 air report type，例如编队相关状态。

但如果当前 runtime logic 还没有赋予它们稳定的闭环语义，就应把它们视作 extension surface，
而不是把它们写成当前已经实现的主合同。

换句话说，本文档不应把大段战术简语目录写成“仓库已经全部消费”的既成事实。

## 汇报生成规则

当前维护中的 pilot-report contract 至少应稳定保留：

- 有效的 `report_type`
- sender/task identity
- timestamp
- location
- active 状态

若编队上下文重要，还可以填充：

- formation role
- formation error
- bearing error
- closure
- separation

## 归属边界

应继续保留在 common core 的内容：

- 通用 report identity 与 metadata
- 跨域共享的 tasking/report skeleton

应继续保留在 air specialization 的内容：

- formation-specific error 与 closure 数据
- 与空中任务执行绑定的 phase / element 上下文
- 建立在共享 report type 之上的 air-specific 解释

## 非目标

本文档不试图标准化完整 brevity-code 手册，不穷举所有空战口令，也不预写未来 leader-agent 的全部汇报启发式。
它只描述当前代码与测试能够真实 roundtrip 或解释的维护合同。
