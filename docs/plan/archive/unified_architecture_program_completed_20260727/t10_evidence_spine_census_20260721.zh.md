# T10 证据脊柱普查（2026-07-21）

语言：
- 英文正本：[t10_evidence_spine_census_20260721.md](t10_evidence_spine_census_20260721.md)
- 中文伴随：`t10_evidence_spine_census_20260721.zh.md`

文档种类：`reference`
生命周期：`maintained`
正本：`docs/plan/archive/unified_architecture_program_completed_20260727/t10_evidence_spine_census_20260721.md`
所有者：`unified architecture program workline`
最后核验：`2026-07-21`
基线提交：`8bd21d86`

状态：面向[统一架构计划](README.zh.md)的 T10 第一切片证据面普查。T10 的职责是"把
trace ids、packet ancestry、snapshot versions、replay gates 以及
worldline/counterfactual 面统一为一套由 T1 事件 schema 生成的证据架构"，主目标是
"任何维护中的 run 都可按构造重放且可比较"，关键风险是"证据面被测试与保留产物钉扎，
扩展必须是叠加式的"。本文件是描述性的普查登记（`reference`），非独立评审：它记录已核验
的基线状态，不携带评审结论。它不改变任何行为、不改动 `src/**`/`python/**` 代码；它清点
现状以便 T10 后续切片叠加式扩展。词汇以
[Simulation System Architecture Design](../../../architecture/standards/simulation_system_architecture_design.md)
的 SCAL Evidence Graph 面为准（第 2 节，Evidence Graph："Trace ids, packet ancestry,
snapshot versions, event order, and validation verdicts"）。

## 0. 方法与范围

- 在基线 `8bd21d86` 上普查了维护面（`src/**` 只读、`python/**`、
  `tools/maintenance/dto_schema/**`、`tests/**`）。
- 五类证据相关 DTO 族在 `tools/maintenance/dto_schema/schemas/` 下 schema 单源（T1，
  I26/I31）：`diagnostics_trace`、`track_packet`、`observation_batch_packet`、
  `engagement_event_packet`、`runtime_counterfactual_snapshot`、
  `runtime_worldline_comparison`、`runtime_experiment_ancestry`、
  `runtime_experiment_request/result`、
  `runtime_counterfactual_branch/restore_request/result`，外加 C++ 契约类型
  `src/runtime/contracts/counterfactual_replay_contract_types.h`。
- I44 落地的报告信封（`python/experiment/report_envelope.py`）刻意只携带通用元数据
  （`envelope_schema_version`、`tool_id`、`generated_at`、`git_rev`、`experiment_ref`、
  `payload`），明确把 trace/ancestry 机制留给 T10；下文将其作为边界标记列出，而非证据
  生产者。
- 零行为变更。未新增可选的只读架构测试：五类面已被既有测试钉扎（见各行）——多数入 smoke，
  但 packet `snapshot_version`/view-spec 事实仅由未入 smoke 的 `test_runtime_dto_contracts.py`
  钉扎——新增钉扎要么重复要么把 T10 必须替换的占位态固化。决策记录于第 4 节。

## 1. 证据面普查

### (i) Trace ids

