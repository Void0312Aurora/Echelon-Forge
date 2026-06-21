# 测试系统治理

状态：`2026-06-21` 已验收的治理切片，用于在保留维护态覆盖的前提下降低测试冗余；
剩余 blocker 由
[测试系统残余治理](../../issues/test_system_residual_governance/README.zh.md)
继续追踪。

语言：

- 英文规范页：[README.md](README.md)
- 中文配套页：`README.zh.md`

输入：

- 父级 review 索引：[../README.zh.md](../README.zh.md)
- 测试系统意图：[../../../tests/README.md](../../../../tests/README.md)
- Agent authority map：[../../../agent/rules/document_authority_map.md](../../../agent/rules/document_authority_map.md)
- 子项目创建标准：[../../../agent/rules/subproject_creation_standard.md](../../../agent/rules/subproject_creation_standard.md)
- 审计 runner：[../../../../tools/runners/audit_test_system.py](../../../../tools/runners/audit_test_system.py)

## 目的

本子项目承接 2026-06-20 开始的测试系统治理工作。当前测试树有真实价值，
但也存在超长快照式测试、源码扫描 guard、隐藏 mixin 测试、smoke/contract
提升不均衡等问题。

目标不是为了减少测试数量而删测试，而是让业务覆盖、CI gate、focused/local/manual
分层和 JSON contract 关系变得可解释、可复跑、可验收。

## 当前状态

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| 审计工具 | 当前切片已验收 | [audit_test_system.py](../../../../tools/runners/audit_test_system.py), [test_audit_test_system.py](../../../../tests/runners/test_audit_test_system.py) | 只做静态审计，不替代 pytest collection 或 coverage 报告。 |
| 活跃 pytest 面 | 已盘点 / 残余已追踪 | 审计摘要：343 个已追踪活跃 test 文件、256 个已追踪活跃 Python 文件、1990 个修正后静态 test item、152 个风险标记 Python 文件；pytest 工作树 collect：2000 个测试。 | 这些数排除了 `archive`，但不能单独证明语义冗余。 |
| smoke 提升 | 当前切片已验收 | 审计摘要：51 个 pytest smoke entry、49 个文件、10 个 JSON contract smoke spec；smoke suite 保持通过。 | smoke membership 是 gate 决策，不是完整覆盖声明。 |
| coverage 基线 | 作为 scoped evidence 已验收 | 当前本地 `.coverage` 覆盖 Python roots：34376 statements，11916 missed，65%。 | 不覆盖 C++ `src/`、branch coverage，也不代表所有 Python 业务面。 |
| 测试精简 | 已验收并保留残余 | 两个最大的 `tests/tools` airframe geometry 测试和十个高风险 damage-model 文件已拆成更小的语义测试。 | Airframe 行为和剩余 literal/source-scan 集中由残余 issue 追踪。 |
| mixin collection | 文档已验收 / 行为残余保留 | [P2-C evidence](test_system_governance_p2c_mixin_evidence_20260621.md) 记录 `weapon_guidance_realism` 通过五个 wrapper 收集 192 个测试。 | 包级运行当前失败；该包保留为 local/focused，不进入 smoke。 |

## 范围

范围内：

- 维护一个排除 `archive` / `Archive` 的活跃测试审计口径。
- 将测试分为 smoke、focused、local、manual、contract 或 archive candidate。
- 将选定的硬编码快照测试转为更小的不变量检查或数据驱动 contract。
- 在能提高可维护性且不丢覆盖时，减少隐藏 collection 模式。
- 测试治理规则或验收边界变化时同步测试文档和任务状态。

范围外：

- 因为审计 runner 通过就声称整个测试系统健康。
- 因为测试很长或不在 smoke 中就直接删除。
- 用 coverage 百分比替代业务覆盖分析。
- 在测试清理 cluster 中重写 runtime、模型算法或领域 contract。
- 未经维护 README 或状态文档提升就把 archive 证据当成当前权威。

