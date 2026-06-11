# A2 任务簇执行状态 - 2026-06-01

状态：`2026-06-02 / task_cluster_execution_status / G5 research accepted / non_authoritative`。

本文记录按 [任务粒度与协调总账](task_granularity_and_coordination_20260601.zh.md)
分发并执行后的当前结果。它确认 `G1 runtime`、`G2 candidate acceptance`、
`G3 residual research closeout`、`G4 research integration` 和当前 `G5 research acceptance`
的就绪度。当前目标是 research / candidate model；工业级 / release-grade 准入不作为完成条件。

## 总体结论

新的 A2 子项目包已经可以作为后续任务分发入口使用；`TC-A2-BF-001-HASH`
已完成 retained manifest hash integrity 收口；`TC-A2-BF-001..004` 已按 `G2`
收尾为 `accepted_non_authoritative`。当前就绪范围只到：

- `TC-A2-RUNTIME` / `G1 runtime engineering`：工程维护面已通过本轮回归验证；
- `TC-A2-BF-001..004` / `G2 candidate acceptance`：候选证据包收尾为可审阅、可复现、
  fail-closed 的非权威验收结果；retained manifest hash integrity 已通过；
- `G3 residual`：只作为状态读取层，不作为本轮关闭条件；
- `G4-R-B` / `G4-R-C`：已完成 research dispatch 与串行 integration；`G4-R-B`
  三件套已完成，`G4-R-C` 的 source scan、surface draft 和 uncertainty / independence
  audit 已完成并通过 integration acceptance；
- `G5-R`：Pk / fuze proxy research packet 已完成 source scan、proxy boundary design、
  event-chain map、uncertainty / independence audit 和 integration acceptance；
- 工业级 / release-grade 准入：不在当前目标内，只作为防误用 guard 和历史 backlog 保留。

不得把本文中的“就绪”或“通过”上卷为 full A2 kill-chain、stock runtime authority、
Pk 或 deterministic fuze 完成。

## 任务簇执行矩阵

| 任务簇 | 粒度 | 本轮结论 | 下一步 |
|---|---|---|---|
| `TC-A2-RUNTIME` | `G1` | 就绪为 non-authoritative runtime engineering 维护面 | 可继续在 runtime contract、binding、event/report consumer 层分发维护任务 |
| `TC-A2-BF-001` source / identity / retained evidence | `G2 candidate acceptance` | source admission、candidate docs 和 retained manifest integrity 通过；authority guards 全 false | 保持路径稳定，不移动 `source_pin_update*`、calibration narrative 或 retained artifacts |
| `TC-A2-BF-002` scope / geometry / warhead evidence | `G2 candidate acceptance`；只读 `G3 residual` 状态 | Stage B witness geometry / family-scope retained gate 可复现；真实 geometry/warhead truth 继续 open | 只可分发 review/retained-evidence hygiene，不可扩面到真实 AIM-120C/F-16 truth |
| `TC-A2-BF-003` mechanism admission evidence | `G2 candidate acceptance`；只读 `G3 residual` 状态 | TP-21 / BEC-O retained/fail-closed 状态和 2026-06-01 review packets 可由 retained manifest 读取 | 若继续推进，必须取得 reviewer/signoff 输入，不能消费为 release evidence |
| `TC-A2-BF-004` candidate bundle / regression | `G2 candidate acceptance` | candidate bundle CLI 和 regression 提供机器入口；retained manifest checker 通过；top-level authority guard 全 false | 可作为当前 candidate package acceptance 的 G2 分发/验收入口 |
| `G4-R-B` mechanism-load envelope | `G4 research` | source scan、derived envelope draft、validation audit 均完成为 research packet | 按 [G4 research dispatch](g4_research_dispatch_20260601.zh.md)、[mechanism-load envelope 分发包](g4_research_mechanism_load_envelope_dispatch_20260601.zh.md)、[source scan](g4_research_mechanism_load_envelope_source_ledger_20260601.zh.md)、[draft](g4_research_mechanism_load_envelope_draft_20260601.zh.md) 和 [audit](g4_research_mechanism_load_envelope_validation_audit_20260601.zh.md) 执行 |
| `G4-R-C` component fragility surface | `G4 research` | source scan、surface draft、uncertainty / independence audit 均完成为 research packet；integration accepted | 按 [G4 research dispatch](g4_research_dispatch_20260601.zh.md)、[component fragility 分发包](g4_research_component_fragility_dispatch_20260601.zh.md)、[source scan](data_collection/component_fragility_vulnerability/g4_r_c_source_scan_20260601.zh.md)、[surface draft](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/g4_r_c_component_fragility_surface_draft_20260601.zh.md)、[audit](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/g4_r_c_uncertainty_independence_audit_20260601.zh.md) 和 [G4 integration acceptance](g4_research_integration_acceptance_20260601.zh.md) 执行 |
| `G5-R` Pk / fuze proxy | `G5 research` | source scan、proxy boundary design、event-chain map、uncertainty / independence audit 均完成为 research packet；integration accepted | 按 [G5 research dispatch](g5_research_dispatch_20260602.zh.md)、[source scan](data_collection/kill_chain_proxy_methods/g5_r_source_scan_20260602.zh.md)、[proxy boundary design](g5_research_pk_fuze_proxy_boundary_design_20260602.zh.md)、[event-chain map](g5_research_event_chain_map_20260602.zh.md)、[audit](g5_research_uncertainty_independence_audit_20260602.zh.md) 和 [G5 integration acceptance](g5_research_integration_acceptance_20260602.zh.md) 执行 |
| industrial / release-grade admission | out of current research goal | 未启动；不作为当前完成条件 | 只有用户明确要求时才另起准入任务 |

