# M3 Formal Problem Statement

Status: `2026-06-05` problem definition for model-selection research.

Parent: [M3 Optimal-Stopping Model Selection](README.md).

## Abstract Problem

We study a finite-horizon, partially observed, one-shot timing problem with
post-event censoring.

Let:

```text
T              finite horizon
X_t            latent Markov state
O_t            observation emitted to the learner
H_t            learner history, H_t = (O_1, A_1, ..., O_t)
M_t in {0,1}   legality or feasibility mask for taking the one-shot event
Q_t in {0,1}   desirable timing window label, possibly latent or delayed
A_t in {0,1}   event action: 0=wait, 1=take event
C_t in {0,1}   censored regime indicator after the first event
```

The policy may take the event at most once:

```text
tau = inf { t : A_t = 1 and M_t = 1 }
```

After `tau`, the process enters a censored regime:

```text
C_t = 1 for t > tau
```

In this regime, future observations may still exist, but they no longer have
the same action mask, label semantics, or counterfactual meaning as the
pre-event sequence. This is the structural mismatch that makes the task harder
than ordinary per-step binary classification.

## Desired Decision Rule

The learned decision rule should satisfy:

```text
P(tau < first_desirable_time) is small
P(tau in desirable_window) is large
P(tau = infinity) is small when a desirable window exists
P(multiple events) = 0 by construction or contract
A_t = 1 is impossible or ignored when M_t = 0
```

Equivalently, we want a calibrated stopping-time policy:

```text
pi(tau | H_1:T, M_1:T)
```

or an online hazard representation whose cumulative mass is controlled:

```text
lambda_t = P(tau = t | tau >= t, H_t, M_t)
S_t = product_{k < t} (1 - lambda_k)
P(tau = t) = S_t lambda_t
```

The central issue is that choosing `lambda_t` independently per step can make
small local probabilities dangerous over many prewindow steps, while a large
local probability causes early censoring.

## Observed Failure Mode

The current empirical failure can be represented without domain terms:

```text
low startup hazard:
  lambda_t around 0.003
  deterministic argmax never crosses the event threshold
  stochastic events occur only by cumulative chance

relaxed startup hazard:
  lambda_t around 0.112
  stochastic event is almost certain before the desirable window
  later desirable labels are censored by the policy's own early event

on-policy training:
  early stochastic event changes the remaining trajectory
  rollout-local label construction loses or weakens later desirable evidence
  active training rows disappear late in training
```

This is not merely a missing feature or a weak coefficient. It is a mismatch
between:

```text
the target object: an episode-level stopping-time decision
the training object: local per-step action probabilities from censored rollouts
```

## Model-Selection Criteria

Candidate models should be compared by these criteria:

| Criterion | Required question |
| --- | --- |
| Identifiability | Can the model learn the desired timing rule from on-policy censored data, or does it require counterfactual/replay/off-policy labels? |
| Deterministic decision boundary | Does the model provide a calibrated deterministic choice, not only stochastic chance firing? |
| Early cumulative hazard control | Can it bound `P(tau < desirable_window)` over many wait steps rather than only bounding each step independently? |
| Desirable-window mass allocation | Can it move probability mass into the desirable window without raising all open-window hazards together? |
| Legality masking | Can hard masks remain authoritative without teaching on closed-mask rows as if they were executable actions? |
| Memory requirement | Does it require full sequence memory, a small carried state, or only local observations? |
| Objective compatibility | Does the loss align with event-time density, survival likelihood, ranking, advantage, or supervised labels? |
| Implementation risk | Can it be implemented as a bounded training contract without broad runtime or physics changes? |

## Candidate Model Families

M3 research should compare at least:

- survival / hazard models with explicit event-time likelihood;
- constrained optimal stopping or American-option-style stopping policies;
- sequence models that output a stopping distribution or calibrated hazard;
- offline or counterfactual label models that train from non-censored hold
  trajectories;
- ranking or ordinal timing models that compare prewindow and desirable-window
  states;
- hierarchical policies that separate "episode intent" from "step execution";
- rejection cases such as naive per-step Bernoulli classification or pure
  coefficient tuning.

## Deliverable Shape

Each research packet should include:

- the model class or algorithm family;
- its objective in equations or precise pseudo-code;
- assumptions about data and observability;
- how it handles censoring and one-shot constraints;
- how it prevents early cumulative hazard;
- how deterministic deployment is chosen;
- expected failure modes;
- whether it should be recommended, kept as fallback, or rejected for M3.
