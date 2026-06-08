# A6 Objective Contract：受掩码约束的首事件 Hazard

状态：`2026-06-03`，`A6-EVT-C Objective Contract` 的 P2 contract。

父级框架：
[a6_event_value_first_event_timing_mathematical_framing_20260603.zh.md](a6_event_value_first_event_timing_mathematical_framing_20260603.zh.md)。
输入：
[A6 observation](a6_event_value_first_event_timing_observation_20260603.zh.md)、
[A6 acceptance gate](a6_event_value_first_event_timing_acceptance_20260603.zh.md)，以及 A5
[event contract](../a5_constrained_event_action_model/a5_constrained_event_action_model_event_contract_20260603.md)。

## 选择

第一个 A6 implementation contract 选择 masked first-event hazard auxiliary
objective，并配套一个有边界的 curriculum bootstrap；该 curriculum 必须在 learned-policy
probe 前衰减为零。

选定 primary objective：

```text
hazard_t = P(tau = t | tau >= t, s_t, fire_mask_t = 1)
```

其中 `tau` 是 `AuthorizedReady` first-shot window 内第一次 accepted `fire_once` 的时刻。
hazard 由现有 masked `hold/fire_once` event logit delta 表示：

```text
z_t = logit_fire_once_t - logit_hold_t
p_fire_t = sigmoid(z_t)
```

auxiliary loss 只在 active legal first-shot windows 上监督 `z_t`。它不替代 A5 masked
categorical distribution、PPO log-prob、entropy、sampling 或 deterministic argmax semantics。

## 拒绝的备选项

| Alternative | Decision | Reason |
| --- | --- | --- |
| 把 event-value head 作为第一个 contract | 本 slice 拒绝。 | 它是正确的长期候选，但在 hazard / label plumbing 被证明前，会引入新的 value surface 和 bootstrapping risk。 |
| curriculum-only labels | 拒绝。 | 有边界 curriculum 可以让 near-zero logits 脱困，但单独使用会把 correctness 定义成任意 timing rule。 |
| reward-only tuning | 拒绝。 | A3/A5 合法性由 mask/state 持有；reward-only legality tuning 已经没有让 deterministic fire，并且会再次混淆边界。 |
| M2 或 sequence-native objective | 拒绝。 | A6 必须先证明当前 masked event surface 可训练，之后才有 M2 release vote。 |

本 contract 有意选择最小 implementation surface：在已经存在的 event logit pair 上加 auxiliary
loss，直接移动 event timing。

## Active Window

loss 只在以下条件全部成立时 active：

- `engagement_state == AuthorizedReady`；
- `fire_mask == 1`，或 `event_action_mask[fire_once] == 1`；
- episode 尚未 accepted 第一次 `fire_once`；
- step 属于当前 first-shot window，而不是 reattack window；
- 必需 target fields 存在且 finite。

`ReattackReady` 从第一个 A6 contract 中排除。后续工作可以把它建模为独立 window type，但必须有独立
labels、diagnostics 和 acceptance criteria。

## Target Definition

对每个 first-shot window `W = {t_0, ..., t_n}`：

```text
accepted_tau = first t in W where fire_once_accepted_t = 1
```

自然 hazard labels：

- 如果存在 `accepted_tau`，则 active steps 中 `accepted_tau` 之前设 `target_t = 0`，
  `accepted_tau` 设 `target_accepted_tau = 1`，之后 steps inactive。
- 如果没有 accepted event，则该 window 作为 right-censored。默认情况下，right-censored windows
  不给 primary hazard loss 贡献 negative labels。
- rejected fire requests 永远不是 positive labels。
- mask-closed steps 永远 inactive，既不是 positive 也不是 negative labels。

primary auxiliary loss 是：

```text
L_hazard =
  mean(active_weight_t * BCEWithLogits(z_t, target_t))
```

其中 `active_weight_t` 在 active first-shot windows 外为零。D/E 以后可以加入一个很小的可配置
censored-survival weight，但本 contract 默认值是 `0.0`，避免把 near-zero deterministic fire
强化成 "正确地永不 fire"。

## Curriculum Bootstrap

curriculum 只作为有边界 bootstrap 使用。最终 learned-policy evidence 必须禁用它，除非 evidence
明确报告 curriculum 仍 active，因此该证据不具备 acceptance-grade。

Curriculum rule：

