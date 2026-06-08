# A7 Event-Value / Advantage Credit Head

状态：`2026-06-08 closed / historical event-credit line superseded`。A7 保留
event-value / advantage-credit 调研与实现证据，但它不再是当前发射闭合任务。当前继续训练所需的
发射门已经由 M3-S2 有边界发射门记录关闭：
[../../model/archive/m3_s2_fire_timing_learnability_audit/README.zh.md](../../../model/archive/m3_s2_fire_timing_learnability_audit/README.zh.md)。
A7 没有验收自己的 quality-window timing gate；这是历史 timing research evidence，
不是当前模型仍不能发射的证明。

语言：

- 英文权威版：[README.md](README.md)
- 中文伴随版：`README.zh.md`

输入：

- 父级空战任务：[../README.zh.md](../../README.zh.md)
- A3 C2/ROE 发射纪律指针：
  [../a3_c2_roe_release_discipline/README.zh.md](../a3_c2_roe_release_discipline/README.zh.md)
- A5 受约束事件动作模型：
  [../a5_constrained_event_action_model/README.zh.md](../a5_constrained_event_action_model/README.zh.md)
- A6 event-value / first-event timing：
  [../a6_event_value_first_event_timing/README.zh.md](../a6_event_value_first_event_timing/README.zh.md)
- A6 根因分析：
  [../a6_event_value_first_event_timing/a6_event_value_first_event_timing_root_cause_rescope_20260604.zh.md](../a6_event_value_first_event_timing/a6_event_value_first_event_timing_root_cause_rescope_20260604.zh.md)
- HMoE 层级化计算断裂：
  [../../issues/hmoe_hierarchical_computation_gap/README.zh.md](../../../issues/hmoe_hierarchical_computation_gap/README.zh.md)
- A6 发射窗口标签密度失衡：
  [../../issues/a6_launch_window_label_imbalance/README.zh.md](../../../issues/a6_launch_window_label_imbalance/README.zh.md)
- 子项目创建标准：
  [../../../agent/rules/subproject_creation_standard.zh.md](../../../../agent/rules/subproject_creation_standard.zh.md)

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

