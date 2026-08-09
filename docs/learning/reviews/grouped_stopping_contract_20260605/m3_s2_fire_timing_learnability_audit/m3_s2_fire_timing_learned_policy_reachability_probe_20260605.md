# M3-S2 Learned-Policy Reachability Probe

Parent: [README.md](README.md).

Status: `2026-06-05` evidence update; records why the learned policies still
select no-fire after the oracle sweep proved reachable winning shots.

## Question

The full delay sweep proves that the environment/reward surface contains legal
release times that can produce effects, damage, and terminal combat wins. The
remaining question is therefore not whether firing is physically reachable, but
whether the learned policy can express a supported `fire_once` event through the
hybrid action contract.

The executable chain is:

```text
observation/history
  -> actor event logits: [hold, fire_once]
  -> deterministic categorical mode or stochastic sample
  -> action[9] > 0.5
  -> C2/ROE fire_mask gate
  -> missile release
```

Code evidence:

- `python/rl/policy_algo/policies.py`: `air_combat_hybrid_v1` uses action index
  `9` as the event action; deterministic mode takes `argmax([hold, fire])`,
  while stochastic mode samples a categorical event.
- `gym_envs/universal_env_parts/air_combat_event_action.py`: the runtime accepts
  `fire_once` only when `action[9] > 0.5` and `fire_mask` is open, then records
  one accepted event and suppresses further first-shot releases while pending
  assessment is active.
- `python/rl/policy_algo/m3s1_grouped_stopping.py`: the M3 stopping head is an
  auxiliary hazard/loss head; the probed policies do not automatically convert
  that head into the executable `fire_once` action.

## Probe Artifacts

M3-S1 state-completed 8k model:

```text
experiments_tmp/m3s1_p5_state_completed_8k_20260605_r1/final_model.zip
experiments_tmp/m3s1_p5_state_completed_8k_20260605_r1/m3s1_deterministic_probe.json
experiments_tmp/m3s1_p5_state_completed_8k_20260605_r1/m3s1_stochastic_probe.json
experiments_tmp/m3s1_p5_state_completed_8k_model_probe_deterministic_20260605.json
experiments_tmp/m3s1_p5_state_completed_8k_model_probe_stochastic_20260605.json
```

A7 conservative safe-bias 8k model:

```text
experiments_tmp/a7_event_policy_margin_safe_bias_8k_20260605_r1/final_model.zip
experiments_tmp/a7_event_policy_margin_safe_bias_8k_20260605_r1/deterministic_probe.json
experiments_tmp/a7_event_policy_margin_safe_bias_8k_20260605_r1/stochastic_probe.json
experiments_tmp/a7_event_policy_margin_safe_bias_8k_model_probe_deterministic_matched_20260605.json
experiments_tmp/a7_event_policy_margin_safe_bias_8k_model_probe_stochastic_matched_20260605.json
```

Direct model-attribute check confirms that the trained objects preserve the
configured A7/M3 knobs:

| Model | `a7_event_policy_margin_coef` | `a7_event_policy_projection_margin_coef` | `m3s1_grouped_stopping_coef` | Event head | Credit head | M3 head |
| --- | ---: | ---: | ---: | --- | --- | --- |
| M3-S1 state-completed 8k | `0.35` | `0.15` | `1.0` | yes | yes | yes |
| A7 safe-bias 8k | `0.35` | `0.15` | `0.0` | yes | yes | no |

## Learned-Policy Results

Deterministic probes:

| Model | Episodes | Accepted releases | Open-mask steps | Mean fire probability | Max fire probability | Event-mode fire count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M3-S1 state-completed 8k | `2` | `0` | `1880`, `1840` | `0.00354`, `0.00345` | `0.00384`, `0.00377` | `0`, `0` |
| A7 safe-bias 8k | `2` | `0` | `639`, `599` | `0.00309`, `0.00288` | `0.00314`, `0.00308` | `0`, `0` |

The mask is open for hundreds to thousands of steps, but deterministic
categorical mode always selects `hold`.

Stochastic probes:

| Model | Episodes | Accepted releases | Release steps | Interpretation |
| --- | ---: | ---: | --- | --- |
| M3-S1 state-completed 8k | `4` | `3` | `[154]`, `[57]`, `[]`, `[451]` | Random low-probability samples, not deterministic timing. |
| A7 safe-bias 8k | `4` | `3` | `[84]`, `[407]`, `[]`, `[18]` | Random low-probability samples, often prewindow. |

