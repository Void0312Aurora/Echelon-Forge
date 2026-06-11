# M3-S2 开火时机可学习性审计

状态：`2026-06-08 已归档 / bounded firing gate accepted；timing、robustness、
effects 与 kill-chain behavior held`。

本归档保留 M3-S2 证据包。原 live 路径
`docs/task/model/m3_s2_fire_timing_learnability_audit/` 现在只保留轻量
pointer README。

语言：

- 英文主文：[README.md](README.md)
- 中文配套：`README.zh.md`

输入：

- 父级归档索引：[模型任务归档](../README.zh.md)
- active 模型任务索引：[模型任务](../../README.zh.md)
- M3-S1 timing contract：
  [M3-S1 Censored Optimal-Stopping Timing Contract](../../m3_s1_censored_optimal_stopping_timing_contract/README.zh.md)
- Stage-1 C2/ROE shaped scenario：
  `scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json`
- M3-S1 维护 probe config：
  `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s1_grouped_stopping_state_completed_world_batch_probe_v1.json`
- M3-S2 event-window 维护 probe config：
  `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json`
- 子项目标准：
  [子项目创建标准](../../../../agent/rules/subproject_creation_standard.zh.md)

## 目的

M3-S2 审计当前一次性开火时机问题在 active Stage-1 环境、reward、C2/ROE mask
与 hybrid action transport 下是否真正可学习。它暂停系数调参，转而回答一个更窄的问题：
如果 oracle 给出正确的合法开火脉冲，环境是否暴露了足够区分“何时脉冲”的信号？

本审计把开火视为 edge-triggered masked stopping problem，而不是普通连续控制。
policy 输出连续 transport 信号 `u_t`；只有当 legal mask 打开且 `u_t` 从低到高形成脉冲时，
才出现 executable fire event。若 legal window 前持续高电平，可能先被 `no_target` 拒绝，
随后不再产生新的事件。

## 当前状态

