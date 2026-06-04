# A6 事件价值与首事件时机

状态：`2026-06-04` launch-window short learned-policy evidence 与 root-cause re-scope
后 held。A6 已证明 hazard/curriculum 与 deadline-bootstrap 训练路径真实生效，审计也证明
event-head gradients 路由正确；A6-EVT-K 证明专用 event-head optimizer lane 可以跨过
deterministic `fire_once` argmax。A6-EVT-L 已实现有边界的 launch-window label contract；
A6-EVT-M 显示它压制了 deterministic 近立即 release，但尚未产生可验收的 launch-window
timing；A6-EVT-N 进一步判定剩余 blocker 是 on-policy first-event censoring 与缺失
counterfactual hold/fire credit，而不是继续调 L 参数的问题。

语言：

- 英文权威版：`README.md`
- 中文伴随版：[README.zh.md](README.zh.md)

输入：

- 父级空战任务：[../README.zh.md](../README.zh.md)
- A3 C2/ROE 发射纪律：
  [../a3_c2_roe_release_discipline/README.zh.md](../a3_c2_roe_release_discipline/README.zh.md)
- A4 授权首发训练信号：
  [../a4_authorized_first_shot_training_signal/README.zh.md](../a4_authorized_first_shot_training_signal/README.zh.md)
- A5 受约束事件动作模型：
  [../a5_constrained_event_action_model/README.zh.md](../a5_constrained_event_action_model/README.zh.md)
- M1 temporal-window HMoE：
  [../../model/m1_temporal_window_hmoe/README.zh.md](../../model/m1_temporal_window_hmoe/README.zh.md)
- M2 causal Transformer HMoE：
  [../../model/m2_causal_transformer_hmoe/README.zh.md](../../model/m2_causal_transformer_hmoe/README.zh.md)
- 子项目创建标准：
  [../../../agent/rules/subproject_creation_standard.zh.md](../../../agent/rules/subproject_creation_standard.zh.md)
- subagent 使用策略：
  [../../../standards/governance/subagent_usage_policy.zh.md](../../../standards/governance/subagent_usage_policy.zh.md)

## 目的

A5 已经把第一枚导弹发射从逐帧 binary threshold control 改成
`hold/fire_once` masked event action。保留的短探针显示，这确实修复了结构性的
stochastic 多发问题：随机探针现在每个 episode 只有一次授权发射，没有重复发射、
shot-budget violation 或违规发射。

但同一探针也显示剩余问题：deterministic policy 能看到大量 `AuthorizedReady` /
fire-mask-open 步，却仍把 `fire_once` 概率压在接近零的位置，masked argmax 继续选择
`hold`。A6 因此把问题提升为 event-value / first-event timing：下一步应直接给事件头
提供价值、hazard 或首事件目标，而不是继续扩大 reward-only legality penalties。

## 当前状态

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| A3 C2/ROE discipline | accepted | authorization、shot budget、pending assessment、salvo、reattack 字段已可观察且有测试。 | 它约束合法性，不提供事件价值 credit。 |
| A4 reward/routing | held | reward、HMoE route、binary diagnostics 和 opportunity-penalty trial 都没有让 deterministic fire。 | reward-only tuning 不再作为默认主线。 |
| A5 event-action support | held after evidence | event mask/state machine/policy event head 已实现；stochastic probing 能按纪律授权发射。 | deterministic learned policy 仍为零 `fire_once` requests。 |
| A5 retained observation | pass as A6 input | deterministic：`1880` 个 fire-mask-open 步，`0` 次 fire request；stochastic：`3` 局 `3` 次授权发射，`0` 违规。 | 这是短训保留证据，不是最终 policy acceptance。 |
| A6 model direction | held after root-cause re-scope | A6 labels/loss 已进入 PPO 和 diagnostics；deadline bootstrap 让 event probability 约翻倍，但 deterministic policy 仍为零 `fire_once` requests。Event-head audit 证明 gradients 到达 shared 与 HMoE heads；A6-EVT-K 随后跨过 deterministic argmax，并执行一次 authorized release。A6-EVT-L 增加 launch-window gated labels。A6-EVT-M deterministic probe 达到 `34.6% / 35.0%` open-window fire probability，但仍为零 requests；stochastic release steps 为 `7`、`43`、`4`。A6-EVT-N 说明逐步 stochastic hazard 累积、absorbing first-event censoring 与缺失 counterfactual hold/fire credit 是当前根因。 | L 调参和额外短训暂停；下一机制必须是 counterfactual event-time/value contract；M2 继续 held。 |

## 范围

范围内：

- 将 S1 C2/ROE 武器发射重述为受约束 semi-MDP event surface 下的 first-event timing
  问题。
