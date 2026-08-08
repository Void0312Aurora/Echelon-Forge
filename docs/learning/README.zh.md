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
- [模型任务区](../task/model/README.zh.md)：活跃实验、证据、dispatch 与 held/pass
  裁决。M3-S1、M3-S2 等任务标签不会重命名可复用实现 API。
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

## 开放工作入口

- [分层 MoE 执行策略](work/issues/hierarchical_moe_execution_policy.zh.md)：维护中的设计方向，不是实现标准。
- [强化学习与自博弈](work/issues/rl_selfplay.zh.md)：草拟路线图。

两份页面都只是 `work/issues` 下的规划输入，路径本身不授予实施权威。

未来 learning standard、reference、active work、issue 和 review 使用
[共享文档结构](../engineering/documentation/structure_examples.zh.md)。