| 方面 | 结论 |
|------|------|
| 现有词汇 | `DiagnosticsTrace`：`trace_id`、`parent_trace_id`、`chain_id`、`track_id`、`launch_request_id`、`launch_event_id`、`effects_event_id`、`damage_report_id`（均 `std::uint64_t`），加 `observation_packet_version`/`source_snapshot_version`（`std::uint64_t`）、`barrier_id`/`barrier_detail`、`source_node_id`/`export_node_id`。`EngagementEventPacket.trace_ids` 为 `std::vector<std::uint64_t>`。`TrackPacket`：`track_id`（`std::uint64_t`）、`correlation_policy`（`"unresolved"`）、`correlated_entity`/`has_correlated_entity`。 |
| 生产者 | Kernel：`simulation_kernel_engagement_event_store.cpp` 以 `trace.trace_id = next_engagement_event_id_++` 铸造（仅在单个 event-store epoch 内单调——`next_engagement_event_id_` 从 `1` 起，`clear()` 与 `reset_if_event_clock_rewound`（帧/时钟回退）都会把它重置为 `1`，故跨重置非全局单调——且取自 *engagement-event* id 空间）。Facade：`runtime_facade_packet.cpp` 构造 `DiagnosticsTrace{.trace_id = trace_id, .parent_trace_id = 0}`——导出路径上 `parent_trace_id` 硬编码 `0`——并循环 `request.trace_ids` 给导出的 observation trace 打标。`runtime_window_coordinator_selection_helpers.h` 在 `trace_ids` 为空时默认填 `[index + 1]`。 |
| 消费者 | 维护中的 Python 路径 `python/rl/runtime/world_batch/adapter.py` 设 `engagement_request.trace_ids = [1]`（占位常量），并不读取生产出的 `trace_id`/`chain_id`。无维护 run 为重放/比较消费该 trace 链。 |
| 测试钉扎 | `tests/runtime/engagement/test_diagnostics_trace_contract.py`（1 项，trace 链链接）；`tests/runtime/engagement/test_trace_replay_gates.py`（2 项，可重放排序 id、`chain_id == event_id`、版本元数据显式/分离）——两者入 smoke。另有 `tests/runtime/bindings/test_bindings_engagement_surface.py`、`tests/tools/test_target_geometry_damage_event_trace.py`。 |
| 与"按构造可重放"的差距 | Kernel 生产的 `trace_id` 仅在单个 event-store epoch 内单调（`clear()`/时钟回退会重置），但 facade 导出路径从不填 `parent_trace_id`（恒 `0`），故 trace *ancestry* 只有单层（仅 `chain_id == event_id`）；维护 Python 消费者以占位 `[1]` 打标，真实 kernel id 未端到端接线。`trace_id` 共享 engagement-event id 空间，与字符串 id 的 worldline/replay 面无链接。 |

### (ii) Packet ancestry（`InformationStateSource` / provenance）

| 方面 | 结论 |
|------|------|
| 现有词汇 | `InformationStateSource`（于 `policy_contracts.h`/`information_transform_contracts.h`），由 `make_information_state_source(information_state, source_label, maintained_status)` 基于枚举 `kPolicyInformationState*`（Truth/Sensed/Track/Picture/AgentObservation/DecisionBelief）、`kPolicySourceLabel*`、`kPolicyMaintainedStatus*`（Maintained/DiagnosticsOnly/AdapterProjection）构造。该类型化 provenance 字段出现六种不同命名：`ObservationBatchPacket.provenance`、`EngagementEventPacket.packet_provenance` + `diagnostics_provenance`、`ReplayFacadeProvenanceRef.information_state_source`、`WorldlineBranchMetadata.source_information_state`、`CounterfactualExperimentRequest.authority_information_state`。`RuntimeExperimentAncestry` 携带全字符串 `*_ref` 谱系（`setup_ref`、`generation_ref`、`replay_envelope_ref`、`branch_point_ref`、`generated_input_ref`、`counterfactual_request_ref`、`counterfactual_admission_ref`、`backend_profile_ref`、`fidelity_profile_ref`）加 `capability_refs`/`profile_observation_refs`/`evidence_refs` 与 `evidence_bridge_valid`/`fail_closed`/`rejection_reason`/`errors`。 |
| 生产者 | C++ facade：`run_counterfactual_experiment` 产出 `RuntimeExperimentAncestry`；每个 packet 通过 `make_information_state_source` 默认其 provenance。Python adapter 构造 `AgentRole.information_state_source`，`source_observation_versions = [str(input_snapshot_version)]`（合成字符串）。 |
| 消费者 | provenance 由测试与维护窗口授权路径强制（`run_maintained_window` 要求带标签 provenance + `AgentRole` 授权）。`python/scenario/compiler/generation_request.py` 把谱系词汇（`replay_envelope_ref`/`branch_point_ref`/`evidence_refs`/`deterministic_seed`）**平行**重实现为一套 Python 面。无维护 run 消费 `RuntimeExperimentAncestry`。 |
| 测试钉扎 | `tests/architecture/policy_execution/test_belief_and_read_side_boundaries.py`（13 项，WP11/WP12/WP24 provenance 词汇 + 维护 provenance 要求）；`tests/architecture/policy_execution/test_information_transformation_surface.py`；`tests/runtime/engagement/test_facade_engagement_evidence_gates.py`（smoke）；`tests/architecture/causal_runtime/test_experiment_evidence_bridge.py`（5 项）；`tests/runtime/facade/test_runtime_facade_counterfactual.py`（ancestry 断言）。 |
| 与"按构造可重放"的差距 | 同一类型（`InformationStateSource`）有六种字段名；ancestry 引用为自由 `std::string` `*_ref` 值，与其所指的 `_id` 无类型化链接（匹配靠字符串相等）；谱系词汇被实现两遍（C++ 契约类型与 Python `generation_request.py`）；无维护训练/评估 run 端到端产出 packet ancestry。 |

