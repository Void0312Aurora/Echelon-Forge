# A7 Shadow Quality Target Repair

Status: `2026-06-04` `A7-EVC-J` implementation repair pass; learned-policy
outcome still held after short training.

Parent: [README.md](README.md). Chinese companion:
[a7_event_value_advantage_credit_head_shadow_quality_repair_20260604.zh.md](a7_event_value_advantage_credit_head_shadow_quality_repair_20260604.zh.md).

## Repair

`A7-EVC-I` found that early stochastic accepted release censored all later
quality-window positives from A7 labels. `A7-EVC-J` repairs that target
construction path:

- `build_first_event_hazard_labels()` now supports an A7-only
  `shadow_quality_after_early_accept` pass.
- Early accepted release before quality still produces pre-window /
  early-accepted negative labels.
- Later launch-window quality facts in the same episode can now create
  `shadow_quality` positive credit labels tied to the first-event window id.
- `compute_first_event_credit_loss()` accepts a `delta_align_active` mask.
- `AdaptiveKLPPO._first_event_credit_loss()` excludes `shadow_quality` rows
  from event-logit delta alignment, so post-release closed-mask observations
  train the credit head but are not distilled as legal fire actions.
- The A7 active config now explicitly sets
  `a7_event_credit_shadow_quality_weight = 1.0`.

This keeps A3/A5 runtime legality unchanged.

## Focused Validation

Commands:

```bash
python -m compileall -q \
  python/rl/policy_algo/first_event_hazard.py \
  python/rl/policy_algo/ppo_adaptive_kl.py \
  python/training/diagnostics.py \
  tests/policy/test_first_event_timing_contracts.py \
  tests/training/test_event_timing_training_config_contracts.py \
  tests/training/test_air_combat_training_entry_contracts.py
python -m json.tool examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json
pytest tests/policy/test_first_event_timing_contracts.py -q
pytest tests/policy/test_event_head_update_contracts.py tests/policy/test_auxiliary_training_updates.py -q
pytest tests/training/test_event_timing_training_config_contracts.py \
  tests/training/test_air_combat_training_entry_contracts.py \
  tests/training/test_diagnostics_callback_contracts.py \
  tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q
```

Outcomes:

- compileall: pass;
- JSON active config: pass;
- first-event label/loss tests: `15 passed`;
- A7 gradient/PPO warmup tests: `14 passed`;
- config/diagnostics/process-probe tests: `27 passed`.

New focused tests cover:

- early accepted release before quality plus later shadow quality;
- no-shadow-quality fallback, preserving early-accepted negatives;
- delta alignment skip for shadow rows.

## Label Reconstruction Check

Using the old r3 stochastic probe CSV and the repaired builder:

| Probe | Active | Positives | Negatives | Sources |
| --- | ---: | ---: | ---: | --- |
| deterministic r3 | `1880` | `1076` | `804` | `prewindow=804`, `deadline=1076` |
| stochastic r3 | `3241` | `3222` | `19` | `prewindow=16`, `early_accepted=3`, `shadow_quality=3222` |

The former `0`-positive stochastic label distribution is fixed.

## Short Training

Run:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a7_shadow_quality_repair_32k_20260604_r1 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260681
```

Outcome:

- completed `32768` steps;
- final model:
  `experiments_tmp/a7_shadow_quality_repair_32k_20260604_r1/final_model.zip`;
- final train scalar sample:
  - `a7/event_credit_active_count_mean = 450`;
  - `a7/event_credit_target_positive_frac = 0.6`;
  - `a7/event_credit_loss = 0.322`;
  - `a7/event_credit_delta_align_loss = 0.000476`;
  - `a7/event_credit_advantage_mean = -0.96`.

Interpretation: repaired labels entered the training stream, but the learned
event-credit advantage remained negative.

## Probe Results

Deterministic probe:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a7_shadow_quality_repair_32k_20260604_r1/final_model.zip \
  --episodes 1 \
  --seed 20260682 \
  --max_steps 2400 \
  --json_out experiments_tmp/a7_shadow_quality_repair_32k_20260604_r1/a7_shadow_quality_deterministic_probe.json \
  --csv_out experiments_tmp/a7_shadow_quality_repair_32k_20260604_r1/a7_shadow_quality_deterministic_probe.csv
```

Observed:

- deterministic release count: `0`;
- fire mask open steps: `1880`;
- open-window event fire probability mean/max: `25.5%` / `27.2%`;
- quality-window A7 advantage mean: `-0.902`;
- legality violations: `0`.

Stochastic probe:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a7_shadow_quality_repair_32k_20260604_r1/final_model.zip \
  --episodes 3 \
  --seed 20260682 \
  --max_steps 2400 \
  --stochastic \
  --json_out experiments_tmp/a7_shadow_quality_repair_32k_20260604_r1/a7_shadow_quality_stochastic_probe.json \
  --csv_out experiments_tmp/a7_shadow_quality_repair_32k_20260604_r1/a7_shadow_quality_stochastic_probe.csv
```

Observed:

- release steps: `4`, `43`, `2`;
- authorized releases: `3/3`;
- unauthorized, repeat, and shot-budget violations: `0`;
- still no quality-window timing acceptance.

Repaired label reconstruction on this new probe:

| Probe | Active | Positives | Negatives | Sources |
| --- | ---: | ---: | ---: | --- |
| deterministic r1 | `1880` | `1071` | `809` | `prewindow=809`, `deadline=1071` |
| stochastic r1 | `3215` | `3209` | `6` | `prewindow=3`, `early_accepted=3`, `shadow_quality=3209` |

## Decision

`A7-EVC-J` fixes the confirmed label-censoring bug: stochastic early accepted
episodes no longer become zero-positive A7 target samples.

It does not solve learned first-shot timing. The behavior remains held:

- deterministic still does not fire;
- stochastic still fires too early;
- A7 advantage remains negative in the quality window.

The next mechanism question is no longer "why are there no positives after
early accepted release?" It is how to make shadow credit affect legal-open
quality states. The likely follow-on is a legal-state counterfactual projection
or a stronger split between shadow value learning and legal-state policy
distillation.

No new M2, HMoE redesign, missile authority, doctrine, `2v2`, or self-play
scope is released.
