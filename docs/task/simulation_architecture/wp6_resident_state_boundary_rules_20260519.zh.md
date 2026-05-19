# WP6-C1 Resident-State 边界规则

状态：`2026-05-19` resident-state ownership、sync policy、diagnostics
隔离与 capability projection 的 implementation-ready 边界规则。

语言版本：

- 英文主文：[wp6_resident_state_boundary_rules_20260519.md](wp6_resident_state_boundary_rules_20260519.md)
- 中文辅文：`wp6_resident_state_boundary_rules_20260519.zh.md`

输入：

- [WP6-A backend profile registry](wp6_backend_profile_registry_20260519.zh.md)
- [WP6-B parity budget registry](wp6_parity_budget_registry_20260519.zh.md)
- [WP6-C + WP6-D integration and index sync](wp6_integration_and_index_sync_20260519.zh.md)
- [WP2.5 scheduler semantics freeze](scheduler_semantics_wp25_20260519.zh.md)
- [WP5 validation harness](validation_harness_wp5_20260519.zh.md)

规范术语：

- `MUST` 表示任何维护中的 resident-state profile 都必须具备的元数据或行为。
- `MUST NOT` 表示 candidate、diagnostics-only 或 unsynced backend-local state 不能声明的能力。
- `SHOULD` 表示默认实现准备规则。
- `MAY` 表示允许的 diagnostics、compatibility 或未来 promotion 路径。

## 1. 目的

本文定义 WP6-C1 中 host-maintained truth、backend-resident operational state、
diagnostics export 与未来 resident-state capability projection 之间的边界。

本文刻意保持保守。当前 A/B registry 包含
`resident_state.unmaintained_candidate`，但没有验收维护中的 resident-state
profile。因此 `RuntimeCapabilities`、`BackendCapabilityFacade` 或任何后续
capability surface 都 MUST 保持 `supports_resident_state` 为 false，直到维护中的
profile revision 满足本文的 promotion gate。

## 2. Source Registry Consumption

WP6-C1 消费但不修改下列 WP6-A 与 WP6-B registry 记录：

| 来源 | 消费的记录 | WP6-C1 解释 |
|------|------------|-------------|
| WP6-A backend profile registry | `resident_state.unmaintained_candidate` | 一个占位 `resident_state` 行。它仍然是 unmaintained candidate，`sync_policy` 是 `undeclared_blocked`，不能投影为维护中的 resident-state support。 |
| WP6-B parity budget registry | `parity_budget.resident_state.unmaintained_candidate.v1` | candidate budget，不是 acceptance budget。它列出未来所需的 comparison domain 与 barrier，但不会让 backend-resident state 成为维护中真值。 |

Registry consumer MUST NOT 从任一记录的存在推断支持。当前这组记录唯一有效的投影是：

```yaml
backend_profile_id: resident_state.unmaintained_candidate
parity_budget_ref: parity_budget.resident_state.unmaintained_candidate.v1
maintained_status: unmaintained_candidate
supports_resident_state: false
diagnostics_result: report_only
```

## 3. Boundary Vocabulary

下面五个 sync-policy label 是 WP6-C1 resident-state boundary 唯一允许的
边界标签。未来维护中的 profile 只有在每个 state shard 都有单一权威 owner
且具备显式 barrier contract 时，才可以组合使用这些标签。

