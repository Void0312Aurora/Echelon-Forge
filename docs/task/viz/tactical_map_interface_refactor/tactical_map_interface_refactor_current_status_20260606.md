# Tactical Map Interface Refactor Current Status

Status: `2026-06-06` closed. `P0` pass; `P1` shell layout, `P2` map
workspace, `P3` layer/symbology grouping, `P4` profile UI defaults, and `P5`
validation roll-up accepted; `P6` closure/archive sync complete.

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
- Implemented and accepted `VIZ-TMAP-P4` profile UI defaults for default
  tactical workspace and layer selection in
  [profile_loader.py](../../../../examples/viz/app/profile_loader.py) and
  [index.html](../../../../examples/viz/web_viz/templates/index.html).
- Added focused profile/default regression coverage in
  [test_tactical_profile_ui_defaults.py](../../../../tests/viz/test_tactical_profile_ui_defaults.py).
- Updated viz profile fixtures so the air forced-fire profile can persist full
  COP layer defaults and the naval contact-report profile can default to the
  `TRACKS` workspace.
- Realigned naval viz profiles with the maintained `naval_station3` action
  surface so profile smoke loading reaches `READY`.
- Recorded P4 browser, syntax, JSON, and focused regression evidence in
  [P4 profile-default acceptance](tactical_map_interface_refactor_p4_profile_defaults_acceptance_20260606.md).
- Accepted `VIZ-TMAP-P5` as the evidence roll-up for `P1` through `P4`, including
  fresh module syntax, focused pytest, and profile JSON validation in
  [P5 validation roll-up](tactical_map_interface_refactor_p5_validation_rollup_20260606.md).
- Accepted `VIZ-TMAP-P6` as the closure/archive synchronization slice in
  [P6 closure/archive sync](tactical_map_interface_refactor_p6_closure_archive_sync_20260606.md).
- Synchronized the parent viz README, this README/status, task clusters,
  dispatch queue, and archive pointers so the scoped refactor is now `closed`.

## Maturity Matrix

| Surface | Status | Evidence | Residual |
| --- | --- | --- | --- |
| Subproject authority | closed | [README.md](README.md) | Current authority is synchronized by `P6`; future work needs a new cluster. |
| Task clusters | closed | [task clusters](tactical_map_interface_refactor_task_clusters_20260606.md) | `P0` through `P6` are complete; new work should not reopen this queue. |
| Style/reference baseline | pass | [style baseline](tactical_map_interface_refactor_style_reference_baseline_20260606.md) | Reference material guides style only; it is not a standards-compliance claim. |
| Runtime shell layout | accepted slice | [P1 acceptance](tactical_map_interface_refactor_p1_shell_layout_acceptance_20260606.md) | Does not accept layer grouping, profile defaults, or new simulation behavior. |
| Multi-map workspace | accepted slice | [P2 acceptance](tactical_map_interface_refactor_p2_workspace_acceptance_20260606.md) | Tabbed surfaces only; split-map layout remains deferred. |
| Layer and symbology model | accepted slice | [P3 acceptance](tactical_map_interface_refactor_p3_layer_symbology_acceptance_20260606.md) | Grouped UI controls and first-pass styling only; no standard-compliance or payload semantics claim. |
| Profile UI defaults | accepted slice | [P4 acceptance](tactical_map_interface_refactor_p4_profile_defaults_acceptance_20260606.md) | UI preferences only; no scenario or simulation semantics mutation. |
| Validation roll-up | accepted | [P5 validation roll-up](tactical_map_interface_refactor_p5_validation_rollup_20260606.md) | Evidence consolidation only; no runtime feature added. |
| Closure/archive sync | closed | [P6 closure/archive sync](tactical_map_interface_refactor_p6_closure_archive_sync_20260606.md) | Closes the scoped refactor only; future tactical visualization work needs a new cluster. |

## Next Recommended Action Order

1. Treat this tactical-map interface refactor as closed.
2. Open a new task cluster or subproject for richer environment-derived layers,
   split-map layout, symbol registry extraction, or other future tactical
   visualization work.

## Explicit Overclaim Refusals

- This closeout accepts only the scoped first tactical-map interface refactor
  documented by `P1` through `P6`; it does not accept all future tactical
  visualization ideas.
- This closeout does not accept split-map layout.
- This closeout does not prove military-standard symbology compliance.
- This closeout does not release terrain-aware movement, LOS, cover,
  passability, weather effects, combat behavior, or environment-runtime
  mutation.
- This closeout does not change the scenario/profile boundary.
