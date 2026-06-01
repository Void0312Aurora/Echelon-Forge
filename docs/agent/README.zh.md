# Agent 文档索引

语言：
- 英文规范页：[README.md](README.md)
- 中文配套页：`README.zh.md`

状态：`2026-06-01`，面向仓库内 AI/Agent 的维护入口。

本目录把维护中的文档树整理成一个紧凑的 Agent 操作面。它不替代根 README、
标准文档、代码或测试。它的作用是告诉 Agent：先加载哪些文档，哪些文档具有
规范性，以及哪些能力声明必须先有实现证据才能复述。

## 入口文件

| 文件 | 用途 |
| --- | --- |
| [rules/document_authority_map.zh.md](rules/document_authority_map.zh.md) | 仓库文档权威、标准引用、任务阅读路径和能力声明门槛的规则索引。 |
| [rules/subproject_creation_standard.zh.md](rules/subproject_creation_standard.zh.md) | 创建任务子项目的标准：README、阶段计划、任务簇、当前状态、验收、残余和 archive 边界。 |
| [prompts/project_orientation_prompt.zh.md](prompts/project_orientation_prompt.zh.md) | 可复制给 Agent 的项目任务启动提示词。 |
| [../standards/governance/subagent_usage_policy.zh.md](../standards/governance/subagent_usage_policy.zh.md) | 当执行环境允许 subagent/worker 时使用的仓库委派规范。 |

## Agent 使用方式

1. 先读根 [README.md](../../README.md)、[docs/README.zh.md](../README.zh.md)
   和 [rules/document_authority_map.zh.md](rules/document_authority_map.zh.md)。
2. 判断任务属于哪个工作面：文档、代码/runtime、tests/contracts、领域成熟度、
   贡献/治理，或发布/维护。
3. 按权威索引读取该工作面的文档。
4. 更新状态文字前，先对照当前代码、测试、场景、配置或保留制品核验证据。
5. 需要给新 Agent 准备可复用提示词时，使用
   [prompts/project_orientation_prompt.zh.md](prompts/project_orientation_prompt.zh.md)。
6. 如果任务会创建或重新启用 `docs/task/**` 子项目，遵循
   [rules/subproject_creation_standard.zh.md](rules/subproject_creation_standard.zh.md)。

## 仓库边界

被忽略的 `.agent/` 目录可以作为本地运行态或个人 Agent 工作区存在。它不是
可提交的项目文档系统。正式的 Agent-facing 指引放在 `docs/agent/`。

## 维护规则

- 本目录应保持小而可执行。
- 链接既有标准，不复制标准全文。
- 维护中的入口、规则和提示词文档应配中文辅文。
- 不要把 archive、temp、retained artifact 或带日期的任务记录提升为当前权威，
  除非维护中的 README 明确这样做。
- 新标准化文档改变项目级规则时，应把它加入 authority map，而不是依赖聊天记忆。
