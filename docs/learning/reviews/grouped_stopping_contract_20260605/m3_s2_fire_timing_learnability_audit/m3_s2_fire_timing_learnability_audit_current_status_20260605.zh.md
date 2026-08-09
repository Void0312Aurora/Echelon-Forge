# M3-S2 开火时机可学习性审计当前状态

父级：[README.zh.md](README.zh.md)。

状态：`2026-06-08` diagnosis active；support-preserving collect repair 已部分接受，
boundary-dedicated 短训方向已改善，log-domain cumulative-hazard repair 已接受，
scale-separated stopping contract 已实现，chain-breakpoint localization 已接受，
behavioral event timing 仍 held，head-normalization calibration 负向证据已记录，
window-classifier replay 负向行为证据已记录，calibrated standardization 负向集成证据已记录，
classifier standardization contract 断点已局部化，execution-support classifier mismatch
已确认，direct fire-boundary training path 已在 nonfinite-probe tracing 下恢复；
首个 continuation run 已记录一次 deterministic authorized release，但行为仍 held。

## 形式对象

active Stage-1 开火问题可抽象为 masked、edge-triggered stopping process：

```text
state/history:      h_t
legal mask:         m_t in {0, 1}
transport output:   u_t in [0, 1]
event pulse:        e_t = 1[u_t > 0.5 and u_{t-1} <= 0.5 and m_t = 1]
early rejection:    q_t = 1[u_t > 0.5 and u_{t-1} <= 0.5 and m_t = 0]
return:             R = shaping + release_bonus * sum(e_t) + downstream_effect_terms
constraint:         sum(e_t) <= 1 unless explicit reattack is authorized
```

learned policy 必须同时解决两个问题：

- 在有用 legal window 内选择 stopping time；
- 把 stopping time 表达成 low-to-high executable pulse，而不是持续高的连续标量。

## 当前诊断

