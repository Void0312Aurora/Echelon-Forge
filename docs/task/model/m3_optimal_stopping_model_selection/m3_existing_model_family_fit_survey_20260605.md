# M3 Existing Model-Family Fit Survey

Status: `2026-06-05` M3-R3 research packet.

Parent: [M3 Optimal-Stopping Model Selection](README.md).

Assigned cluster: `M3-R3 Existing Model-Family Fit Survey`.

## Scope

This note surveys practical model families that can fit the current repo
constraints for a finite-horizon one-shot timing problem with legality masks,
post-event censoring, deterministic deployment, and cumulative early-hazard
control. It focuses on engineering fit, not academic breadth.

No implementation is proposed as accepted here. The synthesis pass owns the
final model contract.

## Repo-Fit Constraints

Current constraints from M3, M1/M2, and A7:

- Runtime legality remains authoritative. A3/A5 masks, fire-state discipline,
  shot budgets, and one-shot execution rules must not be weakened by a model
  family.
- A7 already has an additive event surface: `hybrid_event_head`,
  `hybrid_event_credit_head`, first-event labels carried through rollout data,
  per-window mass caps, source tags, `window_id`, `window_age`, and active
  diagnostics.
- The current PPO path samples flattened per-step minibatches. It can consume
  label fields outside observations, but it does not preserve contiguous
  sequence samples unless M2-style buffer work is opened.
- M1 is an observation-window validation line. It can provide short fixed
  history to the current HMoE PPO, but it is not a sequence-native training
  algorithm.
- M2 is held. A sequence-native Causal Transformer HMoE is a candidate route,
  not an allowed assumption for M3-R3.
- A7 evidence shows the key failure: conservative startup hazard gives
  deterministic `hold`; relaxed per-step hazard makes stochastic early release
  likely before desirable labels persist; online active event-credit rows can
  collapse late in training.
- A bounded follow-on should mostly touch policy/loss/config/test surfaces such
  as `python/rl/policy_algo/first_event_hazard.py`,
  `python/rl/policy_algo/ppo_adaptive_kl.py`,
  `python/rl/policy_algo/policies.py`, active config entries, diagnostics, and
  focused tests. It should not require physics, damage, ROE, or world runtime
  changes.

## Existing Data Surface

The current first-event label path already exposes useful fields:

```text
active, target, weight, source, window_age, window_id, had_accepted
```

It also distinguishes practical source classes:

```text
accepted, censored, deadline, prewindow, early_accepted,
shadow_quality, legal_open_quality
```

This is enough to prototype losses that operate per legal-open window or per
episode chunk. It is not enough to prove counterfactual behavior after an early
event unless the training path also collects hold trajectories, replay labels,
or explicit off-policy counterfactual windows.

## Candidate Families

| Family | Fit | Data requirement | Implementation risk | Status |
| --- | --- | --- | --- | --- |
| Episode survival-hazard head | Strong near-term fit if trained with window-level likelihood and deployment hazard budget. | Episode/window ids, legal masks, target/source labels, right-censored no-event rows. | Medium. Requires grouped loss over rollout windows and deterministic thresholding. | `recommend` |
| Direct stopping-distribution head | Strong for deterministic deployment because it predicts `P(tau=t)` or `P(no event)` directly. | Full legal-open window slices or padded windows; optional no-event bin. | Medium-high under current flattened PPO; easier as offline/distillation or M2. | `recommend for synthesis` |
| Constrained optimal-stopping / advantage head | Good conceptual fit, close to A7 credit head, but fragile if advantage is tiny or uncoupled from actor logits. | Event value targets, wait/fire returns, legal masks, counterfactual or stable proxy returns. | Medium-high. Current A7 evidence shows weak value-to-policy coupling risk. | `fallback` |
| Sequence or Transformer stopping distribution | Best long-horizon fit when sequence training exists. | Contiguous sequences, causal masks, valid masks, action/event history tokens. | High unless M2 is released. | `needs synthesis` |
| Offline hold-trajectory distillation | Strong support mechanism for censoring. | Deterministic hold rollouts, reconstructed desirable windows, optional replay/counterfactual labels. | Medium. Mostly tools and auxiliary training, but may diverge from on-policy distribution. | `recommend as support` |
| Ranking / ordinal timing losses | Useful auxiliary to separate prewindow from desirable rows without requiring exact event time. | Positive and negative rows within the same window or episode. | Low-medium. Easy to add, incomplete as a standalone policy. | `fallback auxiliary` |
| Hierarchical intent/execution split | Useful when intent can be chosen conservatively and execution obeys masks. | Intent labels or distillation targets, legal-open execution rows. | Medium. Needs clean contract to avoid hiding another threshold problem. | `recommend as support` |
| Naive per-step Bernoulli or coefficient tuning | Poor fit. It controls local probability, not episode-level early mass. | Current labels only. | Low code risk, high behavior risk. | `reject` |

