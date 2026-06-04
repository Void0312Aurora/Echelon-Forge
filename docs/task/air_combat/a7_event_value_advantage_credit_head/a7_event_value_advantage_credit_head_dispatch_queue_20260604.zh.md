# A7 分发队列

状态：`2026-06-04` A7 在 short projection learned evidence 后保持 held。Objective
contract、policy head、PPO auxiliary credit、config/diagnostics、focused
validation、learned-evidence、closure/index-sync、target audit、shadow-repair、
projection-audit、projection-contract 与 projected legal-open prototype slices
已通过；`A7-EVC-N` 也已作为 held learned evidence 通过，`A7-EVC-O` 已关闭
projection-eligibility audit，且 `A7-EVC-P` 已选择 legal-open opportunity-credit
contract。A7 仍在 behavior acceptance 上 held，直到 P 合同被实现并评估。

父级：[README.zh.md](README.zh.md)。任务簇：
[a7_event_value_advantage_credit_head_task_clusters_20260604.zh.md](a7_event_value_advantage_credit_head_task_clusters_20260604.zh.md)。

## Active Queue

| Cluster | Dispatch status | Owner guidance | Write scope | Guard |
| --- | --- | --- | --- | --- |
| `A7-EVC-Q Legal-Open Opportunity Credit Prototype` | planned next | implementation worker；training 前按 P 合同实现 source/loss/diagnostic focused tests。 | `python/rl/policy_algo/first_event_hazard.py`、`python/rl/policy_algo/ppo_adaptive_kl.py`、`python/rl/support/nonfinite_probe.py`、focused tests、active config/diagnostics docs。 | 不做 broad reward tuning；不削弱 A3/A5 masks；不做 raw shadow delta alignment；不释放 HMoE/M2/doctrine/missile authority；focused gates 前不跑 learned-policy wave。 |

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

## Still Blocked

| Cluster | Blocker | Unlock condition |
| --- | --- | --- |
| A7 behavior acceptance | 当前 projection credit 除非采样 early accepted release，否则 candidate-starved；deterministic 仍为 `0` releases，stochastic 仍过早发射。 | `A7-EVC-Q` 实现 P opportunity-credit contract，然后记录有界 learned evidence。 |

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
