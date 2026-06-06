# 战术地图界面重构当前状态

状态：`2026-06-06`，`P0` 已通过，`P1` 壳布局已作为切片接受，`P2` 地图工作区已作为切片接受，`P3` 图层/符号分组计划为下一步。

父项：[战术地图界面重构](README.zh.md)

## 本检查点变化

- 在 `docs/task/viz` 下创建战术地图界面重构的持久子项目。
- 增加有限任务簇计划，避免未来 UI 工作只依赖聊天中的追加要求。
- 增加现实战术地图、GIS、COP、OSINT 呈现的风格/参考基线，但不声明标准合规。
- 将本子项目挂回 viz 父 README。
- 开启第一份派发队列，并把 `VIZ-TMAP-P1-DIAG-A` 作为 runtime 实现前的只读
  preflight packet 分发出去。
- 接受 `VIZ-TMAP-P1-DIAG-A` 为 diagnostics-only `pass`。
- 在 [index.html](../../../../examples/viz/web_viz/templates/index.html) 中实现并接受
  `VIZ-TMAP-P1` 地图优先壳布局。
- 增加可折叠 `SETUP` 与 `DATA` docks，同时保留既有
  profile/scenario/asset/run/layer/telemetry/unit DOM ID。
- 增加 UI-only scenario-only profile 占位，避免直接加载 scenario 时界面误显第一个 profile 正在生效。
- 在 [P1 壳布局验收](tactical_map_interface_refactor_p1_shell_layout_acceptance_20260606.zh.md)
  中记录 P1 浏览器、语法和聚焦 overlay 证据。
- 在 [index.html](../../../../examples/viz/web_viz/templates/index.html) 中实现并接受
  `VIZ-TMAP-P2` tabbed 地图工作区模型。
- 增加 `COP`、`Environment`、`Tracks/Sensors`、`3D Inspect` 表面，并为它们记录明确 UI 角色和默认图层姿态。
- 增加聚焦静态覆盖：
  [test_tactical_map_workspace.py](../../../../tests/viz/test_tactical_map_workspace.py)。
- 在 [P2 工作区验收](tactical_map_interface_refactor_p2_workspace_acceptance_20260606.zh.md)
  中记录 P2 浏览器、语法和聚焦回归证据。

## 成熟度矩阵

| 表面 | 状态 | 证据 | 残余 |
| --- | --- | --- | --- |
| 子项目权威 | pass | [README.zh.md](README.zh.md) | 实现开始后需要继续保持当前。 |
| 任务簇 | pass | [任务簇](tactical_map_interface_refactor_task_clusters_20260606.zh.md) | 派发必须保持在有限任务簇和 round cap 内。 |
| 风格/参考基线 | pass | [风格基线](tactical_map_interface_refactor_style_reference_baseline_20260606.zh.md) | 接受 UI 声明前仍需实现证据。 |
| Runtime 壳布局 | accepted slice | [P1 验收](tactical_map_interface_refactor_p1_shell_layout_acceptance_20260606.zh.md) | 不接受图层分组、profile 默认值或新的仿真行为。 |
| 多地图工作区 | accepted slice | [P2 验收](tactical_map_interface_refactor_p2_workspace_acceptance_20260606.zh.md) | 只接受 tabbed surfaces；split-map 布局仍推迟。 |
| Profile UI 默认值 | planned/held until needed | [profile_loader.py](../../../../examples/viz/app/profile_loader.py) | 只有 `P3` 图层默认值稳定到值得持久化后才添加。 |

## 下一步推荐顺序

1. 在 `VIZ-TMAP-P3` 增加分组图层/符号规则。
2. 只有当 runtime UI 需要稳定持久默认值时，才在 `VIZ-TMAP-P4` 扩展 profile UI 默认值。
3. 随后续实现切片落地，在 `VIZ-TMAP-P5` 记录浏览器 smoke、截图和残余。

## 明确拒绝的过度声明

- 本检查点没有接受完整战术地图界面重构。
- 本检查点只接受第一版 tabbed map-workspace 切片；不接受 split-map 布局。
- 本检查点没有证明军用符号标准合规。
- 本检查点没有释放地形感知机动、LOS、掩蔽、可通行性、天气效果、战斗行为或环境 runtime 变异。
- 本检查点没有改变 scenario/profile 边界。
