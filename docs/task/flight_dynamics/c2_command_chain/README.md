# C2 指挥链与通信子项目

状态：`2026-05-17` 活跃推进中。

本子项目收纳与当前 `MissionCommand / CommandLink / DataLink / ROE / naval command-chain` 推进直接相关的文档，避免把持续进展继续堆回冻结分析稿。

## 文档入口

- [冻结分析基线](c2_command_chain_realism_analysis_20260517.zh.md)
  作用：保留 `2026-05-17` 时点的缺陷分析与不应夸大的表述。
- [当前进展检查点](c2_command_chain_progress_checkpoint_20260517.zh.md)
  作用：记录当前这轮已经完成的实现、验证和主线能力面。
- [待解决问题分析](c2_command_chain_unresolved_issues_20260517.zh.md)
  作用：聚焦还没解决的技术缺口、当前边界和下一轮建议。

## 当前范围

当前子项目关注：

1. `MissionCommand` 在 air / naval 两侧的最小执行语义与 authority 统一。
2. `CommandLink` 的最小 FIFO / latency / pending queue 语义。
3. `PilotAction` 与 `MissionCommand` 的控制权边界。
4. `ROE / engagement authority` 的最小字段和 runtime gate。
5. `DataLink` 的最小预算、优先级和可观测拥塞状态。

当前子项目不试图一次解决：

1. 完整 Link 16 / NPG / relay / ACK / retransmission。
2. 完整 naval fire-control AI / CEC / engage-on-remote。
3. 完整海军 tasking state machine 与多舰编队 doctrine。
4. 全量 episode/json/schema 冗余消解。

## 关联文档

- [海战仿真现实性分析](../naval/naval_realism_analysis_20260516.zh.md)
- [传感器与态势感知现实性分析](../sensor_situation/sensor_situation_realism_analysis_20260516.zh.md)
- [武器系统与制导回路现实性分析](../weapon_guidance/weapon_guidance_realism_analysis_20260516.zh.md)
- [海战推进检查点](../../naval/naval_progress_checkpoint_20260517.zh.md)

## 维护规则

1. 冻结分析继续保留原文件，不在原文中改写“当时判断”。
2. 当前实现进展统一进入 `progress checkpoint`。
3. 仍待解决且会影响下一轮排期的内容统一进入 `unresolved issues`。
