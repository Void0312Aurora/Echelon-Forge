# Tactical Map Interface Refactor Current Status

Status: `2026-06-06` `P0` pass, `P1` shell layout accepted as a slice,
`P2` map workspace accepted as a slice, and `P3` layer/symbology grouping
accepted as a slice.

Parent: [Tactical Map Interface Refactor](README.md)

## What Changed At This Checkpoint

- Created a durable `docs/task/viz` subproject for the tactical map interface
  refactor.
- Added a finite cluster plan so future UI work is not driven by chat-only
  follow-ups.
- Added a style/reference baseline for realistic tactical-map, GIS, COP, and
  OSINT-inspired presentation without claiming standard compliance.
- Linked the subproject from the parent viz README.
- Opened the first dispatch queue and assigned `VIZ-TMAP-P1-DIAG-A` as a
  read-only preflight packet before runtime implementation.
- Accepted `VIZ-TMAP-P1-DIAG-A` as `pass` for diagnostics only.
- Implemented and accepted `VIZ-TMAP-P1` as a map-first shell layout in
  [index.html](../../../../examples/viz/web_viz/templates/index.html).
- Added collapsible `SETUP` and `DATA` docks while preserving the existing
  profile/scenario/asset/run/layer/telemetry/unit DOM IDs.
- Added a UI-only scenario-only profile placeholder so direct scenario loads do
  not appear to be using the first profile.
- Recorded P1 browser, syntax, and focused overlay evidence in
  [P1 shell-layout acceptance](tactical_map_interface_refactor_p1_shell_layout_acceptance_20260606.md).
- Implemented and accepted `VIZ-TMAP-P2` as a tabbed map-workspace model in
  [index.html](../../../../examples/viz/web_viz/templates/index.html).
- Added `COP`, `Environment`, `Tracks/Sensors`, and `3D Inspect` surfaces with
  explicit UI roles and default layer postures.
- Added focused static coverage in
  [test_tactical_map_workspace.py](../../../../tests/viz/test_tactical_map_workspace.py).
- Recorded P2 browser, syntax, and focused regression evidence in
  [P2 workspace acceptance](tactical_map_interface_refactor_p2_workspace_acceptance_20260606.md).
- Implemented and accepted `VIZ-TMAP-P3` as grouped tactical layer controls,
  centralized draw phases, and first-pass symbology styling in
  [index.html](../../../../examples/viz/web_viz/templates/index.html).
- Added focused static coverage in
  [test_tactical_layer_model.py](../../../../tests/viz/test_tactical_layer_model.py).
- Recorded P3 browser, syntax, and focused regression evidence in
  [P3 layer/symbology acceptance](tactical_map_interface_refactor_p3_layer_symbology_acceptance_20260606.md).

## Maturity Matrix

| Surface | Status | Evidence | Residual |
| --- | --- | --- | --- |
| Subproject authority | pass | [README.md](README.md) | Keep current after implementation starts. |
| Task clusters | pass | [task clusters](tactical_map_interface_refactor_task_clusters_20260606.md) | Dispatch must stay within finite clusters and round caps. |
| Style/reference baseline | pass | [style baseline](tactical_map_interface_refactor_style_reference_baseline_20260606.md) | Needs implementation evidence before accepted UI claims. |
| Runtime shell layout | accepted slice | [P1 acceptance](tactical_map_interface_refactor_p1_shell_layout_acceptance_20260606.md) | Does not accept layer grouping, profile defaults, or new simulation behavior. |
| Multi-map workspace | accepted slice | [P2 acceptance](tactical_map_interface_refactor_p2_workspace_acceptance_20260606.md) | Tabbed surfaces only; split-map layout remains deferred. |
| Layer and symbology model | accepted slice | [P3 acceptance](tactical_map_interface_refactor_p3_layer_symbology_acceptance_20260606.md) | Grouped UI controls and first-pass styling only; no standard-compliance or payload semantics claim. |
| Profile UI defaults | planned/held until needed | [profile_loader.py](../../../../examples/viz/app/profile_loader.py) | Only add after `P3` layer defaults are stable enough to persist. |

## Next Recommended Action Order

1. Extend profile UI defaults in `VIZ-TMAP-P4` only if the runtime UI needs
   stable persisted defaults.
2. Record browser smoke, screenshots, and residuals in `VIZ-TMAP-P5` as later
   implementation slices land.

## Explicit Overclaim Refusals

- This checkpoint does not accept the full tactical-map interface refactor.
- This checkpoint accepts the first tabbed map-workspace slice and grouped
  layer/symbology slice only; it does not accept split-map layout.
- This checkpoint does not prove military-standard symbology compliance.
- This checkpoint does not release terrain-aware movement, LOS, cover,
  passability, weather effects, combat behavior, or environment-runtime
  mutation.
- This checkpoint does not change the scenario/profile boundary.
