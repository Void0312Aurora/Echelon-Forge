# WP20-A Public Capability Fact Ledger

状态：`2026-05-21` pass / source-backed facts accepted。

语言版本：

- 英文主文：
  [wp20_public_capability_fact_ledger_cluster_20260521.md](wp20_public_capability_fact_ledger_cluster_20260521.md)
- 中文辅文：`wp20_public_capability_fact_ledger_cluster_20260521.zh.md`

输入：

- [WP20 主计划](public_capability_platform_composition_wp20_20260521.zh.md)
- [WP14 capability composition](../wp14_capability_composition/capability_composition_wp14_20260521.zh.md)
- [WP17 capability spawn runtime promotion](../wp17_stage3_runtime_materialization_cleanup/wp17_capability_spawn_runtime_cluster_20260521.zh.md)

## 目的

在 WP20 晋级任何 public capability-platform setup surface 之前，冻结当前
source-backed 事实。

这份 ledger 的范围刻意很窄：只记录仓库里已经存在的内容、测试已经强制的
边界，以及当前仍然存在的 public gap。

## 范围

范围内：

- `Capability`、`CapabilityBundle`、`ResolvedPlatformSpawnPlan`、
  `TypedPlatformSpawnRequest`、validation helpers、factory resolution、
  facade setup、world-batch setup 与 bindings 的 source/test inventory；
- 当前哪些 surface 是 public、additive-only、consumed、ignored 或 explicit blocked；
- B/C/D 三条 stream 的最小安全实现 seam；
- 仍然存在的 source-backed residuals 与 blockers。

范围外：

- code changes；
- acceptance review；
- runtime behavior edits；
- 任何没有被 source 或 test 直接支持的未来推断。

## 任务项

| ID | 任务 | 验收 |
|----|------|------|
| `A1` | Source ledger | 精确列出 source/test files 与当前行为，不做无证据推断。 |
| `A2` | Public gap map | 命名 DTO exposure、validation、facade setup 与 materialization 之间的 gap。 |
| `A3` | Compatibility boundary | 冻结 type-name compatibility、scenario-schema stability 与 backend capability separation。 |
| `A4` | Implementation recommendation | 推荐最小 B/C/D implementation seam，或命名 blocker。 |

## Source-Backed Facts

### 1) platform capability contracts 是独立的 platform 命名空间

`src/runtime/contracts/platform_capability_contracts.h` 在
`namespace runtime::platform_capabilities` 下定义 platform vocabulary，
而不是放进 `RuntimeCapabilities`。

证据：

- families 与 request/materialization kinds 在
  [platform_capability_contracts.h](../../../../src/runtime/contracts/platform_capability_contracts.h:12)
  和 [platform_capability_contracts.h](../../../../src/runtime/contracts/platform_capability_contracts.h:20)
- `Capability`、`CapabilityBundle`、`ResolvedPlatformSpawnPlan` struct 在
  [platform_capability_contracts.h](../../../../src/runtime/contracts/platform_capability_contracts.h:105)
  、[platform_capability_contracts.h](../../../../src/runtime/contracts/platform_capability_contracts.h:117)
  、[platform_capability_contracts.h](../../../../src/runtime/contracts/platform_capability_contracts.h:127)
- fail-closed validation helpers 在
  [platform_capability_contracts.h](../../../../src/runtime/contracts/platform_capability_contracts.h:246)
  、[platform_capability_contracts.h](../../../../src/runtime/contracts/platform_capability_contracts.h:286)
  、[platform_capability_contracts.h](../../../../src/runtime/contracts/platform_capability_contracts.h:337)

当前事实：

- contract header 已经包含兼容性保留与 typed request 相关 vocabulary，例如
  `type_name_compatibility`、`typed_platform_request`、`resolved_spawn_plan_bridge`。
- 该 header 中没有 `RuntimeCapabilities`，这与 WP14 的边界一致：backend/fidelity
  capability projection 与 platform capability composition 仍然分离。

### 2) `world_batch_contracts.h` 已公开 typed setup DTO，但 public runtime setup
仍保留 legacy `WorldSpawnRequest` 路径

