# 环境 Overlay 可视元素 P1 验收

状态：`2026-06-06`，已接受的 visualization-only 切片。

父项：[环境 Overlay 可视元素](README.zh.md)

英文规范页：
[environment_overlay_visual_elements_p1_acceptance_20260606.md](environment_overlay_visual_elements_p1_acceptance_20260606.md)

## 决策

`VIZ-ENV-OVERLAY-P1` 接受为 G0 environment overlays 的战术地图可读性切片。

已接受实现增加：

- environment overlay entries 的中心锚点；
- `SURF`、`SURF-IDX`、`STRUCT`、`VEG` 等紧凑类型/来源 callout；
- surface zones 的地表类型与尺寸；
- occlusion candidates 在存在 `height_m` 时显示高度提示；
- callout 夹取在 tactical canvas 内。

## 证据

静态与聚焦测试：

```bash
perl -0ne 'while (/<script\s+type="module"[^>]*>(.*?)<\/script>/sg) { print $1, "\n" }' examples/viz/web_viz/templates/index.html | node --input-type=module --check -
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/viz/test_environment_overlays.py tests/viz/test_environment_overlay_visual_elements.py tests/viz/test_tactical_map_only_mode.py tests/viz/test_tactical_profile_ui_defaults.py
git diff --check -- docs/task/viz examples/viz tests/viz
```

观察结果：module 语法检查通过；聚焦 viz 测试报告 `9 passed`；diff whitespace 检查通过。

浏览器 smoke 使用 `http://127.0.0.1:5069` 与
`output/generated_maps/g0_generated_terrain_map_smoke_20260606.json`：

- server emit 1 个 generated surface zone 与 3 个 environment overlay layers；
- 浏览器加载 generated-map scenario 并达到 `READY`；
- `ENV` 图层处于开启状态；
- map-only 模式设置 `mapOnly=true`、`layoutMode=map-only`，并隐藏 menubar；
- session 达到 `RUNNING`；
- canvas 尺寸为 `1280x720`；
- pixel probe 返回 `nonBg=36538`、`envLike=9716`、`cyanText=607`、
  `brightLabel=2154`；
- 浏览器 console 报告 `Errors: 0`；
- 截图：
  `output/playwright/g0_generated_terrain_map_visual_elements_20260606.png`。

截图显示 generated overlay callout，包括 `STRUCT` 和
`SURF-IDX HARDSTAND SURFACE`，以及 detail label `CONCRETE 80M X 80M`。

## 已接受边界

- 不改变地形生成器算法。
- 不释放 scenario-producing generated terrain artifact。
- 不释放 projection-profile generation。
- 不释放 runtime setup application。
- 不释放 road graph、movement-cost grid、passability mask、LOS、cover、
  concealment、fires、damage、combat、reward 或 termination 行为。
- 不释放 G0 derived products 的 runtime consumers。

smoke 期间出现的 ground shell `failfast_extreme_pitch` 信息与 shutdown 时的 nanobind
leak warnings 仍是既有 runtime/shutdown 行为，不属于本 visualization-only 验收。
