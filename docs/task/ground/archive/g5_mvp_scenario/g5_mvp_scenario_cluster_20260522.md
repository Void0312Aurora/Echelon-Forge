# G5 MVP Scenario Cluster

Status: `2026-05-22` implementation cluster for the first maintained ground
scenario smoke fixture.

## Decision

G5 selects the smallest safe scenario after G0-G4:

`ground_platoon_tasking_smoke_v1`

This scenario validates tasking-chain participation only:

`ScenarioLoader -> TaskOrder -> LeaderIntent -> PilotReport`.

It does not promote a real ground platform model. The entity uses `Aircraft`
as a compatibility spawn shell because the current G2 ground content seed is
deliberately not runtime-loadable JSON.

## Task Cluster

| Stream | Owner | Scope | Write set | Status |
|--------|-------|-------|-----------|--------|
| `G5-A` | main thread | Add minimal canonical scenario shell. | `scenarios/ground/ground_platoon_tasking_smoke_v1.json` | implemented |
| `G5-B` | main thread | Add focused loader/tasking validation. | `tests/runtime/ground/test_ground_mvp_scenario.py` | implemented |
| `G5-C` | main thread | Seal G0-G4 and open G5 navigation. | `docs/task/ground/**`, `docs/standards/ground/**`, `scenarios/README*.md` | implemented |
| `G5-D` | subagent preflight | Audit docs and scenario-loader boundaries. | read-only | returned |

## Acceptance Criteria

The cluster is accepted only if all checks below are true:

- The scenario file is under `scenarios/ground/` and is listed in
  `scenarios/README.md`.
- The scenario contains `tasking_profile = ground` and a `task_order` with
  `service_profile = Army`.
- The task is one of the accepted starter tasks from G0-G4; this cluster uses
  `TASK_OCCUPY` to avoid implying maintained movement runtime.
- The only entity is explicitly documented as a compatibility spawn shell,
  not a maintained ground unit schema.
- Loader validation proves the scenario produces Army/common-core
  `TaskOrder`, `LeaderIntent`, and `PilotReport` in the kernel.
- The test asserts the deferred runtime surfaces so the smoke scenario cannot
  be reused as evidence for movement, terrain, sensing, fires, damage,
  `CommandPacket`, `ObservationPacket`, or `TrackPacket`.
- G0-G4 are marked sealed in the ground entry docs, and G5 is the active
  follow-on slice.

## Validation

Run from repo root:

```powershell
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\ground\test_ground_mvp_scenario.py
```

Recommended compatibility check before closing a larger branch:

```powershell
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\mission\test_ground_runtime_lifecycle_bridge.py tests\leader\test_tasking_profile_contracts.py
```

## Residual Map

Held:

- runtime-loadable ground unit schema
- capability-bundle/public-platform lowering for real ground units
- movement, route traversal, terrain traversal, cover, concealment, and
  line-of-sight
- sensing, track fusion, shared tactical picture, and observation export
- direct fire, indirect fire, effects, damage, suppression, and combat
- formal `P3 CommandDelivery`
- formal `P10 ObservationExport`
- `CommandPacket`, `ObservationPacket`, and `TrackPacket`

Next credible expansion:

- add a real runtime-loadable ground platform only after the platform schema
  and capability lowering route are accepted
- then extend the scenario from tasking smoke to one scoped behavior slice
