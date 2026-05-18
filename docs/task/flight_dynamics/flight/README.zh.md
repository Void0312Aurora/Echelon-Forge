# 飞行动力学子项目

语言版本：

- 英文主文：[README.md](README.md)
- 中文辅文：`README.zh.md`

状态：`2026-05-18` `P0/P1` 文档骨架已形成；当前口径以分析文档中的收口标记为准，而不是 `program/` 或 `archive/`。

本子项目收纳飞行动力学、推进、气动参数、失速/高攻角恢复及其相关验收口径文档。

## 文档入口

- [飞行动力学现实性分析与空战前置门槛](flight_dynamics_realism_analysis_20260516.zh.md)
  作用：冻结记录当前失真点、空战前置门槛和分析依据。
- [归档的飞行动力学真实化 P0 实施包](../archive/flight/flight_dynamics_realism_p0_implementation_package_20260516.zh.md)
  作用：已归档的最小气动/推进/失速骨架首轮实施范围。
- [归档的飞行动力学真实化 P1 实施包](../archive/flight/flight_dynamics_realism_p1_implementation_package_20260517.zh.md)
  作用：已归档的数据库驱动、推进瞬态、压缩性和高 AoA 语义后续任务。

## 当前阅读顺序

1. 先看本目录的 `analysis` 与其 `2026-05-18` 收口标记。
2. 需要追溯“为什么当时这样做”时，再回看 `analysis` 正文。

## 维护约定

1. 新的飞行动力学调研、标定说明和数据来源说明优先放在本目录。
2. 若后续拆出更细的机型或数据子项目，应继续在 `flight/` 下分层，而不是回到上层平铺。
