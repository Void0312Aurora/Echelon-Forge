# Tactical Map Interface Refactor Dispatch Queue

Status: `2026-06-06` active dispatch queue for
[Tactical Map Interface Refactor](README.md). `P0` is pass; first `P1`
read-only diagnostics packet returned `pass`; the main-thread `P1` shell
implementation is accepted as a slice.

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

Residuals remain assigned to `P2`, `P3`, and `P4`.

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
