# 海军

状态：海军真实性工作线仍在活跃推进；N4 开火前 bridge 已于 `2026-05-25`
闭合，N4 RL action/observation surface 修复已于 `2026-05-27` 落地。

## 当前状态

- 当前海军线已经从最小接触演示推进到具备海上运动、态势感知、局部武器链骨架和支援链雏形的战术原型。
- 最新状态总结应以 [海军当前进展追踪](./naval_current_progress_20260524.zh.md) 为准。
- N4 威胁/ROE bridge 已作为开火前场景与 active training-entry gate 闭合。原任务路径现在只保留轻量指针；
  完整 closure/evidence package 位于
  [archive/archive/n4_threat_roe_bridge/](./archive/archive/n4_threat_roe_bridge/README.zh.md)：
  [naval_n4_closure_20260525.zh.md](./archive/archive/n4_threat_roe_bridge/naval_n4_closure_20260525.zh.md)。
- RL action/observation surface split 已实现，并保留为已接受的 N4 training-entry repair 记录。
  原任务路径现在只保留轻量指针；完整 packet 位于
  [archive/archive/n5_rl_action_surface_split/](./archive/archive/n5_rl_action_surface_split/README.zh.md)：
  [naval_n5_rl_action_surface_split_cluster_20260526.zh.md](./archive/archive/n5_rl_action_surface_split/naval_n5_rl_action_surface_split_cluster_20260526.zh.md)。
  尽管目录名带 `N5`，它当前是 N4 pre-fire training-entry repair，不是 N5 武器
  交战释放。新的海军 surface-split 工作应继续进入下面的 domain-surface split package。
- 当前领域执行面拆分追踪于
  [naval_domain_surface_split/README.zh.md](./naval_domain_surface_split/README.zh.md)。
  它会在打开任何 N5/N6 声明前，继续把 maintained naval action、command、observation
  和配置表面从 air-first compatibility carrier 中拆出。
- 旧的 `2026-05-17` 进度检查点仍保留在归档中，用于追溯阶段性上下文。
- 该工作线仍然活跃，但当前重点是把已有海军命令链、传感器、runtime 和 RL/tasking 对接继续收口，而不是横向大规模扩功能。

## 当前入口

- 当前进展追踪：
  [naval_current_progress_20260524.zh.md](./naval_current_progress_20260524.zh.md)
- 当前领域执行面拆分续作：
  [naval_domain_surface_split/README.zh.md](./naval_domain_surface_split/README.zh.md)
- 归档索引：
  [archive/README.zh.md](./archive/README.zh.md)
- 历史规划/检查点材料已移入归档。

## 已闭合 / 保留记录

以下记录已经闭合或接受。它们通过本节保持可追溯、可供测试和 gate 检查引用，但不再作为
新的 active 子项目入口使用。

- 已闭合的 N4 场景扩大化子项目：
  [archive/n4_threat_roe_bridge/README.zh.md](./archive/n4_threat_roe_bridge/README.zh.md)
- N4 闭合记录：
  [archive/archive/n4_threat_roe_bridge/naval_n4_closure_20260525.zh.md](./archive/archive/n4_threat_roe_bridge/naval_n4_closure_20260525.zh.md)
- 已实现的 N4 RL action/observation repair，尽管目录名带 `N5`：
  [archive/n5_rl_action_surface_split/README.zh.md](./archive/n5_rl_action_surface_split/README.zh.md)
  与
  [archive/archive/n5_rl_action_surface_split/README.zh.md](./archive/archive/n5_rl_action_surface_split/README.zh.md)

## 当前继续推进重点

- 将 `N4` 视为已闭合，避免为了 engagement 工作重新打开 N4
- 从 active N4 smoke/probe 条目继续推进：
  `naval_contact_report_threat_roe_v1`、
  `naval_screen_station_hold_threat_aware_v1` 和
  `naval_screen_station_recovery_threat_aware_v1`
- 让这些入口保持在专门的 `naval_station3` 站位指令动作面，而不是空军
  `takeoff4` 训练面
- 让这些入口的策略任务输入保持在 `naval_screen_station_v1`，而不是空军
  formation-role 观测面
- 继续拆分剩余 air-first compatibility carrier：中性 `PilotAction` transport、flat
  `MissionCommand` 聚合、Python-owned naval mission observation fallback，以及
  air-labeled backend 配置名
- 将有限武器交战继续放在独立 N5 package 与 opening gate 之后
- 将仍有业务含义的 loader-owned raw simulation compatibility seam 继续迁到 facade-owned maintained surface
- 补强 `MissionCommand -> naval weapon`、`screen-hold`、`tasking_profile: naval` 的 facade/world-batch 级守门
- 在扩展多舰队高保真海战前，优先稳住 maritime state、传感器/LOS、武器命令链和训练入口

较早的场景边界冻结快照和 backlog 现已转入 [archive/README.zh.md](./archive/README.zh.md)。

已归档子项目的完整清单见 [归档注册表](archive_registry.zh.md)。
