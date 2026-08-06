# 面向 Agent 的项目启动提示词

语言：
- 英文规范页：[project_orientation_prompt.md](project_orientation_prompt.md)
- 中文配套页：`project_orientation_prompt.zh.md`

状态：`2026-06-01`，面向本仓库 Agent 的可复制提示词模板。

启动新的 Agent 或 worker 处理 Echelon Forge 任务时可使用本模板。派发或粘贴前，
先填好任务块。

```md
你正在 Echelon Forge 仓库中工作。

任务：
<描述具体任务>

写入范围：
<列出允许修改的文件/目录，或说明 read-only>

非目标：
<列出不在范围内的文件/目录或能力声明>

预期验证：
<列出命令、链接检查、测试或检查项>

行动前先读：

1. README.md
2. docs/README.zh.md
3. docs/engineering/automation/rules/document_authority_map.zh.md
4. authority map 为本任务指定的局部 README、标准文档和任务文档。
5. 如果创建或重新启用任务子项目：
   docs/engineering/automation/rules/subproject_creation_standard.zh.md。

仓库规则：

- 不要把 archive、Archive、temp、retained artifacts 或带日期的 cluster packet
  当作当前权威，除非维护 README 明确提升它们。
- 不要升级能力声明，除非同时存在维护中的实现 owner、维护中的 runtime/config/test
  表面，以及说明证据等级的当前文档。
- 从维护入口文档读取项目定位、领域成熟度和当前状态，并先对照代码/测试核验，
  再复述这些状态。
- retained artifact 只能作为范围化证据；不要让单个 retained packet 或带日期记录
  定义更广项目成熟度。
- 保留无关的 dirty worktree 改动。
- 如果当前执行环境和用户请求允许 subagent/worker，则遵循
  docs/standards/governance/subagent_usage_policy.zh.md。
- 如果创建 `docs/task/**` 子项目，必须按子项目创建标准包含 README、有限任务簇
  文档、阶段/状态/验收/残余章节、父索引链接，以及 archive/current 边界。

输出要求：

- 报告修改了哪些文件。
- 区分已确认实现事实与文档解释。
- 列出残余风险。
- 列出验证命令和结果。
- 如果任务产出可持久化的项目评估，应写入相关维护评估、任务或 README 表面，
  不要只留在聊天里。
```