`src/runtime/contracts/world_batch_contracts.h` 定义了
`TypedPlatformSpawnRequest`，而 batch setup request 同时携带 legacy 与 typed 两类数组。

证据：

- `WorldSpawnRequest` 仍是 legacy surface：
  [world_batch_contracts.h](../../../../src/runtime/contracts/world_batch_contracts.h:46)
- typed-request rejection 常量与 typed DTO 位于：
  [world_batch_contracts.h](../../../../src/runtime/contracts/world_batch_contracts.h:69)
  和 [world_batch_contracts.h](../../../../src/runtime/contracts/world_batch_contracts.h:88)
- `BatchWorldSetupRequest` 同时包含 `spawn_requests` 与
  `typed_platform_spawn_requests`：
  [runtime_facade_types.h](../../../../src/runtime/facade/runtime_facade_types.h:112)
  和 [world_batch_contracts.h](../../../../src/runtime/contracts/world_batch_contracts.h:88)
- `validate_typed_platform_spawn_request()` 只是 declarative/fail-closed，
  只检查 DTO 形状以及 bundle/plan validation：
  [world_batch_contracts.h](../../../../src/runtime/contracts/world_batch_contracts.h:140)

当前事实：

- typed DTO 已经在 contracts 与 Python bindings 中公开。
- validation helper 不会 materialize runtime 行为。
- mainline setup path 仍然通过 legacy spawn request 执行。

### 3) `RuntimeFacade` setup surface 仍消费 legacy world-spawn requests

`RuntimeFacade` 暴露 `BatchWorldSetupRequest`，并把 setup 直接转发到 legacy
`spawn_requests` 向量。

证据：

- facade setup 声明位于：
  [runtime_facade.h](../../../../src/runtime/facade/runtime_facade.h:47)
  和 [runtime_facade.h](../../../../src/runtime/facade/runtime_facade.h:52)
- setup forwarding 位于：
  [runtime_facade.cpp](../../../../src/runtime/facade/runtime_facade.cpp:1312)
  和 [runtime_facade.cpp](../../../../src/runtime/facade/runtime_facade.cpp:1330)
- Python binding 暴露了 `apply_world_setup_batch` 与 `apply_world_setup`：
  [bindings_runtime.cpp](../../../../src/interfaces/python/bindings_runtime.cpp:1340)
  和 [bindings_runtime.cpp](../../../../src/interfaces/python/bindings_runtime.cpp:1350)

当前事实：

- `RuntimeFacade::apply_world_setup()` 只是把 `request.spawn_requests` 复制到 runtime batch 调用。
- 这里没有 public `spawn_platform` surface。
- `RuntimeFacade::runtime()` 仍然只是兼容或诊断用途的 escape hatch，不是推荐的 mainline setup surface。

### 4) `WorldBatchRuntime` consume path 仍只 materialize `WorldSpawnRequest`

`src/core/engine/world_batch_runtime.cpp` 的 mainline setup path 还没有消费 typed request。

证据：

- `spawn_units_batch(const std::vector<WorldSpawnRequest>&)` 位于
  [world_batch_runtime.cpp](../../../../src/core/engine/world_batch_runtime.cpp:514)
- `apply_world_setup_batch(...)` 也只接受
  `const std::vector<WorldSpawnRequest>&`：
  [world_batch_runtime.cpp](../../../../src/core/engine/world_batch_runtime.cpp:526)
- setup loop 只 group 与 spawn `WorldSpawnRequest` 条目：
  [world_batch_runtime.cpp](../../../../src/core/engine/world_batch_runtime.cpp:538)
  到 [world_batch_runtime.cpp](../../../../src/core/engine/world_batch_runtime.cpp:577)

当前事实：

- typed platform requests 并没有在 `WorldBatchRuntime` 中被 auto-materialize。
- 明确的 public gap 是 typed request 到 legacy world-materialization path 之间缺少 consume bridge。

### 5) `DefaultUnitFactory` 已经通过 bundle template 与 resolved plan 在 type-name
兼容链上完成 resolution

