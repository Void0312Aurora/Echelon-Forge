# WP16-D Legacy Path Deprecation And Compatibility Gates

状态：`2026-05-21` complete / legacy compatibility gates accepted。

语言版本：

- 英文主文：[wp16_legacy_deprecation_compatibility_cluster_20260521.md](wp16_legacy_deprecation_compatibility_cluster_20260521.md)
- 中文辅文：`wp16_legacy_deprecation_compatibility_cluster_20260521.zh.md`

输入：

- [WP16 runtime spine consolidation](runtime_spine_consolidation_wp16_20260521.zh.md)
- [WP9 contract and infrastructure closure](../wp9_contract_infrastructure_closure/contract_infrastructure_closure_wp9_20260520.zh.md)
- [WP14 capability composition](../wp14_capability_composition/capability_composition_wp14_20260521.zh.md)
- [WP15 counterfactual experiment generation](../wp15_counterfactual_experiment_generation/counterfactual_experiment_generation_wp15_20260521.zh.md)

## 1. 目标

`WP16-D` 把 inventory 转成 compatibility policy。Legacy paths 不应继续暧昧存在：
每条路径都必须被标为 preserved、wrapped、deprecated、removed 或 diagnostics-only，
并带有测试和理由。

## 2. 范围

范围内：

- 为已知 bypass paths 添加 guard tests 或 allowlist updates；
- 分类 raw runtime、direct state、legacy spawn、scenario setup、diagnostics 与
  training compatibility paths；
- 适当添加 deprecation records 或 runtime warnings；
- 在 WP16-C 证明 maintained replacement 前保护 public compatibility APIs；
- 防止 diagnostics-only path 静默成为 maintained。

范围外：

- 缺少 replacement evidence 的 broad API removal；
- 超出 compatibility gates 的 scenario-schema migration；
- 改变 capability 或 backend/fidelity support semantics；
- 创建 acceptance reviews。

## 3. 交付物

- Legacy path status table 或 machine-readable fixture。
- 证明 diagnostics-only 与 compatibility boundaries 的 guard tests。
- 后续应迁移路径的 deprecation records。
- 带 replacement evidence 与 risk notes 的 removal candidates。

## 4. Gate 规则

| Gate item | Pass condition |
|-----------|----------------|
| Classification | WP16-A 发现的每条 legacy path 都有 bounded status 与 owner。 |
| Replacement evidence | deprecated 或 removed paths 引用 maintained replacement 或文档化理由。 |
| Diagnostics isolation | diagnostics-only path 不能意外被称为 maintained。 |
| Compatibility preservation | public APIs 保持可用，除非 removal 被显式 gate 并测试。 |

## 5. 建议验证

```bash
git diff --check
python -m pytest -q tests/architecture/runtime_spine/test_runtime_spine_inventory_gates.py
python -m pytest -q tests/architecture/runtime_facade
```

## 6. 交接契约

返回：

- touched files；
- legacy classification table 或 fixture；
- deprecation/removal candidates；
- 精确验证命令和结果；
- compatibility risks；
- 给 WP16-F 的 notes。
