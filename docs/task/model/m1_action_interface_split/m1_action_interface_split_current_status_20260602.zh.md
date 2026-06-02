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

## 成熟度矩阵

| Surface | Status | Evidence | Residual |
| --- | --- | --- | --- |
| Action contract | pass | `docs/standards/air/act*.md`、action adapter tests | 后续不能把 flat transport 误写成 Gym `Dict` 迁移。 |
| Runtime wiring | pass | `UniversalEnv`、`WorldBatchVecEnv` 聚焦测试 | cooperative world-batch 不是当前 active air-combat route。 |
| HMoE hybrid policy | pass | HMoE forward/evaluate 与 tiny PPO smoke | 连续轴熵沿用 `-log_prob` sampled fallback。 |
| Active config migration | pass | training-entry tests、JSON bootstrap、32-step train smoke、1000-step load/predict smoke、Stage-1 range-gate diagnostics | learned policy 仍未通过。 |
| Shaped S1 training recovery | partial | 65,536-step shaped run 完成，训练窗口内飞行状态健康且没有 deep-stall/combat-loss 回归 | deterministic policy 仍不发射；stochastic policy 会早发/多发，武器使用尚未验收。 |
| Action-interface closure | accepted | [m1_action_interface_split_acceptance_20260602.zh.md](m1_action_interface_split_acceptance_20260602.zh.md) | M1 temporal evidence 与 M2 release 仍 held。 |

## 已运行证据