| Area | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| Release reachability | pass | `legal_mask_fire` oracle 在每个审计 episode 都能合法发射一枚导弹。 | 不证明 learned policy 能形成该脉冲。 |
| Release-vs-hold reward | pass | 合法 oracle release 相比 hold-fire 增加约 `450` return。 | 这是发射奖励，不是时机质量。 |
| Legal timing identifiability | partial | delay `0`、`31`、`63` 是平的，但 full delay sweep 找到 damage 与 combat-win spikes。 | oracle surface 中存在目标，但稀疏，并且 reward 排序偏向 late close-range wins。 |
| Reward ordering | fail | 更晚的 combat win 因终止前正向 per-step shaping 累加而高于更早 win。 | 这是 reward-contract 缺陷，不证明 no-fire 是最优。 |
| Post-release effects | pass/partial | full sweep 观察到 `270` 个 effects/damage reports 与 `27` 个 combat wins。 | 早期 bounded probes 漏掉了这个稀疏区域。 |
| Learned-policy event reachability | fail | deterministic learned models 看到 open masks，但 `fire_once` probability 约 `0.3%`，event mode 仍为 `hold`。 | 机制是 labels-to-credit-to-policy training contract，而不是环境可达性。 |
| Direct event-window supervision | held | M3-S2 到达 executable event logits 并产生非零梯度，但 deterministic probe 在 `1080` 个 quality-window steps 下仍记录 `0` releases。 | 这证明路径已接通；不证明行为开火时机已学会。 |
| Cumulative prewindow hazard | fail | prewindow event probability 均值约 `0.0055`，在 `800` 个 prewindow steps 上意味着 `0.988` 的累计 early-sample risk。 | 逐行意义上的“小”开火概率，对 one-shot stopping 是灾难性的。 |
| Support-preserving collection | partial repair | whole-window shield 在 8k run 中保持 `grouped_active_group_count = 4`，并阻止 collection 阶段出现 accepted rollout events。 | 它只修复训练支持；deterministic evaluation 仍记录 `0` releases。 |
| Event boundary transport | fail | support-preserving r2 保住 supported rows，但 `boundary_cross_count = 0`，event logits 仍在约 `-5.4` 到 `-6.3`。 | 剩余失败是 policy boundary/adapter transport，不是缺少 rows。 |
| Structural toy learnability | pass | 抽象 `800 + 1080` one-shot window toy 在 free logits 与 MLP 下都能把 prewindow risk 压到 `0.02` 以下，并在 quality window 跨边界。 | 这排除了纯 grouped loss object；不排除真实 rollout/update integration path。 |
| Real update path | localized | 真实 Stage-1 forced-hold rows 上，复用 optimizer 的 M3-S2 update 会一起压低 prewindow 和 quality logits；boundary-only reset-optimizer probe 能把 quality max logit 抬高约 `0.3136`。 | 断点是 event-mass 与 deterministic-boundary 合同不一致，以及复用 PPO Adam 状态；不是参数路径不可达。 |
| Boundary dedicated short train | partial direction repair / behavior held | 8k run 将 logged `m3s2/q_boundary_logit` 从约 `-5.95` 抬到 `-4.71`；deterministic probe 仍记录 `0` releases；stochastic probe 在第 `623` 步采样到一次授权发射。 | 这是在线方向证据，不是 deterministic timing 验收。 |
| Single-batch window signal | localized | 最新 forced-hold batch 中，raw mission fields、frozen extractor features 与 frozen actor latent 都线性可分；但 active M3-S2 overfit 与 current action path 上的 row-wise BCE 都坍缩为 all-positive/all-high transport。 | 剩余断点是 executable event-logit contract，不是缺少观测信号。 |
| Stopping-head log-domain adapter | partial numerical repair / behavior held | log-domain grouped stopping loss 在 8k run 中将 deterministic M3 stop probability 从约 `0.47` 降到 `0.145`，但 deterministic release 仍为 `0`，stochastic 仍在第 `5` 步提前采样 release。 | 它恢复长 prewindow survival gradient；没有学会 quality-window pulse。 |
| Scale-separated stopping contract | diagnostic accepted / behavior held | 8k run 将 logged prewindow hazard 从 `0.413` 降到 `0.218`，但 prewindow 与 quality logits 同步下移；deterministic release 仍为 `0`，stochastic 仍在第 `7` 步提前 release。 | contract 已接线，但当前 executable stopping/action transport 仍没有学出 prewindow-vs-quality discriminator。 |
| Chain breakpoint localization | root localized | 一条固定真实 forced-hold 轨迹上，label 通过；standardized frozen actor latent 学到 prewindow `0 / 840`、quality `1040 / 1040` boundary；folded head 能产生一次 quality pulse；raw M3 head 优化仍残留 prewindow positives。 | 第一个局部断点是 M3 head optimization conditioning/calibration，不是缺少状态信号或 action adapter 行为。 |
| Head-normalized calibration | negative integration evidence | 8k run 启用 M3 LayerNorm 与显式 prewindow/quality logit margins，将 deterministic M3 stop probability 降到 `0.118269`，但 deterministic release 仍为 `0`；real-update probe 通过把 quality logits 从 `-2.003` 压到 `-2.965` 来降低 loss。 | capacity 存在，但在线 M3-S2 objective 仍把 global hazard suppression 当作更容易的 loss 下降方向。 |
| Window classifier replay | local classifier repair / behavior held | Balanced latent 与 observation replay 让在线 classifier batch 中正/负 logit 分离，但 saved deterministic probe 仍记录 `release_count = 0`，quality-window classifier logit 约 `-8.24`；stochastic probe 在 quality rows 前第 `48` 步早发。 | Replay 修复的是局部 batch imbalance，不是 saved actor/executable trajectory boundary。 |
| Calibrated classifier standardization | negative integration evidence | deterministic latest-balanced standardization 避免随机 replay-batch 坐标刷新，但 8k final 仍记录 `release_count = 0`；fixed-chain final quality classifier logit mean 为 `-9.902827`，而 fresh head 在同一 latent 上可完美拟合。 | 失败仍是 online head optimization/training-distribution contract，不是 standardization randomness。 |
| Classifier standardization contract | root localized / behavior held | 在固定 `model_event_hold` 轨迹上，保存的 buffer 给出 quality logit mean `-9.837499` 与 `0 / 1080` 个 quality boundaries。只在该 fixed batch 上重算 classifier 输入标准化 buffer 后，quality logit mean 变为 `2.195754`，quality boundaries 变为 `1053 / 1080`。 | executable path 使用的是按 replay/support batches 校准的 inference-time normalization contract，而不是 execution-support 轨迹合同。 |
| Classifier execution-support contract | root localized / behavior held | actor-gradient isolation 与 post-update best-restore 让 classifier logs 可信；8k run 仍记录 deterministic `release_count = 0`、saved quality-window classifier logit mean `-6.336187`，但同一 fixed execution latent 上的 fresh standardized head 达到 `1080 / 1080` quality boundaries。 | 剩余断点是 training/replay support 与 deterministic execution-support 错配，而不是缺少状态信号、adapter 接线或 final-step logging。 |
| Direct fire-boundary owner | bounded firing gate accepted / timing and effects held | Active M3-S2 现在直接训练 executable `hybrid_event_head`。`2026-06-08` 从 r3 初始化的 continuation run 在 deterministic probe 中于 step `423` 记录一次 authorized release、零 violation/repeat，并有一次 effects/damage report。A5 武器保险动作帧修复清除了 focused stochastic reject；bounded batch validation 中 deterministic/stochastic 共 `16 / 16` 个 episode 通过，rejected requests、violations、repeat-before-assessment releases 均为 `0`。 | 对该 active scenario/config pair，release gate 已闭合。Timing quality、effects quality 与 kill-chain behavior 仍在本发射 gate 之外 held。 |
| Edge-trigger adapter | hazard | `forced_fire` 从 reset 高电平会产生 `no_target` 拒绝，之后无发射。 | 这是 action transport 语义，不是 C2/ROE 失败。 |

