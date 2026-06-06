# Tactical Map Interface Refactor Dispatch Queue

Status: `2026-06-06` closed dispatch queue for
[Tactical Map Interface Refactor](README.md). `P0` is pass; first `P1`
read-only diagnostics packet returned `pass`; the main-thread `P1` shell
implementation is accepted as a slice; the main-thread `P2` tabbed workspace
implementation is accepted as a slice; the main-thread `P3` grouped
layer/symbology implementation is accepted as a slice; the main-thread `P4`
profile-default implementation is accepted as a slice; `P5` validation roll-up
is accepted; `P6` closure/archive sync is closed.

Language:

- English canonical: `tactical_map_interface_refactor_dispatch_queue_20260606.md`
- Chinese companion:
  [tactical_map_interface_refactor_dispatch_queue_20260606.zh.md](tactical_map_interface_refactor_dispatch_queue_20260606.zh.md)

Authority:

- [Task clusters](tactical_map_interface_refactor_task_clusters_20260606.md)
- [Current status](tactical_map_interface_refactor_current_status_20260606.md)
- [Style reference baseline](tactical_map_interface_refactor_style_reference_baseline_20260606.md)
- [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)

## Dispatch Boundary

This dispatch queue starts from `VIZ-TMAP-P0` authority verification and opens
the first `VIZ-TMAP-P1` diagnostics packet. It does not authorize concurrent
writers on `examples/viz/web_viz/templates/index.html`.

The first packet is read-only because `P1`, `P2`, and `P3` all touch the same
frontend template and must be sequenced by the main thread after diagnostics
return.

## Applied Rules

- Do not create new conversation threads or sessions.
- Reuse the existing available subagent for diagnostics.
- Every packet maps to one named cluster from the finite task-cluster plan.
- Diagnostics workers must not edit files, revert unrelated work, or claim
  simulation behavior.
- Main thread owns implementation, integration, acceptance, and status changes.
- Any worker packet must use the required worker packet format before it can
  become evidence.

## Dispatch Packets

| Packet | Cluster | Worker | Model / reasoning | Scope | Write set | Required return | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `VIZ-TMAP-P0-AUTH` | `VIZ-TMAP-P0` | main thread | current main thread | Verify parent README link, task clusters, current status, style baseline, and clean docs-only validation before dispatch. | `docs/task/viz/tactical_map_interface_refactor/**`, `docs/task/viz/README*.md` | authority check; dirty-worktree boundary; validation outcome | pass |
| `VIZ-TMAP-P1-DIAG-A` | `VIZ-TMAP-P1` | `Carson` | inherited parent / diagnostics | Read-only preflight of the existing `examples/viz` tactical shell and first map-first layout implementation boundary. | none | current layout map; exact edit surfaces; recommended first patch shape; responsive risks; validation commands; held capability claims | pass |
| `VIZ-TMAP-P1-IMPL-MAIN` | `VIZ-TMAP-P1` | main thread | current main thread | Implement the first map-first tactical shell and validate narrow, desktop, air-profile, ground-scenario, and 3D-toggle smoke paths. | `examples/viz/web_viz/templates/index.html`, P1 acceptance docs | worker-equivalent implementation summary; commands/outcomes; residuals; held capability claims | accepted slice |
| `VIZ-TMAP-P2-IMPL-MAIN` | `VIZ-TMAP-P2` | main thread | current main thread | Implement the first maintained map-workspace model as tabbed `COP`, `Environment`, `Tracks/Sensors`, and `3D Inspect` surfaces. | `examples/viz/web_viz/templates/index.html`, `tests/viz/test_tactical_map_workspace.py`, P2 acceptance docs | worker-equivalent implementation summary; commands/outcomes; residuals; held capability claims | accepted slice |
| `VIZ-TMAP-P3-IMPL-MAIN` | `VIZ-TMAP-P3` | main thread | current main thread | Centralize tactical layer groups, draw phases, and first-pass symbology styling while preserving tactical payload semantics. | `examples/viz/web_viz/templates/index.html`, `tests/viz/test_tactical_layer_model.py`, P3 acceptance docs | worker-equivalent implementation summary; commands/outcomes; residuals; held capability claims | accepted slice |
| `VIZ-TMAP-P4-IMPL-MAIN` | `VIZ-TMAP-P4` | main thread | current main thread | Extend profile UI defaults for default tactical workspace/layer/view selection while preserving scenario semantics. | `examples/viz/app/profile_loader.py`, `examples/viz/profiles/*.json`, `examples/viz/web_viz/templates/index.html`, `tests/viz/test_tactical_profile_ui_defaults.py`, P4 acceptance docs | worker-equivalent implementation summary; commands/outcomes; residuals; held capability claims | accepted slice |
| `VIZ-TMAP-P5-ROLLUP-MAIN` | `VIZ-TMAP-P5` | main thread | current main thread | Roll up validation evidence, screenshots, residuals, and capability boundaries across `P1` through `P4`. | P5 validation roll-up docs | worker-equivalent validation summary; commands/outcomes; residuals; held capability claims | accepted |
| `VIZ-TMAP-P6-CLOSE-MAIN` | `VIZ-TMAP-P6` | main thread | current main thread | Synchronize parent/subproject status and archive pointers after the acceptance decision. | parent viz README, subproject README/status/task clusters/dispatch/archive docs, P6 closure docs | closure decision; synchronized indexes; archive boundary; validation outcome | closed |

