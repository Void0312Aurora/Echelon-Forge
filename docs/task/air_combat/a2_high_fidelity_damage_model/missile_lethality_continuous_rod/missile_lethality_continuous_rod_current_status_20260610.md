# A2 MLF-4 Current Status

Status: `2026-06-11` active planning. MLF-4 exists as a separate continuous-rod/cutting subproject; `MLF-4A-X1`, `MLF-4B-W1-R2`, `MLF-4C-W1`, `MLF-4D-W1`, and `MLF-4E-W1` are accepted. `MLF-4F-C1` is ready for closeout/archive preparation.

Chinese main text: [missile_lethality_continuous_rod_current_status_20260610.zh.md](missile_lethality_continuous_rod_current_status_20260610.zh.md)

## What Changed

- Created an MLF-4 planning surface separate from archived MLF-2 and MLF-3.
- Recorded that the current code already has reusable rod/cut fields and candidate `continuous_rod` branches.
- Accepted `MLF-4A-X1` read-only inventory through main-thread recovery review.
- Accepted `MLF-4B-W1-R2` test-first standard event surface after local verification.
- Accepted `MLF-4C-W1` generic rod geometry after local verification.
- Accepted `MLF-4D-W1` component cut projection after local verification.
- Accepted `MLF-4E-W1` diagnostics and gates after main-thread implementation and local verification.
- Kept component failure, structural breakup, debris/wreck, Pk, and real weapon calibration outside this phase.

## Maturity Matrix

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Subproject docs | active planning | README, task clusters, current status, dispatch queue, archive index | Not runtime acceptance |
| 4A read-only inventory | accepted slice | [missile_lethality_continuous_rod_inventory_20260610.md](missile_lethality_continuous_rod_inventory_20260610.md) | Proves inventory completion only, not runtime behavior |
| Existing rod fields | accepted standard event surface | `rod_cut_margin` fields in standard events/effects records plus [test_continuous_rod_event_surface.py](../../../../../tests/runtime/air_combat/test_continuous_rod_event_surface.py) | Cutting facts only, not failure |
| Existing continuous_rod behavior | accepted for event-surface, generic-geometry, component-projection, and diagnostic slices | focused MLF-4B/4C/4D/4E tests plus retained historical tests | Final closeout remains open |
| Standard rod event surface | accepted slice | `MLF-4B-W1-R2` local verification | No new event fields or default constants |
| Generic rod geometry | accepted slice | [test_continuous_rod_geometry_response.py](../../../../../tests/runtime/air_combat/test_continuous_rod_geometry_response.py) | No true weapon parameters |
| Component cut projection | accepted slice | [test_continuous_rod_component_cut_projection.py](../../../../../tests/runtime/air_combat/test_continuous_rod_component_cut_projection.py) | No component failure probability or integrity mutation |
| Diagnostics and gates | accepted slice | [test_continuous_rod_diagnostic_projection.py](../../../../../tests/runtime/air_combat/test_continuous_rod_diagnostic_projection.py) | No kill/crash/structural conclusion |

## Residual Register

- Need 4F to summarize 4A-4E accepted/held boundaries and sync the README, current-status, dispatch, and archive entry points.

## Recommended Action Order

1. Execute `MLF-4F-C1 Acceptance And Archive Prep`.
2. Sync accepted/held state, test evidence, and follow-on phase boundaries.
3. Close MLF-4 only as a cutting-fact chain, not as failure or breakup.

## Overclaim Refusals

- Do not claim a target is cut apart merely because `rod_cut_margin` is positive.
- Do not claim component failure before MLF-5.
- Do not claim structural breakup before MLF-6.
- Do not claim debris/wreck before MLF-8.
- Do not claim Pk or real AIM-120C/MQ-9 lethality before a later calibration gate.
