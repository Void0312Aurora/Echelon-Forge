# A7 执行断点分析

状态：`2026-06-05` 已完成为结构性根因证据；结论 held。

父级：[README.zh.md](README.zh.md)。

## 目的

`A7-EVC-Y` 已证明 cross-rollout first-event credit state 确实进入训练，但 learned
policy 仍在 deterministic 模式下选择 hold，并在 stochastic 模式中过早采样发射。本记录
通过同一个 post-X final model 的三类固定批次 probe 来隔离剩余断点：

- 在 no-release `hold` 轨迹上重建 labels；
- 离线只拟合 credit head；
- 离线拟合 event logits，并比较当前 A7 delta-align 目标与直接 label supervision。

## 固定批次

模型：

```text
experiments_tmp/a7_cross_rollout_state_32k_20260605_r1/final_model.zip
```

场景/配置：

```text
scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json
examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json
```

hold collector 固定批次使用 `1 x 2400` steps，seed `7`。

Label reconstruction：

| 指标 | 数值 |
| --- | ---: |
| steps | `2400` |
| fire-open steps | `1880` |
| launch-open steps | `1040` |
| accepted releases | `0` |
| active labels | `1880` |
| `prewindow` negatives | `840` |
| `legal_open_quality` positives | `1040` |
| mass-capped positive weight | `1.0` |
| mass-capped negative weight | `1.0` |

这排除了“当前主要故障是缺失 labels”。Post-X labels 存在，并且经过 per-window mass
cap 后正负权重平衡，符合预期 prewindow/quality 切分。

## 当前策略形状

在同一固定批次上，learned event head 几乎是平的：

| 切片 | Event delta mean | Fire probability mean | Credit advantage mean | Argmax fire fraction |
| --- | ---: | ---: | ---: | ---: |
| active | `-0.9792` | `0.2731` | `0.00415` | `0.0` |
| `legal_open_quality` | `-0.9774` | `0.2734` | `0.00421` | `0.0` |
| `prewindow` | `-0.9813` | `0.2726` | `0.00407` | `0.0` |

策略没有学到“quality window 前 hold，quality window 中 fire”。它学到的是到处都很小的
正 credit advantage，而真正决定 deterministic event-mode 的 event-logit delta 到处都小于
零。

## 离线 Credit Fit

使用同一模型/配置运行
`tools/diagnostics/event_credit_head_probe.py --mode offline_fit`，hold collector，`1 x 2400`
steps，只拟合 credit head `300` 步。

初始 credit advantage：

| 切片 | Advantage mean | Positive fraction |
| --- | ---: | ---: |
| `legal_open_quality` | `0.00421` | `1.0` |
| `prewindow` | `0.00407` | `0.925` |

只拟合 `hybrid_event_credit_head` 后：

| 切片 | Advantage mean | Positive fraction |
| --- | ---: | ---: |
| `legal_open_quality` | `0.16646` | `1.0` |
| `prewindow` | `-0.21944` | `0.527` |

Credit head 能在固定批次上向正确方向移动。因此剩余故障不只是“labels 不存在”或
“credit head 收不到梯度”。

## Event-Logit Fit

在同一固定批次上比较了两种 event-head-only 目标。

当前 A7 delta-align 目标：

```text
target_delta = (Q_fire_once - Q_hold).detach()
```

只训练 `hybrid_event_head` `300` 步后：

| 切片 | Event delta mean | Fire probability mean | Argmax fire fraction |
| --- | ---: | ---: | ---: |
| `legal_open_quality` | `0.00758` | `0.50190` | `0.996` |
| `prewindow` | `0.00403` | `0.50101` | `0.585` |

这个目标没有编码稳健的有符号决策边界。它一旦生效，会把 positive 和 negative window 都拉向
接近零的小 credit advantage。Deterministic selection 于是变成阈值偶然事件；prewindow rows
也会泄漏成 `fire_once`。

直接在 event logits 上做 label BCE，只训练 `hybrid_event_head`：

| 切片 | Event delta mean | Fire probability mean | Argmax fire fraction |
| --- | ---: | ---: | ---: |
| `legal_open_quality` | `0.18575` | `0.54630` | `1.0` |
| `prewindow` | `0.02402` | `0.50617` | `0.643` |

直接 labels 更强，但 frozen actor latent 加 event head 仍不足以压制双峰 negative set。

直接在 event logits 上做 label BCE，同时训练 `hybrid_event_head` 与
`mlp_extractor.policy_net`：

| 切片 | Event delta mean | Fire probability mean | Argmax fire fraction |
| --- | ---: | ---: | ---: |
| `legal_open_quality` | `1.25132` | `0.74852` | `0.891` |
| `prewindow` | `-9.43967` | `0.08289` | `0.017` |

这证明模型类本身能分离 timing windows，前提是 actor representation 收到直接的有符号
event-logit 训练信号。

## 结论

剩余根因是 A7 value-to-policy execution contract，而不是 missile damage、A3/A5
legality、label starvation 或基础模型容量。

具体失败链路是：

```text
labels -> credit head -> tiny detached advantage -> smooth-L1 event-logit delta
```

这条链太弱且目标不完整：

- `compute_first_event_credit_loss()` 把 event-logit delta 对齐到 detached credit
  advantage，而不是校准后的 label target 或 margin。
- Post-X learned model 中，prewindow 与 quality rows 的 credit advantage 都只有约
  `0.004`，所以 event-logit target 实际接近零。
- `a7_event_credit_delta_align_positive_only=true` 会在 credit head 变负后移除负标签压力；
  它保护 shadow rows，但也意味着普通 prewindow negatives 不会稳定地把 event logits 推到零下。
- 独立 credit-head update 使用 detached actor latents，因此它可以改善 credit head，却不会教会
  actor representation 学到 deterministic event-mode selection 所需的 timing discriminant。

如果把当前 alignment 强行加大，它倾向于在 prewindow 与 quality rows 上同时产生近阈值 firing。
如果保持当前弱度，deterministic mode 会继续 hold。这两种结果都与当前观测到的失败模式一致。

## 下一合同边界

下一步不应是另一轮 coefficient sweep，而应定义新的 event-policy training contract，满足：

- 对普通 legal-open quality positives 与 prewindow negatives 提供直接的有符号
  event-logit targets 或 margins；
- 为 event timing discriminant 提供受控的 actor-representation update lane，而不是只做
  detached-latent credit-head learning；
- A3/A5 masks 继续保持权威，不削弱 runtime legality；
- credit head 继续作为 value/diagnostic support，但不再作为 deterministic event-mode crossing
  的唯一教师。

一个合理的下一子项目候选是 calibrated event-logit margin distillation /
actor-timing representation update 的 A7 follow-on contract。
