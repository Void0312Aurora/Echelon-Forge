# 纯地图查看模式 P1 验收

状态：`2026-06-06`，`VIZ-MAPONLY-P1` 作为 UI-only viewer 切片接受。
父级 follow-on 仍保持活跃，用于后续 profile/object-binding 设计。

父项：[纯地图查看模式与 Profile 绑定后续项](README.zh.md)

英文规范页：
[map_only_viewer_mode_p1_acceptance_20260606.md](map_only_viewer_mode_p1_acceptance_20260606.md)

## 决策

`VIZ-MAPONLY-P1` 接受为战术地图查看器切片。

已接受实现：

- 在现有 viz 顶栏增加显式 `MAP ONLY` action；
- 纯地图模式隐藏顶栏、setup dock、data dock 和 help overlay，同时保留 tactical canvas；
- 纯地图模式保留小型 `EXIT MAP` 控件；
- `Escape` 可退出纯地图模式；
- profile `ui.map_only` 可作为 UI 偏好设置初始查看姿态；
- 从 `3D Inspect` 进入纯地图时，先回到最近的战术地图 workspace。

该变化仅是 visualization posture 变化。它不改变 scenario 内容、runtime action 语义、
simulation payload 或 profile 对 world state 的所有权边界。

## 证据

代码与回归检查：

```bash
perl -0ne 'while (/<script\s+type="module"[^>]*>(.*?)<\/script>/sg) { print $1, "\n" }' examples/viz/web_viz/templates/index.html | node --input-type=module --check -
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/viz/test_tactical_map_workspace.py tests/viz/test_tactical_layer_model.py tests/viz/test_tactical_profile_ui_defaults.py tests/viz/test_tactical_map_only_mode.py
git diff --check -- docs/task/viz examples/viz tests/viz
```

观察结果：module 语法检查通过；聚焦 viz 测试报告 `12 passed`；diff whitespace 检查通过。

浏览器 smoke 使用本地 viz 服务与 `scenarios/ground/ground_platoon_tasking_smoke_v1.json`：

- 初始页面达到 `READY`。
- 点击 `MAP ONLY` 后，`document.documentElement.dataset.mapOnly` 为 `true`，
  `layoutMode` 为 `map-only`。
- menubar、left dock、right dock 和 help overlay 均被隐藏；`EXIT MAP` 控件保持可见。
- tactical canvas 仍可见，尺寸约为 `780x493`。
- 按下 `Space` 后 session 继续推进，地图绘制出非背景像素。
- 点击 `EXIT MAP` 后恢复正常 shell。
- 再次进入纯地图并按 `Escape` 后，也能恢复正常 shell。
- 浏览器 console 报告 `Errors: 0`。
- 截图：`output/playwright/tactical_map_only_mode_20260606.png`。

文档/测试清理后的最终 re-smoke 使用 `http://127.0.0.1:5066`，确认：

- 点击 `MAP ONLY` 后，`mapOnly=true`、`layoutMode=map-only`、`leftDock=closed`
  且 `rightDock=closed`；
- menubar、left dock、right dock 和 help overlay 的 computed `display` 均为 `none`；
- `EXIT MAP` 的 computed `display` 为 `block`；
- tactical canvas 尺寸为 `1280x720`；
- 按下 `Escape` 后恢复 `mapOnly=false`，menubar `display: flex`，`EXIT MAP`
  `display: none`；
- 浏览器 console 报告 `Errors: 0`。

smoke 期间，该场景仍使用既有 ground compatibility shell，session 启动后出现重复的
aircraft-style `failfast_extreme_pitch` episode。这里将其记录为既有 scenario/runtime 行为，
不归因于本 UI-only viewer 切片。

## 已接受边界

- 不改变 scenario schema。
- 不改变 simulation runtime 行为。
- 不接受地形生成或生成地图 artifact。
- 不接受 movement、LOS、cover、sensing、fires、damage、reward 或 termination 行为。
- 除规范化并应用 `ui.map_only` 作为布尔 UI 默认值外，不接受 profile object-binding 语义。
- 不接受 service/domain 硬编码移除。

## 残余

- 替换 viz profiles 中硬编码 service/domain 假设之前，需要先把 profile/object binding
  设计为后续切片。
- 更丰富的 map-only toolbar 应等待 object-binding 和 multi-map 需求更加清楚后再设计。
