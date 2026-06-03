# M1 观测窗口 HMoE 验证

状态：`2026-06-02` 已进入 M1-A4 证据采集；M1-A4 已有 Stage-0 与 Stage-1
reactive/temporal probe 入口。`2026-06-02` A3 C2/ROE 发射纪律已作为
重复发射解释的前置约束层加入。

M1 对应路径 A。它不是最终正式架构，而是进入路径 C 前的证据包：
用最小侵入方式把近期时间窗口暴露给当前 HMoE PPO，观察空战 stage-0 / stage-1
中重复发射、动作可达性和策略稳定性是否改善。

输入：

- [时间 HMoE 策略计划](../temporal_hmoe_policy_plan_20260525.zh.md)
- [空战 1v1 真实度梯度课程](../../air_combat/a1_1v1_realism_gradient/README.zh.md)
- [A3 C2/ROE 发射纪律](../../air_combat/a3_c2_roe_release_discipline/README.zh.md)
- [A3 C2/ROE P4 探针证据 - 2026-06-03](../../air_combat/a3_c2_roe_release_discipline/a3_c2_roe_p4_probe_evidence_20260603.zh.md)
- [A3 C2/ROE Learned-Policy 探针证据 - 2026-06-03](../../air_combat/a3_c2_roe_release_discipline/a3_c2_roe_learned_policy_probe_20260603.zh.md)
- [A3 C2/ROE Reactive vs Temporal 对照证据 - 2026-06-03](../../air_combat/a3_c2_roe_release_discipline/a3_c2_roe_reactive_temporal_comparison_20260603.zh.md)
- [M1-A4 Stage-1 短程证据 - 2026-06-02](m1_a4_stage1_evidence_20260602.zh.md)
- [M1-A4 Hybrid Temporal Shaped 对照证据 - 2026-06-02](m1_a4_hybrid_temporal_shaped_pair_20260602.zh.md)
- 当前空战训练配置：
  `examples/config/training/active/air_combat/`
- 当前 PPO/HMoE 代码：
  `python/models/transformer.py`、
  `python/rl/policy_algo/policies.py`、
  `python/rl/policy_algo/ppo_adaptive_kl.py`

## 目的

回答一个 release 问题：

时间上下文是否足以改善当前空战武器使用行为，使我们有理由投入更重的
sequence-native causal Transformer PPO？

M1 不要求解决所有时序建模问题。它只要求证明“给当前 HMoE 可观察的短历史”
比单帧 reactive HMoE 更适合空战武器使用。

`2026-06-02` 后，重复发射不再直接作为“记忆不足”的单一证据。A3 需要先定义并暴露
C2/ROE 发射纪律，使 probe 能区分授权齐射、授权再攻击、过早第二发和未授权开火；
只有在这些 command state 可观测后仍存在未解释的重复发射，才把剩余问题升级为
M1/M2 的 policy-memory 或 sequence-model 证据。

## 边界

M1 允许：

- 增加 observation-level history window；
- 增加 `TemporalTransformerExtractor` 或等价非视觉 temporal extractor；
- 增加一组 stage-0 / stage-1 temporal HMoE 配置；
- 增加 shape、non-finite、world-batch runtime 与短程训练 smoke；
- 增加空战重复发射诊断指标。

M1 不允许：

- 改写 PPO 为 sequence-native 算法；
- 引入 recurrent hidden state 主线；
- 在仿真系统里新增战术记忆板；
- 改变导弹物理、制导、杀伤、弹药或冷却真实性；
- 将 `fire_weapon` 的最终动作语义冻结为 pulse 或 held-control。

## 设计目标

### 观测窗口

首版应采用固定长度窗口，例如 `history_len = 8 / 16 / 32`。

推荐优先纳入：

- `instruments` 历史；
- `mission` 历史；
- `contacts` 历史；
- `rwr` 历史；
- previous actions 或 `proprio` 历史；
- 物理上可观测的武器状态字段，例如剩余弹药、冷却、己方导弹在飞计数或发射事件。

视觉历史暂不纳入首版，除非后续单独做压缩或稀疏采样。

### 特征提取器

首版 extractor 应满足：

- 不破坏现有 `TransformerExtractor` checkpoint 兼容；
- 可以通过 config 显式选择；
- 对每一帧复用或仿照当前单帧 token embedding；
- 在 frame 维度做 temporal attention；
- 输出最近一帧的上下文化 embedding 给现有 HMoE policy。

### runtime 路径

必须覆盖两个入口：

- `gym_envs/universal_env.py` 单 env 路径；
- `python/rl/runtime/world_batch_vec_env.py` world-batch 路径。

两条路径的 reset、episode done、terminal observation 和 last action 更新必须一致。

## 任务簇

