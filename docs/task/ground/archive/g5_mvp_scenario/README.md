# G5 MVP Scenario

Status: `2026-05-22` accepted for the first minimal ground scenario shell.

Language:

- English canonical: `README.md`
- Chinese companion: not required yet; this is a high-churn task slice.

Inputs:

- [G4 runtime slice](../g4_runtime_slice/README.md)
- [Ground standards overview](../../../standards/ground/README.md)
- [Ground minimal task structure](../../../standards/ground/minimal_task_structure.md)
- [Scenarios README](../../../../scenarios/README.md)

## Purpose

Construct the smallest maintained ground MVP scenario after the accepted
G0-G4 baseline.

The MVP is intentionally a scenario smoke shell, not a land-combat model. It
must prove that a canonical `scenarios/ground/` fixture can drive the existing
shared loader and the accepted G4 tasking lifecycle:

`ScenarioLoader -> normalized ground TaskOrder -> LeaderIntent -> PilotReport`.

## Output

- [G5 MVP scenario cluster](g5_mvp_scenario_cluster_20260522.md)
- Canonical scenario:
  `scenarios/ground/ground_platoon_tasking_smoke_v1.json`
- Focused validation:
  `tests/runtime/ground/test_ground_mvp_scenario.py`

## Scope

In scope:

- one canonical ground scenario shell under `scenarios/ground/`
- explicit `tasking_profile = ground`
- Army service-profile task order using `TASK_OCCUPY`
- focused test coverage proving loader/tasking/profile status-chain behavior
- documentation that G0-G4 are now sealed as the accepted ground baseline

Out of scope:

- runtime-loadable ground unit schemas
- movement, terrain traversal, terrain masking, line-of-sight, sensing, fires,
  effects, damage, suppression, or combat
- formal `CommandPacket`, `ObservationPacket`, or `TrackPacket`
- formal `P3 CommandDelivery` or `P10 ObservationExport`
- broad `MissionCommand` expansion

## Acceptance Gate

G5 is accepted because all of the following are true:

- `scenarios/ground/ground_platoon_tasking_smoke_v1.json` loads through
  `ScenarioLoader` against the standard example database.
- The scenario resolves through the maintained `ground` tasking profile and
  produces Army/common-core `TaskOrder`, `LeaderIntent`, and `PilotReport`
  status objects in the kernel.
- The scenario documents that its single entity uses the current
  runtime-compatible `Aircraft` spawn shell and does not claim a maintained
  ground unit schema.
- The focused test explicitly checks the deferred surfaces so later work cannot
  accidentally treat this smoke fixture as movement, sensing, fires, damage, or
  observation-export evidence.
- G0-G4 docs are marked as sealed baseline, and G5 is listed as the accepted
  MVP scenario slice.

Validation command:

```powershell
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\ground\test_ground_mvp_scenario.py
```

## Residuals

- Promote a runtime-loadable ground unit schema only after capability-bundle or
  additive public-platform lowering is accepted.
- Keep movement, terrain, sensing, fires, effects, and damage in later scoped
  work packages.
- Open formal `P3`/`P10` work only after this MVP scenario remains stable as a
  tasking smoke baseline.
