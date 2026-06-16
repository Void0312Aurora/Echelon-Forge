# A2 Missile Lethality Proximity Fuze Realism

Status: `2026-06-16` PF-R5 surrogate validation complete with residuals / PF-R6
documentation closeout synced. This subproject records the public-source
research boundary, current runtime gaps, surrogate contract, non-authoritative
runtime explainability slice, and focused matrix validation evidence.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Parent A2 pointer: [../README.md](../README.md)
- MLF-2 geometry/fuze evidence pointer:
  [../missile_lethality_geometry_fuze/README.md](../missile_lethality_geometry_fuze/README.md)
- Target-geometry retained follow-on:
  [../missile_lethality_target_geometry/README.md](../missile_lethality_target_geometry/README.md)
- Agent subproject standard:
  [../../../../agent/rules/subproject_creation_standard.md](../../../../agent/rules/subproject_creation_standard.md)
- Realism and authority boundary:
  [../../../../standards/foundation/realism_authority_boundary.zh.md](../../../../standards/foundation/realism_authority_boundary.zh.md)
- Public-source admission:
  [../../../../standards/foundation/public_data_source_admission.zh.md](../../../../standards/foundation/public_data_source_admission.zh.md)
- Current runtime implementation surface:
  [../../../../../src/systems/combat/damage_system_common.h](../../../../../src/systems/combat/damage_system_common.h)
- Current fuze realism test entry:
  [../../../../../tests/runtime/air_combat/weapon_guidance_realism/test_launch_guidance_and_dynamics.py](../../../../../tests/runtime/air_combat/weapon_guidance_realism/test_launch_guidance_and_dynamics.py)
