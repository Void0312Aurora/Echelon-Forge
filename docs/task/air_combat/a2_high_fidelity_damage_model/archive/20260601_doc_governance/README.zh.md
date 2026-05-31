# A2 文档治理归档 - 2026-06-01

本目录保存 A2 高保真杀伤模型子项目在 `2026-06-01` 文档治理中移出的历史叙事、
审计快照和中间 review note。

当前活跃入口：

- [../../README.zh.md](../../README.zh.md)

## 归档文件

| 文件 | 原角色 | 归档原因 |
|---|---|---|
| [README_legacy_runtime_narrative_20260601.zh.md](README_legacy_runtime_narrative_20260601.zh.md) | 旧中文总入口 | 承载过多 Phase/runtime/candidate/authority 叙事，已由薄 README 和状态文件替代 |
| [README_legacy_runtime_narrative_20260601.md](README_legacy_runtime_narrative_20260601.md) | 旧英文总入口 | 英文副本滞后，改为短入口后保留历史文本 |
| [high_fidelity_damage_model_cluster_20260526.zh.md](high_fidelity_damage_model_cluster_20260526.zh.md) | 旧任务簇总表 | 与粒度总账、runtime status、candidate status 和 backlog 重合 |
| [phase0_preflight_20260526.zh.md](phase0_preflight_20260526.zh.md) | Phase 0 预检审计 | 已完成的历史审计证据，不再作为任务分发入口 |
| [review_high_fidelity_requirements_20260526.zh.md](review_high_fidelity_requirements_20260526.zh.md) | 独立要求评审 | 保留为要求基线参考，不再作为执行计划入口 |
| [surface_incidence_evidence_gate_20260528.zh.md](surface_incidence_evidence_gate_20260528.zh.md) | surface-incidence row gate 进展记录 | 已并入 runtime / vulnerability / authority 边界叙事 |
| [current_authority_status_and_minimal_closeout_20260530.zh.md](current_authority_status_and_minimal_closeout_20260530.zh.md) | authority 状态审计快照 | 已由 `authority_promotion_backlog.zh.md` 承接活跃待办 |

## 使用规则

- 本目录文件可用于追溯历史判断，但不得作为新的任务分发入口；
- 若历史文件与 retained artifact manifest、residual register 或活跃入口冲突，以活跃入口和机器证据为准；
- 本轮未归档 `data_collection/**/source_pin_update*.zh.md`、`calibration/**/*.zh.md`
  或 `retained_artifacts/**`，因为它们仍受审计脚本和候选包工具读取。
