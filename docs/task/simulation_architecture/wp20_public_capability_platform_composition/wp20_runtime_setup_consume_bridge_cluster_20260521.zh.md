# WP20-C Runtime Setup Consume Bridge

状态：`2026-05-21` accepted / focused pass。

语言版本：

- 英文主文：[wp20_runtime_setup_consume_bridge_cluster_20260521.md](wp20_runtime_setup_consume_bridge_cluster_20260521.md)
- 中文辅文：`wp20_runtime_setup_consume_bridge_cluster_20260521.zh.md`

输入：

- [WP20 主计划](public_capability_platform_composition_wp20_20260521.zh.md)
- [WP20-B public typed platform spawn contract](wp20_public_typed_platform_spawn_contract_cluster_20260521.zh.md)
- `src/core/engine/world_batch_runtime.*`
- `src/runtime/facade/runtime_facade.*`
- `src/models/core/default_unit_factory.h`

## 目的

通过现有 compatibility-preserving resolved-plan bridge 消费 validated typed platform
spawn requests。

## 范围

范围内：

- 在任何 spawn 前验证 typed requests；
- 只通过 preserved `source_type_name` compatibility path 与 admitted resolved plan
  进行 materialization；
- 为 admitted、materialized 与 rejected typed requests 返回 result evidence；
- 测试证明 legacy `spawn_requests` 行为不变。

范围外：

- 直接 materialize 任意 capability bundle；
- Python binding edits；
- scenario schema migration；
- 新平台行为。

## 任务项

| ID | 任务 | 验收 |
|----|------|------|
| `C1` | Validation before consume | 每个 typed request 都先 validation，后 spawn attempt。 |
| `C2` | Compatibility bridge | Materialization 使用 preserved `source_type_name` / resolved plan evidence，而非任意 bundle semantics。 |
| `C3` | Result evidence | 按 B 的 ordering contract 返回 admitted/materialized/rejected typed results。 |
| `C4` | Legacy preservation | 既有 `spawn_units_batch` 与 `apply_world_setup_batch` legacy tests 仍有效。 |

## 建议验证

```bash
git diff --check
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "spawn or world_setup"
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "world_setup or capability or spawn"
```

## 交付

返回 touched files、behavior summary、validation results，以及需要 D 暴露或 F 收口的 residuals。

当前实现说明：

- `RuntimeFacade::apply_world_setup()` 继续把
  `BatchWorldSetupResult.entity_ids` 保留为 legacy `spawn_requests` 的结果通道，
  并按输入顺序单独填充 `typed_platform_spawn_results`。
- 每个 typed request 在任何 spawn attempt 前都会先经过
  `validate_typed_platform_spawn_request()`。
- runtime consume 仍然局限在 facade；`WorldBatchRuntime` 不新增 typed public
  spawn API。
- bridge 只允许通过 preserved compatibility path 进行 materialization：
  已 admitted 的 `resolved_spawn_plan` 加 preserved `source_type_name`，然后复用
  legacy `spawn_unit(type_name)` materialization chain。
- 本流实际使用的 runtime fail-closed reasons 为
  `typed_platform_spawn_world_index_out_of_range` 与
  `typed_platform_spawn_materialization_failed`。
- validation 失败、`source_type_name` 不匹配、或 admitted-plan handoff 被拒绝时，
  都维持 B 合同里的 stable reason，并把 runtime diagnostics 追加到 `errors`。
- typed materialization 成功时会保留 helper 预置的 evidence refs，再在其后追加
  runtime/facade bridge evidence。

D 下一步必须暴露的 public surface：

- `BatchWorldSetupResult.typed_platform_spawn_results`
- `TypedPlatformSpawnResult` 的全部 public fields
- additive 行为：legacy caller 仍可只消费 `entity_ids`
