# A6 Objective Contract: Masked First-Event Hazard

Status: `2026-06-03` P2 contract for `A6-EVT-C Objective Contract`.

Parent framing:
[a6_event_value_first_event_timing_mathematical_framing_20260603.md](a6_event_value_first_event_timing_mathematical_framing_20260603.md).
Inputs:
[A6 observation](a6_event_value_first_event_timing_observation_20260603.md),
[A6 acceptance gate](a6_event_value_first_event_timing_acceptance_20260603.md),
and the A5
[event contract](../a5_constrained_event_action_model/a5_constrained_event_action_model_event_contract_20260603.md).

## Selection

The first A6 implementation contract is a masked first-event hazard auxiliary
objective, with a bounded curriculum bootstrap that decays to zero before the
learned-policy probe.

Selected primary objective:

```text
hazard_t = P(tau = t | tau >= t, s_t, fire_mask_t = 1)
```

where `tau` is the first accepted `fire_once` time inside an `AuthorizedReady`
first-shot window. The hazard is represented by the existing masked
`hold/fire_once` event logit delta:

```text
z_t = logit_fire_once_t - logit_hold_t
p_fire_t = sigmoid(z_t)
```

The auxiliary loss supervises `z_t` only on active legal first-shot windows. It
does not replace the A5 masked categorical distribution, PPO log-prob, entropy,
sampling, or deterministic argmax semantics.

## Rejected Alternatives

| Alternative | Decision | Reason |
| --- | --- | --- |
| Event-value head as the first contract | Rejected for this slice. | It is the right long-term candidate, but it adds a new value surface and bootstrapping risk before the hazard/label plumbing is proven. |
| Curriculum-only labels | Rejected. | A bounded curriculum can escape near-zero logits, but by itself it would define correctness as an arbitrary timing rule. |
| Reward-only tuning | Rejected. | A3/A5 legality is mask/state-owned; reward-only legality tuning already failed to make deterministic fire and would blur the boundary again. |
| M2 or sequence-native objective | Rejected. | A6 must prove the current masked event surface is trainable before any M2 release vote. |

The contract deliberately chooses the lowest implementation surface that
directly moves event timing: an auxiliary loss on the already-existing event
logit pair.

## Active Window

The loss is active only when all of these are true:

- `engagement_state == AuthorizedReady`;
- `fire_mask == 1`, or `event_action_mask[fire_once] == 1`;
- the episode has not already accepted a first `fire_once`;
- the step belongs to the current first-shot window, not a reattack window;
- required target fields are present and finite.

`ReattackReady` is excluded from the first A6 contract. Later work may model it
as a separate window type, but it must use distinct labels, diagnostics, and
acceptance criteria.

## Target Definition

For each first-shot window `W = {t_0, ..., t_n}`:

```text
accepted_tau = first t in W where fire_once_accepted_t = 1
```

Natural hazard labels:

- If `accepted_tau` exists, set `target_t = 0` for active steps before
  `accepted_tau`, set `target_accepted_tau = 1`, and make later steps inactive.
- If no accepted event exists, treat the window as right-censored. By default,
  right-censored windows do not contribute negative labels to the primary
  hazard loss.
- Rejected fire requests are never positive labels.
- Mask-closed steps are always inactive, never positive or negative labels.

The primary auxiliary loss is:

```text
L_hazard =
  mean(active_weight_t * BCEWithLogits(z_t, target_t))
```

where `active_weight_t` is zero outside active first-shot windows. D/E may add a
small configurable censored-survival weight later, but the default for this
contract is `0.0` so near-zero deterministic fire is not reinforced as "correct
never fire."

## Curriculum Bootstrap

Curriculum is used only as a bounded bootstrap. It must be disabled for final
learned-policy evidence unless the evidence explicitly reports that curriculum
was still active and therefore not acceptance-grade.

Curriculum rule:

- For a first-shot window with no accepted event label in the rollout, choose at
  most one seed step:

  ```text
  t_seed = first active step in W where window_age >= curriculum_min_window_age_steps
  ```

- Default `curriculum_min_window_age_steps` should be `32`.
- If the window has fewer than `32` active steps, create no seed.
- Set `target_t_seed = 1`; active steps before `t_seed` may be survival
  negatives; later steps are inactive for the curriculum label.
- Create at most one curriculum seed per episode.
- Never create a curriculum label outside `AuthorizedReady` with
  `fire_mask == 1`.

Schedule:

```text
curriculum_coef = initial_curriculum_coef * linear_decay(completed_fraction, 0.0, 0.25)
```

The coefficient must be exactly zero after the first `25%` of training progress
and zero during deterministic/stochastic evaluation probes. The hazard
coefficient may remain active for training.

## Coupling To Event Logits

D must expose or compute the event logit delta from the existing hybrid event
head:

```text
z_t = logit_fire_once_t - logit_hold_t
```

The PPO action distribution remains:

```text
event_dist = MaskedCategorical(logits=[logit_hold, logit_fire], mask=[1, fire_mask])
```

Required coupling rules:

- The auxiliary hazard loss backpropagates into the event logits used by the
  masked categorical distribution.
- PPO policy loss, value loss, entropy, KL, sampling, and deterministic eval
  continue to use the existing masked categorical semantics.
- Illegal `fire_once` keeps zero probability mass through the A5 mask.
- The auxiliary loss is zero when `a6_first_event_hazard_coef == 0`, when no
  active legal first-shot steps exist, or when required target fields are
  missing.
- The implementation must not add a parallel action path or raw
  `fire_weapon` threshold.

This matches the current feasibility surface: the policy already builds a
masked event categorical for action index `9`, and PPO already has a pattern
for optional auxiliary loss terms.

## Required Fields For D/E

Rollout or training-buffer fields:

| Field | Purpose |
| --- | --- |
| `a6_first_event_active` | Loss mask for `AuthorizedReady` first-shot legal steps. |
| `a6_first_event_target` | Hazard or curriculum target in `{0, 1}`. |
| `a6_first_event_weight` | Per-step weight after curriculum/censor handling. |
| `a6_first_event_source` | `accepted`, `curriculum`, `censored`, or `inactive`. |
| `a6_first_event_window_age` | Active-step age within the current first-shot window. |
| `a6_first_event_window_id` | Stable per-episode window identifier for diagnostics. |
| `a6_first_event_had_accepted` | Whether the window already contains an accepted event label. |

Environment info / observation sources:

- `engagement_state`;
- `fire_mask` or `event_action_mask`;
- A5 mask components when available;
- `fire_once_requested`;
- `fire_once_accepted`;
- `fire_once_rejected_reason`;
- `release_executed`;
- `authorized_release_count`;
- `violation_release_count`;
- `repeat_release_before_assessment_count`;
- `shot_budget_violation_count`;
- `post_launch_suppressed`;
- `reattack_ready`;
- final missile count and release steps for probes.

Policy/training diagnostics:

- `a6/hazard_loss`;
- `a6/hazard_coef`;
- `a6/curriculum_coef`;
- `a6/active_frac`;
- `a6/target_positive_frac`;
- `a6/curriculum_positive_count`;
- `a6/censored_window_count`;
- `a6/event_logit_delta_mean_open`;
- `a6/event_fire_prob_mean_open`;
- `a6/event_fire_prob_max_open`;
- deterministic and stochastic `policy_event_mode_fire_once_count`.

## Deterministic Metrics To Move

The A5 baseline is:

- deterministic: `1880` fire-mask-open / `AuthorizedReady` steps, `0` requests,
  `0` releases, `policy_event_prob_fire_once_mean=0.217%`, max `0.278%`;
- stochastic: `3` authorized releases over `3` episodes, `0` violation release,
  `0` repeat release, and `0` budget violation.

A6-EVT-F should evaluate the same categories. The contract target is:

- primary success: deterministic probe has `policy_event_mode_fire_once_count >
  0`, `fire_once_accepted_count >= 1`, `authorized_release_count >= 1`, and
  `violation/repeat/budget = 0`;
- held-but-informative movement: if deterministic mode remains `hold`, the note
  must report whether `policy_event_prob_fire_once_mean` over open steps reached
  at least `2.0%` or max reached at least `10.0%`, then assign the blocker;
- stochastic discipline must remain at least as clean as A5 on comparable short
  probes.

Probability movement without deterministic mode movement is not acceptance. It
is only evidence for the next held residual.

## Tests Required For D/E

Training-kernel tests:

- Hazard loss is exactly zero when the coefficient is zero.
- Hazard loss is exactly zero on mask-closed or non-`AuthorizedReady` steps.
- Accepted-event labels produce finite BCE loss and gradients on the event
  logit delta.
- Right-censored windows do not create default full-window negative labels.
- Curriculum creates at most one positive seed per episode and only on
  `AuthorizedReady + fire_mask=1` steps.
- Curriculum coefficient decays to zero after `25%` completed training.
- The auxiliary loss does not change masked categorical sampling,
  deterministic argmax, log-prob, or entropy semantics.

Policy/distribution tests:

- `fire_mask=0` still forces deterministic and stochastic support to `hold`.
- Event logit delta / fire probability diagnostics are derived from the same
  logits used by the masked categorical.
- Masked illegal `fire_once` receives no probability mass even if the hazard
  target data is malformed.

Config/diagnostics tests:

- Active S1 C2/ROE config can enable A6 hazard/curriculum knobs without
  reintroducing reward-only legality penalties.
- Callback logs finite `a6/*` diagnostics when active windows exist and stable
  zeros when they do not.
- Process probe reports requested, accepted, rejected, executed, authorized,
  violation, repeat, budget, mode, and event probability fields.

Retained A5 discipline tests:

- `FiredAssess` still suppresses immediate repeat fire.
- Shot-budget exhaustion still masks `fire_once`.
- Pending assessment still masks `fire_once`.
- `ReattackReady` is not treated as a first-shot window by A6 labels.

## Rollback Criteria

A6 implementation must be rolled back, held, or re-scoped if any of these occur
in focused tests or comparable short probes:

- any `violation_release_count > 0`;
- any `repeat_release_before_assessment_count > 0`;
- any `shot_budget_violation_count > 0`;
- any increase caused by bypassing A5 mask/state support rather than a named
  runtime mismatch;
- rejected reasons include `masked_hold_only`, `hold_state`,
  `pending_assessment`, `shot_budget_empty`, `ammo_empty`, or
  `reattack_not_authorized` after an A6-driven `fire_once` request;
- `weapon_not_ready` rejected requests exceed the A5 short stochastic baseline
  of `1` over `3` comparable episodes without a bounded config/runtime
  explanation;
- stochastic probing no longer produces disciplined one-authorized-release
  behavior under the same short probe shape;
- deterministic policy remains at `0` requests and the evidence note does not
  show a material probability/logit movement or a stronger diagnosis.

## Boundaries

This contract does not permit:

- M2 release or sequence-native PPO implementation;
- missile physics, Pk, fuze, damage authority, or stock-weapon authority
  changes;
- real-world doctrine or tactical correctness claims;
- broad reward-only legality tuning;
- weakening A3/A5 masks, state transitions, post-launch suppression, pending
  assessment, shot budget, or ammo constraints;
- raw `fire_weapon` threshold labels;
- treating stochastic one-shot behavior alone as deterministic acceptance.

## Unlock Statement

This contract unlocks A6-EVT-D/E only for the masked first-event hazard
objective described here, with bounded curriculum bootstrap and explicit
diagnostics. It does not accept A6. Learned-policy acceptance still requires
focused tests and short deterministic/stochastic evidence against the retained
A5 baseline.
