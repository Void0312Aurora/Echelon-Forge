# Tactical Map Interface Refactor P1 Shell Layout Acceptance

Status: `2026-06-06` `VIZ-TMAP-P1` accepted slice. Historical slice note: the
overall tactical-map interface refactor remained active at this checkpoint;
`P2` map workspace and later layer/symbology work were not accepted by this
note. Current overall status is superseded by
[P6 closure/archive sync](tactical_map_interface_refactor_p6_closure_archive_sync_20260606.md).

Parent: [Tactical Map Interface Refactor](README.md)

Chinese companion:
[tactical_map_interface_refactor_p1_shell_layout_acceptance_20260606.zh.md](tactical_map_interface_refactor_p1_shell_layout_acceptance_20260606.zh.md)

## Decision

`VIZ-TMAP-P1` is accepted as a map-first shell-layout slice.

The accepted implementation is the single-template patch in
[index.html](../../../../examples/viz/web_viz/templates/index.html). It keeps
the tactical canvas as the first-viewport surface, moves session setup into a
collapsible left dock, moves telemetry/mission/unit/layer data into a
collapsible right dock, and preserves the existing profile, scenario, asset,
run-control, layer-control, telemetry, and unit-list DOM IDs.

This slice also adds a UI-only "Scenario only (no profile active)" profile
placeholder when a session is loaded directly from a scenario. That clarifies
the profile/scenario boundary without changing profile or scenario schemas.

## Evidence

Code and regression checks:

```bash
perl -0ne 'while (/<script\s+type="module"[^>]*>(.*?)<\/script>/sg) { print $1, "\n" }' examples/viz/web_viz/templates/index.html | node --input-type=module --check -
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/viz/test_environment_overlays.py
```

Observed result: module syntax check passed; `tests/viz/test_environment_overlays.py`
reported `2 passed`.

Browser smoke, using the local viz server on `http://127.0.0.1:5064` and the
project Playwright wrapper:

- Narrow initial shell at `780x493`: `layoutMode=narrow`, left/right docks
  default closed, tactical canvas `780x493`, console errors `0`.
- Narrow interactive shell: `SETUP` and `DATA` docks open as overlay panels;
  map padding remains narrow-overlay style rather than pushing the canvas below
  stacked controls.
- Direct ground scenario load:
  `scenarios/ground/ground_platoon_tasking_smoke_v1.json` reached `READY`, then
  `RUNNING`; profile selector showed `Scenario only (no profile active)`;
  `ENV` remained pressed; the canvas was nonblank.
- Desktop ground smoke at `1440x900`: `layoutMode=wide`, left/right docks open,
  tactical canvas `1440x900`, sampled non-background pixels `30 / 1852`;
  screenshot updated at
  `output/playwright/tactical-map-p1-ground-desktop-20260606.png`.
- Narrow screenshot updated at
  `output/playwright/tactical-map-p1-ground-narrow-20260606.png`.
- Air-combat profile smoke:
  `examples/viz/profiles/air_combat_1v1_stage0_forced_fire_debug.json` reached
  `READY`, then `RUNNING`; unit list included `Blue_Fighter`, `Red_Drone`, and
  `Missile_584`; sampled non-background pixels `21 / 1852`.
- 3D toggle smoke: `VIEW: 3D`, tactical panel display `none`, renderer opacity
  `1`, renderer pointer events `auto`, docks remained open.
- Final browser console check: `Errors: 0`.

The screenshot paths are local ignored artifacts under `output/`; they are
evidence aids, not tracked project deliverables.

## Accepted Boundaries

- No scenario schema changes.
- No profile-loader contract changes.
- No terrain-aware movement, passability, LOS, cover, concealment, sensing,
  fires, damage, reward, termination, scenario editor, terrain generator UI, or
  environment-runtime mutation is accepted here.
- No MIL-STD-2525, APP-6, or other military-symbol standard compliance is
  claimed.

## Residuals

- Historical note: at the `P1` checkpoint, `VIZ-TMAP-P2`, `VIZ-TMAP-P3`, and
  `VIZ-TMAP-P4` remained residuals. Current status is superseded by
  [P2 workspace acceptance](tactical_map_interface_refactor_p2_workspace_acceptance_20260606.md),
  [P3 layer/symbology acceptance](tactical_map_interface_refactor_p3_layer_symbology_acceptance_20260606.md),
  and [P4 profile-default acceptance](tactical_map_interface_refactor_p4_profile_defaults_acceptance_20260606.md).
- Historical note: the naval debug profile action-mode mismatch observed during
  `P1` smoke is repaired by the later `P4` profile-default slice, which aligns
  the naval viz profiles with `action_mode='naval_station3'`.
