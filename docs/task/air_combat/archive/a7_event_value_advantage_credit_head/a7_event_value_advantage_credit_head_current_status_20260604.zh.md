# A7 当前状态

状态：`2026-06-05` active implementation。A7 已选定 objective contract，并完成
`A7-EVC-C Policy Head Prototype`、`A7-EVC-D PPO Auxiliary Credit` 与
`A7-EVC-E Config And Diagnostics`；`A7-EVC-F Focused Validation Sweep` 也已通过。
`A7-EVC-G Short Learned Evidence` 已完成为有效证据，但 learned-policy outcome
继续 held。`A7-EVC-I Target Construction And Credit Sign Audit` 已将主要结构性故障定位为
缺失 shadow-quality target repair。`A7-EVC-J Shadow Quality Target Repair` 已修复
确认过的 label-censoring bug，并通过 focused tests 与 32k repair probe；但 learned
first-shot timing 仍 held。`A7-EVC-K Legal-State Projection And Coupling Audit`
已关闭 post-repair 诊断，`A7-EVC-L Legal-State Projection Contract` 已选择下一机制；
`A7-EVC-M Projected Legal-Open Credit Prototype` 已完成该机制的 focused
implementation 与验证。Projection 后 learned-policy behavior 已由 `A7-EVC-N Short
Projection Learned Evidence` 评估，并继续 held：deterministic probing 记录 `0`
releases，stochastic probing release steps 为 `2`、`47`、`5`，新修复的 projection
diagnostics 显示 32k run 结束时 `a7/evc_proj_active_count_mean=0.0`。
`A7-EVC-O Projection Eligibility Root-Cause Audit` 已关闭该分裂：N 中 projection
path candidate-starved，因为 logged training rollouts 没有 accepted release，因此没有
`shadow_quality` projection candidates。`A7-EVC-P Legal-Open Opportunity Credit
Contract` 已选择 direct legal-open quality positives 作为下一条 non-starved credit
source。`A7-EVC-Q Legal-Open Opportunity Credit Prototype` 已实现该 source 并通过
focused gates。`A7-EVC-R Short Opportunity Learned Evidence` 已评估 Q 后 learned
behavior：direct legal-open source counts 是 live 的，但 deterministic probing
仍记录 `0` releases，stochastic probing 在 steps `3`、`44`、`10` 过早 release，
quality-window advantage 仍为负。`A7-EVC-S Explicit State Completion Probe` 已用
`air_combat_c2_roe_v2` 测试 pre-M2 observability 假设：policy 现在可以显式看到
legal/window age 与 readiness fields，但 deterministic probing 仍记录 `0`
releases，quality-window advantage 仍为负。`A7-EVC-T Value/Policy Coupling
Audit` 已用 offline fixed-batch fit 验证断点：S final model 的
`LEGAL_OPEN_QUALITY` advantage 起初为负，但同一固定 batch 只更新 credit head
即可拟合出正 legal-open advantage。`A7-EVC-U Online Update-Path Isolation`
已定位 online blocker：PPO-alone 不更新 `hybrid_event_credit_head`，但 PPO+A7
共享同一次 global clip 与同一 actor/feature representation，压低 credit-head
有效更新预算，并造成 value/delta representation conflict。`A7-EVC-V Online
Credit Update Contract` 已实现 protected repair：A7 value credit 通过 detached
latent features、独立 optimizer step 与独立 clip budget 只更新
`hybrid_event_credit_head`，delta-align 也改为 positive-only gated。V 作为结构修复
通过，8k observation 改善 legal-open advantage，但 learned first-shot behavior
仍 held。`A7-EVC-W Active Update Window Diagnosis` 已将剩余失败定位到
rollout-local first-event credit assignment：完整 episode 在 stochastic early
release 后包含 shadow-quality positives，但训练尺寸的 rollout chunks 会在 PPO
segment boundary 丢失这些 positives。`A7-EVC-X Cross-Rollout First-Event
Credit State` 已以 focused validation 修复该 rollout-boundary handoff：带
carried-state 的 `128` step chunks 与完整 512-step episode labels 一致，并恢复
`231` 个 shadow-quality positives。`A7-EVC-Y Post-X Learned Observation` 已运行
bounded 32k post-X train 与 probes。修复后的 signal 进入了 training，stochastic
execution 保持 one-shot legality；但 learned behavior 仍 held：deterministic
probing 仍记录 `0` releases，stochastic releases 仍是 near-immediate/prewindow
samples，长 stochastic episodes 也没有 effects/damage chain。`A7-EVC-Z Execution
Breakpoint Analysis` 已隔离剩余结构故障：fixed-batch labels 存在且平衡，credit
head 可在离线向正确方向移动，并且当 event logits 收到直接有符号监督时，actor 可以分离
prewindow 与 quality。当前 A7 contract 失败的原因是 event-logit delta 对齐到 tiny
detached credit advantage，而不是 calibrated signed margin；credit-head-only
detached-latent learning 也没有训练 actor timing representation。`A7-EVC-AA
Event-Policy Margin Repair` 已实现该 direct signed actor/event margin，增加有边界的
actor/event separate update lane。后续分析否定了 A7 margin config 下放宽 safe fire
bias：它将 quality-window fire probability 推到约 `0.1126` 的同时，也让 prewindow
stochastic firing 几乎必然发生并饿死 legal-open labels。当前 startup fire prior 已恢复
保守。本轮 follow-up 8k safe-bias run 将 event fire probability 保持在约
`0.0031`，保留了 stochastic one-shot legality，并在训练中段短暂恢复
legal-open quality labels；但 deterministic probing 仍记录 `0` releases，最终
active event-credit rows 又回到 `0`。A7 继续 held。

