# A7 Online Update-Path Isolation

Status: `2026-06-04` pass; online blocker localized, A7 remains held.

Parent: [README.md](README.md).

## Purpose

`A7-EVC-T` proved that the S final-model fixed batch is not missing state,
positive labels, or credit-head capacity: `LEGAL_OPEN_QUALITY` rows can be fit
to positive advantage by updating the credit head alone. This slice isolates why
that same locally fit-able signal does not survive online PPO training.

The suspected mechanisms were:

- PPO/shared updates interfering with A7 credit learning;
- loss scaling and global gradient clipping starving the credit head;
- delta alignment dragging event logits in the wrong direction;
- stochastic rollout distribution removing legal-open positives;
- HMoE routing/capacity as a deeper blocker.

## Diagnostic

Added:

- `tools/diagnostics/a7_online_update_path_probe.py`

The probe records two separate contexts:

1. a deterministic fixed S batch, matching the T breakpoint and preserving
   legal-open positives;
2. a stochastic online rollout batch with PPO-style GAE/returns, actions, old
   log-probs, A7 labels, and PPO/A7 gradient comparisons.

Main command:

```bash
python tools/diagnostics/a7_online_update_path_probe.py \
  --episodes 4 \
  --max_steps 640 \
  --online_episodes 4 \
  --online_max_steps 640 \
  --batch_size 512 \
  --eval_batch_size 512 \
  --update_steps 8 \
  --device auto \
  --json_out experiments_tmp/a7_online_update_path_probe_20260604.json
```

Credit-head-only 8-step control:

```bash
python tools/diagnostics/a7_credit_head_offline_fit_probe.py \
  --episodes 4 \
  --max_steps 640 \
  --fit_steps 8 \
  --fit_batch_size 512 \
  --eval_batch_size 512 \
  --fit_lr 0.00018 \
  --scopes credit_head \
  --json_out experiments_tmp/a7_credit_head_only_8step_probe_20260604.json
```

Validation:

```bash
python -m compileall -q tools/diagnostics/a7_online_update_path_probe.py
```

Observed: pass.

Experiment outputs are retained under `experiments_tmp/` and must not be
staged.

## Fixed-Batch Results

The deterministic fixed batch still matches T:

| Metric | Value |
| --- | ---: |
| rollout steps | `2560` |
| fire-open steps | `2516` |
| launch-open steps | `1356` |
| active labels | `2516` |
| `PREWINDOW` negatives | `1160` |
| `LEGAL_OPEN_QUALITY` positives | `1356` |
| initial legal-open advantage | `-0.8536` |
| initial legal-open event-logit delta | `-1.0071` |
| initial legal-open event-fire probability | `0.2676` |
| initial legal-open deterministic fire fraction | `0.0` |

Selected 512-row minibatch gradient norms:

| Loss | Total norm | Clip scale | Credit head norm / effective | Event head norm / effective | Actor MLP norm / effective | Features norm / effective |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A7 value | `1.1515` | `0.4342` | `1.0942` / `0.4751` | `0.0000` / `0.0000` | `0.0831` / `0.0361` | `0.3491` / `0.1516` |
| A7 delta-align | `0.6747` | `0.7411` | `0.0000` / `0.0000` | `0.2984` / `0.2211` | `0.1255` / `0.0930` | `0.5109` / `0.3786` |
| A7 combined | `1.1992` | `0.4170` | `1.0942` / `0.4562` | `0.2984` / `0.1244` | `0.0631` / `0.0263` | `0.2417` / `0.1008` |

Gradient direction checks:

| Comparison | Group | Cosine |
| --- | --- | ---: |
| delta-align vs value | actor MLP | `-0.8954` |
| delta-align vs value | features | `-0.9097` |
| delta-align vs value | all available grads | `-0.2209` |
| combined vs value | actor MLP | `-0.4642` |
| combined vs value | features | `-0.4786` |
| combined vs value | all available grads | `0.8360` |

Interpretation:

- A7 value loss does not update the event head directly, but it does update the
  actor MLP and feature extractor. Those shared representation updates can
  change the event logits even without an explicit event-head gradient.
- Delta alignment does not update the credit head, confirming the intended
  `advantage.detach()` separation.
- Delta alignment and A7 value loss strongly disagree in actor/features. This
  is a representation-coupling fault, not merely a scalar-coefficient question.

Eight update steps on the fixed batch:

| Update path | Legal-open advantage before | Legal-open advantage after | Positive sign frac after | Legal-open event-logit delta after | Deterministic fire frac after |
| --- | ---: | ---: | ---: | ---: | ---: |
| credit head only | `-0.8536` | `-0.5095` | `0.0` | not changed by probe | not changed by probe |
| A7 value, normal online graph | `-0.8536` | `-0.0651` | `0.0` | `-2.6259` | `0.0` |
| A7 combined, normal online graph | `-0.8536` | `-0.2823` | `0.0` | `-0.3088` | `0.0` |