| Question | Result | Evidence |
| --- | --- | --- |
| oracle legal pulse 能否发射导弹？ | yes | `legal_mask_fire_delay_*` 在两个审计 episode 中均发射一枚 authorized missile。 |
| 环境是否区分 release 与 no release？ | yes | 合法 release 相比 hold-fire 增加约 `450` return。 |
| 环境是否区分合法时机差异？ | partial | delay `0`、`31`、`63` 是平的，但 `0..1778` full delay sweep 找到稀疏 damage 与 terminal-win spikes。 |
| release 是否暴露 downstream effects？ | yes, sparsely | full sweep 记录 `270` 个 effects/damage reports 与 `27` 个 combat wins。 |
| reward 是否正确排序 useful wins？ | no | 更晚 win 因 terminal success 前每步约 `0.04` return 的正向 shaping 而高于更早 win。 |
| learned deterministic policies 是否选择 supported fire？ | no | M3-S1 与 A7 probes 在 open masks 下仍将 event fire probability 保持在约 `0.3%`，event mode 仍为 `hold`。 |
| credit support 是否完全不存在？ | no | probe rows 显示 event-credit advantage 约 `0.8` 为正，但 actor event logits 仍约 `-5.6` 到 `-5.8`。 |
| direct actor event-window supervision 是否解决？ | no | M3-S2 产生 executable-event 非零梯度，并将 window logits 从约 `-6.25` 抬到 `-5.62`，但 deterministic probing 仍记录 `0` releases。 |
| 很小的每步 fire probability 在 prewindow 中是否安全？ | no | `p ~= 0.0055` 在 `800` 个 prewindow steps 上意味着 `0.988` 的累计 early-sample risk。 |
| support-preserving collection 能否阻止 rollout support collapse？ | yes, for collection | whole-window shield 在 8k run 中保持 `grouped_active_group_count = 4`，最终 `closed_mask_row_count = 0`，并阻止 collection 阶段出现 accepted rollout events。 |
| 该修复是否让 learned deterministic policy 开火？ | no | deterministic probing 仍记录 `release_count = 0`、`policy_event_mode_fire_once_count = 0`，以及 `1080` 个 quality-window steps。 |
| 纯 M3-S2 grouped objective 能否学会抽象 one-shot window pulse？ | yes | Structural toy `800 + 1080` 在 free logits 与 MLP 下均通过：prewindow risk 低于 `0.02`，prewindow 无边界 crossing，quality-window logits 跨过 deterministic mode。 |
| 真实 M3-S2 update path 是否抬高 quality-window logits？ | only after contract/optimizer repair | 复用 optimizer 的 event-mass update 会压低 quality logits；final boundary-contract probe 在 reset/dedicated optimizer 模拟下把 quality max logit 抬高约 `0.3136`。 |
| boundary-dedicated 短训是否改变行为？ | 方向 yes，deterministic 行为 no | 8k run 将 `m3s2/q_boundary_logit` 从约 `-5.95` 抬到 `-4.71`；deterministic probe 仍 release `0`；stochastic probe 在第 `623` 步采样到一次授权发射。 |
| policy observation/latent 是否包含窗口信号？ | yes | 固定 forced-hold batch 上，raw mission fields、frozen extractor features 与 frozen actor latent 都线性可分；窗口分类 accuracy 约 `100%`。 |
| 当前 executable action path 能否过拟合该划分？ | no | Boundary-only 与 active-contract overfits 会抬高所有 legal logits；`current` 与 `current_plus_features` 上的 row-wise BCE 坍缩为 all-positive majority-class behavior。 |
| log-domain cumulative-hazard repair 是否改善 stopping-head adapter？ | partially | 它将 deterministic M3 stop probability 从约 `0.47` 降到 `0.145`，但 deterministic release 仍为 `0`，stochastic 仍在第 `5` 步提前采样一次授权 release。 |
| 显式尺度分离 stopping contract 是否解决窗口脉冲？ | no | 它将 logged prewindow hazard 从 `0.413` 降到 `0.218`，但 quality logits 与 prewindow logits 同步下降；deterministic release 仍为 `0`，stochastic 仍在第 `7` 步提前 release。 |
| 固定链路断点在哪里？ | M3 head optimization conditioning | 固定 forced-hold 轨迹上，label、standardized frozen actor latent、folded-head action adapter 与 edge-trigger pulse 都通过；direct raw M3 head fitting 仍残留 prewindow positives。 |
| head normalization 加显式 logit calibration 是否解决？ | no | 8k run 将 deterministic M3 stop probability 降到 `0.118269`，但 deterministic release 仍为 `0`；real-update probe 通过同时压低 prewindow 与 quality logits 来降低 loss，其中 quality mean 从 `-2.003` 降到 `-2.965`。 |
| balanced window-classifier replay 是否解决？ | no | Latent 与 observation replay 都能在训练 batch 上分开正/负 classifier logits，但 saved deterministic probe 仍记录 `release_count = 0`，quality-window classifier logits 约 `-8.24`；observation-replay stochastic probe 在第 `48` 步、quality-window rows 出现前早发一次。 |
| deterministic calibrated standardization 是否解决？ | no | latest-balanced calibration 避免每个 auxiliary step 随机刷新标准化，但 8k final 仍 `release_count = 0`；fixed-chain final 的 current quality classifier logit mean 为 `-9.902827`，fresh head 同轨迹 `200` 步可完美分离。 |
| classifier 输入 standardization contract 在推理时是否对齐？ | no | 固定 `model_event_hold` 轨迹上，保存的 buffer 给出 quality logit mean `-9.837499` 与 `0 / 1080` 个 quality boundaries。只重算该 fixed batch 的 `m3_window_classifier_input_mean/std` 后，quality logit mean 变为 `2.195754`，quality boundaries 变为 `1053 / 1080`。 |
| actor-gradient isolation 与 post-update classifier restore 是否解决行为？ | no | 8k best-restore run 的 post-update replay batch 指标可分离，但 deterministic execution 仍记录 `release_count = 0`；fixed-chain current quality classifier logit mean 为 `-6.339776`，同一 execution latent 上 fresh standardized head 达到 `1080 / 1080` quality boundaries。 |
| direct executable fire-boundary ownership 是否解决行为？ | bounded firing gate accepted, timing/effects held | `2026-06-08` continuation run 从 r3 初始化，deterministic probe 在 step `423` 记录一次 authorized release。A5 武器保险动作帧修复后，bounded batch validation 检查 `8` 个 deterministic episode 与 `8` 个 stochastic episode，结果 `16 / 16` 通过：每个 episode 都记录 `1 / 1 / 0` requested/accepted/rejected、一次 authorized release、零 violation、零 repeat-before-assessment release。 |
| target acquisition 前高标量是否能后来恢复？ | no | `forced_fire` 记录 `{"no_target": 2}` 且无 release，因为后续没有新的 rising edge。 |

## 根因陈述

当前失败不只是“短训没有学会”。当前证据需要区分症状与机制：

- already-winning shots 的 reward ordering 错误：正向 per-step shaping 让更晚 terminal success
  高于更早 terminal success；
- no-fire 不能由 reward surface 解释：oracle legal release 可达、有奖励，并且能产生 terminal wins；
- learned-policy no-fire 是可见症状：masks 打开且 stochastic samples 可以 release，但 deterministic
  event logits 仍在 `hold` 一侧；