### (iii) Snapshot versions

| 方面 | 结论 |
|------|------|
| 现有词汇（两个被混用的概念） | **状态切片版本：** `snapshot_version`（`std::uint64_t`）于 `TrackPacket`、`ObservationBatchPacket`、`EngagementEventPacket`、`RuntimeCounterfactualSnapshot`；`source_snapshot_version`——`DiagnosticsTrace` 中为 `std::uint64_t`，`RuntimeWindowNodeExecutionRecord` 中为 `std::string`；`observation_packet_version`（`std::uint64_t`，`DiagnosticsTrace`）；`snapshot_version_ref`（`std::string`，`ReplaySnapshotRef`/`BranchPoint`）；`fact_snapshot_version`（`RewardReport`）、`snapshot_version`（`TerminationSpec`）；Python adapter `input_snapshot_version`（字符串，默认 `"obs:{world}:{entity}"`）。**格式/schema 版本：** `schema_version` = `std::string` `"1.0"`（`ObservationViewSpec`，由 `parse_observation_schema_version` 解析）vs `std::uint32_t`（`lethality_chain_header`、`kill_chain_runtime_facade`）；`envelope_schema_version` = `"1"`（报告信封）；`contract_version`/`request_version`（scenario 生成）；`evidence_schema_version`（effects vulnerability）。 |
| 生产者 | C++ facade 用 `next_snapshot_version(index)` 设 packet `snapshot_version`，其返回 `index + 1`——一个**每次导出都重置为 `1`** 的按导出批次序号（各导出循环重启局部 `next_snapshot_version = 1`；`runtime_facade_execution.cpp` 对每个 step index 同样处理），并非 run 全局单调计数；counterfactual snapshot 的 `snapshot_version` 是**固定常量** `kRuntimeCounterfactualSelectedSliceSnapshotVersion = 1`。Python adapter 产出**字符串**合成 `input_snapshot_version`。`ObservationViewSpec` 兼容性由 `evaluate_observation_view_checkpoint_compatibility` 基于解析后的 `schema_version` 计算。 |
| 消费者 | `ObservationViewSpec` checkpoint 兼容性引擎（major/minor 漂移）；测试。 |
| 测试钉扎 | `tests/architecture/runtime_facade/test_runtime_dto_contracts.py`（带版本的 view spec + packet `snapshot_version` 字段；**不在 smoke**）；`tests/runtime/engagement/test_trace_replay_gates.py`（track `snapshot_version > 0`、版本分离）；`tests/architecture/governance/test_dto_schema_freshness.py`（smoke，全部 schema 拥有的 DTO 重生成）。 |
| 与"按构造可重放"的差距 | `source_snapshot_version` 在一个 DTO 里是 `std::uint64_t`、另一个里是 `std::string`（类型不一致）；状态切片与格式-schema 两概念都用 `version` 后缀且无命名纪律（`observation_schema_version` 与 `observation_packet_version`/`snapshot_version` 易混）；replay 契约里的字符串 `snapshot_version_ref` 未绑定 packet 上的 `std::uint64_t` `snapshot_version`，故 replay envelope 无法按构造引用一个真正产出的 packet 版本。 |

### (iv) Replay gates

