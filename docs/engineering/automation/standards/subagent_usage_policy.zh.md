# Subagent 使用规范

Language:
- English canonical: [subagent_usage_policy.md](subagent_usage_policy.md)
- Chinese companion: `subagent_usage_policy.zh.md`

状态：`2026-05-23`，适用于维护中文档与实现任务中的分布式工作。

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/engineering/automation/standards/subagent_usage_policy.md`
Owner: `engineering/automation`
Last verified: `2026-08-07`

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
- 在相关 owner 的职责范围内，naming 与 layering 以该 owner 接受并维护在
  `docs/<owner>/standards/` 下的标准为准。
- 只有在子任务彼此独立、且不互相等待时才并行分发。
- 不要把当前立即阻塞的那一步交出去。
- 如果两个子任务可能碰到同一段行范围或同一套 canonical 术语，就改为串行。
- 优先使用能完成该有边界任务的最小 worker。
- 更大的 worker 留给跨文件、架构关键或发布敏感的工作。

## 任务簇规划纪律

分布式工作必须先有有限任务簇计划，不能从开放式的临时追加 wave 开始。

派发 implementation worker 之前，main thread 必须记录或命名：

- 当前 WP、阶段或 remediation slice 的有限任务簇列表；
- 每个任务簇的目标、写入范围、非目标、验证命令和关闭门；
- 哪些任务簇可以并行，哪些任务簇受依赖门控；
- 每个任务簇在重新划边界之前最多允许几轮 implementation。

硬规则：

- 不能派发无法映射到命名任务簇的 worker。
- 不能通过反复追加“再补一轮”让任务簇无限膨胀，而不重新基线化任务边界。
- 如果任务簇超过计划轮次上限，应停下来重新划定 scope，而不是继续发临时 wave。
- closure 或 acceptance 任务簇必须保持串行，直到 implementation 任务簇返回完整 packet。

推荐默认值：

- 小型 stabilization 或 repair 任务簇最多允许一轮 repair。
- implementation 任务簇最多允许两轮，超过后必须重新划分。
- 同一任务簇超过三轮是规划失败信号，继续派发前必须显式说明。

## 文档预算纪律

计划文档本身也是有成本的工作产物。任何 recovery、remediation 或 cleanup WP 在创建
sidecar plans、双语 companion、dispatch queue、ledger 或 acceptance files 前，必须先
声明明确的文档预算。

硬规则：

- 不得仅为了用新结构重述同一计划而创建额外 task-cluster、salvage-ledger、dispatch
  或 acceptance 文档。
- 如果某个 recovery WP 宣称要减少流程拖拽，它的文档数量必须下降，或给出显式理由。
- 如果计划无法装入已声明的 planning surface，应停止并 re-baseline，而不是继续加文档。
- closure lane 只有在 implementation stream 达到 mergeable 或显式 blocked 后，才可补
  必需 acceptance/index artifacts。

## 模型与思考预算规则

当工具支持相关控制时，subagent 派发必须记录 capability/risk tier 与 reasoning
budget。只有当前执行环境明确列出某个 model ID 可用时，才能记录该精确 ID；不得
从历史任务 packet 或仓库文字中复制 model ID。

默认复杂度阶梯：

- 低风险、局部或 diagnostics-only 任务，应使用能够可靠检查被分配证据的、成本最低
  的当前通用能力档。这包括文档审计、source fact ledger、聚焦验证、状态同步，以及
  不拥有复杂代码的 closure-lane chores。
- 中风险实现或集成任务，应使用具备实施能力的档位，并在控制可用时至少使用
  medium-equivalent reasoning。若任务触及 public APIs、bindings、architecture guards、
  compatibility behavior，或多个紧密相关的文件族，应提高 reasoning budget。
- 高风险重构、架构关键 seam、public contracts、scheduler semantics、runtime
  materialization、capability/spawn/fidelity paths，以及 counterfactual 或 replay
  semantics，应使用当前可用且适合任务的最强 coding/reasoning 能力档，并采用
  high-equivalent 或更强 reasoning。如果错误设计会导致后续返工或扩大架构边界，
  应使用有充分理由的最高预算。
- 如果任务复杂度难以判定，应归入更高风险档，或把立即阻塞的工作留在主线程。

最低规则：

- 当 reasoning 控制可用时，非平凡 implementation、refactor、public-surface 或
  architecture 工作不得低于 medium-equivalent reasoning。
- 不要仅因为较低能力或速度优化档允许更大 reasoning budget，就把复杂跨文件设计或
  高风险代码所有权交给该档位。
- dispatch queue 与 worker packet 应包含 `Capability tier / model ID / reasoning`
  列或等价字段。若当前环境不暴露可选择的精确 ID，则记录 `model ID: n/a`。任何偏离
  本规范的派发都必须在 dispatch packet 中显式说明。

## 派发生命周期与后台执行

main thread 应把 subagent 视为可持续后台 worker，而不是临时交互草稿。

- main thread 不应接管已经分配给 worker 的主要实现，除非任务明确 blocked、
  scope 错误或返回 incomplete。
- 派发成功后，main thread 可以结束当前轮，让 worker 在后台继续执行。
- 不得仅因为 main thread 不再等待、用户要求状态交接、或当前前台轮次应结束，
  就关闭、取消或替换 worker。
- 只有遇到明确 transport/request failure、重复或错误 scope 派发、不安全 scope
  冲突，或用户明确要求停止该 worker 时，才应提前关闭 worker。
- 已关闭、超时、rate-limited 或 interrupted 的 worker 只是 transport event。
  除非关闭前已经返回完整 packet，否则不能作为 implementation evidence。
- 如果派发因 request/platform error 失败，例如线程上限或 rate limit，main thread
  可以关闭已经完成的 worker 并重新派发失败任务。这属于异常恢复，不是新的任务 wave。
- 不要重新派发正在正常执行的任务。

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

必需 worker packet：

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

验收规则：

- `pass` 只对被分配的任务簇切片有效。
- `partial` 只能记录证据，永远不能解锁下游 closure。
- `blocked` 必须说明 blocker、owner、replacement path、失败或缺失的 guard，以及
  forced review trigger。它不是 pass state，但当继续推进只会制造 churn 时，它是可接受的
  诚实停止状态。
- main thread 必须本地复验重要 worker claim，才能把它作为 integration evidence。
- 只要仍存在未归属的 compatibility、legacy、diagnostics 或 public escape-hatch
  residual，就不能把 WP 或阶段标记为完成。

## 链接规则

- 项目规则应从最近的权威索引中链接出来。
- Tier A 的治理规则应配齐中文辅文。
- 依赖本规范的 task README 应链接本文件，而不是重复全文。
- 如果 worker 结果改变了 naming、layering 或 ownership，integration pass
  必须先把相关文档对齐，再把任务标记为完成。
