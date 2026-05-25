# M2 Causal Transformer HMoE 目标架构

状态：held。只有在 M1 观测窗口 HMoE 验证显示时间上下文确实改善空战训练后，
M2 才能进入实现。

M2 对应路径 C，是正式、可扩展的目标路线：让 PPO/HMoE 本身变成 sequence-native，
用 causal Transformer 在时间维度上处理观测、动作、事件和奖励延迟。

输入：

- [M1 观测窗口 HMoE 验证](../m1_temporal_window_hmoe/README.zh.md)
- [时间 HMoE 策略计划](../temporal_hmoe_policy_plan_20260525.zh.md)

## 目的

构建正式的 temporal HMoE 主线，使模型能够直接学习：

- 最近动作与当前动作之间的关系；
- 发射事件、导弹在飞和目标航迹变化之间的延迟关系；
- BVR 交战中跨十几到数十秒的决策依赖；
- 未来 `2v2`、自博弈、多域事件历史中的因果上下文。

## 核心设计

M2 不再把历史作为“当前 observation 的附加字段”处理，而是把 rollout 本身保留为连续序列。

核心组件：

- `SequenceDictRolloutBuffer`
  - 保存 `(time, env, ...)`；
  - 采样 contiguous sequence；
  - 保留 `episode_starts` / valid mask；
  - 支持 CUDA device-resident 路径。
- `CausalTemporalTransformerExtractor`
  - 对每个 timestep 构造 frame tokens；
  - 加入 action/event/history tokens；
  - 使用 causal mask，禁止看未来；
  - 输出每个 timestep 的 actor/value embedding。
- `CausalTemporalHMoEPolicy`
  - 保留 HMoE semantic routing；
  - actor/value 对 sequence 输出逐步计算；
  - 支持 rollout inference 的缓存或滑动窗口。
- `SequenceAdaptiveKLPPO`
  - sequence-aware log-prob、value loss、entropy、KL 与 advantage normalization；
  - 支持 masked loss；
  - 兼容短 episode 和 world-batch reset。

## 范围

M2 允许：

- 新增 sequence-native buffer；
- 新增 causal temporal extractor；
- 新增 sequence HMoE policy；
- 新增 sequence PPO 变体；
- 新增 air-combat temporal config；
- 增加 profile / memory / throughput evidence。

M2 不允许：

- 重新定义仿真物理；
- 把战术逻辑写回环境；
- 把 M1 observation-window 作为最终模型接口；
- 在没有 M1 改善证据时提前实现；
- 同时展开 self-play 或 `2v2`。

## 任务簇

| 流 | 状态 | 目标 | 写入面 | 非目标 | 验证 | 退出条件 |
|----|------|------|--------|--------|------|----------|
| `M2-C0 Release Vote` | held | 基于 M1 证据决定是否启动。 | docs only | 代码实现 | M1 metrics review | accepted / delayed / rejected |
| `M2-C1 Sequence Buffer` | held | 实现 contiguous sequence rollout sampling。 | `python/rl/policy_algo/*buffer*`、tests | policy 架构 | buffer mask/shape tests | sequence samples 正确 |
| `M2-C2 Causal Extractor` | held | 实现 causal temporal attention。 | `python/models/**`、tests | env 逻辑 | causal mask tests | 无未来信息泄漏 |
| `M2-C3 Temporal HMoE Policy` | held | 接入 HMoE routing 与 sequence actor/value。 | `python/rl/policy_algo/policies.py` 或新模块 | self-play | forward/evaluate tests | PPO 可调用 |
| `M2-C4 Sequence PPO` | held | 实现 sequence-aware PPO loss。 | `ppo_adaptive_kl` sibling、新 tests | 算法大改合并进旧类 | synthetic PPO tests | smoke train 可跑 |
| `M2-C5 Air-Combat Probe` | held | 和 M1 / reactive baseline 对比。 | config、result docs | 长训结论 | short probes | 决定是否主线化 |

## 验收信号

M2 初版成功标准：

- sequence buffer 不展平时间语义；
- causal mask 测试证明无未来信息泄漏；
- sequence PPO 的 log-prob、KL、entropy、value loss 支持 valid mask；
- stage-0 空战训练 smoke 通过；
- 相同预算下不明显劣于 M1，并至少在一个时间依赖指标上更合理；
- 显存和吞吐在可接受范围内，有 profile 记录。

## 风险

- 实现成本高，容易破坏当前稳定 PPO/HMoE；
- CUDA device rollout buffer 与 sequence sampling 的接口需要谨慎；
- HMoE routing 当前依赖 mission observation，sequence 化后要明确逐 timestep route；
- 如果 M1 无改善，M2 的投入依据不足；
- 如果观测中的武器事件不完整，causal Transformer 也学不到正确时序。

## 退出状态

M2 只能以下列状态之一关闭：

- `accepted mainline candidate`：sequence-native HMoE 已通过短程对比，准备扩大训练；
- `prototype only`：技术可行但效果或成本不足，保留为原型；
- `blocked`：缺少观测、buffer、算法或 runtime 条件；
- `rejected`：M1/M2 证据都不支持继续。

