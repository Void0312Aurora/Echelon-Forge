# MLF-7 Secondary Consequence Coupling — Acceptance Record

Status: `2026-06-18` accepted for the engineering-proxy MLF-7 slice. P1/P2/P3,
P4 diagnostics, P5 focused validation, P6 broad smoke, and P7 status sync are
satisfied.

## Acceptance Scope

This record marks the bounded MLF-7 slice accepted. `[x]` = met. `[~]` =
intentionally held outside MLF-7.

## MLF-7A: Boundary And Index

- [x] README, task clusters, current status, dispatch queue, acceptance draft,
  and archive placeholder exist.
- [x] Parent A2 README links MLF-7 as an accepted engineering-proxy bridge with
  event and smoke evidence.
- [x] Air-combat README routes MLF-7 as the follow-on after MLF-6 acceptance and
  records the MLF-8/9/10 residual boundary.
- [x] Forbidden claims are listed and remain refused.

## MLF-7B: Consequence Inventory

- [x] Inventory lists every `StructuralBreakupState` field MLF-7 may read.
- [x] Inventory lists every `StructuralBreakupEvent` field MLF-7 may use for
  diagnostics or chain linkage.
- [x] Inventory lists every candidate write surface and owner:
  `AircraftDamageState`, `PlatformDamageState`, `Health`, `FlightModel`,
  `Propulsion`, diagnostics, and tests.
- [x] Inventory records execution order between `AircraftDamageStateUpdate`,
  `StructuralFailureUpdate`, and the MLF-7 bridge.
- [x] Inventory marks direct deletion, debris lifecycle, and Pk projection as
  forbidden.

## MLF-7C: Coupling Contract

- [x] Each break mode has an explicit bounded consequence mapping.
- [x] No-breakup / intact state has a zero-effect guard.
- [x] Multi-axis and `full_breakup` behavior is explicit and testable.
- [x] Loss-state escalation threshold is explicit and does not bypass maintained
  damage/loss-state helpers.
- [x] Contract states that aircraft-damage/loss-state fields update after
  `StructuralFailureUpdate`, while downstream flight/propulsion/sensor projection
  consumes them on the next tick.

## MLF-7D: Runtime Bridge

- [x] Runtime bridge reads `StructuralBreakupState` or approved event facts.
- [x] Runtime bridge writes only P2-approved consequence surfaces.
- [x] No direct `e.destruct()` path is added.
- [x] No debris/wreck entities are created.
- [x] No Pk or training reward projection is added.

## MLF-7E: Diagnostics

- [x] Consequence deltas are visible by target entity in focused C++ state tests.
- [x] Chain linkage from structural fact to consequence diagnostic is preserved
  where an upstream `chain_id` exists.
- [x] Diagnostics separate engineering proxy values from calibrated truth through
  `generic_research_structural_consequence_projection`, diagnostics-only
  visibility, and the continued refusal of calibration/Pk claims.

## MLF-7F: Focused Validation

- [x] No-breakup case produces zero MLF-7 consequence deltas.
- [x] `wing_loss`, `tail_loss`, `engine_detach`, and `fuselage_rupture` each
  produce expected bounded consequences.
- [x] `multi_axis` / `full_breakup` produces expected loss-state behavior.
- [x] Irreversible MLF-6 state does not create duplicate runaway deltas.
- [x] Focused tests prove no direct debris lifecycle or direct deletion path.

## MLF-7G: Regression Smoke

- [x] C++ focused lanes pass.
- [x] Relevant Python diagnostic/runtime tests pass:
  `PYTHONPATH=build-workshop:. pytest -q tests/runtime/engagement/ tests/runtime/facade/ tests/runtime/bindings/ tests/tools/test_structural_breakup_export.py`
  -> 160 passed.
- [x] Full `tests/runtime/air_combat/` and `tests/world_batch/` lanes pass:
  `PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/ tests/world_batch/`
  -> 447 passed.

## MLF-7H: Acceptance And Archive

- [x] Current status summarizes implementation evidence and residuals.
- [x] Parent A2 and air-combat README statuses are synchronized.
- [x] Explicit archive movement completed under the parent A2 local archive.
- [x] MLF-8/9/10 residuals remain named.

## Forbidden Claims

- [x] No real-world Pk authority.
- [x] No deterministic kill authority.
- [x] No stock AIM-120C/MQ-9/F-16C lethality authority.
- [x] No debris/wreck lifecycle authority.
- [x] No naval or ground structural consequence authority.
- [x] No direct crash/deletion rule outside maintained platform damage paths.
