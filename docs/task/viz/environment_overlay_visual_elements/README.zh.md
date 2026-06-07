# 环境 Overlay 可视元素

状态：`2026-06-06`，已接受的 P1 visualization follow-on。Environment overlay
小对象锚点与 zoom-LOD callout 已实现，并完成 browser smoke 验证。

英文规范页：[README.md](README.md)

父级 viz 入口：[../README.zh.md](../README.zh.md)

P1 验收：
[environment_overlay_visual_elements_p1_acceptance_20260606.zh.md](environment_overlay_visual_elements_p1_acceptance_20260606.zh.md)

## 目的

增强 G0 environment-substrate overlays 在战术地图上的可读性。当前 `ENV` 图层已经能画
`environment.zones`、`surface_zone_index` 和 `occlusion_candidate_index`，但 generated
对象在公里级缩放下可能只有几个像素，肉眼很难看出是什么。

本切片只增加显示辅助：

- 每个 environment overlay entry 都绘制中心锚点；
- 绘制紧凑 callout，显示 `SURF`、`SURF-IDX`、`STRUCT`、`VEG` 等来源/类型码；
- 按缩放等级显示 callout：低缩放保留形状与锚点，中等缩放显示一行摘要，
  更高缩放再浮出细节行；
- surface zone 显示地表类型与尺寸；
- occlusion candidate 在 metadata 携带 `height_m` 时显示高度提示；
- callout 会夹取在 tactical canvas 内，避免跑出画布。

## 边界

本 follow-on 不新增或释放：

- 地形生成器算法；
- scenario-producing generated terrain artifacts；
- projection-profile generation；
- road graph、movement-cost grid、passability mask、LOS、cover、concealment、
  fires、damage、combat、reward 或 termination 行为；
- runtime setup application 或 G0 derived products 的 runtime consumers。

## 验证

已完成：

```bash
perl -0ne 'while (/<script\s+type="module"[^>]*>(.*?)<\/script>/sg) { print $1, "\n" }' examples/viz/web_viz/templates/index.html | node --input-type=module --check -
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/viz/test_environment_overlays.py tests/viz/test_environment_overlay_visual_elements.py tests/viz/test_tactical_map_only_mode.py tests/viz/test_tactical_profile_ui_defaults.py tests/viz/test_ground_nav_marker_suppression.py
git diff --check -- docs/task/viz examples/viz tests/viz
```

观察结果：module 语法检查通过；聚焦 viz 测试报告 `13 passed`；diff whitespace 检查通过。

浏览器 smoke：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python examples/viz/run_viz.py --scenario output/generated_maps/test_terrain_constructs_20260606.json --port 5072
```

观察结果：本地服务 emit 9 个 generated surface zones 与 2 个 environment overlay layers；
Playwright 打开 map-only 模式、启动 session，并确认 `mapOnly=true`、`layoutMode=map-only`、
canvas `1280x720`、默认缩放 `100 PX = 0.9 KM`、放大视图 `100 PX = 0.4 KM`，
浏览器 console `Errors: 0`。标签颜色探针从默认缩放的 `brightLabel=260`、`cyanText=1546`
增加到 `221%` 缩放下的 `brightLabel=1021`、`cyanText=3000`。

截图：
`output/playwright/test_terrain_constructs_lod_collision_default_20260606.png`
和 `output/playwright/test_terrain_constructs_lod_collision_zoomed_20260606.png`。

Ground shell 的 `failfast_extreme_pitch` 信息和 nanobind shutdown leak warnings
仍是既有 runtime/shutdown 噪声，不属于本 visualization-only 切片。
