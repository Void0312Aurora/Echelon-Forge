# A2 G4/G5 Research Continuation - 2026-06-01

状态：`2026-06-01 / G4 research accepted / G5 deferred / research_only / replaceable_data`。

本文只定义 `G4/G5` 的研究级延续入口。它不启动 release-grade 准入，
不创建 runtime descriptor，不把 stock / Pk / deterministic fuze 等机器 guard 置真。
这些 `authority_*` 词只对应仓库既有机器 guard 和历史 backlog；在当前用户确认的
research 口径下，它们不是完成条件。

当前前提：

- `G1/G2/G3` 已作为 research / candidate profile 的当前完成面；
- `RES-001..014` 已按当前研究口径收尾为 `research_closed_authority_retained`；
- 底层数据允许使用公开、第三方、社区、开源配置和 derived estimate，但必须可追溯、
  可替换、带 uncertainty / confidence 和 replacement rule；
- 工业级 / release-grade 准入只在用户明确要求时另启。

当前 G4 research 分发入口：

- [G4 research dispatch](g4_research_dispatch_20260601.zh.md)
- `G4-R-B`: [mechanism-load envelope dispatch](g4_research_mechanism_load_envelope_dispatch_20260601.zh.md)
- `G4-R-B-001`: [mechanism-load source scan](g4_research_mechanism_load_envelope_source_ledger_20260601.zh.md)
- `G4-R-B-002`: [mechanism-load envelope draft](g4_research_mechanism_load_envelope_draft_20260601.zh.md)
- `G4-R-B-003`: [mechanism-load validation audit](g4_research_mechanism_load_envelope_validation_audit_20260601.zh.md)
- `G4-R-C`: [component fragility dispatch](g4_research_component_fragility_dispatch_20260601.zh.md)
- `G4-R-C-SCAN`: [component fragility source scan](data_collection/component_fragility_vulnerability/g4_r_c_source_scan_20260601.zh.md)
- `G4-R-C-SURFACE`: [component fragility surface draft](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/g4_r_c_component_fragility_surface_draft_20260601.zh.md)
- `G4-R-C-AUDIT`: [component fragility uncertainty / independence audit](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/g4_r_c_uncertainty_independence_audit_20260601.zh.md)
- `G4-R-INTEGRATION`: [G4 research integration acceptance](g4_research_integration_acceptance_20260601.zh.md)

## Boundary Decision

接下来可以启动的是 `G4/G5 research lane`。工业级准入不在当前目标内，只保留为
防误用边界。

| lane | 研究级目标 | 可用数据 | 不得声称 |
|---|---|---|---|
| `G4-R-B` mechanism-load envelope | 为 `RES-005/006` 形成 fragment / blast research load envelope，并让参数、source tier、uncertainty 和 replacement rule 可审计 | Tier A 方法、Tier B 工程公开资料、Tier C/community sanity check、derived estimate、hash-only restricted references | 型号级真值、release-consumed TP-21/BEC-O evidence、stock descriptor |
| `G4-R-C` component fragility surface | 为 `RES-009..012` 形成 research component fragility surface、uncertainty ledger 和 independent-input note | 公开 LFTE/MSVV 方法、论文、社区/开源 fragility sanity envelope、derived sigmoid / threshold surface | calibrated component probability、aircraft-wide fragility truth、Stage C release-grade closeout |
| `G5-R` kill-chain proxy | 形成 Pk / fuze proxy 的研究设计，明确哪些变量、事件和不确定性会进入未来 kill-chain | 公开方法、游戏外推禁用清单、社区 sanity envelope、simulation-derived proxy | calibrated Pk、deterministic fuze、mission-kill probability |

## Start Conditions

可以开始 `G4/G5 research lane` 的条件：

- 当前 candidate bundle 继续输出 `candidate_non_authoritative_bundle`；
- `research_blocker_residual_ids=[]`；
- 机器 guard 保持 false，不把研究估计写入 stock/runtime；
- source admission 允许 Tier B/C/community/derived estimate，但 ledger 必须标注非权威；
- 每个新增数据项有 replacement rule。

若未来另行启动工业级准入，仍需独立来源、rights / allowed-output、release-grade
validation、review record、residual closeout 和 stock gate；这些不属于当前 research lane。

## First Research Work Items

| id | 目标 | 输出 | 验收 |
|---|---|---|---|
| `G4-R-B-001..003` | 建立 fragment / blast mechanism-load source scan、derived envelope 和 guard audit | [source scan](g4_research_mechanism_load_envelope_source_ledger_20260601.zh.md)、[envelope draft](g4_research_mechanism_load_envelope_draft_20260601.zh.md)、[validation audit](g4_research_mechanism_load_envelope_validation_audit_20260601.zh.md) | 已完成 research packet，可作为 `G4-R-C` mechanism side input |
| `G4-R-C-SCAN/SURFACE/AUDIT` | 建立 component fragility source scan、surface draft 和 uncertainty / independence audit | [source scan](data_collection/component_fragility_vulnerability/g4_r_c_source_scan_20260601.zh.md)、[surface draft](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/g4_r_c_component_fragility_surface_draft_20260601.zh.md)、[audit](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/g4_r_c_uncertainty_independence_audit_20260601.zh.md) | 已完成核心 research packet，并通过 [G4 integration acceptance](g4_research_integration_acceptance_20260601.zh.md) |
| `G5-R-001` | 建立 Pk / fuze proxy boundary design | proxy variables、event chain、forbidden claims、data needs | `RES-013/014` 保持 out-of-scope / boundary deferred；不替换 RNG hit gate |

## Acceptance

研究级 G4/G5 延续可以被视为完成单个工作项时，必须同时满足：

- 输出中没有 machine guard 置真或 stock descriptor 写入；
- source tier、scope、uncertainty、confidence 和 replacement rule 齐全；
- residual 状态仍区分 research closed、research out-of-scope 和未来可选准入边界；
- 文档明确该工作项只支持 research model，不支持 release-grade claim。

任何要把上述研究结果提升为工业级 runtime / stock 写入的尝试，都必须转入
[authority_promotion_backlog.zh.md](authority_promotion_backlog.zh.md) 或新的准入任务，并另设 gate。
