# A6 当前状态

状态：`2026-06-04` launch-window short learned-policy evidence 与 root-cause re-scope
后 held。P0-P13 作为 evidence-producing / re-scope / audit / implementation / analysis
slices 均已 pass；但 A6 未 accepted，因为 L 压制了 deterministic early fire，但尚未形成稳定
launch-window timing，且剩余 blocker 需要 counterfactual event-time/value credit，而不是继续
调 L 参数。

父级：[README.zh.md](README.zh.md)。

## 本检查点变化

- 创建 A6 子项目，作为 A5 之后明确的 event-value / first-event timing follow-on。
- 在
  [a6_event_value_first_event_timing_observation_20260603.zh.md](a6_event_value_first_event_timing_observation_20260603.zh.md)
  中记录 A5 retained deterministic/stochastic observations。
- 实现并验证 A6 hazard/curriculum 训练路径，包括 rollout-label attachment、non-finite probe
  parity、world-batch A5 event-info propagation 和 active config diagnostics。
- 执行
  [A6 short learned evidence](a6_event_value_first_event_timing_short_learned_probe_20260603.zh.md)。
  A6 继续 held：deterministic policy 仍为零 `fire_once` requests。
- 完成 `A6-EVT-G` closure/re-scope：M2 继续 held，不把单纯调参作为主修复路径；下一有边界
  wave 是 deadline bootstrap。
- 完成 `A6-EVT-H` implementation，加入 sustained deadline labels 与独立 active config：
  `air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_shaped_world_batch_probe_v1.json`。
- 执行
  [deadline short learned evidence](a6_event_value_first_event_timing_deadline_short_learned_probe_20260603.zh.md)。
  A6 继续 held：deterministic probability 移动到 `0.494%`，但 requests 仍为 `0`。
- 完成
  [event-head update-strength audit](a6_event_value_first_event_timing_event_head_update_audit_20260603.zh.md)。
  审计显示 A6 labels 与 gradients 是 live，但当前 event-head optimizer/head scaling 太弱，
  不能从约 `-5.3` event delta 跨过 deterministic argmax。
- 实现
  [event-head optimization lane](a6_event_value_first_event_timing_event_head_optimization_lane_20260603.zh.md)。
  Policy 现在支持零初始化的专用 `hybrid_event_head` optimizer group，并新增独立 event-head
  active config，等待下一轮 learned-policy evidence。
- 执行
  [event-head short learned evidence](a6_event_value_first_event_timing_event_head_short_learned_probe_20260603.zh.md)。
  Event head 跨过 deterministic argmax，并保留 one-shot release discipline；但 deterministic
  first release 发生在 step `2`，stochastic release steps 为 `4`、`42`、`2`。A6 因此继续
  held，残余变成 launch-window timing 问题。
- 实现
  [launch-window timing contract](a6_event_value_first_event_timing_launch_window_timing_contract_20260604.zh.md)。
  Label builder 现在通过 quality window gate 约束 accepted/curriculum/deadline positives，
  early accepted releases 会变成 negative labels，PPO 从 policy-observed contacts 中派生
  window 谓词，diagnostics 暴露 pre-window/early-accepted counts，并新增独立 L active config。
- 执行
  [launch-window short learned evidence](a6_event_value_first_event_timing_launch_window_short_learned_probe_20260604.zh.md)。
  Deterministic probe 为 `0` requests 与 `0` releases，但 open-window event probability
  达到 `34.6% / 35.0%`。Stochastic probe 保留 one-shot discipline，但仍采样出早期
  authorized releases，steps 为 `7`、`43`、`4`。
- 完成
  [root-cause re-scope](a6_event_value_first_event_timing_root_cause_rescope_20260604.zh.md)。
  进一步 L 训练与参数调节暂停。当前 blocker 被重新表述为逐步 stochastic hazard 累积与
  absorbing first-event censoring：stochastic collection 可在 `0.25` 到 `0.35` 的单步概率下
  早发，而 accepted release 会删除本应教学 hold 决策的后续 quality-window evidence。

## 成熟度矩阵

