# 空战 1v1 训练烟测进展

状态：`2026-05-16` 当前轮已完成 HMoE 主线烟测。

关联文档：

- [空战 1v1 切入分析](/home/void0312/Workshop/CMO/docs/task/air_combat/air_combat_1v1_entry_analysis_20260516.zh.md)
- [空战 1v1 冻结计划](/home/void0312/Workshop/CMO/docs/task/air_combat/air_combat_1v1_freeze_plan_20260516.zh.md)
- [空战 1v1 F-16C 基线切换与最小对战合同进展](/home/void0312/Workshop/CMO/docs/task/air_combat/air_combat_1v1_f16c_baseline_progress_20260516.zh.md)

## 一、这轮入口口径

这轮把 `1v1` active 训练入口收口到 HMoE 主线：

- [examples/config/training/active/air_combat/README.md](/home/void0312/Workshop/CMO/examples/config/training/active/air_combat/README.md)
- [air_combat_1v1_f16c_scripted_red_smoke_v1.json](/home/void0312/Workshop/CMO/examples/config/training/active/air_combat/air_combat_1v1_f16c_scripted_red_smoke_v1.json)
- [air_combat_1v1_f16c_scripted_red_world_batch_smoke_v1.json](/home/void0312/Workshop/CMO/examples/config/training/active/air_combat/air_combat_1v1_f16c_scripted_red_world_batch_smoke_v1.json)

当前维护口径：

1. 蓝方学习机为 `F-16C_Block50`；
2. 红方对手为场景内声明的脚本 `F-16C_Block50`；
3. 训练策略直接使用 `HierarchicalMoEExecutionPolicy`；
4. 一份配置覆盖标准 `execution` 路径，一份配置覆盖默认 `WorldBatchVecEnv` 路径；
5. 当前 `1v1` active 线不再把 shared policy 作为主入口记录。

## 二、当前 HMoE 配置形态

这轮 `1v1` HMoE 配置沿用了当前维护主线的核心口径：

1. `policy = HierarchicalMoEExecutionPolicy`
2. `hmoe.bootstrap_from_shared_action_head = auto`
3. `family_subexpert_counts = [3, 2, 3, 1]`
4. `hmoe_residual_scale = 0.18`
5. `hmoe_head_lr_scale = 0.15`
6. `hmoe_residual_warmup_fraction = 0.3`
7. `device = cuda`
8. `diagnostics.nonfinite_probe = true`

这保证空战 `1v1` 不是临时退回 shared 架构，而是直接站在当前 HMoE 训练主线上开烟测。

补充说明：

1. 当前 `1v1` smoke 仍使用 `mission_obs_mode = basic`；
2. 因此 HMoE 已经真实激活，但策略可见的任务语义仍然偏简；
3. 这意味着本轮更像“主线 HMoE 训练链已接通”，而不是“空战专用 HMoE 路由语义已经完整展开”。

## 三、为什么仍然没有启用 scripted residual wrapper

这轮仍然没有启用现有 `stable_flight` / `takeoff_cruise_landing` 的 scripted residual wrapper。

原因仍然成立：

1. 当前维护配置里的 `scripted_lock_indices` 会锁住较多开关维度；
2. 其中包含空战需要保留学习自由度的武器相关控制面；
3. 对 `1v1` 而言，先保留原始 `full` action surface` 更适合验证空战 HMoE 主线，而不是把关键维度预先交给非空战脚本基线。

## 四、烟测执行结果

执行命令一：

```bash
source tools/maintenance/cmo_env.sh
cmo_python train.py \
  --scenario scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_f16c_scripted_red_smoke_v1.json \
  --run_name air_combat_1v1_f16c_scripted_red_hmoe_smoke_v1_manual \
  --output_base experiments/smoke
```

执行命令二：

```bash
source tools/maintenance/cmo_env.sh
cmo_python train.py \
  --scenario scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_f16c_scripted_red_world_batch_smoke_v1.json \
  --run_name air_combat_1v1_f16c_scripted_red_hmoe_world_batch_smoke_v1_manual \
  --output_base experiments/smoke
