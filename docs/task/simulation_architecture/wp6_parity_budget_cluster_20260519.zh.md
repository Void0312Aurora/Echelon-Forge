# WP6-B 规范分发单：Parity Budget 与比较规则

状态：`2026-05-19` parity budget 与比较规则已完成分发单，并已产出面向实现的注册表。

语言版本：

- 英文主文：[wp6_parity_budget_cluster_20260519.md](wp6_parity_budget_cluster_20260519.md)
- 中文辅文：`wp6_parity_budget_cluster_20260519.zh.md`
- 实现注册表：[wp6_parity_budget_registry_20260519.zh.md](wp6_parity_budget_registry_20260519.zh.md)

输入：

- [WP6 后端配置文件策略](backend_profile_policy_wp6_20260519.zh.md)
- [WP6-A 后端配置文件分类分发单](wp6_backend_profile_taxonomy_cluster_20260519.zh.md)
- [仿真系统架构设计](../../plan/architecture/simulation_system_architecture_design.zh.md)
- [架构与性能路线进一步调研](../../plan/architecture/architecture_and_performance_research_followup.zh.md)
- [架构计划审查](../review/architecture_plan_review_20260519.zh.md)
- [Temp-02 SCAL 架构愿景审查](../review/temp-02_review_20260519.zh.md)
- [WP2.5 调度语义冻结](scheduler_semantics_wp25_20260519.zh.md)
- [WP5 验证套件](validation_harness_wp5_20260519.zh.md)

规范术语：

- `MUST` 表示 WP6 维护文档与后续实现所要求的行为。
- `MUST NOT` 表示不能定义维护中的 parity 真值的行为。
- `SHOULD` 表示默认规则，偏离需要显式补充任务或审查说明。
- `MAY` 表示允许的兼容或 diagnostics 路径。

## 1. 目的

本分发单把 `WP6-B Parity Budget And Comparison Rules` 收敛成一个有边界的文档任务。它要冻结 backend profile 如何发布 parity-budget 元数据、哪些比较属于 exact / toleranced，以及哪些差异只能保留为 diagnostics-only。

中心规则很简单：parity budget 是 profile-owned metadata，不是一个单独的标量旋钮。它属于声明该 budget 的 backend profile，并且必须和该 profile 的比较契约一起出现。

## 2. 分发产物

| 流 | 必需产出 | 负责人画像 | 思考预算 |
|----|---------|-----------|---------|
| `WP6-B1 Budget Template` | 规范化的 parity-budget 模板、必需字段，以及每个 profile class 的一个示例。 | parity budget worker。 | 高。 |
| `WP6-B2 Comparison Domain Rules` | event order、snapshot versions、numeric state、observation export 与 diagnostics trace 的 exact / tolerance 规则。 | parity budget worker。 | 高。 |
| `WP6-B3 Profile-Specific Guidance` | 面向 `reference`、`accelerated_exact`、`resident_state` 与 `approximate` 的可执行预算指导。 | parity budget worker。 | 高。 |
| `WP6-B4 Diagnostics And Acceptance Rules` | 维护预算所需的 diagnostics 元数据、mismatch 分类与验收条件。 | 兼顾集成的 parity worker。 | 中高。 |

## 3. Parity Budget 模板

任何声称 parity 的维护中 backend profile 都 MUST 携带一个 profile-owned 的 `parity_budget` block，或者在 profile-owned 的引用记录中指向它。这个 budget 不能是脱离 profile 契约的自由浮动标量。

### 3.1 必需字段

| 字段 | 状态 | 含义 |
|------|------|------|
| `budget_id` | MUST | budget 记录的稳定 id。 |
| `budget_version` | MUST | budget 记录的版本号。 |
| `backend_profile_id` | MUST | 该 budget 的 owner profile。 |
| `profile_class` | MUST | `reference`、`accelerated_exact`、`resident_state`、`approximate` 之一。 |
| `comparison_reference` | MUST | 用作比较锚点的语义参照。 |
| `budget_scope` | MUST | 该 budget 覆盖的 clock domain、state shard 与 output family。 |
| `comparison_domains` | MUST | 各比较域的 exact / tolerance 规则。 |
| `sync_barriers` | MUST | 用于 replay 与比较的 barrier。 |
| `diagnostics_requirements` | MUST | 用于解释 mismatch 的结构化字段。 |
| `mismatch_policy` | MUST | 比较失败后如何处理。 |
| `acceptance_gate` | MUST | 进入维护状态前所需的审查或测试门。 |
| `change_reason` | MAY | 该 budget revision 的简短原因。 |