## Returned Diagnostics Summary

`VIZ-TMAP-P1-DIAG-A` returned `pass` and stayed read-only.

Accepted implementation guidance:

- Keep `VIZ-TMAP-P1` as a single-template patch in
  `examples/viz/web_viz/templates/index.html`.
- Preserve existing DOM IDs so current JavaScript update paths continue to work.
- Keep the canvas/map workspace primary.
- Move profile/scenario/asset selectors into a collapsible left dock.
- Move telemetry, mission, unit list, and current layer controls into a
  collapsible right dock.
- Add dock state and collapse buttons that refresh tactical layout padding and
  redraw the map.
- Leave workspace tabs/split maps for `VIZ-TMAP-P2`.
- Leave profile/workspace/layer defaults for `VIZ-TMAP-P4`.

Main risks to verify:

- `780x493` must not keep selectors as a permanent top stack.
- Collapsed docks must update `layoutState.tacticalPadding`.
- `updatePresentationModeUI()` must hide the map surface for `3D`, not break the
  whole shell.
- `#unit-list`, layer buttons, and profile/session controls must retain their
  existing event paths.

## Returned Implementation Summary

`VIZ-TMAP-P1-IMPL-MAIN` is accepted as a slice. Evidence is recorded in
[P1 shell-layout acceptance](tactical_map_interface_refactor_p1_shell_layout_acceptance_20260606.md).

Accepted implementation points:

- `#tactical-panel` remains a first-viewport canvas surface.
- `SETUP` and `DATA` docks are collapsible and responsive.
- Existing IDs and event paths are preserved.
- Direct scenario loads now show a UI-only scenario-only profile placeholder.
- Browser smoke covered narrow, desktop, ground ENV, air weapons/trails, 3D
  toggle, screenshots, and final `Errors: 0`.

At the `P1` checkpoint, residuals remained assigned to `P2`, `P3`, and `P4`.

## Returned P2 Implementation Summary

`VIZ-TMAP-P2-IMPL-MAIN` is accepted as a slice. Evidence is recorded in
[P2 workspace acceptance](tactical_map_interface_refactor_p2_workspace_acceptance_20260606.md).

Accepted implementation points:

- The first map-workspace model uses tabbed surfaces, not split-map layout.
- `COP`, `Environment`, `Tracks/Sensors`, and `3D Inspect` are explicit UI
  workspaces with default layer postures.
- Workspace tabs stay in the top bar so `3D Inspect` can return to map
  workspaces without a hidden control.
- Manual layer toggles are remembered per workspace for the current browser
  session.
- Static regression coverage locks the workspace IDs, tab controls, default
  layer model, and UI-only boundary.
- Browser smoke covered workspace switching, desktop and narrow layouts, map
  pixel sampling, 3D renderer visibility, screenshots, and final `Errors: 0`.

At the `P2` checkpoint, residuals remained assigned to `P3` and `P4`.

## Returned P3 Implementation Summary

