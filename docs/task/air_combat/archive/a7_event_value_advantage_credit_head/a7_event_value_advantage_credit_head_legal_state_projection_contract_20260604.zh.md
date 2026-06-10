# A7 Legal-State Projection Contract

状态：`2026-06-04`，`A7-EVC-L` 已选择设计合同；本文档不启动实现。

父级：[README.zh.md](README.zh.md)。英文规范页：
[a7_event_value_advantage_credit_head_legal_state_projection_contract_20260604.md](a7_event_value_advantage_credit_head_legal_state_projection_contract_20260604.md)。

## 决策

`A7-EVC-K` 证明 J 后的 blocker 不是缺少 positive labels，而是 domain mismatch：

```text
shadow_quality positives 位于 post-release closed-mask observations
event policy 需要 legal-open observations 上的 positive fire_once credit
```

A7 因此不再把 raw `shadow_quality` rows 当作 closed state 上的直接 `fire_once`
advantage target。下一实现切片应把它们作为 legal-state projection path 的证据：

```text
raw shadow row o_t in FiredAssess
  -> 只把 A3/A5 legal-state fields 投影回 AuthorizedReady/open mask
  -> 保留 target/contact geometry 与 launch-quality facts
  -> 训练 A_event(project_legal_open(o_t)) 为 positive
  -> 只允许 projected legal-open sample 参与 delta alignment
```

这是保留合法性的 projection contract，不是让真实环境在 launch 后重新打开 fire
permission。

## 结构模型

当前 S1/A7 学习问题是带 absorbing first-event transition 的 MDP：

```text
s_t = (x_t, z_t)
x_t = target/contact/geometry facts
z_t = C2/ROE and A5 engagement state

fire_once 只有在 z_t 为 AuthorizedReady 且 fire mask open 时合法
quality 前 fire_once accepted -> z_{t+1...} 进入 FiredAssess
```

`A7-EVC-J` 从 `x_u` 恢复了后续 quality evidence，但它是在
`z_u = FiredAssess` 下观察到的。`fire_once` 的 policy update 只有在该动作合法的
状态上才有效。因此需要的对象是：

```text
Pi_legal(s_u) = (x_u, z_authorized_ready)
```

`Pi_legal` 是 auxiliary credit 的 feature-space training projection。它不是 runtime
state transition，不是 physics model，也不是 missile doctrine。

## Projection 白名单

对 `air_combat_c2_roe_v1` observations，projection 只能改写决定 A3/A5 event-action
legality surface 的字段：

| Field surface | Projection rule |
| --- | --- |
| `event_action_mask` | projected samples 上强制 `hold=1`、`fire_once=1`。 |
| `fire_mask` | 只在 projected samples 上强制 open。 |
| `mission[5]` WCS state | 设为与现有 mask reconstruction 一致的可开火值。 |
| `mission[6]` authorization | 设为 authorized。 |
| `mission[14]` engage-order state | 设为非 hold 的 engagement order。 |
| `mission[15]` shot-policy state | 设为正的 fire-permitted shot policy。 |
| `mission[16]` shot budget | projected first-shot decision 上至少保留一发。 |
| `mission[17]` pending assessment | 清除 pending assessment。 |
| `mission[19]` target contact | 只有 source row 已有有效 target/contact evidence 时才保留或强制 present。 |

Projection 必须保留 target/contact geometry、contact history、range、track-age facts
和无关 ownship state。它不能把 damage、missile outcome、post-launch success 或 hidden
future information 复制进 policy inputs。如果未来 observation layout 不能被这个白名单投影，
实现必须跳过 projection 并报告 unsupported layout，不能静默训练 closed-mask alignment。

## Loss 合同

下一实现应拆分三类信号：

| Signal | Source | Trains | Delta alignment |
| --- | --- | --- | --- |
| Legal negative | actual legal-open observations 上的 `prewindow`、`early_accepted` | `A_event(obs) < 0` | yes |
| Raw shadow opportunity | closed-mask observations 上的 `shadow_quality` | 可选 continuation/opportunity value only | no |
| Projected legal positive | `shadow_quality` rows 的 `project_legal_open(obs)` | `A_event(projected_obs) > 0` | yes |

