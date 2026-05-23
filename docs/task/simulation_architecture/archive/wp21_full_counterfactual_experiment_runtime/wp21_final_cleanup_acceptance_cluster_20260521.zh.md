# WP21-F Final Cleanup And Acceptance Handoff

状态：`2026-05-21` planned；A-E 后串行 closure。

Language:

- English canonical:
  [wp21_final_cleanup_acceptance_cluster_20260521.md](wp21_final_cleanup_acceptance_cluster_20260521.md)
- Chinese companion: `wp21_final_cleanup_acceptance_cluster_20260521.zh.md`

## 目的

在 implementation streams 返回后关闭最终重构阶段。本 stream 不从规划创建 acceptance；
它验证代码证据，关闭或加闸 legacy residuals，并发布最终路线状态。

## 范围

范围内：

- 集成 A-E handoff packets；
- 运行 validation rollup 并记录 exact commands；
- 验证 legacy-only counterfactual/generation/loader mirror paths 已删除、加闸，
  或以 compatibility-only 保留且有测试；
- 更新 README/indexes 与 bilingual companions；
- 起草最终 acceptance review。

范围外：

- 除窄 integration fixes 外改变 implementation semantics；
- 在任一 A-E implementation gate blocked 时创建 acceptance；
- 隐藏 residuals 以制造 route complete 外观。

## 任务项

| ID | 项目 | 验收 |
|----|------|------|
| `F1` | Handoff integration | 汇总 A-E returned status、touched files、validation、residuals 与 closure impact。 |
| `F2` | Legacy cleanup review | Legacy-only paths 被删除、加闸，或以 compatibility-only 形式保留且有测试。 |
| `F3` | Validation rollup | 运行并记录 exact validation commands。 |
| `F4` | Publication closure | README/index sync、bilingual docs、acceptance review 与 audit output 完成。 |
| `F5` | Final route verdict | Acceptance review 不留下 unowned refactor-route residuals。 |

## 建议验证

```bash
git diff --check
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/test_wp15_*.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "counterfactual or worldline or experiment or setup"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/scenario -k "generation or counterfactual or scenario_loader"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/bindings/test_bindings_runtime_dto_surface.py -k "counterfactual or experiment"
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP21 --summary
```

## 交接

返回 final validation table、acceptance decision draft、remaining retained
compatibility notes、touched files，以及精确 commit/push readiness。
