# MLF-6 Structural Failure — Acceptance

Status: `2026-06-18` accepted / archived v10 gate. P1/P2 design inputs,
P3 state machine evidence, P4 event-writer evidence, P5 diagnostic export
evidence, P6 focused validation evidence, and P7 broad-regression evidence
are collected. P7 obsolete-oracle updates now produce a clean full
air_combat/world_batch lane (`447 passed`). v10 additionally validates that
continuous-rod beam-side proxy standoff cases produce `wing_loss` through
`4 m`, while `8 m` and `14 m` remain non-breakup. Archive movement is complete
by explicit user instruction.

## Acceptance Scope

This subproject can be marked `accepted` when the user approves the package
below. `[x]` = met. `[~]` = intentionally held by instruction.

## MLF-6A: Boundary And Index (P0)

- [x] MLF-6 v2 README exists with D1-D7 frozen, corrected MLF-6/MLF-7 boundary,
  and 7-phase plan (P0-P7).
- [x] Task clusters, current status, dispatch queue, and acceptance draft exist
  and are internally consistent.
- [x] Parent A2 README registers MLF-6 as accepted / archived evidence.
- [x] Air combat README links MLF-6 in current-priority section.
- [x] All forbidden claims listed in README remain refused.

## MLF-6B: Component Inventory (P1)

- [x] Every `ComponentDamageState` field is listed with type, source file, and
  whether MLF-6 reads it.
- [x] Every F-16C component name from `f16c_block50.json` is listed with its
  system group and structural parent region (from TG-P7 split receivers).
- [x] Every `structural_integrity` write site is listed as a forbidden-touch
  surface.
- [x] Every adjacent damage/effects propagation write to `FlightModel`,
  `Propulsion`, `Health`, and `PlatformDamageState` is listed as a
  forbidden-touch surface.
- [x] Inventory is read-only; no runtime changes.

## MLF-6C: Break-Mode Mapping (P2)

- [x] Every F-16C component is classified into exactly one structural group
  (`wing_left`, `wing_right`, `tail_left`, `tail_right`, `vertical_tail`,
  `engine_left`, `engine_right`, `fuselage`, or `none`), except the documented
  default-DB `wing_spar_center` cross-region case which contributes to both
  `wing_left` and `wing_right`.
- [x] Each structural group has an explicit cumulative integrity-drop threshold
  that triggers its break mode.
- [x] Thresholds are justified by engineering rationale (not arbitrary).
- [x] Near-field cumulative wing-loss rule handles close continuous-rod `cut`
  damage without relaxing all break-mode thresholds.
- [x] Mapping table is a design doc only; no implementation without explicit
  approval.

## MLF-6D: State Machine (P3)

- [x] `StructuralFailureUpdate` ECS system compiles and registers after
  `AircraftDamageStateUpdate`.
- [x] System reads `ComponentDamageState` via ECS query fields.
- [x] New `StructuralBreakupState` ECS component (D7) is defined and attached
  to aircraft entities.
- [x] `StructuralBreakupState` holds `breakup_state` (intact →
  partial_detachment → partial_breakup → full_breakup) and active `break_mode`
  bitmask.
- [x] State is irreversible and cumulative (per D4): component values only
  transition forward; there is no code path reverting `full_breakup` → `intact`.
- [x] Multiple break modes can activate in the same timestep (per D4).
- [x] System does NOT modify any *existing* ECS component (per D2):
  `structural_integrity`, `FlightModel`, `Propulsion`, `Health`,
  `PlatformDamageState` remain untouched.
- [x] `ef_test --test-suite=structural_failure_state` passes.

## MLF-6E: Event Writer (P4)

- [x] `StructuralBreakupEvent` rows are written to
  `RecentEngagementEvents::structural_breakup_events` when a new break mode
  activates or breakup_state advances.
- [x] `breakup_state` field matches the state machine's current state.
- [x] `break_mode` field names the triggering break mode.
- [x] `detached_part_ref` is a stable string label (per D3).
- [x] `detached_part_count` increments correctly when new parts detach.
- [x] `airframe_breakup` is `true` only when `breakup_state == full_breakup`.
- [x] `cause_event_id` references the most recent `ComponentDamageEvent::event_id`
  for the contributing component group when such an event row exists. Near-field
  deterministic cut-state breakups may report `0` when the stochastic
  component-damage event row was not emitted.