## 阶段计划

| 阶段 | 目标 | 入口条件 | 退出条件 | 状态 |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | 固定范围、权威和活跃测试定义。 | 用户要求创建持久任务子项目。 | 父 README、标准、tests README 和 archive 排除规则已链接。 | pass |
| `P1 Evidence` | 建立可复跑审计和基线。 | 存在活跃非归档测试树。 | 审计、pytest collection 和 coverage 语义已分开。 | pass |
| `P2 Consolidation` | 改造最高风险测试簇。 | P1 审计给出具体文件和风险标记。 | 选定 cluster 用更小不变量或 contract 数据保留行为。 | 已验收并保留残余 |
| `P3 Suite Tiers` | 同步 smoke/focused/local/manual 分层。 | P2 替代检查稳定。 | suite manifest 与 README 分层一致。 | 当前切片 pass |
| `P4 Validation` | 运行验收命令并比较覆盖/风险变化。 | P2/P3 变更按 cluster 完成。 | runner 测试、相关领域测试、审计报告和 coverage 备注通过。 | 当前切片 pass |
| `P5 Closure` | 同步索引、残余和 archive/current 边界。 | 存在 scoped acceptance 证据。 | README/status/acceptance 和父索引更新。 | 当前切片 pass |

## 任务簇

- 任务簇计划：[test_system_governance_task_clusters_20260620.md](test_system_governance_task_clusters_20260620.md)
- 当前状态：[test_system_governance_current_status_20260620.md](test_system_governance_current_status_20260620.md)
- 分发队列：[test_system_governance_dispatch_queue_20260620.md](test_system_governance_dispatch_queue_20260620.md)
- 验收记录：[test_system_governance_acceptance_20260620.md](test_system_governance_acceptance_20260620.md)
- P1-B 证据：[test_system_governance_p1b_evidence_20260621.md](test_system_governance_p1b_evidence_20260621.md)
- P2-C mixin 证据：[test_system_governance_p2c_mixin_evidence_20260621.md](test_system_governance_p2c_mixin_evidence_20260621.md)

## 输出与证据

- `tools/runners/audit_test_system.py`：活跃测试审计 runner。
- `tests/runners/test_audit_test_system.py`：archive 排除、smoke/contract 计数和风险标记自测。
- `tests/README.md`：审计 runner 使用和解释规则。
- [test_system_governance_p1b_evidence_20260621.md](test_system_governance_p1b_evidence_20260621.md)：静态审计、pytest collection 与 coverage 证据对齐记录。
- [test_system_governance_p2c_mixin_evidence_20260621.md](test_system_governance_p2c_mixin_evidence_20260621.md)：`weapon_guidance_realism` wrapper/mixin collection 决策。

## 验收门槛

本子项目当前治理切片已满足以下验收条件：

- 审计 runner 保持有测试、有文档。
- 至少一个高风险测试簇完成精简、重新分层或 contract 化，并有前后证据。
- smoke 与 contract suite manifest 表达明确 gate membership。
- coverage 表述限制在实际测量的 source root 内。
- 仍保留的硬编码、超长或源码扫描测试都有明确 tier 或 follow-on。
- 不把窄切片通过表述成全项目测试健康。

## 残余与下一步

剩余 blocker 由
[测试系统残余治理](../../issues/test_system_residual_governance/README.zh.md)
保留追踪：

- 在依赖完整机器上执行已拆分的 `tests/tools/` airframe 检查；
- 继续处理 `tests/architecture/damage_model/` 剩余文件级 literal/source-scan guard；
- 在 `tests/runtime/air_combat/weapon_guidance_realism/` 包级运行转绿前不提升 smoke；
- 产出区分 Python/C++ 的 coverage 记录，写明测量 root，避免过度声明。

## Archive

被替代的状态快照、过期风险报告和已关闭 cluster packet 放入
[archive/README.md](archive/README.md)。archive 仅作 provenance，不作为当前测试系统健康的默认权威。
