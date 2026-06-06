# 战术地图界面重构当前状态

状态：`2026-06-06`，已闭合。`P0` 已通过；`P1` 壳布局、`P2` 地图工作区、`P3`
图层/符号分组、`P4` profile UI 默认值和 `P5` 验证汇总已接受；`P6` closure/archive
同步已完成。

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
- 在 [index.html](../../../../examples/viz/web_viz/templates/index.html) 中实现并接受
  `VIZ-TMAP-P3` 分组战术图层控制、集中绘制阶段和第一版符号样式。
- 增加聚焦静态覆盖：
  [test_tactical_layer_model.py](../../../../tests/viz/test_tactical_layer_model.py)。
- 在 [P3 图层/符号验收](tactical_map_interface_refactor_p3_layer_symbology_acceptance_20260606.zh.md)
  中记录 P3 浏览器、语法和聚焦回归证据。
- 在 [profile_loader.py](../../../../examples/viz/app/profile_loader.py) 和
  [index.html](../../../../examples/viz/web_viz/templates/index.html) 中实现并接受
  `VIZ-TMAP-P4` profile UI 默认值，用于默认 tactical workspace 和 layer 选择。
- 增加聚焦 profile/default 回归覆盖：
  [test_tactical_profile_ui_defaults.py](../../../../tests/viz/test_tactical_profile_ui_defaults.py)。
- 更新 viz profile fixtures，使空战 forced-fire profile 可持久化完整 COP 图层默认值，海军 contact-report profile
  可默认进入 `TRACKS` workspace。
- 将 naval viz profiles 对齐到维护中的 `naval_station3` 动作面，使 profile smoke load 可达到 `READY`。
- 在 [P4 profile-default 验收](tactical_map_interface_refactor_p4_profile_defaults_acceptance_20260606.zh.md)
  中记录 P4 浏览器、语法、JSON 和聚焦回归证据。
- 接受 `VIZ-TMAP-P5` 为 `P1` 到 `P4` 的证据汇总，其中包括新的 module 语法、聚焦 pytest
  和 profile JSON 验证，记录于
  [P5 验证汇总](tactical_map_interface_refactor_p5_validation_rollup_20260606.zh.md)。
- 接受 `VIZ-TMAP-P6` 为 closure/archive 同步切片，记录于
  [P6 closure/archive sync](tactical_map_interface_refactor_p6_closure_archive_sync_20260606.zh.md)。
- 已同步父级 viz README、本 README/status、任务簇、派发队列和 archive 指针，因此当前 scoped
  refactor 已为 `closed`。

## 成熟度矩阵

| 表面 | 状态 | 证据 | 残余 |
| --- | --- | --- | --- |
| 子项目权威 | closed | [README.zh.md](README.zh.md) | 当前权威已由 `P6` 同步；未来工作需要新 cluster。 |
| 任务簇 | closed | [任务簇](tactical_map_interface_refactor_task_clusters_20260606.zh.md) | `P0` 到 `P6` 已完成；新工作不应重开本队列。 |
| 风格/参考基线 | pass | [风格基线](tactical_map_interface_refactor_style_reference_baseline_20260606.zh.md) | 参考资料只指导风格，不构成标准合规声明。 |
| Runtime 壳布局 | accepted slice | [P1 验收](tactical_map_interface_refactor_p1_shell_layout_acceptance_20260606.zh.md) | 不接受图层分组、profile 默认值或新的仿真行为。 |
| 多地图工作区 | accepted slice | [P2 验收](tactical_map_interface_refactor_p2_workspace_acceptance_20260606.zh.md) | 只接受 tabbed surfaces；split-map 布局仍推迟。 |
| 图层和符号模型 | accepted slice | [P3 验收](tactical_map_interface_refactor_p3_layer_symbology_acceptance_20260606.zh.md) | 只接受分组 UI 控制和第一版样式；不声明标准合规或 payload 语义。 |
| Profile UI 默认值 | accepted slice | [P4 验收](tactical_map_interface_refactor_p4_profile_defaults_acceptance_20260606.zh.md) | 只接受 UI 偏好；不改变 scenario 或仿真语义。 |
| 验证汇总 | accepted | [P5 验证汇总](tactical_map_interface_refactor_p5_validation_rollup_20260606.zh.md) | 只汇总证据；不新增 runtime 功能。 |
| Closure/archive 同步 | closed | [P6 closure/archive sync](tactical_map_interface_refactor_p6_closure_archive_sync_20260606.zh.md) | 只关闭当前 scoped refactor；未来战术可视化工作需要新 cluster。 |

## 下一步推荐顺序

1. 将本战术地图界面重构视为已闭合。
2. 若要推进更丰富的环境 derived layers、split-map 布局、symbol registry 抽取或其他未来战术可视化工作，
   开启新的任务簇或子项目。

## 明确拒绝的过度声明

- 本次收口只接受 `P1` 到 `P6` 记录的 scoped 第一版战术地图界面重构；不接受所有未来战术可视化想法。
- 本次收口不接受 split-map 布局。
- 本次收口没有证明军用符号标准合规。
- 本次收口没有释放地形感知机动、LOS、掩蔽、可通行性、天气效果、战斗行为或环境 runtime 变异。
- 本次收口没有改变 scenario/profile 边界。
