# A2 Authority Promotion Backlog

状态：`2026-06-02 / archived_project_backlog / G4-G5 authority / explicit_opt_in_only / non-authoritative`。

本文只登记未来 authority promotion 和 kill-chain authority 的阻塞条件。它不是当前
blastfrag candidate 包的未完成清单，也不授予任何 runtime authority。

当前项目默认保留 research / candidate profile，见
[research_candidate_data_policy_20260601.zh.md](research_candidate_data_policy_20260601.zh.md)。
因此本文中的 `G4/G5` 不再是默认下一步，也不阻塞当前 research 完成口径。只有用户明确要求
release-grade authority、stock runtime authority、Pk 或 deterministic fuze 时，才从本文另启任务线。

当前 G4/G5 research 已由
[g4_g5_research_continuation_20260601.zh.md](g4_g5_research_continuation_20260601.zh.md)
和 [archive closeout](archive/20260602_research_closeout/README.zh.md) 收口。若用户明确要求新的
研究级扩展，应先创建独立 follow-on 任务记录；不得直接重开本 sealed packet。

## 未来任务簇

| 任务簇 | 粒度 | 启动条件 | 验收标准 | 不属于本簇 |
|---|---|---|---|---|
| `TC-A2-AUTH-B` effect-scale promotion | `G4 authority promotion` | 明确另起 release-grade promotion，不和 `G2` candidate acceptance 混验收 | 至少正式处理 `RES-001/002/003/004/006/007/008` 和 `RES-010/011/012` 的 Stage B / effect-scale slice；`RES-005/006` 按 row / mechanism-load 依赖决定；descriptor / row 通过 schema、source、provenance、axis、scope、independent review 和 stock release gate | `component_failure_probability_authority`、Pk、deterministic fuze、跨 aspect/closure/miss-distance 外推 |
| `TC-A2-AUTH-C` component_failure_probability promotion | `G4 authority promotion` | effect-scale release gate 已关闭或被明确声明为前置依赖 | `RES-009/010/011/012` Stage C release-grade closeout；重新声明 `RES-005/006` mechanism-load admission / fail-closed 状态；component-specific row provenance、row 优先级、redundancy group、fragility truth、uncertainty 和 independent audit 可审计 | 越过 blocked Stage B、用 test-local exercise 冒充 stock authority、把 `component_failure_probability` 解释成 Pk |
| `TC-A2-KILLCHAIN` Pk / deterministic fuze | `G5 kill-chain authority` | 另有独立 Pk/fuze 证据链和验收文档 | `pk_authority` 或 `deterministic_fuze_authority` 只能由独立证据链放行；当前默认保持 false/deferred | 当前 blastfrag candidate 包、effect-scale、`component_failure_probability_authority`、runtime smoke、terminal reward、`DamageReport` 终局状态 |

## 当前不得上卷的内容

- `Stage B passed` 不等于 `effect_scale_authority released`；
- `Stage C test-local positive path` 不等于 `component_failure_probability` calibrated；
- `DamageReport` 终局 / 非终局消费可用不等于 `Pk` 已校准；
- fuze profile、fuze event 字段或 PN miss-distance baseline 不等于 deterministic fuze release；
- synthetic descriptor、schema fixture 或 aircraft JSON 自声明不能变成 stock authority。

## 未来放行前的最小证据

`G4` 放行前至少需要：

1. release-grade descriptor 和 row 集合；
2. source ledger、rights policy、payload hash、source/output boundary 的稳定引用；
3. retained artifact manifest 和 gate JSON；
4. scope / axis / bucket / mechanism-load gate 的机器可读 admission 结果；
5. independent review record；
6. regression 证明 stock runtime 默认仍 fail-closed；
7. 明确声明 `Pk` 和 deterministic fuze 是否仍保持 false。

`G5` 放行前必须另建任务线，不能从本 backlog 的 `G4` 条目顺手关闭。

## 历史审计

旧状态审计快照已归档：

- [current_authority_status_and_minimal_closeout_20260530.zh.md](archive/20260601_doc_governance/current_authority_status_and_minimal_closeout_20260530.zh.md)

未来如需恢复其中的细节，应先迁移到 retained gate / residual register；本 backlog
只登记未来 promotion blocker 和入口，不重新承载历史快照叙事。
