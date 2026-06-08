# A6 数学框架：受掩码约束的首事件时机

状态：`2026-06-03`，`A6-EVT-B Mathematical Framing` 的 P1 框架说明。

父级：[README.zh.md](README.zh.md)。输入：
[A6 observation](a6_event_value_first_event_timing_observation_20260603.zh.md)、
[A6 task clusters](a6_event_value_first_event_timing_task_clusters_20260603.zh.md)，以及 A5
[event contract](../a5_constrained_event_action_model/a5_constrained_event_action_model_event_contract_20260603.md)。

## 边界

本文只框定 S1 C2/ROE 的 `hold/fire_once` event surface。它不释放 M2，不改变导弹物理、
Pk、fuze、damage authority、stock-weapon authority、真实 doctrine、场景成熟度、`2v2`
或 self-play。它也不削弱 A3/A5 masks、发射后抑制、shot-budget handling 或
pending-assessment handling。

合法性仍是约束。A6 可以在合法 support 内加入 value、hazard 或 curriculum labels；它不能
通过 reward-only tuning 把未授权发射变成学习出来的偏好问题。

## 受约束 Semi-MDP 视角

在 policy step `t`，定义 policy-visible state：

```text
s_t = (o_t, e_t, c_t, b_t, h_t)
```

其中：

- `o_t` 是当前 reactive 或 M1 temporal observation window。
- `e_t` 是 A5 `engagement_state`，取值属于
  `{Hold, AuthorizedReady, FiredAssess, ReattackReady, Winchester}`。
- `c_t` 是 A5 mask components 向量，包括 C2 authorization、target presence、
  shot budget、pending-assessment suppression、weapon readiness、ammo availability 和
  reattack authorization。
- `b_t` 是 A3/A5 已暴露的剩余 shot-budget / ammo surface。
- `h_t` 是区分 not-yet-fired、fired-and-assess、显式 reopened reattack support 所需的
  event history。

最终发射 support bit 是：

```text
m_t = 1 if and only if A5 fire_mask is true
```

事件动作集合是：

```text
A = {hold, fire_once}
M_t = [1, m_t]
```

`hold` 始终合法。`fire_once` 只有在 `m_t = 1` 时合法。因此 masked policy 是：

```text
pi(a_t | s_t, M_t) over {hold, fire_once}, with pi(fire_once)=0 when m_t=0
```

这是一个受约束 semi-MDP，因为真正有意义的决策不是 raw per-frame threshold，而是在合法
event window 内的 stopping decision。在窗口内继续 `hold` 会推进时间，并在 support 仍开放时
保留选项。`fire_once` 会消费该事件并转入 `FiredAssess`；之后 A5 suppression 会移除
`fire_once` support，直到明确合法的 follow-on state 出现。

## Event Windows 与首事件

合法 first-shot window `W_k` 是一个最大连续区间：

```text
W_k = {t_start, ..., t_end}
where m_t = 1 and e_t = AuthorizedReady for all t in W_k
```

第一个 A6 contract 应以 `AuthorizedReady` 为主窗口。未来 contract 可以纳入
`ReattackReady`，但必须把它作为独立命名 window type，并配套独立 diagnostics；不能混淆
first-shot labels 与 reattack labels。

第一个 accepted event time 是：

```text
tau = min {t in W_k : fire_once_accepted_t = 1}
```

如果窗口关闭或 episode 结束前没有 accepted release，则该 window 是 censored：

```text
tau = censored
```

A6 应优化 mask 下的 `tau` timing，而不是 raw `fire_weapon` thresholding，也不是 illegal
action recovery。

## 可用 Label 来源

A5 diagnostics 已经能为 A6 提供 label material，而不需要把未 staged 的 artifacts 作为权威证据：

| Source field / summary | A6 use | Boundary |
| --- | --- | --- |
| `engagement_state` | 切分 `AuthorizedReady`、`FiredAssess` 和可能的 reattack windows。 | State name 定义 support，不是 doctrine label。 |
| `fire_mask` 与 mask components | 定义 legal support 和 censored / non-censored windows。 | mask-closed steps 不能成为 positive `fire_once` labels。 |
| `fire_once_requested` / `fire_once_accepted` | 区分 policy intent 与 accepted event。 | rejected requests 不是有效 positive labels。 |
| `fire_once_rejected_reason` | 诊断 impossible labels 与 contract mistakes。 | contract 不能学习强行克服这些 reason。 |
| `release_executed` / `authorized_release_count` | 标记 accepted first-event occurrence。 | 它们证明事件执行，不证明 missile outcome quality。 |
| violation、repeat、budget counts | 防止削弱 A3/A5 discipline。 | 这些是 safety diagnostics，不是 reward-only target。 |
| `policy_event_prob_fire_once_*` 与 mode counts | 衡量 logits 是否相对 A5 baseline 移动。 | 概率移动本身不是 acceptance；release 或 safety 退化时不能接受。 |
| A5 stochastic probes 保留的 release steps | 可作为 weak labels 或 curriculum seeds。 | stochastic timing 只证明 firing 可表达，不证明 optimal timing。 |

保留的 A5 observation 给出了必须超越的 baseline：deterministic 有 `1880` 个
fire-mask-open / `AuthorizedReady` steps、`0` 次 fire request，且 `fire_once` probability
接近零；stochastic probing 在 `3` 个 episodes 中产生 `3` 次 authorized release，且没有
violation、repeat 或 budget failures。

## 为什么 Deterministic Hold 是 Credit And Timing 问题

A5 已证明合法 event support 存在，stochastic exploration 也能 sample 到该事件。一旦 sample
并被 accepted，state machine 会消费事件并阻止不安全重复发射。因此 deterministic `hold` 不能
主要解释为缺少 action support 或缺少 legality。