| Surface | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| P0 observation | pass | A6 observation note 汇总 retained A5 probes。 | 仅为 observation；没有 implementation accepted。 |
| Mathematical framing | pass | [Mathematical framing](a6_event_value_first_event_timing_mathematical_framing_20260603.zh.md) 定义 constrained semi-MDP、windows、labels、rejected labels、failure modes 与 C questions。 | 仅为设计；没有 implementation accepted。 |
| Objective contract | pass | [Objective contract](a6_event_value_first_event_timing_objective_contract_20260603.zh.md) 选择 existing event logit delta 上的 masked first-event hazard，并配套有边界 curriculum bootstrap。 | Event-value head 与 sequence-native objectives 继续 deferred。 |
| Training-kernel changes | pass | `python/rl/policy_algo/first_event_hazard.py`、A6 rollout buffers、event logit delta access、optional `AdaptiveKLPPO` hazard hook 与 focused tests 已存在。 | Label fields 保持在 policy observations 之外。 |
| Config and diagnostics | pass | active configs 暴露 A6 knobs，`CMODiagnosticsCallback` 与 process probe 暴露 A6 event metrics，non-finite probe 保留 A6 loss，world-batch 输出 A5 event info。 | 这是 infrastructure，不是 learned-policy acceptance。 |
| Learned-policy evidence | pass；held outcome | `32768` 步 A6 run 完成。Deterministic：`1840` open steps，`0` requests，event probability `0.247% / 0.248%`；stochastic：`3/3` 授权单发，`0` 违规。 | 首个 hazard/curriculum contract 不足；A6 继续 held。 |
| Re-scope | pass | [Deadline-bootstrap re-scope](a6_event_value_first_event_timing_deadline_bootstrap_rescope_20260603.zh.md) 选择在 event-value head 或 M2 前测试 sustained deadline labels。 | 这是 bootstrap / diagnostic bridge，不是真实 doctrine。 |
| Deadline implementation | pass | Deadline label/source/config/logging changes 已由 focused tests 覆盖。 | 这证明 wiring，不是 learned-policy acceptance。 |
| Deadline learned evidence | pass；held outcome | `32768` 步 deadline run 完成。Deterministic：`1840` open steps，`0` requests，event probability `0.494% / 0.496%`；stochastic：`3/3` 授权 releases，`1` rejected request，`0` violations。 | Deadline bootstrap 能移动 probability，但仍未解决 deterministic argmax。 |
| Event-head update audit | pass；held outcome | [Event-head audit](a6_event_value_first_event_timing_event_head_update_audit_20260603.zh.md) 与 `tests/hmoe/test_a6_event_head_update_strength.py` 显示 gradients 到达 shared/HMoE event heads，但当前 `3e-5` LR 和受抑制 residual lane 让 event delta 移动太慢。 | 只是 diagnostic evidence，不是 learned-policy acceptance。 |
| Event-head optimization lane | pass；held timing residual | [Event-head lane](a6_event_value_first_event_timing_event_head_optimization_lane_20260603.zh.md) 与 [short evidence](a6_event_value_first_event_timing_event_head_short_learned_probe_20260603.zh.md) 显示 deterministic crossing 与一次 authorized release；stochastic 给出 `3/3` authorized releases，且零 rejected / violation / repeat / budget issues。 | release timing 收敛到 authorization/contact 后的近立即时刻；A6 继续 held。 |
| Launch-window timing contract | pass | [Launch-window contract](a6_event_value_first_event_timing_launch_window_timing_contract_20260604.zh.md)、focused label/PPO/config/diagnostics tests 与独立 L active config。 | 只是 implementation evidence；learned-policy acceptance 仍依赖证据。 |
| Launch-window learned evidence | pass；held outcome | [Launch-window short evidence](a6_event_value_first_event_timing_launch_window_short_learned_probe_20260604.zh.md) 显示 deterministic 在 `34.6% / 35.0%` open-window probability 下仍为 `0` requests；stochastic 在 steps `7`、`43`、`4` 产生 `3/3` authorized releases，且无 rejected/violation/repeat/budget issues。 | L 减少 deterministic early fire，但未证明 launch-window timing。 |
| Root-cause re-scope | pass；training paused | [Root-cause re-scope](a6_event_value_first_event_timing_root_cause_rescope_20260604.zh.md) 记录 stochastic release 前累计 early-fire probability 为 `0.810`、`0.556` 与 `0.625`，并判定缺失 counterfactual hold/fire credit。 | 这是 analysis 与 re-scope evidence，不是新的 learned-policy acceptance。 |

## 残余登记

Immediate：

- 在 `A6-EVT-O` counterfactual event-time objective contract 存在前，不再运行 L 短训或调 L
  weights。
- 下一设计必须处理累计 pre-window hazard、absorbing first-event censoring 与显式
  hold-vs-fire credit。
- 调研期间保持 runtime legality 不变。

Held：

- M2 sequence-native release 继续 held。
- missile physics、Pk、fuze、damage authority、`2v2` 和 self-play 继续 out of scope。

## 建议行动顺序

1. 将 `A6-EVT-E/F` 视为完成的 evidence，而不是 acceptance。
2. 将 `A6-EVT-G` 视为完成的 re-scope，而不是 acceptance。
3. 将 `A6-EVT-H/I` 视为完成的 evidence，而不是 acceptance。
4. 将 `A6-EVT-J` 视为完成的 audit evidence，而不是 acceptance。
5. 将 `A6-EVT-K` 视为完成的 event-head evidence，而不是 A6 acceptance。
6. 将 `A6-EVT-L/M` 视为 held outcome evidence，而不是 A6 acceptance；任何 M2 release vote
   前先重新 scope launch-window shaping。
7. 将 `A6-EVT-N` 视为完成的 root-cause analysis 与 tuning pause，而不是 acceptance；下一
   packet 是 design-first 的 `A6-EVT-O Counterfactual Event-Time Objective`。

## 拒绝过度声明

- A6 未 accepted。
- A5 stochastic release discipline 不证明 deterministic first-shot learning。
- 首个 A6 hazard/curriculum contract held，并不意味着 reward-only legality tuning 成为默认下一修复。
- Deadline bootstrap 不是真实 tactics 或 doctrine claim。
- Event-head update audit 不是 learned-policy acceptance。
- Event-head deterministic crossing 不证明成熟 launch timing。
- Launch-window learned evidence 不是 A6 acceptance。
- Root-cause re-scope 不允许放松 A3/A5 legality，也不释放 M2。
- M2 继续 held，直到 A6 或后续证据支持 release vote。
