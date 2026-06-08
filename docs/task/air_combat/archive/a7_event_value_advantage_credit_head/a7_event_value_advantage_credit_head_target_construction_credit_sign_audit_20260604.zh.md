# A7 Target Construction And Credit Sign Audit

状态：`2026-06-04`，`A7-EVC-I` 审计通过；该修复需求随后已由
[A7-EVC-J Shadow Quality Target Repair](a7_event_value_advantage_credit_head_shadow_quality_repair_20260604.zh.md)
处理。

父级：[README.zh.md](README.zh.md)。英文权威版：
[a7_event_value_advantage_credit_head_target_construction_credit_sign_audit_20260604.md](a7_event_value_advantage_credit_head_target_construction_credit_sign_audit_20260604.md)。

## 问题

A7 r3 已证明 event-credit 路径可以训练，但 learned policy 仍然 held：

- deterministic probe 执行 `0` 次首发；
- stochastic probe 在 steps `14`、`47`、`2` 过早发射；
- A7 diagnostics 显示 quality window 内 event advantage 仍为负。

所以现在的问题不是再调一个系数或再跑一次短训，而是哪一个模型环节让
credit sign 学反了。

## 结论

主要结构性故障在 target construction。

A7 objective contract 要求 counterfactual shadow-quality evidence：一次 early
stochastic accepted release 不能抹掉后续本应奖励 holding 的 quality-window state。
但当前实现仍然通过 absorbing first-event state machine 构造标签：

- `AdaptiveKLPPO.collect_rollouts()` 先从 pre-step policy observation 采集
  `fire_mask` 与 launch-window facts，再从 `env.step()` infos 记录
  `fire_once_accepted`；
- `build_first_event_hazard_labels()` 只在
  `engagement_state == AuthorizedReady` 且 `fire_mask == true` 时打开 first-event
  label window；
- stochastic `fire_once` 如果在 quality 前被接受，label builder 会生成
  pre-window / early-accepted negative labels，并设置
  `episode_has_first_event = true`；
- absorbing first event 之后，后续 quality-window geometry 不再有资格变成 A7
  positive target。

因此 A7 不是因为 auxiliary head 训练不起来而失败，而是因为 auxiliary head 被训练在一个删失后的
label distribution 上；这个分布删除了 A7 原本必须保留的正样本。

## 代码证据

相关表面：

- `python/rl/policy_algo/ppo_adaptive_kl.py`
  - `_first_event_label_collection_enabled()` 在 A7 credit coeff 激活时正确启用
    label collection。
  - `_build_a6_first_event_labels_from_rollout_infos()` 将 A7-only runs 接入共用
    first-event label builder，并使用 A7 weights。
  - `collect_rollouts()` 在 step 环境前计算 `a6_policy_fire_mask` 与
    `a6_policy_launch_window`，然后记录 post-step accepted/rejected infos。
- `python/rl/policy_algo/first_event_hazard.py`
  - `build_first_event_hazard_labels()` 将 label window 定义为首个连续的
    `AuthorizedReady && fire_mask` segment。
  - quality 前的 early accepted release 会被显式转换为 negative labels，并关闭该
    episode 的 first-event path。
  - `compute_first_event_credit_loss()` 使用 `BCEWithLogits` 训练
    `Q_fire_once - Q_hold`；这更准确地说是 advantage-logit classifier，不是完整的
    two-action value target。作为 prototype 可以接受，但前提是标签语义正确。

这意味着当前 A7 implementation 没有满足 objective contract 中的
`shadow_quality_reachable` 规则。

## 重构标签证据

我按当前 A7 active config 从 r3 probe CSV 重构了标签：

- launch window：`8000m <= range <= 30000m`；
- maximum track age：`5s`；
- minimum window age：`32` steps；
- A7 pre-window hold weight：`0.4`；
- A7 early-accept weight：`1.0`；
- A7 deadline weight：`1.0`。

| Probe | Rows | Active labels | Positive labels | Negative labels | Positive weight | Negative weight | Sources |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| deterministic r3 | `2401` | `1880` | `1076` | `804` | `1076.0` | `321.600067` | `prewindow=804`, `deadline=1076` |
| stochastic r3 | `7203` | `19` | `0` | `19` | `0.0` | `9.3999996` | `prewindow=16`, `early_accepted=3` |

