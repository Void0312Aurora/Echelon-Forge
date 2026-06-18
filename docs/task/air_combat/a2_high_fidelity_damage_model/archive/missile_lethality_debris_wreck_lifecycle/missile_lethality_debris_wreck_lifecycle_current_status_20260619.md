# MLF-8 Current Status

Status: `2026-06-19` accepted / archived. P0 setup, P1 inventory, P2 lifecycle
contract, P3 focused runtime representation, P4 diagnostics/facade exposure,
P5 focused validation, P6 broader smoke, and P7 acceptance/archive are
complete for the diagnostics-only MLF-8 slice.

Chinese companion:
[missile_lethality_debris_wreck_lifecycle_current_status_20260619.zh.md](missile_lethality_debris_wreck_lifecycle_current_status_20260619.zh.md).

## Summary

MLF-8 covered the debris/wreck lifecycle work that was explicitly deferred by
MLF-6, MLF-7, and A8. P1 confirmed that the initial runtime slice should be a
thin lifecycle-event layer, not a new aircraft-damage model. P2 accepted
`LifecycleTransitionEvent` as the base carrier and forbids first-class
debris/wreck entities in the base slice. P3 added diagnostics-only lifecycle
event writing and reward non-leakage. P4/P5 made those rows visible through the
facade/binding/diagnostic surfaces and covered the accepted lifecycle
validation paths. P6 broader smoke passed, and P7 archived the evidence packet.

## Status Table

| Area | Status | Evidence | Next action |
| --- | --- | --- | --- |
| Subproject shell | complete / archived | README, task clusters, contract surface, dispatch queue, acceptance record, archive placeholder, and parent navigation exist | Keep synchronized through registry |
| Upstream facts | complete / inventory-pass | MLF-6 `StructuralBreakupEvent` and MLF-7 diagnostics-only `PlatformConsequenceEvent` are reusable | Consumed by accepted contract |
| Runtime representation | complete / focused-pass | Recorder/store lifecycle writer exists; structural breakup writes detached-part lifecycle rows; chain-linked terminal wreck helper writes diagnostics-only terminal rows | Accepted base slice |
| Lifecycle events | complete / focused-pass | Runtime emits diagnostics-only detached-part lifecycle rows and supports terminal wreck rows without entity spawning | Keep in acceptance evidence |
| Diagnostics/facade exposure | complete / focused-pass | Facade packets append/sort lifecycle rows; binding/contract shape covers terminal fields; diagnostics probe projects `LifecycleTransitionEvent` rows and snapshot fields | Accepted base slice |
| Validation | complete / focused-pass | Focused C++/Python lanes cover no-breakup, single and multi-axis detached-part lifecycle rows, terminal wreck helper, facade/binding/probe exposure, and reward non-leakage | Accepted base slice |
| Reward boundary | complete / focused-pass | Reward ignores diagnostics-only lifecycle transition events before terminal/reward projection | Keep in acceptance evidence |
| Broader smoke | complete / smoke-pass | Full CTest passes; focused P4/P5 lanes pass; geometry/edge smoke passes; broader air-combat+engagement smoke passes | Recorded in acceptance |
| Calibration authority | refused | Debris evidence gates remain fail-closed | Keep out of MLF-8 acceptance |

## Recommended Next Work

1. Keep MLF-9 Pk/statistical trend projection and MLF-10 calibration gates as
   separate follow-on subprojects.
2. Reopen MLF-8 only for a clearly scoped follow-on, such as first-class
   debris entity contracts, debris-to-secondary-damage interaction, or visual
   debris rendering.

## Current Risks

- Future work could confuse original entity retirement with first-class
  wreck/debris objects.
- Future work could let diagnostics-only lifecycle facts leak into reward
  shaping if visibility changes without a new contract.
- Future work could treat `detached_part_ref` labels as calibrated debris
  physics.
- Future work could reopen archived MLF-6 or MLF-7 work instead of consuming
  their accepted outputs.
- Future work could double-count existing ground-crash reward behavior through
  new lifecycle rows.

## Held Items

- Pk/statistical projection: MLF-9.
- Calibration and selected debris-output evidence admission: MLF-10 or later.
- Visual debris rendering: future visual/runtime work.
