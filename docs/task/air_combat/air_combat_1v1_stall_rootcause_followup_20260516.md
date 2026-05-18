<!-- Machine-translated draft generated on 2026-05-18 from docs/task/air_combat/air_combat_1v1_stall_rootcause_followup_20260516.zh.md. Review before treating this file as authoritative. -->

# Air Combat 1v1 Deep Stall Further Investigation and Fix Follow-up

Status: `2026-05-16`

## 1. Core Issues Continued in This Round

In the previous round of `1v1` HMoE smoke testing, `failfast_deep_stall` was clearly the dominant termination reason, but at that time, “why the aircraft would be pushed into high-angle-of-attack deep stall from the very beginning” had not been fully dissected.

This round continues to investigate downward, focusing not on re-proving “there is a stall,” but on confirming:

1. Whether the HMoE activation chain itself amplifies initial actions;
2. Whether the first rollout bypasses residual warmup;
3. Whether fixing these two startup issues will significantly mitigate deep stall.

## 2. Two Root Causes Confirmed at the Activation Layer

### 2.1 Inconsistent Semantics Between HMoE Bootstrap and Residual

The current HMoE forward pass is:

- `mean_actions = shared_mean_actions + effective_scale * expert_residual`

In other words, the routed family/subexpert heads implement semantic residual correction, not an independent action head that replaces the shared head.

However, the old implementation of `initialize_hmoe_from_shared_action_head()` directly copied the shared action head into the family head.

This leads to an obvious consequence:

1. The shared action head already outputs a complete action mean;
2. The family head is then added back as a residual to the shared head;
3. As long as the residual gate is non-zero in early rollout, the initial action mean is biased as a whole.

This is inconsistent with the design document stating: “shared action head remains the initial policy mean, routed heads contribute residual corrections.”

This round has been corrected to residual-neutral bootstrap:

- [policies.py](../../../python/rl/policy_algo/policies.py:141)
- [policies.py](../../../python/rl/policy_algo/policies.py:168)

After correction:

1. `self._hmoe_residual_gate` is initialized to `hmoe_residual_start_factor`;
2. `initialize_hmoe_from_shared_action_head()` no longer copies shared weights to the family head;
3. Family/subexpert heads start with zero residual.

### 2.2 No HMoE Warmup Applied Before the First Rollout Previously

In the old logic, `set_hmoe_training_progress()` was only called inside `train()`.

But the on-policy order of SB3 is:

1. `collect_rollouts()` first
2. Then `train()`

This means that when the first batch of rollouts occurs, the policy still retains the old `resid_gate` value.

This round moves warmup forward to before rollouts start:

- [ppo_adaptive_kl.py](../../../python/rl/policy_algo/ppo_adaptive_kl.py:102)
- [nonfinite_probe.py](../../../python/rl/support/nonfinite_probe.py:437)

The `nonfinite probe` monkeypatch rollout version is also patched here, otherwise the real smoke test path would revert to the old behavior.

## 3. Regression Test Additions

This round adds three categories of regression tests:

1. Residual gate defaults to starting warmup from zero;
2. HMoE bootstrap maintains zero-residual, instead of copying the shared head;
3. `collect_rollouts()` shows `resid_gate = 0.0` before the first policy forward.

Corresponding tests:

- [test_hmoe_policy.py](../../../tests/hmoe/test_hmoe_policy.py:151)
- [test_hmoe_train_bootstrap.py](../../../tests/hmoe/test_hmoe_train_bootstrap.py:45)
- [test_hmoe_ppo_warmup.py](../../../tests/hmoe/test_hmoe_ppo_warmup.py:65)

Local results:

```bash
python -m pytest tests/hmoe/test_hmoe_policy.py tests/hmoe/test_hmoe_train_bootstrap.py tests/hmoe/test_hmoe_ppo_warmup.py -q
```

Result: `16 passed`

## 4. Short Smoke Test Results After Fix

Execution command:

```bash
source tools/maintenance/cmo_env.sh
cmo_python train.py \
  --scenario scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_f16c_scripted_red_smoke_v1.json \
  --run_name air_combat_1v1_f16c_scripted_red_hmoe_smoke_v1_diag64_postfix_manual \
  --output_base experiments/smoke \
  --diagnostics_every 64
```

