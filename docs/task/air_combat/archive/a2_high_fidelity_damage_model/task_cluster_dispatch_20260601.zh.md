# A2 任务簇分发包 - 2026-06-01

状态：`2026-06-01 / dispatch_packet / non-authoritative`。

本文是按 [任务粒度与协调总账](task_granularity_and_coordination_20260601.zh.md)
分发执行任务的唯一入口。它不重新验证任务簇是否成立，只把已经确定的 `TC-A2-*`
以及 `G4-R-*` / `G5-R-*` research 切片拆成可交付工作包。

## 分发原则

- 每个任务必须先标注粒度：`G1`、`G2`、`G3`、`G4 research`、`G4 authority`、`G5 research` 或 `G5 authority`；
- `G2` candidate 包可以被分发执行，但不得写成 `G4/G5` authority；
- `G4 research` 可以在当前 research profile 下分发，输出可替换、可审计的数据面；
- `G5 research` 可以在当前 research profile 下分发，输出 Pk / fuze proxy 的边界和事件链；
- 工业级 / release-grade 准入不作为当前完成条件，只在用户明确要求时另行分发；
- subagent 不做“再判断任务簇是否成立”的泛审阅，只接收有文件边界和验收输出的执行任务；
- 不移动 `calibration/**`、`retained_artifacts/**`、`source_pin_update*.zh.md`
  或 source ledgers，除非同步更新工具和测试。

## 轮次、模型与并行边界

当前 `TC-A2-BF-003` mechanism admission closeout sweep 的实现/诊断预算为最多两轮。
第 1 轮已生成 fail-closed retained packets；第 2 轮是本轮只读证据定位与治理审查。
除非出现新的 reviewer/signoff 输入、selected-case locator/preimage/anchor 输入，或重新基线化
任务簇边界，否则不再追加同范围的临时 wave。

在 evidence sweep 达到 `2 / 2` 后，新增一个独立的 signoff intake 标准化切片，
预算为 `1 / 1`。该切片只定义未来外部 reviewer/signoff packet 的 hash-only 输入形状
与 fail-closed checker，不替代 reviewer 决策，不关闭 `RES-005/006`。
随后新增 `SIGNOFF-INTAKE-NEXT` 标准化切片，预算为 `1 / 1`。它只补齐 reviewer
填写模板、fixture contract 和 admission preflight，不启动新的 evidence sweep，不消费签收，
不进入 `G4/G5`。

