# M3-S2 Stopping-Head Adapter Log-Domain 短训

父级：[README.zh.md](README.zh.md)。

状态：`2026-06-06` 修复证据已记录；log-domain cumulative-hazard loss 作为必要修复接受，
behavioral fire timing 仍 held。

## 问题

在 M3-S2 event-window supervision 已经通过专用 `m3_stopping_head` adapter 接入后，
为什么短训仍不能产生 deterministic fire event？

本切片检查两个实现层候选：

- 新增 balanced BCE 分支不能在运行时失败；
- 长 prewindow stopping loss 必须在 cumulative survival probability 极小时仍保留有用梯度。

## 修复

代码变更：

- `python/rl/policy_algo/m3s1_grouped_stopping.py`
  - 修复 balanced BCE 分支，改用函数本地 `quality_mask` 与 `legal_mask`，
    不再引用调用方局部变量；
  - 将 grouped stopping event-mass 项改为 log-domain 计算，使
    `-log(p_window)` 与 `-log(p_none)` 不再因概率下溢或 `clamp_min(eps)` 丢梯度；
  - 诊断仍保留 event-mass 数值，但 window mass 与 deadline mass 使用 log-sum-exp。
- `tests/policy/test_grouped_stopping_loss_contracts.py`
  - 新增长 prewindow 回归测试，确认当窗口 hazard 初始过低时，prewindow logits
    收到下降方向，quality-window logits 收到上升方向。

该 log-domain 修复是结构修复，不是系数调参。`800` 步 prewindow 下，逐行概率接近
`0.5` 会让 survival to window 极小。旧概率域 loss 会触及 `eps` clamp，进而截断降低
early hazard 所需的梯度。

## 验证

聚焦编译与测试：

```bash
python -m compileall -q \
  python/rl/policy_algo/m3s1_grouped_stopping.py \
  python/rl/policy_algo/policies.py \
  python/rl/policy_algo/ppo_adaptive_kl.py \
  python/rl/support/nonfinite_probe.py \
  tools/diagnostics/fire_timing_fault_localization_probe.py --mode real_update

python -m pytest \
  tests/policy/test_grouped_stopping_loss_contracts.py \
  tests/policy/test_execution_policy_surface.py::ExecutionPolicySurfaceTests::test_m3_stopping_head_can_override_hybrid_fire_event_delta \
  tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_m3s2_event_window_can_train_dedicated_stopping_head_adapter \
  tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_m3s2_event_window_auxiliary_updates_executable_event_policy_path \
  tests/training/test_air_combat_training_entry_contracts.py::AirCombatTrainingEntryContractTests::test_stage1_m3s2_event_window_probe_extends_state_completed_config_only \
  tests/training/test_fire_timing_fault_localization_contracts.py -q
```

结果：`20 passed`。

## 真实更新 Probe

Artifact：

```text
experiments_tmp/m3s2_stopping_head_adapter_8k_20260606_r1/m3s2_real_update_stopping_head_probe_log_domain.json
```

同一 forced-hold real row batch 使用 `scope = m3_stopping_head`、`learning_rate = 0.001`、
`max_grad_norm = 10`、reset optimizer state 更新 `120` 步。

| 指标 | Before | After |
| --- | ---: | ---: |
| loss | `1707.144817` | `70.558770` |
| prewindow logit mean | `-0.117777` | `-2.430021` |
| quality logit mean | `-0.116425` | `-1.954641` |
| quality max logit | `-0.114623` | `-0.889170` |
| quality-boundary crossing | `0 / 1040` | `0 / 1040` |
| balanced BCE loss trace | `0.693269` | `1.107806` |
| quality-prewindow margin trace | `0.003341` | `2.559333` |

解释：

- 修复恢复了降低 prewindow hazard 的强 survival gradient；
- 同一更新仍不能把 quality-window logits 推过 deterministic boundary；
- 真实 rows 上更容易的方向变成“活到窗口”，而不是“在窗口内形成脉冲”。

## 短训

命令：

```bash
env PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name m3s2_stopping_head_adapter_log_domain_8k_20260606_r1
```

Artifacts：

```text
experiments_tmp/m3s2_stopping_head_adapter_log_domain_8k_20260606_r1/final_model.zip
experiments_tmp/m3s2_stopping_head_adapter_log_domain_8k_20260606_r1/m3s2_deterministic_probe.json
experiments_tmp/m3s2_stopping_head_adapter_log_domain_8k_20260606_r1/m3s2_stochastic_probe.json
```

在线训练关键观测：

| Step | event logit mean | q boundary logit | window mass | boundary crosses |
| ---: | ---: | ---: | ---: | ---: |
| 3072 | `-0.426` | `-0.421` | `1.74e-07` | `0` |
| 4096 | `-0.672` | `-0.667` | `2.93e-06` | `0` |
| 5120 | `-0.891` | `-0.888` | `2.35e-05` | `0` |
| 6144 | `-1.09` | `-1.09` | `0.000127` | `0` |
| 7168 | `-1.29` | `-1.28` | `0.000498` | `0` |
| 8192 | `-1.48` | n/a, no-window batch | `0` | `0` |

在线轨迹确认 log-domain 修复改变了学习方向：stopping head 不再卡在每步约 `0.47`
hazard，而是被持续压低。但本 8k run 仍未学出 quality-window boundary。

## 行为 Probe

与 log-domain 前的 stopping-head adapter run 对照：

| Run | Mode | release count | first release step | M3 stop prob mean | M3 stop prob max | prewindow mean | quality mean |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| pre-log-domain adapter | deterministic | `0` | n/a | `0.470836` | `0.471635` | `0.470496` | `0.470783` |
| pre-log-domain adapter | stochastic | `1` | `3` | `0.470360` | `0.471798` | `0.463445` | `0` |
| log-domain adapter | deterministic | `0` | n/a | `0.145112` | `0.146770` | `0.145016` | `0.145566` |
| log-domain adapter | stochastic | `1` | `5` | `0.144738` | `0.146408` | `0.141813` | `0` |

解释：

- deterministic behavior 仍 held：没有 release，也没有 M3 boundary crossing；
- stochastic early release 仍可能发生，因为 `0.14` 每合法步对长 one-shot prewindow 仍过高；
- 因此该修复是必要的数值/模型合同修复，不是完整开火时机解。

## 结论

本切片接受：

- balanced BCE runtime bug 已修复；
- 长 prewindow loss 现在保留 log-domain 梯度；
- 短训不再把 stopping head 留在 `0.47` 每步 hazard 附近。

仍 held：

- deterministic quality-window crossing；
- stochastic early-release suppression 到 `1 / horizon` 尺度；
- learned low-high-low executable pulse。

下一步应把该问题视为 scale-separated stopping contract：prewindow hazard 必须接近或低于
`1 / horizon`，同时 quality window 仍需要 deterministic pulse。普通逐行分类器或未校准的
event-mass objective 不足以完成这一点。