- [x] No-damage baseline produces zero events (no false positives).
- [x] System does NOT modify `structural_integrity`, `FlightModel`, `Propulsion`,
  `Health`, or `PlatformDamageState` (per D2).
- [x] `ef_test --test-suite=structural_failure_events` passes.

## MLF-6F: Diagnostics Export (P5)

- [x] Thin Python probe consumes existing `StructuralBreakupEvent` and
  `structural_breakup_events` bindings (`bindings_runtime.cpp:449-457`,
  `bindings_core.cpp`); no new binding surface introduced.
- [x] Probe exports `structural_breakup_events` per `chain_id`.
- [x] Export includes all `StructuralBreakupEvent` fields.
- [x] `pytest -q tests/tools/test_structural_breakup_export.py` passes.

## MLF-6G: Focused Tests (P6)

- [x] Controlled wing-spar failures produce `break_mode = wing_loss`.
- [x] Controlled stabilator failures produce `break_mode = tail_loss`.
- [x] Controlled engine-mount failures produce `break_mode = engine_detach`.
- [x] Controlled fuselage carrythrough failures produce `break_mode = fuselage_rupture`.
- [x] Multi-group failures (3+ families) produce `break_mode = multi_axis` and
  `breakup_state = full_breakup`. 1-family → `partial_detachment`, 2-family →
  `partial_breakup`.
- [x] No-damage baseline produces zero events.
- [x] Close continuous-rod wing-side cumulative cut damage produces `wing_loss`;
  functional cumulative wing damage still produces zero structural events.
- [x] State irreversibility is tested: once `wing_loss` is set in
  `StructuralBreakupState` (D7), restoring `ComponentDamageState` component
  integrity does not clear the `wing_loss` flag.

## MLF-6H: Zero-Regression Smoke (P7)

- [x] Full `tests/runtime/air_combat/` suite was executed as part of the
  combined P7 lane.
- [x] Full `tests/world_batch/` suite was executed as part of the combined P7
  lane.
- [x] `ctest --test-dir build-workshop -R ef_test_all --output-on-failure` passes.
- [x] Full combined P7 lane passes:
  `PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/ tests/world_batch/`
  → `447 passed`.

## MLF-6I: Acceptance And Archive (P7)

- [x] This acceptance checklist is complete and accepted for archive.
- [x] Current status doc reflects the v10 near-field cumulative calibration.
- [x] Dispatch queue is closed for implementation packets.
- [x] Parent A2 README registers MLF-6 under the local archive registry.
- [x] Air combat README reads MLF-6 as archived upstream evidence for MLF-7.
- [x] Residual map explicitly defers aerodynamics bridging, loss-state
  integration, wreck/debris lifecycle, and Pk to MLF-7 / MLF-8 / MLF-9.
- [x] Archive boundary clear: archive movement completed by explicit user instruction.

## Forbidden Claims (Must Remain Refused)

- [x] `pk_authority` remains `false`.
- [x] `deterministic_kill_authority` remains `false`.
- [x] `real_weapon_structural_kill_authority` remains `false`.
- [x] `wreck_debris_lifecycle_authority` remains `false` (MLF-8).
- [x] `flight_dynamics_modification_authority` remains `false` (MLF-7).
- [x] `structural_integrity_modification_authority` remains `false` (MLF-7).
- [x] `loss_state_modification_authority` remains `false` (MLF-7).
- [x] No AIM-120C, MQ-9, or specific platform/weapon structural-kill calibration.
- [x] No naval or ground platform structural models.
- [x] No direct crash/deletion rules.
- [x] No reopening of sealed MLF-1 through MLF-5 packages.

## Residual Register

| ID | Description | Severity | Status |
| --- | --- | --- | --- |
| MLF6-R2 | P5 diagnostics probe was not implemented yet. | low | closed by v5 focused export tests |
| MLF6-R3 | P7 full air_combat/world_batch regression smoke was initially red. | medium | closed by v8: `447 passed` |
| MLF6-R4 | Archive movement was previously deferred pending explicit user instruction. | medium | closed by 2026-06-18 local A2 archive move |
| MLF6-R5 | Close continuous-rod proxy standoff initially produced structure-damage deltas but zero breakup events. | medium | closed by v10: 43 standoff breakup records total; continuous_rod = 40, beam-side `0.5/1/2/4 m` records break, `8/14 m` records do not |