| 轮次 | 任务 ID | 类型 | Model / reasoning | 并行边界 | 写入边界 | 当前结论 |
|---:|---|---|---|---|---|---|
| 1 / 2 | `TC-A2-BF-003-RES005-TP21`、`TC-A2-BF-003-RES006-BECO` | implementation | inherited main-thread settings；non-trivial implementation 不低于 `medium` reasoning | RES005 与 RES006 retained packet 写入范围互不重叠；closure/status doc 串行 | 各自 tool/test/retained artifact 路径 | retained review packets 已生成，均 fail-closed |
| 1 / 2 | `TC-A2-BF-003-RES005-TP21-CANDIDATE`、`TC-A2-BF-003-RES006-LINEAGE`、`TC-A2-BF-003-RIGHTS-SIGNOFF-REQUEST` | implementation | inherited main-thread settings；non-trivial implementation 不低于 `medium` reasoning | 三个 packet 写入范围互不重叠；依赖 gate/doc sync 后串行重生 | 各自 tool/test/retained artifact 路径 | candidate / request packets 已生成，均不授予 authority |
| 2 / 2 | `TC-A2-BF-003-RES005-EVIDENCE-SWEEP` | diagnostics-only | `gpt-5.4-mini` / `xhigh` | 可与 RES006 sweep 和治理审查并行 | 无写入，只读 JSON/manifest/status docs | 未找到 RES005 selected-case locator/preimage/anchor/signoff 闭合证据 |
| 2 / 2 | `TC-A2-BF-003-RES006-EVIDENCE-SWEEP` | diagnostics-only | `gpt-5.4-mini` / `xhigh` | 可与 RES005 sweep 和治理审查并行 | 无写入，只读 JSON/manifest/status docs | 未找到 RES006 lineage/tolerance/replacement/allowed-output signoff 闭合证据 |
| 2 / 2 | `TC-A2-BF-003-GOVERNANCE-SWEEP` | diagnostics-only | `gpt-5.4-mini` / `xhigh` | 可与 RES005/RES006 sweep 并行 | 无写入，只读 dispatch/status docs | 建议补显式轮次预算、Model/reasoning 和并行/串行边界；由主线程串行整合 |
| 1 / 1 | `TC-A2-BF-003-SIGNOFF-INTAKE` | implementation | inherited main-thread settings；non-trivial implementation 不低于 `medium` reasoning | 单作者标准化切片；写入范围独立 | intake tool/test/retained artifact 和状态文档 | signoff intake contract 已生成；默认无外部签收输入，fail-closed |
| 1 / 1 | `TC-A2-BF-003-SIGNOFF-INTAKE-NEXT-A` | implementation | inherited main-thread settings；non-trivial implementation 不低于 `medium` reasoning | 可与 fixture/preflight 切片并行；写入范围独立 | external template tool/test/retained artifact | reviewer-fillable template 已生成；placeholder 决策保持 intake-invalid |
| 1 / 1 | `TC-A2-BF-003-SIGNOFF-INTAKE-NEXT-B` | implementation | inherited main-thread settings；non-trivial implementation 不低于 `medium` reasoning | 可与 template/preflight 切片并行；只写测试 fixture | signoff intake fixtures/test | valid/invalid fixtures 证明 shape-valid 仍非 approval，raw/authority true fail-closed |
| 1 / 1 | `TC-A2-BF-003-SIGNOFF-INTAKE-NEXT-C` | implementation | inherited main-thread settings；non-trivial implementation 不低于 `medium` reasoning | 可与 template/fixture 切片并行；写入范围独立 | admission preflight tool/test/retained artifact | preflight 默认 fail-closed；shape-valid 外部 packet 只产生 ready flag，不消费决策 |
| 1 / 1 | `G4-R-B-DISPATCH` | dispatch | inherited main-thread settings；non-trivial documentation 不低于 `medium` reasoning | 可与 `G4-R-C-DISPATCH` 并行；中央入口串行整合 | `g4_research_mechanism_load_envelope_dispatch_20260601.zh.md` | 分发 mechanism-load envelope research 工作包 |
| 1 / 1 | `G4-R-C-DISPATCH` | dispatch | inherited main-thread settings；non-trivial documentation 不低于 `medium` reasoning | 可与 `G4-R-B-DISPATCH` 并行；中央入口串行整合 | `g4_research_component_fragility_dispatch_20260601.zh.md` | 分发 component fragility surface research 工作包 |
| 1 / 1 | `G4-R-B-001-SOURCE-LEDGER-SCAN` | research source scan | inherited main-thread settings；source scan 不低于 `medium` reasoning | 可与 `G4-R-C-SCAN` 并行；不修改既有 source ledger 或 retained JSON | `g4_research_mechanism_load_envelope_source_ledger_20260601.zh.md` | source proposal 已落盘；下一步可分发 derived envelope draft |
| 1 / 1 | `G4-R-C-SCAN` | research source scan | inherited main-thread settings；source scan 不低于 `medium` reasoning | 可与 `G4-R-B-001` 并行；surface/audit 必须等待 scan | `data_collection/component_fragility_vulnerability/g4_r_c_source_scan_20260601.zh.md` | source proposal 已落盘；下一步可分发 surface draft 与 uncertainty audit |
| 1 / 1 | `G4-R-B-002-DERIVED-ENVELOPE-DRAFT` | research modeling | inherited main-thread settings；research modeling 不低于 `medium` reasoning | 依赖 `G4-R-B-001`；不修改 calibration 或 retained artifacts | `g4_research_mechanism_load_envelope_draft_20260601.zh.md` | mechanism-load vector 草案已落盘；不写真实参数 |
| 1 / 1 | `G4-R-B-003-VALIDATION-GUARD-AUDIT` | research validation | inherited main-thread settings；validation 不低于 `medium` reasoning | 依赖 `G4-R-B-001/002`；不修改 runtime/test | `g4_research_mechanism_load_envelope_validation_audit_20260601.zh.md` | G4-R-B research packet 审查通过 |
| 1 / 1 | `G4-R-C-SURFACE` | research surface | inherited main-thread settings；surface draft 不低于 `medium` reasoning | 依赖 `G4-R-C-SCAN` 和 `G4-R-B` mechanism axis；不写 stock row | `calibration/.../g4_r_c_component_fragility_surface_draft_20260601.zh.md` | component fragility research surface 草案已落盘 |
| 1 / 1 | `G4-R-C-AUDIT` | research validation | inherited main-thread settings；audit 不低于 `medium` reasoning | 依赖 `G4-R-C-SCAN/SURFACE`；不修改 retained artifacts | `calibration/.../g4_r_c_uncertainty_independence_audit_20260601.zh.md` | uncertainty / independence audit 已落盘 |
| 1 / 1 | `G4-R-INTEGRATION` | research integration | inherited main-thread settings；integration 不低于 `medium` reasoning | 依赖 `G4-R-B` 与 `G4-R-C` packets；串行状态同步 | `g4_research_dispatch_20260601.zh.md`、`g4_research_component_fragility_dispatch_20260601.zh.md`、`g4_research_integration_acceptance_20260601.zh.md`、README/status docs | G4 research 分发已收口为 non-authoritative research packet |
| 1 / 1 | `G5-R-DISPATCH` | dispatch | inherited main-thread settings；non-trivial documentation 不低于 `medium` reasoning | 依赖 G4 integration accepted；中央入口串行整合 | `g5_research_dispatch_20260602.zh.md` | 分发 Pk / fuze proxy research 工作包 |
| 1 / 1 | `G5-R-A-SOURCE-SCAN` | research source scan | inherited main-thread settings；source scan 不低于 `medium` reasoning | 可先行；不修改 retained artifacts 或 runtime | `data_collection/kill_chain_proxy_methods/**` | G5 proxy source / method scan 已落盘 |
| 1 / 1 | `G5-R-B-PROXY-BOUNDARY` | research design | inherited main-thread settings；design 不低于 `medium` reasoning | 依赖 `G5-R-A`；不写 runtime descriptor | `g5_research_pk_fuze_proxy_boundary_design_20260602.zh.md` | Pk / fuze proxy boundary design 已落盘 |
| 1 / 1 | `G5-R-C-EVENT-CHAIN-MAP` | research design | inherited main-thread settings；event-chain map 不低于 `medium` reasoning | 依赖 `G5-R-B`；不修改 runtime/test | `g5_research_event_chain_map_20260602.zh.md` | G5 proxy event-chain map 已落盘 |
| 1 / 1 | `G5-R-D-UNCERTAINTY-AUDIT` | research validation | inherited main-thread settings；audit 不低于 `medium` reasoning | 依赖 `G5-R-C`；不修改 retained artifacts | `g5_research_uncertainty_independence_audit_20260602.zh.md` | G5 uncertainty / independence audit 已落盘 |
| 1 / 1 | `G5-R-INTEGRATION` | research integration | inherited main-thread settings；integration 不低于 `medium` reasoning | 依赖 `G5-R-C/D`；串行状态同步 | `g5_research_integration_acceptance_20260602.zh.md`、README/status docs | G5 research packet accepted；guards false |

