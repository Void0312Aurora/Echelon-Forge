# A7 分发队列

状态：`2026-06-05` A7 在 AA event-policy margin repair 后保持 held。Objective
contract、policy head、PPO auxiliary credit、config/diagnostics、focused
validation、learned-evidence、closure/index-sync、target audit、shadow-repair、
projection-audit、projection-contract 与 projected legal-open prototype slices
已通过；`A7-EVC-N` 也已作为 held learned evidence 通过，`A7-EVC-O` 已关闭
projection-eligibility audit，`A7-EVC-P` 已选择 legal-open opportunity-credit
contract，且 `A7-EVC-Q` 已通过 focused validation 实现该合同。`A7-EVC-R` 已记录
有界 learned evidence：legal-open opportunity source counts 是 live 的，但 learned
timing 仍 held。`A7-EVC-S` 已完成 explicit state-completion probe：observability
已改善，但 deterministic mode 仍为 `hold`，quality-window advantage 仍为负。
`A7-EVC-T` 已验证 value/policy 断点：fixed-batch offline credit-head fitting
可以把 legal-open positives 翻成正 advantage，因此剩余故障是 online update-path
coupling。`A7-EVC-U` 已定位该故障：PPO 不会直接覆盖 credit head，但 shared PPO
global clipping 与 shared actor/features representation coupling 会饿死并扰动
A7 credit learning。`A7-EVC-V` 已实现 protected online credit update contract，
并通过 structural gates 与 8k observation，但 A7 仍 held，因为 deterministic
probing 仍记录 `0` releases，legal-open credit advantage 仍为负。`A7-EVC-W`
已关闭 active update-window diagnosis：active samples 消失的原因是
episode-level first-event label 在 rollout-local `128` step chunks 上求值，并在
PPO segment boundary 丢失 shadow-quality positives。`A7-EVC-X` 已通过 focused
validation 恢复 cross-rollout first-event credit state。`A7-EVC-Y` 已完成 post-X
learned observation：恢复后的 training signal 是 live 的，stochastic one-shot
legality 也保持；但 A7 behavior 仍 held，因为 deterministic probing 仍记录 `0`
releases，stochastic releases 仍过早，长 stochastic probes 也没有 effects/damage
chain。
`A7-EVC-Z` 已完成 execution breakpoint analysis，`A7-EVC-AA` 已实现 direct
signed event-policy margin repair。AA 在短训中移动了 actor surface，但 A7 behavior
仍 held，因为 deterministic probing 仍记录 `0` releases，stochastic releases 仍
early/prewindow。

父级：[README.zh.md](README.zh.md)。任务簇：
[a7_event_value_advantage_credit_head_task_clusters_20260604.zh.md](a7_event_value_advantage_credit_head_task_clusters_20260604.zh.md)。

## Active Queue

| Cluster | Dispatch status | Owner guidance | Write scope | Guard |
| --- | --- | --- | --- | --- |
| Post-AA threshold and sampling-distribution analysis | planned next | main thread；解释 direct signed event-policy margin 为什么能移动 stochastic fire probability，但 deterministic argmax 仍低于 fire threshold，以及 early samples 为什么会在 timing separation 学成前主导。 | 优先 A7 evidence docs 与 focused diagnostics；只有确认 structural fault 后才改代码。 | 默认不再做 coefficient sweep；保持 A3/A5 one-shot legality，且 `experiments_tmp` 不入 staging。 |

## 已完成分发

