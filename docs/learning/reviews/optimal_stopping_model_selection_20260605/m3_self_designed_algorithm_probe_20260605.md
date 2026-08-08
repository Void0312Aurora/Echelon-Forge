# M3 Self-Designed Algorithm Probe

Status: `2026-06-05` R1 reasoning-only packet.

Parent: [M3 Optimal-Stopping Model Selection](README.md).

Cluster: `M3-R1 Self-Designed Algorithm`.

Search policy: no web search; no external citations. The algorithms below are
derived directly from the formal one-shot timing problem.

## Problem Assumptions

Shared notation follows the formal statement:

```text
T                finite horizon
H_t              learner history through t
M_t in {0,1}     hard legality mask
Q_t in {0,1}     desirable-window indicator or delayed proxy
A_t in {0,1}     one-shot action
tau              first legal event time, or infinity
lambda_t         online stopping hazard
S_t              survival probability before t
```

Additional assumptions used by this packet:

- The deployment contract must be deterministic: the model may estimate
  probabilities during training, but runtime must emit a single legal event time
  or no event.
- Masked rows are not negative examples of desire. They are non-executable rows,
  so they may shape state estimation but must not teach the model that the event
  is semantically wrong.
- On-policy data is censored after the first event. Rows after `tau` may be
  logged, but they are not equivalent to counterfactual wait trajectories.
- Low local early hazard is not enough. The relevant object is cumulative
  pre-window event probability over many wait steps.
- If no desirable window exists in an episode, the correct behavior may be
  `tau = infinity`; otherwise the model should allocate most event-time mass
  inside the first reachable desirable window.

## Candidate A: Masked Survival With Episode Risk Budget

Recommendation status: `recommend`.

### Model Class

Train an online masked survival model that predicts a legal stopping hazard
`lambda_t`, but optimize an episode-level event-time likelihood and an explicit
pre-window risk budget rather than independent per-step Bernoulli labels.

The executable hazard is:

```text
z_t = f_theta(H_t)
lambda_t_raw = sigmoid(z_t)
lambda_t = M_t * lambda_t_raw
S_1 = 1
S_t = product_{k < t} (1 - lambda_k)
p_theta(tau = t | H_1:t) = S_t * lambda_t
p_theta(tau = infinity) = product_{k <= T} (1 - lambda_k)
```

Let:

```text
D = {t : Q_t = 1 and M_t = 1}
E = {t : t < min D}
W = D or a soft desirable interval if Q_t is delayed
```

For episodes with an observed desirable legal time set `D`, define:

```text
P_theta(W) = sum_{t in W} S_t lambda_t
P_theta(E) = sum_{t in E} S_t lambda_t
P_theta(no_event) = S_{T+1}
```

The training objective:

```text
L(theta) =
  - log(P_theta(W) + eps)
  + alpha * max(0, P_theta(E) - rho_early)^2
  + beta  * max(0, P_theta(no_event) - rho_miss)^2
  + gamma * smoothness(lambda_1:T)
```

For episodes without a desirable window:

```text
L_none(theta) =
  - log(P_theta(no_event) + eps)
  + alpha_none * sum_t S_t lambda_t
```

The smoothness term should be weak and local, for example:

```text
smoothness(lambda_1:T) = sum_{t=2..T} (lambda_t - lambda_{t-1})^2
```

It is a regularizer only; it must not erase sharp legal-window transitions.

### Treatment Of Censoring

Only pre-event prefixes are used as equivalent-to-wait observations. If the
logged policy fired at `tau_obs`, rows `t > tau_obs` are excluded from direct
event likelihood because they are post-event censored.

For an episode that fires before a later desirable label could be observed, the
episode is treated as left-damaged/right-censored evidence:

```text
observed prefix: 1..tau_obs
known fact: model should not place large mass before tau_obs if tau_obs is
           believed early by the label builder
unknown fact: whether a desirable legal window would have appeared after tau_obs
```

