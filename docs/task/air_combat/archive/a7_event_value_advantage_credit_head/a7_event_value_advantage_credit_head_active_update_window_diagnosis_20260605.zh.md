# A7 Active Update Window 诊断

状态：`2026-06-05` pass；根因定位到 rollout-local first-event credit assignment。
父级：[README.zh.md](README.zh.md)。

## 问题

`A7-EVC-V` 已经修复 online credit update lane：A7 value credit 通过
detached-latent、credit-head-only optimizer step 和独立 clip budget 更新。可是
8k observation 仍以 deterministic `0` releases 与略负的 legal-open credit
advantage 结束。W 要回答的问题是：剩余失败到底是 credit-head 容量、protected
update coupling、active label availability，还是更大的 training-loop contract。

## 证据

V 的 TensorBoard scalar review 显示 A7 labels 与 updates 只在训练早段 live：

| Train step | `a7/event_credit_active_count_mean` | Source pattern |
| --- | ---: | --- |
| `1024` | `174.0` | 主要是 `prewindow`，带 early accepted negatives |
| `1536` | `81.5` | 主要是 `prewindow` |
| `2048` | `64.0` | `LEGAL_OPEN_QUALITY` 短暂出现 |
| `2560` | `64.0` | `LEGAL_OPEN_QUALITY` 仍存在 |
| `3072` | `18.5` | active count 坍缩 |
| `3584` 到 `8192` | `0.0` | 没有 active A7 update samples |

Final deterministic fixed-batch probe 并不缺 labels：

```text
active labels: 2516
LEGAL_OPEN_QUALITY positives: 1356
accepted releases: 0
legal-open positive advantage mean: -0.0525766723
```

一个 stochastic final-model rollout 暴露了真正的 segmentation effect。同一条
512-step episode 在 step `6` 发生 accepted release，而第一个 launch-window open
state 在 step `282` 才出现。

如果按完整 512-step episode 构造 labels：

```text
active labels: 236
positive labels: 231
sources: prewindow=4, early_accepted=1, shadow_quality=231
```

如果按训练中的 `128` step rollout chunk 切开同一条轨迹：

| Chunk | Steps | Fire-open steps | Launch-window steps | Active labels | Positives | Sources |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | `1-128` | `5` | `0` | `5` | `0` | `prewindow=4`, `early_accepted=1` |
| 2 | `129-256` | `0` | `0` | `0` | `0` | none |
| 3 | `257-384` | `0` | `103` | `0` | `0` | none |
| 4 | `385-512` | `0` | `128` | `0` | `0` | none |

所以 positive shadow-quality evidence 在真实 episode 中存在，但当前 PPO
rollout-local label builder 看不到它。

## 诊断

当前 A7 label function 在 episode time 上不是局部函数，但实现却在每个 PPO rollout
segment 内局部求值。

令一条 episode trajectory 为：

```text
tau = (s_1, a_1, ..., s_T)
```

PPO 切片为：

```text
S_k = tau[t_k : t_k + n_steps)
```

目标 first-event credit label 是 episode-level function：

```text
y_t = L(tau, t)
```

因为后续 quality-window 状态上的 label 可以依赖更早的 accepted release。当前实现
实际计算的是：

```text
y_t' = L(S_k, t)
```

也就是只在当前 rollout buffer 内构造 label。只要 early accepted release 和后续
quality window 分别落在 rollout 边界两侧，`L(tau, t)` 和 `L(S_k, t)` 就不等价。

这正好解释 V 的观测：

- stochastic 采样在 quality window 前发生 early accepted release；
- 第一个 rollout chunk 只看到 negative prewindow / early-accepted labels；
- 后续 chunk 已进入 `FiredAssess` / pending-assessment，`fire_mask_open` 为 false；
- 后续 chunk 没有“上一 rollout 已发生 early accepted event”的记忆，因此
  shadow-quality repair 无法补出 positives；
- 当全部 vector env 都进入这个长 pending-assessment tail 后，A7 active samples
  坍缩为 0。

这也解释了为什么 final deterministic probe 仍能看到许多 legal-open windows：
deterministic mode 没有 early accepted release，因此 fire mask 保持 open，fixed-batch
probe 可以构造 legal-open positives。训练使用 stochastic on-policy sampling，采样到
早发后会把 episode 推入一个 rollout-local target 被删失的长段。

## 已排除解释

| Candidate | Current status | Evidence |
| --- | --- | --- |
| Credit-head capacity | 不像根因 | `A7-EVC-T` 证明 fixed-batch legal-open positives 只更新 credit head 即可拟合。 |
| Shared PPO global clipping | 已修复但不充分 | `A7-EVC-V` 已加入 protected credit-head-only update，且 active update lane 早段 live。 |
| 缺少显式 window state | 不充分 | `A7-EVC-S` 已暴露 `air_combat_c2_roe_v2` state completion，但 behavior 仍 held。 |
| 根本没有 positive legal-open labels | deterministic/fixed batch 中为 false | Final fixed-batch probe 有 `1356` 个 legal-open positives。 |
| HMoE hierarchy gap | 仍是 watch item | 正确 credit signs 学到以后它可能重要；当前失败在此之前已经表现为 rollout-local label censoring。 |

## 修复方向

长期修复应当是 cross-rollout first-event credit state contract，而不是再做一轮
coefficient sweep。

建议的 `A7-EVC-X` 合同：

- 在 PPO rollouts 之间维护 per-env first-event credit state：
  `episode_id`、first-window start、early accepted step、early accepted age
  和 pending shadow-quality status。
- 只在 `done` / episode id change 时 reset 该 state。
- 当 quality 前发生 early accepted release 时，为该 episode 记录 carried
  shadow-positive obligation。
- 在同 episode 的后续 rollouts 中，一旦 `launch_window_open` 与配置的 minimum
  quality age 到达，即使 `fire_mask_open` 已因 pending assessment 关闭，也要发出
  `SHADOW_QUALITY` positives。
- 增加 diagnostics：
  `a7/evc_carried_shadow_pending_envs`、
  `a7/evc_carried_shadow_positive_count_mean`、
  `a7/evc_cross_rollout_first_event_count_mean` 和 rollout age summaries。
- 增加 focused regression test：比较完整 episode labels 与 `128` step chunked
  labels，在 early-release-at-step-6、launch-window-at-step-282 的场景下应保持等价。

增大 `n_steps`、fixed positive replay batches 或 adaptive label scheduling 可能有助于
训练稳定，但不应被当作主修复。眼前的结构性错配是：supervised label function 有
episode memory，而训练实现目前在 rollout boundary 丢掉了这段 memory。

## 收口

`A7-EVC-W` 可作为诊断切片验收。剩余 blocker 现在命名为 training-loop contract
fault：

```text
rollout-local first-event labels are not equivalent to episode-level
first-event credit when early accepted release and later quality window cross a
rollout boundary.
```

下一有界行动是 `A7-EVC-X Cross-Rollout First-Event Credit State`。