## 历史证据状态

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| 生命周期 | closed；superseded | M3-S2 后续在 active scenario/config pair 上验收有边界发射门。 | A7 不是当前 launch blocker。 |
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
| A7 projected legal-open credit prototype | pass；N 后 held | [Projected legal-open credit prototype](a7_event_value_advantage_credit_head_projected_legal_open_credit_prototype_20260604.zh.md) 增加 `first_event_projection.py`、projection coeffs、PPO projected-distribution loss、projection metrics、active config knobs 与 focused tests。 | M 只证明机制与 focused gradient path；N 显示 learned behavior 继续 held。 |
| A7 short projection learned evidence | pass；held outcome | [Short projection learned evidence](a7_event_value_advantage_credit_head_short_projection_learned_evidence_20260604.zh.md) 在 projection-logger 修复后验证 r3：projection 已启用，ordinary A7 event-credit 仍 live，deterministic probing 为 `0` releases，stochastic probing release steps 为 `2`、`47`、`5`，projected active rows 保持 `0.0`。 | A7 不能 accepted；下一问题是 shadow-quality evidence 为什么没有在 learned rollout/loss path 中进入 active projected rows。 |
| A7 projection eligibility audit | pass；spawned P | [Projection eligibility root-cause audit](a7_event_value_advantage_credit_head_projection_eligibility_root_cause_audit_20260604.zh.md) 显示 N training diagnostics 中没有 accepted release，而 stochastic probe reconstruction 可产生 `3280` 个 `shadow_quality` positives。 | M projection candidate-starved，因为它依赖 early accepted release；下一步应定义不依赖采样 failure mode 的 legal-open opportunity credit。 |
| A7 legal-open opportunity contract | pass；spawned Q | [Legal-open opportunity credit contract](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_contract_20260604.zh.md) 选择 `A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY` 作为真实 legal-open quality-window positive source。 | P 只是 docs-only；implementation、training 与 learned behavior 继续 held，直到 Q focused gates 通过。 |
| A7 legal-open opportunity prototype | pass；已由 R 评估 | [Legal-open opportunity credit prototype](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_prototype_20260604.zh.md) 实现 direct legal-open quality positives、source metrics、active config knobs 与 focused tests。 | Q 只证明 source/loss/diagnostic path；R 已将 learned behavior 评估为 held。 |
| A7 short opportunity learned evidence | pass；held outcome | [Short opportunity learned evidence](a7_event_value_advantage_credit_head_short_opportunity_learned_evidence_20260604.zh.md) 记录 direct legal-open opportunity credit 后的 r1 32k train 与 deterministic/stochastic probes。 | Source starvation 已修复，但 deterministic 仍为 `0` releases，stochastic 仍过早发射，quality-window advantage 仍为负。 |
| A7 explicit state completion | pass；held outcome | [Explicit state completion probe](a7_event_value_advantage_credit_head_explicit_state_completion_probe_20260604.zh.md) 增加 `air_combat_c2_roe_v2`，显式暴露 legal/window age 与 readiness，并运行 32k learned probe。 | Observability 已改善，但 deterministic 仍为 `0` releases，quality-window advantage 仍为负。 |
| A7 value/policy coupling audit | pass；breakpoint verified | [Value/policy coupling audit](a7_event_value_advantage_credit_head_value_policy_coupling_audit_20260604.zh.md) 增加 fixed-batch 离线 credit-head fit probe，并证明 `1356` 个 legal-open positives 可由 credit head 从负 advantage 拟合到正 advantage。 | label/value 对象本地可拟合；剩余 blocker 是在线联合训练/update coupling。 |
| A7 online update-path isolation | pass；blocker localized | [Online update-path isolation](a7_event_value_advantage_credit_head_online_update_path_isolation_20260604.zh.md) 增加 gradient/update diagnostic：PPO-alone credit-head gradient 为 `0.0`，但 PPO+A7 global clipping 将 credit-head effective norm 从约 `0.4855` 压到 `0.00689`；A7 value 与 delta-align 还会在 shared actor/features 中冲突。 | 下一修复应将 A7 credit update 与 shared PPO clipping / representation drift 解耦；这不是 acceptance。 |
| A7 online credit update contract | pass；held outcome | [Online credit update contract](a7_event_value_advantage_credit_head_online_credit_update_contract_20260604.zh.md) 增加 detached-latent credit values、独立 credit-head-only value update、独立 clip budget、positive-only delta alignment、active config flags 与 nonfinite-probe parity。 | update contract 已修复，但 8k evidence 仍以 deterministic `0` releases 与负 legal-open advantage 结束。 |
| A7 active update-window diagnosis | pass；spawned X | [Active update-window 诊断](a7_event_value_advantage_credit_head_active_update_window_diagnosis_20260605.zh.md) 显示 512-step stochastic episode 含 `231` 个 `shadow_quality` positives，但同一轨迹按 `128` step training chunks 切开后只有 `5` 个 early negative labels，之后 active labels 为 `0`。 | 剩余 blocker 是 rollout-boundary credit-state loss，不是再做 coefficient sweep。 |
| A7 cross-rollout first-event state | pass；已由 Y 评估 | [Cross-rollout first-event credit state](a7_event_value_advantage_credit_head_cross_rollout_first_event_state_20260605.zh.md) 增加 A7-only per-env rollout history、same-episode carried-prefix label construction、episode advance reset、nonfinite-probe parity 与 chunk-vs-full regression coverage。 | 这是 focused repair；Y 表明修复后 behavior 仍 held。 |
| A7 post-X learned observation | pass；held outcome | [Post-X learned observation](a7_event_value_advantage_credit_head_post_x_learned_observation_20260605.zh.md) 记录 post-X 32k train、deterministic/stochastic probes 与更长 stochastic probe。 | X signal 是 live 的，但 deterministic 仍停在 `hold`；stochastic samples 恰好一次 authorized release，但仍过早发射，且没有 effects/damage chain。 |
| A7 execution breakpoint analysis | pass；held outcome | [执行断点分析](a7_event_value_advantage_credit_head_execution_breakpoint_analysis_20260605.zh.md) 在 Y 后重建 fixed-batch labels、credit-head fit 与 event-logit fit。 | 根因是 value-to-policy contract：tiny detached credit advantages 加 positive-only delta alignment 不能形成稳健的有符号 actor timing discriminator。 |
| A7 event-policy margin repair | pass；held outcome | [Event-policy margin 修复](a7_event_value_advantage_credit_head_event_policy_margin_repair_20260605.zh.md) 增加 direct signed event-logit margin 与有边界 actor/event separate update lane，并否定 A7-only safe-bias relaxation 为 label starvation。 | Startup fire prior 已恢复保守；A7 仍需要一个保持低 prewindow hazard 的 learned timing discriminator。 |

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
| `P7 Closure` | accept、hold 或 re-scope A7。 | P6 evidence exists。 | parent/A6/issues docs 与证据一致，且无 overclaim。 | pass；historical sync |
| `P8 Target Audit` | 诊断 quality-window credit sign 为负的原因。 | P7 sync complete。 | target/loss construction 命名失败环节与后续 repair。 | pass；已由 J 修复 |
| `P9 Shadow Target Repair` | 实现并测试 shadow-quality counterfactual targets。 | P8 audit exists。 | early stochastic release 不再从 target credit 中删失 future quality evidence，且 learned-policy probe evidence 记录残余行为。 | pass；held outcome |
| `P10 Projection Audit` | 诊断 repaired positives 为什么不移动 legal-open quality states。 | P9 repair probe exists。 | projection/coupling failure 与缺失 positives、HMoE redesign、coefficient-only tuning 区分开。 | pass；spawned L contract |
| `P11 Projection Contract` | 实现前定义 legal-state projection 机制。 | P10 audit exists。 | Contract 选择 projected legal-open positive alignment，并命名 implementation gates。 | pass；已由 M 实现 |
| `P12 Projection Prototype` | 依据 L 合同实现 projected legal-open credit。 | P11 contract exists。 | Focused tests 证明 projection whitelist、unsupported-layout refusal、no raw closed-mask delta alignment 与 projected positive delta pressure。 | pass；N 已评估 learned behavior |
| `P13 Projection Learned Evidence` | 运行 short projected-credit learned-policy probe。 | P12 focused gates pass。 | 记录 projection metrics、deterministic/stochastic timing 与 one-shot discipline。 | pass；held outcome |
| `P14 Projection Eligibility Audit` | 诊断 learned run 中 projection active rows 为什么为 0。 | P13 evidence exists。 | 在下一轮 training 前解释 shadow-quality labels 到 projected legal-open rows 的 rollout/loss handoff。 | pass；spawned P |
| `P15 Opportunity Credit Contract` | 定义不依赖 early accepted release 的 legal-open positive opportunity credit。 | P14 evidence exists。 | Contract 命名 target source、loss split、diagnostics 与 rollback gates。 | pass；spawned Q |
| `P16 Opportunity Credit Prototype` | 按 P 合同实现 legal-open opportunity credit。 | P15 contract exists。 | Focused tests 在 training 前证明 source construction、loss routing、diagnostics 与 A3/A5 legality boundaries。 | pass；spawned R |
| `P17 Short Opportunity Learned Evidence` | Q 后运行 bounded learned-policy probe，并与 N 的 source counts/timing 对照。 | P16 focused gates pass。 | Evidence 记录 legal-open quality source counts、deterministic/stochastic timing、one-shot discipline 与 advantage signs。 | pass；held outcome |
| `P18 Explicit State Completion` | 测试缺失 Markov state 是否解释 A7/R held outcome。 | P17 evidence exists。 | 记录 v2 observation contract、tests、32k train 与 deterministic/stochastic probes。 | pass；held outcome |
| `P19 Coupling Audit` | 解释 non-starved visible positives 为什么移动 probability 却没有翻转 deterministic mode 或 advantage sign。 | P18 evidence exists。 | 断点已验证：固定 S batch 可由 credit head 分离；剩余故障是在线联合训练/update coupling。 | pass；spawned update-path isolation |
| `P20 Online Update-Path Isolation` | 隔离哪个 online update component 阻断本地可拟合 credit signal。 | P19 evidence exists。 | blocker 定位到 shared PPO global clipping 与 shared actor/feature coupling；排除 direct PPO credit-head overwrite。 | pass；spawned update-contract work |
| `P21 Online Credit Update Contract` | 将 A7 credit value learning 从 shared PPO clipping 与 representation drift 中解耦。 | P20 blocker localized。 | 独立 credit-head-only update、positive-only delta alignment、active config wiring、nonfinite-probe parity 与短训观察已记录。 | pass；held outcome |
| `P22 Active Update Window Diagnosis` | 判断 protected A7 updates 为什么在 early training 后 inactive。 | P21 evidence exists。 | 当 early accepted release 与 quality window 跨 rollout boundary 时，rollout-local first-event labels 已证明不等于完整 episode labels。 | pass；spawned X |
| `P23 Cross-Rollout First-Event State` | 恢复 PPO rollout boundary 上的 episode-level first-event credit。 | P22 evidence exists。 | `128` step chunked labels 在 early-release/late-quality-window regression 中恢复完整 episode 的 `shadow_quality` positives。 | pass；已由 Y 评估 |
| `P24 Post-X Learned Observation` | cross-rollout first-event state repair 后重新观察 learned behavior。 | P23 focused gates pass。 | Training/probe evidence 记录 active labels、advantage signs、deterministic release behavior、stochastic one-shot discipline 与 effects/damage status。 | pass；held outcome |
| `P25 Execution Breakpoint Analysis` | 解释 post-X labels 与 credit 为什么仍没有跨过 deterministic event-mode selection。 | P24 held evidence 存在。 | Fixed-batch probes 分离 label presence、credit-head fit、event-head fit 与 actor-representation capacity。 | pass；spawned event-policy contract work |
| `P26 Event-Policy Margin Repair` | 给 actor/event path 直接有符号 margin，不再依赖 tiny detached credit advantage。 | P25 breakpoint exists。 | Focused tests 与 8k 前后对照 probes 记录 actor event surface 是否变化，以及 learned behavior 是否达到 acceptance。 | pass；historical held outcome |
| `P27 Closure` | 停止把 A7 当作 active firing-closure task。 | M3-S2 firing closure evidence exists。 | 父级文档和本 README 将当前 launch closure 指向 M3-S2，同时保留 A7 为 timing research history。 | closed；superseded by M3-S2 |

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
- Short projection learned evidence：
  [a7_event_value_advantage_credit_head_short_projection_learned_evidence_20260604.zh.md](a7_event_value_advantage_credit_head_short_projection_learned_evidence_20260604.zh.md)
