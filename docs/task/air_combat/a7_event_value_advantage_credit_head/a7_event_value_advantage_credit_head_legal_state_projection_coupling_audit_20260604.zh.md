# A7 Legal-State Projection And Coupling Audit

状态：`2026-06-04`，`A7-EVC-K` 结构性审计通过；behavior 仍 held。

父级：[README.zh.md](README.zh.md)。英文权威版：
[a7_event_value_advantage_credit_head_legal_state_projection_coupling_audit_20260604.md](a7_event_value_advantage_credit_head_legal_state_projection_coupling_audit_20260604.md)。

## 问题

`A7-EVC-J` 已修复确认过的 label-censoring bug：early accepted stochastic episode
现在能暴露后续 `shadow_quality` positives。但修复后的短训仍没有学会 timing：

- deterministic probe：`0` releases，`1880` 个 open-mask steps，quality-window
  A7 advantage mean 约 `-0.902`；
- stochastic probe：在 steps `4`、`43`、`2` 产生 authorized one-shot releases；
- TensorBoard：`a7/event_credit_target_positive_frac` 上升到约 `0.60`，但
  `a7/event_credit_advantage_mean` 下降到约 `-0.96`。

K 的问题因此是：为什么 repaired positives 没有把 legal-open quality states 推向正的
`fire_once` advantage？

## 证据

### Label Mass

修复后的 stochastic probe 必须用 pre-step `policy_event_mask_fire_once` /
`event_action_mask_fire_once` 重构，这与 `AdaptiveKLPPO.collect_rollouts()`
行为一致。post-step `fire_mask` 在 accepted row 上已经关闭，不等价于训练标签面。

使用 repaired r1 stochastic CSV 与 A7 active config：

| Reconstruction | Active rows | Positive rows | Negative rows | Raw positive mass | Raw negative mass | Capped positive mass | Capped negative mass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| post-step `fire_mask` | `3` | `0` | `3` | `0.0` | `1.2` | `0.0` | `1.2` |
| pre-step event mask | `3286` | `3280` | `6` | `3280.0` | `4.2` | `3.0` | `3.0` |

pre-step reconstruction 正确暴露 J 修复：

| Source | Rows | Positive rows | Raw mass | Capped mass | Coupling |
| --- | ---: | ---: | ---: | ---: | --- |
| `prewindow` | `3` | `0` | `1.2` | `0.730159` | value + delta alignment |
| `early_accepted` | `3` | `0` | `3.0` | `2.269841` | value + delta alignment |
| `shadow_quality` | `3280` | `3280` | `3280.0` | `3.0` | value-only；排除出 delta alignment |

修复后的 deterministic probe：

| Source | Rows | Positive rows | Raw mass | Capped mass | Coupling |
| --- | ---: | ---: | ---: | ---: | --- |
| `prewindow` | `800` | `0` | `320.0` | `1.0` | value + delta alignment |
| `deadline` | `1080` | `1080` | `1080.0` | `1.0` | value + delta alignment |

这排除了“J 后仍无正例”作为当前 blocker，但也说明 row count 有误导性：数千个
shadow positives 经 window mass cap 后，总正质量只有 `3.0`。

### Policy-State Probe

修复后的 deterministic probe 有真实 legal-open quality states，但 credit sign 仍错误：

| State group | Count | Fire probability mean | Event advantage mean |
| --- | ---: | ---: | ---: |
| legal-open pre-quality | `800` | `0.2549` | `-0.9021` |
| legal-open quality | `1080` | `0.2553` | `-0.9018` |

修复后的 stochastic probe 早发射后主要产生 closed-mask shadow states：

| State group | Count | Fire mask open | Event advantage mean |
| --- | ---: | ---: | ---: |
| pre-accept open rows | `6` | `6` | 约 `-0.92` |
| post-release track-quality shadow rows | `3280` | `0` | 约 `-0.90` |

因此，修复后的正证据主要存在于 `FiredAssess` / closed-mask observations 上，而不是
policy 真正需要选择 `fire_once` 的 legal-open quality observations 上。

### Coupling Path

当前实现有意把 `shadow_quality` rows 排除出 delta alignment：

- value loss 在 mass caps 后训练所有 active rows 的 `Q_fire_once - Q_hold`；
- delta alignment 只训练 `source != shadow_quality` 的 event logits；
- 这避免非法 post-release closed-mask rows 直接训练合法 fire actions，是符合 A3/A5
  legality 边界的；
