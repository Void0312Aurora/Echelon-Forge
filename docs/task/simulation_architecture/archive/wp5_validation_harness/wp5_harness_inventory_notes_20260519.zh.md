# WP5-A Harness Inventory 笔记

状态：`2026-05-19` 首轮 inventory；仅文档产出，未修改 smoke suite。

语言版本：

- 英文主文：[wp5_harness_inventory_notes_20260519.md](wp5_harness_inventory_notes_20260519.md)
- 中文辅文：`wp5_harness_inventory_notes_20260519.zh.md`

输入：

- [WP5 validation harness](validation_harness_wp5_20260519.zh.md)
- [WP4 facade 对齐最终验收](../review/wp4_facade_alignment_acceptance_review_20260519.zh.md)
- [WP4-F 集成与交接](wp4_integration_handoff_20260519.zh.md)
- 当前 `tests/architecture/`、`tests/runtime/` 与 `tests/smoke/ci_smoke_suite.json`

## 一、目的

WP5-A 先把当前证据映射到五个 WP5 validation tier，暂不提升测试、暂不修改
runtime code，也不直接编辑 smoke suite。本文把可以立即推进的 gate 与仍依赖
runtime/facade metadata 的 gate 分开，供 WP5-B/C/D/E 分发使用。

## 二、五层覆盖盘点

| Validation tier | 当前覆盖 | 候选覆盖 | 缺口 / 下一步决策 |
|-----------------|----------|----------|-------------------|
| Design conformance | `tests/architecture/runtime_facade/test_layering.py` 覆盖 facade layering、escape hatch 文档、contract/facade header 隔离与 engine ownership 隐藏。`tests/architecture/build/test_cmake_target_readiness.py` 覆盖 CMake source grouping 与 mission episode detail ownership。`tests/runtime/engagement/test_engagement_contract_shape.py` 覆盖 engagement contract 的位置和字段形状。 | 保留两个 architecture 文件在 smoke 中。WP5-B 可决定是否把 `tests/runtime/bindings/test_bindings_engagement_surface.py` 与 `tests/runtime/bindings/test_bindings_command_surface.py` 纳入 design/boundary gate。 | 还没有 `StageNodeManifest` / `P0-P10` manifest conformance gate；当前 design 检查偏文件和 layering。 |
| Trace conformance | `tests/runtime/engagement/test_diagnostics_trace_contract.py` 覆盖 track、launch request/event、munition lifecycle、effects、damage 与 observation-version ancestry。`tests/runtime/engagement/test_facade_engagement_evidence_gates.py` 覆盖 producer、deferred slot、diagnostics piggyback 与 multi-world retagging。`tests/runtime/engagement` 已在 smoke suite 中。 | 将 `tests/runtime/facade/test_facade_step_evidence_gates.py` 作为 step/reward/termination/phase/observation evidence 的候选 gate。 | 当前 diagnostics 仍是 engagement piggyback trace；dedicated diagnostics facade、launch-request producer 与 munition-lifecycle producer 仍 deferred。 |
| Boundary conformance | `tests/architecture/runtime_facade/test_layering.py` 防止 raw `RuntimeFacade.runtime()` 与 `WorldBatchRuntime` 从 maintained batch/leader path 泄漏。`tests/runtime/facade/test_runtime_facade.py` 覆盖 setup、observation、engagement export、execution step 与 batch setup 的 request/result shell。`tests/runtime/engagement/test_launch_adapter_static_shape.py` 保证 weapon adapter 是 contract converter，而不是 live engine owner。 | `tests/runtime/test_agent_shim.py` 是 policy/agent boundary label 的 immediate candidate。若 WP5-B 想覆盖 setup adapter，可考虑 `tests/runtime/core/test_world_setup_compat.py`。 | broad direct `sim.*` policy-path ban 仍需 provenance label 与 allowlist；不能误伤 compatibility adapter。 |
| Information/belief leakage | `tests/runtime/test_agent_shim.py` 覆盖 `ObservationProvenance`、`AgentRole`、`ActionIntentCompat`、`CoordinationIntentCompat`、diagnostics-only world-truth label，以及非法 status / merge-policy 拒绝。`tests/runtime/facade/test_runtime_facade.py` 覆盖 typed observation packet export。 | WP5-D 确认 shim 词汇后，可把 `tests/runtime/test_agent_shim.py` 提升为 smoke 候选。直接 `sim.*` 检查应先做 docs-backed AST allowlist，而不是全局禁用。 | Runtime `ObservationBatchPacket` 缺少 typed source-time、barrier 与完整 `SnapshotVersion` provenance；`DecisionBelief` 还不是 C++ DTO。 |
| Replay/evidence conformance | 现有 trace tests 能检查当前 DTO 暴露的 deterministic id 与 ancestry 字段。`tests/runtime/facade/test_facade_step_evidence_gates.py` 覆盖 step result evidence shape。engagement smoke 已覆盖 packet export 与 diagnostics evidence。 | WP5-C 应用现有 seed、trace id、event id、observation packet version 与 facade request/result export 定义第一版 replay envelope gate。 | 还没有 deterministic replay comparison harness；WP2.5 的 event order、barrier、clock-domain merge 与 replay metadata 尚未完全进入 runtime DTO。 |