A conservative censored-prefix loss is:

```text
L_censored(theta) =
  - log(S_{tau_obs} + eps)
  + alpha * max(0, P_theta(1..tau_obs) - rho_censored_prefix)^2
```

This loss says "survive this prefix" without pretending that the unseen suffix
contains negative labels.

If a held or replayed trajectory is available where the event was not taken,
the full `L(theta)` can be used. If only censored on-policy data exists, this
candidate remains identifiable only for early-risk suppression and requires
some uncensored or delayed-positive evidence to learn where to stop.

### Deterministic Deployment Rule

Runtime computes the full masked hazard stream online and tracks event-time
mass. Fire at the first legal time whose current event-time mass clears a
deterministic threshold and whose cumulative early budget remains valid:

```text
S = 1
early_mass = 0
for t in 1..T:
  lambda = M_t * sigmoid(f_theta(H_t))
  p_t = S * lambda

  if not window_candidate(H_t):
    early_mass += p_t

  if M_t == 1 and window_candidate(H_t) and p_t >= eta_stop:
    return A_t = 1

  if early_mass > rho_early_runtime:
    lambda = min(lambda, lambda_budget_cap(S, rho_early_runtime - early_mass))

  S = S * (1 - lambda)

return no_event
```

`window_candidate(H_t)` can be a learned desirable-window score threshold, a
calibrated quantile of `P_theta(W)`, or a small deterministic gate derived from
the same model state. It should not be a stochastic sample.

### Early-Hazard Control

The key control is on cumulative mass:

```text
P_theta(tau < first_desirable_time) =
  sum_{t in E} S_t lambda_t <= rho_early
```

This is stronger than requiring every `lambda_t` to be small. It prevents a
long pre-window prefix from accumulating many small chances into almost-certain
early firing.

### Expected Failure Modes

- If all positive windows are censored away by the behavior policy, the model
  can learn "do not fire early" but cannot identify the correct later window.
- A weak `window_candidate` gate can reintroduce local-classifier behavior.
- If `rho_early` is too strict, deterministic deployment may never fire.
- If masks are noisy, hard multiplication by `M_t` can hide useful positive
  structure on rows that were incorrectly marked illegal.

### Fit To M3

This is the strongest candidate because it matches the target object:
episode-level stopping-time density with one-shot legality and explicit
cumulative early-risk control. It still needs a data contract for uncensored or
delayed-positive evidence, but it avoids the structural mismatch of independent
per-step Bernoulli training.

## Candidate B: Ordinal Margin Stopper

Recommendation status: `fallback`.

### Model Class

Learn a scalar timing score `r_theta(H_t)` where desirable legal states should
rank above pre-window legal states. Deployment stops at the first legal crossing
of a deterministic threshold.

Training examples are ordered pairs, not independent action labels:

```text
P = {i : M_i = 1 and i before desirable window}
W = {j : M_j = 1 and Q_j = 1}
N = {k : M_k = 1 and no desirable window should be taken}
```

Pairwise objective:

```text
L_rank(theta) =
  sum_{i in P, j in W} max(0, m + r_theta(H_i) - r_theta(H_j))
  + delta * sum_{k in N} max(0, r_theta(H_k) - b_none)
  + mu * sum_t max(0, r_theta(H_t) - r_theta(H_{t+1}) - d_drop)
```

The final term is optional and only enforces mild temporal consistency. It
should allow score drops after the desirable opportunity passes.

### Treatment Of Censoring

Pairs are formed only from rows that share compatible counterfactual meaning.
If an episode fired early, then:

```text
use rows t <= tau_obs as pre-window survival evidence
do not create negative pairs against rows t > tau_obs
do not assume W is empty merely because W is unobserved
```

For censored early-fire episodes, the safe contribution is:

```text
L_censored_rank(theta) =
  sum_{i <= tau_obs, M_i = 1} max(0, r_theta(H_i) - b_early)
```

