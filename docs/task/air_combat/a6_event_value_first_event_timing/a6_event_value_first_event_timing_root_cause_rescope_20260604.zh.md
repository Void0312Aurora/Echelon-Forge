# A6 根因分析与重新定界

状态：`2026-06-04` 根因分析完成；训练与 L 参数调节暂停。

父级：[README.zh.md](README.zh.md)。证据输入：
[launch-window short learned evidence](a6_event_value_first_event_timing_launch_window_short_learned_probe_20260604.zh.md)。

## 范围

本文解释为什么 A6 launch-window 路线在机制层面堵塞。它不追加新的短训，不改变
launch-window 权重，不释放 M2，也不修改 A3/A5 合法性约束。

当前根问题不是“下一个 L knob 调多少”，而是当前逐步 hazard objective 在 stochastic PPO
采样与吸收式首发事件下，是否能够表达我们想要的 first-event timing 行为。

## 证据快照

L 不是没有信号：

- `A6-EVT-K` 已证明，当专用 event-head lane 足够强时，event head 能跨过 deterministic
  argmax，但 release 坍缩到 authorization/contact 后的近立即 step-2 发射。
- `A6-EVT-L` 随后在 label builder 中把合法授权与 launch-window timing 分开。
- `A6-EVT-M` 改变了行为：deterministic probe 不再早发，但仍为 `0` requests；open-window
  event probability 达到 `34.6% / 35.0%`。
- Stochastic probe 仍然在每个 episode 采样出一次授权 release，步数为 `7`、`43`、`4`，
  且没有 rejected、violation、repeat 或 budget 问题。

Stochastic probe 直接显示了结构性 hazard 问题：

| Episode | Release step | Release 前 open steps | Release 前单步发射概率 | 累计早发概率 |
| ---: | ---: | ---: | --- | ---: |
| 0 | 7 | 5 | 约 `0.269` 到 `0.290` | `0.810` |
| 1 | 43 | 2 | 约 `0.334` | `0.556` |
| 2 | 4 | 3 | 约 `0.269` 到 `0.288` | `0.625` |

这些概率足以让 stochastic early release 变得很可能；但 deterministic argmax 仍然选择
`hold`，因为二元 `fire_once` 概率尚未跨过 `0.5`。

## 抽象模型

在 A3/A5 合法首发窗口内，定义：

- 状态 `s_t`：policy 可观察的 contact、range、track age、C2/ROE state 与 A5 event mask；
- 动作 `a_t in {hold, fire_once}`；
- stochastic event hazard `h_t = pi(fire_once | s_t)`；
- deterministic release rule：masked binary argmax 下，只有 `h_t > 0.5` 才会 fire；
- stochastic 首事件分布：

```text
P(T = t) = h_t * product_{k < t} (1 - h_k)
P(T < q) = 1 - product_{k < q} (1 - h_k)
```

其中 `q` 是第一个 quality-window step。

当前 A6 label 路径在观测到的 rollout 上训练逐步 BCE-style hazard target。若 stochastic
`fire_once` 在 quality window 前被 accepted，A5 state machine 会转入 `FiredAssess`；对于
first-event objective 来说，该 episode 后续的 quality window 不再被观测。

这造成 on-policy early-event censoring：

- 早发会得到 negative early-accepted label，但这个 label 只在早发已经终止 first-event
  window 后出现；
- 后续 quality-window positives 只会存在于足够“活到”窗口的 episode 中；
- 当 `h_t` 升到 `0.25` 到 `0.35` 区间，跨多个 open steps 的 stochastic survival to quality
  window 会迅速变低；
- deterministic evaluation 需要概率超过 `0.5`，但 stochastic collection 在远低于 `0.5`
  的单步概率下就能触发早发。

## 根因判定

blocker 是结构性的：当前 objective 是 on-policy 轨迹上的逐步 hazard label，而首个 accepted
release 是吸收事件。它能移动 event logits，但没有给 policy 提供“现在 hold，之后在更好窗口
fire”的反事实价值。

因此，当前失败主要不是：

- 训练步数不够；
- A6 labels 缺失；
- event-head gradient routing 缺失；
- A6-EVT-K 之后的原始 event-head learning rate；
- runtime 合法性失败，因为 A3/A5 发射纪律仍然保持。

真正冲突来自三类机制：

1. 逐步 stochastic hazard 累积会在 deterministic argmax 触发前就让早发变得很可能。
2. accepted 首事件会 censor 掉本应教学 delayed firing 的未来 quality-window evidence。
3. hazard BCE 没有为 `hold` 决策提供 option-level 或 action-conditional credit assignment。

因此，继续训练或微调 L weights 大概率只是在两个坏状态之间摆动：概率低于 argmax 但 stochastic
仍会早发，或者概率高过 argmax 后又坍缩回近立即发射。

## 重新定界决策

暂停额外 L 训练与 launch-window 参数调节。下一步 A6 机制应从 independent per-step labels
转向 counterfactual first-event objective。

建议下一契约：

`A6-EVT-O Counterfactual Event-Time Objective`

该契约应研究具备以下性质的机制：

- label 或 target distribution 不会被 on-policy early accepted release 摧毁；
- pre-window hold 相对 early fire 获得显式 credit；
- quality window 内 fire 获得集中的 event-time probability；
- stochastic collection 受到约束或校正，使早期 exploratory samples 不会抹掉全部后续 positives；
- diagnostics 衡量累计 pre-window fire probability，而不只看单步 `fire_once` probability；
- deterministic 与 stochastic acceptance gates 在同一个 first-event timing target 下评估。

候选实现方向：

1. Action-conditional event-value 或 advantage head：在 first-shot window 上估计 `Q_hold` 与
   `Q_fire_once`，给 pre-window hold advantage 与 quality-window fire advantage。
2. Event-time survival objective：训练首发时间分布，包括 survival to quality window 与
   quality window 内 fire likelihood，而不是独立逐步 BCE labels。
3. Counterfactual teacher labels：即使 sampled action 早发，也从 policy-observed contact/ROE
   state 派生 quality-window target，避免 early stochastic censoring 删除未来目标。
4. Training-only exploration constraint：collection 期间抑制或重权重 pre-window stochastic
   `fire_once` samples，同时保持 A3/A5 runtime legality 不变。这只能作为辅助工具，不能替代
   value credit。

## 验收影响

A6 继续 held。未来可验收切片不能只证明“event probability 移动”：

- deterministic probing 在配置的 quality window 内执行一次授权首发；
- stochastic probing 不再积累高 pre-window release probability；
- per-episode release count、unauthorized release count、repeat count 与 shot-budget violations
  继续为零；
- 累计 pre-window early-fire probability 被报告并有界；
- A3/A5 masks 与 state-machine suppression 继续是合法性权威；
- M2、missile physics、Pk、fuze、damage authority、`2v2`、self-play 与真实 doctrine claims
  继续 out of scope。

## 下一工作包

在任何进一步 implementation 或 training 前，先创建 `A6-EVT-O` design-first packet：

```md
cluster: A6-EVT-O Counterfactual Event-Time Objective
scope: objective contract and focused prototype plan
write set: A6 objective/contract docs first; code/config only after contract review
non-goals: L knob tuning, M2 release, runtime legality changes, missile authority
validation: mathematical review, focused label tests, cumulative hazard diagnostics plan
return packet: selected mechanism, labels, losses, diagnostics, acceptance gate, rollback gate
```
