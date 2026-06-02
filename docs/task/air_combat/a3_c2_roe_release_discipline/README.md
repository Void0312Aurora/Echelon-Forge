# A3 C2/ROE Release Discipline

Status: `2026-06-02` planning. This subproject defines the air-combat C2,
ROE, and shot-discipline layer needed before treating repeated missile launch
as only a policy-memory failure.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Parent air-combat task: [../README.md](../README.md)
- A1 staged 1v1 curriculum:
  [../a1_1v1_realism_gradient/README.md](../a1_1v1_realism_gradient/README.md)
- M1 temporal-window evidence:
  [../../model/m1_temporal_window_hmoe/README.zh.md](../../model/m1_temporal_window_hmoe/README.zh.md)
- M1 action-interface split:
  [../../model/m1_action_interface_split/README.md](../../model/m1_action_interface_split/README.md)
- Subproject standard:
  [../../../agent/rules/subproject_creation_standard.md](../../../agent/rules/subproject_creation_standard.md)
- Public source admission:
  [../../../standards/foundation/public_data_source_admission.md](../../../standards/foundation/public_data_source_admission.md)
- Realism and authority boundary:
  [../../../standards/foundation/realism_authority_boundary.zh.md](../../../standards/foundation/realism_authority_boundary.zh.md)
- Public-source scan:
  [c2_roe_public_source_scan_20260602.zh.md](c2_roe_public_source_scan_20260602.zh.md)
- Code-surface scan:
  [c2_roe_code_surface_scan_20260602.zh.md](c2_roe_code_surface_scan_20260602.zh.md)

## Purpose

The current Stage-1 1v1 training line can make the blue fighter fire multiple
missiles at one target without a clear tactical reason. M1 showed that exposing
short temporal history is useful runtime infrastructure, but it does not by
itself define when firing is authorized, when a second shot is allowed, or when
the pilot should hold fire.

A3 makes that missing layer explicit. It turns public C2/ROE concepts into a
scoped simulation contract: weapons-control status, target identity, engagement
order, fire authorization, and shot policy become observable and testable
training facts. The goal is not to reproduce classified tactics. The goal is to
give S1/M1 a realistic enough command constraint so repeated fire can be
classified as authorized salvo, permitted reattack, premature second shot, or
ROE violation.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Public C2/ROE terms | planning | Public source scan records WCS, engage/hold/cease/abort, bandit/hostile, and C2 authority boundaries. | Sources support terminology and state-machine design, not exact BVR tactics or missile-shot doctrine. |
| Existing runtime command fields | available but incomplete for air policy | `mission_command` already carries `authorization_to_fire`, `roe_state`, authority-holder/grantor ids, assigned target ids, and target snapshot fields through loader/runtime paths. | Fields are not yet a complete air-combat release-discipline contract. |
| Air-combat S1 scenarios | gap | Current S1 mission command grants `authorization_to_fire=true` and active configs still use `mission_obs_mode=basic`. | `basic` does not expose ROE, authorization, assigned target, or shot policy to the policy. |
| Naval precedent | useful precedent | `naval_screen_station_v1` exposes `roe_state`, `authorization_to_fire`, and assigned target fields, with reward terms for ROE hold/authorization behavior. | Naval screen logic should guide wiring patterns, not define air tactics. |
| M1 evidence | held input | Hybrid temporal shaped Stage-1 runs remained stable but still produced repeated launches. | This does not prove memory is useless; it shows the command/ROE surface is under-specified. |

## Scope

In scope:

- Define an air-combat C2/ROE state contract for training and diagnostics.
- Separate target assignment/commit from engagement/fire authorization.
- Expose air-combat mission-observation fields for authorization, WCS, target
  identity, assigned target, shot policy, and pending assessment.
- Add reward/diagnostic semantics for hold, unauthorized fire, first authorized
  shot, premature second shot, salvo authorization, reattack authorization, and
  cease/abort override.
