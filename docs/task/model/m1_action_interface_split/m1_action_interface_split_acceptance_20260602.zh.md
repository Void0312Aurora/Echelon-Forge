# M1 动作接口拆分验收

状态：`2026-06-02`，`accepted`。验收范围是 `air_combat_hybrid_v1` 训练动作接口、
HMoE hybrid policy transport、runtime/proprio wiring 和 Stage-1 诊断可达性；不验收 learned
`1v1` policy，也不释放 M2。

## 已接受范围

- `air_combat_hybrid_v1` 保持 12 维 flat `Box` transport，policy 侧按连续飞行轴、
  Bernoulli 开关/脉冲和 categorical 武器选择解释。
- `tms_up`、`fire_weapon`、`fire_gun` 由 raw policy intent 的 rising edge 生成 one-step
  effective pulse。
- `proprio` / `proprio_history` 记录 effective transport action；raw intent 只用于 edge memory。
- HMoE policy 使用 hybrid 参数头并保持 joint log-prob；SB3 rollout buffer 仍接收 flat action。
- Stage-1 active `full` / hybrid reactive / hybrid temporal 配置已配对。

## 验证命令与结果

```bash
python -m py_compile gym_envs/universal_env_parts/spaces.py gym_envs/universal_env_parts/actions.py gym_envs/universal_env.py python/env_config.py python/rl/policy_algo/policies.py python/rl/runtime/world_batch_vec_env.py train.py python/training/cli.py tools/diagnostics/air_combat_stage0_process_probe.py tools/eval/eval_utils.py tools/eval/sb3_eval_base.py
# pass

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop pytest -q tests/training/test_train_bootstrap.py tests/runtime/core/test_air_combat_hybrid_action.py tests/runtime/core/test_env_config.py tests/hmoe/test_hmoe_policy.py tests/hmoe/test_hmoe_ppo_warmup.py tests/training/test_air_combat_active_training_entries.py
# 46 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop pytest -q tests/diagnostics/test_air_combat_process_probe.py tests/training/test_train_bootstrap.py tests/eval/test_eval_sb3.py -k "air_combat or cli or single_eval_builds_world_batch_runtime"
# 4 passed, 7 deselected

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop python train.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json --train_config /tmp/cmo_m1_air_combat_hybrid_smoke_config.json --output_base /tmp/cmo_m1_hybrid_smoke_runs --run_name m1_hybrid_smoke_20260602 --n_envs 1 --torch_threads 1 --seed 20260602
# 32-step hybrid smoke train passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop python train.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json --train_config /tmp/cmo_m1_air_combat_hybrid_smoke_config.json --output_base /tmp/cmo_m1_hybrid_smoke_runs --run_name m1_hybrid_smoke_eval_20260602 --n_envs 1 --torch_threads 1 --seed 20260602 --test_only --resume_path /tmp/cmo_m1_hybrid_smoke_runs/m1_hybrid_smoke_20260602/final_model.zip
# 1000-step hybrid load/predict/step smoke passed
```

## Stage-1 诊断证据

场景：
`scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json`

同 seed 固定 `range_gate_fire`：

| Config | action_mode | first_fire / release | fire attempts | invalid fire | releases | damage reports | miss distance |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `full` baseline | `full` | `1233 / 1233` | `1` | `0` | `1` | `1` | `8.096 m` |
| hybrid reactive | `air_combat_hybrid_v1` | `1233 / 1233` | `1` | `0` | `1` | `1` | `8.096 m` |

hybrid 短训模型 deterministic probe：

| Model | termination | steps | radar / master | fire attempts | releases | invalid fire |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `/tmp/cmo_m1_hybrid_smoke_runs/m1_hybrid_smoke_20260602/final_model.zip` | `failfast_deep_stall` | `421` | `1.0 / 1.0` | `0` | `0` | `0` |

解释：

- 固定 range-gate 证明新动作接口在 Stage-1 下可以产生有效 release，并和 `full` baseline
  保持相同发射/毁伤链路。
- 短训模型只说明训练内核可跑通；它仍未学会 `fire_weapon` pulse，不能当作 policy acceptance。

## Evidence Artifacts

- 诊断 JSON：
  `/tmp/cmo_m1_hybrid_range_gate_report.json`
- 对照 JSON：
  `/tmp/cmo_m1_full_range_gate_report.json`
- 短训模型 probe：
  `/tmp/cmo_m1_hybrid_smoke_model_probe.json`
- 短训模型：
  `/tmp/cmo_m1_hybrid_smoke_runs/m1_hybrid_smoke_20260602/final_model.zip`

这些 `/tmp` artifacts 是本检查点的运行证据，不是仓库内长期保留模型。

## 仍开放的 Residual

- learned policy 没有通过武器使用验收：短训 deterministic 模型 `fire_attempt_count=0`。
- 需要后续 shaping/curriculum 或更长训练，让策略稳定产生 intentional fire pulse。
- 重复发射间隔和“同目标已有己方导弹在飞”的问题仍未解决；下一步先交由 A3 C2/ROE
  定义 shot policy、pending assessment、salvo 和 reattack 授权，再判断是否仍属策略记忆。
- M2 sequence-native PPO 仍 held，不能由本验收释放。

## 禁止的能力声明

- 不声明 `1v1` learned policy 已成熟或通过。
- 不声明 temporal window 已改善重复发射。
- 不声明导弹物理、毁伤、弹药、冷却或 release kernel 已改变。
- 不声明战术记忆问题已经解决。

## 已同步索引

- [README.zh.md](README.zh.md)
- [README.md](README.md)
- [m1_action_interface_split_current_status_20260602.zh.md](m1_action_interface_split_current_status_20260602.zh.md)
- [m1_action_interface_split_task_clusters_20260602.zh.md](m1_action_interface_split_task_clusters_20260602.zh.md)
- [../README.zh.md](../README.zh.md)