- 机制是当前训练合同本身。episode-level first-event credit 最初在 rollout-local chunks 上计算，
  early stochastic releases 后会删除 shadow-positive support。该 support 问题修复后，剩余 A7
  bridge 仍把 event logits 训练到 detached、tiny、未校准的 credit advantage，而不是 signed
  timing target。因此 actor representation 没有学到 deterministic `argmax(fire_once)` 所需的
  prewindow/quality-window 判别器。

这意味着 reward repair 必要，但不足以解释 learned model 为什么不发射。剩余可达性问题是：
learned policy 能否通过 masked edge-triggered transport 表达一个 supported fire event。

M3-S2 event-window probe 排除了一个候选解释：失败不只是 actor event logits 缺少 direct
supervised loss。现在 executable event distribution 已经能接收 grouped window-level
gradients。剩余问题是 supported quality-window rows 是间歇性的，并且 learned logit 仍远低于
deterministic fire boundary。

`2026-06-06` 更尖锐的诊断是 cumulative prewindow hazard。逐行概率约 `0.0055` 看起来很小，
但在 `800` 个 prewindow steps 上几乎必然 stochastic early consumption。该 early sample 会让
runtime 进入 `FiredAssess`、关闭 `fire_mask`，并移除 M3-S2 后续训练所需的 quality-window rows。

support-preserving collection 修复确认了这个诊断。当 collector 在整个 legal-open support
window 内保持 `fire_once = 0` 时，训练轨迹不再坍缩为 closed-mask rows：8k support run 最终记录
`grouped_active_group_count = 4`、`grouped_active_row_count = 1024`、
`closed_mask_row_count = 0`。但是 learned policy 仍把 `fire_once` 保持在 hold 一侧；
deterministic probing 仍为 `0` releases，而 stochastic probing 仍可能提前采样 release。
因此剩余断点是 event-boundary transport 或 actor target calibration，而不只是缺少
quality-window rows。

structural toy probe 排除了另一个可能解释：grouped M3-S2 loss 本身能够学会所需 boundary。
在 `800` 个 prewindow steps 与 `1080` 个 quality-window steps 下，`free_logits` 达到
prewindow cumulative risk `0.009140485` 与 quality max logit `2.393876`；MLP 达到
prewindow cumulative risk `0.000005254` 与 quality max logit `9.366981`。两者都在第 `800`
步跨过 quality boundary，且 prewindow 中没有 boundary crossing。

real update path probe 随后把失败局部化到真实 policy transport 和 optimizer contract。
forced-hold Stage-1 序列有 `1880` 个 legal rows 与 `1040` 个 quality rows，但复用 optimizer
的 active M3-S2 update 在降低 loss 的同时把 quality max logit 降低约 `0.265`。
contrastive real-row margin 本身不能修复：即使很高的 contrastive weight 仍会压低绝对
quality logits。高 quality-boundary anchor 若不重置 optimizer state，也会沿当前 loss
反向 step 并让 loss 上升；清空 optimizer state 后，同一个 boundary update 会把真实参数路径的
quality max logit 抬高约 `0.3136`。当前局部断点因此是两层：stochastic event-mass
supervision 不是 deterministic boundary contract，且 auxiliary update 必须与 PPO Adam
状态隔离。

boundary-dedicated 8k 短训只在更新方向层面确认了这一修复。supported training batches
将在线 quality-boundary logit 从约 `-5.95` 抬到 `-4.71`，但 deterministic probing
仍记录 `release_count = 0`、`policy_event_mode_fire_once_count = 0` 与
`policy_m3_boundary_cross_count = 0`。stochastic probe 在第 `623` 步采样到一次授权发射，
且最大 event probability 仍约 `0.42%`；这只能证明 sampled executable behavior 存在，
不能证明 deterministic stopping boundary 已学会。

Single-batch window-signal probing 进一步局部化剩余失败。固定 forced-hold batch
中存在直接分离 mission features：prewindow rows 的 `launch_window_open = 0`，
quality-window rows 的 `launch_window_open = 1`。frozen-feature linear probe
在 raw mission fields、temporal extractor output 与 actor latent 上都达到近乎完美分类。
但是通过当前 executable `fire_event_logit_delta` path 训练时，并没有学到这一分离器：
boundary-only 与 active-contract overfits 会把 prewindow 与 quality logits 全部推过 0，
current action path 上的 row-wise BCE 也坍缩为 all-positive majority behavior。因此当前
断点是 event-logit/action-transport contract，而不是缺少状态信号。

