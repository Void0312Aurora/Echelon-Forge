## HMoE Strict Terminal Eval (2026-05-15)

### Scope

This note records the strict terminal comparison used after the HMoE probe-path
fix landed in the cooperative takeoff-to-cruise-to-landing line.

Why this comparison exists:

- Earlier historical HMoE runs were not trustworthy because the nonfinite probe
  wrapper could bypass observation-aware HMoE routing and effectively reduce the
  policy to shared-head behavior during formal training.
- The repaired run
  [20260515_coop_takeoff_to_cruise_landing_hmoe_probe_fix_v1](/home/void0312/Workshop/CMO/experiments/20260515_coop_takeoff_to_cruise_landing_hmoe_probe_fix_v1)
  is the first cooperative HMoE run in this line that is treated as the valid
  mainline result.

### Trusted Models

- Shared baseline terminal model:
  [experiments/coop_takeoff_to_cruise_landing_formal_20260514/final_model.zip](/home/void0312/Workshop/CMO/experiments/coop_takeoff_to_cruise_landing_formal_20260514/final_model.zip)
- HMoE strict-budget terminal comparison model:
  [experiments/20260515_coop_takeoff_to_cruise_landing_hmoe_probe_fix_v1/checkpoints/model_130048_steps.zip](/home/void0312/Workshop/CMO/experiments/20260515_coop_takeoff_to_cruise_landing_hmoe_probe_fix_v1/checkpoints/model_130048_steps.zip)

Notes:

- The repaired HMoE run later continued beyond the original budget and produced
  a latest visualization/final model at
  [experiments/20260515_coop_takeoff_to_cruise_landing_hmoe_probe_fix_v1/final_model.zip](/home/void0312/Workshop/CMO/experiments/20260515_coop_takeoff_to_cruise_landing_hmoe_probe_fix_v1/final_model.zip).
- For strict terminal comparison, the checkpoint tagged `130048` was used
  instead of that later final model so the comparison stays close to the shared
  baseline's `131072`-step budget.

### Eval Command Shape

The comparison used
[tools/eval/eval_sb3_cooperative_policy.py](/home/void0312/Workshop/CMO/tools/eval/eval_sb3_cooperative_policy.py)
with:

- scenario:
  [scenarios/combined/cooperative_takeoff_to_cruise_landing_continuous_train_v1.json](/home/void0312/Workshop/CMO/scenarios/combined/cooperative_takeoff_to_cruise_landing_continuous_train_v1.json)
- train config:
  [examples/config/training/active/cooperative_takeoff_to_cruise_landing_hmoe_v1.json](/home/void0312/Workshop/CMO/examples/config/training/active/cooperative_takeoff_to_cruise_landing_hmoe_v1.json)
- `curriculum_stage=2`
- `seed=20260515`
- `episodes=1` for the fully aligned terminal A/B check

### Strict Terminal Results

#### Shared baseline

- `world_success_rate = 1.0`
- `world_steps = 14781`
- `world_termination_counts = {"success_objective": 2}`
- `ElementLead mean_reward = 13758.964545`
- `Wingman mean_reward = 12319.455807`
- `shared_world_reset_rate = 0.0` for both roles

#### HMoE terminal checkpoint

- `world_success_rate = 1.0`
- `world_steps = 14968`
- `world_termination_counts = {"success_objective": 2}`
- `ElementLead mean_reward = 13655.011646`
- `Wingman mean_reward = 15997.046975`
- `shared_world_reset_rate = 0.0` for both roles

### Interpretation

- Both policies successfully complete the cooperative terminal objective under
  the same stage-2 evaluation setup.
- HMoE passes the strict end-to-end terminal viability check; it does not show a
  terminal collapse relative to the shared baseline.
- This comparison is intentionally narrow. It answers "is HMoE still operational
  at the strict terminal checkpoint?" more than "is HMoE globally better?".
- The single-seed single-episode result is not enough to claim superiority.

### Raw Artifacts

The raw JSON outputs were written under the ignored experiment directory:

- `/home/void0312/Workshop/CMO/experiments/strict_terminal_eval_20260515/shared_final_stage2_ep1.json`
- `/home/void0312/Workshop/CMO/experiments/strict_terminal_eval_20260515/hmoe_130048_stage2_ep1.json`
- `/home/void0312/Workshop/CMO/experiments/strict_terminal_eval_20260515/shared_final_stage2.json`

### Reproduction

Use
[scripts/eval_hmoe_strict_terminal.sh](/home/void0312/Workshop/CMO/scripts/eval_hmoe_strict_terminal.sh)
to rerun the aligned terminal comparison.
