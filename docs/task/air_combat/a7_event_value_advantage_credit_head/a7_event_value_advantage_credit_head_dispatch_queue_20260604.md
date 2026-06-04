# A7 Dispatch Queue

Status: `2026-06-04` A7 is held after short projection learned evidence. The
objective contract, policy head, PPO auxiliary credit, config/diagnostics,
focused validation, learned-evidence, closure/index-sync, target audit,
shadow-repair, projection-audit, projection-contract, and projected legal-open
prototype slices have passed; `A7-EVC-N` has also passed as held learned
evidence, `A7-EVC-O` has closed the projection-eligibility audit, and
`A7-EVC-P` has selected the legal-open opportunity-credit contract. A7 remains
held until the P contract is implemented and evaluated.

Parent: [README.md](README.md). Task clusters:
[a7_event_value_advantage_credit_head_task_clusters_20260604.md](a7_event_value_advantage_credit_head_task_clusters_20260604.md).

## Active Queue

| Cluster | Dispatch status | Owner guidance | Write scope | Guard |
| --- | --- | --- | --- | --- |
| `A7-EVC-Q Legal-Open Opportunity Credit Prototype` | planned next | implementation worker; implement the P contract with focused source/loss/diagnostic tests before training. | `python/rl/policy_algo/first_event_hazard.py`, `python/rl/policy_algo/ppo_adaptive_kl.py`, `python/rl/support/nonfinite_probe.py`, focused tests, active config/diagnostics docs. | No broad reward tuning; no weakening A3/A5 masks; no raw shadow delta alignment; no HMoE/M2/doctrine/missile release; no learned-policy wave before focused gates. |

## Completed Dispatches

| Cluster | Result | Evidence | Residual |
| --- | --- | --- | --- |
| `A7-EVC-C Policy Head Prototype` | pass | `hybrid_event_credit_head_lr_scale`, `get_hybrid_event_credit()`, distribution-side `fire_event_q_values()` / `fire_event_advantage()`, default-disabled and A6-coexistence tests. | Head is exposed only; PPO loss coupling remains `A7-EVC-D`. |
| `A7-EVC-D PPO Auxiliary Credit` | pass | `compute_first_event_credit_loss()`, A7-only label collection, PPO loss coupling, optional delta alignment, focused gradient/PPO tests. | G later proved the credit path active but held on advantage signs. |
| `A7-EVC-E Config And Diagnostics` | pass | A7 active config, callback credit/early-hazard metrics, process-probe credit values and cumulative pre-window hazard summary; focused config/diagnostics tests pass. | G later used these diagnostics and held on quality-window advantage. |
| `A7-EVC-F Focused Validation Sweep` | pass | JSON, compileall, focused HMoE/config/diagnostics/active/probe pytest groups, and diff checks passed. | G is now complete as held evidence. |
| `A7-EVC-G Short Learned Evidence` | pass; held outcome | [short learned evidence](a7_event_value_advantage_credit_head_short_learned_evidence_20260604.md): r3 has live A7 credit loss, deterministic `0` releases, stochastic releases at `14`, `47`, `2`, and no legality/one-shot violations. | A7 is not accepted; quality-window advantage remains negative. |
| `A7-EVC-H Closure And Index Sync` | pass; held sync | A7, parent air-combat, A6, and HMoE issue docs are synced to the held A7-G conclusion. | Next work is diagnosis, not another blind training run. |
| `A7-EVC-I Target Construction And Credit Sign Audit` | pass; repaired by J | [target construction and credit-sign audit](a7_event_value_advantage_credit_head_target_construction_credit_sign_audit_20260604.md): stochastic r3 labels contain `0` positives despite later shadow-quality states after early release. | J repaired the censoring path; remaining work is projection/coupling diagnosis, not coefficient tuning. |
| `A7-EVC-J Shadow Quality Target Repair` | pass; held outcome | [shadow-quality repair](a7_event_value_advantage_credit_head_shadow_quality_repair_20260604.md): repair restores shadow-quality positives after early accepted release and passes focused tests plus a 32k repair probe. | Label censoring is fixed, but deterministic remains `0` releases, stochastic fires early, and quality-window advantage stays negative. |
| `A7-EVC-K Legal-State Projection And Coupling Audit` | pass; spawned L contract | [legal-state projection and coupling audit](a7_event_value_advantage_credit_head_legal_state_projection_coupling_audit_20260604.md): repaired positives exist but mostly live on closed-mask `FiredAssess` rows and are value-only. | The root residual is projection/coupling, not missing positives or coefficient tuning. |
| `A7-EVC-L Legal-State Projection Contract` | pass; implemented by M | [legal-state projection contract](a7_event_value_advantage_credit_head_legal_state_projection_contract_20260604.md): selects projected legal-open positive value/delta alignment from shadow evidence. | L does not itself change behavior; M now implements it as a focused prototype. |
| `A7-EVC-M Projected Legal-Open Credit Prototype` | pass; held after N | [projected legal-open credit prototype](a7_event_value_advantage_credit_head_projected_legal_open_credit_prototype_20260604.md): implements L through `first_event_projection.py`, PPO projected-distribution loss, projection metrics, active config knobs, and focused tests. | M proves projected legal-open pressure in focused tests; N shows the learned run does not activate projected rows. |
| `A7-EVC-N Short Projection Learned Evidence` | pass; held outcome | [short projection learned evidence](a7_event_value_advantage_credit_head_short_projection_learned_evidence_20260604.md): projection is enabled and logged, ordinary event-credit remains live, deterministic is still `0` releases, stochastic release steps are `2`, `47`, and `5`, and projected active rows stay `0.0`. | The next bounded work is O: explain why shadow-quality evidence does not reach active projected legal-open rows. |
| `A7-EVC-O Projection Eligibility Root-Cause Audit` | pass; spawned P contract | [projection eligibility root-cause audit](a7_event_value_advantage_credit_head_projection_eligibility_root_cause_audit_20260604.md): N training diagnostics have no accepted releases; deterministic probe reconstruction is deadline/prewindow only, while stochastic reconstruction has `3280` shadow-quality positives after early release. | The next bounded work is P: define legal-open opportunity credit that does not depend on sampling early accepted release. |
| `A7-EVC-P Legal-Open Opportunity Credit Contract` | pass; spawned Q prototype | [legal-open opportunity credit contract](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_contract_20260604.md): selects `A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY` for real legal-open quality-window positives. | The next bounded work is Q: implement the source/loss/diagnostic path before another learned-policy wave. |

## Still Blocked

| Cluster | Blocker | Unlock condition |
| --- | --- | --- |
| A7 behavior acceptance | Current projection credit is candidate-starved unless early accepted release is sampled; deterministic remains `0` releases and stochastic fires early. | `A7-EVC-Q` implements the P opportunity-credit contract and then records bounded learned evidence. |

## Dispatch Packet Template

```md
cluster: A7-EVC-*
scope:
write set:
non-goals:
validation:
return packet:
```

## Integration Notes

- Do not create separate conversation sessions for this work.
- `A7-EVC-A/B` are closed by
  [the objective contract](a7_event_value_advantage_credit_head_objective_contract_20260604.md).
- `experiments_tmp` stays out of staging.
- Keep A3/A5 legality authoritative.
- Keep M2 and HMoE redesign held unless a separate release vote or issue task
  is created.