父级：[README.zh.md](README.zh.md)。

## 本检查点

- A3 已作为 accepted C2/ROE evidence packet 归档，并通过 pointer README 保持可达。
- A6 在 root-cause analysis 后继续 held；L tuning 暂停。
- A7 开启，用于实现 counterfactual event-value / advantage credit。
- Objective contract 已选定：
  [a7_event_value_advantage_credit_head_objective_contract_20260604.zh.md](a7_event_value_advantage_credit_head_objective_contract_20260604.zh.md)。
- `A7-EVC-C Policy Head Prototype` 已完成：zero-safe `hybrid_event_credit_head`
  API 已暴露，并由 focused HMoE policy tests 覆盖。
- `A7-EVC-D PPO Auxiliary Credit` 已完成：A7-only coeffs 可采集 first-event
  labels，credit head 接收 value loss，delta alignment 可更新 event logits，且不改变
  runtime masks。
- `A7-EVC-E Config And Diagnostics` 已完成：A7 active config 打开 credit
  head/loss 路径，callback/process-probe diagnostics 暴露 credit values、
  advantage signs 与 cumulative early-fire hazard。
- `A7-EVC-F Focused Validation Sweep` 已完成：JSON、compileall、focused
  HMoE/A7、active-entry、diagnostics、process-probe 与 diff gates 通过。
- `A7-EVC-G Short Learned Evidence` 已完成为 held evidence：有效 r3 training run
  记录到 live `a7/event_credit_loss`，但 deterministic probing 仍为 `0` releases，
  stochastic probing 仍在 steps `14`、`47`、`2` 过早发射。
- `A7-EVC-I Target Construction And Credit Sign Audit` 已完成：stochastic r3
  label reconstruction 只有 `19` 个 active labels 与 `0` 个 positives，而每个
  early-release episode 随后都有超过 `1000` 个 shadow quality states。
- `A7-EVC-J Shadow Quality Target Repair` 已作为 implementation repair 完成：
  stochastic early accepted episodes 不再塌缩成 zero-positive A7 target samples；
  但修复后的 short learned evidence 仍未达到 timing acceptance。
- `A7-EVC-K Legal-State Projection And Coupling Audit` 已完成：repaired positives
  存在，但大多位于 closed-mask `FiredAssess` observations，并且被有意排除出
  delta alignment。
- `A7-EVC-L Legal-State Projection Contract` 已作为 design contract 完成：raw
  shadow rows 变成 projection/opportunity evidence，positive value/delta alignment
  只允许在 projected legal-open observations 上发生。
- `A7-EVC-M Projected Legal-Open Credit Prototype` 已作为 implementation slice
  完成：projected legal-open observations 现在可为 shadow-quality evidence 训练
  positive value/delta alignment，raw closed-mask rows 继续排除出 ordinary
  delta alignment。
- `A7-EVC-N Short Projection Learned Evidence` 已完成为 held evidence：
  projection path 已启用并能在日志中观测，ordinary event-credit 仍 live，但
  projected active rows 为 `0.0`，learned behavior 未达到 timing acceptance。
- `A7-EVC-O Projection Eligibility Root-Cause Audit` 已完成：N TensorBoard 的 logged
  diagnostics 中 accepted releases 为 `0`；deterministic probe reconstruction 为
  `deadline=1080` / `prewindow=800`；stochastic probe reconstruction 则只在 early
  sampled release 后出现 `shadow_quality=3280`。
- `A7-EVC-P Legal-Open Opportunity Credit Contract` 已完成：它选择
  `A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY` 作为 direct legal-open
  quality-window positives，保留 `SHADOW_QUALITY` 作为 projection repair source，
  并将 `DEADLINE` 保持为 fallback/diagnostic source。
- `A7-EVC-Q Legal-Open Opportunity Credit Prototype` 已完成：direct legal-open
  quality positives、source metrics、active config knobs 与 focused tests 已就位。
- `A7-EVC-R Short Opportunity Learned Evidence` 已完成为 held evidence：r1
  32k train 记录最终 `a7/evc_src_legal_open_quality_count_mean=332` 与
  `a7/evc_src_legal_open_quality_positive_count_mean=332`，但 learned timing
  未 accepted。
