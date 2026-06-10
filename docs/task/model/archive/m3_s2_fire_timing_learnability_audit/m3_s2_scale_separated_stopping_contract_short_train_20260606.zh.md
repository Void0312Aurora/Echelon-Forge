# M3-S2 尺度分离 Stopping Contract 短训

父级：[README.zh.md](README.zh.md)。

状态：`2026-06-06` 已实现并测试；行为仍 held。

## 修改

本切片为 M3-S2 grouped stopping loss 增加显式的尺度分离 stopping contract：

- `prewindow_hazard_scale`：当 prewindow rows 的每步 hazard 超过预算尺度目标时惩罚。
  如果配置目标为 `0`，则从 `early_mass_budget` 和观测到的 prewindow 长度推导每步目标。
- `quality_hazard_target`：quality-window rows 维持独立的正向 hazard target，
  避免 optimizer 只通过全局压低所有 stopping logits 来满足 prewindow 约束。

active M3-S2 config 当前启用：

```text
m3s2_event_window_prewindow_hazard_scale_coef = 1.0
m3s2_event_window_prewindow_hazard_target = 0.0
m3s2_event_window_quality_hazard_target_coef = 10.0
m3s2_event_window_quality_hazard_target = 0.75
```

## 验证

命令：

```bash
python -m compileall -q \
  python/rl/policy_algo/m3s1_grouped_stopping.py \
  python/rl/policy_algo/ppo_adaptive_kl.py \
  python/rl/support/nonfinite_probe.py \
  tools/diagnostics/m3s2_real_update_path_probe.py

python -m pytest \
  tests/policy/test_grouped_stopping_loss_contracts.py \
  tests/policy/test_execution_policy_surface.py::ExecutionPolicySurfaceTests::test_m3_stopping_head_can_override_hybrid_fire_event_delta \
  tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_m3s2_event_window_can_train_dedicated_stopping_head_adapter \
  tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_m3s2_event_window_auxiliary_updates_executable_event_policy_path \
  tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_nonfinite_probe_preserves_m3s2_event_window_training_path \
  tests/training/test_air_combat_training_entry_contracts.py::AirCombatTrainingEntryContractTests::test_stage1_m3s2_event_window_probe_extends_state_completed_config_only \
  tests/training/test_fire_timing_fault_localization_contracts.py -q
```

结果：`22 passed in 8.17s`。

## 短训

命令：

```bash
env PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name m3s2_scale_separated_contract_8k_20260606_r1
```

Artifacts：

- `experiments_tmp/m3s2_scale_separated_contract_8k_20260606_r1/final_model.zip`
- `experiments_tmp/m3s2_scale_separated_contract_8k_20260606_r1/m3s2_deterministic_probe.json`
- `experiments_tmp/m3s2_scale_separated_contract_8k_20260606_r1/m3s2_stochastic_probe.json`

有窗口样本的训练日志：

| Step | prewindow hazard mean | inferred target | scale loss | quality target loss | quality boundary logit | prewindow logit mean | window logit mean | boundary crosses |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3072 | 0.413139 | 0.000651 | 48.7846 | 2.0856 | -0.3456 | -0.3510 | -0.3481 | 0 |
| 4096 | 0.355096 | 0.000651 | 45.4126 | 2.8560 | -0.5914 | -0.5967 | -0.5935 | 0 |
| 5120 | 0.302603 | 0.000651 | 42.2586 | 3.7337 | -0.8337 | -0.8349 | -0.8346 | 0 |
| 6144 | 0.256218 | 0.000651 | 39.3114 | 4.6773 | -1.0641 | -1.0657 | -1.0653 | 0 |
| 7168 | 0.218366 | 0.000651 | 36.7283 | 5.6267 | -1.2735 | -1.2752 | -1.2749 | 0 |

contract 确实生效并压低了 prewindow hazard，但 prewindow 与 quality logits 同步下移。
quality target loss 上升而不是收敛，且没有出现 deterministic boundary crossing。

## 行为探针

deterministic probe：

```bash
env PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/m3s2_scale_separated_contract_8k_20260606_r1/final_model.zip \
  --device cuda \
  --episodes 1 \
  --max_steps 2400 \
  --json_out experiments_tmp/m3s2_scale_separated_contract_8k_20260606_r1/m3s2_deterministic_probe.json
```

stochastic probe 使用同一命令并增加 `--stochastic`。

| Probe | release count | first release | M3 stop prob mean/max | boundary crosses | prewindow M3 mean/cum | quality M3 mean | final missiles |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| deterministic | 0 | n/a | 0.157226 / 0.158519 | 0 | 0.157071 / 1.0 | 0.156935 | 4 |
| stochastic | 1 | 7 | 0.156184 / 0.158168 | 0 | 0.157353 / 0.495823 | 0.0 | 3 |

## 诊断

这是一个行为负结果，但提供了有价值的诊断：

- 新 prewindow scale 项已经正确接线，并产生可见训练压力。
- learned head 在在线训练中没有分离 prewindow 与 quality rows；两段 logits 几乎同步漂移。
- 最终每步 stopping probability 仍约为 `0.157`，远高于 inferred prewindow target `0.000651`。
- deterministic release 仍缺失，stochastic release 仍提前到第 `7` 步，
  此时该 episode 中还没有观测到 quality-window rows。

该结果强化了既有结构性诊断：M3-S2 现在不只是缺少梯度或 support。
当前 executable stopping/action transport 仍存在全局 hazard-suppression 方向，
不会自动形成校准后的 quality-window boundary。下一步应修复模型合同结构，
而不是继续调系数。