`src/models/core/default_unit_factory.h` 已经包含 WP20 想要 publicize 的 internal bridge，
而不是需要重写一套新的桥。

证据：

- bundle lowering 位于
  [default_unit_factory.h](../../../../src/models/core/default_unit_factory.h:329)
- sensing、mobility、communication、launching、survivability、command、doctrine 的
  capability-family evidence 覆盖位于
  [default_unit_factory.h](../../../../src/models/core/default_unit_factory.h:347)
  到 [default_unit_factory.h](../../../../src/models/core/default_unit_factory.h:560)
- resolved-plan 构建位于
  [default_unit_factory.h](../../../../src/models/core/default_unit_factory.h:573)
- unknown definition 的 type-name fallback rejection 位于
  [default_unit_factory.h](../../../../src/models/core/default_unit_factory.h:619)
  到 [default_unit_factory.h](../../../../src/models/core/default_unit_factory.h:640)
- spawn gate 在 materialization 前验证 resolved plan：
  [default_unit_factory.h](../../../../src/models/core/default_unit_factory.h:656)
  到 [default_unit_factory.h](../../../../src/models/core/default_unit_factory.h:684)

当前事实：

- factory 已经从 `type_name` 计算出 `CapabilityBundle`、`ResolvedPlatformSpawnPlan`
  与 evidence refs。
- spawn path 仍然保持 compatibility-preserving，并且在 plan validation 之后才进入
  legacy unit-definition materialization。

### 6) Python bindings 已公开新 platform DTO，但还没有 public consume bridge

`src/interfaces/python/bindings_runtime.cpp` 已经暴露 platform DTO 以及 batch setup request
字段，也就是说 DTO surface 已经对 Python 可见。

证据：

- `CapabilityBundle` 与 `ResolvedPlatformSpawnPlan` bindings 位于
  [bindings_runtime.cpp](../../../../src/interfaces/python/bindings_runtime.cpp:302)
  和 [bindings_runtime.cpp](../../../../src/interfaces/python/bindings_runtime.cpp:336)
- `TypedPlatformSpawnRequest` binding 位于
  [bindings_runtime.cpp](../../../../src/interfaces/python/bindings_runtime.cpp:406)
- `BatchWorldSetupRequest.typed_platform_spawn_requests` binding 位于
  [bindings_runtime.cpp](../../../../src/interfaces/python/bindings_runtime.cpp:725)
- `RuntimeFacade.apply_world_setup` binding 位于
  [bindings_runtime.cpp](../../../../src/interfaces/python/bindings_runtime.cpp:1341)

当前事实：

- Python 现在已经可以构造 typed DTO。
- 但 Python 还不能通过一个单独的 typed consume bridge 去驱动 facade，因为 facade 仍然只转发 legacy spawn-request 数组。

### 7) WP14 boundary guards 已经明确冻结第一阶段 public gap

`tests/architecture/platform_spawn/test_boundary_guards.py` 以及相关 WP14 tests 证明当前 public gap
是 intentional，而不是遗漏。

证据：

- runtime/bindings/scenario compatibility layers 中没有 public `spawn_platform` surface：
  [test_wp14_boundary_guards.py](../../../../tests/architecture/platform_spawn/test_boundary_guards.py:26)
- `RuntimeCapabilities` 仍然只用于 backend/fidelity：
  [test_wp14_boundary_guards.py](../../../../tests/architecture/platform_spawn/test_boundary_guards.py:43)
- legacy `WorldSpawnRequest.type_name` surface 仍然存在：
  [test_wp14_boundary_guards.py](../../../../tests/architecture/platform_spawn/test_boundary_guards.py:94)
- typed requests 被明确标记为 additive 且不会 auto-materialize：
  [test_wp14_boundary_guards.py](../../../../tests/architecture/platform_spawn/test_boundary_guards.py:140)
- typed DTO validation 保持 declarative/fail-closed：
  [test_wp14_boundary_guards.py](../../../../tests/architecture/platform_spawn/test_boundary_guards.py:176)
