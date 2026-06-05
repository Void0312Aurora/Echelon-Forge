# M3-S2 开火时机可学习性审计

状态：`2026-06-06` active audit slice；oracle 证据已通过，
event-window remediation probe 已实现，support-preserving collect repair 已部分接受，
boundary-dedicated 短训方向已改善，log-domain cumulative-hazard repair 已接受，
behavioral deterministic fire timing 仍 held。

语言：

- 英文主文：[README.md](README.md)
- 中文配套：`README.zh.md`

输入：

- 父级模型任务索引：[模型任务](../README.zh.md)
- M3-S1 timing contract：
  [M3-S1 Censored Optimal-Stopping Timing Contract](../m3_s1_censored_optimal_stopping_timing_contract/README.zh.md)
- Stage-1 C2/ROE shaped scenario：
  `scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json`
- M3-S1 维护 probe config：
  `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s1_grouped_stopping_state_completed_world_batch_probe_v1.json`
- M3-S2 event-window 维护 probe config：
  `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json`
- 子项目标准：
  [子项目创建标准](../../../agent/rules/subproject_creation_standard.zh.md)

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
| `P3 Root-Cause Decision` | 决定下一步模型或环境合同。 | P2 evidence exists。 | current status 命名 primary breakpoint 与候选修复。 | active |
| `P4 Remediation Plan` | 决策后才打开下一实现切片。 | P3 accepted。 | Event-window 实现证据记录 direct actor supervision 是否充分。 | held |
| `P5 Closure` | 同步父索引并归档过期记录。 | P4 direction exists 或审计明确 held。 | 父文档指向维护证据。 | active |

## 任务簇

- Task cluster plan：
  [m3_s2_fire_timing_learnability_audit_task_clusters_20260605.zh.md](m3_s2_fire_timing_learnability_audit_task_clusters_20260605.zh.md)

## 输出与证据

- Audit tooling：
  `tools/diagnostics/air_combat_stage0_process_probe.py`
- Aggregate runner：
  `tools/diagnostics/air_combat_fire_timing_learnability_audit.py`
- Focused tests：
  `tests/diagnostics/test_air_combat_process_probe.py`
  `tests/diagnostics/test_air_combat_fire_timing_learnability_audit.py`
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
- Current status：
  [m3_s2_fire_timing_learnability_audit_current_status_20260605.zh.md](m3_s2_fire_timing_learnability_audit_current_status_20260605.zh.md)
- Aggregate artifact：
  `experiments_tmp/air_combat_fire_timing_learnability_audit_20260605.json`

## 验收门

本子项目只有在以下条件满足后才能 accepted：

- oracle diagnostics 可复现四个断点：hold、early high、legal pulse、delayed legal pulse；
- audit 记录 release、effects、damage、health 与 return 是否可区分；
- 文档明确当前证据支持 learnability diagnosis，而不是 learned-policy success claim；
- 下一实现切片打开前，必须先选择修复 action transport、reward/effects observability，
  或在目标信号可识别后再释放 memory/sequence state。

## 残余与下一步

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
- 次级 breakpoint：hybrid fire transport 是 edge-triggered。target acquisition 前高电平会消耗
  pulse 并以 `no_target` 拒绝，之后不再发射。
- 后续方向应按 model-contract change 评估，而不是继续调系数：real-row
  contrastive/margin discriminator、穿过 temporal extractor 与 actor MLP 的 feature-to-logit
  audit、event-head 到 executable-pulse adapter、reward-contract repair，或仅在 stopping
  output 接入 executable event 后再释放 M2 memory/sequence。

## Archive

- Archive index：[archive/README.zh.md](archive/README.zh.md)
