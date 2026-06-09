# HMoE 层级化计算断裂

状态：`2026-06-04` 开放中；subexpert head 不接收 family-head 输出，且空战
C2/ROE 观测布局下五家族层级塌缩为单家族扁平结构。

首次观察：`2026-06-04`，A6 空战深度代码审查期间。

问题类别：架构设计 gap——参数组织和训练调度是层级化的，但前向计算图不是。

## 摘要

`HierarchicalMoEExecutionPolicy` 是空战和海军任务的主要执行层策略。它将计算
组织为三个层级：

- 共享 backbone（`action_net`）——基线策略均值；
- `_HMoEHeadBank`——五个 family head × 每 family (1–3) 个 subexpert head，
  作为共享均值的残差叠加；
- `hybrid_event_head`（A6-EVT-K）——masked `hold/fire_once` 决策的专用
  event-logit delta。

架构名称和 docstring 宣称 "explicit hierarchical semantic routing"，参数组织
（独立 LR scales、warmup 调度、残差初始化）也确实是层级化的。然而，两个结构性
gap 限制了层级化在前向计算中的实现程度：

1. Subexpert head 接收与 family head 相同的原始 `latent_pi`——它们无法访问
   family head 已经计算出的结果。
2. 空战 C2/ROE 布局（`mission_dim=20`）将每步硬路由到 `FAMILY_COMBAT_WEAPONS`，
   导致 S1 空战训练中 5 个 family 中的 4 个、12 个 subexpert 中的 9 个永不激活。

## 当前证据

### Gap 1：Subexpert 输入扁平

