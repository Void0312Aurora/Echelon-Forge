# M3-S2 Boundary Dedicated Short Train - 2026-06-06

父级：[README.zh.md](README.zh.md)。

状态：`短训证据`；更新方向改善，但 deterministic 行为开火时机仍 held。

## 问题

在加入 deterministic quality-window boundary anchor，并把 M3-S2 auxiliary
optimizer 与 PPO Adam 状态隔离后，8k 短训是否改变 learned firing behavior？

## 运行

Scenario：

```text
scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json
```

Training config：

```text
examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json
```

Command：

```bash
env PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name m3s2_boundary_dedicated_8k_20260606_r2
```

Artifact：

```text
experiments_tmp/m3s2_boundary_dedicated_8k_20260606_r2/final_model.zip
```

第一次尝试 `m3s2_boundary_dedicated_8k_20260606_r1` 已进入训练，但在 logger dump
阶段失败：两个较长的 M3-S2 key 被 SB3 logger 截断到同名。缩短 M3-S2 log key
后，维护证据采用 `r2`。

## 训练信号

有 quality-window rows 的 logged batches 显示 boundary target 正沿预期方向移动：

| Timestep | `window_group_count` | `support_preserving_quality_count` | `m3s2/q_boundary_logit` | `boundary_cross_count` |
| ---: | ---: | ---: | ---: | ---: |
| `3072` | `4` | `924` | `-5.95` | `0` |
| `4096` | `4` | present | `-5.63` | `0` |
| `5120` | `4` | present | `-5.32` | `0` |
| `6144` | `4` | present | `-5.01` | `0` |
| `7168` | `4` | `324` | `-4.71` | `0` |

最终 logger dump 没有 quality rows，因此 quality-boundary statistic 为中性值；
它不能代表行为窗口。

## 行为 Probes

Deterministic probe：

```text
experiments_tmp/m3s2_boundary_dedicated_8k_20260606_r2/m3s2_deterministic_probe.json
```

| Metric | Value |
| --- | ---: |
| `termination_reason` | `combat_timeout` |
| `release_count` | `0` |
| `first_release_step` | `null` |
| `final_missiles` | `4` |
| `fire_mask_open_step_count` | `1880` |
| `a7_quality_window_step_count` | `1080` |
| `policy_event_prob_fire_once_max` | `0.004191798` |
| `policy_event_mode_fire_once_count` | `0` |
| `policy_m3_boundary_cross_count` | `0` |

Stochastic probe：

```text
experiments_tmp/m3s2_boundary_dedicated_8k_20260606_r2/m3s2_stochastic_probe.json
```

| Metric | Value |
| --- | ---: |
| `termination_reason` | `combat_timeout` |
| `release_count` | `1` |
| `first_release_step` | `623` |
| `final_missiles` | `3` |
| `fire_once_accepted_count` | `1` |
| `fire_once_rejected_count` | `0` |
| `a7_quality_window_step_count` | `109` |
| `policy_event_prob_fire_once_max` | `0.004182533` |
| `policy_event_mode_fire_once_count` | `0` |
| `policy_m3_boundary_cross_count` | `0` |

## 判定

短训确实改变了更新方向：在线 quality-boundary logit 在 supported batches 中单调抬升，
不再像先前真实 update path 一样与 prewindow logits 一起被压低。

但它还没有改变 deterministic learned behavior。确定性策略仍然选择 `hold`，
没有 event-boundary crossing，并且带着 4 枚导弹超时。随机策略能够采样到一次授权发射，
但最大 event probability 仍只有约 `0.42%`；这属于低概率采样，不是 learned deterministic
stopping boundary。

当前 verdict 仍为 held：

- dedicated optimizer 与 deterministic boundary anchor 修复了局部更新方向；
- 8k 训练不足以跨过 executable deterministic mode；
- 剩余问题仍是 event-boundary calibration / executable pulse transport，
  而不是环境不可达或缺少 support rows。
