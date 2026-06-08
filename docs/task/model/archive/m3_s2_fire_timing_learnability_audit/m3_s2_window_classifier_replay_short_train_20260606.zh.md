# M3-S2 Window Classifier Replay Short Train

状态：`2026-06-06` 修复已测试；分类器在线 batch 指标有改善，但 learned fire timing 仍 held。

父项目：

- [M3-S2 Fire-Timing Learnability Audit](README.zh.md)

## 边界

本记录跟进 dedicated `m3_window_classifier_head` 集成后的修复。初始实现证明了分类头可以接线和局部训练，但在线 rollout chunk 经常只有单类或强不平衡样本。

本次假设是：

- 分类器辅助更新需要跨 rollout 的正/负平衡 replay；
- detached latent replay 可能随着 PPO actor 漂移而过期；
- observation replay 应该保存观测行，并在每次更新时用当前 actor 重新计算 latent。

本切片不声明行为验收，只判断 replay 是否修复分类器学习断点，以及是否传递到最终 deterministic/stochastic learned-policy probe。

## 实现

- `AdaptiveKLPPO` 新增 `m3s2_window_classifier_replay_*` 参数。
- replay 支持两种存储：
  - detached latent rows：`m3s2_window_classifier_replay_storage = "latent"`；
  - observation rows：`"observation"`，每次分类器更新时重新计算当前 actor latent。
- 当前 M3-S2 active config 使用 observation replay：
  - `m3s2_window_classifier_replay_enabled = true`；
  - `m3s2_window_classifier_replay_storage = "observation"`；
  - capacity `8192`，balanced batch size `1024`；
  - classifier update steps `64`，max grad norm `5.0`；
  - `m3_window_classifier_head_lr_scale = 100.0`。
- `air_combat_stage0_process_probe.py` 现在记录 `policy_m3_window_classifier_*` per-step 与 episode summary 字段。

## 验证

```bash
python -m compileall \
  python/rl/policy_algo/ppo_adaptive_kl.py \
  python/rl/policy_algo/policies.py \
  python/rl/support/nonfinite_probe.py \
  tools/diagnostics/air_combat_stage0_process_probe.py
```

```bash
pytest \
  tests/hmoe/test_hmoe_policy.py \
  tests/hmoe/test_hmoe_ppo_warmup.py \
  tests/training/test_air_combat_active_training_entries.py \
  tests/diagnostics/test_m3s2_chain_breakpoint_probe.py \
  -q
```

本轮重点结果：

- `tests/hmoe/test_hmoe_ppo_warmup.py`、`tests/training/test_air_combat_active_training_entries.py`、`tests/diagnostics/test_m3s2_chain_breakpoint_probe.py`：`46 passed`。
- observation replay 前的更广 HMoE/config sweep：`84 passed`。

## 短训 A：Latent Replay

run:

- `experiments_tmp/m3s2_window_classifier_replay_8k_20260606_r1`

训练中 replay batch 指标出现分离：

| Step | Replay used | Replay positives | Replay negatives | Positive logit mean | Negative logit mean |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2048 | 0 | 0 | 1024 | 0.00 | -11.7 |
| 3072 | 1 | 900 | 1140 | 2.27 | -1.68 |
| 4096 | 1 | 1800 | 1270 | 2.38 | -1.41 |
| 8192 | 1 | 3800 | 3360 | 2.67 | -2.20 |

但 saved-model deterministic probe 仍失败：

| Metric | Value |
| --- | ---: |
| `release_count` | 0 |
| `a7_quality_window_step_count` | 1080 |
| `a7_quality_window_m3_window_classifier_logit_mean` | -7.721 |
| `policy_m3_window_classifier_boundary_cross_count` | 0 |

诊断：latent replay 在训练时分开的是旧 actor latent，不会稳定传递到 probe 时的当前 actor 表征。

## 短训 B：Observation Replay

run:

- `experiments_tmp/m3s2_window_classifier_obs_replay_8k_20260606_r1`

训练中 observation replay batch 仍能分离：

| Step | Replay used | Storage is observation | Positive logit mean | Negative logit mean |
| ---: | ---: | ---: | ---: | ---: |
| 2048 | 0 | 1 | 0.00 | -11.7 |
| 3072 | 1 | 1 | 1.62 | -2.11 |
| 4096 | 1 | 1 | 1.98 | -2.98 |
| 6144 | 1 | 1 | 1.85 | -2.66 |
| 8192 | 1 | 1 | 1.60 | -3.06 |

Deterministic probe：

| Metric | Value |
| --- | ---: |
| `release_count` | 0 |
| `a7_quality_window_step_count` | 1080 |
| `a7_quality_window_m3_window_classifier_logit_mean` | -8.240 |
| `policy_m3_window_classifier_boundary_cross_count` | 0 |
| `policy_event_prob_fire_once_max` | 0.000655 |

Stochastic probe：

| Metric | Value |
| --- | ---: |
| `release_count` | 1 |
| `first_release_step` | 48 |
| `a7_quality_window_step_count` | 0 |
| `policy_m3_window_classifier_boundary_cross_count` | 0 |
| `a7_prewindow_m3_window_classifier_logit_mean` | -7.876 |

该 stochastic release 是 quality-window 出现前的早发采样，不是学会窗口。

## 诊断

Balanced replay 修复了一个局部问题：分类器在线更新可以看到两类样本，训练 batch 中正/负 logit 会分开。

但它没有修复行为策略：

- saved deterministic policy 在实际评估轨迹上仍把 classifier 和 fire event 都压在负侧；
- stochastic release 仍是低概率早发，不是 quality-window pulse；
- observation replay 减轻了 latent replay 过期问题，但没有消除训练 batch 和 saved-model rollout 之间的断裂。

当前断点可以写成：

```text
sidecar/replay batch 可以训练出分类边界
    -> saved actor/executable trajectory 没有保留这个边界
    -> fire event probability 仍极低
    -> deterministic policy 不发射
```

下一步不应继续只调 replay。更可能的方向是：

1. actor trunk drift / PPO overwrite 对分类头的冲刷；
2. legacy M3-S2 event-window/stopping losses 与 executable classifier adapter 互相竞争；
3. evaluation-like current trajectory 缺乏直接分类监督；
4. event/action distribution calibration，因为辅助 batch 看起来分离时，`fire_once` 仍然很低。
