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
| `A7-EVC-D PPO Auxiliary Credit` | main thread plus read-only subagent scan | high | 训练 A7 head，并将 advantage credit 接到 event-logit delta。 | `python/rl/policy_algo/**`、rollout/loss tests | Reward-only legality、削弱 masks | focused PPO/loss tests；finite stats | Loss 处理 masks、early censoring 与 counterfactual targets。 | E 前完成；尚未运行 learned-policy。 | 2 | pass |
| `A7-EVC-E Config And Diagnostics` | implementation worker | medium | 增加 active config、callback/process-probe metrics 与累计 pre-window hazard。 | active configs、diagnostics/callback tests、docs | learned evidence、doctrine claims | config parse；diagnostics tests | A7 metrics 包含 advantage sign 与 cumulative early-fire probability。 | After D；只可与 F test refinement 并行 | 2 | pass |
| `A7-EVC-F Focused Validation Sweep` | main thread | n/a | 在 learned-policy probe 前运行 compile/JSON/focused tests。 | evidence note only unless tests require repair | training、broad refactor | compileall；pytest subset；`git diff --check` | Implementation ready for short learned evidence。 | After C/D/E | 1 | pass |
| `A7-EVC-G Short Learned Evidence` | main thread | n/a | 运行短训/probe，并与 A6-EVT-M 对比。 | A7 evidence note；不 stage `experiments_tmp` | formal long training、M2 release | train/probe commands；deterministic/stochastic summaries | evidence 记录 release timing、violations、advantage sign 与 cumulative hazard。 | After F；serial | 1 | pass；held outcome |
| `A7-EVC-H Closure And Index Sync` | main thread | n/a | accept、hold 或 re-scope A7，并同步 parent/A6/issues docs。 | A7 docs、parent air-combat README、必要时 issue cross-links | hiding residuals、overclaiming stochastic-only behavior | `git diff --check -- docs/task/air_combat docs/task/issues` | status 与 indexes 和 evidence 一致。 | After G；serial | 1 | pass；held sync |
| `A7-EVC-I Target Construction And Credit Sign Audit` | main thread 或 read-only diagnostics worker | high | 解释为什么 A7 quality-window advantage 仍为负，并决定继续训练前是否需要 target/loss repair。 | A7 evidence/status docs | 继续 32k training、HMoE redesign、M2 release、削弱 A3/A5 masks | label reconstruction；code-surface review；docs diff check | Audit 将 early stochastic accepted release 后缺失 shadow-quality target repair 命名为失败环节。 | After H；serial | 2 | pass；spawned J repair |
| `A7-EVC-J Shadow Quality Target Repair` | implementation worker plus read-only diagnostics review | high | 修复 target construction，使 early accepted release 不再从 target credit 中删失 future quality-window evidence。 | `python/rl/policy_algo/first_event_hazard.py`、`python/rl/policy_algo/ppo_adaptive_kl.py`、`python/training/diagnostics.py`、`tests/hmoe/**` 与 `tests/training/**` focused tests、A7 docs、active config | runtime legality changes、削弱 A3/A5 masks、HMoE redesign、M2 release | focused target-construction tests；compileall；focused PPO/loss tests；docs diff check；short repair probe | Shadow quality evidence 在 early accepted release 后恢复，post-release shadow rows 不通过 event-logit delta alignment 训练，且 repair probe 记录剩余 behavior。 | After I；K 前串行 | 2 | pass；held outcome |
| `A7-EVC-K Legal-State Projection And Coupling Audit` | main thread 或 diagnostics worker | high | 解释 repaired shadow positives 为什么仍未让 legal-open quality states 学到 positive event advantage。 | 优先 A7 docs；只有在写出有边界 contract 后才增加 optional focused diagnostics/tests | coefficient-only tuning、继续盲跑 32k training、削弱 A3/A5 masks、HMoE redesign、M2 release | label/value/coupling audit；repaired-run probe review；docs diff check | Audit 在下一轮 training 前区分 target projection、value-head learning、delta alignment、policy distillation 与 HMoE-routing hypotheses。 | After J；串行 | 2 | pass；spawned L contract |
| `A7-EVC-L Legal-State Projection Contract` | main thread | high | 选择 legal-state projection 机制，在不做 closed-mask delta alignment 的前提下把 shadow-quality evidence 转成 legal-open positive credit。 | 仅 A7 contract/status docs | implementation、training、削弱 A3/A5 masks、HMoE redesign、M2 release | contract review；docs diff check | Contract 命名 projection whitelist、loss split、implementation entry points 与 validation gates。 | After K；串行 | 1 | pass；已由 M 实现 |
| `A7-EVC-M Projected Legal-Open Credit Prototype` | implementation worker plus diagnostics review | high | 实现 L 合同：对 shadow-quality rows 构造 projected legal-open value/delta alignment，同时 raw closed-mask rows 保持 value-only/opportunity-only。 | `python/rl/policy_algo/first_event_projection.py`、`python/rl/policy_algo/first_event_hazard.py`、`python/rl/policy_algo/ppo_adaptive_kl.py`、focused tests、active config/diagnostics docs | closed-mask delta alignment、runtime fire-mask weakening、broad HMoE/M2 work、focused gates 前盲跑 32k training | projection helper tests；PPO/loss tests；active config/diagnostics tests；compileall；docs diff check | Projected positives 产生 legal-open credit pressure，unsupported layouts 被报告，A3/A5 masks 继续权威。 | After L；串行 | 2 | pass；N 后 learned behavior held |
| `A7-EVC-N Short Projection Learned Evidence` | main thread | n/a | M 后运行有边界 learned-policy probe，并与 J repair evidence 对照 projected-credit behavior。 | A7 evidence/status docs；`experiments_tmp` 不入 staging | formal long training、M2 release、HMoE redesign、missile/doctrine authority | train/probe commands；deterministic/stochastic summaries；projection metrics；docs diff check | Evidence 记录 projected credit 是否改变 deterministic timing、stochastic early-fire、one-shot discipline 与 projected advantage/delta signs。 | After M；串行 | 1 | pass；held outcome |
| `A7-EVC-O Projection Eligibility Root-Cause Audit` | main thread 或 diagnostics worker | high | 解释为什么 projection 已启用且 focused projected-loss tests 已通过，但 learned run 中 `a7/evc_proj_active_count_mean` 仍为 `0.0`。 | 优先 A7 docs；只有在隔离失败 handoff 后才增加 optional focused diagnostics/tests | 继续盲跑 32k training、coefficient tuning、削弱 A3/A5 masks、HMoE redesign、M2 release | TensorBoard/probe review；rollout/loss label-source audit；只针对 confirmed interface gap 增加 focused test；docs diff check | Audit 命名 candidate starvation：N train diagnostics 中没有 accepted releases，而 stochastic probe reconstruction 在 early release 后能产生 shadow candidates。 | After N；串行 | 2 | pass；spawned P contract |
| `A7-EVC-P Legal-Open Opportunity Credit Contract` | main thread | high | 定义不依赖采样 early accepted release 的 positive legal-open opportunity credit。 | A7 contract/status docs | implementation、training、削弱 A3/A5 masks、closed-mask delta alignment、HMoE redesign、M2 release | contract review；docs diff check | Contract 为 non-starved opportunity-credit path 选择 target source、loss split、diagnostics 与 rollback gates。 | After O；串行 | 1 | pass；spawned Q prototype |
| `A7-EVC-Q Legal-Open Opportunity Credit Prototype` | implementation worker plus diagnostics review | high | 按 P 合同实现 direct legal-open quality-window positives，使 credit 不再需要先采样 early release。 | `python/rl/policy_algo/first_event_hazard.py`、`python/rl/policy_algo/ppo_adaptive_kl.py`、`python/rl/support/nonfinite_probe.py`、focused tests、active config/diagnostics docs | broad reward tuning、削弱 A3/A5 masks、raw shadow delta alignment、HMoE redesign、M2 release、focused gates 前 training | source-construction tests；PPO/loss tests；nonfinite-probe metric test；active config/diagnostics tests；compileall；docs diff check | Legal-open quality positives 进入 ordinary A7 value/delta credit，shadow projection 继续分离，source metrics 证明该路径不再 candidate-starved。 | After P；串行 | 2 | planned next |

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

- `A7-EVC-Q Legal-Open Opportunity Credit Prototype`。

Follow-on：

- 只有当 projection prototype 暴露剩余的有界 weighting issue 后，Adaptive label scheduling
  才作为 guardrail。
- 只有当 A7 学到正确 credit signs 后仍出现可归因于 hierarchy 的 policy coupling
  failure，才进入 HMoE repair。

Deferred：

- M2、HMoE soft routing、missile authority、`2v2`、self-play 与 doctrine。
