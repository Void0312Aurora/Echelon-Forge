# Submarine damage response and mobility contract

Language:
- English canonical contract.
- Chinese companion: `submarine_damage_mobility_contract.zh.md`.
Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/architecture/standards/submarine_damage_mobility_contract.md`
Owner: `architecture/naval-submarine`
Last verified: `2026-10-10`

## Current admission

Submarine entities are admitted to two bounded native mechanisms:

1. `SubmarineDamageStateUpdate` consumes `Health`, `PlatformDamageState`, and `SubmarinePlatform` in the naval damage stage. It advances fire, flooding, and hull-breach severity with the explicit synthetic profile `naval_damage_response_submarine_v1`.
2. `SubmarineMotion` reads the optional shared `PlatformDamageState`. `mobility_capability` caps attainable submerged speed and scales acceleration, heading turn rate, and depth-rate authority. A mobility kill or capability `<= 0.25` commands zero target speed and the platform coasts/decelerates under the bounded kinematic law.

The submarine profile is a runtime-closure mechanism. It is synthetic, uncalibrated, and not a claim about any named class. It does not admit torpedo, VLS, ASW weapon release, pressure-hull kill physics, crew casualties, or a complete sinking model.

## Response profile

`naval_damage_response_submarine_v1` uses these per-second coefficients:

| Term | Value |
| --- | ---: |
| fire decay | `0.0006` |
| hull-breach decay | `0.00008` |
| breach-to-flooding gain | `0.004` |
| flooding decay | `0.00015` |
| mission loss from fire | `0.0018` |
| sensor loss from fire | `0.0014` |
| mobility loss from flooding | `0.0030` |
| survivability loss from flooding | `0.0035` |
| survivability loss from fire | `0.0012` |

The response uses the shared `sync_platform_damage_loss_state` helper for capability clamps, kill flags, Health flags, loss state, and destruction. A submarine with a `ShipPlatform` component is not processed by the submarine selector, preventing double ownership.

## Timing and ordering

- The damage system uses the finite-positive entity timestep policy. Zero, negative, and non-finite iterator deltas resolve to the maintained `1/60 s` compatibility cadence.
- `SubmarineMotion` is an earlier stage than naval damage. Motion therefore consumes the damage projection from the previous step, matching the existing ship damage/mobility ordering. Tests must account for this one-step lag.
- A positive timestep advances severity and capability by rate times elapsed seconds. No content-level `damage_model` record alone implies that the submarine response or a weapon mechanism is admitted.

## Validation contract

Native tests in `src/tests/test_ship_maneuvering.cpp` prove:

- an impaired submarine cannot reach the pristine speed or depth-rate response under the same command;
- the admitted submarine profile increases flooding from a breach and decreases mobility capability while retaining shared Health/loss ownership;
- existing pristine submarine motion and instrument behavior remain available when no `PlatformDamageState` is attached.

The contract intentionally leaves pressure-hull mechanics, class-specific calibration, torpedo/ASCM execution, and full ASW end-to-end outcomes outside the admitted surface until separate source-backed profiles and acceptance tests exist.
