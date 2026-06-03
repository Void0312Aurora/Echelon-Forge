# A4 Authorized First-Shot Training Signal

Status: `2026-06-03` active follow-on from the accepted A3 C2/ROE layer;
reward-side, routing, and post-routing learned evidence recorded. A4 remains
held because deterministic policy still does not fire.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Parent air-combat task: [../README.md](../README.md)
- A3 C2/ROE release-discipline layer:
  [../a3_c2_roe_release_discipline/README.md](../a3_c2_roe_release_discipline/README.md)
- M1 action interface split:
  [../../model/m1_action_interface_split/README.md](../../model/m1_action_interface_split/README.md)
- M1 temporal window evidence:
  [../../model/m1_temporal_window_hmoe/README.zh.md](../../model/m1_temporal_window_hmoe/README.zh.md)
- Subproject creation standard:
  [../../../agent/rules/subproject_creation_standard.md](../../../agent/rules/subproject_creation_standard.md)

## Purpose

A3 made C2/ROE release discipline observable and testable, but the post-fix
learned-policy evidence still shows that deterministic policies do not fire.
This subproject covers the next bounded repair: make the authorized first shot
trainable before reconsidering M2 or larger sequence-native policy work.

The target behavior is narrow: in the S1 C2/ROE single-shot-then-assess probe,
the policy should learn the radar / target-management / master-arm /
weapon-select / fire chain well enough to produce an authorized first release.
This is a training-signal and policy-routing project, not a missile physics,
Pk, fuze, real BVR tactics, or C2 hierarchy release.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| A3 C2/ROE contract | accepted | A3 README and focused tests expose authorization, shot budget, pending assessment, and release buckets. | Does not prove learned weapon employment. |
| Reactive vs temporal evidence | held | `2026-06-03` 32k comparison: temporal stochastic removed violation releases, deterministic still did not fire. | Temporal memory alone is not accepted as a fix. |
| Reward surface | partial | A4 reward probe adds once-per-episode authorized weapon-chain shaping and stronger violation penalties. | Reward-only tuning did not make deterministic fire. |
| Learned evidence | partial | `2026-06-03` A4 32k temporal probe: deterministic 0 fire/release; stochastic 11 releases, 3 authorized, 8 violation. | Does not accept the policy; it narrows the next cut to pulse/routing mechanics. |
| Policy routing | pass | `2026-06-03` routing probe adds a combat-weapons HMoE family for `air_combat_c2_roe_v1` and tests the stats surface. | Does not prove learned authorized release yet. |
| Post-routing learned evidence | held after evidence | `2026-06-03` retained routed temporal 32k probe kept deterministic at 0 fire/release; stochastic produced 15 attempts, 9 releases, 3 authorized releases, 6 violation releases, and 2 damage reports. | Retained route improves stochastic discipline modestly, but A4 is not accepted. |
| Binary diagnostics / opportunity trial | held after evidence | `2026-06-03` binary diagnostics show authorized-window `fire_weapon` probability remains about `0.22%` and max logit about `-6.11`; a temporary fire-opportunity penalty completed 32k but deterministic still did not fire and stochastic discipline regressed. | Reward magnitude/urgency tuning alone is rejected as the next active default. |

## Scope

In scope:

- Add bounded reward terms that make the authorized first-shot chain reachable.
- Keep the C2/ROE single-shot budget and post-launch pending-assessment
  penalties active.
- Add focused reward/config tests and short learned-policy evidence.
- Analyze whether HMoE routing needs an air-combat / weapons-employment route.

Out of scope:

- Silent suppression of fire actions as the primary fix.
- Missile physics, ammunition runtime, damage authority, Pk authority, or fuze
  authority changes.
- M2 release, causal transformer implementation, self-play, `2v2`, or real BVR
  shot doctrine.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Freeze A4 as training-signal work. | A3 accepted but deterministic policy does not fire. | README and task clusters define scope and non-goals. | active |
| `P1 Reward Signal` | Add authorized weapon-chain shaping. | Existing A3 reward surface and tests. | Focused tests prove terms are gated by authorization and single-shot state. | pass |
| `P2 Config Probe` | Enable shaping in maintained S1 C2/ROE probes. | P1 reward keys exist. | Active-entry tests prove scenario/config surface carries the knobs. | pass |
| `P3 Learned Evidence` | Run a bounded short train/probe. | P1/P2 tests pass. | Evidence records deterministic/stochastic fire and release deltas. | partial |
| `P4 Routing Review` | Decide whether policy routing needs a weapons family. | P3 evidence is recorded. | Routing recommendation is documented or implemented with tests. | pass |
| `P5 Binary Diagnostics` | Expose binary logits/probabilities and test one bounded reward urgency trial. | P4 route evidence is held. | Diagnostics and rejected trial are recorded. | pass, held outcome |
| `P6 Closure` | Sync parent docs and residuals. | P5 complete. | M1/M2 decision is updated without overclaim. | planned |

## Task Clusters

- Task cluster plan:
  [a4_authorized_first_shot_training_signal_task_clusters_20260603.md](a4_authorized_first_shot_training_signal_task_clusters_20260603.md)

## Outputs And Evidence

Current outputs:

- A4 subproject scope and task-cluster packet.
- Configurable A3/A4 reward terms for authorized weapon-chain preparation and
  authorized fire attempts without release; positive preparation terms are
  once-per-episode.
- Focused runtime and active-entry tests.
- Reward-side evidence:
  [a4_authorized_first_shot_reward_probe_20260603.md](a4_authorized_first_shot_reward_probe_20260603.md)
- Routing evidence:
  [a4_authorized_first_shot_routing_probe_20260603.md](a4_authorized_first_shot_routing_probe_20260603.md)
- Post-routing learned-policy evidence:
  [a4_authorized_first_shot_post_routing_probe_20260603.md](a4_authorized_first_shot_post_routing_probe_20260603.md)
- Binary diagnostics and rejected opportunity-penalty evidence:
  [a4_authorized_first_shot_binary_diagnostics_20260603.md](a4_authorized_first_shot_binary_diagnostics_20260603.md)

## Acceptance Gate

This subproject can be marked accepted only when:

- The maintained S1 C2/ROE probe produces an authorized first release under a
  deterministic learned policy or the residual is precisely attributed to
  policy routing / optimization rather than reward sparsity alone.
- Reward breakdown tests prove the new shaping cannot bypass hold-fire,
  unauthorized, shot-budget, or pending-assessment constraints.
- Parent A3/M1/M2 docs state that this is training evidence only and does not
  release M2, missile authority, or real-world tactics.

## Residuals And Next Steps

- HMoE now has an explicit air-combat weapons-employment route for
  `air_combat_c2_roe_v1`.
- Post-routing learned-policy evidence is recorded but held: deterministic still
  does not fire, while stochastic still repeats after the first authorized release.
- Binary-logit/probability diagnostics are now retained: deterministic
  `fire_weapon` remains near `0.22%` probability / `-6.11` max logit inside the
  authorized window.
- A bounded authorized fire-opportunity penalty trial is rejected as an active
  default; it made reward more negative without moving deterministic fire and
  worsened stochastic release discipline.
- The next residual is promoted to A5:
  [../a5_constrained_event_action_model/README.md](../a5_constrained_event_action_model/README.md).
  A5 treats `fire_weapon` as a constrained event action rather than another
  reward-only pulse target.
- M2 remains held until A5, not A4 reward/routing repair alone, proves
  deterministic authorized first-shot behavior is stable enough to justify
  sequence-native follow-up work.

## Archive

Superseded evidence and dated calibration records should move under
`archive/README.md` once A4 has a current-status or closeout record.