核心 loss 变为：

```text
L_raw_negative =
  BCEWithLogits(A_event(obs), 0) on prewindow/early_accepted rows

L_projection_value =
  BCEWithLogits(A_event(Pi_legal(obs)), 1) on shadow_quality rows

L_projection_delta =
  SmoothL1(delta(Pi_legal(obs)), stop_gradient(clamp(A_event(Pi_legal(obs)))))
  or BCEWithLogits(delta(Pi_legal(obs)), 1)

L_A7L =
  a7_event_credit_value_coef * L_raw_negative
  + a7_event_credit_projection_value_coef * L_projection_value
  + a7_event_credit_projection_delta_align_coef * L_projection_delta
  + optional a7_event_credit_opportunity_coef * L_opportunity
```

Raw `shadow_quality` rows 不得在其 closed-mask observation 上进入 `L_delta`。如果实现保留
任何 raw shadow value term，应把它命名为 opportunity/continuation value，而不是直接
fire advantage。

## 实现切入点

后续 prototype 的预期写入面：

- 增加一个小型 projection helper，优先放在
  `python/rl/policy_algo/first_event_projection.py`。
- 扩展 `AdaptiveKLPPO._first_event_credit_loss()`，为
  `source == A6_FIRST_EVENT_SOURCE_SHADOW_QUALITY` 的 minibatch rows 构造 projected
  observations，并在 projected observations 上计算第二个 distribution。
- 扩展 `compute_first_event_credit_loss()`，或新增 sibling helper，分别报告 raw
  negatives、projected positives 与可选 opportunity value。
- 增加 projection value/delta coefficients 和显式
  `a7_event_credit_legal_projection_enabled` guard。
- 扩展 diagnostics，报告 projected active count、projected advantage mean、
  projected delta mean 与 unsupported projection count。
- Focused tests 覆盖 projection field rewrites、unsupported layout refusal、
  no closed-mask delta alignment，以及 positive projected delta pressure。

如果 projection 可从 `rollout_data.observations` 与现有 `source/window_id` 字段派生，
第一版实现不应要求 rollout-buffer schema changes。若事实证明不能做到，实现必须先记录缺失的
buffer contract，再扩展 buffer。

## 验证门

下一次 learned-policy training run 前：

```bash
python -m compileall -q python/rl/policy_algo/first_event_projection.py python/rl/policy_algo/first_event_hazard.py python/rl/policy_algo/ppo_adaptive_kl.py
pytest tests/policy/test_first_event_timing_contracts.py -q
pytest tests/policy/test_event_head_update_contracts.py tests/policy/test_auxiliary_training_updates.py -q
pytest tests/training/test_event_timing_training_config_contracts.py tests/training/test_diagnostics_callback_contracts.py -q
git diff --check -- docs/task/air_combat docs/task/issues python/rl/policy_algo tests/policy tests/training
```

这些 gate 后的第一次 learned-policy probe 应保持 short，并报告 deterministic timing、
stochastic timing、one-shot violations、raw shadow active count、projected legal active
count、projected advantage sign 与 projected delta sign。

## 非目标

- 不对 raw closed-mask `shadow_quality` rows 启用 delta alignment。
- 不削弱 A3/A5 masks 或 `FiredAssess` suppression。
- 不把 projection 当作 runtime fire permission re-opening。
- 不用本文档释放 HMoE redesign、M2、missile/Pk/fuze/damage authority、`2v2`、
  self-play 或 real doctrine。
- Projection prototype 通过 focused gates 前，不再启动新的 32k training wave。

## 分发结果

`A7-EVC-L` 选择 legal-state projection，并拆分 raw-shadow opportunity 与 projected
legal-open positive alignment。下一实现候选是
`A7-EVC-M Projected Legal-Open Credit Prototype`。