- 对 rollout 中没有 accepted event label 的 first-shot window，最多选择一个 seed step：

  ```text
  t_seed = first active step in W where window_age >= curriculum_min_window_age_steps
  ```

- 默认 `curriculum_min_window_age_steps` 应为 `32`。
- 如果该 window 少于 `32` 个 active steps，则不创建 seed。
- 设置 `target_t_seed = 1`；`t_seed` 之前的 active steps 可作为 survival negatives；
  后续 steps 对 curriculum label inactive。
- 每个 episode 最多创建一个 curriculum seed。
- 绝不在 `AuthorizedReady` 且 `fire_mask == 1` 之外创建 curriculum label。

Schedule：

```text
curriculum_coef = initial_curriculum_coef * linear_decay(completed_fraction, 0.0, 0.25)
```

该 coefficient 必须在训练完成前 `25%` 后精确为零，并且在 deterministic / stochastic evaluation
probes 中为零。hazard coefficient 可在训练中继续 active。

## Coupling To Event Logits

D 必须从现有 hybrid event head 暴露或计算 event logit delta：

```text
z_t = logit_fire_once_t - logit_hold_t
```

PPO action distribution 仍然是：

```text
event_dist = MaskedCategorical(logits=[logit_hold, logit_fire], mask=[1, fire_mask])
```

耦合规则：

- auxiliary hazard loss 反传到 masked categorical distribution 使用的 event logits。
- PPO policy loss、value loss、entropy、KL、sampling 和 deterministic eval 继续使用现有 masked
  categorical semantics。
- illegal `fire_once` 继续通过 A5 mask 保持 zero probability mass。
- 当 `a6_first_event_hazard_coef == 0`、没有 active legal first-shot steps，或必需 target fields
  缺失时，auxiliary loss 为零。
- implementation 不得增加并行 action path，也不得回到 raw `fire_weapon` threshold。

这与当前 feasibility surface 匹配：policy 已经为 action index `9` 构造 masked event categorical，
PPO 训练循环也已有 optional auxiliary loss term 的挂载模式。

## D/E 必需字段

Rollout 或 training-buffer fields：

| Field | Purpose |
| --- | --- |
| `a6_first_event_active` | `AuthorizedReady` first-shot legal steps 的 loss mask。 |
| `a6_first_event_target` | hazard 或 curriculum target，取值 `{0, 1}`。 |
| `a6_first_event_weight` | curriculum / censor handling 后的 per-step weight。 |
| `a6_first_event_source` | `accepted`、`curriculum`、`censored` 或 `inactive`。 |
| `a6_first_event_window_age` | 当前 first-shot window 内的 active-step age。 |
| `a6_first_event_window_id` | 用于 diagnostics 的 per-episode stable window identifier。 |
| `a6_first_event_had_accepted` | 该 window 是否已有 accepted event label。 |

Environment info / observation sources：

- `engagement_state`；
- `fire_mask` 或 `event_action_mask`；
- 可用时的 A5 mask components；
- `fire_once_requested`；
- `fire_once_accepted`；
- `fire_once_rejected_reason`；
- `release_executed`；
- `authorized_release_count`；
- `violation_release_count`；
- `repeat_release_before_assessment_count`；
- `shot_budget_violation_count`；
- `post_launch_suppressed`；
- `reattack_ready`；
- probe 用的 final missile count 与 release steps。

Policy/training diagnostics：

- `a6/hazard_loss`；
- `a6/hazard_coef`；
- `a6/curriculum_coef`；
- `a6/active_frac`；
- `a6/target_positive_frac`；
- `a6/curriculum_positive_count`；
- `a6/censored_window_count`；
- `a6/event_logit_delta_mean_open`；
- `a6/event_fire_prob_mean_open`；
- `a6/event_fire_prob_max_open`；
- deterministic 与 stochastic `policy_event_mode_fire_once_count`。

## 必须移动的 Deterministic Metrics

A5 baseline 是：

- deterministic：`1880` 个 fire-mask-open / `AuthorizedReady` steps，`0` requests，
  `0` releases，`policy_event_prob_fire_once_mean=0.217%`，max `0.278%`；
- stochastic：`3` 个 episodes 中 `3` 次 authorized releases，`0` violation release，
  `0` repeat release，`0` budget violation。

A6-EVT-F 应评估同类指标。本 contract 的目标是：

