# 发射决策架构整理与重构计划

状态：2026-10-08，C0–C5 架构重组已实现，并通过 PR #39–#42 于 2026-09-29 合入 `main`。结构性实施与合并已完成；真实模型的 learned-firing 效果和行为验收仍需独立证据。

本文是 Tier B 工作面下的中文导航页，不是英文规范版的语义镜像。权威内容、
范围、任务簇、验证命令和残留项以 [英文 README](README.md) 为准。

## 导航

- [计划正文与当前状态](README.md)
- [有限任务簇计划](launch_decision_reorg_task_clusters_20260922.md)
- [策略执行架构基线](../../../standards/policy_execution_architecture.md)
- [双语文档规范](../../../../engineering/documentation/standards/bilingual_documentation_policy.md)
- [子项目创建规范](../../../../engineering/automation/rules/subproject_creation_standard.md)

## 已定型的方向

- 长期默认是 `governed_composed_v1`：由受治理的 event-delta 组合契约
  负责最终组合，而不是让某一个 head 永久独占架构。
- `direct_boundary_v1_strict` 是严格实验/验收 profile：direct-boundary
  更新只能写 `hybrid_event_head.*`，HMoE event slice、共享 action/trunk
  和 adapter 不得隐式参与。
- `legacy_composed_v0` 只用于旧 checkpoint/config 的加载和对比；旧的
  window-before-stopping 优先级会被记录，新配置的冲突必须拒绝。
- Composer 返回未加 mask 的 event pair 和 trace；mask、采样、概率由
  hybrid distribution 负责；A5 仍是运行时最终权威。

英文 README 和任务簇文档是语义权威。`C0 -> C1 -> C2 -> C3 -> C4 -> C5`
串行任务簇的实施、测试与合并已经完成；历史的构建、固定夹具、聚焦测试和
目标 worktree 验证记录继续作为当时的工程证据，不等于已达到 learned-firing
的完整行为验收。