- 但这也意味着大多数 repaired positives 不能直接把 event logits 推向 `fire_once`。

因此，early stochastic trajectories 中剩余的直接 policy signal 是负的：
`prewindow` 与 `early_accepted` 会 delta-align，而 `shadow_quality` 只是 value-only。

## 诊断

J 后的 blocker 不是 label censoring，而是 projection and coupling。

`A7-EVC-J` 在 target stream 里创建了 counterfactual evidence，但这些证据挂在
post-release closed-mask states 上。实际 event policy 需要在 legal-open quality states
得到正信号。当前 A7 路径没有把 shadow evidence 投影到 legal-open decision surface 的机制：

```text
early stochastic fire
  -> environment enters FiredAssess
  -> later quality facts exist
  -> J labels those later rows as shadow_quality positive
  -> delta alignment skips them because fire is illegal there
  -> event policy sees mostly early negative delta targets
  -> legal-open quality states remain negative
```

这解释了已观察到的 scalar pattern：

- `target_positive_frac` 上升，因为许多 shadow rows 被激活；
- `event_credit_delta_align_loss` 变得很小，因为 shadow positives 不参与 alignment，
  non-shadow rows 已经是负向；
- `event_credit_advantage_mean` 仍为负，因为 closed-mask shadow states 上的 value
  learning 没有强制 legal-open quality states 变成正 advantage。

## 排除的主要原因

| Candidate | Result |
| --- | --- |
| A3/A5 runtime legality | 不是主要原因。修复后的 stochastic probe 保持 authorized one-shot discipline，且 zero unauthorized/repeat/budget violations。 |
| J 后仍无 positives | 不是主要原因。pre-step reconstruction 暴露了数千个 `shadow_quality` positive rows。 |
| HMoE redesign | 不升级。故障发生在 target projection / value-to-policy coupling，尚未到 hierarchy-attributable diagnosis。 |
| coefficient-only tuning | 不是根修复。它可以增加 value loss pressure，但不会创建 legal-open projection target 或安全的 positive delta alignment path。 |

## 下一合同方向

下一有界 slice 应为 `A7-EVC-L Legal-State Projection Contract`。在另一轮 learned-policy
run 前，需要先定义以下机制之一：

1. Projected-observation distillation：
   使用后续 contact/geometry facts，但恢复 legal first-shot C2/ROE mask semantics，
   为 `shadow_quality` rows 构造 counterfactual legal-open observation；随后在该 projected
   observation 上训练 positive value 与 policy coupling。

2. Sequence continuation value：
   把“现在 hold 会抵达 future quality”和“现在 fire 是好动作”分离，引入 continuation /
   event-time value target；用它训练 pre-window hold preference 与 legal quality fire
   preference，而不是把 closed-mask rows 当成 legal actions。

3. Split-head contract：
   保留 `shadow_quality` 作为 value-only survival/opportunity signal，但增加只在
   legal-open projected states 上接收 positive targets 的 fire-advantage head 或
   distillation anchor。

立即非目标：

- 不直接对 closed-mask `shadow_quality` rows 启用 delta alignment；
- 不削弱 A3/A5 masks 或 `FiredAssess` suppression；
- projection contract 前不再启动新的 32k training wave；
- 不从本证据释放 HMoE redesign 或 M2。

## Worker Packet

```md
status: pass；behavior held
touched files:
- docs/task/air_combat/a7_event_value_advantage_credit_head/a7_event_value_advantage_credit_head_legal_state_projection_coupling_audit_20260604.md
- docs/task/air_combat/a7_event_value_advantage_credit_head/a7_event_value_advantage_credit_head_legal_state_projection_coupling_audit_20260604.zh.md
commands/outcomes:
- repaired r1 CSV label-mass reconstruction -> shadow positives restored but value-only after caps
- repaired r1 probe state summary -> legal-open quality advantage remains negative
- TensorBoard scalar read -> positive fraction rises while advantage remains negative
remaining paths:
- `A7-EVC-L Legal-State Projection Contract`
behavior risks:
- coefficient-only training can keep reinforcing the same projection gap
- enabling delta alignment on closed-mask rows would violate the A3/A5 boundary
integration notes:
- `experiments_tmp` remains evidence only and must not be staged
- HMoE gap remains a watch item, not the active A7 blocker
```
