# A7 Event-Value / Advantage Credit Head

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/learning/reviews/optimal_stopping_model_selection_20260605/a7_event_value_advantage_credit_head_20260604/README.md`
Owner: `learning/policy-architecture`
Last verified: `2026-08-09`
Review basis: 保留的 A7 event-credit probe 与 optimal-stopping review。

状态：已闭合的历史 event-credit 线。A7 未接受自身 quality-window timing gate；
可执行 bounded firing gate 记录在 M3-S2 review 中。

输入：

- [Optimal-stopping review](../README.zh.md)
- [A6 timing review](../a6_event_value_first_event_timing_20260604/README.zh.md)
- [M3-S2 firing-gate review](../../grouped_stopping_contract_20260605/m3_s2_fire_timing_learnability_audit/README.zh.md)
- [Learning owner](../../../README.zh.md)

证据：

- [Execution breakpoint analysis](a7_event_value_advantage_credit_head_execution_breakpoint_analysis_20260605.zh.md)
- [Event-policy margin repair](a7_event_value_advantage_credit_head_event_policy_margin_repair_20260605.zh.md)
- [Current status snapshot](a7_event_value_advantage_credit_head_current_status_20260604.zh.md)

边界：event-value/advantage credit 仍是研究证据，不是维护中的 runtime
policy contract，也不声明 learned firing quality。
