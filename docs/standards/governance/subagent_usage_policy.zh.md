# Subagent 使用规范

Language:
- English canonical: [subagent_usage_policy.md](subagent_usage_policy.md)
- Chinese companion: `subagent_usage_policy.zh.md`

状态：`2026-05-20`，适用于维护中文档与实现任务中的分布式工作。

在分发实施 worker 时使用这些规则。

## 目的与范围

本规范适用于任务被拆分到 subagent、worker 或 integration helper 的情形，
无论场景出现在文档、计划、代码还是测试中。

它不会覆盖仓库里已经存在的安全规则、ownership 规则或架构闭合规则。

项目原则：

- policy computation 和 test/orchestration 应被建模为 facade contracts 的显式
  producer / consumer，而不是仿真状态的隐藏 owner。

## 术语

- `subagent`：任何被委派去推进一个有边界子任务的代理。
- `worker`：被分配了明确写入或分析范围的 subagent。
- `main thread`：负责意图、范围与最终验收的主线程。
- `integration worker`：负责跨文件冲突处理与最终同步发布的 worker。
- `diagnostics worker`：仅限只读验证、审查或证据收集的 worker。

## 规则

- 每个 worker 只拿一个有边界的 scope，最好是互不重叠的文件集或段落集。
- 不得让多个并行作者拆写同一张规范性表格。
- 同一个文件通常只应有一个写作者，除非编辑范围明确不重叠且非常小。
- 除非负责 integration pass，worker 不得回滚、改写或重排其他 worker 已完成
  的编辑。
- naming 与 layering 以 standards tree 为准。
- 只有在子任务彼此独立、且不互相等待时才并行分发。
- 不要把当前立即阻塞的那一步交出去。
- 如果两个子任务可能碰到同一段行范围或同一套 canonical 术语，就改为串行。
- 优先使用能完成该有边界任务的最小 worker。
- 更大的 worker 留给跨文件、架构关键或发布敏感的工作。

## 交接与集成

- 每个被委派的任务都必须返回 touched files 和简短结论。
- main thread 负责最终 scope 决策、验收，以及任何发布或合并动作。
- 最终的 integration worker 负责跨文件冲突处理与 task status 更新。
- 状态文档和 README 索引必须与最终权威位置保持同步。
- WP implementation stream 可以停在 `Mergeable`；专门的 closure lane 负责
  acceptance review、README/index、archive 和必需双语同步，然后 WP 才标为
  `Closed`。
- 当被委派任务包含 simulation-architecture WP 发布或验收收尾时，使用
  [WP Closure Lane Policy](wp_closure_lane_policy.zh.md)。

## 链接规则

- 项目规则应从最近的权威索引中链接出来。
- Tier A 的治理规则应配齐中文辅文。
- 依赖本规范的 task README 应链接本文件，而不是重复全文。
- 如果 worker 结果改变了 naming、layering 或 ownership，integration pass
  必须先把相关文档对齐，再把任务标记为完成。