## 分发记录

本轮并行分发了两个只读审阅任务：

- `G1 runtime` 审阅：确认 `DamageReport` 终局/非终局 flags、binding、contract 和
  WP22 guardrails 属于 reporting / engineering surface，不是 Pk、fuze 或 G4 authority；
- `G2 candidate` 审阅：检查 `README.zh.md`、`candidate_acceptance_status.zh.md`、
  candidate package README、`residual_register.zh.md`、retained manifests 和
  `a2_candidate_vps_bundle.py` 的入口一致性；
- `TC-A2-BF-001-HASH` 执行：新增 retained manifest integrity checker 和 architecture test，
  并将 retained manifest hash mismatches 收口到 0；
- `TC-A2-BF-003-FAILCLOSED` 执行：新增 [mechanism admission fail-closed backlog](mechanism_admission_failclosed_backlog_20260601.zh.md)，
  拆解 `RES-005/006` 下一轮 blockers。
- `TC-A2-BF-003-RES005-TP21` 执行：新增 retained selected-case review packet，
  当前仍 `blocked_fail_closed_tp21_selected_case_admission_review_packet`；
- `TC-A2-BF-003-RES006-BECO` 执行：新增 retained replacement/tolerance review packet，
  当前仍 `blocked_fail_closed_res006_beco_replacement_tolerance_admission_review`。
- `TC-A2-BF-003-RES005-TP21-CANDIDATE` 执行：新增 retained selected-case candidate packet，
  当前仍 `blocked_fail_closed_tp21_selected_case_candidate_packet`；
- `TC-A2-BF-003-RES006-LINEAGE` 执行：新增 retained BEC-O lineage/tolerance candidate packet，
  当前仍缺 independent lineage / allowed-output / tolerance / replacement signoff；
- `TC-A2-BF-003-RIGHTS-SIGNOFF-REQUEST` 执行：新增 retained source-rights signoff request packet，
  `approval_granted=false`、`release_grade_satisfied=false`。
- `TC-A2-BF-003-EVIDENCE-SWEEP` 只读诊断：按 `2 / 2` 轮次上限并行检查 RES005、RES006
  和治理文档。RES005 现有 payload 与 rights-support 已在场，但 selected-case
  locator / preimage / anchor / independent-reviewer / allowed-output / authority-boundary
  链未闭合；RES006 现有 cached/recalculated hash anchors 已在场，但 independent lineage /
  allowed-output / numeric tolerance / replacement-anchor signoff 未闭合；治理审查确认
  `G2/G3` 边界正确，需由主线程串行记录轮次、Model/reasoning 和并行/串行边界。
- `TC-A2-BF-003-SIGNOFF-INTAKE` 执行：新增 retained signoff intake contract，
  定义未来外部 reviewer/signoff packet 的 hash-only 输入形状、raw-content absence
  要求和 authority guard checker；当前无外部 signoff packet supplied，仍 fail-closed，
  不消费 reviewer 决策，不关闭 `RES-005/006`。
