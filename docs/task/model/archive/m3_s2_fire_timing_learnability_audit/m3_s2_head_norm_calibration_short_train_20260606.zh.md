# M3-S2 停止头归一化与校准短训

父级：[README.zh.md](README.zh.md)。

状态：`2026-06-06` implementation 已接线；behavioral fire timing 仍 held。

## 目的

chain breakpoint probe 将第一个失败链路定位为
`m3_head_optimization_conditioning`：actor latent 已经包含线性可分的
prewindow/quality 信号，但在线 M3 stopping head 没有学到经过校准的分离器。
本切片实现直接修复候选：

- 归一化 M3 stopping-head 输入；
- 将 normalizer 和 linear head 一起放进 M3-S2 dedicated update lane；
- 增加显式 logit 校准项：把 prewindow rows 压到负 ceiling 以下，把 quality-window
  rows 抬到正 floor 以上。

## 实现

代码变更：

- `python/rl/policy_algo/policies.py`
  - 增加 `m3_stopping_head_norm_enabled`；
  - 在 M3 stopping head 启用且 flag 为 true 时创建
    `m3_stopping_norm = LayerNorm(latent_dim)`；
  - 在 `get_m3_stopping_logits()` 与 executable hybrid event adapter 中使用归一化 latent；
  - normalizer 参数归入 `m3_stopping_head` optimizer group。
- `python/rl/policy_algo/m3s1_grouped_stopping.py`
  - 增加 `window_prewindow_logit_ceiling_coef`、
    `window_prewindow_logit_ceiling`、`window_quality_logit_floor_coef` 与
    `window_quality_logit_floor`；
  - 记录 ceiling/floor diagnostics。
- `python/rl/policy_algo/ppo_adaptive_kl.py`、
  `python/rl/support/nonfinite_probe.py` 与
  `tools/diagnostics/m3s2_real_update_path_probe.py`
  传递并记录新合同字段。
- `tools/diagnostics/m3s2_chain_breakpoint_probe.py`
  在 flag 启用时基于实际 normalized M3 head input 评估 fitted heads。

active config：

```text
examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json
```

新增 active values：

```json
{
  "m3s2_event_window_prewindow_logit_ceiling_coef": 5.0,
  "m3s2_event_window_prewindow_logit_ceiling": -2.0,
  "m3s2_event_window_quality_logit_floor_coef": 5.0,
  "m3s2_event_window_quality_logit_floor": 2.0,
  "policy_kwargs": {
    "m3_stopping_head_norm_enabled": true
  }
}
```

## 验证

命令：

```bash
python -m compileall -q \
  python/rl/policy_algo/policies.py \
  python/rl/policy_algo/m3s1_grouped_stopping.py \
  python/rl/policy_algo/ppo_adaptive_kl.py \
  python/rl/support/nonfinite_probe.py \
  tools/diagnostics/m3s2_real_update_path_probe.py \
  tools/diagnostics/m3s2_chain_breakpoint_probe.py

python -m pytest \
  tests/policy/test_grouped_stopping_loss_contracts.py \
  tests/policy/test_execution_policy_surface.py::ExecutionPolicySurfaceTests::test_m3_stopping_head_can_override_hybrid_fire_event_delta \
  tests/policy/test_execution_policy_surface.py::ExecutionPolicySurfaceTests::test_m3_stopping_head_gets_dedicated_optimizer_lane_and_zero_outputs \
  tests/policy/test_execution_policy_surface.py::ExecutionPolicySurfaceTests::test_m3_stopping_head_norm_uses_dedicated_optimizer_lane_and_zero_outputs \
  tests/policy/test_execution_policy_surface.py::ExecutionPolicySurfaceTests::test_initialize_hmoe_from_shared_action_head_zeroes_m3_stopping_head \
  tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_m3s2_event_window_can_train_dedicated_stopping_head_adapter \
  tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_m3s2_event_window_auxiliary_updates_executable_event_policy_path \
  tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_nonfinite_probe_preserves_m3s2_event_window_training_path \
  tests/training/test_air_combat_training_entry_contracts.py::AirCombatTrainingEntryContractTests::test_stage1_m3s2_event_window_probe_extends_state_completed_config_only \
  tests/training/test_fire_timing_fault_localization_contracts.py \
  tests/training/test_fire_timing_fault_localization_contracts.py -q
```

结果：`29 passed in 5.04s`。

补充 normalized parameter grouping 后的探针测试：

```bash
python -m pytest \
  tests/training/test_fire_timing_fault_localization_contracts.py \
  tests/training/test_fire_timing_fault_localization_contracts.py -q
```

结果：`5 passed in 2.49s`。

## 短训

运行：

```bash
env PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name m3s2_head_norm_calibration_8k_20260606_r1
```

artifact：

```text
experiments_tmp/m3s2_head_norm_calibration_8k_20260606_r1/final_model.zip
```

训练轨迹摘要：