stopping-head adapter 与 log-domain cumulative-hazard repair 为诊断增加了一层。
先前 grouped stopping loss 在概率域计算 `p_window`/`p_none`，随后用 `eps` clamp；
`800` 步 prewindow 下，概率下溢后这会擦掉 survival gradient。修复后的 loss 使用
log-sum-exp 与 log survival 项。聚焦 real-update probe 现在能把 prewindow logit mean
从 `-0.117777` 压到 `-2.430021`，loss 从 `1707.144817` 降到 `70.558770`，
证明长 prewindow survival gradient 已恢复。同一更新也会压低 quality logits，并且仍记录
`0 / 1040` quality-boundary crossings，因此剩余合同问题是尺度分离：prewindow hazard
必须接近 `1 / horizon`，同时 quality window 仍需要 deterministic pulse。

显式尺度分离 stopping contract 直接验证了这一判断。contract 已接入 loss、logs、
diagnostics、active config 和 focused tests。8k 短训中，有窗口样本的 update 推导出
prewindow target `0.000651`；logged prewindow hazard 从 `0.413` 降到 `0.218`，
说明新项确实生效。但是 quality-window logits 也跟着 prewindow logits 同步下降：
quality boundary logit 从 `-0.346` 降到 `-1.273`，quality target loss 从
`2.086` 升到 `5.627`，boundary crossing 仍为 `0`。deterministic probing 再次记录
`release_count = 0`；stochastic probing 仍在第 `7` 步提前采样 release。这把“尺度分离”
从假设推进为负向集成结果：当前 executable stopping/action contract 仍缺少已学会的
prewindow-versus-quality discriminator。

链路断点定位 probe 把这个诊断转成固定 yes/no 阶梯。在最新 scale-separated checkpoint 上，
一条 forced-hold 轨迹包含 `840` 个 prewindow rows 与 `1040` 个 quality rows。
standardized frozen actor latent 上的线性 head 能完美分离：prewindow boundary
`0 / 840`，quality boundary `1040 / 1040`，separation margin 超过 `10`。
将该 standardized head 折叠回 raw latent space 并安装为 M3 stopping head 后，
action transport 行为正确：event mode 在 prewindow `0 / 840`，在 quality `1040 / 1040`，
edge-trigger 模拟在 row `281` 产生一次合法 quality pulse。相反，当前 learned head 的
quality boundary 是 `0 / 1040`，event mode fire 为 `0`。在同一 frozen latent 上直接优化
raw M3 head 几乎能通过，但根据学习率仍残留 `4` 到 `6` 个 prewindow positives，并漏掉
`2` 到 `5` 个 quality rows。因此第一个局部断点是 M3 head optimization
conditioning/calibration，而不是 labels、latent signal、adapter behavior 或 edge-trigger
semantics。

head-normalized calibration 修复验证了最直接的下一假设，但结果仍 held。M3 `LayerNorm`、
显式 prewindow/quality logit margins、dedicated optimizer membership、logs、diagnostics
和 active config support 均已接线。8k 短训将 deterministic M3 stop probability 从上一轮
scale-separated 的 `0.157226` 降到 `0.118269`，但 prewindow 与 quality probabilities
仍几乎相同，deterministic release 仍为 `0`。real-update probe 更尖锐：在一批包含
`1040` 个 quality rows 的 forced-hold 样本上，`current` updates 将 loss 从 `634.18`
降到 `557.86`，同时把 quality mean logit 从 `-2.003` 继续压到 `-2.965`。更容易的
loss 下降方向仍是 global hazard suppression，而不是 quality-window boundary formation。

direct fire-boundary owner 修复首先定位了一个具体实现断点：`NonFiniteTrainingProbe`
曾用 copied training loop 覆盖 `model.train()`，但该路径没有调用
`_m3s2_fire_boundary_auxiliary_update()`。同步 traced train path 后，`2026-06-07`
r3 run 证明 `m3s2/fb_*` updates 已经 live，但 deterministic release 仍为 `0`。
`2026-06-08` continuation 从 r3 初始化，是 active evidence 中第一次记录一次
deterministic authorized release 的结果，release step 为 `423`。剩余 stochastic
拒绝不是杀伤链问题，而是动作帧不一致：模型请求 `fire_once`，但同一帧武器保险开关
（代码字段 `master_arm`）是关的。A5 有效动作修复后，请求 `fire_once` 会同时派生
`master_arm = 1`。后续 batch validation 检查 seeds `20260608..20260615` 上
`8` 个 deterministic episode 与 `8` 个 stochastic episode；全部 `16` 个 episode
通过 firing gate，rejected requests、violations、repeat-before-assessment releases
均为 `0`。因此，对该 active scenario/config pair，release gate 已闭合。Timing
quality、post-release effect quality 与 kill-chain behavior 仍是独立 held claim。

## Learned-Policy 可达性证据

