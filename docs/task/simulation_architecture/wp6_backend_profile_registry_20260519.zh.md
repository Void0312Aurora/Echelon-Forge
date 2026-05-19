# WP6-A 后端配置文件注册表

状态：`2026-05-19` 面向实现准备的 backend profile 元数据注册表种子。
本文件是文档注册表，不是生成式 runtime 代码。

语言版本：

- 英文主文：[wp6_backend_profile_registry_20260519.md](wp6_backend_profile_registry_20260519.md)
- 中文辅文：`wp6_backend_profile_registry_20260519.zh.md`

输入：

- [WP6 后端配置文件策略](backend_profile_policy_wp6_20260519.zh.md)
- [WP6-A 后端配置文件 taxonomy 分发单](wp6_backend_profile_taxonomy_cluster_20260519.zh.md)
- [WP6-B parity budget 分发单](wp6_parity_budget_cluster_20260519.zh.md)
- [WP6-C + WP6-D 集成与索引同步](wp6_integration_and_index_sync_20260519.zh.md)
- [WP2.5 调度语义冻结](scheduler_semantics_wp25_20260519.zh.md)
- [WP5 验证套件](validation_harness_wp5_20260519.zh.md)

规范术语：

- `MUST` 表示维护中的 backend profile 必须具备的元数据。
- `MUST NOT` 表示不能从本注册表种子推出的声明。
- `SHOULD` 表示默认的实现准备规则。
- `MAY` 表示允许的 diagnostics、兼容或未来提升路径。

## 1. 目的

本注册表把 WP6-A taxonomy 落成具体 profile 记录，供后续实现工作投影到
capability surface。它刻意保持保守：在这个种子里，只有
`cpu_exact.reference` 是维护中的 reference 记录。

`RuntimeCapabilities` 是 projection，不是 source of truth。它可以镜像已声明的
backend profile registry 元数据和可探测部署事实，但绝不能发明 exact GPU、
resident-state 或 shadow 风格支持。backend profile registry 是未来 capability
projection 的元数据来源之一；runtime probe 可以解释 availability，但不能把未声明的
profile 提升为维护中的真值。

## 2. 字段契约

每个维护中的 backend profile 条目 MUST 声明下列字段。candidate 与
diagnostics-only 行也使用同一组字段，这样缺失的 gate 会显式可见，而不是被
`RuntimeCapabilities` 或 helper code 推断出来。

| 字段 | 注册表规则 |
|------|------------|
| `backend_profile_id` | 供文档、审查、replay、diagnostics 与后续 capability projection 使用的稳定 id。 |
| `profile_class` | `reference`、`accelerated_exact`、`resident_state`、`approximate`、`diagnostics_only` 之一。 |
| `comparison_reference` | 语义比较锚点；只有在不宣称维护中比较时才使用 `not_maintained`。 |
| `host_state_owner` | 该 profile 声明范围内由 host 拥有的状态 shard 或输出。 |
| `backend_state_owner` | 该 profile 声明范围内由 backend 拥有的状态 shard 或输出。 |
| `sync_policy` | Host-owned、backend-owned、partial-sync、observation-only、export-only 或 `undeclared_blocked`。 |
| `state_scope` | profile 覆盖的状态族；candidate 必须说明哪些内容尚未维护。 |
| `parity_budget_ref` | profile-owned parity budget 引用，或阻止提升的缺失 budget。 |
| `observability_scope` | 可作为维护中输出或 diagnostics-only 证据导出的内容。 |
| `compatibility_rule` | legacy/helper 行为与 capability-projection 规则。 |
| `deprecation_rule` | 该行何时必须删除、收窄、重命名或经审查提升。 |
| `validation_gate` | 维护中使用前必须通过的审查或测试门。 |

## 3. 初始注册表

