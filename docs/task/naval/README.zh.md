# 海军

状态：海军真实性工作线仍在活跃推进；N4 开火前 bridge 已于 `2026-05-25` 闭合。

## 当前状态

- 当前海军线已经从最小接触演示推进到具备海上运动、态势感知、局部武器链骨架和支援链雏形的战术原型。
- 最新状态总结应以 [海军当前进展追踪](./naval_current_progress_20260524.zh.md) 为准。
- 当前 N4 威胁/ROE bridge 已作为开火前场景与 active training-entry gate 闭合：
  [naval_n4_closure_20260525.zh.md](./n4_threat_roe_bridge/naval_n4_closure_20260525.zh.md)。
- 旧的 `2026-05-17` 进度检查点仍保留在归档中，用于追溯阶段性上下文。
- 该工作线仍然活跃，但当前重点是把已有海军命令链、传感器、runtime 和 RL/tasking 对接继续收口，而不是横向大规模扩功能。

## 推荐阅读顺序

- 当前进展追踪：
  [naval_current_progress_20260524.zh.md](./naval_current_progress_20260524.zh.md)
- 下一阶段场景扩大化子项目：
  [n4_threat_roe_bridge/README.zh.md](./n4_threat_roe_bridge/README.zh.md)
- N4 闭合：
  [n4_threat_roe_bridge/naval_n4_closure_20260525.zh.md](./n4_threat_roe_bridge/naval_n4_closure_20260525.zh.md)
- 归档索引：
  [archive/README.zh.md](./archive/README.zh.md)
- 历史规划/检查点材料已移入归档。

## 当前继续推进重点

- 将 `N4` 视为已闭合，避免为了 engagement 工作重新打开 N4
- 从两个 active N4 smoke/probe 条目继续推进：
  `naval_contact_report_threat_roe_v1` 和
  `naval_screen_station_hold_threat_aware_v1`
- 将有限武器交战继续放在独立 N5 package 与 opening gate 之后
- 将仍有业务含义的 loader-owned raw simulation compatibility seam 继续迁到 facade-owned maintained surface
- 补强 `MissionCommand -> naval weapon`、`screen-hold`、`tasking_profile: naval` 的 facade/world-batch 级守门
- 在扩展多舰队高保真海战前，优先稳住 maritime state、传感器/LOS、武器命令链和训练入口

较早的场景边界冻结快照和 backlog 现已转入 [archive/README.zh.md](./archive/README.zh.md)。
