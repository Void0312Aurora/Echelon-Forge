# A6 Event-Head Update-Strength Audit

Status: `2026-06-03` `A6-EVT-J` pass as an update-strength audit. A6
remains held because the audit explains the deterministic blocker but does not
itself produce an accepted learned policy.

Parent: [README.md](README.md). Cluster plan:
[a6_event_value_first_event_timing_task_clusters_20260603.md](a6_event_value_first_event_timing_task_clusters_20260603.md).

## Question

The deadline-bootstrap run connected sustained positive labels to the existing
`hold/fire_once` event logit delta, but deterministic probing still produced
`0` requests. The open-window event probability moved only from about `0.247%`
to about `0.494%`.

This audit asks whether the A6 labels are disconnected, or whether the labels
are connected but too weak under the current optimizer/head scaling.

## Evidence

Existing deadline run scalars:

| Signal | Observation | Interpretation |
| --- | --- | --- |
| A6 labels | `a6/active_count_mean` is present, first `237.5`, last `386.0`. | Deadline labels reached PPO minibatches. |
| Positive source | `a6/deadline_weight=1.0`, `a6/target_positive_frac` reaches `1.0`. | Late open-window labels are sustained positives. |
| Loss | `a6/hazard_loss` remains nonzero, first `1.4603`, last `1.5972`. | A6 loss is live rather than inactive. |
| Learning rate | `train/learning_rate=3e-5`, `train/kl_lr_mult=1.0` throughout. | KL control does not amplify the update. |
| KL | `train/approx_kl` stays low: min about `0.00015`, max about `0.00169`. | The run is conservative; it is not blocked by high KL early stop. |
| Event delta callback | open-window delta moved from `-5.9625` at `10240` to `-5.3986` at `30720`. | The event head moves, but remains far below deterministic argmax. |
| Final probe | open-window delta around `-5.306`, probability max about `0.496%`, `0` deterministic requests. | The learned policy remains held. |

Focused probes:

| Probe | Result | Meaning |
| --- | --- | --- |
| Bias-only Adam, `128` steps, `lr=3e-5` | event delta moves only `+0.00769`. | A standalone event bias cannot cross a `-5` margin at current short-train scale. |
| Bias-only Adam, `128` steps, `lr=3e-4` | event delta moves `+0.07679`. | Step size, not active-count volume, is the controlling factor for this simple case. |
| HMoE policy, first-shot route, first gradient | shared action head gradient is nonzero; HMoE gradient is nonzero; optimizer groups are `shared=3e-5`, `hmoe=1.05e-5`. | The A6 loss is routed to both shared and routed heads. |
| HMoE policy, `32` hazard-only steps, current `lr=3e-5` | event delta moves about `+0.046` to `+0.050`. | Current LR can move the high-dimensional head, but slowly. |
| HMoE policy, `128` hazard-only steps, current `lr=3e-5` | event delta moves about `+0.254`. | This is still far from the roughly `+5.3` needed to cross deterministic argmax from the final probe. |
| HMoE policy, `32` hazard-only steps, `lr=3e-4` | event delta moves about `+0.61` to `+0.67`. | A dedicated stronger event-head update lane is a credible next slice. |

New regression/diagnostic test:

```bash
.venv/bin/python -m pytest -q tests/policy/test_event_head_update_contracts.py
```

Result: `2 passed`.

## Diagnosis

The blocker is not a dead label path. The deadline labels, A6 hazard loss,
event logit delta accessor, first-shot route, shared action head gradients, and
HMoE residual gradients are all live.

The blocker is update strength and optimization ownership. Deterministic
`fire_once` requires the masked event delta `fire - hold` to become positive.
The deadline run ends near `-5.3`, so the policy needs a logit displacement of
roughly `+5.3` before deterministic argmax can switch from `hold` to
`fire_once`. The current `32768`-step probe produces only a fraction of that
movement.

Important mechanisms:

- A6 hazard loss averages over active labels. More deadline-positive samples
  improve state coverage, but they do not by themselves multiply the total
  gradient scale once a minibatch has enough active labels.
- With Adam, simply increasing the scalar hazard coefficient is not guaranteed
  to multiply the effective bias update; the step is mainly governed by the
  optimizer learning rate and competing gradients/clipping.
- The HMoE residual path receives gradients, but its effective correction is
  damped by residual scale/warmup and `hmoe_head_lr_scale=0.35`. At startup the
  route-specific residual is especially weak; even at full gate it is still a
  low-scale residual on top of the shared action head.