Stochastic releases prove the runtime path is executable when the sample happens
to choose `fire_once`. They do not prove the learned deterministic policy has
learned a stopping boundary.

## Credit/Action Split

The probes expose a split between value support and executable action:

| Model/probe | Prewindow event fire probability | Quality-window event fire probability | Prewindow credit advantage | Quality-window credit advantage |
| --- | ---: | ---: | ---: | ---: |
| M3-S1 deterministic | `0.003776` | `0.003763` | `0.8122` | `0.8116` |
| A7 safe-bias deterministic ep0 | `0.003098` | `0.003100` | `0.8103` | `0.8109` |
| A7 safe-bias deterministic ep1 | `0.003078` | `0.003078` | `0.8031` | `0.8042` |

The credit head can assign positive `fire_once - hold` advantage, but the actor
event logit delta remains about `-5.6` to `-5.8`, leaving fire probability near
`0.3%`. That is far below the deterministic `argmax` boundary.

The M3 stopping head does not currently solve this execution step. In the
state-completed deterministic probe it reports `stop_prob = 0.5` and boundary
crossing on every step, while the executable event action remains `hold` and no
missile is released.

## Mechanistic Cause

The low `fire_once` probability is only the observed symptom. The causal chain
identified by the A7 follow-on probes is:

```text
episode-level first-event label
  -> rollout-local / stochastic on-policy support
  -> A7 credit head
  -> detached, tiny Q_fire_once - Q_hold target
  -> event-logit delta
  -> deterministic categorical argmax
```

This chain fails in two places.

First, the label function is episode-level while PPO trains on rollout chunks.
Before the cross-rollout repair, an early stochastic release before the quality
window put the environment into `FiredAssess`; the later quality-window
shadow-positive labels existed on the full episode but were lost when the
episode was split into rollout-local chunks. That explains the observed collapse
of active A7 labels to zero in the earlier training logs.

Second, after that label-support issue was repaired, the remaining policy
contract was still too weak. A7 trains a credit head and then optionally aligns
event-logit delta to the detached credit advantage:

```text
target_delta = stop_gradient(Q_fire_once - Q_hold)
```

In the fixed-batch post-repair probe, this advantage was approximately `0.004`
on both prewindow and quality rows. That is not a calibrated signed decision
target. Aligning event logits to it pulls both regions toward the threshold
instead of teaching "hold before quality, fire in quality". With
`a7_event_credit_delta_align_positive_only=true`, negative-label pressure is
also removed once the credit head goes negative, so ordinary prewindow rows do
not reliably push the event logits below zero.

The offline event-logit probe rules out basic model capacity as the primary
cause. Training only the event head with direct labels remained weak, but
training `hybrid_event_head` plus `mlp_extractor.policy_net` with direct signed
labels separated the windows: quality rows moved to high fire probability and
prewindow rows moved strongly negative. Therefore the actual root cause is the
training contract between labels, credit, actor representation, and executable
event logits, not the existence of an optimal shot or the C2/ROE mask.

## Diagnosis

The current no-fire problem is now narrowed to the learned event/action layer:

- not C2/ROE reachability: the mask is open and oracle/stochastic paths release;
- not physical kill reachability: the full oracle sweep finds effects and
  terminal wins;
- not a pure missing-credit-head issue: credit advantage can be positive in
  probe rows, but it is uncalibrated and does not supply a signed timing
  discriminator to the actor;
- not solved by the M3 stopping head: that head is diagnostic/auxiliary unless
  explicitly adapted into the event action;
- the executable actor event logits remain on the `hold` side because the
  actor/event path is not trained with a strong signed timing target.

This is an event-head-to-executable-event training-contract failure. Earlier A7
short evidence already showed the two bad extremes:

- relaxing the startup prior raises fire probability everywhere and causes early
  stochastic releases before quality labels can be maintained;
- restoring the conservative prior keeps one-shot discipline but leaves event
  logits too negative for deterministic release.

## Consequence

The next model change should not be another coefficient sweep. The maintained
contract must explicitly bridge one of these paths:

1. stop/event head to executable one-step pulse under `fire_mask`;
2. direct actor event-logit target with maintained legal-open positive support;
3. reward contract repair so terminal timing is not ordered toward late wins.

M2 memory remains a representation candidate, but this probe shows that memory
alone does not address the current actuator boundary unless its stopping output
is wired into an executable pulse.