- Projection eligibility root-cause audit：
  [a7_event_value_advantage_credit_head_projection_eligibility_root_cause_audit_20260604.zh.md](a7_event_value_advantage_credit_head_projection_eligibility_root_cause_audit_20260604.zh.md)
- Legal-open opportunity credit contract：
  [a7_event_value_advantage_credit_head_legal_open_opportunity_credit_contract_20260604.zh.md](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_contract_20260604.zh.md)
- Legal-open opportunity credit prototype：
  [a7_event_value_advantage_credit_head_legal_open_opportunity_credit_prototype_20260604.zh.md](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_prototype_20260604.zh.md)
- Short opportunity learned evidence：
  [a7_event_value_advantage_credit_head_short_opportunity_learned_evidence_20260604.zh.md](a7_event_value_advantage_credit_head_short_opportunity_learned_evidence_20260604.zh.md)
- Explicit state completion probe：
  [a7_event_value_advantage_credit_head_explicit_state_completion_probe_20260604.zh.md](a7_event_value_advantage_credit_head_explicit_state_completion_probe_20260604.zh.md)
- Value/policy coupling audit：
  [a7_event_value_advantage_credit_head_value_policy_coupling_audit_20260604.zh.md](a7_event_value_advantage_credit_head_value_policy_coupling_audit_20260604.zh.md)
