# A2 高保真空战毁伤模型归档索引

状态：`2026-06-02 / archive_index / sealed_research_record / non-authoritative`。

本目录保存 A2 高保真空战毁伤模型子项目已经移出默认活跃分发路径的治理记录、
历史叙事和最终 research closeout。当前保留入口仍在：

- [../README.zh.md](../README.zh.md)

该入口是 sealed retained index，不再作为新的默认任务分发面。

## 索引

| 归档目录 | 角色 |
|---|---|
| [20260601_doc_governance](20260601_doc_governance/README.zh.md) | 文档治理归档；保存旧 Phase 叙事、旧 README、Phase 0 审计和历史 authority 状态快照 |
| [20260602_research_closeout](20260602_research_closeout/README.zh.md) | 子项目 research / candidate profile 最终收口记录；确认 G1..G5 research 均已封存为非权威完成面 |

## 使用规则

- 本归档只支持追溯、复核和恢复上下文，不作为默认任务分发入口；
- A2 目录不整体搬入 `archive/`，因为 maintenance tools、candidate bundle 和 retained
  artifact manifest 仍硬引用 `calibration/`、`data_collection/` 与 `retained_artifacts/`
  路径；
- 若未来用户明确要求 industrial / release-grade authority、stock descriptor、Pk 或
  deterministic fuze，再从 [../authority_promotion_backlog.zh.md](../authority_promotion_backlog.zh.md)
  另启新任务线；
- 若只是读取当前已完成状态，应以 [../README.zh.md](../README.zh.md) 和
  [20260602_research_closeout](20260602_research_closeout/README.zh.md) 为准。
