# M3-S2 Single-Batch Window Signal Probe - 2026-06-06

父级：[README.zh.md](README.zh.md)。

状态：`根因证据`；观测与 frozen policy features 中存在窗口信号，但当前 M3-S2
executable-action 合同允许全局高电平坏解。

## 问题

boundary-dedicated 短训把 event logit 往上推了一些，但 deterministic release 仍为 0。
本 probe 提出一个更硬的诊断问题：

如果固定一批 forced-hold Stage-1 数据，其中同时包含 prewindow 与 quality-window rows，
当前 policy path 能否直接过拟合出正确的窗口划分？

## Batch

所有 probes 使用最新短训模型，并采集一个 forced-hold episode，从而不消耗 one-shot
event support：

```text
model = experiments_tmp/m3s2_boundary_dedicated_8k_20260606_r2/final_model.zip
steps = 2400
legal_rows = 1880
prewindow_rows = 840
quality_rows = 1040
accepted_count = 0
launch_min_age = 32
```

mission observation 中存在直接分离字段：

| Field | Prewindow | Quality window |
| --- | --- | --- |
| `launch_window_open` | 始终 `0` | 始终 `1` |
| `target_range_m` | mean `13127.2` | mean `19407.0` |
| `target_track_age_s` | mean `2.30833` | mean `1.35962` |

本 batch 中 `quality_window_ready`、`legal_open_age_steps` 与
`launch_window_age_steps` 仍为 0，因此当前维护划分实际依赖
`launch_window_open` 与 sidecar age rule，而不是这些显式 age fields。

## Probes

### Boundary-Only Overfit

Artifact：

```text
experiments_tmp/m3s2_single_batch_boundary_only_overfit_20260606.json
```

Overrides：

```text
quality_boundary_coef = 100
early_mass_coef = 0
no_event_coef = 0
delay_coef = 0
deadline_coef = 0
contrastive_margin_coef = 0
scope = current
update_steps = 120
learning_rate = 0.001
reset_optimizer_state = true
```

Result：

| Metric | Before | After |
| --- | ---: | ---: |
| `prewindow_boundary_count` | `0` | `840` |
| `quality_boundary_count` | `0` | `1040` |
| `prewindow_logit_mean` | `-5.477109` | `24.141708` |
| `quality_logit_mean` | `-5.477063` | `24.180077` |

这证明参数路径能跨过 deterministic boundary，但 boundary-only target 不是时机判别器。
它制造的是全程高电平 transport。

### Active-Contract Overfit

Artifact：

```text
experiments_tmp/m3s2_single_batch_active_contract_overfit_20260606.json
```

同一 batch，active config loss coefficients，`scope = current`、
`update_steps = 120`、`learning_rate = 0.001`，并重置 optimizer state。

Result：

| Metric | Before | After |
| --- | ---: | ---: |
| `prewindow_boundary_count` | `0` | `840` |
| `quality_boundary_count` | `0` | `1040` |
| `prewindow_logit_mean` | `-5.477109` | `20.376913` |
| `quality_logit_mean` | `-5.477063` | `20.474621` |

active contract 也进入全程高电平 transport。early-mass 与 contrastive terms
不足以在 strong boundary pressure 下让 supported batch 学出干净的
prewindow/quality split。

### Row-Wise BCE On Current Action Path

Artifacts：

```text
experiments_tmp/m3s2_single_batch_row_bce_capacity_20260606.json
experiments_tmp/m3s2_single_batch_row_bce_capacity_features_20260606.json
```

标签直接给出：legal prewindow rows 为 `0`，quality-window rows 为 `1`。

| Scope | Accuracy | Negative boundary count | Positive boundary count | Verdict |
| --- | ---: | ---: | ---: | --- |
| `current` | `0.553191` | `840 / 840` | `1040 / 1040` | majority-class all-positive |
| `current_plus_features` | `0.553191` | `840 / 840` | `1040 / 1040` | majority-class all-positive |

这不证明观测无信息。它证明当前 event/action transport path 会把直接标签吸收成全局 bias。

### Frozen Feature Signal

Artifact：

```text
experiments_tmp/m3s2_window_signal_feature_probe_20260606.json
```

在 frozen inputs 上训练独立 linear probe：

| Input | Accuracy | Negative boundary count | Positive boundary count |
| --- | ---: | ---: | ---: |
| raw mission fields (`launch_window_open`, range, track age) | `1.000000` | `0 / 840` | `1040 / 1040` |
| frozen extractor features | `1.000000` | `0 / 840` | `1040 / 1040` |
| frozen actor latent | `1.000000` | `0 / 840` | `1040 / 1040` |

这把失败从环境信号和 temporal feature extractor 中排除出去。actor latent 中已经存在
线性可分的窗口信号。

### Frozen-Latent Event Head

Artifact：

```text
experiments_tmp/m3s2_frozen_latent_event_head_balanced_bce_20260606.json
```

冻结 latent 与 base action delta 后，使用 balanced BCE 训练一个新 event head：

```text
accuracy = 0.944149
positive boundary = 1040 / 1040
negative boundary = 105 / 840
```

这还不是行为验收，但它说明隔离且校准的 event head 明显比当前 mixed action-delta
training path 更接近所需合同。

## 判定

当前失败不再适合描述为“模型看不到开火窗口”。固定 batch 中有直接分离的 mission fields，
frozen features/actor latent 也能让该划分线性可分。

失败对象是 executable event-logit training contract：

- quality-boundary anchor 是 existential positive-only 目标，最容易的解是抬高所有 legal logits；
- active grouped loss 在 strong boundary pressure 下仍允许 all-high solution；
- early-mass penalty 相对 boundary anchor 太弱，并且 hazard 饱和后可能变得无效；
- `fire_event_logit_delta` 不是独立 stopping head，而是 base `action_net` 与
  `hybrid_event_head` 调整后的 transport action 坐标差。

下一步修复应是模型合同变化，而不是继续加长训练：

1. 用 dedicated stopping/event head 训练校准 signed target；
2. 保留明确 prewindow negatives，最好采用 balanced BCE 或 hard cumulative-hazard constraint；
3. stopping head 跨过 deterministic threshold 后，再把 selected stopping boundary 转成
   executable low-high-low pulse；
4. 把当前 transport delta 当成 adapter output，而不是主学习对象。
