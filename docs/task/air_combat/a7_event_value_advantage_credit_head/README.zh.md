# A7 Event-Value / Advantage Credit Head

状态：`2026-06-04` active implementation subproject。A7 是 A6 root-cause re-scope
后的 follow-on：在继续 launch-window 调参前，实现 masked `hold/fire_once` 动作的
event-value / advantage-credit 机制。`A7-EVC-A/B` 已由 objective contract 关闭，
`A7-EVC-C` 已落地 zero-safe policy-head prototype，`A7-EVC-D` 已接入 focused
PPO auxiliary credit；`A7-EVC-E` 已补上 active config 与 diagnostics surface，
`A7-EVC-F` 已通过 focused validation sweep；`A7-EVC-G` 已产出有效短训证据，
但 learned-policy outcome 继续 held。credit-training path 已恢复，launch-window
timing 尚未达到验收门。`A7-EVC-I` 已将 held outcome 追踪到 early stochastic
accepted release 后缺失 shadow-quality target repair。`A7-EVC-J` 已修复该
label-censoring 路径，并通过 focused tests 与 32k repair probe；但 learned-policy
outcome 仍 held：deterministic probing 仍为 `0` releases，stochastic probing
仍过早发射，quality-window advantage 仍为负。`A7-EVC-K` 已关闭 post-repair
结构审计：剩余 blocker 是 legal-state projection / value-to-policy coupling。
`A7-EVC-L` 已选择 projection contract，`A7-EVC-M` 已实现 projected legal-open
credit prototype 并通过 focused validation。M 后 learned-policy behavior 尚未评估。

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
| A7 PPO auxiliary credit | pass | `compute_first_event_credit_loss()` 与 `AdaptiveKLPPO._first_event_credit_loss()` 训练 A7 head，可选对齐 event-logit delta，并在 A7-only coeff 下启用 first-event label collection；focused PPO/gradient tests 已通过。 | 不声明 learned-policy。 |
| A7 config and diagnostics | pass | [Config and diagnostics evidence](a7_event_value_advantage_credit_head_config_diagnostics_20260604.md) 增加 A7 active config、callback event-credit/early-hazard metrics 与 process-probe summary metrics。 | 它本身不声明 learned-policy；G 已将 learned behavior 评估为 held。 |
| A7 focused validation | pass | [Focused validation sweep](a7_event_value_advantage_credit_head_focused_validation_sweep_20260604.md) 重跑 JSON、compileall、HMoE policy/PPO、config、callback、active-entry、process-probe 与 diff checks。 | 不声明 learned-policy。 |
| A7 short learned evidence | pass；held outcome | [Short learned evidence](a7_event_value_advantage_credit_head_short_learned_evidence_20260604.md) 在 nonfinite-probe 修复后验证 r3：`a7/event_credit_loss` 为 live，deterministic 仍为 `0` releases，stochastic release steps 为 `14`、`47`、`2`。 | A7 credit training 已生效，但 quality-window event advantage 仍为负，A7 不能 accepted。 |
| A7 target construction audit | pass；已由 J 修复 | [Target construction and credit-sign audit](a7_event_value_advantage_credit_head_target_construction_credit_sign_audit_20260604.zh.md) 重构当前标签：stochastic r3 只有 `19` 个 active labels、`0` 个 positives，而每个 episode 在 early release 后都有超过 `1000` 个 shadow quality states。 | 故障点是 target construction，不是 runtime legality、training path disabled 或 HMoE primary blocker；J 已修复该 censoring path。 |
| A7 shadow-quality target repair | pass；held outcome | [Shadow-quality repair](a7_event_value_advantage_credit_head_shadow_quality_repair_20260604.zh.md) 增加 post-early `shadow_quality` positives，保留 early-accepted negatives，将 shadow rows 排除出 delta alignment，并验证修复后的 active config。 | label-censoring bug 已修复，但 learned timing 仍未 accepted。下一问题是 repaired shadow credit 如何影响 legal-open quality states。 |
| A7 legal-state projection audit | pass；held outcome | [Legal-state projection and coupling audit](a7_event_value_advantage_credit_head_legal_state_projection_coupling_audit_20260604.zh.md) 证明 J 后 positives 存在，但主要位于 closed-mask `FiredAssess` observations；直接 policy alignment 仍由 legal-open negatives 主导。 | K 只是 docs/diagnostics evidence，不验收 A7，也不授权 closed-mask delta alignment。 |
| A7 legal-state projection contract | pass；已由 M 实现 | [Legal-state projection contract](a7_event_value_advantage_credit_head_legal_state_projection_contract_20260604.zh.md) 选择 projected legal-open credit：raw shadow rows 作为 projection/opportunity evidence，positive delta alignment 只允许在 projected legal-open observations 上发生。 | 合同不削弱 A3/A5 masks，且已作为 focused prototype 实现；仍不证明 learned-policy behavior。 |
| A7 projected legal-open credit prototype | pass；learned behavior not evaluated | [Projected legal-open credit prototype](a7_event_value_advantage_credit_head_projected_legal_open_credit_prototype_20260604.zh.md) 增加 `first_event_projection.py`、projection coeffs、PPO projected-distribution loss、projection metrics、active config knobs 与 focused tests。 | M 只证明机制与 focused gradient path；短训证据前 A7 继续 held。 |

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
| `P5 Config And Diagnostics` | 增加 active config 与累计 hazard diagnostics。 | P4 integration passes。 | config 与 callback/process-probe tests 暴露 A7 metrics。 | pass |
| `P6 Learned Evidence` | 运行短训 learned-policy probe。 | P5 tests pass 且 F validation sweep clean。 | 记录 deterministic/stochastic timing、release counts 与累计 early hazard。 | pass；held outcome |
| `P7 Closure` | accept、hold 或 re-scope A7。 | P6 evidence exists。 | parent/A6/issues docs 与证据一致，且无 overclaim。 | pass；held sync |
| `P8 Target Audit` | 诊断 quality-window credit sign 为负的原因。 | P7 sync complete。 | target/loss construction 命名失败环节与后续 repair。 | pass；已由 J 修复 |
| `P9 Shadow Target Repair` | 实现并测试 shadow-quality counterfactual targets。 | P8 audit exists。 | early stochastic release 不再从 target credit 中删失 future quality evidence，且 learned-policy probe evidence 记录残余行为。 | pass；held outcome |
| `P10 Projection Audit` | 诊断 repaired positives 为什么不移动 legal-open quality states。 | P9 repair probe exists。 | projection/coupling failure 与缺失 positives、HMoE redesign、coefficient-only tuning 区分开。 | pass；spawned L contract |
| `P11 Projection Contract` | 实现前定义 legal-state projection 机制。 | P10 audit exists。 | Contract 选择 projected legal-open positive alignment，并命名 implementation gates。 | pass；已由 M 实现 |
| `P12 Projection Prototype` | 依据 L 合同实现 projected legal-open credit。 | P11 contract exists。 | Focused tests 证明 projection whitelist、unsupported-layout refusal、no raw closed-mask delta alignment 与 projected positive delta pressure。 | pass；learned behavior not evaluated |

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
- Legal-state projection contract：
  [a7_event_value_advantage_credit_head_legal_state_projection_contract_20260604.zh.md](a7_event_value_advantage_credit_head_legal_state_projection_contract_20260604.zh.md)
