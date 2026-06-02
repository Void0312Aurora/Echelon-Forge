# A2 高保真空战毁伤模型

状态：`2026-06-02 / archived_sealed_index / research_profile_closed / G1-G5 research accepted / non-authoritative`。

本文是 A2 高保真空战毁伤模型子项目的 sealed retained 入口。该子项目在当前
research / candidate profile 下已完成并归档；本文只给出封存口径、阅读路径和恢复边界，
不再作为默认任务分发面，也不再承载完整 Phase 叙事、source pin 增量记录、
candidate package 明细或工业级准入待办。

## 当前口径

当前 A2 主线应按下面四句话理解：

1. `G1 runtime`：structured aircraft damage/effects runtime 主链已经进入维护路径；
2. `G2 candidate acceptance`：`AIM-120C-class blast_fragmentation -> F-16C_Block50`
   窄域候选包已收尾为 `accepted_non_authoritative`；`G3 residual` 只作为状态读取层，
   不是当前批次验收上限；
3. `G3 residual research closeout`：`RES-001..014` 已按 research 口径收尾；剩余
   industrial / release-grade 准入不作为当前完成条件；
4. `G4/G5 research`：机制载荷包络、组件脆弱性研究面以及 Pk / fuze proxy
   均已完成非权威 research packet / integration。

默认目标已收敛为 research / candidate model，而不是工业级或 release-grade 准入。
底层数据可以来自公开、第三方、社区或 derived estimate，但必须保持可替换、可扩展、
可追溯，并显式标注非权威边界。详见
[research candidate data policy](research_candidate_data_policy_20260601.zh.md)。
文档或工具中保留的 `authority_*` 字段只作为防误用 guard，不是当前工作进度或完成条件。

禁止把任何局部“闭合/收口”写成整个高保真 kill-chain 完成。除非明确标注 `G4` 或
`G5`，闭合只表示对应子层级完成。

## G2 收尾口径

`TC-A2-BF-001..004` 当前可写成 `candidate package accepted`，含义仅限：

- source / identity / retained evidence、scope / geometry / warhead evidence、mechanism
  admission fail-closed evidence、candidate bundle / regression 均有可审阅入口；
- retained manifest integrity、source admission audit、candidate bundle 和 runtime /
  engagement 回归在当前工作区通过；
- machine guards 继续全 false，且不创建 stock runtime descriptor。

不得把该结论写成 `G4 industrial admission completed`、`G5 kill-chain closed`、Pk calibration 或
deterministic fuze authority。

## 保留入口

