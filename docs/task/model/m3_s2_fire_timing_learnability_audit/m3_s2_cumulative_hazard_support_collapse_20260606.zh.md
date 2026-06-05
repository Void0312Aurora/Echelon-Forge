# M3-S2 累计风险与训练支持坍缩 - 2026-06-06

父级：[README.zh.md](README.zh.md)。

状态：`root-cause evidence`；support-preserving collection 确认了 support-collapse
机制并修复了 collection support，但 M3-S2 行为仍为 held。

## 问题

为什么 direct event-window supervision 已经到达 executable hybrid `fire_once`
event logits，并且产生了非零梯度，行为上仍然失败？

关键区别是每步概率与一次性事件的累计风险。对于每个 legal-open step 都会采样的一次性事件，
很小的每步开火概率 `p_t` 在很长 prewindow 中并不小：

```text
P(quality window 前提前开火) = 1 - product_t(1 - p_t)
```

如果 `p_t` 近似常数，则为：

```text
P_early = 1 - (1 - p)^n
```

## Probe 证据

Artifact：

```text
experiments_tmp/m3s2_event_window_8k_20260605_r2/
```

deterministic probe：

| Metric | Value |
| --- | ---: |
| `a7_prewindow_step_count` | `800` |
| `a7_prewindow_event_fire_prob_mean` | `0.005541579` |
| 计算得到的 `1 - (1 - p)^n` | `0.988269849` |
| 已记录的 `a7_prewindow_event_fire_prob_cum` | `0.988269851` |
| `a7_quality_window_step_count` | `1080` |
| `policy_event_prob_fire_once_max` | `0.005557978` |
| `policy_event_mode_fire_once_count` | `0` |
| `release_count` | `0` |

deterministic policy 不发射，是因为 `argmax(fire_once)` 从未跨过 event boundary。
但是同一组 logits 意味着 stochastic sampling 几乎必然会在 800 步 prewindow 中某处消耗
one-shot。

stochastic probe：

| Metric | Value |
| --- | ---: |
| release 前 `a7_prewindow_step_count` | `11` |
| `a7_prewindow_event_fire_prob_mean` | `0.005408502` |
| 计算得到的 `1 - (1 - p)^n` | `0.057910495` |
| 已记录的 `a7_prewindow_event_fire_prob_cum` | `0.057910509` |
| `first_release_step` | `14` |
| `release_count` | `1` |
| `a7_quality_window_step_count` | `0` |
| `effects_event_count` | `0` |
| `damage_report_count` | `0` |

因此 stochastic release 是 early low-probability sample，不是 learned quality-window fire。

## 训练轨迹证据

同一 run 的 TensorBoard scalars：

| Step | Accepted events | Early-prefix groups | Window groups | Active groups | Closed rows | Early mass | Window mass | Grad norm |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2048 | `3` | `3` | `0` | `4` | `4` | `0.223625` | `0.000000` | `7.566911` |
| 3072 | `0` | `0` | `1` | `1` | `768` | `0.058136` | `0.332401` | `21.615065` |
| 4096 | `0` | `0` | `1` | `1` | `768` | `0.074416` | `0.397732` | `20.607054` |
| 5120 | `1` | `0` | `1` | `1` | `768` | `0.105678` | `0.141995` | `22.187145` |
| 6144 | `0` | `0` | `0` | `0` | `1024` | `0.000000` | `0.000000` | `0.000000` |
| 7168 | `0` | `0` | `0` | `0` | `1024` | `0.000000` | `0.000000` | `0.000000` |
| 8192 | `0` | `0` | `0` | `0` | `1024` | `0.000000` | `0.000000` | `0.000000` |

这解释了表面矛盾：

- early stochastic samples 在 quality window 到来前消耗 one-shot event；
- runtime state 进入 `FiredAssess`，进而关闭 `fire_mask`；
- grouped sidecar 随后失去 supported quality-window rows；
- 后续 updates 变成 `active_group_count = 0`，所以即使 M3-S2 辅助路径接通，也没有有效
  训练支持。

## 严重性

当前 prewindow probability 只是在逐行分类意义下“小”。在 one-shot stopping 意义下它很大。

若要把 `800` 个 legal-open prewindow steps 的累计提前风险压到 `0.02` 以下，近似常数的每步概率
必须满足：

```text
p <= 1 - 0.98^(1 / 800) ~= 0.00002525
logit(p) ~= -10.59
```

deterministic executable event boundary 仍然要求 `fire_once` 击败 `hold`，也就是 quality
window 中 logit delta 大于 `0`。因此 learned policy 需要非常陡的跃迁：

```text
prewindow:      logit << -10
quality window: logit > 0
```

实测 M3-S2 logits 没有出现这种跃迁。3072 到 5120 updates 中，prewindow 与 quality-window
均值仍然贴近，约在 `-6` 到 `-5.6`。

## 根因判定

隐藏失败不是简单的“event head 没有梯度”。它是 training-support 与 event-transport 的不匹配：

- M3-S2 在 executable event logits 上优化 grouped event-mass objective；
- 同一个 stochastic policy 又被用于收集 on-policy trajectories；
- prewindow 每步约 `0.5%` 的概率已经足以在 quality-window evidence 被收集前毁掉多数 one-shot support；
- support 被毁后，状态机正确关闭 legal fire mask，但 learner 失去了用于锐化 boundary 的 positive rows。

当前 `early_mass_budget = 0.02` 语义上是对的，但现有 penalty 太弱，无法把每步 prewindow
hazard 压到所需的 `1 / horizon` 尺度。更重要的是，只靠系数调节并不稳健，因为同一个 sampled
policy 会擦除自己的监督样本。

## 对下一步的影响

下一切片应被视为 model/training contract repair，而不是继续做 coefficient sweep。

候选修复：

1. 增加 support-preserving training path：在 first quality window 前以 forced hold 收集或 replay
   quality-window groups，同时仍训练 executable event logits。
2. 增加 event-to-pulse adapter：先训练 stopping decision，再在 `fire_mask` 下确定性发出
   low-high-low executable pulse，避免把 stopping 直接暴露给逐步 Bernoulli sampling。
3. 强化 survival contract：直接约束并记录 prewindow cumulative hazard，而不是只使用很小的
   quadratic excess penalty。
4. 修复 reward ordering，但把它视为 timing quality 的必要条件，而不是 no-fire/early-sample
   support collapse 的充分解。

除非 M2 memory 明确负责 stopping-to-pulse adapter 或 support-preserving collection contract，
否则不应把 M2 作为主要修复释放。

## 后续修复证据

维护 follow-up：
[m3_s2_support_preserving_collect_probe_20260606.zh.md](m3_s2_support_preserving_collect_probe_20260606.zh.md)。

whole-window support-preserving collector 阻断了已诊断的 collection 失败：accepted rollout
events 保持为 `0`，active groups 持续存在，closed-mask rows 不再主导最终 update。这验证了
support-collapse 诊断。

行为失败仍然存在：修复后的 deterministic probing 在 `1080` 个 quality-window steps 下仍记录
`0` releases，并且 learned event logits 从未跨过 deterministic `fire_once` boundary。
