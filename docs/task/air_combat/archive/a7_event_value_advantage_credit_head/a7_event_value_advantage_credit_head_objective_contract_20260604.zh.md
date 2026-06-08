# A7 Objective Contract

状态：`2026-06-04`，`A7-EVC-A/B` 的已选择实现合同；本文档不修改 policy/PPO code。

父级：[README.zh.md](README.zh.md)。英文规范页：
[a7_event_value_advantage_credit_head_objective_contract_20260604.md](a7_event_value_advantage_credit_head_objective_contract_20260604.md)。

## 决策

A7 将为 masked `hold/fire_once` event action 实现 action-conditional
event-value / advantage-credit head。选定机制为：

```text
A_event(s_t) = Q_fire_once(s_t) - Q_hold(s_t)
```

该 head 使用 counterfactual first-shot timing target 训练，并将 policy event-logit
delta 与学到的 event advantage 绑定。这不是 L-only label-weight tuning。Adaptive label
balancing 可作为 guardrail，但主要修复是 A3/A5 legal event surface 下的
counterfactual hold/fire credit。

## 证据输入

| 输入 | 合同含义 |
| --- | --- |
| A5 event action | `hold/fire_once`、event mask、`FiredAssess` 与 one-shot suppression 继续是 runtime authority。 |
| A6-EVT-K | 专用 event lane 足够强时，event decision 可以跨过 deterministic argmax。 |
| A6-EVT-L/M | Launch-window labels 能压制近立即 deterministic release，但也会把 deterministic fire 推回 crossing 以下。 |
| A6-EVT-N | Per-step stochastic hazard accumulation 加 absorbing first-event censoring 是机制 blocker。 |
| A6 label-density issue | Window-balanced credit 必须避免无界 pre-window negative mass。 |
| HMoE gap issue | A7 head 不能只依赖 hard-routed combat subexpert 来学习 hold/fire timing。 |

## Target 语义

A7 label builder 应从 rollout infos 和 policy observations 派生有边界的逐步 target：

| 术语 | 含义 |
| --- | --- |
| `legal_open_t` | A3 C2/ROE 状态下 A5 fire mask 打开。 |
| `quality_open_t` | A6 launch-window quality gate 打开，使用配置的 range、track-age 与最小 window-age 条件。 |
| `pre_quality_t` | `legal_open_t` 为真、`quality_open_t` 为假，且还未进入期望 quality window。 |
| `early_accepted_t` | `quality_open_t` 前 `fire_once` 被 accepted。 |
| `shadow_quality_reachable` | 即使 early accepted first event 关闭普通 fire mask，rollout 后续仍从 policy-observed contact/C2 facts 暴露 quality-window state。 |

Target sign：

```text
y_t = -1  for pre-quality hold credit
y_t = -1  for early accepted fire penalties
y_t = +1  for quality-window fire credit
```

该 value target 是相对偏好，不是真实导弹 doctrine 或 Pk target。`y_t=-1` 表示
`Q_hold > Q_fire_once`；`y_t=+1` 表示 `Q_fire_once > Q_hold`。

## Counterfactual Censoring 规则

A7 不得让过早 stochastic accepted release 删除所有后续正证据。第一版实现应增加 shadow
target pass：

- runtime A5 state machine 不变；
- ordinary `fire_once` acceptance 对环境合法性仍是 absorbing；
- early accepted release 后，如果 rollout 中仍能看到 contact/C2 facts，则继续从 policy-observed
  facts 派生 `quality_open_t`；
- shadow pass 显示 episode 本会到达 quality window 时，为 pre-quality states 分配 hold credit；
- 没有 shadow quality evidence 时，只分配较低置信 hold credit，而不是密集 full-weight negatives。

如果当前 rollout data 无法支持 shadow pass，`A7-EVC-D` 必须先记录 blocker，不能退回成
简单 L reweighting。

## Window Balancing

A7 必须按 first-shot window 归一化 target mass，而不是按原始 step count 累加。实现应约束每个
window 的正负权重：

```text
sum(w_negative_pre_quality in window) <= a7_event_credit_negative_mass_cap
sum(w_positive_quality in window) <= a7_event_credit_positive_mass_cap
```

这避免 A6-L 中“许多 legal-open pre-window negatives 压过稀少 quality-window positives”的失效模式。
Balancing guard 属于 A7，但它只是 credit head 的支持机制，不是主修复。

## Head Placement

第一版 A7 implementation 应在
[policies.py](../../../../../python/rl/policy_algo/policies.py) 中把 A7 head 作为
`hybrid_event_head` 的 policy-level sibling：

