# P11 期望包络候选重基线审计

- 状态：`p11_expectation_rebaseline_candidate_ready_for_review`；候选可供人工审查：`True`。
- 来源：`integrated_structure_passed_residuals_open`，`93` cells；跨三种子稳定 `93`。
- 观测状态计数：`{'complete_effect_chain': 63, 'in_radius_fuze_blocked': 2, 'outside_no_load': 28}`。
- 候选 N/M/O：`{'M': 2, 'N': 63, 'O': 28}`；旧标签发生变化的 cells：`49`。
- 旧→候选转移：`{'M->N': 27, 'M->O': 4, 'N->N': 20, 'O->M': 2, 'O->N': 16, 'O->O': 24}`。
- 候选角度拓扑单调：`True`；违规 `0`。
- terminal-track residual cells：`2`；这些残差仍被保留，不被重基线吞并。

结论：P10 默认制导改变了原始 P11 N/M/O 标签，现有报告足以形成一个稳定的候选重基线，但不能自动视为已接受的期望包络。需人工审查旧标签语义与terminal-track 残差后，才能显式修改 harness；本审计不改变 P11 complete 状态。
