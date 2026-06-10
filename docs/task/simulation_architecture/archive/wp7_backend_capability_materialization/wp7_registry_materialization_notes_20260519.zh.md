# WP7-A Registry Materialization Implementation Notes

状态：`2026-05-19` WP7-A 第一波 implementation-ready notes。

语言版本：

- 英文主文：[wp7_registry_materialization_notes_20260519.md](wp7_registry_materialization_notes_20260519.md)
- 中文辅文：`wp7_registry_materialization_notes_20260519.zh.md`
- 父级 cluster：
  [wp7_registry_materialization_cluster_20260519.zh.md](wp7_registry_materialization_cluster_20260519.zh.md)

输入：

- [WP7 后端能力物化](backend_capability_materialization_wp7_20260519.zh.md)
- [WP6-A 后端配置文件注册表](wp6_backend_profile_registry_20260519.zh.md)
- [WP6-B parity budget 注册表](wp6_parity_budget_registry_20260519.zh.md)
- [WP6-C1 resident-state 边界规则](wp6_resident_state_boundary_rules_20260519.zh.md)
- [WP6 后端配置文件 policy 验收评审](../review/wp6_backend_profile_policy_acceptance_review_20260519.zh.md)

## 1. 第一波选择

WP7-A 应把 WP6 registries 物化为 hand-maintained YAML seed，并通过 schema
checks 验证。Markdown generation 应等 seed 与 schema 通过一轮 review 后再做。

理由：

1. WP6 已验收 surface 很小：五个 `backend_profile_id` rows 与五个
   `budget_id` rows。
2. WP6 文档混合了规范表格、prose 与 YAML 示例。markdown parser 会比较脆弱，
   还可能意外让格式选择变成权威。
3. WP7-B 与 WP7-C 现在需要具体字段词汇，尤其是 `maintained_status`、
   `projection_eligibility`、`validation_gate` 与 `acceptance_gate`。
4. seed 可以通过显式 `source_doc_provenance` 字段与 drift checks 继续从属于
   WP6 policy。

拒绝的替代方案：

| 替代方案 | 为什么不用于第一波 |
|----------|--------------------|
| Generated-from-markdown registry | table/YAML extraction contract 在 review 前过于脆弱。 |
| Docs-only with parser tests deferred | 会让 WP7-B projection 与 WP7-C promotion evidence 缺少稳定的 machine-facing shape。 |

## 2. Seed Shape 提案

未来 seed 应使用两个顶层数组：

```yaml
registry_version: 1
accepted_policy_date: 2026-05-19
source_authority:
  - docs/task/simulation_architecture/wp6_backend_profile_registry_20260519.md
  - docs/task/simulation_architecture/wp6_parity_budget_registry_20260519.md
  - docs/task/simulation_architecture/wp6_resident_state_boundary_rules_20260519.md
  - docs/task/review/wp6_backend_profile_policy_acceptance_review_20260519.md
profiles: []
parity_budgets: []
```

第一版 seed 文件建议路径：

```text
docs/task/simulation_architecture/generated/wp7_backend_registry_seed_20260519.yaml
```

本文不创建该 seed。本文先定义 shape，使后续实现可以在不改动 WP6 权威文档的
前提下新增 seed 与窄范围 architecture-doc test。

## 3. Profile Row Contract

每个 profile row 必须包含这些 WP6-A 字段：

1. `backend_profile_id`
2. `profile_class`
3. `comparison_reference`
4. `host_state_owner`
5. `backend_state_owner`
6. `sync_policy`
7. `state_scope`
8. `parity_budget_ref`
9. `observability_scope`
10. `compatibility_rule`
11. `deprecation_rule`
12. `validation_gate`

每个 profile row 还必须包含这些 WP7-A materialization 字段：

| 字段 | 第一波允许值 |
|------|--------------|
| `maintained_status` | `maintained_exact_baseline`、`diagnostics_only`、`unmaintained_candidate` |
| `projection_eligibility.maintained_cpu_exact_baseline` | 仅 `cpu_exact.reference` 为 `true` |
| `projection_eligibility.exact_gpu_supported` | 当前所有 WP6 rows 均为 `false` |
| `projection_eligibility.resident_state_supported` | 当前所有 WP6 rows 均为 `false` |
| `projection_eligibility.shadow_supported` | 当前所有 WP6 rows 均为 `false` |
| `projection_eligibility.diagnostics_allowed` | diagnostics-only/candidate evidence 保持 report-only 标签时为 `true` |
| `source_doc_provenance.path` | WP6 source doc 路径 |
| `source_doc_provenance.section` | source heading 或 table section |
| `source_doc_provenance.row_label` | profile id 或 row label |
| `source_doc_provenance.accepted_by` | `wp6_backend_profile_policy_acceptance_review_20260519.md` |

Maintained support 必须由显式 materialized 字段计算，不能由 helper
availability 或 `profile_class` 单独推断。

## 4. Parity Budget Row Contract

每个 parity budget row 必须包含这些 WP6-B 字段：

1. `budget_id`
2. `budget_version`
3. `backend_profile_id`
4. `profile_class`
5. `comparison_reference`
6. `budget_scope`
7. `comparison_domains`
8. `sync_barriers`
9. `diagnostics_requirements`
10. `mismatch_policy`
11. `acceptance_gate`
12. `change_reason`