| 方面 | 结论 |
|------|------|
| 现有词汇 | `ReplayEnvelope`（`replay_envelope_id`、`run_id`、`episode_id`、`deterministic_seed` `std::uint64_t`、`source_time_s`、`snapshot_ref`、`barrier_ref`、`event_order_ref`、`facade_provenance_ref`、`snapshot_restore_supported`、`restore_support_boundary`）；`ReplaySnapshotRef.snapshot_version_ref`；`ReplayBarrierRef`（`barrier_id`、`barrier_sequence`、`barrier_detail`）；`ReplayEventOrderRef`（`sort_key`、`event_id`、`producer_node_id`）；`ReplayFacadeProvenanceRef`（`packet_ref`、`packet_kind`、`information_state_source`）；`BranchPoint`。验证器：`validate_replay_envelope`、`validate_branch_point`、`validate_branch_point_against_replay_envelope`、`make_branch_point_identity`、`ordered_replay_envelope_evidence_refs`、`validate_replay_envelope_for_snapshot_restore`。恢复边界 `kReplayRestoreSupportBoundary*`（`Unsupported`、`HostOwnedFacadeStateOnly`）；拒绝常量 `kReplayEnvelopeRejection*`/`kBranchPointRejection*`；排序键 `kDeterministicReplayEventOrderSortKey`。 |
| 生产者 | 维护 `RuntimeFacadeAdapter`/live-run 路径无 `ReplayEnvelope`/`BranchPoint` 生产者。裸 counterfactual facade **确实**在两个生产代码点构造 `ReplayEnvelope`——`replay_envelope_from_experiment_request()`（`runtime_facade_counterfactual.cpp`，从调用方的 experiment/branch 请求）与 `runtime_counterfactual_restore_boundary_for_snapshot()`（从 `RuntimeCounterfactualSnapshot`）——但它们是从 request/snapshot 字段拼装的**合成**信封，并非从维护 run 的真实 packet 证据（packet `snapshot_version` + event order + provenance）构造。测试 fixture 也以手写字符串 id 构造信封。 |
| 消费者 | C++ 验证器（fail-closed）；`python/scenario/compiler/generation_request.py` 要求 `replay_envelope_ref` 或 `branch_point_ref`。无维护 Python run 构建或消费 `ReplayEnvelope`。 |
| 测试钉扎 | `tests/architecture/causal_runtime/test_replay_envelope_contracts.py`（7 项，WP15：必需面、有效 fixture 校验、稳定的 `make_branch_point_identity`、恢复限于 `host_owned_facade_state_only`、缺字段 fail-closed、非法 provenance/event order）；`tests/architecture/causal_runtime/test_counterfactual_admission.py`（6 项）；`tests/architecture/structural_boundaries/test_counterfactual_structure_boundaries.py`（3 项）；`tests/runtime/facade/test_runtime_facade_counterfactual.py`（恢复拒绝）。`tests/runtime/engagement/test_trace_replay_gates.py` 与 `test_facade_engagement_evidence_gates.py` 入 smoke；WP15 causal-runtime 的 C++ 片段测试不在 smoke。 |
| 与"按构造可重放"的差距 | replay gate 是契约验证器（fail-closed）；两个裸 facade 生产者从 request/snapshot 字段合成信封，且维护路径上没有任何东西从真实 run 构造 `ReplayEnvelope`，故这些门守护的是一个非从真实 run 按构造产出的面。确定性仅由 `deterministic_seed` 表达；run 路径上无维护的同种子逐字节重放门。快照恢复分三层：WP15 `WorldlineBranchMetadata` 契约仅元数据（`metadata_only = true`、`snapshot_restore_supported = false`、边界 `unsupported`）；`RuntimeFacade` 恢复路径**确实**写回 host-owned facade kinematics（`restore_counterfactual_entity` 调用 `try_set_entity_kinematics`），限于 `host_owned_facade_state_only`；resident-state / exact-GPU / full-clone 恢复被显式拒绝。 |

### (v) Worldline / counterfactual