- 设计显式 event-value 机制，例如 action-conditional event value head、first-event
  hazard objective，或有边界的 first-shot curriculum，并且这些机制必须直接影响
  `hold/fire_once` logits。
- 从 A5 event state 定义 first-event labels、masks、windows 和 diagnostics，而不是回到
  raw `fire_weapon` threshold。
- 继续让 A3/A5 合法性和发射后抑制由约束负责，而不是由学习到的 penalty preference
  负责。
- 产出短训/探针证据，对比 deterministic event mode、event probability、
  request/accept/release counts 和 violation counts。
- 与 M1 观测窗口及未来 M2 sequence modeling 保持兼容，但本 slice 不释放 M2。

范围外：

- 重新把 broad invalid-fire、pending-assessment 或 shot-budget penalties 作为主要合法性机制。
- 移除 A5 masks 或 state-machine suppression 来降低发射难度。
- 导弹物理、Pk、fuze、damage authority 或 stock-weapon authority 改动。
- 真实 BVR doctrine 断言、`2v2`、self-play 或 M2 实现。
- 仅凭 stochastic one-shot behavior 宣告 deterministic learned-policy acceptance。

## 阶段计划

| 阶段 | 目标 | 进入条件 | 退出条件 | 状态 |
| --- | --- | --- | --- | --- |
| `P0 Observation` | 冻结 A5 保留现象和残余诊断。 | A5 short learned-policy probe 存在。 | A6 observation note 记录 deterministic/stochastic 对照，并拒绝 reward-only legality tuning 作为下一默认主线。 | pass |
| `P1 Mathematical Framing` | 把问题抽象为 masked first-event timing with delayed sparse credit。 | P0 observation 已作为输入。 | 设计说明命名 event state、objective target、label source 和失败模式。 | pass |
| `P2 Objective Contract` | 选择首个 A6 objective contract。 | P1 framing 存在。 | event-value、hazard 或 curriculum target 的 mask 与 diagnostics 被写清楚。 | pass |
| `P3 Training Kernel Integration` | 实现有边界的 auxiliary objective 或 head。 | P2 contract accepted。 | policy/PPO focused tests 证明 shape、mask、loss、eval semantics。 | pass |
| `P4 Scenario And Config Probe` | 将维护中的 S1 C2/ROE probe 接到 A6 objective。 | P3 tests pass。 | active config tests、diagnostics 与 world-batch runtime info 证明合法性仍由 state/mask 持有。 | pass |
| `P5 Short Learned Evidence` | 运行短训/探针对照。 | P4 wiring valid。 | 记录 deterministic `fire_once` mode/probability 与 release counts 相对 A5 baseline 的变化。 | pass；held outcome |
| `P6 Closure/Re-scope` | 同步 A3/A4/A5/M1/M2，并选择下一 objective wave。 | P5 evidence complete。 | A6 保持 held，下一 wave 限定为 deadline bootstrap，而不是 M2 release。 | pass；re-scoped |
| `P7 Deadline Bootstrap` | 增加持续 open-window deadline labels 与独立 active config。 | P6 re-scope decision exists。 | focused tests 证明 label/source/config/logging 行为，A3/A5 masks 仍为权威。 | pass |
| `P8 Deadline Short Evidence` | 运行 deadline wave 短训/探针对照。 | P7 tests pass。 | deterministic/stochastic probes 记录 event logits 是否跨过 masked argmax。 | pass；held outcome |
| `P9 Event-Head Update Audit` | 审计 optimizer/head scaling 是否阻止 A6 正例推动 event logits。 | P8 held evidence exists。 | focused update probe 解释为什么持续正例只把 probability 推到约 `0.5%`。 | pass；held outcome |
| `P10 Event-Head Optimization Lane` | 给 `hold/fire_once` event rows 一个更强但有边界的更新路径。 | P9 将 blocker 归因到 update strength。 | 短训证据测试 deterministic argmax 能否在不削弱 A3/A5 masks 的情况下 crossing。 | pass；held timing residual |
| `P11 Launch-Window Timing Contract` | 把 authorization 与良好首发 timing 分开。 | P10 证明 event argmax 可 crossing，但 release 过早。 | 有边界 contract 定义 engagement-quality/window labels，且不削弱 A3/A5 masks；focused tests 覆盖实现表面。 | pass |
| `P12 Launch-Window Short Evidence` | 在 learned-policy probe 中测试 L contract。 | P11 focused tests pass。 | deterministic/stochastic outcomes 记录 release timing 与 discipline。 | pass；held outcome |
| `P13 Root-Cause Re-scope` | 停止 L 调参并识别机制 blocker。 | P12 held evidence exists。 | 根因记录解释 stochastic hazard 累积、吸收式 first-event censoring 与缺失 counterfactual hold/fire credit；继续训练前先重新定义下一 contract。 | pass；training paused |