## Family Notes

### 1. Episode Survival-Hazard Head

Model:

```text
lambda_t = sigmoid(g(H_t))
S_t = product_{k < t} (1 - lambda_k)
P(tau = t) = S_t * lambda_t
P(no event through window) = S_{T+1}
```

Fit:

- This is the smallest conceptual shift from the existing `hybrid_event_head`.
  It can still emit a local hazard/logit delta, but the loss is evaluated as an
  episode/window likelihood instead of independent per-step BCE.
- `window_id`, `window_age`, `active`, `target`, and `weight` already provide
  most grouping inputs needed for a first implementation.
- The loss can use right-censored no-event rows from deterministic hold
  trajectories without pretending every open step is an independent positive
  or negative action.

Data requirements:

- For accepted desirable events: event position within the legal-open window.
- For no-release hold windows: right-censored survival target.
- For prewindow rows: negative survival pressure before the desirable window.
- For early accepted rows: either negative event likelihood at the early step
  or exclusion from positive policy labels plus shadow-quality support.

Deterministic deployment rule:

```text
fire at first legal t where cumulative P(tau <= t | H_1:t) >= theta
and lambda_t >= lambda_min
and early_budget_before_desirable <= epsilon
```

For a purely online implementation, maintain `S_t` per environment and fire
when `S_t * lambda_t` or cumulative mass crosses a calibrated threshold. Runtime
masking still gates the final action.

Early-hazard control:

- Penalize cumulative prewindow mass directly:

```text
L_early = max(0, sum_{t < t_quality} S_t * lambda_t - epsilon)^2
```

- Alternatively bound survival before quality:

```text
S_{t_quality} >= 1 - epsilon
```

Expected failure modes:

- If legal-open positive rows collapse late in online training, the hazard head
  may learn survival forever.
- If no-event censored windows are over-weighted, deterministic deployment will
  remain `hold`.
- If early negatives are weak, cumulative early mass can still become dangerous
  even with small local hazards.

Recommendation:

`recommend`. This is the most compatible near-term family because it addresses
the exact local-vs-episode mismatch while reusing much of the current A7 label
and diagnostics surface.

### 2. Direct Stopping-Distribution Head

Model:

For each legal-open window, predict normalized logits over legal event times and
one optional no-event bin:

```text
p_t = softmax(z_t masked over legal t plus z_no_event)
L = -log p_tau
```

Fit:

- This avoids the repeated small-hazard accumulation problem by allocating
  episode/window mass once.
- Deterministic deployment is natural: choose the first time whose mass crosses
  a threshold, or choose `argmax_t p_t` when online lookahead is available.
- It is less natural in flattened PPO minibatches because normalization needs
  all rows for a window.

Data requirements:

- Padded or grouped window slices with valid masks.
- One target index per window, or a no-event/censored target.
- If used online, either causal partial-window logits or a carried distribution
  state must be defined.

Implementation risk:

