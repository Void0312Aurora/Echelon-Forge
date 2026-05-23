# WP11-C Facade Vertical Slice Proof

状态：`2026-05-20` planned WP11 dispatch sheet。

语言：

- 英文主文：[wp11_facade_vertical_slice_proof_cluster_20260520.md](wp11_facade_vertical_slice_proof_cluster_20260520.md)
- 中文辅文：`wp11_facade_vertical_slice_proof_cluster_20260520.zh.md`

输入：

- [WP11 facade vertical slice and provenance](facade_vertical_slice_provenance_wp11_20260520.zh.md)
- [WP11-A ActionHoldPolicy contract](wp11_action_hold_policy_cluster_20260520.zh.md)
- [WP11-B information provenance labels](wp11_information_provenance_labels_cluster_20260520.zh.md)
- [WP10 acceptance review](../../review/wp10_causal_runtime_foundation_acceptance_review_20260520.zh.md)

## 1. 目的

`WP11-C` 在已验收 WP10 seam 上证明一条 maintained chain。该链必须从 runtime evidence
经 facade export 一直在 Python binding 或 maintained consumer smoke test 中可见。

## 2. 范围

范围内：

- 使用 WP10 node ids 与 barrier ids，不重新定义；
- 在一条 facade-visible chain 中证明 event/snapshot/barrier/provenance metadata；
- 把 `ActionHoldPolicy` 作为 contract-visible prerequisite 纳入，但不运行完整 cadence loop；
- 证明 selected chain 的 Python/binding visibility；
- 添加一个端到端或紧密耦合的 focused test。

范围外：

- broad facade API rewrite；
- full scheduler replacement；
- new backend/fidelity behavior；
- 用 hidden raw runtime access 作为 maintained proof path。

## 3. 必需链路

Proof 应跨层引用相同标识符：

```text
p7.fire_control_launch.v1 / p9.effects_damage.v1 / p10.observation_export.v1
  -> input_injection / window_commit / export barrier evidence
  -> LaunchEvent / EffectsEvent / DamageReport / DiagnosticsTrace ancestry
  -> ObservationBatchPacket or EngagementEventPacket provenance
  -> Python binding or maintained consumer smoke
```

## 4. 验收测试

最小测试：

- end-to-end proof 引用 WP10 node ids 与 export barrier ids；
- facade export 携带 event/snapshot/barrier/source-time/provenance metadata；
- Python-facing object 暴露相同 evidence fields；
- test 不依赖 undocumented insertion order 或 wall-clock time；
- 任何 raw runtime setup path 都必须 diagnostics-only 且显式 allowlisted。

## 5. Handoff Contract

返回：

- vertical-slice test paths 与 runtime/facade files touched；
- across chain 被证明的 exact identifiers；
- commands run and outcomes；
- raw runtime escape hatches added or changed，如果有；
- 给 `WP11-D/E` 的 integration notes。