- `TC-A2-BF-003-SIGNOFF-INTAKE-NEXT` 执行：新增 external signoff packet template、
  signoff intake valid/invalid fixtures 和 retained signoff admission preflight packet。
  template 的 placeholder 决策刻意保持 intake-invalid；fixture 只证明 shape contract；
  preflight 默认无外部 packet supplied，`ready_for_admission_gate=false`。即使未来
  shape-valid 外部 packet 进入 preflight，也只产生 ready flag，不消费 signoff decision，
  不关闭 `RES-005/006`。
- `G4-R-B-DISPATCH` 分发：启动 mechanism-load envelope 的研究级任务拆分；只输出
  source scan、derived envelope 和 guard audit 工作包，不写型号级真值。
- `G4-R-B-001-SOURCE-LEDGER-SCAN` 执行：新增
  [mechanism-load source scan](g4_research_mechanism_load_envelope_source_ledger_20260601.zh.md)，
  从既有公开来源账本整理 fragment / blast research envelope 的 source proposal。
- `G4-R-B-002-DERIVED-ENVELOPE-DRAFT` 执行：新增
  [mechanism-load envelope draft](g4_research_mechanism_load_envelope_draft_20260601.zh.md)，
  定义 research mechanism-load vector、assumptions、uncertainty 和 replacement rule。
- `G4-R-B-003-VALIDATION-GUARD-AUDIT` 执行：新增
  [mechanism-load validation audit](g4_research_mechanism_load_envelope_validation_audit_20260601.zh.md)，
  确认 G4-R-B 只作为 research-ready mechanism side input。
- `G4-R-C-DISPATCH` 分发：启动 component fragility surface 的研究级任务拆分；只输出
  source/data scan、fragility surface draft 和 uncertainty/independence audit 工作包，不写
  F-16C 全机组件概率真值。
- `G4-R-C-SCAN` 执行：新增
  [component fragility source scan](data_collection/component_fragility_vulnerability/g4_r_c_source_scan_20260601.zh.md)，
  从既有公开来源账本整理 research surface 的 source proposal。
- `G4-R-C-SURFACE` 执行：新增
  [component fragility surface draft](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/g4_r_c_component_fragility_surface_draft_20260601.zh.md)，
  只定义 research row shape、curve-family placeholder 和 replacement path。
- `G4-R-C-AUDIT` 执行：新增
  [uncertainty / independence audit](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/g4_r_c_uncertainty_independence_audit_20260601.zh.md)，
  确认 Stage C test-local、synthetic baseline 和 research surface 仍保持分离。
- `G4-R-INTEGRATION` 主线程整合：新增 [G4 research integration acceptance](g4_research_integration_acceptance_20260601.zh.md)，
  并把中央入口标记为 `dispatch_closed_non_authoritative`；G4 research 与工业级准入保持拆开。
- `G5-R-DISPATCH` 分发：新增 [G5 research dispatch](g5_research_dispatch_20260602.zh.md)，
  启动 Pk / fuze proxy research lane；只输出 source scan、boundary design、event-chain map
  和 uncertainty audit 工作包，不写 Pk 或 deterministic fuze truth。
- `G5-R-A-SOURCE-SCAN` 执行：新增
  [G5 source scan](data_collection/kill_chain_proxy_methods/g5_r_source_scan_20260602.zh.md)，
  从既有 G4 research packet、fuze authority package、guidance/miss-distance 方法和 runtime
  event/report surface 整理 proxy input proposal。
- `G5-R-B-PROXY-BOUNDARY` 执行：新增
  [G5 proxy boundary design](g5_research_pk_fuze_proxy_boundary_design_20260602.zh.md)，
  定义 terminal geometry、fuze proxy、mechanism-load、component response、consequence 和
  uncertainty 的研究级连接边界。
- `G5-R-C-EVENT-CHAIN-MAP` 执行：新增
  [G5 event-chain map](g5_research_event_chain_map_20260602.zh.md)，
  将 terminal geometry、fuze proxy、G4 mechanism-load、G4 component response 和
  consequence proxy 串成 research event chain。
- `G5-R-D-UNCERTAINTY-AUDIT` 执行：新增
  [G5 uncertainty / independence audit](g5_research_uncertainty_independence_audit_20260602.zh.md)，
  确认 source/model/scope/result uncertainty 和 non-circularity。
