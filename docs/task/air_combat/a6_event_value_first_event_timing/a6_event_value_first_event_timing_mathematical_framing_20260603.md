# A6 Mathematical Framing: Masked First-Event Timing

Status: `2026-06-03` P1 framing for `A6-EVT-B Mathematical Framing`.

Parent: [README.md](README.md). Inputs:
[A6 observation](a6_event_value_first_event_timing_observation_20260603.md),
[A6 task clusters](a6_event_value_first_event_timing_task_clusters_20260603.md),
and the A5
[event contract](../a5_constrained_event_action_model/a5_constrained_event_action_model_event_contract_20260603.md).

## Boundary

This note frames only the S1 C2/ROE `hold/fire_once` event surface. It does not
release M2, change missile physics, Pk, fuze, damage authority, stock-weapon
authority, real-world doctrine, scenario maturity, `2v2`, or self-play. It also
does not weaken A3/A5 masks, post-launch suppression, shot-budget handling, or
pending-assessment handling.

Legality remains a constraint. A6 may add value, hazard, or curriculum labels
inside legal support; it must not make unauthorized release a learned
preference through reward-only tuning.

## Constrained Semi-MDP View

At policy step `t`, define the policy-visible state:

```text
s_t = (o_t, e_t, c_t, b_t, h_t)
```

where:

- `o_t` is the current reactive or M1 temporal observation window.
- `e_t` is A5 `engagement_state` in
  `{Hold, AuthorizedReady, FiredAssess, ReattackReady, Winchester}`.
- `c_t` is the vector of A5 mask components, including C2 authorization,
  target presence, shot budget, pending-assessment suppression, weapon
  readiness, ammo availability, and reattack authorization.
- `b_t` is the remaining shot-budget / ammo surface already exposed by A3/A5.
- `h_t` is event history needed to distinguish not-yet-fired, fired-and-assess,
  and explicitly reopened reattack support.

The final release support bit is:

```text
m_t = 1 if and only if A5 fire_mask is true
```

The event-action set is:

```text
A = {hold, fire_once}
M_t = [1, m_t]
```

`hold` is always legal. `fire_once` is legal only when `m_t = 1`. The masked
policy is therefore:

```text
pi(a_t | s_t, M_t) over {hold, fire_once}, with pi(fire_once)=0 when m_t=0
```

This is a constrained semi-MDP because the meaningful decision is not a raw
per-frame threshold. It is a stopping decision over legal event windows. Holding
inside a window advances time and preserves the option while the support remains
open. Firing once consumes the event and transitions to `FiredAssess`, after
which A5 suppression removes `fire_once` support until an explicit legal
follow-on state exists.

## Event Windows And First Event

A legal first-shot window `W_k` is a maximal contiguous interval:

```text
W_k = {t_start, ..., t_end}
where m_t = 1 and e_t = AuthorizedReady for all t in W_k
```

For the first A6 contract, `AuthorizedReady` should be the primary window. A
future contract may include `ReattackReady`, but only as a separate named
window type with its own diagnostics. It must not blur first-shot and reattack
labels.

The first accepted event time is:

```text
tau = min {t in W_k : fire_once_accepted_t = 1}
```

If no accepted release occurs before the window closes or the episode ends, the
window is censored:

```text
tau = censored
```

A6 should optimize the timing of `tau` under the mask, not raw
`fire_weapon` thresholding and not illegal action recovery.

## Available Label Sources

A5 diagnostics already provide label material for A6 without reading unstaged
artifacts as authoritative evidence:

| Source field / summary | A6 use | Boundary |
| --- | --- | --- |
| `engagement_state` | Segment `AuthorizedReady`, `FiredAssess`, and possible reattack windows. | State names define support; they are not doctrine labels. |
| `fire_mask` and mask components | Define legal support and censored/non-censored windows. | Mask-closed steps cannot be positive `fire_once` labels. |
| `fire_once_requested` / `fire_once_accepted` | Distinguish policy intent from accepted event. | Rejected requests are not valid positive labels. |
| `fire_once_rejected_reason` | Diagnose impossible labels and contract mistakes. | A contract must not learn to overcome these reasons by force. |
| `release_executed` / `authorized_release_count` | Mark accepted first-event occurrence. | They prove event execution, not missile outcome quality. |
| violation, repeat, and budget counts | Guard against weakening A3/A5 discipline. | These are safety diagnostics, not targets to tune via reward only. |
| `policy_event_prob_fire_once_*` and mode counts | Measure whether logits move from A5 baseline. | Probability movement alone is not acceptance if releases or safety regress. |
| retained A5 release steps in stochastic probes | Candidate weak labels or curriculum seeds. | Stochastic timing is evidence that firing is expressible, not proof of optimal timing. |

The retained A5 observation gives the baseline to beat: deterministic had `1880`
fire-mask-open / `AuthorizedReady` steps, `0` fire requests, and near-zero
`fire_once` probability, while stochastic probing produced `3` authorized
releases over `3` episodes with no violation, repeat, or budget failures.

## Why Deterministic Hold Is Credit And Timing

