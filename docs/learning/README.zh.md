# 学习文档

语言：[英文规范页](README.md)；本页为中文配套。

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/learning/README.md`
Owner: `learning and experimentation`
Last verified: `2026-08-08`

本目标区域拥有强化学习、策略/模型架构、训练、评估协议、world model 和实验定义。
它不拥有任务领域语义、runtime action legality、physics、weapon effects 或活跃实验的
验收状态。

## 维护中权威

- [策略执行架构基线](standards/policy_execution_architecture.zh.md)：维护 executable
  policy path、auxiliary mechanism、loss、rollout label 与证据边界的标准。
- [Air Pilot Action Contract](../domains/air/standards/pilot_action_contract.zh.md)：
  `air_combat_hybrid_v1`、`event_action_mask`、`fire_once` 与 runtime trigger
  interpretation 的 owner。

## 当前实现地图

- Policy 与 heads：[policies.py](../../python/rl/policy_algo/policies.py)
- PPO composition 与 rollout/update orchestration：
  [ppo_adaptive_kl.py](../../python/rl/policy_algo/ppo_adaptive_kl.py)
- Grouped stopping loss 与 update：
  [grouped_stopping.py](../../python/rl/policy_algo/grouped_stopping.py)、
  [_grouped_stopping_mixin.py](../../python/rl/policy_algo/_grouped_stopping_mixin.py)
- Event-window、fire-boundary 与 window-classifier updates：
  [_event_window_mixin.py](../../python/rl/policy_algo/_event_window_mixin.py)
- Mission-observation assembly：
  [mission_observation.py](../../gym_envs/scenario_loader/mission_observation.py)
- 活跃空战训练入口：
  [训练配置索引](../../examples/config/training/active/air_combat/README.zh.md)

当前可复用名称按角色命名，包括 `stopping_head`、`window_classifier_head`、
`grouped_stopping_*`、`event_window_*` 与 `fire_boundary_*`。历史 `M3-S1` /
`M3-S2` 标签仍可用于 task、mechanism-ID 和 `m3s1/`、`m3s2/` metric namespace；
它们不是通用实现前缀。

## 活跃工作

- [空战 1v1 realism gradient](work/active/air_combat_1v1_realism_gradient/README.zh.md)
- [Damage-consequence reward surface](work/active/air_combat_damage_consequence_reward/README.zh.md)
- [Temporal-window HMoE](work/active/temporal_window_hmoe/README.zh.md)

这些包只拥有范围化执行状态，不重定义 Air mission 语义、effects physics 或
policy-architecture standard。

## 开放工作入口

- [分层 MoE 执行策略](work/issues/hierarchical_moe_execution_policy.zh.md)：维护中的设计方向，不是实现标准。
- [强化学习与自博弈](work/issues/rl_selfplay.zh.md)：草拟路线图。
- [Temporal policy 路线图](work/issues/temporal_policy_roadmap.zh.md)
- [Causal-transformer HMoE](work/issues/causal_transformer_hmoe/README.zh.md)
- [Launch-window 标签失衡](work/issues/launch_window_label_imbalance/README.zh.md)
- [HMoE 层级计算缺口](work/issues/hmoe_hierarchical_computation_gap/README.zh.md)
- [Policy hold baseline drift](work/issues/policy_hold_baseline_drift/README.zh.md)
- [协同训练基础与性能](work/issues/multi_agent_cooperative_training_foundation_and_performance_plan.zh.md)
- [协同执行管线发现](work/issues/p8_cooperative_execution_pipeline_findings_and_plan.zh.md)

这些页面都只是 `work/issues` 下的规划输入，路径本身不授予实施权威。

## 保留评审

- [空战 action-interface 拆分](reviews/air_combat_action_interface_split_20260602/README.zh.md)
- [Optimal-stopping 模型选择](reviews/optimal_stopping_model_selection_20260605/README.zh.md)
- [Grouped-stopping contract](reviews/grouped_stopping_contract_20260605/README.zh.md)

这些是带日期的 accepted 或 retained evidence packet，不是 active work queue。

未来 learning standard、reference、active work、issue 和 review 使用
[共享文档结构](../engineering/documentation/structure_examples.zh.md)。
