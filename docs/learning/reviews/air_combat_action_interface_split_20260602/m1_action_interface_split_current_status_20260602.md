# M1 Action Interface Split Current Status

Status: `2026-06-02`, `accepted`. The `air_combat_hybrid_v1` training action
interface slice is implemented and passes short scenario action-reachability
diagnostics; learned policy and M2 release remain held.

## Changes In This Checkpoint

- Added `air_combat_hybrid_v1`: a 12D flat `Box` transport interpreted with
  policy-side hybrid semantics.
- Added the hybrid effective-action adapter: `tms_up`, `fire_weapon` and
  `fire_gun` are rising-edge pulses; `radar_active` and `master_arm` are held
  switches; `weapon_select_id` is a `[0, 7]` categorical selector.
- Wired the hybrid path through `UniversalEnv` and `WorldBatchVecEnv`;
  `proprio` / `proprio_history` record effective transport actions, while raw
  policy intent is kept only as edge memory.
- Extended HMoE policy: continuous flight axes use tanh-squashed Gaussian
  samples, combat commands use Bernoulli / categorical logits, and the transport
  action remains `(batch, 12)`.
- Added Stage-1 reactive / temporal hybrid active configs paired with `full`
  baselines.
- Added a Stage-1 shaped hybrid training probe that lowers `log_std_init` and
  applies a narrow stable-flight residual wrapper only to flight-control axes
  `[0, 1, 2, 3]`; radar, master-arm, fire and weapon-select commands remain
  policy-controlled.
- Fixed the process probe to apply the train-config action wrapper so model
  diagnostics report the same effective action channel used during training.
- Added the A3 C2/ROE probe interpretation layer:
  `air_combat_c2_roe_v1` now lets Stage-1 diagnostics split repeated release
  into authorized and violation buckets before M1/M2 memory claims.

## Maturity Matrix

| Surface | Status | Evidence | Residual |
| --- | --- | --- | --- |
| Action contract | pass | `docs/domains/air/standards/pilot_action_contract*.md`, action adapter tests | Do not describe flat transport as a Gym `Dict` migration. |
| Runtime wiring | pass | Focused `UniversalEnv` and `WorldBatchVecEnv` tests | Cooperative world-batch is not the active air-combat route. |
| HMoE hybrid policy | pass | HMoE forward/evaluate and tiny PPO smoke | Continuous-axis entropy uses the `-log_prob` sampled fallback. |
| Active config migration | pass | training-entry tests, JSON bootstrap, 32-step train smoke, 1000-step load/predict smoke, Stage-1 range-gate diagnostics | Learned policy is still not accepted. |
| A3 C2/ROE interpretation | pass | [A3 P4 probe evidence](a3_c2_roe_release_discipline_20260603/a3_c2_roe_p4_probe_evidence_20260603.md) | This classifies release behavior; it does not prove learned policy quality. |
| A3 learned-policy probe | held | [A3 learned-policy probe evidence](a3_c2_roe_release_discipline_20260603/a3_c2_roe_learned_policy_probe_20260603.md) | 32k deterministic does not fire and stochastic still makes violation releases; post-launch mission observation dynamic state has been added. |
| A3 reactive/temporal comparison | held | [A3 reactive/temporal comparison](a3_c2_roe_release_discipline_20260603/a3_c2_roe_reactive_temporal_comparison_20260603.md) | Temporal stochastic reduces violation releases from 8 to 0, but deterministic policy still does not fire. |
| Shaped S1 training recovery | partial | 65,536-step shaped run completed with healthy flight-state diagnostics and no deep-stall/combat-loss regression in training windows | Deterministic policy does not fire; stochastic policy fires early/repeatedly and is not weapon-employment accepted. |
| Action-interface closure | accepted | [m1_action_interface_split_acceptance_20260602.md](m1_action_interface_split_acceptance_20260602.md) | M1 temporal evidence and M2 release remain held. |

## Evidence Run

