# 杀伤链标准提升决策

状态：`2026-06-23` P5 pass closeout / promotion decision，用于
[杀伤链期望标准化](README.zh.md)。

英文规范页：
[kill_chain_standard_promotion_decision_20260623.md](kill_chain_standard_promotion_decision_20260623.md)

## 输入

- P1 期望合同：
  [kill_chain_idealized_expectation_contract_20260621.zh.md](kill_chain_idealized_expectation_contract_20260621.zh.md)
- P2 场景矩阵：
  [kill_chain_scenario_expectation_matrix_20260622.zh.md](kill_chain_scenario_expectation_matrix_20260622.zh.md)
- P3 指标映射：
  [kill_chain_metric_mapping_20260623.zh.md](kill_chain_metric_mapping_20260623.zh.md)
- P4 harness 计划：
  [kill_chain_calibration_harness_plan_20260623.zh.md](kill_chain_calibration_harness_plan_20260623.zh.md)
- 标准维护政策：
  [../../../../engineering/documentation/standards/standards_maintenance_policy.zh.md](../../../../engineering/documentation/standards/standards_maintenance_policy.zh.md)
- 标准树总览：
  [../../../../standards/README.zh.md](../../../../standards/README.zh.md)

## 决策摘要

| 字段 | 决策 |
| --- | --- |
| `decision_id` | `KCES-P5-20260623` |
| `promotion_decision` | `retain_task_local_standard` |
| `standards_tree_write` | `none` |
| `runtime_calibration_authority` | `false` |
| `accepted_scope` | P1-P4 docs-only 期望合同、heatmap 约束、指标字段映射和 harness 计划。 |
| `held_scope` | runtime 参数、descriptor、批量仿真结果、概率 / 完整度阈值、真实弹种 / 目标 authority、全局标准提升。 |

结论：本子项目在 P5 收口为 `accepted / retained task-local docs-only standard`。
P1-P4 内容足以作为 A2 校准前的任务局部标准，但还不足以写入 `docs/standards/`
作为项目级维护标准。

## 提升评估

| 内容 | 当前成熟度 | P5 决策 | 后续提升条件 |
| --- | --- | --- | --- |
| 阶段拆分和 authority 边界 | 稳定 task-local 词汇。 | 保留在本子项目；不新增 standards 页面。 | 若多个空战 follow-on 共同复用同一词汇，再提出标准树补充。 |
| P2 距离 x 偏置角 heatmap | 期望矩阵已定义，但尚未执行 runtime heatmap。 | 保留为任务局部校准前 oracle。 | 未来 harness 生成 before/after heatmap，且结果被验收后，可考虑提升为空空校准报告约定。 |
| P3 report row schema | 字段映射存在，但部分字段仍是 planned-harness。 | 保留为 task-local report schema。 | CLI / artifact 实现存在，字段由测试或诊断报告稳定产出。 |
| P4 harness plan | 计划已完成，没有批量仿真 artifact。 | 保留为后续实现入口，不提升标准。 | smoke / pilot / main grid 执行并通过 delta guard 后，再评估是否抽取通用 harness 规范。 |
| 真实 authority 拒绝 | 已由 foundation policy 约束。 | 不重复写入新标准；继续引用既有准入规则。 | 只有未来 admission gate 明确授予字段后才可更新。 |

## 接受边界

Accepted：

- P1-P4 的文档、词汇和报告字段可作为 A2 kill-chain calibration 的前置约束。
- `R_effect_policy=independent_review_variable` 保持有效。
- P2 主网格建议、边界加密预算和第一轮 `R_effect_variant` 集合作为未来 harness
  输入保留。
- P3/P4 的单层 guard 约束作为未来 runtime 校准的进入条件保留。

Held：

- 不声明 8 km / 30 deg 当前 runtime 结果已经被校准。
- 不声明 10 m 量级近炸一定杀伤或一定不杀伤。
- 不设定概率阈值、完整度阈值或真实战斗部参数。
- 不修改 runtime、descriptor、测试或 `docs/standards/`。

## 后续入口

P5 之后，本子项目没有继续排队的 P0-P5 工作。后续只能从新的、明确命名的 workstream
进入：

| Future entry | 触发条件 | 写入范围 |
| --- | --- | --- |
| `KCES-FUTURE-HARNESS-IMPLEMENTATION` | 用户要求把 P4 计划实现为 CLI / artifact。 | tools/tests/docs evidence，仍不得默认重调参数。 |
| `KCES-FUTURE-BEFORE-HEATMAP` | harness 已实现，需要生成 before report。 | evidence artifact + current status，不写入 standards。 |
| `KCES-FUTURE-STANDARDS-PROMOTION` | 至少有已验收 runtime/test/admission 证据。 | 先开 review/task gap，再按 standards maintenance policy 更新。 |

## Closeout

P5 为 pass。当前推荐状态是：

```text
subproject_status = accepted_retained_task_local_docs_only_standard
standards_promotion = held_until_runtime_evidence
runtime_calibration = held
authority_claims = refused
```
