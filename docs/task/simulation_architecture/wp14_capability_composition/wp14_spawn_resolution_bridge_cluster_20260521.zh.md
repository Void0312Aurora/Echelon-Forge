# WP14-C Spawn Resolution Bridge

状态：`2026-05-21` planned / second-wave implementation candidate。此切片
必须等待 B 提供 resolution evidence，且在 first slice 仍 open/planned 时
不应被标记为 accepted。

语言版本：

- 英文主文：[wp14_spawn_resolution_bridge_cluster_20260521.md](wp14_spawn_resolution_bridge_cluster_20260521.md)
- 中文辅文：`wp14_spawn_resolution_bridge_cluster_20260521.zh.md`

输入：

- [WP14 capability composition](capability_composition_wp14_20260521.zh.md)
- [WP14-B content definition lowering](wp14_content_definition_lowering_cluster_20260521.zh.md)
- Current `src/core/engine/simulation_kernel.*`
- Current `src/core/engine/world_batch_runtime.*`
- Current `src/runtime/facade/runtime_facade.*`

## 1. 目的

`WP14-C` 让现有 spawn entry points 在 materialization 前先通过 resolution。它保持
`spawn_unit(type_name)`、`WorldSpawnRequest` 与 facade setup 兼容，同时让
resolved-plan evidence 可检查。

## 2. 范围

范围内：

- 让 kernel/world-batch/facade spawn paths 经过 B 的 resolver；
- 保持 public type-name surfaces 与现有 Python behavior；
- 暴露足够 diagnostics/evidence，证明 bridge 被使用；
- 为 world batch 与 facade setup 添加 compatibility regression tests。

范围外：

- 把所有 call sites 迁到 `CapabilityBundle`；
- 删除 `WorldSpawnRequest.type_name`；
- 直接晋级 public `spawn_platform`；
- 改变 entity/component behavior。

## 3. 候选实现缝

编辑前检查：

- `src/core/engine/simulation_kernel.h`
- `src/core/engine/simulation_kernel.cpp`
- `src/core/engine/world_batch_runtime.cpp`
- `src/runtime/facade/runtime_facade_types.h`
- `src/runtime/facade/runtime_facade.cpp`
- `src/interfaces/python/bindings_core.cpp`
- `src/interfaces/python/bindings_runtime.cpp`

首选方式：

- 保持 caller-facing signatures 稳定；
- 在 factory materialization 前插入窄的 resolution step；
- 成功时保持旧行为，resolver 失败时添加显式 rejection/evidence；
- 避免对 tests 或 scenarios 做大范围 search-and-replace。

并行规则：

- `WP14-C` 只能在 B 的语义稳定到足以被引用后启动。
- 它不能与 `WP14-B` 在同一 factory/kernel seam 上共享 writer。
- 主线程的 integration/gate 仍然是 `WP14-F` 中的串行责任。

## 4. Gate 规则

| Boundary | Required behavior |
|----------|-------------------|
| Public compatibility | 现有 `spawn_unit(type_name)` 与 batch setup callers 仍可工作。 |
| Resolution before materialization | Kernel/batch/facade setup paths 在 factory creation 前使用 resolved plan。 |
| Evidence | 测试可检查 type name resolved to capability plan。 |
| No broad migration | acceptance 不要求全仓 caller rewrite。 |

## 5. 验收测试

最低测试：

- direct `SimulationKernel::spawn_unit` compatibility fixture 仍通过；
- `WorldBatchRuntime::spawn_units_batch` 保持当前 `type_name` 行为；
- facade world setup 使用 type-name compatibility，并暴露 resolution evidence 或稳定 diagnostics；
- invalid type names 以可检查原因 fail closed。

建议命令：

```powershell
git diff --check
cmake --build build-local-win -j4
python -m pytest -q tests\world_batch\test_world_batch_runtime.py -k "spawn or world_setup"
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\facade\test_runtime_facade.py -k "world_setup or observation_packet"
python -m pytest -q tests\architecture\test_runtime_facade_layering.py
```

此切片的最低 acceptance gates：

- `git diff --check` 通过；
- `python -m pytest -q tests\world_batch\test_world_batch_runtime.py -k "spawn or world_setup"` 通过；
- `.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\facade\test_runtime_facade.py -k "world_setup or observation_packet"` 通过；
- `python -m pytest -q tests\architecture\test_runtime_facade_layering.py` 通过；
- bridge 需要能展示可检查的 resolution evidence，且不要求 broad caller migration；
- `WorldSpawnRequest.type_name` 仍是 maintained compatibility surface。

## 6. 交接契约

返回：

- touched kernel/world-batch/facade files；
- preserved compatibility behavior；
- exposed resolution evidence；
- added or updated tests；
- exact commands and outcomes；
- 给 additive facade DTO 或 materialization work 的 residuals。
