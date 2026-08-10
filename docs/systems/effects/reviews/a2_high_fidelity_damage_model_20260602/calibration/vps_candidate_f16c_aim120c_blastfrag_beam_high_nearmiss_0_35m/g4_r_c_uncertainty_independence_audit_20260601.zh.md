# G4-R-C Uncertainty And Independence Audit - 2026-06-01

状态：`2026-06-01 / G4-R-C-AUDIT / pass / non-authoritative / research_only`。

本文审查 `G4-R-C` source scan 与 component fragility surface draft 的 uncertainty、
independence 和 research-only 边界。它不关闭工业级准入，不创建 runtime descriptor，不替换
`synthetic_sigmoid` baseline。

## Worker Packet

| 字段 | 内容 |
|---|---|
| task id | `G4-R-C-AUDIT` |
| owner | main-thread uncertainty and independence reviewer |
| touched files | 本文件 |
| 输入 | `data_collection/component_fragility_vulnerability/g4_r_c_source_scan_20260601.zh.md`；`g4_r_c_component_fragility_surface_draft_20260601.zh.md`；Stage C matrix / benchmark / uncertainty / independence docs |
| status | `pass` |
| closure decision | `research_ready` |
| remaining paths | `G4-R-C-INTEGRATE` can now run as a serial main-thread rollup |

## Uncertainty Ledger

| row id | uncertainty class | source | impact | mitigation / replacement trigger |
|---|---|---|---|---|
| `G4RC-UNC-SOURCE-001` | source / rights | FOI, textbooks, open papers and public program material have mixed rights and reuse limits | cannot retain raw tables or protected figures | keep source ids and self-written summaries; replace with open artifact/hash or reviewer-owned packet when available |
| `G4RC-UNC-SCOPE-002` | scope | many sources are transport, helicopter, civil safety, structure or generic survivability methods | cannot infer F-16C whole-aircraft truth | mark every row as method / consequence / analogy; require target-specific source before any stronger claim |
| `G4RC-UNC-MECHANISM-003` | mechanism-load | mechanism axes are proxy fields from `G4-R-B`, not measured warhead loads | probability surface cannot be calibrated from these axes alone | keep mechanism axis refs and assumptions; replace with scoped benchmark manifest if acquired |
| `G4RC-UNC-MODELFORM-004` | model form | sigmoid / threshold / piecewise families are placeholders | curve shape may bias downstream research estimates | retain multiple allowed curve families; require sensitivity table in future draft revisions |
| `G4RC-UNC-INDEPENDENCE-005` | independence | Stage C candidate rows, synthetic baseline and author-side outputs share project-local provenance | cannot become independent truth | keep Stage C inputs comparison-only; require reviewer-owned benchmark before any stronger use |
| `G4RC-UNC-COVERAGE-006` | coverage | current surface covers only candidate component scopes and consequence classes | missing many component groups and hit conditions | label rows as partial; add rows only when source ids and replacement rules exist |

## Independence Review

| layer | artifact / input | allowed role | forbidden role | audit result |
|---|---|---|---|---|
| source scan | `g4_r_c_source_scan_20260601.zh.md` | source proposal and rejected-source ledger | component probability truth | `pass` |
| mechanism load | `g4_research_mechanism_load_envelope_draft_20260601.zh.md` | mechanism-axis research input | measured warhead / target load | `pass` |
| surface draft | `g4_r_c_component_fragility_surface_draft_20260601.zh.md` | research row shape and placeholder curve family | stock/runtime descriptor | `pass` |
| Stage C matrix | `validation_fragility_matrix_stage_c_component_probability_20260531.zh.md` | component naming and comparison boundary | independent review result | `pass` |
| synthetic baseline | existing Stage C baseline | comparator / current stock baseline | independent truth | `pass` |
| author-side benchmark | `validation_fragility_benchmark_stage_c_component_probability_20260531.zh.md` | delta / repeatability evidence | benchmark truth | `pass` |

## Guard Review

| check | result |
|---|---|
| no runtime descriptor created | `pass` |
| no stock row written | `pass` |
| no calibrated probability claimed | `pass` |
| no game / forum / restricted source used | `pass` |
| no raw protected table, figure, long prose or selected value retained | `pass` |
| every surface row has replacement rule | `pass` |
| every surface row links source rows and mechanism axis refs | `pass` |

## Research Acceptance

`G4-R-C` now has:

- source scan packet: `pass`;
- surface draft: `pass`;
- uncertainty / independence audit: `pass`.

The surface is ready for serial integration as a research packet. It remains unsuitable for stock/runtime
or calibrated component probability use.
