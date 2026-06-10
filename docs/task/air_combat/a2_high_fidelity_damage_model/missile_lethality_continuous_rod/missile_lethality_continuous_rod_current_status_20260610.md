# A2 MLF-4 Current Status

Status: `2026-06-10` active planning. MLF-4 exists as a separate continuous-rod/cutting subproject; `MLF-4A-X1` read-only inventory is accepted, and no implementation slice is accepted yet.

Chinese main text: [missile_lethality_continuous_rod_current_status_20260610.zh.md](missile_lethality_continuous_rod_current_status_20260610.zh.md)

## What Changed

- Created an MLF-4 planning surface separate from archived MLF-2 and MLF-3.
- Recorded that the current code already has reusable rod/cut fields and candidate `continuous_rod` branches.
- Accepted `MLF-4A-X1` read-only inventory through main-thread recovery review.
- Kept component failure, structural breakup, debris/wreck, Pk, and real weapon calibration outside this phase.

## Maturity Matrix

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Subproject docs | active planning | README, task clusters, current status, dispatch queue, archive index | Not runtime acceptance |
| 4A read-only inventory | accepted slice | [missile_lethality_continuous_rod_inventory_20260610.md](missile_lethality_continuous_rod_inventory_20260610.md) | Proves inventory completion only, not runtime behavior |
| Existing rod fields | reusable scaffold | `rod_cut_margin` fields in standard events and effects records | Semantics not accepted by MLF-4B yet |
| Existing continuous_rod behavior | candidate scaffold | default effects `continuous_rod` branches and historical tests | Historical tests are retained scaffold only |
| Standard rod event surface | ready for dispatch | 4B cluster | Not implemented/accepted |
| Generic rod geometry | planned | 4C cluster | No true weapon parameters |
| Component cut projection | planned | 4D cluster | No component failure probability |
| Diagnostics and gates | planned | 4E cluster | No kill/crash/structural conclusion |

## Residual Register

- Need 4B to lock the standard-event semantics of existing `rod_cut_margin` fields; 4A recommends reusing existing fields before adding a dedicated event.
- Need focused MLF-4 tests that are separate from retained historical Phase 3 tests.
- Need no-detonation and non-rod guards for positive rod/cut facts.

## Recommended Action Order

1. Dispatch `MLF-4B-W1 Standard Rod Event Surface`.
2. Decide the event-surface shape before changing runtime logic.
3. Validate generic rod geometry before component projection.
4. Add diagnostics and guard tests after the standard event surface is stable.
5. Close MLF-4 only as a cutting-fact chain, not as failure or breakup.

## Overclaim Refusals

- Do not claim a target is cut apart merely because `rod_cut_margin` is positive.
- Do not claim component failure before MLF-5.
- Do not claim structural breakup before MLF-6.
- Do not claim debris/wreck before MLF-8.
- Do not claim Pk or real AIM-120C/MQ-9 lethality before a later calibration gate.
