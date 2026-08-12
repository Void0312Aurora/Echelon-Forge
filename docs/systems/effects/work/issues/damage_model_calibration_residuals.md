# Damage Model Calibration Residuals

Language:
- English canonical: `damage_model_calibration_residuals.md`
- Chinese companion: not maintained (English-only work surface).

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/systems/effects/work/issues/damage_model_calibration_residuals.md`
Owner: `systems/effects/damage-calibration`
Last verified: `2026-08-08`
Content status: owner-local extraction from the completed T6 residual ledger;
the entries are held calibration/product expectations, not accepted behavior.

## Scope

This issue owns residuals where current binary behavior diverges from a named
damage-model or air-combat calibration expectation. It does not own test
harness defects, source-rights admission, or C++ include-direction decisions.

## Current Residuals

- The retained weapon-guidance realism suite contains 33 adjudicated methods
  across six drift groups: primary-response selection, proximity-projection
  spread, cross-subsystem overspill, loss-state escalation/saturation,
  aero/fuze response, and mechanism calibration. Twenty-five are governed by
  strict `xfail` markers and eight by `expectedFailure` because mixed subtests
  cannot safely use strict xfail markers.
- The focused I97 repair records seven binary residuals: direct-hit component
  identity, detonation outcome, fragment energy, blast overpressure, spatial
  sample count, nonblank component-source rows, and the synthetic fragility
  vector. Their current markers are alarms, not a new baseline.

## Evidence Boundary

The source ledger and its dated verification records are retained in the
[completed T6 ledger](../../../../plan/archive/unified_architecture_program_completed_20260727/t6_residual_ledger.md).
The ledger records the two-binary inherence evidence for the I65/I97
calibration group and the exact test node IDs. This page is a current route,
not a replacement for those historical measurements.

## Promotion Gate

Remove or change a residual only after the effects owner supplies a new
calibration authority, reproduces the expected behavior on a current matched
build, updates the affected test contract, and records an independent review.
An unexpected pass of a strict xfail is a re-review trigger, not automatic
promotion.

## Non-goals

- Do not weaken or delete residual markers to make a suite green.
- Do not reinterpret the held values as a maintained effects standard.
- Do not modify archived evidence or unrelated runtime/documentation owners.
