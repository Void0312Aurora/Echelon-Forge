<!-- Machine-translated draft generated on 2026-05-18 from docs/task/air_combat/air_combat_1v1_training_smoke_progress_20260516.zh.md. Review before treating this file as authoritative. -->

# Air Combat 1v1 Training Smoke Test Progress

Status: `2026-05-16` The current round has completed the HMoE mainline smoke test.

Related documents:

- [Air Combat 1v1 Engagement Analysis](air_combat_1v1_entry_analysis_20260516.md)
- [Air Combat 1v1 Freeze Plan](air_combat_1v1_freeze_plan_20260516.md)
- [Air Combat 1v1 F-16C Baseline Switch and Minimum Combat Contract Progress](air_combat_1v1_f16c_baseline_progress_20260516.md)

## 1. Entry Scope for This Round

This round consolidates the `1v1` active training entry into the HMoE mainline:

- [examples/config/training/active/air_combat/README.md](../../../../examples/config/training/active/air_combat/README.md)
- [air_combat_1v1_f16c_scripted_red_smoke_v1.json](../../../../examples/config/training/active/air_combat/air_combat_1v1_f16c_scripted_red_smoke_v1.json)
- [air_combat_1v1_f16c_scripted_red_world_batch_smoke_v1.json](../../../../examples/config/training/active/air_combat/air_combat_1v1_f16c_scripted_red_world_batch_smoke_v1.json)

Current maintained scope:

1. The blue learner is `F-16C_Block50`;
2. The red opponent is the scripted `F-16C_Block50` declared in the scenario;
3. The training strategy directly uses `HierarchicalMoEExecutionPolicy`;
4. One config covers the standard `execution` path, one config covers the default `WorldBatchVecEnv` path;
5. The current `1v1` active line no longer treats the shared policy as the main entry record.

## 2. Current HMoE Configuration Form

This round's `1v1` HMoE configuration follows the core scope of the currently maintained mainline:

1. `policy = HierarchicalMoEExecutionPolicy`
2. `hmoe.bootstrap_from_shared_action_head = auto`
3. `family_subexpert_counts = [3, 2, 3, 1]`
4. `hmoe_residual_scale = 0.18`
5. `hmoe_head_lr_scale = 0.15`
6. `hmoe_residual_warmup_fraction = 0.3`
7. `device = cuda`
8. `diagnostics.nonfinite_probe = true`

This ensures that air combat `1v1` is not temporarily falling back to the shared architecture, but directly starting the smoke test on the current HMoE training mainline.

Additional notes:

1. The current `1v1` smoke still uses `mission_obs_mode = basic`;
2. Therefore, HMoE is indeed activated, but the task semantics visible to the policy are still simplified;
3. This means this round is more like "the HMoE mainline training chain is connected" rather than "air-combat-specific HMoE routing semantics are fully expanded."

## 3. Why the Scripted Residual Wrapper Is Still Not Enabled

This round still does not enable the existing `stable_flight` / `takeoff_cruise_landing` scripted residual wrapper.

The reasons remain valid:

1. The `scripted_lock_indices` in the current maintained configuration lock many switch dimensions;
2. These include weapon-related control surfaces that require learning freedom for air combat;
3. For `1v1`, keeping the original `full` action surface is more suitable for verifying the air combat HMoE mainline, rather than handing key dimensions over to a non-air-combat scripted baseline.

## 4. Smoke Test Execution Results

Execution command one:

```bash
source tools/maintenance/cmo_env.sh
cmo_python train.py \
  --scenario scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_f16c_scripted_red_smoke_v1.json \
  --run_name air_combat_1v1_f16c_scripted_red_hmoe_smoke_v1_manual \
  --output_base experiments/smoke
```

Execution command two:

```bash
source tools/maintenance/cmo_env.sh
cmo_python train.py \
  --scenario scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_f16c_scripted_red_world_batch_smoke_v1.json \
  --run_name air_combat_1v1_f16c_scripted_red_hmoe_world_batch_smoke_v1_manual \
  --output_base experiments/smoke
```

Results:

1. The HMoE standard `execution` path started normally and ran fully for `512` timesteps;
2. The HMoE default `WorldBatchVecEnv` path also ran fully for `512` timesteps;
3. Both paths generated checkpoints at `256` and `512` timesteps normally;
4. Both paths generated `final_model.zip` normally;
5. Both paths enabled HMoE bootstrap and non-finite probe, and no non-finite abort was triggered in this round;
6. This round verified whether the HMoE mainline can carry the minimum training loop for `1v1` air combat, not a shared-vs-HMoE A/B.

Artifact locations:

- [experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_smoke_v1_manual/final_model.zip](../../../../experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_smoke_v1_manual/final_model.zip)
- [experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_smoke_v1_manual/checkpoints/model_256_steps.zip](../../../../experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_smoke_v1_manual/checkpoints/model_256_steps.zip)
- [experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_smoke_v1_manual/checkpoints/model_512_steps.zip](../../../../experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_smoke_v1_manual/checkpoints/model_512_steps.zip)
- [experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_world_batch_smoke_v1_manual/final_model.zip](../../../../experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_world_batch_smoke_v1_manual/final_model.zip)
- [experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_world_batch_smoke_v1_manual/checkpoints/model_256_steps.zip](../../../../experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_world_batch_smoke_v1_manual/checkpoints/model_256_steps.zip)
- [experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_world_batch_smoke_v1_manual/checkpoints/model_512_steps.zip](../../../../experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_world_batch_smoke_v1_manual/checkpoints/model_512_steps.zip)

