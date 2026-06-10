# WP7-A Registry Materialization

状态：`2026-05-19` WP7 第一波 implementation-ready 准备。

语言版本：

- 英文主文：[wp7_registry_materialization_cluster_20260519.md](wp7_registry_materialization_cluster_20260519.md)
- 中文辅文：`wp7_registry_materialization_cluster_20260519.zh.md`
- 实现说明：
  [wp7_registry_materialization_notes_20260519.zh.md](wp7_registry_materialization_notes_20260519.zh.md)

输入：

- [WP7 后端能力物化](backend_capability_materialization_wp7_20260519.zh.md)
- [WP6-A 后端配置文件注册表](wp6_backend_profile_registry_20260519.zh.md)
- [WP6-B parity budget 注册表](wp6_parity_budget_registry_20260519.zh.md)
- [WP6-C1 resident-state 边界规则](wp6_resident_state_boundary_rules_20260519.zh.md)
- [WP6 后端配置文件 policy 验收评审](../review/wp6_backend_profile_policy_acceptance_review_20260519.zh.md)

命名说明：

- 本文属于新的 post-WP6 `WP7-A` registry materialization 活线。
- 不要复活旧评审里 `WP7` 等同于 backend profile policy 的历史别名；该
  policy 已作为 `WP6` 验收并关闭。

## 1. 目的

WP7-A 把 WP6 已验收的文档注册表转化为 implementation-ready 的物化计划。
该计划需要足够可机器检查，以支撑后续 `RuntimeCapabilities` projection 与
promotion evidence 工作，但不能让生成数据反过来高于已验收的 WP6 policy
文档。

产物应让后续 runtime code 与 test 能回答这个窄问题：

```text
哪些 backend profile 与 parity budget 已声明、处于维护中、仍是候选项，
或者只是 diagnostics-only；它们分别允许投影哪些 capability claim？
```

## 2. 第一波物化决策

第一版 materialized registry 应采用 hand-maintained seed，并配套 schema
validation；从 WP6 markdown 自动生成应等字段形态稳定后再做。

决策：

| 选项 | WP7-A 决策 | 理由 |
|------|------------|------|
| Hand-maintained seed | 第一波采用。 | WP6 只有五个 profile row 和五个 budget row，人工审阅 seed 成本低，也避免脆弱的 markdown 表格解析。 |
| Generated-from-markdown | 推迟到第二波。 | WP6 markdown 同时包含规范 prose、表格和 YAML 示例；立即生成会让 parser 细节看起来像权威来源。 |
| Docs-only with parser tests deferred | 不作为主计划。 | WP7-B/C 需要稳定字段名、`maintained_status` 与 projection eligibility；docs-only 会留下太多隐含语义。 |

seed 路径在实现前只是提案：

```text
docs/task/simulation_architecture/generated/wp7_backend_registry_seed_20260519.yaml
```

seed 创建后仍只是 WP6 policy 的物化镜像。权威来源仍是 WP6-A profile
registry、WP6-B parity budget registry、WP6-C1 resident-state boundary
rules 以及 WP6 acceptance review。

## 3. 必需工作项

| 流 | 必需产出 | 写入范围 | 预算 |
|----|----------|----------|------|
| `WP7-A1 Registry Schema Shape` | 定义 profile row、parity budget row、`maintained_status`、projection eligibility、drift 字段与 source-doc provenance。 | 本 cluster 与 implementation notes；仅提出 seed 文件路径。 | 高。 |
| `WP7-A2 Seed Strategy` | 第一波使用 hand-maintained YAML seed；schema 与 review checks 稳定后再做 markdown extraction。 | 文档、seed 路径提案、后续测试计划。 | 高。 |
| `WP7-A3 Conservative Projection Matrix` | 把每个当前 WP6 row 映射为维护中 baseline、diagnostics-only fact、candidate evidence 或 false support。 | 文档与未来 fixture 计划。 | 高。 |
| `WP7-A4 Drift Detection Gate` | 定义捕获字段缺失、stale `parity_budget_ref`、stale `budget_id`、状态漂移与意外晋级的检查。 | 当前为 doc-check 提案；seed 落地后再加 architecture test。 | 中高。 |

## 4. Profile Schema

materialized seed 中每个 profile row 必须保留 WP6-A 字段契约，并增加
provenance、lifecycle 与 projection 字段。