```bash
python -m py_compile gym_envs/universal_env_parts/spaces.py gym_envs/universal_env_parts/actions.py gym_envs/universal_env.py python/env_config.py python/rl/policy_algo/policies.py python/rl/runtime/world_batch_vec_env.py train.py
# pass

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/core/test_air_combat_hybrid_action.py tests/runtime/core/test_env_config.py tests/hmoe/test_hmoe_policy.py tests/hmoe/test_hmoe_ppo_warmup.py tests/training/test_air_combat_active_training_entries.py
# 40 passed

git diff --check -- docs/task/model docs/standards/air gym_envs python examples/config/training/active/air_combat tests train.py
# pass

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop pytest -q tests/training/test_train_bootstrap.py tests/runtime/core/test_air_combat_hybrid_action.py tests/runtime/core/test_env_config.py tests/hmoe/test_hmoe_policy.py tests/hmoe/test_hmoe_ppo_warmup.py tests/training/test_air_combat_active_training_entries.py
# 46 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop python train.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json --train_config /tmp/cmo_m1_air_combat_hybrid_smoke_config.json --output_base /tmp/cmo_m1_hybrid_smoke_runs --run_name m1_hybrid_smoke_20260602 --n_envs 1 --torch_threads 1 --seed 20260602
# 32-step hybrid smoke train passed; final_model.zip saved

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop python train.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json --train_config /tmp/cmo_m1_air_combat_hybrid_smoke_config.json --output_base /tmp/cmo_m1_hybrid_smoke_runs --run_name m1_hybrid_smoke_eval_20260602 --n_envs 1 --torch_threads 1 --seed 20260602 --test_only --resume_path /tmp/cmo_m1_hybrid_smoke_runs/m1_hybrid_smoke_20260602/final_model.zip
# 1000-step hybrid load/predict/step smoke passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop python tools/diagnostics/air_combat_stage0_process_probe.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_world_batch_probe_v1.json --mode range_gate_fire --episodes 1 --seed 20260602 --max_steps 2400 --json_out /tmp/cmo_m1_hybrid_range_gate_report.json --csv_out /tmp/cmo_m1_hybrid_range_gate_trace.csv
# fire_attempt_count=1, release_count=1, invalid_fire_attempt_count=0, damage_report_count=1

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop python tools/diagnostics/air_combat_stage0_process_probe.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_world_batch_probe_v1.json --mode range_gate_fire --episodes 1 --seed 20260602 --max_steps 2400 --json_out /tmp/cmo_m1_full_range_gate_report.json --csv_out /tmp/cmo_m1_full_range_gate_trace.csv
# same-seed full baseline matched first_fire/release=1233, release_count=1, invalid_fire_attempt_count=0

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop python tools/diagnostics/air_combat_stage0_process_probe.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_world_batch_probe_v1.json --mode model --model /tmp/cmo_m1_hybrid_smoke_runs/m1_hybrid_smoke_20260602/final_model.zip --algo auto --device cpu --episodes 1 --seed 20260602 --max_steps 600 --json_out /tmp/cmo_m1_hybrid_smoke_model_probe.json --csv_out /tmp/cmo_m1_hybrid_smoke_model_probe.csv
# failfast_deep_stall at step 421; fire_attempt_count=0, release_count=0

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/diagnostics/test_air_combat_process_probe.py tests/hmoe/test_hmoe_policy.py tests/runtime/core/test_air_combat_hybrid_action.py tests/runtime/air_combat/test_air_combat_reward_surface.py tests/training/test_air_combat_active_training_entries.py tests/training/test_cooperative_diagnostics_callback.py
# 35 passed, 5 subtests passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_training_shaped_v1.json --train_config experiments_tmp/generated_configs/m1_s1_hybrid_shaped_residual65k_20260602.json --run_name m1_s1_hybrid_shaped_residual65k_20260602 --output_base experiments_tmp --seed 20260604 --diagnostics --diagnostics_every 8192
# 65,536 steps 完成；最终诊断：combat_timeout window，pitch_mean=1.37deg，preterm_max_abs_g=1.05，fire_weapon_frac=0.0

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/diagnostics/air_combat_stage0_process_probe.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_training_shaped_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_shaped_world_batch_probe_v1.json --mode range_gate_fire --episodes 1 --seed 20260604 --max_steps 1800 --json_out experiments_tmp/m1_s1_hybrid_shaped_residual_range_gate_wrapped_20260602.json --csv_out experiments_tmp/m1_s1_hybrid_shaped_residual_range_gate_wrapped_20260602.csv
# wrapped range gate: release_count=1, invalid_fire_attempt_count=0, damage_report_count=1

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/diagnostics/air_combat_stage0_process_probe.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_training_shaped_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_shaped_world_batch_probe_v1.json --mode model --model experiments_tmp/m1_s1_hybrid_shaped_residual65k_20260602/final_model.zip --algo auto --device cpu --episodes 1 --seed 20260604 --max_steps 2400 --json_out experiments_tmp/m1_s1_hybrid_shaped_residual65k_model_det_wrapped_20260602.json --csv_out experiments_tmp/m1_s1_hybrid_shaped_residual65k_model_det_wrapped_20260602.csv
# deterministic final model: combat_timeout，total_reward=73.1186，fire_attempt_count=0，release_count=0

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/diagnostics/air_combat_stage0_process_probe.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_training_shaped_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_shaped_world_batch_probe_v1.json --mode model --model experiments_tmp/m1_s1_hybrid_shaped_residual65k_20260602/final_model.zip --algo auto --device cpu --episodes 3 --seed 20260604 --max_steps 2400 --stochastic --json_out experiments_tmp/m1_s1_hybrid_shaped_residual65k_model_stoch3_wrapped_20260602.json --csv_out experiments_tmp/m1_s1_hybrid_shaped_residual65k_model_stoch3_wrapped_20260602.csv
# stochastic final model: combat_timeout=3/3，release_counts=[4,3,2]，invalid_fire_attempt_counts=[1,0,0]，damage_report_counts=[0,1,0]
```

## Residual Register

- learned policy 仍没有通过武器使用验收：65k shaped deterministic 模型飞行稳定，但
  `fire_attempt_count=0`。
- stochastic policy sampling 已恢复 release 可达性，但战术质量不足：同 seed 3 episode probe
  产生早发/多发（`release_counts=[4,3,2]`），且只有 1 个 episode 产生 damage report。
- 把 accepted 动作接口证据并回 M1-A4 / M1-A5；M2 sequence-native PPO 仍不得释放。
- “同一目标已有己方导弹在飞时是否再打一枚”先交由 A3 C2/ROE 定义 shot policy、
  pending assessment、salvo 和 reattack 授权；本实现不补内核记忆板。

## 下一步顺序

1. 用 accepted hybrid action interface 作为后续 S1 训练默认候选。
2. 增加 A3 C2/ROE shaping/curriculum，更直接区分授权单发、授权齐射、再攻击许可、
   过早第二发和未授权开火。
3. 在 deterministic learned release 出现后，再比较 reactive/hybrid temporal 的 repeated-release interval。

## 禁止的过度声明

- 不声明导弹物理、毁伤、弹药或冷却模型已改变。
- 不声明 `1v1` learned policy 已训练通过。
- 不声明 tactical memory 问题已解决。
- 不声明 M2 可以启动；M2 仍依赖 M1 evidence review。
