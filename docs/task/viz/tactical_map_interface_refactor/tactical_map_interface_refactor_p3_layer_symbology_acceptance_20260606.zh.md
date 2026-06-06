# 战术地图界面重构 P3 图层符号验收

状态：`2026-06-06`，`VIZ-TMAP-P3` 已作为切片接受。整体战术地图界面重构仍为活跃状态；
`P4` profile 默认值持久化不由本文接受。

父项：[战术地图界面重构](README.zh.md)

英文规范页：
[tactical_map_interface_refactor_p3_layer_symbology_acceptance_20260606.md](tactical_map_interface_refactor_p3_layer_symbology_acceptance_20260606.md)

## 决策

`VIZ-TMAP-P3` 作为图层组织和第一版符号样式切片接受。

已接受实现保持既有 `examples/viz` tactical payload 语义不变，同时集中管理：

- `tacticalLayerCatalog`：图层标签、分组、绘制顺序、按钮 ID 和默认启用状态。
- `tacticalLayerGroups`：右侧 dock 中的 `ENVIRONMENT`、`MANEUVER`、`SENSORS`
  和 `EFFECTS` 分组控制。
- `tacticalDrawPhases`：从 grid/environment 到 labels 的地图绘制阶段顺序。
- `tacticalSymbology`：阵营、路线、数据链、track、环境、武器和标签渲染的第一版颜色样式。

分组图层控件由 catalog 在 runtime 生成。`P2` 已接受的 workspace 默认值继续决定每个
workspace 默认启用哪些图层。

## 证据

代码和回归检查：

```bash
perl -0ne 'while (/<script\s+type="module"[^>]*>(.*?)<\/script>/sg) { print $1, "\n" }' examples/viz/web_viz/templates/index.html | node --input-type=module --check -
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/viz/test_environment_overlays.py tests/viz/test_tactical_map_workspace.py tests/viz/test_tactical_layer_model.py
```

观察结果：module 语法检查通过；聚焦 viz 测试报告 `8 passed`。

浏览器 smoke 使用本地 viz 服务 `http://127.0.0.1:5064` 和
`scenarios/ground/ground_platoon_tasking_smoke_v1.json`：

- 桌面视口 `1440x900` 显示右侧 dock 的 `LAYERS` 面板已分为
  `ENVIRONMENT`、`MANEUVER`、`SENSORS` 和 `EFFECTS`。
- `COP` 默认按下 environment、route、trail 和 weapon 控制。
- `ENVIRONMENT` 保持 `VIEW: MAP`，并默认只按下 environment 图层。
- `TRACKS` 保持 `VIEW: MAP`，并默认按下 trail、track、sensor ring 和 datalink 控制。
- `3D INSPECT` 切换到 `VIEW: 3D`，且顶栏 workspace 仍可回到地图。
- 浏览器 console 报告 `Errors: 0`；warnings 仅为 WebGL `ReadPixels` 性能提示。
- 截图：`output/playwright/tactical_map_p3_layer_groups_20260606.png`。

smoke 结束后关闭服务时出现既有 nanobind leak warning。该警告发生在浏览器证据收集之后，
不归因于本次 UI-only 图层模型。

## 已接受边界

- 不改变 scenario schema。
- 不改变 profile-loader contract。
- 不改变 tactical payload 语义。
- 不接受地形感知机动、可通行性、LOS、掩蔽/隐蔽、感知、火力、毁伤、奖励、终止、scenario 编辑器、地形生成器 UI 或环境 runtime 变异。
- 不声明 MIL-STD-2525、APP-6 或其他军用符号标准合规。

## 残余

- 历史说明：在 `P3` 检查点，`VIZ-TMAP-P4` 继续 held，直到稳定的 workspace/layer 默认值需要通过
  profile UI defaults 持久化。当前 P4 状态由
  [P4 profile-default 验收](tactical_map_interface_refactor_p4_profile_defaults_acceptance_20260606.zh.md) 覆盖。
- 更丰富的地形、道路、建筑、植被、天气和环境产品图层，应先通过 common environment substrate
  进入，再成为新的 tactical layer catalog 条目。
- 是否拆出专门 JS/CSS 文件仍为可选项，应等单模板 catalog 变得难维护后再处理。
