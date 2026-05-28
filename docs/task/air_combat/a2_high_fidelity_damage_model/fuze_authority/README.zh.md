# A2 deterministic fuze / P4 放行条件文档包

状态：`2026-05-28` 计划/标准文档。本文档包定义 A2 deterministic fuze / Phase 4 的放行证据、schema 草案、回放准入矩阵和残余风险；它不是实现记录，不代表 deterministic fuze 已放行，也不得作为移除现有 RNG hit gate 的授权依据。

## 文档边界

本目录只讨论 fuze authority。它不定义 vulnerability descriptor，不扩展 vulnerability evidence schema，也不把 Pk、component failure probability 或 vulnerability scale 当作引信放行依据。P4 放行必须有独立的 fuze authority schema / manifest、fuze evidence、replay/admission 结果和残余风险签核。

当前 vulnerability descriptor 可以证明 vulnerability / Pk 数据通路是否有权威；它不能替代 fuze trigger、target signature、contact surface、timed setting、fuze reliability 或 replay determinism 证据。

## 文件列表

- [当前 fuze runtime/event 覆盖与 deferred 原因](current_fuze_runtime_event_coverage_20260528.zh.md)
- [独立 fuze authority schema / manifest 草案](fuze_authority_schema_manifest_draft_20260528.zh.md)
- [radar / laser / contact / timed 放行证据清单](fuze_release_evidence_checklist_20260528.zh.md)
- [replay / admission matrix](replay_admission_matrix_20260528.zh.md)
- [residual risks](residual_risks_20260528.zh.md)
- [authority gap update](authority_gap_update_20260528.zh.md)

## P4 总体判定

当前判定：`deterministic_fuze_authority = not_admitted / deferred`。

允许继续使用的内容：

- `FuzeProfile` runtime / event 审计字段；
- proximity / radar_proximity / laser_proximity / contact / impact / timed 的最小触发语义分支；
- `EffectsEvent` 中的 miss distance、nearest approach、detonation time、fuze type、trigger radius、delay、reliability、signature proxy、contact surface evidence 等诊断字段；
- 用于 future admission 的测试 fixture、schema fixture 和 replay 设计。

不允许据此做的事：

- 不允许宣称 deterministic fuze 已完成；
- 不允许把 vulnerability descriptor 的 `deterministic_fuze_authority` 字段当作 P4 放行；
- 不允许仅凭 PN miss-distance baseline 或 fuze profile 字段移除 RNG hit roll；
- 不允许把 synthetic / engineering proxy / schema fixture 当作校准引信证据；
- 不允许让训练 smoke 的单发 combat-win 结果成为引信放行标准。