- Public mechanism references:
  [FAS Naval Weapons, Chapter 14 Fuzing](https://man.fas.org/dod-101/navy/docs/fun/part14.htm),
  [FAS Naval Weapons, Chapter 13 Warheads](https://man.fas.org/dod-101/navy/docs/fun/part13.htm),
  [Smithsonian proximity fuze cutaway](https://www.si.edu/object/fuze-proximity-cutaway%3Anasm_A19940233000),
  [JHU APL Talos continuous-rod paper](https://secwww.jhuapl.edu/techdigest/content/techdigest/pdf/V03-N02/03-02-Brown.pdf)

## Purpose

The current air-combat lethality chain can explain nearest approach, fuze
evaluation, detonation handoff, warhead effects, continuous-rod exposure, and
component failure facts. Recent review of launch-window and damage-chain probes
showed that the proximity-fuze decision itself is still too close to a geometric
proxy: it largely treats a nearest-distance event and trigger radius as the
detonation gate, then applies reliability and target-signature scaling.

This subproject creates the durable planning surface for replacing that proxy
with a more realistic but still non-authoritative surrogate. The goal is to
preserve the causal structure that matters for learning and diagnostics:
safe/arm state, terminal track support, target-sensor detection, target passage
through a fuze window, burst timing, warhead orientation, and mechanism-specific
coverage. It does not release a real missile fuze model, deterministic fuze
authority, Pk, or weapon-specific lethality.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| A2 authority | retained / sealed | [../README.md](../README.md) | A2 remains non-authoritative for stock weapon truth, Pk, and deterministic fuze. |
| Existing fuze event chain | observed runtime | [../../../../../src/systems/combat/damage_system_common.h](../../../../../src/systems/combat/damage_system_common.h) | Event observability does not prove realistic fuze triggering. |
| Existing trigger proxy | known gap | nearest-distance, trigger-radius, reliability, signature-scale behavior in current runtime | This is a useful engineering proxy, not a real proximity-fuze mechanism. |
| Target geometry handoff | retained evidence | [../missile_lethality_target_geometry/README.md](../missile_lethality_target_geometry/README.md) | Geometry proxy is opt-in / retained evidence, not default fuze replacement. |
| Public mechanism survey | pass / non-authoritative | [public_mechanism_source_note_20260616.md](public_mechanism_source_note_20260616.md) | Public sources support mechanism shape only, not AIM-120C-class hidden parameters. |
| Runtime gap audit | pass / read-only | [current_runtime_gap_audit_20260616.md](current_runtime_gap_audit_20260616.md) | Identifies proxy gaps; does not change behavior. |
| Surrogate contract | pass / implementation-ready design | [proximity_fuze_surrogate_contract_20260616.md](proximity_fuze_surrogate_contract_20260616.md) | Defines a proposed future contract; implementation still requires explicit approval. |
| Implementation | pass / focused surrogate evidence | [proximity_fuze_runtime_implementation_20260616.md](proximity_fuze_runtime_implementation_20260616.md) | Runtime change is limited to non-authoritative fuze explainability, not Pk or real fuze authority. |
| Validation | pass_with_residuals / focused matrix evidence | [validation/pf_r5_proximity_fuze_validation_20260616.md](validation/pf_r5_proximity_fuze_validation_20260616.md); [validation/pf_r5_proximity_fuze_validation_heatmaps_20260616.png](validation/pf_r5_proximity_fuze_validation_heatmaps_20260616.png) | Validates surrogate gating trends only; live guidance offsets are not pure detonation-point symmetry tests. |

## Scope

In scope:

- Build a public-source, non-authoritative mechanism summary for proximity
  fuzes: safe/arm, detection, terminal track, range/range-rate cues, target
  aspect, burst timing, and backup no-detonation outcomes.
- Audit the current runtime chain against that mechanism summary, separating
  observed facts from proxy assumptions.
- Design a future surrogate contract that distinguishes nearest approach,
  fuze-sensor detection, fuze trigger, detonation point, and warhead coverage.
- Preserve separate behavior for blast-fragmentation and continuous-rod
  mechanisms.
- Preserve focused validation and diagnostics for the implemented surrogate.

Out of scope:

- Runtime expansion beyond the approved surrogate evidence slice.
- AIM-120C-specific fuze thresholds, classified logic, real target-detecting
  device parameters, or real Pk.
- Claiming deterministic fuze authority, stock runtime authority, or
  weapon-specific lethality.
- Using reward or terminal-state tuning to hide a fuze-chain modeling problem.
- Reopening archived MLF-2, MLF-3, MLF-4, MLF-5, or the sealed A2 package.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Create this subproject and freeze non-implementation scope. | User requested a `docs/agent`-compliant subproject. | README, task clusters, status, dispatch, acceptance draft, and parent link exist. | active |
| `P1 Public Mechanism` | Record high-level public-source fuze mechanism facts. | P0 exists. | Source list and admitted/non-admitted claims are documented without parameters. | pass |
| `P2 Runtime Gap Audit` | Compare current runtime behavior to the mechanism facts. | P1 source facts exist. | Gap table separates current proxy behavior from required surrogate behavior. | pass |
| `P3 Surrogate Contract` | Design the future event and diagnostic contract. | P2 gap table exists. | Contract names detection, trigger, detonation point, and mechanism coverage fields. | pass |
| `P4 Implementation` | Implement only the approved scoped surrogate. | Explicit approval after P1-P3 review. | Focused runtime tests and diagnostics pass. | pass |
| `P5 Validation` | Run matrix tests and compare mechanism behavior. | P4 passes focused tests. | Range, initial lateral/vertical offset, and mechanism-family behavior are explainable and documented. | pass_with_residuals |
| `P6 Closure` | Sync parent docs, acceptance, and residuals. | P5 validation exists. | Acceptance closeout records the final surrogate boundary. | pass |

## Task Clusters

- Task cluster plan:
  [missile_lethality_proximity_fuze_realism_task_clusters_20260616.md](missile_lethality_proximity_fuze_realism_task_clusters_20260616.md)
- Current status:
  [missile_lethality_proximity_fuze_realism_current_status_20260616.md](missile_lethality_proximity_fuze_realism_current_status_20260616.md)
- Dispatch queue:
  [missile_lethality_proximity_fuze_realism_dispatch_queue_20260616.md](missile_lethality_proximity_fuze_realism_dispatch_queue_20260616.md)
- Acceptance draft:
  [missile_lethality_proximity_fuze_realism_acceptance_20260616.md](missile_lethality_proximity_fuze_realism_acceptance_20260616.md)

## Outputs And Evidence

Planned outputs:

- A public-source fuze-mechanism note under this subproject.
- A current-runtime gap audit tied to `damage_system_common.h` and focused tests.
- A future surrogate contract for `nearest_approach`, `fuze_detection`,
  `fuze_trigger`, `detonation_point`, and mechanism coverage diagnostics.
- Focused tests for the first accepted surrogate evidence slice.
- Comparison artifacts for blast-fragmentation and continuous-rod behavior after
  implementation approval.

Current outputs:

- This planning surface and finite task cluster list.
- [public_mechanism_source_note_20260616.md](public_mechanism_source_note_20260616.md):
  PF-R1 public mechanism source note.
- [current_runtime_gap_audit_20260616.md](current_runtime_gap_audit_20260616.md):
  PF-R2 read-only runtime gap audit.
- [proximity_fuze_surrogate_contract_20260616.md](proximity_fuze_surrogate_contract_20260616.md):
  PF-R3 future surrogate contract and validation plan.
- [proximity_fuze_runtime_implementation_20260616.md](proximity_fuze_runtime_implementation_20260616.md):
  PF-R4 focused runtime implementation result.
- [validation/pf_r5_proximity_fuze_validation_20260616.md](validation/pf_r5_proximity_fuze_validation_20260616.md):
  PF-R5 focused matrix validation summary.
- [validation/pf_r5_proximity_fuze_validation_heatmaps_20260616.png](validation/pf_r5_proximity_fuze_validation_heatmaps_20260616.png):
  final heatmap figure for no-load-aware detonation probability, detection
  confidence, and mechanism coverage.

## Acceptance Gate

This subproject can be marked accepted only when:

- Public-source mechanism claims are admitted as high-level, non-parameterized
  evidence and rejected where they would imply real weapon truth.
- The current runtime gap audit identifies exactly which proxy behaviors are
  being replaced or kept.
- The future surrogate contract preserves event explainability and does not
  collapse fuze behavior into reward, terminal status, or a single health
  scalar.
- Focused tests cover no-terminal-track, outside-sensor-window, detection but no
  trigger, trigger with delay, blast-fragmentation coverage, continuous-rod
  coverage, and no-detonation no-load behavior.
- PF-R5 matrix evidence is retained as final CSV, JSON, one heatmap, and a
  summary; extra intermediate artifacts are not required.
- Parent A2 docs continue to reject stock authority, Pk, deterministic fuze, and
  weapon-specific kill conclusions.

## Residuals And Next Steps

- Public sources can support mechanism structure, not real fuze constants.
- Geometry-driven target-surface distance can inform the future surrogate, but
  default runtime replacement needs a separate acceptance decision.
- Trajectory randomness, seeker/weather/environment uncertainty, and pilot or
  control-authority consequences are adjacent packages, not this first
  proximity-fuze slice.
- PF-R5 confirms surrogate trend behavior across trigger radius, initial
  lateral/vertical offset, and mechanism family, but live guidance keeps actual
  miss distance in a narrow band and makes initial-offset symmetry a residual.
- Real fuze thresholds, Pk, deterministic fuze authority, and weapon-specific
  lethality remain rejected.

## Archive

Archive index: [archive/README.md](archive/README.md). No historical records have
been archived yet.
