# M3-S2 开火时机可学习性审计收口 2026-06-08

状态：`archived as bounded firing gate accepted; robustness and timing research held`。

## 判定

将 M3-S2 开火时机可学习性审计归档为 sealed evidence package。

最近这轮工作的 release-gate 问题，在 active Stage-1 C2/ROE scenario/config pair
上已经闭合：

- deterministic 与 stochastic learned-policy probes 都会请求 `fire_once`；
- A5 接受该请求；
- 实际执行 exactly one authorized missile release；
- bounded batch validation 中 rejected requests、violation releases、
  repeat-before-assessment releases 均为 `0`。

这不是说更大的 fire-timing 研究已经完成。它只是一个有边界的 release-gate
验收，因此后续训练可以继续推进，不应再把“模型不能发射”当成第一嫌疑 blocker。

## 保留证据

- Focused A5 fix evidence：
  [m3_s2_fire_closure_validation_20260608.zh.md](m3_s2_fire_closure_validation_20260608.zh.md)
- Batch firing-gate evidence：
  [m3_s2_fire_closure_batch_validation_20260608.zh.md](m3_s2_fire_closure_batch_validation_20260608.zh.md)
- Current status 与历史诊断：
  [m3_s2_fire_timing_learnability_audit_current_status_20260605.zh.md](m3_s2_fire_timing_learnability_audit_current_status_20260605.zh.md)

## 保留残余

- Timing quality 未验收。本 batch 验证的是合法 release execution，不是 first-release
  step 是否在战术或统计意义上最优。
- Cross-config robustness 未证明。已接受 gate 只限定于 batch validation 中记录的 active
  Stage-1 C2/ROE scenario/config pair 与 seeds。
- Effects、damage 与 kill-chain behavior 不由本包验收，仍属于独立 A8/model evidence。
- 后续研究仍可以重访 event-logit calibration、support distribution、timing-quality
  labels、sequence-memory/modeling，但应作为 follow-on task 打开，而不是继续让本证据包保持 live。

## 归档动作

将本包移动到 `docs/task/model/archive/`，并在原
`docs/task/model/m3_s2_fire_timing_learnability_audit/` 路径留下 pointer README。
