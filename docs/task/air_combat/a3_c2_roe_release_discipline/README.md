# A3 C2/ROE Release Discipline

Status: `2026-06-03` bounded C2/ROE implementation, P4 evidence, and P5 index
sync pass; M2 remains held. This subproject defines the air-combat C2, ROE,
and shot-discipline layer needed before treating repeated missile launch as
only a policy-memory failure.

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
| Public C2/ROE terms | source scan accepted | Public source scan records WCS, engage/hold/cease/abort, bandit/hostile, and C2 authority boundaries. | Sources support terminology and state-machine design, not exact BVR tactics or missile-shot doctrine. |
| Existing runtime command fields | registered in A3 contract | `air_combat_c2_roe_v1` consumes `authorization_to_fire`, `roe_state`, WCS, engage order, assigned target, shot policy, and pending assessment through the loader/runtime path. | First version is a simulation contract, not a full C2 hierarchy or datalink model. |
| Air-combat S1 scenarios | additive A3 probe available | `air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json` and its active config use `mission_obs_mode=air_combat_c2_roe_v1` and enable the C2/ROE reward gate. | Existing M1 baseline entries intentionally remain on `mission_obs_mode=basic`. |
| Naval precedent | useful precedent | `naval_screen_station_v1` exposes `roe_state`, `authorization_to_fire`, and assigned target fields, with reward terms for ROE hold/authorization behavior. | Naval screen logic should guide wiring patterns, not define air tactics. |
| M1 evidence | A3-aware interpretation complete | Hybrid temporal shaped Stage-1 runs remained stable but still produced repeated launches; P4 probes now classify authorized and violation releases under the C2/ROE contract. | This does not prove memory is solved or useless; it keeps M2 held until learned-policy evidence is available. |

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

## Schema Contract: `air_combat_c2_roe_v1`

Status: `2026-06-03` first C/D contract. This is a simulation contract for
training and diagnostics, not real ROE, BVR timelines, or platform tactics.

Field order:

| Field | Value/default | Meaning |
| --- | --- | --- |
| `command_code` | existing mission command code | Preserves the current task command code. |
| `target_heading_deg` / `target_altitude_m` / `target_speed_mps` | existing mission target kinematics | Preserves the basic mission-observation target kinematics. |
| `roe_state` | raw existing int, default `0` | Existing mission-command ROE field, kept as a legacy observation fact. |
| `wcs_state` | `1` hold by default | A3 weapons-control status: `0=unspecified/legacy`, `1=hold`, `2=tight`, `3=free`. |
| `authorization_to_fire` | `0/1`, default `0` | Explicit fire authorization. |
| `engagement_authority_holder_id` / `engagement_authority_grantor_id` | entity id or `0` | Authority holder and grantor. IDs are diagnostic facts and are not normalized. |
| `assigned_target_id` / `assigned_target_track_id` / `assigned_target_source_id` | entity/source id or `0` | Assigned target, track, and source. |
| `assigned_target_snapshot_time_s` | seconds, default `0.0` | Assigned-target snapshot time. |
| `target_identity_state` | default mission `threat_state` or contact classification | Simplified contract value: `0=unknown`, `1=bogey`, `2=bandit`, `3=hostile`, `4=friendly`. |
| `engage_order_state` | default `0` | `0=none`, `1=commit`, `2=engage`, `3=hold_fire`, `4=cease_fire`, `5=cease_engagement`, `6=abort`. |
| `shot_policy_state` | default `0` | `0=weapons_hold`, `1=single_shot_then_assess`, `2=salvo_authorized`, `3=reattack_authorized`. |
| `shot_budget_remaining` | default `0` | Remaining launches authorized by the current contract; first version is scenario/command supplied. |
| `pending_assessment` | `0/1`, default `0` | Whether the aircraft is waiting for effect assessment or reauthorization after first shot. |
| `own_missiles_in_flight_count` | default `0` | Own missiles in flight against the same target; first version consumes only an explicit mission field, with runtime diagnostics left for follow-up. |
| `target_contact_present` | derived `0/1` | Whether the assigned-target track is present in the current observation. |

Fail-closed defaults:

- Missing `wcs_state` observes as `hold`.
- Missing `shot_policy_state` observes as `weapons_hold`.
- Missing `shot_budget_remaining` observes as `0`.
- `authorization_to_fire=true` only means fire is authorized; it does not
  automatically authorize salvo, reattack, or a second shot.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Freeze public-source and authority boundaries. | User asks for C2/ROE constraints. | Source scan records safe facts and non-claims. | pass |
| `P1 Code Surface` | Audit current command, observation, reward, scenario, and diagnostics paths. | Current air-combat and naval ROE code exists. | Cut-in map names files, fields, tests, and residuals. | pass |
| `P2 Contract` | Define air-combat C2/ROE schema and state transitions. | P0/P1 facts accepted. | `air_combat_c2_roe_v1` field list and state values are documented. | pass |
| `P3 Implementation` | Wire observation, reward, diagnostics, and scenario/config probes. | P2 contract stable. | Focused tests pass and S1 C2/ROE probe can run. | pass |
| `P4 Evidence` | Compare reactive/temporal behavior under A3 constraints. | P3 probe entries exist. | Repeated-launch metrics split authorized vs violation cases. | pass |
| `P5 Closure` | Sync docs, residuals, and M1/M2 decision. | P4 evidence recorded. | Bounded A3 C2/ROE layer accepted; M2 remains held. | pass |

## Task Clusters

- Task cluster plan:
  [a3_c2_roe_release_discipline_task_clusters_20260602.md](a3_c2_roe_release_discipline_task_clusters_20260602.md)
- Chinese companion:
  [a3_c2_roe_release_discipline_task_clusters_20260602.zh.md](a3_c2_roe_release_discipline_task_clusters_20260602.zh.md)

## Outputs And Evidence

Current outputs and evidence:

- Public source and non-claim scan for C2/ROE terms.
- Code-surface scan for current mission-command, observation, release-gating,
  reward, scenario, config, and process-probe cut-in points.
- Air-combat C2/ROE mission-observation contract and taxonomy entry.
- Focused tests for mission observation fields, scenario round-trip, reward
  terms, active training entry bootstrap, and world-batch mission observations.
- S1 C2/ROE probe scenario/config pair under maintained air-combat locations,
  with legacy M1 baseline configs kept on `basic`.
- Process-probe metrics that separate total releases, invalid fire attempts,
  authorized releases, unauthorized/violation releases, premature second shots,
  authorized salvos, and reattack shots.
- A3-aware P4 probe evidence:
  [a3_c2_roe_p4_probe_evidence_20260603.md](a3_c2_roe_p4_probe_evidence_20260603.md)
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
- The next substantive work is learned-policy training/evaluation against the
  A3 C2/ROE probe config when RL resources are available; local P5 closure does
  not claim that result.

## Archive

Superseded A3 planning notes and dated worker packets should move to
`archive/README.md` once a current-status or closeout document replaces them.
