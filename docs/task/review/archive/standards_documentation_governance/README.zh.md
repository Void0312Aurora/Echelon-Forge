# 标准化文档治理

状态：`2026-06-10`，用于 standards drift、准入与收口的已归档 accepted 治理切片。

语言：

- 英文主文：[README.md](README.md)
- 中文辅文：`README.zh.md`

输入：

- [审查任务区](../../README.zh.md)
- [标准化-实现对齐审查 2026-06-10](../standards_implementation_alignment_review_20260610.zh.md)
- [标准化文档总览](../../../../standards/README.zh.md)
- [文档对齐映射](../../../../standards/overview/document_alignment_map.zh.md)
- [标准维护政策](../../../../standards/governance/standards_maintenance_policy.zh.md)
- [Agent 文档权威索引](../../../../agent/rules/document_authority_map.zh.md)
- [子项目创建标准](../../../../agent/rules/subproject_creation_standard.zh.md)

## 目的

本子项目把标准化-实现对齐审查转化为可持续治理通道。标准树已经可以作为项目
ownership map 使用，但审查也说明，实现变更仍然可能跑在标准条目、状态日期和
规划补充页之前。

目标是让 `docs/standards/` 保持当前可信，同时避免任务计划、diagnostics、
兼容路径或早期 runtime 实验意外改写维护中的所有权层级。

## 当前状态

| 领域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| 标准权威性 | accepted | `docs/standards/README.md`、`docs/standards/overview/document_alignment_map.md` | 拥有命名和分层权威，不等于每个字段级合同都已刷新。 |
| 对齐审查 | archived provenance | `archive/standards_implementation_alignment_review_20260610.md` | 六个 gap 已获得 owner closure 或显式 held 处置。 |
| 双语治理 | accepted | `docs/standards/governance/bilingual_documentation_policy.md` | 语言配对检查不证明语义与实现对齐。 |
| 维护政策 | active | `docs/standards/governance/standards_maintenance_policy.md` | 政策定义门槛，但本身不关闭六个 gap。 |

## 范围

范围内：

- 为 `2026-06-10` 对齐审查中的 GAP-001 到 GAP-006 建立有限收口通道。
- 定义 runtime、DTO、场景、测试或任务验收变化后，标准文档何时必须同步更新。
- 同步标准状态行、索引、双语辅文和当前实现声明。
- 记录每个 gap 是已关闭、保持 held，还是有意延后。

范围外：

- 宣称 air、naval、ground、model 或 weapon effects 具备新的 runtime 成熟度。
- 在 `src/*/domains` 下创建生产路径的 `demo` 或空壳示范域。
- 在 MLF-3 warhead-effects 任务面达到验收之前，把未接受工作提升为标准合同。
- 一次性重写完整标准树。

## 阶段计划

| 阶段 | 目标 | 进入条件 | 退出条件 | 状态 |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | 记录治理通道与维护政策。 | 对齐审查已存在。 | 子项目、政策和索引存在。 | pass |
| `P1 Triage` | 为每个 GAP 分类 owner、写集和收口门槛。 | P0 完成。 | 六个 gap 均有串行或 held 任务簇。 | pass |
| `P2 Remediation` | 分批执行已接受的标准/runtime 修复。 | triage 完成。 | 每个已修改合同都有文档、测试和必要双语同步。 | pass |
| `P3 Validation` | 运行文档、架构和受影响 runtime gate。 | remediation 批次完成。 | 记录通过/失败证据。 | pass |
| `P4 Closure` | 更新状态、残余、索引和归档准备度。 | 验证完成。 | 已接受切片和仍 held 项明确。 | closed |

## 任务簇

- 任务簇计划：`standards_documentation_governance_task_clusters_20260610.md`
- 当前状态：`standards_documentation_governance_current_status_20260610.zh.md`
- 派发表：`standards_documentation_governance_dispatch_queue_20260610.zh.md`

## 输出与证据

- 本 review 子项目。
- [标准维护政策](../../../../standards/governance/standards_maintenance_policy.zh.md)。
- [当前状态账本](standards_documentation_governance_current_status_20260610.zh.md)。
- [派发表](standards_documentation_governance_dispatch_queue_20260610.zh.md)。
- 父级 review 归档索引条目。
- 确保本治理通道被注册的 architecture governance 测试。
- 后续针对单个 GAP 的 remediation commits。

P0 验证证据：

