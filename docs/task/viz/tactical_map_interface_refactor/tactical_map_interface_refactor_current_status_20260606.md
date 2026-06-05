# Tactical Map Interface Refactor Current Status

Status: `2026-06-06` `P0` pass, `P1` shell layout accepted as a slice,
`P2` map workspace planned next.

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

## Maturity Matrix

| Surface | Status | Evidence | Residual |
| --- | --- | --- | --- |
| Subproject authority | pass | [README.md](README.md) | Keep current after implementation starts. |
| Task clusters | pass | [task clusters](tactical_map_interface_refactor_task_clusters_20260606.md) | Dispatch must stay within finite clusters and round caps. |
| Style/reference baseline | pass | [style baseline](tactical_map_interface_refactor_style_reference_baseline_20260606.md) | Needs implementation evidence before accepted UI claims. |
| Runtime shell layout | accepted slice | [P1 acceptance](tactical_map_interface_refactor_p1_shell_layout_acceptance_20260606.md) | Does not accept multi-map workspace or new simulation behavior. |
| Multi-map workspace | planned | no maintained implementation yet | Needs `P2` implementation and browser evidence. |
| Profile UI defaults | planned/held until needed | [profile_loader.py](../../../../examples/viz/app/profile_loader.py) | Only add after workspace/layer defaults are concrete. |

## Next Recommended Action Order

1. Decide whether `VIZ-TMAP-P2` first lands tabbed maps or a split-map mode.
2. Add grouped layer/symbology rules in `VIZ-TMAP-P3`.
3. Extend profile UI defaults in `VIZ-TMAP-P4` only if the runtime UI needs
   stable persisted defaults.
4. Record browser smoke, screenshots, and residuals in `VIZ-TMAP-P5` as later
   implementation slices land.

## Explicit Overclaim Refusals

- This checkpoint does not accept the full tactical-map interface refactor.
- This checkpoint does not accept a multi-map runtime workspace.
- This checkpoint does not prove military-standard symbology compliance.
- This checkpoint does not release terrain-aware movement, LOS, cover,
  passability, weather effects, combat behavior, or environment-runtime
  mutation.
- This checkpoint does not change the scenario/profile boundary.