| 文件 | 职责 |
|---|---|
| [任务粒度与协调总账](task_granularity_and_coordination_20260601.zh.md) | 定义 `G0..G5`、最终任务簇、文件优先级和冲突处理规则 |
| [任务簇分发包](task_cluster_dispatch_20260601.zh.md) | 已完成任务簇的保留分发记录；不再作为默认新增任务入口 |
| [任务簇执行状态](task_cluster_execution_status_20260601.zh.md) | 记录按任务簇分发和验证后的归档前就绪度 |
| [runtime 状态](runtime_status.zh.md) | 承接 `TC-A2-RUNTIME` / `G1` 的已维护工程面、回归面和非目标 |
| [Default effects modularization](default_effects_modularization/README.zh.md) | 已关闭归档的 `default_effects_model.cpp` 结构化拆分；包含 DFM-P4 fixture、DFM-P6 收口同步、DFM-P3F structure-spatial helper 与 debug early-return snapshot guard |
| [candidate 验收状态](candidate_acceptance_status.zh.md) | 承接当前 `TC-A2-BF-001..004` / `G2` 非权威候选包验收，并读取 `G3` residual 状态 |
| [G3 residual 收尾状态](g3_residual_closeout_status_20260601.zh.md) | 清点 `RES-001..014`，将 G3 台账收尾为当前 research profile 已闭合，并保留防误用边界 |
| [research candidate 数据策略](research_candidate_data_policy_20260601.zh.md) | 固化当前默认目标为 research / candidate，底层数据可替换、可扩展 |
| [G4/G5 research continuation](g4_g5_research_continuation_20260601.zh.md) | 记录已启动并收口的 G4/G5 research-only 延续；工业级准入不在当前目标内 |
| [G4 research dispatch](g4_research_dispatch_20260601.zh.md) | `G4 research` 中央分发入口；当前已收口为 `dispatch_closed_non_authoritative` |
| [G4 research integration acceptance](g4_research_integration_acceptance_20260601.zh.md) | 串行整合 G4-R-B/G4-R-C worker packet、验证结果和非权威边界 |
| [G4-R-B mechanism-load source scan](g4_research_mechanism_load_envelope_source_ledger_20260601.zh.md) | 第一波 fragment / blast mechanism-load research 来源整理 |
| [G4-R-B mechanism-load envelope draft](g4_research_mechanism_load_envelope_draft_20260601.zh.md) | 研究级 mechanism-load vector、assumption、uncertainty 与 replacement rule |
| [G4-R-B mechanism-load validation audit](g4_research_mechanism_load_envelope_validation_audit_20260601.zh.md) | 审查 G4-R-B source scan / envelope draft 的 research-only 边界 |
| [G4-R-C component fragility source scan](data_collection/component_fragility_vulnerability/g4_r_c_source_scan_20260601.zh.md) | 第一波 component fragility research 来源整理 |
| [G4-R-C component fragility surface draft](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/g4_r_c_component_fragility_surface_draft_20260601.zh.md) | 研究级 component fragility row shape 与 curve-family placeholders |
| [G4-R-C uncertainty / independence audit](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/g4_r_c_uncertainty_independence_audit_20260601.zh.md) | 审查 G4-R-C surface 的 uncertainty、independence 和防误用边界 |
| [G5 research dispatch](g5_research_dispatch_20260602.zh.md) | `G5 research` 中央分发入口；当前已收口为 `research_packet_accepted` |
| [G5-R source scan](data_collection/kill_chain_proxy_methods/g5_r_source_scan_20260602.zh.md) | 第一波 Pk / fuze proxy 方法来源、拒绝项和 replacement rule |
| [G5-R proxy boundary design](g5_research_pk_fuze_proxy_boundary_design_20260602.zh.md) | 研究级 kill-chain proxy 变量、事件链边界和 forbidden claims |
| [G5-R event-chain map](g5_research_event_chain_map_20260602.zh.md) | 串联 terminal geometry、fuze proxy、G4 mechanism、G4 component response 和 consequence surface |
| [G5-R uncertainty / independence audit](g5_research_uncertainty_independence_audit_20260602.zh.md) | 审查 G5 proxy chain 的不确定性、独立性和防误用边界 |
| [G5 research integration acceptance](g5_research_integration_acceptance_20260602.zh.md) | 串行整合 G5-R source/boundary/event-chain/audit packet 和验证结果 |
| [authority promotion backlog](authority_promotion_backlog.zh.md) | 历史/可选的工业级准入 backlog；不作为当前 research 完成条件 |
| [窄域 authority 边界](narrow_scope_authority_loop_aim120c_blastfrag_f16c_block50_20260529.zh.md) | 固定当前 weapon-target-scope 和防误用边界 |
| [Vulnerability evidence schema v1](vulnerability_evidence_schema_v1.zh.md) | 记录 descriptor / row 证据形状与当前禁用边界 |

## 证据源

| 证据面 | 保留入口 |
|---|---|
| source admission | [data_collection/README.zh.md](data_collection/README.zh.md) 和各 `source_ledger.zh.md` |
| validation / CI | [validation/a2_validation_ci_matrix_20260528.zh.md](validation/a2_validation_ci_matrix_20260528.zh.md) |
| BFM source trace gate | [validation/bfm_bm_006_source_trace_manifest_gate_20260528.zh.md](validation/bfm_bm_006_source_trace_manifest_gate_20260528.zh.md) |
| candidate package | [calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/README.zh.md](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/README.zh.md) |
| research 数据策略 | [research_candidate_data_policy_20260601.zh.md](research_candidate_data_policy_20260601.zh.md) |
| G3 台账收尾 | [g3_residual_closeout_status_20260601.zh.md](g3_residual_closeout_status_20260601.zh.md) |
| residual 状态 | [calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md) |
| retained artifacts | `calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/retained_artifacts/**/manifest.json` |

冲突时以 [任务粒度与协调总账](task_granularity_and_coordination_20260601.zh.md) 的证据优先级为准。

## 归档

最终 research closeout 记录：

- [archive/20260602_research_closeout/README.zh.md](archive/20260602_research_closeout/README.zh.md)

归档索引：

- [archive/README.zh.md](archive/README.zh.md)

历史 Phase 叙事、旧 README、Phase 0 审计、旧状态审计和中间 review note 已移入
[archive/20260601_doc_governance/README.zh.md](archive/20260601_doc_governance/README.zh.md)。
这些文件只作为历史证据，不再作为任务分发入口。

本轮暂不移动 `data_collection/**/source_pin_update*.zh.md`、
`guidance_miss_distance/*source_pin_integration*.zh.md`、`calibration/**/*.zh.md` 或
`retained_artifacts/**`，因为现有审计脚本和候选包工具会读取这些路径和命名。

归档后若要恢复工作，只允许两种路径：

- 用户明确要求工业级 / release-grade / stock / Pk / deterministic fuze authority 时，从
  [authority promotion backlog](authority_promotion_backlog.zh.md) 另启新任务；
- 用户明确要求新的 research expansion 时，先更新本 sealed 入口并新建独立 follow-on 记录。
