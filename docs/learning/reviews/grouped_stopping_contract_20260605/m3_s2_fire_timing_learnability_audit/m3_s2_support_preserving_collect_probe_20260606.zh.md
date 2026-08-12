# M3-S2 支持保持采样探针 - 2026-06-06

父级：[README.zh.md](README.zh.md)。

状态：`partial repair evidence`；训练采样中的 support collapse 已修复，
但 learned deterministic fire timing 仍为 held。

## 问题

如果 stochastic rollout sampling 会在 quality window 前消耗 one-shot event，
能否通过 collection 阶段 forced hold 保住 M3-S2 的 quality-window rows，同时仍然训练
executable `fire_once` event logits？

本探针测试的是训练合同变化，不是 runtime C2/ROE 改动。support-preserving path 只改写训练
rollout actions；评估 probe 仍直接使用 learned policy，不加 shield。

## 实现

代码与配置：

- `python/rl/policy_algo/m3s1_grouped_stopping.py`
  - 增加 `early_survival_coef`，在既有 early-mass budget 之外，直接惩罚 prewindow
    survival loss；
  - 默认值为 `0.0`，所以既有 M3-S1 调用保持兼容。
- `python/rl/policy_algo/ppo_adaptive_kl.py`
  - 增加 M3-S2 support-preserving collection knobs；
  - 复用 A6 launch-window observation path 计算 legal-open 与 quality-ready masks；
  - 在 shield 下把训练 rollout 的动作索引 `9`（`fire_once`）强制为 `0.0`，并用当前
    distribution 重新计算 log-probability；
  - 将 hold/candidate/quality counts 作为一等 `m3s2/*` scalars 记录。
- `python/rl/support/nonfinite_probe.py`
  - 在 non-finite probe monkey patch 启用时，同步同一 support-preserving action rewrite
    与 logging。
- Active config：
  `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json`
  - `m3s2_event_window_early_survival_coef = 8.0`
  - `m3s2_event_window_support_preserving_collect_enabled = true`
  - `m3s2_event_window_support_preserving_hold_quality_enabled = true`

第一轮只在 quality window 前 forced hold。下面作为有效证据的第二轮在整个 legal-open collection
window 内 forced hold，从而避免 stochastic samples 在训练中擦除 quality-window rows。

## 验证

```bash
python -m compileall -q \
  python/rl/policy_algo/m3s1_grouped_stopping.py \
  python/rl/policy_algo/ppo_adaptive_kl.py \
  python/rl/support/nonfinite_probe.py \
  tests/policy/test_grouped_stopping_loss_contracts.py \
  tests/policy/test_auxiliary_training_updates.py
```

结果：pass。

```bash
pytest tests/policy/test_grouped_stopping_loss_contracts.py -q
pytest tests/policy/test_auxiliary_training_updates.py -q
pytest tests/training/test_air_combat_training_entry_contracts.py -q
```

结果：

- `10 passed`
- `24 passed`
- `16 passed`

focused coverage 包括：

- early-survival penalty 会惩罚高 prewindow mass；
- support-preserving masks 会在 quality ready 前 hold，并且在配置开启时延续到整个 legal-open
  window；
- active M3-S2 config 携带新的 support-preserving knobs。

## 短训

主要 artifact：

```text
experiments_tmp/m3s2_support_preserve_8k_20260606_r2/
```

训练支持对照：

| Run | Shield | Accepted events | Early-prefix groups | Window groups | Active groups | Closed rows | Boundary crosses |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `m3s2_event_window_8k_20260605_r2` | none | max `3`, final `0` | max `3` | max `1`, final `0` | final `0` | final `1024` | `0` |
| `m3s2_support_preserve_8k_20260606_r1` | pre-quality | max `2`, final `0` | max `1` | max `4`, final `0` | final `0` | final `1024` | `0` |
| `m3s2_support_preserve_8k_20260606_r2` | whole legal-open | `0` throughout | `0` throughout | max `4`, final `0` | min `4`, final `4` | max `4`, final `0` | `0` |

whole-window shield 改变了之前失败的 training-support 指标：

- 旧 event-window training 以 `grouped_active_group_count = 0` 和
  `closed_mask_row_count = 1024` 结束；
- whole-window support-preserving training 以 `grouped_active_group_count = 4`、
  `grouped_active_row_count = 1024` 和 `closed_mask_row_count = 0` 结束；
- shielded run 全程 `accepted_event_count = 0`，所以 collection 不再在 learner 看到
  supported rows 前烧掉 one-shot。

最终 update 的 `window_group_count = 0` 是因为该 rollout segment 只有 legal-open no-window
support，不是因为早发后状态机关闭了 `fire_mask`。

## Learned-Policy Probes

deterministic probe：

```text
experiments_tmp/m3s2_support_preserve_8k_20260606_r2/m3s2_deterministic_probe.json
```

| Metric | Value |
| --- | ---: |
| `release_count` | `0` |
| `fire_mask_open_step_count` | `1880` |
| `a7_prewindow_step_count` | `800` |
| `a7_quality_window_step_count` | `1080` |
| `policy_event_prob_fire_once_max` | `0.003296760` |
| `policy_event_mode_fire_once_count` | `0` |
| `a7_prewindow_event_fire_prob_mean` | `0.003266293` |
| `a7_prewindow_event_fire_prob_cum` | `0.927001125` |
| `a7_quality_window_event_fire_prob_mean` | `0.003259922` |
| `effects_event_count` | `0` |
| `damage_report_count` | `0` |

stochastic probe：

```text
experiments_tmp/m3s2_support_preserve_8k_20260606_r2/m3s2_stochastic_probe.json
```

| Metric | Value |
| --- | ---: |
| `release_count` | `1` |
| `first_release_step` | `61` |
| release 前 `a7_prewindow_step_count` | `56` |
| release 前 `a7_quality_window_step_count` | `0` |
| `a7_prewindow_event_fire_prob_cum` | `0.166411451` |
| `effects_event_count` | `0` |
| `damage_report_count` | `0` |

评估 probes 因此区分了两个问题：

- support-preserving collection 修复了训练数据 support collapse；
- learned policy 仍没有形成 deterministic `fire_once` pulse，并且 stochastic event
  probability 仍足以提前采样开火。

## 判定

本修复只作为 diagnostic/training-support repair 接受。它证明先前的 support-collapse
机制是真实的，并且可以在 collection 阶段被阻断。

它不是行为层面的开火时机解法：

- deterministic evaluation 在 `1080` 个 quality-window steps 下仍记录 `0` releases；
- 训练全过程 `boundary_cross_count` 仍为 `0`；
- prewindow cumulative event risk 仍比目标 `0.02` 高几个数量级；
- stochastic evaluation 仍可能在 quality window 前开火。

剩余根因现在更窄：actor/event training 能保住 rows，也能到达 executable logits，
但仍不能把 learned window target 传输成 deterministic low-high-low event pulse。下一切片应集中在
event-to-pulse adapter，或带显式 prewindow survival 与 quality-window crossing target 的更强
signed event-logit actor objective。除非 M2 memory 明确承担该 adapter，否则它应保持次级候选。
