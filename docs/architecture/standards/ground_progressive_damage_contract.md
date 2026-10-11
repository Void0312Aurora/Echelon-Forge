# Ground progressive damage time-step contract

Language:
- English canonical contract.
- Chinese companion: `ground_progressive_damage_contract.zh.md`.
Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/architecture/standards/ground_progressive_damage_contract.md`
Owner: `architecture/ground-damage`
Last verified: `2026-10-10`

## Scope

`GroundDamageStateUpdate` owns progressive ground fire, ignition-source, structural, casualty, and projected capability changes. All evolving terms are rates per simulated second. The system samples the Flecs iterator delta once per run and applies the rate to every matched ground entity.

The `1/60 s` kernel cadence remains the compatibility calibration baseline: each previous per-tick coefficient is multiplied by 60, so one baseline tick produces the existing response within floating-point tolerance.

## Rate inventory

| Term | Rate per second | State owner |
| --- | ---: | --- |
| Fire decay | `0.048` | `GroundPlatformDamageState.fire_severity` |
| Ignition-source decay | `0.030` | `GroundPlatformDamageState.ignition_source_severity` |
| Ongoing structural decay | `0.006` | `GroundPlatformDamageState.ongoing_structural_damage` |
| Structural integrity loss | `0.024 * structural_progress` | `GroundPlatformDamageState.structural_integrity` |
| Casualty growth | `0.090 * fire_progress` | `GroundPlatformDamageState.casualty_fraction` |
| Mission capability loss | `0.090 * fire + 0.060 * structure + 0.048 * uncontained_fire` | shared `PlatformDamageState` |
| Mobility capability loss | `0.120 * unavailable_mobility + 0.036 * structure` | shared `PlatformDamageState` |
| Survivability loss | `0.132 * fire + 0.108 * structure` | shared `PlatformDamageState` |

Each rate is evaluated from the state at the start of the tick and then clamped to its declared range. Fire and structural load are projected into the shared state by assignment; they are not accumulated a second time.

## Delta and pause semantics

- A finite positive `dt` advances the response by `rate * dt`.
- `dt == 0`, negative `dt`, `NaN`, and infinities resolve to `0` through `ground_damage_detail::resolve_damage_dt`; the update is a no-op. Ground damage must not create casualties or decay while a stage is paused or has no valid elapsed time.
- This no-op policy is specific to progressive ground damage. It is not the shared physics integrator fallback used by air and rigid-body systems.
- Clamping, `sync_platform_damage_loss_state`, Health ownership, destruction, and loss-state thresholds remain unchanged.

## Reachability and validation

The system is admitted at stage 30 (`builtin.system.ground_damage`) and is reachable from the native kernel and WorldBatch worlds that install the default contribution graph. It remains a consequence owner; it does not own ground movement, route following, sensing, terrain, or weapon release.

`src/tests/test_ground_damage_system.cpp` proves:

- equal one-second runs at `1/60`, `0.05`, and `0.1 s` produce equivalent bounded state;
- one baseline `1/60 s` tick preserves the former per-tick response;
- zero and invalid deltas are no-ops.

The positive timestep comparison is a numerical contract, not a promise of bitwise identity for arbitrary step sizes or future nonlinear damage models.
