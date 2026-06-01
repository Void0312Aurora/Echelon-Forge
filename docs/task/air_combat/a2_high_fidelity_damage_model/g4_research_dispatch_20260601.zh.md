# A2 G4 Research Dispatch - 2026-06-01

状态：`2026-06-01 / dispatch_closed_non_authoritative / research_only / replaceable_data`。

本文是 A2 进入 `G4 research` 的中央分发包。它只启动研究级、可替换、非权威的数据面工作；
不启动工业级 / release-grade 准入任务。文档或工具中保留的 `authority_*` 字段只作为
机器 guard，防止研究估计被误写成 stock/runtime 真值。

父入口：

- [G4/G5 research continuation](g4_g5_research_continuation_20260601.zh.md)
- [research candidate data policy](research_candidate_data_policy_20260601.zh.md)
- [G3 residual closeout status](g3_residual_closeout_status_20260601.zh.md)
- [residual register](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md)

## Boundary Decision

`G4` 本轮只按 research lane 分发：

- `G4-R-B`：fragment / blast mechanism-load envelope；
- `G4-R-C`：component fragility research surface；
- `G5-R`：暂不在本轮分发，只保留后续 proxy design 入口。

本轮不得写成：

- effect scale 或 component probability 已校准；
- fragment / blast row 已成为型号级真值；
- calibrated component probability；
- stock descriptor created；
- Pk 或 deterministic fuze 已完成。

## Dispatch Matrix

