# C2 指挥链与通信分析

语言版本：

- 英文主文：[README.md](README.md)
- 中文辅文：`README.zh.md`

状态：`2026-05-17` 分析基线保留；可信口径以本分析的收口标记为准，不再依赖 `program/` 或 `archive/`。

本子树保留 `MissionCommand / CommandLink / DataLink / ROE / naval command-chain`
的冻结分析基线。

## 文档入口

- [冻结分析基线](c2_command_chain_realism_analysis_20260517.zh.md)
  作用：保留 `2026-05-17` 时点的缺陷分析与不应夸大的表述。
## 分析范围

这份分析关注：

1. `MissionCommand` 在 air / naval 两侧的最小执行语义与 authority 统一。
2. `CommandLink` 的最小 FIFO / latency / pending queue 语义。
3. `PilotAction` 与 `MissionCommand` 的控制权边界。
4. `ROE / engagement authority` 的最小字段和 runtime gate。
5. `DataLink` 的最小预算、优先级和可观测拥塞状态。

这份分析不试图一次解决：

1. 完整 Link 16 / NPG / relay / ACK / retransmission。
2. 完整 naval fire-control AI / CEC / engage-on-remote。
3. 完整海军 tasking state machine 与多舰编队 doctrine。
4. 全量 episode/json/schema 冗余消解。

## 关联文档

- [海战仿真现实性分析](../naval/naval_realism_analysis_20260516.zh.md)
- [传感器与态势感知现实性分析](../sensor_situation/sensor_situation_realism_analysis_20260516.zh.md)
- [武器系统与制导回路现实性分析](../weapon_guidance/weapon_guidance_realism_analysis_20260516.zh.md)

## 维护规则

1. 冻结分析继续保留原文件，不在原文中改写“当时判断”。
2. 当前状态只看本分析里的收口标记。
3. 如果后续需要新的状态快照，应新建文档，不要回写冻结分析。