| 方面 | 结论 |
|------|------|
| 现有词汇 | `RuntimeCounterfactualSnapshot`（`worldline_id`、`parent_worldline_id`、`deterministic_seed`、`world_index`、`entity_id`、物理量、`snapshot_version`、`barrier_id` `"counterfactual_selected_slice"`、`fidelity_profile_id`、`provider_family`、`selected_stage_node_id`、`cadence_reason`、`evidence_refs`）；`RuntimeWorldlineComparison`（`comparable`、`comparison_id`、`parent_worldline_id`、`branch_worldline_id`、`barrier_id`、增量、`evidence_refs`）；schema DTO `RuntimeCounterfactualBranch/Restore_Request/Result`、`RuntimeExperiment_Request/Result`、`RuntimeExperimentAncestry`；C++ `WorldlineBranchMetadata`、`CounterfactualExperimentRequest`、`CounterfactualAdmissionResult`、`ExperimentEvidenceBridgeRecord`。 |
| 生产者 | C++ facade：`run_counterfactual_branch`、`restore_counterfactual_snapshot`、`run_counterfactual_experiment`。若干 id **在运行时生成**：`worldline_id` 为空时默认 `worldline:runtime:<world_index>:<entity_id>`（`snapshot_counterfactual_entity`），experiment 路径上默认 `worldline:baseline`/`worldline:branch`；`comparison_id` 生成为 `counterfactual:selected_slice[:<branch_point_id>]`；`replay:facade:<worldline_id>` 信封 id 及其 run/episode/event/packet ref 在 `runtime_counterfactual_restore_boundary_for_snapshot` 中从 snapshot 派生。仅部分请求字段（`replay_envelope_id`、`branch_point_id`，以及提供时的 `parent_worldline_id`/`branch_worldline_id`）仍为调用方手写字符串（如 `"worldline:wp17f:baseline"`、`"replay:wp17f:0001"`）。 |
| 消费者 | 仅 C++ 测试 + Python 绑定。在 `python/**` 中，唯一的维护引用是 `python/rl/policy_algo/grouped_stopping.py` 里的路由标签 `ROUTE_COUNTERFACTUAL_REPLAY = "counterfactual_replay"`（仅名字）加 scenario 生成谱系 ref。counterfactual/worldline API **不**经维护 `RuntimeFacadeAdapter` 暴露；它在裸 `ef_py.RuntimeFacade` 上。 |
| 测试钉扎 | `tests/runtime/facade/test_runtime_facade_counterfactual.py`（branch/restore/experiment，smoke）；`tests/architecture/causal_runtime/test_worldline_branch_metadata.py`（5 项）；`test_counterfactual_admission.py`（6 项）；`test_experiment_evidence_bridge.py`（5 项）；`tests/architecture/structural_boundaries/test_counterfactual_structure_boundaries.py`（3 项）；`tests/runtime/facade/test_runtime_facade_core.py`。 |
| 与"按构造可重放"的差距 | 部分 id 由 facade 生成（`worldline_id` 默认值、`comparison_id`、从 snapshot 派生的 `replay:facade:*` ref），但 `branch_point_id` 与请求的 `replay_envelope_id` 仍为调用方提供的字符串，且无跨 run 稳定 id 方案，故按构造可比较性仅对生成的 id、且仅在单次裸 facade 调用内成立。整个面与维护 Python run 路径脱钩（adapter 不暴露）。恢复写回 host-owned facade kinematics（非仅元数据），限于 `host_owned_facade_state_only`，resident/gpu/full-clone 被拒。 |

## 2. 词汇对齐清单（只建议，未实施）

每条列出五类面之间的不一致与一条**叠加式**对齐建议。本切片不实施任一条；后续 T10 切片须
在第 3 节的 additive-only 红线下实施。

