# A7 Dispatch Queue

Status: `2026-06-05` A7 is held after AA event-policy margin repair. The
objective contract, policy head, PPO auxiliary credit, config/diagnostics,
focused validation, learned-evidence, closure/index-sync, target audit,
shadow-repair, projection-audit, projection-contract, and projected legal-open
prototype slices have passed; `A7-EVC-N` has also passed as held learned
evidence, `A7-EVC-O` has closed the projection-eligibility audit,
`A7-EVC-P` has selected the legal-open opportunity-credit contract, and
`A7-EVC-Q` has implemented it with focused validation. `A7-EVC-R` has now
recorded bounded learned evidence: legal-open opportunity source counts are
live, but learned timing remains held. `A7-EVC-S` has now completed the
explicit state-completion probe: observability is improved, but deterministic
mode remains `hold` and quality-window advantage remains negative. `A7-EVC-T`
has now verified the value/policy breakpoint: fixed-batch offline credit-head
fitting can flip legal-open positives to positive advantage, so the remaining
fault is online update-path coupling. `A7-EVC-U` has now localized that fault:
PPO does not directly overwrite the credit head, but shared PPO global clipping
and shared actor/features representation coupling starve and destabilize A7
credit learning. `A7-EVC-V` has now implemented the protected online credit
update contract and passed structural gates plus an 8k observation, but A7
remains held because deterministic probing still records `0` releases and
legal-open credit advantage remains negative. `A7-EVC-W` has now closed the
active update-window diagnosis: the active samples disappear because the
episode-level first-event label is evaluated on rollout-local `128` step chunks
and loses shadow-quality positives across PPO segment boundaries. `A7-EVC-X` has
now restored cross-rollout first-event credit state with focused validation.
`A7-EVC-Y` has now completed the post-X learned observation: the restored
training signal is live and stochastic one-shot legality is preserved, but A7
behavior remains held because deterministic probing still records `0` releases,
stochastic releases remain too early, and long stochastic probes show no
effects/damage chain. `A7-EVC-Z` has completed the execution breakpoint
analysis, and `A7-EVC-AA` has implemented the direct signed event-policy margin
repair. AA moves the actor surface in short training, but A7 behavior remains
held because deterministic probing still records `0` releases and stochastic
releases remain early/prewindow.

Parent: [README.md](README.md). Task clusters:
[a7_event_value_advantage_credit_head_task_clusters_20260604.md](a7_event_value_advantage_credit_head_task_clusters_20260604.md).

## Active Queue

