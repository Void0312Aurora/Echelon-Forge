# M3-S2 Head Normalization And Calibration Short Train

Parent: [README.md](README.md).

Status: `2026-06-06` implementation wired; behavioral fire timing still held.

## Purpose

The chain breakpoint probe localized the first failing link to
`m3_head_optimization_conditioning`: the actor latent already contains a
linearly separable prewindow/quality signal, but the online M3 stopping head
does not learn the calibrated separator. This slice implements the direct
repair candidate:

- normalize the M3 stopping-head input;
- train that normalizer and linear head in the dedicated M3-S2 update lane;
- add explicit logit calibration terms that push prewindow rows below a
  negative ceiling and quality-window rows above a positive floor.

## Implementation

Code changes:

- `python/rl/policy_algo/policies.py`
  - adds `m3_stopping_head_norm_enabled`;
  - creates `m3_stopping_norm = LayerNorm(latent_dim)` when the M3 stopping head
    is enabled and the flag is true;
  - applies the normalized latent in both `get_m3_stopping_logits()` and the
    executable hybrid event adapter;
  - keeps normalizer parameters in the `m3_stopping_head` optimizer group.
- `python/rl/policy_algo/m3s1_grouped_stopping.py`
  - adds `window_prewindow_logit_ceiling_coef`,
    `window_prewindow_logit_ceiling`, `window_quality_logit_floor_coef`, and
    `window_quality_logit_floor`;
  - records ceiling/floor diagnostics.
- `python/rl/policy_algo/ppo_adaptive_kl.py`,
  `python/rl/support/nonfinite_probe.py`, and
  `tools/diagnostics/m3s2_real_update_path_probe.py`
  propagate and log the new contract fields.
- `tools/diagnostics/m3s2_chain_breakpoint_probe.py`
  evaluates fitted heads on the actual normalized M3 head input when enabled.

Active config:

```text
examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json
```

New active values:

```json
{
  "m3s2_event_window_prewindow_logit_ceiling_coef": 5.0,
  "m3s2_event_window_prewindow_logit_ceiling": -2.0,
  "m3s2_event_window_quality_logit_floor_coef": 5.0,
  "m3s2_event_window_quality_logit_floor": 2.0,
  "policy_kwargs": {
    "m3_stopping_head_norm_enabled": true
  }
}
```

## Verification

Commands:

```bash
python -m compileall -q \
  python/rl/policy_algo/policies.py \
  python/rl/policy_algo/m3s1_grouped_stopping.py \
  python/rl/policy_algo/ppo_adaptive_kl.py \
  python/rl/support/nonfinite_probe.py \
  tools/diagnostics/m3s2_real_update_path_probe.py \
  tools/diagnostics/m3s2_chain_breakpoint_probe.py

python -m pytest \
  tests/policy/test_grouped_stopping_loss_contracts.py \
  tests/policy/test_execution_policy_surface.py::ExecutionPolicySurfaceTests::test_m3_stopping_head_can_override_hybrid_fire_event_delta \
  tests/policy/test_execution_policy_surface.py::ExecutionPolicySurfaceTests::test_m3_stopping_head_gets_dedicated_optimizer_lane_and_zero_outputs \
  tests/policy/test_execution_policy_surface.py::ExecutionPolicySurfaceTests::test_m3_stopping_head_norm_uses_dedicated_optimizer_lane_and_zero_outputs \
  tests/policy/test_execution_policy_surface.py::ExecutionPolicySurfaceTests::test_initialize_hmoe_from_shared_action_head_zeroes_m3_stopping_head \
  tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_m3s2_event_window_can_train_dedicated_stopping_head_adapter \
  tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_m3s2_event_window_auxiliary_updates_executable_event_policy_path \
  tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_nonfinite_probe_preserves_m3s2_event_window_training_path \
  tests/training/test_air_combat_training_entry_contracts.py::AirCombatTrainingEntryContractTests::test_stage1_m3s2_event_window_probe_extends_state_completed_config_only \
  tests/training/test_fire_timing_fault_localization_contracts.py \
  tests/training/test_fire_timing_fault_localization_contracts.py -q
```

Result: `29 passed in 5.04s`.

Post-probe test after adding normalized parameter grouping:

```bash
python -m pytest \
  tests/training/test_fire_timing_fault_localization_contracts.py \
  tests/training/test_fire_timing_fault_localization_contracts.py -q
```

Result: `5 passed in 2.49s`.

## Short Train

Run:

```bash
env PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name m3s2_head_norm_calibration_8k_20260606_r1
```

Artifact:

```text
experiments_tmp/m3s2_head_norm_calibration_8k_20260606_r1/final_model.zip
```

Training trace highlights:

| Step | Window groups | Prewindow mean | Quality mean | Boundary crosses | Key read |
| ---: | ---: | ---: | ---: | ---: | --- |
| 2048 | 0 | n/a | n/a | 0 | no quality-window support in that logged batch |
| 3072 | 4 | `-0.740` | `-0.739` | 0 | calibration losses active but no separation |
| 4096 | 4 | `-1.11` | `-1.10` | 0 | logits move down together |
| 6144 | 4 | `-1.06` | `-1.06` | 0 | no discriminator emerges |
| 7168 | 4 | `-1.05` | `-1.05` | 0 | `q_pre_margin = 0.00297` |
| 8192 | 0 | n/a | n/a | 0 | final logged batch has no window rows |

The new losses were active: at 3072 steps the probe logged
`prewindow_logit_ceiling_loss = 1.59` and `quality_logit_floor_loss = 7.5`.
However, the online head learned a shared negative offset instead of a
prewindow-vs-quality separator.

## Behavior Probes

Deterministic artifact:

```text
experiments_tmp/m3s2_head_norm_calibration_8k_20260606_r1/m3s2_deterministic_probe.json
```

Key deterministic fields:

| Field | Value |
| --- | ---: |
| `release_count` | 0 |
| `policy_m3_stop_prob_mean` | `0.118269` |
| `policy_m3_boundary_cross_count` | 0 |
| `a7_prewindow_step_count` | 800 |
| `a7_quality_window_step_count` | 1080 |
| `a7_prewindow_m3_stop_prob_mean` | `0.117957` |
| `a7_quality_window_m3_stop_prob_mean` | `0.118636` |

Stochastic artifact:

```text
experiments_tmp/m3s2_head_norm_calibration_8k_20260606_r1/m3s2_stochastic_probe.json
```

Key stochastic fields:

| Field | Value |
| --- | ---: |
| `release_count` | 1 |
| `first_release_step` | 14 |
| `a7_prewindow_step_count` | 10 |
| `a7_quality_window_step_count` | 0 |
| `policy_m3_stop_prob_mean` | `0.117586` |
| `policy_m3_boundary_cross_count` | 0 |

The stochastic result is still an early sampled release before any quality rows.

## Breakpoint Probes

Chain breakpoint artifact:

```text
experiments_tmp/m3s2_head_norm_calibration_8k_20260606_r1/m3s2_chain_breakpoint_probe.json
```

Result:

| Segment | Result | Evidence |
| --- | --- | --- |
| Label support | pass | `840` prewindow rows and `1040` quality rows. |
| Current learned M3 head | fail | quality boundary `0 / 1040`; event mode fires `0` times. |
| Fresh standardized head on normalized M3 input | pass | accuracy `1.0`; prewindow boundary `0 / 840`; quality boundary `1040 / 1040`; separation margin `9.0797`. |
| Folded head through adapter | behavior pass | one legal quality pulse at row `281`, no prewindow pulse. |
| Direct trained M3 head initialized from current head | near pass / strict fail | accuracy `0.9968`, but leaves `3` prewindow positives and misses `3` quality rows. |

Verdict remains:

```text
first_breakpoint = m3_head_optimization_conditioning
```

Real update artifact:

```text
experiments_tmp/m3s2_head_norm_calibration_8k_20260606_r1/m3s2_real_update_path_probe.json
```

Result:

| Scope | Loss delta | Prewindow mean delta | Quality mean delta | Quality boundary |
| --- | ---: | ---: | ---: | --- |
| `current` | `634.18 -> 557.86` | `-2.011 -> -2.975` | `-2.003 -> -2.965` | still `0 / 1040` |
| `current_plus_features` | `634.18 -> 539.74` | `-2.011 -> -2.760` | `-2.003 -> -2.725` | still `0 / 1040` |

The real update verdict is:

```text
any_update_raises_quality_logit = false
any_update_quality_boundary = false
```

This is the strongest negative evidence in the slice: the true M3-S2 update can
reduce the configured loss while moving quality-window logits farther from the
deterministic boundary.

## Verdict

The implemented repair is wired and measurable, but it does not solve learned
fire timing. It improves global hold pressure and reduces mean stop probability
relative to the previous scale-separated run (`0.157226 -> 0.118269` in the
deterministic probe), but it still does not create a quality-window boundary.

The updated diagnosis is:

```text
normalized/calibrated linear head capacity exists,
but the online M3-S2 auxiliary objective still has a lower-loss direction that
suppresses hazard globally instead of raising quality-window logits.
```

The next repair should not be another coefficient sweep. It should change the
mathematical training object so the quality-window term cannot be satisfied, or
loss-reduced, by global hazard suppression. Candidate directions are a
two-stage discriminative window classifier plus one-shot hazard shaping, a
positive-bag boundary objective with an explicit prewindow negative set, or a
separate calibrated classifier head whose output is converted to a stopping
hazard only after the classifier boundary is learned.