- Online update-path isolation：
  [a7_event_value_advantage_credit_head_online_update_path_isolation_20260604.zh.md](a7_event_value_advantage_credit_head_online_update_path_isolation_20260604.zh.md)
- Online credit update contract：
  [a7_event_value_advantage_credit_head_online_credit_update_contract_20260604.zh.md](a7_event_value_advantage_credit_head_online_credit_update_contract_20260604.zh.md)
- Active update-window 诊断：
  [a7_event_value_advantage_credit_head_active_update_window_diagnosis_20260605.zh.md](a7_event_value_advantage_credit_head_active_update_window_diagnosis_20260605.zh.md)
- Cross-rollout first-event credit state：
  [a7_event_value_advantage_credit_head_cross_rollout_first_event_state_20260605.zh.md](a7_event_value_advantage_credit_head_cross_rollout_first_event_state_20260605.zh.md)
- Post-X learned observation：
  [a7_event_value_advantage_credit_head_post_x_learned_observation_20260605.zh.md](a7_event_value_advantage_credit_head_post_x_learned_observation_20260605.zh.md)
- Execution breakpoint analysis：
  [a7_event_value_advantage_credit_head_execution_breakpoint_analysis_20260605.zh.md](a7_event_value_advantage_credit_head_execution_breakpoint_analysis_20260605.zh.md)
- Event-policy margin 修复：
  [a7_event_value_advantage_credit_head_event_policy_margin_repair_20260605.zh.md](a7_event_value_advantage_credit_head_event_policy_margin_repair_20260605.zh.md)

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
- Short projection learned evidence：
  [a7_event_value_advantage_credit_head_short_projection_learned_evidence_20260604.zh.md](a7_event_value_advantage_credit_head_short_projection_learned_evidence_20260604.zh.md)。