stochastic 的逐 episode 结果很关键：

| Episode | Accepted step | Active labels | Positive labels | Shadow quality states after accepted release |
| --- | ---: | ---: | ---: | ---: |
| `0` | `14` | `12` | `0` | `1080` |
| `1` | `47` | `6` | `0` | `1061` |
| `2` | `2` | `1` | `0` | `1081` |

每个 stochastic episode 在 early accepted release 后都物理进入了大量 quality-window states，
但当前 label builder 输出的 positives 是 `0`。event-credit head 于是被训练为：这些轨迹只提供负的
timing evidence。

## 模型层诊断

把当前问题抽象成 first-event decision process：

```text
state s_t includes contact/C2/geometry facts
action a_t in {hold, fire_once}
fire_once is absorbing for the first-shot event surface
quality(s_t) becomes true later in many trajectories
label y_t should express whether fire_once is better than hold at s_t
```

当前 supervised auxiliary target 会被 sampled action 内生影响：

```text
if a_tau = fire_once before quality:
    later quality(s_t) is removed from the target builder
    observed positives for the episode become zero
```

这不是普通的 sparse reward，而是 action-induced censoring of the supervised target。
一旦 stochastic exploration 采样出 early accepted shot，数据集只告诉模型
“quality 前 fire 是坏的”，却不告诉模型“hold 会抵达更好的 fire state”。随后 delta alignment 会忠实地把这个负号蒸馏进 event logits。

这解释了所有现象：

- deterministic argmax 不释放，因为 quality-window advantage 仍为负；
- stochastic sampling 仍可能早发射，因为非零概率质量仍存在；
- one-shot discipline 合法，因为 A3/A5 masks 是工作的；
- 继续 label-weight tuning 不能凭空创造被 target builder 删掉的反事实正样本。

## 排除的主要原因

| Candidate | Audit result |
| --- | --- |
| Runtime legality / C2/ROE | 不是主要原因。stochastic r3 releases 是 authorized one-shot releases，且没有 unauthorized、repeat 或 budget violations。 |
| A7 training path disabled | 不是主要原因。TensorBoard 有 live `a7/event_credit_loss`，focused PPO tests 也确认 credit head update path。 |
| HMoE hierarchy gap | 是 watch item，但不是本轮主要故障。错误符号在 A7 credit labels/advantages 上已经出现，还没到需要用 hierarchy-attributable policy coupling 解释的阶段。 |
| 只是系数太小或短训太短 | 不是主要原因。继续在同一删失标签上训练，只会强化同样的 sign bias。 |

## 修复方向

本审计派生出 `A7-EVC-J Shadow Quality Target Repair`，且该项随后已修复
label-censoring path。下面内容作为 J 已实现的 repair contract 保留。

必要方向：

- 保持 A3/A5 runtime masks 与 absorbing first-shot legality 不变；
- 将 runtime legal fire eligibility 与 target-side shadow quality observability 分离；
- 当 contact/C2/geometry 仍可观测时，采集 post-early-release quality facts；
- 将 shadow evidence 回填到 pre-release states，而不是训练非法的 post-release
  `fire_once` actions；
- 保留 window mass caps，避免修复后的 positives 引入新的 dense label imbalance；
- 增加 focused target-construction tests：
  - quality 前 early accepted，随后 shadow quality reachable；
  - quality 内 accepted fire；
  - no shadow quality reachable；
  - 同时存在 positive 与 negative target mass 时的 window mass caps。

关键设计点是：post-release quality state 是关于 counterfactual hold trajectory 的证据，
不是合法 post-release fire action。修复应为 pre-release decision timeline 生成 target credit，
而不是简单把 closed-mask post-release rows 标为 fire positives。

## 决定

`A7-EVC-I` 关闭本轮调查：失败环节是 counterfactual target construction，具体是 early
stochastic accepted release 后缺少 shadow-quality target repair。

`A7-EVC-J` 已修改并测试 target builder。它的 repaired 32k probe 仍为 behavior-held，
所以下一残余是 legal-state projection / policy-coupling 诊断，而不是原先的
label-censoring bug。
