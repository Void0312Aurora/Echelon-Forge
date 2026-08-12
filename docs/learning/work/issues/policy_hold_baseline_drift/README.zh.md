# RL 策略保持基线漂移

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/learning/work/issues/policy_hold_baseline_drift/README.md`
Owner: `learning/policy-evaluation`
Last verified: `2026-08-08`

状态：保持类 N4 确定性探针已闭合；仍保留为后续离站位课程和随机策略验收的跟踪项。

首次观察：`2026-05-26`，N4 海军屏护站位 RL 验证期间。

问题类别：强保持基线附近的策略更新漂移。

## 摘要

第一个具体实例出现在 N4 海军屏护站位任务：场景初始就在理想站位，
零动作是一个很强且已经测量过的基线。策略可以被正确初始化为零动作，
但经过 PPO 更新后，会学出稳定的非零命令，而这个命令比零动作基线更差。

这应被视为通用 RL / 训练问题，而不是只属于海军域的问题。未来任何
“保持当前命令”是局部正确行为的任务，都可能遇到同类问题。

## 当前证据

针对 N4 海军屏护站位场景的聚焦诊断显示：

- 零动作回放：`1200` 步总奖励 `89.775565`；
- 低探索 / 动作惩罚探针训练后，确定性回放：`1200` 步总奖励 `-3.1535`；
- 同一 checkpoint 的随机回放：总奖励约 `-16.78`；
- 未训练、只做零动作安全初始化的模型：总奖励 `89.775565`，动作均值正好是
  `[0.0, 0.0, 0.0]`；
- 训练后确定性动作均值：
  `[+0.077, -0.194, +0.024]`。

按当前 `naval_station3` 映射，这个确定性动作大致意味着：

- 屏护站位方位偏移约 `+1.9 deg`；
- 屏护半径缩小约 `350 m`；
- 很小的正速度偏置。

接触发现、共享航迹、报告链和预开火 ROE 奖励仍然正常出现。因此失败
不能解释为场景坏了或报告链缺失；关键是 actor 在训练后离开了中性的
保持命令。

## 2026-05-27 小范围修复探针

已加入一个默认关闭的训练侧保持先验：

- `AdaptiveKLPPO` 支持 `action_mean_regularization_coef` 和
  `action_mean_regularization_target`；
- 该正则约束当前策略的确定性动作均值贴近目标动作；
- 非有限值探针会替换训练循环，因此已同步同一项损失和日志，避免诊断模式下
  配置项被静默忽略；
- 活跃海军屏护站位 smoke 配置暂用该保持先验，并关闭 actor/critic 共享特征层，
  作为继续诊断的保守入口。

同一 `WorldBatchVecEnv` 回放路径下的 4096 步低探索探针结果：

- 零动作基线：`89.775565`；
- `coef=5`：确定性回放 `29.689964`，随机回放 `6.865154`，
  确定性动作均值约 `[+0.093636, -0.177952, -0.000888]`；
- `coef=50`：确定性回放 `63.706747`，随机回放 `56.213039`，
  确定性动作均值约 `[-0.042754, +0.009271, -0.041420]`；
- `coef=50` 且 `share_features_extractor=false`：确定性回放 `80.572003`，
  随机回放 `73.745653`，确定性动作均值约
  `[-0.014999, -0.000956, -0.014365]`；
- `coef=500` 且 `share_features_extractor=false`：确定性回放 `85.676334`，
  随机回放 `79.300771`，确定性动作均值约
  `[-0.000535, -0.012665, -0.000574]`。
- `coef=500`、`share_features_extractor=false`、`learning_rate=1e-4`、
  `n_steps=batch_size=128`：确定性回放 `89.330973`，随机回放 `78.927745`，
  确定性动作均值约 `[+0.000879, -0.001092, -0.003074]`。
- 同上，并给 `naval_station3` 增加 `0.005` 近零动作死区后重新训练 `4096` 步：
  确定性回放 `89.775565`，与零动作基线一致；随机回放 `79.597278`；
  原始确定性动作均值约 `[+0.000795, -0.001017, -0.003045]`，实际下发动作均值约
  `[+0.0000007, -0.0000007, -0.0000026]`。

确认过的细节：当前 `SquashedDiagGaussianDistribution.mode()` 返回 tanh 后动作，
因此 actor mean 正则约束的是实际下发给环境的动作空间，不是未压缩的内部高斯均值。

结论：问题根因已经收敛到动作面解释层：千分位级别的策略均值微抖被当成真实站位
改令，并持续触发动作惩罚和站位误差。小范围修复组合（actor mean 保持先验、
actor/critic 特征解耦、保守 PPO batch/学习率、`naval_station3` 近零死区）已经让
N4 屏护保持任务的确定性训练探针追平零动作基线。随机策略仍低于基线，因此该结论
只覆盖确定性保持探针，不覆盖离站位课程、随机策略验收、武器释放或交火。

## 相关领域上下文

- 海军 N5 动作 / 观测拆分：
  [保留的 N4 action-surface repair](../../../../domains/naval/reviews/n5_rl_action_surface_split_20260527/README.zh.md)
- 当前 N4 海军测试场景：
  `scenarios/naval/ddg51_take1_screen_threat_roe_v1.json`
- 第一批短探针使用的训练配置：
  `examples/config/training/active/naval/naval_screen_station_hold_threat_aware_smoke_v1.json`

## 2026-05-27 海军基础设施闭合更新

N4 海军屏护站位运行时已经不再依赖奖励抵消来处理机场专用安全项：

- 海军 tasking profile 会在构造 safety runtime 输入之前关闭跑道阶段 / 离跑道解释；
- 海军 profile 下的 `naval_suppress_off_runway_penalty` 已退役；开启它会快速失败，而不是
  遮盖一个仍然活跃的 `off_runway_penalty`；
- 海军 profile 不再构造飞行塑形奖励输入，因此 `speed_reward` 和 `roll_stability` 不再作为
  零值海军奖励项出现。
- 海军 profile 的 full step-info 输出会过滤 `on_runway`、`runway_cross_m`、
  `gear_collapsed`、`gear_stress` 这类机场 / 起降诊断字段，包括 episode-controller
  mainline facade 路径。
- 海军策略观测暂时保持现有 `instruments` 形状以兼容模型接口，但在暴露给 policy 前过滤
  IAS、Mach、气压 / 雷达高度、AOA、起落架 / 襟翼 / 减速板、ILS 等飞机 / 机场专用字段；
  执行运行时和安全判定内部仍使用原始仪表状态。海军 loader 也会禁用 execution-observation
  device export，使 torch policy bridge 从过滤后的 buffer 读取，而不是通过 flat device view
  绕过过滤。
- 海军 tasking profile 使用 `takeoff4` 等空军动作模式启动时会快速失败；单槽位和
  cooperative batch 路径都会把 `naval_station3` 解释为站位指令意图，同时只发送中性的
  低层舰艇 carrier action。
- `naval_station3` 死区会先于 policy 自感知 / `last_action` 记录生效，因此 policy
  看到的上一步动作、奖励中的动作惩罚、实际下发的站位指令都使用同一个生效命令。
  `0.004` 级别的小动作现在会在 `proprio`、`last_action` 和
  `_naval_station3_last_action` 中同时表现为 `[0.0, 0.0, 0.0]`；覆盖路径包括
  维护中的 world-batch 路径、cooperative 路径、显式 raw-compat `UniversalEnv`，
  以及 single-world / leader 兼容运行时门面。

零动作基线仍为 `1200` 步 `89.775565`，但奖励拆分现在只包含海军站位、接触、报告、
ROE 项，以及零值的通用安全生存项。这是基础设施闭合进展，不代表武器释放、毁伤、
随机策略验收或离站位站位改令学习已经闭合。

## 2026-05-27 离站位奖励参考闭合

后续探针发现了一个独立的奖励参考风险：如果站位奖励使用 policy 已经改写过的站位
命令来评价，那么半径改令可以把评分参考点移动到舰艇附近，看起来像是动作有用，
但舰艇并没有真正回到原始任务站位。

N4 海军运行时现在会在 reset 时绑定站位评价参考：

- `naval_station3` 动作仍然可以更新经 task / mission-command 链下发给舰艇的站位命令；
- 站位误差奖励和 `mission_status[0]` 使用 reset 时捕获的原始任务站位参考评价；
- world-batch、cooperative 和 raw `UniversalEnv` reset 路径绑定同一套评价参考；
- 聚焦 runtime 测试覆盖 world-batch 与 cooperative 路径，确保匹配半径改令不能把奖励
  参考点拉到离站位的本舰位置。

维护中的 eval 工具现在支持 `--mode offstation_probe`。该 probe 可以派生临时
DDG-inside-station 场景，也可以直接运行维护态
`scenarios/naval/ddg51_take1_screen_threat_roe_offstation_recovery_v1.json`
场景。在 DDG 初始位于名义屏护半径内侧 `1800 m` 时，零动作脚本站位保持现在会在
固定原始任务参考下降低站位误差。匹配半径改令仍低于零动作奖励，且最终离原始任务
站位更远，因为动作成本和固定参考都在生效。维护态恢复场景启用
`naval_station_recovery_progress_bonus`，让 curriculum 信号绑定真实站位误差下降，
而不是移动评分参考点。这闭合的是自引用奖励漏洞并证明脚本恢复 gate，不是已学会
离站位恢复策略的证据。

## 已修复的前置问题

在把本问题拆出来之前，若干更早的阻塞已经识别或修复：

- 海军 mission observation 已拆出专用 `naval_screen_station_v1`，不再使用
  空军 formation-role 观测面；
- transformer mission 预处理已按海军字段语义处理该向量，不再按空军航线字段缩放；
- `naval_station3` 安全初始化会同时清零 bias 和 action-head weight；
- 奖励面已经可以惩罚无必要的站位改令。

这些修复是必要条件，但单独还不足够：若不同时保留保持先验、保守 PPO 设置和
`naval_station3` 近零死区，PPO 更新后 actor 仍可能漂向非零确定性命令。采用这组
小范围修复后，确定性保持探针已经追平零动作基线；随机策略验收和离站位学习仍然开放。

## 假设

当前主要假设：

- 任务局部退化：初始就在正确站位，探索通常只会伤害收益，所以训练信号主要是在
  保持最优附近的小噪声差异；
- 当前 PPO 探针 rollout 很小，`n_steps=32`、`batch_size=32`、`n_epochs=1`，
  每次更新平均不足，容易被单个小批次推动 actor；
- 将 `n_steps=batch_size` 提升到 `128` 并把学习率降到 `1e-4` 后，确定性回放
  已接近零动作基线，但仍没有追平；
- `naval_station3` 需要小死区来表达“保持命令”的工程语义；否则数值微抖会被解释为
  每步改令；
- actor/critic 共享特征层会让 value loss 间接改变 actor 表征；关闭共享特征层后
  漂移明显下降，但没有完全消失；
- 当前配置下日志中的 KL 接近零，并不能证明更新后的确定性均值仍然贴近保持策略；
- 奖励层动作惩罚能减轻损害，但没有显式约束 actor mean 保持在零附近；
- 当前课程没有给出“非零站位改令能带来正收益”的场景；离站位探针现在也会阻止
  站位改令通过移动奖励参考点得分，因此有用非零命令仍需要单独课程验证。
- `naval_station_recovery_progress_bonus` 只在维护态离站位恢复入口中启用；普通
  contact-report 和 station-hold 入口仍保持关闭。这提供稳定的脚本恢复 gate，但不提升为
  learned off-station policy 验收。

## 不能宣称

该 issue 未关闭前，不应宣称：

- N4 海军正式 RL 训练成功；
- 训练后的 N4 确定性保持探针优于零动作基线；
- 该问题只属于海军域；
- 接触 / 报告链行为是主要失败原因；
- 本 issue 覆盖武器释放、毁伤或击杀行为。

## 下一步门槛

后续修复应选择一个或多个受控路径：

- 为保持类任务加入显式 actor mean 正则或保持命令先验；
- 通过更大的 rollout batch、更低学习率或更保守的 actor 更新降低 PPO 更新噪声，
  然后重新检查确定性均值漂移；
- 为中性保持命令加入行为克隆或约束步骤；
- 构造离站位课程，让非零站位动作在固定原始任务站位参考下产生真实正收益，再与保持
  基线分开比较；
- 迁移正式 eval 工具，使正式验证使用和训练一致的 `WorldBatchVecEnv` 路径。

任何修复的验收都应同时包含奖励和动作输出证据：

- 零动作基线仍被测量；
- 离站位探针确认站位动作不能把奖励参考点移动到本舰身上；
- 训练后的确定性回放在目标课程阶段追平或超过基线；
- 汇报确定性动作均值和绝对均值；
- 奖励项摘要确认接触、报告、ROE 链仍然按预期工作。
