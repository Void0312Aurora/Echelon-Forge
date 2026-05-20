# WP11-E Integration And Acceptance Handoff

状态：`2026-05-20` planned WP11 dispatch sheet。

语言：

- 英文主文：[wp11_integration_acceptance_cluster_20260520.md](wp11_integration_acceptance_cluster_20260520.md)
- 中文辅文：`wp11_integration_acceptance_cluster_20260520.zh.md`

输入：

- [WP11 facade vertical slice and provenance](facade_vertical_slice_provenance_wp11_20260520.zh.md)
- [WP11-A ActionHoldPolicy contract](wp11_action_hold_policy_cluster_20260520.zh.md)
- [WP11-B information provenance labels](wp11_information_provenance_labels_cluster_20260520.zh.md)
- [WP11-C facade vertical slice proof](wp11_facade_vertical_slice_proof_cluster_20260520.zh.md)
- [WP11-D consumer boundary pre-gates](wp11_consumer_boundary_pregates_cluster_20260520.zh.md)
- [WP closure lane policy](../../../standards/governance/wp_closure_lane_policy.zh.md)

## 1. 目的

`WP11-E` 是 serial integration and acceptance-handoff stream。它在 implementation
streams 达到 `Mergeable` 后协调 shared glue，记录 residuals，并准备 acceptance evidence，
同时避免 README/archive/bilingual chores 变成主实现瓶颈。

## 2. 范围

范围内：

- 验证 A-D evidence 引用相同 WP10 node ids、barrier ids、provenance labels 与 consumer surfaces；
- 运行并记录 focused validation commands；
- 创建或准备 WP11 acceptance review；
- 运行 WP closure audit，并把 non-blocking closure chores 交给 closure lane；
- 列出 Law 14、Agency Graph、backend/fidelity 与 cadence work residuals。

范围外：

- A-D close 后继续实现新的 runtime semantics；
- 宣称 full Law 14 enforcement；
- 宣称 maintained multi-rate cadence；
- 让 optional archive 或 bilingual polish 阻塞 code/test mergeability。

## 3. Integration Checklist

| Check | Required result |
|-------|-----------------|
| Contract consistency | `ActionHoldPolicy` typed，且触碰 bindings 时 binding-visible。 |
| Provenance consistency | Maintained facade packets 与 beliefs 使用同一 label vocabulary。 |
| WP10 seam consistency | Vertical proof 引用 accepted WP10 node ids 与 barrier ids。 |
| Consumer boundary | Focused fixtures 中 maintained consumers 避免 unlabeled truth/raw-ECS inputs。 |
| Residual register | Full cadence、Law 14、Agency Graph、backend/fidelity 与 counterfactual work 保持 named later work。 |
| Closure lane | README/index/archive/bilingual chores 交给 closure lane，除非发现 broken links 或 contradictory status。 |

## 4. Acceptance Review Skeleton

最终 acceptance review 应包含：

- `WP11-A` 到 `WP11-E` 的 gate-by-gate verdicts；
- exact changed runtime/test/docs paths；
- exact validation commands and outcomes；
- blockers with exact command and next environment；
- residuals mapped to later phases；
- closure-lane checklist and owner。

## 5. Validation Commands

最小最终检查集：

```bash
git diff --check
cmake --build build-workshop -j4
CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/bindings tests/runtime/facade tests/runtime/engagement
CMO_BUILD_DIR=build-workshop pytest -q tests/architecture
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP11
```

Integrator 可按实际 touched files 缩小或扩大 test set，但 acceptance review 必须解释选择。