## 三、Smoke Suite 成员审查

当前 `tests/smoke/ci_smoke_suite.json` 成员：

| Smoke member | 当前 WP5 价值 | 建议 |
|--------------|---------------|------|
| `tests/architecture/runtime_facade/test_layering.py` | design/boundary 主证据，覆盖 facade layering 与 raw-runtime escape hatch containment。 | 保留，是 WP5-B 最强 immediate anchor。 |
| `tests/architecture/build/test_cmake_target_readiness.py` | design 证据，覆盖 source grouping 与 mission controller ownership。 | 保留。 |
| `tests/runtime/core/test_env_config.py` | runtime config smoke，不是 WP5 facade/evidence 主 tier。 | 保留为运行健康检查，但不要当作主要 WP5 tier proof。 |
| `tests/runtime/engagement` | engagement 目录覆盖 contract shape、launch adapter、diagnostics trace、facade evidence、live event capture 与 damage/adapter。 | 暂时保留；若成本过高，后续拆成 WP5-C focused subset。 |
| `tests/runtime/facade/test_runtime_facade.py` | maintained facade request/result 与 observation/engagement/execution evidence。 | 保留；若 WP5-E 需要，可单独加入 `test_facade_step_evidence_gates.py`。 |
| `tests/world_batch/test_world_batch_runtime.py` | 既有 batch runtime regression，位于 WP5-A 输入范围外。 | 保留为已有 smoke 基线，但只作为 runtime health 支撑。 |

高价值但尚未进入 smoke 的候选：

| Candidate | Tier 价值 | 提升说明 |
|-----------|-----------|----------|
| `tests/runtime/test_agent_shim.py` | Information/belief 与 boundary label。 | WP5-D 接受 shim 词汇后可提升；运行成本低。 |
| `tests/runtime/facade/test_facade_step_evidence_gates.py` | execution-step result 的 trace/evidence 与 boundary shape。 | WP4 已验收为 focused evidence，可作为 immediate candidate。 |
| `tests/runtime/bindings/test_bindings_engagement_surface.py` | engagement DTO binding 的 design/boundary 证据。 | 若 binding drift 成为 smoke 关注点，由 WP5-B/E 决定。 |
| `tests/runtime/bindings/test_bindings_command_surface.py` | command/action binding shape 的 boundary 证据。 | 等 WP5-B 判断 command binding shape 是否进入 maintained harness。 |
| `tests/runtime/core/test_world_setup_compat.py` | setup compatibility helper 的 boundary 证据。 | 仅当 setup adapter drift 成为 WP5-B 关注点时提升。 |

