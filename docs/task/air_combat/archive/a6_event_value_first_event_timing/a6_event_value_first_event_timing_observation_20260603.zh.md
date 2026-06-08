# A6 观察：A5 事件头 deterministic 仍保持 hold

状态：`2026-06-03` P0 observation evidence，用于
[README.zh.md](README.zh.md)。本文读取 `experiments_tmp/` 下保留的 A5 probe artifacts，
但不把这些 artifacts 纳入 staging evidence。

## 来源 artifacts

保留但不入库的 artifacts：

- `experiments_tmp/a5_event_action_temporal_32k_20260603/a5_deterministic_probe.json`
- `experiments_tmp/a5_event_action_temporal_32k_20260603/a5_stochastic_probe.json`

权威入库摘要仍是 A5 short learned-policy note：
[../a5_constrained_event_action_model/a5_constrained_event_action_model_short_learned_probe_20260603.zh.md](../a5_constrained_event_action_model/a5_constrained_event_action_model_short_learned_probe_20260603.zh.md)。

## 观察命令

Deterministic summary：

```bash
jq '. as $r | {probe: "deterministic", episodes: ($r.episode_summaries|length), terminations: $r.termination_reasons, fire_mask_open_steps: ([$r.episode_summaries[].fire_mask_open_step_count]|add), authorized_ready_steps: ([$r.episode_summaries[].engagement_state_counts.AuthorizedReady]|add), fire_requests: ([$r.episode_summaries[].fire_once_requested_count]|add), accepted: ([$r.episode_summaries[].fire_once_accepted_count]|add), releases: ([$r.episode_summaries[].release_executed_count]|add), violations: ([$r.episode_summaries[].violation_release_count]|add), event_prob_fire_once_mean: (([$r.episode_summaries[].policy_event_prob_fire_once_mean]|add) / ($r.episode_summaries|length)), event_prob_fire_once_max: ([$r.episode_summaries[].policy_event_prob_fire_once_max]|max), mode_fire_count: ([$r.episode_summaries[].policy_event_mode_fire_once_count]|add), final_missiles: [$r.episode_summaries[].final_missiles], release_steps: [$r.episode_summaries[].release_steps]}' \
  experiments_tmp/a5_event_action_temporal_32k_20260603/a5_deterministic_probe.json
```

Stochastic summary：

```bash
jq '. as $r | {probe: "stochastic", episodes: ($r.episode_summaries|length), terminations: $r.termination_reasons, fire_mask_open_steps: ([$r.episode_summaries[].fire_mask_open_step_count]|add), authorized_ready_steps: ([$r.episode_summaries[].engagement_state_counts.AuthorizedReady]|add), fire_requests: ([$r.episode_summaries[].fire_once_requested_count]|add), accepted: ([$r.episode_summaries[].fire_once_accepted_count]|add), rejected: ([$r.episode_summaries[].fire_once_rejected_count]|add), releases: ([$r.episode_summaries[].release_executed_count]|add), authorized_releases: ([$r.episode_summaries[].authorized_release_count]|add), violations: ([$r.episode_summaries[].violation_release_count]|add), repeats: ([$r.episode_summaries[].repeat_release_before_assessment_count]|add), budgets: ([$r.episode_summaries[].shot_budget_violation_count]|add), event_prob_fire_once_mean: (([$r.episode_summaries[].policy_event_prob_fire_once_mean]|add) / ($r.episode_summaries|length)), event_prob_fire_once_max: ([$r.episode_summaries[].policy_event_prob_fire_once_max]|max), mode_fire_count: ([$r.episode_summaries[].policy_event_mode_fire_once_count]|add), final_missiles: [$r.episode_summaries[].final_missiles], release_steps: [$r.episode_summaries[].release_steps]}' \
  experiments_tmp/a5_event_action_temporal_32k_20260603/a5_stochastic_probe.json
```

## 结果

| Probe | Episodes | Termination | Fire-mask-open / `AuthorizedReady` steps | Requests | Accepted | Releases | Authorized releases | Violations | Repeat / budget violations | Event fire probability mean / max | Deterministic event mode fire count |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| deterministic | 1 | `combat_timeout=1` | `1880 / 1880` | 0 | 0 | 0 | 0 | 0 | 0 | `0.217% / 0.278%` | 0 |
| stochastic | 3 | `combat_timeout=3` | `1647 / 1647` | 4 | 3 | 3 | 3 | 0 | 0 | `0.066% / 0.278%` | 0 |

Stochastic release steps 为 `823`、`346`、`592`；每个 episode 最终剩余 `3`
枚导弹。唯一 rejected event request 是 `weapon_not_ready=1`；没有 post-launch
repeat release、pending-assessment release 或 shot-budget violation。

## 解释

A5 event surface 已经足以表达并约束武器事件：

- 合法开火窗口存在且可见；
- stochastic exploration 可以最终采样到 `fire_once`；
- 一旦采样并 accepted，state machine 会抑制不安全重复发射。

因此 deterministic 失败不能再解释为“缺少开火窗口”或“缺少发射纪律”。它是
optimization / timing-credit failure：event head 将 `fire_once` 长期压在 `hold`
以下，所以 deterministic argmax 永远不使用合法首事件动作。

## A6 设计推论

A6 不应从另一轮 broad reward-penalty pass 开始。下一机制必须直接给 first event 一个可学习的
value 或 timing signal。可行 contract 包括：

- `hold` vs `fire_once` 的 action-conditional event value head；
- `AuthorizedReady` windows 上的 first-event hazard objective；
- 有边界的 first-shot curriculum，用于产生可用 event labels，同时 A3/A5 masks 继续持有合法性。

长期优先形态是 event-value/hazard first，curriculum second as stabilization or data-generation aid。
这可以把合法性、时机和未来 sequence modeling 分开。

## 残余

本文没有验收任何 A6 implementation。它只把下一工作面从“继续调 reward”提升为
“设计并测试 event-value / first-event timing objective”。