失败点是 credit/timing：

- 有用事件可能在窗口打开数百步之后才发生。
- terminal 或 mission reward 相对 `hold/fire_once` logit update 是 delayed and sparse。
- 同一窗口里 `hold` 有大量合法 samples，普通 PPO update 容易让 "继续 hold" 成为 deterministic
  dominant mode。
- 偶发 stochastic `fire_once` sample 可以被 accepted，但其 advantage 未必能稳定地把价值分配到
  正确时刻的 masked event action。

A6 因此应给 event head 一个显式可学习的合法窗口内 stopping target。

## 候选 Objective Contracts

| Candidate | Target | How it affects logits | Strength | Main risk |
| --- | --- | --- | --- | --- |
| Event-value head | 学习 `Q_event(s_t, hold)` 与 `Q_event(s_t, fire_once)`，或 `m_t=1` window 内的 advantage delta。 | 用 action-conditional event value bias 或 supervise event head。 | 直接处理 mask 下 `hold` versus `fire_once` 的 value。 | 需要谨慎 bootstrapping，不能在 censored / illegal steps 上发明 value。 |
| First-event hazard objective | 在合法窗口上学习 `h_t = P(tau=t | tau>=t, s_t, m_t=1)`。 | 加入 masked binary / time-to-event loss，让 fire probability 靠近 labeled event times。 | 与 stopping-time data 和 censored windows 自然匹配。 | 如果 positive times 全来自 stochastic weak labels，label quality 会脆弱。 |
| Curriculum-assisted labels | 构造有边界的 positive labels，例如 "fire once within a legal window"，用于早期训练。 | 在 A5 masks 继续持有合法性的同时，临时提高 `fire_once` likelihood。 | 有助于摆脱接近零的 event probability，并生成数据。 | 如果不配合 event value 或 hazard，可能退化为模仿任意 timing rule。 |

对 `A6-EVT-C` 的推荐顺序：先选择一个 primary contract，再说明 curriculum 是否仅作为
bootstrap aid。长期可持久的 contract 应是 event-value 或 hazard；curriculum 只能作为有边界的
support，不能成为 correctness 的定义。

## 拒绝的 Labels

A6 必须拒绝以下 label sources 或 target definitions：

- 在 `fire_mask=0` 的任何 step 上给 positive `fire_once` label。
- 要求绕过 `FiredAssess`、pending-assessment suppression、shot-budget limits、ammo limits
  或 weapon readiness 的 labels。
- 来自 A5 之前 binary surface 的 raw `fire_weapon` threshold targets。
- 把 "总是在第一个 `AuthorizedReady` step fire" 当作最终 optimality claim。它最多只能作为有边界
  curriculum seed。
- 把 rejected fire requests 当作 successful labels。
- accepted S1 C2/ROE event contract 没有暴露的 missile hit、Pk、fuze、damage 或 weapon-physics
  labels。
- 真实 doctrine labels 或 tactical correctness claims。
- 用 reward-only legality penalties 作为让 illegal release 变得不吸引的机制。

## Failure Modes

A6-EVT-C 和后续实现必须防止：

- event logits 在 stochastic mode 下移动，但 deterministic argmax 仍是 `hold`。
- objective 没有应用 A5 mask，导致 `fire_once` probability 在 mask-closed steps 上升。
- objective 学到了 first-shot timing，却让 A5 no-repeat、no-budget-violation 或
  pending-assessment discipline 退化。
- curriculum labels 造成任意 early-fire habit，并且在移除 curriculum weight 后不能保留。
- hazard labels 把 censored windows 的每一步都当成 negative，从而压制合法 late firing。
- event value bootstrapping 把 terminal reward 泄漏到 illegal 或 post-launch states。
- reattack support 被意外合并进 first-shot support。
- diagnostics 报告 `release_executed`，但无法区分 requested、accepted、rejected、authorized、
  violation、repeat 和 budget outcomes。

## A6-EVT-C 必须回答的问题

`A6-EVT-C Objective Contract` 在 implementation 前必须准确回答：

1. primary contract 选择哪一个：event-value head、hazard objective、curriculum-assisted
   labels，还是 staged combination？
2. supervised 或 bootstrapped target 是什么？它的 loss 在哪些 masked window steps 上生效？
3. censored windows 如何表示：忽略、right-censored hazard examples、negative labels，还是
   bootstrapped value states？
4. rollout buffers、callbacks 和 process probes 需要哪些 A5 fields 来计算 target 与 diagnostics？
5. selected target 如何在 PPO 中耦合到 `hold/fire_once` logits，同时不替代 A5 masked
   categorical semantics？
6. 哪些 deterministic-eval metrics 必须相对 A5 baseline 移动：`fire_once` probability、mode
   count、request count、accepted release count，还是全部？
7. 如果 violations、repeat release、budget failures 或 rejected-fire reasons 退化，哪些 rollback
   criteria 保护 A3/A5 legality？
8. 是否使用 curriculum？如果使用，什么 schedule 会移除或约束它，避免它成为 acceptance claim？
9. `ReattackReady` windows 是从首个 contract 中排除，还是作为独立 window type 并使用独立 labels？
10. 哪些 focused tests 证明 mask handling、loss shape、finite stats、deterministic evaluation 和未改变的
    A5 suppression？

## Exit Statement

P1 将 A6 框定为受约束 semi-MDP 下的 masked first-event timing 问题。它不选择 implementation
contract。下一个 cluster 必须先选择 objective，并定义其 labels、masks、diagnostics、tests 与
rollback criteria，之后才能进行任何 code、config、scenario 或 training-kernel edits。