每个 parity budget row 还必须包含：

| 字段 | 第一波允许值 |
|------|--------------|
| `maintained_status` | 规范化后镜像 `budget_scope.maintained_status`。 |
| `source_doc_provenance.path` | `docs/task/simulation_architecture/wp6_parity_budget_registry_20260519.md` |
| `source_doc_provenance.section` | budget subsection，例如 `4.1 cpu_exact.reference`。 |
| `source_doc_provenance.row_label` | `budget_id`。 |
| `source_doc_provenance.accepted_by` | `wp6_backend_profile_policy_acceptance_review_20260519.md` |

规范化后的 `maintained_status` 值：

| WP6 budget scope value | WP7-A normalized value |
|------------------------|------------------------|
| `maintained_exact_baseline` | `maintained_exact_baseline` |
| `diagnostics_only_not_truth` | `diagnostics_only` |
| `unmaintained_candidate` | `unmaintained_candidate` |

## 5. 初始 Row Mapping

seed 在后续 promotion review 新增或修订 record 前，必须只包含已验收的 WP6 rows。

| `backend_profile_id` | `budget_id` | `maintained_status` | `projection` |
|----------------------|-------------|---------------------|--------------|
| `cpu_exact.reference` | `parity_budget.cpu_exact.reference.v1` | `maintained_exact_baseline` | 仅 CPU exact reference baseline。 |
| `gpu_helpers.diagnostics_only` | `parity_budget.gpu_helpers.diagnostics_only.v1` | `diagnostics_only` | 仅 diagnostics/probe facts；无 maintained support。 |
| `gpu_exact.unmaintained_candidate` | `parity_budget.gpu_exact.unmaintained_candidate.v1` | `unmaintained_candidate` | 仅 candidate evidence；exact GPU support false。 |
| `resident_state.unmaintained_candidate` | `parity_budget.resident_state.unmaintained_candidate.v1` | `unmaintained_candidate` | 仅 candidate evidence；resident-state support false。 |
| `shadow_compare.unmaintained_candidate` | `parity_budget.shadow_compare.unmaintained_candidate.v1` | `unmaintained_candidate` | 仅 diagnostics reports；shadow support false。 |

WP7-B 计划中的 projection adapter 可以暴露 deployment facts，但不能把它们转成
maintained capability support。当前保守事实是：

```yaml
projection:
  maintained_cpu_exact_baseline: true
  exact_gpu_supported: false
  resident_state_supported: false
  shadow_supported: false
  gpu_helper_diagnostics_allowed: true
```

## 6. Drift Detection Plan

seed 与 tests 落地后，doc/schema test 应在以下条件失败：

1. 缺少 profile 字段：
   `backend_profile_id`、`profile_class`、`comparison_reference`、
   `host_state_owner`、`backend_state_owner`、`sync_policy`、`state_scope`、
   `parity_budget_ref`、`observability_scope`、`compatibility_rule`、
   `deprecation_rule`、`validation_gate`、`maintained_status`、
   `projection_eligibility` 或 `source_doc_provenance`。
2. 缺少 parity budget 字段：
   `budget_id`、`budget_version`、`backend_profile_id`、`profile_class`、
   `comparison_reference`、`budget_scope`、`comparison_domains`、
   `sync_barriers`、`diagnostics_requirements`、`mismatch_policy`、
   `acceptance_gate`、`change_reason`、`maintained_status` 或
   `source_doc_provenance`。
3. `parity_budget_ref` 无法匹配任何 `budget_id`。
4. 某个 `budget_id` 的 `backend_profile_id` 无法匹配 profile row。
5. budget/profile `profile_class` 不一致。
6. 除 `cpu_exact.reference` 外任何当前 WP6 row 将 maintained projection
   support 设为 true。
7. promotion claim 缺少更新后的 `validation_gate`、`acceptance_gate`、
   maintained budget status 与 source provenance。

如果新增第一版测试，应保持为窄范围 architecture-doc governance check，
覆盖 WP7 registry materialization。

```text
legacy proposed target name: wp7_registry_materialization_docs
```

它应只检查 documentation 或 seed。不得依赖 runtime GPU helper behavior、
runtime backend selection 或 capability promotion。

## 7. Handoff Notes For WP7-B/C

WP7-B 可以消费 materialized seed shape 来定义保守的 `RuntimeCapabilities`
projection contract。它必须把 `maintained_status` 与
`projection_eligibility` 作为 gate，然后只把可探测 deployment facts 组合为
diagnostics 或 availability explanation。

WP7-C 可以消费同一 seed shape 来要求 promotion evidence。Promotion 必须同时
更新 registry pair 的两侧：profile `validation_gate` 与 budget
`acceptance_gate`。如果任一侧仍是 candidate、diagnostics-only 或缺少 source
provenance，则 capability claim 不应被接受。

## 8. 验证命令

```bash
git diff --check
rg -n "backend_profile_id|parity_budget_ref|validation_gate|budget_id|acceptance_gate|projection|maintained_status" docs/task/simulation_architecture/wp7_registry_materialization*20260519*.md
```
