# A7 Online Credit Update Contract

Status: `2026-06-04` pass as an implementation contract; A7 behavior remains
held.

Parent: [README.md](README.md).

## Purpose

`A7-EVC-U` localized the online blocker to the update contract: A7 credit was
trained inside the same PPO backward pass, global gradient clip, actor/features
representation, and optimizer step as the PPO value/policy losses. This made a
locally separable credit-head signal compete with PPO value loss and
delta-alignment representation gradients.

This slice implements the bounded repair selected by U: give A7 value credit a
separate credit-head-only update lane, protect it with a separate gradient clip
budget, and keep policy delta alignment gated until the learned credit sign is
positive.

## Implementation

Code changes:

- `python/rl/policy_algo/policies.py` adds
  `HierarchicalMoEExecutionPolicy.get_hybrid_event_credit_values(obs,
  detach_latent=False)`. With `detach_latent=True`, actor features and latent
  actor state are computed under `no_grad`, then only
  `hybrid_event_credit_head` receives gradients.
- `python/rl/policy_algo/ppo_adaptive_kl.py` adds:
  - `a7_event_credit_delta_align_positive_only`;
  - `a7_event_credit_separate_update_enabled`;
  - `a7_event_credit_separate_update_max_grad_norm`;
  - `_first_event_credit_head_parameters()`;
  - `_first_event_credit_separate_value_update()`.
- The separate value update calls `_first_event_credit_loss()` with detached
  latent features, A7 value/projection-value coefficients enabled, and
  delta-align disabled. It updates only `hybrid_event_credit_head`, applies a
  separate clip budget, and zeroes optimizer gradients before and after the
  update.
- The main PPO path then calls `_first_event_credit_loss()` with A7
  value/projection-value coefficients set to `0.0` when the separate update is
  enabled. Delta alignment remains in the PPO path, but
  `a7_event_credit_delta_align_positive_only=true` gates it to positive credit
  signs.
- `python/rl/support/nonfinite_probe.py` mirrors the same separate-update path.
  This is required because the active probe config monkey-patches
  `model.train()`; without this mirror the validated training entry would
  silently bypass the repair.

Active A7 configs now enable:

```json
"a7_event_credit_delta_align_positive_only": true,
"a7_event_credit_separate_update_enabled": true,
"a7_event_credit_separate_update_max_grad_norm": 0.5
```

## Validation

Focused structural gates:

```bash
python -m compileall -q python/rl/policy_algo/ppo_adaptive_kl.py python/rl/policy_algo/policies.py python/rl/support/nonfinite_probe.py tests/policy/test_auxiliary_training_updates.py
pytest tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_nonfinite_probe_preserves_a7_event_credit_training_path tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_a7_separate_credit_update_only_writes_credit_head -q
pytest tests/policy/test_execution_policy_surface.py::ExecutionPolicySurfaceTests::test_hybrid_event_credit_head_gets_dedicated_optimizer_lane_and_zero_outputs tests/policy/test_execution_policy_surface.py::ExecutionPolicySurfaceTests::test_hybrid_event_credit_head_exposes_hold_fire_values_without_changing_event_logits tests/policy/test_event_head_update_contracts.py -q
pytest tests/training/test_event_timing_training_config_contracts.py::EventTimingTrainingConfigContractTests::test_a7_event_credit_config_exposes_credit_head_without_reusing_a6_hazard_loss tests/training/test_air_combat_training_entry_contracts.py::AirCombatTrainingEntryContractTests::test_stage1_c2_roe_a7_event_credit_probe_is_separate_from_a6_launch_window_baseline -q
```

Observed final validation: compileall and both active-config JSON parse gates
passed; focused separate-update and nonfinite-probe tests passed with
`2 passed`; policy/update-strength tests passed with `7 passed`;
active-config tests passed with `2 passed`; the final combined focused rerun
passed with `111 passed`; diff whitespace check passed.

Short learned observation:

```bash
python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config experiments_tmp/a7_separate_update_8k_v2_config_20260604.json \
  --run_name a7_separate_update_8k_v2_20260604 \
  --output_base experiments_tmp \
  --seed 7
```

Observed:

- training completed `8192` steps;
- `stderr` was empty and `final_model.zip` exists;
- `a7/evc_separate_update_enabled=1.0`;
- `a7/evc_separate_update_grad_norm_mean` was nonzero early
  (`2.365` before clipping), proving the separate lane is live;
- `a7/event_credit_advantage_mean` improved from about `-0.121` early to about
  `-0.0583` final;
- `a7/event_credit_delta_align_loss=0.0`, because positive-only gating correctly
  keeps policy coupling disabled while the learned credit sign is still
  negative;
- `train/value_loss` fell from about `9516` to about `0.475`.

Final fixed-batch credit probe:

```bash
python tools/diagnostics/a7_credit_head_offline_fit_probe.py \
  --model experiments_tmp/a7_separate_update_8k_v2_20260604/final_model.zip \
  --episodes 4 \
  --max_steps 640 \
  --fit_steps 0 \
  --eval_batch_size 512 \
  --json_out experiments_tmp/a7_separate_update_8k_v2_final_credit_probe_20260604.json
```

Observed: the fixed batch has `1356` legal-open positives, but
`legal_open_quality_positive_advantage_mean=-0.05257667228579521` and positive
sign fraction remains `0.0`.

Final process probe:

```bash
python tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config experiments_tmp/a7_separate_update_8k_v2_config_20260604.json \
  --mode model \
  --model experiments_tmp/a7_separate_update_8k_v2_20260604/final_model.zip \
  --episodes 2 \
  --max_steps 640 \
  --device auto \
  --json_out experiments_tmp/a7_separate_update_8k_v2_process_probe_20260604.json
```

Observed: `release_count=0`, `fire_once_requested_count=0`, and one-shot
legality is preserved trivially. Quality-window credit advantage remains
negative, with per-episode quality means around `-0.0542` and `-0.0521`.

Experiment outputs are retained under `experiments_tmp/` and must not be
staged.

## Interpretation

The V repair works structurally:

- the credit-head-only update lane is live;
- it is preserved under the nonfinite probe's monkey-patched training loop;
- the main PPO value/global-clip path no longer owns A7 value credit;
- policy delta alignment is correctly held while credit signs are negative.

The behavioral blocker is not solved:

- the legal-open credit advantage improves substantially compared with the old
  8k endpoint, but it does not cross zero;
- deterministic policy still chooses `hold`;
- after early training, active A7 update windows can drop to zero, so the
  remaining problem is now credit-sample/update-window availability or
  curriculum scheduling under the protected update contract.

Therefore V is accepted only as an online credit-update repair. A7 first-shot
behavior remains held.

## Next Boundary

Do not revert to coefficient-only tuning as the primary next step. The next
bounded work should explain why active positive update windows disappear after
the protected update is live, then decide whether the remedy belongs in
curriculum sampling, replay/fixed positive batches, adaptive label scheduling,
or a broader training-loop contract.