- `A7-EVC-S Explicit State Completion Probe` 已完成为 held evidence：
  `air_combat_c2_roe_v2` 暴露 legal/window age、launch readiness、quality
  readiness、target range 与 target track age。32k learned probe 提升了
  open-window event-fire probability，但 deterministic mode 仍为 `hold`，且
  quality-window advantage 仍为负。
- `A7-EVC-T Value/Policy Coupling Audit` 已作为 breakpoint evidence 完成：
  固定 deterministic S batch 含 `1356` 个 `LEGAL_OPEN_QUALITY` positives，
  初始 legal-open advantage 为 `-0.8536`，离线拟合只放开 credit head 即可把这些
  rows 翻成正值。
- `A7-EVC-U Online Update-Path Isolation` 已作为 blocker-localization evidence
  完成：PPO-alone credit-head gradient 为 `0.0`，PPO+A7 global clipping 将
  credit-head effective norm 从约 `0.4855` 压到 `0.00689`，且 A7
  value/delta gradients 在 shared actor/features 中冲突。
- `A7-EVC-V Online Credit Update Contract` 已作为 structural repair 完成：
  detached-latent credit value updates、protected credit-head clipping、
  positive-only delta alignment、active config wiring 与 nonfinite-probe parity
  均已实现并测试。8k observation 改善 credit advantage，但仍以 deterministic
  `0` releases 与负 legal-open advantage 结束。
- `A7-EVC-W Active Update Window Diagnosis` 已完成为 root-cause evidence：
  一个 stochastic 512-step final-model episode 含 `231` 个 `shadow_quality`
  positives，但同一轨迹按 `128` step rollout chunks 切开后只有 `5` 个 early
  negative labels，之后 active labels 为 `0`。
- `A7-EVC-X Cross-Rollout First-Event Credit State` 已完成为 focused
  implementation repair：A7-only same-episode carried history 跨 PPO rollouts
  attach，保留 nonfinite-probe parity，并由 chunk-vs-full regression 恢复缺失的
  `231` 个 `shadow_quality` positives。
- `A7-EVC-Y Post-X Learned Observation` 已完成为 held evidence：post-X 32k run
  显示 carried cross-rollout credit 在 training 中是 live 的；deterministic probing
  仍为 `0` releases；stochastic probing 每个 episode 恰好一次 authorized release，
  但 timing 仍过早，且即使在 `2400` step probes 中也没有 effects/damage events。
- `A7-EVC-Z Execution Breakpoint Analysis` 已完成为 structural root-cause
  evidence：固定 hold batch 含 `1880` 个 active labels（`840` 个 prewindow negatives
  与 `1040` 个 legal-open positives），当前策略 fire probability 近似平坦在
  `0.273`；直接 event-logit supervision 加 actor-policy-net updates 可以分离
  quality（mean fire probability `0.749`）与 prewindow（`0.083`），而当前 detached
  credit-advantage delta-align objective 没有提供这种有符号 actor training signal。
- `A7-EVC-AA Event-Policy Margin Repair` 已完成为 structural repair 与 held short
  learned evidence：`FirstEventPolicyMarginLoss` 与 PPO margin/separate-update
  lane 直接用有符号 legal-open positive 与 prewindow negative margins 训练
  event-logit delta；A7 active configs 已使用 margin path。relaxed initial fire bias
  probe 被否定，因为它同时抬高 prewindow hazard 与 quality-window probability；startup
  hybrid fire bias 已恢复为保守设置。
- HMoE hierarchical computation gap 被记录为 architecture risk：A7 不应只依赖 hard-routed
  subexpert behavior；但当前 A7 failure 已经在被删失的 target construction 与 event-credit
  advantage sign 上可见。

## 成熟度矩阵

