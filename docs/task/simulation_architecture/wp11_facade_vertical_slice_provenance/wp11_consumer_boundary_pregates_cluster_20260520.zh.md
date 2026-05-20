# WP11-D Consumer Boundary Pre-Gates

状态：`2026-05-20` planned WP11 dispatch sheet。

语言：

- 英文主文：[wp11_consumer_boundary_pregates_cluster_20260520.md](wp11_consumer_boundary_pregates_cluster_20260520.md)
- 中文辅文：`wp11_consumer_boundary_pregates_cluster_20260520.zh.md`

输入：

- [WP11 facade vertical slice and provenance](facade_vertical_slice_provenance_wp11_20260520.zh.md)
- [WP11-B information provenance labels](wp11_information_provenance_labels_cluster_20260520.zh.md)
- [Post-WP9 gap analysis](../../review/post_wp9_gap_analysis_20260520.zh.md)

## 1. 目的

`WP11-D` 为 maintained consumers 添加 pre-enforcement gates。它不宣称完整
Architecture Law 14 enforcement；它只把边界做得足够可测试，以供后续
information/agency enforcement 阶段使用。

## 2. 范围

范围内：

- 添加 static 或 runtime guard tests，区分 maintained consumer paths 与 diagnostics-only
  truth/raw-ECS paths；
- 要求 maintained fixtures 消费 provenance-labeled `ObservationPacket` /
  `DecisionBelief` 风格 inputs；
- 保持 diagnostics-only raw runtime paths 显式且 allowlisted；
- 记录 full Law 14 与 Agency Graph enforcement 的 residuals。

范围外：

- 阻断仓库内所有 raw ECS reads；
- enforcing role authority scopes；
- 通过 Agency Graph dispatch decision models；
- 超出 focused fixtures 地重写 training 或 experiment code。

## 3. Gate Rules

| Boundary | WP11-D behavior |
|----------|-----------------|
| Maintained consumer | 必须在 focused slice 中使用 provenance-labeled packet 或 belief inputs。 |
| Diagnostics fixture | 可使用 truth/raw runtime setup，但必须有 explicit diagnostics-only label 或 allowlist。 |
| Compatibility adapter | 可保留，但必须 labeled compatibility-only，且不得作为 maintained decision evidence。 |
| Unknown source | 在 focused guard tests 中 fail closed。 |

## 4. 验收测试

最小测试：

- architecture guard 拒绝 unlabeled maintained consumer fixtures；
- diagnostics-only truth/raw-ECS setup 保持显式；
- maintained consumer smoke 读取 provenance-labeled packet 或 belief input；
- tests 不宣称 complete Law 14 enforcement；
- residuals 标明下一 enforcement WP。

## 5. Handoff Contract

返回：

- guard files 与 allowlists touched；
- maintained 与 diagnostics-only fixture paths；
- tests added or updated；
- commands run and outcomes；
- full Law 14 / Agency Graph enforcement residuals；
- 给 `WP11-E` 的 integration notes。
