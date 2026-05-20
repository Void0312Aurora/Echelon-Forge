# WP14-E Capability Effects Materialization

状态：`2026-05-21` planned / second-wave materialization candidate。此切片在
B/C/D 尚未 mergeable 时保持 open/planned。

语言版本：

- 英文主文：[wp14_capability_effects_materialization_cluster_20260521.md](wp14_capability_effects_materialization_cluster_20260521.md)
- 中文辅文：`wp14_capability_effects_materialization_cluster_20260521.zh.md`

输入：

- [WP14 capability composition](capability_composition_wp14_20260521.zh.md)
- [WP14-B content definition lowering](wp14_content_definition_lowering_cluster_20260521.zh.md)
- [WP14-C spawn resolution bridge](wp14_spawn_resolution_bridge_cluster_20260521.zh.md)
- Current `src/models/core/default_unit_factory.h`
- Current `src/components/*`

## 1. 目的

`WP14-E` 把 capability families 绑定到现有 ECS/component materialization evidence。
它应解释 factory 已经构造了什么，以及 unsupported capability effect 为什么被拒绝。

## 2. 范围

范围内：

- 当前 components/factory logic 已支持的 mobility、sensing、communication、
  launcher、survivability、command 与 doctrine materialization evidence；
- unsupported-effect rejection reasons；
- 证明 capability effects 不改变当前 platform behavior 的测试。

范围外：

- 添加新战术行为；
- 调整 weapons、sensors、flight dynamics 或 mission logic；
- 创建新平台族；
- 改变 backend/fidelity capability projection。

## 3. 候选实现缝

编辑前检查：

- `src/models/core/default_unit_factory.h`
- `src/content/unit_definition.h`
- 相关 `src/components/*`
- 现有 air/naval engagement 与 mission runtime tests。

首选方式：

- 把 capability family evidence 映射到现有 component creation paths；
- 在改变 materialization behavior 前先添加 diagnostics 或 helper evidence；
- 对 unsupported effect families fail closed，而不是静默忽略；
- 保持既有 platform fixtures。

并行规则：

- `WP14-E` 只有在写入范围互不重叠时才可以与 `WP14-D` 并行。
- 它应该等到 B/C semantics 稳定后再声称 coverage。
- 主线程的 integration/gate 仍由 `WP14-F` 串行负责。

## 4. Gate 规则

| Boundary | Required behavior |
|----------|-------------------|
| Evidence first | Materialization evidence 命名现有 component/factory effects。 |
| No behavior drift | 既有 platform behavior 不变化，除非另有明确 scope。 |
| Unsupported effects | Unsupported 或 undeclared capability effects fail closed。 |
| Family separation | Capability families 不折叠成一个 flat type-name string。 |

## 5. 验收测试

最低测试：

- capability family evidence 匹配代表性 air 与 naval fixtures 的现有 materialized components；
- unsupported capability effects 以稳定原因拒绝；
- 现有 engagement/facade export tests 仍通过；
- acceptance 不要求新增 platform behavior。

建议命令：

```powershell
git diff --check
cmake --build build-local-win -j4
python -m pytest -q tests\architecture\test_wp14_capability_effects_materialization.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\engagement\test_facade_engagement_export.py
python -m pytest -q tests\world_batch\test_world_batch_runtime.py -k "spawn"
```

此切片的最低 acceptance gates：

- `git diff --check` 通过；
- `python -m pytest -q tests\architecture\test_wp14_capability_effects_materialization.py` 通过；
- `.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\engagement\test_facade_engagement_export.py` 通过；
- `python -m pytest -q tests\world_batch\test_world_batch_runtime.py -k "spawn"` 通过；
- 证据只停留在现有 component/factory behavior 上；
- 不引入新的战术行为、平台族或 backend 语义。

## 6. 交接契约

返回：

- touched factory/component files；
- covered capability families；
- unsupported-effect rejection reasons；
- compatibility tests run；
- exact commands and outcomes；
- future platform-family expansion 的 residuals。
