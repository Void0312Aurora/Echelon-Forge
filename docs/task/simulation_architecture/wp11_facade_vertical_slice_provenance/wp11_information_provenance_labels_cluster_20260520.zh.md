# WP11-B Information Provenance Labels

状态：`2026-05-20` planned WP11 dispatch sheet。

语言：

- 英文主文：[wp11_information_provenance_labels_cluster_20260520.md](wp11_information_provenance_labels_cluster_20260520.md)
- 中文辅文：`wp11_information_provenance_labels_cluster_20260520.zh.md`

输入：

- [WP11 facade vertical slice and provenance](facade_vertical_slice_provenance_wp11_20260520.zh.md)
- [WP10 causal runtime foundation](../wp10_causal_runtime_foundation/causal_runtime_foundation_wp10_20260520.zh.md)
- [Post-WP9 gap analysis](../../review/post_wp9_gap_analysis_20260520.zh.md)

## 1. 目的

`WP11-B` 给 maintained facade-visible packets 与 beliefs 添加稳定 information-state
provenance labels。这些 labels 会成为后续 Law 14 与 Agency Graph enforcement 消费的词汇。

## 2. 范围

范围内：

- 定义或复用一个 canonical provenance DTO/vocabulary；
- 在适用处标注 maintained `ObservationBatchPacket`、engagement/facade export metadata 与
  `DecisionBelief` surfaces；
- 区分 `WorldTruth`、`SensedState`、`TrackState`、`SharedTacticalPicture`、
  `AgentObservation` 与 `DecisionBelief`；
- 保留 `maintained`、`diagnostics_only`、`compatibility_adapter` status labels；
- 添加 Python/binding-visible tests，证明 provenance survive。

范围外：

- 完整 Law 14 enforcement；
- 每个 observation view 的 field masking；
- Agency Graph authority checks；
- broad data-link 或 shared tactical picture runtime implementation。

## 3. Provenance Rules

Maintained facade exports 不得无标签。

| Label | Maintained use |
|-------|----------------|
| `WorldTruth` | Diagnostics-only，除非后续 accepted gate 声明 transformation。 |
| `SensedState` | 通过 declared sensor/facade metadata 采样时可 maintained。 |
| `TrackState` | track ids、source snapshot/version 与 confidence metadata 存在时可 maintained。 |
| `SharedTacticalPicture` | 保留，除非 link/roster constraints 已实现或显式 compatibility-only。 |
| `AgentObservation` | Maintained facade-facing observation input。 |
| `DecisionBelief` | 只有从 declared observation、memory、estimator 或 decision-model inputs 推导时可 maintained。 |

## 4. 验收测试

最小测试：

- maintained facade observation packets 携带非空 provenance label；
- maintained diagnostics/engagement traces 在相关处保留 source snapshot 与 information-state label；
- maintained `DecisionBelief` 不能悄悄声明 truth/raw-ECS ancestry；
- binding tests 证明 labels survive Python-facing DTOs；
- diagnostics-only truth paths 只有在显式标注时仍可允许。

## 5. Handoff Contract

返回：

- provenance vocabulary 与 DTO/helper paths；
- packet 或 belief fields added/updated；
- tests added or updated；
- commands run and outcomes；
- reserved 但尚未 runtime-populated 的 labels；
- 给 `WP11-C/D/E` 的 integration notes。
