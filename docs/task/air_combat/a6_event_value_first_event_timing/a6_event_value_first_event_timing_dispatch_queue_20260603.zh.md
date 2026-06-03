# A6 分发队列

状态：`2026-06-03` 首轮、deadline waves、event-head update audit 和 event-head optimization
learned evidence 已完成。A6 因 launch-window timing quality 继续 held。

父级：[README.zh.md](README.zh.md)。任务簇计划：
[a6_event_value_first_event_timing_task_clusters_20260603.zh.md](a6_event_value_first_event_timing_task_clusters_20260603.zh.md)。

## Completed Queue

| Cluster | Dispatch status | Owner guidance | Write scope | Guard |
| --- | --- | --- | --- | --- |
| `A6-EVT-B Mathematical Framing` | pass | Arendt 已返回完整 packet。 | Framing notes 与 README links。 | 没有 code/config/scenario/test changes。 |
| `A6-EVT-C Objective Contract` | pass | Arendt 已返回完整 packet。 | Objective contract notes。 | 没有 code/config/scenario/test changes。 |
| `A6-EVT-D Training Kernel Prototype` | pass | Arendt 已返回完整 packet。 | `python/rl/policy_algo/**` 与 focused policy/training tests。 | 没有 config/probe/callback/scenario changes。 |
| `A6-EVT-E Scenario Config And Diagnostics` | pass | Arendt 返回 E；main thread 补完 runtime/rollout integration blockers。 | active configs、diagnostics、world-batch runtime info、non-finite probe parity、focused tests。 | A3/A5 合法性仍由 mask/state 持有。 |
| `A6-EVT-F Short Learned Evidence` | pass；held outcome | main thread 执行 `32768` 步训练与 deterministic/stochastic probes。 | evidence note only；`experiments_tmp` 不 staging。 | deterministic 未修复；stochastic discipline 保持。 |
| `A6-EVT-G Closure And Index Sync` | pass；re-scoped | main thread 与 Arendt 只读检查共同收敛到 deadline bootstrap 作为下一有边界 wave。 | A6 docs、必要时父级 indexes。 | A6 继续 held；M2 继续 held。 |
| `A6-EVT-H Deadline Bootstrap Implementation` | pass | main thread 实现 deadline labels/config/logging 与 tests。 | A6 label/PPO/logging code、独立 active config、focused tests、A6 docs。 | A3/A5 masks 保持；fixed-age teacher 不作为 doctrine 接受。 |
| `A6-EVT-I Deadline Short Learned Evidence` | pass；held outcome | main thread 执行 `32768` 步 deadline train 与 deterministic/stochastic probes。 | evidence note only；`experiments_tmp` 不 staging。 | deterministic 仍为 0 requests；stochastic 有 1 次 rejected request，但 0 violation/repeat/budget issues。 |
| `A6-EVT-J Event-Head Update-Strength Audit` | pass；held outcome | main thread 审计 A6 loss/optimizer routing，并新增 focused update-strength diagnostic test。 | `tests/hmoe/test_a6_event_head_update_strength.py`、A6 evidence note。 | 仅为 diagnostic；A6 与 M2 均继续 held。 |
| `A6-EVT-K Event-Head Optimization Lane` | pass；held timing residual | main thread 增加零初始化的专用 event-head optimizer lane、diagnostics、focused tests、独立 active config 和短训 learned evidence。 | `python/rl/policy_algo/policies.py`、focused tests、active config、A6 docs/evidence。 | deterministic crossing 已证明，但 release timing 近立即；A6 与 M2 held。 |

## Active Queue

| Cluster | Dispatch status | Owner guidance | Write scope | Guard |
| --- | --- | --- | --- | --- |
| `A6-EVT-L Launch-Window Timing Contract` | planned next | main thread 或 future worker；先做 design。 | 优先 A6 contract/status docs；contract accepted 后才进入 code/config。 | 把 authorization 与良好 launch timing 分开；保持 A3/A5 masks 权威，M2 held。 |

## Completed Blockers

| Cluster | Blocker | Unlock condition |
| --- | --- | --- |
| `A6-EVT-F Short Learned Evidence` | 曾需要 implementation tests。 | 已 unblocked 并完成；结果 held。 |
| `A6-EVT-G Closure And Index Sync` | 曾需要 learned evidence。 | 已由 F unblock，并作为 re-scope 完成。 |
| `A6-EVT-H Deadline Bootstrap Implementation` | 曾需要 re-scope decision。 | 已由 G unblock 并完成。 |
| `A6-EVT-I Deadline Short Learned Evidence` | 曾需要 deadline implementation tests。 | 已由 H unblock 并完成；结果 held。 |
| `A6-EVT-J Event-Head Update-Strength Audit` | 曾需要 deadline evidence。 | 已由 I unblock 并完成；结果 held。 |
| `A6-EVT-K Event-Head Optimization Lane` | 需要 update-strength diagnosis 与 learned evidence。 | 已由 J unblock，并作为 held timing residual 完成。 |
| `A6-EVT-L Launch-Window Timing Contract` | 需要 K evidence。 | 已由 K unblock；可进入 design/contract packet。 |

## Dispatch Packet Template

```md
cluster: A6-EVT-*
model / reasoning:
scope:
write set:
non-goals:
validation:
return packet:
```

## 集成说明

- 本工作严禁创建新的会话线程。
- 若使用 subagents，每个 worker 必须映射到一个 cluster，并遵从
  [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.zh.md)。
- `experiments_tmp` 不入 staging。
- M2 保持 held，除非后续 A6 evidence 显式触发 release vote。
