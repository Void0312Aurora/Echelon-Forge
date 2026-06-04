# A7 Event-Value / Advantage Credit Head 任务簇

状态：`2026-06-04` finite task-cluster plan，用于
[README.zh.md](README.zh.md)。

## 边界决策

A7 可以为 masked `hold/fire_once` event action 增加 event-value / advantage-credit head
和 auxiliary objective。它不得削弱 A3/A5 legal masks，不得把 L label-weight scheduling
变成主修复，不得重设计 HMoE，不得释放 M2，也不得声明 missile/real-doctrine authority。

## 有限任务簇列表

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `A7-EVC-A Evidence And Architecture Intake` | main thread or read-only diagnostics worker | high | 对齐 A6-N、A6 label-density issue、HMoE gap 与当前 policy/PPO code entry points。 | 仅 A7 docs；可选 issue cross-links | code changes、training、HMoE redesign | Markdown review；code-surface references | Intake 命名 A7 必须解决什么，以及 HMoE gap 只能影响什么。 | First；B 前串行 | 1 | pass |
| `A7-EVC-B Objective Contract` | main thread | high | 定义 value/advantage targets、target source、losses、diagnostics 与 rollback gates。 | A7 contract/status docs | L-only tuning、M2 release、runtime legality changes | Contract review against A3/A5/A6-N | Contract 足够具体，可以实现，并拒绝 unsupported labels。 | After A；C/D 前串行 | 2 | pass |
| `A7-EVC-C Policy Head Prototype` | main thread plus read-only subagent review | high | 增加有边界的 event-value 或 advantage head，并暴露 outputs。 | `python/rl/policy_algo/policies.py`、focused policy tests | HMoE family/subexpert redesign、soft routing、M2 | focused policy tests；serialization/load smoke | Head zero-safe、shape-stable、optimizer-visible，并可接到 event logits。 | D 前完成；API 已稳定，可进入 PPO coupling。 | 2 | pass |
| `A7-EVC-D PPO Auxiliary Credit` | future implementation worker | high | 训练 A7 head，并将 advantage credit 接到 event-logit delta。 | `python/rl/policy_algo/**`、rollout/loss tests | Reward-only legality、削弱 masks | focused PPO/loss tests；finite stats | Loss 处理 masks、early censoring 与 counterfactual targets。 | After C API；E 前串行 | 2 | planned next |
| `A7-EVC-E Config And Diagnostics` | future implementation worker | medium | 增加 active config、callback/process-probe metrics 与累计 pre-window hazard。 | active configs、diagnostics/callback tests、docs | learned evidence、doctrine claims | config parse；diagnostics tests | A7 metrics 包含 advantage sign 与 cumulative early-fire probability。 | After D；只可与 F test refinement 并行 | 2 | planned |
| `A7-EVC-F Focused Validation Sweep` | main thread | n/a | 在 learned-policy probe 前运行 compile/JSON/focused tests。 | evidence note only unless tests require repair | training、broad refactor | compileall；pytest subset；`git diff --check` | Implementation ready for short learned evidence。 | After C/D/E | 1 | planned |
| `A7-EVC-G Short Learned Evidence` | main thread | n/a | 运行短训/probe，并与 A6-EVT-M 对比。 | A7 evidence note；不 stage `experiments_tmp` | formal long training、M2 release | train/probe commands；deterministic/stochastic summaries | evidence 记录 release timing、violations、advantage sign 与 cumulative hazard。 | After F；serial | 1 | planned |
| `A7-EVC-H Closure And Index Sync` | main thread | n/a | accept、hold 或 re-scope A7，并同步 parent/A6/issues docs。 | A7 docs、parent air-combat README、必要时 issue cross-links | hiding residuals、overclaiming stochastic-only behavior | `git diff --check -- docs/task/air_combat docs/task/issues` | status 与 indexes 和 evidence 一致。 | After G；serial | 1 | planned |

## 分发规则

- 每个 worker packet 必须精确映射到上表中的一个 cluster。
- 只从 `A7-EVC-C` 或后续 cluster 分发 implementation；`A7-EVC-B` 已由 objective
  contract 关闭。
- 不允许并行编辑同一个 policy-loss surface 或 status table。
- HMoE gap 在 A7 中只读，除非另建 issue-board implementation task。
- `experiments_tmp` 不入 staging。
- 若 cluster 超过 round cap，先停下重新 scope，再增加新 wave。

## Worker Packet 要求

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## 验证计划

Docs-only gate：

```bash
git diff --check -- docs/task/air_combat docs/task/issues
```

Implementation gates 必须包含 focused policy/PPO tests、active-entry/config tests、
diagnostics tests、JSON parsing、touched Python files 的 compileall，以及验收前的
learned-policy probe。

## 验收标准

- A7 objective 在 A5 masks 下直接提供 counterfactual hold/fire credit。
- Deterministic learned evidence 在配置的 quality window 内单次发射。
- Stochastic early-fire cumulative probability 被报告并有界。
- A3/A5 legality 与 one-shot discipline 保持完好。
- HMoE gap 被纳入考虑，但 A7 不变成 HMoE redesign。

## 残余地图

Immediate：

- 基于稳定 `hybrid_event_credit_head` API 的 PPO auxiliary-credit coupling。

Follow-on：

- 若 value credit 有效但训练不稳定，Adaptive label scheduling 可作为 guardrail。
- 只有当 A7 evidence 证明 HMoE hierarchical-computation 是活跃 blocker，才进入 HMoE repair。

Deferred：

- M2、HMoE soft routing、missile authority、`2v2`、self-play 与 doctrine。