| Surface | 状态 | 证据 | 边界 |
| --- | --- | --- | --- |
| A7 docs | active | README/task clusters/current status/dispatch/acceptance/objective contract 已存在。 | 仅 documentation 与 dispatch surface。 |
| Objective contract | pass | 已选合同定义 counterfactual target semantics、window balancing、head placement、loss coupling、diagnostics 与 rollback gates。 | 只授权 focused implementation，不释放 broad architecture。 |
| Policy head prototype | pass | `python/rl/policy_algo/policies.py` 暴露 `hybrid_event_credit_head_lr_scale`、`get_hybrid_event_credit()` 与 distribution-side credit values；`tests/policy/test_execution_policy_surface.py` 覆盖 default-off、zero init、optimizer lane、A6 coexistence、load smoke 与 bootstrap zeroing。 | 不声明 PPO auxiliary loss 或 training 已完成。 |
| PPO auxiliary credit | pass | `first_event_hazard.py` 增加带 finite masking 与 window mass caps 的 `compute_first_event_credit_loss()`；`ppo_adaptive_kl.py` 增加 A7 coeffs、A7-only label collection、credit loss coupling、delta alignment 与 finite logs；focused HMoE tests 已通过。 | 不声明 learned-policy。 |
| Config and diagnostics | pass | [config diagnostics evidence](a7_event_value_advantage_credit_head_config_diagnostics_20260604.md) 增加 A7 active entry、callback A7 credit/hazard metrics 与 process-probe A7 summaries。 | 不声明 learned-policy。 |
| Focused validation | pass | [focused validation sweep](a7_event_value_advantage_credit_head_focused_validation_sweep_20260604.md) 记录 JSON、compileall、focused pytest 与 diff checks。 | 不声明 learned-policy。 |
| Short learned evidence | pass；held outcome | [short learned evidence](a7_event_value_advantage_credit_head_short_learned_evidence_20260604.md) 记录 nonfinite-probe 修复后的有效 r3 training/probe evidence。 | A7 不能 accepted：deterministic 仍为 `0` releases，stochastic 过早发射，quality-window advantage 仍为负。 |
| Target construction audit | pass；已由 J 修复 | [target construction and credit-sign audit](a7_event_value_advantage_credit_head_target_construction_credit_sign_audit_20260604.zh.md) 证明 early stochastic accepted release 会从 A7 labels 中删失后续 quality-window positives。 | J 已修复该 target-construction bug；剩余 blocker 是修复后的 projection/coupling，不是再调 coefficient。 |
| Shadow-quality target repair | pass；held outcome | [shadow-quality repair](a7_event_value_advantage_credit_head_shadow_quality_repair_20260604.zh.md) 增加 `A6_FIRST_EVENT_SOURCE_SHADOW_QUALITY`、early accepted release 后的 positive shadow labels、A7 config knob、diagnostics 覆盖，并让 shadow rows 跳过 delta alignment。 | Label censoring 已修复，但 behavior 仍 held：deterministic `0` releases、stochastic 过早 release、quality-window advantage 为负。 |
| Legal-state projection audit | pass；held outcome | [legal-state projection and coupling audit](a7_event_value_advantage_credit_head_legal_state_projection_coupling_audit_20260604.zh.md) 显示 shadow positives 已恢复，但仍是 closed-mask rows 上的 value-only 信号，legal-open quality states 继续为负。 | 这是结构性诊断，不是验收。 |
| Legal-state projection contract | pass；已由 M 实现 | [legal-state projection contract](a7_event_value_advantage_credit_head_legal_state_projection_contract_20260604.zh.md) 选择 projected legal-open positive credit，并禁止 raw closed-mask delta alignment。 | 合同已作为 focused prototype 实现；仍不证明 learned-policy behavior。 |
| Projected legal-open credit prototype | pass；N 后 held | [projected legal-open credit prototype](a7_event_value_advantage_credit_head_projected_legal_open_credit_prototype_20260604.zh.md) 增加 `first_event_projection.py`、projection coeffs、PPO projected-distribution loss、projection metrics、active config knobs 与 focused tests。 | M 只证明机制和 gradient path；N 显示 learned behavior 继续 held。 |
| Short projection learned evidence | pass；held outcome | [short projection learned evidence](a7_event_value_advantage_credit_head_short_projection_learned_evidence_20260604.zh.md) 记录 projection-logger 修复后的 r3 32k train 与 deterministic/stochastic probes。 | Projection 已启用，但 active projected rows 保持 `0.0`；deterministic 仍为 `0` releases，stochastic 仍过早发射。 |
| Projection eligibility root-cause audit | pass；spawned P | [projection eligibility root-cause audit](a7_event_value_advantage_credit_head_projection_eligibility_root_cause_audit_20260604.zh.md) 将 no-candidate starvation 与 unsupported projection rejection 分离。 | M projection 仍是 post-early-release repair path；下一合同必须在采样 failure mode 前提供 legal-open opportunity credit。 |
| Legal-open opportunity credit contract | pass；spawned Q | [legal-open opportunity credit contract](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_contract_20260604.zh.md) 选择 `A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY` 作为真实 legal-open quality-window positive source。 | P 是 docs-only；Q 必须在 training 前证明 source construction、loss routing 与 diagnostics。 |
| Legal-open opportunity credit prototype | pass；已由 R 评估 | [legal-open opportunity credit prototype](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_prototype_20260604.zh.md) 实现 direct legal-open quality positives，并验证 source/loss/diagnostic path。 | Q 不证明 learned behavior；R 已将其评估为 held。 |
| Short opportunity learned evidence | pass；held outcome | [short opportunity learned evidence](a7_event_value_advantage_credit_head_short_opportunity_learned_evidence_20260604.zh.md) 记录 direct `LEGAL_OPEN_QUALITY` credit 后的 r1 32k train/probe。 | Source starvation 已修复，但 deterministic 仍为 `0` releases，stochastic 仍过早 release，quality-window advantage 仍为负。 |
| Explicit state completion | pass；held outcome | [explicit state completion probe](a7_event_value_advantage_credit_head_explicit_state_completion_probe_20260604.zh.md) 增加 `air_combat_c2_roe_v2`、focused tests、32k learned train 与 deterministic/stochastic probes。 | 缺失 window-age observability 不是充分根因：deterministic 仍记录 `0` releases，quality-window advantage 仍为负。 |
| Value/policy coupling audit | pass；breakpoint verified | [value/policy coupling audit](a7_event_value_advantage_credit_head_value_policy_coupling_audit_20260604.zh.md) 增加 offline fixed-batch fit probe，并证明 legal-open positives 可由 credit head 分离。 | 剩余 blocker 是在线联合训练/update coupling，而不是 label starvation、显式状态或 credit-head 容量。 |
| Online update-path isolation | pass；blocker localized | [online update-path isolation](a7_event_value_advantage_credit_head_online_update_path_isolation_20260604.zh.md) 增加 gradient/update probe 与 TensorBoard scalar review。 | 剩余 blocker 是 update contract：shared PPO global clipping 加 shared actor/feature coupling。排除 direct PPO credit-head overwrite。 |
| Online credit update contract | pass；held outcome | [online credit update contract](a7_event_value_advantage_credit_head_online_credit_update_contract_20260604.zh.md) 增加独立 detached-latent credit-head value update、protected clip budget、positive-only delta alignment、active config flags 与 nonfinite-probe parity。 | update contract 已修复，但 behavior 仍 held：8k observation 后 deterministic `0` releases，legal-open advantage 仍为负。 |
| Active update-window diagnosis | pass；spawned X | [active update-window 诊断](a7_event_value_advantage_credit_head_active_update_window_diagnosis_20260605.zh.md) 证明 A7 positives 存在于完整 episode 上，但 stochastic early release 后会被 `128` step rollout-local labels 删失。 | 下一修复是 cross-rollout credit state，而不是 coefficient tuning。 |
| Cross-rollout first-event state | pass；已由 Y 评估 | [cross-rollout first-event credit state](a7_event_value_advantage_credit_head_cross_rollout_first_event_state_20260605.zh.md) 实现 A7-only per-env carried episode history、current-slice label attach、episode advance reset 与 nonfinite-probe diagnostics parity。 | Focused validation 修复 rollout-boundary label handoff；Y 将 learned behavior 评估为仍 held。 |
| Post-X learned observation | pass；held outcome | [post-X learned observation](a7_event_value_advantage_credit_head_post_x_learned_observation_20260605.zh.md) 记录 post-X 32k train、deterministic/stochastic probes 与更长 stochastic probe。 | Deterministic 仍 hold；stochastic single-shot legality clean，但 release timing 过早且没有 effects/damage chain。 |
| Execution breakpoint analysis | pass；held outcome | [execution breakpoint analysis](a7_event_value_advantage_credit_head_execution_breakpoint_analysis_20260605.zh.md) 证明 label presence、credit-head fit 与 actor-capacity fit，同时定位 weak detached delta-align target。 | 下一步应定义 direct signed event-policy contract；A7 仍未 accepted。 |
| Event-policy margin repair | pass；held outcome | [event-policy margin 修复](a7_event_value_advantage_credit_head_event_policy_margin_repair_20260605.zh.md) 实现 direct signed event-logit margin 与独立 actor/event update lane；A7-only safe-bias relaxation 被否定为 label starvation；conservative-bias follow-up 维持低 fire probability，但 deterministic 仍 hold。 | Startup fire prior 已恢复保守；A7 仍需要足以学习 low-prewindow-hazard timing 的 online label/update persistence。 |
| HMoE relation | watch item | issue board 记录 flat subexpert input 与 combat-family collapse。 | 除非正确 credit signs 已学到但 policy coupling 仍以可归因于 hierarchy gap 的方式失败，否则 A7 不修 HMoE。 |