- `python -m pytest -q tests/architecture/governance/test_standards_documentation_governance.py` 通过，4 项测试。
- `python3 tools/maintenance/translate_docs_batch.py audit --root docs --registry docs/standards/bilingual_document_clusters.json` 报告 registry 内 66 对文档 synced，无 registry drift。它仍报告既有问题：`docs/standards/foundation/realism_authority_boundary.zh.md` 缺少英文 peer。
- `git diff --check` 对本批 standards governance 路径通过。
- `python -m pytest -q tests/architecture/governance` 仍有无关既有失败，原因是旧 governance 测试期待的若干 simulation-architecture WP 路径在当前树中不存在。

P1 验证证据：

- `python -m pytest -q tests/architecture/governance/test_standards_documentation_governance.py` 通过，5 项测试。
- `python3 tools/maintenance/translate_docs_batch.py audit --root docs --registry docs/standards/bilingual_document_clusters.json` 报告 registry 内 66 对文档 synced，无 registry drift；既有英文 peer 缺口仍在本子项目外。
- `git diff --check` 对扩展后的 standards governance 路径通过。

Batch A remediation 验证证据：

- `cmake --build build-workshop --target ef_py -j2` 通过。
- `python -m pytest -q tests/architecture/ground/test_tasking_component_boundary.py tests/runtime/mission/test_mission_command_ground_fields_roundtrip.py tests/leader/test_ground_profile_semantics.py tests/runtime/mission/test_mission_command_roe_fields.py` 通过，24 项测试。
- `python -m pytest -q tests/architecture/governance/test_standards_documentation_governance.py` 在扩展 closure guard 后通过。

Batch B remediation 验证证据：

- `python -m pytest -q tests/runtime/mission/test_mission_obs_taxonomy.py tests/runtime/air_combat/test_air_combat_c2_roe_mission_observation.py tests/runtime/naval/test_naval_n4_reward_surface.py` 通过，31 项测试。
- `python -m pytest -q tests/architecture/governance/test_standards_documentation_governance.py` 通过，7 项测试。
- `python3 tools/maintenance/translate_docs_batch.py clusters --root docs --write` 已将维护 registry 刷新到 67 对。
- `python3 tools/maintenance/translate_docs_batch.py audit --root docs --registry docs/standards/bilingual_document_clusters.json` 报告 registry 内 67 对文档 synced，无 registry drift。它仍报告既有问题：`docs/standards/foundation/realism_authority_boundary.zh.md` 缺少英文 peer。
- `git diff --check` 对 Batch B 触及的 standards/governance 路径通过。

Batch C 与最终 status/header closure 验证证据：

- `python -m pytest -q tests/architecture/governance/test_standards_documentation_governance.py` 通过，9 项测试。
- `python3 tools/maintenance/translate_docs_batch.py clusters --root docs --write` 保持维护 registry 为 67 对。
- `python3 tools/maintenance/translate_docs_batch.py audit --root docs --registry docs/standards/bilingual_document_clusters.json` 报告 registry 内 67 对文档 synced，无 registry drift。它仍报告既有问题：`docs/standards/foundation/realism_authority_boundary.zh.md` 缺少英文 peer。
- `git diff --check -- docs/standards docs/task/review/standards_documentation_governance tests/architecture/governance/test_standards_documentation_governance.py` 通过。

## 验收门槛

本子项目只有在满足以下条件后才可标记 accepted：

- GAP-001 到 GAP-006 均已用证据关闭，或以命名 owner 和 release trigger 明确 held。
- remediation 修改的维护中标准拥有中文辅文，或明确记录 Tier-B 延迟。
- standards README、document alignment map 和受影响本地 README 不再把读者指向过期权威。
- 聚焦验证命令有记录并通过；若失败，则失败项作为 blocking residual 列明。

当前 gate 结果：GAP-001 到 GAP-005 已满足；GAP-006 是显式 held 项，release trigger 为
MLF-3 acceptance。

## 残余与下一步

- GAP-006 应在 MLF-3 warhead effects 达到任务验收前保持 held。
- 未来可以把审查清单变成只读 standards drift audit 工具，但这不是第一批治理切片的必要条件。

## 归档

本子项目已归档到
`docs/task/review/archive/standards_documentation_governance/`。它继续作为
2026-06-10 standards drift closure 的 accepted provenance 记录存在，但不再是未来
standards 工作的默认 active planning surface。
