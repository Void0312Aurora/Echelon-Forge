# M3 Academic Literature Model Survey

Status: `2026-06-05` worker packet for `M3-R2 Academic Literature Survey`.

Parent: [M3 Optimal-Stopping Model Selection](README.md).

## Scope

This packet maps academic model families to the M3 formal problem: a
finite-horizon, partially observed, one-shot stopping-time decision with
legality masks and post-event censoring. The survey emphasizes primary sources
or stable publisher/preprint pages and treats the A7 evidence only as the
motivating instance of the generic problem.

M3 notation used below:

```text
lambda_t = P(tau = t | tau >= t, H_t, M_t)
S_t      = product_{k < t} (1 - lambda_k)
P(tau=t)= S_t lambda_t
```

## Recommendation Map

| Model family | Representative sources | Fit to M3 | Recommendation status |
| --- | --- | --- | --- |
| Discrete survival / event-time distribution networks | DeepHit; Dynamic-DeepHit | Strong fit for explicit `P(tau=t)` and right-censored labels if M3 can build counterfactual or hold-trajectory event-time labels. | `recommend` as a supervised event-time head, conditional on data repair. |
| Optimal stopping / American-option regression | Longstaff-Schwartz LSMC; Tsitsiklis-Van Roy; deep optimal stopping | Strongest mathematical match to "stop now vs continue" and deterministic stopping boundaries. | `recommend` as the conceptual contract for the synthesis. |
| Counterfactual dynamic treatment / off-policy learning under censoring | Marginal structural models; censored Q-learning; CRN/RMSN | Strong fit for action-induced censoring and policy-regime comparison, but assumption-heavy. | `recommend` as a correction layer, not as the whole deployed head. |
| Classical and neural survival hazards | Kaplan-Meier, Cox, DeepSurv, random survival forests | Useful calibration vocabulary and censoring likelihoods; incomplete for action-induced informative censoring. | `fallback` for diagnostics or auxiliary loss. |
| Sequence decision / point-process models | Decision Transformer; Transformer/Hawkes point processes | Useful for long history `H_t` and event intensity modeling; weak by default on identifiability and early-hazard control. | `needs synthesis`; use only with explicit stopping distribution and censoring contract. |
| Naive per-step Bernoulli classification | Common baseline rather than a recommended literature path | Recreates M3's observed mismatch: local step probability is not controlled episode-level event mass. | `reject`. |

## Source Summaries And M3 Fit

### 1. Classical Survival And Hazard Models

Sources:

- Kaplan and Meier, 1958, "Nonparametric Estimation from Incomplete
  Observations", JASA:
  <https://www.tandfonline.com/doi/abs/10.1080/01621459.1958.10501452>
- Cox, 1972, "Regression Models and Life-Tables", JRSS-B:
  <https://academic.oup.com/jrsssb/article/34/2/187/7027194>
- Katzman et al., 2016/2018, "DeepSurv: Personalized Treatment Recommender
  System Using A Cox Proportional Hazards Deep Neural Network":
  <https://arxiv.org/abs/1606.00931> and
  <https://link.springer.com/article/10.1186/s12874-018-0482-1>
- Ishwaran et al., 2008, "Random survival forests":
  <https://arxiv.org/abs/0811.1645>

Short summary:

Survival analysis estimates an event-time distribution under incomplete
observations. Kaplan-Meier estimates survival curves from right-censored data;
Cox models covariate effects on a hazard through a semi-parametric proportional
hazards assumption; DeepSurv replaces the Cox linear predictor with a neural
network; random survival forests provide a nonparametric tree ensemble for
right-censored outcomes.

Objective shape:

```text
continuous: h(t | x), S(t | x) = exp(- integral_0^t h(u | x) du)
discrete:   L = sum_i [ event_i log P(T_i=t_i | x_i)
                      + censored_i log P(T_i > c_i | x_i) ]
```

Assumptions:

- Event and censoring times are observed in a comparable population.
- Censoring is non-informative or is modeled well enough to avoid biased
  survival estimates.
- Cox and DeepSurv add proportional-hazard structure unless extended.
- Baseline survival is a population property, not automatically a causal
  counterfactual under a new policy.

