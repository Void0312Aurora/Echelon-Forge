# M3-S2 Boundary Optimizer Contract Probe - 2026-06-06

父级：[README.zh.md](README.zh.md)。

状态：`方向修复证据`；不是行为验收。

## 问题

real update path probe 显示，M3-S2 update 能到达 executable event 参数，但会同时压低
prewindow 与 quality-window logits。本探针区分三个可能断点：

- 缺少直接的 quality-vs-prewindow 判别器；
- 缺少绝对 deterministic fire boundary 目标；
- auxiliary event-window update 复用了 PPO Adam 状态。

## 实现

代码变化：

- `compute_m3s1_grouped_stopping_loss` 现在支持：
  - `window_contrastive_margin_coef` 与 `window_contrastive_margin`；
  - `window_quality_boundary_coef` 与 `window_quality_boundary_logit`。
- M3-S2 `AdaptiveKLPPO` 现在记录：
  - `m3s2/q_pre_margin`；
  - `m3s2/q_pre_margin_loss`；
  - `m3s2/q_boundary_logit`；
  - `m3s2/q_boundary_loss`。
- M3-S2 可启用 `m3s2_event_window_dedicated_optimizer_enabled`，为 event-policy
  参数子集构建隔离 auxiliary optimizer，而不是复用 PPO Adam 状态。
- `tools/diagnostics/m3s2_real_update_path_probe.py` 支持 loss overrides 和
  `--reset-optimizer-state`，用于真实行更新对照。

active M3-S2 config 现在把 deterministic boundary 形成作为主合同：

```text
m3s2_event_window_quality_boundary_coef = 100.0
m3s2_event_window_quality_boundary_logit = 0.0
m3s2_event_window_contrastive_margin_coef = 2.0
m3s2_event_window_contrastive_margin = 2.0
m3s2_event_window_dedicated_optimizer_enabled = true
```

## 证据

所有 probes 使用同一个 support-preserving checkpoint 与 forced-hold 真实行采集：

```text
experiments_tmp/m3s2_support_preserve_8k_20260606_r2/final_model.zip
legal_rows = 1880
quality_rows = 1040
accepted_count = 0
```

| Probe artifact | 改动 | Optimizer state | Quality max delta | Loss delta | Verdict |
| --- | --- | --- | ---: | ---: | --- |
| `experiments_tmp/m3s2_real_update_path_probe_20260606_contrastive_4step.json` | active contract 增加 contrastive | reused | `-0.265431` | `-2.033103` | 仍压低 quality |
| `experiments_tmp/m3s2_real_update_path_probe_20260606_contrastive_window_only_4step.json` | 关闭 early/deadline/delay，仅保留 contrastive | reused | `-0.263480` | `-0.171080` | 仍压低 quality |
| `experiments_tmp/m3s2_real_update_path_probe_20260606_contrastive100_window_only_4step.json` | 高 contrastive only | reused | `-0.175797` | `-0.681381` | 相对 margin 改善，但绝对 boundary 仍下降 |
| `experiments_tmp/m3s2_real_update_path_probe_20260606_boundary100_window_only_4step.json` | 高 boundary anchor only | reused | `-0.052877` | `+5.247437` | update step 与当前 loss 反向 |
| `experiments_tmp/m3s2_real_update_path_probe_20260606_boundary100_window_only_resetopt_4step.json` | 高 boundary anchor only | reset | `+0.313639` | `-31.054993` | 真实参数路径可以抬高 quality |
| `experiments_tmp/m3s2_real_update_path_probe_20260606_final_config_dedicated_sim_4step.json` | final active config，用 reset 模拟 dedicated optimizer | reset | `+0.313624` | `-28.099365` | 更新方向修复 |

final probe 仍为 `quality_boundary_count = 0`：4 个离线步能把 quality logits 往正确方向推，
但从初始 quality max logit 约 `-5.72` 出发，尚未跨过 deterministic mode。

## 决策

失败不是单一 missing label，而是两个机制耦合：

1. grouped event-mass objective 是 stochastic window-probability contract。在很长的
   quality window 上，它可以通过降低 prewindow hazard，并在 quality rows 上分散小 hazard
   来改善目标。这不等价于 deterministic `fire_once` boundary。
2. M3-S2 auxiliary update 复用了 PPO Adam 状态。真实行 probe 中，该历史状态可以让一步更新与当前
   boundary loss 反向；清空 optimizer state 后，同一个 boundary-only update 从 quality-down
   变为 quality-up。

因此下一条 M3-S2 slice 应按 deterministic boundary contract + isolated auxiliary
optimization 验收。只有正式训练和 deterministic release probe 出现非零合法 release 后，才能称为
learned behavior。

## 验证

```bash
python -m compileall -q \
  python/rl/policy_algo/m3s1_grouped_stopping.py \
  python/rl/policy_algo/ppo_adaptive_kl.py \
  python/rl/support/nonfinite_probe.py \
  tools/diagnostics/m3s2_real_update_path_probe.py \
  tests/hmoe/test_m3s1_grouped_stopping.py \
  tests/hmoe/test_hmoe_ppo_warmup.py \
  tests/training/test_air_combat_active_training_entries.py
```

结果：pass。

```bash
python -m pytest \
  tests/hmoe/test_m3s1_grouped_stopping.py \
  tests/hmoe/test_hmoe_ppo_warmup.py \
  tests/training/test_air_combat_active_training_entries.py \
  tests/diagnostics/test_m3s2_real_update_path_probe.py -q
```

结果：`54 passed`。