| ID | 不一致 | 叠加式对齐建议 |
|----|--------|----------------|
| VA-1 | **id 类型分裂。** "用于重放/诊断的身份"在 trace/engagement/packet 面是 `std::uint64_t`（`trace_id`、`parent_trace_id`、`chain_id`、`track_id`、`*_event_id`），在 worldline/replay/experiment 面是 `std::string`（`worldline_id`、`replay_envelope_id`、`branch_point_id`、`comparison_id`、`run_id`、`episode_id`、`event_id`）。SCAL 命名了一个 `source_id`（"用于重放与诊断的稳定生产者 id"），但没有单一类型实现它。 | 声明一份 schema 单源的证据 id 词典，记录两种表示及其映射（或加一个桥接 ref 字段）。**不**改现有字段类型。 |
| VA-2 | **snapshot 版本名 + 类型（当前无单调计数）。** 状态切片版本在 packet 上是 `snapshot_version`（`uint64`），在 `DiagnosticsTrace` 是 `source_snapshot_version`（`uint64`）、在 `RuntimeWindowNodeExecutionRecord` 是 `source_snapshot_version`（`std::string`）、还有 `observation_packet_version`（`uint64`）和 `snapshot_version_ref`（`string`）。同概念，≥3 名、2 型。注意**当前不存在单调 `snapshot_version` 计数**：packet `snapshot_version` 是按导出序号（`index + 1`，每次导出重置），counterfactual snapshot 固定为 `1`。 | 先记录当前无单调计数；再保留 `snapshot_version` 表示（待建的）`uint64` 单调计数、`snapshot_version_ref` 表示字符串 ref；把 `RuntimeWindowNodeExecutionRecord.source_snapshot_version` 视作独立的节点源标签，或叠加式新增一个类型化 `uint64`。不改型。 |
| VA-3 | **版本概念混用。** 格式/schema 版本（`schema_version` `"1.0"`/`uint32`、`envelope_schema_version`、`contract_version`）与状态切片版本（`snapshot_version`）都用 `version` 后缀；`observation_schema_version`（格式）与 `observation_packet_version`/`snapshot_version`（状态切片）易混。 | 文档化区分：`*_schema_version`/`*_contract_version` 表格式，`*_snapshot_version`/`*_packet_version` 表状态切片。不改字段。 |
| VA-4 | **provenance 字段名。** `InformationStateSource` 被命名为 `provenance` / `packet_provenance` / `diagnostics_provenance` / `information_state_source` / `source_information_state` / `authority_information_state`。 | 对 `InformationStateSource` 类型字段采用文档化的 `<role>_provenance` 约定；保留现名，仅对新字段应用约定。 |
| VA-5 | **无类型 ancestry ref。** 谱系以自由 `std::string` `*_ref` 字段携带，与其所指 `_id` 无类型化链接；匹配靠字符串相等（`make_branch_point_identity` 拼成字符串）。 | 保留字符串 ref（它们是序列化形式），但加一份 schema 声明的"ref → id-kind"注册表以对已知 id 类别校验 ref；该新校验须**版本化或 opt-in**，因为对既有/旧输入强制新校验会拒绝先前被接受的 ref，故非叠加式。 |
| VA-6 | **平行谱系词汇。** C++ `counterfactual_replay_contract_types.h`（`ScenarioGenerationRequestMetadata`）与 Python `generation_request.py`（`ScenarioGenerationRequest`）都实现了 `replay_envelope_ref`/`branch_point_ref`/`evidence_refs`/`deterministic_seed` 谱系。 | 让**共享 schema 作为单一 owner**，由它（经 T1 机制）**同时生成 C++ 与 Python 两面**，而非手工维护两套平行、也非把 Python 做成 C++ 源的投影；叠加式，保名。 |
| VA-7 | **barrier-id 默认词汇。** `barrier_id` 一律 `std::string`，但默认不同：`"export"`（trace/observation/engagement packet）、`"counterfactual_selected_slice"`（counterfactual snapshot/comparison）、`"window_commit"`（`ReplayBarrierRef`）。 | 文档化 barrier-id 枚举/注册表（`export`/`window_commit`/`counterfactual_selected_slice`/...）；不改默认。 |
| VA-8 | **`trace_id` 共享 engagement-event id 空间；`parent_trace_id` 未填。** `trace_id` 从 `next_engagement_event_id_` 铸造，facade 导出上 `parent_trace_id` 硬编码 `0`。 | 文档化当前共享；若需独立 trace ancestry，则新增专用 trace-id 分配器并填 `parent_trace_id`——但注意更换分配器或填充 `parent_trace_id` 会**改变序列化值**（保留产物哈希与被钉扎的测试），故须以新生产者/版本化路径落地以保留既有兼容面。 |

## 3. 后续切片建议顺序与 additive-only 红线

本普查之后的 T10 切片建议顺序（各消费 T1 事件 schema；各为叠加式）：

1. **冻结普查 + 词汇（本切片）。**
2. **叠加式证据词典。** 一份 schema 单源的 id/版本词典（VA-1、VA-2、VA-3），映射
   `uint64` 与 `string` id 空间及两个版本概念——文档 + schema 元数据，不改字段。
