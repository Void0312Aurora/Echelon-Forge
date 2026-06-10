# 空战 1v1 失速问题进一步排查与修复跟进

状态：`2026-05-16`

## 一、这次继续追的核心问题

在前一轮 `1v1` HMoE 烟测里，`failfast_deep_stall` 已经明确是主导终止原因，但当时还没有把“为什么一开始就会被推到高攻角深失速”拆干净。

这次继续往下追，重点不是再证明“有失速”，而是确认：

1. HMoE 启动链路本身是否在放大初始动作；
2. 首个 rollout 是否绕过了 residual warmup；
3. 修复这两个启动问题之后，深失速是否会显著缓解。

## 二、这次确认到的两个启动层根因

### 2.1 HMoE bootstrap 语义和 residual 语义原先并不一致

当前 HMoE 前向是：

- `mean_actions = shared_mean_actions + effective_scale * expert_residual`

也就是说 routed family/subexpert head 在实现语义上是 residual correction，而不是替代 shared head 的独立动作头。

但旧实现里 `initialize_hmoe_from_shared_action_head()` 会把 family head 直接复制成 shared action head。

这会带来一个明显后果：

1. shared action head 已经输出一份完整动作均值；
2. family head 再被当作 residual 加回 shared；
3. 只要 residual gate 在 rollout 初期不是零，就会把初始动作均值整体推偏。

这和设计文档里“shared action head remains the initial policy mean, routed heads contribute residual corrections”的口径不一致。

本次已修正为 residual-neutral bootstrap：

- [policies.py](../../../../python/rl/policy_algo/policies.py:141)
- [policies.py](../../../../python/rl/policy_algo/policies.py:168)

修正后：

1. `self._hmoe_residual_gate` 初始即为 `hmoe_residual_start_factor`；
2. `initialize_hmoe_from_shared_action_head()` 不再复制 shared 权重到 family head；
3. family/subexpert head 都以零 residual 起步。

### 2.2 首个 rollout 之前原先没有应用 HMoE warmup

旧逻辑里 `set_hmoe_training_progress()` 只在 `train()` 里调用。

但 SB3 的 on-policy 顺序是：

1. 先 `collect_rollouts()`
2. 再 `train()`

这意味着第一批 rollout 发生时，policy 还停留在旧的 `resid_gate` 值。

本次已把 warmup 前移到 rollout 开始前：

- [ppo_adaptive_kl.py](../../../../python/rl/policy_algo/ppo_adaptive_kl.py:102)
- [nonfinite_probe.py](../../../../python/rl/support/nonfinite_probe.py:437)

这里连 `nonfinite probe` 的 monkeypatch rollout 版本也一并补了，否则真实烟测路径会绕回旧行为。

## 三、回归测试补充

这次补了三类回归：

1. residual gate 默认从零 warmup 起步；
2. HMoE bootstrap 保持 zero-residual，而不是复制 shared head；
3. `collect_rollouts()` 的第一次 policy forward 前就能看到 `resid_gate = 0.0`。

对应测试：

- [test_execution_policy_surface.py](../../../../tests/policy/test_execution_policy_surface.py:151)
- [test_policy_bootstrap_initialization.py](../../../../tests/policy/test_policy_bootstrap_initialization.py:45)
- [test_auxiliary_training_updates.py](../../../../tests/policy/test_auxiliary_training_updates.py:65)

本地结果：

```bash
python -m pytest tests/policy/test_execution_policy_surface.py tests/policy/test_policy_bootstrap_initialization.py tests/policy/test_auxiliary_training_updates.py -q
```

结果：`16 passed`

## 四、修复后短烟测结果

执行命令：

```bash
source tools/maintenance/cmo_env.sh
cmo_python train.py \
  --scenario scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_f16c_scripted_red_smoke_v1.json \
  --run_name air_combat_1v1_f16c_scripted_red_hmoe_smoke_v1_diag64_postfix_manual \
  --output_base experiments/smoke \
  --diagnostics_every 64
```

产物：

- [final_model.zip](../../../../experiments/smoke/air_combat_1v1_f16c_scripted_red_hmoe_smoke_v1_diag64_postfix_manual/final_model.zip)

