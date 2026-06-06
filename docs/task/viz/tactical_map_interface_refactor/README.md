# Tactical Map Interface Refactor

Status: `2026-06-06` active visualization subproject. `P0` planning and
reference baseline are installed; `P1` shell layout, `P2` map workspace, and
`P3` layer/symbology grouping, and `P4` profile integration are accepted as
slices; `P5` validation roll-up remains next.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Parent task domain: [Viz](../README.md)
- Subproject format rule:
  [Subproject Creation Standard For Agents](../../../agent/rules/subproject_creation_standard.md)
- Delegation rule:
  [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)
- Existing unified-entry authority:
  [viz_unified_entry_session_profile_plan_20260516.md](../archive/viz_unified_entry_session_profile_plan_20260516.md)
- Current frontend shell:
  [index.html](../../../../examples/viz/web_viz/templates/index.html)
- Current profile/session layers:
  [profile_loader.py](../../../../examples/viz/app/profile_loader.py),
  [viz_session.py](../../../../examples/viz/runtime/viz_session.py)
- Accepted G0 environment overlay surface:
  [environment_substrate_g0_viz_overlay_sync_acceptance_20260606.md](../../ground/environment_substrate_g0_architecture/environment_substrate_g0_viz_overlay_sync_acceptance_20260606.md)
- Local style/reference baseline:
  [tactical_map_interface_refactor_style_reference_baseline_20260606.md](tactical_map_interface_refactor_style_reference_baseline_20260606.md)

## Purpose

This subproject turns the current `examples/viz` tactical display from a
debug-heavy single-map overlay into a map-first situational interface. The
near-term target is a usable tactical map shell that keeps the map visible,
uses collapsible controls, and can support more than one map surface when the
scenario demands it.

The work sits above the accepted unified-entry/profile/session foundation. It
does not replace the app/session/profile/asset-registry layers; it adds a
maintained interface and map-workspace plan on top of them.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Unified viz entry | active foundation, first usable closure already recorded | [viz_unified_entry_session_profile_plan_20260516.md](../archive/viz_unified_entry_session_profile_plan_20260516.md) | This does not solve the tactical-map layout or multi-map workspace. |
| Current tactical map | `P1` map-first shell accepted as a slice | [P1 acceptance](tactical_map_interface_refactor_p1_shell_layout_acceptance_20260606.md) | This accepts dock/collapse layout only, not layer grouping or profile defaults. |
| G0 environment overlays | accepted visualization-only slice | [environment_substrate_g0_viz_overlay_sync_acceptance_20260606.md](../../ground/environment_substrate_g0_architecture/environment_substrate_g0_viz_overlay_sync_acceptance_20260606.md) | This is drawing metadata only, not terrain-aware movement, LOS, cover, or combat behavior. |
| Multi-map workspace | `P2` tabbed workspace accepted as a slice | [P2 acceptance](tactical_map_interface_refactor_p2_workspace_acceptance_20260606.md) | This accepts named UI surfaces and default layer postures only, not split-map layout or new simulation semantics. |
| Tactical layer model | `P3` grouped layer/symbology slice accepted | [P3 acceptance](tactical_map_interface_refactor_p3_layer_symbology_acceptance_20260606.md) | This accepts cataloged UI layer controls and first-pass styling only, not military-standard compliance or new payload semantics. |
| Profile UI defaults | `P4` profile-default slice accepted | [P4 acceptance](tactical_map_interface_refactor_p4_profile_defaults_acceptance_20260606.md) | This accepts profile-selected workspace/layer/view UI defaults only, not scenario or simulation semantics. |
| Tactical-map style baseline | pass for `P0` | [style baseline](tactical_map_interface_refactor_style_reference_baseline_20260606.md) | References guide visual design only; they do not create military-symbol standard compliance. |

## Scope

In scope:

- Redesign the `examples/viz` tactical UI around a map-first layout.
- Define a multi-map workspace model, including at least `COP`,
  `Environment`, `Tracks/Sensors`, and `3D Inspect` surfaces.
- Move layer controls into grouped, collapsible, and responsive UI surfaces.
- Add a tactical layer/symbology model that can evolve without scattering
  drawing rules through unrelated UI code.
- Preserve the `profile` versus `scenario` boundary: profiles may choose
  default views, workspaces, and UI layer toggles; scenarios remain simulation
  content and world semantics.
- Validate the interface with browser smoke tests and screenshots across narrow
  and desktop viewports.

Out of scope:

- Full compliance with MIL-STD-2525, APP-6, or any other operational standard.
- Terrain-aware movement, passability, LOS, cover, concealment, sensing,
  fires, damage, reward, or termination behavior.
