# A5 受约束事件动作模型当前状态

状态：`2026-06-03`，短训 learned-policy evidence 后 held。Surface audit、event
contract、runtime prototype、policy event head、reward/config cleanup 和 diagnostics
implementation 已验收；A5 仍未 accepted，因为短训 learned-policy probe 没有产生
deterministic `fire_once`。

## Decision

已选长期方案是：

```text
显式交战状态机
+ C2/ROE/weapon action-support mask
+ 独立事件动作 head：hold / fire_once
+ post-launch FiredAssess 禁射状态
+ 显式 ReattackReady 后续入口
```

首版实现应采用 masked categorical event semantics：它能修复结构性多发和
stochastic/deterministic eval mismatch，同时兼容当前 PPO stack。需要价值比较时，event
Q-head 是优先 follow-on。hazard / first-event 和完整 hierarchical options 暂缓。

## Why A4 Is Not Enough

| Symptom | A4 evidence | A5 interpretation |
| --- | --- | --- |
| deterministic policy 不发射 | retained A4 32k routed probe 仍为 `0 fire / 0 release` | event head 跨不过 deterministic threshold，因为动作语义和训练数据对稀有 fire event 不友好。 |
| stochastic policy 仍产生坏 release | retained stochastic probe 能 fire/release，但包含 violations/invalid attempts | 只要逐帧采样仍存在，重复或无效 event attempts 就会自然出现，除非 action support 结构性移除。 |
| reward urgency trial 失败 | bounded opportunity penalty 没推动 deterministic fire，且恶化 release discipline | 增大奖励压力不能修复错误的 event-action model。 |
| binary fire probability 仍很低 | authorized-window fire probability 约 `0.22%`，max logit 约 `-6.11` | fire 被学成了长序列中的稀有 pulse，而不是 finite-window event decision。 |

## Selected Architecture Surface

| Surface | Planned A5 treatment | Risk |
| --- | --- | --- |
| `engagement_state` | 显式 policy-visible state，例如 `Hold`、`AuthorizedReady`、`FiredAssess`、`ReattackReady`、`Winchester`。 | 字段命名必须对齐 A3 mission observation 和 M1 action contract。 |
| `fire_mask` | 由 C2/ROE、weapon state、ammo、pending assessment 和 reattack permission 派生的最终 action-support bit。 | 避免只给一个 opaque mask，而不暴露主要解释字段。 |
| `event_action` | `hold/fire_once`，只在合法 support 中采样。 | PPO rollout/log-prob 不应纳入非法动作概率。 |
| post-launch behavior | accepted `fire_once` 立即进入 `FiredAssess`，fire 禁止直到显式后续状态。 | 必须区分默认 suppression 与 intentional salvo/reattack rules。 |
| reward | 表达 mission result、effect、timing、ammo cost 和 tracking preference。 | 不得把 invalid-fire penalty 重新变成主要合法性机制。 |
| evaluation | 使用 masked argmax 或 event-value comparison，不用 raw `sigmoid(logit)>0.5` threshold。 | deterministic behavior 必须能被 diagnostics 审计。 |

## Latest Learned Evidence

A5 post-change 短训记录在
[a5_constrained_event_action_model_short_learned_probe_20260603.zh.md](a5_constrained_event_action_model_short_learned_probe_20260603.zh.md)。

摘要：

- deterministic probe：`1880` 个 fire-mask-open / `AuthorizedReady` steps，但
  `0` fire requests、`0` releases；masked event fire probability 仍约 `0.217%`
  mean / `0.278%` max。
- stochastic probe：3 个 episode，4 次 fire requests，3 次 accepted requests，
  3 次 releases，3 次均为 authorized，`0` violation releases，`0` repeat 或
  shot-budget violations。

这说明 A5 结构性修复了 stochastic 多发 / release discipline，但 deterministic timing
仍 held。

## Immediate Work

1. 继续 fail-closed 地同步 A3/A4/M1/M2 与父级索引，使 A5 保持 held closure，且不得过度声明
   accepted。
2. 继续已创建的 A6 follow-on：
   [../a6_event_value_first_event_timing/README.zh.md](../a6_event_value_first_event_timing/README.zh.md)。
   A6 下一步是 mathematical framing 和 objective-contract selection，候选机制包括
   event-value、显式 first-shot curriculum，或 hazard / first-event timing。

## Continuation Decision

后续只能通过新的 A5-trained short evidence run 继续。既有 A3/A4/M1 模型不能作为 A5
learned-policy evidence，因为 hybrid policy head 已从旧 19 参数 layout 变为新的 20 参数
event-action layout。对
`experiments_tmp/a4_authorized_first_shot_routed_retained_temporal_32k_20260603/final_model.zip`
的快速加载检查已经失败，报错为 `action_net` 与 HMoE heads 的 shape mismatch（`19`
versus `20`）。因此直接探测旧 checkpoint 只能证明兼容性问题，不能证明 A5 行为。

## Accepted Planning Evidence

- Surface audit：
  [a5_constrained_event_action_model_surface_audit_20260603.zh.md](a5_constrained_event_action_model_surface_audit_20260603.zh.md)
- Event action contract：
  [a5_constrained_event_action_model_event_contract_20260603.zh.md](a5_constrained_event_action_model_event_contract_20260603.zh.md)
- Air action contract overlay：
  [../../../standards/air/act.zh.md](../../../standards/air/act.zh.md)
- Implementation evidence：
  [a5_constrained_event_action_model_implementation_evidence_20260603.zh.md](a5_constrained_event_action_model_implementation_evidence_20260603.zh.md)
- 短训 learned-policy probe：
  [a5_constrained_event_action_model_short_learned_probe_20260603.zh.md](a5_constrained_event_action_model_short_learned_probe_20260603.zh.md)

## Open Risks

- 当前 loaded-model HMoE residual gate 可能恢复到 start factor，而不是 trained gate value。
  在依赖 learned residual event behavior 前，A5 需要修复或显式处理这一点。
- 如果 `fire_mask` 过严，策略学不到 timing；如果过松，A5 会重新引入 invalid samples。
  contract 需要 component fields 和 diagnostics，不能只有 final bit。
- masked categorical event head 能修复结构性重复，但如果 `hold` 局部仍更容易，可能还需要
  window-level exploration 或 event Q-head。

## Forbidden Conclusions

- A5 是 held after evidence，尚未 accepted。
- A5 不释放 M2。
- A5 不修改导弹物理、毁伤、Pk、引信或真实 doctrine。
- A5 不让 `2v2` 或 self-play 进入范围。
