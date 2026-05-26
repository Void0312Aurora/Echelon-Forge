# A2 High-Fidelity Air-Combat Damage Model

Status: opened on `2026-05-26`; the main Phase 0 evidence audit is recorded, but the PN miss-distance baseline is still blocking behavior code.

Inputs:

- [Air-combat damage model evaluation](../../../forward/air_combat_damage_model_evaluation_20260522.md)
- [Codebase cross-evaluation](../../../forward/air_combat_damage_model_cross_eval_20260522.md)

This subproject supports the staged `1v1` realism curriculum, but it is not an RL-convenience track. Weapon events must first produce physically interpretable local structure and subsystem damage. Platform-level kill state is then derived from that state. RL rewards, curricula, and legacy `health` readouts consume these results; they do not define the physical damage authority.

## Design Stance

- `Health.current_hp` may remain as a compatibility readout, but it is not the air-combat kill authority.
- Authoritative effects originate from weapon events: impact/proximity detonation, fuze state, miss distance, relative geometry, warhead family, and target vulnerability.
- Damage first mutates structure, propulsion, fuel, sensors, flight controls, cockpit/pilot state, and related subsystems.
- Kill state is derived from subsystem and structure state, not from direct scalar `damage` subtraction.
- Randomness is allowed only for explicitly modeled uncertainty or physical sampling.
- RL shaping belongs in consuming layers, not in the physical effects model.

## Phase 0 Gates

Phase 1 code must not begin until these audits are closed and recorded:

- `PlatformLossState` enum audit, especially raw integer comparisons and append-only or overlay semantics for `ForcedLanding`;
- Python health observer audit for `health > 0`, `get_unit_health`, and `is_unit_active` callers;
- `ShipPlatform` filter audit for `NavalDamageStateUpdate` and adjacent ship-only systems;
- aircraft JSON inventory and authored-hitbox versus generated-fallback decision;
- `Score` write-point audit and event-driven scoring consumer plan;
- PN miss-distance benchmark matrix before deterministic fuze work.

Current Phase 0 evidence:

- [Phase 0 preflight audit - 2026-05-26](phase0_preflight_20260526.zh.md)

## Implementation Phases

| Phase | Status | Goal | Primary Risk |
|---|---|---|---|
| `Phase 0 Preflight` | open | Close audits and guidance baselines. | Missing evidence leads to unsafe behavior changes. |
| `Phase 1 Aircraft Structured Damage` | held | Reverse HP-first bypass, spawn aircraft damage state, derive kill state from damage state. | Medium-high behavior change. |
| `Phase 2 Aircraft Subsystem Effects` | held | Add propulsion, flight-control, structure, fuel, sensor, avionics, and cockpit effects. | Flight dynamics and sensor consumers. |
| `Phase 3 Warhead Profiles` | held | Replace scalar `damage` with blast/fragment/rod/HTK profiles. | Content and geometry calibration. |
| `Phase 4 Deterministic Fuze` | held/deferred | Replace RNG hit probability with geometry-first fuze/effects. | Must wait for PN miss-distance baselines. |
| `Phase 5 Vulnerability Evidence` | future | Add target/weapon/aspect/closure evidence and Pk calibration. | Data provenance. |

## Non-Goals

- Do not simplify damage physics for short training convenience.
- Do not treat a scalar `damage` value as a high-fidelity warhead model.
- Do not keep `health <= 0` as authoritative for structured aircraft damage.
- Do not remove RNG fuze before PN miss-distance evidence exists.
- Do not renumber shared loss-state enum values during Phase 0.

## Acceptance Signals

- A structured aircraft target cannot be killed through the HP-first bypass.
- Missile events produce inspectable `EffectsEvent`, `DamageReport`, and subsystem mutation.
- Different hitboxes produce different capability consequences.
- HP is a derived compatibility readout.
- Reward/score layers consume damage reports and kill state without writing back into physical effects authority.
- Legacy smoke remains compatible but tests distinguish legacy HP path from structured damage path.

## Task Cluster

- [High-fidelity damage model cluster](high_fidelity_damage_model_cluster_20260526.zh.md)