- 暴露 `Q_hold`、`Q_fire_once` 与 `A_event`；
- zero initialization，保证初始 policy 不变；
- 显式 optimizer group，或记录清楚其 optimizer membership；
- 读取 shared policy latent，必要时读取 post-HMoE hold/fire event logits；
- 不把唯一 A7 信号放入某个 hard-routed subexpert 内。

这种 placement 吸收了 HMoE hierarchical-computation gap 的风险，但不重设计 HMoE。除非 A7
evidence 显示 advantage signs 正确而 policy coupling 失败，否则 HMoE repair 仍作为 issue-board
follow-on。

## Loss 合同

实现应训练两个绑定 loss：

```text
A_value = Q_fire_once - Q_hold
target = 1 if y_t = +1 else 0

L_value = window_balanced_BCEWithLogits(A_value, target, active, weight)
L_delta = SmoothL1(event_logit_delta, stop_gradient(clamp(A_value, -c, c)))
          or confidence-gated BCEWithLogits(event_logit_delta, target)
L_A7 = a7_event_credit_value_coef * L_value
     + a7_event_credit_delta_align_coef * L_delta
```

`L_delta` 可选 `SmoothL1` distillation 或 confidence-gated BCE，但必须满足一条门槛：
advantage head 不能只是 diagnostic-only，它必须影响 event logits 或 PPO update。

## Diagnostics

A7 diagnostics 必须包含：

- pre-window 与 quality-window 下的 `Q_hold` mean；
- pre-window 与 quality-window 下的 `Q_fire_once` mean；
- pre-window 与 quality-window 下的 `A_event` sign fraction；
- 同窗口下的 policy `event_logit_delta`；
- 累计 pre-window stochastic release probability：

```text
P_early = 1 - product_t(1 - sigmoid(event_logit_delta_t))
```

learned-policy evidence 必须报告 deterministic release timing、stochastic first-release timing、
release counts、violation/repeat/budget counts、advantage signs 与 `P_early`。

## 实现切入点

后续 clusters 的预期写入面：

- `python/rl/policy_algo/policies.py`
- `python/rl/policy_algo/ppo_adaptive_kl.py`
- `python/rl/policy_algo/first_event_rollout_buffer.py`
- `python/rl/policy_algo/` 下新增或扩展 first-event credit helper
- `python/training/diagnostics.py`
- `python/training_callbacks.py`
- `tests/hmoe/`、`tests/training/`、`tests/diagnostics/` 下 focused tests
- active air-combat training config JSONs

`experiments_tmp` 只作为证据输出，不得 stage。

## 初始实现门

learned-policy probe 前，A7 implementation 必须通过以下 focused gates：

- zero initialization 与 constructor serialization；
- head output shape 与 finite values；
- event mask open/closed 下的 event-logit coupling；
- pre-quality、quality、early accepted 与 shadow-quality cases 的 A7 target labels；
- sparse positives 和 dense negatives 下的 window balancing；
- PPO loss plumbing 与 finite logs；
- cumulative pre-window hazard diagnostics；
- active config parsing。

## 回滚门

若出现以下情况，A7 必须 held 或 re-scope：

- A3/A5 masks 或 `FiredAssess` suppression 被削弱；
- head 变成 diagnostic-only；
- implementation 退化成 L-only weight tuning；
- deterministic probing 回到近立即 authorization/contact release；
- `A_event` signs 正确但 deterministic probing 仍不 fire；
- stochastic probing 累积高 `P_early` 或违反 one-shot discipline；
- 未建立独立 accepted issue task 就尝试 HMoE redesign。

## 分发结果

本文档关闭 `A7-EVC-A` 与 `A7-EVC-B`。`A7-EVC-C Policy Head Prototype` 已提供稳定的
`hybrid_event_credit_head` API，`A7-EVC-D PPO Auxiliary Credit` 已接入 focused PPO
loss；`A7-EVC-E Config And Diagnostics` 已提供 active entry 与 diagnostics
surface；`A7-EVC-F Focused Validation Sweep` 已通过，`A7-EVC-G Short Learned
Evidence` 已完成为 held outcome，`A7-EVC-I Target Construction And Credit Sign
Audit` 已将缺失 shadow-quality target repair 定位为下一实现阻塞点。`A7-EVC-J
Shadow Quality Target Repair` 随后修复 label-censoring 路径，但 learned behavior
仍 held。`A7-EVC-K Legal-State Projection And Coupling Audit` 随后证明剩余 blocker
是 projection/coupling，`A7-EVC-L Legal-State Projection Contract` 已选择 projected
legal-open credit 作为下一机制。当前可分发 cluster 是 `A7-EVC-M Projected Legal-Open
Credit Prototype`。
