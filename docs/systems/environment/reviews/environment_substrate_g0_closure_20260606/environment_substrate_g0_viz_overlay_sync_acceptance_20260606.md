# Environment Substrate G0-Viz Overlay Sync Acceptance

Status: `2026-06-06` accepted implementation follow-on for visualizing accepted
G0 environment data in `examples/viz`.

## Decision

G0-Viz-A is accepted as a visualization-only sync package. It does not reopen
the closed G0 substrate line and does not release runtime environment behavior.

The accepted slice adds:

- a pure Python `examples/viz` overlay normalizer for G0 environment data;
- a backward-compatible `map_setup.environment_overlays` payload alongside the
  existing `map_setup.zones`;
- an `ENV` tactical-map layer that draws environment area overlays before
  routes, tracks, weapons, and units;
- metadata-only support for `surface_zone_index` and
  `occlusion_candidate_index` when a scenario carries a G0-M bundle;
- focused tests that keep held derived products out of the viz overlay surface.

## Accepted Surface

The visualization surface may display:

- `environment.zones` as surface-zone rectangles;
- G0-M `surface_zone_index` entries as surface-zone rectangles;
- G0-M `occlusion_candidate_index` entries as candidate footprints using
  `rect` or `aabb` geometry.

The tactical map may use these entries for viewport bounds, drawing order,
styling, and labels only. The payload carries explicit evidence flags for no
runtime setup application, no runtime consumer release, no movement release,
and no LOS/cover release.

## Explicit Non-Release Boundary

Still not released by G0-Viz-A:

- runtime setup application;
- scenario-producing terrain generator plugins or checked-in generated terrain
  artifacts;
- road graph, movement-cost grid, passability mask, runtime LOS occlusion,
  cover/concealment runtime products, tactical-area runtime graph;
- route following, speed updates, terrain-aware movement, sensing, fires,
  damage, combat, suppression, reward/termination binding, observation/export;
- weather simulation, hydrodynamics, hydrology effects, or dynamic environment
  mutation.

## Evidence

| Area | Evidence | Result |
| --- | --- | --- |
| Overlay normalizer | [environment_overlays.py](../../../../../examples/viz/runtime/environment_overlays.py) | accepted |
| Viz map payload | [viz_session.py](../../../../../examples/viz/runtime/viz_session.py) emits `environment_overlays` in `map_setup` | accepted |
| Tactical map layer | [index.html](../../../../../examples/viz/web_viz/templates/index.html) adds `ENV` and draws `rect`/`aabb` overlays | accepted |
| Contract tests | [test_environment_overlays.py](../../../../../tests/viz/test_environment_overlays.py) | accepted |

## Validation

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/viz/test_environment_overlays.py
# 2 passed
```

```bash
./.venv/bin/python -m py_compile examples/viz/runtime/environment_overlays.py examples/viz/runtime/viz_session.py
# clean
```

```bash
perl -0ne 'while (/<script\s+type="module"[^>]*>(.*?)<\/script>/sg) { print $1, "\n" }' examples/viz/web_viz/templates/index.html | node --input-type=module --check -
# clean
```

Browser smoke:

- started `examples/viz` on `http://localhost:5062`;
- loaded `scenarios/ground/ground_platoon_tasking_smoke_v1.json`;
- observed `map_setup` with `GroundTaskingSmokeArea` and one environment overlay
  layer;
- confirmed `ENV` tactical layer button appears and toggles without console
  errors;
- after `START`, canvas pixel probe returned nonblank tactical drawing with
  environment-style pixels: `nonBackground=5844`, `environmentLike=1130`;
- browser console had `0` errors. WebGL readback warnings and nanobind shutdown
  leak warnings were observed during the smoke and are not caused by the
  overlay contract.

The ground smoke scenario still uses the current aircraft-compatible ground
shell and produced existing failfast aircraft dynamics during the short run.
That runtime behavior is not evidence for ground movement or terrain behavior.