- Projected legal-open credit prototype：
  [a7_event_value_advantage_credit_head_projected_legal_open_credit_prototype_20260604.zh.md](a7_event_value_advantage_credit_head_projected_legal_open_credit_prototype_20260604.zh.md)

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
- Config and diagnostics：
  [a7_event_value_advantage_credit_head_config_diagnostics_20260604.md](a7_event_value_advantage_credit_head_config_diagnostics_20260604.md)、
  `examples/config/training/active/air_combat/` 下的 A7 active config、
  `python/training/diagnostics.py` 中的 callback event-credit diagnostics，
  以及 `tools/diagnostics/air_combat_stage0_process_probe.py` 中的 A7
  process-probe summary metrics。
- Focused validation：
  [a7_event_value_advantage_credit_head_focused_validation_sweep_20260604.md](a7_event_value_advantage_credit_head_focused_validation_sweep_20260604.md)。
- Short learned evidence：
  [a7_event_value_advantage_credit_head_short_learned_evidence_20260604.md](a7_event_value_advantage_credit_head_short_learned_evidence_20260604.md)。
- Target construction and credit-sign audit：
  [a7_event_value_advantage_credit_head_target_construction_credit_sign_audit_20260604.zh.md](a7_event_value_advantage_credit_head_target_construction_credit_sign_audit_20260604.zh.md)。
- Shadow-quality target repair：
  [a7_event_value_advantage_credit_head_shadow_quality_repair_20260604.zh.md](a7_event_value_advantage_credit_head_shadow_quality_repair_20260604.zh.md)。
- Legal-state projection and coupling audit：
  [a7_event_value_advantage_credit_head_legal_state_projection_coupling_audit_20260604.zh.md](a7_event_value_advantage_credit_head_legal_state_projection_coupling_audit_20260604.zh.md)。
- Legal-state projection contract：
  [a7_event_value_advantage_credit_head_legal_state_projection_contract_20260604.zh.md](a7_event_value_advantage_credit_head_legal_state_projection_contract_20260604.zh.md)。
- Projected legal-open credit prototype：
  [a7_event_value_advantage_credit_head_projected_legal_open_credit_prototype_20260604.zh.md](a7_event_value_advantage_credit_head_projected_legal_open_credit_prototype_20260604.zh.md)。

计划 follow-on 输出：

- Short projected-credit learned-policy evidence。

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

- 立即下一步：运行 `A7-EVC-N Short Projection Learned Evidence`。`A7-EVC-M`
  已实现 projected legal-open path；剩余问题是这个 focused fix 是否能在短训探针中改变
  deterministic timing 与 stochastic early-fire behavior。
- 修复方向是 legal-state counterfactual projection，并更强地区分 raw shadow
  opportunity learning 与 legal-state policy distillation；不应回到盲目
  coefficient-only training。
- Adaptive label weight scheduling 仍是 guardrail candidate，不是主要 repair。
- HMoE hierarchical computation 保持 issue-board item；只有当 A7 学到正确 credit
  signs 后仍出现可归因于 policy coupling 的失败，才把它升级为 active blocker。

## 归档

当前没有 A7 归档内容。历史 A7 记录只有在已有替代 current-status 或 closeout surface 后才移动到
[archive/README.zh.md](archive/README.zh.md)。