## 当前分发队列与验收状态

| 优先级 | 任务 ID | 任务簇 | 粒度 | 状态 | 执行目标 | 写入范围 | 验收输出 |
|---:|---|---|---|---|---|---|---|
| 1 | `TC-A2-BF-001-HASH` | `TC-A2-BF-001` | `G2` | accepted | 固化 retained manifest hash integrity 检查，并修正 retained manifest 与产物 hash 不一致的问题 | `tools/maintenance/**`、`tests/architecture/**`、相关 `retained_artifacts/**/manifest.json` | `manifest_count=29`, `missing_total=0`, `sha_mismatch_total=0`, `guard_true_total=0` |
| 2 | `TC-A2-BF-004-PACKAGE` | `TC-A2-BF-004` | `G2` | closed | 将 candidate bundle 输出和任务簇执行状态整理成当前 G2 closeout record | `candidate_acceptance_status.zh.md`、`task_cluster_execution_status_20260601.zh.md` | 文档只声明 G2 candidate acceptance closeout 和 residual blockers，不上卷到 G4/G5 |
| 3 | `TC-A2-BF-003-FAILCLOSED` | `TC-A2-BF-003` | `G2` + `G3` 状态读取 | accepted as backlog split | 把 `RES-005/006` fail-closed blockers 拆成下一轮可执行项 | [mechanism_admission_failclosed_backlog_20260601.zh.md](mechanism_admission_failclosed_backlog_20260601.zh.md) | 不消费 TP-21 / BEC-O 为 release evidence，只输出 blocker closeout plan |
| 4 | `TC-A2-RUNTIME-FINALIZE` | `TC-A2-RUNTIME` | `G1` | accepted | 收口当前 `DamageReport` consequence flags 的工程说明和测试映射 | `runtime_status.zh.md`、相关 runtime tests 如需补注 | 明确 flags 是 reporting / consequence surface，不是 Pk/fuze |
| 5 | `TC-A2-BF-003-RES005-TP21` | `TC-A2-BF-003` | `G2` + `G3` 状态读取 | accepted as fail-closed retained packet | 生成 TP-21 selected-case admission review packet，记录缺 reviewer/signoff 输入 | `tools/maintenance/a2_blastfrag_res005_tp21_selected_case_admission_gate.py`、`tests/architecture/damage_model/test_benchmark_evidence_admission.py`、`retained_artifacts/res005_tp21_selected_case_admission_20260601/**` | retained packet 存在且 authority fail-closed；research profile 用可替换 envelope，不授予 authority |
| 6 | `TC-A2-BF-003-RES006-BECO` | `TC-A2-BF-003` | `G2` + `G3` 状态读取 | accepted as fail-closed retained packet | 生成 BEC-O replacement/tolerance admission review packet，记录缺 lineage/tolerance/signoff 输入 | `tools/maintenance/a2_blastfrag_res006_beco_replacement_tolerance_admission_gate.py`、`tests/architecture/damage_model/test_benchmark_recalculation_admission.py`、`retained_artifacts/res006_beco_replacement_tolerance_admission_20260601/**` | retained packet 存在且 authority fail-closed；research profile 用可替换 envelope，不授予 authority |
| 7 | `TC-A2-BF-003-RES005-TP21-CANDIDATE` | `TC-A2-BF-003` | `G2` + `G3` 状态读取 | accepted as fail-closed candidate packet | 基于已有 TP-21 payload 生成 selected-case candidate packet，确认仍缺 locator/preimage/hash/signoff | `tools/maintenance/a2_blastfrag_res005_tp21_selected_case_candidate_packet.py`、`tests/architecture/damage_model/test_benchmark_evidence_admission.py`、`retained_artifacts/res005_tp21_selected_case_candidate_20260601/**` | candidate packet 存在且 authority fail-closed；research profile 用可替换 envelope，不授予 authority |
| 8 | `TC-A2-BF-003-RES006-LINEAGE` | `TC-A2-BF-003` | `G2` + `G3` 状态读取 | accepted as fail-closed candidate packet | 基于已有 BEC-O cached/recalculated hash anchors 生成 lineage/tolerance candidate packet | `tools/maintenance/a2_blastfrag_res006_beco_lineage_tolerance_review_packet.py`、`tests/architecture/damage_model/test_benchmark_recalculation_admission.py`、`retained_artifacts/res006_beco_lineage_tolerance_review_20260601/**` | candidate packet 存在且 fail-closed；不关闭 `RES-006`；不授予 authority |
| 9 | `TC-A2-BF-003-RIGHTS-SIGNOFF-REQUEST` | `TC-A2-BF-003` | `G2` + `G3` 状态读取 | accepted as fail-closed signoff request | 生成 source-rights signoff request/checklist，明确 hash-only review request 和 forbidden outputs | `tools/maintenance/a2_blastfrag_source_rights_signoff_request_packet.py`、`tests/architecture/damage_model/test_source_evidence_governance.py`、`retained_artifacts/source_rights_signoff_request_20260601/**` | request packet 存在；`approval_granted=false`；`release_grade_satisfied=false` |
| 10 | `TC-A2-BF-003-EVIDENCE-SWEEP` | `TC-A2-BF-003` | `G2` + `G3` 状态读取 | completed read-only diagnostics | 并行确认已有数据是否已经包含可复用 RES005/RES006 closeout evidence，并审查 subagent 派发纪律 | 无写入；只读 retained JSON/manifest/status docs | 数据与 retained packets 存在；RES005/006 signoff/admission evidence 仍缺；本轮达到 2/2 轮次上限 |
| 11 | `TC-A2-BF-003-SIGNOFF-INTAKE` | `TC-A2-BF-003` | `G2` + `G3` 状态读取 | accepted as fail-closed intake contract | 定义未来外部 reviewer/signoff packet 的 hash-only schema/checker，使后续材料可机器预检 | `tools/maintenance/a2_blastfrag_signoff_intake_contract.py`、`tests/architecture/damage_model/test_external_signoff_intake_contracts.py`、`retained_artifacts/signoff_intake_contract_20260601/**` | contract 存在；无外部 signoff packet supplied；`approval_granted=false`；`admission_granted=false`；不关闭 `RES-005/006` 的 authority fail-closed 状态 |
| 12 | `TC-A2-BF-003-SIGNOFF-INTAKE-NEXT` | `TC-A2-BF-003` | `G2` + `G3` 状态读取 | accepted as fail-closed template/preflight standardization | 补齐 external signoff packet template、valid/invalid fixture contract 和 admission preflight packet | `tools/maintenance/a2_blastfrag_external_signoff_packet_template.py`、`tools/maintenance/a2_blastfrag_signoff_admission_preflight.py`、对应 tests/fixtures、`retained_artifacts/external_signoff_packet_template_20260601/**`、`retained_artifacts/signoff_admission_preflight_20260601/**` | template/preflight 存在；无真实外部 signoff supplied；`approval_granted=false`；`admission_granted=false`；不关闭 `RES-005/006` 的 authority fail-closed 状态 |
| 13 | `G4-R-B-DISPATCH` | `G4-R-B` | `G4 research` | dispatched | 分发 fragment / blast mechanism-load envelope 的 source scan、derived envelope 和 guard audit | [g4_research_mechanism_load_envelope_dispatch_20260601.zh.md](g4_research_mechanism_load_envelope_dispatch_20260601.zh.md) | 只建立 research envelope 工作包；工业级准入不在当前目标内 |
| 14 | `G4-R-C-DISPATCH` | `G4-R-C` | `G4 research` | dispatched | 分发 component fragility surface、uncertainty ledger 和 independence audit | [g4_research_component_fragility_dispatch_20260601.zh.md](g4_research_component_fragility_dispatch_20260601.zh.md) | 只建立 research surface 工作包；Stage C 真值不在当前目标内 |
| 15 | `G4-R-INTEGRATION` | `G4 research` | `G4 research` | pass | 整合 G4 research 中央分发入口和验证边界 | [g4_research_dispatch_20260601.zh.md](g4_research_dispatch_20260601.zh.md)、[g4_research_integration_acceptance_20260601.zh.md](g4_research_integration_acceptance_20260601.zh.md)、本文件、`task_cluster_execution_status_20260601.zh.md` | 中央入口声明 `dispatch_closed_non_authoritative`；工业级准入不在当前目标内 |
| 16 | `G4-R-B-001-SOURCE-LEDGER-SCAN` | `G4-R-B` | `G4 research` | pass | 整理 mechanism-load envelope 第一波公开来源 proposal | [g4_research_mechanism_load_envelope_source_ledger_20260601.zh.md](g4_research_mechanism_load_envelope_source_ledger_20260601.zh.md) | source ids、tier/rights、scope、uncertainty/confidence、replacement rule 已列出；不写数值 row |
| 17 | `G4-R-C-SCAN` | `G4-R-C` | `G4 research` | pass | 整理 component fragility surface 第一波公开来源 proposal | [data_collection/component_fragility_vulnerability/g4_r_c_source_scan_20260601.zh.md](data_collection/component_fragility_vulnerability/g4_r_c_source_scan_20260601.zh.md) | source ids、tier/rights、scope、uncertainty/confidence、replacement rule 已列出；不写 runtime row |
| 18 | `G4-R-B-002-DERIVED-ENVELOPE-DRAFT` | `G4-R-B` | `G4 research` | pass | 将 mechanism-load source proposal 整理成 research mechanism-load vector | [g4_research_mechanism_load_envelope_draft_20260601.zh.md](g4_research_mechanism_load_envelope_draft_20260601.zh.md) | 只写 formula-family / placeholder / qualitative axis；不写真实战斗部或目标参数 |
| 19 | `G4-R-B-003-VALIDATION-GUARD-AUDIT` | `G4-R-B` | `G4 research` | pass | 审查 G4-R-B source scan 和 envelope draft | [g4_research_mechanism_load_envelope_validation_audit_20260601.zh.md](g4_research_mechanism_load_envelope_validation_audit_20260601.zh.md) | G4-R-B 可作为 downstream research mechanism side input |
| 20 | `G4-R-C-SURFACE` | `G4-R-C` | `G4 research` | pass | 起草 component fragility research surface | [calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/g4_r_c_component_fragility_surface_draft_20260601.zh.md](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/g4_r_c_component_fragility_surface_draft_20260601.zh.md) | row shape、curve family、uncertainty、replacement rule 已列出；不写概率真值 |
| 21 | `G4-R-C-AUDIT` | `G4-R-C` | `G4 research` | pass | 审查 G4-R-C uncertainty 与 independence | [calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/g4_r_c_uncertainty_independence_audit_20260601.zh.md](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/g4_r_c_uncertainty_independence_audit_20260601.zh.md) | source/surface/mechanism-axis 分离；Stage C test-local 仍 comparison-only |
| 22 | `G5-R-DISPATCH` | `G5-R` | `G5 research` | pass | 分发 Pk / fuze proxy source scan、boundary、event-chain map 和 audit | [g5_research_dispatch_20260602.zh.md](g5_research_dispatch_20260602.zh.md) | 只建立 research proxy 工作包；Pk / deterministic fuze authority 不在当前目标内 |
| 23 | `G5-R-A-SOURCE-SCAN` | `G5-R` | `G5 research` | pass | 整理 Pk / fuze proxy 的第一波方法输入和拒绝项 | [data_collection/kill_chain_proxy_methods/g5_r_source_scan_20260602.zh.md](data_collection/kill_chain_proxy_methods/g5_r_source_scan_20260602.zh.md) | source ids、class、scope、uncertainty/confidence、replacement rule 已列出；不写 Pk 曲线 |
| 24 | `G5-R-B-PROXY-BOUNDARY` | `G5-R` | `G5 research` | pass | 定义 Pk / fuze proxy 变量、事件链边界和 forbidden claims | [g5_research_pk_fuze_proxy_boundary_design_20260602.zh.md](g5_research_pk_fuze_proxy_boundary_design_20260602.zh.md) | proxy shape 已落盘；不替换 RNG hit gate，不创建 descriptor |
| 25 | `G5-R-C-EVENT-CHAIN-MAP` | `G5-R` | `G5 research` | pass | 将 terminal geometry、fuze proxy、G4 mechanism、G4 fragility 和 consequence 串成 event-chain map | [g5_research_event_chain_map_20260602.zh.md](g5_research_event_chain_map_20260602.zh.md) | 只允许 research proxy event chain；不写 mission-kill probability |
| 26 | `G5-R-D-UNCERTAINTY-AUDIT` | `G5-R` | `G5 research` | pass | 审查 G5 proxy 的 uncertainty、independence 和防误用边界 | [g5_research_uncertainty_independence_audit_20260602.zh.md](g5_research_uncertainty_independence_audit_20260602.zh.md) | audit 通过；source/model/scope/result uncertainty 均有边界 |
| 27 | `G5-R-INTEGRATION` | `G5-R` | `G5 research` | pass | 整合 G5-R source scan、boundary design、event-chain map 和 audit | [g5_research_integration_acceptance_20260602.zh.md](g5_research_integration_acceptance_20260602.zh.md) | `research_packet_accepted`；Pk / deterministic fuze authority 仍 false |