- Medium-high for current PPO because the training batch must preserve grouping.
- Lower as an offline distillation probe over reconstructed hold windows.
- Lower again if M2 opens a sequence buffer.

Interaction with M1/M2/A7:

- M1 can feed richer fixed history into the logits but cannot solve grouped
  normalization by itself.
- M2 would make this family clean because contiguous sequence samples and valid
  masks are first-class.
- A7's current event head could be reused only as a per-step score function;
  the loss and deterministic rule would change.

Recommendation:

`recommend for synthesis`. It is behaviorally attractive, but the next bounded
contract must decide whether grouped loss support is acceptable before M2.

### 3. Constrained Optimal-Stopping / Advantage Head

Model:

Learn stop-vs-wait values:

```text
A_stop(t) = Q_stop(H_t) - Q_wait(H_t)
fire if M_t = 1 and A_stop(t) >= margin
```

Fit:

- This matches the current A7 credit-head idea and can keep value diagnostics.
- It can express "wait now, stop later" if `Q_wait` includes future desirable
  event value.
- It is a standard way to frame one-shot decisions when future value matters.

Data requirements:

- Stable targets for stop and wait returns.
- Counterfactual or replay support is needed when early stop censors the future.
- If only current on-policy outcomes are used, the model can confuse early
  sampled stops with good stops.

Implementation risk:

- A7 already demonstrated the main risk: credit-head-only learning and tiny
  detached advantages did not create a reliable deterministic actor boundary.
- A future value head must not be the sole teacher for event logits unless the
  actor receives direct signed stopping supervision or calibrated margins.

Early-hazard control:

- Add an explicit prewindow constraint on `A_stop`:

```text
max_{t < quality} A_stop(t) <= -margin
```

- Do not rely only on entropy, startup bias, or coefficient sweeps.

Recommendation:

`fallback`. Keep value/advantage as diagnostics or auxiliary support, but do
not make it the only next contract after A7's value-to-policy breakpoint.

### 4. Sequence / Transformer Stopping Distribution

Model:

Use a causal sequence model over observation/action/event history:

```text
h_1:T = causal_transformer(O_1:T, A_1:T-1, event_tokens)
z_t = stop_head(h_t)
```

Then train either hazard likelihood, direct stopping distribution, or ordinal
timing losses over masked sequence samples.

Fit:

- This is the cleanest long-horizon representation for delayed effects, recent
  actions, launch events, and target-track evolution.
- It fits the M2 target architecture, not the current unlocked implementation
  boundary.

Data requirements:

- Contiguous rollout slices, `episode_starts`, valid masks, and no future
  leakage.
- Action/event history tokens and reset-safe inference state.

Implementation risk:

- High if started immediately. It needs sequence buffer, causal extractor,
  sequence HMoE policy, and sequence-aware PPO.
- It should not be launched merely because A7 is blocked; M3 explicitly keeps
  M2 as a candidate, not an assumed cure.

Recommendation:

`needs synthesis`. Strong family, but too broad for the next bounded fix unless
M3 synthesis chooses a deliberate M2 release.

### 5. Offline Hold-Trajectory Distillation

Model:

Collect deterministic or scripted hold trajectories that preserve future
desirable-window evidence, then distill a stopping target:

```text
teacher_tau = first desirable legal-open time, best ranked time, or no-event
student loss = event-time likelihood / margin / ranking on policy observations
```

Fit:

- Directly addresses post-event censoring by observing what would have happened
  if the agent had not fired early.
- A7 already uses hold-batch diagnostics effectively; this turns that diagnostic
  path into a training or pretraining data source.

Data requirements:

- Hold or constrained-low-hazard trajectories from the same scenario family.
- Reconstructed legality, quality window, and prewindow labels.
- Optional replay/counterfactual validation that labels remain meaningful under
  the policy's observation contract.

Implementation risk:

- Medium. Data collection and label generation are toolable without runtime
  behavior changes, but off-policy distillation can overfit to hold-only state
  distributions.
