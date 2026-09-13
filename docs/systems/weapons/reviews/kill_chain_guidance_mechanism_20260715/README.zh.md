# 杀伤链制导机制复核 - 2026-07-15

语言：[英文主文](README.md)；中文配套。

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/systems/weapons/reviews/kill_chain_guidance_mechanism_20260715/README.md`
Owner: `systems/weapons/reviews`
Last verified: `2026-09-13`
Review basis：保留的制导校准记录与完整的 `2026-07-15` 五阶段机制、包络及标量校准证据包。

## 范围

本包保留仓库 AIM-120C-like 工程代理中的制导/机制归因诊断。这些实验是
仿真证据，不是真实导弹性能测量。

## 保留证据

- [制导与杀伤校准记录](kill_chain_guidance_lethality_calibration_20260621.zh.md)
- [机制消融结论](review_packets/kill_chain_guidance_mechanism_ablation_20260715/kill_chain_guidance_mechanism_ablation_conclusions_20260715.zh.md)
- [精确机制结论](review_packets/kill_chain_guidance_exact_mechanism_ablation_20260715/kill_chain_guidance_exact_mechanism_ablation_conclusions_20260715.zh.md)
- [世界系 LOS-history PN 验证](review_packets/kill_chain_world_pn_production_validation_20260715/world_pn_production_validation.zh.md)
- [世界系 CV tracker 验证](review_packets/kill_chain_world_cv_tracker_validation_20260715/world_cv_tracker_validation.zh.md)
- [Capture 结构消融](review_packets/kill_chain_capture_structure_ablation_20260715/kill_chain_capture_structure_ablation_conclusions_20260715.zh.md)
- [修正后连续包络](review_packets/kill_chain_guidance_envelope_rebuild_20260715/kill_chain_guidance_envelope_rebuild_20260715_conclusions.zh.md)
- [受约束标量校准](review_packets/kill_chain_guidance_scalar_calibration_20260715/kill_chain_guidance_scalar_calibration_20260715_conclusions.zh.md)
- [第四/第五阶段热图证据](review_packets/kill_chain_guidance_calibration_visualization_20260715/kill_chain_guidance_calibration_visualization_summary_20260715.md)

## 结论与限制

本包仅作为保留诊断证据接受。该序列保留 `nav_gain=4`，并因缺少机动目标/APN
权威而继续暂缓默认发布；它不建立真实 AIM-120C 制导、引信、杀伤或 Pk 权威，
也不授权 descriptor 或默认 runtime 重调。后续实验必须建立独立 owner-local 工作包。