WP5-A 不建议直接提升：

| 范围 | 原因 |
|------|------|
| `tests/runtime/air_combat`、`tests/runtime/naval`、`tests/runtime/mission`、`tests/runtime/multi_agent`、`tests/runtime/link` 等大目录 | 是有价值的 domain regression，但不适合作为第一版 WP5 maintained validation harness。只提升有明确 tier ownership 的 focused gate。 |
| 依赖 observation、belief、replay 或 dedicated diagnostics metadata 的检查 | 这些 metadata 是 WP4 明确 deferred 的内容；应先记录，等 runtime 字段存在后再强制。 |

## 四、Immediate Gates

可以不重开 facade 语义、立即推进的 gate：

1. 保留 architecture layering checks，作为 WP5-B design/boundary anchor。
2. 保留 engagement contract、adapter、diagnostics trace 与 facade evidence tests，
   作为 WP5-C trace anchor。
3. 将 `tests/runtime/facade/test_facade_step_evidence_gates.py` 提升或记录为当前
   execution-step evidence gate。
4. 使用 `tests/runtime/test_agent_shim.py` 验证 passive `ObservationProvenance`、
   `AgentRole`、action intent 与 coordination intent label。
5. `RuntimeFacade::runtime()` / raw `WorldBatchRuntime` 只允许继续存在于已记录的
   compatibility 或 diagnostics surface。

## 五、Metadata-Dependent Gates

以下 gate 应等待对应 runtime/facade metadata 后再强制：

1. runtime-enforced `ObservationViewSpec` schema compatibility。
2. `ObservationPacket` 的 source `SnapshotVersion`、barrier、source-time 与
   clock-domain metadata。
3. typed `DecisionBelief` provenance 与 consumed observation/source version。
4. typed C++ `AgentRole`、`ActionIntentPacket`、`CoordinationIntentPacket`
   binding surface。
5. typed `RewardReport` fact/shaping attribution。
6. typed termination reason-source attribution。
7. 独立于 engagement piggyback evidence 的 dedicated `DiagnosticsTrace`
   facade query/export。
8. 基于 event order、seed、snapshot version、barrier 与 replay metadata 的
   deterministic replay comparison harness。
9. 显式 compatibility allowlist 之外的 broad direct `sim.*` policy-path AST ban。

## 六、后续分发建议

| 后续任务簇 | 建议 ownership | 避免重叠 |
|------------|----------------|----------|
| `WP5-B Design And Boundary Gates` | 负责 `tests/architecture/`、binding-surface 候选判断与窄 facade/boundary docs；强化 raw-runtime 与 facade-only gate。 | 在 WP5-D 定义 maintained label 和 allowlist 前，不做 broad direct `sim.*` ban。 |
| `WP5-C Trace And Replay Gates` | 负责 `tests/runtime/engagement/` 与窄 `tests/runtime/facade/` evidence fixture，覆盖 trace ancestry、step evidence 与 replay envelope presence。 | 暂不要求缺失的 WP2.5 replay metadata 作为 runtime DTO 字段；缺口先标 pending。 |
| `WP5-D Information And Belief Gates` | 负责 `tests/runtime/test_agent_shim.py` 提升建议，以及 docs-backed information/belief leakage checks；从 label 和 allowlist 开始。 | 不把 diagnostics/oracle fixture 误归类为 maintained policy input。 |
| `WP5-E Smoke Promotion And Docs` | 负责 `tests/smoke/ci_smoke_suite.json`、WP5 index sync、最终 validation command 与 smoke rationale。 | 等 WP5-B/C/D 稳定候选文件后再改 smoke；提升 smoke 时不改测试行为。 |

## 七、验收备注

本 inventory 已为每个 validation tier 给出当前覆盖、候选覆盖或显式 gap；
列出了 smoke candidate 与理由；区分了 immediate gates 和 metadata-dependent
gates；并为 WP5-B/C/D/E 划定了不重叠的 ownership 边界。
