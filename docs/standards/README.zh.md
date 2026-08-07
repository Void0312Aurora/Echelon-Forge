# 旧标准迁移索引

语言：[英文规范页](README.md)；本页为中文配套。

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/standards/README.md`
Owner: `legacy/standards-migration-index`
Last verified: `2026-08-08`

状态：尚未迁入内容 owner 的标准所使用的迁移期索引。

`docs/standards/` 不是目标所有权根。下列既有文档在各自迁移切片落地前保留当前
权威，但不得在此旧根下新增文档。稳定规则必须写入适用 owner 的 `standards/`
表面。

## 已迁移 Owner 路由

| 内容 | 当前 owner 路由 | 状态 |
| --- | --- | --- |
| Joint common core | [Joint owner](../domains/joint/README.zh.md) | 已迁移 |
| Service profiles | [Service-profile owner](../domains/joint/service_profiles/README.zh.md) | 已迁移 |
| Air 特化 | [Air owner](../domains/air/README.zh.md) | 已迁移 |
| Ground 特化 | [Ground owner](../domains/ground/README.zh.md) | 已迁移 |
| 文档治理 | [文档工程](../engineering/documentation/README.zh.md) | 已迁移 |
| 自动化治理 | [自动化工程](../engineering/automation/README.zh.md) | 已迁移 |
| 发布与依赖治理 | [发布工程](../engineering/release/README.zh.md) | 已迁移 |

已迁移内容的当前路由由这些 owner-local 文档定义，而不是本旧目录。

## 剩余 Legacy 来源

| Legacy 子树 | 当前维护用途 | 目标处置 |
| --- | --- | --- |
| [`naval/`](naval/README.zh.md) | Naval 特化标准与 reference 数据 | `docs/domains/naval/` |
| [`model/`](model/README.zh.md) | Policy/model execution architecture | `docs/learning/` |
| [`foundation/`](foundation/conventions.zh.md) | 混合的 architecture、system-realism 与 research-source 规则 | 拆分到 `docs/architecture/`、`docs/systems/`、`docs/research/` |
| [`bridge/`](bridge/runtime_workflow_and_contract_baseline.zh.md) | Runtime/workflow contracts 与场景指南 | 拆分到 `docs/architecture/` 与 `docs/operations/` |
| [`overview/`](overview/document_alignment_map.zh.md) | 文档对齐 reference | `docs/engineering/documentation/reference/` |
| [`planning/`](planning/modularization_plan.zh.md) | 带当前 `src/*/domains` 布局说明的 draft modularization issue | 经事实刷新后迁入 `docs/architecture/work/issues/` |

目标列是迁移裁决，不表示目标文件已经存在。`foundation/` 与 `bridge/` 混合多个
owner，必须拆分；整体移动任一目录都会重新制造当前分类问题。

## 路由规则

1. 移动或实质改写 legacy 来源前，先确定内容 owner。
2. 保留 document kind 与 lifecycle。Draft planning supplement 不会因为进入 owner
   目录就自动变成 standard。
3. 同一切片更新所有非归档 consumer。既有 archive 文件保持冻结，不进入默认裁决面。
4. 不得在 `docs/standards/` 下新增文档或子目录。
5. 只有旧根不再包含维护源，且所有当前入口都直接路由到 owner 后，才删除本索引。

## 与 Work 文档的关系

旧 [plans](../plan/README.zh.md) 和 [tasks](../task/README.zh.md) 可以记录实现状态、
证据或未解决工作，但必须引用相关 owner standard，不能重新定义稳定词汇。任务中形成
稳定合同后，应将其提升到 owner 的 `standards/` 表面，不得复制回本目录。

## 治理依据

- [标准维护政策](../engineering/documentation/standards/standards_maintenance_policy.zh.md)
- [文档生命周期规范](../engineering/documentation/standards/document_lifecycle_policy.zh.md)
- [双语文档政策](../engineering/documentation/standards/bilingual_documentation_policy.zh.md)
- [文档信息架构](../project/documentation_architecture.zh.md)
- [文档对齐映射](overview/document_alignment_map.zh.md)
