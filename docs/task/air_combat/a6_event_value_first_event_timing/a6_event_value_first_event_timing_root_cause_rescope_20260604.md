# A6 Root-Cause Re-scope

Status: `2026-06-04` complete for root-cause analysis; training and L-parameter
tuning are paused.

Parent: [README.md](README.md). Evidence input:
[launch-window short learned evidence](a6_event_value_first_event_timing_launch_window_short_learned_probe_20260604.md).

## Scope

This note explains why the A6 launch-window line is blocked at the mechanism
level. It does not add another short training run, change launch-window weights,
release M2, or modify A3/A5 legality constraints.

The current root question is not "which L knob should move next". It is whether
the current per-step hazard objective can represent the desired first-event
timing behavior under stochastic PPO sampling and an absorbing first release.

## Evidence Snapshot

The L run is not a dead signal:

- `A6-EVT-K` proved the event head can cross deterministic argmax when the
  dedicated event-head lane is strong enough, but the release collapsed to a
  near-immediate step-2 authorization/contact shot.
- `A6-EVT-L` then separated legal authorization from launch-window timing in
  the label builder.
- `A6-EVT-M` changed behavior: deterministic probing no longer fired early,
  but still made `0` requests while open-window event probability reached
  `34.6% / 35.0%`.
- Stochastic probing still sampled one authorized release in every episode at
  steps `7`, `43`, and `4`, with no rejected, violation, repeat, or budget
  issues.

The stochastic probe shows the structural hazard problem directly:

| Episode | Release step | Open steps before release | Per-step fire probability before release | Cumulative early-fire probability |
| ---: | ---: | ---: | --- | ---: |
| 0 | 7 | 5 | about `0.269` to `0.290` | `0.810` |
| 1 | 43 | 2 | about `0.334` | `0.556` |
| 2 | 4 | 3 | about `0.269` to `0.288` | `0.625` |

These probabilities are high enough to make stochastic early release likely
even though deterministic argmax still chooses `hold` because the binary
`fire_once` probability has not crossed `0.5`.

## Abstract Model

Within an A3/A5 legal first-shot window, define:

- state `s_t`: policy-observed contact, range, track age, C2/ROE state, and A5
  event mask;
- action `a_t in {hold, fire_once}`;
- stochastic event hazard `h_t = pi(fire_once | s_t)`;
- deterministic release rule: fire only if `h_t > 0.5` under the masked binary
  argmax;
- stochastic first-event distribution:

```text
P(T = t) = h_t * product_{k < t} (1 - h_k)
P(T < q) = 1 - product_{k < q} (1 - h_k)
```

where `q` is the first quality-window step.

The current A6 label path trains a per-step BCE-style hazard target on the
observed rollout. If a stochastic `fire_once` is accepted before the quality
window, the A5 state machine transitions to `FiredAssess`; for the first-event
objective, the later quality window is no longer observed in that episode.

This creates on-policy early-event censoring:

- early stochastic fire produces a negative early-accepted label, but only after
  the early event has already terminated the first-event window;
- later quality-window positives exist only in episodes that survive long
  enough to reach them;
- as `h_t` rises into the `0.25` to `0.35` range, stochastic survival to the
  quality window becomes unlikely across several open steps;
- deterministic evaluation wants a probability above `0.5`, while stochastic
  collection can trigger early release at much lower per-step probability.

## Root Cause

The blocker is structural: the current objective is a per-step hazard label on
an on-policy trajectory whose first release is absorbing. It can move event
logits, but it does not provide the policy with a counterfactual value for
"hold now so that a better fire action is available later".

The observed failure is therefore not primarily:

- insufficient training steps;
- missing A6 labels;
- missing event-head gradient routing;
- raw event-head learning rate after A6-EVT-K;
- runtime legality failure, since A3/A5 release discipline remains intact.

It is a mismatch among three mechanisms:

1. Per-step stochastic hazard accumulation makes early release likely before
   deterministic argmax would ever fire.
2. The accepted first event censors the future quality-window evidence that
   should teach delayed firing.
3. The hazard BCE has no option-level or action-conditional credit assignment
   for the hold decision.

As a result, more L training or weight changes can trade between two bad
regimes: probabilities below argmax that still sample early stochastically, or
probabilities above argmax that can collapse back to near-immediate firing.

## Re-scope Decision

Pause additional L training and launch-window parameter tuning. The next A6
mechanism should be re-scoped away from independent per-step labels and toward a
counterfactual first-event objective.

Recommended next contract:

`A6-EVT-O Counterfactual Event-Time Objective`

The contract should investigate a mechanism with these properties:

- label or target distribution is not destroyed by on-policy early accepted
  releases;
- holding in the pre-window receives explicit credit relative to firing early;
- firing in the quality window receives concentrated event-time probability;
- stochastic collection is constrained or corrected so that early exploratory
  samples do not erase all later positives;
- diagnostics measure cumulative pre-window fire probability, not only per-step
  `fire_once` probability;
- deterministic and stochastic acceptance gates are evaluated under the same
  first-event timing target.

Candidate implementation directions:

1. Action-conditional event-value or advantage head: estimate `Q_hold` and
   `Q_fire_once` over the first-shot window, with pre-window hold advantage and
   quality-window fire advantage.
2. Event-time survival objective: train a distribution over the first release
   time, including survival to the quality window and fire likelihood inside the
   quality window, rather than independent per-step BCE labels.
3. Counterfactual teacher labels: derive the quality-window target from
   policy-observed contact/ROE state even when the sampled action fired early,
   so early stochastic censoring does not remove the future target.
4. Training-only exploration constraint: suppress or reweight pre-window
   stochastic `fire_once` samples during collection while preserving A3/A5
   runtime legality. This is a supporting tool, not a substitute for value
   credit.

## Acceptance Implications

A6 remains held. A future accepted slice must prove more than "event probability
moved":

- deterministic probing executes one authorized first release inside the
  configured quality window;
- stochastic probing does not accumulate high pre-window release probability;
- per-episode release count, unauthorized release count, repeat count, and shot
  budget violations remain zero;
- cumulative pre-window early-fire probability is reported and bounded;
- A3/A5 masks and state-machine suppression remain the legal authority;
- M2, missile physics, Pk, fuze, damage authority, `2v2`, self-play, and real
  doctrine claims remain out of scope.

## Next Work Packet

Create `A6-EVT-O` as a design-first packet before any further implementation or
training:

```md
cluster: A6-EVT-O Counterfactual Event-Time Objective
scope: objective contract and focused prototype plan
write set: A6 objective/contract docs first; code/config only after contract review
non-goals: L knob tuning, M2 release, runtime legality changes, missile authority
validation: mathematical review, focused label tests, cumulative hazard diagnostics plan
return packet: selected mechanism, labels, losses, diagnostics, acceptance gate, rollback gate
```
