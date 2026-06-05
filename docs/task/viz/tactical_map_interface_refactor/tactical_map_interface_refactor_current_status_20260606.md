# Tactical Map Interface Refactor Current Status

Status: `2026-06-06` `P0` pass, implementation not started.

Parent: [Tactical Map Interface Refactor](README.md)

## What Changed At This Checkpoint

- Created a durable `docs/task/viz` subproject for the tactical map interface
  refactor.
- Added a finite cluster plan so future UI work is not driven by chat-only
  follow-ups.
- Added a style/reference baseline for realistic tactical-map, GIS, COP, and
  OSINT-inspired presentation without claiming standard compliance.
- Linked the subproject from the parent viz README.

## Maturity Matrix

| Surface | Status | Evidence | Residual |
| --- | --- | --- | --- |
| Subproject authority | pass | [README.md](README.md) | Keep current after implementation starts. |
| Task clusters | pass | [task clusters](tactical_map_interface_refactor_task_clusters_20260606.md) | Dispatch must stay within finite clusters and round caps. |
| Style/reference baseline | pass | [style baseline](tactical_map_interface_refactor_style_reference_baseline_20260606.md) | Needs implementation evidence before accepted UI claims. |
| Runtime shell layout | planned | [index.html](../../../../examples/viz/web_viz/templates/index.html) | Map-first refactor not implemented yet. |
| Multi-map workspace | planned | no maintained implementation yet | Needs `P2` implementation and browser evidence. |
| Profile UI defaults | planned/held until needed | [profile_loader.py](../../../../examples/viz/app/profile_loader.py) | Only add after workspace/layer defaults are concrete. |

## Next Recommended Action Order

1. Run `VIZ-TMAP-P1` and rework the shell layout so the tactical map remains the
   primary first-viewport surface.
2. Decide whether `VIZ-TMAP-P2` first lands tabbed maps or a split-map mode.
3. Add grouped layer/symbology rules in `VIZ-TMAP-P3`.
4. Extend profile UI defaults in `VIZ-TMAP-P4` only if the runtime UI needs
   stable persisted defaults.
5. Record browser smoke, screenshots, and residuals in `VIZ-TMAP-P5`.

## Explicit Overclaim Refusals

- This checkpoint does not implement a new UI.
- This checkpoint does not accept a multi-map runtime workspace.
- This checkpoint does not prove military-standard symbology compliance.
- This checkpoint does not release terrain-aware movement, LOS, cover,
  passability, weather effects, combat behavior, or environment-runtime
  mutation.
- This checkpoint does not change the scenario/profile boundary.
