# WP9-A DTO Promotion Batch 1

状态：`2026-05-20` complete / accepted WP9 并行流。

语言版本：

- 英文主文：[wp9_dto_promotion_batch1_cluster_20260520.md](wp9_dto_promotion_batch1_cluster_20260520.md)
- 中文辅文：`wp9_dto_promotion_batch1_cluster_20260520.zh.md`

输入：

- [WP9 contract and infrastructure closure](contract_infrastructure_closure_wp9_20260520.zh.md)
- [仿真系统架构设计](../../../plan/architecture/simulation_system_architecture_design.zh.md)
- [WP4 facade 对齐验收](../../review/archive/wp-acceptance/wp4_facade_alignment_acceptance_review_20260519.zh.md)
- [WP5 验证套件验收](../../review/archive/wp-acceptance/wp5_validation_harness_acceptance_review_20260519.zh.md)
- [WP7.5 训练路径 facade 桥接](../wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.zh.md)

## 1. 目的

WP9-A 把第一批 DTO 从已验收架构词汇晋升为 typed implementation surface。它关闭非结构化 reward/termination 与 observation-view 缺口，但不改变 ownership 规则。

本流覆盖：

- DTO-1 `RewardReport`
- DTO-2 `TerminationSpec`
- DTO-3 `ObservationBatchPacket` provenance metadata
- DTO-4 `ObservationViewSpec`

## 2. 必需 DTO 形状

| DTO | 必需字段 | Ownership 规则 |
|-----|----------|----------------|
| `RewardReport` | `fact_terms`、`shaping_terms`、`fact_snapshot_version`、`term_owner` | 仿真事实与实验 shaping 必须可分离。现有 string JSON 只能作为 compatibility text 保留，不能作为权威 typed shape。 |
| `TerminationSpec` | `reason`、`reason_source`、`snapshot_version` | `reason_source` 至少区分 `simulation`、`policy` 与 `orchestration`。 |
| `ObservationBatchPacket` metadata | `snapshot_version`、`barrier_id`、`source_time_s` | Metadata 描述采样来源，不是 policy-owned belief。 |
| `ObservationViewSpec` | `<major>.<minor>` `schema_version`、`required_fields`、`optional_fields`、checkpoint compatibility rule fields | Major mismatch 必须拒绝；minor-compatible optional-field drift 只有在 required fields 满足时才可加载。 |

## 3. 实施路线

推荐路线：

1. 在 `src/runtime/contracts/` 或 `src/runtime/facade/` 下添加或更新 C++ contract headers，避免导入 engine owner types。
2. 只在已验收 runtime output 已携带对应信息时添加 facade result fields。
3. 暴露 DTO 与字段的 Python bindings。
4. 添加 focused binding 与 facade-shape tests。
5. 保留 `reward_breakdown_jsons` 等 compatibility fields，直到后续迁移明确删除它们。

推荐写入范围：

- `src/runtime/contracts/*`
- `src/runtime/facade/runtime_facade_types.h`
- `src/runtime/facade/runtime_facade.cpp`
- `src/interfaces/python/bindings_runtime.cpp`
- `tests/runtime/bindings/*`
- `tests/runtime/facade/*`
- `tests/architecture/*`

冲突提示：

- `bindings_runtime.cpp` 与 `runtime_facade_types.h` 会与 WP9-B 共享。如果 WP9-B 正在并行运行，除非主线程把该 worker 指定为 integration owner，否则应停在 compile-ready contract patch，把共享 binding glue 留给 WP9-E。

## 4. 工作项

| 流 | 必需产出 | 预算 |
|----|----------|------|
| `WP9-A1 RewardReport` | Typed reward report struct、Python binding fields，以及证明 fact/shaping split 存在的测试。 | High. |
| `WP9-A2 TerminationSpec` | Typed termination reason/source struct、Python binding fields，以及 source label 测试。 | High. |
| `WP9-A3 ObservationBatchPacket Metadata` | Packet output 上的 provenance fields，以及证明 metadata 可从 Python 访问的测试。 | High. |
| `WP9-A4 ObservationViewSpec` | Versioned view spec struct/schema，以及 major/minor 行为的 compatibility tests。 | Xhigh. |

## 5. 非目标

- 不删除现有 compatibility reward strings。
- 不让 policy 或 learning code 拥有 simulation fact terms。
- 不在本流实现完整 observation encoder。
- 不改变 runtime stepping semantics。
- 如果 extension 未重建或未导入，不宣称 Python binding 通过。

## 6. 验收 Gate

WP9-A 满足以下条件后可进入 WP9-E：

1. DTO-1 至 DTO-4 都有 typed C++ surface，或有明确 blocked implementation note 与 owner。
2. Python bindings 暴露 typed fields，或记录准确 binding build/import blocker。
3. Focused tests 检查字段存在与默认行为。
4. 现有 execution 与 observation compatibility path 仍可工作。
5. 最终 notes 识别任何留给 WP9-E 的 shared binding glue。

## 7. 验证命令

```bash
git diff --check
pytest tests/runtime/bindings tests/runtime/facade tests/architecture
rg -n "RewardReport|TerminationSpec|ObservationViewSpec|snapshot_version|barrier_id|source_time_s" src tests docs/task/simulation_architecture/wp9_contract_infrastructure_closure
```