- The event logits are still ordinary rows inside the shared action head plus a
  low-scale routed residual. There is no dedicated event-logit optimizer lane or
  event-value calibration surface.

## Recommendation

Do not accept A6 and do not release M2 from this audit. The correct next bounded
implementation slice is an event-head optimization lane before any sequence
native release vote.

Proposed next cluster:

`A6-EVT-K Event-Head Optimization Lane`

Goal:

- Give the `hold/fire_once` event rows a bounded, observable update path strong
  enough to test deterministic crossing without weakening A3/A5 masks.

Candidate implementation options, in priority order:

1. Add a dedicated optimizer group for event-logit parameters/rows, covering the
   shared fire binary row and the separate hold logit row, with an explicit
   event-head LR multiplier and diagnostics.
2. Add a matching routed-residual event-row lane or temporarily raise the HMoE
   event-row LR/scale only for the combat first-shot route.
3. Keep the deadline/hazard labels, but add diagnostics for event-row gradient
   norm, event-row LR, event delta before/after train updates, and deterministic
   crossing margin.
4. If event-head optimization moves delta strongly but still cannot learn a
   stable first-shot policy, then escalate to an event-value/advantage head.

Acceptance boundary for the next slice:

- A3/A5 legality must remain mask/state-machine owned.
- No reward-only legality penalty path should be restored as the main fix.
- M2, `2v2`, self-play, missile physics, Pk, fuze, and damage authority remain
  held.
- A short learned probe must compare deterministic event probability, event
  mode, request/accept/release counts, rejected reasons, and violation counts.

## Worker Packet

```md
status: pass
touched files:
- tests/policy/test_event_head_update_contracts.py
- docs/task/air_combat/a6_event_value_first_event_timing/a6_event_value_first_event_timing_event_head_update_audit_20260603.md
- docs/task/air_combat/a6_event_value_first_event_timing/a6_event_value_first_event_timing_event_head_update_audit_20260603.zh.md
- docs/task/air_combat/a6_event_value_first_event_timing/README.md
- docs/task/air_combat/a6_event_value_first_event_timing/README.zh.md
- docs/task/air_combat/a6_event_value_first_event_timing/a6_event_value_first_event_timing_current_status_20260603.md
- docs/task/air_combat/a6_event_value_first_event_timing/a6_event_value_first_event_timing_current_status_20260603.zh.md
- docs/task/air_combat/a6_event_value_first_event_timing/a6_event_value_first_event_timing_task_clusters_20260603.md
- docs/task/air_combat/a6_event_value_first_event_timing/a6_event_value_first_event_timing_task_clusters_20260603.zh.md
- docs/task/air_combat/a6_event_value_first_event_timing/a6_event_value_first_event_timing_dispatch_queue_20260603.md
- docs/task/air_combat/a6_event_value_first_event_timing/a6_event_value_first_event_timing_dispatch_queue_20260603.zh.md
- docs/task/air_combat/a6_event_value_first_event_timing/a6_event_value_first_event_timing_acceptance_20260603.md
- docs/task/air_combat/a6_event_value_first_event_timing/a6_event_value_first_event_timing_acceptance_20260603.zh.md
- docs/task/air_combat/README.md
- docs/task/air_combat/README.zh.md
commands/outcomes:
- .venv/bin/python -m pytest -q tests/policy/test_event_head_update_contracts.py -> 2 passed
- .venv/bin/python -m pytest -q tests/policy/test_event_head_update_contracts.py tests/policy/test_first_event_timing_contracts.py tests/policy/test_execution_policy_surface.py tests/policy/test_auxiliary_training_updates.py tests/training/test_event_timing_training_config_contracts.py tests/training/test_diagnostics_callback_contracts.py tests/runtime/air_combat/test_diagnostics_probe_contracts.py -> 73 passed, 9 subtests passed
- python -m compileall -q tests/policy/test_event_head_update_contracts.py -> passed
- git diff --check -- docs/task/air_combat tests/policy/test_event_head_update_contracts.py -> passed
remaining paths:
- Implement A6-EVT-K event-head optimization lane.
behavior risks:
- Higher event-head LR could overfire unless A3/A5 masks and rejected-reason diagnostics stay active.
integration notes:
- This audit is diagnostic evidence only; it is not learned-policy acceptance.
```
