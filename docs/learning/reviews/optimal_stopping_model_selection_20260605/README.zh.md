# M3 Optimal-Stopping Model Selection

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/learning/reviews/optimal_stopping_model_selection_20260605/README.md`
Owner: `learning/reviews`
Last verified: `2026-08-08`
Review basis：`2026-06-05` 问题定义、研究包与综合结论。

状态：`2026-06-05` model-selection synthesis complete；后续 planning contract 已作为 M3-S1
打开，但训练代码仍 held。

语言：

- 英文主文：[README.md](README.md)
- 中文配套：`README.zh.md`

输入：

- 父级模型任务索引：[模型任务](../../../task/model/archive/owner_migration_20260808/README.zh.md)
- A7 当前证据：
  [A7 当前状态](../../../task/air_combat/archive/a7_event_value_advantage_credit_head/a7_event_value_advantage_credit_head_current_status_20260604.zh.md)
- A7 执行断点：
  [A7 执行断点分析](../../../task/air_combat/archive/a7_event_value_advantage_credit_head/a7_event_value_advantage_credit_head_execution_breakpoint_analysis_20260605.zh.md)
- A7 event-policy margin 修复：
  [A7 Event-Policy Margin 修复](../../../task/air_combat/archive/a7_event_value_advantage_credit_head/a7_event_value_advantage_credit_head_event_policy_margin_repair_20260605.zh.md)
- 子项目标准：
  [子项目创建标准](../../../engineering/automation/rules/subproject_creation_standard.zh.md)
- 分发规则：
  [Subagent 使用规范](../../../engineering/automation/standards/subagent_usage_policy.zh.md)

## 目的

M3 将 A7 first-event timing 的堵塞状态转化为模型选择问题。当前目标不是再做一次
coefficient sweep，也不是继续给 A7 打补丁，而是定义该失败背后的抽象数学对象，并比较哪些
模型族能以更低结构风险解决这个对象。

军事场景只作为一个实例。核心问题是通用的一次性时机决策：agent 观察序列，最多选择一次
事件时间；过早事件应被避免，事件应落在 desirable window 内；由于早期事件会改变后续轨迹，
on-policy 数据存在删失。

## 当前状态

| Area | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| A7 local repairs | held | A7 已有 labels、credit-head capacity、direct event-policy margin 和 one-shot legality，但 deterministic probing 仍是 `0` releases，active event-credit rows 在训练后期坍缩。 | 不支持默认继续 A7 coefficient sweep。 |
| 数学抽象 | pass | [Formal problem statement](m3_formal_problem_statement_20260605.md) 定义 censored constrained one-shot timing problem。 | 不实现所选模型。 |
| 分布式调研 | pass | R1/R2/R3 research packets 已完成并分别成文。 | 调研结果是 evidence inputs，不是 runtime changes。 |
| 模型选择综合 | pass | [Model-selection synthesis](m3_model_selection_synthesis_20260605.md) 推荐 censored optimal-stopping timing contract，配合 survival/event-time calibration 与 wait-preserving data。 | 不打开或验收实现合同。 |
| 后续计划 | 已由保留 review 证据接管 | [M3-S1 Censored Optimal-Stopping Timing Contract](../grouped_stopping_contract_20260605/README.zh.md) 记录已实现边界与 P5 证据。 | 本带日期决策不重开代码，也不声明 learned-policy acceptance。 |

## 范围

范围内：

- 定义一个与领域无关的数学对象，描述 partial observability、legality masks 与
  post-event censoring 下的一次性事件时机问题。
- 按 identifiability、deterministic decision boundary、cumulative early-event
  hazard、on-policy data compatibility 与 implementation risk 比较模型族。
- 为自设计算法、学术文献、现成模型族分别产出独立调研文档。
- 后续综合判断 M1/M2/A7 是否继续，或是否需要新的模型合同。

范围外：

- 新训练代码、新 runtime behavior 或领域物理修改。
- 宣称 A7 已 accepted 或 rejected。
- 仅因为 A7 堵塞就启动 M2。
- 将军事术语作为核心数学定义。

## 阶段计划

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Problem` | 固定抽象数学对象与模型选择标准。 | A7 safe-bias follow-up 仍 held。 | Formal problem statement 与 README 存在。 | pass |
| `P1 Parallel Research` | 收集三个独立模型选择视角。 | P0 draft 存在。 | 每个 worker 写出一个指定研究文档。 | pass |
| `P2 Synthesis` | 对比研究输出并命名候选模型合同。 | P1 文档返回。 | Synthesis 区分 recommended、fallback 与 rejected paths。 | pass |
| `P3 Decision` | 决定是否打开后续实现合同。 | P2 synthesis 被主线程接受。 | 父级 model README 与 A7 residuals 同步，且不做过度声明。 | pass；spawned M3-S1 planning |

## 任务簇

- Task cluster plan：
  [m3_optimal_stopping_model_selection_task_clusters_20260605.md](m3_optimal_stopping_model_selection_task_clusters_20260605.md)
- Dispatch queue：
  [m3_optimal_stopping_model_selection_dispatch_queue_20260605.md](m3_optimal_stopping_model_selection_dispatch_queue_20260605.md)

## 输出与证据

- Formal problem statement：
  [m3_formal_problem_statement_20260605.md](m3_formal_problem_statement_20260605.md)
- Self-designed algorithm packet：
  [m3_self_designed_algorithm_probe_20260605.md](m3_self_designed_algorithm_probe_20260605.md)
- Academic literature packet：
  [m3_academic_literature_model_survey_20260605.md](m3_academic_literature_model_survey_20260605.md)
- Existing model-family packet：
  [m3_existing_model_family_fit_survey_20260605.md](m3_existing_model_family_fit_survey_20260605.md)
- Synthesis：
  [m3_model_selection_synthesis_20260605.md](m3_model_selection_synthesis_20260605.md)
- 后续 planning contract：
  [M3-S1 Censored Optimal-Stopping Timing Contract](../grouped_stopping_contract_20260605/README.zh.md)

## 验收门

本子项目只有在以下条件满足后才能 accepted：

- formal mathematical problem 足够稳定，后续实现 agent 不需要阅读聊天记录即可复用；
- 每个 research packet 都列出 assumptions、candidate model class、expected failure
  modes，以及与当前堵塞证据的具体匹配；
- synthesis 推荐一个有边界的下一模型合同，并明确拒绝至少一个诱人但结构上薄弱的替代方案；
- 父级 model docs 已同步，且不声明 learned-policy success。

## 残余与下一步

- M3-S1 已作为 planning contract 打开；先处理 architecture boundaries 与
  data/censoring，再改训练 loop。
- M2 保持为候选模型族，而不是默认解法。
- A7 证据作为经验失败案例，而不是数学问题本身。

## Archive

暂无 archive records。只有当 synthesis 文档取代旧调研包时，历史 research packets 才应移入
`archive/`。
