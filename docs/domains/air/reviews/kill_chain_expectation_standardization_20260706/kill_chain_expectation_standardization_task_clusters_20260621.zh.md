# 杀伤链期望标准化任务簇

状态：`2026-06-23`，用于
[杀伤链期望标准化](README.zh.md) 的有限任务簇计划。P0-P5 均已 pass。

英文规范页：
[kill_chain_expectation_standardization_task_clusters_20260621.md](kill_chain_expectation_standardization_task_clusters_20260621.md)

## 边界决定

本子项目可以定义期望合同、场景矩阵、指标映射和校准 harness 计划。它不得重调 runtime
参数，不得编辑武器 / 目标 descriptor，不得声明真实 AIM-120C、F-16C 或 Pk 权威。

## 有限任务簇列表

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `KCES-P0 Project Boundary` | main thread | n/a | 创建子项目、状态、队列、archive 入口和父级 A2 链接。 | `docs/domains/air/reviews/kill_chain_expectation_standardization_20260706/**`；父级 A2 README | runtime/code/test 修改；标准提升 | `git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model` | 必需文件存在，父级 README 链接本项目，禁止声明明确。 | first, serial | 1 | pass |
| `KCES-P1 Expectation Contract` | main thread | n/a | 定义阶段合同、归一化分区、AIM-120C-like 种子画像和通用 row 模板。 | 本子项目内合同文档 | 概率数值校准；真实武器权威 | Markdown/link review 和 `git diff --check` | 合同只能通过已声明 profile 字段解释 10 m 量级歧义，并关闭 `R_effect_policy=independent_review_variable`。 | after P0 | 2 | pass |
| `KCES-P2 Scenario Matrix` | main thread | n/a | 增加距离 x 偏置角 heatmap，覆盖 nominal、marginal 和 outside-envelope cells，并估算后续采样密度。 | 本子项目内新增矩阵文档 | runtime 仿真修改；learned-policy 证据 | 矩阵审阅加 `git diff --check` | heatmap 声明距离轴、偏置角轴、目标运动层、launch-window 类别、期望阶段分区、推荐主网格 / seed 预算和第一轮 `R_effect_variant` handoff。 | after P1 | 2 | pass |
| `KCES-P3 Metric Mapping` | main thread | n/a | 将定性期望分区映射到既有或计划中的 stage-report 字段。 | 指标映射文档；可选 diagnostics-readiness checklist | 参数值；descriptor 编辑 | docs check 和字段引用审阅 | 每个指标由一个阶段拥有，或标为 cross-stage；heatmap report row schema 存在。 | after P2 | 2 | pass |
| `KCES-P4 Calibration Harness Plan` | main thread | n/a | 把期望 rows 绑定到 P6 单层 before/after 和 delta-guard 要求。 | harness plan 文档；可选 dry-run artifact path proposal | 运行完整校准或改变 runtime 参数 | docs check；若已有 artifact，可选 CLI dry-run | 计划拒绝跨层变化并命名 frozen stage ids。 | after P3 | 2 | pass |
| `KCES-P5 Closure / Promotion Decision` | main thread | n/a | 记录 accepted/held residuals，并决定稳定合同是否进入 `docs/standards`。 | [kill_chain_standard_promotion_decision_20260623.zh.md](kill_chain_standard_promotion_decision_20260623.zh.md) 和 README/status/task-cluster 更新 | 静默提升标准；过度声明 accepted runtime 行为 | docs diff check 和父级 index sync | status、residuals 和父级 README 一致；决策为 retained task-local standard。 | last, serial | 1 | pass |

## 派发规则

- 每个 worker packet 必须只对应上表一个 cluster。
- 不允许两个 worker 并发编辑合同、status line 或父级 README 链接。
- 在 P4 明确打开 docs-only harness plan 前，runtime descriptor、C++/Python 代码、
  测试和场景配置均保持 out of scope。
- closure 和 standards-promotion 决策必须串行。
- 严禁创建新的 Codex 会话线程；如使用委派 worker，也必须留在当前会话和 cluster
  write set 内。

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

```bash
git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model
```

未来 cluster 可增加链接检查、schema 检查或 diagnostics dry run；P0/P1 是 docs-only。

## 验收标准

- 合同区分期望阶段和禁止 authority 声明。
- 场景 row 必须声明 `R_fuze`、`R_effect`、目标代理和几何类别后才可解释。
- 后续校准工作可以一次只针对一个 layer。
- 真实武器、真实目标、确定性引信和 Pk 权威保持拒绝。

## 残余图

Immediate：

- 无。本 P0-P5 docs-only workstream 已收口。

Follow-on：

- future harness implementation：实现 P4 CLI / artifact 并生成 before heatmap report。
- future standards promotion：只有在 runtime/test/admission 证据验收后重开。

Deferred：

- runtime 参数修改。
- descriptor 编辑。
- 真实世界 authority admission。
