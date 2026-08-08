# 模型任务

状态：时间策略工作的活跃规划线；`2026-05-25` 确定采用“先 A 验证、后 C 正式化”的路线。

本目录追踪跨域模型侧改造。当前维护中的 task slice 是时间策略工作，而不是
替代 `docs/learning/work/issues/` 下的学习/模型议题规划，或
`python/world_model/` 实现面的总入口。
当前直接动因是 `1v1` 空战武器使用线路：重复发射导弹这类行为问题，应优先通过
策略的时间上下文与可观测物理状态解决，而不是继续在仿真系统里扩张战术记忆板。

## 当前路线

- 标准基线：模型架构词汇与实现 ownership 归
  [模型架构标准](../../../../learning/README.zh.md)；活跃任务在增加或重新解释
  model branch、adapter、loss、buffer 或 probe 前，应先引用该标准层。
- 目标架构：路径 C，sequence-native causal Transformer HMoE/PPO。
- 先行验证：路径 A，observation-window temporal HMoE。
- 动作接口：`2026-06-02` 已接受 `M1 空战动作接口拆分` 的 `air_combat_hybrid_v1`
  训练表面；这只释放动作接口，不释放 learned policy 或 M2。
- 模型选择暂停：`2026-06-05`，A7 first-event timing 证据被重新收束为 M3，即一个
  与领域无关的一次性时机 / optimal-stopping 模型选择问题；M3-S1 现在作为架构分离、
  data/censoring 与 grouped stopping objectives 的 planning contract，代码实现仍需等合同明确。
- 可学习性审计：M3-S2 现在是 sealed evidence package。它证明 legal release 与 terminal
  wins 在 oracle surface 中可达，局部化了多处 event-timing 与 calibration 断点，并在
  `2026-06-08` A5 武器保险动作帧修复后闭合有边界 learned-policy firing gate。已接受的声明
  很窄：在 active Stage-1 C2/ROE scenario/config pair 下，active model 可以请求并执行一次
  authorized release，且没有 rejected requests、violations 或 repeat-before-assessment releases。
  Timing quality、cross-config robustness、effects quality、damage 与 kill-chain behavior
  仍 held，只有作为 follow-on work 时才重新打开。
- 释放原则：只有当路径 A 在 stage-0 / stage-1 空战课程中显示时间信息能改善
  重复发射、可达性或策略稳定性后，才展开路径 C 的实现。
- 路径 B recurrent HMoE 只作为对照/备用，不作为正式主线。

## 当前入口

- [时间 HMoE 策略计划](../../../../learning/work/issues/temporal_policy_roadmap.zh.md)
- [M1 观测窗口 HMoE 验证](../../../../learning/work/active/temporal_window_hmoe/README.zh.md)
- [M1 空战动作接口拆分](../../../../learning/reviews/air_combat_action_interface_split_20260602/README.zh.md)
- [M2 Causal Transformer HMoE 目标架构](../../../../learning/work/issues/causal_transformer_hmoe/README.zh.md)
- [M3 Optimal-Stopping Model Selection](../../../../learning/reviews/optimal_stopping_model_selection_20260605/README.zh.md)
- [M3-S1 Censored Optimal-Stopping Timing Contract](../../../../learning/reviews/grouped_stopping_contract_20260605/README.zh.md)
- [M3-S2 开火时机可学习性审计](../m3_s2_fire_timing_learnability_audit/README.zh.md)
  archived pointer；完整包：
  [archive/m3_s2_fire_timing_learnability_audit](../m3_s2_fire_timing_learnability_audit/README.zh.md)
- 英文主文：
  [Temporal HMoE Policy Plan](../../../../learning/work/issues/temporal_policy_roadmap.md)

已归档子项目的完整清单见 [归档注册表](archive_registry.zh.md)。
