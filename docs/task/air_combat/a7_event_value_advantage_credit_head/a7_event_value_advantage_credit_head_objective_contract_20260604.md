# A7 Objective Contract

Status: `2026-06-04` selected implementation contract for `A7-EVC-A/B`;
policy/PPO code is not changed by this document.

Parent: [README.md](README.md). Chinese companion:
[a7_event_value_advantage_credit_head_objective_contract_20260604.zh.md](a7_event_value_advantage_credit_head_objective_contract_20260604.zh.md).

## Decision

A7 will implement an action-conditional event-value / advantage-credit head for
the masked `hold/fire_once` event action. The selected mechanism is:

```text
A_event(s_t) = Q_fire_once(s_t) - Q_hold(s_t)
```

The head is trained from a counterfactual first-shot timing target, and the
policy event-logit delta is coupled to the learned event advantage. This is not
an L-only label-weight tuning wave. Adaptive label balancing may be used as a
guardrail, but the primary repair is counterfactual hold/fire credit under the
A3/A5 legal event surface.

## Evidence Inputs

| Input | Contract implication |
| --- | --- |
| A5 event action | `hold/fire_once`, the event mask, `FiredAssess`, and one-shot suppression remain runtime authority. |
| A6-EVT-K | The event decision can cross deterministic argmax when the dedicated event lane is strong enough. |
| A6-EVT-L/M | Launch-window labels suppress near-immediate deterministic release, but can push deterministic fire below crossing. |
| A6-EVT-N | Per-step stochastic hazard accumulation plus absorbing first-event censoring is the mechanism blocker. |
| A6 label-density issue | Window-balanced credit must avoid unbounded pre-window negative mass. |
| HMoE gap issue | The A7 head must not rely only on the hard-routed combat subexpert to learn hold/fire timing. |

## Target Semantics

The A7 label builder should derive a bounded per-step target from rollout infos
and policy observations:

| Term | Meaning |
| --- | --- |
| `legal_open_t` | A5 fire mask is open under A3 C2/ROE state. |
| `quality_open_t` | The A6 launch-window quality gate is open, using configured range, track-age, and minimum window-age conditions. |
| `pre_quality_t` | `legal_open_t` is true and `quality_open_t` is false before the desired quality window. |
| `early_accepted_t` | `fire_once` is accepted before `quality_open_t`. |
| `shadow_quality_reachable` | The rollout later exposes a quality-window state from policy-observed contact/C2 facts, even if an early accepted first event closed the ordinary fire mask. |

The target sign is:

```text
y_t = -1  for pre-quality hold credit
y_t = -1  for early accepted fire penalties
y_t = +1  for quality-window fire credit
```

The value target is the relative preference, not a real-world missile doctrine
or Pk target. `y_t=-1` means `Q_hold > Q_fire_once`; `y_t=+1` means
`Q_fire_once > Q_hold`.

## Counterfactual Censoring Rule

A7 must not let an early stochastic accepted release erase all later positive
evidence. The first implementation should add a shadow target pass:

- keep the runtime A5 state machine unchanged;
- keep ordinary `fire_once` acceptance absorbing for environment legality;
- continue deriving `quality_open_t` from policy-observed contact/C2 facts after
  an early accepted release when those facts remain present in the rollout;
- assign hold credit to pre-quality states when the shadow pass shows the
  episode would have reached a quality window;
- assign lower-confidence hold credit, not dense full-weight negatives, when no
  shadow quality evidence appears.

If the current rollout data cannot support this shadow pass, `A7-EVC-D` must
record that as a blocker before falling back to simple L reweighting.

## Window Balancing

A7 must normalize target mass by first-shot window, not by raw step count. The
implementation should bound positive and negative weight per window:

```text
sum(w_negative_pre_quality in window) <= a7_event_credit_negative_mass_cap
sum(w_positive_quality in window) <= a7_event_credit_positive_mass_cap
```

This prevents the A6-L failure mode where many legal-open pre-window negatives
overwhelm rare quality-window positives. The balancing guard is part of A7, but
it is a support mechanism for the credit head rather than the main fix.

