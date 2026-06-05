# M3-S1 P5 Dispatch Plan

Status: `2026-06-05` short-training evidence pass after nonfinite-probe
training-path repair. This is not learned-policy acceptance.

Parent: [M3-S1 Censored Optimal-Stopping Timing Contract](README.md).

## Purpose

P5 verifies whether the P4 grouped stopping implementation exposes enough
evidence to decide the next architectural move. It must answer whether the
independent stopping head moves a deterministic stop boundary at the right
time, whether early/prewindow mass remains budgeted, whether no-event mass is
visible, and whether stochastic execution remains one-shot legal under existing
C2/ROE and action masks.

P5 must not become another reward-scale or coefficient sweep.

## Active Packets

| Packet | Owner | Write set | Required output | Status |
| --- | --- | --- | --- | --- |
| `M3S1-P5A Diagnostics Surface` | diagnostics worker | `python/rl/policy_algo/ppo_adaptive_kl.py`; `tests/hmoe/test_hmoe_ppo_warmup.py` | Focused test evidence that `m3s1/*` validation metrics are emitted without changing loss/reward/legality semantics. | pass |
| `M3S1-P5B Short Training Evidence Path` | read-only explorer | none | Conservative short-training command, artifacts, metrics, and stop criteria. | pass |
| `M3S1-P5 Integration Review` | main thread | M3-S1 docs, process probe, active probe config | Review worker packets, run focused tests, and decide whether short training can begin. | pass |
| `M3S1-P5C Nonfinite Probe Drift Repair` | main thread | `python/rl/support/nonfinite_probe.py`; `tests/hmoe/test_hmoe_ppo_warmup.py` | Prove that `--nonfinite_probe` preserves M3-S1 sidecar construction, auxiliary update, and grouped diagnostics. | pass |
| `M3S1-P5 Short Training Run` | main thread | experiment outputs under `experiments_tmp/` | Run the bounded 8k M3-S1 probe and collect deterministic/stochastic process probes. | pass |

## Required Diagnostic Surface

| Diagnostic | Question answered | Acceptance role |
| --- | --- | --- |
| grouped sidecar group/row counts | Did grouped evidence survive rollout flattening and minibatching? | Required before any short train. |
| grouped active group/row counts | Is the auxiliary objective training on supported windows? | Required before any loss interpretation. |
| boundary crossing count and in-window count | Does the deterministic stop boundary move, and does it move inside desirable windows? | Core P5 signal. |
| early/prewindow event mass | Is the model spending stop probability before evidence supports stopping? | Must stay within configured budget. |
| no-event mass | Are right-censored/no-window cases represented instead of ignored? | Required to diagnose all-wait collapse. |
| closed-mask stop attempts | Does the stopping head try to stop when legal masks are closed? | Must remain diagnostic-only; masks stay authoritative. |
| one-shot legality count or violation rate | Does stochastic execution still prevent repeated fire/stop behavior? | Required before learned behavior claims. |
| stop-logit or hazard means by window kind | Is the new stopping head separating desirable, prewindow, and no-window rows? | Helps decide whether failure is representational or training-signal related. |

## Validation Ladder

1. Run focused M3-S1 tests after any P5-A code patch:

   ```bash
   python -m pytest tests/hmoe/test_hmoe_ppo_warmup.py -q -k m3s1
   ```

2. If focused tests pass, run the broader adjacent gate:

   ```bash
   python -m pytest tests/hmoe/test_m3s1_grouped_stopping.py tests/hmoe/test_hmoe_policy.py tests/hmoe/test_hmoe_ppo_warmup.py -q
   ```

3. Only after diagnostics exist, open a short-training run with explicit output
   artifacts and a step budget. Do not run long formal training as part of the
   dispatch itself.

4. After a short-training run, use the process probe in deterministic and
   stochastic modes to separate independent stopping-head movement from
   executable fire-action behavior.

## Worker Evidence

`M3S1-P5A Diagnostics Surface` returned pass and was main-thread checked with:

```bash
python -m py_compile python/rl/policy_algo/ppo_adaptive_kl.py \
  tests/hmoe/test_hmoe_ppo_warmup.py
python -m pytest tests/hmoe/test_hmoe_ppo_warmup.py -q -k m3s1
git diff --check -- python/rl/policy_algo/ppo_adaptive_kl.py \
  tests/hmoe/test_hmoe_ppo_warmup.py
```

Outcome:

- `py_compile`: pass.
- focused M3-S1 pytest: `2 passed, 18 deselected`.
- adjacent M3-S1/HMoE pytest:
  `64 passed`.
- A6/A7 adjacent regression pytest:
  `14 passed`.
- `git diff --check`: pass.

P5-A added logging for:

- `m3s1/grouped_labels_reached_loss`;
- stop-logit means and counts for all, desirable, prewindow, no-window, and
  closed-mask rows;
- event-logit delta diagnostic mean/count, explicitly diagnostic-only;
- boundary-cross and closed-mask ratios;
- rollout-level accepted-event, one-shot-violation, and closed-mask-accepted
  event counts.