This confirms a subtle failure mode: allowing A7 value loss to backpropagate
through the actor representation can move the credit advantage faster than a
credit-head-only update, but it can also damage or destabilize the event-logit
surface. Delta alignment partially repairs the event-logit delta, but at the
cost of conflicting with the value gradient in shared representation space.

## Online PPO Results

The stochastic online rollout batch differs from the deterministic fixed batch:

| Metric | Value |
| --- | ---: |
| rollout steps | `2560` |
| fire-open steps | `19` |
| launch-open steps | `1356` |
| accepted events | `4` |
| accepted steps | `[6, 46, 9, 2]` |
| active labels | `1375` |
| positive labels | `1356` |
| `PREWINDOW` negatives | `15` |
| `EARLY_ACCEPTED` negatives | `4` |
| `SHADOW_QUALITY` positives | `1356` |

PPO/A7 gradient comparison on the online batch:

| Loss | Total norm | Clip scale | Credit head norm / effective | Event head norm / effective | Features norm / effective | Value-net norm / effective |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A7 combined alone | `5.0605` | `0.0988` | `4.9141` / `0.4855` | `0.5839` / `0.0577` | `0.8597` / `0.0849` | `0.0000` / `0.0000` |
| PPO alone | `356.3418` | `0.001403` | `0.0000` / `0.0000` | `0.0274` / `0.000038` | `142.4263` / `0.1998` | `314.2057` / `0.4409` |
| PPO + A7 | `356.4866` | `0.001403` | `4.9141` / `0.00689` | `0.6047` / `0.00085` | `142.7010` / `0.2001` | `314.2057` / `0.4407` |

The direct PPO gradient into `hybrid_event_credit_head` is zero. Therefore PPO
does not overwrite credit-head parameters directly. The blocker is that PPO's
value/feature/value-net gradients dominate the shared global gradient norm, so
the single PPO-style `clip_grad_norm_(self.policy.parameters(), 0.5)` reduces
the A7 credit-head effective gradient from about `0.4855` in A7-alone training
to about `0.00689` inside PPO+A7, a roughly 70x reduction for the head's clipped
update budget on this diagnostic batch.

Real S TensorBoard scalars are consistent with this:

| Scalar | Observation |
| --- | --- |
| `train/value_loss` | max `6526.7822`; final `0.2110` |
| `train/loss` | max `4348.9019`; final `0.4425` |
| `a7/event_credit_loss` | max `1.0749`; final `0.3186` |
| `a7/event_credit_advantage_mean` | starts around `-0.0442`, drifts to `-0.9239` |
| `a7/event_credit_target_positive_frac` | final `0.6445` |
| `a7/evc_src_legal_open_quality_positive_count_mean` | final `330.0` |

This means the online run is not merely "too short." It trains under a regime
where early/value-dominated PPO phases can establish a negative event-credit
surface, and later positive A7 windows do not have enough protected update
budget to reverse it.

## Suspect Assessment

| Suspect | U finding | Status |
| --- | --- | --- |
| Missing positive labels | fixed deterministic batch has `1356` legal-open positives; online stochastic batch has `1356` shadow positives | excluded as primary |
| Missing explicit state | T/S already exposed v2 state; U still reproduces fixed-batch separability | excluded as primary |
| Credit-head capacity | T fits the fixed batch; U confirms nonzero credit-head gradients | excluded as primary |
| Direct PPO overwrite of credit head | PPO-alone credit-head gradient is `0.0` | excluded |
| Loss scaling / global clipping | PPO+A7 clip scale is about `0.0014`; credit-head effective norm drops to `0.00689` | confirmed primary |
| Shared actor/feature drift | A7 value gradients enter actor/features and can worsen event-logit delta | confirmed primary |
| Delta-align dragging policy | delta-align does not touch credit head, but fights value loss in actor/features | confirmed contributing |
| Rollout non-stationarity | deterministic legal-open rows and stochastic shadow rows differ sharply | confirmed contributing |
| HMoE hierarchy gap | HMoE receives small gradients, but U localizes failure before a hierarchy-attributable gate | watch item, not current primary |

## Conclusion

The structural failure is an online update-contract bug:

```text
A7 credit is implemented as an auxiliary loss inside the same PPO backward,
global clip, shared actor representation, and optimizer step.

That makes a locally separable event-credit target compete with PPO value loss
and event-logit distillation for the same representation and gradient budget.
```

Therefore the next fix should not be another coefficient-only train. The next
bounded contract should decouple A7 credit learning from the shared PPO update:

- make the A7 value update credit-head-only, or give it a separate credit
  encoder/critic lane with detached actor features;
- use a separate optimizer step and separate gradient clipping budget for A7
  credit instead of the PPO global clip;
- make delta alignment a second-stage or gated update after credit signs are
  reliable, and restrict its write surface so it does not fight A7 value in the
  shared actor representation;
- preserve A3/A5 masks and one-shot event authority.

M2 and HMoE redesign remain held. U narrows the immediate root cause to the
A7/PPO update contract rather than memory, labels, state, or credit-head
capacity.
