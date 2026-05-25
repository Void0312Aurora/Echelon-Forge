# 时间 HMoE 策略计划 - 2026-05-25

## 目的

建立一条从当前反应式 HMoE PPO 策略，升级到具备时间上下文的策略路线。
目标不是只修补 `1v1` 空战里的重复发射导弹问题，而是形成跨域通用原则：
仿真侧只保存物理状态和合约，行为记忆放到策略侧学习。

## 当前发现

- `python/models/transformer.py::TransformerExtractor` 目前是单帧 token
  特征提取器。它在同一帧的 `instruments`、`mission`、可选
  `proprio`、`contacts`、`rwr` token 之间做注意力。
- `python/rl/policy_algo/policies.py::HierarchicalMoEExecutionPolicy`
  每个 PPO step 调用 `extract_features(obs)`，没有携带 hidden state，
  也没有 causal attention cache。
- `gym_envs/universal_env_parts/observations.py` 可以暴露 `proprio`，
  但当前主要只是上一帧 action。它是有用证据，不等价于时间策略。
- `python/rl/policy_algo/device_dict_rollout_buffer.py` 以
  `(time, env, ...)` 存储 rollout tensor，但 `get()` 会展平成随机
  per-step 样本，训练时丢失连续时间结构。
- `python/world_model/networks.py::GRUActor` 和 Dreamer 路线已有具备历史能力的
  policy 组件，但它们还没有接入当前维护中的 PPO/HMoE 空战主线。

## 架构边界

仿真侧应保存并暴露物理真实或传感器可观测事实：

- 弹药数量与挂架可用性；
- 武器冷却与发射约束；
- 导弹实体、在飞导弹和归属关系；
- 发射事件，以及可观测时的传感器/RWR 提示；
- 目标航迹与航迹质量。

策略侧应学习战术时序：

- 上一次发射是否仍在等待效果评估；
- 应该保持不开火、再次攻击，还是切换目标；
- 如何结合几何、距离和闭合率安排发射；
- 连续发射何时是有意齐射，而不是误触发。

环境侧 latch 只应作为动作接口合约或硬物理约束存在，不应变成战术记忆替代品。

## 候选路径

### 路径 A：观测时间窗口特征提取器

增加时间观测 wrapper 和新的 `TemporalTransformerExtractor`。它消费固定长度的近期观测窗口：

- shape 可选方案：
  - 给每个 Dict observation key 增加顶层 `history` 轴；
  - 或显式增加 `instruments_history`、`contacts_history`、`rwr_history`、
    `mission_history`、`action_history` 等 key。
- 每帧先用当前单帧 token 提取器或轻量投影编码；
- 在 frame embedding 上做有序或 causal temporal attention；
- 输出最近一帧的上下文化 embedding，继续接入现有
  `SquashedMultiInputPolicy` / `HierarchicalMoEExecutionPolicy`。

优点：

- 对 SB3 PPO 侵入最小；
- 可以保留当前 per-step PPO loss 和 buffer 采样；
- 可以快速验证时间上下文是否缓解重复发射行为。

限制：

- 记忆长度固定在 observation window 内；
- per-step 随机 minibatch 仍是在预构造窗口上训练，不是通过 minibatch sequence
  传播 hidden state；
- 如果包含 visual observation，成本会很高，需要排除、降采样或压缩。

建议首个用途：

- 非视觉空战 HMoE，`history_len` 从 8 到 32 step 起步；
- 包含上一段 actions、导弹数量/剩余弹药、接触特征，以及物理上可观测的发射事件。

### 路径 B：Recurrent HMoE PPO

围绕 HMoE head 构造 recurrent policy：

- feature extractor 编码当前帧；
- GRU/LSTM 在 rollout 时为每个 env 携带 hidden state；
- rollout buffer 存储 hidden states 和 `episode_starts`；
- 训练时采样连续序列并 mask episode 边界；
- actor 和 critic 可以共享 recurrent trunk，也可以分离。

优点：

- 与在线控制较匹配；
- 记忆不受固定 observation stack 长度限制；
- `python/world_model/networks.py` 中的 `GRUActor` 已提供实现先例。

限制：

- 比路径 A 更深入地改动 PPO；
- `collect_rollouts`、`evaluate_actions`、buffer sample、推理/reset state
  需要一起更新；
