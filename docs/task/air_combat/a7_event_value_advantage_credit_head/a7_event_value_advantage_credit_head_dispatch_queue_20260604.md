# A7 Dispatch Queue

Status: `2026-06-04` A7 is held after repaired short learned evidence. The
objective contract, policy head, PPO auxiliary credit, config/diagnostics,
focused validation, learned-evidence, closure/index-sync, target audit,
shadow-repair, projection-audit, and projection-contract slices have passed.
A7 remains held on behavior acceptance until projected legal-open credit is
implemented and tested.

Parent: [README.md](README.md). Task clusters:
[a7_event_value_advantage_credit_head_task_clusters_20260604.md](a7_event_value_advantage_credit_head_task_clusters_20260604.md).

## Active Queue

| Cluster | Dispatch status | Owner guidance | Write scope | Guard |
| --- | --- | --- | --- | --- |
| `A7-EVC-M Projected Legal-Open Credit Prototype` | planned next | implementation worker plus diagnostics review; implement L's projection path before another learned-policy wave. | Projection helper, A7 loss/PPO coupling, focused tests, active config/diagnostics docs. | Do not align raw closed-mask `shadow_quality` rows; do not weaken A3/A5 masks; no blind 32k training before focused gates; no HMoE/M2/doctrine/missile release. |

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
| `A7-EVC-L Legal-State Projection Contract` | pass; implementation not started | [legal-state projection contract](a7_event_value_advantage_credit_head_legal_state_projection_contract_20260604.md): selects projected legal-open positive value/delta alignment from shadow evidence. | Next work is M implementation; L does not itself change behavior. |

## Still Blocked

| Cluster | Blocker | Unlock condition |
| --- | --- | --- |
| A7 behavior acceptance | Repaired shadow credit still does not make legal-open quality states prefer `fire_once`. | `A7-EVC-M` implements and tests projected legal-open credit before another learned-policy wave. |

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
