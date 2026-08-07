# M1 动作接口拆分当前状态

状态：`2026-06-02`，`accepted`。`air_combat_hybrid_v1` 训练动作接口切片已实现并通过
短场景 action-reachability 诊断；learned policy 与 M2 release 仍 held。

## 本检查点变化

- 增加 `air_combat_hybrid_v1` action mode：12 维 flat `Box` transport，policy 侧按 hybrid 语义解释。
- 增加 hybrid effective-action adapter：`tms_up`、`fire_weapon`、`fire_gun` 为 rising-edge pulse；
  `radar_active`、`master_arm` 为 held switch；`weapon_select_id` 为 `[0, 7]` categorical selector。
- 将 hybrid path 接入 `UniversalEnv` 与 `WorldBatchVecEnv`；`proprio` / `proprio_history`
  记录 effective transport action，raw policy intent 只用于 edge memory。
- 扩展 HMoE policy：连续飞行轴使用 tanh-squashed Gaussian，combat commands 使用
  Bernoulli / categorical logits，transport action 仍保持 `(batch, 12)`。
- 增加 Stage-1 reactive / temporal hybrid active config，与 `full` baseline 配对。
- 增加 Stage-1 shaped hybrid 训练探针：降低 `log_std_init`，并只在飞控轴 `[0, 1, 2, 3]`
  上使用很窄的 stable-flight residual wrapper；雷达、master-arm、fire、weapon-select
  仍由策略直接控制。
- 修复 process probe，使 model 诊断按 train_config 套用 action wrapper，避免诊断面和训练有效动作通道不一致。
- 增加 A3 C2/ROE probe 解释层：`air_combat_c2_roe_v1` 现在能让 Stage-1
  诊断先把重复发射拆成授权 bucket 和违规 bucket，再讨论 M1/M2 记忆证据。

## 成熟度矩阵

| Surface | Status | Evidence | Residual |
| --- | --- | --- | --- |
| Action contract | pass | `docs/domains/air/standards/pilot_action_contract*.md`、action adapter tests | 后续不能把 flat transport 误写成 Gym `Dict` 迁移。 |
| Runtime wiring | pass | `UniversalEnv`、`WorldBatchVecEnv` 聚焦测试 | cooperative world-batch 不是当前 active air-combat route。 |
| HMoE hybrid policy | pass | HMoE forward/evaluate 与 tiny PPO smoke | 连续轴熵沿用 `-log_prob` sampled fallback。 |
| Active config migration | pass | training-entry tests、JSON bootstrap、32-step train smoke、1000-step load/predict smoke、Stage-1 range-gate diagnostics | learned policy 仍未通过。 |
| A3 C2/ROE interpretation | pass | [A3 P4 探针证据](../../air_combat/archive/a3_c2_roe_release_discipline/a3_c2_roe_p4_probe_evidence_20260603.zh.md) | 它分类 release 行为，但不证明 learned policy 质量。 |
| A3 learned-policy probe | held | [A3 learned-policy 探针证据](../../air_combat/archive/a3_c2_roe_release_discipline/a3_c2_roe_learned_policy_probe_20260603.zh.md) | 32k deterministic 不发射，stochastic 仍违规多发；已补 post-launch mission observation 动态状态。 |
| A3 reactive/temporal comparison | held | [A3 reactive/temporal 对照证据](../../air_combat/archive/a3_c2_roe_release_discipline/a3_c2_roe_reactive_temporal_comparison_20260603.zh.md) | temporal stochastic 将违规发射从 8 次降到 0 次，但 deterministic policy 仍不发射。 |
| Shaped S1 training recovery | partial | 65,536-step shaped run 完成，训练窗口内飞行状态健康且没有 deep-stall/combat-loss 回归 | deterministic policy 仍不发射；stochastic policy 会早发/多发，武器使用尚未验收。 |
| Action-interface closure | accepted | [m1_action_interface_split_acceptance_20260602.zh.md](m1_action_interface_split_acceptance_20260602.zh.md) | M1 temporal evidence 与 M2 release 仍 held。 |

## 已运行证据