## 暂不分发

G2 收尾后，`TC-A2-BF-001..004` 同 scope 下不再追加临时收尾 wave。新的默认工作来自
`G4/G5 research` lane；当前已启动 `G5-R` proxy 分发。外部 reviewer/signoff packet 只在进入 fail-closed admission 流程时处理；
工业级 / release-grade 准入任务必须由用户明确启动。

| 任务簇 | 原因 |
|---|---|
| `TC-A2-AUTH-B` | 需要另起 release-grade `effect_scale_authority` promotion，不得混入当前 G2 |
| `TC-A2-AUTH-C` | 依赖 Stage C fragility truth / review closeout，当前仍 blocked |
| `TC-A2-KILLCHAIN` | `Pk` 与 deterministic fuze authority 仍是 boundary deferred；当前只启动 `G5-R` research proxy，不启动 authority 证据链 |

## Subagent 投递模板

### `TC-A2-BF-001-HASH`

负责修复 retained manifest integrity。不要重新审阅任务簇是否成立。

写入范围：

- `tools/maintenance/` 下新增或扩展 A2 retained manifest integrity checker；
- `tests/architecture/` 下新增对应测试；
- 仅在 checker 明确指出 hash mismatch 时更新相关 `retained_artifacts/**/manifest.json`。

验收：

