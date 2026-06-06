# Tactical Map Interface Refactor P2 Workspace Acceptance

Status: `2026-06-06` `VIZ-TMAP-P2` accepted slice. Historical slice note: the
overall tactical-map interface refactor remained active at this checkpoint;
`P3` layer/symbology grouping and `P4` profile-default persistence were not
accepted by this note. Current overall status is superseded by
[P6 closure/archive sync](tactical_map_interface_refactor_p6_closure_archive_sync_20260606.md).

Parent: [Tactical Map Interface Refactor](README.md)

Chinese companion:
[tactical_map_interface_refactor_p2_workspace_acceptance_20260606.zh.md](tactical_map_interface_refactor_p2_workspace_acceptance_20260606.zh.md)

## Decision

`VIZ-TMAP-P2` is accepted as the first maintained map-workspace model slice.

This slice chooses tabbed map surfaces first, not split-map layout. The accepted
implementation is the single-template patch in
[index.html](../../../../../examples/viz/web_viz/templates/index.html) plus the
focused static regression test
[test_tactical_map_workspace.py](../../../../../tests/viz/test_tactical_map_workspace.py).

Accepted surfaces:

| Surface | Role | Default view | Default layer posture |
| --- | --- | --- | --- |
| `COP` | Common operational picture | `MAP` | Environment, route, trails, and weapons on; tracks/sensor rings/data links off. |
| `Environment` | Environment and area inspection | `MAP` | Environment on; route/trails/weapons/tracks/sensor rings/data links off. |
| `Tracks` | Tracks, sensors, and links | `MAP` | Trails, tracks, sensor rings, and data links on; environment/route/weapons off. |
| `3D Inspect` | 3D model inspection | `3D` | Reuses the existing 3D renderer path and keeps map tabs reachable from the top bar. |

The workspace tabs are UI runtime state only. They do not change scenario
schema, profile schema, simulation payload semantics, or environment-runtime
behavior.

## Evidence

Code and regression checks:

```bash
perl -0ne 'while (/<script\s+type="module"[^>]*>(.*?)<\/script>/sg) { print $1, "\n" }' examples/viz/web_viz/templates/index.html | node --input-type=module --check -
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/viz/test_environment_overlays.py tests/viz/test_tactical_map_workspace.py
```

Observed result: module syntax check passed; focused viz tests reported
`5 passed`.

Browser smoke used the local viz server on `http://127.0.0.1:5064` with
`scenarios/ground/ground_platoon_tasking_smoke_v1.json`:

- Initial `READY` state showed `COP`, `ENVIRONMENT`, `TRACKS`, and
  `3D INSPECT` workspace tabs in the top bar.
- `ENVIRONMENT` switched to `workspace=environment`, kept `VIEW: MAP`, and
  enabled only the `ENV` layer by default.
- `TRACKS` switched to `workspace=tracks`, kept `VIEW: MAP`, and enabled
  trails, tracks, rings, and links by default.
- `3D INSPECT` switched to `workspace=inspect3d`, changed the button to
  `VIEW: 3D`, hid the tactical map panel, and kept the 3D renderer at
  `opacity=1` with pointer events enabled.
- Returning to `COP` restored `VIEW: MAP` and the map panel.
- After `START`, map canvas pixel sampling returned `53 / 1344` non-background
  samples.
- Desktop viewport `1440x900`: `layoutMode=wide`, `workspace=cop`, canvas
  `1440x900`, left/right docks open. Screenshot:
  `output/playwright/tactical-map-p2-ground-desktop-20260606.png`.
- Narrow viewport `780x493`: `layoutMode=narrow`, `workspace=cop`, canvas
  `780x493`, workspace tabs width `756`, left/right docks closed. Screenshot:
  `output/playwright/tactical-map-p2-ground-narrow-20260606.png`.
- Final browser console check reported `Errors: 0`.

The screenshot paths are local ignored artifacts under `output/`; they are
evidence aids, not tracked project deliverables.

## Accepted Boundaries

- No scenario schema changes.
- No profile-loader contract changes.
- No split-map workspace is accepted in this slice.
- No terrain-aware movement, passability, LOS, cover, concealment, sensing,
  fires, damage, reward, termination, scenario editor, terrain generator UI, or
  environment-runtime mutation is accepted here.
- No MIL-STD-2525, APP-6, or other military-symbol standard compliance is
  claimed.

## Residuals

- Historical note: at the `P2` checkpoint, `VIZ-TMAP-P3` and `VIZ-TMAP-P4`
  remained residuals. Current status is superseded by
  [P3 layer/symbology acceptance](tactical_map_interface_refactor_p3_layer_symbology_acceptance_20260606.md)
  and [P4 profile-default acceptance](tactical_map_interface_refactor_p4_profile_defaults_acceptance_20260606.md).
- Split-map layout remains deferred until a later need proves it can preserve
  the map-first ergonomics accepted by `P1` and this P2 tabbed slice.