## 立即下一步

Post-X observation、Z breakpoint analysis 与 AA event-policy margin repair 已完成，
A7 继续 held。下一步应分析 AA 后的 threshold 与 online sampling-distribution blocker：
direct signed margin 已经移动 actor surface，但 deterministic argmax 仍没有跨过 fire
threshold，stochastic samples 仍过早。默认不应再做 coefficient sweep。

## 验证快照

- A7-EVC-AA focused gates：
  - `python -m compileall -q train.py python/rl/policy_algo/first_event_hazard.py python/rl/policy_algo/ppo_adaptive_kl.py`：pass。
  - `python -m json.tool <two A7 active configs>`：pass。
  - `pytest tests/training/test_event_timing_training_config_contracts.py -q`：pass，
    `7 passed`。
  - `pytest tests/policy/test_event_head_update_contracts.py -q`：pass，
    `7 passed`。
  - `pytest tests/policy/test_auxiliary_training_updates.py -q`：pass，`18 passed`。
  - `pytest tests/policy/test_execution_policy_surface.py -q`：pass，`32 passed`。
  - `git diff --check -- <A7 event-policy margin write set>`：pass。
- A7-EVC-AA short learned observation：
  - r1 deterministic：`0` accepted releases，quality-window fire probability
    mean `0.00391`，open-window event-logit delta mean `-5.5409`；
  - r2 deterministic：`0` accepted releases，quality-window fire probability
    mean `0.11261`，open-window event-logit delta mean `-2.0643`；
  - r2 stochastic：`4/4` authorized one-shot releases，steps 为 `6`、`51`、
    `11`、`18`，仍为 early/prewindow。