- checker 输出 `missing_total=0`、`sha_mismatch_total=0`；
- authority guard 中任意 `*_authority*`、`stock_*`、`pk_*`、`fuze_*` 不得变为 true；
- 不移动 calibration narrative、source ledger 或 retained artifact 文件。

### `TC-A2-BF-004-PACKAGE`

负责整理 G2 candidate acceptance record。不要补写 G4/G5 结论。

写入范围：

- `candidate_acceptance_status.zh.md`
- `task_cluster_execution_status_20260601.zh.md`

验收：

- 明确 `TC-A2-BF-001..004` 是 `G2 candidate acceptance`，且 `G4/G5 authority deferred`；
- 记录 `RES-005/006` fail-closed 不被覆盖；
- 记录 `G3 residual` 只读取状态；
- 若 `TC-A2-BF-001-HASH` 未完成，不能声明 retained manifest 强验收通过。

### `TC-A2-BF-003-FAILCLOSED`

负责把 mechanism admission 的 fail-closed blocker 拆成下一轮执行项。

写入范围：

- blocker note 或 backlog 文档；
- 不修改 retained gate JSON，除非主线程明确要求重生 gate。

验收：

- 每个 blocker 有 owner、输入、输出、不得越界项；
- 不把 TP-21 / BEC-O comparison output 消费为 release evidence；
- 不授予 fragment/blast row authority。