| Cluster | Dispatch status | Owner guidance | Write scope | Guard |
| --- | --- | --- | --- | --- |
| Post-AA threshold and sampling-distribution analysis | planned next | main thread; explain why direct signed event-policy margin moves stochastic fire probability but deterministic argmax still stays below the fire threshold, and why early samples dominate before timing separation is learned. | A7 evidence docs and focused diagnostics first; code changes only after a confirmed structural fault. | Do not run another coefficient sweep by default; preserve A3/A5 one-shot legality and keep `experiments_tmp` unstaged. |

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
| `A7-EVC-Q Legal-Open Opportunity Credit Prototype` | pass; spawned R learned evidence | [legal-open opportunity credit prototype](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_prototype_20260604.md): implements `LEGAL_OPEN_QUALITY`, source metrics, nonfinite-probe mirroring, active config knobs, and focused tests. | R has since completed and holds learned behavior; the next bounded work is S. |
| `A7-EVC-R Short Opportunity Learned Evidence` | pass; held outcome | [short opportunity learned evidence](a7_event_value_advantage_credit_head_short_opportunity_learned_evidence_20260604.md): legal-open quality source counts are live in the r1 32k train, deterministic remains `0` releases, stochastic release steps are `3`, `44`, and `10`, and one-shot legality is preserved. | S has since tested explicit state completion; source starvation remains fixed but learned timing is still held. |
| `A7-EVC-S Explicit State Completion Probe` | pass; held outcome | [explicit state completion probe](a7_event_value_advantage_credit_head_explicit_state_completion_probe_20260604.md): `air_combat_c2_roe_v2` exposes legal/window age, readiness, range, and track-age fields; focused tests passed with `105 passed`; the 32k probe preserves one-shot legality but deterministic still records `0` releases. | The next bounded work is T: explain the value/advantage-to-policy coupling failure now that both source starvation and missing explicit window state are insufficient explanations. |
| `A7-EVC-T Value/Policy Coupling Audit` | pass; breakpoint verified | [value/policy coupling audit](a7_event_value_advantage_credit_head_value_policy_coupling_audit_20260604.md): fixed S batch has `1356` `LEGAL_OPEN_QUALITY` positives, initial legal-open advantage `-0.8536`, and credit-head-only offline fitting flips legal-open advantage positive. | The next bounded work is U: isolate the online update path that keeps the learned checkpoint negative despite local credit-head separability. |
| `A7-EVC-U Online Update-Path Isolation` | pass; blocker localized | [online update-path isolation](a7_event_value_advantage_credit_head_online_update_path_isolation_20260604.md): PPO-alone credit-head gradient is `0.0`; PPO+A7 global clipping reduces credit-head effective norm from about `0.4855` to `0.00689`; A7 value and delta-align gradients also conflict in shared actor/features. | The next bounded work is V: specify a decoupled A7 credit update contract before implementation. |
| `A7-EVC-V Online Credit Update Contract` | pass; held outcome | [online credit update contract](a7_event_value_advantage_credit_head_online_credit_update_contract_20260604.md): adds detached-latent credit values, separate credit-head-only value update, protected clip budget, positive-only delta alignment, active config flags, and nonfinite-probe parity. The 8k observation proves the lane is live and improves legal-open credit advantage, but deterministic probing still records `0` releases. | The next bounded work is W: explain update-window/sample availability after the protected update contract is live. |
| `A7-EVC-W Active Update Window Diagnosis` | pass; spawned X contract | [active update-window diagnosis](a7_event_value_advantage_credit_head_active_update_window_diagnosis_20260605.md): full stochastic 512-step episode labels contain `231` `shadow_quality` positives, but training-sized `128` step chunks contain only early negatives and then zero active labels. | The next bounded work is X: carry first-event credit state across PPO rollout boundaries. |
| `A7-EVC-X Cross-Rollout First-Event Credit State` | pass; evaluated by Y | [cross-rollout first-event credit state](a7_event_value_advantage_credit_head_cross_rollout_first_event_state_20260605.md): implements A7-only carried episode history across PPO rollouts, mirrors diagnostics in NonFiniteTrainingProbe, and proves chunked labels recover full-episode shadow-quality positives. | Y shows the repair is live but behavior remains held. |
| `A7-EVC-Y Post-X Learned Observation` | pass; held outcome | [post-X learned observation](a7_event_value_advantage_credit_head_post_x_learned_observation_20260605.md): 32k post-X training shows carried credit is live; deterministic probing records `0` releases; stochastic probing records exactly one authorized release per episode but releases early; long stochastic probes show no effects or damage. | The next bounded work is execution-breakpoint analysis, not more label repair or coefficient tuning. |
| `A7-EVC-Z Execution Breakpoint Analysis` | pass; spawned AA | [execution breakpoint analysis](a7_event_value_advantage_credit_head_execution_breakpoint_analysis_20260605.md): fixed-batch labels, credit-head fit, and event-logit fit isolate the old value-to-policy link as too weak and not signed enough. | AA has since implemented direct signed event-policy margin. |
| `A7-EVC-AA Event-Policy Margin Repair` | pass; held outcome | [event-policy margin repair](a7_event_value_advantage_credit_head_event_policy_margin_repair_20260605.md): direct signed event-logit margin and separate actor/event update lane are complete; safe-bias relaxation is rejected as label starvation. | Startup fire prior is conservative again; A7 still needs low-prewindow-hazard timing learning. |

## Still Blocked

| Cluster | Blocker | Unlock condition |
| --- | --- | --- |
| A7 behavior acceptance | AA still fails acceptance: deterministic stays `hold` even after direct signed margin, and stochastic releases remain early/prewindow. | Explain the post-AA policy-threshold and online sampling-distribution blocker before another training wave. |

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
