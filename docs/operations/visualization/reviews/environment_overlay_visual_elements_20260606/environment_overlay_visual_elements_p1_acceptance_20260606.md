# Environment Overlay Visual Elements P1 Acceptance

Status: `2026-06-06` accepted visualization-only slice.

Parent: [Environment Overlay Visual Elements](README.md)

Chinese companion:
[environment_overlay_visual_elements_p1_acceptance_20260606.zh.md](environment_overlay_visual_elements_p1_acceptance_20260606.zh.md)

## Decision

`VIZ-ENV-OVERLAY-P1` is accepted as a tactical-map readability slice for G0
environment overlays.

The accepted implementation adds:

- center anchors for environment overlay entries;
- compact type/source callouts such as `SURF`, `SURF-IDX`, `STRUCT`, and `VEG`;
- surface type plus dimensions for surface zones;
- height hints for occlusion candidates when `height_m` is available;
- callout clamping inside the tactical canvas.

## Evidence

Static and focused tests:

```bash
perl -0ne 'while (/<script\s+type="module"[^>]*>(.*?)<\/script>/sg) { print $1, "\n" }' examples/viz/web_viz/templates/index.html | node --input-type=module --check -
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/viz/test_environment_overlays.py tests/viz/test_environment_overlay_visual_elements.py tests/viz/test_tactical_map_only_mode.py tests/viz/test_tactical_profile_ui_defaults.py
git diff --check -- docs/task/viz examples/viz tests/viz
```

Observed result: module syntax check passed; focused viz tests reported
`9 passed`; diff whitespace check passed.

Browser smoke used `http://127.0.0.1:5069` with
`output/generated_maps/g0_generated_terrain_map_smoke_20260606.json`:

- server emitted 1 generated surface zone and 3 environment overlay layers;
- browser loaded the generated-map scenario and reached `READY`;
- `ENV` layer was enabled;
- map-only mode set `mapOnly=true`, `layoutMode=map-only`, and hid the menubar;
- session reached `RUNNING`;
- canvas measured `1280x720`;
- pixel probe returned `nonBg=36538`, `envLike=9716`, `cyanText=607`,
  `brightLabel=2154`;
- browser console reported `Errors: 0`;
- screenshot:
  `output/playwright/g0_generated_terrain_map_visual_elements_20260606.png`.

The screenshot shows generated overlay callouts including `STRUCT` and
`SURF-IDX HARDSTAND SURFACE`, plus the detail label `CONCRETE 80M X 80M`.

## Accepted Boundaries

- No terrain generator algorithm changes.
- No scenario-producing generated terrain artifact release.
- No projection-profile generation release.
- No runtime setup application.
- No road graph, movement-cost grid, passability mask, LOS, cover,
  concealment, fires, damage, combat, reward, or termination behavior.
- No runtime consumer release for G0 derived products.

Ground shell `failfast_extreme_pitch` messages during smoke and nanobind leak
warnings during shutdown remain existing runtime/shutdown behavior outside this
visualization-only acceptance.
