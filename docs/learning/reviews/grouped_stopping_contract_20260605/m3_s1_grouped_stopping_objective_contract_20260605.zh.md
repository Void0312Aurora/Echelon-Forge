# M3-S1 Grouped Stopping Objective Contract

状态：`2026-06-05` pass；P2 objective contract 已作为设计验收，implementation 现在由 P4
dispatch queue 承接。

父项目：[M3-S1 Censored Optimal-Stopping Timing Contract](README.zh.md)。

输入：

- [P1 Data/Censoring Contract](m3_s1_data_censoring_contract_20260605.zh.md)
- [M3 Model-Selection Synthesis](../optimal_stopping_model_selection_20260605/m3_model_selection_synthesis_20260605.md)
- [Architecture Boundary Map](m3_s1_model_architecture_boundary_map_20260605.zh.md)

## 决策

M3-S1 不从普通 shuffled PPO minibatches 计算 stopping objective。第一实现路线必须使用
grouped evidence carrier 和 rollout-level auxiliary pass，同时保持 base PPO minibatches
不变。

推荐第一实现形状：

```text
collect_rollouts()
  -> ordinary PPO rollout buffer
  -> M3S1 grouped timing evidence sidecar

train()
  -> base PPO minibatch loop unchanged
  -> M3S1 auxiliary grouped pass over complete windows/groups
```

如果出现内存压力，按 complete groups 分块，而不是按 random rows 分块。

## 数学对象

对每个 group `g`，有序 rows 为 `t = 1..T_g`：

```text
M_t       = legal executable stop mask
Q_t       = desirable quality-window indicator
z_t       = stop logit / boundary score
lambda_t  = M_t * sigmoid(z_t)
S_t       = product_{k < t} (1 - lambda_k)
p_t       = S_t * lambda_t
p_none    = S_{T_g + 1}
```

Grouped loss 必须在整个 group 上考虑 event mass：

```text
P_window = sum_{t: Q_t = 1} p_t
P_early  = sum_{t: Q_t = 0 and before first desirable row} p_t
```

默认 grouped objective：

```text
L_group =
  - log(P_window + eps)                 for groups with supported desirable window
  + alpha * max(0, P_early - rho)^2     early stop mass budget
  + beta  * censor_or_no_event_term
  + gamma * optional ranking/margin auxiliary
```

对 no-window groups：

```text
L_none = -log(p_none + eps)
```

对 early-event censored prefixes：

```text
L_prefix =
  -log(S_tau + eps)
  + alpha * max(0, P_before_tau - rho_prefix)^2
```

Early-event prefix loss 不为 unobserved suffix 创建标签。

## 必需承载结构

Grouped evidence carrier 必须在 `rollout_buffer.get()` 破坏 `(step, env)` layout 之前可用。

必需 group-level fields：

| Field | Meaning |
| --- | --- |
| `group_id` | loss pass 使用的唯一 group id。 |
| `episode_id` | cross-rollout/censor accounting 使用的 episode id。 |
| `route_source` | `on_policy`、`forced_hold_probe` 或后续支持 source。 |
| `row_indices` | group 内有序 row indices。 |
| `step_indices` | 有序 step indices。 |
| `env_indices` | 用于 row reconstruction 的 env slots。 |
| `legal_mask` | executable legal stop mask `M_t`。 |
| `quality_mask` | desirable window mask `Q_t`。 |
| `accepted_event` | executed first event indicator。 |
| `censoring_kind` | group censoring type。 |
| `censor_step` | censor boundary，若存在。 |
| `support_horizon` | 最后 observed support row。 |

可选 diagnostic fields：

- policy fire request；
- collection time event-logit delta；
- collection time fire probability；
- target range / track age / launch-window age；
- reward breakdown reference only，不拥有 target。

## Loss 集成规则

允许：

- 从 normal minibatches 计算 base PPO losses；
- 从 complete groups 或 complete-group chunks 计算 M3-S1 grouped loss；
- 对选中 group rows 的 current policy observations 反传 grouped loss；
- 独立于 A6/A7 legacy losses 记录 grouped diagnostics。

不允许：

- 用 `rollout_buffer.get(batch_size)` shuffled samples 计算 `P_window`、`P_early`、
  survival products 或 no-event mass；
- 把 random minibatch 中的 `window_id` 当作 full group 已存在的证明；
- 只在 minibatch fragments 上应用 group mass caps，然后宣称这是 grouped event-time objective；
- 没有显式 projection/source contract 时，从 closed-mask shadow rows 训练 executable event logits。

## 与 A6/A7 的关系

A6 hazard、A7 credit 与 A7 policy-margin losses 保持为 support/diagnostic branches：

- A6 row-wise BCE 可以保留为 legacy local signal。
- A7 `Q_fire_once - Q_hold` 可以保留为 ranking/value diagnostic。
- A7 event-policy margin 只有在输入 legal-open 或显式 projected evidence 时，才能支持
  boundary shaping。

M3-S1 的验收依赖 grouped survival/stopping metrics，而不是仅依赖 A6/A7 loss activity。

## 短训前必需诊断

任何 short learned run 被作为 evidence 前，必须记录：

- grouped active group count；
- grouped row count；
- groups with desirable window；
- groups with early-event censoring；
- mean/quantile `P_window`；
- mean/quantile `P_early`；
- no-event mass；
- deterministic boundary crossing step；
- boundary crossing relative to first desirable row；
- closed-mask executable-logit training count，期望为 `0`；
- one-shot legality count。

## 下一合同

P3 选择独立 survival/stopping head 作为 `z_t`，而不是现有 hybrid event-logit delta。
P3 还定义 deterministic deployment：

```text
stop iff M_t = 1 and z_t >= threshold
```

Implementation 已通过 `M3S1-P4 Minimal Integration`；grouped objective 仍必须限制在
complete groups 或 complete-group chunks 上。