## Head Placement

The first A7 implementation should add a policy-level sibling to
`hybrid_event_head` inside
[policies.py](../../../../python/rl/policy_algo/policies.py):

- expose `Q_hold`, `Q_fire_once`, and `A_event`;
- initialize the head at zero so the initial policy is unchanged;
- give the head an explicit optimizer group or documented optimizer membership;
- read the shared policy latent and, if needed, the post-HMoE hold/fire event
  logits;
- do not place the only A7 signal inside one hard-routed subexpert.

This placement accounts for the HMoE hierarchical-computation gap without
redesigning HMoE. HMoE repair remains an issue-board follow-on unless A7
evidence shows correct credit signs but failed policy coupling.

## Loss Contract

The implementation should train two coupled losses:

```text
A_value = Q_fire_once - Q_hold
target = 1 if y_t = +1 else 0

L_value = window_balanced_BCEWithLogits(A_value, target, active, weight)
L_delta = SmoothL1(event_logit_delta, stop_gradient(clamp(A_value, -c, c)))
          or confidence-gated BCEWithLogits(event_logit_delta, target)
L_A7 = a7_event_credit_value_coef * L_value
     + a7_event_credit_delta_align_coef * L_delta
```

Implementation may choose either `SmoothL1` distillation or confidence-gated
BCE for `L_delta`, but it must satisfy this gate: the advantage head cannot be
diagnostic-only. It must influence the event logits or PPO update.

## Diagnostics

A7 diagnostics must include:

- `Q_hold` mean by pre-window and quality-window states;
- `Q_fire_once` mean by pre-window and quality-window states;
- `A_event` sign fraction by pre-window and quality-window states;
- policy `event_logit_delta` by the same windows;
- cumulative pre-window stochastic release probability:

```text
P_early = 1 - product_t(1 - sigmoid(event_logit_delta_t))
```

The learned-policy evidence must report deterministic release timing,
stochastic first-release timing, release counts, violation/repeat/budget counts,
advantage signs, and `P_early`.

## Implementation Entry Points

Expected write surfaces for later clusters:

- `python/rl/policy_algo/policies.py`
- `python/rl/policy_algo/ppo_adaptive_kl.py`
- `python/rl/policy_algo/first_event_rollout_buffer.py`
- a new or extended first-event credit helper under `python/rl/policy_algo/`
- `python/training/diagnostics.py`
- `python/training_callbacks.py`
- focused tests under `tests/hmoe/`, `tests/training/`, and
  `tests/diagnostics/`
- active air-combat training config JSONs

`experiments_tmp` output is evidence only and must not be staged.

## Initial Implementation Gates

Before a learned-policy probe, A7 implementation must pass focused gates for:

- zero initialization and constructor serialization;
- head output shape and finite values;
- event-logit coupling when the event mask is open and closed;
- A7 target labels for pre-quality, quality, early accepted, and shadow-quality
  cases;
- window balancing under sparse positives and dense negatives;
- PPO loss plumbing and finite logs;
- cumulative pre-window hazard diagnostics;
- active config parsing.

## Rollback Gates

Hold or re-scope A7 if any of these occur:

- A3/A5 masks or `FiredAssess` suppression are weakened;
- the head becomes diagnostic-only;
- implementation reduces to L-only weight tuning;
- deterministic probing returns to near-immediate authorization/contact release;
- deterministic probing never fires despite correct `A_event` signs;
- stochastic probing accumulates high `P_early` or violates one-shot discipline;
- HMoE redesign is attempted without a separate accepted issue task.

## Dispatch Result

`A7-EVC-A` and `A7-EVC-B` are closed by this contract. `A7-EVC-C Policy Head
Prototype` has supplied the stable `hybrid_event_credit_head` API, and
`A7-EVC-D PPO Auxiliary Credit` has wired the focused PPO loss. The next
dispatchable cluster is `A7-EVC-E Config And Diagnostics`.
