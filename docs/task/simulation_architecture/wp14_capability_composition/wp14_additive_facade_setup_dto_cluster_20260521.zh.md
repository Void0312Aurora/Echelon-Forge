# WP14-D Additive Facade Setup DTO

状态：`2026-05-21` planned / additive surface candidate。此切片保持 open/planned，
直到 typed DTOs 真正 additive 且不会被误当成 accepted public spawn replacement。

语言版本：

- 英文主文：[wp14_additive_facade_setup_dto_cluster_20260521.md](wp14_additive_facade_setup_dto_cluster_20260521.md)
- 中文辅文：`wp14_additive_facade_setup_dto_cluster_20260521.zh.md`

输入：

- [WP14 capability composition](capability_composition_wp14_20260521.zh.md)
- [WP14-A capability bundle contract](wp14_capability_bundle_contract_cluster_20260521.zh.md)
- [WP14-C spawn resolution bridge](wp14_spawn_resolution_bridge_cluster_20260521.zh.md)
- Current `src/runtime/contracts/world_batch_contracts.h`
- Current `src/runtime/facade/runtime_facade_types.h`
- Current `src/interfaces/python/bindings_runtime.cpp`

## 1. 目的

`WP14-D` 通过 additive typed setup DTOs 为未来 `spawn_platform({capabilities...})`
surface 铺路。它不替换当前 `WorldSpawnRequest.type_name` 或 batch setup behavior。

## 2. 范围

范围内：

- typed platform spawn request/result DTO vocabulary；
- 如果添加 runtime surface，则暴露 Python-visible DTO shape；
- incomplete bundles 的 fail-closed validation helpers；
- 证明旧 setup path 仍为 maintained 的 compatibility tests。

范围外：

- 强制 caller 使用 typed platform spawn；
- 把未经验证的 `SimulationKernel::spawn_platform` 暴露为新的 public main API；
- 大范围 scenario JSON migration；
- backend/fidelity capability claims。

## 3. 候选实现缝

编辑前检查：

- `src/runtime/contracts/world_batch_contracts.h`
- `WP14-A` 新增的 contract header
- `src/runtime/facade/runtime_facade_types.h`
- `src/runtime/facade/runtime_facade.cpp`
- `src/interfaces/python/bindings_runtime.cpp`
- `tests/runtime/bindings/test_bindings_runtime_dto_surface.py`

首选方式：

- 在 C 证明 resolution 前，让 DTO 保持 additive 且明确是 bridge-shaped；
- 暴露 validation/rejection，而不是 direct unchecked materialization；
- 保留 `type_name` path 作为维护中的兼容路径。

并行规则：

- 这个切片要与 B/C writer scope 保持 disjoint。
- subagents 可以负责 DTO shape 或 bindings，但主线程保留 F 中的串行
  integration/gate 责任。

## 4. Gate 规则

| Boundary | Required behavior |
|----------|-------------------|
| Additive only | 新 DTO 不移除或取代 `WorldSpawnRequest.type_name`。 |
| Validation | Incomplete capability requests 以稳定原因 fail closed。 |
| Binding shape | Python DTO fields 只在 C++ contract 稳定后可见。 |
| Facade boundary | 证明使用 facade/setup contracts，而不是 raw kernel-only shortcuts。 |

## 5. 验收测试

最低测试：

- DTO fields and defaults 在 C++ 与 Python 中可见；
- incomplete typed spawn requests 以稳定原因拒绝；
- legacy `WorldSpawnRequest.type_name` setup tests 仍通过；
- facade layering tests 不新增 raw kernel escape hatch。

建议命令：

```powershell
git diff --check
cmake --build build-local-win -j4
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\bindings\test_bindings_runtime_dto_surface.py
.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\facade\test_runtime_facade.py -k "world_setup"
python -m pytest -q tests\architecture\test_runtime_facade_layering.py
```

此切片的最低 acceptance gates：

- `git diff --check` 通过；
- `.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\bindings\test_bindings_runtime_dto_surface.py` 通过；
- `.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\bindings\test_wp14_additive_platform_spawn_bindings.py` 通过；
- `.\tools\maintenance\cmo_env.ps1 python -m pytest -q tests\runtime\facade\test_runtime_facade.py -k "world_setup"` 通过；
- `python -m pytest -q tests\architecture\test_runtime_facade_layering.py` 通过；
- `WorldSpawnRequest.type_name` 仍保留，且没有强制 public `spawn_platform`。

## 6. 交接契约

返回：

- touched DTO files；
- binding fields and helper names；
- validation/rejection vocabulary；
- compatibility tests run；
- exact commands and outcomes；
- future public `spawn_platform` promotion 的 residuals。