`VIZ-TMAP-P3-IMPL-MAIN` is accepted as a slice. Evidence is recorded in
[P3 layer/symbology acceptance](tactical_map_interface_refactor_p3_layer_symbology_acceptance_20260606.md).

Accepted implementation points:

- Tactical layers are centralized in `tacticalLayerCatalog` with group, label,
  draw-order, button-ID, and default-enabled metadata.
- The right-dock `LAYERS` panel renders grouped controls for `ENVIRONMENT`,
  `MANEUVER`, `SENSORS`, and `EFFECTS`.
- Draw phases are named and layer-gated through `tacticalDrawPhases` and
  `isTacticalDrawPhaseEnabled()`.
- First-pass affiliation, route, datalink, track, environment, weapon, and
  label styling lives in `tacticalSymbology`.
- Static regression coverage locks the catalog/group/draw-phase structure and
  UI-only boundary.
- Browser smoke covered grouped layer controls, `COP`, `ENVIRONMENT`, `TRACKS`,
  and `3D INSPECT` workspace switching, screenshot evidence, and final
  `Errors: 0`.

At the `P3` checkpoint, residuals remained assigned to `P4` only if persisted
profile UI defaults were needed.

## Returned P4 Implementation Summary

`VIZ-TMAP-P4-IMPL-MAIN` is accepted as a slice. Evidence is recorded in
[P4 profile-default acceptance](tactical_map_interface_refactor_p4_profile_defaults_acceptance_20260606.md).

Accepted implementation points:

- Profile `ui` may now specify `tactical_workspace` and `tactical_layers`.
- `profile_loader.py` normalizes workspace/layer aliases and filters unknown or
  non-boolean layer values.
- `index.html` applies profile layer defaults over the selected workspace
  defaults and records them as workspace UI state.
- Existing air/naval viz profiles demonstrate persistent layer/workspace
  defaults.
- Naval viz profiles were realigned to the maintained `naval_station3` action
  surface so profile smoke loading reaches `READY`.
- Static regression coverage locks the profile loader contract, front-end apply
  path, and UI-only boundary.
- Browser smoke loaded the naval contact-report profile, reached `READY`,
  applied `TRACKS`, and ended with `Errors: 0`.

## Returned P5 Validation Summary

`VIZ-TMAP-P5-ROLLUP-MAIN` is accepted. Evidence is recorded in
[P5 validation roll-up](tactical_map_interface_refactor_p5_validation_rollup_20260606.md).

Accepted validation points:

- `P1` through `P4` browser smoke, screenshots, console checks, and residual
  boundaries are consolidated into a single roll-up.
- Fresh code-side refresh passed embedded module syntax, focused viz pytest,
  and profile JSON parsing.
- Browser evidence remains in the accepted slice documents because `P5` is
  docs-only and does not change runtime code.
- Immediate implementation residuals inside this subproject are closed; richer
  environment products, split-map layout, and symbol registry extraction remain
  follow-on work.

## Returned P6 Closure Summary

`VIZ-TMAP-P6-CLOSE-MAIN` is closed. Evidence is recorded in
[P6 closure/archive sync](tactical_map_interface_refactor_p6_closure_archive_sync_20260606.md).

Accepted closure points:

- The parent viz README, subproject README, current status, task clusters,
  dispatch queue, and archive README now agree that this scoped refactor is
  `closed`.
- No local evidence file was moved to `archive/`; dated acceptance and closure
  documents remain live evidence.
- Future tactical visualization work should open a new cluster or subproject.

## Worker Packet Template

```md
status: pass | partial | blocked | failed
touched files: none expected for diagnostics
files inspected:
commands/outcomes:
current layout map:
recommended first patch shape:
responsive risks:
behavior risks:
explicit held capability claims:
integration notes:
```

## Acceptance Boundary

`VIZ-TMAP-P1-DIAG-A` can support implementation planning only if it remains
read-only, maps to current repo files, and refuses terrain-aware movement, LOS,
cover, sensing, fires, damage, combat, scenario editing, terrain generator UI,
and military-standard compliance claims.

The diagnostics packet alone did not mark the shell layout accepted. The
accepted `P1` decision comes from the later main-thread implementation and
browser evidence packet above.
