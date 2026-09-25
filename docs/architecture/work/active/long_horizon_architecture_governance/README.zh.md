# 长期架构治理

状态：`2026-09-24`，长期架构治理计划处于 active；P0 authority/baseline、P1
target-architecture 决策、完整的 P3-A/P3-B/P3-C contract、authority-envelope、
ledger 与 compatibility foundation，以及 P4-A dark/shadow host lifecycle 已在
独立复核后接受。P4-B dark/shadow candidate implementation 与独立综合复核已完成；P4-C 首个 build-tree/internal candidate 任务已通过 candidate-scope 独立复核并被接受，尚未获得 production acceptance。
P2-A 已有 manifest-level lifecycle baseline 实现，P2-B 也已有首个可重复的本地 sustainability baseline；P5-D 的有界 maintained caller parity 已完成，并有独立可执行门禁记录于
[parity evidence](evidence/p5d_maintained_caller_parity_20260925.md)。代表性 release cadence、production caller
cutover、production rollback-window operation、rebuild retirement 与 P6-P8 仍开放；尚无 production truth 发布或 production cutover 被接受。maintained 合同调用方迁移、process-resync、
mandatory production-state release/receipt binding、ArtifactLedger durable rollout controller
以及首个 operations drill 证据见
[P5-D caller migration evidence](evidence/p5d_facade_caller_migration_20260923.md) 与
[process-resync evidence](evidence/p5d_process_restart_admission_resync_20260923.md)、
[release/receipt binding evidence](evidence/p5d_release_receipt_binding_20260923.md) 和
[production binding and operations evidence](evidence/p5d_production_binding_operations_20260923.md) 与
[SQLite rollout controller evidence](evidence/p5d_sqlite_rollout_controller_20260923.md)，
以及 [real process/package rollback evidence](evidence/p5d_real_process_package_rollback_20260923.md)。
三轮 supported-row SLO/adoption 测量见
[measurement evidence](evidence/p5d_supported_row_measurement_20260923.md)。
真实 admission-bound facade VecEnv 的 reset/step 检查见
[VecEnv canary evidence](evidence/p5d_facade_vecenv_canary_20260923.md)。
完整的本地 durable rollout lifecycle/retention 检查以及独立的 fail-closed
rebuild-retirement gate 见
[lifecycle controller evidence](evidence/p5d_sqlite_rollout_controller_20260923.md)
与 [rebuild retirement gate evidence](evidence/p5d_rebuild_retirement_gate_20260924.md)。
分支内 P5-D 门禁汇总见
[local gate matrix](evidence/p5d_local_gate_matrix_20260925.md)。
cutover 前的 rebuild-unreachability inventory（维护生产调用方与 Python
binding 均为零，但尚未退役 rebuild）见
[rebuild evidence](evidence/p5d_rebuild_unreachability_20260923.md)。
首个 P2-B control/cost/retrieval baseline 见
[sustainability evidence](evidence/p2b_sustainability_baseline_20260923.md)。
distinct-package cadence follow-up 见
[cadence evidence](evidence/p2b_release_cadence_followup_20260924.md)，代表性
cadence 仍开放。

P6-A 测试 authority baseline 记录于[派生审计包]
(evidence/p6a_test_authority_audit_20260924.md)：architecture tier manifest
现在声明 owner、failure audience 与 execution strategy，派生报告保留
source-scan residual，并拒绝 orphan、stale、duplicate 与跨 tier assignment。
Native CTest 的 25 个条目现在均暴露 primary lane label。P6-A 的替换/退役证据
与 P6-B workflow lane 工作仍开放。

语言：

