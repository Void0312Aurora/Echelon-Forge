# Agent 文档权威索引

语言：
- 英文规范页：[document_authority_map.md](document_authority_map.md)
- 中文配套页：`document_authority_map.zh.md`

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/engineering/automation/rules/document_authority_map.md`
Owner: `engineering/automation-governance`
Last verified: `2026-08-08`

状态：`2026-08-08`，面向 Agent 阅读仓库文档的维护规则索引。

范围：仓库文档和项目特定操作规则。本文件不覆盖用户请求、工具/运行时约束、
安全规则或平台指令。在仓库文档集合内部，用本索引判断应读什么、什么可以
作为当前权威。

## 快速开始

几乎所有任务都先读：

1. [根 README](../../../../README.md)
2. [文档索引](../../../README.zh.md)
3. 本权威索引

然后再选择下方对应任务路径。

## 权威层级

| 顺位 | 来源 | 规则 |
| --- | --- | --- |
| 1 | 当前用户任务、当前工作区和当前代码/测试 | 不覆盖无关本地改动；实现 claim 必须本地核验。 |
| 2 | 维护中的代码、场景、配置、测试和 contract runner | 可执行证据优先于过期文字。窄 gate 通过不自动提升整个领域成熟度。 |
| 3 | `docs/<owner>/standards/` 下维护中的 owner-local 标准，以及仍由 `docs/standards/` 索引的维护中共享标准 | 在对应职责范围内，以相关 owner-local 标准为准；其余共享标准在 owner 接受并迁移前继续保持权威。 |
| 4 | 根 README、`docs/README*`、局部 README | 拥有当前导航和成熟度入口。进入带日期任务文件前先读这里。 |
| 5 | `docs/plan/` 和活跃 `docs/task/` 入口 | 拥有架构方向、范围化实现计划、进度记录和残余。 |
| 6 | `docs/operations/`、`docs/reference_artifacts*`、`tests/README*` | 描述代码边界、操作工作流、保留证据和测试系统意图。 |
| 7 | `forward/`、`archive`、`Archive`、`temp`、retained artifacts、带日期 cluster packet | 仅为支撑或历史记录，除非维护 README 明确提升。 |

## 标准化文档索引

| 问题 | 阅读 |
| --- | --- |
| 哪一份维护 standard 拥有命名与层级？ | 先从适用的 owner README 及其 owner-local `standards/` 开始；尚未迁移的领域与建模路由使用迁移期[标准总览](../../../standards/README.zh.md)和[文档对齐图](../../../standards/overview/document_alignment_map.zh.md)。 |
| 跨域约定是什么？ | [仿真约定](../../../standards/foundation/conventions.zh.md)、[Runtime Workflow and Contract Baseline](../../../standards/bridge/runtime_workflow_and_contract_baseline.zh.md)、[场景配置指南](../../../standards/bridge/scenario_guide.zh.md) |
| 允许怎样声明真实性？ | [梯度真实性原则](../../../standards/foundation/gradient_realism_principles.zh.md)、[公开来源准入标准](../../../standards/foundation/public_data_source_admission.zh.md) |
| 军种/领域术语如何路由？ | [联合标准总览](../../../domains/joint/README.zh.md)、[军种 Profile 总览](../../../domains/joint/service_profiles/README.zh.md)、[空域标准](../../../domains/air/README.zh.md)、[海军标准](../../../standards/naval/README.zh.md)、[地面标准](../../../domains/ground/README.zh.md) |
| 架构/runtime 工作如何路由？ | [Runtime Workflow and Contract Baseline](../../../standards/bridge/runtime_workflow_and_contract_baseline.zh.md)、[场景配置指南](../../../standards/bridge/scenario_guide.zh.md)、[标准总览](../../../standards/README.zh.md) |
| 双语文档如何处理？ | [双语文档策略](../../documentation/standards/bilingual_documentation_policy.zh.md)、[双语文档簇](../../documentation/reference/bilingual_document_clusters.zh.md) |
| 文档类型、生命周期、evidence、generated 输出、config 索引、链接和 archive 如何治理？ | [文档生命周期规范](../../documentation/standards/document_lifecycle_policy.zh.md) |
| release 与依赖变更如何治理？ | [发布与依赖规范](../../release/standards/release_and_dependency_policy.zh.md) |
| 全仓精简在哪里排序和验收？ | [仓库精简与整合路线图](../../../plan/repository_consolidation/README.zh.md) |
| 社区、许可或安全文本如何处理？ | [CONTRIBUTING](../../../../CONTRIBUTING.md)、[LICENSE](../../../../LICENSE)、[THIRD_PARTY_NOTICES](../../../../THIRD_PARTY_NOTICES.md)、[SECURITY](../../../../SECURITY.md)、[CODE_OF_CONDUCT](../../../../CODE_OF_CONDUCT.md) |
| 委派工作如何协调？ | [Subagent 使用规范](../standards/subagent_usage_policy.zh.md)、[WP Closure Lane Policy](../standards/wp_closure_lane_policy.zh.md) |
| 新任务子项目应如何创建？ | [子项目创建标准](subproject_creation_standard.zh.md)、[Subagent 使用规范](../standards/subagent_usage_policy.zh.md)、[任务索引](../../../task/README.zh.md) |

## 能力声明门槛

写出某个能力“已实现”“成熟”“已验收”或“就绪”之前，至少需要同时具备：

1. 维护中的代码或数据 owner。
2. 维护中的 runtime、配置、场景、测试或 contract 表面。
3. 当前文档明确证据等级，且不暗示更高能力。

通用负边界：

- 不要把范围化证据扩写成整个领域成熟。
- 不要把 scenario-only 资产当作 active training/runtime evidence，除非维护文档和
  测试表面都这样说明。
- 不要把 retained artifact、signoff packet 或带日期记录当作更广项目权威，除非
  维护入口明确提升它们。
- 不要让 compatibility、diagnostics 或 exploratory 路径在没有标准或任务更新的
  情况下重定义维护路径。

## 任务阅读配方

| 任务类型 | 必读 |
| --- | --- |
| 文档刷新 | 根 README、docs 索引、本索引、[文档生命周期规范](../../documentation/standards/document_lifecycle_policy.zh.md)、受影响局部 README、标准 owner。 |
| 仓库精简 | [仓库精简与整合路线图](../../../plan/repository_consolidation/README.zh.md)、受影响 owner README、当前 callers/tests，以及必需的独立审阅协议。 |
| 代码/runtime 修改 | 受影响的 `src/`、`python/` 或 `gym_envs` README；源码层级图；相关 plan/task 入口；相关测试。 |
| 测试或 contract 修改 | tests README、局部 test README、reference artifacts、相关 standards/bridge contract。 |
| 领域成熟度表述 | 领域 task README、领域 standards README、被索引的当前状态或验收文档、实现/测试证据。 |
| 社区/治理/许可文本 | CONTRIBUTING、LICENSE、THIRD_PARTY_NOTICES、SECURITY，以及相关 owner 索引路由的维护中标准。 |
| release 或依赖变更 | [发布与依赖规范](../../release/standards/release_and_dependency_policy.zh.md)、受影响 manifest/lockfile、release tooling 与聚焦测试。 |
| 委派 Agent 工作 | 本索引、subagent 使用规范、被分配写集、必需输出 packet。 |
| 新建 `docs/task/**` 子项目 | 本索引、子项目创建标准、父领域 README、相关 standards owner、任务簇计划。 |

## Agent 输出规则

回报时分清：

- 已确认的实现事实
- 文档解释
- 残余风险
- 验证命令与结果
- 已修改文件

如果用户要求可持久化的项目评估，不要让重要发现只停留在聊天里。应记录到相关
维护评估、任务或 README 表面。
