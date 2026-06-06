# 战术地图界面重构派发队列

状态：`2026-06-06`，面向
[战术地图界面重构](README.zh.md) 的已闭合派发队列。`P0` 已通过；第一份
`P1` 只读 diagnostics packet 已返回 `pass`；主线程 `P1` 壳实现已作为切片接受；
主线程 `P2` tabbed workspace 实现已作为切片接受；主线程 `P3` 分组图层/符号实现已作为切片接受；
主线程 `P4` profile-default 实现已作为切片接受；`P5` 验证汇总已接受；`P6`
closure/archive 同步已关闭。

语言：

- 英文规范页：[tactical_map_interface_refactor_dispatch_queue_20260606.md](tactical_map_interface_refactor_dispatch_queue_20260606.md)
- 中文辅文：`tactical_map_interface_refactor_dispatch_queue_20260606.zh.md`

权威依据：

- [任务簇](tactical_map_interface_refactor_task_clusters_20260606.zh.md)
- [当前状态](tactical_map_interface_refactor_current_status_20260606.zh.md)
- [风格参考基线](tactical_map_interface_refactor_style_reference_baseline_20260606.zh.md)
- [Subagent 使用规范](../../../standards/governance/subagent_usage_policy.zh.md)

## 派发边界

本派发队列从 `VIZ-TMAP-P0` 权威复核开始，并开启第一份 `VIZ-TMAP-P1`
diagnostics packet。它不授权多个作者并发写
`examples/viz/web_viz/templates/index.html`。

第一份 packet 是只读的，因为 `P1`、`P2`、`P3` 都会触及同一个前端模板，必须在
diagnostics 返回后由主线程串行实施。

## 已应用规则

- 不创建新的会话线程。
- 复用当前可用的既有 subagent 做 diagnostics。
- 每个 packet 必须映射到有限任务簇计划中的一个命名 cluster。
- Diagnostics worker 不得编辑文件、回滚无关工作或声明仿真行为。
- 主线程拥有 implementation、integration、acceptance 和状态变更。
- worker packet 使用必需格式返回后，才可以成为 evidence。

## Dispatch Packets

| Packet | Cluster | Worker | Model / reasoning | Scope | Write set | Required return | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `VIZ-TMAP-P0-AUTH` | `VIZ-TMAP-P0` | main thread | 当前主线程 | 在派发前复核父 README 链接、任务簇、当前状态、风格基线和 docs-only validation。 | `docs/task/viz/tactical_map_interface_refactor/**`、`docs/task/viz/README*.md` | authority check；dirty-worktree boundary；validation outcome | pass |
| `VIZ-TMAP-P1-DIAG-A` | `VIZ-TMAP-P1` | `Carson` | inherited parent / diagnostics | 只读预检当前 `examples/viz` 战术壳和第一版地图优先布局实现边界。 | none | current layout map；exact edit surfaces；recommended first patch shape；responsive risks；validation commands；held capability claims | pass |
| `VIZ-TMAP-P1-IMPL-MAIN` | `VIZ-TMAP-P1` | main thread | 当前主线程 | 实现第一版地图优先战术壳，并验证窄屏、桌面、空军 profile、陆军 scenario 和 3D toggle smoke 路径。 | `examples/viz/web_viz/templates/index.html`、P1 验收文档 | worker-equivalent implementation summary；commands/outcomes；residuals；held capability claims | accepted slice |
| `VIZ-TMAP-P2-IMPL-MAIN` | `VIZ-TMAP-P2` | main thread | 当前主线程 | 将第一版维护中的地图工作区模型实现为 tabbed `COP`、`Environment`、`Tracks/Sensors`、`3D Inspect` 表面。 | `examples/viz/web_viz/templates/index.html`、`tests/viz/test_tactical_map_workspace.py`、P2 验收文档 | worker-equivalent implementation summary；commands/outcomes；residuals；held capability claims | accepted slice |
| `VIZ-TMAP-P3-IMPL-MAIN` | `VIZ-TMAP-P3` | main thread | 当前主线程 | 集中管理战术图层分组、绘制阶段和第一版符号样式，同时保持 tactical payload 语义不变。 | `examples/viz/web_viz/templates/index.html`、`tests/viz/test_tactical_layer_model.py`、P3 验收文档 | worker-equivalent implementation summary；commands/outcomes；residuals；held capability claims | accepted slice |
| `VIZ-TMAP-P4-IMPL-MAIN` | `VIZ-TMAP-P4` | main thread | 当前主线程 | 扩展 profile UI defaults，用于默认 tactical workspace/layer/view 选择，同时保持 scenario 语义不变。 | `examples/viz/app/profile_loader.py`、`examples/viz/profiles/*.json`、`examples/viz/web_viz/templates/index.html`、`tests/viz/test_tactical_profile_ui_defaults.py`、P4 验收文档 | worker-equivalent implementation summary；commands/outcomes；residuals；held capability claims | accepted slice |
| `VIZ-TMAP-P5-ROLLUP-MAIN` | `VIZ-TMAP-P5` | main thread | 当前主线程 | 汇总 `P1` 到 `P4` 的验证证据、截图、残余和能力边界。 | P5 验证汇总文档 | worker-equivalent validation summary；commands/outcomes；residuals；held capability claims | accepted |
| `VIZ-TMAP-P6-CLOSE-MAIN` | `VIZ-TMAP-P6` | main thread | 当前主线程 | 验收决策后同步父级/子项目状态和 archive 指针。 | 父级 viz README、子项目 README/status/task clusters/dispatch/archive 文档、P6 closure 文档 | closure decision；synchronized indexes；archive boundary；validation outcome | closed |

