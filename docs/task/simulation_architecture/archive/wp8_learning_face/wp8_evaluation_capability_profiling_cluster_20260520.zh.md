# WP8-B Evaluation 与 Capability Profiling

状态：`2026-05-20` WP8 第二波分发单，已完成 / 已验收。

语言版本：

- 英文主文：
  [wp8_evaluation_capability_profiling_cluster_20260520.md](wp8_evaluation_capability_profiling_cluster_20260520.md)
- 中文辅文：`wp8_evaluation_capability_profiling_cluster_20260520.zh.md`

输入：

- [WP8 SCAL Learning Face](learning_face_wp8_20260520.zh.md)
- [WP7.5 Training Path Facade Bridge](../wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.zh.md)
- [WP7-B Runtime Capability Projection](../wp7_backend_capability_materialization/wp7_runtime_capability_projection_cluster_20260519.zh.md)
- [WP5 验证套件](../wp5_validation_harness/validation_harness_wp5_20260519.zh.md)
- [WP8 验收审查](../../review/wp8_learning_face_acceptance_review_20260520.zh.md)

命名说明：

- WP8 是 SCAL Learning 面的 task family。
- `WP8-B` 是该 family 内的 evaluation 与 capability-profiling 流。
- 维护中的 training-path bridge 仍然是 `WP7.5`；`WP8-B` 必须把它
  作为 facade-shaped bridge reference 来引用，而不是重新定义它。
- `WP8-B` 是 docs-first 线。它不能因为 helper 或 probe 存在就推断 support，
  也不能触碰 `WP8-A`、`WP8-C` 或 `WP8-D` 文件。

## 1. 目的

`WP8-B` 规定 evaluation run、benchmark protocol、capability profile、
score attribution 与 capability evidence 的描述方式，使 Learning 面能够
比较输出，但不会变成 hidden truth source。

这是一条高推理流，因为最容易的失败模式就是把 helper 或 probe 的可用性当成
support proof。这不允许。helper/probe 的存在最多只能解释 observability 或
deployment state，不能单独证明维护中的 capability。

`WP8-B` 需要回答：

1. evaluation run 的 benchmark protocol 是什么？
2. capability profile schema 里哪些字段属于 metadata，哪些不属于？
3. score attribution 如何记录，才能不坍缩成 support claim？
4. 什么算 capability evidence，什么明确不算？

## 2. 范围边界

`WP8-B` 可以：

1. 定义 benchmark protocol 词汇、run identity 与 reproducibility 要求。
2. 定义 capability profile schema 字段，并把 metadata 与 support claims 分开。
3. 定义 score attribution 规则、权重与可追踪性要求。
4. 定义 capability evidence bundle 与 evidence 接受规则。
5. 定义并行 worker 角色、reasoning budget 与本簇的 doc-only validation 检查。

`WP8-B` 不可以：

1. 添加新的 simulation lifecycle，或改变 simulation authority 边界。
2. 因为 helper、probe 或 diagnostic path 存在，就晋级 capability support。
3. 把 metadata、profile claims 与 hidden support claims 混成一条不区分的记录。
4. 修改本双文档之外的 runtime code、tests 或 review artifacts。
5. 把维护中的 training-path bridge 从 `WP7.5` 改派到 `WP8-B`。

## 3. 工作包

| 流 | 必需产出 | 写入范围 | 预算 |
|----|----------|----------|------|
| `WP8-B1 Benchmark Protocol Boundary` | 定义 benchmark identity、输入、seed/version 纪律与 reproducibility 字段。 | `docs/task/simulation_architecture/wp8_learning_face/` 下的 docs。 | 高。 |
| `WP8-B2 Profile Schema And Claim Separation` | 定义 profile schema，以及 metadata、profile claims 与 hidden support claims 的分离。 | 仅 docs。 | 高。 |
| `WP8-B3 Score Attribution And Evidence` | 定义 score 分解、权重、evidence bundling 与 anti-overclaim 规则。 | 仅 docs；可引用 `WP7.5`。 | 高。 |
| `WP8-B4 Validation And Publication Sync` | 定义 acceptance gates、doc-only validation commands，以及与 `WP8` / `WP7.5` 的交叉引用。 | 仅 docs；串行发布步骤。 | 中等。 |

## 4. 分发计划

