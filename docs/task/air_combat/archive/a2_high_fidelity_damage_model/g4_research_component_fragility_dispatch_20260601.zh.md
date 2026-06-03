# A2 G4-R-C Component Fragility Research Surface 分发包 - 2026-06-01

状态：`2026-06-01 / research_packet_accepted / G4-R-C / research_candidate / replaceable_data`。

本文只分发 `G4-R-C component fragility research surface` 的研究级工作。它不启动
工业级 / release-grade 准入任务，不创建 runtime descriptor，不写 stock row，不把
Stage C test-local 或公开方法示例改写成 F-16C 全机组件概率真值。

## 范围

目标是在当前 A2 research / candidate profile 下，为 `RES-009..012` 准备一个可审计、
可替换、非权威的 component fragility research surface，并同步 uncertainty ledger 与
independent-input note。

允许产物：

- 公开 LFTE / MSVV 方法、论文、Tier B/C/community/open-source sanity envelope 的来源扫描；
- derived sigmoid / threshold / piecewise surface 草案，但必须记录输入、算法、单位、
  uncertainty、confidence 和 replacement rule；
- component fragility candidate table、uncertainty ledger、independence audit note；
- 对既有 Stage C test-local row 的边界说明。

禁止产物：

- calibrated component probability authority；
- aircraft-wide fragility truth；
- stock/runtime descriptor 或 stock database row；
- Stage C release-grade closeout；
- 把 `right_aileron_actuator` 的 test-local candidate row 上卷为 F-16C 全机真值；
- 复制受版权保护报告、教材、工具输出或受控材料的表格、图、长段正文或 raw selected values。

## 输入

必读输入：

| 输入 | 用途 |
|---|---|
| `docs/agent/README.zh.md` | Agent 操作入口和维护规则。 |
| `docs/agent/rules/document_authority_map.zh.md` | 文档权威层级、能力声明门槛和委派阅读路径。 |
| `docs/standards/governance/subagent_usage_policy.zh.md` | 有限任务簇、worker packet、轮次和模型/思考预算规则。 |
| `g4_g5_research_continuation_20260601.zh.md` | 定义 `G4-R-C` 为 research lane；工业级准入不在当前目标内。 |
| `research_candidate_data_policy_20260601.zh.md` | 定义 Tier A/B/C、derived estimate、hash-only 和 replacement rule。 |
| `calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md` | `RES-009..012` 的当前 blocked / non-authoritative 边界。 |

候选数据与 Stage C 参考输入：

| 输入 | 当前可用解释 |
|---|---|
| `data_collection/component_fragility_vulnerability/source_ledger.zh.md` | 公开 component fragility / validation criteria 候选与拒绝清单。 |
| `data_collection/component_fragility_benchmark_methods/source_ledger.zh.md` | LFTE、MSVV、FOI、NASA、FAA、论文与拒绝来源的 method ledger。 |
| `vulnerability_evidence_schema_v1.zh.md` | 研究表面可借用的 descriptor / row 字段形状；本任务不得创建 descriptor。 |
| `calibration/.../validation_fragility_matrix_stage_c_component_probability_20260531.zh.md` | Stage C `right_aileron_actuator` candidate review matrix；只作边界输入。 |
| `calibration/.../validation_fragility_benchmark_stage_c_component_probability_20260531.zh.md` | candidate-vs-`synthetic_sigmoid` delta evidence；不是 independent truth。 |
| `calibration/.../validation_uncertainty_closeout_stage_c_component_probability_20260531.zh.md` | author-side repeatability probe 与 uncertainty closeout plan。 |
| `calibration/.../validation_independence_trace_stage_c_component_probability_20260531.zh.md` | input/result/reviewer layer separation trace。 |

## 任务簇表

