# A8 Damage Effect Chain Closeout 2026-06-08

Status: `archived as accepted with deferred residuals`.

## Decision

Archive A8 as a sealed evidence package for the bounded damage-effect-chain
slice.

The accepted claim is intentionally narrow:

- public shot rows expose concrete synthetic failure modes;
- fixed MQ-9/AIM-120C-like cases explain the path from detonation to damaged
  part and maintained-system response;
- propulsion, wing/control aerodynamics, fuel/leak/mass, broader fire,
  data-link mission/sensor degradation, and original-entity ground-contact
  lifecycle observability are covered by focused evidence;
- the package does not claim calibrated weapon truth, real-world Pk, deterministic
  fuze truth, a stock AIM-120C/MQ-9 lethality result, or first-class
  debris/residue objects.

## Retained Evidence

- Current status and validation record:
  [a8_damage_effect_chain_current_status_20260607.md](a8_damage_effect_chain_current_status_20260607.md)
- Dispatch and P6 acceptance record:
  [a8_damage_effect_chain_dispatch_queue_20260607.md](a8_damage_effect_chain_dispatch_queue_20260607.md)
- Task clusters:
  [a8_damage_effect_chain_task_clusters_20260607.md](a8_damage_effect_chain_task_clusters_20260607.md)

## Held Residuals

- Calibration-grade warhead, fire, and target-vulnerability truth is not
  accepted.
- Aircraft-specific control-law fidelity is not accepted.
- Platform-family expansion is not accepted.
- Real-world Pk, fuze, and stock lethality authority remain refused.
- First-class debris/residue objects are deferred; original-entity
  `landed_airframe` / `crashed_wreck` observability is accepted for this slice.

## Archive Action

Move this package under `docs/task/air_combat/archive/` and leave the original
`docs/task/air_combat/a8_damage_effect_chain/` path as a pointer README.