This suppresses early scores without claiming to know the missing positive
suffix. Positive ranking still requires complete, held, replayed, or otherwise
uncensored sequences containing desirable rows.

### Deterministic Deployment Rule

```text
armed = false
for t in 1..T:
  score = r_theta(H_t)

  if M_t == 1 and score >= b_arm:
    armed = true

  if armed and M_t == 1 and score >= b_stop and local_peak(score_history):
    return A_t = 1

return no_event
```

`b_arm <= b_stop`. The `local_peak` condition can be replaced by a required
minimum dwell time above `b_arm`. This prevents a single noisy tick from firing.

### Early-Hazard Control

This candidate controls early action by score separation:

```text
r_theta(H_i) + m <= r_theta(H_j)
for pre-window i and desirable-window j
```

and by setting `b_stop` from a validation quantile that bounds observed
pre-window false crossings:

```text
Pr(max_{i in P} r_theta(H_i) >= b_stop) <= rho_early
```

This is deterministic and easy to inspect, but it is not a true probability
budget unless validation data is representative.

### Expected Failure Modes

- Does not naturally express "fire somewhere in this window" as probability
  mass; it expresses "score is high enough now."
- Early censored data supplies negatives but not positives, so the model can
  become overly conservative.
- If the desirable window is broad, the first threshold crossing may be legal
  but suboptimal within the window.
- Threshold calibration can drift when rollout policy or mask distribution
  changes.

### Fit To M3

This is a useful fallback when deterministic interpretability and low
implementation risk matter more than full event-time calibration. It should not
be the primary recommendation unless the available data cannot support a
survival likelihood but can support reliable pairwise ordering.

## Candidate C: Anchor-Then-Gate Stopping Policy

Recommendation status: `needs synthesis`.

### Model Class

Separate the episode-level intent from step-level execution. A sequence encoder
or carried recurrent state proposes an anchor distribution over legal event
times, and a small execution gate fires deterministically when the online state
matches the selected anchor.

Training model:

```text
g_theta(H_1:t) -> u_t
a_phi(u_1:T, M_1:T) -> p_phi(tau = t), with p_phi(t) = 0 when M_t = 0
e_psi(H_t, anchor_state_t) -> executable gate score
```

The anchor distribution is normalized over legal times plus no-event:

```text
p_phi(t) =
  M_t * exp(a_t) / (exp(a_infty) + sum_k M_k exp(a_k))
p_phi(infinity) =
  exp(a_infty) / (exp(a_infty) + sum_k M_k exp(a_k))
```

Objective for episodes with desirable windows:

```text
L_anchor =
  - log(sum_{t in W} p_phi(t) + eps)
  + alpha * sum_{t in E} p_phi(t)
  + beta  * max(0, p_phi(infinity) - rho_miss)^2
```

Execution imitation binds the online gate to the chosen anchor:

```text
t_star = deterministic_anchor(p_phi, W, M)
L_gate =
  sum_t BCE(e_psi(H_t, t_star), 1[t = t_star])
  with rows M_t = 0 masked out of the positive class
```

Total:

```text
L = L_anchor + kappa * L_gate
```

### Treatment Of Censoring

The anchor head must not train on post-event rows from early-fired on-policy
episodes as if they were complete legal alternatives. For censored prefixes:

```text
if tau_obs is before any verified desirable row:
  penalize anchor mass on t <= tau_obs
  keep remaining suffix unlabelled
else if tau_obs is inside verified W:
  allow likelihood mass on observed W prefix
```

In equations:

```text
L_anchor_censored =
  alpha * sum_{t <= tau_obs, M_t = 1} p_phi(t)
  - log(p_phi(infinity) + sum_{t > tau_obs} p_phi(t) + eps) * w_survive
```

The second term is weak: it says the chosen time should survive beyond the
censored early prefix, not that no event should occur later.

### Deterministic Deployment Rule

The model first selects a deterministic anchor from the current episode prefix
or from a rolling sequence state:

```text
t_hat = argmax_{t in legal_future or infinity} p_phi(t)

for t in 1..T:
  if t_hat == infinity:
    continue
  if t == t_hat and M_t == 1 and e_psi(H_t, t_hat) >= b_exec:
    return A_t = 1
  if t > t_hat + grace and no fire:
    recompute t_hat or return no_event according to contract
```

For strict determinism, recomputation must be contract-defined: either anchors
are fixed at an episode planning point, or they are recomputed at fixed ticks
with monotone "no earlier than current time" constraints.

### Early-Hazard Control

The anchor distribution directly penalizes early mass:

```text
sum_{t in E} p_phi(t) <= rho_early
```

The execution gate cannot fire outside the selected anchor region. This makes
early firing a two-key failure: both anchor selection and gate threshold must
fail.

### Expected Failure Modes

- Requires more sequence memory and a clearer contract for when anchors are
  computed.
- If the anchor is selected too early under partial observability, it may miss
  late-emerging desirable evidence.
- Gate imitation can collapse into a local classifier if the anchor head is not
  authoritative.
- Handling dynamic legality masks is harder when future masks are unknown.

### Fit To M3

This is promising if the next model contract is allowed to carry episode-level
state or perform fixed-interval replanning. It is less minimal than Candidate A
and should be decided during synthesis against implementation risk.

## Candidate D: Local Bernoulli With Cumulative Penalty

Recommendation status: `reject`.

### Model Class

This candidate keeps a local per-step Bernoulli action head but adds an
episode-level early-risk penalty:

```text
lambda_t = M_t * sigmoid(f_theta(H_t))
L_local =
  sum_t BCE(lambda_t, y_t)
  + alpha * max(0, sum_{t in E} lambda_t - rho_step_sum)^2
```

Deployment would fire when:

```text
M_t == 1 and lambda_t >= b_stop
```

### Treatment Of Censoring

It can drop post-event rows and mask illegal rows, but the core labels remain
local. If early action censors later positives, the objective still sees many
wait labels and few active desirable labels.

### Early-Hazard Control

The penalty controls `sum lambda_t`, not event-time mass:

```text
sum_{t in E} lambda_t
```

This is only an approximation to:

```text
sum_{t in E} S_t lambda_t
```

It ignores survival interaction and therefore does not fully represent a
one-shot stopping distribution.

### Expected Failure Modes

- Low hazards can still fail deterministic threshold crossing.
- Raising hazards can still make stochastic or threshold deployment fire early.
- Censored positives remain missing, so late desirable evidence can disappear.
- The objective remains dominated by local row balance rather than event-time
  allocation.

### Fit To M3

This is a useful rejection baseline because it appears close to the current
local-action framing while leaving the central mismatch intact. It should not
be selected as the next M3 contract.

## Cross-Candidate Recommendation

| Candidate | Status | Best use | Main blocker |
| --- | --- | --- | --- |
| A Masked Survival With Episode Risk Budget | `recommend` | Primary next model contract if M3 can require uncensored or delayed-positive evidence. | Needs enough non-censored positive-window evidence to identify where to stop. |
| B Ordinal Margin Stopper | `fallback` | Low-risk deterministic scorer when ranking evidence is easier than likelihood calibration. | No native event-time mass or survival likelihood. |
| C Anchor-Then-Gate Stopping Policy | `needs synthesis` | Higher-capacity design if episode-level planning state is acceptable. | More implementation contract complexity. |
| D Local Bernoulli With Cumulative Penalty | `reject` | Baseline to rule out coefficient-only repairs. | Keeps the local-label mismatch. |

My R1 recommendation is to synthesize around Candidate A as the default
mathematical contract, keep Candidate B as the simplest deterministic fallback,
and compare Candidate C only if the project is willing to introduce an explicit
episode-planning state. Candidate D should be rejected because it does not solve
the event-time/censoring mismatch from the formal problem.