## 范围

范围内：

- 增加能区分 hold、早高电平、合法 oracle pulse、延迟合法 oracle pulse 的 diagnostics。
- 记录 legal fire 是否可达、是否有 reward、effects 是否可观察、合法时机是否可区分。
- 在选择 M2、新 adapter 或 reward/effect contract 前，把失败抽象成可学习性问题。

范围外：

- 再开 reward coefficient sweep。
- 削弱 C2/ROE masks、one-shot gates 或导弹释放合法性。
- 宣称 M2 或 learned policy accepted。
- 把 stochastic one-shot release 当作 deterministic timing success。

## 阶段计划

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | 固定可学习性问题和形式对象。 | M3-S1 P5 held learned fire timing。 | README 定义 masked edge-triggered stopping 与审计断点。 | pass |
| `P1 Diagnostic Tooling` | 增加 oracle modes 与 aggregate audit runner。 | 现有 process probe 已记录 release/effects/reward。 | `hold_fire`、`legal_mask_fire` 与 aggregate verdict 有测试覆盖。 | pass |
| `P2 Oracle Evidence` | 运行有边界 Stage-1 oracle 对照。 | P1 tests pass。 | Audit JSON 记录 reachability、reward、effects、timing spread 与 verdict。 | pass |
| `P3 Root-Cause Decision` | 决定下一步模型或环境合同。 | P2 evidence exists。 | current status 命名 primary breakpoint 与候选修复。 | accepted |
| `P4 Remediation Plan` | 决策后才打开下一实现切片。 | P3 accepted。 | follow-on work 拆出去，不继续把本包保持为 live。 | held |
| `P5 Closure` | 同步父索引并归档过期记录。 | P4 direction exists 或审计明确 held。 | 父文档指向归档证据与 pointer README。 | archived |

## 任务簇

- Task cluster plan：
  [m3_s2_fire_timing_learnability_audit_task_clusters_20260605.zh.md](m3_s2_fire_timing_learnability_audit_task_clusters_20260605.zh.md)

## 输出与证据

- Audit tooling：
  `tools/diagnostics/air_combat_weapon_employment_process_probe.py`
- Aggregate runner：
  `tools/diagnostics/fire_timing_fault_localization_probe.py --mode learnability_audit`