### 3.2 规范形状

```yaml
parity_budget:
  budget_id: parity_budget.cpu_exact.reference.v1
  budget_version: 1
  backend_profile_id: cpu_exact.reference
  profile_class: reference
  comparison_reference: cpu_exact
  budget_scope:
    clock_domains: [physics.fixed_tick, sensor.scan_slot]
    state_shards: [physics, track, observation]
    output_families: [observation_packet, diagnostics_trace]
  acceptance_gate: wp6_b_acceptance_review
  change_reason: reference profile parity budget initial revision
  comparison_domains:
    event_order:
      mode: exact
      key: [timestamp, priority, event_id]
      allowed_drift: none
    snapshot_versions:
      mode: exact
      identity: [world_id, global_version, barrier_id, barrier_sequence, shard_versions]
      allowed_drift: none
    numeric_state:
      mode: exact_or_toleranced
      comparator: exact
      tolerance_budget: {}
    observation_export:
      mode: exact_envelope_with_domain_payload
      envelope: [schema_version, field_set, visibility_label, provenance, source_snapshot_version]
      payload: inherit_numeric_state
    diagnostics_trace:
      mode: exact_graph_with_diagnostics_text
      ancestry: [source_request_id, event_id, source_snapshot_version, mismatch_summary]
      summary_text: diagnostics_only
  sync_barriers: [input_injection, window_commit, export]
  diagnostics_required:
    - backend_profile_id
    - budget_id
    - budget_version
    - source_snapshot_version
    - resulting_snapshot_version
    - comparison_reference
    - mismatch_summary
  mismatch_policy:
    maintained_profiles: fail
    diagnostics_only_profiles: report_only
```

规则：

1. budget MUST 位于 backend profile 元数据中，或由 profile 引用的 profile-owned block 中。
2. budget MUST 写明 comparison reference。
3. budget MUST 写明覆盖的 clock domain 或 output families。
4. budget MUST 写明 replayability 所需的 sync barrier。
5. budget MUST 写明解释 mismatch 所需的 diagnostics 字段。
6. budget MUST 自身带版本号，避免后续 revision 语义不清。

## 4. 比较域规则

比较域是分层的，不是可互换的：

- event order 与 snapshot versions 属于 identity 域。
- numeric state 属于 payload comparison 域。
- observation export 是 envelope + payload 的桥接域。
- diagnostics trace 属于 ancestry + explanation 域。

如果一个值同时落入多个域，那么 identity 层永远优先按 exact 规则比较；numeric tolerance 只作用在 payload 层。

| 比较域 | exact 边界 | toleranced 边界 | diagnostics-only 边界 |
|--------|------------|-----------------|-----------------------|
| Event order | 生成顺序所用的 `(timestamp, priority, event_id)` 以及 event-family membership MUST 完全一致。 | 维护中的 parity 不允许漂移。任何重排都是 mismatch。 | 说明文字可以不同，但不能改变顺序定义。 |
| Snapshot versions | snapshot identity、barrier id、barrier sequence、shard-version map 与 lineage MUST 完全一致。任何内部版本号必须先归一化成导出的 `SnapshotVersion` 再比较。 | 维护中的 parity 不允许漂移。snapshot 里的 numeric payload 不在这一层比较。 | 只有在标注为 diagnostics-only 且排除在维护真值之外时，才允许 pre-commit 或 compatibility snapshot 存在。 |
| Numeric state | profile 明确写 exact 时，值就必须 exact。 | 只有 `tolerance_budget` 里列出的 field family 才能漂移，而且只能使用显式 comparator（如 `abs`、`rel`、`ulp` 或其他明确写出的 comparator）。未列出的字段默认 exact。 | 经过 rounding 或 summary 化的输出可用于 diagnostics，但不能算维护真值。 |
| Observation export | schema、field set、visibility label、provenance 与 source snapshot 引用 MUST 完全一致。 | numeric payload 值继承 `numeric_state` 规则；export envelope 本身永远不走 tolerance。 | pre-commit export 或 compatibility view 只可以作为 diagnostics-only artifact，并且必须显式标记。 |
| Diagnostics trace | 结构化 ancestry id、source request/event id、source snapshot 链接与 mismatch code MUST 完全一致。 | 只要结构化 trace 一致，human-readable summary text 与排版 MAY 变化。 | 只有 summary-only 或 narrative-only trace 才是 diagnostics-only，不能替代结构化 trace。 |