- Needs on-policy fine-tuning or a deployment guard so the model does not fail
  after a real event changes observations.

Early-hazard control:

- Train the teacher to choose inside the desirable window and assign strong
  negative labels before it.
- Calibrate deployment on cumulative prewindow false-stop probability, not only
  per-step accuracy.

Recommendation:

`recommend as support`. It is likely the best way to supply non-censored timing
evidence to a survival or stopping-distribution head.

### 6. Ranking / Ordinal Timing Losses

Model:

Instead of requiring an exact event time, enforce ordering:

```text
score(quality row) >= score(prewindow row) + margin
score(late/deadline row) >= score(prewindow row) + margin_late
```

Fit:

- This is easy to add to A7-style labels because rows already have source tags
  and window ids.
- It directly targets the observed failure where prewindow and quality rows
  rise together.

Data requirements:

- At least one positive and one negative row in the same window or episode.
- Window grouping for pair construction.

Implementation risk:

- Low-medium. Pair sampling must be bounded to avoid quadratic cost.
- It does not allocate total event probability mass and therefore should not be
  the only deterministic policy contract.

Early-hazard control:

- Ranking helps by pushing prewindow score below quality score, but it still
  needs a separate cumulative-hazard or deterministic threshold calibration.

Recommendation:

`fallback auxiliary`. Useful with survival or stopping-distribution losses, not
enough alone.

### 7. Hierarchical Intent / Execution Split

Model:

Separate an episode/window-level intent from step execution:

```text
intent_t in {no_event_yet, prepare_to_stop, execute_now, post_event}
execution fires only when intent_t = execute_now and M_t = 1
```

Fit:

- This aligns with HMoE routing and the existing distinction between mission
  state, event head, and execution masks.
- It can keep deterministic execution conservative while allowing an upstream
  head to choose a timing mode or target window.

Data requirements:

- Intent labels from hold-trajectory teachers, ordinal windows, or hand-built
  phases.
- Legal-open execution labels for `execute_now`.

Implementation risk:

- Medium. If intent is only another per-step classifier, it inherits the same
  cumulative hazard problem.
- Must avoid turning environment state into tactical memory. Intent belongs in
  policy/model state, not simulation-side hidden latches.

Recommendation:

`recommend as support`. Pair it with survival or distributional timing so the
hierarchy has an episode-level object.

### 8. Naive Per-Step Bernoulli / Coefficient Tuning

Model:

```text
fire_t ~ Bernoulli(sigmoid(z_t))
L = per-step BCE(target_t, sigmoid(z_t))
```

Fit:

- This is closest to the rejected behavior pattern: local probability is tuned
  while episode-level early mass is uncontrolled.
- A low startup prior gives deterministic hold; a modest relaxed prior makes
  early stochastic fire likely over many prewindow steps.

Recommendation:

`reject`. It can remain as a diagnostic baseline, but it should not be the next
M3 model contract.

## Deterministic Deployment Rule

Any recommended family should expose an explicit deterministic rule before
training is accepted. The minimum rule:

```text
if M_t == 0:
    action = wait
elif already_fired:
    action = wait
elif early_budget_before_quality_exceeded:
    action = wait
elif stop_score crosses calibrated threshold:
    action = fire_once
else:
    action = wait
```

For survival models, `stop_score` should be cumulative event mass or event
density, not only local `lambda_t`. For distributional models, it should be the
selected event-time mass under a no-event-aware distribution. For
optimal-stopping value models, it should be a signed margin with calibrated
prewindow suppression.

Deployment diagnostics should record at least:

```text
prewindow cumulative mass
quality-window mass
no-event mass
first crossing step
deterministic fire count
stochastic first-event step distribution
active label count by source
```

## Early-Hazard Control

The next contract should treat early hazard as an episode-level budget:

```text
P(tau < t_quality) <= epsilon
```

Practical controls:

- cumulative prewindow penalty for survival heads;
- no-event bin plus masked stopping distribution for distributional heads;
- hard negative signed margin on prewindow rows for actor/event logits;
- per-window positive and negative mass caps retained from A7;
- low stochastic exploration before the desirable window, with exploration
  scheduled through a budget rather than startup-bias relaxation;
- hold-trajectory distillation to keep positive windows visible without
  requiring early stochastic exploration.

## Interaction With M1, M2, And A7

M1:

- Helps any per-step or window head by adding short observable history.
- Does not by itself solve grouped event-time likelihood or sequence training.
- Good near-term pairing: M1 observation window plus survival-hazard or ranking
  auxiliary loss.

M2:

- Best fit for direct stopping distributions and sequence Transformer stopping
  heads.
- Should remain held unless synthesis decides the grouped/sequence contract is
  worth the implementation cost.
- If M2 opens, M3 should require causal-mask tests, valid-mask sequence losses,
  and deterministic timing probes before learned-policy claims.

A7:

- Provides valuable label infrastructure, source diagnostics, event-head and
  credit-head hooks, projection support, and mass caps.
- Also provides negative evidence: value-to-policy detached credit alignment,
  safe-bias relaxation, and local BCE-like hazard tuning are not enough.
- A near-term M3 contract should reuse A7's label and diagnostic surface but
  change the target object from local action probability to event-time or
  window-level stopping control.

## Expected Failure Modes

Any M3 follow-on should explicitly gate against these behavior risks:

- Deterministic non-crossing: the learned score stays below the fire threshold
  everywhere, producing `0` deterministic releases even when positives exist.
- Cumulative early release: individually small local hazards accumulate across
  many prewindow steps and censor the desirable window.
- Coupled score lift: prewindow and quality-window rows rise together, giving
  stochastic events but no timing discriminator.
- Label starvation: stochastic early releases or rollout segmentation remove
  legal-open quality rows from the online update path.
- Value-policy mismatch: value or credit heads improve while actor/event logits
  do not receive a calibrated signed boundary.
- Off-policy teacher drift: hold-trajectory labels are clean but fail after the
  deployed policy enters post-event observations.
- Grouping loss mismatch: a model that needs full windows is trained on
  flattened minibatches and silently degenerates into per-step BCE.
- Mask leakage: closed-mask or post-event shadow rows train executable fire
  logits instead of remaining value-only, projected, or diagnostic evidence.

## Recommendation Status

Recommended core candidate:

- Episode survival-hazard head with explicit window/episode likelihood,
  cumulative early-hazard budget, no-event/censor handling, and deterministic
  threshold rule.

Recommended support mechanisms:

- Offline hold-trajectory distillation to create non-censored timing evidence.
- Ranking/ordinal timing auxiliary to separate prewindow and quality rows.
- Hierarchical intent/execution split only if the intent head is trained on an
  episode-level timing object.

Needs synthesis:

- Direct stopping-distribution head. Strong behavior fit, but grouped training
  may require a new buffer/loss contract.
- Sequence/Transformer stopping distribution. Strong long-term fit, but should
  be gated through M2.

Fallback:

- Constrained optimal-stopping value head, if actor/event logits receive direct
  signed supervision and early-hazard constraints.

Rejected:

- Naive per-step Bernoulli classification.
- Another coefficient sweep over startup fire bias or local BCE weights without
  cumulative early-mass diagnostics.

## Residual Questions For Synthesis

- Can the next bounded contract add grouped window losses inside current PPO
  without opening M2?
- Should the no-event/censored bin be trained from deterministic hold rollouts,
  on-policy no-release rollouts, or both?
- What is the acceptable prewindow early-mass budget for short probes?
- Should the first implementation keep a hazard head for online causality and
  add a distributional offline probe for calibration?
- Which A7 diagnostics should become required gates for any M3 follow-on:
  cumulative prewindow mass, active label persistence, deterministic crossing,
  or all three?