- Focused tests：
  `tests/runtime/air_combat/test_diagnostics_probe_contracts.py`
  `tests/training/test_fire_timing_fault_localization_contracts.py`
- Oracle evidence：
  [m3_s2_fire_timing_learnability_oracle_probe_20260605.zh.md](m3_s2_fire_timing_learnability_oracle_probe_20260605.zh.md)
- Full delay sweep 与 reward-ordering evidence：
  [m3_s2_fire_timing_reward_delay_sweep_20260605.zh.md](m3_s2_fire_timing_reward_delay_sweep_20260605.zh.md)
- Learned-policy reachability evidence：
  [m3_s2_fire_timing_learned_policy_reachability_probe_20260605.zh.md](m3_s2_fire_timing_learned_policy_reachability_probe_20260605.zh.md)
- Event-window supervision evidence：
  [m3_s2_event_window_supervision_probe_20260605.zh.md](m3_s2_event_window_supervision_probe_20260605.zh.md)
- Cumulative hazard 与 support-collapse evidence：
  [m3_s2_cumulative_hazard_support_collapse_20260606.zh.md](m3_s2_cumulative_hazard_support_collapse_20260606.zh.md)
- Support-preserving collection evidence：
  [m3_s2_support_preserving_collect_probe_20260606.zh.md](m3_s2_support_preserving_collect_probe_20260606.zh.md)
- Structural toy evidence：
  [m3_s2_structural_toy_probe_20260606.zh.md](m3_s2_structural_toy_probe_20260606.zh.md)
- Real update path evidence：
  [m3_s2_real_update_path_probe_20260606.zh.md](m3_s2_real_update_path_probe_20260606.zh.md)
- Boundary 与 optimizer contract evidence：
  [m3_s2_boundary_optimizer_contract_probe_20260606.zh.md](m3_s2_boundary_optimizer_contract_probe_20260606.zh.md)
- Boundary dedicated short-train evidence：
  [m3_s2_boundary_dedicated_short_train_20260606.zh.md](m3_s2_boundary_dedicated_short_train_20260606.zh.md)
- Single-batch window-signal evidence：
  [m3_s2_single_batch_window_signal_probe_20260606.zh.md](m3_s2_single_batch_window_signal_probe_20260606.zh.md)
- Stopping-head log-domain 短训 evidence：
  [m3_s2_stopping_head_adapter_log_domain_short_train_20260606.zh.md](m3_s2_stopping_head_adapter_log_domain_short_train_20260606.zh.md)
- 尺度分离 stopping contract 短训 evidence：
  [m3_s2_scale_separated_stopping_contract_short_train_20260606.zh.md](m3_s2_scale_separated_stopping_contract_short_train_20260606.zh.md)
- 链路断点定位 evidence：
  [m3_s2_chain_breakpoint_probe_20260606.zh.md](m3_s2_chain_breakpoint_probe_20260606.zh.md)
- 停止头归一化与校准短训 evidence：
  [m3_s2_head_norm_calibration_short_train_20260606.zh.md](m3_s2_head_norm_calibration_short_train_20260606.zh.md)
- 窗口分类器短训 evidence：
  [m3_s2_window_classifier_short_train_20260606.zh.md](m3_s2_window_classifier_short_train_20260606.zh.md)
- 窗口分类器 replay 短训 evidence：
  [m3_s2_window_classifier_replay_short_train_20260606.zh.md](m3_s2_window_classifier_replay_short_train_20260606.zh.md)
- 窗口分类器校准标准化短训 evidence：
  [m3_s2_window_classifier_calibrated_standardization_short_train_20260606.zh.md](m3_s2_window_classifier_calibrated_standardization_short_train_20260606.zh.md)
- 窗口分类器标准化合同 evidence：
  [m3_s2_window_classifier_standardization_contract_probe_20260606.zh.md](m3_s2_window_classifier_standardization_contract_probe_20260606.zh.md)
- 窗口分类器 execution-support 短训 evidence：
  [m3_s2_window_classifier_execution_support_short_train_20260606.zh.md](m3_s2_window_classifier_execution_support_short_train_20260606.zh.md)