| `backend_profile_id` | `profile_class` | `comparison_reference` | `host_state_owner` | `backend_state_owner` | `sync_policy` | `state_scope` | `parity_budget_ref` | `observability_scope` | `compatibility_rule` | `deprecation_rule` | `validation_gate` |
|----------------------|-----------------|------------------------|--------------------|-----------------------|---------------|---------------|---------------------|-----------------------|----------------------|--------------------|-------------------|
| `cpu_exact.reference` | `reference` | `self` / 维护中的 CPU exact path | Host 拥有 committed scheduler state、world state、observation envelope 与 diagnostics ancestry。 | 维护中真值没有 backend owner。backend helper 不能在此 profile 下拥有 state。 | 仅 `host-owned`；没有 backend-owned truth。 | 通过 facade contract 暴露的维护中 CPU exact execution、event order、snapshot、observation 与 diagnostics ancestry。 | `parity_budget.cpu_exact.reference.v1`。 | 维护中的 facade 输出和结构化 diagnostics ancestry；diagnostics prose 仍是 diagnostics-only。 | 其他 profile 的默认 fallback 与 comparison anchor。`RuntimeCapabilities` 可以把它投影为维护中 baseline，但不能投影为 accelerated support。 | 只有在替代 reference profile 继续保持 WP2.5 event order、snapshot identity 与 WP5 validation 义务时才可废弃。 | WP6-A registry review 加 WP6-B reference budget acceptance；不暗示 GPU/resident/shadow 提升。 |
| `gpu_helpers.diagnostics_only` | `diagnostics_only` | 仅为解释引用 `cpu_exact.reference`；不宣称维护中 parity。 | Host 仍拥有全部维护中真值。 | GPU/helper-local diagnostics buffer 或 probe 只有在标为 diagnostics-only 时才允许。 | `export-only`；单向 diagnostics export。 | GPU availability check、helper trace、probe output 或 debug artifact，且不影响 committed state。 | `parity_budget.gpu_helpers.diagnostics_only.v1`；diagnostics-only，不是维护中 parity。 | Diagnostics trace、probe summary、build/runtime availability fact；绝不是维护中 state。 | `RuntimeCapabilities` 可以从声明的 probe 投影可探测部署事实，但除非另有维护中 profile 声明，exact GPU、resident-state 与 shadow support 必须保持 false。 | 如果 helper 开始影响 committed state，必须删除或收窄；只能通过另建含 ownership、sync、parity 与 validation gate 的维护中 profile 来提升。 | Diagnostics labeling review；测试可以断言 report-only 行为，但不能把它验收为维护中 parity。 |
| `gpu_exact.unmaintained_candidate` | `accelerated_exact` | 如果未来提升，则引用 `cpu_exact.reference`。 | 在维护中 profile 另行声明之前，假定 host 拥有 committed state。 | 未声明 backend-owned maintained state；GPU execution internals 不具权威性。 | `undeclared_blocked`；尚未声明 exact sync 与 committed-state visibility。 | 可能的 exact GPU world-step 或 accelerated exact path 占位；不宣称维护中的 exact GPU support。 | `parity_budget.gpu_exact.unmaintained_candidate.v1`；candidate budget，不是 acceptance。 | 仅可作为显式标记的 candidate diagnostics，例如 mismatch evidence 或 performance note。 | `RuntimeCapabilities` 绝不能从此行投影维护中的 exact GPU support。它只能通过 diagnostics 或 availability 字段暴露独立的可探测部署事实。 | 如果不再有 exact 提升计划则删除；只有在 WP6-B/C gate 通过后，才能替换为维护中的 `accelerated_exact` profile。 | 阻塞，直到 exact event order、snapshot identity、host/backend ownership、sync barrier、parity budget 与 WP5 replay/validation gate 均被接受。 |
| `resident_state.unmaintained_candidate` | `resident_state` | 如果未来提升，则引用 `cpu_exact.reference` 或另一个维护中的 host-visible reference。 | 在 profile 声明 host-visible reconstruction 或 export 规则前，host 仍拥有维护中的 committed state。 | Candidate backend-resident operational shard 不是维护中真值。 | `undeclared_blocked`；使用前必须声明 partial-sync、observation-only 或 export-only policy。 | backend-resident observation、physics 或 operational state 的占位；不宣称维护中的 resident-state support。 | `parity_budget.resident_state.unmaintained_candidate.v1`；candidate budget，不是 acceptance。 | 仅 candidate diagnostics；未同步的 backend-local state 必须留在维护中 parity 之外。 | `RuntimeCapabilities` 必须从此行保持 resident-state capability false。可探测 backend presence 不意味着 resident-state ownership。 | 如果 resident scope 无法按 WP6-C 规则重建、导出或同步，则删除或拆分；只能通过维护中 registry revision 提升。 | 阻塞，直到 ownership split、sync cadence/trigger、sync barrier、host-visible reconstruction/export、parity budget 与 validation gate 均被接受。 |
| `shadow_compare.unmaintained_candidate` | `diagnostics_only` | 仅用于 comparison report 引用 `cpu_exact.reference`；不维护 shadow execution support。 | Host reference path 拥有 committed state。 | Shadow helper output 是 diagnostics-only，不能拥有 committed state。 | `export-only`，除非后续维护中 profile 显式声明 non-mutating shadow contract。 | shadow comparison report 或离线 A/B evidence 占位；不宣称维护中的 shadow support。 | `parity_budget.shadow_compare.unmaintained_candidate.v1`；diagnostics/candidate budget，不是维护中真值。 | 标为 diagnostics-only 的 comparison report、mismatch summary 与 replay evidence。 | `RuntimeCapabilities` 绝不能从此行投影 shadow-style capability。Shadow output 不能影响 committed state 或 fallback control flow。 | 如果 report 不再使用则删除；只有在定义 what is shadowed、是否影响 committed state、以及 diagnostics 如何与维护中真值分离后才可提升。 | 阻塞，直到 shadow scope、non-interference rule、diagnostics separation、维护中使用时的 parity budget 与 validation review 均被接受。 |