- A7-EVC-AA safe-bias follow-up 8k observation：
  - run：
    `experiments_tmp/a7_event_policy_margin_safe_bias_8k_20260605_r1`；
  - TensorBoard：`a7/event_credit_active_count_mean` 在中段 live，step
    `3072` 为 `718`、step `4096` 为 `762`，但 step `8192` 回到 `0`；
    `a7/evc_src_legal_open_quality_count_mean` 短暂记录 `231` 与 `128`，
    之后回到 `0`；
  - deterministic probe：`2/2` episodes 记录 `0` releases，final missiles
    保持 `4`，quality/prewindow fire probability 约 `0.0031`，且没有 effects
    或 damage；
  - stochastic probe：`3/4` episodes 各记录恰好一次 authorized release，steps
    为 `84`、`407`、`18`；另一个 episode 未 release；没有
    unauthorized/repeat/salvo/budget issues，但仍没有 effects 或 damage。
- `python -m compileall -q python/rl/policy_algo/policies.py`：pass。
- `pytest tests/policy/test_execution_policy_surface.py -q`：pass，`31 passed`。
- `pytest tests/policy/test_event_head_update_contracts.py -q`：pass，`5 passed`。
- `pytest tests/policy/test_auxiliary_training_updates.py -q`：pass，`8 passed`。
- `git diff --check -- python/rl/policy_algo/policies.py tests/policy/test_execution_policy_surface.py`：pass。
- `python -m json.tool <A7 active config>`：pass。
- `python -m compileall -q python/training/diagnostics.py tools/diagnostics/air_combat_weapon_employment_process_probe.py`：pass。
- `pytest tests/training/test_event_timing_training_config_contracts.py -q`：pass，`6 passed`。
- `pytest tests/training/test_diagnostics_callback_contracts.py -q`：pass，`5 passed`。
- `pytest tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q`：pass，`3 passed`。
- `pytest tests/training/test_air_combat_training_entry_contracts.py -q`：pass，`13 passed`。
- `pytest tests/training/test_diagnostics_callback_contracts.py -q`：pass，`13 passed`。
- `pytest tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q`：pass，`9 passed`。
- `pytest tests/policy/test_execution_policy_surface.py tests/policy/test_event_head_update_contracts.py tests/policy/test_auxiliary_training_updates.py -q`：pass，`44 passed`。
- `pytest tests/training/test_event_timing_training_config_contracts.py tests/training/test_diagnostics_callback_contracts.py tests/training/test_air_combat_training_entry_contracts.py -q`：pass，`24 passed`。
- `pytest tests/runtime/air_combat/test_diagnostics_probe_contracts.py tests/training/test_diagnostics_callback_contracts.py -q`：pass，`25 passed`。
- `git diff --check -- <A7 write set>`：pass。
- `python -m compileall -q python/rl/support/nonfinite_probe.py python/training/diagnostics.py tests/policy/test_auxiliary_training_updates.py`：pass。
- `pytest tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_nonfinite_probe_preserves_a7_event_credit_training_path tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_a7_event_credit_only_collects_labels_and_updates_credit_head tests/training/test_diagnostics_callback_contracts.py -q`：pass，`7 passed`。
- A7 r3 TensorBoard scalar check：`a7/event_credit_loss` 在 step `32768` 存在；
  active count `450.0`；advantage mean `-0.978105`。
- A7 r3 deterministic probe：`0` requests、`0` releases、`1880` open-window steps，
  open-window fire probability mean/max 为 `23.1%` / `23.3%`，且 prewindow/quality
  advantage 均为负。
- A7 r3 stochastic probe：`3/3` authorized one-shot releases，steps 为 `14`、
  `47`、`2`，且 `0` unauthorized/violation/repeat/budget issues。
- A7-EVC-I label reconstruction：
  - deterministic r3：`1880` 个 active labels、`1076` 个 positives、`804` 个
    negatives；
  - stochastic r3：`19` 个 active labels、`0` 个 positives、`19` 个 negatives；
  - stochastic early-release episodes 随后仍暴露 `1080`、`1061`、`1081` 个
    post-accepted shadow quality states。
- A7-EVC-J focused repair gates：touched policy/diagnostic files 的 compileall
  通过；`pytest tests/policy/test_first_event_timing_contracts.py -q` 通过，`15 passed`；
  focused HMoE/PPO tests 通过，`14 passed`；focused config/diagnostics/active-entry
  tests 通过，`27 passed`。
- A7-EVC-J 修复后的 label reconstruction：
  - old r3 deterministic：`1880` 个 active labels、`1076` 个 positives、`804`
    个 negatives；
  - old r3 stochastic：`3241` 个 active labels、`3222` 个 positives、`19` 个
    negatives，且 `shadow_quality=3222`；
  - repaired r1 stochastic probe：`3215` 个 active labels、`3209` 个 positives、
    `6` 个 negatives，且 `shadow_quality=3209`。