维护证据页：
[m3_s2_fire_timing_learned_policy_reachability_probe_20260605.zh.md](m3_s2_fire_timing_learned_policy_reachability_probe_20260605.zh.md)。

关键发现：

- M3-S1 state-completed deterministic probes 记录 open masks `1880` 和 `1840` 步，
  但 `policy_event_prob_fire_once_max` 低于 `0.00384`，且
  `policy_event_mode_fire_once_count` 为 `0`。
- A7 safe-bias deterministic probes 记录 open masks `639` 和 `599` 步，但
  `policy_event_prob_fire_once_max` 低于 `0.00315`，且
  `policy_event_mode_fire_once_count` 为 `0`。
- stochastic probes 有时能 release 一枚 missile，说明 runtime event path 在采样到时可执行，
  但这些 release 是低概率样本，不是 learned deterministic boundary。
- event-credit advantage 在 prewindow 与 quality rows 中可为约 `0.8` 的正值，但 actor event
  probabilities 在两个区域几乎相同，并且都约为 `0.3%`。
- M3 stopping head 仍然只是辅助：M3-S1 deterministic probe 中它报告 `stop_prob = 0.5`
  并且每步 boundary crossing，但没有 emit executable `fire_once` action。
- M3-S2 direct event-window supervision 能到达 executable event path：
  `m3s2/event_window_grad_norm` 峰值为 `22.19`，但 deterministic probing 仍看到
  `1080` 个 quality-window steps、`policy_event_prob_fire_once_max = 0.00556`，
  且 `policy_event_mode_fire_once_count = 0`。
- 同一个 deterministic probe 记录 `a7_prewindow_step_count = 800`、
  `a7_prewindow_event_fire_prob_mean = 0.005541579`、
  `a7_prewindow_event_fire_prob_cum = 0.988269851`；stochastic probe 随后在第 `14`
  步提前 release，此前没有观测到 quality-window row。
- support-preserving r2 训练轨迹在所有 logged updates 中都保持 active groups
  (`min = 4`, `final = 4`)，并阻止 rollout accepted events
  (`accepted_event_count = 0` throughout)，但 `boundary_cross_count` 仍为 `0`。
- support-preserving r2 deterministic probe 记录 `release_count = 0`、
  `a7_quality_window_step_count = 1080`、
  `policy_event_prob_fire_once_max = 0.003296760`、
  `a7_prewindow_event_fire_prob_cum = 0.927001125`。
- structural toy probe 对 `free_logits` 与 `mlp` 均记录
  `all_structural_toys_pass = true`；artifact 为
  `experiments_tmp/m3s2_structural_toy_probe_20260606.json`。
- real update path probe 记录 `has_quality_rows = true`、
  `any_update_raises_quality_logit = false` 与
  `any_update_quality_boundary = false`；artifacts 为
  `experiments_tmp/m3s2_real_update_path_probe_20260606_4step.json` 与
  `experiments_tmp/m3s2_real_update_path_probe_20260606_40step_current.json`。
- boundary/optimizer contract probe 记录 contrastive margin 本身仍会压低绝对 quality logits；
  final boundary-contract update 在 reset/dedicated optimizer 模拟下把 quality max logit
  抬高 `0.313624`；artifact 为
  `experiments_tmp/m3s2_real_update_path_probe_20260606_final_config_dedicated_sim_4step.json`。
- boundary-dedicated 短训记录在线 quality-boundary 从约 `-5.95` 到 `-4.71` 的移动、
  deterministic `release_count = 0`，以及 stochastic 在第 `623` 步一次授权发射；artifacts 为
  `experiments_tmp/m3s2_boundary_dedicated_8k_20260606_r2/final_model.zip`、
  `experiments_tmp/m3s2_boundary_dedicated_8k_20260606_r2/m3s2_deterministic_probe.json`
  与
  `experiments_tmp/m3s2_boundary_dedicated_8k_20260606_r2/m3s2_stochastic_probe.json`。
- Single-batch window-signal probes 显示：boundary-only 与 active-contract overfits
  均发生 all-high collapse，current action path 上的 row-wise BCE 发生 majority-class
  collapse，而 raw mission、frozen features 与 frozen actor latent 近乎完美可分；artifacts 为
  `experiments_tmp/m3s2_single_batch_boundary_only_overfit_20260606.json`、
  `experiments_tmp/m3s2_single_batch_active_contract_overfit_20260606.json`、
  `experiments_tmp/m3s2_single_batch_row_bce_capacity_20260606.json`、
  `experiments_tmp/m3s2_single_batch_row_bce_capacity_features_20260606.json`、
  `experiments_tmp/m3s2_window_signal_feature_probe_20260606.json` 与
  `experiments_tmp/m3s2_frozen_latent_event_head_balanced_bce_20260606.json`。