`M3S1-P5B Short Training Evidence Path` returned pass as read-only evidence.
It initially found no dedicated M3-S1/P5 active training config. The main
thread then added a maintained short-probe config derived from:

```text
examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_state_completed_world_batch_probe_v1.json
```

The maintained M3-S1 P5 short-probe config is:

```text
examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s1_grouped_stopping_state_completed_world_batch_probe_v1.json
```

It keeps the A7 state-completed observation and A7 coefficients unchanged while
opening `policy_kwargs.m3_stopping_head_lr_scale = 5.0` and the
`m3s1_grouped_stopping_*` auxiliary objective under an 8k budget.

The first short-training command should target the Stage-1 C2/ROE shaped
scenario and write outputs under `experiments_tmp/`:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s1_grouped_stopping_state_completed_world_batch_probe_v1.json \
  --run_name m3s1_p5_state_completed_8k_20260605_r1 \
  --output_base experiments_tmp \
  --seed 7 \
  --diagnostics \
  --diagnostics_every 1024 \
  --nonfinite_probe
```

Config deltas from A7 state-completed:

- `total_timesteps = 8192` for the first evidence run, or `1024`/`2048` for
  dry smoke if a temporary local copy is made.
- `policy_kwargs.m3_stopping_head_lr_scale = 5.0`.
- `m3s1_grouped_stopping_coef = 1.0`.
- `m3s1_grouped_stopping_early_mass_budget = 0.05`.
- `m3s1_grouped_stopping_boundary_threshold = 0.0`.
- Keep A7 coefficients unchanged for the first comparison.

After training, the model process probes should use the same maintained config:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s1_grouped_stopping_state_completed_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/m3s1_p5_state_completed_8k_20260605_r1/final_model.zip \
  --algo auto \
  --device cpu \
  --episodes 1 \
  --seed 7 \
  --max_steps 640 \
  --json_out experiments_tmp/m3s1_p5_state_completed_8k_20260605_r1/m3s1_deterministic_probe.json \
  --csv_out experiments_tmp/m3s1_p5_state_completed_8k_20260605_r1/m3s1_deterministic_probe.csv
```

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s1_grouped_stopping_state_completed_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/m3s1_p5_state_completed_8k_20260605_r1/final_model.zip \
  --algo auto \
  --device cpu \
  --episodes 4 \
  --seed 17 \
  --max_steps 640 \
  --stochastic \
  --json_out experiments_tmp/m3s1_p5_state_completed_8k_20260605_r1/m3s1_stochastic_probe.json \
  --csv_out experiments_tmp/m3s1_p5_state_completed_8k_20260605_r1/m3s1_stochastic_probe.csv
```

The process probe now emits M3 stopping-head diagnostics:

- `policy_m3_stop_logit`, `policy_m3_stop_prob`, and
  `policy_m3_boundary_cross` at row level;
- `policy_m3_boundary_cross_count` and
  `policy_m3_first_boundary_cross_step` at episode-summary level;
- `a7_prewindow_m3_stop_prob_cum`,
  `a7_prewindow_m3_stop_prob_mean`,
  `a7_quality_window_m3_stop_prob_mean`,
  `a7_prewindow_m3_boundary_cross_count`, and
  `a7_quality_window_m3_boundary_cross_count`.

Additional main-thread checks for the probe/config handoff:

```bash
python -m pytest tests/diagnostics/test_a6_event_value_process_probe.py \
  tests/diagnostics/test_air_combat_process_probe.py -q
python -m pytest tests/training/test_air_combat_active_training_entries.py \
  -q -k 'm3s1 or stage1_bvr_probe_bootstraps'
python -m json.tool \
  examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s1_grouped_stopping_state_completed_world_batch_probe_v1.json