## 4. Projection 规则

1. `RuntimeCapabilities` MUST 把本注册表作为已声明元数据消费，而不是作为推断目标。某一行只能按照它的
   `compatibility_rule`、`sync_policy` 与 `validation_gate` 投影。
2. 可探测部署事实可以与 registry metadata 结合，用来解释 availability，但不能覆盖
   `profile_class`、`parity_budget_ref` 或 `validation_gate`。
3. unmaintained candidate 行在 maintained exact GPU、resident-state 与 shadow-style capability 上必须投影为 unavailable 或 false。
4. diagnostics-only 行可以投影 observability 或 report-only affordance，但输出必须留在维护中 state 之外。
5. 未来任何维护中的 accelerated、resident、approximate 或 shadow-like profile，都必须先加入本注册表，capability surface 才能声明它。

## 5. 提升门

placeholder 提升为维护中 profile，需要一次 registry revision，并写明以下所有内容：

1. 稳定的 `backend_profile_id` 与 `profile_class`。
2. 维护中的 `comparison_reference`。
3. 明确的 `host_state_owner` 与 `backend_state_owner` 切分。
4. `sync_policy`，包括 cadence、trigger、barrier 或 export direction。
5. `state_scope` 与 `observability_scope`。
6. profile-owned `parity_budget_ref`。
7. `compatibility_rule`、`deprecation_rule` 与 `validation_gate`。

缺少这些字段时，即使代码、probe 或 helper 已存在，maintained support 的 capability projection 也仍保持 false。

## 6. 非目标

- 生成 runtime registry 文件。
- 修改 runtime code、binding、test、README 或 index 文件。
- 宣称维护中的 exact GPU execution。
- 宣称维护中的 resident-state ownership。
- 宣称维护中的 shadow execution 或 shadow fallback。
- 重开 WP6-B parity rules、WP6-C resident-state rules 或 WP6-D publication handoff。

## 7. 验证命令

```bash
git diff --check
rg -n "backend_profile_id|profile_class|comparison_reference|host_state_owner|backend_state_owner|sync_policy|state_scope|parity_budget_ref|observability_scope|compatibility_rule|deprecation_rule|validation_gate" docs/task/simulation_architecture/wp6_backend_profile_registry_20260519*.md
rg -n "cpu_exact\\.reference|gpu_helpers\\.diagnostics_only|gpu_exact\\.unmaintained_candidate|resident_state\\.unmaintained_candidate|shadow_compare\\.unmaintained_candidate|RuntimeCapabilities" docs/task/simulation_architecture/wp6_backend_profile_registry_20260519*.md
rg -n "wp6_backend_profile_registry_20260519\\.zh\\.md" docs/task/simulation_architecture/wp6_backend_profile_registry_20260519.md
rg -n "wp6_backend_profile_registry_20260519\\.md" docs/task/simulation_architecture/wp6_backend_profile_registry_20260519.zh.md
```
