# 可视化

状态：统一入口重构工作线仍在活跃推进；局部入口已于 `2026-05-18` 收敛；战术地图界面重构已于
`2026-06-06` 闭合并归档。

## 当前状态

- 原来的大体量设计/冻结文档仍然是当前主记录；虽然它位于 `archive/` 下，
  但本 README 明确提升它作为当前入口。
- 计划文档已经记录了统一入口工作流的第一版可用收口，尤其是 `WP-V4` 资产注册表和 `WP-V5` 应用内加载/会话流。
- 后续默认重点已经不再是重新设计整体架构，而是在已落地结构上扩展 registry 覆盖范围，并清理 runtime 退出与重复调试流程噪音。
- 战术地图界面重构现在是已归档的第一切片：地图优先壳、tabbed workspaces、分组战术图层、
  profile UI 默认值，以及验证/收口证据，都在文档边界内接受。原路径只保留轻量 pointer；
  完整包位于
  [archive/tactical_map_interface_refactor/](./archive/tactical_map_interface_refactor/README.zh.md)。

## 推荐阅读顺序

- 活跃计划与当前实现边界：
  [viz_unified_entry_session_profile_plan_20260516.zh.md](./archive/viz_unified_entry_session_profile_plan_20260516.zh.md)
- 战术地图界面重构 pointer：
  [tactical_map_interface_refactor/README.zh.md](./tactical_map_interface_refactor/README.zh.md)
- 已归档的战术地图界面证据包：
  [archive/tactical_map_interface_refactor/README.zh.md](./archive/tactical_map_interface_refactor/README.zh.md)
- 活跃的纯地图查看 follow-on：
  [map_only_viewer_mode/README.zh.md](./map_only_viewer_mode/README.zh.md)
- 活跃的环境 overlay 可视元素 follow-on：
  [environment_overlay_visual_elements/README.zh.md](./environment_overlay_visual_elements/README.zh.md)
- 活跃的双语显示 follow-on：
  [bilingual_display/README.zh.md](./bilingual_display/README.zh.md)

## 当前继续推进重点

- 将已归档的战术地图界面重构作为统一入口/profile/session 基础上的当前地图优先 UI 基线
- 扩展更多已验证海空资产的 asset registry 覆盖
- 清理 runtime 退出路径和重复会话调试噪音
- 继续保持“可视化便利性”和“真实性/世界参数”分层
- 若要加入更丰富环境图层、split-map 布局或 symbol registry 抽取，先开启新的任务簇或子项目
- 纯地图查看和 profile/object-binding 工作从
  [map_only_viewer_mode/README.zh.md](./map_only_viewer_mode/README.zh.md) 继续
- generated environment overlay 的可读性增强从
  [environment_overlay_visual_elements/README.zh.md](./environment_overlay_visual_elements/README.zh.md) 继续
- 中英双语 UI 显示从
  [bilingual_display/README.zh.md](./bilingual_display/README.zh.md) 继续
- 除非本 README 明确提升，不要把 `archive/` 下其他文件当作 active 入口

较早的大体量冻结/设计快照现已转入 [archive/README.zh.md](./archive/README.zh.md)。