| Step | Window groups | Prewindow mean | Quality mean | Boundary crosses | 读取 |
| ---: | ---: | ---: | ---: | ---: | --- |
| 2048 | 0 | n/a | n/a | 0 | logged batch 中无 quality-window support |
| 3072 | 4 | `-0.740` | `-0.739` | 0 | 校准 losses 生效但没有分离 |
| 4096 | 4 | `-1.11` | `-1.10` | 0 | logits 同步下移 |
| 6144 | 4 | `-1.06` | `-1.06` | 0 | 未出现 discriminator |
| 7168 | 4 | `-1.05` | `-1.05` | 0 | `q_pre_margin = 0.00297` |
| 8192 | 0 | n/a | n/a | 0 | final logged batch 无窗口 rows |

新 losses 确实生效：3072 steps 时记录
`prewindow_logit_ceiling_loss = 1.59` 与 `quality_logit_floor_loss = 7.5`。
但是在线 head 学到的是共享负偏置，而不是 prewindow-vs-quality separator。

## 行为探针

deterministic artifact：

```text
experiments_tmp/m3s2_head_norm_calibration_8k_20260606_r1/m3s2_deterministic_probe.json
```

关键 deterministic 字段：

| Field | Value |
| --- | ---: |
| `release_count` | 0 |
| `policy_m3_stop_prob_mean` | `0.118269` |
| `policy_m3_boundary_cross_count` | 0 |
| `a7_prewindow_step_count` | 800 |
| `a7_quality_window_step_count` | 1080 |
| `a7_prewindow_m3_stop_prob_mean` | `0.117957` |
| `a7_quality_window_m3_stop_prob_mean` | `0.118636` |

stochastic artifact：

```text
experiments_tmp/m3s2_head_norm_calibration_8k_20260606_r1/m3s2_stochastic_probe.json
```

关键 stochastic 字段：

| Field | Value |
| --- | ---: |
| `release_count` | 1 |
| `first_release_step` | 14 |
| `a7_prewindow_step_count` | 10 |
| `a7_quality_window_step_count` | 0 |
| `policy_m3_stop_prob_mean` | `0.117586` |
| `policy_m3_boundary_cross_count` | 0 |

stochastic 结果仍是 quality rows 出现前的 early sampled release。

## 断点探针

chain breakpoint artifact：

```text
experiments_tmp/m3s2_head_norm_calibration_8k_20260606_r1/m3s2_chain_breakpoint_probe.json
```

结果：

| Segment | Result | Evidence |
| --- | --- | --- |
| Label support | pass | `840` prewindow rows 与 `1040` quality rows。 |
| Current learned M3 head | fail | quality boundary `0 / 1040`；event mode fire 为 `0`。 |
| Fresh standardized head on normalized M3 input | pass | accuracy `1.0`；prewindow boundary `0 / 840`；quality boundary `1040 / 1040`；separation margin `9.0797`。 |
| Folded head through adapter | behavior pass | row `281` 出现一次合法 quality pulse，无 prewindow pulse。 |
| Direct trained M3 head initialized from current head | near pass / strict fail | accuracy `0.9968`，但残留 `3` 个 prewindow positives，并漏掉 `3` 个 quality rows。 |

verdict 仍是：

```text
first_breakpoint = m3_head_optimization_conditioning
```

real update artifact：

```text
experiments_tmp/m3s2_head_norm_calibration_8k_20260606_r1/m3s2_real_update_path_probe.json
```

结果：

| Scope | Loss delta | Prewindow mean delta | Quality mean delta | Quality boundary |
| --- | ---: | ---: | ---: | --- |
| `current` | `634.18 -> 557.86` | `-2.011 -> -2.975` | `-2.003 -> -2.965` | 仍为 `0 / 1040` |
| `current_plus_features` | `634.18 -> 539.74` | `-2.011 -> -2.760` | `-2.003 -> -2.725` | 仍为 `0 / 1040` |

real update verdict：

```text
any_update_raises_quality_logit = false
any_update_quality_boundary = false
```

这是本切片最强的负向证据：真实 M3-S2 update 可以降低 configured loss，同时让
quality-window logits 离 deterministic boundary 更远。

## 结论

本次修复已接线且可测，但没有解决 learned fire timing。它增强了全局 hold pressure，
并将 deterministic probe 的 mean stop probability 相比上一轮 scale-separated run 从
`0.157226` 降到 `0.118269`，但仍没有形成 quality-window boundary。

更新后的诊断是：

```text
normalized/calibrated linear head capacity exists,
but the online M3-S2 auxiliary objective still has a lower-loss direction that
suppresses hazard globally instead of raising quality-window logits.
```

下一步不应继续系数扫描。需要改变数学训练对象，使 quality-window 项不能被 global hazard
suppression 满足或降低 loss。候选方向包括：两阶段 discriminative window classifier +
one-shot hazard shaping、带显式 prewindow negative set 的 positive-bag boundary objective，
或单独的 calibrated classifier head，先学 classifier boundary，再把输出转换为 stopping hazard。