- Direct fire-boundary owner evidence：
  [m3_s2_direct_fire_boundary_probe_20260607.zh.md](m3_s2_direct_fire_boundary_probe_20260607.zh.md)
- Direct fire-boundary continuation evidence：
  [m3_s2_direct_fire_boundary_continuation_20260608.zh.md](m3_s2_direct_fire_boundary_continuation_20260608.zh.md)
- Fire-closure validation：
  [m3_s2_fire_closure_validation_20260608.zh.md](m3_s2_fire_closure_validation_20260608.zh.md)
- Fire-closure batch validation：
  [m3_s2_fire_closure_batch_validation_20260608.zh.md](m3_s2_fire_closure_batch_validation_20260608.zh.md)
- Current status：
  [m3_s2_fire_timing_learnability_audit_current_status_20260605.zh.md](m3_s2_fire_timing_learnability_audit_current_status_20260605.zh.md)
- Aggregate artifact：
  `experiments_tmp/air_combat_fire_timing_learnability_audit_20260605.json`

## 归档验收门

本证据包以窄口径 sealed：

- oracle 与 diagnostic breakpoints 已记录；
- direct fire-boundary ownership 已接入 active M3-S2 training path；
- bounded batch validation 在 active Stage-1 C2/ROE scenario/config pair 上
  deterministic/stochastic 合计 `16 / 16` 个 episode 通过；
- accepted claim 只限于 learned policy 能在该有界 gate 中请求并执行一次 authorized
  release，且没有 rejected requests、violation releases 或
  repeat-before-assessment releases。

Timing quality、cross-config robustness、effects quality、target damage 与
kill-chain behavior 不由本归档接受。

## 残余与下一步

- Direct fire-boundary ownership 已经接入 active training path，并通过有边界的
  firing gate。`2026-06-08` batch validation 检查了 seeds
  `20260608..20260615` 上 `8` 个 deterministic episode 与 `8` 个 stochastic
  episode；全部 `16` 个 episode 都产生 exactly one accepted authorized release，
  rejected requests、violations 与 repeat-before-assessment releases 均为 `0`。
  Timing/effect quality 仍在本 gate 之外 held。
- 当前 reward breakpoint：oracle surface 存在数学最优点，但该最优点是 late close-range win，
  因为正向 per-step shaping 会在 already-winning shots 之间奖励更晚终止。
- 当前 reachability breakpoint：reward surface 不能解释 no-fire，因为 oracle release 与 terminal
  wins 均可达且有奖励。learned-policy probes 已将原因收窄到当前训练合同：episode-level
  first-event labels 历史上会被 rollout-local support 破坏；剩余 A7 bridge 又把 event logits
  训练到 detached、tiny、未校准的 credit advantage，而不是 signed timing target。
- Direct event-window supervision 进一步收窄该问题：executable event logit path 能接收
  window-level gradients，但 prewindow event probability 均值约 `0.0055`，在很长
  one-shot prewindow 中几乎必然导致 early stochastic consumption。一旦发生，runtime 会正确进入
  `FiredAssess`、关闭 `fire_mask`，并移除用于锐化 boundary 的 supported quality-window rows。
- Support-preserving collection 修复了 collection-time support collapse：whole-window shield
  能在 8k run 中保持 active groups，并阻止 rollout releases 消耗 one-shot support。它本身
  不构成行为修复：deterministic probing 仍看到 `1080` 个 quality-window steps、`0` releases，
  且 event boundary 没有 crossing。
- Structural toy probing 显示，当 support 与 quality-window features 干净时，纯 grouped M3-S2
  objective 能学会所需 one-shot window boundary：长 toy 将 prewindow cumulative risk 压到
  `0.02` 以下，并在 quality window 跨过 deterministic boundary。因此剩余失败位于真实集成路径：
  feature-to-logit transport、selected update parameters、PPO overwrite/dilution、sidecar
  distribution 或 executable pulse adapter。
- Real update probing 进一步局部化该集成失败：在真实 forced-hold Stage-1 rows 上，当前
  M3-S2 update 有 quality rows、大梯度和实际参数移动，但会同时压低 prewindow 与 quality
  logits，而不是抬高 quality logits。更容易的 loss 方向是全局 hazard suppression，
  不是尖锐的 prewindow/quality discriminator。
