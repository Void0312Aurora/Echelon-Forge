# A5 受约束事件动作模型派发队列

状态：`2026-06-03`，dispatch queue。`A5-DQ-001` 至 `A5-DQ-004` 已返回 `pass`；
diagnostics/evidence 仍被 reward/config cleanup 阻塞。

父级：[README.zh.md](README.zh.md) 与
[任务簇](a5_constrained_event_action_model_task_clusters_20260603.zh.md)。

## Queue

| Packet | Cluster | Status | Write set | Expected output | Validation |
| --- | --- | --- | --- | --- | --- |
| `A5-DQ-001 Surface Audit` | `A5-EAM-B Surface Audit` | pass：`Lagrange` packet 已验收 | 仅 A5 docs，可选 read-only scan notes | action、observation、reward、policy、config、diagnostics 和 tests 触点图。 | read-only audit accepted |
| `A5-DQ-002 Contract Draft` | `A5-EAM-C Event Contract` | pass | `docs/standards/air/act*.md`、A5 docs | 稳定字段名和 event-state transition table。 | contract docs 已冻结；focused tests 留在 D/E |
| `A5-DQ-003 Runtime Prototype` | `A5-EAM-D Runtime State Machine` | pass：`Noether` packet 已验收 | `gym_envs/**`、`scenarios/air_combat/1v1/**`、runtime tests | Fire-once 状态转移和 post-launch suppression。 | focused runtime tests |
| `A5-DQ-004 Policy Prototype` | `A5-EAM-E Policy Event Head` | pass：`Hume` packet 已验收 | `python/rl/policy_algo/**`、HMoE/policy tests | Masked event distribution 或 event Q-head prototype。 | forward/evaluate/log-prob tests |
| `A5-DQ-005 Reward Config Cleanup` | `A5-EAM-F Reward And Config Cleanup` | ready | reward runtime/config tests 与 active S1 C2/ROE configs | 将 reward/config defaults 对齐 event-action 语义。 | reward/config focused tests |
| `A5-DQ-006 Evidence Packet` | `A5-EAM-G Diagnostics And Evidence` | blocked on DQ-005 | diagnostics tools、A5 evidence docs | deterministic/stochastic event-action evidence。 | diagnostics tests 与 probe logs |

## Dispatch Notes

- 不得创建新的会话线程。如果当前会话提供 subagents，只能在当前会话内派发 packet。
- `A5-DQ-001` 为只读任务，现已作为 planning evidence 验收。
- 不得 stage 或 commit `experiments_tmp`。
- `A5-DQ-002` 必须与实现 packets 串行，因为字段名会成为 contract 输入。
- `A5-DQ-003` 与 `A5-DQ-004` 已通过不重叠写集并行执行，并返回 `pass`。
- 如果 packet 无法在 round cap 内关闭，应返回 `partial` 和收窄后的 residual，而不是开启新 wave。

## Packet Template

```md
status: pass | partial | blocked | failed
cluster:
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```
