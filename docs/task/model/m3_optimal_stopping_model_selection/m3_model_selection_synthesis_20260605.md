# M3 Model-Selection Synthesis

Status: `2026-06-05` synthesis complete; follow-on M3-S1 planning contract
opened, while implementation code remains held.

Parent: [M3 Optimal-Stopping Model Selection](README.md).

Inputs:

- [Formal problem statement](m3_formal_problem_statement_20260605.md)
- [Self-designed algorithm probe](m3_self_designed_algorithm_probe_20260605.md)
- [Academic literature model survey](m3_academic_literature_model_survey_20260605.md)
- [Existing model-family fit survey](m3_existing_model_family_fit_survey_20260605.md)

## Decision Summary

M3 should model the blocked first-event timing problem as a censored constrained
optimal-stopping problem, not as another local per-step action-probability
repair.

The recommended next contract is a two-layer model:

```text
data/censoring layer:
  collect or reconstruct wait-preserving timing evidence
  treat early-event suffixes as censored, not as ordinary negatives
  expose support diagnostics for candidate stopping rules

stopping model layer:
  train a legal masked stop-vs-continue boundary
  attach a survival/event-time head for calibrated tau mass
  constrain cumulative prewindow event mass
  deploy deterministically by a boundary or calibrated event-time threshold
```

This keeps the strongest parts of A7, but changes the target object from
"raise the fire probability on good rows" to "allocate one-shot stopping mass
over an episode/window while preserving a deterministic continuation boundary."

## Research Packet Agreement

| Evidence route | Primary recommendation | Key warning |
| --- | --- | --- |
| R1 self-designed algorithms | Masked survival with episode risk budget. | It needs uncensored or delayed-positive evidence; otherwise it only learns not to stop early. |
| R2 academic literature | Optimal stopping as conceptual core; DeepHit-style event-time distribution or survival head as calibrated support; counterfactual/off-policy correction for action-induced censoring. | Ordinary survival censoring assumptions are too weak when the policy itself censors the future. |
| R3 engineering fit | Episode survival-hazard head is the best near-term fit; direct stopping distribution and M2 sequence models are attractive but need grouped/sequence buffer contracts. | Current flattened PPO can silently collapse grouped losses back into per-step BCE. |

All three packets reject another coefficient sweep over startup fire bias or a
naive per-step Bernoulli event head as the default next step.

## Mathematical Contract

Let the legal one-shot stopping time be:

```text
tau = inf { t : A_t = 1 and M_t = 1 }
```

For a masked hazard head:

```text
lambda_t = M_t * sigmoid(g_theta(H_t))
S_t = product_{k < t} (1 - lambda_k)
p_theta(tau = t) = S_t * lambda_t
p_theta(no_event) = S_{T+1}
```

For a stop-vs-continue boundary:

```text
Delta_t = V_stop(H_t, M_t) - V_continue(H_t)
stop iff M_t = 1 and Delta_t >= delta
```

The synthesis recommends tying these together:

```text
Delta_t supplies the deterministic boundary
lambda_t / p(tau=t) supplies calibration and cumulative risk diagnostics
```

The core window loss should be grouped by episode/window, not flattened into
independent step labels:

```text
P_window = sum_{t in desirable_window} S_t lambda_t
P_early  = sum_{t before desirable_window} S_t lambda_t

L_window =
  - log(P_window + eps)
  + alpha * max(0, P_early - rho_early)^2
  + beta  * no_event_or_miss_penalty
  + gamma * ranking_or_margin_auxiliary
```

For episodes with no desirable window:

```text
L_none = -log(p_theta(no_event) + eps)
```

For early-event censored prefixes:

```text
L_censored_prefix =
  - log(S_tau + eps)
  + alpha * max(0, P(tau_before_observed_early_event) - rho_prefix)^2
```

Post-event rows should not train executable event logits as ordinary negatives.
They may remain diagnostic, value-only, projected, or counterfactual evidence
depending on the data contract.

## Required Data Contract

The model cannot be selected honestly unless M3 also selects a data route.
The next implementation contract must provide at least one of:

| Data route | Use | Risk |
| --- | --- | --- |
| Wait-preserving hold rollouts | Reveal later desirable windows that early on-policy stopping would censor. | May drift from the deployed policy distribution. |
| Replay/counterfactual hold branches | Compare stop vs continue from the same prefix. | Requires simulator/tool support and strict ownership boundaries. |
| Low-hazard exploratory rollouts with censor-aware labels | Keep on-policy data closer while reducing early censoring. | May still produce too few positive windows. |
| Off-policy/censoring correction with support diagnostics | Estimate whether candidate stopping rules are supported by data. | High variance and assumption-heavy under partial observability. |

Recommended near-term data route:

```text
start with wait-preserving hold rollouts and reconstructed desirable windows
add support diagnostics before any on-policy learned-policy claim
```

This is the smallest route that directly attacks the observed A7 failure:
online early events censor later timing evidence.

## Recommended Next Contract

Open a bounded follow-on only if it is framed as a new M3 stopping contract, not
as A7 coefficient repair.

Suggested name:

```text
M3-S1 Censored Optimal-Stopping Timing Contract
```

Minimum implementation scope:

- add grouped episode/window loss support for first-event timing;
- add or reuse an event-time / survival head over legal windows;
- add deterministic stop-vs-continue boundary diagnostics;
- add cumulative prewindow mass diagnostics;
- add wait-preserving hold-trajectory data generation or reconstruction;
- keep A3/A5 legality masks authoritative;
- keep A7 credit/value heads as support diagnostics, not as the sole actor
  teacher.

Minimum acceptance probes:

- deterministic boundary crosses inside desirable windows on held-out
  wait-preserving trajectories;
- cumulative prewindow mass stays below a configured budget;
- stochastic one-shot legality remains clean;
- active grouped labels persist through late training;
- post-event rows do not train executable event logits as ordinary negatives;
- no learned-policy success is claimed until a real training run passes these
  gates.

## Fallbacks

`Fallback A`: Ordinal margin stopper.

Use when grouped event-time likelihood is too expensive. It should rank
prewindow legal states below desirable-window legal states and deploy by a
deterministic threshold. It is lower-risk but lacks native event-time mass.

`Fallback B`: Direct stopping-distribution head as offline probe.

Use when padded/complete windows are easy to collect outside PPO. It can test
whether a normalized `P(tau=t)` objective solves the timing discriminator
before opening a full online grouped-loss implementation.

`Fallback C`: M2 sequence model.

Keep as a long-term route. M2 is justified only if M3 shows grouped window
losses or direct stopping distributions cannot be implemented safely in the
current PPO buffer. A generic sequence model is not a cure unless it carries the
same stopping/censoring contract.

## Rejected Paths

Rejected as default next steps:

- another startup-bias relaxation;
- another local per-step BCE / Bernoulli head with coefficient tuning;
- credit-head-only value learning as the sole teacher for event logits;
- generic Transformer or recurrent policy release without an explicit
  stopping-time objective;
- treating closed-mask post-event shadow rows as executable negative or positive
  action labels.

These paths are rejected because they do not address the formal mismatch:

```text
target object: episode-level stopping time
bad training object: independent local action probabilities from censored data
```

## Status And Next Action

M3-P0 and M3-R1/R2/R3 are complete. M3-S1 planning is now open as the next
bounded contract, but implementation code remains held until the architecture
boundary, data/censoring contract, and grouped objective contract are explicit.

Immediate next action:

- complete `M3S1-P0 Boundary Map` review;
- draft `M3S1-P1 Data Censoring Contract` and diagnostics before any training
  loop change.