Censoring treatment:

These models directly handle ordinary right censoring by contributing survival
past the censoring time rather than a false negative event. This is useful for
M3 notation, but the M3 censoring source is policy-induced: an early event
changes the later trajectory and label semantics. That is generally informative
censoring, not the benign follow-up loss assumed by basic survival estimators.

Fit-to-M3 analysis:

Survival hazards match M3's desired `lambda_t`, `S_t`, and `P(tau=t)` form.
They make cumulative early risk explicit:

```text
P(tau < t0) = 1 - product_{k < t0}(1 - lambda_k)
```

This is already better aligned than per-step binary classification. However,
classical survival models do not decide whether to stop; they predict time to
an event under a data-generating process. For M3 they are best used as a
calibrated event-time head, a diagnostic for early cumulative hazard, or an
auxiliary likelihood inside a larger stopping contract.

Deterministic deployment implications:

Survival output can deploy deterministically by selecting the legal time with
maximum `S_t lambda_t`, by crossing a calibrated cumulative probability
threshold, or by selecting the earliest legal time whose predicted value exceeds
a continuation baseline. The third rule already imports optimal-stopping logic.

Early-hazard control implications:

Survival losses let M3 penalize total prewindow mass rather than each local
hazard independently. A synthesis contract should include an explicit constraint
or regularizer such as:

```text
sum_{t < first_desirable_time} S_t lambda_t <= epsilon
```

Expected failure modes:

- Independent-censoring assumptions break when early stopping removes later
  desirable labels.
- Cox-style hazards may rank risk while still failing to allocate enough event
  mass inside a narrow desirable window.
- A survival predictor trained on behavior-policy events may learn when the old
  policy fired, not when the new policy should fire.
- Tree or Cox models can be easier to inspect but may underfit partial
  observability unless the history state is already well summarized.

Recommendation status: `fallback`.

Use the survival family as the calibration and likelihood vocabulary, but do not
make a plain Cox/DeepSurv-style hazard the sole M3 answer unless censoring is
made exogenous by data construction.

### 2. Direct Event-Time Distribution Networks

Sources:

- Lee et al., 2018, "DeepHit: A Deep Learning Approach to Survival Analysis
  With Competing Risks", AAAI:
  <https://ojs.aaai.org/index.php/AAAI/article/view/11842>
- Lee, Yoon, and van der Schaar, 2020, "Dynamic-DeepHit: A Deep
  Learning Approach for Dynamic Survival Analysis With Competing Risks Based on
  Longitudinal Data", IEEE Transactions on Biomedical Engineering:
  <https://pubmed.ncbi.nlm.nih.gov/30951460/> and
  <https://ieeexplore.ieee.org/abstract/document/8681104/>

Short summary:

DeepHit learns a discrete event-time distribution directly instead of assuming
a specific stochastic process or a proportional hazard. It combines likelihood
terms for observed/censored data with ranking terms. Dynamic-DeepHit extends the
same idea to longitudinal covariate histories, making predictions at successive
landmark times from temporal observations.

Objective shape:

```text
network outputs p_t = P(T=t | H_t_or_H_1:T)
event loss:    -log p_T
censor loss:   -log sum_{u > C} p_u
ranking loss:  encourage earlier predicted risk for subjects with earlier events
```

Assumptions:

- Time can be discretized at the decision cadence.
- Training data contain event times, censoring times, and enough uncensored or
  partially censored examples to identify the event-time distribution.
- Longitudinal versions need histories aligned to prediction landmarks.
- Ranking losses assume comparable subjects or trajectories.

Censoring treatment:

DeepHit-style likelihood naturally represents right-censored examples as
probability mass after the censoring time. For M3, this is attractive because
post-event rows can be excluded from event-label training without pretending
they are negatives. The unresolved issue is whether the censoring event is
independent. M3's early event is chosen by the policy and therefore must be
handled through hold trajectories, replay, inverse-probability correction, or a
counterfactual simulator branch.

Fit-to-M3 analysis:

This is the cleanest supervised form of the desired M3 event-time object. A
DeepHit-like head could output a finite-horizon distribution over `tau`, with
`M_t` applied as a hard mask before normalization or by zeroing illegal mass:

```text
p_t = 0 when M_t = 0
sum_t p_t + p_infinity = 1
```

It also directly supports "put probability mass in the desirable window without
raising all early hazards", because the model predicts a distribution rather
than independent Bernoulli logits.

Deterministic deployment implications:

Deployment can select:

```text
tau_hat = argmax_{t: M_t=1} p_t
```

or a risk-controlled earliest time:

```text
stop at first legal t where cumulative window utility exceeds wait utility
and prewindow cumulative mass remains below epsilon
```

The argmax rule is deterministic and avoids relying on stochastic chance firing,
but it must be paired with an abstain/no-event option when the desirable window
does not exist.

Early-hazard control implications:

Because the network's output mass is normalized across the horizon, early
probability can be controlled by distribution-level losses:

```text
L_early = alpha * sum_{t < first_desirable_time} p_t
L_window = - beta * log sum_{t in desirable_window} p_t
```

This is structurally closer to M3 than a local Bernoulli head.

Expected failure modes:

- The model will learn behavior-policy event times if labels come only from
  censored on-policy rollouts.
- Ranking losses may reward earlier predicted risk even when M3 wants low
  early hazard and a delayed desirable window.
- Discretization can blur narrow windows.
- Competing risks are not identical to "wait vs one-shot event"; adapting the
  objective must keep one-shot legality explicit.

Recommendation status: `recommend`.

Recommend as a supervised event-time distribution head if M3 can supply
uncensored, held, replayed, or counterfactually reconstructed labels. Without
that data repair, keep it as a target shape rather than a sufficient fix.

### 3. Optimal Stopping And American-Option Regression

Sources:

- Longstaff and Schwartz, 2001, "Valuing American Options by Simulation: A
  Simple Least-Squares Approach", Review of Financial Studies:
  <https://academic.oup.com/rfs/article-pdf/14/1/113/24432078/113.pdf>
- Tsitsiklis and Van Roy, 2001, "Regression Methods for Pricing Complex
  American-Style Options", IEEE Transactions on Neural Networks:
  <https://web.mit.edu/~jnt/www/Papers/J086-01-bvr-options.pdf>
- Becker, Cheridito, and Jentzen, 2018/2019, "Deep optimal stopping":
  <https://arxiv.org/abs/1804.05394>
- Becker et al., 2019, "Solving high-dimensional optimal stopping problems
  using deep learning":
  <https://arxiv.org/abs/1908.01602>

Short summary:

American-option methods solve finite-horizon problems where an agent may
exercise once. Longstaff-Schwartz estimates continuation value by regression on
simulated paths. Tsitsiklis-Van Roy frame related regression-based dynamic
programming. Deep optimal stopping replaces hand-crafted continuation
regressions with neural stopping rules or value approximators for high
dimensional paths.

Objective shape:

```text
V_T(H_T) = stop_payoff(H_T)
V_t(H_t) = max(stop_payoff(H_t), E[V_{t+1}(H_{t+1}) | H_t, wait])
stop when stop_payoff(H_t) >= continuation_value(H_t)
```

Assumptions:

- A payoff or utility is defined for stopping at each legal time.
- The learner can estimate continuation value from paths on which stopping has
  not already removed the future, usually through simulation, replay, or an
  off-policy dataset.
- The state/history representation is sufficient for continuation prediction.
- Distribution shift between training paths and deployed stopping behavior is
  controlled.

Censoring treatment:

This family does not treat censoring as a missing-data nuisance; it avoids the
problem by estimating "continue" values from paths that actually continue. That
matches the M3 core issue: after stopping, later labels are not valid evidence
for what would have happened under waiting. M3 therefore needs a data contract
that preserves wait-trajectory evidence, not only stopped rollouts.

Fit-to-M3 analysis:

This is the strongest literature match to the M3 formal object. M3's one-shot
event is an exercise decision; `M_t` is an exercise feasibility mask; the
desirable window is encoded in stop payoff and early-penalty terms; and the
deterministic decision boundary is native:

```text
if M_t = 1 and stop_value(H_t) - continue_value(H_t) >= delta:
    stop
else:
    wait
```

The hazard representation can be retained as a calibrated stochastic
approximation, but the core contract should be value/boundary based if the
desired deployment is deterministic.

Deterministic deployment implications:

Optimal stopping naturally deploys as a boundary rule rather than a Bernoulli
sample. A margin `delta` can provide conservative late firing and reduce early
boundary chatter. If no legal time has positive stop advantage, the model emits
`tau = infinity`.

Early-hazard control implications:

Early stops are controlled by the payoff design and continuation estimate. The
contract can make early event risk expensive at the episode level:

```text
stop_payoff_t = window_reward_t - early_penalty_t - illegal_penalty_t
```

Because the action is selected by comparing stop and wait values, M3 can avoid
raising all open-window hazards just to obtain any deterministic event.

Expected failure modes:

- If continuation value is learned from trajectories already censored by early
  events, the regression target is biased.
- Poor payoff shaping can make "never stop" or "stop immediately" optimal.
- Approximate dynamic programming can overfit simulated paths and produce
  unstable boundaries near narrow windows.
- Full-sequence or high-dimensional history may require a learned state encoder,
  increasing implementation risk.

Recommendation status: `recommend`.

Use this family as the primary conceptual anchor for M3 synthesis: a bounded
contract should compare stop value vs continuation value, with survival/event
distribution outputs used for calibration and diagnostics.

### 4. Counterfactual Dynamic Treatment And Off-Policy Decision Learning

Sources:

- Robins, Hernan, and Brumback, 2000, "Marginal Structural Models and Causal
  Inference in Epidemiology":
  <https://pubmed.ncbi.nlm.nih.gov/10955408/> and
  <https://journals.lww.com/epidem/fulltext/2000/09000/marginal_structural_models_and_causal_inference_in.11.aspx>
- Goldberg and Kosorok, 2012, "Q-learning with censored data":
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC3385950/>
- "Constructing Dynamic Treatment Regimes with Shared Parameters for Censored
  Data":
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC7305816/>
- Bica et al., 2020, "Estimating Counterfactual Treatment Outcomes over Time
  Through Adversarially Balanced Representations" / Counterfactual Recurrent
  Network:
  <https://arxiv.org/abs/2002.04083>
- Lim et al., 2018, "Forecasting Treatment Responses Over Time Using Recurrent
  Marginal Structural Networks":
  <https://papers.neurips.cc/paper/7977-forecasting-treatment-responses-over-time-using-recurrent-marginal-structural-networks.pdf>

Short summary:

Dynamic treatment-regime literature estimates policies over time from
observational or trial data where actions, outcomes, and censoring interact.
Marginal structural models use inverse-probability weighting to address
time-varying confounding. Censored Q-learning adapts sequential value learning
to right-censored survival outcomes. CRN and RMSN use recurrent sequence models
and balancing/weighting ideas to predict counterfactual outcomes under treatment
plans.

Objective shape:

```text
estimate E[Y^pi | H_t] or Q(H_t, A_t)
with weights approximately inverse to behavior treatment/censor probabilities
pi_hat(H_t) = argmax_a Q_hat(H_t, a)
```

Assumptions:

- Sequential ignorability: after conditioning on observed history, treatment
  assignment and censoring contain no unmeasured confounding relevant to the
  counterfactual outcome.
- Positivity: the data include enough examples of the relevant actions at the
  relevant histories.
- Treatment and censoring models are correctly specified or robustly estimated.
- Outcomes can be defined consistently under alternative policies.

Censoring treatment:

This family is directly relevant to M3 because it treats censoring and action
selection as part of the statistical problem. It offers inverse probability of
censoring weights, imputation, doubly robust estimation, and learned balanced
representations. For M3, early one-shot events can be treated as treatment
regimes whose later counterfactual labels must be estimated from comparable
wait trajectories or simulator branches.

Fit-to-M3 analysis:

The fit is strongest on identifiability, not on architecture. These methods
answer: "Can the desired timing rule be learned from on-policy censored data?"
The likely answer is "only with explicit correction or additional data." They
can provide off-policy estimates of a stopping rule's utility:

```text
regime pi_t(H_t) in {wait, stop}
evaluate E[window_reward - early_penalty - miss_penalty | do(pi)]
```

They are less direct as a deployable deterministic head unless paired with
optimal stopping or event-time distribution modeling.

Deterministic deployment implications:

Deployment is usually a deterministic regime:

```text
stop if estimated value(stop | H_t) > estimated value(wait | H_t)
```

or an `argmax` over candidate treatment/stopping policies. Confidence or
overlap diagnostics should gate deployment because high inverse-probability
weights indicate weak support.

Early-hazard control implications:

Early hazard can be controlled at the policy-evaluation level by assigning
large early-stop penalties and estimating the full-regime value. This prevents
the "many tiny local hazards accumulate" failure only if the learner evaluates
the whole stopping rule rather than isolated step logits.

Expected failure modes:

- Positivity violations are likely near rare desirable windows: the behavior
  data may not contain enough legal wait-until-window examples.
- Inverse-probability weights can have high variance.
- Hidden simulator state or partial observability can break ignorability.
- Learned counterfactual sequence models may produce plausible but unverifiable
  futures after an early event.
- These methods can estimate values while leaving the final stopping-boundary
  design unresolved.

Recommendation status: `recommend`.

Recommend as the evidence-correction layer for M3. If M3 continues to train on
on-policy censored rollouts, some counterfactual/off-policy treatment of the
data is structurally required.

### 5. Sequence Decision And Temporal Point-Process Models

Sources:

- Chen et al., 2021, "Decision Transformer: Reinforcement Learning via Sequence
  Modeling":
  <https://arxiv.org/abs/2106.01345>
- Janner et al., 2021, "Offline Reinforcement Learning as One Big Sequence
  Modeling Problem" / Trajectory Transformer:
  <https://trajectory-transformer.github.io/trajectory-transformer-neurips-2021.pdf>
- Zhang et al., 2019/2020, "Self-Attentive Hawkes Processes":
  <https://arxiv.org/abs/1907.07561>
- Zuo et al., 2020, "Transformer Hawkes Process":
  <https://arxiv.org/abs/2002.09291>

Short summary:

Sequence-modeling RL treats trajectories as token sequences of states, actions,
returns, and sometimes future plans. Temporal point-process models estimate
event intensities over time, and transformer variants use attention to capture
long-range dependencies in event histories.

Objective shape:

```text
Decision Transformer:
  maximize log P(a_t | return_to_go, H_t)

Trajectory model:
  maximize log P(s_{t+1}, r_t, a_t | history)
  plan by decoding or search

Point process:
  maximize sum_events log lambda(t_i | H_t) - integral lambda(u | H_u) du
```

Assumptions:

- Large, diverse offline trajectories exist.
- The behavior data include enough high-quality examples to imitate or plan
  from.
- Desired return conditioning or event intensity is identifiable from logged
  data.
- The model can represent `H_t` without relying on post-event rows that have
  changed semantics.

Censoring treatment:

These models do not inherently solve action-induced censoring. A Decision
Transformer trained naively on censored rollouts will imitate the old policy's
early events or no-events. A point-process model can represent intensity, but
it still needs a censoring likelihood and a distinction between "not yet
observed" and "future invalidated by our own stop."

Fit-to-M3 analysis:

The strong fit is memory: M3 is partially observed and may need a sequence
encoder over `H_t`. The weak fit is decision semantics: sequence models by
themselves optimize token likelihood, not necessarily the episode-level
stopping distribution or early cumulative hazard. A useful M3 variant would
attach a survival/event-time or stop-vs-continue head to a transformer/RNN
history encoder rather than deploy a generic action decoder.

Deterministic deployment implications:

Deterministic deployment is possible through greedy decoding, beam search, or
argmax event-time selection. But without an explicit one-shot mask and
probability-mass normalization, deterministic greedy actions can reproduce the
same threshold problem as A7: never fire when logits are too low, or fire too
early when they are raised.

Early-hazard control implications:

Point-process likelihood makes cumulative intensity visible:

```text
P(no event before t) = exp(- integral_0^t lambda(u) du)
```