```

结果：

1. HMoE 标准 `execution` 路径已正常启动并完整跑满 `512` timesteps；
2. HMoE 默认 `WorldBatchVecEnv` 路径也已完整跑满 `512` timesteps；
3. 两条路径都正常生成 `256` 与 `512` timesteps checkpoint；
4. 两条路径都正常生成 `final_model.zip`；
5. 两条路径都启用了 HMoE bootstrap 与 non-finite probe，且本轮未触发 non-finite abort；
6. 这轮验证的是 HMoE 主线能否承载 `1v1` 空战最小训练闭环，而不是 shared-vs-HMoE A/B。

产物位置：

- [experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_smoke_v1_manual/final_model.zip](/home/void0312/Workshop/CMO/experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_smoke_v1_manual/final_model.zip)
- [experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_smoke_v1_manual/checkpoints/model_256_steps.zip](/home/void0312/Workshop/CMO/experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_smoke_v1_manual/checkpoints/model_256_steps.zip)
- [experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_smoke_v1_manual/checkpoints/model_512_steps.zip](/home/void0312/Workshop/CMO/experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_smoke_v1_manual/checkpoints/model_512_steps.zip)
- [experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_world_batch_smoke_v1_manual/final_model.zip](/home/void0312/Workshop/CMO/experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_world_batch_smoke_v1_manual/final_model.zip)
- [experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_world_batch_smoke_v1_manual/checkpoints/model_256_steps.zip](/home/void0312/Workshop/CMO/experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_world_batch_smoke_v1_manual/checkpoints/model_256_steps.zip)
- [experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_world_batch_smoke_v1_manual/checkpoints/model_512_steps.zip](/home/void0312/Workshop/CMO/experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_world_batch_smoke_v1_manual/checkpoints/model_512_steps.zip)

## 五、从日志看到的当前信号

两条 HMoE 烟测日志都显示：

1. rollout 可以持续推进，episode 并非一步即死；
2. 平均 episode 长度大致在 `98` 到 `125` 步附近；
3. 平均回报仍明显为负，当前大致在 `-370` 到 `-361` 区间；
4. HMoE 路径确实被激活，因为训练启动时明确打印了：
   - `HMoE bootstrap: initialized family heads from shared action head and reset subexpert residuals.`
   - `Diagnostics: auto-enabled for HMoE route/parameter observability.`
5. 这说明当前问题已经不再是“有没有切到 HMoE”，而是 `1v1` 空战 reward / termination / eval 仍比较粗，训练信号还没有变得可解释。

## 六、补充统计

为了把诊断信息真正落盘，这轮补跑了两组相同配置、但 `--diagnostics_every 64` 的 HMoE 烟测：

标准路径：

- [experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_smoke_v1_diag64_manual/final_model.zip](/home/void0312/Workshop/CMO/experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_smoke_v1_diag64_manual/final_model.zip)

batch 路径：

- [experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_world_batch_smoke_v1_diag64_manual/final_model.zip](/home/void0312/Workshop/CMO/experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_world_batch_smoke_v1_diag64_manual/final_model.zip)

### 6.1 最终训练标量

标准 `execution` HMoE：

1. `rollout/ep_len_mean = 98.0`
2. `rollout/ep_rew_mean = -370.07`
3. `time/fps = 33`
4. `train/approx_kl = 1.31e-4`
5. `train/value_loss = 17447.53`
6. `train/kl_penalty_coef = 0.032`
7. `train/std = 0.2231`

默认 `WorldBatchVecEnv` HMoE：

1. `rollout/ep_len_mean = 110.0`
2. `rollout/ep_rew_mean = -361.02`
3. `time/fps = 34`
4. `train/approx_kl = 9.30e-5`
5. `train/value_loss = 24897.13`
6. `train/kl_penalty_coef = 0.032`
7. `train/std = 0.2231`

### 6.2 终止分布

诊断版两条路径都给出了同一个非常明确的现象：

1. 当前窗口内终止几乎全部是 `failfast_deep_stall`；
2. `diag/failure_frac_window = 1.0`；
3. `diag/term_frac_failfast_deep_stall = 1.0`；
4. `diag/term_rew_failfast_penalty = -50`；
5. 终局总回报主项大约在 `-85` 到 `-88` 一带。

这说明当前 `1v1` HMoE 主线已经跑通，但“训练学不会空战”的第一障碍不是 HMoE 架构本身，而是：

1. 初期飞行稳定性不足；
2. failfast 终止过早主导了训练信号；
3. 空战胜负与武器链收益还没有成为主导学习驱动。

### 6.3 HMoE 路由统计

诊断版日志还补出了 HMoE 路由分布。

当前结果非常一致：

1. `hmoe/fam/nav = 1.0`
2. `hmoe/sub/nav/vector = 1.0`
3. 没有看到 `takeoff_ground / formation_cooperative / recovery_landing` family 被激活

这并不表示 HMoE 没有工作，而是表示：

1. 现在的 `1v1` smoke 使用的是 `mission_obs_mode = basic`；
2. 当前 mission 语义会把 routing 稳定地送进导航 family；
3. 所以这轮 HMoE 主线验证更偏“架构和训练链有效”，还不是“空战专用 family/subexpert 已经分化”。

### 6.4 HMoE 参数统计

参数统计也给出了一个有用信号：

标准路径最终大致为：

1. `hmoe_params/family/nonzero_frac = 1.0`
2. `hmoe_params/sub/nonzero_frac = 0.111`
3. `hmoe_params/family/weight_norm_mean ≈ 0.0412`
4. `hmoe_params/sub/weight_norm_mean ≈ 1.2e-4`

batch 路径最终大致为：

1. `hmoe_params/family/nonzero_frac = 1.0`
2. `hmoe_params/sub/nonzero_frac = 0.111`
3. `hmoe_params/family/weight_norm_mean ≈ 0.0412`
4. `hmoe_params/sub/weight_norm_mean ≈ 1.5e-4`

这说明：

1. family head 已经处于真实非零工作态；
2. subexpert residual 也开始被更新，但规模仍然很小；
3. 这和当前 routing 长期集中在 `nav/vector` 上是相互一致的。

## 七、当前阶段解释边界

这轮烟测完成后，可以说明：

1. `1v1` 空战 active 线已经切回 HMoE 主线口径；
2. 脚本红方与 HMoE policy 已经进入真实 rollout 闭环；
3. 当前真正暴露出来的主问题是 `failfast_deep_stall` 主导终止，而不是 HMoE 是否被启用；
4. 当前 HMoE routing 已经工作，但在 `basic` mission 语义下基本全集中在 `nav/vector`；
5. 但不再需要把“先用 shared 过一遍”当作当前主线叙事的一部分。

## 八、下一步建议

在 HMoE 主线口径下，后续更自然的推进顺序是：

1. 固化 HMoE `1v1` 烟测结果与最小回归命令；
2. 优先处理早期飞行稳定性与 `failfast_deep_stall` 主导问题；
3. 补 `1v1` 终止原因统计与 eval 输出；
4. 明确 `combat_win / combat_loss / combat_draw / combat_timeout / 弹尽未决` 的训练与评估字段；
5. 再为空战补更贴近交战语义的 mission / routing 语义，让 HMoE 不再长期停在 `nav/vector` 单一路由上。