- A7-EVC-J 32k repair run 在
  `experiments_tmp/a7_shadow_quality_repair_32k_20260604_r1` 下完成 `32768`
  steps；deterministic probe 仍为 `0` releases，open-window fire probability
  mean/max 为 `25.5%` / `27.2%`，quality-window A7 advantage mean 为 `-0.902`；
  stochastic probe 记录 `3/3` authorized one-shot releases，steps 为 `4`、`43`、
  `2`，且 `0` unauthorized/repeat/budget violations。
- A7-EVC-M focused repair gates：`first_event_projection.py`、
  `first_event_hazard.py` 与 `ppo_adaptive_kl.py` 的 compileall 通过；
  `pytest tests/policy/test_first_event_timing_contracts.py -q` 通过，`17 passed`；
  focused projected-loss PPO test 通过，`1 passed`；focused HMoE/PPO group
  通过，`15 passed`；JSON parsing 与 active config/entry tests 通过，
  `19 passed`；docs sync 后 combined focused rerun 通过，`51 passed`。
- A7-EVC-N diagnostic repair gates：`python/rl/policy_algo/ppo_adaptive_kl.py`、
  `python/rl/support/nonfinite_probe.py` 与 `tests/policy/test_auxiliary_training_updates.py`
  的 compileall 通过；focused projection/nonfinite tests 通过，`3 passed`。
- A7-EVC-N 32k projection run 在
  `experiments_tmp/a7_projection_credit_32k_20260604_r3` 下完成；TensorBoard
  step `32768` 记录 `a7/event_credit_loss=0.322098`、
  `a7/event_credit_active_count_mean=450.0`、
  `a7/event_credit_target_positive_frac=0.599887`、
  `a7/event_credit_advantage_mean=-0.962887`、`a7/evc_proj_enabled=1.0`
  与 `a7/evc_proj_active_count_mean=0.0`。
- A7-EVC-N deterministic probe 记录 `0` requests 与 `0` releases，`1880`
  open-window steps，open-window fire probability mean/max 为 `25.2%` / `26.2%`，
  quality-window A7 advantage mean 为 `-0.866`。
- A7-EVC-N stochastic probe 记录 `3/3` authorized one-shot releases，steps 为
  `2`、`47`、`5`，且 `0` unauthorized/repeat/budget violations。
- A7-EVC-O diagnostics：`FirstEventCreditLoss` 现在记录 projection-candidate 与关键
  source counts；normal PPO 与 nonfinite-probe train paths 记录
  `a7/evc_proj_candidate_count_mean`、`a7/evc_src_shadow_count_mean`、
  `a7/evc_src_deadline_count_mean`、`a7/evc_src_early_count_mean` 与
  `a7/evc_src_pre_count_mean`。
- A7-EVC-O evidence review：N TensorBoard logged diagnostic snapshots 中
  `diag/a5_release_executed_count=0` 且 `diag/a5_fire_once_accepted_count=0`；
  全部 `31` 条 train records 中 `a7/evc_proj_active_count_mean=0` 且
  `a7/evc_proj_unsupported_count_mean=0`。
- A7-EVC-O probe reconstruction：deterministic N 产生 `1880` 个 active labels，
  来源为 `deadline=1080` 与 `prewindow=800`；stochastic N 产生 `3291` 个 active
  labels，来源为 `shadow_quality=3280`、`prewindow=8` 与 `early_accepted=3`。
- A7-EVC-P contract：direct legal-open quality opportunity credit 被选择为
  `A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY`；它只在真实 pre-release legal-open
  quality-window rows 上为 positive，且不经过 projection。
- A7-EVC-Q focused gates：compileall 通过；focused Q tests 通过，`5 passed`；
  combined A6/A7/HMoE/active-config pytest 通过，`55 passed`。
- A7-EVC-Q source diagnostics 现在包含
  `a7/evc_src_legal_open_quality_count_mean`、
  `a7/evc_src_legal_open_quality_positive_count_mean` 与
  `a7/evc_src_legal_open_quality_advantage_mean`。
- A7-EVC-R 32k opportunity run 在
  `experiments_tmp/a7_legal_open_opportunity_32k_20260604_r1` 下完成；TensorBoard
  step `32768` 记录 `a7/event_credit_active_count_mean=512.0`、
  `a7/event_credit_target_positive_frac=0.648438`、
  `a7/event_credit_advantage_mean=-0.850262`、
  `a7/evc_src_legal_open_quality_count_mean=332.0` 与
  `a7/evc_src_legal_open_quality_positive_count_mean=332.0`。
- A7-EVC-R deterministic probe 记录 `0` requests 与 `0` releases，`1840`
  open-window steps，open-window fire probability mean/max 为
  `0.281221` / `0.293340`，quality-window A7 advantage mean 为 `-0.792674`。
- A7-EVC-R stochastic probe 记录 `3/3` authorized one-shot releases，steps 为
  `3`、`44`、`10`，且 `0` unauthorized/repeat/budget violations。
