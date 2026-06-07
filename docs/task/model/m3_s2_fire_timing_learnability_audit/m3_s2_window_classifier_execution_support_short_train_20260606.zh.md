# M3-S2 窗口分类器执行支持短训 - 2026-06-06

## 目的

本切片验证 M3-S2 窗口分类器 no-fire plateau 是否来自两个实现合同：

- PPO actor loss 会通过 executable window-classifier event adapter 反传到窗口分类器头。
- 窗口分类器日志记录的是最后一次 auxiliary step 之前的 loss，而不是保存模型中的 post-update head。

## 修改

- `HierarchicalMoEExecutionPolicy` 新增
  `m3_window_classifier_event_adapter_detach`，active M3-S2 配置将其设为 `true`。
- executable adapter 仍使用 `m3_window_classifier_head` 设置 hold/fire logit 差值，
  但 PPO actor/action-log-prob 路径不再把该 supervised contract head 往 rollout hold
  动作方向训练。
- `_m3s2_window_classifier_auxiliary_update()` 现在会在 step 后重评估 classifier loss，
  保留 auxiliary batch 上最优的 classifier 参数，结束时恢复最优参数，并记录恢复后的
  post-update 指标。

## 聚焦验证

```bash
./.venv/bin/python -m py_compile \
  python/rl/policy_algo/ppo_adaptive_kl.py \
  python/rl/policy_algo/policies.py

./.venv/bin/python -m pytest \
  tests/hmoe/test_hmoe_policy.py -k "m3_window_classifier" -q

./.venv/bin/python -m pytest \
  tests/training/test_air_combat_active_training_entries.py -k m3s2 -q
```

结果：

- `4 passed, 39 deselected`
- `1 passed, 15 deselected`

## 短训证据

Run：

```text
experiments_tmp/m3s2_window_classifier_best_restore_8k_20260606_r1
```

命令：

```bash
env PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name m3s2_window_classifier_best_restore_8k_20260606_r1
```

最终训练关键指标：

| Metric | Value |
| --- | ---: |
| `m3s2/window_classifier_positive_logit_mean` | `1.39` |
| `m3s2/window_classifier_negative_logit_mean` | `-2.82` |
| `m3s2/window_classifier_accuracy` | `0.842` |
| `m3s2/window_classifier_replay_used` | `1` |
| `m3s2/boundary_cross_count` | `0` |
| `m3s2/event_logit_delta_mean` | `-1.22` |

由于日志现在是 post-restore 指标，这说明保存更新点上的训练/replay support 中，
classifier 确实能分离正负样本。

## Deterministic Probe

Artifact：

```text
experiments_tmp/m3s2_window_classifier_best_restore_8k_20260606_r1/m3s2_deterministic_probe.json
```

关键结果：

| Metric | Value |
| --- | ---: |
| `release_count` | `0` |
| `final_missiles` | `4` |
| `a7_quality_window_step_count` | `1080` |
| `policy_event_mode_fire_once_count` | `0` |
| `a7_quality_window_m3_window_classifier_logit_mean` | `-6.336187` |
| `a7_quality_window_m3_window_classifier_boundary_cross_count` | `0` |
| `a7_prewindow_m3_window_classifier_logit_mean` | `-6.782465` |

deterministic execution 仍不发射。

## Chain Probe

Artifact：

```text
experiments_tmp/m3s2_window_classifier_best_restore_8k_20260606_r1/m3s2_chain_breakpoint_probe_final_model_event_hold.json
```

固定 `model_event_hold` 结果：

| Head | Prewindow boundary | Quality boundary | Quality logit mean | Pass |
| --- | ---: | ---: | ---: | --- |
| current saved head | `0 / 800` | `0 / 1080` | `-6.339776` | no |
| direct trained raw head | `41 / 800` | `1080 / 1080` | `1.576526` | no，仍有 prewindow positives |
| fresh standardized latent head | `0 / 800` | `1080 / 1080` | `9.599181` | yes |

Verdict 仍为：

```text
first_breakpoint = m3_head_optimization_conditioning
```

## 解释

actor-gradient isolation 与 post-update restore 是有效的工程修复，但没有根治行为。
它们排除了两个错误解释：

- saved head 不是单纯因为最后一个未记录 step 过冲而坏掉；
- actor loss 不再直接把 classifier adapter 往 hold 方向训练。

剩余失败是 training-support contract mismatch。classifier 能分离 auxiliary update
看到的 replay/training support，但同一个 saved head 在必须执行开火的 deterministic
`model_event_hold` execution support 上仍是全负。同一 execution latent 上的 fresh
standardized linear head 能完美分离，因此状态信号和 adapter 仍然存在。

## 结论

下一步不应继续调系数。根治方向应让窗口分类器在 execution-support distribution 本身上
训练或校准，或增加显式 fixed-support auxiliary calibration gate。在 deterministic execution
产生单次 quality-window pulse 前，M3-S2 行为仍保持 held。