- A scenario editor or runtime terrain generator UI.
- Rewriting `examples/viz` into a new frontend framework unless a later task
  cluster proves that the current template cannot support the accepted design.
- New conversation threads or sessions for this subproject. Subagents may be
  used only through the existing project governance and must produce worker
  packets tied to the finite clusters below.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary And Reference` | Install the subproject, task clusters, current status, and map-style baseline. | User requests a durable `docs/task/viz` work surface. | Parent README links this subproject and docs-only validation is clean. | pass |
| `P1 Shell Layout` | Rework the current UI into a map-first tactical shell. | `P0` pass. | Map is first-viewport primary surface on narrow and desktop screens. | accepted slice |
| `P2 Map Workspace Model` | Add multiple named map surfaces and switching/split behavior. | `P1` shell can host map panels. | `COP`, `Environment`, `Tracks/Sensors`, and `3D Inspect` have explicit UI roles. | accepted slice |
| `P3 Layer And Symbology Model` | Centralize layer grouping, draw order, and tactical symbol styling. | `P2` workspace exists. | Existing overlays render through grouped layer rules without broader capability claims. | accepted slice |
| `P4 Profile Integration` | Let profiles select default workspace/layers without changing scenario semantics. | `P2` and `P3` stable enough for defaults. | Profile loader accepts and validates UI defaults for map workspace selection. | accepted slice |
| `P5 Validation Evidence` | Capture browser, syntax, and regression evidence. | Implementation clusters pass local checks. | Evidence doc records screenshots, console status, and residuals. | planned |
| `P6 Closure And Archive Sync` | Decide accepted/held/next-slice state and sync indexes. | `P5` evidence is complete. | README/status/archive surfaces agree on current authority. | planned |

## Task Clusters

- Finite task cluster plan:
  [tactical_map_interface_refactor_task_clusters_20260606.md](tactical_map_interface_refactor_task_clusters_20260606.md)
- Dispatch queue:
  [tactical_map_interface_refactor_dispatch_queue_20260606.md](tactical_map_interface_refactor_dispatch_queue_20260606.md)
- P1 shell-layout acceptance:
  [tactical_map_interface_refactor_p1_shell_layout_acceptance_20260606.md](tactical_map_interface_refactor_p1_shell_layout_acceptance_20260606.md)
- P2 workspace acceptance:
  [tactical_map_interface_refactor_p2_workspace_acceptance_20260606.md](tactical_map_interface_refactor_p2_workspace_acceptance_20260606.md)
- P3 layer/symbology acceptance:
  [tactical_map_interface_refactor_p3_layer_symbology_acceptance_20260606.md](tactical_map_interface_refactor_p3_layer_symbology_acceptance_20260606.md)
- P4 profile-default acceptance:
  [tactical_map_interface_refactor_p4_profile_defaults_acceptance_20260606.md](tactical_map_interface_refactor_p4_profile_defaults_acceptance_20260606.md)

## Outputs And Evidence

Expected maintained outputs:

- Updated `examples/viz/web_viz/templates/index.html` tactical shell and map
  workspace implementation.
- Optional focused profile-loader tests if profile UI defaults are extended.
- Browser smoke screenshots for narrow and desktop map layouts.
- Syntax checks for embedded module scripts and any Python touched by the
  profile/session surface.
- Acceptance or closeout evidence before status changes to accepted or closed.

## Acceptance Gate

This subproject can be marked accepted only when:

- The tactical map remains visible and primary on at least one narrow viewport
  and one desktop viewport.
- The interface supports multiple map surfaces or a clearly documented first
  accepted subset of the workspace model.
- Layer controls are grouped and responsive; they do not push the map below the
  useful first viewport.
- Existing naval, air, and ground smoke profiles still load without browser
  console errors attributable to this refactor.
- Profile defaults remain visualization/runtime UI preferences and do not
  mutate scenario realism/world parameters.
- Documentation refuses military-standard compliance and simulation-behavior
  claims that were not implemented and tested.

## Residuals And Next Steps

Immediate:

- Roll up `P1` through `P4` validation evidence in `VIZ-TMAP-P5`.
- Keep `P1`/`P2`/`P3`/`P4` evidence current if later UI work touches the same
  template or profile-loader blocks.

Follow-on:

- Add richer terrain/building/road/vegetation layer rendering after the common
  environment substrate exposes accepted derived products.
- Consider a dedicated tactical symbol registry after the layer model proves
  useful in the current template.

Deferred:

- Standard-compliant military symbology.
- Scenario editing, terrain generator UI, and environment-runtime behavior.

## Archive

No local records are archived yet. Future superseded notes move under
[archive/README.md](archive/README.md) after this README or a dated status file
promotes the replacement authority.