## 任务簇

- 任务簇计划：
  [a6_event_value_first_event_timing_task_clusters_20260603.zh.md](a6_event_value_first_event_timing_task_clusters_20260603.zh.md)
- 当前状态：
  [a6_event_value_first_event_timing_current_status_20260603.zh.md](a6_event_value_first_event_timing_current_status_20260603.zh.md)
- 分发队列：
  [a6_event_value_first_event_timing_dispatch_queue_20260603.zh.md](a6_event_value_first_event_timing_dispatch_queue_20260603.zh.md)
- 验收门：
  [a6_event_value_first_event_timing_acceptance_20260603.zh.md](a6_event_value_first_event_timing_acceptance_20260603.zh.md)
- 观察证据：
  [a6_event_value_first_event_timing_observation_20260603.zh.md](a6_event_value_first_event_timing_observation_20260603.zh.md)
- 数学框架：
  [a6_event_value_first_event_timing_mathematical_framing_20260603.zh.md](a6_event_value_first_event_timing_mathematical_framing_20260603.zh.md)
- Objective contract：
  [a6_event_value_first_event_timing_objective_contract_20260603.zh.md](a6_event_value_first_event_timing_objective_contract_20260603.zh.md)
- 短训 learned evidence：
  [a6_event_value_first_event_timing_short_learned_probe_20260603.zh.md](a6_event_value_first_event_timing_short_learned_probe_20260603.zh.md)
- Deadline bootstrap re-scope：
  [a6_event_value_first_event_timing_deadline_bootstrap_rescope_20260603.zh.md](a6_event_value_first_event_timing_deadline_bootstrap_rescope_20260603.zh.md)
- Deadline short learned evidence：
  [a6_event_value_first_event_timing_deadline_short_learned_probe_20260603.zh.md](a6_event_value_first_event_timing_deadline_short_learned_probe_20260603.zh.md)
- Event-head update-strength audit：
  [a6_event_value_first_event_timing_event_head_update_audit_20260603.zh.md](a6_event_value_first_event_timing_event_head_update_audit_20260603.zh.md)
- Event-head optimization lane：
  [a6_event_value_first_event_timing_event_head_optimization_lane_20260603.zh.md](a6_event_value_first_event_timing_event_head_optimization_lane_20260603.zh.md)
- Event-head short learned evidence：
  [a6_event_value_first_event_timing_event_head_short_learned_probe_20260603.zh.md](a6_event_value_first_event_timing_event_head_short_learned_probe_20260603.zh.md)
- Launch-window timing contract：
  [a6_event_value_first_event_timing_launch_window_timing_contract_20260604.zh.md](a6_event_value_first_event_timing_launch_window_timing_contract_20260604.zh.md)
- Launch-window short learned evidence：
  [a6_event_value_first_event_timing_launch_window_short_learned_probe_20260604.zh.md](a6_event_value_first_event_timing_launch_window_short_learned_probe_20260604.zh.md)
- Root-cause re-scope：
  [a6_event_value_first_event_timing_root_cause_rescope_20260604.zh.md](a6_event_value_first_event_timing_root_cause_rescope_20260604.zh.md)

## 输出与证据

当前输出：

- A6 子项目范围和有限任务簇计划。
- A5 retained observation 的 deterministic / stochastic 对照摘要。
- Mathematical framing 已按 `A6-EVT-B` 验收。
- Objective contract 已按 `A6-EVT-C` 验收：masked first-event hazard，并使用有边界的
  curriculum bootstrap。
- Training-kernel prototype 已按 `A6-EVT-D` 验收：hazard label/loss helpers、
  event logit delta access 和 focused tests。
- Config/diagnostics 与 runtime wiring 已按 `A6-EVT-E` 验收：A6 active configs 暴露 knobs，
  diagnostics 报告 event probabilities，world-batch C2/ROE info 可用，且 A6 labels 在
  policy observations 之外附加。
- Short learned evidence 已按 `A6-EVT-F` 完成：deterministic 在 `1840` 个 open-window
  steps 下仍为 `0` requests，event probability 为 `0.247% / 0.248%`；stochastic 保留
  `3/3` 授权单发且无违规。
- Closure/re-scope 已按 `A6-EVT-G` 完成：M2 继续 held，不把单纯调参作为主线；下一
  有边界机制是在既有 first-event hazard labels 上加入 deadline bootstrap。
- Deadline-bootstrap implementation 已按 `A6-EVT-H` 完成：授权 open-window 达到年龄阈值后
  给出持续正例，并使用独立 probe config，避免覆盖首次 A6 evidence 的复现实验入口。
