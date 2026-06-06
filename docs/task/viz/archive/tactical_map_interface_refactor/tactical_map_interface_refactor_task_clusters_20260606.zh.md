# 战术地图界面重构任务簇

状态：`2026-06-06`，对应
[战术地图界面重构](README.zh.md) 的有限任务簇计划。`P0` 已通过；
`P1` 壳布局、`P2` 地图工作区、`P3` 图层/符号分组、`P4` profile defaults
和 `P5` 验证汇总已接受；`P6` closure/archive 同步已关闭。

## 边界决策

本子项目可以修改 `examples/viz` 的界面结构、战术地图图层呈现、地图工作区默认值、聚焦的 profile UI 默认值，以及验证这些变化所需的文档。它不得修改 scenario 真实性、环境 runtime 行为、地形机动、感知、火力、毁伤、奖励、终止逻辑，也不得声明军用符号标准合规。

战术地图可以演进为包含多个表面的工作区。这些表面是已接受 payload 之上的 UI 视图，不是新的仿真语义。

## 有限任务簇列表

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `VIZ-TMAP-P0` | main thread | n/a | 建立持久子项目权威、任务簇、当前状态和风格基线。 | `docs/task/viz/tactical_map_interface_refactor/**`、`docs/task/viz/README*.md` | Runtime UI 实现；scenario/profile schema 变更。 | `git diff --check -- docs/task/viz`；本地链接/路径检查。 | 父 README 已链接子项目，docs-only 校验干净。 | 首项，串行。 | 1 | pass |
| `VIZ-TMAP-P1` | main thread | n/a | 将当前战术 UI 重构为地图优先壳，控制区 dock/collapse。 | `examples/viz/web_viz/templates/index.html`；可选 dated evidence 截图路径 | 多地图语义；profile schema 变更；地形或战斗行为。 | 嵌入式 module 语法检查；窄屏/桌面浏览器 smoke；console 错误检查。 | 战术地图在第一视口中是主表面，控制区不再把地图顶出有用视野。 | 依赖 `P0`；若触及同一模板区域，与 `P2` 串行。 | 2 | accepted slice |
| `VIZ-TMAP-P2` | main thread 或 implementation worker | n/a | 增加维护中的地图工作区模型，包含 `COP`、`Environment`、`Tracks/Sensors`、`3D Inspect` 等具名表面。 | `examples/viz/web_viz/templates/index.html`；仅在默认值需要时可加 profile fixture | Scenario 编辑器；runtime 地形生成；新的仿真 payload 要求。 | 浏览器 smoke 证明地图表面切换或分屏行为；既有 profile 加载仍可用。 | 每个已接受表面都有清晰角色、默认图层集，且不会遮挡主地图。 | 依赖 `P1`；可与 `P3` 只读设计评审并行。 | 2 | accepted slice |
| `VIZ-TMAP-P3` | implementation worker 或 integration worker | n/a | 集中管理战术图层分组、绘制顺序和第一版符号风格。 | `examples/viz/web_viz/templates/index.html`；若本地证明合理，可少量抽出 JS/CSS | 完整 MIL-STD-2525/APP-6 合规；改变 tactical payload 语义。 | Module 语法检查；单元、路线、航迹、传感器、武器、ENV 图层截图检查。 | 现有叠加通过分组图层控制渲染，阵营、不确定性、环境样式可读。 | 依赖 `P1`；如写区重叠，可跟随 `P2`。 | 2 | accepted slice |
| `VIZ-TMAP-P4` | integration worker | n/a | 仅在需要时扩展 profile UI 默认值，用于默认 workspace/layer/view 选择。 | `examples/viz/app/profile_loader.py`、`examples/viz/profiles/*.json`、`tests/viz` 下聚焦测试 | Scenario schema 变更；训练配置变更；世界/真实性参数。 | 聚焦 profile-loader 测试和既有 viz smoke 加载。 | Profiles 可选择默认 UI 工作区/图层，而 scenarios 保持不变。 | 依赖已接受的 `P2` 或 `P3` 默认值。 | 2 | accepted slice |
| `VIZ-TMAP-P5` | main thread | n/a | 记录验证证据、截图、残余和能力边界。 | 本子项目下新增 dated acceptance/evidence 文档；如仓库保留截图则可加截图 artifacts | 新功能实现；验收前归档迁移。 | `P1`-`P4` 命令；Playwright 或浏览器 smoke 证据；触及文档/代码的 `git diff --check`。 | 证据足以脱离聊天历史判定 accepted、partial 或 held。 | 依赖实现任务簇。串行。 | 1 | accepted |
| `VIZ-TMAP-P6` | main thread | n/a | 验收决策后同步父 README、当前状态和 archive 指针。 | `docs/task/viz/README*.md`、本子项目 README/status/archive 文件 | 未开新任务簇而重启已接受实现；删除历史记录。 | 链接/路径检查；`git diff --check -- docs/task/viz`。 | 验收决策后当前权威和归档边界一致。 | 依赖 `P5`。串行。 | 1 | closed |

## 派发规则

- 每个 worker packet 必须精确映射到上表的一个 cluster。
- 本子项目不得创建新的会话线程。
- subagent 可选；如使用，必须遵循
  [Subagent 使用规范](../../../../standards/governance/subagent_usage_policy.zh.md)，
  并返回下方 worker packet 格式。
- 不允许两个 worker 同时编辑同一段 `index.html` 布局块、profile loader contract、公开状态行或验收表。
- `P5` 和 `P6` 保持 main thread 串行。
- 若某个 cluster 超出 round cap，应停止并重新划分范围，而不是追加一轮 wave。

## Worker Packet 要求

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## 验证计划

Docs-only `P0`：

```bash
git diff --check -- docs/task/viz
```

实现任务簇：

```bash
perl -0ne 'while (/<script\s+type="module"[^>]*>(.*?)<\/script>/sg) { print $1, "\n" }' examples/viz/web_viz/templates/index.html | node --input-type=module --check -
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/viz/test_environment_overlays.py tests/viz/test_tactical_map_workspace.py tests/viz/test_tactical_layer_model.py tests/viz/test_tactical_profile_ui_defaults.py
```

浏览器 smoke 至少覆盖：

- 接近 `780x493` 的窄屏视口；
- 接近 `1440x900` 的桌面视口；
- 一个会触发 tracks/sensors/weapons 的海军或空军 profile；
- 一个会触发 `ENV` overlay 可见性的陆军 scenario/profile 路径。

## 验收标准

- 第一版已接受实现必须让地图保持主视图，并修复“地图被控制区顶到下方”的失败模式。
- 即使只落地第一子集，也必须明确地图工作区模型。
- 图层控制按用途分组，并在窄屏和桌面视口都可用。
- 若加入 profile 默认值，它们必须是 UI/runtime 偏好，不得改写 scenario 世界语义。
- 没有代码和测试支撑时，不声明新的仿真行为。

## 残余地图

立即项：

- 当前 closed 子项目内没有立即任务。
- 如果后续工作触及同一模板或 profile-loader 结构，应开启新 cluster，并引用 `P1` 到 `P6` 证据作为基线。

后续项：

- 当道路、建筑、植被、天气或其他 derived products 被所属环境基底工作线验收后，再增加更丰富的环境图层。
- 如果分组图层绘制在当前模板中膨胀过大，再考虑可选的战术符号注册表。

推迟项：

- 军标级符号合规。
- Scenario 编辑器、地形生成器 UI 和环境 runtime 行为。