- SB3 兼容性和 CUDA device-buffer 路径都需要回归测试。

### 路径 C：真正的 Causal Transformer PPO

构建 sequence-native policy：

- 将 rollout chunk 保存为连续 `(batch, time, feature)` 样本；
- 对观测、动作和历史 token 使用 causal mask；
- 对训练序列里的每个 timestep 预测 action 和 value；
- 使用 last-state loss 或全序列 masked loss。

优点：

- 最符合 Transformer 时间注意力方向；
- attention 可以直接查看早前发射动作、航迹演化和延迟结果；
- 一旦观测 schema 稳定，较自然地扩展到多智能体事件历史。

限制：

- 实现成本最高；
- action log-prob、value loss、KL、entropy 和 advantage normalization
  都要 sequence-aware；
- 大规模使用前需要先做显存与吞吐 profiling。

## 推荐实施阶梯

1. 冻结边界：除物理约束或明确动作合约外，不为武器行为继续新增战术记忆板。
2. 为非视觉 execution 任务增加 observation-level temporal window。
   在 env/runtime 层实现小型 wrapper，并在 `python/models/transformer.py`
   或相邻模块中实现 `TemporalTransformerExtractor`。
3. 在 `examples/config/training/active/air_combat/` 下增加 stage-0 temporal
   配置，和当前 HMoE probe 的差异只保留在时间设置上。
4. 执行短程固定策略和 PPO smoke：
   - 普通 runtime 与 world-batch runtime 的 observation shape 稳定；
   - 没有 non-finite feature；
   - held-fire 诊断下的发射次数可以由动作语义和物理约束解释。
5. 升级 `DeviceDictRolloutBuffer`，或增加 sibling sequence buffer，使其能在不展平
   time/env 维度的情况下采样连续序列。
6. 实现 recurrent HMoE 或 causal-Transformer HMoE，作为维护中的 sequence-native 路线。
7. 在相同空战 stage-0 和 stage-1 课程上比较 reactive HMoE、observation-window HMoE
   和 sequence-native HMoE。

## 初始代码切入点

- `python/models/transformer.py`
  - 增加 temporal extractor，或抽出可复用的 frame-token embedding；
  - 保持当前 `TransformerExtractor` checkpoint 兼容。
- `gym_envs/universal_env.py`
  - 为单 env 路径维护每环境观测历史。
- `python/rl/runtime/world_batch_vec_env.py`
  - 为 world-batch 训练路径的每个 handle 维护观测/action 历史。
- `gym_envs/universal_env_parts/observations.py`
  - 定义 history keys 的组装与 sanitization。
- `python/rl/policy_algo/policies.py`
  - 只有当需要 hidden state 或 sequence 语义时再增加 temporal HMoE policy；
    路径 A 可以复用当前 policy class。
- `python/rl/policy_algo/device_dict_rollout_buffer.py`
  - 在路径 A 证明有价值后，再增加 sequence sampling。
- `python/rl/policy_algo/ppo_adaptive_kl.py`
  - sequence-native 训练必须同步更新 `collect_rollouts()` 和 `train()`。

## 空战验收信号

对于当前重复发射导弹问题，成功不应定义为“环境静默拦截所有重复发射”。
成功应体现为：

- observation 包含足够物理证据，使策略知道近期是否发射过、是否已有导弹在飞；
- 当目标未变化且第一枚导弹仍有战术意义时，策略能学到较低重复发射率；
- 后续课程如果 reward 和战术设定支持，有意齐射仍然可以发生；
- fixed held-fire 诊断能够清晰区分动作接口行为和学习策略行为。

## 待定设计问题

- `fire_weapon` 应在 action adapter 边界变成显式 pulse command，还是保留为连续高/低控制并交给策略学习时机？
- 每个真实性阶段中，哪些发射相关观测对飞行员物理可得：己方在飞导弹数、导弹航迹、发射事件 bit、RWR launch cue，还是只有弹药/冷却？
- 在当前仿真 timestep 下，stage-0 武器使用最小有效历史长度是多少？
- temporal attention 应把上一段 actions 作为一等 token，还是只依赖 `proprio` 历史？
- 开启 visual observation 后，视觉历史应排除、稀疏采样，还是先压缩再进入 temporal attention？