| 字段 | 必需值形态 | 用途 |
|------|------------|------|
| `backend_profile_id` | WP6-A 稳定字符串 id。 | profile row、diagnostics、review 与 projection 的主键。 |
| `profile_class` | `reference`、`accelerated_exact`、`resident_state`、`approximate` 或 `diagnostics_only`。 | 声明的类别，不从代码可用性推断。 |
| `comparison_reference` | profile id 或 `self`/`not_maintained`。 | 语义比较锚点。 |
| `host_state_owner` | 文本或结构化 owner 列表。 | host-owned maintained truth。 |
| `backend_state_owner` | 文本或结构化 owner 列表。 | backend-owned maintained 或 candidate state。 |
| `sync_policy` | `host-owned`、`backend-owned`、`partial-sync`、`observation-only`、`export-only` 或 `undeclared_blocked`。 | 所有权与同步边界。 |
| `state_scope` | 保留 WP6-A scope 的列表或文本。 | 覆盖或明确排除的 state family。 |
| `parity_budget_ref` | 已存在的 WP6-B `budget_id`。 | 指向 parity budget row 的交叉引用。 |
| `observability_scope` | maintained 或 diagnostics-only output surface。 | 定义可导出的内容。 |
| `compatibility_rule` | 保留 WP6-A rule 的文本。 | Projection 与 fallback guard。 |
| `deprecation_rule` | 保留 WP6-A rule 的文本。 | 删除、拆分或晋级 guard。 |
| `validation_gate` | 保留 WP6-A gate 的文本。 | 维护中使用前的 review/test gate。 |
| `maintained_status` | `maintained_exact_baseline`、`diagnostics_only` 或 `unmaintained_candidate`。 | projection 使用的显式 lifecycle state。 |
| `projection_eligibility` | 针对 maintained 与 diagnostics claim 的结构化布尔值。 | 防止 helper/probe 存在导致意外 support。 |
| `source_doc_provenance` | source doc 路径、section/heading、row label、accepted date。 | 支撑 drift detection 与 review traceability。 |

Profile row 不能只根据 `profile_class` 推导 `maintained_status`。例如
`gpu_exact.unmaintained_candidate` 虽然有 `profile_class: accelerated_exact`，
仍必须映射为 `maintained_status: unmaintained_candidate`。

## 5. Parity Budget Schema

materialized seed 中每个 parity budget row 必须保留 WP6-B 字段契约，并增加
provenance、lifecycle 与反向链接字段。

| 字段 | 必需值形态 | 用途 |
|------|------------|------|
| `budget_id` | WP6-B 稳定字符串 id。 | parity budget row 主键。 |
| `budget_version` | 整数。 | drift detection 使用的 revision tracking。 |
| `backend_profile_id` | 已存在的 profile id。 | owner profile；必须匹配一个 profile row。 |
| `profile_class` | 与 owner profile row 相同的 enum。 | 对 profile drift 的冗余检查。 |
| `comparison_reference` | profile id 或 `self`。 | 语义比较锚点。 |
| `budget_scope` | 包含 `maintained_status` 与 diagnostics-only surface 的结构化 scope。 | 声明 maintained 与 diagnostics 覆盖范围。 |
| `comparison_domains` | event order、snapshot versions、numeric state、observation export、diagnostics trace。 | 各 domain 的 exactness 与 tolerance policy。 |
| `sync_barriers` | barrier id 列表。 | replay 与 comparison 锚点。 |
| `diagnostics_requirements` | required structured diagnostics fields 列表。 | 解释 mismatch evidence。 |
| `mismatch_policy` | 结构化 result action。 | failure、quarantine、candidate 或 report-only 行为。 |
| `acceptance_gate` | 保留 WP6-B gate 的文本。 | 维护中使用前的 review/test gate。 |
| `change_reason` | 短文本。 | 解释 budget revision。 |
| `maintained_status` | 镜像 budget scope lifecycle 值。 | 显式 lifecycle 值，供检查使用。 |
| `source_doc_provenance` | source doc 路径、section/heading、code-block label、accepted date。 | 支撑 drift detection 与 review traceability。 |

Budget row 不能因为存在就被视为 maintained。只有 `maintained_status`、
`acceptance_gate` 与 owning profile row 都允许 maintained projection 时，
budget 才能参与 maintained claim。

## 6. Conservative Projection Matrix

第一版 materialized registry 必须按下表精确保守投影当前 WP6 rows：

