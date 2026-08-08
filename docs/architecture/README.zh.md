# 架构文档

语言：英文为规范页；[中文配套](README.md)。

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/architecture/README.md`
Owner: `cross-domain architecture`
Last verified: `2026-08-08`

这里是跨领域系统架构、runtime 分层、contracts、后端和架构决策的目标 owner。
迁移期间，当前权威仍位于 [plan/architecture](../plan/architecture/README.zh.md)、
[plan/runtime_facade](../plan/runtime_facade/README.zh.md) 和
[plan/exact_runtime](../plan/exact_runtime/README.zh.md)。只有经过单独评审的迁移
迭代才能把入口移入本区域。

## Standards

- [仿真约定](standards/simulation_conventions.zh.md)：维护中的引擎中立坐标、单位、观测、
  array、action 与确定性约定。
- [Runtime workflow 与 contract 基线](standards/runtime_workflow_and_contract_baseline.zh.md)：
  维护 loader 到 runtime 的阶段归属与 roundtrip seam，并服从严格仿真架构基线。

## 开放问题

- [系统模块化 issue](work/issues/modularization_plan.zh.md)：draft residual 分析；
  目录位置不授权实施。

## 评审

- [架构评审 — 2026-06-03](reviews/architecture_review_20260603.zh.md)
- [架构规范性与正确性评审 — 2026-06-03](reviews/architecture_norms_correctness_review_20260603.zh.md)

这些文档是保留的评审快照，不能替代当前 standards、plans、实现或可执行证据。

未来架构 standard、reference、work 和 review 使用
[共享文档结构](../engineering/documentation/structure_examples.zh.md)。
