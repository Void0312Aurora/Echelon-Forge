# MLF-6 Structural Failure — Acceptance

Status: `2026-06-17` v2 draft acceptance gate, corrected per P0 self-review.
No evidence collected yet.

## Acceptance Scope

This subproject can be marked `accepted` only when all `[ ]` items below are
resolved or explicitly deferred with residual entries. `[x]` = met. `[~]` =
partially met with residual.

## MLF-6A: Boundary And Index (P0)

- [ ] MLF-6 v2 README exists with D1-D6 frozen, corrected MLF-6/MLF-7 boundary,
  and 7-phase plan (P0-P7).
- [ ] Task clusters, current status, dispatch queue, and acceptance draft exist
  and are internally consistent.
- [ ] Parent A2 README links MLF-6 as active subproject.
- [ ] Air combat README links MLF-6 in current-priority section.
- [ ] All forbidden claims listed in README remain refused.

## MLF-6B: Component Inventory (P1)

- [ ] Every `ComponentDamageState` field is listed with type, source file, and
  whether MLF-6 reads it.
- [ ] Every F-16C component name from `f16c_block50.json` is listed with its
  system group and structural parent region (from TG-P7 split receivers).
- [ ] Every `structural_integrity` write site is listed as a forbidden-touch
  surface.
- [ ] Every `FlightModel`, `Propulsion`, `Health`, `PlatformDamageState` write
  site is listed as a forbidden-touch surface.
- [ ] Inventory is read-only; no runtime changes.

## MLF-6C: Break-Mode Mapping (P2)

- [ ] Every F-16C component is classified into exactly one structural group
  (`wing_left`, `wing_right`, `tail_left`, `tail_right`, `vertical_tail`,
  `engine_left`, `engine_right`, `fuselage`, or `none`), except the documented
  default-DB `wing_spar_center` cross-region case which contributes to both
  `wing_left` and `wing_right`.
- [ ] Each structural group has an explicit cumulative integrity-drop threshold
  that triggers its break mode.
- [ ] Thresholds are justified by engineering rationale (not arbitrary).
- [ ] Mapping table is a design doc only; no implementation without explicit
  approval.

## MLF-6D: State Machine (P3)

- [ ] `StructuralFailureUpdate` ECS system compiles and registers after
  `AircraftDamageStateUpdate`.
- [ ] System reads `ComponentDamageState` via ECS `get<>()`.
- [ ] New `StructuralBreakupState` ECS component (D7) is defined and attached
  to aircraft entities.
- [ ] `StructuralBreakupState` holds `breakup_state` (intact →
  partial_detachment → partial_breakup → full_breakup) and active `break_mode`
  bitmask.
- [ ] State is irreversible and cumulative (per D4): component values only
  transition forward; there is no code path reverting `full_breakup` → `intact`.
- [ ] Multiple break modes can activate in the same timestep (per D4).
- [ ] System does NOT modify any *existing* ECS component (per D2):
  `structural_integrity`, `FlightModel`, `Propulsion`, `Health`,
  `PlatformDamageState` remain untouched.
- [ ] `ef_test --test-suite=structural_failure_state` passes.

## MLF-6E: Event Writer (P4)

- [ ] `StructuralBreakupEvent` rows are written to
  `RecentEngagementEvents::structural_breakup_events` when a new break mode
  activates or breakup_state advances.
- [ ] `breakup_state` field matches the state machine's current state.
- [ ] `break_mode` field names the triggering break mode.
- [ ] `detached_part_ref` is a stable string label (per D3).
- [ ] `detached_part_count` increments correctly when new parts detach.
- [ ] `airframe_breakup` is `true` only when `breakup_state == full_breakup`.
- [ ] `cause_event_id` references the most recent `ComponentDamageEvent::event_id`
  for the contributing component group.
- [ ] No-damage baseline produces zero events (no false positives).
- [ ] System does NOT modify `structural_integrity`, `FlightModel`, `Propulsion`,
  `Health`, or `PlatformDamageState` (per D2).
- [ ] `ef_test --test-suite=structural_failure_events` passes.

## MLF-6F: Diagnostics Export (P5)

- [ ] Thin Python probe consumes existing `StructuralBreakupEvent` and
  `structural_breakup_events` bindings (`bindings_runtime.cpp:449-457`,
  `bindings_core.cpp`); no new binding surface introduced.
- [ ] Probe exports `structural_breakup_events` per `chain_id`.
- [ ] Export includes all `StructuralBreakupEvent` fields.
- [ ] `pytest -q tests/tools/test_structural_breakup_export.py` passes.

## MLF-6G: Focused Tests (P6)

- [ ] Controlled wing-spar failures produce `break_mode = wing_loss`.
- [ ] Controlled stabilator failures produce `break_mode = tail_loss`.
- [ ] Controlled engine-mount failures produce `break_mode = engine_detach`.
- [ ] Controlled fuselage-longeron failures produce `break_mode = fuselage_rupture`.
- [ ] Multi-group failures (3+ families) produce `break_mode = multi_axis` and
  `breakup_state = full_breakup`. 1-family → `partial_detachment`, 2-family →
  `partial_breakup`.
- [ ] No-damage baseline produces zero events.
- [ ] State irreversibility is tested: once `wing_loss` is set in
  `StructuralBreakupState` (D7), restoring `ComponentDamageState` component
  integrity does not clear the `wing_loss` flag.

## MLF-6H: Zero-Regression Smoke (P7)

- [ ] Full `tests/runtime/air_combat/` suite passes.
- [ ] Full `tests/world_batch/` suite passes.
- [ ] `ctest --test-dir build-workshop -R ef_test_all --output-on-failure` passes.
- [ ] Zero regressions vs main branch.

## MLF-6I: Acceptance And Archive (P7)

- [ ] This acceptance checklist is complete.
- [ ] Current status doc reflects final accepted state.
- [ ] Dispatch queue is closed.
- [ ] Parent A2 README updated with MLF-6 accepted status.
- [ ] Air combat README updated.
- [ ] Residual map explicitly defers aerodynamics bridging, loss-state
  integration, wreck/debris lifecycle, and Pk to MLF-7 / MLF-8 / MLF-9.
- [ ] Archive boundary clear.

## Forbidden Claims (Must Remain Refused)

- [ ] `pk_authority` remains `false`.
- [ ] `deterministic_kill_authority` remains `false`.
- [ ] `real_weapon_structural_kill_authority` remains `false`.
- [ ] `wreck_debris_lifecycle_authority` remains `false` (MLF-8).
- [ ] `flight_dynamics_modification_authority` remains `false` (MLF-7).
- [ ] `structural_integrity_modification_authority` remains `false` (MLF-7).
- [ ] `loss_state_modification_authority` remains `false` (MLF-7).
- [ ] No AIM-120C, MQ-9, or specific platform/weapon structural-kill calibration.
- [ ] No naval or ground platform structural models.
- [ ] No direct crash/deletion rules.
- [ ] No reopening of sealed MLF-1 through MLF-5 packages.

## Residual Register

| ID | Description | Severity | Status |
| --- | --- | --- | --- |
| — | No residuals yet; subproject in planning | — | — |
