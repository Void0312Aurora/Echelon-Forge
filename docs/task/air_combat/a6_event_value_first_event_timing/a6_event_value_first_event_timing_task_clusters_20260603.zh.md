# A6 事件价值与首事件时机任务簇

状态：`2026-06-03` finite task-cluster plan，用于
[README.zh.md](README.zh.md)，已推进到 event-head learned evidence 与 launch-window
timing residual 后的 re-scope。

## 边界决策

A6 可以改变 masked `hold/fire_once` event 的 policy/training objective，但不得削弱
A3/A5 合法性约束，不得释放 M2，也不得把 reward-only penalties 当作主修复。首个可验收实现必须直接处理
event-value 或 first-event timing。

## 有限任务簇列表

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `A6-EVT-A Observation Baseline` | main thread | n/a | 创建 A6，并冻结 A5 retained deterministic/stochastic evidence。 | `docs/task/air_combat/a6_event_value_first_event_timing/**`、父级 air-combat READMEs | 代码改动、新训练、staging `experiments_tmp` | `jq` summaries；`git diff --check -- docs/task/air_combat` | A6 docs 存在，observation 解释为什么 A6 不是 reward-only tuning。 | First；serial | 1 | pass |
| `A6-EVT-B Mathematical Framing` | Arendt | inherited, high | 形式化 masked first-event timing、delayed sparse credit、label sources 和 failure modes。 | 本子项目下 A6 design note | PPO 实现、scenario rewrites、M2 | Markdown inspection；link check | 设计命名 objective inputs/outputs，并拒绝不可用 labels。 | After A；can run before C only | 2 | pass |
| `A6-EVT-C Objective Contract` | Arendt | inherited, high | 选择首个 contract：event-value head、hazard objective、curriculum-assisted labels，或 staged combination。 | 仅 A6 contract note；返回后由 main thread 负责 status/index integration | broad reward penalty tuning、removing masks、sequence PPO | Contract review against A3/A5 constraints | selected objective 有 masks、diagnostics、tests 和 rollback criteria。 | After B；serial before D/E | 2 | pass |
| `A6-EVT-D Training Kernel Prototype` | Arendt | inherited, high | 实现 selected masked first-event hazard auxiliary loss，并补 policy/PPO tests。 | `python/rl/policy_algo/**`、focused training/policy tests | M2、self-play、missile physics、config/probe/callback integration、超出 selected objective 的 broad PPO rewrite | Focused policy/PPO tests | tests 证明 shape、loss、mask、deterministic eval、finite stats 和 masked categorical semantics 未改变。 | After C；field/loss interface 稳定前与 E 串行 | 2 | pass |
| `A6-EVT-E Scenario Config And Diagnostics` | Arendt + main thread | inherited, medium | 将维护中的 S1 C2/ROE training entry 与 diagnostics 接到 A6 metrics。 | `examples/config/training/active/air_combat/**`、`tools/diagnostics/**`、`python/training_callbacks.py`、`python/rl/runtime/world_batch_vec_env.py`、相关 tests | 新 scenario maturity claims、通过 reward penalties 管合法性 | Active-entry、diagnostics、non-finite probe parity、world-batch info tests | A6 metrics 可见，A3/A5 合法性仍由 mask/state 持有。 | D 暴露 field/loss interface 后 | 2 | pass |
| `A6-EVT-F Short Learned Evidence` | main thread | n/a | 基于 A5 baseline 跑短训/探针并记录结果。 | A6 evidence note；不 stage `experiments_tmp` | formal long training、M2 release | Training command plus deterministic/stochastic probes | evidence 记录 event probability/mode、requests、releases、violations 和 blocker status。 | After D/E tests pass；serial | 1 | pass；held outcome |
| `A6-EVT-G Closure And Index Sync` | main thread | n/a | accept、hold 或 re-scope A6，并同步 A3/A4/A5/M1/M2/parent indexes。 | A6 docs、父级 air-combat READMEs、必要时相关 model docs | hiding residuals、accepting stochastic-only behavior | `git diff --check`；focused doc/link inspection | status 和 indexes 与 evidence 一致。 | After F；serial | 1 | pass；re-scoped |
| `A6-EVT-H Deadline Bootstrap Implementation` | main thread | n/a | 为下一 A6 wave 增加持续 deadline labels 与独立 probe entry。 | `python/rl/policy_algo/**`、`python/rl/support/nonfinite_probe.py`、`python/training_callbacks.py`、active config README/JSON、focused tests、A6 docs | M2 release、reward-only legality、削弱 A5 masks、改变 missile/damage authority | compileall；focused A6/config/diagnostics tests | deadline source/weight/config/logging 有覆盖；旧 hazard evidence config 保持独立。 | After G；serial before I | 1 | pass |
| `A6-EVT-I Deadline Short Learned Evidence` | main thread | n/a | 运行 deadline 短训/探针并记录 deterministic/stochastic outcomes。 | A6 evidence note；不 stage `experiments_tmp` | formal long training、把 fixed-age teacher 当 doctrine 接受 | Training command plus deterministic/stochastic probes | evidence 记录 event probability/mode、requests、releases、violations，以及 deadline bootstrap accepted/held。 | After H tests pass；serial | 1 | pass；held outcome |
| `A6-EVT-J Event-Head Update-Strength Audit` | main thread | n/a | 判定为什么持续正例只把 event probability 推到约 `0.5%`。 | `tests/hmoe/test_a6_event_head_update_strength.py`、A6 evidence note | M2 release、update audit 前实现 value-head、reward-only legality | focused gradient/update probe；unit probe 不能单独作为 learned-policy acceptance | Audit 识别 optimizer/head scaling blocker，或为 event-value head 清路。 | After I；serial | 1 | pass；held outcome |
| `A6-EVT-K Event-Head Optimization Lane` | main thread | n/a | 为 `hold/fire_once` event rows 增加更强但有边界的更新路径与 diagnostics。 | `python/rl/policy_algo/**`、focused tests、必要时 A6 docs/config | M2 release、削弱 masks、broad reward-only legality、missile/damage authority | compileall；focused policy/PPO tests；短训 learned probe | event-row LR/diagnostics 可见，并且 learned evidence 要么显示 deterministic crossing，要么留下精确 held residual。 | After J；event-value head 前串行 | 2 | pass；held timing residual |
| `A6-EVT-L Launch-Window Timing Contract` | main thread 或 dispatched worker | inherited, high | 定义有边界的 timing-quality contract，把合法 authorization 与良好 first-release timing 分开。 | 优先 A6 design/contract/status docs；contract accepted 后才进入 code/config | M2 release、missile/damage authority、真实 doctrine claims、削弱 A3/A5 masks | 按 K evidence 做 contract review；实现后再补 focused tests | contract 命名 label source、window predicates、rejection handling、diagnostics 与 acceptance/rollback gates。 | After K；更多训练改动前串行 | 2 | planned |

