# A7 Target Construction And Credit Sign Audit

Status: `2026-06-04` `A7-EVC-I` audit pass; this repair requirement was
addressed later by
[A7-EVC-J Shadow Quality Target Repair](a7_event_value_advantage_credit_head_shadow_quality_repair_20260604.md).

Parent: [README.md](README.md). Chinese companion:
[a7_event_value_advantage_credit_head_target_construction_credit_sign_audit_20260604.zh.md](a7_event_value_advantage_credit_head_target_construction_credit_sign_audit_20260604.zh.md).

## Question

The A7 r3 run proves that the event-credit path is trainable, but the learned
policy remains held:

- deterministic probe executes `0` first-shot releases;
- stochastic probe releases too early at steps `14`, `47`, and `2`;
- A7 diagnostics report negative event advantage even in the quality window.

The audit question is therefore not whether another coefficient or short train
could move the curve. The question is which model link makes the learned
credit sign wrong.

## Verdict

The primary structural fault is target construction.

A7's objective contract required counterfactual shadow-quality evidence:
an early stochastic accepted release must not erase the later quality-window
state that would have rewarded holding. The implementation still builds labels
through the absorbing first-event state machine:

- `AdaptiveKLPPO.collect_rollouts()` collects `fire_mask` and launch-window
  facts from the pre-step policy observation, then records `fire_once_accepted`
  from `env.step()` infos.
- `build_first_event_hazard_labels()` only opens a first-event label window
  while `engagement_state == AuthorizedReady` and `fire_mask == true`.
- when a stochastic `fire_once` is accepted before quality, the label builder
  marks pre-window / early-accepted negative labels and sets
  `episode_has_first_event = true`;
- after that absorbing first event, the later quality-window geometry is no
  longer eligible to become a positive A7 target.

So A7 did not fail because the auxiliary head cannot train. It failed because
the auxiliary head is trained on a censored label distribution that removes
the very positives it was supposed to preserve.

## Code Evidence

Relevant surfaces:

- `python/rl/policy_algo/ppo_adaptive_kl.py`
  - `_first_event_label_collection_enabled()` correctly enables label
    collection when A7 credit coefficients are active.
  - `_build_a6_first_event_labels_from_rollout_infos()` routes A7-only runs
    into the shared first-event label builder with A7 weights.
  - `collect_rollouts()` computes `a6_policy_fire_mask` and
    `a6_policy_launch_window` before stepping the environment, then appends
    post-step accepted/rejected infos.
- `python/rl/policy_algo/first_event_hazard.py`
  - `build_first_event_hazard_labels()` defines a label window as the first
    contiguous `AuthorizedReady && fire_mask` segment.
  - early accepted release before quality is explicitly converted into
    negative labels and then closes the episode's first-event path.
  - `compute_first_event_credit_loss()` trains
    `Q_fire_once - Q_hold` with `BCEWithLogits`; this is an advantage-logit
    classifier, not a full two-action value target. That is acceptable as a
    prototype only if labels are semantically correct.

This means the actual A7 implementation does not satisfy the objective
contract's `shadow_quality_reachable` rule.

## Reconstructed Label Evidence

I reconstructed current labels from the r3 probe CSVs under the active A7
config:

- launch window: `8000m <= range <= 30000m`;
- maximum track age: `5s`;
- minimum window age: `32` steps;
- A7 pre-window hold weight: `0.4`;
- A7 early-accept weight: `1.0`;
- A7 deadline weight: `1.0`.

| Probe | Rows | Active labels | Positive labels | Negative labels | Positive weight | Negative weight | Sources |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| deterministic r3 | `2401` | `1880` | `1076` | `804` | `1076.0` | `321.600067` | `prewindow=804`, `deadline=1076` |
| stochastic r3 | `7203` | `19` | `0` | `19` | `0.0` | `9.3999996` | `prewindow=16`, `early_accepted=3` |

The stochastic per-episode reconstruction is decisive:

| Episode | Accepted step | Active labels | Positive labels | Shadow quality states after accepted release |
| --- | ---: | ---: | ---: | ---: |
| `0` | `14` | `12` | `0` | `1080` |
| `1` | `47` | `6` | `0` | `1061` |
| `2` | `2` | `1` | `0` | `1081` |

Each stochastic episode physically reaches many quality-window states after
the early accepted release, but the current label builder emits zero positives.
The event-credit head is therefore trained to view those trajectories as only
negative timing evidence.

## Model-Level Diagnosis

Abstract the current setting as a first-event decision process:

```text
state s_t includes contact/C2/geometry facts
action a_t in {hold, fire_once}
fire_once is absorbing for the first-shot event surface
quality(s_t) becomes true later in many trajectories
label y_t should express whether fire_once is better than hold at s_t
```

The current supervised auxiliary target is endogenous to the sampled action:

```text
if a_tau = fire_once before quality:
    later quality(s_t) is removed from the target builder
    observed positives for the episode become zero
```

This is not ordinary sparse reward. It is action-induced censoring of the
supervised target. Once stochastic exploration samples an early accepted shot,
the dataset says only "fire was bad before quality" and never says "holding
would have reached a good firing state". Delta alignment then faithfully
distills that negative sign into the event logits.

This explains all observed symptoms:

- deterministic argmax does not cross into release because the quality-window
  advantage is still negative;
- stochastic sampling can still fire early because probability mass remains
  nonzero;
- one-shot discipline remains legal because A3/A5 masks work;
- further label-weight tuning cannot create positive counterfactual evidence
  once the target builder has censored it.

## Ruled-Out Primary Causes

| Candidate | Audit result |
| --- | --- |
| Runtime legality / C2/ROE | Not primary. Stochastic r3 releases are authorized one-shot releases with no unauthorized, repeat, or budget violations. |
| A7 training path disabled | Not primary. TensorBoard contains live `a7/event_credit_loss`, and focused PPO tests confirm the credit head update path. |
| HMoE hierarchy gap | Watch item, not primary for this failure. The wrong sign is already present in A7 credit labels/advantages before a hierarchy-attributable policy-coupling diagnosis is needed. |
| Small coefficient / short train only | Not primary. More training on the same censored labels reinforces the same sign bias. |

## Repair Direction

This audit spawned `A7-EVC-J Shadow Quality Target Repair`, which has since
fixed the label-censoring path. The direction below is retained as the repair
contract that J implemented.

Required direction:

- keep A3/A5 runtime masks and absorbing first-shot legality unchanged;
- split runtime legal fire eligibility from target-side shadow quality
  observability;
- collect post-early-release quality facts when contact/C2/geometry remain
  observable;
- back-propagate shadow evidence to pre-release states instead of training
  invalid post-release `fire_once` actions;
- preserve window mass caps so repaired positives do not create another dense
  label imbalance;
- add focused target-construction tests for:
  - early accepted before quality with later shadow quality reachable;
  - accepted fire inside quality;
  - no shadow quality reachable;
  - window mass caps with both positive and negative target mass.

The important design point is that a post-release quality state is evidence
about a counterfactual hold trajectory, not a legal post-release fire action.
The repair should therefore create target credit for the pre-release decision
timeline rather than simply labeling closed-mask post-release rows as fire
positives.

## Decision

`A7-EVC-I` closes the current investigation: the failing link is the
counterfactual target construction, specifically missing shadow-quality target
repair after early stochastic accepted release.

`A7-EVC-J` has since changed and tested the target builder. Its repaired 32k
probe remains behavior-held, so the next residual is legal-state projection /
policy-coupling diagnosis rather than the original label-censoring bug.