- Deadline short evidence 已按 `A6-EVT-I` 完成：deterministic event probability 从约
  `0.247%` 移动到 `0.494%`，但 deterministic 仍为 `0` requests。Stochastic 产生
  `3/3` 授权 releases，零 violation/repeat/budget issues，但有一次 `weapon_not_ready`
  rejected request。
- Event-head update-strength audit 已按 `A6-EVT-J` 完成：A6 labels 与 gradients 是 live；
  first-shot route gradients 到达 shared 与 HMoE heads；当前 `3e-5` / low-scale residual
  设置解释了为什么 event probability 能移动、但 deterministic argmax 仍不 crossing。
- Event-head optimization lane implementation 已按 `A6-EVT-K` 完成：
  `hybrid_event_head_lr_scale` 增加零初始化的 `hold/fire_once` event-logit 专用 head 和
  optimizer group，并提供独立 active config 等待 learned-policy evidence。
- Event-head short evidence 已按 `A6-EVT-K` 完成：deterministic 现在在 step `2` 执行一次
  accepted authorized release；stochastic 产生 `3/3` accepted authorized releases，且无
  rejected、violation、repeat 或 budget 问题。这证明 event decision 可训练，但暴露 early
  launch-window residual。
- Launch-window timing contract implementation 已按 `A6-EVT-L` 完成：
  A6 labels 现在区分 legal authorization 与 quality-window release，early accepted releases
  会变成 negative labels，deadline/curriculum positives 被 quality window gate 约束，PPO
  从 policy observations 中派生 contact quality，并提供独立 L active config。
- Launch-window short learned evidence 已按 `A6-EVT-M` 完成：deterministic 不再近立即发射，
  但也没有 crossing；open-window event probability 达到 `34.6% / 35.0%`，requests 为 `0`。
  Stochastic 仍然每局采样一次 authorized release，steps 为 `7`、`43`、`4`，无 rejected、
  violation、repeat 或 budget 问题。
- Root-cause re-scope 已按 `A6-EVT-N` 完成：额外 L 训练与参数调节暂停。当前 blocker 是结构性
  问题：逐步 stochastic hazard 累积会在 deterministic argmax crossing 前产生 early first
  events，而 accepted first event 会 censor 后续 quality-window evidence。下一轮 implementation
  或 training 前，A6 需要 counterfactual event-time/value contract。

Held output：

- 首个 hazard/curriculum objective 不足。
- Deadline bootstrap 能移动 event probability，但不能推动 deterministic argmax。
- Event-head optimization 推动 deterministic argmax crossing，但 learned release 发生在
  authorization/contact 后的近立即时刻，尚未证明成熟 first-event timing。
- Launch-window short evidence 压制 deterministic early fire，但尚未证明 launch-window timing。
- L 参数搜索暂停，因为根因是在 on-policy absorbing first-event collection 下缺失
  counterfactual hold/fire credit。

## 验收门

本子项目只有在以下条件满足时才能标记 accepted：

- selected objective 直接针对 masked `hold/fire_once` event timing，而不是 raw
  `fire_weapon` thresholding。
- A3/A5 合法性仍由 event mask 与 state-machine transition 执行。
- focused tests 覆盖 objective shape、mask handling、deterministic evaluation，以及保留 A5
  no-repeat/no-budget-violation discipline。
- 短训证据显示 deterministic `fire_once` probability/mode 相对 A5 baseline 有实质移动，并且
  要么执行一次授权首发，要么把 remaining blocker 精确归属到 reward-only legality tuning
  之外。
- 文档继续拒绝 M2 release、真实 doctrine、导弹物理、Pk、fuze 与 damage-authority overclaims。

## 残余与下一步

- 立即下一步：继续在 A7 implementation-contract 子项目内推进：
  [../a7_event_value_advantage_credit_head/README.zh.md](../a7_event_value_advantage_credit_head/README.zh.md)。
  A7 已实现并验证 event-credit path，并已修复 shadow-quality label-censoring bug；
  但修复后的 short learned evidence 仍 held：deterministic 仍为 `0` releases，
  stochastic 过早发射，quality-window advantage 仍为负。
- Event-value 不再只是可能的长期扩展方向；A7-G held 结果与 A7-I/J 证据将下一设计要求收窄到
  修复后的 legal-state projection / policy-coupling analysis。
- 有边界的 first-shot curriculum 产生了早期 gradient，并按要求衰减为零；但单独使用未推动
  deterministic argmax。
- M2 继续 held，直到 deterministic first-event behavior 在当前 A3/A5 约束下可训练，或 A6
  residual 明确证明 sequence modeling 是下一 release vote 的必要条件。

## 归档

当前 A6 记录保持 live。被替代的 observation notes、rejected objectives 和 dated probe
records 只有在已有替代 current-status 或 closeout surface 后才移动到
[archive/README.zh.md](archive/README.zh.md)。