| 流 | 状态 | 目标 | 写入面 | 非目标 | 验证 | 退出条件 |
|----|------|------|--------|--------|------|----------|
| `M1-A0 文档与边界冻结` | accepted | 记录 M1 是路径 C 前的验证包，并冻结不新增战术记忆板原则。 | `docs/task/model/**` | 代码实现 | 文档 diff 检查 | README 与 cluster 明确 release gate |
| `M1-A1 源码盘点与 shape 设计` | accepted | 确认 observation space、world-batch tensor bridge、config 注册点和 extractor 注册点。 | 文档为主，必要时加只读 probe | 训练、算法改造 | shape probe 计划 | 形成具体 patch 列表 |
| `M1-A2 temporal window runtime 实现` | in validation | 实现非视觉 observation history，覆盖单 env、world-batch 与 cooperative 参数兼容。 | env/runtime/observation 相关文件、focused tests | PPO sequence buffer、causal policy | shape/reset/done 测试 | 两条 runtime 路径 shape 稳定 |
| `M1-A3 TemporalTransformerExtractor 实现` | in validation | 增加可配置 temporal extractor。 | `python/models/**`、注册/配置文件、focused tests | checkpoint 破坏、visual history | extractor forward + non-finite probe | 可用当前 HMoE policy 训练 |
| `M1-A4 空战 temporal probe` | in evidence | 在 stage-0 / stage-1 对比 reactive 与 temporal HMoE。 | air_combat training config、结果记录 | 正式长训、自博弈、路径 C 实现 | 短程 PPO + 固定诊断 | 形成改善/无改善结论 |
| `M1-A5 路径 C release vote` | held | 在 A3-aware evidence 下判断是否进入 M2 实现。 | docs/task/model/** | 代码实现 | M1 + A3 结果复盘 | 接受、延迟或拒绝 M2 |

## 验收信号

M1 可以进入 M2 release vote 的最低证据：

- temporal 配置能正常完成短程 PPO smoke；
- reactive 与 temporal 配置使用相同 stage、seed 规则和主要超参；
- temporal 版本没有引入新的 non-finite、reset 或 world-batch shape 问题；
- 在 stage-0 固定/训练诊断中，重复发射率、无效发射率或 fire action 稳定性至少一项改善；
- A3 C2/ROE P4 probe 已把授权发射、违规重复发射、无效 fire attempt 和 legacy fallback
  计数面区分开；
- A3 learned-policy probe 已显示 32k deterministic 不发射、stochastic 仍多发违规；
  发射后 `shot_budget_remaining` / `pending_assessment` 已进入动态 mission observation；
- post-fix reactive/temporal 对照显示 temporal stochastic 能把违规发射从 8 降到 0，
  但 deterministic 仍不发射，且 temporal 授权发射偏少、无 damage report；
- 改善来自策略可观察历史，而不是环境侧静默拦截重复发射；
- 若改善只来自新增 command/ROE 约束，而不是 temporal history，M2 release 继续 held；
- 若无改善，文档记录原因并暂停 M2 实现。

## 建议验证命令

实际命令以实现后的配置名为准，形式应保持类似：

```bash
bash tools/maintenance/cmo_env.sh python -m pytest -q \
  tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py \
  tests/world_batch/test_world_batch_runtime.py
```

```bash
bash tools/maintenance/cmo_env.sh python train.py \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage0_drone_weapon_employment_temporal_world_batch_probe_v1.json \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage0_drone_weapon_employment_v1.json
```

当前 M1-A4 入口：

- Stage-0 reactive 对照：
  `examples/config/training/active/air_combat/air_combat_1v1_stage0_drone_weapon_employment_world_batch_probe_v1.json`
- Stage-0 temporal probe：
  `examples/config/training/active/air_combat/air_combat_1v1_stage0_drone_weapon_employment_temporal_world_batch_probe_v1.json`

二者应使用同一 stage-0 场景：
`scenarios/air_combat/1v1/air_combat_1v1_stage0_drone_weapon_employment_v1.json`

- Stage-1 reactive 对照：
  `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_world_batch_probe_v1.json`
- Stage-1 temporal probe：
  `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_temporal_world_batch_probe_v1.json`

二者应使用同一 stage-1 场景：
`scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json`

- Stage-1 hybrid shaped 对照：
  `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_shaped_world_batch_probe_v1.json`
- Stage-1 hybrid temporal shaped probe：
  `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_temporal_shaped_world_batch_probe_v1.json`

二者应使用同一 training-shaped stage-1 场景：
`scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_training_shaped_v1.json`

## 退出状态

M1 只能以下列状态之一关闭：

- `accepted for M2`：短程证据显示 temporal window 对空战武器使用有实际改善；
- `needs more A`：shape 或训练可达，但证据不足，需要调整窗口/观测字段；
- `blocked`：runtime、训练或观测物理边界存在阻塞；
- `rejected`：时间窗口没有帮助，且不支持继续投入路径 C。