Artifacts:

- [final_model.zip](../../../experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_smoke_v1_diag64_postfix_manual/final_model.zip)

### 4.1 Confirmed Fix Effectiveness

The first `64` timestep diagnostics already show signals completely different from before the fix:

1. `hmoe/resid_gate = 0`
2. `hmoe/resid_effective_scale = 0`
3. `hmoe/resid_abs_mean = 0`
4. `hmoe_params/family/nonzero_frac = 0`
5. `hmoe_params/sub/nonzero_frac = 0`

This indicates:

1. The first rollout indeed no longer carries routed residual;
2. HMoE cold start now truly starts from the shared mean;
3. The root cause of “first batch of trajectories being amplified by HMoE residual” has been verified fixed.

### 4.2 Deep Stall Problem Not Eliminated

After the fix, the termination distribution within `512` steps is still dominated by deep stall:

1. `diag/failure_frac_window = 1.0`
2. `diag/term_frac_failfast_deep_stall = 1.0`
3. Typical `preterm_max_abs_aoa_deg ≈ 50.0 ~ 51.2`
4. Typical `preterm_max_abs_pitch_deg ≈ 77.0 ~ 81.8`
5. Typical `preterm_max_abs_roll_deg ≈ 19.3 ~ 51.7`

Near the final summary:

1. `rollout/ep_len_mean = 90`
2. `rollout/ep_rew_mean = -348`
3. `hmoe/resid_gate = 1`
4. `hmoe/resid_abs_mean ≈ 0.00305`

Compared to before the fix:

1. The amplification issue in the HMoE activation chain has been removed;
2. But after removal, the aircraft still enters high-angle-of-attack deep stall in subsequent rollouts;
3. Therefore, the current main cause has been further narrowed down to the “action surface/flight control protection/reward-termination coupling” layer, not the HMoE cold start itself.

## 5. Most Plausible Explanation at Current Stage

We are now closer to the following judgment:

1. The previous HMoE cold start implementation was indeed problematic and worsened early behavior;
2. After this fix, the first rollout now starts with zero residual;
3. However, the current `full` action space in `1v1` still allows the policy to output relatively aggressive pitch/roll/rudder directly;
4. With `mission_obs_mode = basic` and routing still fixed at `nav/vector`, the policy has not yet developed sufficiently strong energy management and high-AoA suppression;
5. Consequently, episodes are still pushed toward `AoA > 50 deg` in later stages, triggering `failfast_deep_stall`.

In other words, we can now state with reasonable confidence:

- The HMoE cold start issue is a “confirmed and fixed aggravating factor”
- But it is not the sole root cause of the current deep stall phenomenon, nor is it a total root cause that can eliminate stalls by itself after the fix.

## 6. More Valuable Next Steps

After this point, the most valuable direction is no longer to keep investigating HMoE bootstrap, but to converge on flight action constraints and training signals:

1. Check whether the `full` action space needs more conservative pitch/roll initialization or clipping in the early smoke phases of air combat;
2. Assess whether to add additional shaping for high AoA / high pitch specifically for `1v1`, rather than relying solely on failfast termination with end-of-episode penalty;
3. Check whether any path in the execution control/runtime allows RL to bypass or override current soft protections;
4. Continue to add finer-grained action-attitude-termination timing diagnostics, directly observing stick magnitude and attitude evolution in the tens of steps before stall;
5. Later, consider upgrading the air combat routing semantics from `basic` to `more combat-centric`, but this is not the top priority for the current stall issue.

## 7. Current Conclusion

After this investigation, the assessment of the stall issue can be updated to:

1. The stall is not a misinterpretation; it is a real deep-stall termination;
2. The HMoE activation chain originally had an implementation gap that amplified early instability;
3. This gap has now been fixed, and short smoke testing confirms warmup takes effect before the first rollout;
4. However, after the fix, `failfast_deep_stall` is still the dominant termination in `1v1`;
5. Therefore, the next phase should shift primary focus to action space stability, the degree to which flight control protections are enforced, and reward shaping related to high angle of attack.
