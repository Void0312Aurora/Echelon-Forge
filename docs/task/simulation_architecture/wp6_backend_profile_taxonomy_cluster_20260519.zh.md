# WP6-A 规范分发单：后端配置文件分类

状态：`2026-05-19` 后端配置文件 taxonomy 已完成分发单，并已产出面向实现的注册表。

语言版本：

- 英文主文：[wp6_backend_profile_taxonomy_cluster_20260519.md](wp6_backend_profile_taxonomy_cluster_20260519.md)
- 中文辅文：`wp6_backend_profile_taxonomy_cluster_20260519.zh.md`

输入：

- [WP6 后端配置文件策略](backend_profile_policy_wp6_20260519.zh.md)
- [WP6-A 后端配置文件注册表](wp6_backend_profile_registry_20260519.zh.md)
- [仿真系统架构设计](../../plan/architecture/simulation_system_architecture_design.zh.md)
- [架构与性能路线进一步调研](../../plan/architecture/architecture_and_performance_research_followup.zh.md)
- [架构计划审查](../review/architecture_plan_review_20260519.zh.md)
- [Temp-02 SCAL 架构愿景审查](../review/temp-02_review_20260519.zh.md)
- [WP2.5 调度语义冻结](scheduler_semantics_wp25_20260519.zh.md)
- [WP4 facade 对齐](facade_alignment_wp4_20260519.zh.md)

规范术语：

- `MUST` 表示 WP6 维护文档与后续实现所要求的行为。
- `MUST NOT` 表示不能定义维护中的 backend 真值的行为。
- `SHOULD` 表示默认规则，偏离需要显式补充任务或审查说明。
- `MAY` 表示允许的兼容或文档路径。

## 1. 目的

本分发单把 `WP6-A Backend Profile Taxonomy` 收敛为一个有边界的文档任务。它会先冻结后端 profile 词汇，再去写 parity budget 或 resident-state 发布细节。

taxonomy 必须把维护中的 reference 路径，与 accelerated、resident-state、approximate 和 diagnostics-only 路径区分开。它还必须把 host-owned 与 backend-owned 的边界写清楚，避免后续 backend capability 工作偷偷长出第二条语义路径。

如果旧规划里仍把这一区域叫作 `WP7`，那只应视为历史别名。本分发单的规范命名线是 `WP6`。

## 2. 分发产物

| 流 | 必需产出 | 负责人画像 | 思考预算 |
|----|---------|-----------|---------|
| `WP6-A1 Profile Catalog` | backend profile 类别、id、维护状态、比较锚点与禁止声明的规范表。 | backend taxonomy worker。 | 高。 |
| `WP6-A2 Ownership And Sync Classification` | host-owned、backend-owned、partial-sync、observation-only 与 export-only 规则，以及单向 / 双向约束。 | backend taxonomy worker。 | 高。 |
| `WP6-A3 Capability Surface Boundary` | `RuntimeCapabilities`、`BackendCapabilityFacade` 与所有 backend capability query 入口的边界规则。 | 兼顾集成的 taxonomy worker。 | 中高。 |
| `WP6-A4 Naming And Cross-Reference Sync` | 中英对齐，以及对历史 `WP7` 引用的兼容说明。 | 集成负责人。 | 中。 |

## 3. 后端 profile 类别

| profile 类别 | WP6 默认判断 | 维护状态 | 状态 ownership | sync 规则 | parity 规则 | 备注 |
|-------------|--------------|----------|---------------|------------|-------------|------|
| `reference` | 规范基线。 | 维护中。 | host-owned state。 | 仅 host-owned。 | exact。 | CPU exact 路径。 |
| `accelerated_exact` | 语义相同，但实现更快。 | 仅在保持 exact 时才维护。 | host-owned 或 hybrid，但 host truth 必须显式。 | 显式 host sync 与 committed-state 可见性。 | exact event order 与 exact committed state。 | 通过契约接入的 CUDA helper。 |
| `resident_state` | 后端保留部分运行状态。 | 受门控；在 sync 与 parity 显式化前不算维护中。 | backend-owned partial state，且显式说明 host 可见性。 | 显式 partial sync 或 observation-only export。 | 需要声明 parity budget。 | device-resident observation 或 physics helper。 |
| `approximate` | 故意近似。 | 默认实验态。 | backend-owned 或 hybrid。 | 显式且受限。 | 仅容差式比较。 | surrogate 或 fidelity 降级后端。 |
| `diagnostics_only` | 只用于检查或调试。 | 永远不是维护中的真值。 | 按 helper 声明。 | 仅导出。 | 不宣称维护中的 parity。 | trace 导出或 probe helper。 |

### 3.1 profile 类别不变式

这五类 profile 不是性能档位，而是语义契约：

1. `reference` 是唯一可用作维护中比较锚点的基线。它定义 host-owned 的真值线，也是后续文档需要稳定语义参照时的默认回退。
2. `accelerated_exact` 可以改变执行策略、调度或硬件落点，但必须保持与 reference 一致的事件顺序和 committed-state 含义。
3. `resident_state` 可以保留 backend-local 状态，但前提是 host 可见的重建规则必须明确。如果 host 无法恢复或检查声明的 state 范围，这条路径就不能算维护中。
4. `approximate` 只允许在明确的容差包内偏离。它必须在 parity budget 里写清楚该容差，且不能通过措辞、别名或兼容快捷方式把自己说成 exact。
5. `diagnostics_only` 可以导出 trace、指标或快照，但它绝不能变成维护中的比较目标、隐藏 runtime 真值或回退控制路径。

### 3.2 ownership 与 sync 边界规则

ownership 标签与 sync policy 是两个独立决定：