| 边界标签 | 定义 | 允许用途 | 禁止声明 | Promotion gate |
|----------|------|----------|----------|----------------|
| `host-owned` | Host state 是权威的维护中真值。Backend work 可以从 host input 派生，但 host committed snapshot、event order 与 structured diagnostics 保持 canonical。 | 维护中的 CPU exact baseline、compatibility fallback、backend helper input，以及按 host snapshot 检查真值的 reconstructed export。 | MUST NOT 把 backend-local cache、device memory、queue completion order 或 helper output 声明为维护中真值。MUST NOT 仅凭该标签把 `supports_resident_state` 设为 true。 | 识别 host-owned shard、host barrier、exported snapshot identity，以及验证 host truth source 的 parity budget。 |
| `backend-owned` | 某个具名 backend shard 在已验收的 sync 与 replay gate 后，成为具名维护中 state scope 的权威 owner。Host-visible truth 在声明的 barrier 上从该 backend-owned shard reconstruction、export 或 commit。 | 未来维护中的 resident-state profile，其中 backend 拥有特定 operational shard 并暴露 host-visible maintained result。 | MUST NOT 用于 `resident_state.unmaintained_candidate`。MUST NOT 用 generic acceleration 或 probe availability 隐藏 owner 变化。MUST NOT 让 unsynced backend-local state 影响 committed host state。 | 创建维护中的 registry revision，命名 `backend_state_owner`、`state_scope`、reconstruction 或 export 规则、sync barrier、parity budget、replay evidence 与 validation gate。 |
| `partial-sync` | Host 与 backend 分别拥有具名 shard，且只有声明过的字段会在声明的 cadence、trigger 与 barrier point 跨越边界。 | 周期性同步 host-visible state、observation packet 或 committed export 的 backend-resident working set。 | MUST NOT 让 cadence、trigger、barrier、conflict resolution 或 stale-read behavior 保持隐式。MUST NOT 把未同步字段当作维护中 parity evidence。 | 声明 per-shard ownership、sync cadence、sync trigger、barrier id、stale-state policy、reconstruction rule、mismatch policy 与 replay validation。 |
| `observation-only` | Backend-resident state 可以生成 host-visible observation，但它不拥有 observation envelope 与声明 provenance 之外的 committed world state。 | Sensor、visibility 或 perception output，其中维护面是 observation envelope 加 payload comparison domain。 | MUST NOT 修改 committed world state、scheduler state、engagement state 或 fallback control flow。MUST NOT 用 observation 成功来声明完整 resident-state ownership。 | 声明 observation field set、source snapshot version、visibility label、provenance、numeric comparison rule、export barrier，以及 against reference profile 的 replay evidence。 |
| `export-only` | Backend 或 helper output 以 report-only diagnostics 或 one-way export 跨到 host。它永远不是维护中 state owner。 | Diagnostics trace、helper metric、probe export、mismatch report 与 candidate evidence。 | MUST NOT 把 `supports_resident_state` 设为 true。MUST NOT 驱动 committed state、scheduler ordering、fallback decision 或维护中 parity acceptance。 | 输出保持 diagnostics-only 或 candidate evidence；promotion 需要重分类为 `backend-owned`、`partial-sync` 或 `observation-only`，并具备维护中的 budget 与 validation gate。 |

`undeclared_blocked` 不是维护中的边界标签。它表示该 profile 尚未声明足够的
ownership 或 sync semantics，不能作为维护中的 resident-state support 使用。

## 4. Maintained Profile Contract

未来维护中的 resident-state profile MUST 在任何 capability surface 把
`supports_resident_state` 设为 true 前声明以下所有字段：

1. `backend_profile_id`、`profile_class: resident_state` 与维护中的
   `comparison_reference`。
2. 作用域内每个 state shard 的 `host_state_owner` 与 `backend_state_owner`。
3. 从 `host-owned`、`backend-owned`、`partial-sync`、`observation-only` 或
   `export-only` 中选择的 `sync_policy`；混合使用时要按 shard 指派。
4. `state_scope`，包括 host-visible maintained state 与
   backend-resident operational state。
5. Sync cadence、trigger、barrier、stale-read behavior、conflict resolution
   与 failure quarantine behavior。
6. Host-visible reconstruction、commit 或 export rule；比较 snapshot 时必须包括
   `SnapshotVersion` normalization。
7. 维护中的 `parity_budget_ref`，不能是 candidate placeholder。
8. Structured diagnostics requirement，以及每个 unsynced backend-local field 的
   diagnostics-only label。
9. Validation gate，包含 replay evidence、mismatch policy，以及声明 state scope 的
   WP5 harness coverage。

如果任一字段缺失，即使已有 backend code、device memory、worker thread 或可探测部署事实，
该 profile 仍不可作为维护中的 resident-state support。

## 5. Completion Order And Unsynced State

Backend thread completion order MUST NOT 成为维护中真值。维护中的 event order
仍然是在已验收 barrier 上声明的 scheduler order，而不是 backend worker、GPU kernel、
async queue 或 helper thread 完成的物理顺序。