- contract header tests 确认 `RuntimeCapabilities` 没有进入
  `platform_capability_contracts.h`：
  [test_wp14_platform_capability_contracts.py](../../../../tests/architecture/platform_spawn/test_platform_capability_contracts.py:51)
- content-lowering tests 确认 type-name plan resolution 在 materialization 之前：
  [test_wp14_content_definition_lowering.py](../../../../tests/architecture/platform_spawn/test_default_factory_spawn_plan_resolution.py:48)
  和 [test_wp14_resolved_spawn_plan_evidence.py](../../../../tests/architecture/platform_spawn/test_default_factory_spawn_plan_resolution.py:60)
- Python DTO tests 确认 typed DTO 可构造，同时保留 legacy `WorldSpawnRequest`
  surface：
  [test_wp14_additive_platform_spawn_bindings.py](../../../../tests/runtime/bindings/test_wp14_additive_platform_spawn_bindings.py:75)

当前事实：

- 仓库已经预期 `typed_platform_spawn_requests` 会存在于 DTO 层，而 runtime path 仍然
  明确不进行 materialization。

## Public Gap

当前 public gap 不在 DTO 声明，而在 consumption。

已存在：

- contracts 与 Python bindings 中的 public typed DTO；
- typed DTO 与 resolved plan 的 fail-closed validation helpers；
- 从 `type_name` 到 bundle/plan evidence 的 internal factory resolution；
- 通过 `WorldSpawnRequest` 的 legacy setup execution。

缺失：

- 一个 public typed setup consume bridge，能够先 admit typed requests，再将它们路由到
  compatibility-preserving resolved-plan path；
- 该 consume path 的 explicit result evidence；
- 任何让 typed setup 成为 mainline execution path 的 facade/runtime surface。

## Compatibility Boundary

source-backed compatibility facts：

- `WorldSpawnRequest.type_name` 仍然是 legacy public setup field。
- scenario 与 example schema files 被 tests 约束为在本 slice 中保持 legacy request shape。
- `RuntimeCapabilities` 只用于 backend/fidelity projection，而不是 platform composition。
- `DefaultUnitFactory` 已经使用 type-name compatibility chain，并且在 plan validation 后才 materialize。
- `spawn_platform` 仍未出现在 runtime/facade/binding surface 中。

## Safe Seam Recommendation

B/C/D 的第一条推荐实现 seam：

1. 保持 `DefaultUnitFactory::resolve_platform_spawn_plan_for_type_name()` 作为 resolved-plan
   evidence 的 source；
2. 在 facade boundary 增加 typed-request consume bridge，先 validate `TypedPlatformSpawnRequest`，
   再把 admitted request 通过 compatibility-preserving plan path 转发；
3. 在 typed consume bridge 明确并测试通过之前，让 `WorldBatchRuntime` 继续保持 legacy spawn
   request 的 materialization owner；
4. 只有在 consume bridge 稳定之后，才向 Python 暴露 admitted typed surface。

为什么这个 seam 安全：

- 它复用已经经过测试的 source facts，而不是引入并行 spawn schema；
- 它保留 compatibility path 与 legacy `type_name` surface；
- 它继续把 backend capability projection 与 platform composition 分离；
- 它避免在 typed consume bridge 被证明前改变 `SimulationKernel` 的 materialization semantics。

## Residuals

- `WorldBatchRuntime` 的 mainline setup path 仍然只消费 `WorldSpawnRequest`。
- `RuntimeFacade::apply_world_setup()` 仍然只 forward `spawn_requests`。
- 目前还没有 public typed setup result/admission surface。
- 没有 source-backed evidence 显示当前 slice 中 runtime materialization 已经消费
  `typed_platform_spawn_requests`。

## Continuation State

- 原 A-slice entry gate：`WP20-B` 与 `WP20-E` 可以继续，因为 typed request DTO、
  boundary facts 与 backend/platform separation 已有 source-backed evidence。
- B/C 后续更新：`WP20-C` 已在 public admission/result contract 返回后释放，并已通过验收。
- 当前下一流：`WP20-D` 已释放给 binding/public-surface 工作，且只应发布 C consume bridge
  真正消费的 surface。

## Commands Run

