# 海军

状态：海军真实性工作线仍在活跃推进；当前追踪入口更新于 `2026-05-24`。

## 当前状态

- 当前海军线已经从最小接触演示推进到具备海上运动、态势感知、局部武器链骨架和支援链雏形的战术原型。
- 最新状态总结应以 [海军当前进展追踪](./naval_current_progress_20260524.zh.md) 为准。
- 旧的 `2026-05-17` 进度检查点仍保留在归档中，用于追溯阶段性上下文。
- 该工作线仍然活跃，但当前重点是把已有海军命令链、传感器、runtime 和 RL/tasking 对接继续收口，而不是横向大规模扩功能。

## 推荐阅读顺序

- 当前进展追踪：
  [naval_current_progress_20260524.zh.md](./naval_current_progress_20260524.zh.md)
- 下一阶段场景扩大化子项目：
  [n4_threat_roe_bridge/README.zh.md](./n4_threat_roe_bridge/README.zh.md)
- 归档索引：
  [archive/README.zh.md](./archive/README.zh.md)
- 历史规划/检查点材料已移入归档。

## 当前继续推进重点

- 冻结一个最小海军 RL 任务入口，例如 `naval_screen_station_hold` 或 `naval_contact_report`
- 将 `N4` 威胁/ROE 桥接作为当前 `N1-N3` 屏护/接触 MVP 之后的第一个扩展，
  在有限武器交战前先补齐受威胁机动与授权态守门
- 将仍有业务含义的 loader-owned raw simulation compatibility seam 继续迁到 facade-owned maintained surface
- 补强 `MissionCommand -> naval weapon`、`screen-hold`、`tasking_profile: naval` 的 facade/world-batch 级守门
- 在扩展多舰队高保真海战前，优先稳住 maritime state、传感器/LOS、武器命令链和训练入口

较早的场景边界冻结快照和 backlog 现已转入 [archive/README.zh.md](./archive/README.zh.md)。
