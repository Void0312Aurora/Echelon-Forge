# M3-S2 Boundary Optimizer Contract Probe - 2026-06-06

Parent: [README.md](README.md).

Status: `direction repair evidence`; not behavioral acceptance.

## Question

The real update path probe showed that M3-S2 updates reached executable event
parameters but lowered both prewindow and quality-window logits. This probe asks
which part is broken:

- the absence of a direct quality-vs-prewindow discriminator;
- the absence of an absolute deterministic fire boundary target;
- or reuse of PPO Adam state during the auxiliary event-window update.

## Implementation

Code changes:

- `compute_m3s1_grouped_stopping_loss` now supports:
  - `window_contrastive_margin_coef` and `window_contrastive_margin`;
  - `window_quality_boundary_coef` and `window_quality_boundary_logit`.
- M3-S2 `AdaptiveKLPPO` wiring now logs:
  - `m3s2/q_pre_margin`;
  - `m3s2/q_pre_margin_loss`;
  - `m3s2/q_boundary_logit`;
  - `m3s2/q_boundary_loss`.
- M3-S2 can use `m3s2_event_window_dedicated_optimizer_enabled`, which builds an
  isolated auxiliary optimizer over the event-policy parameter subset instead of
  reusing PPO Adam state.
- `tools/diagnostics/m3s2_real_update_path_probe.py` now supports loss overrides
  and `--reset-optimizer-state` for controlled real-row update comparisons.

Active M3-S2 config now treats deterministic boundary formation as the main
contract:

```text
m3s2_event_window_quality_boundary_coef = 100.0
m3s2_event_window_quality_boundary_logit = 0.0
m3s2_event_window_contrastive_margin_coef = 2.0
m3s2_event_window_contrastive_margin = 2.0
m3s2_event_window_dedicated_optimizer_enabled = true
```

## Evidence

All probes used the same support-preserving checkpoint and forced-hold real row
collection:

```text
experiments_tmp/m3s2_support_preserve_8k_20260606_r2/final_model.zip
legal_rows = 1880
quality_rows = 1040
accepted_count = 0
```

| Probe artifact | Change | Optimizer state | Quality max delta | Loss delta | Verdict |
| --- | --- | --- | ---: | ---: | --- |
| `experiments_tmp/m3s2_real_update_path_probe_20260606_contrastive_4step.json` | contrastive added to active contract | reused | `-0.265431` | `-2.033103` | still lowers quality |
| `experiments_tmp/m3s2_real_update_path_probe_20260606_contrastive_window_only_4step.json` | early/deadline/delay off, contrastive only | reused | `-0.263480` | `-0.171080` | still lowers quality |
| `experiments_tmp/m3s2_real_update_path_probe_20260606_contrastive100_window_only_4step.json` | high contrastive only | reused | `-0.175797` | `-0.681381` | relative margin improves, absolute boundary still falls |
| `experiments_tmp/m3s2_real_update_path_probe_20260606_boundary100_window_only_4step.json` | high boundary anchor only | reused | `-0.052877` | `+5.247437` | update steps against the current loss |
| `experiments_tmp/m3s2_real_update_path_probe_20260606_boundary100_window_only_resetopt_4step.json` | high boundary anchor only | reset | `+0.313639` | `-31.054993` | real parameter path can raise quality |
| `experiments_tmp/m3s2_real_update_path_probe_20260606_final_config_dedicated_sim_4step.json` | final active config, dedicated optimizer simulated by reset | reset | `+0.313624` | `-28.099365` | update direction repaired |

The final probe still has `quality_boundary_count = 0`: four offline steps move
quality logits in the right direction but do not yet cross deterministic mode
from an initial quality max logit near `-5.72`.

## Decision

The failure was not one single missing label. It has two coupled mechanisms:

1. The grouped event-mass objective is a stochastic window-probability contract.
   On a long quality window, it can improve by lowering prewindow hazard and
   spreading small hazard across many quality rows. That is not equivalent to a
   deterministic `fire_once` boundary.
2. The M3-S2 auxiliary update reused PPO Adam state. In real-row probes, that
   stale state can step opposite the current boundary loss; resetting optimizer
   state changes the same boundary-only update from quality-down to quality-up.

Therefore the next M3-S2 slice should be evaluated as a deterministic boundary
contract with isolated auxiliary optimization. It should not be counted as
learned behavior until a training run and deterministic release probe show
nonzero legal releases.

## Validation

```bash
python -m compileall -q \
  python/rl/policy_algo/m3s1_grouped_stopping.py \
  python/rl/policy_algo/ppo_adaptive_kl.py \
  python/rl/support/nonfinite_probe.py \
  tools/diagnostics/m3s2_real_update_path_probe.py \
  tests/policy/test_grouped_stopping_loss_contracts.py \
  tests/policy/test_auxiliary_training_updates.py \
  tests/training/test_air_combat_training_entry_contracts.py
```

Outcome: pass.

```bash
python -m pytest \
  tests/policy/test_grouped_stopping_loss_contracts.py \
  tests/policy/test_auxiliary_training_updates.py \
  tests/training/test_air_combat_training_entry_contracts.py \
  tests/training/test_fire_timing_fault_localization_contracts.py -q
```

Outcome: `54 passed`.