- Boundary-dedicated 短训把这个局部更新方向在线修复了一部分：supported batches 将
  quality-boundary logit 从约 `-5.95` 抬到 `-4.71`。但它仍未跨过 deterministic mode；
  deterministic probing 记录 `0` releases，而 stochastic probing 能在最大约 `0.42%`
  event probability 下采样到一次授权发射。
- Single-batch window-signal probing 显示，当前模型的 frozen features 与 actor latent
  已经包含所需窗口信号。失败在于当前 executable action-delta objective 允许 all-high
  transport 解，并没有训练一个经过校准、带 prewindow negatives 的 stopping boundary。
- stopping-head adapter 加 log-domain cumulative-hazard repair 修复了一个数值/模型合同断点：
  长 prewindow survival loss 不再在概率下溢后丢失梯度。8k 短训中，M3 stop probability
  均值从约 `0.47` 降到 `0.145`。但这对 `800` 步 one-shot prewindow 仍远远过高，
  stochastic probing 仍会在第 `5` 步提前 release，deterministic quality-window crossing
  仍缺失。
- 尺度分离 stopping contract 明确了目标尺度，但在线模型仍让 prewindow 与 quality logits
  几乎同步移动。8k run 中，有窗口样本的 prewindow hazard 从 `0.413` 降到 `0.218`，
  目标为 inferred `0.000651`；与此同时 quality boundary logit 从 `-0.346` 降到
  `-1.273`。deterministic behavior 仍不发，stochastic behavior 仍在第 `7` 步提前采样 release。
- 链路断点定位把剩余断点局部化。在同一条固定真实轨迹上，label support 有效
  （`840` 个 prewindow rows 与 `1040` 个 quality rows），standardized frozen actor latent
  上的线性 head 可以完美分离，folded head 通过 action adapter 能产生一次 quality-window
  edge-trigger pulse。直接优化 raw M3 head 时几乎成功，但仍残留少量 prewindow positives；
  对 one-shot stopping 来说，这几个 positive 足以失败。下一步应修复 head normalization、
  calibration 与在线 auxiliary optimizer contract。
- head-normalized calibration 修复已测试但仍 held。该切片接入 M3 `LayerNorm`、显式 logit
  ceiling/floor losses、logging、diagnostics 与 active config。短训将 deterministic M3 stop
  probability 从上一轮 scale-separated 的 `0.157226` 降到 `0.118269`，但 prewindow 与 quality
  probabilities 仍几乎相同，deterministic release 仍为 `0`；real-update probe 通过把
  quality logits 继续压低来降低 loss。剩余问题是数学目标：global hazard suppression
  仍是比 quality-window boundary 更容易的 loss 下降方向。
- 当前最强断点转为 executable classifier standardization contract。保存的
  `m3_window_classifier_input_mean/std` buffer 会让固定 execution-support 轨迹明显偏心
  （`saved_z_mean_abs_mean = 2.439337`，`saved_z_std_mean = 0.633167`），
  因而 quality boundary 为 `0 / 1080`。只重算该 fixed batch 的 buffer 后，
  quality boundary 立刻升至 `1053 / 1080`，说明 head 内已有可用 timing signal，
  但执行时处在错误的 normalization contract 下。
- 次级 breakpoint：hybrid fire transport 是 edge-triggered。target acquisition 前高电平会消耗
  pulse 并以 `no_target` 拒绝，之后不再发射。
- 后续方向应按 model-contract change 评估，而不是继续调系数：real-row
  contrastive/margin discriminator、穿过 temporal extractor 与 actor MLP 的 feature-to-logit
  audit、event-head 到 executable-pulse adapter、reward-contract repair，或仅在 stopping
  output 接入 executable event 后再释放 M2 memory/sequence。

## Archive

- Archive index：[模型任务归档](../README.zh.md)
- Pointer README：
  [m3_s2_fire_timing_learnability_audit](../../m3_s2_fire_timing_learnability_audit/README.zh.md)
