# Environment Overlay Visual Elements

Status: `2026-06-06` accepted P1 visualization follow-on. Environment overlay
small-object anchors and zoom-LOD callouts are implemented and
browser-smoke validated.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Document kind: `review`
Lifecycle: `accepted`
Canonical: `docs/operations/visualization/reviews/environment_overlay_visual_elements_20260606/README.md`
Owner: `operations/visualization`
Last verified: `2026-08-08`

Parent owner: [Operations](../../../README.md)

P1 acceptance:
[environment_overlay_visual_elements_p1_acceptance_20260606.md](environment_overlay_visual_elements_p1_acceptance_20260606.md)

## Purpose

Improve tactical-map readability for G0 environment-substrate overlays. The
current `ENV` layer can draw `environment.zones`, `surface_zone_index`, and
`occlusion_candidate_index`, but generated objects can be too small to read at
kilometer-scale zoom levels.

This slice adds display affordances only:

- center anchors for every environment overlay entry;
- compact callouts with source/type codes such as `SURF`, `SURF-IDX`, `STRUCT`,
  and `VEG`;
- zoom-dependent callout LOD: low zoom keeps shapes and anchors, medium zoom
  shows one-line summaries, and higher zoom reveals detail lines;
- surface dimensions for surface zones;
- height hints for occlusion candidates when metadata provides `height_m`;
- label clamping so callouts remain inside the tactical canvas.

## Boundaries

This follow-on does not add or release:

- terrain generator algorithms;
- scenario-producing generated terrain artifacts;
- projection-profile generation;
- road graph, movement-cost grid, passability mask, LOS, cover, concealment,
  fires, damage, combat, reward, or termination behavior;
- runtime setup application or runtime consumers for G0 derived products.

## Validation

Completed:

```bash
perl -0ne 'while (/<script\s+type="module"[^>]*>(.*?)<\/script>/sg) { print $1, "\n" }' examples/viz/web_viz/templates/index.html | node --input-type=module --check -
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/viz/test_environment_overlays.py tests/viz/test_environment_overlay_visual_elements.py tests/viz/test_tactical_map_only_mode.py tests/viz/test_tactical_profile_ui_defaults.py tests/viz/test_ground_nav_marker_suppression.py
git diff --check -- docs/operations/visualization examples/viz tests/viz
```

Observed result: module syntax check passed; focused viz tests reported
`13 passed`; diff whitespace check passed.

Browser smoke:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python examples/viz/run_viz.py --scenario output/generated_maps/test_terrain_constructs_20260606.json --port 5072
```

Observed result: local server emitted 9 generated surface zones and 2
environment overlay layers; Playwright opened map-only mode, started the
session, confirmed `mapOnly=true`, `layoutMode=map-only`, canvas `1280x720`,
default zoom `100 PX = 0.9 KM`, zoomed view `100 PX = 0.4 KM`, and browser
console `Errors: 0`. Label-color probe increased from `brightLabel=260` and
`cyanText=1546` at default zoom to `brightLabel=1021` and `cyanText=3000` at
zoom `221%`.

Screenshots:
`output/playwright/test_terrain_constructs_lod_collision_default_20260606.png`
and `output/playwright/test_terrain_constructs_lod_collision_zoomed_20260606.png`.

Ground shell `failfast_extreme_pitch` messages and nanobind shutdown leak
warnings remain existing runtime/shutdown noise outside this visualization-only
slice.
