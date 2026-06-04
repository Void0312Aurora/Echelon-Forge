# A7 Event-Value / Advantage Credit Head

状态：`2026-06-04` active implementation subproject。A7 是 A6 root-cause re-scope
后的 follow-on：在继续 launch-window 调参前，实现 masked `hold/fire_once` 动作的
event-value / advantage-credit 机制。`A7-EVC-A/B` 已由 objective contract 关闭，
`A7-EVC-C` 已落地 zero-safe policy-head prototype，`A7-EVC-D` 已接入 focused
PPO auxiliary credit；active config、diagnostics callbacks 与 learned-policy
evidence 尚未完成。

语言：

- 英文权威版：[README.md](README.md)
- 中文伴随版：`README.zh.md`

输入：

- 父级空战任务：[../README.zh.md](../README.zh.md)
- A3 C2/ROE 发射纪律指针：
  [../a3_c2_roe_release_discipline/README.zh.md](../a3_c2_roe_release_discipline/README.zh.md)
- A5 受约束事件动作模型：
  [../a5_constrained_event_action_model/README.zh.md](../a5_constrained_event_action_model/README.zh.md)
- A6 event-value / first-event timing：
  [../a6_event_value_first_event_timing/README.zh.md](../a6_event_value_first_event_timing/README.zh.md)
- A6 根因分析：
  [../a6_event_value_first_event_timing/a6_event_value_first_event_timing_root_cause_rescope_20260604.zh.md](../a6_event_value_first_event_timing/a6_event_value_first_event_timing_root_cause_rescope_20260604.zh.md)
- HMoE 层级化计算断裂：
  [../../issues/hmoe_hierarchical_computation_gap/README.zh.md](../../issues/hmoe_hierarchical_computation_gap/README.zh.md)
- A6 发射窗口标签密度失衡：
  [../../issues/a6_launch_window_label_imbalance/README.zh.md](../../issues/a6_launch_window_label_imbalance/README.zh.md)
- 子项目创建标准：
  [../../../agent/rules/subproject_creation_standard.zh.md](../../../agent/rules/subproject_creation_standard.zh.md)

## 目的

A6 已证明 `hold/fire_once` event head 可以被训练，但逐步 hazard labels 没有解决
first-event timing。一旦 stochastic exploration 过早发射，A5 会进入 `FiredAssess`，后续
quality-window evidence 被 censor。缺失机制是“现在 hold，之后在更好窗口 fire”的反事实 credit。

A7 将该诊断转成实现线。核心对象是 event-value 或 advantage head，用来学习 A5 event mask 下
`fire_once` 与 `hold` 的有符号偏好：

```text
A_event(s_t) = Q_fire_once(s_t) - Q_hold(s_t)
```

policy event-logit delta 应与这个 advantage 对齐：pre-window 状态偏好 `hold`，
quality-window 状态偏好 `fire_once`，且早期 stochastic samples 不能删除本应奖励 hold 的未来目标。

## 当前状态

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| A3 合法性 | accepted；archived pointer | A3 evidence packet 已归档到 `archive/a3_c2_roe_release_discipline`，原路径保留指针。 | A3 持有合法发射纪律；A7 不得削弱 masks 或 state transitions。 |
| A5 event surface | held but usable input | `hold/fire_once` masked event action、post-launch suppression 与 stochastic one-shot discipline 已存在。 | A5 未解决 deterministic first-shot learning。 |
| A6 first-event labels | held after root-cause analysis | hazard/deadline/launch-window labels 是 live 的，但 L evidence 下 deterministic 为 `0` requests，stochastic early release risk 高。 | 进一步 L tuning 暂停。 |
| A6-N root cause | pass | 逐步 stochastic hazard 累积与 absorbing first-event censoring 解释 held outcome。 | 下一机制需要 counterfactual credit，而不只是 label weighting。 |
| HMoE gap | open issue | subexpert 不接收 family-head 输出，C2/ROE combat routing 塌缩到单 family。 | A7 必须考虑该风险，但本 slice 不重设计 HMoE。 |
| A7 objective contract | pass | [Objective contract](a7_event_value_advantage_credit_head_objective_contract_20260604.zh.md) 选择 counterfactual event-value head、window balancing、policy-logit coupling 与 cumulative hazard diagnostics。 | 这只授权 focused A7 prototype，不释放 M2、HMoE redesign 或 missile/doctrine authority。 |
| A7 policy head prototype | pass | `hybrid_event_credit_head` 暴露 `Q_hold`、`Q_fire_once` 与 event advantage，并覆盖 zero initialization、dedicated optimizer lane、default-disabled behavior、A6 coexistence tests 和 load smoke。 | A7-C 只暴露 credit；尚不训练该 head，也不把 credit 写回 event logits。 |
| A7 PPO auxiliary credit | pass | `compute_first_event_credit_loss()` 与 `AdaptiveKLPPO._first_event_credit_loss()` 训练 A7 head，可选对齐 event-logit delta，并在 A7-only coeff 下启用 first-event label collection；focused PPO/gradient tests 已通过。 | 不声明 active JSON config、callback diagnostics、learned evidence 或 A7 accepted。 |

## 范围

范围内：

- 为 masked `hold/fire_once` 定义 action-conditional event-value / advantage target。
- 增加有边界的 policy head 或 auxiliary head，估计 `Q_hold`、`Q_fire_once` 或其 advantage。
- 通过文档化 auxiliary loss 或 regularizer 将该 head 接到 event-logit delta。
- 保持 A3/A5 合法性 masks 与 post-launch state-machine suppression。
- 增加累计 pre-window hazard diagnostics：
  `P_early = 1 - product(1 - h_t)`。
