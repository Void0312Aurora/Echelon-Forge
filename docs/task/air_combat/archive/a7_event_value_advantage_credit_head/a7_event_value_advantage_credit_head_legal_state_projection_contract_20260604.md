# A7 Legal-State Projection Contract

Status: `2026-06-04` selected design contract for `A7-EVC-L`; implementation is
not started by this document.

Parent: [README.md](README.md). Chinese companion:
[a7_event_value_advantage_credit_head_legal_state_projection_contract_20260604.zh.md](a7_event_value_advantage_credit_head_legal_state_projection_contract_20260604.zh.md).

## Decision

`A7-EVC-K` shows that the post-J blocker is not missing positive labels. It is
a domain mismatch:

```text
shadow_quality positives live on post-release closed-mask observations
event policy needs positive fire_once credit on legal-open observations
```

A7 will therefore stop treating raw `shadow_quality` rows as direct
`fire_once` advantage targets on the closed state. The next implementation
slice should use them as evidence for a legal-state projection path:

```text
raw shadow row o_t in FiredAssess
  -> project only A3/A5 legal-state fields back to AuthorizedReady/open mask
  -> keep target/contact geometry and launch-quality facts
  -> train A_event(project_legal_open(o_t)) positive
  -> allow delta alignment only on the projected legal-open sample
```

This is a legality-preserving projection contract, not an instruction to
re-open the real environment state after launch.

## Structural Model

The current S1/A7 learning problem is an MDP with an absorbing first-event
transition:

```text
s_t = (x_t, z_t)
x_t = target/contact/geometry facts
z_t = C2/ROE and A5 engagement state

fire_once legal only when z_t is AuthorizedReady and the fire mask is open
fire_once accepted before quality -> z_{t+1...} becomes FiredAssess
```

`A7-EVC-J` recovers later quality evidence from `x_u`, but it observes it under
`z_u = FiredAssess`. A policy update on `fire_once` is only valid on a state in
which `fire_once` is legal. The required object is therefore:

```text
Pi_legal(s_u) = (x_u, z_authorized_ready)
```

`Pi_legal` is a feature-space training projection for auxiliary credit. It is
not a runtime state transition, not a physics model, and not missile doctrine.

## Projection Whitelist

For `air_combat_c2_roe_v1` observations, projection may only rewrite fields
that determine the A3/A5 event-action legality surface:

| Field surface | Projection rule |
| --- | --- |
| `event_action_mask` | Force `hold=1`, `fire_once=1` for projected samples. |
| `fire_mask` | Force open only for projected samples. |
| `mission[5]` WCS state | Set to a fire-permissive value consistent with the existing mask reconstruction. |
| `mission[6]` authorization | Set authorized. |
| `mission[14]` engage-order state | Set to a non-hold engagement order. |
| `mission[15]` shot-policy state | Set to a positive fire-permitted shot policy. |
| `mission[16]` shot budget | Set to at least one remaining shot for the projected first-shot decision. |
| `mission[17]` pending assessment | Clear pending assessment. |
| `mission[19]` target contact | Preserve or force present only when the source row already has valid target/contact evidence. |

Projection must preserve target/contact geometry, contact history, range,
track-age facts, and any unrelated ownship state. It must not copy damage,
missile outcome, post-launch success, or hidden future information into policy
inputs. If a future observation layout cannot be projected by this whitelist,
the implementation must skip projection and report that unsupported layout
rather than silently training closed-mask alignment.

## Loss Contract

The next implementation should separate three signals:

| Signal | Source | Trains | Delta alignment |
| --- | --- | --- | --- |
| Legal negative | `prewindow`, `early_accepted` on actual legal-open observations | `A_event(obs) < 0` | yes |
| Raw shadow opportunity | `shadow_quality` on closed-mask observations | optional continuation/opportunity value only | no |
| Projected legal positive | `project_legal_open(obs)` for `shadow_quality` rows | `A_event(projected_obs) > 0` | yes |

The core loss becomes:

```text
L_raw_negative =
  BCEWithLogits(A_event(obs), 0) on prewindow/early_accepted rows

L_projection_value =
  BCEWithLogits(A_event(Pi_legal(obs)), 1) on shadow_quality rows

L_projection_delta =
  SmoothL1(delta(Pi_legal(obs)), stop_gradient(clamp(A_event(Pi_legal(obs)))))
  or BCEWithLogits(delta(Pi_legal(obs)), 1)

L_A7L =
  a7_event_credit_value_coef * L_raw_negative
  + a7_event_credit_projection_value_coef * L_projection_value
  + a7_event_credit_projection_delta_align_coef * L_projection_delta
  + optional a7_event_credit_opportunity_coef * L_opportunity
```

Raw `shadow_quality` rows must not enter `L_delta` on their closed-mask
observation. If the implementation keeps any raw shadow value term, it should
be renamed as opportunity/continuation value rather than direct fire advantage.

## Implementation Entry Points

Expected write surfaces for the follow-on prototype:

- Add a small projection helper, preferably under
  `python/rl/policy_algo/first_event_projection.py`.
- Extend `AdaptiveKLPPO._first_event_credit_loss()` to build projected minibatch
  observations for `source == A6_FIRST_EVENT_SOURCE_SHADOW_QUALITY` and compute
  a second distribution on the projected observations.
- Extend `compute_first_event_credit_loss()` or add a sibling helper so raw
  negatives, projected positives, and optional opportunity value are reported
  separately.
- Add config knobs for projection value/delta coefficients and an explicit
  `a7_event_credit_legal_projection_enabled` guard.
- Extend diagnostics to report projected active count, projected advantage
  mean, projected delta mean, and unsupported projection count.
- Focused tests should cover projection field rewrites, unsupported layout
  refusal, no closed-mask delta alignment, and positive projected delta
  pressure.

The first implementation should not require rollout-buffer schema changes if
projection can be derived from `rollout_data.observations` and existing
`source/window_id` fields. If that proves false, the implementation must record
the missing buffer contract before expanding the buffer.

## Validation Gates

Before another learned-policy training run:

```bash
python -m compileall -q python/rl/policy_algo/first_event_projection.py python/rl/policy_algo/first_event_hazard.py python/rl/policy_algo/ppo_adaptive_kl.py
pytest tests/policy/test_first_event_timing_contracts.py -q
pytest tests/policy/test_event_head_update_contracts.py tests/policy/test_auxiliary_training_updates.py -q
pytest tests/training/test_event_timing_training_config_contracts.py tests/training/test_diagnostics_callback_contracts.py -q
git diff --check -- docs/task/air_combat docs/task/issues python/rl/policy_algo tests/policy tests/training
```

The first learned-policy probe after these gates should remain short and should
report deterministic timing, stochastic timing, one-shot violations, raw shadow
active count, projected legal active count, projected advantage sign, and
projected delta sign.

## Non-Goals

- Do not enable delta alignment on raw closed-mask `shadow_quality` rows.
- Do not weaken A3/A5 masks or `FiredAssess` suppression.
- Do not treat projection as a runtime re-opening of fire permission.
- Do not use this contract to release HMoE redesign, M2, missile/Pk/fuze/damage
  authority, `2v2`, self-play, or real doctrine.
- Do not start another 32k training wave until the projection prototype passes
  focused gates.

## Dispatch Result

`A7-EVC-L` selects legal-state projection with split raw-shadow opportunity and
projected legal-open positive alignment. The next implementation candidate is
`A7-EVC-M Projected Legal-Open Credit Prototype`.
