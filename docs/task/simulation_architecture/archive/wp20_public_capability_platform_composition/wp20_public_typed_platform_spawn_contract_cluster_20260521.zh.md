# WP20-B Public Typed Platform Spawn Contract

状态：`2026-05-21` implemented / focused pass。

语言版本：

- 英文主文：[wp20_public_typed_platform_spawn_contract_cluster_20260521.md](wp20_public_typed_platform_spawn_contract_cluster_20260521.md)
- 中文辅文：`wp20_public_typed_platform_spawn_contract_cluster_20260521.zh.md`

输入：

- [WP20 主计划](public_capability_platform_composition_wp20_20260521.zh.md)
- [WP20-A fact ledger](wp20_public_capability_fact_ledger_cluster_20260521.zh.md)
- `src/runtime/contracts/world_batch_contracts.h`
- `src/runtime/facade/runtime_facade_types.h`

## 目的

在 typed platform spawn requests 能被 setup execution 消费之前，定义 public
admission/result contract。

## 范围

范围内：

- additive result/admission DTO 字段：request id、entity id、validity、
  fail-closed state、rejection reason、source type-name、resolved plan id、
  capability bundle id 与 evidence refs；
- legacy `spawn_requests` 与 typed platform requests 的 result ordering 规则；
- typed setup optional 且 fail closed 的 validation rules；
- 聚焦 architecture/DTO tests。

范围外：

- runtime materialization；
- Python bindings，除非只是为了 compile surface discovery；
- scenario schema migration；
- public `spawn_platform` convenience API。

## 任务项

| ID | 任务 | 验收 |
|----|------|------|
| `B1` | Result DTO shape | public result/admission DTO 存在并携带 request/entity/evidence 字段。 |
| `B2` | Ordering contract | returned ids/results 的 ordering 被文档化并有测试保护。 |
| `B3` | Fail-closed reasons | missing ids、invalid bundles、invalid plans、missing evidence 与 compatibility loss 都用稳定 reason 拒绝。 |
| `B4` | Optionality | Legacy `WorldSpawnRequest` 与 `spawn_unit(type_name)` 仍是 maintained compatibility surfaces。 |

## 候选形态

已实现的 additive 形态：

- 保持 `BatchWorldSetupResult.entity_ids` 兼容；
- 添加 `BatchWorldSetupResult.typed_platform_spawn_results`；
- 定义 `TypedPlatformSpawnAdmission`，用于 materialization 之前的
  validation/admission handoff；
- 定义 `TypedPlatformSpawnResult`，用于 admission/materialization 之后的
  public result 传播；
- 所有新增字段都保持 additive，且仅属于 public contract；本流不改 runtime
  behavior。

已实现字段集：

- `TypedPlatformSpawnAdmission`：
  `request_index`、`world_index`、`admitted`、`fail_closed`、
  `request_id`、`source_type_name`、`plan_id`、`capability_bundle_id`、
  `rejection_reason`、`errors`、`evidence_refs`。
- `TypedPlatformSpawnResult`：
  `request_index`、`world_index`、`entity_id`、`admitted`、`materialized`、
  `fail_closed`、`request_id`、`source_type_name`、`plan_id`、
  `capability_bundle_id`、`rejection_reason`、`errors`、`evidence_refs`。

提供给 C 的 helper 形态：

- `collect_typed_platform_spawn_evidence_refs(const TypedPlatformSpawnRequest&)`
  以首次出现顺序去重汇总 facade、bundle-template、bundle、plan-template、
  resolution、materialization 与 plan evidence；
- `make_typed_platform_spawn_admission(...)` 从 request 生成稳定 admission
  记录；
- `make_typed_platform_spawn_result(...)` 将 admission 转为 public result DTO，
  不要求当前流执行 materialization。

## Ordering Rule

`typed_platform_spawn_results` 的 public ordering contract：

1. 对每个输入
   `BatchWorldSetupRequest.typed_platform_spawn_requests[i]` 生成一个 result；
2. 维护 `typed_platform_spawn_results[i].request_index == i`，保持请求向量顺序；
3. typed request results 不重排、也不重新解释 legacy
   `BatchWorldSetupResult.entity_ids`；
4. `entity_ids` 继续作为 legacy `spawn_requests` 的 materialized result channel；
   typed request outcomes 从 `typed_platform_spawn_results` 消费；
5. 若 typed request 已 validation/admission 但尚未 materialize，也必须返回
   一条 result，且 `admitted=true`、`materialized=false`、`entity_id=0`。

这个规则让 `WP20-C` 可以稳定回填结果，而不用为 legacy/typed 两组 spawn
集合建立隐式 zip 对位关系。

## Fail-Closed Reasons

稳定 typed spawn rejection reasons 现在包括：

- `typed_platform_spawn_request_id_required`
- `typed_platform_spawn_source_type_name_required`
- `typed_platform_spawn_requires_capability_bundle`
- `typed_platform_spawn_capability_bundle_invalid`
- `typed_platform_spawn_requires_resolved_spawn_plan`
- `typed_platform_spawn_resolved_plan_invalid`
- `typed_platform_spawn_requires_typed_platform_request_kind`
- `typed_platform_spawn_requires_type_name_compatibility_path`
- `typed_platform_spawn_evidence_required`
- `typed_platform_spawn_world_index_out_of_range`
- `typed_platform_spawn_materialization_failed`

`WP20-B` 只声明 contract-level reasons。若 setup consume 在 request validation
之后拒绝，`WP20-C` 必须使用新的 world-index/materialization reasons。

## C/D 必须消费的精确接口

`WP20-C` 必须消费：

- `TypedPlatformSpawnAdmission`
- `TypedPlatformSpawnResult`
- `make_typed_platform_spawn_admission(std::uint64_t request_index, const TypedPlatformSpawnRequest& request)`
- `make_typed_platform_spawn_result(const TypedPlatformSpawnAdmission& admission)`
- `collect_typed_platform_spawn_evidence_refs(const TypedPlatformSpawnRequest& request)`
- `BatchWorldSetupResult.typed_platform_spawn_results`

`WP20-C` 的 fill rules：

- 保留 `request_index`、`world_index`、`request_id`、`source_type_name`、
  `plan_id`、`capability_bundle_id`；
- 仅在 validation/bridge admission 通过后设置 `admitted`；
- 仅在 compatibility-preserving spawn 成功后设置 `materialized`；
- 拒绝时设置 `fail_closed=true` 与稳定 `rejection_reason`，并可把 bridge/runtime
  诊断文本追加进 `errors`，但不能替换稳定 reason；
- `evidence_refs` 先保持 helper 产生的顺序，再把新的 bridge evidence 追加到后面。

`WP20-D` 必须暴露：

- `BatchWorldSetupResult.typed_platform_spawn_results`
- `TypedPlatformSpawnResult` 的全部 public 字段
- additive 默认行为：忽略新字段的 legacy callers 仍保持兼容。

## 建议验证

```bash
git diff --check
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/platform_spawn/test_typed_platform_spawn_contracts.py
bash tools/maintenance/cmo_env.sh python -m pytest -q tests/architecture/platform_spawn/test_typed_platform_spawn_contracts.py
```

## 交付

返回 touched files、DTO/result shape、ordering rule、tests run、blockers，以及
C/D 必须消费的精确 contract。
