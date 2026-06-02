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

## 成熟度矩阵

| Surface | Status | Evidence | Residual |
| --- | --- | --- | --- |
| Action contract | pass | `docs/standards/air/act*.md`、action adapter tests | 后续不能把 flat transport 误写成 Gym `Dict` 迁移。 |
| Runtime wiring | pass | `UniversalEnv`、`WorldBatchVecEnv` 聚焦测试 | cooperative world-batch 不是当前 active air-combat route。 |
| HMoE hybrid policy | pass | HMoE forward/evaluate 与 tiny PPO smoke | 连续轴熵沿用 `-log_prob` sampled fallback。 |
| Active config migration | pass | training-entry tests、JSON bootstrap、32-step train smoke、1000-step load/predict smoke、Stage-1 range-gate diagnostics | learned policy 仍未通过。 |
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
```

## Residual Register

- learned policy 仍没有通过武器使用验收：短训 deterministic 模型 `fire_attempt_count=0`。
- 把 accepted 动作接口证据并回 M1-A4 / M1-A5；M2 sequence-native PPO 仍不得释放。
- “同一目标已有己方导弹在飞时是否再打一枚”的战术记忆问题仍 deferred，不在本实现中补内核记忆板。

## 下一步顺序

1. 用 accepted hybrid action interface 作为后续 S1 训练默认候选。
2. 增加 weapon-employment shaping/curriculum 或更长训练，推动 learned policy 产生 intentional pulse。
3. 在出现实际 learned release 后，再比较 temporal reactive/hybrid temporal 的 repeated-release interval。

## 禁止的过度声明

- 不声明导弹物理、毁伤、弹药或冷却模型已改变。
- 不声明 `1v1` learned policy 已训练通过。
- 不声明 tactical memory 问题已解决。
- 不声明 M2 可以启动；M2 仍依赖 M1 evidence review。