- stopping-head adapter log-domain 短训将 deterministic
  `policy_m3_stop_prob_mean` 从约 `0.470836` 降到 `0.145112`，但仍记录
  deterministic `release_count = 0`；stochastic probing 在第 `5` 步提前 release。
  Artifacts：
  `experiments_tmp/m3s2_stopping_head_adapter_log_domain_8k_20260606_r1/final_model.zip`、
  `experiments_tmp/m3s2_stopping_head_adapter_log_domain_8k_20260606_r1/m3s2_deterministic_probe.json`、
  `experiments_tmp/m3s2_stopping_head_adapter_log_domain_8k_20260606_r1/m3s2_stochastic_probe.json`
  与
  `experiments_tmp/m3s2_stopping_head_adapter_8k_20260606_r1/m3s2_real_update_stopping_head_probe_log_domain.json`。
- 尺度分离 stopping contract 短训记录了 active prewindow scale pressure，但没有学出边界：
  deterministic `release_count = 0`，stochastic `first_release_step = 7`，
  final deterministic `policy_m3_stop_prob_mean = 0.157226`，且没有 M3 boundary crossing。
  Artifacts：
  `experiments_tmp/m3s2_scale_separated_contract_8k_20260606_r1/final_model.zip`、
  `experiments_tmp/m3s2_scale_separated_contract_8k_20260606_r1/m3s2_deterministic_probe.json`
  与
  `experiments_tmp/m3s2_scale_separated_contract_8k_20260606_r1/m3s2_stochastic_probe.json`。
- 链路断点定位 probe 记录当前局部根因：
  `first_breakpoint = m3_head_optimization_conditioning`、
  `fresh_latent_linear_probe_pass = true`、`adapter_projection_pass = true`、
  `edge_trigger_pass = true`、`current_policy_distribution_pass = false`。
  Artifacts：
  `experiments_tmp/m3s2_chain_breakpoint_probe_20260606_scale_contract_r3_3kfit.json`
  与
  `experiments_tmp/m3s2_chain_breakpoint_probe_20260606_scale_contract_r3_3kfit_lr003.json`。
- head-normalized calibration 短训记录负向集成结果：deterministic `release_count = 0`，
  stochastic `first_release_step = 14`，fresh normalized-head-input probe 通过，而
  real-update probe 记录 `any_update_raises_quality_logit = false`。Artifacts：
  `experiments_tmp/m3s2_head_norm_calibration_8k_20260606_r1/final_model.zip`、
  `experiments_tmp/m3s2_head_norm_calibration_8k_20260606_r1/m3s2_deterministic_probe.json`、
  `experiments_tmp/m3s2_head_norm_calibration_8k_20260606_r1/m3s2_stochastic_probe.json`、
  `experiments_tmp/m3s2_head_norm_calibration_8k_20260606_r1/m3s2_chain_breakpoint_probe.json`
  与
  `experiments_tmp/m3s2_head_norm_calibration_8k_20260606_r1/m3s2_real_update_path_probe.json`。
- 显式 window-classifier integration 已接线但行为仍 held：focused tests 通过，synthetic
  sidecar update 能分离 quality 与 non-quality rows；但 8k Stage-1 run 记录
  deterministic `release_count = 0`，stochastic `first_release_step = 5` 且发生在任何
  quality rows 前，online classifier logits 仍只形成很弱分离。Artifacts：
  `experiments_tmp/m3s2_window_classifier_8k_20260606_r1/final_model.zip`、
  `experiments_tmp/m3s2_window_classifier_8k_20260606_r1/m3s2_deterministic_probe.json`
  与
  `experiments_tmp/m3s2_window_classifier_8k_20260606_r1/m3s2_stochastic_probe.json`。
- calibrated-standardization window-classifier run 给出当前最强根因证据。保存的 buffer
  在固定 `model_event_hold` 轨迹上得到 `quality_logit_mean = -9.837499` 与
  `quality_boundary_count = 0 / 1080`。不改变 classifier 权重，只在 fixed batch 上重算
  `m3_window_classifier_input_mean/std` 后，得到 `quality_logit_mean = 2.195754`
  与 `quality_boundary_count = 1053 / 1080`。head 内含 timing signal，但 executable path
  在按 replay 校准的 normalization contract 下运行，未与 execution-support 轨迹对齐。
  Artifact：
  `experiments_tmp/m3s2_window_classifier_calibrated_std_8k_20260606_r2/m3s2_chain_breakpoint_probe_final_model_event_hold_recalibration_r1.json`。

## 推荐下一切片

