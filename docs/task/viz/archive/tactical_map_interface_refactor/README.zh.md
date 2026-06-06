# 战术地图界面重构

状态：`2026-06-06`，已闭合的可视化子项目。`P0` 规划与参考基线已建立；
`P1` 壳布局、`P2` 地图工作区、`P3` 图层/符号分组、`P4` profile integration
和 `P5` 验证汇总已接受；`P6` closure/archive 同步已完成。

语言：

- 英文规范页：[README.md](README.md)
- 中文辅文：`README.zh.md`

输入：

- 父任务域：[可视化](../../README.zh.md)
- 子项目格式规则：
  [面向 Agent 的子项目创建标准](../../../../agent/rules/subproject_creation_standard.zh.md)
- 委派规则：
  [Subagent 使用规范](../../../../standards/governance/subagent_usage_policy.zh.md)
- 既有统一入口权威：
  [viz_unified_entry_session_profile_plan_20260516.zh.md](../viz_unified_entry_session_profile_plan_20260516.zh.md)
- 当前前端壳：
  [index.html](../../../../../examples/viz/web_viz/templates/index.html)
- 当前 profile/session 层：
  [profile_loader.py](../../../../../examples/viz/app/profile_loader.py)、
  [viz_session.py](../../../../../examples/viz/runtime/viz_session.py)
- 已验收的 G0 环境可视化叠加面：
  [environment_substrate_g0_viz_overlay_sync_acceptance_20260606.zh.md](../../../ground/environment_substrate_g0_architecture/environment_substrate_g0_viz_overlay_sync_acceptance_20260606.zh.md)
- 本地风格/参考基线：
  [tactical_map_interface_refactor_style_reference_baseline_20260606.zh.md](tactical_map_interface_refactor_style_reference_baseline_20260606.zh.md)

## 目的

本子项目把当前 `examples/viz` 的战术显示从偏调试的单地图叠加界面，推进为以地图为第一对象的态势界面。近期目标是让战术地图始终占据主要视野，控制面板可折叠，并允许场景需要时使用不止一张地图。

这项工作位于已接受的统一入口/profile/session 基础之上。它不推翻 app、session、profile、asset registry 等层，而是在这些层上新增维护中的界面和地图工作区计划。

## 当前状态

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| 统一可视化入口 | 活跃基础，已记录第一版可用收口 | [viz_unified_entry_session_profile_plan_20260516.zh.md](../viz_unified_entry_session_profile_plan_20260516.zh.md) | 这不等于已解决战术地图布局或多地图工作区。 |
| 当前战术地图 | `P1` 地图优先壳已作为切片接受 | [P1 验收](tactical_map_interface_refactor_p1_shell_layout_acceptance_20260606.zh.md) | 这里只接受 dock/collapse 布局，不接受图层分组或 profile 默认值。 |
| G0 环境叠加 | 已验收的“仅可视化”切片 | [environment_substrate_g0_viz_overlay_sync_acceptance_20260606.zh.md](../../../ground/environment_substrate_g0_architecture/environment_substrate_g0_viz_overlay_sync_acceptance_20260606.zh.md) | 这里只是绘制元数据，不释放地形机动、LOS、遮蔽或战斗行为。 |
| 多地图工作区 | `P2` tabbed workspace 已作为切片接受 | [P2 验收](tactical_map_interface_refactor_p2_workspace_acceptance_20260606.zh.md) | 这里只接受具名 UI 表面和默认图层姿态，不接受 split-map 布局或新的仿真语义。 |
| 战术图层模型 | `P3` 分组图层/符号切片已接受 | [P3 验收](tactical_map_interface_refactor_p3_layer_symbology_acceptance_20260606.zh.md) | 这里只接受 catalog 化 UI 图层控制和第一版样式，不接受军标合规或新的 payload 语义。 |
| Profile UI 默认值 | `P4` profile-default 切片已接受 | [P4 验收](tactical_map_interface_refactor_p4_profile_defaults_acceptance_20260606.zh.md) | 这里只接受 profile 选择的 workspace/layer/view UI 默认值，不接受 scenario 或仿真语义。 |
| 验证汇总 | `P5` 已接受 | [P5 验证汇总](tactical_map_interface_refactor_p5_validation_rollup_20260606.zh.md) | 这里只汇总证据和边界，不新增 runtime 功能。 |
| Closure/archive 同步 | `P6` 已关闭 | [P6 closure/archive sync](tactical_map_interface_refactor_p6_closure_archive_sync_20260606.zh.md) | 这只关闭当前 scoped refactor，不代表所有未来战术可视化想法完成。 |
| 战术地图风格基线 | `P0` 已通过 | [风格基线](tactical_map_interface_refactor_style_reference_baseline_20260606.zh.md) | 参考资料只指导视觉设计，不构成军标合规声明。 |

## 范围

范围内：

- 围绕地图优先布局重构 `examples/viz` 战术 UI。
- 定义多地图工作区模型，至少覆盖 `COP`、`Environment`、`Tracks/Sensors`、`3D Inspect` 等表面。
- 将图层控制迁移为分组、可折叠、响应式的 UI 面。
- 增加战术图层/符号模型，避免绘制规则继续散落在无关 UI 逻辑中。
- 保持 `profile` 与 `scenario` 的边界：profile 可以选择默认视图、工作区和 UI 图层开关；scenario 仍然是仿真内容和世界语义。
- 使用浏览器 smoke 和截图验证窄屏、桌面视口。

范围外：

