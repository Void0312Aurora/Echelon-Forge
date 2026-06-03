# A3 C2/ROE Reactive vs Temporal 对照证据 - 2026-06-03

状态：`2026-06-03`，post-launch observation 修复后的对照证据。本记录不验收
learned policy，也不释放 M2。

语言：

- 英文规范页：[a3_c2_roe_reactive_temporal_comparison_20260603.md](a3_c2_roe_reactive_temporal_comparison_20260603.md)
- 中文辅文：`a3_c2_roe_reactive_temporal_comparison_20260603.zh.md`

## 范围

本轮在 `air_combat_c2_roe_v1` mission observation 动态暴露发射后状态之后，对比
A3 C2/ROE reactive 与 temporal HMoE。

两轮训练共同使用：

- 场景：`scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json`；
- seed：`20260613`；
- 32,768 training steps；
- 4 个 world-batch env；
- `action_mode=air_combat_hybrid_v1`；
- `mission_obs_mode=air_combat_c2_roe_v1`。

配置：

- reactive：`examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_shaped_world_batch_probe_v1.json`；
- temporal：`examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json`。

## 训练结果

两轮训练都完成，未产生 non-finite report。二者都以 `combat_timeout` 为主，最终
`ep_rew_mean` 约为 `-753`。训练诊断仍路由到 `nav/vector`，deterministic 诊断窗口
显示 `action_fire_weapon_frac=0`。

训练日志仍出现 no-missiles-remaining warning。也就是说，动态 post-launch observation
本身没有消除 stochastic exploration 中的耗弹行为。

## Final-Model Probes

| Probe | Episodes | Termination | Fire attempts | Releases | Authorized releases | Violation releases | Invalid attempts | Damage reports |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| reactive deterministic | 1 | `combat_timeout=1` | 0 | 0 | 0 | 0 | 0 | 0 |
| reactive stochastic | 3 | `combat_timeout=3` | 14 | 11 | 3 | 8 | 3 | 3 |
| temporal deterministic | 1 | `combat_timeout=1` | 0 | 0 | 0 | 0 | 0 | 0 |
| temporal stochastic | 3 | `combat_timeout=3` | 7 | 2 | 2 | 0 | 5 | 0 |

逐 episode stochastic release buckets：

| Policy | Episode | Fire attempts | Releases | Authorized releases | Violation releases | Invalid attempts |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| reactive | 0 | 5 | 4 | 1 | 3 | 1 |
| reactive | 1 | 4 | 4 | 1 | 3 | 0 |
| reactive | 2 | 5 | 3 | 1 | 2 | 2 |
| temporal | 0 | 1 | 0 | 0 | 0 | 1 |
| temporal | 1 | 3 | 1 | 1 | 0 | 2 |
| temporal | 2 | 3 | 1 | 1 | 0 | 2 |

## 解释

Temporal history 现在是更好的 stochastic 发射纪律表面：在这组固定 seed 的 32k 对照中，
违规发射从 8 次降到 0 次。但它的改善方式偏保守。deterministic policy 仍完全不发射，
temporal stochastic 只产生 2 次授权发射，并且没有 damage report。

剩余问题不能声明为记忆已解决。下一项工作应转向训练信号和 policy routing 修复：策略需要先学到
deterministic 授权首发，再学会发射后 hold 或等待 reattack 授权。
