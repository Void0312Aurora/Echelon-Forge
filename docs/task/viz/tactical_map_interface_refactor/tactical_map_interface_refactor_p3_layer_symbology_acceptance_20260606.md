# Tactical Map Interface Refactor P3 Layer Symbology Acceptance

Status: `2026-06-06` `VIZ-TMAP-P3` accepted slice. The overall
tactical-map interface refactor remains active; `P4` profile-default
persistence is not accepted by this note.

Parent: [Tactical Map Interface Refactor](README.md)

Chinese companion:
[tactical_map_interface_refactor_p3_layer_symbology_acceptance_20260606.zh.md](tactical_map_interface_refactor_p3_layer_symbology_acceptance_20260606.zh.md)

## Decision

`VIZ-TMAP-P3` is accepted as a layer organization and first-pass symbology
slice.

The accepted implementation keeps the existing `examples/viz` tactical payload
semantics intact while centralizing:

- `tacticalLayerCatalog`: layer labels, groups, draw orders, button IDs, and
  default enabled state.
- `tacticalLayerGroups`: right-dock grouped controls for `ENVIRONMENT`,
  `MANEUVER`, `SENSORS`, and `EFFECTS`.
- `tacticalDrawPhases`: the map draw phase sequence from grid/environment
  through labels.
- `tacticalSymbology`: first-pass colors for affiliation, route, datalink,
  track, environment, weapon, and label rendering.

The grouped layer controls are generated from the catalog at runtime. Existing
workspace defaults from `P2` continue to drive which layers are enabled per
workspace.

## Evidence

Code and regression checks:

```bash
perl -0ne 'while (/<script\s+type="module"[^>]*>(.*?)<\/script>/sg) { print $1, "\n" }' examples/viz/web_viz/templates/index.html | node --input-type=module --check -
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/viz/test_environment_overlays.py tests/viz/test_tactical_map_workspace.py tests/viz/test_tactical_layer_model.py
```

Observed result: module syntax check passed; focused viz tests reported
`8 passed`.

Browser smoke used the local viz server on `http://127.0.0.1:5064` with
`scenarios/ground/ground_platoon_tasking_smoke_v1.json`:

- Desktop viewport `1440x900` showed the right-dock `LAYERS` panel grouped as
  `ENVIRONMENT`, `MANEUVER`, `SENSORS`, and `EFFECTS`.
- `COP` showed environment, route, trail, and weapon controls pressed by
  default.
- `ENVIRONMENT` kept `VIEW: MAP` and pressed only the environment layer by
  default.
- `TRACKS` kept `VIEW: MAP` and pressed trail, track, sensor ring, and datalink
  controls by default.
- `3D INSPECT` switched to `VIEW: 3D` and kept top-bar workspace recovery
  available.
- Browser console reported `Errors: 0`; warnings were WebGL `ReadPixels`
  performance messages only.
- Screenshot: `output/playwright/tactical_map_p3_layer_groups_20260606.png`.

Server shutdown after the smoke run emitted existing nanobind leak warnings.
Those warnings occur after the browser evidence is collected and are not
attributed to this UI-only layer model.

## Accepted Boundaries

- No scenario schema changes.
- No profile-loader contract changes.
- No tactical payload semantic changes.
- No terrain-aware movement, passability, LOS, cover, concealment, sensing,
  fires, damage, reward, termination, scenario editor, terrain generator UI, or
  environment-runtime mutation is accepted here.
- No MIL-STD-2525, APP-6, or other military-symbol standard compliance is
  claimed.

## Residuals

- Historical note: at the `P3` checkpoint, `VIZ-TMAP-P4` remained held until
  stable workspace/layer defaults needed to be persisted through profile UI
  defaults. Current P4 status is superseded by
  [P4 profile-default acceptance](tactical_map_interface_refactor_p4_profile_defaults_acceptance_20260606.md).
- Richer terrain, road, building, vegetation, weather, and environment product
  layers should enter through the common environment substrate before becoming
  new tactical layer catalog entries.
- A dedicated JS/CSS extraction remains optional and should wait until the
  single-template catalog becomes hard to maintain.