| `backend_profile_id` | `parity_budget_ref` / `budget_id` | `maintained_status` | Maintained projection | Diagnostics projection | Blocked claims |
|----------------------|-----------------------------------|---------------------|-----------------------|------------------------|----------------|
| `cpu_exact.reference` | `parity_budget.cpu_exact.reference.v1` | `maintained_exact_baseline` | `projection.cpu_exact_baseline: true`；CPU exact reference 可作为维护中比较锚点。 | reference budget 覆盖的 structured diagnostics ancestry 可为 maintained；diagnostics prose 仍为 diagnostics-only。 | 不暗示 accelerated、resident-state、device-observation 或 shadow support。 |
| `gpu_helpers.diagnostics_only` | `parity_budget.gpu_helpers.diagnostics_only.v1` | `diagnostics_only` | 无维护中 runtime support。 | helper availability、helper traces、probe exports 与 build/runtime facts 可作为 diagnostics-only 报告。 | `projection.exact_gpu_supported`、`projection.resident_state_supported` 与 `projection.shadow_supported` 必须保持 false。 |
| `gpu_exact.unmaintained_candidate` | `parity_budget.gpu_exact.unmaintained_candidate.v1` | `unmaintained_candidate` | 无维护中 exact GPU support。 | Candidate mismatch/performance evidence 在明确标注时可保留为 diagnostics-only。 | Exact GPU support、maintained acceleration 与 exact parity acceptance 均保持 false。 |
| `resident_state.unmaintained_candidate` | `parity_budget.resident_state.unmaintained_candidate.v1` | `unmaintained_candidate` | 无维护中 resident-state support。 | Candidate ownership/sync evidence 与 unsynced backend-local state 可作为 report-only diagnostics。 | `projection.resident_state_supported` 与 backend-owned truth 保持 false。 |
| `shadow_compare.unmaintained_candidate` | `parity_budget.shadow_compare.unmaintained_candidate.v1` | `unmaintained_candidate` | 无维护中 shadow execution 或 shadow fallback support。 | Shadow reports、mismatch summaries 与 replay evidence 可作为 diagnostics-only。 | Shadow output 不能影响 committed state、fallback control flow 或 maintained support。 |

Projection rule：后续 adapter 可以把 materialized registry metadata 与可探测
deployment facts 组合，但 probes 只能解释已声明 maintained profile 的可用性。
probe availability 不能改变 `maintained_status`，不能满足 `validation_gate` 或
`acceptance_gate`，也不能晋级 candidate。

## 7. Drift Detection 策略

WP7-A 应分两阶段引入 drift checks。

Phase 1，seed 尚未存在前：

1. 保持本 cluster 与 implementation notes 对齐 WP6 字段名：
   `backend_profile_id`、`parity_budget_ref`、`validation_gate`、`budget_id`、
   `acceptance_gate`、`projection` 与 `maintained_status`。
2. 验证中英文 WP7-A 文档互链，并保留相同的主要章节顺序。
3. 本阶段不新增 runtime capability promotion tests。

Phase 2，hand-maintained seed 落地后：

1. 如果任何 profile row 缺少 WP6-A 字段、`maintained_status`、
   `projection_eligibility` 或 `source_doc_provenance`，schema validation 必须失败。
2. 如果任何 budget row 缺少 WP6-B 字段、`maintained_status` 或
   `source_doc_provenance`，schema validation 必须失败。
3. 如果 `parity_budget_ref` 没有匹配的 `budget_id`，budget
   `backend_profile_id` 没有 profile row，或 profile/budget `profile_class`
   不一致，cross-reference validation 必须失败。
4. 如果除 `cpu_exact.reference` 外任何 row 投影维护中 exact baseline support，
   conservative projection validation 必须失败。
5. 如果 GPU exact、resident-state 或 shadow support 在没有 maintained profile
   row、maintained budget、已接受 `validation_gate`、已接受 `acceptance_gate`
   和更新后的 source provenance 时变为 true，promotion validation 必须失败。

如果后续新增测试，应保持在 WP7 registry materialization 的窄范围
architecture-doc target。它只应检查 schema 与文档约束；不得依赖 runtime
capability promotion。

## 8. 非目标

- 不晋级任何 candidate profile。
- 不实现 runtime backend selection。
- 不让生成 registry 文件覆盖 WP6 policy。
- 不解析所有历史草稿；范围只包括已验收的 WP6 线。
- 本任务簇不新增公开 capability flag。
- 不编辑 WP7-B/C/D/E 文件、runtime C++、GPU helpers、README/index 文件或已验收
  WP6 文档。

## 9. 验收门槛

本任务簇在以下条件满足后可交给 WP7-B/C：

1. 每个 WP6 profile row 都有 materialization strategy。
2. 每个 WP6 parity budget row 都有 materialization strategy。
3. 第一波决策明确：先 hand-maintained seed，推迟 markdown generation。
4. `cpu_exact.reference` 是第一版 materialized shape 里唯一维护中的 exact baseline。
5. GPU helper、exact GPU candidate、resident-state candidate 与 shadow candidate
   row 都投影为 diagnostics-only 或 false maintained support。
6. drift detection 足够具体，能捕获字段缺失、stale `parity_budget_ref`、
   stale `budget_id` 或意外 capability promotion。
7. 英文与中文 WP7-A 文档相互链接，并保持结构对齐。

## 10. 验证命令

```bash
git diff --check
rg -n "backend_profile_id|parity_budget_ref|validation_gate|budget_id|acceptance_gate|projection|maintained_status" docs/task/simulation_architecture/wp7_registry_materialization*20260519*.md
```
