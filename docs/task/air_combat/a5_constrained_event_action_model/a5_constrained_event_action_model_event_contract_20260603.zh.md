# A5 事件动作合同

状态：`2026-06-03`，contract draft 已冻结，供 A5 实现使用。本文在 runtime 或
policy 编辑开始前定义 S1 C2/ROE 受约束 event-action 语义。

父级：[README.zh.md](README.zh.md)。输入：
[surface audit](a5_constrained_event_action_model_surface_audit_20260603.zh.md)。

## Boundary

本文不修改导弹物理、释放运动学、毁伤、Pk、引信行为或真实 BVR doctrine。它修改的是
accepted S1 C2/ROE training/eval entries 的 policy-facing release semantics。

核心拆分：

- 合法性和可用性属于 event state 与 action support；
- policy 只在 valid support 内学习 timing；
- reward 表达 outcome、timing、ammo 和 tracking preferences。

## Event State

`engagement_state` 是 policy-visible 的 finite state，用来定义 weapon-release event
support。A5 首版实现应使用这些值：

| Value | Meaning | Fire support |
| --- | --- | --- |
| `Hold` | C2/ROE、target、weapon 或 mission state 不允许 release。 | 仅 `hold` |
| `AuthorizedReady` | 首发 release 已授权，event 可用。 | `hold`、`fire_once` |
| `FiredAssess` | release 已被接受，episode 等待 missile outcome 或 assessment。 | 仅 `hold` |
| `ReattackReady` | assessment 或 mission state 显式允许 follow-on shot。 | `hold`、`fire_once` |
| `Winchester` | 没有可用武器，或 release path 不再可用。 | 仅 `hold` |

未来实现可以加入 terminal/disengage value，但 A5 首个 event-action gate 不依赖它。

## Mask Components

`fire_mask` 是 `fire_once` 的最终 action-support bit。它必须从具名 component 派生，
让 diagnostics 能解释 event 不可用的原因。

推荐 component names：

| Component | Meaning |
| --- | --- |
| `fire_mask_c2_authorized` | C2/ROE authorization 允许 release。 |
| `fire_mask_target_present` | 存在有效 assigned/primary target track。 |
| `fire_mask_shot_budget_available` | 当前 event cycle 仍有 shot budget。 |
| `fire_mask_not_pending_assessment` | no-fire assessment state 未阻塞首发或 salvo。 |
| `fire_mask_weapon_ready` | master arm、selected weapon 与 runtime weapon readiness 允许 release。 |
| `fire_mask_ammo_available` | selected weapon 仍有 ammunition。 |
| `fire_mask_reattack_allowed` | assessment 后显式授权 follow-on release。 |

最终 support rule：

```text
fire_mask =
  engagement_state in {AuthorizedReady, ReattackReady}
  and fire_mask_c2_authorized
  and fire_mask_target_present
  and fire_mask_shot_budget_available
  and fire_mask_weapon_ready
  and fire_mask_ammo_available
  and (
    engagement_state == AuthorizedReady
    or fire_mask_reattack_allowed
  )
  and fire_mask_not_pending_assessment
```

如果未来加入 salvo state，必须是显式 state 或显式 mask component。不能通过削弱
`FiredAssess` suppression 来表达。

## Event Action

policy-facing event action 为：

```text
event_action in {hold, fire_once}
event_action_mask = [1, fire_mask]
```

规则：

- `hold` 永远可用。
- `fire_once` 在 `fire_mask == 0` 时不可用。
- sampling 和 deterministic evaluation 必须使用同一个 mask。
- accepted S1 C2/ROE training entry 不得再用 raw
  `sigmoid(fire_weapon_logit) > 0.5` 或 continuous threshold 作为 event semantics。

## State Transitions

最小 transition contract：

