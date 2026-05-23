# WP16-A Runtime Spine Inventory And Bypass Map

状态：`2026-05-21` complete / inventory and bypass map accepted。

语言版本：

- 英文主文：[wp16_runtime_spine_inventory_cluster_20260521.md](wp16_runtime_spine_inventory_cluster_20260521.md)
- 中文辅文：`wp16_runtime_spine_inventory_cluster_20260521.zh.md`

输入：

- [WP16 runtime spine consolidation](runtime_spine_consolidation_wp16_20260521.zh.md)
- [WP10 causal runtime foundation](../wp10_causal_runtime_foundation/causal_runtime_foundation_wp10_20260520.zh.md)
- [WP15 counterfactual experiment generation](../wp15_counterfactual_experiment_generation/counterfactual_experiment_generation_wp15_20260521.zh.md)

## 1. 目标

`WP16-A` 创建 WP16 其余工作共用的地图。它盘点哪些路径已经经过已验收 runtime
spine，哪些仍通过 raw runtime access、direct ECS/state mutation、compatibility
wrappers、diagnostics-only helpers、legacy spawn、scenario setup、training
adapters 或 experiment scaffolding 绕过该主干。

## 2. 范围

范围内：

- 检查 runtime facade、runtime window coordinator、world-batch runtime、Python RL
  adapters、scenario compiler/runtime、training helpers、experiment evidence surfaces、
  spawn/setup paths 与 diagnostics exports；
- 把每条路径分类为 `maintained_spine`、`compatibility_wrapper`、
  `diagnostics_only`、`deprecated_candidate`、`blocked` 或 `unknown_requires_owner`；
- 识别 WP16-B/C 的 selected spine slice；
- 命名后续 stream 必须使用的 node ids、barrier ids、facade APIs、Python adapters 与 tests。

范围外：

- 实现 clock-domain enforcement；
- 迁移 facade 或 batch consumers；
- 删除 legacy APIs；
- 创建 acceptance review files。

## 3. 交付物

- 位于 owner 选定位置的 code-backed 或 fixture-backed bypass inventory。
- maintained runtime-spine definition，命名 setup/admission、input injection、
  manifest nodes、clock-domain cadence、barrier/event evidence、facade export 与
  downstream consumer evidence。
- 无法安全分类路径的 residual list。
- focused tests 或 audit fixtures，证明 inventory 覆盖本阶段选定的 maintained files。

## 4. Gate 规则

| Gate item | Pass condition |
|-----------|----------------|
| Coverage | WP10-WP15 触及的 runtime/facade/batch/scenario/training/experiment/spawn/replay/diagnostics paths 都被显式分类。 |
| Ownership | 每条 non-maintained path 都有 owner、next gate 或保留理由。 |
| No hidden bypass | unknown path 不被默认视为 maintained。 |
| GAP-9 handoff | 为 WP16-B 命名 selected clock-domain slice 与 manifest nodes。 |

## 5. 建议验证

```bash
git diff --check
python -m pytest -q tests/architecture/test_wp16_runtime_spine_inventory.py
```

如果 worker 用 audit tool 而不是 test，需要返回精确命令与输出摘要。

## 6. 交接契约

返回：

- touched files；
- inventory path 与 classification vocabulary；
- selected WP16-B/C spine slice；
- 精确命令和结果；
- blockers 与 residual paths；
- 给 B、C、D、E 的 notes。