```

Outcome:

- diagnostics process-probe tests: `13 passed`;
- active config M3-S1/bootstrap tests: `2 passed, 13 deselected`;
- JSON syntax check: pass.

## Short-Training Evidence

The first bounded run completed but is rejected as M3 learning evidence:

```text
experiments_tmp/m3s1_p5_state_completed_8k_20260605_r1
```

Observed failure:

- `train_config_backup.json` preserved the `m3s1_grouped_stopping_*` knobs.
- The console emitted only `m3s1/stopping_head_params/*`, not
  `m3s1/grouped_*` loss/sidecar diagnostics.
- M3 stopping-head parameter norms stayed zero through `8192` steps.
- Deterministic probe stayed flat:
  `policy_m3_stop_logit_mean = 0.0`,
  `policy_m3_stop_prob_mean = 0.5`,
  `policy_m3_boundary_cross_count = 640`, and `release_count = 0`.
- Stochastic probe also kept M3 flat while the executable action branch made
  one-shot releases in 3 of 4 episodes.

Root cause:

- `--nonfinite_probe` installed copied `collect_rollouts()` and `train()` loops
  from an older PPO surface.
- That diagnostic path attached A6/A7 labels but did not build
  `_m3s1_grouped_stopping_sidecar`.
- Its copied `train()` loop did not call
  `_m3s1_grouped_stopping_auxiliary_update()` and did not emit
  `m3s1/grouped_*` logger keys.

Repair:

- `python/rl/support/nonfinite_probe.py` now resets M3-S1 tracking state,
  builds the grouped stopping sidecar during traced rollout, runs the grouped
  stopping auxiliary update during traced train, and records the M3 grouped
  diagnostics.
- Regression coverage added
  `test_nonfinite_probe_preserves_m3s1_grouped_stopping_training_path`.

Repair validation:

```bash
python -m py_compile python/rl/support/nonfinite_probe.py \
  tests/hmoe/test_hmoe_ppo_warmup.py
python -m pytest tests/hmoe/test_hmoe_ppo_warmup.py \
  -q -k 'nonfinite_probe_preserves_m3s1 or m3s1_grouped_stopping_auxiliary'
python -m pytest tests/hmoe/test_m3s1_grouped_stopping.py \
  tests/hmoe/test_hmoe_policy.py tests/hmoe/test_hmoe_ppo_warmup.py -q
python -m pytest tests/diagnostics/test_a6_event_value_process_probe.py \
  tests/diagnostics/test_air_combat_process_probe.py \
  tests/training/test_air_combat_active_training_entries.py \
  -q -k 'm3s1 or stage1_bvr_probe_bootstraps or model_policy_diagnostics_include_m3'
```

Outcome:

- `py_compile`: pass.
- targeted nonfinite/M3 pytest: `2 passed, 19 deselected`.
- adjacent HMoE/M3 pytest: `65 passed`.
- diagnostics/config focused pytest: `3 passed, 25 deselected`.

The repaired bounded run completed:

```text
experiments_tmp/m3s1_p5_nonfinite_fixed_8k_20260605_r1
```

Training evidence:

- At `2048` steps, M3 grouped diagnostics were live:
  `m3s1/grouped_stopping_grad_norm = 8.9`,
  `m3s1/grouped_stopping_loss = 15.9`,
  `m3s1/grouped_sidecar_group_count = 4`,
  `m3s1/grouped_active_group_count = 4`.
- M3 stopping-head parameters moved:
  `weight_norm = 0.00208`, `bias_norm = 0.00015` at `2048`.
- The run completed `8192` steps with no nonfinite abort and saved
  `final_model.zip`.
- Final stopping-head parameters remained nonzero:
  `weight_norm = 0.00454`, `bias_norm = 0.000328`.
- Late rollouts often had `m3s1/grouped_active_group_count = 0`; in those cases
  zero grouped grad is expected and now visible rather than silent.

Post-run process probes:

| Probe | Fire behavior | M3 stop output | Boundary signal |
| --- | --- | --- | --- |
| deterministic, seed 7, 1 episode | `release_count = 0`, final missiles `4` | `policy_m3_stop_logit_mean = -0.02457`, `policy_m3_stop_prob_mean = 0.49386` | `policy_m3_boundary_cross_count = 0` |
| stochastic, seed 17, 4 episodes | one-shot releases in episodes `0`, `1`, and `3`; no repeated-release violations | per-episode stop-prob means `0.49389` to `0.49397` | boundary-cross count `0` in all episodes |

Interpretation:

- P5 evidence confirms the M3-S1 independent stopping head can train under the
  real `--nonfinite_probe` diagnostic training path.
- The process probe can now distinguish a trained M3 stopping head from the
  executable hybrid action branch.
- The 8k probe does not show learned executable fire timing: deterministic
  release remains flat and stochastic release is still sampling-driven.
- Learned-policy acceptance remains held. Further work must decide whether to
  connect the stopping head through an adapter, change the training data/window
  supply, or re-enter broader model analysis.

## Behavior Risk

P4/P5 trains an independent stopping head, while executable `model.predict()`
still follows the hybrid event action branch. Therefore P5 can show that the
M3 stopping boundary learned without proving executable fire timing. Conversely,
deterministic release can remain flat even if the M3 head improves. Treat this
as held learned behavior until an adapter/probe explicitly connects or compares
the stopping head and executable action path.

## Stop Criteria

- Stop P5 and re-scope if diagnostics cannot be emitted without changing reward
  magnitude, C2/ROE masks, or action legality.
- Stop P5 and return to model analysis if boundary metrics remain flat while
  grouped labels, active rows, and gradient norms are healthy.
- Proceed to short training only when P5-A diagnostics and P5-B command/artifact
  plan are both integrated.

## Current Outcome

P5 diagnostics, short-probe config, process-probe support, nonfinite-probe
training-path repair, bounded 8k training, and deterministic/stochastic
post-run probes are complete. P5 is evidence-complete but not
learned-policy-accepted: the independent M3 stopping head now moves, while the
executable fire action remains low-probability and deterministic release remains
flat.