## 分发规则

- 每个 worker packet 必须精确映射到上表中的一个 cluster。
- 不允许两个 worker 同时编辑同一个 normative table、status line、scenario contract 或
  policy-loss surface。
- `A6-EVT-C`、`A6-EVT-F` 和 `A6-EVT-G` 必须串行。
- `A6-EVT-C Objective Contract` 未关闭前，不分发 implementation。
- 若 cluster 超过 round cap，先停下重新 scope，再考虑新 wave。
- 遵从
  [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.zh.md)。

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

初始 docs-only gate：

```bash
git diff --check -- docs/task/air_combat
```

Implementation gates 由 `A6-EVT-C` 定义，但必须包含 focused policy/PPO tests、
active-entry/config tests、diagnostics tests，以及至少一次短训 learned-policy probe。

## 验收标准

- selected objective 直接移动 masked event timing，而不是 raw `fire_weapon` thresholding。
- A3/A5 合法性仍由 mask/state transitions 持有。
- deterministic learned evidence 相对 A5 baseline 有实质改善，或 residual 被精确归属到
  reward-only legality tuning 之外。
- M2 和更广 combat maturity claims 继续 held。

## 残余地图

Immediate：

- Launch-window / engagement-quality timing contract。

Follow-on：

- 若 timing contract 在合法/timing labels 分离后仍缺 value credit，则进入 event-value /
  advantage head。

Deferred：

- M2 sequence-native PPO/HMoE。
- `2v2`、self-play、missile physics、Pk、fuze 和 damage authority。