| 边界类型 | 含义 | 允许的真值持有者 | 必需的 sync 形态 | 禁止声明 |
|---------|------|------------------|-----------------|----------|
| `host-owned` | host 保持维护中真值的权威来源。 | host。 | 仅在声明时才允许显式 host sync。 | 默认把 backend-local state 视为权威。 |
| `backend-owned` | backend 持有声明范围内的权威 shard。 | backend。 | 声明式 export、partial sync 或 observation 路径。 | host 在同一 shard 上静默拥有权威。 |
| `partial-sync` | 只把 backend state 的受限子集同步回 host。 | mixed，但必须写出谁是权威侧。 | 一个声明的子集，加上一个声明的 cadence / trigger。 | 在没有明确契约时宣称全状态等价。 |
| `observation-only` | backend 只暴露度量或 trace，不参与维护中的控制流。 | 由 helper 或 backend 按声明决定。 | 只读可见。 | 把观测数据说成维护中的 state。 |
| `export-only` | backend 只输出用于检查、replay 或离线分析的工件。 | 由 helper 或 backend 按声明决定。 | 单向导出。 | 把导出结果当作运行时真值。 |

在本分发单里，只有当 ownership 标签、sync 形态和 parity budget 三者能一起写出来时，某条 backend 路径才算维护中。如果其中任何一项缺失，那条路径就应留给后续实现工作，而不是放进 taxonomy。

## 4. 必需 taxonomy 元数据

每个维护中的 backend profile 条目 MUST 声明：

| 字段 | 规则 |
|------|------|
| `backend_profile_id` | 供文档、审查、replay 和 diagnostics 使用的稳定 id。 |
| `profile_class` | `reference`、`accelerated_exact`、`resident_state`、`approximate`、`diagnostics_only` 之一。 |
| `comparison_reference` | 用作语义比较锚点的后端或路径。 |
| `host_state_owner` | 仍然由 host 拥有的状态 shard 或输出。 |
| `backend_state_owner` | 可以驻留在后端的状态 shard 或输出。 |
| `sync_policy` | host-owned、backend-owned、partial sync、observation-only sync 或 explicit export。 |
| `state_scope` | 该 profile 覆盖的状态族。 |
| `parity_budget_ref` | 关联的 parity budget 或 comparison budget。 |
| `observability_scope` | 哪些内容可以作为维护中的输出暴露。 |
| `compatibility_rule` | 旧调用方或 diagnostics-only helper 的行为。 |
| `deprecation_rule` | 何时该 profile 不再维护或必须收窄。 |
| `validation_gate` | 证明该 profile 安全的审查或测试门。 |

这些字段的 implementation-ready registry seed 是
[WP6-A 后端配置文件注册表](wp6_backend_profile_registry_20260519.zh.md)。
该注册表是 WP6-A 后续 capability projection 的元数据来源；`RuntimeCapabilities`
仍然只是已声明 registry/profile 元数据与可探测部署事实的 projection，不是
source of truth。

## 5. capability surface 边界

WP6-A MUST 说明：

1. `RuntimeCapabilities` 是 capability projection，不是 profile 类别，也不是 planner。
2. `RuntimeCapabilities` 可以镜像已声明的 profile 元数据和不可变部署事实，但不能发明 profile 未声明的能力语义。
3. `BackendCapabilityFacade` 是查询 capability 的受支持策略面。它可以汇总已声明的 profile 数据，但不能绕过 taxonomy 规则，也不能去读隐藏的实现真值。
4. 任何会改变维护语义的 capability flag，都必须先在 profile 上声明。如果某个含义无法用 profile 元数据表达，那条规则就应留给后续实现工作，而不是塞进 facade。
5. diagnostics-only helper 可以贡献观测数据，但不能变成维护中的 capability 真值，也不能改变 host/backend ownership。
6. 如果某个 capability query 需要隐藏的 resident state、私有缓存或仅实现分支逻辑才能回答，那它还不算 capability query。

## 6. 非目标

- 实现 backend 选择逻辑。
- 重写 GPU 或 resident-state 代码。
- 改变调度语义。
- 把 `RuntimeCapabilities` 提升成新语义路径。
- 把性能档位名称当成 profile 类别。
- 把兼容 helper 收编为维护中的真值。

## 7. 退出标准

当以下条件满足时，本分发单退出：

1. profile catalog 区分五类 backend profile，而且每一类的定义都不互相重叠。
2. 每个维护中的类别都写清比较锚点、ownership、sync policy 和禁止声明。
3. ownership 与 sync 矩阵明确覆盖 `host-owned`、`backend-owned`、`partial-sync`、`observation-only` 与 `export-only`。
4. `RuntimeCapabilities` 与 `BackendCapabilityFacade` 被摆放为策略面，而不是隐藏 runtime 真值。
5. 英文与中文辅文的章节顺序、profile 类别列表和互链关系一致。
6. 对历史 `WP7` 的命名说明足够明确，但不会重新打开规范命名决定。

## 8. 验证命令

```bash
git diff --check
rg -n "reference|accelerated_exact|resident_state|approximate|diagnostics_only|host-owned|backend-owned|partial-sync|observation-only|export-only|RuntimeCapabilities|BackendCapabilityFacade" docs/task/simulation_architecture/wp6_backend_profile_taxonomy_cluster_20260519*.md
rg -n "wp6_backend_profile_taxonomy_cluster_20260519\\.zh\\.md" docs/task/simulation_architecture/wp6_backend_profile_taxonomy_cluster_20260519.md
rg -n "wp6_backend_profile_taxonomy_cluster_20260519\\.md" docs/task/simulation_architecture/wp6_backend_profile_taxonomy_cluster_20260519.zh.md
```
