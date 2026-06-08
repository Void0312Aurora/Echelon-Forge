# A2 Damage Consequence Reward Surface Idea

Status: `2026-06-08` idea seed / held. This records the direction only; it is
not expanded into implementation, dispatch, or acceptance work.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- A2 pointer: [../README.md](../README.md)
- A2 sealed package: [../../archive/a2_high_fidelity_damage_model/README.md](../../archive/a2_high_fidelity_damage_model/README.md)
- A8 damage-effect chain: [../../a8_damage_effect_chain/README.md](../../a8_damage_effect_chain/README.md)
- Current air-combat entry: [../../README.md](../../README.md)

## Purpose

Record a possible follow-on direction: air-combat training should not wait only
for a `kill` or inactive target. Higher-value training signal may come from what
the shot actually caused: mission-system loss, sensor/data-link degradation,
mobility degradation, fuel leak, fire growth, loss of control, ground contact, or
crash.

This belongs under A2 rather than a new A9 because the first question is damage
model fidelity and consequence interpretation; reward design comes after that.
This note does not start implementation, declare acceptance, or promote A8's
bounded damage-effect chain into stock AIM-120C / MQ-9 lethality authority.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| A2 high-fidelity damage model | archived / sealed | A2 archive retains research/candidate evidence | Does not release Pk, deterministic fuze, or stock weapon-outcome authority |
| A8 damage-effect chain | accepted bounded slice | Detonation can be inspected as concrete part damage and maintained-system response | Does not add direct crash rules, MQ-9 special kill rules, or debris/residue objects |
| Current training feedback | suspected too narrow | Nonterminal damage can produce small progress rewards; delayed fire, ground contact, crash, and inactive outcomes are not yet a primary feedback surface | Legacy `Health` or one `kill` flag must not be treated as the complete kill-chain evaluation |

## Scope

Tentatively in scope:

- Record only the idea of consequence-graded rewards.
- Place future work as an A2 research / calibration / consequence-fidelity follow-on.
- Preserve a possible minimal witness: MQ-9 / AIM-120C-like synthetic training
  calibration, continuous consequence observation, and reward surface design.

Out of scope for now:

- No code, scenario, training config, or reward-weight changes.
- No A9 creation.
- No reopening of the sealed A2 archive package.
- No real Pk, real fuze, real AIM-120C lethality, or MQ-9 special-kill claim.
- No direct-crash rule as a substitute for the damage chain.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Idea Seed` | Freeze the location and boundary. | Current discussion. | This README exists and is linked from the A2 pointer. | held |
| `P1 Boundary` | If explicitly expanded, define rewardable consequences, observable fields, and forbidden claims. | User asks to expand. | Task-cluster document exists. | not started |
| `P2 Evidence` | Verify delayed consequences are stable and observable. | P1 complete. | Minimal witness and diagnostics are pinned. | not started |
| `P3 Reward Surface` | Design the training reward surface. | P2 complete. | Candidate tests and training config exist. | not started |

## Outputs And Evidence

- The only current output is this idea-seed README.
- There is no task cluster, dispatch packet, implementation, or acceptance record.

## Acceptance Gate

This note cannot be marked accepted. If expanded later, acceptance would first
need evidence that:

- damage-consequence fields are stably observable and do not rely on legacy
  `Health` as the main truth;
- consequence reward weights do not encourage obvious simulation exploits;
- training synthetic calibration is kept separate from real weapon/target
  authority;
- sealed A2 and accepted A8 boundaries are not overclaimed.

## Residuals And Next Steps

- A later explicit request decides whether this idea seed becomes a full A2
  follow-on.
- If upgraded, add a task-cluster document before changing reward code.
- The likely first step is continuous consequence diagnostics: mission,
  mobility, sensor, survivability, aircraft internal damage, fuel/fire,
  ground-contact lifecycle, and inactive transitions in one acceptance table.

## Archive

If this direction expands, replace or promote this note through a current-status
and task-cluster document. If abandoned, move it into the local A2 archive as a
held idea seed.