| 流 | 主要关注点 | 备注 |
|----|------------|------|
| `WP8-B1 Benchmark Protocol Boundary` | benchmark protocol、run identity、scenario/seed/version 纪律。 | 为后续所有 profile 工作建立共享词汇。 |
| `WP8-B2 Profile Schema And Claim Separation` | metadata 字段、profile claims、hidden support claims。 | 必须保持保守，并明确说明什么不是 support。 |
| `WP8-B3 Score Attribution And Evidence` | score breakdown、evidence reference、helper/probe anti-overclaim。 | 本簇内部最高边界纪律。 |
| `WP8-B4 Validation And Publication Sync` | acceptance gates、validation commands、bridge reference。 | 在发布被视为完成前的串行检查。 |

并行规则：

- `WP8-B1` 与 `WP8-B2` 在共享 benchmark vocabulary 固定后可以并行。
- `WP8-B3` 可以在 profile schema 稳定到足以承载 evidence reference 与 score
  attribution 之后推进。
- `WP8-B4` 是串行步骤，只应在其它流稳定后执行。

## 5. Protocol 与 Boundary 规则

### 5.1 Benchmark Protocol

每个 benchmark run 都必须是可版本化、可复现的。protocol 至少要说明：

- benchmark 或 scenario family 名称，
- protocol version，
- seed 或 seed policy，
- environment 或 runner identity，
- input slice 或 dataset selector，
- score dimensions，
- evidence bundle references，
- result status 与 timestamp。

evaluation 文本必须显式描述 protocol。像“模型表现很好”这种模糊句子不是
protocol。

### 5.2 Profile Schema

profile schema 必须把三类内容分开：

| 类别 | 作用 | 规则 |
|------|------|------|
| Metadata | identity、provenance、versioning、run context、ownership、timestamp。 | 只负责描述，不能证明 support。 |
| Profile claims | 从 benchmark run 派生出的 evaluation-facing claims。 | 必须引用 protocol 与 evidence bundle。 |
| Hidden support claims | 会暗示真实 capability ownership 的维护中 support statement。 | 不能从 metadata、profile claims 或 helper/probe presence 推断出来。 |

schema 可以把 capability 记为 `observed`、`proposed`、`blocked` 或
`unsupported`，但这些标签必须始终被 evidence 约束。它们不是维护中 support
的同义词。

### 5.3 Score Attribution

score attribution 必须拆成显式维度，而不是一个黑箱总分。每个 score component
都必须记录：

- 测量了什么，
- 是哪次 benchmark run 产出的，
- 哪个 evidence bundle 支撑它，
- 该 score 是 descriptive、comparative 还是 gating-related。

score attribution 不能悄悄升级 capability status。高分可以表示潜力或 benchmark
适配度，但不能单独证明维护中的 support。

### 5.4 Capability Evidence

capability evidence 可以包括：

- benchmark logs，
- trace digests，
- seeded configuration records，
- result artifacts，
- reproducibility notes，
- 明确描述证据的 review references。

capability evidence 不包括：

- 仅仅有 helper 或 probe 存在，
- 某个 code symbol 存在，
- implementation shortcut，
- 没有解释的 success log，
- 跳过 benchmark protocol 的任何说法。

### 5.5 Highest-Reasoning Boundary Discipline

本簇必须对 overclaim 保持 fail-closed。规则是：

- helper 或 probe presence 可能提升 observability，
- helper 或 probe presence 可能解释 evaluation 是怎么跑的，
- helper 或 probe presence 不代表 support。

如果唯一证据只是 helper 或 probe 存在，那么正确输出是 `unknown`、
`observed` 或 `unsupported`，取决于 protocol。但它不是 `supported`。

## 6. 验收产物

任何 `WP8-B` gate 若要报告为通过，验收包必须包含下列规范性产物：

| 产物 | 必需状态 | 作用 |
|------|----------|------|
| `docs/task/simulation_architecture/wp8_learning_face/wp8_evaluation_capability_profiling_cluster_20260520.md` | required | 英文规范分发单，定义 evaluation 与 capability profiling。 |
| `docs/task/simulation_architecture/wp8_learning_face/wp8_evaluation_capability_profiling_cluster_20260520.zh.md` | required | 同一套规范规则的中文辅文。 |
| `docs/task/simulation_architecture/wp8_learning_face/learning_face_wp8_20260520.md` | required | Learning 面的 task-family 锚点。 |
| `docs/task/simulation_architecture/wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.md` | required | facade-shaped training-path 维护桥接参考。 |

产物规则：

- 任一必需产物缺失，则结果必须为 `fail`。
- 如果 docs 没有显式区分 metadata、profile claims 与 hidden support claims，
  结果必须为 `fail`。
- 如果允许 helper/probe presence 推出 support，结果必须为 `fail`。

## 7. 严格 Gate 规则