3. **先建立专用生产者（切片 4 的前置）。** 当前不存在单调 snapshot producer
   （`next_snapshot_version` 返回 `index + 1` 且每次导出重置；counterfactual snapshot
   固定为 `1`），也无专用 trace-id 分配器（`trace_id` 共享 `next_engagement_event_id_`，
   被 `clear()`/时钟回退重置，且 `parent_trace_id` 未填）。叠加式**新增**一个 run 全局
   单调 snapshot-version 生产者（VA-2）与一个专用 trace-id 分配器（VA-8），保留既有字段；
   因其改变序列化值，须以新生产者/版本化路径落地。
4. **把真实 trace ids / snapshot versions 接入维护 run**（依赖切片 3）。用 facade 背后
   真实产出的值替换 adapter 占位 `trace_ids = [1]` 与合成 `input_snapshot_version`，由既有
   `test_trace_replay_gates.py` 守护。
5. **面向维护 run 的 replay-envelope 生产者**（依赖切片 3–4）。当前已有两个合成生产者
   （`replay_envelope_from_experiment_request`、
   `runtime_counterfactual_restore_boundary_for_snapshot`），但均非从真实 run 构造；从维护
   run 构造 `ReplayEnvelope`（真实 packet `snapshot_version` + event order + provenance），
   使 `validate_replay_envelope` 运行在真实证据上而非合成/fixture 输入。
6. **端到端填充 packet ancestry。** 设置 `parent_trace_id`（经切片 3 的分配器）与 `*_ref`
   谱系；把 Python 谱系词汇统一为共享 schema 投影（VA-4、VA-5、VA-6）。
7. **经维护 adapter 暴露 worldline/counterfactual 比较**（opt-in），消费 T1 engagement
   schema。

**additive-only 红线**（T10 关键风险：面被测试与保留产物钉扎）：

- 任何现有证据字段不得改名、改型、删除或重排。成员顺序是 ABI；JSON codec 别名与保留产物
  哈希钉扎序列化形状；第 1 节的测试钉扎该面。
- 新证据以新字段 / 新 DTO / 新生产者到来，配重生成 freshness 门
  （`tools/maintenance/dto_schema/generate.py --check`）；行为可能漂移处配内嵌参照 parity；
  兼容壳保留至 T7 最终残余审计有意退役。
- 词汇对齐（第 2 节）以文档加新叠加字段交付，绝不对被钉扎面做原地编辑。

## 4. 只读架构测试决策

切片预算允许至多新增一个只读架构测试以钉住一个原本无守护的证据面。未新增，原因有二：

1. **已被钉扎。** 五类面各有既有钉扎（第 1 节），含入 smoke 的
   （`test_diagnostics_trace_contract.py`、`test_trace_replay_gates.py`、
   `test_facade_engagement_evidence_gates.py`、`test_facade_step_evidence_gates.py`、
   `test_runtime_facade_counterfactual.py`、`test_dto_schema_freshness.py`）与全面但未入
   smoke 的 `test_runtime_dto_contracts.py`。
2. **避免固化占位。** 最"无守护"的事实恰是 T10 必须替换的占位（adapter `trace_ids = [1]`、
   合成字符串 `input_snapshot_version`、调用方提供的 worldline id）。钉住它们会妨碍叠加式
   迁移而非保护它。

这样本切片保持纯普查 + 文档，符合零行为变更纪律。

## 5. 验证

- 基线（本文档之前）维护 smoke：`8bd21d86` 上 `446 passed, 45 subtests passed`。
- 在不做 `clusters --write` 注册表刷新（按切片纪律刻意延后）的情况下新增此双语文档对，会让
  入 smoke 的
  `tests/architecture/governance/test_document_link_audit.py::test_repository_bilingual_registry_matches_the_maintained_surface`
  标记这个未注册的新对。注册表刷新与迭代台账登记不属本文件范围（SCAL 普查先例做了同样的范围
  裁定）。确切的 smoke 前后数字在迭代台账条目中报告。

## 相关权威

- [统一架构计划](README.zh.md)（T10 轨道定义与风险）
- [Simulation System Architecture Design](../../../architecture/standards/simulation_system_architecture_design.md)（SCAL Evidence Graph 面）
- [SCAL 一致性普查（2026-07-20）](scal_conformance_census_20260720.zh.md)（T0 普查先例与格式）
- [T6 残差台账（2026-07-20）](t6_residual_ledger.zh.md)
- [仓库整合计划](../repository_consolidation_completed_20260729/README.zh.md)（迭代台账与协议）