## 5. Current Signals from the Logs

Both HMoE smoke test logs show:

1. Rollout can proceed continuously, episodes are not dead on the first step;
2. Average episode length is around `98` to `125` steps;
3. Average return is still significantly negative, currently in the range of approximately `-370` to `-361`;
4. The HMoE path is indeed activated, as clearly printed at training start:
   - `HMoE bootstrap: initialized family heads from shared action head and reset subexpert residuals.`
   - `Diagnostics: auto-enabled for HMoE route/parameter observability.`
5. This indicates that the current issue is no longer "whether it has switched to HMoE", but that the `1v1` air combat reward / termination / eval are still coarse, and the training signal has not yet become interpretable.

## 6. Supplementary Statistics

To actually log diagnostic information, this round additionally ran two sets of HMoE smoke tests with the same configuration but `--diagnostics_every 64`:

Standard path:

- [experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_smoke_v1_diag64_manual/final_model.zip](../../../../experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_smoke_v1_diag64_manual/final_model.zip)

Batch path:

- [experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_world_batch_smoke_v1_diag64_manual/final_model.zip](../../../../experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_world_batch_smoke_v1_diag64_manual/final_model.zip)

### 6.1 Final Training Scalars

Standard `execution` HMoE:

1. `rollout/ep_len_mean = 98.0`
2. `rollout/ep_rew_mean = -370.07`
3. `time/fps = 33`
4. `train/approx_kl = 1.31e-4`
5. `train/value_loss = 17447.53`
6. `train/kl_penalty_coef = 0.032`
7. `train/std = 0.2231`

Default `WorldBatchVecEnv` HMoE:

1. `rollout/ep_len_mean = 110.0`
2. `rollout/ep_rew_mean = -361.02`
3. `time/fps = 34`
4. `train/approx_kl = 9.30e-5`
5. `train/value_loss = 24897.13`
6. `train/kl_penalty_coef = 0.032`
7. `train/std = 0.2231`

### 6.2 Termination Distribution

Both diagnostic paths show the same very clear phenomenon:

1. In the current window, almost all terminations are `failfast_deep_stall`;
2. `diag/failure_frac_window = 1.0`;
3. `diag/term_frac_failfast_deep_stall = 1.0`;
4. `diag/term_rew_failfast_penalty = -50`;
5. The main component of the final total return is around `-85` to `-88`.

This indicates that the current `1v1` HMoE mainline is functional, but the primary obstacle to "learning air combat in training" is not the HMoE architecture itself, but rather:

1. Insufficient early flight stability;
2. Failfast termination dominates the training signal too early;
3. Air combat victory/defeat and weapon chain rewards have not yet become the main learning drivers.

### 6.3 HMoE Routing Statistics

The diagnostic logs also provided HMoE routing distributions.

The current results are very consistent:

1. `hmoe/fam/nav = 1.0`
2. `hmoe/sub/nav/vector = 1.0`
3. No activation of `takeoff_ground / formation_cooperative / recovery_landing` families was observed.

This does not mean HMoE is not working, but rather:

1. The current `1v1` smoke uses `mission_obs_mode = basic`;
2. The current mission semantics consistently route into the navigation family;
3. Therefore, this round's HMoE mainline verification is more about "architecture and training chain are effective," not yet "air-combat-specific family/subexpert differentiation."

### 6.4 HMoE Parameter Statistics

Parameter statistics also provide a useful signal:

Standard path final approximate values:

1. `hmoe_params/family/nonzero_frac = 1.0`
2. `hmoe_params/sub/nonzero_frac = 0.111`
3. `hmoe_params/family/weight_norm_mean ≈ 0.0412`
4. `hmoe_params/sub/weight_norm_mean ≈ 1.2e-4`

Batch path final approximate values:

1. `hmoe_params/family/nonzero_frac = 1.0`
2. `hmoe_params/sub/nonzero_frac = 0.111`
3. `hmoe_params/family/weight_norm_mean ≈ 0.0412`
4. `hmoe_params/sub/weight_norm_mean ≈ 1.5e-4`

This indicates:

1. The family head is indeed in a non-zero working state;
2. Subexpert residuals are also being updated, but the magnitude is still very small;
3. This is consistent with the current routing being long-term concentrated on `nav/vector`.

## 7. Interpretability Boundaries of the Current Stage

After this round of smoke tests, we can state:

1. The `1v1` air combat active line has been switched back to the HMoE mainline scope;
2. The scripted red side and HMoE policy have entered a real rollout loop;
3. The main issue currently exposed is `failfast_deep_stall` dominating termination, not whether HMoE is enabled;
4. HMoE routing is working, but under the `basic` mission semantics, it is almost entirely concentrated on `nav/vector`;
5. However, there is no longer a need to treat "first go through shared" as part of the mainline narrative.

## 8. Next Steps

Under the HMoE mainline scope, the natural progression sequence is:

1. Freeze the HMoE `1v1` smoke test results and minimal regression commands;
2. Prioritize addressing early flight stability and the `failfast_deep_stall` dominance issue;
3. Add `1v1` termination reason statistics and eval output;
4. Clearly define `combat_win / combat_loss / combat_draw / combat_timeout / ammo_exhausted` training and evaluation fields;
5. Then supplement mission/routing semantics more closely aligned with engagement contexts, so that HMoE no longer remains on a single `nav/vector` route for extended periods.