| From | Condition | To | Notes |
| --- | --- | --- | --- |
| `Hold` | 所有 first-shot support components 为 true | `AuthorizedReady` | Fire 可用。 |
| `AuthorizedReady` | `event_action=hold` 且 support 仍为 true | `AuthorizedReady` | policy 可继续等待。 |
| `AuthorizedReady` | release 前 support 关闭 | `Hold` | 该 transition 本身不暗示 penalty。 |
| `AuthorizedReady` | `event_action=fire_once` 且 `fire_mask=1` | `FiredAssess` | release event 被接受并消费。 |
| `FiredAssess` | mission success 或 terminal condition | terminal/end state | 如果 terminal 已由别处处理，首版可不显式实现。 |
| `FiredAssess` | assessment complete，且无 ammo | `Winchester` | Fire 仍不可用。 |
| `FiredAssess` | assessment complete 且 reattack allowed | `ReattackReady` | follow-on fire 显式可用。 |
| `FiredAssess` | assessment complete 且无 reattack support | `Hold` | assessment 后默认 no-fire。 |
| `ReattackReady` | `event_action=fire_once` 且 `fire_mask=1` | `FiredAssess` | follow-on event 被接受并消费。 |
| `ReattackReady` | release 前 support 关闭 | `Hold` | 不存在隐式 repeated fire。 |

## Runtime Info Fields

runtime 与 diagnostics 应收敛到这些字段：

| Field | Meaning |
| --- | --- |
| `fire_once_requested` | policy 本步请求 `fire_once`。 |
| `fire_once_accepted` | runtime 接受并消费 event。 |
| `fire_once_rejected_reason` | requested fire 不可用时的稳定 reason string。 |
| `release_executed` | 实际发生 missile release。 |
| `post_launch_suppressed` | 因 assessment/no-fire state active，fire request 被抑制。 |
| `reattack_ready` | 显式 follow-on release support 可用。 |
| `engagement_state` | 当前 event state value。 |
| `fire_mask` | 最终 event action support bit。 |

推荐初始 `fire_once_rejected_reason` values：

- `masked_hold_only`
- `hold_state`
- `no_c2_authorization`
- `no_target`
- `shot_budget_empty`
- `pending_assessment`
- `weapon_not_ready`
- `ammo_empty`
- `reattack_not_authorized`

## Policy Semantics

首版实现：

```text
event_dist = MaskedCategorical(logits=[logit_hold, logit_fire], mask=[1, fire_mask])
```

训练：

```text
event_action ~ event_dist
```

deterministic evaluation：

```text
event_action = argmax_masked(event_dist)
```

log-prob 与 entropy 必须在 masked distribution 上计算。非法 `fire_once` 不得占据概率质量。
即使为了 SB3 兼容继续使用 flat transport，event head 仍拥有 policy log-prob 与 eval 语义。

## Reward Boundary

reward 可以评价：

- mission success 或 failure；
- missile effect；
- timing 与 opportunity cost；
- ammo usage；
- tracking 与 weapon-chain preparation。

reward 不应作为主要机制来：

- 教会 unauthorized fire illegal；
- 阻止 release 后 immediate repeated fire；
- 强制 shot budget；
- 在 assessment 期间 suppress fire。

这些都是 event-state 与 action-support 职责。

## Contract Test Requirements

实现簇必须新增或更新 tests，证明：

- `fire_mask=0` 强制 event action support 只有 `hold`。
- `AuthorizedReady + fire_once` 消费一个 event 并进入 `FiredAssess`。
- `FiredAssess` 即使 policy 请求 fire，也会 suppress immediate repeat fire。
- `ReattackReady` 是首版唯一能重新打开 `fire_once` 的 follow-on state。
- policy stochastic sampling、deterministic eval、log-prob 和 entropy 使用同一个 mask。
- diagnostics 区分 requested、accepted、rejected、executed 和 post-launch-suppressed fire。

## Acceptance Result

`A5-EAM-C Event Contract` 作为 contract draft 验收。它解锁 runtime 和 policy
implementation packets，但这些 packets 仍必须用 focused tests 证明合同。