```bash
python -m py_compile gym_envs/universal_env_parts/spaces.py gym_envs/universal_env_parts/actions.py gym_envs/universal_env.py python/env_config.py python/rl/policy_algo/policies.py python/rl/runtime/world_batch_vec_env.py train.py
# pass

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/core/test_air_combat_hybrid_action.py tests/runtime/core/test_env_config.py tests/policy/test_execution_policy_surface.py tests/policy/test_auxiliary_training_updates.py tests/training/test_air_combat_training_entry_contracts.py
# 40 passed

git diff --check -- docs/task/model docs/domains/air gym_envs python examples/config/training/active/air_combat tests train.py
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
# 65,536 steps 完成；最终诊断：combat_timeout window，pitch_mean=1.37deg，preterm_max_abs_g=1.05，fire_weapon_frac=0.0

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/diagnostics/air_combat_weapon_employment_process_probe.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_training_shaped_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_shaped_world_batch_probe_v1.json --mode range_gate_fire --episodes 1 --seed 20260604 --max_steps 1800 --json_out experiments_tmp/m1_s1_hybrid_shaped_residual_range_gate_wrapped_20260602.json --csv_out experiments_tmp/m1_s1_hybrid_shaped_residual_range_gate_wrapped_20260602.csv
# wrapped range gate: release_count=1, invalid_fire_attempt_count=0, damage_report_count=1

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/diagnostics/air_combat_weapon_employment_process_probe.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_training_shaped_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_shaped_world_batch_probe_v1.json --mode model --model experiments_tmp/m1_s1_hybrid_shaped_residual65k_20260602/final_model.zip --algo auto --device cpu --episodes 1 --seed 20260604 --max_steps 2400 --json_out experiments_tmp/m1_s1_hybrid_shaped_residual65k_model_det_wrapped_20260602.json --csv_out experiments_tmp/m1_s1_hybrid_shaped_residual65k_model_det_wrapped_20260602.csv
# deterministic final model: combat_timeout，total_reward=73.1186，fire_attempt_count=0，release_count=0

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/diagnostics/air_combat_weapon_employment_process_probe.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_training_shaped_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_shaped_world_batch_probe_v1.json --mode model --model experiments_tmp/m1_s1_hybrid_shaped_residual65k_20260602/final_model.zip --algo auto --device cpu --episodes 3 --seed 20260604 --max_steps 2400 --stochastic --json_out experiments_tmp/m1_s1_hybrid_shaped_residual65k_model_stoch3_wrapped_20260602.json --csv_out experiments_tmp/m1_s1_hybrid_shaped_residual65k_model_stoch3_wrapped_20260602.csv
# stochastic final model: combat_timeout=3/3，release_counts=[4,3,2]，invalid_fire_attempt_counts=[1,0,0]，damage_report_counts=[0,1,0]
```

## Residual Register

- learned policy 仍没有通过武器使用验收：65k shaped deterministic 模型飞行稳定，但
  `fire_attempt_count=0`。
- stochastic policy sampling 已恢复 release 可达性，但战术质量不足：同 seed 3 episode probe
  产生早发/多发（`release_counts=[4,3,2]`），且只有 1 个 episode 产生 damage report。
- 把 accepted 动作接口证据并回 M1-A4 / M1-A5；M2 sequence-native PPO 仍不得释放。
- “同一目标已有己方导弹在飞时是否再打一枚”先交由 A3 C2/ROE 定义 shot policy、
  pending assessment、salvo 和 reattack 授权。A3 P4 probe 现在显示重复发射可被拆成
  授权和违规 bucket；本实现不补内核记忆板。

## 下一步顺序

1. 用 accepted hybrid action interface 作为后续 S1 训练默认候选。
2. 修复训练信号和 policy routing，使 deterministic policy 在 A3 C2/ROE 下学到授权首发。
3. 在 deterministic learned release 出现后，用 A3-aware 指标比较 reactive/hybrid temporal
   repeated-release interval 与 post-launch hold 行为。

## 禁止的过度声明

- 不声明导弹物理、毁伤、弹药或冷却模型已改变。
- 不声明 `1v1` learned policy 已训练通过。
- 不声明 tactical memory 问题已解决。
- 不声明 M2 可以启动；M2 仍依赖 M1 evidence review。