### `TC-A2-BF-003-RES005-TP21`

负责生成 TP-21 selected-case admission 的 retained review packet。该任务只把缺失的
reviewer-selected case、preimage hash、selected-output anchor、independent review 和
allowed-output signoff 机器化，不关闭 `RES-005`。

写入范围：

- `tools/maintenance/a2_blastfrag_res005_tp21_selected_case_admission_gate.py`
- `tests/architecture/damage_model/test_benchmark_evidence_admission.py`
- `retained_artifacts/res005_tp21_selected_case_admission_20260601/**`

验收：

- retained manifest integrity 通过；
- `benchmark_consumed_for_release=false`；
- 不复制 TP-21 原文、表格、图或原始数值；
- authority guards 全 false。

### `TC-A2-BF-003-RES006-BECO`

负责生成 BEC-O replacement/tolerance admission 的 retained review packet。该任务只把
cached-vs-recalculated mismatch、lineage、allowed-output、tolerance 和 replacement signoff
缺口机器化，不关闭 `RES-006`。

写入范围：

- `tools/maintenance/a2_blastfrag_res006_beco_replacement_tolerance_admission_gate.py`
- `tests/architecture/damage_model/test_benchmark_recalculation_admission.py`
- `retained_artifacts/res006_beco_replacement_tolerance_admission_20260601/**`

验收：

- retained manifest integrity 通过；
- `benchmark_consumed_for_release=false`；
- 不保留 spreadsheet raw selected values、formula text、stdout/stderr、temporary workbook copy 或 raw output tables；
- authority guards 全 false。

### `TC-A2-RUNTIME-FINALIZE`

负责 G1 runtime 说明收口。

写入范围：

- `runtime_status.zh.md`
- 需要时补 runtime test 注释或断言名。

验收：

- `DamageReport` flags 被描述为 consequence/reporting flags；
- 不使用 `Pk calibrated`、`fuze released`、`authority promoted` 等措辞。
