# Bilingual Display P1 Acceptance - 2026-06-06

Status: accepted for the display-only P1 slice.

Scope accepted:

- English/Chinese language toggle in the tactical-map action bar.
- Static labels and ARIA labels for the main viz shell.
- Dynamic workspace, layer, session/run, map-only, view/camera, speed, tactical
  scale, mission, and environment callout display text.
- Stable preservation of scenario/profile/unit/asset identifiers as runtime data.

Boundary:

This acceptance does not release scenario schema changes, profile object-binding,
terrain generation, runtime setup application, passability, movement cost, LOS,
cover, concealment, combat, reward, or termination behavior.

Validation:

```bash
perl -0ne 'while (/<script\s+type="module"[^>]*>(.*?)<\/script>/sg) { print $1, "\n" }' examples/viz/web_viz/templates/index.html | node --input-type=module --check -
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/viz/test_environment_overlays.py tests/viz/test_environment_overlay_visual_elements.py tests/viz/test_tactical_map_only_mode.py tests/viz/test_tactical_profile_ui_defaults.py tests/viz/test_ground_nav_marker_suppression.py tests/viz/test_tactical_bilingual_ui.py
git diff --check -- docs/operations/visualization examples/viz tests/viz
```

Observed result:

- JS module syntax check passed.
- Focused viz pytest reported `16 passed, 1 warning`.
- Whitespace check passed.

Browser smoke:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python examples/viz/run_viz.py --scenario output/generated_maps/test_terrain_constructs_20260606.json --port 5073
```

Observed result:

- The page loaded the generated terrain fixture with 9 map zones and 2
  environment overlay layers.
- Clicking `中文` changed `document.documentElement.lang` to `zh-CN`.
- The language button changed to `EN`.
- Session label changed to `就绪 | output/generated_maps/test_terrain_constructs_20260606.json`.
- View button changed to `视图: 地图`.
- Tactical layer ARIA label changed to `战术图层`.
- Chinese map-only mode reported `mapOnly=true`, `layout=map-only`, and both
  main/exit controls displayed `退出地图`.
- Clicking `EN` changed `document.documentElement.lang` back to `en`, and the
  visible controls returned to English.
- Browser console reported `Errors: 0`.
- A running-state canvas probe reported `documentElement.lang=zh-CN`,
  `canvas=1280x720`, Chinese scale text
  `100 PX = 1.2公里 | 网格 2.0公里 | 缩放 100%`, and `nonDark=140213`.

Screenshot artifact:

- `output/playwright/test_terrain_constructs_bilingual_zh_20260606.png`
- `output/playwright/test_terrain_constructs_bilingual_zh_running_20260606.png`

Known noise:

- The viz shutdown path still emits nanobind leak warnings. This is existing
  runtime/shutdown noise and is outside the display-only P1 scope.
- Running the ground terrain fixture also emitted repeated
  `failfast_extreme_pitch` episode resets. This is existing ground smoke runtime
  noise and was not used as bilingual UI evidence.
- The pytest warning is the existing Eventlet deprecation warning from
  `examples/viz/runtime/viz_session.py`.