- 英文规范页：[README.md](README.md)
- 中文配套页：`README.zh.md`

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/README.md`
Owner: `cross-domain architecture`
Last verified: `2026-09-24`

相关权威：

- [架构 owner](../../../README.zh.md)
- [仿真系统架构设计](../../../standards/simulation_system_architecture_design.zh.md)
- [Runtime workflow 与 contract 基线](../../../standards/runtime_workflow_and_contract_baseline.zh.md)
- [Runtime composition 基线](../../../standards/runtime_composition_baseline.zh.md)
- [已归档 Cordis composition 计划](../../archive/cordis_simulation_composition_kernel/README.zh.md)
- [文档生命周期规范](../../../../engineering/documentation/standards/document_lifecycle_policy.zh.md)
- [子项目创建规范](../../../../engineering/automation/rules/subproject_creation_standard.zh.md)
- [Subagent 使用规范](../../../../engineering/automation/standards/subagent_usage_policy.zh.md)
- [独立 P0-B 计划审查（英文）](../../../reviews/long_horizon_architecture_governance_plan_review_20260825.md)
- [P1-A host lifecycle 与 episode authority 决策（英文）](decisions/p1a_host_lifecycle_and_episode_authority_decision_20260825.md)
- [P1-B plan 与 RunReceipt authority 决策（英文）](decisions/p1b_plan_and_run_receipt_authority_decision_20260825.md)
- [P1-C rollout、operations 与 security 决策（英文）](decisions/p1c_rollout_operations_and_security_decision_20260825.md)
- [独立 P1 architecture review（英文）](../../../reviews/long_horizon_architecture_governance_p1_review_20260825.md)

## Purpose

本计划改变 Echelon Forge 演进 runtime 架构的方式，以及架构控制被创建、提升、
续期和退役的方式。它不是一次仓库清理 wave，不得被重新定义成短期测试、CI 或
文档减量项目。

长期终态是：由一份闭合 executable plan 构造不可变的 admitted kernel；
replacement 归属于 host-level 生命周期边界；production binding 在物理上只能依赖
facade contract；治理控制必须退役或续期，而不是在每次迁移后永久累积。

## Current State

| 区域 | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| Runtime composition | 已接受有界默认 CPU-exact 基线 | [runtime composition standard](../../../standards/runtime_composition_baseline.zh.md) 与 [`SimulationKernel`](../../../../../src/core/engine/simulation_kernel.cpp) | 已接受构造和证据不能证明 kernel 内 rebuild 存在生产消费者 |
| Composition replacement | 已实现，但战略方向未裁定 | `rebuild_world_composition`、mutation barrier、raw-world quarantine、scope generation 与 handover 机制 | 当前没有 maintained 非测试 caller 或 binding 要求原地 kernel rebuild |
| Runtime 边界 | facade 方向已接受；compatibility surface 仍存在 | [runtime facade guards](../../../../../tests/architecture/runtime_facade/test_runtime_escape_hatches.py) | source scan 能描述边界，但不能让越界在物理上不可表示 |
| Contract 与证据链 | 已覆盖 accepted 默认 profile | request、catalog lock、projection、requested/resolved manifest、provenance、parity 与 closure artifact | 中间迁移 artifact 仍是永久治理输入 |
| Public/runtime authority boundary | P3-A/P3-B/P3-C 与 P4-A accepted；P4-B 已通过独立复核；P4-C candidate-scope 任务已接受 | [`ef_runtime_contracts`](../../../../../include/echelon_forge/runtime_contracts/runtime_identity.h)、[`RuntimeHostCandidate`](../../../../../src/runtime/host/runtime_host_candidate.h)、[P4-B candidate](p4b_state_transfer_candidate_20260830.md)、[P4-C candidate seam](p4c_internal_candidate_seam_20260915.md)、12-row owner adapters、authority/ledger schema、exact vector、non-production ArtifactLedger simulator、fresh Windows/MSVC native gate 与 [P4-B 独立审查](../../../reviews/long_horizon_architecture_governance_p4b_review_20260831.md) | P4-A/B/C 仍仅 dark/shadow；完整 maintained facade parity 与 P5-B/P5-D production durability、authenticity、activation、cutover 仍受 gate 约束 |
| 测试与 CI 治理 | CI smoke 已验证为绿；P6-A authority baseline 与 P7-A retention 检查已有聚焦证据；完整 hosted governance/CI 验收未完成 | [CI smoke suite](../../../../../tests/smoke/ci_smoke_suite.json)、[governance audit suite](../../../../../tests/suites/governance_audit_suite.json)、[P6-A 派生审计](evidence/p6a_test_authority_audit_20260924.md) 与 [retention authority](../../../../engineering/documentation/reference/retention_authority.json) | source-scan residual 与 hosted CI/branch-protection 证据仍开放；archive 路由受 P7-A authority 约束 |
| 文档生命周期 | P7-A retention authority baseline 已实现 | [P7-A retention 证据](evidence/p7a_retention_authority_20260924.md)、[文档生命周期规范](../../../../engineering/documentation/standards/document_lifecycle_policy.zh.md)、[retention authority](../../../../engineering/documentation/reference/retention_authority.json)、archive gate 与当前 architecture archive | 仅登记的 Cordis owner-local archive 可保留；其他 archive 路径禁止，退役材料使用 owner ledger/Git 历史 |

## Scope

范围内：

- 选择并实现长期 immutable-kernel 与 host-owned replacement 架构；
- 定义 host lifecycle state machine、publication linearization point、
  epoch/fencing/lease、唯一 episode-barrier authority、drain/reclamation 规则和完整
  state-transfer census；
- 把 runtime composition interchange 与 run evidence 收敛到最小的耐久 contract 链；
- 通过 single-writer、bounded dual-reader、canary/shadow、rollback window 与
  backout semantics 支持 producer/native/wheel 的 mixed-version rollout；
- 用 CMake target、header visibility、package、type、runtime contract 与行为边界
  替代 source-text 边界治理；
- 为架构控制建立生命周期，包括 owner、检测目的、续期、到期、替代与退役；
- 按反馈目的重新设计测试和 CI lane，同时不削弱 native、facade、wheel、replay、
  parity 或 CPU-canonical correctness；
- 在保留可复现 provenance 的同时，把历史 acceptance 与 evidence 移出永久执行权威；
- 迁移既有 caller、compatibility 路径、文档和 evidence，且不创造第二个 runtime truth。
- 定义受支持 platform/process topology、运营 owner、lifecycle SLO、adoption
  telemetry，以及 multi-process/external host 的 fail-closed activation gate。

范围外：

- 削弱 deterministic CPU-exact execution，或在没有独立提升证据时把 CUDA 作为
  canonical；
- 在没有 authenticity、compatibility、state-transfer 与 failure-containment 规则时，
  接受外部 plugin、remote catalog 或 live reload；
- 只为改善仓库比率而删除 behavior、packaging 或 native admission evidence；
- 声称文档、inventory 或 source-scan 通过就实现了目标架构；
- 因核心迁移困难而用 cleanup-only 或短期交付计划替代长期目标。

## Architecture Decision

目标方向如下：

1. `SimulationKernel` 从不可变 `ResolvedCompositionPlan` 构造，在生命周期内
   不原地改变会影响 truth 的 composition。
2. host-level composition owner 具备显式 state machine、共用单一 CAS 的 initial /
   replacement / checkpoint-recovery publication、terminal shutdown、publication 前
   quiescence 与 final-state transfer fence、monotonic generation、fenced
   world/entity/request/result ref、共同线性化的 instance lease、drain/quarantine budget
   和 deterministic reclamation。Native simulation 拥有 authoritative episode barrier；
   Python mirror 通过 versioned handshake 参与。
3. Versioned resolved-plan contract shell 与 engine-independent public-contract target
   必须先于 truth-changing host cutover。此前 host 只允许 dark/shadow，不能基于临时
   JSON 或 engine-owned DTO 发布 production seam。
4. 耐久 execution artifact 收敛为 experiment request、一份闭合 resolved executable
   plan 与 native per-run receipt；正交的 ReleaseManifest、RolloutDecision 和
   StateCheckpoint authority 各有唯一 writer/validator。Catalog、projection、generated
   diagnostics/metadata 与 migration artifact 具备显式派生、过渡或历史路由。
5. Canonical JSON/detached-digest contract 与 versioned rollout authority 管理 N/N-1
   producer、native、stored-plan 与 wheel：one writer、bounded reader、非 authoritative
   shadow、唯一 production-canary cutover decision、rollback checkpoint、kill switch
   与量化 backout trigger。
6. Per-run `RunReceipt` 绑定准确 plan bytes/hash、executable/module/wheel digest、
   build/toolchain/ABI/platform、scenario/content/config/seed、world/episode/run identity、
   lifecycle receipt、determinism profile、result hash 与 completion state。Durable journal
   admission 先于 truth mutation；recovery/finalization 具备 fencing，rollback artifact
   在 production cutover 前已证明可恢复。
7. Maintained Python、RL、visualization 和 host 路径只通过 runtime contract 与 facade
   target 链接。Raw engine access 被隔离到 diagnostics-only build/package surface。
8. 稳定 invariant 优先由 compiler、target、type、runtime contract 与 behavior 执行。
   Source scan 的 lifecycle metadata 附着在既有 gate declaration 上。到期 migration
   control 不得静默续期：最多一次 bounded renewal，并要求独立 sponsor 和 forced
   removal date；否则退役，或重新 admission 为 permanent semantic control。
9. Accepted topology/platform matrix 必须显式。Unsupported multi-process fail closed；
   activation 需要 single-writer leader fencing、persistent epoch、crash recovery、
   authentication/authorization、artifact authenticity、quota 和同一 native owner。
10. Normative standard 与当前 operator/developer 入口保持 maintained；已结束的 review
   packet、dispatch record 与 acceptance evidence 迁入已准入的 review、git ledger、
   release 或 CI artifact retention surface。

阶段可以调整实现顺序，但必须保留这些结果。独立审查只有在替代机制达到相同的
长期 authority、compatibility 与 lifecycle 结果时，才能替换既定机制。

## Phase Plan

| 阶段 | 目标 | 进入条件 | 退出条件 | 状态 |
| --- | --- | --- | --- | --- |
| `P0 Authority And Baseline` | 建立已核验 source、control、CI、evidence、ownership 基线及独立审查。 | 用户授权与最新 `origin/main` | 项目包、度量、审查 finding 与 owner index 保持当前 | accepted |
| `P1 Target Architecture` | 固定 lifecycle、episode authority、versioning/rollout、platform/process topology、contract chain、boundary 与 control lifecycle 决策。 | P0 evidence accepted | 决策包含 compatibility、rollback、operations、storage 与 security activation 路径并通过独立审查 | accepted |
| `P2 Control Lifecycle` | 将每个架构控制分类为 permanent、renewable、migratory 或 evidentiary，并明确 owner 与退役。 | P1 术语固定 | 既有控制完成分类，migration control 具备可执行退出条件 | P2-A 基线；P2-B 首个基线与 distinct-package follow-up；代表性 cadence 开放 |
| `P3 Contract And Public Boundary Foundation` | 在 host cutover 前落地 canonical authority envelope、plan/release/rollout/checkpoint shell、engine-independent DTO target、ledger foundation 与初始 visibility。 | P1 accepted | transitional adapter 单一 owner，host 可使用最终 public type/storage 且不发布第二 truth | P3-A/P3-B/P3-C accepted |
| `P4 Host Lifecycle And Immutable Kernel Candidate` | 实现 fenced host replacement、唯一 episode authority、完整 state transfer 与 dark/shadow immutable candidate path。 | P3 contract/boundary foundation 稳定 | candidate path 已 state-complete 且 fenced，但不得成为 production truth 或退役 production rebuild | P4-A accepted；P4-B 已通过独立复核；P4-C candidate-scope 任务已接受；完整 maintained facade parity 与 P5 仍开放 |
| `P5 Plan, Evidence, Binding, And Production Cutover` | 闭合 executable plan，引入完整 RunReceipt，完成 facade/diagnostics packaging，再执行唯一 production cutover/backout 并退役 rebuild。 | P4 candidate 通过 dark/shadow | Cordis/native/facade/wheel 使用同一 plan；supported caller 只切换一次且有 rollback evidence，rebuild 失去 production authority | planned |
| `P6 Test And CI Architecture` | 按独立 failure audience 对齐 fast、qualification、nightly、release 与 research lane。 | P2 control class 与 P5 boundary 可用 | permanent gate 有具名检测价值，migration scan 已消失或带到期约束 | P6-A authority baseline；替换/退役证据与 P6-B lane 仍开放 |
| `P7 Evidence And Documentation Lifecycle` | 保留可复现 proof，且不让 closed work package 留在永久权威。 | P2 class 与 P5 evidence ownership 稳定 | standard、current reference、历史记录与 generated evidence 有单一 owner 和路由 | P7-A retention authority 基线；P7-B 首条零项 inventory 退役完成；其余清理与 restore/provider drill 开放 |
| `P8 Long-Horizon Acceptance` | 证明迁移 compatibility、operational sustainability 与不存在 duplicate truth。 | P3-P7 完成 | 完整 acceptance contract 与独立审查通过；长期规则提升且 task history 遵循已准入退役路由 | [P8-A acceptance 基线](evidence/p8_acceptance_baseline_20260924.md) 与 matrix/fail-closed topology 检查；所有验收项仍为 open 或 partial |

## Task Clusters

- [有限任务簇计划](long_horizon_architecture_governance_task_clusters_20260825.md)
- [当前状态与风险登记](long_horizon_architecture_governance_current_status_20260825.md)
- [派发队列](long_horizon_architecture_governance_dispatch_queue_20260825.md)
- [验收合同](long_horizon_architecture_governance_acceptance_20260825.md)
- [P0 authority 清单（英文）](evidence/p0_authority_inventory_20260825.md)
- [P1-A lifecycle 决策（英文）](decisions/p1a_host_lifecycle_and_episode_authority_decision_20260825.md)
- [P1-B authority 决策（英文）](decisions/p1b_plan_and_run_receipt_authority_decision_20260825.md)
- [P1-C rollout 决策（英文）](decisions/p1c_rollout_operations_and_security_decision_20260825.md)
- [P1 独立审查（英文）](../../../reviews/long_horizon_architecture_governance_p1_review_20260825.md)
- [P3-A 独立审查（英文）](../../../reviews/long_horizon_architecture_governance_p3a_review_20260825.md)
- [P3-B 独立审查（英文）](../../../reviews/long_horizon_architecture_governance_p3b_review_20260825.md)
- [P3-C 独立审查（英文）](../../../reviews/long_horizon_architecture_governance_p3c_review_20260827.md)
- [P4-A 独立审查（英文）](../../../reviews/long_horizon_architecture_governance_p4a_review_20260827.md)
- [P4-B 独立审查与修复后通过记录（英文）](../../../reviews/long_horizon_architecture_governance_p4b_review_20260831.md)
- [P4-B state-transfer candidate snapshot（英文）](p4b_state_transfer_candidate_20260830.md)：
- [P4-B 修正路线（英文权威）](p4b_remediation_route_20260830.md)
  记录 source/target owner 分离、typed artifacts、transaction abort guard、host-owned
  native control 与当前验收边界；candidate 仍不得成为 production truth。另记录
  child-entity transfer closure 修复已实现并通过本地回归；独立复核已在
  dark/shadow candidate 范围内通过，production gate 仍由 P5 保持。
- [P4-B owner adapter 清单（英文）](p4b_owner_adapter_inventory_20260830.md)
- [P4-C internal candidate seam（英文）](p4c_internal_candidate_seam_20260915.md)
- [P4-C 独立复核（英文）](../../../reviews/long_horizon_architecture_governance_p4c_review_20260919.md)
- [P2-A control lifecycle 清单（英文）](evidence/p2_control_lifecycle_inventory_20260923.md)
- [P2-B sustainability baseline（英文）](evidence/p2b_sustainability_baseline_20260923.md)
- [P2-B release cadence follow-up（英文）](evidence/p2b_release_cadence_followup_20260924.md)

## Outputs And Evidence

预期输出包括：

- 经审查的架构决策和 compatibility map；
- host-owned construction/replacement seam 与 immutable-kernel contract；
- 收敛后的 composition-plan 与 run-evidence contract；
- epoch-bearing ref、episode authority、lifecycle SLO、runbook 和 adoption/rollback
  telemetry；
- facade-only production binding 与隔离 raw diagnostics 的 CMake/package boundary；
- 带续期和退役证据的 control 分类清单；
- 按目的划分的 CI lane 与保留行为覆盖的测试迁移；
- 具有可用 retrieval path 的 owner-local standard、reference、review、已准入历史保留
  路由和 externalized evidence；
- 足以拒绝第二 truth path 的 replay、parity、failure-injection、packaging、resource
  与 migration evidence。

## Acceptance Gate

只有满足以下条件，本计划才能被接受：

- maintained runtime composition 在一个 kernel 内不可变；任何例外都证明不可避免的
  identity requirement 与完整 state-transfer semantics；
- host replacement、facade ownership、raw diagnostics 隔离和 compatibility migration
  已实现并通过测试；
- request、resolved plan 与 run evidence 形成耐久 authority chain，不存在第二个
  Cordis、Python、native 或 fixture-owned resolver；
- replacement publication、lease、fencing、state transfer、mixed-version rollout、
  canary/backout、完整 RunReceipt 和 supported topology/platform 规则已实现并测试；
- 每个 permanent control 都说明受保护 invariant 与独立检测路径，每个 migration
  control 都已退役，或获得最多一次、有界、带 forced removal date 的独立审查续期；
- CI 与文档证据证明 ordinary development、qualification、release 与长期演进的
  可持续性；
- 独立架构审查对长期结果不存在未解决 critical/high finding。

局部清理、绿色文档测试或更窄的短期计划不能满足此 gate。

## Residuals And Next Steps

- P1-A/P1-B/P1-C 已在独立初审与修复复核后获得 decision-level acceptance。
  P3-A/P3-B/P3-C 也在独立修复复核后分别接受；当前解锁 P2-A/P2-B 与 P4
  dark/shadow candidate work，不授权 runtime truth publication 或 production
  migration。
- Dynamic in-place replacement 是候选例外，不是预设需求；其 admission 需要真实
  consumer 与 state-transfer proof。
- 初始 accepted topology 默认为 in-process；只有 P1 与 P8 显式 admission 后才支持
  fenced multi-process，其他 topology fail closed。
- 外部 plugin distribution 与 CUDA promotion 保留既有 owner，必须接入而不是绕开
  本计划。

## Archive

计划开放期间，active README 与 current-status 文件保持为入口。Accepted 决策提升到
architecture standard 或 review。P7-A 通过 `retention_authority.json` 解决
owner-archive policy：已接受的 Cordis 历史是唯一登记的 owner-local archive，其他
archive 路径仍禁止；该路由之外的退役材料使用 owner ledger 和 Git 历史。active
目录仍是当前执行面，不得变成 append-only evidence store。首条 P7-B 零项
inventory 退役记录在 [P7-B 证据包](evidence/p7b_zero_inventory_retirement_20260924.md)；
其余清理与 provider/restore drill 仍开放。
