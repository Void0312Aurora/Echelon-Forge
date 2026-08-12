# 军种画像

Language: [English canonical](README.md); Chinese companion.

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/domains/joint/service_profiles/README.md`
Owner: `domains/joint/service-profiles`
Last verified: `2026-08-08`

这个嵌套 owner 定义各美军军种画像如何解释共享的 Joint common-core 词汇。
Service profile 选择可接受的组织、任务编组、授权和战术单位解释，但不拥有 air、
naval 或 ground 执行语义。

## 当前权威

- [美国空军画像](standards/air_force_profile.zh.md)
- [美国陆军画像](standards/army_profile.zh.md)
- [美国海军画像](standards/navy_profile.zh.md)
- [美国海军陆战队画像](standards/marine_corps_profile.zh.md)

阅读这些画像前，先阅读上级 [Joint owner 索引](../README.zh.md)及其
[指挥与建模](../standards/command_and_modeling_baseline.zh.md)和
[命令链与汇报](../standards/command_link_and_reporting_baseline.zh.md)标准。

## Owner 边界

Service profile 拥有：

- 对 Joint common-core 字段的军种特定解释；
- 哪些组织层级应保留为场景或兵力编组元数据；
- 哪些战术单位形态可以进入领域 runtime；
- 军种术语必须在哪个边界移交给领域 owner。

Service profile 不拥有平台控制、观测/动作布局、运动、站位几何、感知、武器行为、
毁伤或其他领域执行合同。这些内容仍归 air、naval 和 ground owner。

## 领域移交

执行语义使用当前领域 owner 路由：

- [空中特化](../../air/README.zh.md)
- [地面特化](../../ground/README.zh.md)
- [海上特化](../../naval/README.zh.md)

本目录位于 Joint 之下只是信息架构决策；它不把 service-profile 解释合并进 Joint
common core，也不授予 Joint 对领域执行语义的所有权。

## 相关 Legacy 路由

- [仿真约定](../../../architecture/standards/simulation_conventions.zh.md)
- [文档对齐映射](../../../engineering/documentation/reference/document_alignment_map.zh.md)
- [场景配置指南](../../../operations/howto/scenario_configuration_guide.zh.md)
- [运行时工作流与合同基线](../../../architecture/standards/runtime_workflow_and_contract_baseline.zh.md)