## 5. Profile 专属预算指导

下面的 profile 指导是可执行的，不是愿望清单。diagnostics-only artifact 可以复用相同字段名做报告，但它们不算维护中的 parity budget。

| Profile | comparison reference | 预算规则 | 默认 mismatch policy |
|---------|----------------------|----------|----------------------|
| `reference` | `cpu_exact` 或维护中的 CPU exact 路径。 | 所有维护中的比较域都必须 exact；不允许 tolerance budget。 | fail。 |
| `accelerated_exact` | 维护中的 reference profile。 | 必须保持语义 exact；加速内部实现不能放松 parity。 | fail。 |
| `resident_state` | 维护中的 host-visible reference path。 | 必须把 host-visible 的维护状态与 backend-resident 的运行状态分开，并在声明的 sync barrier 上做锚定比较。 | fail，除非某个域明确标成 diagnostics-only。 |
| `approximate` | 命名好的 baseline profile。 | 必须写出所有被允许容差的字段族与 comparator；未列出的字段仍然 exact。 | report 并隔离，等待审查。 |

### 5.1 `reference`

- `comparison_reference` SHOULD 指向 `cpu_exact` 或当前维护中的 CPU 基线。
- `comparison_domains` MUST 全部为 exact。
- `tolerance_budget` MUST 为空。
- `diagnostics_only` 行为不接受为维护真值。
- `mismatch_policy` SHOULD 为 fail-fast，因为任何漂移都是真实 parity 破坏。

### 5.2 `accelerated_exact`

- 该 profile 复用 reference 的 parity budget。
- event order、snapshot versions、numeric state、observation export 与 diagnostics ancestry 在维护表面上 MUST 保持 exact。
- 任何 accelerator-specific kernel 差异都必须留在比较层之下，不能泄漏到导出的维护状态里。
- 如果必须引入 tolerance，那它就不再是 `accelerated_exact`，而必须重分类。
- `mismatch_policy` MUST 为 fail。

### 5.3 `resident_state`

- budget MUST 把 `host_visible_maintained_state` 和 `backend_resident_operational_state` 分开写清楚。
- 比较 SHOULD 锚定在声明的 sync barrier 上；未同步的 backend-local state 只算 diagnostics-only，除非被显式提升。
- 导出的维护 snapshot 在 event order、snapshot versions、provenance 与 observation envelope 上仍必须遵守 exact 规则。
- 任何被允许的 numeric 漂移都必须局限在显式命名的 field family 中，而且只能在审查接受该 budget 后存在。
- 如果没有写明 host/backend split，这个 budget 就是不完整的。

### 5.4 `approximate`

- budget MUST 列出所有被允许容差的 field family、comparator 与 threshold。
- 未列出的字段默认 exact。
- profile MUST 写明 comparison reference，并解释为什么允许近似。
- profile SHOULD 保持 diagnostics-only，直到审查显式把它提升为维护中。
- profile MUST NOT 在仍存在 tolerance 时把自己描述成 `reference` 或 `accelerated_exact`。

## 6. 非目标

- 实现 parity 检查或 runtime comparator。
- 构建 replay harness。
- 改变 WP2.5 scheduler 语义。
- 让 wall-clock speed 决定 parity。
- 把 tolerance 藏进未版本化的 helper 代码里。
- 把 approximate 输出当成 exact。
- 在本分发单里重新打开 profile taxonomy。

## 7. 退出标准

当以下条件满足时，本分发单退出：

1. 每个维护中的 profile 都携带 profile-owned 的 parity budget 记录或对该记录的 profile-owned 引用。
2. event order 与 snapshot versions 被写成 exact-only 的 identity 域。
3. numeric state tolerance 是显式的、字段族限定的，并且由 comparator 名称约束。
4. observation export 分清 exact envelope 规则与 payload 比较规则。
5. diagnostics trace 区分结构化 ancestry 与 diagnostics-only prose。
6. `reference`、`accelerated_exact`、`resident_state` 与 `approximate` 的指导可以直接执行，没有歧义。
7. 中文辅文已经足够对齐，可用于后续发布。

## 8. 验证命令

```bash
git diff --check
rg -n "budget_scope|mismatch_policy|diagnostics_requirements|comparison_domains|host_visible_maintained_state|tolerance_budget" docs/task/simulation_architecture/wp6_*.md
```