For discrete M3 this maps back to `S_t`. Sequence RL models need an added
episode-level penalty or constrained decoder to control early mass.

Expected failure modes:

- Imitation of behavior-policy timing rather than desired timing.
- Out-of-distribution return conditioning when successful late-stop examples
  are scarce.
- Long context increases implementation risk without fixing labels.
- Attention over post-event tokens may leak invalid semantics into pre-event
  decisions unless censoring is explicitly masked.

Recommendation status: `needs synthesis`.

Use sequence models as history encoders or candidate offline planners only if
the final contract remains an explicit stopping distribution or value boundary.
Do not use generic sequence RL as a replacement for the M3 stopping objective.

## Cross-Family Conclusions

### Assumptions That Matter Most

1. M3 cannot assume ordinary independent censoring if the policy itself creates
   censoring by stopping early.
2. Any recommended model needs either wait-preserving trajectories,
   counterfactual simulator labels, replayed hold trajectories, or explicit
   off-policy correction.
3. A deterministic deployment rule must be part of the model contract. A
   stochastic Bernoulli head with tuned coefficients is not enough.
4. Legality masks should be hard constraints on admissible stopping times, not
   negative training labels on impossible actions.
5. Narrow desirable windows favor normalized event-time distributions or
   stop-vs-continue boundaries over independent local classifiers.

### Censoring Treatment For M3

Recommended synthesis pattern:

```text
pre-event rows:
  train event-time / stop-vs-continue objective

post-event rows:
  do not train as ordinary negatives for the same event semantics

held or replayed wait trajectories:
  supply continuation labels and desirable-window evidence

off-policy correction:
  estimate whether the candidate stopping rule remains supported by data
```

This pattern combines the survival literature's likelihood discipline with the
optimal-stopping literature's continuation-value discipline and the causal
literature's warning about policy-induced censoring.

### Deterministic Deployment Implications

The literature supports three deterministic deployment rules worth carrying to
synthesis:

```text
event-time MAP:
  tau_hat = argmax_t p(tau=t | H, M)

hazard threshold with cumulative cap:
  stop at first t where utility-adjusted cumulative event probability is high
  while P(tau < desirable_window) <= epsilon

optimal-stopping boundary:
  stop when stop_value(H_t) - continue_value(H_t) >= delta
```

The boundary rule is the most robust default for M3 because it explains both
"why stop now" and "why wait one more step."

### Early-Hazard Control Implications

Early hazard should be controlled as episode-level mass:

```text
P(tau < first_desirable_time) = sum_{t < first_desirable_time} S_t lambda_t
```

or through a continuation-value margin. Literature that only gives local action
probabilities must be adapted before it is acceptable for M3.

### Expected Failure Modes Across The Literature

- Event-time models identify the old behavior policy unless labels are repaired.
- Survival censoring assumptions are too weak for action-induced censoring.
- Optimal stopping fails if continuation labels are unavailable.
- Counterfactual methods fail under hidden confounding or support gaps.
- Sequence models improve memory but can hide the same local-action mismatch
  behind a larger architecture.
- All families can overfit narrow windows unless the no-event option and
  legality masks are explicit.

## Recommended M3 Synthesis Direction

Primary recommendation:

Use an optimal-stopping contract as the conceptual core:

```text
learn stop_value(H_t, M_t)
learn continue_value(H_t)
deploy stop iff legal and stop_value - continue_value >= delta
```

Attach either:

```text
1. a discrete event-time distribution head, DeepHit-style, for calibrated
   probability mass over tau; or
2. a survival hazard head for diagnostics and cumulative early-risk constraints.
```

Data recommendation:

Do not train the final M3 candidate only on rollout-local post-event labels.
Require one of:

- wait-preserving rollouts;
- replay/hold trajectories that reveal later desirable windows;
- simulator counterfactual branches;
- off-policy/censoring correction with support diagnostics.

Rejected alternative:

Reject another naive per-step Bernoulli coefficient sweep as the default path.
The literature points toward event-time likelihoods, continuation-value
regression, and counterfactual correction because the target is a stopping time,
not an independent binary label at each step.
