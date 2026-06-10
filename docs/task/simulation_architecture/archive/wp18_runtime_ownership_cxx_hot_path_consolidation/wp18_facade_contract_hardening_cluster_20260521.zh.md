# WP18-D Facade Contract Hardening

状态：`2026-05-21` complete / accepted。

语言版本：

- 英文主文：[wp18_facade_contract_hardening_cluster_20260521.md](wp18_facade_contract_hardening_cluster_20260521.md)
- 中文辅文：`wp18_facade_contract_hardening_cluster_20260521.zh.md`

输入：

- [WP18 主计划](runtime_ownership_cxx_hot_path_consolidation_wp18_20260521.zh.md)
- [WP18-A ownership fact ledger](wp18_ownership_fact_ledger_hot_path_map_cluster_20260521.zh.md)
- [WP17 验收审查](../../review/wp17_stage3_runtime_materialization_cleanup_acceptance_review_20260521.zh.md)

## 目标

在 WP17 后强化 facade-shaped frontend contract，防止 maintained callers 回退到 raw
runtime/world handles，同时保留并显式约束 compatibility surfaces。

## 范围

范围内：

- maintained raw runtime/world-handle reads 的 architecture guards；
- selected execution ownership seams 的 facade/adapter method shape checks；
- 带显式理由的 compatibility allowlist updates；
- 证明 `batch_runtime` 与 `RuntimeFacade.runtime()` 仍是 compatibility-only 的回归测试。

范围外：

- public API deletion；
- broad facade redesign；
- CUDA/resident-state 或 `spawn_platform` 工作。

## 任务项

| ID | 项目 | 验收 |
|----|------|------|
| `D1` | Maintained path guard | 新增 maintained raw runtime/world reads 若未作为 compatibility allowlist，会触发 architecture tests。 |
| `D2` | Facade shape check | WP18-B/C/E 选定替代表面有稳定 method/DTO expectations。 |
| `D3` | Compatibility retention | Compatibility surfaces 仍可通过命名测试调用，且不会被静默晋级。 |
| `D4` | Residual routing | 任意 guard exception 都路由到 WP18 residuals 或后续 WP19/WP21 prerequisites。 |

## 建议验证

```bash
git diff --check
python -m pytest -q tests/architecture/runtime_facade
python -m pytest -q tests/architecture/runtime_spine/test_runtime_spine_inventory_gates.py
python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "compatibility_view"
```

## Handoff

返回 guard changes、allowlist entries and reasons、compatibility tests run、
blocked raw reads，以及 B/C/E integration notes。