- 完整 MIL-STD-2525、APP-6 或其他实战标准合规。
- 地形感知机动、可通行性、LOS、掩蔽/隐蔽、感知、火力、毁伤、奖励或终止逻辑。
- scenario 编辑器或 runtime 地形生成器 UI。
- 除非后续任务簇证明当前模板无法承载验收设计，否则不把 `examples/viz` 重写为新的前端框架。
- 本子项目不得创建新的会话线程。可使用 subagent，但必须遵守既有项目治理，并输出绑定到下方有限任务簇的 worker packet。

## 阶段计划

| 阶段 | 目标 | 进入条件 | 退出条件 | 状态 |
| --- | --- | --- | --- | --- |
| `P0 Boundary And Reference` | 建立子项目、任务簇、当前状态和地图风格基线。 | 用户要求在 `docs/task/viz` 建立持久工作面。 | 父 README 已链接本子项目，docs-only 校验干净。 | pass |
| `P1 Shell Layout` | 将当前 UI 重构为地图优先的战术壳。 | `P0` 通过。 | 窄屏和桌面中地图都是第一视口的主表面。 | accepted slice |
| `P2 Map Workspace Model` | 增加多个具名地图表面和切换/分屏行为。 | `P1` 壳可以承载地图面板。 | `COP`、`Environment`、`Tracks/Sensors`、`3D Inspect` 均有明确 UI 角色。 | accepted slice |
| `P3 Layer And Symbology Model` | 集中管理图层分组、绘制顺序和战术符号风格。 | `P2` 工作区存在。 | 现有叠加层通过分组图层规则渲染，且不扩大能力声明。 | accepted slice |
| `P4 Profile Integration` | 让 profile 能选择默认工作区/图层，但不改变 scenario 语义。 | `P2` 和 `P3` 足够稳定。 | profile loader 接受并校验地图工作区 UI 默认值。 | accepted slice |
| `P5 Validation Evidence` | 记录浏览器、语法和回归证据。 | 实现任务簇通过本地检查。 | 证据文档记录截图、console 状态和残余。 | accepted |
| `P6 Closure And Archive Sync` | 判定 accepted/held/下一切片状态并同步索引。 | `P5` 证据完整。 | README/status/archive 当前权威一致。 | closed |

## 任务簇

- 有限任务簇计划：
  [tactical_map_interface_refactor_task_clusters_20260606.zh.md](tactical_map_interface_refactor_task_clusters_20260606.zh.md)
- 派发队列：
  [tactical_map_interface_refactor_dispatch_queue_20260606.zh.md](tactical_map_interface_refactor_dispatch_queue_20260606.zh.md)
- P1 壳布局验收：
  [tactical_map_interface_refactor_p1_shell_layout_acceptance_20260606.zh.md](tactical_map_interface_refactor_p1_shell_layout_acceptance_20260606.zh.md)
- P2 工作区验收：
  [tactical_map_interface_refactor_p2_workspace_acceptance_20260606.zh.md](tactical_map_interface_refactor_p2_workspace_acceptance_20260606.zh.md)
- P3 图层/符号验收：
  [tactical_map_interface_refactor_p3_layer_symbology_acceptance_20260606.zh.md](tactical_map_interface_refactor_p3_layer_symbology_acceptance_20260606.zh.md)
- P4 profile-default 验收：
  [tactical_map_interface_refactor_p4_profile_defaults_acceptance_20260606.zh.md](tactical_map_interface_refactor_p4_profile_defaults_acceptance_20260606.zh.md)
- P5 验证汇总：
  [tactical_map_interface_refactor_p5_validation_rollup_20260606.zh.md](tactical_map_interface_refactor_p5_validation_rollup_20260606.zh.md)
- P6 closure/archive sync：
  [tactical_map_interface_refactor_p6_closure_archive_sync_20260606.zh.md](tactical_map_interface_refactor_p6_closure_archive_sync_20260606.zh.md)

## 输出与证据

已维护输出：

- 更新后的 `examples/viz/web_viz/templates/index.html` 战术壳和地图工作区实现。
- 如果扩展 profile UI 默认值，则增加聚焦的 profile-loader 测试。
- 窄屏和桌面地图布局的浏览器 smoke 截图。
- 嵌入式 module script 语法检查，以及触及 profile/session 面时的 Python 检查。
- 上方 `P1` 到 `P6` 记录中的验收和收口证据。

## 验收门

本子项目标记为 accepted 并 closed，依据是：

- 战术地图在至少一个窄屏视口和一个桌面视口中保持可见并作为主表面。
- 界面支持多个地图表面，或明确记录了 workspace model 的第一版已接受子集。
- 图层控制已经分组且响应式，不会把地图顶出有用的第一视口。
- 既有海军、空军、陆军 smoke profile 仍可加载，且没有由本重构引入的浏览器 console 错误。
- profile 默认值仍然是可视化/runtime UI 偏好，不会改写 scenario 真实性或世界参数。
- 文档继续拒绝未实现、未测试的军标合规和仿真行为声明。

## 残余与下一步

立即项：

- 当前 closed 子项目内没有立即工作。

后续项：

- 在通用环境基底释放已验收 derived products 后，再增加更丰富的地形、建筑、道路、植被图层渲染。
- 当当前模板中的图层模型证明有价值后，考虑专门的战术符号注册表。
- 如果后续需要 split-map 布局或大型前端抽取，应开启新的任务簇或子项目。

推迟项：

- 军标级符号合规。
- scenario 编辑、地形生成器 UI 和环境 runtime 行为。

## 归档

Post-closeout archive note：本子项目闭合后，完整包已移动到父级 viz archive：
[../tactical_map_interface_refactor/](../tactical_map_interface_refactor/README.zh.md)。
嵌套的 [archive/README.zh.md](archive/README.zh.md) 继续保留给这个 archived package
内部未来被取代的记录。