### 4.1 已确认修复生效的部分

前 `64` timesteps 诊断已经出现了和修复前完全不同的信号：

1. `hmoe/resid_gate = 0`
2. `hmoe/resid_effective_scale = 0`
3. `hmoe/resid_abs_mean = 0`
4. `hmoe_params/family/nonzero_frac = 0`
5. `hmoe_params/sub/nonzero_frac = 0`

这说明：

1. 首个 rollout 确实不再带 routed residual；
2. HMoE 冷启动已经真正贴着 shared mean 起步；
3. “第一批轨迹先被 HMoE 残差放大”这条根因已经被实修并验证。

### 4.2 但深失速问题并没有因此消失

修复后，`512` steps 内终止分布依旧被深失速主导：

1. `diag/failure_frac_window = 1.0`
2. `diag/term_frac_failfast_deep_stall = 1.0`
3. 典型 `preterm_max_abs_aoa_deg ≈ 50.0 ~ 51.2`
4. 典型 `preterm_max_abs_pitch_deg ≈ 77.0 ~ 81.8`
5. 典型 `preterm_max_abs_roll_deg ≈ 19.3 ~ 51.7`

最终汇总附近：

1. `rollout/ep_len_mean = 90`
2. `rollout/ep_rew_mean = -348`
3. `hmoe/resid_gate = 1`
4. `hmoe/resid_abs_mean ≈ 0.00305`

和修复前相比，可以说：

1. HMoE 启动链路里的放大问题已经被拿掉；
2. 但拿掉之后，飞机仍会在后续 rollout 中进入高攻角深失速；
3. 所以当前主因已经进一步收缩到“动作面/飞控保护/奖励与终止耦合”这一层，而不是 HMoE 冷启动本身。

## 五、当前阶段最可信的解释

现在更接近下面这个判断：

1. 之前的 HMoE 冷启动实现确实有问题，而且会恶化早期行为；
2. 这个问题修掉后，首轮 rollout 已经恢复为零 residual 启动；
3. 但 `1v1` 当前 `full` 动作面仍允许策略直接输出较激进的 pitch/roll/rudder；
4. 在 `mission_obs_mode = basic`、路由仍固定在 `nav/vector` 的情况下，策略还没有形成足够强的能量管理和高攻角抑制；
5. 于是 episode 仍然会在后续阶段被推到 `AoA > 50 deg`，触发 `failfast_deep_stall`。

换句话说，当前已经可以比较有把握地说：

- HMoE 冷启动问题是“已证实并已修复的加重因素”
- 但不是当前深失速现象的唯一根因，也不是修完后就能单独消掉失速的总根因

## 六、下一步更值得做的事

在这一步之后，最有价值的方向已经不是继续纠缠 HMoE bootstrap，而是继续往飞行动作约束和训练信号上收敛：

1. 检查 `full` 动作面在空战 smoke 初期是否需要更保守的 pitch/roll 初始化或限幅；
2. 评估是否要为 `1v1` 单独增加高 AoA / 高 pitch 的 shaping，而不是只靠 failfast 终止在末端惩罚；
3. 检查 execution control/runtime 是否存在“RL 可以绕过或压穿”当前软保护的路径；
4. 继续补更细的动作-姿态-终止时序诊断，直接看失速前几十步的杆量和姿态演化；
5. 后续再考虑把空战 routing 语义从 `basic -> 更贴近交战语义`，但这不是当前失速问题的第一优先级。

## 七、当前结论

这次排查后，可以把失速问题的判断更新为：

1. 失速不是“你看错了”，而是真实的深失速终止；
2. HMoE 启动链路原先确实有实现缺口，会放大早期不稳定性；
3. 这个缺口现在已经被修掉，并且通过短烟测确认 warmup 在首 rollout 前生效；
4. 但修完后 `failfast_deep_stall` 仍然是 `1v1` 当前主导终止；
5. 因此下一阶段应把主要精力转向动作面稳定性、飞控保护兑现程度、以及高攻角相关 reward shaping。
