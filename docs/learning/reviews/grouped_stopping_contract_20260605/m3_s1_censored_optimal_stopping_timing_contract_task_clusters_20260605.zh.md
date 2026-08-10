# M3-S1 Censored Optimal-Stopping Timing Contract 任务簇

状态：`2026-06-05`，用于
[M3-S1 Censored Optimal-Stopping Timing Contract](README.zh.md) 的有限任务簇计划；
P5 validation dispatch 已启动。

## 边界决策

M3-S1 可以定义并随后实现一个有边界的 censored optimal-stopping timing contract。
它必须先拆清模型主干与分支。只有在 data/censoring 与 grouped-objective contracts
存在后，才允许打开代码修改。

本计划明确拒绝再做一次盲目的 A7 coefficient sweep，也拒绝 reward-only fire-discipline
repair。

## 有限任务簇列表

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `M3S1-P0 Boundary Map` | main thread | current main thread | 固定 trunk/branch/loss/reward ownership 与第一批切入点。 | `README*`, `m3_s1_model_architecture_boundary_map_20260605*.md`, parent/M3 indexes | training code、reward tuning、M2 release | `git diff --check -- docs/learning`；link inspection | Boundary map 足够清楚地命名 owners 与 forbidden couplings。 | serial first | 1 + 1 repair | pass |
| `M3S1-P1 Data Censoring Contract` | main thread or diagnostics worker | high reasoning | 定义 wait-preserving timing evidence、early-event censoring 处理与必要 rollout metadata。 | new `m3_s1_data_censoring_contract_*.md`；必要时仅 probe tests | PPO loss implementation、reward changes、policy-head changes | markdown review；必要时 optional probe script/test | Contract 选择 data route，并命名 unsupported evidence assumptions。 | after P0；serial | 2 | pass |
| `M3S1-P2 Grouped Objective Contract` | main thread | high reasoning | 定义基于 episode/window IDs 的 grouped survival/stopping objective。 | new objective contract doc；P1 后必要时可有 `python/rl/policy_algo` 设计注记 | per-row BCE tuning、A7 coefficient sweep | formula review；buffer grouping audit | Objective 保留 grouped windows，并包含 early-mass/censoring terms。 | after P1；serial | 2 | pass |
| `M3S1-P3 Policy Head Boundary` | main thread plus focused implementation worker | high reasoning | 决定 reuse-vs-new-head 与 deterministic stop boundary contract。 | contract doc；若打开代码则仅后续 `policies.py` tests | broad HMoE redesign、M2 release | opened 后 focused policy-distribution tests | Stop boundary、event-time calibration 与 diagnostics 已指定。 | after P2；serial | 2 | pass |
| `M3S1-P4 Minimal Integration` | implementation workers plus main-thread integration | high reasoning | 只实现 P1-P3 选中的 data/loss/head 最小改动。 | `python/rl/policy_algo/**`, focused tests, 必要 active config docs | reward-only fixes、legality weakening、broad training rewrites | focused unit/PPO/loss tests；compileall | Code path 有限，grouped labels 到达 loss，masks 继续权威。 | after P1-P3 accepted；P4-A/P4-B disjoint；P4-C serial | 2 | pass |
| `M3S1-P5 Diagnostics And Short Training` | diagnostics worker plus read-only evidence explorer | high reasoning | 增加/报告 boundary crossing、cumulative prewindow mass、no-event mass、grouped-label persistence 与 one-shot legality。 | diagnostics docs、probe scripts/tests、active config logs | focused gates 前 long formal training；coefficient tuning | focused m3s1 tests；diagnostics 存在后才写 short-train command/evidence packet | deterministic boundary 与 stochastic legality 带边界说明地报告。 | after P4 | 2 | active |
| `M3S1-P6 Closure And Archive Sync` | main thread | current main thread | 同步 model/A7/M3 indexes，并且只有在替代证据存在时归档旧 local repair docs。 | `docs/learning/**`, selected A7 docs/archive pointers | deleting evidence、无 probes 宣称 success | `git diff --check -- docs/learning docs/learning/reviews/optimal_stopping_model_selection_20260605/a7_event_value_advantage_credit_head_20260604` | Docs 区分 accepted slices、held learned behavior 与 residuals。 | after P5 | 1 | held |

## 分发规则

- 每个 worker packet 必须映射到上方唯一任务簇。
- worker 不得创建新的 Codex conversation thread。
- 不允许并发编辑 `ppo_adaptive_kl.py`、`first_event_hazard.py`、rollout buffers 或规范性
  README/status tables。
- P1-P3 串行，因为每一项都决定下一项合同。
- P1-P3 明确 accepted 后，P4 已通过。P4-A 与 P4-B 只在写入面互不重叠时并行；
  P4-C 保持串行。
- P5 短训只有在 focused loss/buffer/head tests 通过后才能开始。
- P5 拆为 `P5-A Diagnostics Surface` 与 `P5-B Short Training Evidence Path`。
  只有 P5-A 可以触碰 `ppo_adaptive_kl.py`，且同一时间只能有一个 worker 拥有该文件。
- 任一任务簇超过 round cap 时，停止并重新划定范围，而不是打开无边界 repair wave。

## Worker Packet 要求

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

实现 worker packet 还必须命名：

- 精确 write set；
- loss/reward/legality ownership boundary；
- 预期 diagnostics；
- rollback gate；
- 是否保留 grouped episode/window structure。

## 验证计划

```bash
git diff --check -- docs/learning
rg -n "M3-S1|Boundary Map|Data/Censoring|Grouped Objective|reward-only|per-row" docs/learning
```

代码打开后，验证必须扩展到 focused unit tests：

- first-event label grouping；
- grouped loss math；
- policy stop-boundary behavior；
- one-shot legality and mask authority；
- diagnostic metric emission。

## 验收标准

- P0-P3 contracts 存在，并且具体到 implementation 不需要依赖聊天记录。
- 若实现打开，必须保持 C2/ROE legality 与 action masks。
- Grouped timing objectives 不会静默坍缩成 independent per-row labels。
- Rewards、PPO base loss 与 auxiliary stopping losses 在文档和代码中保持分离。
- 在提出更长训练前，短训证据报告 deterministic boundary behavior 与 cumulative early-event mass。

## 残余地图

Immediate：

- `M3S1-P4A Policy Head Skeleton`、`M3S1-P4B Grouped Evidence/Loss Skeleton` 与
  `M3S1-P4C PPO Auxiliary Integration` 已通过。
- P5 只能作为 diagnostics/short-training validation 打开，不能变成又一轮 coefficient-tuning
  loop。当前 P5 evidence 追踪在
  [m3_s1_p5_dispatch_plan_20260605.zh.md](m3_s1_p5_dispatch_plan_20260605.zh.md)。

Follow-on：

- 决定第一个实现 objective 是 survival-hazard likelihood、ordinal margin fallback，还是
  offline direct stopping-distribution probe。

Deferred：

- M2 sequence-native causal Transformer release。
- broad reward-surface redesign。
- 任何 learned-policy acceptance claim。
