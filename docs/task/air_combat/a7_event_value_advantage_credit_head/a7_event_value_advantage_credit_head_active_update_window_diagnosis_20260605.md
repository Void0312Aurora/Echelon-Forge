# A7 Active Update Window Diagnosis

Status: `2026-06-05` pass; root cause localized to rollout-local first-event
credit assignment. Parent: [README.md](README.md).

## Question

`A7-EVC-V` repaired the online credit update lane by moving A7 value credit onto
a detached-latent, credit-head-only optimizer step with its own clip budget. The
8k observation still ended with deterministic `0` releases and slightly
negative legal-open credit advantage. The W question was whether this remaining
failure is credit-head capacity, protected update coupling, active-label
availability, or a broader training-loop contract.

## Evidence

V TensorBoard scalar review shows that A7 labels and updates are live only
early in the run:

| Train step | `a7/event_credit_active_count_mean` | Source pattern |
| --- | ---: | --- |
| `1024` | `174.0` | mostly `prewindow`, with early accepted negatives |
| `1536` | `81.5` | mostly `prewindow` |
| `2048` | `64.0` | `LEGAL_OPEN_QUALITY` becomes visible |
| `2560` | `64.0` | `LEGAL_OPEN_QUALITY` still visible |
| `3072` | `18.5` | active count collapses |
| `3584` to `8192` | `0.0` | no active A7 update samples |

The final deterministic fixed-batch probe is not label-starved:

```text
active labels: 2516
LEGAL_OPEN_QUALITY positives: 1356
accepted releases: 0
legal-open positive advantage mean: -0.0525766723
```

A stochastic final-model rollout exposes the missing segmentation effect. The
same 512-step episode has an accepted release at step `6` and first launch-window
open state at step `282`.

When labels are built on the whole 512-step episode:

```text
active labels: 236
positive labels: 231
sources: prewindow=4, early_accepted=1, shadow_quality=231
```

When the same trajectory is split into training-sized `128` step chunks:

| Chunk | Steps | Fire-open steps | Launch-window steps | Active labels | Positives | Sources |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | `1-128` | `5` | `0` | `5` | `0` | `prewindow=4`, `early_accepted=1` |
| 2 | `129-256` | `0` | `0` | `0` | `0` | none |
| 3 | `257-384` | `0` | `103` | `0` | `0` | none |
| 4 | `385-512` | `0` | `128` | `0` | `0` | none |

So the positive shadow-quality evidence exists on the real episode, but it is
not visible to the current PPO rollout-local label builder.

## Diagnosis

The current A7 label function is non-local in episode time, but it is evaluated
locally on each PPO rollout segment.

Let an episode trajectory be:

```text
tau = (s_1, a_1, ..., s_T)
```

and PPO slices be:

```text
S_k = tau[t_k : t_k + n_steps)
```

The intended first-event credit label is an episode-level function:

```text
y_t = L(tau, t)
```

because a label at a later quality-window state can depend on an earlier
accepted release. The implementation instead computes:

```text
y_t' = L(S_k, t)
```

inside each rollout buffer. In the early-release case, `L(tau, t)` and
`L(S_k, t)` differ whenever the accepted release and later quality window fall
on different sides of a rollout boundary.

This is exactly the observed V failure:

- early stochastic accepted release happens before the quality window;
- the first rollout chunk sees only negative prewindow/early-accepted labels;
- later chunks are in `FiredAssess` / pending-assessment, so `fire_mask_open`
  is false;
- the later chunks have no memory that an early accepted event happened in a
  previous rollout, so the shadow-quality repair cannot emit positives;
- after all vector envs enter that long pending-assessment tail, A7 active
  samples collapse to zero.

This explains why final deterministic probes still see many legal-open windows:
deterministic mode does not accept the early release, so the fire mask stays
open and the fixed-batch probe can build legal-open positives. Training uses
stochastic on-policy sampling, and the sampled early release pushes the episode
into a long segment where the rollout-local target is censored.

## Ruled-Out Explanations

| Candidate | Current status | Evidence |
| --- | --- | --- |
| Credit-head capacity | unlikely root cause | `A7-EVC-T` showed fixed-batch legal-open positives can be fit by updating the credit head alone. |
| Shared PPO global clipping | repaired, not sufficient | `A7-EVC-V` added protected credit-head-only updates and the active update lane is live early. |
| Missing explicit window state | not sufficient | `A7-EVC-S` exposed `air_combat_c2_roe_v2` state completion, but behavior remained held. |
| No positive legal-open labels exist | false in deterministic/fixed batch | Final fixed-batch probe has `1356` legal-open positives. |
| HMoE hierarchy gap | still a watch item | It can become relevant after correct credit signs are learned; the present failure is visible before that as rollout-local label censoring. |

## Repair Direction

The long-term repair should be a cross-rollout first-event credit state
contract, not another coefficient sweep.

Recommended `A7-EVC-X` contract:

- Maintain per-env first-event credit state across PPO rollouts:
  `episode_id`, first-window start, early accepted step, early accepted age,
  and pending shadow-quality status.
- Reset the state only on `done` / episode id change.
- When an early accepted release is observed before quality, mark a carried
  shadow-positive obligation for that episode.
- In later rollouts from the same episode, emit `SHADOW_QUALITY` positives once
  `launch_window_open` and the configured minimum quality age are reached, even
  if `fire_mask_open` is now false due to pending assessment.
- Add diagnostics:
  `a7/evc_carried_shadow_pending_envs`,
  `a7/evc_carried_shadow_positive_count_mean`,
  `a7/evc_cross_rollout_first_event_count_mean`, and rollout age summaries.
- Add a focused regression test that compares whole-episode labels against
  `128` step chunked labels for the early-release-at-step-6, launch-window-at-
  step-282 case.

Secondary mitigations such as larger `n_steps`, fixed positive replay batches,
or adaptive label scheduling may help training stability, but they should not
be treated as the primary repair. The immediate structural mismatch is that the
supervised label function has episode memory while the training implementation
currently throws that memory away at rollout boundaries.

## Closure

`A7-EVC-W` is accepted as a diagnosis slice. The remaining blocker is now named
as a training-loop contract fault:

```text
rollout-local first-event labels are not equivalent to episode-level
first-event credit when early accepted release and later quality window cross a
rollout boundary.
```

The next bounded action is `A7-EVC-X Cross-Rollout First-Event Credit State`.
