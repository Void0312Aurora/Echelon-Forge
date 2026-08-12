# 杀伤链机制解耦复核 - 2026-06-21

语言：[英文主文](README.md)；中文配套。

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/systems/effects/reviews/kill_chain_mechanism_decoupling_20260621/README.md`
Owner: `systems/effects/reviews`
Last verified: `2026-08-08`
Review basis：保留的 `2026-06-21` 机制、facade、load、response 与 admission 证据。

## 范围

本包复核 approach、fuze decision、warhead load、component response 与
consequence projection 的分离，保留中文详细记录和机器可读诊断包。

## 保留证据

- [机制分析](kill_chain_mechanism_decoupling_analysis_20260621.zh.md)
- [解耦 probe 结果](kill_chain_decoupling_probe_results_20260621.zh.md)
- [部件 load-factor 视图](kill_chain_component_load_factor_view_20260621.zh.md)
- [部件 response 边界](kill_chain_component_response_boundary_20260621.zh.md)
- [校准 admission gate](kill_chain_calibration_admission_gate_20260621.zh.md)
- [机器可读 review packet](review_packets/kill_chain_decoupling_20260621/kill_chain_decoupling_probe_20260621.json)

## 结论与限制

本包仅作为保留的诊断与实现边界证据接受，不授权 runtime retuning、
真实弹种/目标校准、确定性引信、Pk 或跨层校准。当前行为以代码、测试和
维护中 system standards 为准；这些带日期记录不是 active task queue。
