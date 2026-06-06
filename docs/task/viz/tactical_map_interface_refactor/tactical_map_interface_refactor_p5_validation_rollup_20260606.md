# Tactical Map Interface Refactor P5 Validation Roll-Up

Status: `2026-06-06` `VIZ-TMAP-P5` accepted validation roll-up. Historical
next step: `P6` closure/archive synchronization is now complete in
[P6 closure/archive sync](tactical_map_interface_refactor_p6_closure_archive_sync_20260606.md).

Parent: [Tactical Map Interface Refactor](README.md)

Chinese companion:
[tactical_map_interface_refactor_p5_validation_rollup_20260606.zh.md](tactical_map_interface_refactor_p5_validation_rollup_20260606.zh.md)

## Decision

`VIZ-TMAP-P5` is accepted as the validation roll-up for the scoped tactical-map
interface refactor. The evidence from `P1` through `P4`, plus the fresh
code-side validation below, is sufficient to decide that the first maintained
map-first tactical interface can be accepted within its documented boundaries.

This roll-up does not add runtime functionality. It consolidates the evidence
needed so the acceptance decision does not depend on chat history.

## Evidence Matrix

| Slice | Accepted scope | Evidence | What it does not prove |
| --- | --- | --- | --- |
| `P0` boundary/reference | Durable subproject authority, finite task clusters, status, and style baseline. | [style baseline](tactical_map_interface_refactor_style_reference_baseline_20260606.md), [task clusters](tactical_map_interface_refactor_task_clusters_20260606.md) | Runtime UI implementation or simulation behavior. |
| `P1` shell layout | Map-first tactical shell with collapsible `SETUP` and `DATA` docks. | [P1 shell-layout acceptance](tactical_map_interface_refactor_p1_shell_layout_acceptance_20260606.md) | Multi-map workspace, layer grouping, profile defaults, or new simulation semantics. |
| `P2` workspace model | Tabbed `COP`, `Environment`, `Tracks/Sensors`, and `3D Inspect` workspaces. | [P2 workspace acceptance](tactical_map_interface_refactor_p2_workspace_acceptance_20260606.md), [test_tactical_map_workspace.py](../../../../tests/viz/test_tactical_map_workspace.py) | Split-map layout, scenario editor behavior, or new payload requirements. |
| `P3` layer/symbology model | Centralized tactical layer catalog, grouped controls, draw phases, and first-pass styling. | [P3 layer/symbology acceptance](tactical_map_interface_refactor_p3_layer_symbology_acceptance_20260606.md), [test_tactical_layer_model.py](../../../../tests/viz/test_tactical_layer_model.py) | MIL-STD-2525/APP-6 compliance or changed tactical payload semantics. |
| `P4` profile UI defaults | Profile-selected tactical workspace and layer defaults as UI/runtime preferences. | [P4 profile-default acceptance](tactical_map_interface_refactor_p4_profile_defaults_acceptance_20260606.md), [test_tactical_profile_ui_defaults.py](../../../../tests/viz/test_tactical_profile_ui_defaults.py) | Scenario schema changes, realism/world-parameter mutation, or new naval behavior. |

## Consolidated Validation

Fresh `P5` code-side refresh:

```bash
perl -0ne 'while (/<script\s+type="module"[^>]*>(.*?)<\/script>/sg) { print $1, "\n" }' examples/viz/web_viz/templates/index.html | node --input-type=module --check -
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/viz/test_environment_overlays.py tests/viz/test_tactical_map_workspace.py tests/viz/test_tactical_layer_model.py tests/viz/test_tactical_profile_ui_defaults.py
python -m json.tool examples/viz/profiles/air_combat_1v1_stage0_forced_fire_debug.json >/dev/null
python -m json.tool examples/viz/profiles/naval_ddg51_contact_report_debug.json >/dev/null
python -m json.tool examples/viz/profiles/naval_ddg51_closing_contact_debug.json >/dev/null
```

Observed result on `2026-06-06`: module syntax check passed; focused viz tests
reported `12 passed`; all three profile JSON files parsed cleanly.

Browser evidence is retained in the accepted slice documents:

- `P1` covered narrow and desktop map-first shell behavior, direct ground
  scenario loading, air-combat profile loading, 3D toggle behavior, and final
  browser console `Errors: 0`.
- `P2` covered workspace switching across `COP`, `ENVIRONMENT`, `TRACKS`, and
  `3D INSPECT`, desktop and narrow viewports, nonblank map pixels, and final
  browser console `Errors: 0`.
- `P3` covered grouped layer controls and workspace/layer behavior with final
  browser console `Errors: 0`; screenshot path:
  `output/playwright/tactical_map_p3_layer_groups_20260606.png`.
- `P4` covered naval contact-report profile loading to `READY`, `TRACKS`
  workspace defaults, profile-selected layer defaults, and final browser
  console `Errors: 0`; screenshot path:
  `output/playwright/tactical_map_p4_profile_defaults_20260606.png`.

The screenshot paths under `output/` are local ignored evidence aids, not
tracked project deliverables. The `P5` refresh did not rerun browser smoke
because `P5` itself changes documentation only; it relies on the accepted
runtime evidence from `P1` through `P4`.

## Known Non-Blocking Noise

- Browser smoke for `P3` and `P4` reported WebGL `ReadPixels` performance
  warnings only, not console errors.
- Server shutdown after some browser smoke runs emitted existing nanobind leak
  warnings after evidence collection. These are not attributed to the UI-only
  tactical-map refactor.

## Accepted Capability

The scoped first tactical-map interface refactor is accepted as:

- a map-first shell that keeps the tactical canvas as the primary surface;
- a tabbed multi-surface workspace model;
- grouped tactical layer controls with centralized first-pass draw metadata;
- profile-driven UI defaults for workspace/layer selection;
- documentation that keeps profile defaults separate from scenario/world
  semantics.

## Residuals And Held Claims

No immediate `P1`-through-`P4` residual remains inside this subproject after
the roll-up. The following remain held or deferred outside this closeout:

- split-map layout;
- richer terrain, road, building, vegetation, weather, or other environment
  derived-product rendering until the owning environment substrate accepts
  those products;
- dedicated tactical symbol registry extraction until the current template
  becomes difficult to maintain;
- scenario editing, terrain generator UI, terrain-aware movement, passability,
  LOS, cover, concealment, sensing, fires, damage, reward, termination, or
  environment-runtime behavior;
- MIL-STD-2525, APP-6, or other military-symbol standard compliance.

## Next Step

Completed by
[P6 closure/archive sync](tactical_map_interface_refactor_p6_closure_archive_sync_20260606.md),
which synchronizes README/status/task-cluster/dispatch/archive surfaces and
marks this subproject `closed`.
