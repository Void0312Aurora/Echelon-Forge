# G4-R-B Mechanism-Load Envelope 分发包 - 2026-06-01

状态：`2026-06-01 / G4-R-B / research_packet_ready / research_candidate / replaceable_data`。

本文只分发 `G4-R-B` research lane 的 `fragment / blast mechanism-load envelope`
独立切片。当前目标是研究估计与可替换 source surface，不创建 runtime descriptor，
不写 stock row，不把公开方法来源改写成型号级真值。

## 范围

固定 scope：

| 项 | 当前值 |
|---|---|
| lane | `G4-R-B` / effect-scale and mechanism-load research envelope |
| profile | `research / candidate profile` |
| candidate scope | `F-16C_Block50` x `AIM-120C-class/blast_fragmentation` x `beam/high/near_miss_0_35m` |
| residual focus | `RES-005` fragment mechanism、`RES-006` blast mechanism |
| output class | non-authoritative, replaceable, auditable mechanism-load envelope |
| machine guard state | stock/runtime promotion guards remain false |

本切片允许整理公开、第三方、社区、开源配置、derived estimate 和 hash-only restricted
references，目标是形成可追溯、可替换、带 uncertainty / confidence / replacement rule 的
research envelope。`TP-21` 与 `BEC-O` 既有 retained/hash-only 材料只能作为
replacement target 或 fail-closed context，不得被消费为 release evidence。

非目标：

- 不把 `RES-005/006` 的工业级 admission 缺口当成当前 research 阻塞；
- 不把 TP-21 selected debris 或 BEC-O recalculation output admit 为 release-grade evidence；
- 不写 stock descriptor、runtime descriptor、calibration row 或 authority row；
- 不更新 `calibration_status`、candidate bundle authority guard 或 release readiness gate；
- 不复制受限来源的长段正文、表格、图、raw selected values 或 spreadsheet raw outputs。

## 输入

| 输入 | 用途 |
|---|---|
| [g4_g5_research_continuation_20260601.zh.md](g4_g5_research_continuation_20260601.zh.md) | `G4-R-B` research lane 入口和非权威边界 |
| [research_candidate_data_policy_20260601.zh.md](research_candidate_data_policy_20260601.zh.md) | Tier A/B/C/community/derived/hash-only 数据准入与 replaceability rule |
| [residual_register.zh.md](calibration/vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m/residual_register.zh.md) | `RES-005/006` 当前 research replacement target 与边界 |
| [mechanism_admission_failclosed_backlog_20260601.zh.md](mechanism_admission_failclosed_backlog_20260601.zh.md) | TP-21 / BEC-O retained blocker 与 signoff 缺口背景 |
| 既有 retained manifests / gate JSON | 仅作 hash-only context、guard audit 和 replacement target；不得提升为 release evidence |
| 新增公开/社区/工程来源候选 | 只允许进入 source ledger proposal 或 derived estimate manifest；必须标注 tier、rights、uncertainty、confidence、replacement rule |

每个新增候选数据项最少保留：

- stable `source_id` 或 artifact id；
- source ref、DOI/URL/ISBN/report id/code commit/hash-only locator；
- data class 与 source tier；
- rights / redistribution note；
- scope：target、weapon family、aspect、closure、miss-distance、mechanism、component；
- value type、单位、范围或 distribution；
- uncertainty、confidence、cross-check notes；
- affected residual ids；
- replacement rule：什么更好来源或 reviewer 输入可以 supersede 当前估计。

## 任务簇

| task id | owner | 目标 | write set | non-goals | validation | closure gate | round cap | status |
|---|---|---|---|---|---|---|---:|---|
| `G4-R-B-001-SOURCE-LEDGER-SCAN` | source-ledger worker + rights reviewer | 扫描可用于 fragment/blast mechanism-load envelope 的 Tier A/B/C/community/derived/hash-only 候选来源，形成可替换 source ledger proposal | [g4_research_mechanism_load_envelope_source_ledger_20260601.zh.md](g4_research_mechanism_load_envelope_source_ledger_20260601.zh.md)；本分发包不授权修改既有 source ledger、retained JSON、runtime 或 tests | 不复判 G1/G2/G3 是否完成；不复制受限 raw content；不消费 TP-21/BEC-O 为 release evidence；不写型号级真值 | ledger rows 必须含 source id、tier、rights、scope、value type、uncertainty、confidence、replacement rule；抽样检查 raw-content absence；确认 machine guard 未置真 | source ledger proposal 可审计、可替换，且每行都有 replacement rule；若 rights 或 provenance 不清，则该行标为 `hash_only_restricted_reference` 或 `candidate_rejected` | 1 | `pass` |
| `G4-R-B-002-DERIVED-ENVELOPE-DRAFT` | mechanism-load modeling worker | 基于已准入 candidate rows 起草 fragment / blast research envelope，区分 mechanism、units、range/distribution、assumption 和 uncertainty | [g4_research_mechanism_load_envelope_draft_20260601.zh.md](g4_research_mechanism_load_envelope_draft_20260601.zh.md)；不得写 runtime descriptor、stock descriptor、calibration row 或 retained gate JSON | 不拟合 authoritative effect scale；不把 community 或 derived estimate 写成型号级真值；不覆盖 Stage C component probability | envelope table 每项必须回链 source ids；单位与 scope 一致；给出 sensitivity / uncertainty note；标出不能支持的结论；检查无 machine guard 置真、release admission 置真或 stock descriptor 语义 | 产出 research envelope draft，且 fragment/blast 两侧都有 uncertainty、confidence、replacement rule 和 conflict notes；无法定量的项必须降级为 qualitative range 或 data gap | 1 | `pass` |
| `G4-R-B-003-VALIDATION-GUARD-AUDIT` | validation / governance worker | 审查 source-ledger proposal 与 envelope draft 是否保持 research-only、replaceable、rights-safe 和 guard-false | [g4_research_mechanism_load_envelope_validation_audit_20260601.zh.md](g4_research_mechanism_load_envelope_validation_audit_20260601.zh.md)；不得修改 candidate bundle、residual register、retained gates 或 tests，除非主线程另行授权 | 不把 audit pass 写成工业级准入；不新增 runtime checker；不把 TP-21/BEC-O retained context 改写为 release evidence | 文档 grep / review：禁止工业级准入词义、禁止 raw restricted values、禁止 release evidence consumption；比对 `RES-005/006` 仍只作为 research replacement target | audit 明确列出 pass / fail / residual risk；只有所有 guard 均 false、source rows 可替换、rights notes 完整时，才允许进入后续 research closeout review | 1 | `pass` |

