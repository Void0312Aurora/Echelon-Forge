# A2 MLF-4 Current Status

Status: `2026-06-11` accepted / archived. MLF-4 is closed as a separate continuous-rod/cutting subproject; `MLF-4A-X1`, `MLF-4B-W1-R2`, `MLF-4C-W1`, `MLF-4D-W1`, `MLF-4E-W1`, and `MLF-4F-C1` are accepted.

Chinese main text: [missile_lethality_continuous_rod_current_status_20260610.zh.md](missile_lethality_continuous_rod_current_status_20260610.zh.md)

## What Changed

- Created an MLF-4 planning surface separate from archived MLF-2 and MLF-3.
- Recorded that the current code already has reusable rod/cut fields and candidate `continuous_rod` branches.
- Accepted `MLF-4A-X1` read-only inventory through main-thread recovery review.
- Accepted `MLF-4B-W1-R2` test-first standard event surface after local verification.
- Accepted `MLF-4C-W1` generic rod geometry after local verification.
- Accepted `MLF-4D-W1` component cut projection after local verification.
- Accepted `MLF-4E-W1` diagnostics and gates after main-thread implementation and local verification.
- Closed `MLF-4F-C1` by archiving accepted/held state, test evidence, and follow-on phase boundaries.
- Kept component failure, structural breakup, debris/wreck, Pk, and real weapon calibration outside this phase.

## Maturity Matrix

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Subproject docs | accepted / archived | README, task clusters, current status, dispatch queue, archive index, closeout acceptance | Accepts only the MLF-4 cutting-fact chain |
| 4A read-only inventory | accepted slice | [missile_lethality_continuous_rod_inventory_20260610.md](missile_lethality_continuous_rod_inventory_20260610.md) | Proves inventory completion only, not runtime behavior |
| Existing rod fields | accepted standard event surface | `rod_cut_margin` fields in standard events/effects records plus [test_continuous_rod_event_surface.py](../../../../../../../tests/runtime/air_combat/test_continuous_rod_event_surface.py) | Cutting facts only, not failure |
| Existing continuous_rod behavior | accepted for event-surface, generic-geometry, component-projection, diagnostic, and closeout slices | focused MLF-4B/4C/4D/4E tests plus closeout acceptance | Does not directly claim failure or structural consequence |
| Standard rod event surface | accepted slice | `MLF-4B-W1-R2` local verification | No new event fields or default constants |
| Generic rod geometry | accepted slice | [test_continuous_rod_geometry_response.py](../../../../../../../tests/runtime/air_combat/test_continuous_rod_geometry_response.py) | No true weapon parameters |
| Component cut projection | accepted slice | [test_continuous_rod_component_cut_projection.py](../../../../../../../tests/runtime/air_combat/test_continuous_rod_component_cut_projection.py) | No component failure probability or integrity mutation |
| Diagnostics and gates | accepted slice | [test_continuous_rod_diagnostic_projection.py](../../../../../../../tests/runtime/air_combat/test_continuous_rod_diagnostic_projection.py) | No kill/crash/structural conclusion |

## Residual Register

- MLF-5 consumes rod/cut facts for component failure probability.
- MLF-6 consumes component failure for structural breakup.
- MLF-8/MLF-9 still need separate follow-on subprojects for debris lifecycle and Pk/statistical trends.

## Recommended Action Order

1. Do not continue dispatch inside MLF-4.
2. Create MLF-5 as a separate `docs/agent` subproject before entering component failure.
3. Archive MLF-4 only as a cutting-fact chain, not as failure or breakup.

## Overclaim Refusals

- Do not claim a target is cut apart merely because `rod_cut_margin` is positive.
- Do not claim component failure before MLF-5.
- Do not claim structural breakup before MLF-6.
- Do not claim debris/wreck before MLF-8.
- Do not claim Pk or real AIM-120C/MQ-9 lethality before a later calibration gate.