- `G5-R-INTEGRATION` 主线程整合：新增
  [G5 research integration acceptance](g5_research_integration_acceptance_20260602.zh.md)，
  将 G5-R 标记为 `research_packet_accepted`，且 Pk / deterministic fuze authority 仍保持 false。

主线程负责集成与验证，不把 worker packet 单独作为工业级证据。

## 已执行验证

本节保留此前 Windows 本地维护环境验证记录，并补充本轮当前工作区复核。两组验证都只支持
`G1/G2` 工程与候选包结论，以及 `G4` 的 research 分发 / integration acceptance；
不支持工业级 / release-grade 准入。

```powershell
cmake --build build-local-win --target ef_core ef_py -j2
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 validate
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python -m pytest tests\runtime\air_combat\test_weapon_guidance_realism_guards.py
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python -m pytest tests\runtime\bindings\test_bindings_engagement_surface.py tests\runtime\engagement
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python -m pytest tests\architecture\test_wp22_structural_guardrails.py
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python -m pytest tests/architecture/damage_model/test_source_admission_audit.py tests/architecture/damage_model/test_scope_provenance_closeout_gates.py tests/architecture/damage_model/test_scope_provenance_closeout_gates.py tests/architecture/damage_model/test_independent_review_closeout_gates.py
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python tools\maintenance\damage_model_source_governance.py admission-audit --strict
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python -m pytest tests\architecture\test_a2_retained_manifest_integrity.py
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python tools\maintenance\a2_retained_manifest_integrity.py
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python -m pytest tests\architecture\damage_model\test_candidate_artifact_contracts.py
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\maintenance\cmo_env.ps1 python tools\maintenance\a2_candidate_vps_bundle.py --output $env:TEMP\a2_candidate_vps_bundle_task_cluster_exec.json
git diff --check
```

当前结果：

- build：`ninja: no work to do`
- runtime realism guards：`146 passed`
- bindings / engagement：`52 passed`
- WP22 structural guardrails：`16 passed`
- source admission + retained/gate tests：`20 passed`
- source admission strict：`9 ledgers, 29 candidate docs, 53 calibration docs`
- retained manifest integrity tests：`8 passed`
- retained manifest integrity checker：`manifest_count=29`, `missing_total=0`,
  `sha_mismatch_total=0`, `guard_true_total=0`
- RES-005 selected-case review packet tests：`6 passed`
- RES-006 replacement/tolerance review packet tests：`3 passed`
- RES-005 selected-case candidate packet tests：`6 passed`
- RES-006 lineage/tolerance packet tests：`3 passed`
- source-rights signoff request packet tests：`7 passed`
- signoff intake contract tests：`5 passed`
- external signoff packet template tests：`4 passed`
- signoff intake fixture contract tests：`2 passed`
- signoff admission preflight tests：`4 passed`
- retained mechanism admission regression tests：`22 passed`
- retained mechanism admission focused suite：`50 passed`
- candidate VPS bundle tests：`2 passed`
- candidate VPS bundle CLI：exit 0
- Markdown local link check：`0 missing`
- old Linux absolute path scan：no matches
- `git diff --check`：exit 0，仅有 Windows LF/CRLF 提示

本轮当前工作区复核：

```bash
python -m pytest -q tests/architecture/damage_model/test_retained_manifest_integrity.py tests/architecture/damage_model/test_candidate_artifact_contracts.py tests/architecture/damage_model/test_source_admission_audit.py tests/runtime/air_combat/test_vulnerability_evidence_dataset_descriptor.py
python -m pytest -q tests/runtime/engagement/test_engagement_contract_shape.py tests/runtime/engagement/test_launch_adapter_static_shape.py tests/runtime/engagement/test_live_engagement_event_capture.py
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
python -m pytest -q tests/architecture/damage_model/test_external_signoff_admission_preflight.py tests/architecture/damage_model/test_benchmark_recalculation_admission.py tests/architecture/damage_model/test_benchmark_evidence_admission.py tests/architecture/damage_model/test_external_signoff_intake_contracts.py tests/architecture/damage_model/test_source_evidence_governance.py
python tools/maintenance/a2_retained_manifest_integrity.py
python tools/maintenance/damage_model_source_governance.py admission-audit --strict
python tools/maintenance/a2_candidate_vps_bundle.py
```

当前工作区结果：

