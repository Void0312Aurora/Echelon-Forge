# WP10-D Event And Snapshot Evidence

状态：`2026-05-20` planned WP10 dispatch sheet。

语言版本：

- 英文主文：[wp10_event_snapshot_evidence_cluster_20260520.md](wp10_event_snapshot_evidence_cluster_20260520.md)
- 中文辅文：`wp10_event_snapshot_evidence_cluster_20260520.zh.md`

输入：

- [WP10 causal runtime foundation](causal_runtime_foundation_wp10_20260520.zh.md)
- [WP10-A manifest registry](wp10_manifest_registry_cluster_20260520.zh.md)
- [WP10-B window loop and injection](wp10_window_loop_injection_cluster_20260520.zh.md)
- [WP10-C same-window validation](wp10_same_window_validation_cluster_20260520.zh.md)
- [WP5 validation harness](../wp5_validation_harness/validation_harness_wp5_20260519.zh.md)
- [WP9 contract and infrastructure closure](../wp9_contract_infrastructure_closure/contract_infrastructure_closure_wp9_20260520.zh.md)

## 1. 目的

`WP10-D` 证明 selected runtime seam 可通过 maintained evidence 被看见，而不只是内部代码结构。
facade-visible path 必须暴露或断言 deterministic event ordering、snapshot version、
barrier id、source time 与 diagnostics ancestry。

## 2. 范围

范围内：

- 把 events 绑定到 manifest node ids 或 maintained source ids；
- 按 `(timestamp, priority, event_id)` 保持 deterministic event ordering；
- 在 facade 已经返回 packets 的地方暴露或断言 `SnapshotVersion` / source shard ancestry；
- 保留 `barrier_id`、barrier sequence/detail 与 simulated source time；
- 让 diagnostics traces 绑定 event ancestry；
- 为 selected slice 添加 facade-visible 或 binding-visible tests。

范围外：

- replay engine rewrite；
- snapshot/restore implementation；
- counterfactual branching；
- broad DTO redesign；
- 把 diagnostics-only truth 当作 maintained policy 或 training truth。

## 3. Evidence Fields

selected slice 应保留下列字段组。

| Field group | 必需证据 |
|-------------|----------|
| Event identity | `event_id`, `event_family`, `timestamp`, `priority`, producing `node_id` 或 maintained `source_id`。 |
| Event ordering | 按 `(timestamp, priority, event_id)` 稳定排序，并使用 deterministic tie-breakers。 |
| Snapshot ancestry | `world_id`, `SnapshotVersion` 或 source shard versions，以及可用时的 `global_version`。 |
| Barrier ancestry | `barrier_id`, `barrier_sequence`, optional `barrier_detail`。 |
| Source time | Simulated `source_time_s`；wall-clock time 不得定义 ordering。 |
| Diagnostics ancestry | diagnostics trace id/ref，以及解释 exported packet 所需的 source request/event refs。 |
| Facade/binding visibility | Runtime facade 或 Python-visible packet/test 证明 metadata 能跨过 consumer boundary。 |

## 4. 验收测试

最低测试：

- repeated runs 为 selected fixture 产生相同 event ordering；
- facade-visible recent engagement events 或 observation exports 携带 source
  snapshot/barrier/source-time metadata；
- diagnostics trace 能命名 event ancestry；
- Python binding smoke 证明 metadata 可见，或记录 exact import/build blocker；
- tests 拒绝 insertion-order-only event ordering。

## 5. Handoff Contract

返回：

- added/asserted metadata fields；
- added/updated facade/binding tests；
- deterministic ordering fixture details；
- commands run and outcomes；
- Python binding blockers；
- Phase 2 provenance-label work 的 residuals。