| 任务 ID | 任务 | Owner | Model / reasoning | 拟派发写集 | Non-goals | Validation | Closure gate | Round cap | Status |
|---|---|---|---|---|---|---|---|---:|---|
| `G4-R-C-SCAN` | source/data scan | source ledger worker | `gpt-5.4-mini / xhigh` | [data_collection/component_fragility_vulnerability/g4_r_c_source_scan_20260601.zh.md](data_collection/component_fragility_vulnerability/g4_r_c_source_scan_20260601.zh.md) | 不新增 runtime row；不从受控/JMEM/J-ACE/AJEM/COVART/游戏/论坛材料抽取参数；不把 Tier C sanity 变成校准来源。 | `git diff --check -- <write_set>`；source ids 全部有 tier、rights、scope、uncertainty/confidence、replacement rule；拒绝项保持 rejected/sanity-only。 | 已列出 Tier A method references、Tier B sanity candidates、derived-estimate allowed inputs 和 rejected sources；每条可用输入说明能支持的字段与不能支持的 claim。 | 1 | `pass` |
| `G4-R-C-SURFACE` | fragility surface draft | research surface worker | `gpt-5.4 / high` | [calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/g4_r_c_component_fragility_surface_draft_20260601.zh.md](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/g4_r_c_component_fragility_surface_draft_20260601.zh.md) | 不写 stock descriptor；machine guard 保持 false；不替换 `synthetic_sigmoid` baseline；不宣称 `right_aileron_actuator` row 是全机 truth。 | `git diff --check -- <write_set>`；surface row 均有 source ids、mechanism-load axis、component scope、function/consequence scope、uncertainty/confidence、replacement rule；显式标注 `non_authoritative_research_surface`。 | 输出 candidate table 与公式/算法说明；derived sigmoid/threshold 参数可追溯到 scan 输入；所有 probabilities 只为 research estimates，且 `industrial_admission=false`；同时必须允许数据替换。 | 2 | `pass` |
| `G4-R-C-AUDIT` | uncertainty / independence audit | uncertainty and independence reviewer | `gpt-5.4 / high` | [calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/g4_r_c_uncertainty_independence_audit_20260601.zh.md](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/g4_r_c_uncertainty_independence_audit_20260601.zh.md) | 不把 `RES-009..012` 写成工业级已准入；不把 author-side repeatability probe 写成 uncertainty truth；不把 candidate-vs-synthetic delta 写成 benchmark truth。 | `git diff --check -- <write_set>`；ledger 覆盖 epistemic/aleatory/source/scope/model-form uncertainty；独立性检查证明输入、tuning、output、reviewer notes 不循环。 | 每条 surface row 有 uncertainty class、confidence、sensitivity/replacement trigger；independence note 明确 Stage C test-local row、synthetic baseline、derived surface 和 independent truth 的区别。 | 1 | `pass` |
| `G4-R-C-INTEGRATE` | research packet integration and boundary review | main-thread integration owner | `gpt-5.4 / high` | [g4_research_integration_acceptance_20260601.zh.md](g4_research_integration_acceptance_20260601.zh.md) 与状态同步；不得由并行 worker 改写同一表格 | 不做工业级准入；不把 partial packet 当 pass；不修改 retained artifacts。 | 本地复验 worker packet；`git diff --check`；guard 搜索不得出现 machine guard true / calibrated descriptor claim。 | 三个核心 packet 均已返回完整 packet；integration owner 已完成最终验证并标记 accepted。 | 1 | `pass` |

并行边界：`G4-R-C-SCAN` 必须先行，`G4-R-C-SURFACE` 与 `G4-R-C-AUDIT` 可在 scan
返回完整 packet 后并行；`G4-R-C-INTEGRATE` 串行。

## Worker Packet 要求

每个 worker 必须返回：

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

额外要求：

- `status=pass` 只表示被分配切片完成，不解锁工业级准入；
- `partial` 只能作为证据，不得让 integration 标记完成；
- `blocked` 必须说明 blocker、owner、replacement path、失败或缺失的 guard、forced review trigger；
- 每个新增 source 或 derived value 必须有 stable id、source ref、tier/data class、rights note、
  scope、value type、uncertainty/confidence、cross-check note、affected residuals 和 replacement rule；
- 所有概率、阈值、sigmoid 参数和 surface row 必须标注 `non_authoritative_research_estimate` 或等价字段；
- 不得编辑其他 worker 的写集，不得移动 calibration narrative、source ledger 或 retained artifacts。

## 验证计划

最低验证：

```bash
git diff --check -- docs/task/air_combat/archive/a2_high_fidelity_damage_model
rg -n "authorit[y]=true|component_failure_probability_authorit[y].*true|stock_descriptor_create[d].*true|calibration_statu[s].*calibrated|authority_admissio[n].*true|industrial_admissio[n].*true|replacement_allowe[d].*false" docs/task/air_combat/archive/a2_high_fidelity_damage_model
```

integration owner 还应检查：

- 每个 worker packet 的 touched files 只落在分配写集内；
- source scan 没有复制受限原文、表格、图片或 raw selected values；
- surface draft 没有 runtime descriptor、stock database row 或 aircraft-wide truth 文案；
- uncertainty / independence audit 没有把 author-side result、test-local fixture 或 synthetic baseline 写成 independent truth；
- `RES-009..012` 仍保持 research 可推进、工业级准入不在当前目标内的解释。

## 验收标准

`G4-R-C` research slice 只能在同时满足以下条件时从 `planned` 更新为 research-level accepted：

- 三个核心任务均有完整 worker packet，且 integration owner 本地复验通过；
- research surface 的每个 row 都能追溯到 source ids 或 derived-estimate manifest；
- 每个 row 都有 scope、unit/value type、uncertainty、confidence 和 replacement rule；
- source tier、rights 和 rejected/sanity-only 来源边界清楚；
- Stage C test-local rows 只作为 comparison / boundary input，不上卷为 truth；
- machine guards 全 false，且没有 runtime descriptor 或 stock row 写入；
- 文档明确本切片只支持 research model，不支持 release-grade claim。

## 残余边界

本分发包保留以下边界，不把它们写成工业级已准入：

| Residual | 当前解释 | 本切片最多能提供 | 仍不得声称 |
|---|---|---|---|
| `RES-009` | component fragility truth 不作为当前 research 完成条件 | research surface 与 replacement path | calibrated component probability truth |
| `RES-010` | formal Stage C result promotion 不在本轮 | reviewer-ready result structure 与 validation needs | Stage C release-grade closeout |
| `RES-011` | probability uncertainty coverage 作为 research ledger 继续完善 | uncertainty ledger、coverage plan、sensitivity triggers | reviewer-accepted uncertainty truth |
| `RES-012` | result-level independence 作为 audit note 继续完善 | input/result/reviewer separation note | independent fragility truth 或 non-circular signoff |

任何把本研究表面提升到工业级 runtime / stock 写入的请求，必须转入
`authority_promotion_backlog.zh.md` 或新的显式准入任务，并重新建立 source、rights /
allowed-output、release-grade validation、review record、residual closeout 和 stock gate。