## Worker Packet 要求

每个 worker 返回的 packet 必须包含：

- `task id`、owner、执行日期、round 编号；
- touched files 或 `write_set_empty=true`；
- 输入文件和 source ids；
- 新增或引用的数据行列表；
- 每个数据项的 tier、rights note、uncertainty、confidence、replacement rule；
- 是否包含 hash-only restricted references，以及 raw content absence 声明；
- affected residual ids，至少标注 `RES-005/006`；
- machine guard diff：fragment / blast / effect-scale / component probability / stock / Pk / fuze 全 false；
- validation commands 或人工审查清单；
- closure decision：`research_ready`、`needs_revision` 或 `blocked_waiting_source`；
- 明确说明是否仍不得用于 release evidence。

禁止在 worker packet 中出现：

- 任何 machine guard、release admission 或 stock descriptor guard 置真；
- 把 TP-21 / BEC-O comparison outputs 写成 release-consumed evidence；
- 未标注 source tier、rights、uncertainty 或 replacement rule 的数值；
- 受版权或再分发限制来源的正文、表格、图、raw selected values、spreadsheet raw outputs。

## 验证计划

1. Source-ledger scan 完成后，先审查每行是否满足 replaceability rule，并确认不含 raw restricted output。
2. Derived envelope draft 完成后，检查 envelope 的每个 numeric/range/qualitative claim 都能回链到 source ids。
3. Validation/guard audit 对两个前序产物做 cross-check：machine guard false、release consumption false、scope 不越界。
4. 若任何来源 rights 不清或冲突无法消解，降级为 `hash_only_restricted_reference`、`candidate_rejected` 或 data gap。
5. 若未来显式要求工业级准入，必须另转入 [authority_promotion_backlog.zh.md](authority_promotion_backlog.zh.md) 或新的准入任务，不得复用本 research packet 直接上卷。

建议的轻量检查：

- 搜索新增文档中的 machine guard 置真、release admission、stock descriptor、Pk 校准或 deterministic fuze 放行语义；
- 抽查 source rows 是否均含 `uncertainty`、`confidence`、`replacement rule`；
- 抽查 TP-21 / BEC-O 相关文字是否只作为 fail-closed context 或 replacement target；
- 确认 `RES-005/006` 未被写成工业级准入已完成。

## 验收标准

`G4-R-B` research mechanism-load envelope 切片只能在以下条件同时满足时进入后续
research closeout review：

- 三个任务均有 worker packet，且状态不是 `blocked_waiting_source`；
- source ledger proposal 覆盖 fragment 与 blast 两类 mechanism，且每行都有 source tier、
  rights、scope、uncertainty、confidence、replacement rule；
- derived envelope draft 明确单位、范围或 distribution、假设、冲突与 data gaps；
- validation/guard audit 明确 machine guards 全 false；
- `RES-005/006` 仍保留为 research profile 可替换路线；
- 没有 runtime descriptor、stock descriptor、release evidence consumption 或 row authority 声称。

本文档当前表示 `G4-R-B` 三个 research packet 均已完成，可作为 `G4-R-C`
surface draft 的机制载荷输入。它仍不是 stock/runtime 数据发布。

## 残余边界

| residual | 当前在本切片中的角色 | 不得越界 |
|---|---|---|
| `RES-005` | fragment mechanism-load research envelope 的 source / replacement target | 不 admit TP-21 selected debris outputs；不写 fragment row 或 component probability 真值 |
| `RES-006` | blast mechanism-load research envelope 的 source / replacement target | 不 admit BEC-O cached/recalculated comparison outputs；不写 blast row、effect-scale 或 component probability 真值 |
| `RES-009..012` | 后续 `G4-R-C` component fragility surface 关注项；本切片只提供 mechanism-load side input | 不关闭 Stage C probability truth、uncertainty 或 independent validation needs |
| `RES-013/014` | G5 research proxy 边界 | 不声明 Pk、deterministic fuze、mission-kill probability 或替代 RNG hit gate |

如果后续 worker 发现更强来源或外部 reviewer/signoff 输入，只能作为 replacement candidate
或另启工业级准入任务；不能在本 `G4-R-B` research dispatch 下直接上卷为 release-grade 结论。