不要把 M2 memory 作为第一修复。memory 可能帮助表示历史，但最新证据显示，当前 no-fire
plateau 的直接原因是 classifier normalization contract 断裂：保存的 executable
standardization buffers 校准到 replay/support batches，并把 execution-support 轨迹整体推到负侧。

下一切片应作为 classifier standardization-contract repair 打开，包含以下候选方向：

1. 从 executable classifier path 移除 mutable population standardization，依赖 per-sample
   `LayerNorm` 加 linear classifier head。
2. 若保留 population standardization，则用稳定的 execution-support population 校准，而不是
   latest-balanced replay，并在 deterministic evaluation 前冻结。
3. 增加 post-update diagnostics：每次都在固定 `model_event_hold` support 轨迹上评估 saved
   executable head，避免把 training-batch separation 误当成 execution readiness。
4. 保持 deterministic boundary contract：要求 quality-window boundary crossing，且不能有
   prewindow pulse consumption；不能只看 replay accuracy。
5. 将 support-preserving collection 保持为 diagnostic guard，但不计为 behavior acceptance。
6. standardization contract 修复后，再复查 event-to-pulse adapter 与 reward-contract 缺陷；
   二者仍是验收门。

M2 只应在 action-event adapter 与 reward contract 有明确验收门后继续作为候选，或者由 M2
明确承担 stopping output 到 executable pulse 的 adapter。

## 已运行验证

```bash
python -m py_compile \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  tools/diagnostics/fire_timing_fault_localization/learnability_audit.py \
  tests/runtime/air_combat/test_diagnostics_probe_contracts.py \
  tests/training/test_fire_timing_fault_localization_contracts.py
```

结果：pass。

```bash
python -m pytest \
  tests/runtime/air_combat/test_diagnostics_probe_contracts.py \
  tests/training/test_fire_timing_fault_localization_contracts.py -q
```

结果：`13 passed`。

Audit artifact：

```text
experiments_tmp/air_combat_fire_timing_learnability_audit_20260605.json
```

Full delay sweep artifacts：

```text
experiments_tmp/air_combat_fire_timing_full_delay_sweep_seed7_ep1_0_1778_20260605_summary.json
experiments_tmp/air_combat_fire_timing_full_delay_sweep_seed7_ep1_0_1778_20260605_compact.csv
experiments_tmp/air_combat_fire_timing_full_delay_sweep_seed7_ep1_0_1778_20260605.png
```

Learned-policy reachability artifacts：

```text
experiments_tmp/m3s1_p5_state_completed_8k_20260605_r1/m3s1_deterministic_probe.json
experiments_tmp/m3s1_p5_state_completed_8k_20260605_r1/m3s1_stochastic_probe.json
experiments_tmp/a7_event_policy_margin_safe_bias_8k_20260605_r1/deterministic_probe.json
experiments_tmp/a7_event_policy_margin_safe_bias_8k_20260605_r1/stochastic_probe.json
```

M3-S2 event-window artifacts：

```text
experiments_tmp/m3s2_event_window_8k_20260605_r2/final_model.zip
experiments_tmp/m3s2_event_window_8k_20260605_r2/m3s2_deterministic_probe.json
experiments_tmp/m3s2_event_window_8k_20260605_r2/m3s2_stochastic_probe.json
```

M3-S2 support-preserving artifacts：

```text
experiments_tmp/m3s2_support_preserve_8k_20260606_r1/final_model.zip
experiments_tmp/m3s2_support_preserve_8k_20260606_r1/m3s2_deterministic_probe.json
experiments_tmp/m3s2_support_preserve_8k_20260606_r1/m3s2_stochastic_probe.json
experiments_tmp/m3s2_support_preserve_8k_20260606_r2/final_model.zip
experiments_tmp/m3s2_support_preserve_8k_20260606_r2/m3s2_deterministic_probe.json
experiments_tmp/m3s2_support_preserve_8k_20260606_r2/m3s2_stochastic_probe.json
```

M3-S2 boundary-dedicated short-train artifacts：

```text
experiments_tmp/m3s2_boundary_dedicated_8k_20260606_r2/final_model.zip
experiments_tmp/m3s2_boundary_dedicated_8k_20260606_r2/m3s2_deterministic_probe.json
experiments_tmp/m3s2_boundary_dedicated_8k_20260606_r2/m3s2_stochastic_probe.json
```

M3-S2 single-batch window-signal artifacts：

```text
experiments_tmp/m3s2_single_batch_boundary_only_overfit_20260606.json
experiments_tmp/m3s2_single_batch_active_contract_overfit_20260606.json
experiments_tmp/m3s2_single_batch_row_bce_capacity_20260606.json
experiments_tmp/m3s2_single_batch_row_bce_capacity_features_20260606.json
experiments_tmp/m3s2_window_signal_feature_probe_20260606.json
experiments_tmp/m3s2_frozen_latent_event_head_balanced_bce_20260606.json
```