| Cluster | Result | Evidence | Residual |
| --- | --- | --- | --- |
| `A7-EVC-C Policy Head Prototype` | pass | `hybrid_event_credit_head_lr_scale`、`get_hybrid_event_credit()`、distribution-side `fire_event_q_values()` / `fire_event_advantage()`，以及 default-disabled 与 A6-coexistence tests。 | Head 仅已暴露；PPO loss coupling 仍属于 `A7-EVC-D`。 |
| `A7-EVC-D PPO Auxiliary Credit` | pass | `compute_first_event_credit_loss()`、A7-only label collection、PPO loss coupling、optional delta alignment 与 focused gradient/PPO tests。 | G 随后证明 credit path 已激活，但 advantage signs 仍 held。 |
| `A7-EVC-E Config And Diagnostics` | pass | A7 active config、callback credit/early-hazard metrics、process-probe credit values 与 cumulative pre-window hazard summary；focused config/diagnostics tests 已通过。 | G 已使用这些 diagnostics，并因 quality-window advantage held。 |
| `A7-EVC-F Focused Validation Sweep` | pass | JSON、compileall、focused HMoE/config/diagnostics/active/probe pytest groups 与 diff checks 通过。 | G 已完成为 held evidence。 |
| `A7-EVC-G Short Learned Evidence` | pass；held outcome | [short learned evidence](a7_event_value_advantage_credit_head_short_learned_evidence_20260604.md)：r3 有 live A7 credit loss，deterministic 为 `0` releases，stochastic release steps 为 `14`、`47`、`2`，且无 legality/one-shot violations。 | A7 不能 accepted；quality-window advantage 仍为负。 |
| `A7-EVC-H Closure And Index Sync` | pass；held sync | A7、parent air-combat、A6 与 HMoE issue docs 已同步到 A7-G held 结论。 | 下一步是 diagnosis，而不是继续盲训。 |
| `A7-EVC-I Target Construction And Credit Sign Audit` | pass；已由 J 修复 | [target construction and credit-sign audit](a7_event_value_advantage_credit_head_target_construction_credit_sign_audit_20260604.zh.md)：stochastic r3 labels 中 positives 为 `0`，但 early release 后存在 shadow-quality states。 | J 已修复该 censoring path；剩余工作是 projection/coupling 诊断，不是 coefficient tuning。 |
| `A7-EVC-J Shadow Quality Target Repair` | pass；held outcome | [shadow-quality repair](a7_event_value_advantage_credit_head_shadow_quality_repair_20260604.zh.md)：repair 恢复 early accepted release 后的 shadow-quality positives，并通过 focused tests 与 32k repair probe。 | Label censoring 已修复，但 deterministic 仍为 `0` releases，stochastic 仍过早发射，quality-window advantage 仍为负。 |
| `A7-EVC-K Legal-State Projection And Coupling Audit` | pass；spawned L contract | [legal-state projection and coupling audit](a7_event_value_advantage_credit_head_legal_state_projection_coupling_audit_20260604.zh.md)：repaired positives 存在，但主要位于 closed-mask `FiredAssess` rows，且是 value-only。 | 根残余是 projection/coupling，不是缺 positives 或 coefficient tuning。 |
| `A7-EVC-L Legal-State Projection Contract` | pass；已由 M 实现 | [legal-state projection contract](a7_event_value_advantage_credit_head_legal_state_projection_contract_20260604.zh.md)：选择从 shadow evidence 构造 projected legal-open positive value/delta alignment。 | L 自身不改变 behavior；M 已将它实现为 focused prototype。 |
| `A7-EVC-M Projected Legal-Open Credit Prototype` | pass；N 后 held | [projected legal-open credit prototype](a7_event_value_advantage_credit_head_projected_legal_open_credit_prototype_20260604.zh.md)：通过 `first_event_projection.py`、PPO projected-distribution loss、projection metrics、active config knobs 与 focused tests 实现 L。 | M 只在 focused tests 中证明 projected legal-open pressure；N 显示 learned run 没有激活 projected rows。 |
| `A7-EVC-N Short Projection Learned Evidence` | pass；held outcome | [short projection learned evidence](a7_event_value_advantage_credit_head_short_projection_learned_evidence_20260604.zh.md)：projection 已启用并记录日志，ordinary event-credit 仍 live，deterministic 仍为 `0` releases，stochastic release steps 为 `2`、`47`、`5`，projected active rows 保持 `0.0`。 | 下一有界工作是 O：解释 shadow-quality evidence 为什么没有进入 active projected legal-open rows。 |
| `A7-EVC-O Projection Eligibility Root-Cause Audit` | pass；spawned P contract | [projection eligibility root-cause audit](a7_event_value_advantage_credit_head_projection_eligibility_root_cause_audit_20260604.zh.md)：N training diagnostics 中没有 accepted releases；deterministic probe reconstruction 只有 deadline/prewindow，而 stochastic reconstruction 在 early release 后有 `3280` 个 shadow-quality positives。 | 下一有界工作是 P：定义不依赖采样 early accepted release 的 legal-open opportunity credit。 |
| `A7-EVC-P Legal-Open Opportunity Credit Contract` | pass；spawned Q prototype | [legal-open opportunity credit contract](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_contract_20260604.zh.md)：选择 `A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY` 作为真实 legal-open quality-window positives。 | 下一有界工作是 Q：在另一轮 learned-policy wave 前实现 source/loss/diagnostic path。 |
| `A7-EVC-Q Legal-Open Opportunity Credit Prototype` | pass；spawned R learned evidence | [legal-open opportunity credit prototype](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_prototype_20260604.zh.md)：实现 `LEGAL_OPEN_QUALITY`、source metrics、nonfinite-probe mirroring、active config knobs 与 focused tests。 | R 已完成并将 learned behavior 评估为 held；下一有界工作是 S。 |
| `A7-EVC-R Short Opportunity Learned Evidence` | pass；held outcome | [short opportunity learned evidence](a7_event_value_advantage_credit_head_short_opportunity_learned_evidence_20260604.zh.md)：r1 32k train 中 legal-open quality source counts 是 live 的，deterministic 仍为 `0` releases，stochastic release steps 为 `3`、`44`、`10`，且 one-shot legality 保持。 | S 已测试 explicit state completion；source starvation 已不再是 active explanation，但 learned timing 仍 held。 |
| `A7-EVC-S Explicit State Completion Probe` | pass；held outcome | [explicit state completion probe](a7_event_value_advantage_credit_head_explicit_state_completion_probe_20260604.zh.md)：`air_combat_c2_roe_v2` 暴露 legal/window age、readiness、range 与 track-age fields；focused tests 为 `105 passed`；32k probe 保持 one-shot legality，但 deterministic 仍记录 `0` releases。 | 下一有界工作是 T：在 source starvation 与缺失显式 window state 都不足以解释失败后，定位 value/advantage-to-policy coupling failure。 |
| `A7-EVC-T Value/Policy Coupling Audit` | pass；breakpoint verified | [value/policy coupling audit](a7_event_value_advantage_credit_head_value_policy_coupling_audit_20260604.zh.md)：固定 S batch 有 `1356` 个 `LEGAL_OPEN_QUALITY` positives，初始 legal-open advantage 为 `-0.8536`，credit-head-only offline fitting 可把 legal-open advantage 翻正。 | 下一有界工作是 U：隔离 online update path 为什么在本地 credit-head 可分的情况下仍让 learned checkpoint 保持负值。 |
| `A7-EVC-U Online Update-Path Isolation` | pass；blocker localized | [online update-path isolation](a7_event_value_advantage_credit_head_online_update_path_isolation_20260604.zh.md)：PPO-alone credit-head gradient 为 `0.0`；PPO+A7 global clipping 将 credit-head effective norm 从约 `0.4855` 压到 `0.00689`；A7 value 与 delta-align gradients 还会在 shared actor/features 中冲突。 | 下一有界工作是 V：implementation 前指定 decoupled A7 credit update contract。 |
| `A7-EVC-V Online Credit Update Contract` | pass；held outcome | [online credit update contract](a7_event_value_advantage_credit_head_online_credit_update_contract_20260604.zh.md)：增加 detached-latent credit values、独立 credit-head-only value update、protected clip budget、positive-only delta alignment、active config flags 与 nonfinite-probe parity。8k observation 证明 lane 是 live 的，并改善 legal-open credit advantage，但 deterministic probing 仍记录 `0` releases。 | 下一有界工作是 W：在 protected update contract 生效后解释 update-window/sample availability。 |
| `A7-EVC-W Active Update Window Diagnosis` | pass；spawned X contract | [active update-window 诊断](a7_event_value_advantage_credit_head_active_update_window_diagnosis_20260605.zh.md)：完整 stochastic 512-step episode labels 含 `231` 个 `shadow_quality` positives，但训练尺寸的 `128` step chunks 只有 early negatives，之后 active labels 为零。 | 下一有界工作是 X：跨 PPO rollout boundary 携带 first-event credit state。 |
| `A7-EVC-X Cross-Rollout First-Event Credit State` | pass；已由 Y 评估 | [cross-rollout first-event credit state](a7_event_value_advantage_credit_head_cross_rollout_first_event_state_20260605.zh.md)：实现 A7-only carried episode history across PPO rollouts，镜像 NonFiniteTrainingProbe diagnostics，并证明 chunked labels 能恢复完整 episode 的 shadow-quality positives。 | Y 表明该修复是 live 的，但 behavior 仍 held。 |
| `A7-EVC-Y Post-X Learned Observation` | pass；held outcome | [post-X learned observation](a7_event_value_advantage_credit_head_post_x_learned_observation_20260605.zh.md)：post-X 32k training 显示 carried credit 是 live 的；deterministic probing 记录 `0` releases；stochastic probing 每个 episode 恰好一次 authorized release 但过早；长 stochastic probes 没有 effects 或 damage。 | 下一有界工作是 execution-breakpoint analysis，而不是更多 label repair 或 coefficient tuning。 |
| `A7-EVC-Z Execution Breakpoint Analysis` | pass；spawned AA | [execution breakpoint analysis](a7_event_value_advantage_credit_head_execution_breakpoint_analysis_20260605.zh.md)：fixed-batch labels、credit-head fit 与 event-logit fit 将旧 value-to-policy link 定位为太弱且缺少有符号 actor target。 | AA 已实现 direct signed event-policy margin。 |
| `A7-EVC-AA Event-Policy Margin Repair` | pass；held outcome | [event-policy margin 修复](a7_event_value_advantage_credit_head_event_policy_margin_repair_20260605.zh.md)：direct signed event-logit margin 与 separate actor/event update lane 已完成；safe-bias relaxation 被否定为 label starvation。 | Startup fire prior 已恢复保守；A7 仍需要低 prewindow hazard 的 timing learning。 |

## Still Blocked

| Cluster | Blocker | Unlock condition |
| --- | --- | --- |
| A7 behavior acceptance | AA 仍未通过 acceptance：direct signed margin 后 deterministic 仍停在 `hold`，stochastic releases 仍 early/prewindow。 | 在另一轮 training wave 前解释 post-AA policy-threshold 与 online sampling-distribution blocker。 |

## Dispatch Packet Template

```md
cluster: A7-EVC-*
scope:
write set:
non-goals:
validation:
return packet:
```

## 集成说明

- 严禁为本工作创建新的会话线程。
- `A7-EVC-A/B` 已由
  [objective contract](a7_event_value_advantage_credit_head_objective_contract_20260604.zh.md)
  关闭。
- `experiments_tmp` 不入 staging。
- 保持 A3/A5 legality 权威。
- 除非另有 release vote 或 issue task，M2 与 HMoE redesign 继续 held。
