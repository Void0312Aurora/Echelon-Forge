# WP5-B Design 与 Boundary 笔记

状态：`2026-05-19` 聚焦 design/boundary gate 已完成。

语言版本：

- 英文主文：[wp5_design_boundary_notes_20260519.md](wp5_design_boundary_notes_20260519.md)
- 中文辅文：`wp5_design_boundary_notes_20260519.zh.md`

输入：

- [WP5-B design/boundary 任务簇](wp5_design_boundary_cluster_20260519.zh.md)
- [WP5 验证套件](validation_harness_wp5_20260519.zh.md)
- [WP4 facade 对齐验收审查](../review/wp4_facade_alignment_acceptance_review_20260519.zh.md)
- [WP4-I compatibility guard 笔记](wp4_compat_guard_notes_20260519.zh.md)
- `tests/architecture/runtime_facade/test_layering.py`

## 新增 Gate

`tests/architecture/runtime_facade/test_design_boundary_gates.py` 新增聚焦检查：

1. maintained facade request/result header 不 include `core/engine/*` 或
   `world_batch_runtime` owner header；
2. facade contract/type header 不命名 `WorldBatchRuntime` 或 `SimulationKernel`；
3. `runtime_facade.h` 中 `WorldBatchRuntime` 暴露仅限已文档化的 `runtime()`
   escape hatch 与 private owner pointer；
4. facade README 继续把 raw runtime access 记录为 compatibility/diagnostics-only；
5. architecture tests 在 allowlist 与 provenance label 成熟前，不编码宽泛 direct
   `sim.*` ban。

## Smoke 候选建议

推荐交给 WP5-E 评估的 smoke 候选：

```bash
python -m pytest -q tests/architecture/runtime_facade/test_layering.py tests/architecture/runtime_facade/test_design_boundary_gates.py
```

这些是低成本 static/design gate，应在更重的 runtime facade 或 engagement evidence
测试前运行。

WP5-B 不直接编辑 `tests/smoke/ci_smoke_suite.json`。Smoke membership 由串行
WP5-E integration owner 处理。

## Deferred Boundary 工作

现在不要添加仓库级 direct `sim.*` ban。当前 legacy Gym、scenario、oracle、
diagnostics 与 test path 有意把 direct simulation access 作为
`compatibility_adapter` 或 `diagnostics_only` 使用。安全 guard 需要窄 maintained-path
allowlist 与 observation provenance label。