```bash
pwd && rg --files docs task . | rg 'wp20|wp14|wp17|platform_capability_contracts|world_batch_contracts|bindings_runtime|DefaultUnitFactory|RuntimeFacade|WorldBatchRuntime|boundary guards|test'
rg -n "TypedPlatformSpawnRequest|ResolvedPlatformSpawnPlan|typed_platform_spawn_requests|spawn_platform|RuntimeFacade::apply_world_setup|apply_world_setup\\(|WorldBatchRuntime|DefaultUnitFactory::spawn|ResolvedSpawnPlan|CapabilityBundle|Capability" src tests
sed -n '1,240p' src/runtime/contracts/platform_capability_contracts.h
sed -n '1,260p' src/runtime/contracts/world_batch_contracts.h
sed -n '1,260p' src/interfaces/python/bindings_runtime.cpp
sed -n '1,260p' src/runtime/facade/runtime_facade.h
sed -n '1,360p' src/runtime/facade/runtime_facade.cpp
sed -n '1,260p' src/core/engine/world_batch_runtime.h
sed -n '1,260p' src/core/engine/world_batch_runtime.cpp
sed -n '1,260p' src/models/core/default_unit_factory.h
sed -n '1,240p' tests/architecture/platform_spawn/test_platform_capability_contracts.py
sed -n '1,240p' tests/architecture/platform_spawn/test_boundary_guards.py
sed -n '1,260p' tests/architecture/platform_spawn/test_typed_platform_spawn_contracts.py
sed -n '1,260p' tests/runtime/bindings/test_wp14_additive_platform_spawn_bindings.py
sed -n '1,260p' tests/world_batch/test_world_batch_runtime.py
sed -n '1,260p' tests/architecture/platform_spawn/test_default_factory_spawn_plan_resolution.py
sed -n '1,260p' tests/architecture/runtime_facade
sed -n '1,220p' tests/architecture/platform_spawn/test_default_factory_spawn_plan_resolution.py
nl -ba src/runtime/facade/runtime_facade.cpp | sed -n '1310,1365p'
nl -ba src/core/engine/world_batch_runtime.cpp | sed -n '510,560p'
nl -ba src/models/core/default_unit_factory.h | sed -n '320,700p'
nl -ba src/interfaces/python/bindings_runtime.cpp | sed -n '280,440p'
nl -ba tests/architecture/platform_spawn/test_boundary_guards.py | sed -n '1,260p'
nl -ba tests/architecture/platform_spawn/test_platform_capability_contracts.py | sed -n '1,260p'
nl -ba tests/architecture/platform_spawn/test_default_factory_spawn_plan_resolution.py | sed -n '1,220p'
nl -ba tests/architecture/platform_spawn/test_default_factory_spawn_plan_resolution.py | sed -n '1,220p'
nl -ba tests/runtime/bindings/test_wp14_additive_platform_spawn_bindings.py | sed -n '1,220p'
nl -ba tests/world_batch/test_world_batch_runtime.py | sed -n '1,120p'
nl -ba src/runtime/contracts/platform_capability_contracts.h | sed -n '1,220p'
nl -ba src/runtime/contracts/platform_capability_contracts.h | sed -n '220,520p'
nl -ba src/runtime/contracts/world_batch_contracts.h | sed -n '1,260p'
nl -ba src/runtime/facade/runtime_facade_types.h | sed -n '1,180p'
nl -ba src/runtime/facade/runtime_facade.cpp | sed -n '200,260p'
nl -ba src/interfaces/python/bindings_runtime.cpp | sed -n '1328,1362p'
nl -ba src/core/engine/world_batch_runtime.cpp | sed -n '520,590p'
```

## 交接

返回 source-backed fact ledger、安全 seam 建议、blockers、residuals，以及
B/E 是否可以继续推进。

当前返回：

- Status: `pass`
- `WP20-B` 与 `WP20-E` 已从本 ledger 继续推进。
- `WP20-C` 已在 `WP20-B` 返回 public admission/result contract 后推进，并已通过 focused validation。
- `WP20-D` 现在是已释放的下一流。
