# WP14-B Content Definition Lowering

状态：`2026-05-21` planned / first-wave implementation candidate。此切片仍
保持 open/planned，直到 B 有 implementation evidence；不要为 WP14 创建
acceptance review。

语言版本：

- 英文主文：[wp14_content_definition_lowering_cluster_20260521.md](wp14_content_definition_lowering_cluster_20260521.md)
- 中文辅文：`wp14_content_definition_lowering_cluster_20260521.zh.md`

输入：

- [WP14 capability composition](capability_composition_wp14_20260521.zh.md)
- [WP14-A capability bundle contract](wp14_capability_bundle_contract_cluster_20260521.zh.md)
- Current `src/content/unit_definition.h`
- Current `src/core/interfaces/unit_factory.h`
- Current `src/models/core/default_unit_factory.h`

## 1. 目的

`WP14-B` 定义第一版 deterministic lowering：从兼容性的 `type_name` 到 capability
bundle template 和 resolved platform spawn plan。它让现有 factory 的隐式组合关系可见，
但不改变 public callers。

## 2. 范围

范围内：

- 把当前 `UnitDefinition` evidence lower 成 capability bundle templates；
- 覆盖现有 sensor refs、mounted sensors、loadouts、naval weapon systems、mobility
  hints、command/doctrine defaults，以及已经存在的 survivability placeholders；
- 返回 `WP14-C` 可 materialize 的 resolved spawn plan；
- 为 unknown 或 incomplete templates 产出 fail-closed reasons。

范围外：

- 改变 Python public APIs；
- 替换所有 scenario/content JSON shape；
- 编辑 `WP14-C` 所属 kernel/facade setup bridge；
- 添加新平台族或行为模型。

## 3. 候选实现缝

编辑前检查：

- `src/content/unit_definition.h`
- `src/content/unit_catalog.*`
- `src/core/interfaces/unit_factory.h`
- `src/models/core/default_unit_factory.h`
- 会 spawn `Aircraft`、`F-16C_Block50`、ships、sensors 与 naval weapon systems 的测试。

首选方式：

- 保持 `type_name` 作为兼容 lookup key；
- 添加一个小型 resolver/helper，返回 capability bundle template evidence；
- 第一切片不要求 JSON migration；
- 保持 factory materialization behavior 完全一致。

并行规则：

- 此切片可以与 `WP14-A` 并行，但前提是不会反向改动 A 正在定义的 shared contract
  名称。
- 它不能与 `WP14-C` 在同一 factory/kernel seam 上并行。
- 主线程的 integration/gate 责任在 `WP14-F`；subagent 只负责彼此 disjoint 的文件
  或 helper block。

## 4. Gate 规则

| Boundary | Required behavior |
|----------|-------------------|
| Compatibility | 现有 type names 无需 caller 变化即可 resolve。 |
| Explicit lowering | 当当前 definition 包含证据时，sensor、launcher/loadout、command/doctrine、mobility 与 survivability evidence 被表示出来。 |
| Determinism | Resolution order 与 evidence refs 稳定。 |
| Fail closed | Unknown 或 incomplete templates 返回可检查 rejection reasons。 |

## 5. 验收测试

最低测试：

- 已知 aircraft 与 naval type names resolve 成 deterministic capability plans；
- sensor refs、mounted sensors、default loadouts 与 naval weapon systems 在存在时被表示为 capability evidence；
- unknown type names 以稳定原因拒绝；
- resolved-plan path 保持当前 factory materialization behavior。

建议命令：

```powershell
git diff --check
cmake --build build-local-win -j4
python -m pytest -q tests\architecture\test_wp14_content_definition_lowering.py
python -m pytest -q tests\architecture\test_wp14_platform_capability_contracts.py
python -m pytest -q tests\world_batch\test_world_batch_runtime.py -k "spawn or world_setup"
```

此切片的最低 acceptance gates：

- `git diff --check` 无新增 diff 错误；
- `python -m pytest -q tests\architecture\test_wp14_content_definition_lowering.py` 通过；
- `python -m pytest -q tests\architecture\test_wp14_platform_capability_contracts.py` 通过；
- `python -m pytest -q tests\world_batch\test_world_batch_runtime.py -k "spawn or world_setup"` 通过；
- 用于证明新 evidence coverage 的任何 `rg` audit 都要写入 handoff；
- 既有 `spawn_unit(type_name)` 行为不变。

## 6. 交接契约

返回：

- touched content/factory files；
- resolver/helper names；
- covered type names and capability families；
- added or updated tests；
- exact commands and outcomes；
- 给 `WP14-C` bridge 或 `WP14-E` materialization 的 blockers。
