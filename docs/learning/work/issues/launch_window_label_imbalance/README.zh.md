# A6 发射窗口标签密度失衡

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/learning/work/issues/launch_window_label_imbalance/README.md`
Owner: `learning/air-combat-training`
Last verified: `2026-08-08`

状态：`2026-06-04` 开放中；L contract 下 deterministic `fire_once` argmax
不 crossing，尽管 open-window event probability 达到 `34.6%`。该 issue 现在作为
A7 的 balancing requirement，而不是独立 L-tuning repair。

首次观察：`2026-06-04`，A6-EVT-M 短训 learned-policy probe 期间。

问题类别：有门控的 launch-window contract 下正/负训练标签密度失衡。

## 摘要

A6-EVT-K（event-head optimization lane）证明了 masked `hold/fire_once` 事件
决策可以跨过 deterministic argmax。但其 learned release 坍缩到近立即
authorization/contact（step 2）。

A6-EVT-L 增加了 launch-window timing contract，将正例通过 quality window 门控，
并把过早 accepted release 转为负标签。A6-EVT-M 运行短训 learned-policy probe：

- deterministic：`0` requests，`0` releases，open-window event probability
  `34.6% / 35.0%`；
- stochastic：`3/3` 授权单发，steps 为 `7`、`43`、`4`。

L contract 压制了 deterministic early fire，但也把 deterministic argmax 推回
crossing 阈值以下。这是一个标签密度失衡问题，不是 update-strength 或 gradient
routing 问题——K 已经证明这两者是正常工作的。

## 当前证据

A6-EVT-M probe，使用 L active config
`air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_launch_window_shaped_world_batch_probe_v1.json`：

| 信号 | 值 | 解释 |
| --- | --- | --- |
| Deterministic requests | `0` | Masked argmax 从不选择 `fire_once`。 |
| Open-window fire probability | `34.6% / 35.0%` | 部分状态学到了较高概率，但期望 delta 仍为负。 |
| Stochastic requests | `3/3` 授权，steps `7/43/4` | 采样可以克服中等概率；单发纪律保持。 |
| Violation / repeat / budget | 全部 probe 为 `0` | A3/A5 合法性完好。 |

训练中期 ~30720 timesteps 的诊断：

| 信号 | 值 |
| --- | --- |
| `event_logit_delta_mean_open` | `-2.19` |
| `event_fire_prob_mean_open` | `0.10` |
| `pi_event_mode_fire_frac` | `0` |

当前 L config 关键参数：

| 参数 | 值 | 效果 |
| --- | --- | --- |
| `a6_first_event_curriculum_coef` | `0.0` | 无引导正例。 |
| `a6_first_event_deadline_weight` | `1.0` | 仅在 ≥64 quality-window steps 后给正例。 |
| `a6_first_event_deadline_min_window_age_steps` | `64` | 门槛高；许多 episode 结束前达不到。 |
| `a6_first_event_launch_window_prewindow_hold_weight` | `0.3` | 每个 pre-window step 都给负标签。 |
| `a6_first_event_launch_window_early_accept_weight` | `1.0` | 过早 accepted fire 受完整惩罚。 |
| `a6_first_event_launch_window_min_window_age_steps` | `32` | Quality window 打开晚。 |

## 根因

L contract 造成了严重的正/负标签密度偏差：

1. **Quality window 很少打开**：range gate（`8000–30000 m`）、track-age gate
   （`≤5 s`）和最小 window age（`32` steps）组合使 quality window 变窄。
2. **Deadline 正例稀少**：需要在已经很稀有的 quality window 内积累 `64` steps。
   许多 episode 在此阈值之前就结束了。
3. **Pre-window 负例密集**：`prewindow_hold_weight=0.3` 在每个 legal-open 但
   pre-quality-window step 都触发。
4. **Curriculum 被关闭**：`curriculum_coef=0.0` 意味着没有引导正例来帮助早期学习。
5. **净梯度将 fire probability 往下拉**：期望 logit delta 保持为负（~30720 steps
   时 `-2.19`），因此 deterministic argmax 停在 `hold`。

一组典型 rollout 中正/负标签比例严重向负侧倾斜，而 loss 是带 per-sample 权重的
简单 BCE——没有内建的类别不平衡补偿机制。

## 与 A6-EVT-K 的对比

| 维度 | A6-EVT-K（无 L） | A6-EVT-M（有 L） |
| --- | --- | --- |
| Deterministic requests | 1（step 2） | 0 |
| Open-window fire prob | ~67.9% | 34.6% / 35.0% |
| `event_logit_delta_mean_open` | +0.747 | -2.19 |
| `pi_event_mode_fire_frac` | 1 | 0 |
| 过早发射压制 | 无 | 有效 |
| 时序质量 | 近立即发射 | 完全不发射 |

L 解决了 K 的过早发射问题，但矫枉过正：负信号强到阻止了任何 deterministic
fire，而不仅仅是早期 fire。

## 影响

- **阻塞 A6 验收**：验收门要求 deterministic `fire_once` probability/mode
  相对 A5 baseline 有实质移动，并且要么执行授权首发，要么记录精确的 held
  blocker。
- **Stochastic-only 行为不是验收**：stochastic probing 保持单发纪律，但不能
  证明 deterministic learned-policy 行为。
- **不是 reward-only legality 的回归**：A3/A5 masks 仍然权威。修复应调整
  label 语义，而非削弱运行时约束。

## 不能宣称

- 这不代表 event-head optimization lane（K）是坏的。
- 这不代表 launch-window contract（L）方向错误——它正确地识别了过早发射问题。
- 这不是 M2 release 或 sequence-native PPO 的投票。
- 这不代表当前 range gate、track-age gate 或 window age 阈值在绝对意义上是
  错误的——它们是 bootstrap 设置，不是 doctrine。

## 假设

1. **主要**：正例标签（deadline、curriculum）相对负例标签（pre-window hold、
   early-accepted）过于稀疏，净梯度将 fire probability 压制在 deterministic
   argmax 以下。
2. **次要**：关闭 curriculum（`coef=0.0`）移除了唯一能在 quality window
   收紧前建立 fire 基线的早期训练桥梁。
3. **次要**：quality-window gate（range + track age + window age）对当前
   S1 非机动目标场景可能过于严格。
4. **辅助**：带 per-sample 权重的 BCE 没有内建类别平衡修正；即使活跃标签中
   正负比例为 1:10，也会产生净负梯度。

## 相关领域上下文

- A6 子项目：
  [docs/task/air_combat/archive/a6_event_value_first_event_timing/README.zh.md](../../../../task/air_combat/archive/a6_event_value_first_event_timing/README.zh.md)
- A6-EVT-M launch-window 证据：
  [a6_event_value_first_event_timing_launch_window_short_learned_probe_20260604.zh.md](../../../../task/air_combat/archive/a6_event_value_first_event_timing/a6_event_value_first_event_timing_launch_window_short_learned_probe_20260604.zh.md)
- A6-EVT-L launch-window contract：
  [a6_event_value_first_event_timing_launch_window_timing_contract_20260604.zh.md](../../../../task/air_combat/archive/a6_event_value_first_event_timing/a6_event_value_first_event_timing_launch_window_timing_contract_20260604.zh.md)
- A6-EVT-K event-head 证据：
  [a6_event_value_first_event_timing_event_head_short_learned_probe_20260603.zh.md](../../../../task/air_combat/archive/a6_event_value_first_event_timing/a6_event_value_first_event_timing_event_head_short_learned_probe_20260603.zh.md)
- 标签构造器：
  [python/rl/policy_algo/first_event_hazard.py](../../../../../python/rl/policy_algo/first_event_hazard.py)
- 训练入口：
  [python/rl/policy_algo/ppo_adaptive_kl.py](../../../../../python/rl/policy_algo/ppo_adaptive_kl.py)

## 下一步门槛

下一修复门是 A7
（[air-combat A7](../../../../task/air_combat/archive/a7_event_value_advantage_credit_head/README.zh.md)）。
标签密度发现转为 A7 objective 的 guardrail：

1. **Window-balanced target mass**：按 first-shot window 限制正/负权重，避免密集
   pre-window negatives 压过稀少 quality-window positives。
2. **Counterfactual hold/fire credit**：训练 `Q_hold` 与 `Q_fire_once`，让
   pre-quality states 获得相对 early fire 的 hold credit，而不只是另一组 fire negative
   labels。
3. **Shadow quality target**：当 policy-observed contact/C2 facts 仍暴露质量窗口时，不让
   early stochastic accepted releases 删除后续 quality-window evidence。
4. **Adaptive label scheduling 仅作 guardrail**：minimum positive-mass 或 confidence
   checks 可用于稳定 A7，但不是 primary repair。

任何修复必须：

- 保持 A3/A5 合法性不变（masks 和 state machine 仍为权威）；
- 产出 deterministic probe 中 `fire_once` requests > 0，且 release 在 quality
  window 内；
- 保持 stochastic 单发纪律和零违规；
- 报告累计 pre-window early-fire probability；
- 保持 M2 held。

## 闭合验收标准

- Deterministic probe 显示 ≥1 次授权 release，且不在近立即 authorization/contact
  发生。
- 评估时 open-window steps 的 event probability 超过 50%。
- Deterministic 和 stochastic probes 均为零违规/重复/预算问题。
- A3/A5 masks 和 state-machine suppression 未被削弱。
- Config 变更记录为 bootstrap re-balance，不宣称为真实发射区 doctrine。
