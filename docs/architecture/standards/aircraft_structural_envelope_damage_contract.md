# Aircraft Structural-Envelope Damage Contract

Language:
- English canonical: `aircraft_structural_envelope_damage_contract.md`
- Chinese companion: [aircraft_structural_envelope_damage_contract.zh.md](aircraft_structural_envelope_damage_contract.zh.md)

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/architecture/standards/aircraft_structural_envelope_damage_contract.md`
Owner: `architecture/air-damage`
Last verified: `2026-10-10`

This document defines the maintained runtime contract for progressive structural
envelope damage on aircraft. It describes state transition semantics; it does
not claim that the coefficients are calibrated to a particular airframe.

## Onset and accumulation

- The maintained helper is `accumulate_aircraft_structural_envelope_damage` in
  `src/systems/combat/damage_system_air.h`.
- A non-positive timestep is a no-op.
- When dynamic pressure and Mach remain at or below the configured flutter
  baselines, an intact aircraft receives no envelope onset damage.
- When either quantity exceeds its baseline, a bounded positive onset rate is
  added to flutter exposure and structural overstress. This onset term does not
  require pre-existing damage, so an intact airframe can enter the progressive
  failure path.
- Existing structural damage remains an amplification term for the established
  high-energy and stall-related rates. It is not the only trigger.
- Structural integrity, flutter exposure, and structural overstress are clamped
  by the surrounding aircraft damage system after the helper runs.

The current onset coefficients are synthetic defaults that keep the transition
finite and testable. They are intentionally not presented as physical or
airframe-specific calibration. Platform-specific calibration belongs in the
baseline data and must preserve the same zero-inside-envelope and positive-
outside-envelope contract.

## Validation boundary

The native `structural_failure_state` tests cover the zero-onset interior,
positive onset outside the envelope, timestep scaling, and amplification from
pre-existing damage. Passing these tests establishes the state-transition
contract only; it does not establish flight-model fidelity or RL exploitability.
