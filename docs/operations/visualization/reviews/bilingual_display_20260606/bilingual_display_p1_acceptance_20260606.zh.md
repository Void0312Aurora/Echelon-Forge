# 双语显示 P1 验收 - 2026-06-06

状态：显示层 `P1` 切片已接受。

接受范围：

- 战术地图 action bar 中的中英语言切换。
- 主 viz shell 的静态标签与 ARIA 标签。
- 动态 workspace、图层、会话/运行、纯地图、视图/相机、速率、战术比例尺、
  mission 与 environment callout 显示文本。
- scenario/profile/unit/asset 标识继续作为 runtime 数据稳定保留，不做翻译。

边界：

本验收不释放 scenario schema 变化、profile object-binding、地形生成、
runtime setup application、passability、movement cost、LOS、cover、concealment、
combat、reward 或 termination 行为。

验证：

```bash
perl -0ne 'while (/<script\s+type="module"[^>]*>(.*?)<\/script>/sg) { print $1, "\n" }' examples/viz/web_viz/templates/index.html | node --input-type=module --check -
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/viz/test_environment_overlays.py tests/viz/test_environment_overlay_visual_elements.py tests/viz/test_tactical_map_only_mode.py tests/viz/test_tactical_profile_ui_defaults.py tests/viz/test_ground_nav_marker_suppression.py tests/viz/test_tactical_bilingual_ui.py
git diff --check -- docs/task/viz examples/viz tests/viz
```

观察结果：

- JS module 语法检查通过。
- 聚焦 viz pytest 报告 `16 passed, 1 warning`。
- whitespace 检查通过。

Browser smoke：

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python examples/viz/run_viz.py --scenario output/generated_maps/test_terrain_constructs_20260606.json --port 5073
```

观察结果：

- 页面加载 generated terrain fixture，包含 9 个 map zones 和 2 个 environment
  overlay layers。
- 点击 `中文` 后，`document.documentElement.lang` 变为 `zh-CN`。
- 语言按钮变为 `EN`。
- 会话标签变为 `就绪 | output/generated_maps/test_terrain_constructs_20260606.json`。
- 视图按钮变为 `视图: 地图`。
- tactical layer ARIA label 变为 `战术图层`。
- 中文纯地图模式报告 `mapOnly=true`、`layout=map-only`，主按钮和浮动退出按钮均显示
  `退出地图`。
- 点击 `EN` 后，`document.documentElement.lang` 回到 `en`，可见控件回到英文。
- 浏览器 console 报告 `Errors: 0`。
- 运行态 canvas 探针报告 `documentElement.lang=zh-CN`、`canvas=1280x720`、
  中文比例尺 `100 PX = 1.2公里 | 网格 2.0公里 | 缩放 100%`，以及
  `nonDark=140213`。

截图 artifact：

- `output/playwright/test_terrain_constructs_bilingual_zh_20260606.png`
- `output/playwright/test_terrain_constructs_bilingual_zh_running_20260606.png`

已知噪声：

- viz shutdown 路径仍输出 nanobind leak warnings。这是既有 runtime/shutdown 噪声，
  不属于 display-only P1 范围。
- 运行 ground terrain fixture 时还输出了重复的 `failfast_extreme_pitch` episode
  resets。这是既有 ground smoke runtime 噪声，没有作为 bilingual UI 证据使用。
- pytest warning 是 `examples/viz/runtime/viz_session.py` 的既有 Eventlet
  deprecation warning。
