# M3-S1 Policy Head Boundary Contract

Status: `2026-06-05` pass; P3 contract selects Scheme B, an independent
survival/stopping head as the long-term model object. Implementation is now
tracked by the P4 dispatch queue.

Parent: [M3-S1 Censored Optimal-Stopping Timing Contract](README.md).

Inputs:

- [P1 Data/Censoring Contract](m3_s1_data_censoring_contract_20260605.md)
- [P2 Grouped Stopping Objective Contract](m3_s1_grouped_stopping_objective_contract_20260605.md)
- [Architecture Boundary Map](m3_s1_model_architecture_boundary_map_20260605.md)

## Decision

M3-S1 selects Scheme B:

```text
policy trunk
  -> ordinary hybrid action branch
  -> independent survival/stopping-time branch
  -> value branch
  -> optional A7 credit/diagnostic branch
```

The stopping branch is the normative model for one-shot timing. Existing
executable fire logits are not the stopping model. They are part of the action
execution branch and may receive an adapter signal only after the stopping
branch has made a legal stop decision.

Rejected as the long-term mainline:

- using `fire_logit - hold_logit` as the primary stop score;
- making A7 `Q_fire_once - Q_hold` the sole teacher for event logits;
- treating executable action logits as both action distribution and
  event-time density;
- adding a generic sequence model without this stopping-head contract.

## Head Definition

For each row `t`, the policy exposes a stopping score:

```text
z_t = h_stop(H_t)
```

where `H_t` is the policy representation for the current observation or the
future sequence representation selected by M2. In the first M3-S1 implementation
slice, `H_t` may be the current HMoE actor latent. The long-term contract does
not require M2, but it must not prevent M2 from replacing the representation
later.

Legal masking is external to the raw head:

```text
lambda_t = M_t * sigmoid(z_t)
```

where `M_t` is the executable legal stop/fire mask from observation and C2/ROE
state. The head may learn that a state is good or bad, but only the mask decides
whether a stop is executable.

## Deterministic Boundary

Deployment rule:

```text
stop iff M_t = 1 and z_t >= theta_stop
```

`theta_stop` is a configured or calibrated threshold. The grouped objective
calibrates event-time mass; deterministic probes judge whether the boundary
crosses inside desirable windows.

The action branch receives the stop decision through an explicit adapter:

```text
if stop:
  request fire_once through the existing hybrid action transport
else:
  keep fire_once off
```

The adapter is not allowed to bypass C2/ROE. Rejected or closed-mask stops
remain non-executable and should be counted in diagnostics.

## Relationship To Existing Event Logits

The current hybrid event logits remain action-distribution parameters.

Allowed:

- expose `event_logit_delta` as a diagnostic;
- optionally distill the stopping-head decision into executable fire logits on
  legal-open rows after grouped loss is established;
- use event logits for policy log-prob only within the hybrid action branch.

Not allowed:

- use `event_logit_delta` as the M3-S1 primary stop score;
- compute survival/event-time likelihood directly from executable action logits;
- train executable fire logits from closed-mask or unobserved censored suffix
  rows;
- claim deterministic stopping success from stochastic fire samples.

## Relationship To A7 Credit

A7 credit can remain as support:

```text
A7 credit head: Q_hold, Q_fire_once
M3-S1 stopping head: z_t, lambda_t, p(tau=t)
```

A7 credit may diagnose whether stop/fire appears locally better than hold, but
M3-S1 acceptance is based on grouped survival/stopping behavior. A7 credit is
not the authoritative event-time model.

## P4 Implementation Boundary

The minimal implementation should add a distinct stopping-head path, not reuse
the hybrid event head as the head body.

Likely write surfaces:

- `python/rl/policy_algo/policies.py`
  - add an optional `hybrid_stopping_head` or `m3_stopping_head`;
  - expose `stopping_logit` / `stopping_hazard_logit` through policy or
    distribution helper methods;
  - keep event logits and stopping logits separate in stats.
- `python/rl/policy_algo/ppo_adaptive_kl.py`
  - call the stopping-head getter from the grouped auxiliary pass selected by
    P2;
  - do not route the grouped loss through ordinary shuffled PPO minibatches.
- `python/rl/policy_algo/first_event_*`
  - carry grouped evidence and compute survival/stopping terms.
- focused tests under `tests/hmoe/**` and `tests/training/**`
  - prove the new head is separate from event logits;
  - prove masks remain authoritative;
  - prove closed-mask rows do not update executable fire logits.

No P4 implementation may modify reward magnitude, weaken C2/ROE gates, or make
M2 a dependency.

## Required Diagnostics

P4/P5 must log independent stopping-head metrics:

- `m3s1/stop_logit_mean`;
- `m3s1/stop_logit_desirable_mean`;
- `m3s1/stop_logit_prewindow_mean`;
- `m3s1/hazard_desirable_mass`;
- `m3s1/hazard_early_mass`;
- `m3s1/no_event_mass`;
- `m3s1/boundary_cross_count`;
- `m3s1/boundary_cross_in_window_count`;
- `m3s1/closed_mask_stop_attempt_count`;
- `m3s1/event_logit_delta_diagnostic_mean`.

The diagnostic names may be adjusted during implementation, but the categories
must remain separate.

## Acceptance Gate For P3

P3 is accepted because it:

- selects an independent stopping/survival head as the long-term model object;
- rejects action-logit reuse as the primary stopping score;
- defines deterministic deployment by a legal masked stop boundary;
- preserves the action branch as an execution adapter;
- keeps A7 credit as diagnostic/support only;
- names P4 write surfaces and forbidden couplings without opening code.

## Next Step

`M3S1-P4 Minimal Integration` has passed. The next phase is P5 diagnostics and
short training; it must report boundary crossing, early mass, no-event mass,
closed-mask stop attempts, and one-shot legality before any learned-policy
success claim.