| Task | Grain | Owner | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
|---|---|---|---|---|---|---|---|---|---:|---|
| `G4-R-B-DISPATCH` | `G4 research` | worker / mechanism-load dispatch owner | 拆出 fragment / blast mechanism-load envelope 工作包 | `g4_research_mechanism_load_envelope_dispatch_20260601.zh.md` | 不写 source truth；不 consume TP-21/BEC-O 为 release evidence；不写 stock/runtime | 文档包含 source scan、derived envelope、guard audit 三个子任务；链接当前 policy/residual | 分发包存在且所有子任务有 write set、validation、closure gate、round cap | 可与 `G4-R-C-DISPATCH` 并行；中央入口串行整合 | 1 | `dispatched` |
| `G4-R-B-001-SOURCE-LEDGER-SCAN` | `G4 research` | main-thread source scan | 把既有公开来源账本整理成 mechanism-load source proposal | `g4_research_mechanism_load_envelope_source_ledger_20260601.zh.md` | 不写数值 row；不复制受限内容；不把方法来源改写为型号级真值 | source rows 均有 source ids、tier/rights、scope、uncertainty/confidence、replacement rule | source proposal 已落盘，可作为 derived envelope draft 输入 | `G4-R-B-002` 依赖本项 | 1 | `pass` |
| `G4-R-B-002-DERIVED-ENVELOPE-DRAFT` | `G4 research` | main-thread modeling worker | 把 mechanism source proposal 整理成 research mechanism-load vector | `g4_research_mechanism_load_envelope_draft_20260601.zh.md` | 不写真实 blast / fragment 参数；不创建 descriptor；不消费 TP-21/BEC-O 输出 | 每个 envelope field 有 source rows、assumptions、uncertainty/confidence、replacement rule | draft 已落盘，可作为 G4-R-C mechanism axis 输入 | `G4-R-B-003` 依赖本项 | 1 | `pass` |
| `G4-R-B-003-VALIDATION-GUARD-AUDIT` | `G4 research` | main-thread validation worker | 审查 mechanism-load source scan 与 envelope draft 的 research-only 边界 | `g4_research_mechanism_load_envelope_validation_audit_20260601.zh.md` | 不做工业级准入；不新增 runtime checker | audit 确认 no stock/runtime write、no raw output、no truth overclaim | `G4-R-B` 可作为 research-ready mechanism side input | 依赖 `G4-R-B-001/002` | 1 | `pass` |
| `G4-R-C-DISPATCH` | `G4 research` | worker / component-fragility dispatch owner | 拆出 component fragility surface 与 uncertainty ledger 工作包 | `g4_research_component_fragility_dispatch_20260601.zh.md` | 不写 calibrated component probability；不创建 descriptor；不把 Stage C row 上卷成 aircraft truth | 文档包含 source/data scan、surface draft、uncertainty/independence audit 三个子任务；链接当前 policy/residual | 分发包存在且所有子任务有 write set、validation、closure gate、round cap | 可与 `G4-R-B-DISPATCH` 并行；中央入口串行整合 | 1 | `dispatched` |
| `G4-R-C-SCAN` | `G4 research` | main-thread source scan | 把既有公开 component fragility 来源整理成 surface source proposal | `data_collection/component_fragility_vulnerability/g4_r_c_source_scan_20260601.zh.md` | 不写 runtime row；不从受控/游戏/论坛材料抽参数；不把示例概率变成 F-16C 真值 | source rows 均有 source ids、tier/rights、scope、uncertainty/confidence、replacement rule | source proposal 已落盘，`G4-R-C-SURFACE` 与 `G4-R-C-AUDIT` 可继续分发 | `G4-R-C-SURFACE/AUDIT` 依赖本项 | 1 | `pass` |
| `G4-R-C-SURFACE` | `G4 research` | main-thread surface worker | 起草 component fragility research surface row shape 与 curve-family placeholders | `calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/g4_r_c_component_fragility_surface_draft_20260601.zh.md` | 不写 calibrated probability；不替换 `synthetic_sigmoid`；不写 stock row | every row links source rows、mechanism axis refs、uncertainty/confidence、replacement rule | surface draft 已落盘，可进入 audit/integration | 依赖 `G4-R-C-SCAN` 与 `G4-R-B` mechanism axis | 2 | `pass` |
| `G4-R-C-AUDIT` | `G4 research` | main-thread uncertainty reviewer | 审查 surface draft 的 uncertainty、independence 和 research-only 边界 | `calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/g4_r_c_uncertainty_independence_audit_20260601.zh.md` | 不关闭工业级准入；不把 author-side result 写成 independent truth | uncertainty ledger and independence review all pass for research use | `G4-R-C` 可进入 serial integration | 依赖 `G4-R-C-SCAN/SURFACE` | 1 | `pass` |
| `G4-R-INTEGRATION` | `G4 research` | main thread | 把 G4 research 分发入口接入 README、dispatch、execution status 和 validation command list | `README.zh.md`、`task_cluster_dispatch_20260601.zh.md`、`task_cluster_execution_status_20260601.zh.md`、[g4_research_integration_acceptance_20260601.zh.md](g4_research_integration_acceptance_20260601.zh.md)、本文件 | 不启动工业级准入 backlog；不移动 calibration/retained artifacts | retained manifest integrity、candidate bundle、source admission、相关 doc grep / diff check | 中央入口已说明 G4 research 分发完成，工业级准入不在当前目标内 | 依赖两个分发包；最终串行 | 1 | `pass` |

## Worker Packet Requirements

每个 G4 research worker 返回：

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
research boundary confirmation:
```

worker 只需确认没有把 research estimate 写成 stock/runtime 真值。

## Validation Plan

```bash
python tools/maintenance/a2_retained_manifest_integrity.py
python tools/maintenance/a2_source_admission_audit.py --strict
python tools/maintenance/a2_candidate_vps_bundle.py
python -m pytest -q tests/architecture/test_a2_candidate_vps_bundle.py tests/architecture/test_a2_source_admission_audit.py tests/architecture/test_a2_retained_manifest_integrity.py
git diff --check
```

## Acceptance Criteria

本轮 G4 research 分发可以收口为 `dispatch_closed_non_authoritative`，仅当：

- `G4-R-B` 和 `G4-R-C` 分发包都存在；
- 每个分发包都保留 research-only / replaceable data 边界；
- candidate bundle 仍输出 `research_blocker_residual_ids=[]`；
- stock/effect/component/Pk/fuze machine guards 全 false；
- retained manifest integrity 和 source admission audit 通过。

## Residual Boundary

- `RES-005/006`：research envelope 可以推进；TP-21 / BEC-O 只作为 replacement target 或 hash-only context。
- `RES-009..012`：research fragility surface 可以推进；Stage C test-local row 只作为 comparison / boundary input。
- `RES-013/014`：本轮不分发；保持 G5 research proxy 的后续边界。