- Projection eligibility root-cause audit：
  [a7_event_value_advantage_credit_head_projection_eligibility_root_cause_audit_20260604.zh.md](a7_event_value_advantage_credit_head_projection_eligibility_root_cause_audit_20260604.zh.md)。
- Legal-open opportunity credit contract：
  [a7_event_value_advantage_credit_head_legal_open_opportunity_credit_contract_20260604.zh.md](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_contract_20260604.zh.md)。
- Legal-open opportunity credit prototype：
  [a7_event_value_advantage_credit_head_legal_open_opportunity_credit_prototype_20260604.zh.md](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_prototype_20260604.zh.md)。
- Short opportunity learned evidence：
  [a7_event_value_advantage_credit_head_short_opportunity_learned_evidence_20260604.zh.md](a7_event_value_advantage_credit_head_short_opportunity_learned_evidence_20260604.zh.md)。
- Explicit state completion probe：
  [a7_event_value_advantage_credit_head_explicit_state_completion_probe_20260604.zh.md](a7_event_value_advantage_credit_head_explicit_state_completion_probe_20260604.zh.md)。
- Value/policy coupling audit：
  [a7_event_value_advantage_credit_head_value_policy_coupling_audit_20260604.zh.md](a7_event_value_advantage_credit_head_value_policy_coupling_audit_20260604.zh.md)。
- Online update-path isolation：
  [a7_event_value_advantage_credit_head_online_update_path_isolation_20260604.zh.md](a7_event_value_advantage_credit_head_online_update_path_isolation_20260604.zh.md)。
- Online credit update contract：
  [a7_event_value_advantage_credit_head_online_credit_update_contract_20260604.zh.md](a7_event_value_advantage_credit_head_online_credit_update_contract_20260604.zh.md)。
- Active update-window 诊断：
  [a7_event_value_advantage_credit_head_active_update_window_diagnosis_20260605.zh.md](a7_event_value_advantage_credit_head_active_update_window_diagnosis_20260605.zh.md)。
- Cross-rollout first-event credit state：
  [a7_event_value_advantage_credit_head_cross_rollout_first_event_state_20260605.zh.md](a7_event_value_advantage_credit_head_cross_rollout_first_event_state_20260605.zh.md)。
- Post-X learned observation：
  [a7_event_value_advantage_credit_head_post_x_learned_observation_20260605.zh.md](a7_event_value_advantage_credit_head_post_x_learned_observation_20260605.zh.md)。
- Execution breakpoint analysis：
  [a7_event_value_advantage_credit_head_execution_breakpoint_analysis_20260605.zh.md](a7_event_value_advantage_credit_head_execution_breakpoint_analysis_20260605.zh.md)。
- Event-policy margin 修复：
  [a7_event_value_advantage_credit_head_event_policy_margin_repair_20260605.zh.md](a7_event_value_advantage_credit_head_event_policy_margin_repair_20260605.zh.md)。

## 验收门

这是历史 A7 timing-quality 验收门。A7 现在是 closed，不是当前发射方案 accepted。

A7 只有在以下条件满足后才能 accepted：

- deterministic probing 在配置的 quality window 内执行一次授权首发；
- stochastic probing 不再积累高 pre-window release probability；
- A3/A5 one-shot discipline 保持：zero unauthorized releases、repeat releases 与 shot-budget violations；
- diagnostics 显示 event advantage 符号正确：pre-window `Q_hold > Q_fire_once`，
  quality window `Q_fire_once > Q_hold`；
- HMoE gap 对 A7 的影响要么证明不阻塞，要么作为独立 held architecture follow-on 记录；
- M2、missile authority、Pk/fuze/damage authority、`2v2`、self-play 与真实 doctrine 继续 held。

## 收口

- A7 原地关闭，作为历史 event-credit/timing 证据保留。
- 保留结论是：A7 调研了 timing-credit 路径，但没有成为当前发射闭合权威。
- 当前 launch behavior 不要默认重开 A7；有边界发射门以 M3-S2 为准。
- 如果以后重新研究 timing quality，应另开新的 model follow-on，并写清验收门，而不是继续让
  A7 保持 live。

## 归档

完整 A7 包已归档到 `docs/task/air_combat/archive/`。原任务路径现在只保留轻量指针
README。
