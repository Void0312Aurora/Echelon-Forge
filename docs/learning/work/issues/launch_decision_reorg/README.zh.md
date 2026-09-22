# 发射决策架构整理与重构计划

状态：2026-09-22 暂存提案；因 executable-owner 和兼容契约仍未闭合而阻塞，
未授权实现。

本文是 Tier B 工作面下的中文导航页，不是英文规范版的语义镜像。权威内容、
范围、任务簇、验证命令和残留项以 [英文 README](README.md) 为准。

## 导航

- [计划正文与当前状态](README.md)
- [有限任务簇计划](launch_decision_reorg_task_clusters_20260922.md)
- [策略执行架构基线](../../../standards/policy_execution_architecture.md)
- [双语文档规范](../../../../engineering/documentation/standards/bilingual_documentation_policy.md)
- [子项目创建规范](../../../../engineering/automation/rules/subproject_creation_standard.md)

## 当前阻塞摘要

独立审查返回 blocked，主要原因是：

1. 当前 executable event decision 由 action_net、HMoE event slice、
   hybrid_event_head 及可能的 adapter 共同组成，不能简单声明某一个 head
   独占 owner。
2. Composer、policy support mask 和 hybrid distribution 的职责必须唯一化。
3. 测试前必须先构建并验证本地 ef_py；还需冻结配置、checkpoint、optimizer、
   replay、数值容差和 seed/episode 集合。
4. C0-C5 的写集和依赖必须按串行架构 DAG 执行。
5. worktree 验收只针对本任务工作树，不能被其他既有 WIP 迫使修改。

在英文计划的 acceptance gate 和残留项完成前，不应创建 active 实现工作包。
