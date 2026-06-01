# 可视化

状态：统一入口重构工作线仍在活跃推进；局部入口已于 `2026-05-18` 收敛。

## 当前状态

- 原来的大体量设计/冻结文档仍然是当前主记录；虽然它位于 `archive/` 下，
  但本 README 明确提升它作为当前入口。
- 计划文档已经记录了统一入口工作流的第一版可用收口，尤其是 `WP-V4` 资产注册表和 `WP-V5` 应用内加载/会话流。
- 后续默认重点已经不再是重新设计整体架构，而是在已落地结构上扩展 registry 覆盖范围，并清理 runtime 退出与重复调试流程噪音。

## 推荐阅读顺序

- 活跃计划与当前实现边界：
  [viz_unified_entry_session_profile_plan_20260516.zh.md](./archive/viz_unified_entry_session_profile_plan_20260516.zh.md)

## 当前继续推进重点

- 扩展更多已验证海空资产的 asset registry 覆盖
- 清理 runtime 退出路径和重复会话调试噪音
- 继续保持“可视化便利性”和“真实性/世界参数”分层
- 除非本 README 明确提升，不要把 `archive/` 下其他文件当作 active 入口

较早的大体量冻结/设计快照现已转入 [archive/README.zh.md](./archive/README.zh.md)。
