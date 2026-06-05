# 模型任务

状态：时间策略工作的活跃规划线；`2026-05-25` 确定采用“先 A 验证、后 C 正式化”的路线。

本目录追踪跨域模型侧改造。当前维护中的 task slice 是时间策略工作，而不是
替代 `forward/models/` 想法 backlog 或 `python/world_model/` 实现面的总入口。
当前直接动因是 `1v1` 空战武器使用线路：重复发射导弹这类行为问题，应优先通过
策略的时间上下文与可观测物理状态解决，而不是继续在仿真系统里扩张战术记忆板。

## 当前路线

- 目标架构：路径 C，sequence-native causal Transformer HMoE/PPO。
- 先行验证：路径 A，observation-window temporal HMoE。
- 动作接口：`2026-06-02` 已接受 `M1 空战动作接口拆分` 的 `air_combat_hybrid_v1`
  训练表面；这只释放动作接口，不释放 learned policy 或 M2。
- 模型选择暂停：`2026-06-05`，A7 first-event timing 证据被重新收束为 M3，即一个
  与领域无关的一次性时机 / optimal-stopping 模型选择问题；M3-S1 现在作为架构分离、
  data/censoring 与 grouped stopping objectives 的 planning contract，代码实现仍需等合同明确。
- 释放原则：只有当路径 A 在 stage-0 / stage-1 空战课程中显示时间信息能改善
  重复发射、可达性或策略稳定性后，才展开路径 C 的实现。
- 路径 B recurrent HMoE 只作为对照/备用，不作为正式主线。

## 当前入口

- [时间 HMoE 策略计划](temporal_hmoe_policy_plan_20260525.zh.md)
- [M1 观测窗口 HMoE 验证](m1_temporal_window_hmoe/README.zh.md)
- [M1 空战动作接口拆分](m1_action_interface_split/README.zh.md)
- [M2 Causal Transformer HMoE 目标架构](m2_causal_transformer_hmoe/README.zh.md)
- [M3 Optimal-Stopping Model Selection](m3_optimal_stopping_model_selection/README.zh.md)
- [M3-S1 Censored Optimal-Stopping Timing Contract](m3_s1_censored_optimal_stopping_timing_contract/README.zh.md)
- 英文主文：
  [Temporal HMoE Policy Plan](temporal_hmoe_policy_plan_20260525.md)