## 返回诊断摘要

`VIZ-TMAP-P1-DIAG-A` 返回 `pass`，并保持只读。

接受的实现指导：

- `VIZ-TMAP-P1` 保持为
  `examples/viz/web_viz/templates/index.html` 的单模板 patch。
- 保留既有 DOM IDs，避免破坏当前 JavaScript 更新路径。
- 保持 canvas/map workspace 为第一对象。
- 将 profile/scenario/asset selectors 收入可折叠左 dock。
- 将 telemetry、mission、unit list 和当前 layer controls 收入可折叠右 dock。
- 增加 dock state 和 collapse buttons，并在切换时刷新 tactical layout padding 与 redraw。
- workspace tabs/split maps 留给 `VIZ-TMAP-P2`。
- profile/workspace/layer defaults 留给 `VIZ-TMAP-P4`。

需要验证的主要风险：

- `780x493` 下 selectors 不能作为永久顶栏堆叠存在。
- docks collapse 后必须更新 `layoutState.tacticalPadding`。
- `updatePresentationModeUI()` 在 `3D` 模式下应隐藏地图表面，而不是破坏整个 shell。
- `#unit-list`、layer buttons 和 profile/session controls 必须保留现有事件路径。

## 返回实现摘要

`VIZ-TMAP-P1-IMPL-MAIN` 已作为切片接受。证据记录于
[P1 壳布局验收](tactical_map_interface_refactor_p1_shell_layout_acceptance_20260606.zh.md)。

接受的实现点：

- `#tactical-panel` 保持为第一视口 canvas 表面。
- `SETUP` 和 `DATA` docks 可折叠且响应式。
- 既有 ID 和事件路径被保留。
- 直接 scenario 加载现在显示 UI-only scenario-only profile 占位。
- 浏览器 smoke 覆盖窄屏、桌面、陆军 ENV、空军 weapons/trails、3D toggle、截图和最终
  `Errors: 0`。

在 `P1` 检查点，残余仍分配到 `P2`、`P3` 和 `P4`。

## 返回 P2 实现摘要

`VIZ-TMAP-P2-IMPL-MAIN` 已作为切片接受。证据记录于
[P2 工作区验收](tactical_map_interface_refactor_p2_workspace_acceptance_20260606.zh.md)。

接受的实现点：

- 第一版地图工作区模型采用 tabbed surfaces，而不是 split-map 布局。
- `COP`、`Environment`、`Tracks/Sensors`、`3D Inspect` 是显式 UI workspaces，并有默认图层姿态。
- Workspace tabs 保持在顶栏，因此进入 `3D Inspect` 后仍可回到地图工作区。
- 手动图层切换在当前浏览器会话内按 workspace 记忆。
- 静态回归覆盖 workspace IDs、tab controls、默认图层模型和 UI-only 边界。
- 浏览器 smoke 覆盖 workspace 切换、桌面和窄屏布局、地图像素采样、3D renderer 可见性、截图和最终
  `Errors: 0`。

在 `P2` 检查点，残余仍分配到 `P3` 和 `P4`。