A5 proves that legal event support exists and that stochastic exploration can
sample the event. Once sampled and accepted, the state machine consumes the
event and blocks unsafe repeats. Therefore deterministic `hold` is not best
explained by missing action support or missing legality.

The failure is credit/timing:

- The useful event may occur hundreds of steps after the window opens.
- The terminal or mission reward is delayed and sparse relative to the
  `hold/fire_once` logit update.
- `hold` receives many legal samples in the same window, so ordinary PPO updates
  can make "continue holding" the dominant deterministic mode.
- A rare stochastic `fire_once` sample can be accepted, but its advantage does
  not reliably assign value to the masked event action at the right time.

A6 should therefore give the event head an explicit learnable target for
stopping inside legal windows.

## Candidate Objective Contracts

| Candidate | Target | How it affects logits | Strength | Main risk |
| --- | --- | --- | --- | --- |
| Event-value head | Learn `Q_event(s_t, hold)` and `Q_event(s_t, fire_once)` or an advantage delta inside `m_t=1` windows. | Use action-conditional event value to bias or supervise the event head. | Directly addresses `hold` versus `fire_once` value under the mask. | Needs careful bootstrapping and must not invent value on censored/illegal steps. |
| First-event hazard objective | Learn `h_t = P(tau=t | tau>=t, s_t, m_t=1)` over legal windows. | Adds a masked binary/time-to-event loss that increases fire probability near labeled event times. | Natural fit for stopping-time data and censored windows. | Label quality is fragile if all positive times come from stochastic weak labels. |
| Curriculum-assisted labels | Create bounded positive labels, such as "fire once within a legal window," for early training. | Temporarily raises `fire_once` likelihood while A5 masks keep legality. | Useful for escaping near-zero event probability and generating data. | Can become imitation of an arbitrary timing rule unless paired with event value or hazard. |

Recommended ordering for `A6-EVT-C`: choose one primary contract, then state
whether curriculum is only a bootstrap aid. The durable contract should be
event-value or hazard, with curriculum treated as bounded support rather than
the definition of correctness.

## Rejected Labels

A6 must reject these label sources or target definitions:

- Positive `fire_once` labels on any step where `fire_mask=0`.
- Labels that require bypassing `FiredAssess`, pending-assessment suppression,
  shot-budget limits, ammo limits, or weapon readiness.
- Raw `fire_weapon` threshold targets from the pre-A5 binary surface.
- "Always fire on the first `AuthorizedReady` step" as a final optimality
  claim. It may be considered only as a bounded curriculum seed.
- Rejected fire requests as successful labels.
- Missile hit, Pk, fuze, damage, or weapon-physics labels not exposed by the
  accepted S1 C2/ROE event contract.
- Real-world doctrine labels or claims about tactical correctness.
- Reward-only legality penalties as the mechanism that makes illegal release
  unattractive.

## Failure Modes

A6-EVT-C and later implementation must guard against:

- Event logits move in stochastic mode but deterministic argmax remains `hold`.
- `fire_once` probability rises on mask-closed steps because the objective does
  not apply the A5 mask.
- The objective teaches first-shot timing but regresses A5 no-repeat,
  no-budget-violation, or pending-assessment discipline.
- Curriculum labels create an arbitrary early-fire habit that does not survive
  removal of the curriculum weight.
- Hazard labels treat censored windows as negative at every step and suppress
  valid late firing.
- Event value bootstrapping leaks terminal reward into illegal or post-launch
  states.
- Reattack support is accidentally merged with first-shot support.
- Diagnostics report `release_executed` but fail to distinguish requested,
  accepted, rejected, authorized, violation, repeat, and budget outcomes.

## Questions For A6-EVT-C

`A6-EVT-C Objective Contract` must answer exactly these before implementation:

1. Which primary contract is selected: event-value head, hazard objective,
   curriculum-assisted labels, or a staged combination?
2. What is the supervised or bootstrapped target, and on which masked window
   steps is its loss active?
3. How are censored windows represented: ignored, right-censored hazard
   examples, negative labels, or bootstrapped value states?
4. Which A5 fields are required in rollout buffers, callbacks, and process
   probes to compute the target and diagnostics?
5. How does the selected target couple to `hold/fire_once` logits during PPO
   without replacing the A5 masked categorical semantics?
6. What deterministic-eval metric must move relative to the A5 baseline:
   `fire_once` probability, mode count, request count, accepted release count,
   or all of them?
7. What rollback criteria protect A3/A5 legality if violations, repeat release,
   budget failures, or rejected-fire reasons regress?
8. Is curriculum used at all, and if so, what schedule removes or bounds it so
   that it does not become the acceptance claim?
9. Are `ReattackReady` windows excluded from the first contract or modeled as a
   separate window type with separate labels?
10. What focused tests prove mask handling, loss shape, finite stats,
    deterministic evaluation, and unchanged A5 suppression?

## Exit Statement

P1 frames A6 as a masked first-event timing problem under a constrained
semi-MDP. It does not select the implementation contract. The next cluster must
choose the objective and define its labels, masks, diagnostics, tests, and
rollback criteria before any code, config, scenario, or training-kernel edits.
