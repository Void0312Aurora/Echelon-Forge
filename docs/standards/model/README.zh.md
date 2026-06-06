# 模型架构标准总览

语言：
- 英文规范页：[README.md](README.md)
- 中文配套页：`README.zh.md`

状态：`2026-06-07`，维护中的模型与策略架构标准入口。

本目录负责仓库级的模型架构词汇：强化学习策略、辅助头、rollout label、loss、
reward、probe 与 runtime action adapter。它是标准面，不是任务追踪面。
`docs/task/model/` 下的活跃模型任务在增加、拆分或重新解释模型组件时，应引用
本目录。

## 范围

模型标准层定义：

- executable policy component、auxiliary learning head、runtime legality
  constraint、reward surface 与 diagnostics 之间的区别；
- 当前维护中的 PPO/HMoE 训练入口所使用的策略执行图；
- stopping、window-prior、event-action、credit 机制的 ownership 边界；
- 未来任务新增 model branch、adapter、loss、buffer 或 probe 时必须写清的文档项。

本目录不负责：

- 空中、海军或地面任务语义；
- C2/ROE 条令、tasking authority 或军种画像词汇；
- 低层物理、武器效应或毁伤模型参数；
- 活跃训练实验的验收状态。

这些内容归对应的 `joint/`、`services/`、领域特化、`bridge/`、task 或 runtime
文档所有。

## 维护文档

建议按顺序阅读：

1. [策略执行架构基线](policy_execution_architecture.zh.md)

第一份文档刻意保持具体：它映射当前实现表面，并固定后续 M2/M3 工作在继续增加
机制前应使用的共同词汇。

## 当前代码对齐

当前模型标准映射到以下实现表面：

- feature extractor：
  [python/models/transformer.py](../../../python/models/transformer.py)
- HMoE policy、event distribution 与 auxiliary heads：
  [python/rl/policy_algo/policies.py](../../../python/rl/policy_algo/policies.py)
  - 包括 executable `hybrid_event_head`、auxiliary
    `hybrid_event_credit_head`、`m3_stopping_head` 与
    `m3_window_classifier_head` adapter paths。
- HMoE route selection：
  [python/rl/policy_algo/hmoe_routing.py](../../../python/rl/policy_algo/hmoe_routing.py)
- PPO rollout/update loop 与 auxiliary-loss integration：
  [python/rl/policy_algo/ppo_adaptive_kl.py](../../../python/rl/policy_algo/ppo_adaptive_kl.py)
  - 拥有 rollout-time label construction、A6/A7 weighting、M3-S2 event-window
    updates、support-preserving collection、replay/calibration population 与
    diagnostics。
- first-event labels 与 event-credit helpers：
  [python/rl/policy_algo/first_event_hazard.py](../../../python/rl/policy_algo/first_event_hazard.py)
- first-event rollout storage：
  [python/rl/policy_algo/first_event_rollout_buffer.py](../../../python/rl/policy_algo/first_event_rollout_buffer.py)
- grouped stopping objective：
  [python/rl/policy_algo/m3s1_grouped_stopping.py](../../../python/rl/policy_algo/m3s1_grouped_stopping.py)
- air-combat event-action runtime support：
  [gym_envs/universal_env_parts/air_combat_event_action.py](../../../gym_envs/universal_env_parts/air_combat_event_action.py)
  - 在 policy-visible support 塑造 event distribution 之后，拥有最终 A5 runtime gate。

## 标准化规则

- 先按角色命名组件，再按实验代码命名组件。例如，`window-prior classifier` 是模型
  角色；`m3_window_classifier_head` 是当前实现名。
- 每个 model branch 必须声明自己是 executable、auxiliary-only、diagnostic-only，
  还是进入 executable action path 的 adapter。
- Runtime masks 与 state machine 定义合法 support；它们本身不定义 learned
  stopping objective。
- Reward 可以给行为赋值，但不能成为 action legality、one-shot suppression 或
  model-branch ownership 的唯一归属。
- 任何会在 evaluation 时改变 model logits 的 normalization 或 replay buffer，
  都是 model contract 的一部分，必须说明其 support population。
- Deterministic 与 stochastic probes 是评估面。它们可以验证模型合同，但不是模型
  组件本身。

## 与任务工作的关系

`docs/task/model/` 负责活跃实验、dispatch plan、held/pass 状态和证据包。本目录
负责这些任务讨论模型结构时必须使用的稳定词汇。

如果某个任务需要新的模型机制，它应引用这里已有的标准，或在把新机制当作维护架构
前显式要求更新标准。
