# A2 高保真空战毁伤模型

状态：`2026-06-01 / active_index / non-authoritative`。

本文是 A2 高保真空战毁伤模型子项目的活跃入口。它只给出当前口径和阅读路径，
不再承载完整 Phase 叙事、source pin 增量记录、candidate package 明细或
authority promotion 待办。

## 当前口径

当前 A2 主线应按下面四句话理解：

1. `G1 runtime`：structured aircraft damage/effects runtime 主链已经进入维护路径；
2. `G2 candidate acceptance`：`AIM-120C-class blast_fragmentation -> F-16C_Block50`
   窄域候选包已经具备可审阅、可复现、fail-closed 的非权威证据形状；`G3 residual`
   只作为状态读取层，不是当前批次验收上限；
3. `G4 authority promotion`：stock runtime `effect_scale_authority` 和
   `component_failure_probability_authority` 仍未放行；
4. `G5 kill-chain authority`：`Pk` 与 deterministic fuze 继续作为边界项，不属于
   当前 blastfrag candidate 包验收。

禁止把任何局部“闭合/收口”写成整个高保真 kill-chain 完成。除非明确标注 `G4` 或
`G5`，闭合只表示对应子层级完成。

## 活跃入口

| 文件 | 职责 |
|---|---|
| [任务粒度与协调总账](task_granularity_and_coordination_20260601.zh.md) | 定义 `G0..G5`、最终任务簇、文件优先级和冲突处理规则 |
| [任务簇分发包](task_cluster_dispatch_20260601.zh.md) | 将 `TC-A2-*` 拆成可交付 subagent / 主线程任务 |
| [任务簇执行状态](task_cluster_execution_status_20260601.zh.md) | 记录按新任务簇分发和验证后的当前就绪度 |
| [runtime 状态](runtime_status.zh.md) | 承接 `TC-A2-RUNTIME` / `G1` 的已维护工程面、回归面和非目标 |
| [Default effects modularization](default_effects_modularization/README.zh.md) | 固化 `default_effects_model.cpp` 结构化拆分、后续 fixture 和收口任务清单 |
| [candidate 验收状态](candidate_acceptance_status.zh.md) | 承接当前 `TC-A2-BF-001..004` / `G2` 非权威候选包验收，并读取 `G3` residual 状态 |
| [authority promotion backlog](authority_promotion_backlog.zh.md) | 登记未来 `TC-A2-AUTH-B`、`TC-A2-AUTH-C` 和 `TC-A2-KILLCHAIN` |
| [窄域 authority 边界](narrow_scope_authority_loop_aim120c_blastfrag_f16c_block50_20260529.zh.md) | 固定当前 weapon-target-scope 和不得越界的 authority 边界 |
| [Vulnerability evidence schema v1](vulnerability_evidence_schema_v1.zh.md) | 记录 descriptor / row 证据形状与当前禁用边界 |

## 证据源

| 证据面 | 活跃入口 |
|---|---|
| source admission | [data_collection/README.zh.md](data_collection/README.zh.md) 和各 `source_ledger.zh.md` |
| validation / CI | [validation/a2_validation_ci_matrix_20260528.zh.md](validation/a2_validation_ci_matrix_20260528.zh.md) |
| BFM source trace gate | [validation/bfm_bm_006_source_trace_manifest_gate_20260528.zh.md](validation/bfm_bm_006_source_trace_manifest_gate_20260528.zh.md) |
| candidate package | [calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/README.zh.md](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/README.zh.md) |
| residual 状态 | [calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md) |
| retained artifacts | `calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/retained_artifacts/**/manifest.json` |

冲突时以 [任务粒度与协调总账](task_granularity_and_coordination_20260601.zh.md) 的证据优先级为准。

## 归档

历史 Phase 叙事、旧 README、Phase 0 审计、旧状态审计和中间 review note 已移入
[archive/20260601_doc_governance/README.zh.md](archive/20260601_doc_governance/README.zh.md)。
这些文件只作为历史证据，不再作为任务分发入口。

本轮暂不移动 `data_collection/**/source_pin_update*.zh.md`、
`guidance_miss_distance/*source_pin_integration*.zh.md`、`calibration/**/*.zh.md` 或
`retained_artifacts/**`，因为现有审计脚本和候选包工具会读取这些路径和命名。
