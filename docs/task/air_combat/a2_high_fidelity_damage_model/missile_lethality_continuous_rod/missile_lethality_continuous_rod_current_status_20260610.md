# A2 MLF-4 Current Status

Status: `2026-06-11` active planning. MLF-4 exists as a separate continuous-rod/cutting subproject; `MLF-4A-X1`, `MLF-4B-W1-R2`, `MLF-4C-W1`, and `MLF-4D-W1` are accepted. `MLF-4E-W1` is ready to dispatch.

Chinese main text: [missile_lethality_continuous_rod_current_status_20260610.zh.md](missile_lethality_continuous_rod_current_status_20260610.zh.md)

## What Changed

- Created an MLF-4 planning surface separate from archived MLF-2 and MLF-3.
- Recorded that the current code already has reusable rod/cut fields and candidate `continuous_rod` branches.
- Accepted `MLF-4A-X1` read-only inventory through main-thread recovery review.
- Accepted `MLF-4B-W1-R2` test-first standard event surface after local verification.
- Accepted `MLF-4C-W1` generic rod geometry after local verification.
- Accepted `MLF-4D-W1` component cut projection after local verification.
- Kept component failure, structural breakup, debris/wreck, Pk, and real weapon calibration outside this phase.

## Maturity Matrix

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Subproject docs | active planning | README, task clusters, current status, dispatch queue, archive index | Not runtime acceptance |
| 4A read-only inventory | accepted slice | [missile_lethality_continuous_rod_inventory_20260610.md](missile_lethality_continuous_rod_inventory_20260610.md) | Proves inventory completion only, not runtime behavior |
| Existing rod fields | accepted standard event surface | `rod_cut_margin` fields in standard events/effects records plus [test_mlf4_standard_rod_event_surface.py](../../../../../tests/runtime/air_combat/test_mlf4_standard_rod_event_surface.py) | Cutting facts only, not failure |
| Existing continuous_rod behavior | accepted for event-surface, generic-geometry, and component-projection slices | focused MLF-4B/4C/4D tests plus retained historical tests | Diagnostics and final closeout remain open |
| Standard rod event surface | accepted slice | `MLF-4B-W1-R2` local verification | No new event fields or default constants |
| Generic rod geometry | accepted slice | [test_mlf4_generic_rod_geometry.py](../../../../../tests/runtime/air_combat/test_mlf4_generic_rod_geometry.py) | No true weapon parameters |
| Component cut projection | accepted slice | [test_mlf4_component_cut_projection.py](../../../../../tests/runtime/air_combat/test_mlf4_component_cut_projection.py) | No component failure probability or integrity mutation |
| Diagnostics and gates | ready for dispatch | 4E cluster | No kill/crash/structural conclusion |

## Residual Register

- Need 4E diagnostics to explain rod/cut facts from standard events.

## Recommended Action Order

1. Dispatch `MLF-4E-W1 Diagnostics And Gates`.
2. Make diagnostics explain standard rod/cut facts without false rod rows.
3. Close MLF-4 only as a cutting-fact chain, not as failure or breakup.

## Overclaim Refusals

- Do not claim a target is cut apart merely because `rod_cut_margin` is positive.
- Do not claim component failure before MLF-5.
- Do not claim structural breakup before MLF-6.
- Do not claim debris/wreck before MLF-8.
- Do not claim Pk or real AIM-120C/MQ-9 lethality before a later calibration gate.
