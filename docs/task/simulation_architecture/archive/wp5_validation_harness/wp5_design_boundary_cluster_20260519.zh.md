# WP5-B 分发单：Design 与 Boundary Gate

状态：`2026-05-19` 第一波分发单。

语言版本：

- 英文主文：[wp5_design_boundary_cluster_20260519.md](wp5_design_boundary_cluster_20260519.md)
- 中文辅文：`wp5_design_boundary_cluster_20260519.zh.md`

输入：

- [WP5 验证套件](validation_harness_wp5_20260519.zh.md)
- [WP4 facade 对齐验收审查](../review/wp4_facade_alignment_acceptance_review_20260519.zh.md)
- [WP4-I compatibility guard 笔记](wp4_compat_guard_notes_20260519.zh.md)
- 当前 `tests/architecture/runtime_facade`
- 当前 `tests/runtime/facade/`

## 1. 目的

WP5-B 强化维护中 facade 路径的 design 与 boundary gate。它应防止 raw runtime access 变成维护中的 frontend dependency，同时保留 compatibility adapter 与 diagnostics path。

## 2. 必做工作

| 流 | 必要产出 | 写入范围 | 预算 |
|----|----------|----------|------|
| `WP5-B1 Facade Escape-Hatch Guard` | 扩展或记录 architecture checks，确保 `RuntimeFacade::runtime()` 只保留 compatibility-only，且不泄漏到维护中的 frontend class。 | `tests/architecture/`，可选 docs note。 | 中等。 |
| `WP5-B2 Maintained Surface Ownership Gate` | 添加或记录检查，确保维护中的 facade request/result type 保持 engine-encapsulated，不 include engine-owner headers。 | `tests/architecture/`。 | 中等。 |
| `WP5-B3 Smoke Candidate Note` | 建议哪些 design/boundary test 应进入 WP5 smoke loop。 | 文档笔记或交给 integration owner。 | 中等。 |
| `WP5-B4 False-Positive Review` | 除非 allowlist 能安全限定到 maintained path，否则继续推迟 direct `sim.*` 宽泛禁令。 | `tests/architecture/`、docs。 | 中高。 |

## 3. 非目标

- 不禁止 legacy Gym、scenario、oracle 或 diagnostics path 中所有 direct `sim.*` 使用。
- 不移除 compatibility adapter。
- 除非测试无法表达，否则不编辑 runtime/facade C++ signature。
- 除非 integration owner 要求，否则不直接改 smoke-suite membership。

## 4. 验收门槛

本任务簇满足以下条件时验收：

1. 既有 raw-runtime guard 覆盖被保留或加强。
2. Compatibility-only 与 diagnostics-only path 仍与 maintained facade path 明确分离。
3. 每个 deferred broad guard 都有明确理由与后续 enforcement route。
4. 聚焦测试本地通过。