- Adaptive label weighting 只作为辅助 guard，不作为核心机制。
- 纳入 HMoE issue 证据：A7 head 不应只依赖 hard-routed subexpert boundary 学习 hold/fire credit。

范围外：

- HMoE 层级化计算重设计、soft routing 或 M2 release。
- 导弹物理、Pk、fuze、damage authority、stock weapon authority、`2v2`、self-play 或真实 BVR doctrine。
- 通过削弱 A3/A5 masks 降低发射难度。
- 在 A7 objective contract accepted 前再跑 L-only training。

## 阶段计划

| 阶段 | 目标 | 进入条件 | 退出条件 | 状态 |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | 将 A7 冻结为 counterfactual event-credit 工作。 | A6-N root-cause note exists。 | README 和 task clusters 拒绝默认 L tuning 与 M2 release。 | pass |
| `P1 Evidence And HMoE Risk` | 对齐 A6-N、issue-board findings 与 policy code entry points。 | A7 exists。 | Objective contract 记录 HMoE gap 如何影响 head placement 与 diagnostics。 | pass |
| `P2 Objective Contract` | 选择 value/advantage targets、label sources、losses 与 rollback gates。 | P1 evidence accepted。 | Contract 足够具体，可进入实现。 | pass |
| `P3 Policy Head Prototype` | 增加有边界的 event-value / advantage head。 | P2 contract accepted。 | focused policy tests 覆盖 shape、initialization、serialization 与 event-logit coupling。 | pass |
| `P4 PPO Integration` | 训练该 head，并将 auxiliary credit 接入 PPO updates。 | P3 head available。 | loss、stats、finite behavior 与 mask handling 有测试覆盖。 | pass |
| `P5 Config And Diagnostics` | 增加 active config 与累计 hazard diagnostics。 | P4 integration passes。 | config 与 callback/process-probe tests 暴露 A7 metrics。 | planned next |
| `P6 Learned Evidence` | 运行短训 learned-policy probe。 | P5 tests pass。 | 记录 deterministic/stochastic timing、release counts 与累计 early hazard。 | planned |
| `P7 Closure` | accept、hold 或 re-scope A7。 | P6 evidence exists。 | parent/A6/issues docs 与证据一致，且无 overclaim。 | planned |

## 任务簇

- 任务簇计划：
  [a7_event_value_advantage_credit_head_task_clusters_20260604.zh.md](a7_event_value_advantage_credit_head_task_clusters_20260604.zh.md)
- 当前状态：
  [a7_event_value_advantage_credit_head_current_status_20260604.zh.md](a7_event_value_advantage_credit_head_current_status_20260604.zh.md)
- 分发队列：
  [a7_event_value_advantage_credit_head_dispatch_queue_20260604.zh.md](a7_event_value_advantage_credit_head_dispatch_queue_20260604.zh.md)
- 验收门：
  [a7_event_value_advantage_credit_head_acceptance_20260604.zh.md](a7_event_value_advantage_credit_head_acceptance_20260604.zh.md)
- Objective contract：
  [a7_event_value_advantage_credit_head_objective_contract_20260604.zh.md](a7_event_value_advantage_credit_head_objective_contract_20260604.zh.md)

## 输出与证据

当前输出：

- Event-value / advantage objective contract：
  [a7_event_value_advantage_credit_head_objective_contract_20260604.zh.md](a7_event_value_advantage_credit_head_objective_contract_20260604.zh.md)。
- Policy-head prototype：`python/rl/policy_algo/policies.py` 中的
  `hybrid_event_credit_head_lr_scale`、
  `HierarchicalMoEExecutionPolicy.get_hybrid_event_credit()` 与
  `_HybridActionDistribution.fire_event_q_values()` / `fire_event_advantage()`，
  由 `tests/hmoe/test_hmoe_policy.py` 覆盖。
- PPO auxiliary-credit coupling：`python/rl/policy_algo/first_event_hazard.py`
  中的 `compute_first_event_credit_loss()` 与
  `first_event_credit_batch_from_rollout_data()`，以及
  `python/rl/policy_algo/ppo_adaptive_kl.py` 中的
  `AdaptiveKLPPO._first_event_credit_loss()`，由
  `tests/hmoe/test_a6_event_head_update_strength.py` 和
  `tests/hmoe/test_hmoe_ppo_warmup.py` 覆盖。

计划 implementation 输出：

- 覆盖 loss masks、diagnostics 与 active config 的 focused tests。
- 与 A6-EVT-M 对照的短训 learned-policy evidence。

## 验收门

A7 只有在以下条件满足后才能 accepted：

- deterministic probing 在配置的 quality window 内执行一次授权首发；
- stochastic probing 不再积累高 pre-window release probability；
- A3/A5 one-shot discipline 保持：zero unauthorized releases、repeat releases 与 shot-budget violations；
- diagnostics 显示 event advantage 符号正确：pre-window `Q_hold > Q_fire_once`，
  quality window `Q_fire_once > Q_hold`；
- HMoE gap 对 A7 的影响要么证明不阻塞，要么作为独立 held architecture follow-on 记录；
- M2、missile authority、Pk/fuze/damage authority、`2v2`、self-play 与真实 doctrine 继续 held。

## 残余与下一步

- 立即下一步：分发 `A7-EVC-E Config And Diagnostics`，让 active entries 与
  callback/process-probe metrics 暴露新的 credit loss，再进入 learned-policy probe。
- Adaptive label weight scheduling 仍是 guardrail candidate，不是主要 repair。
- HMoE hierarchical computation 保持 issue-board item，除非 A7 evidence 证明它阻塞 advantage-credit learning。

## 归档

当前没有 A7 归档内容。历史 A7 记录只有在已有替代 current-status 或 closeout surface 后才移动到
[archive/README.zh.md](archive/README.zh.md)。