下表中的每个 gate 都必须在 acceptance review 中独立判定。每个 gate 只能以
`pass`、`fail` 或 `blocked` 收束。

| Gate | Required evidence | Pass 口径 | Fail 口径 | 环境阻塞降级表述 |
|------|-------------------|-----------|-----------|------------------|
| `WP8-B1 Benchmark Protocol Boundary` | 验收审查必须点名检查过的 benchmark protocol 字段，说明使用的 versioning 或 seed 纪律，并引用用来验证 protocol 显式且可复现的 doc-only validation commands。 | 只有当 benchmark protocol 词汇显式、已版本化，并且足以在没有 hidden assumption 的情况下复现或比较 run 时，才能 `pass`。 | 如果 protocol 字段是隐式的、缺少 versioning、reproducibility 不清楚，或证据缺失，则必须 `fail`。 | 如果本地验证因缺少 docs、链接损坏或 workspace state 问题而受阻，记为 `blocked`，并写出精确命令、精确阻塞点，以及剩余的有限静态结论。 |
| `WP8-B2 Profile Schema And Claim Separation` | 验收审查必须点名检查过的 profile-schema 字段，说明 metadata 在哪里结束、support claims 从哪里开始，并引用用来确认分离关系的 doc-only validation commands。 | 只有当 schema 将 metadata、profile claims 与 hidden support claims 分开，且没有字段偷偷充当 support 时，才能 `pass`。 | 如果 metadata 与 support claims 混成一条记录、schema label 含糊，或 hidden support claims 被描述性字段推断出来，则必须 `fail`。 | 如果因为某个 reference doc 缺失而无法完整检查 schema，记为 `blocked`，并写出精确命令、精确阻塞点与剩余的 doc-only 结论。 |
| `WP8-B3 Score Attribution And Evidence` | 验收审查必须点名检查过的 score component，说明每个 component 使用的 evidence bundle，并引用用来验证 score attribution 不会暗示 support 的 doc-only validation commands。 | 只有当 score attribution 被拆分、被 evidence 绑定、并且对 capability status 保持保守时，才能 `pass`。 | 如果 score 被当成 support、evidence 不可追踪，或把 helper/probe presence 当成证明，则必须 `fail`。 | 如果 evidence trace 在本地不可用，记为 `blocked`，并写出精确命令、精确阻塞点与剩余的描述性结论。 |
| `WP8-B4 Validation And Publication Sync` | 验收审查必须确认英文与中文文档对齐，引用 `WP8` 和 `WP7.5` 的参考关系，并列出用于检查 publication readiness 的 doc-only validation commands。 | 只有当双文档对齐、bridge reference 指向 `WP7.5`，并且没有任何措辞把 maintained training-path migration 重新分派给 `WP8-B` 时，才能 `pass`。 | 如果对齐漂移、bridge reference 缺失，或 helper/probe anti-overclaim 语句被削弱，则必须 `fail`。 | 如果 publication sync 被 workspace state 或缺失 source doc 阻塞，记为 `blocked` 并保持 gate 开放。 |

判定规则：

- `pass` 要求该 gate 的全部 required evidence 到位，且同一份 review packet 中没有
  相互矛盾的证据。
- 只要 required evidence 缺失、被反证，或被意图性表述替代，就必须 `fail`。
- `blocked` 只允许用于环境或 workspace 限制，并且必须保持 gate 未决。

## 8. 验证命令

```bash
git diff --check
rg -n "WP8-B|benchmark protocol|profile schema|score attribution|capability evidence|hidden support|helper|probe|support claim|WP7.5" docs/task/simulation_architecture/wp8_learning_face/wp8_evaluation_capability_profiling_cluster_20260520*.md docs/task/simulation_architecture/wp8_learning_face/learning_face_wp8_20260520*.md docs/task/simulation_architecture/wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520*.md
```

验证表述规则：

- 命令执行并通过时，acceptance review 应写 `passed`，并附精确命令。
- 命令执行并失败时，acceptance review 应写 `failed`，并附精确命令与失败现象。
- 命令无法执行时，acceptance review 应写 `blocked`，并附精确命令、精确阻塞点和
  所需的下一环境。

## 9. 非目标

- 不添加 benchmark runner code，也不修改 runtime execution path。
- 不把 helper 或 probe presence 当成 support evidence。
- 不把 metadata、profile claims 与 hidden support claims 混在一起。
- 不触碰 `WP8-A`、`WP8-C`、`WP8-D` 或 review artifacts。
- 不重新定义属于 `WP7.5` 的维护桥接。