来自 `_HMoEHeadBank.forward`（[policies.py:86-110](../../../../python/rl/policy_algo/policies.py#L86-L110)）：

```python
family_out = family_head(family_latent)              # family 使用 latent_pi
residual[sub_mask] = sub_head(family_latent[sub_mask])  # subexpert 也使用 latent_pi
family_out = family_out + residual                   # 简单相加
```

Family head 和 subexpert head 接收**完全相同**的 `latent_pi` 张量。真正层级化
的计算应该将 family head 的输出（或其变换）送入 subexpert，使 subexpert 能
基于 family 已经做出的决策进行特化：

```python
# 真正层级化 forward 的样子：
family_out = family_head(latent_pi)
sub_input = concat([latent_pi, family_out.detach()])  # subexpert 看见 family 输出
residual = sub_head(sub_input)
```

后果：subexpert 无法学习 "family 想保持——我应该增强这个" vs "family 想开火
——我应该调节这个"。它必须仅从原始 latent 推断战术上下文，重复 family head
已经做过的工作。

### Gap 2：空战模式下的层级塌缩

来自 `route_from_mission_observation`（[hmoe_routing.py:133-167](../../../../python/rl/policy_algo/hmoe_routing.py#L133-L167)）：

```python
if _air_combat_c2_roe_layout(dim):       # dim == 20 → True
    family = FAMILY_COMBAT_WEAPONS        # 永远是 4
    # ... subexpert 路由 ...
    return HMoERouteBatch(...)            # 提前返回；所有其他 family 被跳过
```

当 mission observation 有 20 维（空战 C2/ROE 布局）时，路由器**立即**设置
`family = COMBAT_WEAPONS` 并返回。其他四个 family 的路由分支永远不会被评估。

当前 S1 空战训练中：

| Family | Head 数 | Subexpert 数 | S1 中激活？ |
| --- | --- | --- | --- |
| `takeoff_ground` (0) | 1 | 3（single / interval / wing） | 从不 |
| `departure_nav` (1) | 1 | 2（vector / route） | 从不 |
| `formation_cooperative` (2) | 1 | 3（generic / lead / wingman） | 从不 |
| `recovery_landing` (3) | 1 | 1（generic） | 从不 |
| `combat_weapons` (4) | 1 | 3（hold / first_shot / assess） | 总是 |

空战训练中的有效架构：**1 family × 3 subexpert**——一个扁平 3-expert 结构，
而非 5×n 层级化 MoE。

这不是路由 bug——C2/ROE 布局确实只描述战斗阶段。但这意味着 HMoE 的"层级化"
特性在最关键的场景（空战）中并未被使用，且其他四个 family 的参数在战斗训练中
接收不到任何梯度。

### Gap 3：确定性不可学习路由

路由使用基于 mission observation 向量的手写规则的硬赋值。没有学习的门控网络，
也没有专家的软混合：

```python
subexpert = th.where(authorized_first_shot, 1, subexpert)
subexpert = th.where(post_launch_assess, 2, subexpert)
```

虽然确定性路由稳定且可解释，但无法适应边界区域。在从 `weapons_hold` 过渡到
`authorized_first_shot` 时，活跃 subexpert 从索引 0 突变为索引 1。没有重叠，
没有渐进交接，且 `authorized_first_shot` 专家必须从零开始学习其策略，而无法
从 `weapons_hold` 专家的计算中获得任何信息。

### 哪些是真正层级化的（公平地说）

该设计并非没有层级——在三个重要维度上确实是层级化的：

1. **参数组织**：family head 和 subexpert head 是独立的 `nn.ModuleList` 结构，
   有清晰的语义分组。
2. **优化器 LR 尺度**：三级学习率（shared `1.0`、HMoE `0.35`、event-head
   `10.0`）创建了训练速度上的层级。
3. **残差 warmup**：`hmoe_residual_warmup_fraction=0.3` 和
   `hmoe_residual_start_factor=0.25` 安排 HMoE 贡献在前 30% 训练中从 25%
   线性增长到 100%，保持训练早期共享 backbone 占主导。

这些都是提升训练稳定性的真正架构决策。gap 在于**前向计算**未能匹配这种层级化
结构。

## 影响

- **空战训练浪费 HMoE 容量**：80% family head 和 75% subexpert head 永不激活。
- **Subexpert 特化受限**：无法访问 family-head 输出，subexpert 无法学习互补
  或调节性行为。
- **授权边界的硬路由**：从 `weapons_hold` 到 `authorized_first_shot` 的突变
  切换可能导致学习稳定 fire timing 的困难。`authorized_first_shot` 专家每次
  mask 打开时都从零知识开始。
- **不直接阻塞 A6**：event-head optimization lane（K）已证明 deterministic
  fire 可在这些 gap 存在的情况下训练。但这些 gap 可能限制策略学习细微时序
  行为的鲁棒性。

## A7 关系

A7
（[air-combat A7](../../air_combat/archive/a7_event_value_advantage_credit_head/README.zh.md)）
将本 issue 作为 head placement 与 diagnostics 约束：

- event-value / advantage-credit head 应作为 `hybrid_event_head` 的 policy-level sibling，
  而不是把唯一信号藏在一个 hard-routed combat subexpert 内；
- diagnostics 应同时报告 event-credit signs 与 HMoE route stats，以区分
  credit-learning failure 和 routing/capacity failure；
- 只有当 A7 学到正确 event-credit signs，但 policy coupling 仍以可归因于层级 gap
  的方式失败时，才把 HMoE repair 提升为活跃任务。

`A7-EVC-K/L` 现在显示当前 failure 仍发生在该升级门之前：修复后的 target builder 已恢复
shadow-quality positives，但它们主要位于 closed-mask rows，需要先完成 legal-state
projection 才能评估 policy coupling。因此本 issue 保持 watch item，而不是 active A7
blocker。

本 issue 不授权在 A7 内进行 HMoE redesign。

## 不能宣称

- 这不代表 HMoE 架构是坏的——它能正常工作并产出有效策略。
- 这不代表学习路由能解决 A6 标签失衡问题。
- 这不是从头重设计 HMoE 的呼吁——残差 warmup 和 LR 层级设计良好，应被保留。
- 这不是 M2 release 的投票。

## 假设

1. **主要**：将 family-head 输出送入 subexpert head 会创建真正的信息层级，
   让 subexpert 能相对 family 基线决策进行特化。
2. **次要**：空战模式层级塌缩是有意的（场景仅为战斗），但可通过允许 combat
   subexpert 的软混合而非授权边界处的硬路由来缓解。
3. **次要**：在确定性基础路由上添加小型学习路由残差会在不牺牲稳定性的前提下
   改善边界区域行为。
4. **辅助**：当前设计对于单阶段场景（如 S1 combat-only）是足够的。层级化在
   多阶段场景（takeoff → nav → combat → landing）中会变得更加重要。

## 相关领域上下文

- HMoE 路由：
  [python/rl/policy_algo/hmoe_routing.py](../../../../python/rl/policy_algo/hmoe_routing.py)
- 策略实现：
  [python/rl/policy_algo/policies.py](../../../../python/rl/policy_algo/policies.py)
- A6 子项目：
  [docs/task/air_combat/archive/a6_event_value_first_event_timing/README.zh.md](../../air_combat/archive/a6_event_value_first_event_timing/README.zh.md)
- M1 temporal-window HMoE：
  [docs/task/model/m1_temporal_window_hmoe/README.zh.md](../../model/m1_temporal_window_hmoe/README.zh.md)
- M2 causal Transformer HMoE：
  [docs/task/model/m2_causal_transformer_hmoe/README.zh.md](../../model/m2_causal_transformer_hmoe/README.zh.md)

## 下一步门槛

本 issue 是设计观察，非活跃实现阻塞项。推荐动作，按投入产出比排列：

1. **P0（低投入，高影响）**：将 family-head 输出送入 subexpert head。将
   subexpert 输入从 `[latent_pi]` 改为 `[latent_pi, family_out.detach()]`。
   需要将 subexpert `in_features` 从 `latent_dim` 增加到
   `latent_dim + action_dim`。HMoE head 的零初始化意味着此改动是向后兼容的——
   已有 checkpoint 需要扩展 subexpert 输入层（用零填充），新训练会立即使用
   层级化输入。
2. **P1（中投入，中影响）**：为 combat-weapons subexpert 添加软门控。替代
   硬路由到单个 subexpert，计算可学习的 softmax gate 覆盖所有三个 combat
   subexpert，并混合其输出。保留确定性路由作为 gate bias 或先验。
3. **P2（中投入，场景相关影响）**：在确定性基础路由上添加学习路由残差。这在
   多阶段场景（takeoff → nav → combat → landing）训练时变得重要。
4. **P3（仅观察）**：在训练期间追踪 HMoE family/subexpert 激活统计，量化
   容量利用情况。路由统计基础设施已在 `_update_route_stats` 中存在。

## 闭合验收标准

本 issue 可在以下任一条件满足时关闭：

- Subexpert head 接收 family-head 输出（Gap 1 已解决）。
- 有文档化的决策解释了为何当前扁平 subexpert 设计是故意的，并且对计划的场景
  覆盖是充分的。
- 多阶段场景训练证明五家族层级被使用且有用。

本 issue 不需要阻塞任何空战验收门——A6 标签失衡问题
（[../a6_launch_window_label_imbalance/README.zh.md](../a6_launch_window_label_imbalance/README.zh.md)）
是当前的活跃阻塞项。
