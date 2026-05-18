# 真实化主线与关联子项目当前状态

状态：`2026-05-17` 当前工作区集成复核版。

关联文档：

- [归档的真实化任务总表](../archive/program/realism_program_taskboard_20260516.zh.md)
- [真实化 P1 任务总表](realism_program_p1_taskboard_20260517.md)
- [C2 指挥链与通信子项目](../c2_command_chain/README.md)
- [归档的 C2 指挥链与通信推进检查点](../archive/c2_command_chain/c2_command_chain_progress_checkpoint_20260517.zh.md)
- [归档的 C2 指挥链与通信待解决问题分析](../archive/c2_command_chain/c2_command_chain_unresolved_issues_20260517.zh.md)
- [海战推进检查点](../../naval/naval_progress_checkpoint_20260517.zh.md)
- [海战后续委派执行单](../../naval/naval_delegated_execution_backlog_20260517.zh.md)
- [空战 1v1 F-16C 基线切换与最小对战合同进展](../../air_combat/air_combat_1v1_f16c_baseline_progress_20260516.zh.md)
- [指挥链与 C2 通信现实性分析](../c2_command_chain/c2_command_chain_realism_analysis_20260517.zh.md)

本文档定位：

- 本文档用于整理 `docs/task/flight_dynamics/` 下与当前真实化主线直接相关的文档入口。
- 本文档同时串起我当前负责的关联子项目文档：`naval/`、`air_combat/`、`C2 command-chain`。
- 本文档不重复展开每份分析细节，只回答“现在该看哪些文档、当前做到哪里、还有哪些稳定性问题”。

## 零、当前总阶段

当前总阶段建议统一表述为：

1. 主线整体仍处于 `P1-A 集成收尾`。
2. `flight`、`sensor`、`weapon`、`naval` 与 `C2` 的关键守门面已经收口，当前更适合转入维护态。
3. 本轮抽样复核里，`sensor / DataLink / track`、海军武器命令链与 weapon 守门面都已转绿；
   当前不再把它们写成稳定红点，剩余重点转向 shared contract 收口与结构债减载。
4. `C2` 已进入“最小工程闭环接入主线”；其推进检查点与待解决问题快照已归档到 `archive/c2_command_chain`，活跃子树只保留冻结分析基线。

这意味着当前最重要的工作不是继续多线扩深，而是先把 shared contract
与结构债务收束，再按需做有限的 deeper modeling。

## 一、当前进展摘要

- `flight` 已转维护态：推进、失速记忆和守门测试都已收口，后续重点是更深的 `Mach/compressibility / stall / FBW`。
- `sensor` 也已转维护态：`track/report` 与 `DataLink` 守门面已绿，后续重点是更紧的 `track lifecycle / IFF / fusion`。
- `weapon` 已打通共享发射链和发射前门槛，剩余风险主要在 tuning 与 runtime assembly 的结构耦合。
- `naval` 与 `C2` 不再是主阻塞，更像验收面和兼容性收尾面。

## 二、稳定性说明

- 当前复核里没有再复现新的稳定失败。
- 现在要做的是继续减结构债，而不是重新打开已经收口的守门面。