## 返回 P3 实现摘要

`VIZ-TMAP-P3-IMPL-MAIN` 已作为切片接受。证据记录于
[P3 图层/符号验收](tactical_map_interface_refactor_p3_layer_symbology_acceptance_20260606.zh.md)。

接受的实现点：

- 战术图层集中到 `tacticalLayerCatalog`，包含 group、label、draw-order、button-ID 和 default-enabled 元数据。
- 右侧 dock 的 `LAYERS` 面板渲染 `ENVIRONMENT`、`MANEUVER`、`SENSORS` 和 `EFFECTS` 分组控制。
- 绘制阶段通过 `tacticalDrawPhases` 和 `isTacticalDrawPhaseEnabled()` 命名并按图层 gate。
- 第一版阵营、路线、数据链、track、环境、武器和标签样式集中在 `tacticalSymbology`。
- 静态回归锁定 catalog/group/draw-phase 结构和 UI-only 边界。
- 浏览器 smoke 覆盖分组图层控制、`COP`、`ENVIRONMENT`、`TRACKS`、`3D INSPECT` workspace 切换、截图证据和最终
  `Errors: 0`。

在 `P3` 检查点，残余只在需要持久化 profile UI defaults 时分配到 `P4`。

## 返回 P4 实现摘要

`VIZ-TMAP-P4-IMPL-MAIN` 已作为切片接受。证据记录于
[P4 profile-default 验收](tactical_map_interface_refactor_p4_profile_defaults_acceptance_20260606.zh.md)。

接受的实现点：

- Profile `ui` 现在可以声明 `tactical_workspace` 和 `tactical_layers`。
- `profile_loader.py` 规范化 workspace/layer aliases，并过滤未知或非布尔 layer 值。
- `index.html` 将 profile layer defaults 应用到所选 workspace 默认值之上，并记录为 workspace UI 状态。
- 既有 air/naval viz profiles 展示持久化 layer/workspace 默认值。
- Naval viz profiles 已对齐到维护中的 `naval_station3` 动作面，使 profile smoke load 可达到 `READY`。
- 静态回归锁定 profile loader contract、前端应用路径和 UI-only 边界。
- 浏览器 smoke 加载 naval contact-report profile，达到 `READY`，应用 `TRACKS`，最终 `Errors: 0`。

## 返回 P5 验证摘要

`VIZ-TMAP-P5-ROLLUP-MAIN` 已接受。证据记录于
[P5 验证汇总](tactical_map_interface_refactor_p5_validation_rollup_20260606.zh.md)。

接受的验证点：

- `P1` 到 `P4` 的浏览器 smoke、截图、console 检查和残余边界被整理到单一汇总。
- 新的代码面复核通过 embedded module 语法、聚焦 viz pytest 和 profile JSON 解析。
- `P5` 只改文档，不改变 runtime code，因此浏览器证据继续来自已接受切片文档。
- 本子项目内的立即实现残余已闭合；更丰富的环境产品、split-map 布局和 symbol registry 抽取保持为后续工作。

## 返回 P6 收口摘要

`VIZ-TMAP-P6-CLOSE-MAIN` 已关闭。证据记录于
[P6 closure/archive sync](tactical_map_interface_refactor_p6_closure_archive_sync_20260606.zh.md)。

接受的收口点：

- 父级 viz README、子项目 README、当前状态、任务簇、派发队列和 archive README 已一致表明本 scoped
  refactor 为 `closed`。
- 没有本地证据文件被移动到 `archive/`；dated acceptance 和 closure 文档仍是 live evidence。
- 未来战术可视化工作应开启新的任务簇或子项目。

## Worker Packet 模板

```md
status: pass | partial | blocked | failed
touched files: none expected for diagnostics
files inspected:
commands/outcomes:
current layout map:
recommended first patch shape:
responsive risks:
behavior risks:
explicit held capability claims:
integration notes:
```

## 验收边界

`VIZ-TMAP-P1-DIAG-A` 只有在保持只读、映射当前 repo 文件，并拒绝地形感知机动、
LOS、掩蔽、感知、火力、毁伤、战斗、scenario 编辑、地形生成器 UI 和军标合规声明时，才能支撑实现规划。

diagnostics packet 本身没有把 shell layout 标记为 accepted。`P1` 的 accepted 决策来自后续
主线程实现和上方浏览器证据 packet。