- A2 candidate/source/manifest/descriptor：`17 passed`；
- engagement contract / launch adapter / live capture shape：`16 passed`；
- weapon guidance realism guards：`150 passed`；
- G2 fail-closed signoff / residual packet focused suite：`44 passed`；
- retained manifest integrity checker：`manifest_count=29`, `missing_total=0`,
  `sha_mismatch_total=0`, `guard_true_total=0`；
- source admission strict：`9 ledgers, 29 candidate docs, 53 calibration docs`；
- candidate VPS bundle CLI：exit 0；`status=candidate_non_authoritative_bundle`，
  `effect_scale_authority_in_stock=false`、`component_failure_probability_authority_in_stock=false`、
  `pk_authority=false`、`deterministic_fuze_authority=false`。
- G4 research integration focused复核：candidate/source/manifest tests `15 passed`；
  retained packet focused tests `34 passed`；G4 guard grep no matches；`git diff --check` exit 0。
- G5 research dispatch focused复核：retained manifest integrity `sha_mismatch_total=0`；
  source admission strict `9 ledgers, 29 candidate docs, 53 calibration docs`；
  candidate bundle `status=candidate_non_authoritative_bundle`、`pk_authority=false`、
  `deterministic_fuze_authority=false`；G5 guard grep no matches；candidate/source/manifest tests
  `15 passed`；retained packet focused tests `34 passed`；`git diff --check` exit 0。

## G2 收尾后队列状态

同 scope 的 `TC-A2-BF-001..004` 不再需要追加临时收尾 wave。后续只有三类合法入口：

- 当前已按 [G4 research dispatch](g4_research_dispatch_20260601.zh.md) 启动
  `G4-R-B`、`G4-R-C` 研究分发；`G4-R-B` 三件套和 `G4-R-C` scan/surface/audit
  已落盘并通过 [G4 integration acceptance](g4_research_integration_acceptance_20260601.zh.md)；
- 当前已按 [G5 research dispatch](g5_research_dispatch_20260602.zh.md) 完成 `G5-R`
  research packet；source scan、proxy boundary design、event-chain map、uncertainty audit
  和 integration acceptance 均已落盘；
- 收到新的外部 reviewer/signoff packet 后，按 signoff intake / preflight / admission gate
  串行处理 `RES-005/006`，仍只改变 `G3 residual` 状态；
- 工业级 / release-grade 准入必须由用户明确另起任务，不复用本轮 G2/G4 research 结论。

## G3 台账收尾状态

`G3 residual` 已另行清点为 `research_closed_authority_retained`，见
[g3_residual_closeout_status_20260601.zh.md](g3_residual_closeout_status_20260601.zh.md)。
该结论表示 `RES-001..014` 对当前 research profile 不再形成阻塞，且均有明确状态、
稳定证据入口和不得上卷边界。

当前项目默认转为 research / candidate profile，见
[research_candidate_data_policy_20260601.zh.md](research_candidate_data_policy_20260601.zh.md)。
因此下列旧 substantive blockers 已被重标为 research-closed 或 research-out-of-scope；
它们现在只作为后续可替换 research data surface 的完善目标，或作为未来可选工业级准入的 guard。

当前仍需保持的 substantive blockers：

- `RES-005/006` 对 research profile 已闭合为可替换 mechanism-load envelope 目标；不消费 TP-21 / BEC-O 原始输出；
- `RES-009/010/011/012` 对 research profile 已闭合为 Stage C candidate surface / uncertainty ledger 目标；
- `RES-013/014` 对 authority 仍 boundary deferred；当前 `G5-R` research proxy packet
  已收口，但不关闭 Pk / deterministic fuze authority。

## 保持的边界

- `DamageReport.forced_landing`、`flight_control_kill`、`propulsion_kill`、`crew_kill`
  是 runtime consequence/reporting flags，不是 Pk；
- runtime debug guard state 仍是 diagnostic/debug surface，不是 stock 写入许可；
- runtime-aligned exercise 只允许作为 test-local / candidate evidence，不得写入 stock DB；
- retained gate JSON 和 manifest 优先于叙事文档；manifest hash mismatch 不得被叙事覆盖；
- `RES-005/006` 的 fail-closed 状态不能被 retained review packet 或 bundle 通过覆盖；
- `RES-013/014` 继续是 Pk / deterministic fuze boundary deferred。
