# A7 Value/Policy Coupling Audit

Status: `2026-06-04` pass; breakpoint verified, A7 still held.

Parent: [README.md](README.md).

## Purpose

This slice verified the suspected post-S breakpoint:

```text
LEGAL_OPEN_QUALITY positive labels and explicit state are present,
but the learned model still reports negative Q_fire_once - Q_hold.
```

The audit asks whether that failure is inside the label/value object itself, or
later in the online PPO/shared-representation/delta-alignment coupling path.

## Diagnostic

Added:

- `tools/diagnostics/event_credit_head_probe.py --mode offline_fit`

The probe:

1. loads the S final model;
2. collects a fixed deterministic rollout batch with the same policy-observation
   fire-mask and launch-window label path used by PPO rollout collection;
3. rebuilds A7 first-event labels from that fixed batch;
4. freezes all policy parameters except selected diagnostic scopes;
5. fits only the A7 supervised credit objective;
6. reports advantage signs by source before and after fitting.

Main fixed batch:

```bash
python tools/diagnostics/event_credit_head_probe.py --mode offline_fit \
  --episodes 4 \
  --max_steps 640 \
  --fit_steps 1200 \
  --fit_batch_size 512 \
  --eval_batch_size 512 \
  --scopes credit_head,credit_head_actor_mlp \
  --json_out experiments_tmp/a7_credit_head_offline_fit_probe_20260604.json
```

Budget controls:

```bash
python tools/diagnostics/event_credit_head_probe.py --mode offline_fit \
  --episodes 4 \
  --max_steps 640 \
  --fit_steps 256 \
  --fit_batch_size 512 \
  --eval_batch_size 512 \
  --fit_lr 0.00018 \
  --scopes credit_head \
  --json_out experiments_tmp/a7_credit_head_offline_fit_training_budget_probe_20260604.json
```

```bash
python tools/diagnostics/event_credit_head_probe.py --mode offline_fit \
  --episodes 4 \
  --max_steps 640 \
  --fit_steps 256 \
  --fit_batch_size 512 \
  --eval_batch_size 512 \
  --fit_lr 0.000072 \
  --scopes credit_head \
  --json_out experiments_tmp/a7_credit_head_offline_fit_valuecoef_budget_probe_20260604.json
```

## Results

The fixed batch is not source-starved:

| Metric | Value |
| --- | ---: |
| rollout steps | `2560` |
| fire-open steps | `2516` |
| launch-open steps | `1356` |
| accepted releases | `0` |
| active A7 labels | `2516` |
| pre-window negatives | `1160` |
| `LEGAL_OPEN_QUALITY` positives | `1356` |

Initial S model signs on this same batch:

| Subset | Advantage mean | Positive sign frac |
| --- | ---: | ---: |
| all active labels | `-0.8553` | `0.000` |
| pre-window negatives | `-0.8573` | `0.000` |
| `LEGAL_OPEN_QUALITY` positives | `-0.8536` | `0.000` |

Offline supervised fits:

| Fit scope / budget | Legal-open advantage mean | Legal-open positive sign frac | Pre-window advantage mean | Pre-window negative sign frac |
| --- | ---: | ---: | ---: | ---: |
| credit head only, `1200` steps, lr `1e-3` | `+0.6417` | `1.000` | `-0.9382` | `0.734` |
| credit head + actor MLP, `1200` steps, lr `1e-3` | `+4.2450` | `0.976` | `-11.7457` | `0.983` |
| credit head only, `256` steps, lr `1.8e-4` | `+0.0292` | `1.000` | `-0.0329` | `0.592` |
| credit head only, `256` steps, lr `7.2e-5` | `+0.0083` | `1.000` | `-0.0142` | `0.685` |

## Interpretation

The breakpoint is real, but it is not inside the immediate label/value object:

- `LEGAL_OPEN_QUALITY` positives exist in a fixed deterministic rollout batch.
- The S final model starts with the same negative legal-open advantage observed
  in learned probes.
- Freezing the entire policy except `hybrid_event_credit_head` is sufficient to
  flip all legal-open positive rows to positive advantage on the same latent
  representation.
- Even a conservative value-coef-adjusted budget flips legal-open rows above
  zero in isolation.

Therefore the current failure is downstream of label construction and downstream
of basic credit-head/latent separability. The likely failing region is the
online joint-training coupling path: PPO/shared updates, non-stationary rollout
distribution, loss scaling through the combined objective, or delta/event-head
distillation can keep the learned policy checkpoint at a negative advantage
even though the supervised credit target is locally fit-able.

This also narrows the M2 question. A true memory mechanism may still be useful
long term, but the S/T evidence shows that the current batch already contains
explicit state and a separable credit signal. Releasing M2 now would skip over a
confirmed online-coupling fault.

## Next Step

Do not start another blind coefficient run. The next bounded work should inspect
the online update path directly:

- log per-loss gradient norms into `hybrid_event_credit_head`;
- compare credit-head parameter drift before and after each PPO train phase;
- isolate a train variant where only the A7 credit head updates for one rollout
  while PPO/shared/event-head updates are frozen;
- then decide whether the fix is a scheduling change, an optimizer/loss-scale
  contract, or a deeper policy/value coupling redesign.

## Validation

```bash
python -m compileall -q tools/diagnostics/event_credit_head_probe.py tools/diagnostics/event_credit_head/offline_fit.py
```

Observed: pass.

Experiment outputs are retained under `experiments_tmp/` and must not be
staged.