- A7-EVC-S focused state-completion gates 通过：
  `pytest tests/runtime/mission/test_mission_obs_taxonomy.py tests/runtime/air_combat/test_air_combat_c2_roe_mission_observation.py tests/policy/test_routing_contracts.py tests/policy/test_execution_policy_surface.py tests/policy/test_auxiliary_training_updates.py tests/policy/test_first_event_timing_contracts.py tests/training/test_event_timing_training_config_contracts.py tests/training/test_air_combat_training_entry_contracts.py -q`
  为 `105 passed`；`git diff --check` 通过。
- A7-EVC-S 32k state-completed run 在
  `experiments_tmp/a7_state_completed_opportunity_32k_20260604_r1` 下完成；最终
  training logs 记录 `a7/evc_src_legal_open_quality_count_mean=330`、
  `a7/evc_src_legal_open_quality_positive_count_mean=330`、
  `a7/event_credit_target_positive_frac=0.645` 与
  `a7/event_credit_advantage_mean=-0.924`。
- A7-EVC-S deterministic probe 在 `4` episodes 中记录 `0` requests 与 `0`
  releases；fire-mask-open steps 为 `[599, 559, 599, 599]`，
  authorized-window event-fire probability mean 为 `0.2634`，quality-window A7
  advantage mean 为 `-0.8534`。
- A7-EVC-S stochastic probe 记录 `8/8` authorized one-shot releases，steps 为
  `[6, 42, 4, 2, 5, 46, 3, 46]`，且 `0` unauthorized/repeat/budget violations；
  releases 仍然过早，不能证明 quality-window timing accepted。
- A7-EVC-T offline fixed-batch fit probe：
  `tools/diagnostics/event_credit_head_probe.py --mode offline_fit` 从 S final model 采集
  `2516` 个 active labels，其中 `1356` 个 `LEGAL_OPEN_QUALITY` positives。
  初始 legal-open advantage 为 `-0.8536`；credit-head-only fitting 将 legal-open
  advantage 翻到 `+0.6417`，正号比例 `1.0`；折算 value-coef 的预算对照仍翻到
  `+0.0083`，正号比例 `1.0`。
- A7-EVC-U online update-path probe：
  `tools/diagnostics/event_credit_head_probe.py --mode online_update` 已完成，并写出
  `experiments_tmp/a7_online_update_path_probe_20260604.json`。Fixed-batch A7
  value 与 delta-align gradients 在 actor/features 中冲突（actor MLP
  `cosine=-0.8954`，features `-0.9097`）。Online PPO-alone credit-head
  gradient 为 `0.0`；PPO+A7 global clipping 将 credit-head effective norm 从约
  `0.4855` 压到 `0.00689`。
- A7-EVC-U 对 S run 的 TensorBoard scalar review：`train/value_loss` 最大到
  `6526.7822`，而 `a7/event_credit_loss` 最大为 `1.0749`；A7 advantage mean
  从约 `-0.0442` 漂移到 `-0.9239`，尽管最终 positive target fraction 为
  `0.6445`。
- A7-EVC-V focused structural gates 已通过：`ppo_adaptive_kl.py`、
  `policies.py`、`nonfinite_probe.py` 与 focused tests 的 compileall 通过；
  direct separate-update 与 nonfinite-probe tests 为 `2 passed`；
  policy/update-strength focused tests 为 `7 passed`；active-config checks 为
  `2 passed`；最终 combined focused rerun 为 `111 passed`；diff whitespace
  check 通过。
- A7-EVC-V 8k protected-update observation 在
  `experiments_tmp/a7_separate_update_8k_v2_20260604` 下完成 `8192` steps；
  separate update lane 记录为 enabled，早期 separate-update grad norm 非零，
  `a7/event_credit_advantage_mean` 改善到约 `-0.0583`。
- A7-EVC-V final probes 仍 hold behavior：fixed-batch legal-open positives
  保持 `1356`，但 legal-open positive advantage 为
  `-0.05257667228579521`，positive sign fraction 为 `0.0`；process probing
  记录 `release_count=0` 与 `fire_once_requested_count=0`。
- A7-EVC-W 对 V 的 TensorBoard review：`a7/event_credit_active_count_mean`
  在 step `1024` 为 `174.0`，`2048` 与 `2560` 为 `64.0`，`3072` 为 `18.5`，
  从 `3584` 到 `8192` 均为 `0.0`；source counts 同步消失。
- A7-EVC-W chunked-label audit：同一条 stochastic final-model 512-step
  episode 在 step `6` accepted release，首个 launch-window open 在 step `282`，
  完整 episode 有 `231` 个 `shadow_quality` positives，但 `128` step rollout
  chunks 只产生 `5` 个 early negative labels，之后 active labels 为 `0`。

## Held Items

- M2 release。
- HMoE redesign 或 soft routing。
- Missile/Pk/fuze/damage authority。
- `2v2`、self-play 与 real doctrine。
