# WP10-E Integration And Acceptance Handoff

状态：`2026-05-20` planned WP10 dispatch sheet。

语言版本：

- 英文主文：[wp10_integration_acceptance_cluster_20260520.md](wp10_integration_acceptance_cluster_20260520.md)
- 中文辅文：`wp10_integration_acceptance_cluster_20260520.zh.md`

输入：

- [WP10 causal runtime foundation](causal_runtime_foundation_wp10_20260520.zh.md)
- [WP10-A manifest registry](wp10_manifest_registry_cluster_20260520.zh.md)
- [WP10-B window loop and injection](wp10_window_loop_injection_cluster_20260520.zh.md)
- [WP10-C same-window validation](wp10_same_window_validation_cluster_20260520.zh.md)
- [WP10-D event and snapshot evidence](wp10_event_snapshot_evidence_cluster_20260520.zh.md)
- [WP closure lane policy](../../../standards/governance/wp_closure_lane_policy.zh.md)

## 1. 目的

`WP10-E` 是串行 integration 与 acceptance-handoff stream。它在 implementation streams
达到 `Mergeable` 后协调 shared glue、记录 residuals，并准备 acceptance evidence，同时避免
README/archive/bilingual chores 成为主实现瓶颈。

## 2. 范围

范围内：

- 集成 A-D 触碰的 shared files；
- 验证 A-D evidence 引用同一组 node ids、barrier ids、event ids 与 snapshot metadata；
- 运行并记录 focused validation commands；
- 创建或准备 WP10 acceptance review；
- 运行 WP closure audit，并 hand off non-blocking closure chores；
- 列出 Phase 2 及后续阶段 residuals。

范围外：

- 在 A-D 收口后实现新 runtime semantics；
- 重新开启 Phase 2 `ActionHoldPolicy` 或 provenance-label work；
- acceptance review 存在前声明 accepted status；
- 让 optional archive 或 bilingual polish 阻塞 code/test mergeability。

## 3. Integration Checklist

| Check | 必需结果 |
|-------|----------|
| Registry consistency | 所有 runtime evidence 引用 `WP10-A` 的 node ids。 |
| Barrier consistency | Loop、tests 与 facade evidence 使用同一 barrier vocabulary。 |
| Edge validation | Same-window validation 在 selected schedule 执行前运行。 |
| Event evidence | Event order 不依赖 insertion order 或 wall-clock time。 |
| Facade/binding proof | 至少一条 consumer-visible path 证明 metadata visibility，或明确 blocked。 |
| Residual register | Strict clock-domain enforcement、`ActionHoldPolicy`、provenance labels、Law 14 与 Agency Graph runtime 保持命名为 later work。 |
| Closure lane | README/index/archive/bilingual chores 交给 closure lane，除非暴露 broken links 或 contradictory status。 |

## 4. Acceptance Review Skeleton

最终 acceptance review 应包含：

- `WP10-A` 到 `WP10-E` 的 gate-by-gate verdicts；
- exact changed runtime/test/docs paths；
- exact validation commands and outcomes；
- blockers，包含 exact command 与 next environment；
- residuals 映射到 Phase 2 或 later phases；
- closure-lane checklist 与 owner。

## 5. 验证命令

最低 final check set：

```bash
git diff --check
pytest -q tests/architecture/runtime_facade/test_layering.py tests/architecture/governance/test_infrastructure_closure_docs.py
pytest -q tests/runtime/engagement tests/runtime/facade tests/runtime/bindings
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP10
```

integrator 可根据实际 touched files 缩小或扩大 test set，但 acceptance review 必须解释选择。

## 6. Handoff Contract

返回：

- final integrated file list；
- validation commands and outcomes；
- acceptance review path if created；
- unresolved blockers；
- Phase 2 与 later phases residuals；
- 不应阻塞 implementation mergeability 的 closure-lane warnings。
