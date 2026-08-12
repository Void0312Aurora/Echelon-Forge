# A6 Event Value 与首事件时机

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/learning/reviews/optimal_stopping_model_selection_20260605/a6_event_value_first_event_timing_20260604/README.md`
Owner: `learning/policy-architecture`
Last verified: `2026-08-09`
Review basis: 保留的首事件时机 probe 与 optimal-stopping review。

状态：已闭合的历史时机线。hazard、deadline 与 launch-window label 未形成稳定
的独立时机解；可执行的 bounded firing gate 记录在 M3-S2 review 中。

输入：

- [Optimal-stopping review](../README.zh.md)
- [M3-S2 firing-gate review](../../grouped_stopping_contract_20260605/m3_s2_fire_timing_learnability_audit/README.zh.md)
- [Learning owner](../../../README.zh.md)

证据：

- [Launch-window probe](a6_event_value_first_event_timing_launch_window_short_learned_probe_20260604.zh.md)
- [Timing contract](a6_event_value_first_event_timing_launch_window_timing_contract_20260604.zh.md)
- [Event-head probe](a6_event_value_first_event_timing_event_head_short_learned_probe_20260603.zh.md)

边界：本包记录时机质量研究历史，不重新打开 active firing closure，
也不授权 reward/系数修改。
