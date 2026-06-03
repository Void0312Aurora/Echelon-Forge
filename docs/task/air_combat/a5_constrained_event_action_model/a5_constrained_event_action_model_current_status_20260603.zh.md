# A5 受约束事件动作模型当前状态

状态：`2026-06-03`，implementation checkpoint。Surface audit、event contract、
runtime prototype 和 policy event head 已验收；reward/config cleanup、diagnostics/evidence
和 closure 仍待推进。

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

## Immediate Work

1. 更新 S1 C2/ROE active entries 和 diagnostics。
2. 运行 focused diagnostics 与 learned-policy probes。
3. 基于 residual map 判定 accepted 或 held。

## Accepted Planning Evidence

- Surface audit：
  [a5_constrained_event_action_model_surface_audit_20260603.zh.md](a5_constrained_event_action_model_surface_audit_20260603.zh.md)
- Event action contract：
  [a5_constrained_event_action_model_event_contract_20260603.zh.md](a5_constrained_event_action_model_event_contract_20260603.zh.md)
- Air action contract overlay：
  [../../../standards/air/act.zh.md](../../../standards/air/act.zh.md)
- Implementation evidence：
  [a5_constrained_event_action_model_implementation_evidence_20260603.zh.md](a5_constrained_event_action_model_implementation_evidence_20260603.zh.md)

## Open Risks

- 当前 loaded-model HMoE residual gate 可能恢复到 start factor，而不是 trained gate value。
  在依赖 learned residual event behavior 前，A5 需要修复或显式处理这一点。
- 如果 `fire_mask` 过严，策略学不到 timing；如果过松，A5 会重新引入 invalid samples。
  contract 需要 component fields 和 diagnostics，不能只有 final bit。
- masked categorical event head 能修复结构性重复，但如果 `hold` 局部仍更容易，可能还需要
  window-level exploration 或 event Q-head。

## Forbidden Conclusions

- A5 尚未 accepted。
- A5 不释放 M2。
- A5 不修改导弹物理、毁伤、Pk、引信或真实 doctrine。
- A5 不让 `2v2` 或 self-play 进入范围。