- primary success：deterministic probe 中 `policy_event_mode_fire_once_count > 0`、
  `fire_once_accepted_count >= 1`、`authorized_release_count >= 1`，并且
  `violation/repeat/budget = 0`；
- held-but-informative movement：如果 deterministic mode 仍为 `hold`，evidence note 必须报告
  open steps 上 `policy_event_prob_fire_once_mean` 是否至少达到 `2.0%`，或 max 是否至少达到
  `10.0%`，然后归属 blocker；
- stochastic discipline 必须在 comparable short probes 中至少保持 A5 的干净程度。

只有 probability movement 而没有 deterministic mode movement 不构成 acceptance；它只是下一轮 held
residual 的证据。

## D/E 必需测试

Training-kernel tests：

- coefficient 为零时 hazard loss 精确为零。
- mask-closed 或非 `AuthorizedReady` steps 上 hazard loss 精确为零。
- accepted-event labels 在 event logit delta 上产生 finite BCE loss 与 gradients。
- right-censored windows 不会默认生成 full-window negative labels。
- curriculum 每个 episode 最多创建一个 positive seed，且只在 `AuthorizedReady + fire_mask=1`
  steps 上创建。
- curriculum coefficient 在训练完成 `25%` 后衰减为零。
- auxiliary loss 不改变 masked categorical sampling、deterministic argmax、log-prob 或 entropy
  semantics。

Policy/distribution tests：

- `fire_mask=0` 仍强制 deterministic 和 stochastic support 为 `hold`。
- event logit delta / fire probability diagnostics 来自 masked categorical 使用的同一组 logits。
- 即使 hazard target data 格式错误，masked illegal `fire_once` 也没有 probability mass。

Config/diagnostics tests：

- active S1 C2/ROE config 可以启用 A6 hazard / curriculum knobs，且不重新引入 reward-only
  legality penalties。
- callback 在 active windows 存在时记录 finite `a6/*` diagnostics，在没有 active windows 时记录
  stable zeros。
- process probe 报告 requested、accepted、rejected、executed、authorized、violation、repeat、
  budget、mode 与 event probability fields。

Retained A5 discipline tests：

- `FiredAssess` 仍抑制 immediate repeat fire。
- shot-budget exhaustion 仍 mask `fire_once`。
- pending assessment 仍 mask `fire_once`。
- `ReattackReady` 不被 A6 labels 当作 first-shot window。

## Rollback Criteria

如果 focused tests 或 comparable short probes 中出现以下情况，A6 implementation 必须 rollback、
held 或 re-scope：

- 任何 `violation_release_count > 0`；
- 任何 `repeat_release_before_assessment_count > 0`；
- 任何 `shot_budget_violation_count > 0`；
- 由于绕过 A5 mask/state support，而不是具名 runtime mismatch，导致 rejected/fire 行为增加；
- A6 驱动的 `fire_once` request 后出现 `masked_hold_only`、`hold_state`、`pending_assessment`、
  `shot_budget_empty`、`ammo_empty` 或 `reattack_not_authorized` rejected reasons；
- `weapon_not_ready` rejected requests 在 `3` 个 comparable episodes 中超过 A5 short stochastic
  baseline 的 `1` 次，并且没有有边界的 config/runtime explanation；
- stochastic probing 在同样 short probe shape 下不再保持有纪律的一次授权发射行为；
- deterministic policy 仍为 `0` requests，且 evidence note 没有显示 material probability/logit
  movement 或更强诊断。

## 边界

本 contract 不允许：

- M2 release 或 sequence-native PPO implementation；
- 导弹物理、Pk、fuze、damage authority 或 stock-weapon authority 改动；
- 真实 doctrine 或 tactical correctness claims；
- broad reward-only legality tuning；
- 削弱 A3/A5 masks、state transitions、post-launch suppression、pending assessment、shot budget
  或 ammo constraints；
- raw `fire_weapon` threshold labels；
- 仅凭 stochastic one-shot behavior 宣告 deterministic acceptance。

## Unlock Statement

本 contract 只为这里定义的 masked first-event hazard objective 解锁 A6-EVT-D/E，并且必须保留有边界
curriculum bootstrap 与显式 diagnostics。它不接受 A6。learned-policy acceptance 仍需要 focused
tests，以及相对 retained A5 baseline 的短 deterministic / stochastic evidence。