Unsynced backend-local state 是 diagnostics-only。这包括 backend-local cache、
device-resident working set、queue-local scratch state、speculative intermediate value、
helper metric，以及任何缺少已验收 host-visible reconstruction 或 export barrier 的 state。
这类 state MAY 作为 candidate evidence 或 diagnostics 导出，但 MUST NOT：

1. 定义 committed host state。
2. 定义维护中的 event order 或 snapshot identity。
3. 独立满足 parity budget。
4. 设置或暗示 `supports_resident_state`。
5. 驱动 fallback、promotion 或 acceptance decision，除非后续维护中的 profile 声明了该 control path。

## 6. Capability Projection Rules

Capability projection MUST 能由维护中的 registry metadata 加可探测部署事实解释。
可探测事实可以解释已声明 profile 的 availability，但不能创造 resident-state semantics。

Projection rules：

1. `resident_state.unmaintained_candidate` MUST 投影为
   `supports_resident_state: false`。
2. `parity_budget.resident_state.unmaintained_candidate.v1` MUST 保持 candidate
   budget，直到被维护中的 budget revision 替换。
3. `export-only` 与 diagnostics-only output MUST 投影为 report-only 或
   observability affordance，而不是维护中 state support。
4. `host-owned` profile MAY 是维护中的 baseline，但它不暗示 resident-state
   support，除非 backend-resident ownership 也被声明并验收。
5. `backend-owned`、`partial-sync` 或 `observation-only` profile 只有在
   maintained profile contract 与 promotion checklist 同时满足后，MAY 把
   `supports_resident_state` 设为 true。

当前必须采用的投影：

```yaml
RuntimeCapabilities:
  supports_resident_state: false
  resident_state_profile_id: null
  resident_state_reason: resident_state.unmaintained_candidate_is_not_maintained
  resident_state_diagnostics_allowed: true
```

## 7. Promotion Checklist

从 `resident_state.unmaintained_candidate` 提升为维护中的 resident-state profile，
需要 registry revision 完成以下全部项目：

1. 替换 candidate id，或将其修订为稳定的维护中 `backend_profile_id`。
2. 用已验收的边界标签与 per-shard ownership map 替换 `undeclared_blocked`。
3. 用维护中的 parity budget revision 替换
   `parity_budget.resident_state.unmaintained_candidate.v1`。
4. 证明声明 barrier 上的 event order，而不是 backend thread completion order。
5. 证明声明 barrier 上的 snapshot identity 或 host-visible reconstruction。
6. 将 unsynced backend-local state 标为 diagnostics-only，并保持在维护中 parity 之外。
7. 定义 mismatch policy、quarantine behavior，以及 rollback 或 fallback non-interference。
8. 为声明 scope 提供 WP5 replay 或 validation harness evidence。
9. 更新 capability projection policy，使 `supports_resident_state` 只对维护中的 profile
   为 true，且仅在 deployment probe 同时满足声明的 availability condition 时为 true。

在每一项通过 review 之前，该 candidate 仍是 unmaintained，且
`supports_resident_state` 仍为 false。

## 8. 非目标

- 编辑 WP6-A 或 WP6-B registry。
- 编辑 runtime code、binding、test、README 文件或 publication index。
- 提升 `resident_state.unmaintained_candidate`。
- 宣称 exact GPU、shadow-style 或 resident-state support。
- 把 backend thread completion order 当成 scheduler truth。
- 把 unsynced backend-local state 当成维护中的 parity evidence。

## 9. Validation Commands

```bash
git diff --check
rg -n "host-owned|backend-owned|partial-sync|observation-only|export-only|resident_state\\.unmaintained_candidate|parity_budget\\.resident_state\\.unmaintained_candidate\\.v1|supports_resident_state|backend thread completion order|unsynced backend-local state" docs/task/simulation_architecture/wp6_resident_state_boundary_rules_20260519*.md
rg -n "wp6_resident_state_boundary_rules_20260519\\.zh\\.md" docs/task/simulation_architecture/wp6_resident_state_boundary_rules_20260519.md
rg -n "wp6_resident_state_boundary_rules_20260519\\.md" docs/task/simulation_architecture/wp6_resident_state_boundary_rules_20260519.zh.md
```