M3-S2 structural toy artifact：

```text
experiments_tmp/m3s2_structural_toy_probe_20260606.json
```

M3-S2 real update path artifacts：

```text
experiments_tmp/m3s2_real_update_path_probe_20260606_4step.json
experiments_tmp/m3s2_real_update_path_probe_20260606_40step_current.json
experiments_tmp/m3s2_real_update_path_probe_20260606_contrastive_4step.json
experiments_tmp/m3s2_real_update_path_probe_20260606_boundary100_window_only_resetopt_4step.json
experiments_tmp/m3s2_real_update_path_probe_20260606_final_config_dedicated_sim_4step.json
experiments_tmp/m3s2_stopping_head_adapter_8k_20260606_r1/m3s2_real_update_stopping_head_probe_log_domain.json
```

M3-S2 stopping-head log-domain 短训 artifacts：

```text
experiments_tmp/m3s2_stopping_head_adapter_log_domain_8k_20260606_r1/final_model.zip
experiments_tmp/m3s2_stopping_head_adapter_log_domain_8k_20260606_r1/m3s2_deterministic_probe.json
experiments_tmp/m3s2_stopping_head_adapter_log_domain_8k_20260606_r1/m3s2_stochastic_probe.json
```

M3-S2 尺度分离 stopping contract 短训 artifacts：

```text
experiments_tmp/m3s2_scale_separated_contract_8k_20260606_r1/final_model.zip
experiments_tmp/m3s2_scale_separated_contract_8k_20260606_r1/m3s2_deterministic_probe.json
experiments_tmp/m3s2_scale_separated_contract_8k_20260606_r1/m3s2_stochastic_probe.json
```

M3-S2 window-classifier standardization-contract artifacts：

```text
experiments_tmp/m3s2_window_classifier_calibrated_std_8k_20260606_r2/final_model.zip
experiments_tmp/m3s2_window_classifier_calibrated_std_8k_20260606_r2/m3s2_chain_breakpoint_probe_final_model_event_hold_recalibration_r1.json
experiments_tmp/m3s2_window_classifier_calibrated_std_8k_20260606_r2/m3s2_chain_breakpoint_probe_final_model_event_hold_stochastic_r1.json
experiments_tmp/m3s2_window_classifier_calibrated_std_8k_20260606_r2/m3s2_chain_breakpoint_probe_final_model_event_hold_fit64_lr003.json
```

Event-window implementation evidence：

```text
docs/learning/reviews/grouped_stopping_contract_20260605/m3_s2_fire_timing_learnability_audit/m3_s2_event_window_supervision_probe_20260605.zh.md
docs/learning/reviews/grouped_stopping_contract_20260605/m3_s2_fire_timing_learnability_audit/m3_s2_cumulative_hazard_support_collapse_20260606.zh.md
docs/learning/reviews/grouped_stopping_contract_20260605/m3_s2_fire_timing_learnability_audit/m3_s2_support_preserving_collect_probe_20260606.zh.md
docs/learning/reviews/grouped_stopping_contract_20260605/m3_s2_fire_timing_learnability_audit/m3_s2_structural_toy_probe_20260606.zh.md
docs/learning/reviews/grouped_stopping_contract_20260605/m3_s2_fire_timing_learnability_audit/m3_s2_real_update_path_probe_20260606.zh.md
docs/learning/reviews/grouped_stopping_contract_20260605/m3_s2_fire_timing_learnability_audit/m3_s2_boundary_optimizer_contract_probe_20260606.zh.md
docs/learning/reviews/grouped_stopping_contract_20260605/m3_s2_fire_timing_learnability_audit/m3_s2_stopping_head_adapter_log_domain_short_train_20260606.zh.md
docs/learning/reviews/grouped_stopping_contract_20260605/m3_s2_fire_timing_learnability_audit/m3_s2_scale_separated_stopping_contract_short_train_20260606.zh.md
docs/learning/reviews/grouped_stopping_contract_20260605/m3_s2_fire_timing_learnability_audit/m3_s2_chain_breakpoint_probe_20260606.zh.md
docs/learning/reviews/grouped_stopping_contract_20260605/m3_s2_fire_timing_learnability_audit/m3_s2_window_classifier_standardization_contract_probe_20260606.zh.md
docs/learning/reviews/grouped_stopping_contract_20260605/m3_s2_fire_timing_learnability_audit/m3_s2_direct_fire_boundary_probe_20260607.zh.md
```
