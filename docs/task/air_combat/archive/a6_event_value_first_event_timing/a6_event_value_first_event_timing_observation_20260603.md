# A6 Observation: A5 Event Head Holds Deterministically

Status: `2026-06-03` P0 observation evidence for
[README.md](README.md). This note reads retained A5 probe artifacts under
`experiments_tmp/` but does not make those artifacts staged evidence.

## Source Artifacts

Retained, unstaged artifacts:

- `experiments_tmp/a5_event_action_temporal_32k_20260603/a5_deterministic_probe.json`
- `experiments_tmp/a5_event_action_temporal_32k_20260603/a5_stochastic_probe.json`

The authoritative staged summary remains the A5 short learned-policy note:
[../a5_constrained_event_action_model/a5_constrained_event_action_model_short_learned_probe_20260603.md](../a5_constrained_event_action_model/a5_constrained_event_action_model_short_learned_probe_20260603.md).

## Observation Commands

Deterministic summary:

```bash
jq '. as $r | {probe: "deterministic", episodes: ($r.episode_summaries|length), terminations: $r.termination_reasons, fire_mask_open_steps: ([$r.episode_summaries[].fire_mask_open_step_count]|add), authorized_ready_steps: ([$r.episode_summaries[].engagement_state_counts.AuthorizedReady]|add), fire_requests: ([$r.episode_summaries[].fire_once_requested_count]|add), accepted: ([$r.episode_summaries[].fire_once_accepted_count]|add), releases: ([$r.episode_summaries[].release_executed_count]|add), violations: ([$r.episode_summaries[].violation_release_count]|add), event_prob_fire_once_mean: (([$r.episode_summaries[].policy_event_prob_fire_once_mean]|add) / ($r.episode_summaries|length)), event_prob_fire_once_max: ([$r.episode_summaries[].policy_event_prob_fire_once_max]|max), mode_fire_count: ([$r.episode_summaries[].policy_event_mode_fire_once_count]|add), final_missiles: [$r.episode_summaries[].final_missiles], release_steps: [$r.episode_summaries[].release_steps]}' \
  experiments_tmp/a5_event_action_temporal_32k_20260603/a5_deterministic_probe.json
```

Stochastic summary:

```bash
jq '. as $r | {probe: "stochastic", episodes: ($r.episode_summaries|length), terminations: $r.termination_reasons, fire_mask_open_steps: ([$r.episode_summaries[].fire_mask_open_step_count]|add), authorized_ready_steps: ([$r.episode_summaries[].engagement_state_counts.AuthorizedReady]|add), fire_requests: ([$r.episode_summaries[].fire_once_requested_count]|add), accepted: ([$r.episode_summaries[].fire_once_accepted_count]|add), rejected: ([$r.episode_summaries[].fire_once_rejected_count]|add), releases: ([$r.episode_summaries[].release_executed_count]|add), authorized_releases: ([$r.episode_summaries[].authorized_release_count]|add), violations: ([$r.episode_summaries[].violation_release_count]|add), repeats: ([$r.episode_summaries[].repeat_release_before_assessment_count]|add), budgets: ([$r.episode_summaries[].shot_budget_violation_count]|add), event_prob_fire_once_mean: (([$r.episode_summaries[].policy_event_prob_fire_once_mean]|add) / ($r.episode_summaries|length)), event_prob_fire_once_max: ([$r.episode_summaries[].policy_event_prob_fire_once_max]|max), mode_fire_count: ([$r.episode_summaries[].policy_event_mode_fire_once_count]|add), final_missiles: [$r.episode_summaries[].final_missiles], release_steps: [$r.episode_summaries[].release_steps]}' \
  experiments_tmp/a5_event_action_temporal_32k_20260603/a5_stochastic_probe.json
```

## Results

| Probe | Episodes | Termination | Fire-mask-open / `AuthorizedReady` steps | Requests | Accepted | Releases | Authorized releases | Violations | Repeat / budget violations | Event fire probability mean / max | Deterministic event mode fire count |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| deterministic | 1 | `combat_timeout=1` | `1880 / 1880` | 0 | 0 | 0 | 0 | 0 | 0 | `0.217% / 0.278%` | 0 |
| stochastic | 3 | `combat_timeout=3` | `1647 / 1647` | 4 | 3 | 3 | 3 | 0 | 0 | `0.066% / 0.278%` | 0 |

Stochastic release steps were `823`, `346`, and `592`; each episode ended with
`3` missiles remaining. The only rejected event request was
`weapon_not_ready=1`; no post-launch repeat release, pending-assessment release,
or shot-budget violation occurred.

## Interpretation

The A5 event surface is coherent enough to express and constrain the weapon
event:

- Legal fire windows exist and are visible.
- Stochastic exploration can eventually sample `fire_once`.
- Once sampled and accepted, the state machine suppresses unsafe repeated fire.

The deterministic failure therefore is not explained by absent fire windows or
missing release discipline. It is an optimization and timing-credit failure:
the event head keeps `fire_once` far below `hold`, so deterministic argmax never
uses the legal first-event action.

## A6 Design Consequence

A6 should not start with another broad reward-penalty pass. The next mechanism
must directly give the first event a learnable value or timing signal. Plausible
contracts include:

- an action-conditional event value head for `hold` versus `fire_once`;
- a first-event hazard objective over `AuthorizedReady` windows;
- a bounded first-shot curriculum that creates usable event labels while A3/A5
  masks retain legality.

The preferred long-term shape is event-value/hazard first, curriculum second as
a stabilization or data-generation aid. This keeps legality, timing, and
future sequence modeling separated.

## Residual

No A6 implementation has been accepted by this observation note. It only
promotes the next work surface from "tune reward again" to "design and test an
event-value / first-event timing objective."