- Add S1 C2/ROE probe scenarios/configs before reopening M2 release.
- Reinterpret M1 repeated-launch metrics after the A3 contract is observable.

Out of scope:

- Classified or platform-specific ROE, real BVR timelines, real shot doctrine,
  or real salvo tactics.
- A general C2 simulation, multi-aircraft command hierarchy, or full data-link
  model.
- Missile physics, damage authority, Pk authority, fuze authority, or ammo
  runtime changes.
- Sequence-native PPO, recurrent memory, M2 release, self-play, or 2v2 tactics.
- Environment-side silent suppression of the fire action as the primary fix.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Freeze public-source and authority boundaries. | User asks for C2/ROE constraints. | Source scan records safe facts and non-claims. | active |
| `P1 Code Surface` | Audit current command, observation, reward, scenario, and diagnostics paths. | Current air-combat and naval ROE code exists. | Cut-in map names files, fields, tests, and residuals. | active |
| `P2 Contract` | Define air-combat C2/ROE schema and state transitions. | P0/P1 facts accepted. | `air_combat_c2_roe_v1` field list and state values are documented. | planned |
| `P3 Implementation` | Wire observation, reward, diagnostics, and scenario/config probes. | P2 contract stable. | Focused tests pass and S1 C2/ROE probe can run. | planned |
| `P4 Evidence` | Compare reactive/temporal behavior under A3 constraints. | P3 probe entries exist. | Repeated-launch metrics split authorized vs violation cases. | planned |
| `P5 Closure` | Sync docs, residuals, and M1/M2 decision. | P4 evidence recorded. | A3 accepted, held, or narrowed with explicit residuals. | planned |

## Task Clusters

- Task cluster plan:
  [a3_c2_roe_release_discipline_task_clusters_20260602.md](a3_c2_roe_release_discipline_task_clusters_20260602.md)
- Chinese companion:
  [a3_c2_roe_release_discipline_task_clusters_20260602.zh.md](a3_c2_roe_release_discipline_task_clusters_20260602.zh.md)

## Outputs And Evidence

Planned outputs:

- Public source and non-claim scan for C2/ROE terms.
- Code-surface scan for current mission-command, observation, release-gating,
  reward, scenario, config, and process-probe cut-in points.
- Air-combat C2/ROE mission-observation contract.
- Focused tests for mission observation fields, scenario round-trip, reward
  terms, and training entry bootstrap.
- S1 C2/ROE probe scenario/config pair under maintained air-combat locations.
- Process-probe metrics that separate total releases, invalid fire attempts,
  unauthorized releases, premature second shots, authorized salvos, and
  reattack shots.
- M1 evidence update deciding whether repeated fire remains a memory problem
  after C2/ROE observability exists.

## Acceptance Gate

This subproject can be marked accepted only when:

- The source scan is linked and every real-world claim remains public,
  conservative, and non-classified.
- The air-combat C2/ROE schema is observable in policy input and does not rely
  on reward-only hidden state.
- S1 C2/ROE probes can distinguish hold, authorized single-shot, authorized
  salvo, and premature second-shot behavior.
- Tests cover mission-observation shape/fields, command field round-trip,
  reward/diagnostic terms, and active training entry bootstrap.
- M1/M2 documentation explicitly separates memory evidence from missing
  command/ROE constraints.

## Residuals And Next Steps

- Self-defense override is a held item until the first S1 command contract is
  accepted.
- Multi-aircraft leader/wingman delegation is held until single-aircraft C2/ROE
  semantics are stable.
- Datalink, offboard sensors, and friendly/no-fire-zone logic are future
  expansions, not A3 acceptance conditions.
- If A3 constraints are observable and repeated unauthorized fire persists, the
  remaining gap can return to M1/M2 as a policy-memory or sequence-model issue.

## Archive

Superseded A3 planning notes and dated worker packets should move to
`archive/README.md` once a current-status or closeout document replaces them.