```bash
python -m py_compile gym_envs/universal_env_parts/spaces.py gym_envs/universal_env_parts/actions.py gym_envs/universal_env.py python/env_config.py python/rl/policy_algo/policies.py python/rl/runtime/world_batch_vec_env.py train.py
# pass

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/core/test_air_combat_hybrid_action.py tests/runtime/core/test_env_config.py tests/policy/test_execution_policy_surface.py tests/policy/test_auxiliary_training_updates.py tests/training/test_air_combat_training_entry_contracts.py
# 40 passed

git diff --check -- docs/learning docs/domains/air gym_envs python examples/config/training/active/air_combat tests train.py
# pass

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop pytest -q tests/training/test_training_bootstrap_contracts.py tests/runtime/core/test_air_combat_hybrid_action.py tests/runtime/core/test_env_config.py tests/policy/test_execution_policy_surface.py tests/policy/test_auxiliary_training_updates.py tests/training/test_air_combat_training_entry_contracts.py
# 46 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop python train.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json --train_config /tmp/cmo_m1_air_combat_hybrid_smoke_config.json --output_base /tmp/cmo_m1_hybrid_smoke_runs --run_name m1_hybrid_smoke_20260602 --n_envs 1 --torch_threads 1 --seed 20260602
# 32-step hybrid smoke train passed; final_model.zip saved

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop python train.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json --train_config /tmp/cmo_m1_air_combat_hybrid_smoke_config.json --output_base /tmp/cmo_m1_hybrid_smoke_runs --run_name m1_hybrid_smoke_eval_20260602 --n_envs 1 --torch_threads 1 --seed 20260602 --test_only --resume_path /tmp/cmo_m1_hybrid_smoke_runs/m1_hybrid_smoke_20260602/final_model.zip
# 1000-step hybrid load/predict/step smoke passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop python tools/diagnostics/air_combat_weapon_employment_process_probe.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_world_batch_probe_v1.json --mode range_gate_fire --episodes 1 --seed 20260602 --max_steps 2400 --json_out /tmp/cmo_m1_hybrid_range_gate_report.json --csv_out /tmp/cmo_m1_hybrid_range_gate_trace.csv
# fire_attempt_count=1, release_count=1, invalid_fire_attempt_count=0, damage_report_count=1

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop python tools/diagnostics/air_combat_weapon_employment_process_probe.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_world_batch_probe_v1.json --mode range_gate_fire --episodes 1 --seed 20260602 --max_steps 2400 --json_out /tmp/cmo_m1_full_range_gate_report.json --csv_out /tmp/cmo_m1_full_range_gate_trace.csv
# same-seed full baseline matched first_fire/release=1233, release_count=1, invalid_fire_attempt_count=0

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop python tools/diagnostics/air_combat_weapon_employment_process_probe.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_world_batch_probe_v1.json --mode model --model /tmp/cmo_m1_hybrid_smoke_runs/m1_hybrid_smoke_20260602/final_model.zip --algo auto --device cpu --episodes 1 --seed 20260602 --max_steps 600 --json_out /tmp/cmo_m1_hybrid_smoke_model_probe.json --csv_out /tmp/cmo_m1_hybrid_smoke_model_probe.csv
# failfast_deep_stall at step 421; fire_attempt_count=0, release_count=0

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/air_combat/test_diagnostics_probe_contracts.py tests/policy/test_execution_policy_surface.py tests/runtime/core/test_air_combat_hybrid_action.py tests/runtime/air_combat/test_air_combat_reward_surface.py tests/training/test_air_combat_training_entry_contracts.py tests/training/test_diagnostics_callback_contracts.py
# 35 passed, 5 subtests passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_training_shaped_v1.json --train_config experiments_tmp/generated_configs/m1_s1_hybrid_shaped_residual65k_20260602.json --run_name m1_s1_hybrid_shaped_residual65k_20260602 --output_base experiments_tmp --seed 20260604 --diagnostics --diagnostics_every 8192
# 65,536 steps completed; final diagnostics: combat_timeout window, pitch_mean=1.37deg, preterm_max_abs_g=1.05, fire_weapon_frac=0.0

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/diagnostics/air_combat_weapon_employment_process_probe.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_training_shaped_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_shaped_world_batch_probe_v1.json --mode range_gate_fire --episodes 1 --seed 20260604 --max_steps 1800 --json_out experiments_tmp/m1_s1_hybrid_shaped_residual_range_gate_wrapped_20260602.json --csv_out experiments_tmp/m1_s1_hybrid_shaped_residual_range_gate_wrapped_20260602.csv
# wrapped range gate: release_count=1, invalid_fire_attempt_count=0, damage_report_count=1

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/diagnostics/air_combat_weapon_employment_process_probe.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_training_shaped_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_shaped_world_batch_probe_v1.json --mode model --model experiments_tmp/m1_s1_hybrid_shaped_residual65k_20260602/final_model.zip --algo auto --device cpu --episodes 1 --seed 20260604 --max_steps 2400 --json_out experiments_tmp/m1_s1_hybrid_shaped_residual65k_model_det_wrapped_20260602.json --csv_out experiments_tmp/m1_s1_hybrid_shaped_residual65k_model_det_wrapped_20260602.csv
# deterministic final model: combat_timeout, total_reward=73.1186, fire_attempt_count=0, release_count=0

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/diagnostics/air_combat_weapon_employment_process_probe.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_training_shaped_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_shaped_world_batch_probe_v1.json --mode model --model experiments_tmp/m1_s1_hybrid_shaped_residual65k_20260602/final_model.zip --algo auto --device cpu --episodes 3 --seed 20260604 --max_steps 2400 --stochastic --json_out experiments_tmp/m1_s1_hybrid_shaped_residual65k_model_stoch3_wrapped_20260602.json --csv_out experiments_tmp/m1_s1_hybrid_shaped_residual65k_model_stoch3_wrapped_20260602.csv
# stochastic final model: combat_timeout=3/3, release_counts=[4,3,2], invalid_fire_attempt_counts=[1,0,0], damage_report_counts=[0,1,0]
```

## Residual Register

- Learned policy weapon-employment acceptance remains open: the 65k shaped
  deterministic model is stable but still has `fire_attempt_count=0`.
- Stochastic policy sampling restores release reachability but not tactics:
  same-seed 3-episode probe produced early/repeated releases
  (`release_counts=[4,3,2]`) and only one damage report.
- Fold the accepted action-interface evidence back into M1-A4 / M1-A5; do not
  release M2 sequence-native PPO before that review.
- Tactical memory for "one friendly missile already in flight against this
  target" now routes first through A3 C2/ROE shot policy, pending assessment,
  salvo authorization and reattack authorization. The A3 P4 probes now show
  that repeated release can be split into authorized and violation buckets; no
  engine memory board is added here.

## Next Actions

1. Use the accepted hybrid action interface as the default candidate for
   follow-on S1 training.
2. Repair training signal and policy routing so deterministic policy learns an
   authorized first shot under A3 C2/ROE.
3. Once deterministic learned release appears, compare reactive/hybrid-temporal
   repeated-release intervals and post-launch hold behavior under A3-aware
   metrics.

## Explicitly Forbidden Overclaims

- Do not claim missile physics, damage, ammo or cooldown changed.
- Do not claim a `1v1` learned policy has passed training acceptance.
- Do not claim tactical memory is solved.
- Do not claim M2 may start; M2 still depends on M1 evidence review.
