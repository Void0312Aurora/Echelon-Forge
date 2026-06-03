# A5 受约束事件动作模型派发队列

状态：`2026-06-03`，未来 work packets 的 ready queue。当前没有实际派发。

父级：[README.zh.md](README.zh.md) 与
[任务簇](a5_constrained_event_action_model_task_clusters_20260603.zh.md)。

## Queue

| Packet | Cluster | Status | Write set | Expected output | Validation |
| --- | --- | --- | --- | --- | --- |
| `A5-DQ-001 Surface Audit` | `A5-EAM-B Surface Audit` | ready | 仅 A5 docs，可选 read-only scan notes | action、observation、reward、policy、config、diagnostics 和 tests 触点图。 | markdown link check；不改 runtime |
| `A5-DQ-002 Contract Draft` | `A5-EAM-C Event Contract` | blocked on DQ-001 | `docs/standards/air/act*.md`、A5 docs | 稳定字段名和 event-state transition table。 | 提出或实现 contract tests |
| `A5-DQ-003 Runtime Prototype` | `A5-EAM-D Runtime State Machine` | blocked on DQ-002 | `gym_envs/**`、`scenarios/air_combat/1v1/**`、runtime tests | Fire-once 状态转移和 post-launch suppression。 | focused runtime tests |
| `A5-DQ-004 Policy Prototype` | `A5-EAM-E Policy Event Head` | blocked on DQ-002 | `python/rl/policy_algo/**`、HMoE/policy tests | Masked event distribution 或 event Q-head prototype。 | forward/evaluate/log-prob tests |
| `A5-DQ-005 Evidence Packet` | `A5-EAM-G Diagnostics And Evidence` | blocked on DQ-003/DQ-004 | diagnostics tools、A5 evidence docs | deterministic/stochastic event-action evidence。 | diagnostics tests 与 probe logs |

## Dispatch Notes

- 不得创建新的会话线程。如果当前会话提供 subagents，只能在当前会话内派发 packet。
- 不得 stage 或 commit `experiments_tmp`。
- `A5-DQ-002` 必须与实现 packets 串行，因为字段名会成为 contract 输入。
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
