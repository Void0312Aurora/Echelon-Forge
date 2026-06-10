# A7 Legal-Open Opportunity Credit Contract

状态：`2026-06-04`，已为
`A7-EVC-P Legal-Open Opportunity Credit Contract` 选择 design contract；本文档不启动
implementation。

父级：[README.zh.md](README.zh.md)。英文规范页：
[a7_event_value_advantage_credit_head_legal_open_opportunity_credit_contract_20260604.md](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_contract_20260604.md)。

## 决策

`A7-EVC-O` 表明：M projection path 在结构上可工作，但它 candidate-starved。
它只有在 `shadow_quality` rows 存在时，才训练 projected legal-open positives；
而这些 rows 只有在 policy 先采样 early accepted release 后才会出现。因此 M 是对已采样
early release 的 repair path，不是主动的 opportunity-credit source。

A7 应新增一个 legal-open source：

```text
A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY
```

该 source 将真实、pre-release、legal-open 的 quality-window observations 标为 positive
`fire_once` opportunity credit。它不投影 closed-mask row，不重新打开环境状态，也不依赖
accepted release 已经发生。

## Source Contract

后续 implementation 应新增满足以下合同的 source：

| Condition | Required behavior |
| --- | --- |
| A5 state/mask | 只在真实 observation 为 `AuthorizedReady` 且 `fire_once` legal/open 时 active。 |
| First event | 只在 episode window 内 first accepted `fire_once` 之前 active。 |
| Quality gate | 必须启用且满足既有 launch-window quality predicate，并达到 configured minimum window age。 |
| Target | `target=1.0`，表示从当前 legal-open state fire 的 positive event credit。 |
| Weight | 由显式 opportunity weight 控制；active A7 configs 外默认 off。 |
| Source id | `A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY`，与 `DEADLINE` 和 `SHADOW_QUALITY` 分离。 |

优先级应为：

1. Accepted quality release 保留既有 accepted-source path。
2. Early accepted release 保留 early-negative 加 `shadow_quality` repair。
3. No-release legal-open quality rows 变成 `LEGAL_OPEN_QUALITY` positives。
4. `DEADLINE` 保留为 late fallback 与 diagnostic source，不再承担主要
   quality-window teacher。

若 `launch_window_open` 缺失，legal-open opportunity credit 必须默认 disabled。
不得用 broad censored-survival positives 伪装成该 source。

## Loss Contract

P 之后的 loss split 应为：

| Signal | Source | Observation legality | Trains value | Trains event-logit delta |
| --- | --- | --- | --- | --- |
| Prewindow hold | `PREWINDOW` | legal-open | negative | yes |
| Early accepted | `EARLY_ACCEPTED` | sampled early release 时的 legal-open | negative | yes |
| Legal-open opportunity | `LEGAL_OPEN_QUALITY` | legal-open | positive | yes |
| Late fallback | `DEADLINE` | legal-open | positive | yes，但单独诊断 |
| Shadow repair | `SHADOW_QUALITY` | closed-mask raw row | raw value/projection candidate only | raw row 上 no；只在 projected legal-open sample 上 yes |

`LEGAL_OPEN_QUALITY` 应进入 ordinary A7 value/delta path，因为样本自身就是
legal-open。它不得经过 projection helper。`SHADOW_QUALITY` 保持 M 行为：raw
closed-mask rows 不能训练 direct event-logit delta，但可以生成 projected legal-open
positives。

## Diagnostics Contract

后续 prototype 必须暴露足够 counters，以证明新信号没有 starvation：

- `a7/evc_src_legal_open_quality_count_mean`
- `LEGAL_OPEN_QUALITY`、`DEADLINE` 与 `SHADOW_QUALITY` 的 source-specific
  positive counts
- legal-open quality rows 的 source-specific event advantage mean
- projection candidate count 仍只绑定到 `SHADOW_QUALITY`
- rollout/probe summaries 区分 no-release quality opportunity rows 与 post-release
  shadow rows

implementation 后的验收问题不只是 ordinary A7 是否 live，而是 train rollouts 是否在
policy 采样 early release 前就包含 legal-open quality positives。

## Implementation Entry Points

预期 follow-on 写入面：

- `python/rl/policy_algo/first_event_hazard.py`
  - 增加 `A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY`；
  - 为 `build_first_event_hazard_labels()` 增加显式 opportunity-weight/min-age knobs；
  - 为 no-release legal-open quality rows 输出 positive labels。
- `python/rl/policy_algo/ppo_adaptive_kl.py`
  - 将新 source 纳入 source diagnostics；
  - 因为该 source 是 legal-open，允许 delta alignment；
  - projection candidates 继续只限于 `SHADOW_QUALITY`。
- `python/rl/support/nonfinite_probe.py`
  - 在 patched train path 中镜像新 source metrics。
- Active A7 config 与 callback/process-probe diagnostics：
  - 暴露新的 opportunity weight 与 count metrics；
  - active A7 experiment config 外保持 defaults off。
- Focused tests：
  - no-release quality window 产生 `LEGAL_OPEN_QUALITY` positives；
  - prewindow rows 继续为 negative；
  - early accepted release 仍产生 `EARLY_ACCEPTED` negatives 和
    `SHADOW_QUALITY` repair candidates；
  - legal-open opportunity rows 允许 delta alignment，raw shadow rows 仍阻断；
  - source counters 到达 logger/probe metrics。

## Validation Gates

下一轮 learned-policy training wave 前：

```bash
python -m compileall -q python/rl/policy_algo/first_event_hazard.py python/rl/policy_algo/ppo_adaptive_kl.py python/rl/support/nonfinite_probe.py
pytest tests/policy/test_first_event_timing_contracts.py tests/policy/test_event_head_update_contracts.py tests/policy/test_auxiliary_training_updates.py -q
pytest tests/training/test_event_timing_training_config_contracts.py tests/training/test_air_combat_training_entry_contracts.py -q
git diff --check -- docs/task/air_combat python/rl tests/policy tests/training
```

完成这些 gates 后的 first short learned-policy probe 应报告：

- deterministic request/release timing；
- stochastic request/release timing 与 one-shot violations；
- `LEGAL_OPEN_QUALITY`、`DEADLINE` 与 `SHADOW_QUALITY` source counts；
- legal-open quality advantage sign；
- projection candidate/active counts。

## Rollback Gates

若出现以下情况，应 re-scope 或回滚 opportunity source：

- positive labels 出现在 `fire_once` 非 legal-open 的状态；
- quality gate 打开前 stochastic near-immediate release probability 上升；
- raw `SHADOW_QUALITY` rows 重新获得 direct event-logit delta alignment；
- 新 source 在没有 `launch_window_open` evidence 的情况下 active；
- A3/A5 masks、one-shot suppression 或 shot-budget discipline 被削弱。

## Non-Goals

- 不在 P 中实现该合同；implementation candidate 是下一切片。
- 不削弱 A3/A5 masks，也不让 `FiredAssess` 再次可发射。
- 不把 broad censored no-release rows 当作 positive labels。
- 不把它视为 HMoE redesign、M2 release、missile authority、`2v2`、self-play
  或 real doctrine。
- focused source/loss diagnostics 通过前，不再运行 learned-policy wave。

## Dispatch Result

`A7-EVC-P` 选择 direct legal-open quality opportunity credit 作为下一条
non-starved teaching signal。下一 implementation candidate 是
`A7-EVC-Q Legal-Open Opportunity Credit Prototype`。
