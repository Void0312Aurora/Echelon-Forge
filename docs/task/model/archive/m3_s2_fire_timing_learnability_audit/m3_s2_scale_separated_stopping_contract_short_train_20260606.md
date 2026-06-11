# M3-S2 Scale-Separated Stopping Contract Short Train

Parent: [README.md](README.md).

Status: `2026-06-06` implemented and tested; behavior still held.

## Change

This slice adds an explicit scale-separated stopping contract to the M3-S2
grouped stopping loss:

- `prewindow_hazard_scale`: prewindow rows are penalized when their per-step
  hazard exceeds a budget-scale target. If the configured target is `0`, the
  target is inferred from `early_mass_budget` and the observed prewindow length.
- `quality_hazard_target`: quality-window rows keep a separate positive hazard
  target so the optimizer cannot satisfy the contract only by globally lowering
  all stopping logits.

The active M3-S2 config now enables:

```text
m3s2_event_window_prewindow_hazard_scale_coef = 1.0
m3s2_event_window_prewindow_hazard_target = 0.0
m3s2_event_window_quality_hazard_target_coef = 10.0
m3s2_event_window_quality_hazard_target = 0.75
```

## Verification

Commands:

```bash
python -m compileall -q \
  python/rl/policy_algo/m3s1_grouped_stopping.py \
  python/rl/policy_algo/ppo_adaptive_kl.py \
  python/rl/support/nonfinite_probe.py \
  tools/diagnostics/fire_timing_fault_localization_probe.py --mode real_update

python -m pytest \
  tests/policy/test_grouped_stopping_loss_contracts.py \
  tests/policy/test_execution_policy_surface.py::ExecutionPolicySurfaceTests::test_m3_stopping_head_can_override_hybrid_fire_event_delta \
  tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_m3s2_event_window_can_train_dedicated_stopping_head_adapter \
  tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_m3s2_event_window_auxiliary_updates_executable_event_policy_path \
  tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_nonfinite_probe_preserves_m3s2_event_window_training_path \
  tests/training/test_air_combat_training_entry_contracts.py::AirCombatTrainingEntryContractTests::test_stage1_m3s2_event_window_probe_extends_state_completed_config_only \
  tests/training/test_fire_timing_fault_localization_contracts.py -q
```

Result: `22 passed in 8.17s`.

## Short Train

Command:

```bash
env PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name m3s2_scale_separated_contract_8k_20260606_r1
```

Artifacts:

- `experiments_tmp/m3s2_scale_separated_contract_8k_20260606_r1/final_model.zip`
- `experiments_tmp/m3s2_scale_separated_contract_8k_20260606_r1/m3s2_deterministic_probe.json`
- `experiments_tmp/m3s2_scale_separated_contract_8k_20260606_r1/m3s2_stochastic_probe.json`

Training trace on window-bearing updates:

| Step | prewindow hazard mean | inferred target | scale loss | quality target loss | quality boundary logit | prewindow logit mean | window logit mean | boundary crosses |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3072 | 0.413139 | 0.000651 | 48.7846 | 2.0856 | -0.3456 | -0.3510 | -0.3481 | 0 |
| 4096 | 0.355096 | 0.000651 | 45.4126 | 2.8560 | -0.5914 | -0.5967 | -0.5935 | 0 |
| 5120 | 0.302603 | 0.000651 | 42.2586 | 3.7337 | -0.8337 | -0.8349 | -0.8346 | 0 |
| 6144 | 0.256218 | 0.000651 | 39.3114 | 4.6773 | -1.0641 | -1.0657 | -1.0653 | 0 |
| 7168 | 0.218366 | 0.000651 | 36.7283 | 5.6267 | -1.2735 | -1.2752 | -1.2749 | 0 |

The contract is active and lowers prewindow hazard, but prewindow and quality
logits move down together. The quality target loss rises instead of closing,
and no deterministic boundary crossing appears.

## Behavior Probes

Deterministic probe:

```bash
env PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/m3s2_scale_separated_contract_8k_20260606_r1/final_model.zip \
  --device cuda \
  --episodes 1 \
  --max_steps 2400 \
  --json_out experiments_tmp/m3s2_scale_separated_contract_8k_20260606_r1/m3s2_deterministic_probe.json
```

Stochastic probe uses the same command with `--stochastic`.

| Probe | release count | first release | M3 stop prob mean/max | boundary crosses | prewindow M3 mean/cum | quality M3 mean | final missiles |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| deterministic | 0 | n/a | 0.157226 / 0.158519 | 0 | 0.157071 / 1.0 | 0.156935 | 4 |
| stochastic | 1 | 7 | 0.156184 / 0.158168 | 0 | 0.157353 / 0.495823 | 0.0 | 3 |

## Diagnosis

This is a negative behavior result but a useful diagnostic result:

- The new prewindow scale term is wired correctly and produces visible training
  pressure.
- The learned head does not separate prewindow and quality rows under online
  training; both logits drift together.
- The final per-step stopping probability remains around `0.157`, far above
  the inferred prewindow target `0.000651`.
- Deterministic release remains absent, and stochastic release is still early
  (`step 7`), before any quality-window rows are observed in that episode.

The result strengthens the existing structural diagnosis: M3-S2 is no longer
blocked by missing gradients or absent support alone. The current executable
stopping/action transport still admits a global hazard-suppression direction
that does not create a calibrated quality-window boundary. The next repair
should therefore target model-contract structure, not coefficient tuning.
