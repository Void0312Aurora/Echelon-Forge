# A6 Deadline-Bootstrap Re-scope

状态：`2026-06-03` 首次 learned evidence held 后的 active implementation wave。

父级：[README.zh.md](README.zh.md)。前序证据：
[a6_event_value_first_event_timing_short_learned_probe_20260603.zh.md](a6_event_value_first_event_timing_short_learned_probe_20260603.zh.md)。

## 决策

首个 A6 objective 已经证明 first-event labels、rollout buffer、PPO loss、
diagnostics 和 world-batch runtime plumbing 都真实接通。但它没有推动 deterministic
`fire_once`：deterministic probe 在 `1840` 个 open-window steps 下仍为 `0` requests，
fire probability 约 `0.25%`。

下一 wave 继续留在 A6 内，并增加 deadline bootstrap：

- A3/A5 合法性继续由 mask/state-machine 持有；
- 保留 `hold/fire_once` event head 和 A6 hazard loss path；
- 在授权 open-window 达到配置的年龄阈值后，提供持续 first-event 正例；
- 使用独立 active config，因此首次 hazard/curriculum evidence 的复现实验入口不被覆盖。

## 本轮拒绝路径

| Path | 决策 | 原因 |
| --- | --- | --- |
| M2 release vote | 本 wave 拒绝 | 当前失败已收窄到既有 A3/A5 event surface 下的 event-logit credit；还没有证据证明必须释放 sequence-native modeling。 |
| 单纯调 hazard/curriculum 超参 | 不作为主线 | 首次运行已显示一次短暂衰减 seed 太弱。仅放大同一 transient signal 不像长期机制。 |
| 完整 event-value head | deferred | 它仍是更强的长期候选，但在测试 sustained labels 之前新增 value surface 会混合 bootstrapping 和架构风险。 |
| reward-only legality penalties | 拒绝 | A3/A5 合法性是 mask/state-owned，A4 reward-only 路线没有让 deterministic fire。 |

## Objective Contract

对每个 first authorized open window `W`，定义 `age_t` 为窗口内从 1 开始的年龄。若窗口中存在
accepted release，则 accepted-release labels 优先。若没有 accepted release：

```text
deadline_t = age_t >= a6_first_event_deadline_min_window_age_steps
target_t = 1 if deadline_t else inactive
weight_t = a6_first_event_deadline_weight if deadline_t else 0
source_t = deadline when target_t is active
```

这不是“固定年龄发射为真实最优战术”的 doctrine claim。它只是一个有边界的 bootstrap，
用来回答更简单的问题：当正信号在 open window 中持续存在，而不是只出现一次并快速衰减时，
当前 event head 与 PPO stack 能否推动 deterministic masked argmax。

## Implementation Surface

- `python/rl/policy_algo/first_event_hazard.py`
  - 增加 `A6_FIRST_EVENT_SOURCE_DEADLINE`；
  - 增加 deadline label 参数；
  - 在达到配置窗口年龄后输出持续正例。
- `python/rl/policy_algo/ppo_adaptive_kl.py`
  - 接受 `a6_first_event_deadline_weight` 与
    `a6_first_event_deadline_min_window_age_steps`；
  - 将 deadline knobs 传入 label construction；
  - 记录 `a6/deadline_weight`。
- `python/rl/support/nonfinite_probe.py`
  - 在 traced PPO path 中保留 deadline-enabled A6 logging。
- `python/training_callbacks.py`
  - 当存在 label diagnostics 时记录 deadline-positive label counts。
- `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_shaped_world_batch_probe_v1.json`
  - 提供独立 deadline-bootstrap training entry。

## Acceptance Gate

本 wave 只有在以下条件满足时才可能产生 accepted A6 result：

- focused tests 通过，覆盖 deadline label/source/config/logging 行为；
- deterministic probe 至少产生一次授权 `fire_once` request 与 release，或者 event probability
  实质移动并记录精确 blocker；
- stochastic probe 保持 A5 discipline：每个 episode 一次授权 release，零 rejected requests，
  零 violation releases，零 repeat/budget violations；
- 文档继续明确 deadline bootstrap 不是真实 tactics、M2、missile physics、Pk、fuze、
  damage authority、`2v2` 或 self-play release。

## Next Evidence

运行 deadline-bootstrap short training entry，然后对其 `final_model.zip` 执行 deterministic /
stochastic probes。改变 A6 acceptance status 之前，必须把结果写入独立 learned evidence note。
