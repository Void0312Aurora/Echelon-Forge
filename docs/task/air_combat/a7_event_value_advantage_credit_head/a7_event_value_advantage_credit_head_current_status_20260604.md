# A7 Current Status

Status: `2026-06-04` active implementation. A7 has selected its objective
contract and completed `A7-EVC-C Policy Head Prototype` plus `A7-EVC-D PPO
Auxiliary Credit` plus `A7-EVC-E Config And Diagnostics`; `A7-EVC-F Focused
Validation Sweep` has also passed. `A7-EVC-G Short Learned Evidence` is now
complete as valid evidence with a held learned-policy outcome. `A7-EVC-I
Target Construction And Credit Sign Audit` has now identified missing
shadow-quality target repair as the primary structural fault. `A7-EVC-J Shadow
Quality Target Repair` has fixed the confirmed label-censoring bug and passed
focused tests plus a 32k repair probe, but learned first-shot timing remains
held. `A7-EVC-K Legal-State Projection And Coupling Audit` has closed the
post-repair diagnosis, and `A7-EVC-L Legal-State Projection Contract` has
selected the next mechanism. `A7-EVC-M Projected Legal-Open Credit Prototype`
has implemented that mechanism with focused validation. Learned-policy behavior
after projection is now evaluated by `A7-EVC-N Short Projection Learned
Evidence` and remains held: deterministic probing records `0` releases,
stochastic probing releases at steps `2`, `47`, and `5`, and the newly repaired
projection diagnostics show `a7/evc_proj_active_count_mean=0.0` at the end of
the 32k run. `A7-EVC-O Projection Eligibility Root-Cause Audit` has now closed
that split: the projection path is candidate-starved in N because logged
training rollouts contain no accepted release and therefore no `shadow_quality`
projection candidates. `A7-EVC-P Legal-Open Opportunity Credit Contract` has now
selected direct legal-open quality positives as the next non-starved credit
source. `A7-EVC-Q Legal-Open Opportunity Credit Prototype` has implemented that
source and passed focused gates. `A7-EVC-R Short Opportunity Learned Evidence`
has now evaluated the learned behavior after Q: direct legal-open source counts
are live, but deterministic probing still records `0` releases, stochastic
probing releases early at steps `3`, `44`, and `10`, and quality-window
advantage remains negative. `A7-EVC-S Explicit State Completion Probe` has now
tested the pre-M2 observability hypothesis with `air_combat_c2_roe_v2`: explicit
legal/window age and readiness fields are visible to the policy, but
deterministic probing still records `0` releases and quality-window advantage
remains negative. `A7-EVC-T Value/Policy Coupling Audit` has now verified the
breakpoint with an offline fixed-batch fit: the S final model starts with
negative `LEGAL_OPEN_QUALITY` advantage, but the same fixed batch can be fit to
positive legal-open advantage by updating the credit head alone. `A7-EVC-U
Online Update-Path Isolation` has now localized the online blocker: PPO-alone
does not update `hybrid_event_credit_head`, but PPO+A7 shares one global clip
and one actor/feature representation, reducing credit-head effective update
budget and creating value/delta representation conflict. `A7-EVC-V Online
Credit Update Contract` has now implemented the protected repair: A7 value
credit updates only `hybrid_event_credit_head` through detached latent
features, a separate optimizer step, and a separate clip budget, while
delta-align is positive-only gated. V passes as a structural repair and the 8k
observation improves legal-open advantage, but learned first-shot behavior
remains held.

Parent: [README.md](README.md).

## Checkpoint

- A3 has been archived as an accepted C2/ROE evidence packet and remains
  reachable through a pointer README.
- A6 remains held after root-cause analysis; L tuning is paused.
- A7 is opened to implement counterfactual event-value / advantage credit.
- The objective contract is now selected:
  [a7_event_value_advantage_credit_head_objective_contract_20260604.md](a7_event_value_advantage_credit_head_objective_contract_20260604.md).
- `A7-EVC-C Policy Head Prototype` is complete: the zero-safe
  `hybrid_event_credit_head` API is exposed and covered by focused HMoE policy
  tests.
- `A7-EVC-D PPO Auxiliary Credit` is complete: A7-only coeffs can collect
  first-event labels, the credit head receives value loss, and delta alignment
  can update event logits without changing runtime masks.
- `A7-EVC-E Config And Diagnostics` is complete: the A7 active config opens the
  credit head/loss path, and callback/process-probe diagnostics expose credit
  values, advantage signs, and cumulative early-fire hazard.
- `A7-EVC-F Focused Validation Sweep` is complete: JSON, compileall, focused
  HMoE/A7, active-entry, diagnostics, process-probe, and diff gates passed.
- `A7-EVC-G Short Learned Evidence` is complete as held evidence: the valid r3
  training run records live `a7/event_credit_loss`, but deterministic probing
  still executes `0` releases and stochastic probing releases too early at
  steps `14`, `47`, and `2`.
- `A7-EVC-I Target Construction And Credit Sign Audit` is complete:
  stochastic r3 label reconstruction yields only `19` active labels and `0`
  positives, while each early-release episode later reaches more than `1000`
  shadow quality states.
- `A7-EVC-J Shadow Quality Target Repair` is complete as implementation repair:
  stochastic early accepted episodes no longer collapse to zero-positive A7
  target samples, but repaired short learned evidence still does not meet timing
  acceptance.
- `A7-EVC-K Legal-State Projection And Coupling Audit` is complete: repaired
  positives exist, but most live on closed-mask `FiredAssess` observations and
  are deliberately excluded from delta alignment.
- `A7-EVC-L Legal-State Projection Contract` is complete as a design contract:
  raw shadow rows become projection/opportunity evidence, while positive
  value/delta alignment is allowed only on projected legal-open observations.
- `A7-EVC-M Projected Legal-Open Credit Prototype` is complete as an
  implementation slice: projected legal-open observations now train positive
  value/delta alignment for shadow-quality evidence while raw closed-mask rows
  remain excluded from ordinary delta alignment.
- `A7-EVC-N Short Projection Learned Evidence` is complete as held evidence:
  the projection path is enabled and visible in logs, ordinary event-credit
  remains live, but projected active rows are `0.0` and learned behavior does
  not improve enough for timing acceptance.
- `A7-EVC-O Projection Eligibility Root-Cause Audit` is complete: N
  TensorBoard has `0` accepted releases in logged diagnostics, deterministic
  probe reconstruction is `deadline=1080` / `prewindow=800`, and stochastic
  probe reconstruction shows `shadow_quality=3280` only after early sampled
  release.
- `A7-EVC-P Legal-Open Opportunity Credit Contract` is complete: it selects
  `A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY` for direct legal-open
  quality-window positives, keeps `SHADOW_QUALITY` as the projection repair
  source, and leaves `DEADLINE` as a fallback/diagnostic source.
- `A7-EVC-Q Legal-Open Opportunity Credit Prototype` is complete: direct
  legal-open quality positives, source metrics, active config knobs, and
  focused tests are in place.
- `A7-EVC-R Short Opportunity Learned Evidence` is complete as held evidence:
  the r1 32k train logs final `a7/evc_src_legal_open_quality_count_mean=332`
  and `a7/evc_src_legal_open_quality_positive_count_mean=332`, but learned
  timing is not accepted.
- `A7-EVC-S Explicit State Completion Probe` is complete as held evidence:
  `air_combat_c2_roe_v2` exposes legal/window age, launch readiness, quality
  readiness, target range, and target track age. The 32k learned probe raises
  open-window event-fire probability, but deterministic mode remains `hold` and
  quality-window advantage remains negative.
- `A7-EVC-T Value/Policy Coupling Audit` is complete as breakpoint evidence:
  the fixed deterministic S batch contains `1356` `LEGAL_OPEN_QUALITY`
  positives, initial legal-open advantage is `-0.8536`, and offline fitting
  flips those rows positive with the credit head alone.
- `A7-EVC-U Online Update-Path Isolation` is complete as blocker-localization
  evidence: PPO-alone credit-head gradient is `0.0`, PPO+A7 global clipping
  reduces credit-head effective norm from about `0.4855` to `0.00689`, and A7
  value/delta gradients conflict in shared actor/features.
- `A7-EVC-V Online Credit Update Contract` is complete as structural repair:
  separate detached-latent credit value updates, protected credit-head clipping,
  positive-only delta alignment, active config wiring, and nonfinite-probe
  parity are implemented and tested. The 8k observation improves credit
  advantage but still ends with deterministic `0` releases and negative
  legal-open advantage.
- The immediate next bounded slice is `A7-EVC-W Active Update Window
  Diagnosis`: explain why protected A7 updates become inactive or insufficient
  after early training before another learned-policy wave.
- The HMoE hierarchical computation gap is recorded as an architecture risk:
  A7 should not rely solely on hard-routed subexpert behavior, but the current
  A7 failure is already visible in the censored target construction and
  event-credit advantage sign.

## Maturity Matrix

| Surface | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| A7 docs | active | README/task clusters/current status/dispatch/acceptance/objective contract exist. | Documentation and dispatch surface only. |
| Objective contract | pass | The selected contract defines counterfactual target semantics, window balancing, head placement, loss coupling, diagnostics, and rollback gates. | It authorizes focused implementation, not broad architecture release. |
| Policy head prototype | pass | `python/rl/policy_algo/policies.py` exposes `hybrid_event_credit_head_lr_scale`, `get_hybrid_event_credit()`, and distribution-side credit values; `tests/hmoe/test_hmoe_policy.py` covers default-off, zero init, optimizer lane, A6 coexistence, load smoke, and bootstrap zeroing. | No PPO auxiliary loss or training claim. |
| PPO auxiliary credit | pass | `first_event_hazard.py` adds `compute_first_event_credit_loss()` with finite masking and window mass caps; `ppo_adaptive_kl.py` adds A7 coeffs, A7-only label collection, credit loss coupling, delta alignment, and finite logs; focused HMoE tests pass. | No learned-policy claim. |
| Config and diagnostics | pass | [config diagnostics evidence](a7_event_value_advantage_credit_head_config_diagnostics_20260604.md) adds the A7 active entry, callback A7 credit/hazard metrics, and process-probe A7 summaries. | No learned-policy claim. |
| Focused validation | pass | [focused validation sweep](a7_event_value_advantage_credit_head_focused_validation_sweep_20260604.md) records JSON, compileall, focused pytest, and diff checks. | No learned-policy claim. |
| Short learned evidence | pass; held outcome | [short learned evidence](a7_event_value_advantage_credit_head_short_learned_evidence_20260604.md) records valid r3 training/probe evidence after nonfinite-probe repair. | A7 is not accepted: deterministic stays at `0` releases, stochastic fires early, and quality-window advantage remains negative. |
| Target construction audit | pass; repaired by J | [target construction and credit-sign audit](a7_event_value_advantage_credit_head_target_construction_credit_sign_audit_20260604.md) proves early stochastic accepted release censors later quality-window positives from A7 labels. | J has repaired this target-construction bug; the remaining blocker is post-repair projection/coupling, not another coefficient-tuning pass. |
| Shadow-quality target repair | pass; held outcome | [shadow-quality repair](a7_event_value_advantage_credit_head_shadow_quality_repair_20260604.md) adds `A6_FIRST_EVENT_SOURCE_SHADOW_QUALITY`, positive shadow labels after early accepted release, an A7 config knob, diagnostics coverage, and delta-align masking for shadow rows. | Label censoring is fixed, but behavior is still held: deterministic `0` releases, early stochastic releases, and negative quality-window advantage. |
| Legal-state projection audit | pass; held outcome | [legal-state projection and coupling audit](a7_event_value_advantage_credit_head_legal_state_projection_coupling_audit_20260604.md) shows shadow positives are restored but remain value-only on closed-mask rows, leaving legal-open quality states negative. | This is a structural diagnosis, not acceptance. |
| Legal-state projection contract | pass; implemented by M | [legal-state projection contract](a7_event_value_advantage_credit_head_legal_state_projection_contract_20260604.md) selects projected legal-open positive credit and forbids raw closed-mask delta alignment. | The contract is now implemented as a focused prototype; it still does not prove learned-policy behavior. |
| Projected legal-open credit prototype | pass; held after N | [projected legal-open credit prototype](a7_event_value_advantage_credit_head_projected_legal_open_credit_prototype_20260604.md) adds `first_event_projection.py`, projection coeffs, PPO projected-distribution loss, projection metrics, active config knobs, and focused tests. | M proves the mechanism and gradient path only; N shows learned behavior still held. |
| Short projection learned evidence | pass; held outcome | [short projection learned evidence](a7_event_value_advantage_credit_head_short_projection_learned_evidence_20260604.md) records the r3 32k train and deterministic/stochastic probes after projection-logger repair. | Projection is enabled but active projected rows stay at `0.0`; deterministic remains `0` releases and stochastic still fires early. |
| Projection eligibility root-cause audit | pass; spawned P | [projection eligibility root-cause audit](a7_event_value_advantage_credit_head_projection_eligibility_root_cause_audit_20260604.md) separates no-candidate starvation from unsupported projection rejection. | M projection remains a post-early-release repair path; next contract must provide legal-open opportunity credit before the failure mode is sampled. |
| Legal-open opportunity credit contract | pass; spawned Q | [legal-open opportunity credit contract](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_contract_20260604.md) selects `A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY` as a real legal-open quality-window positive source. | P is docs-only; Q must prove source construction, loss routing, and diagnostics before training. |
| Legal-open opportunity credit prototype | pass; evaluated by R | [legal-open opportunity credit prototype](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_prototype_20260604.md) implements direct legal-open quality positives and validates the source/loss/diagnostic path. | Q does not prove learned behavior; R now evaluates it as held. |
| Short opportunity learned evidence | pass; held outcome | [short opportunity learned evidence](a7_event_value_advantage_credit_head_short_opportunity_learned_evidence_20260604.md) records the r1 32k train/probe after direct `LEGAL_OPEN_QUALITY` credit. | Source starvation is fixed, but deterministic still records `0` releases, stochastic releases early, and quality-window advantage remains negative. |
| Explicit state completion | pass; held outcome | [explicit state completion probe](a7_event_value_advantage_credit_head_explicit_state_completion_probe_20260604.md) adds `air_combat_c2_roe_v2`, focused tests, a 32k learned train, and deterministic/stochastic probes. | Missing window-age observability is not sufficient root cause: deterministic still records `0` releases and quality-window advantage remains negative. |
| Value/policy coupling audit | pass; breakpoint verified | [value/policy coupling audit](a7_event_value_advantage_credit_head_value_policy_coupling_audit_20260604.md) adds an offline fixed-batch fit probe and shows legal-open positives are separable by the credit head. | The remaining blocker is online joint-training/update coupling, not label starvation, explicit state, or credit-head capacity. |
| Online update-path isolation | pass; blocker localized | [online update-path isolation](a7_event_value_advantage_credit_head_online_update_path_isolation_20260604.md) adds a gradient/update probe and TensorBoard scalar review. | The remaining blocker is the update contract: shared PPO global clipping plus shared actor/feature coupling. Direct PPO credit-head overwrite is excluded. |
| Online credit update contract | pass; held outcome | [online credit update contract](a7_event_value_advantage_credit_head_online_credit_update_contract_20260604.md) adds a separate detached-latent credit-head value update, protected clip budget, positive-only delta alignment, active config flags, and nonfinite-probe parity. | The update contract is repaired, but behavior is still held: deterministic `0` releases and negative legal-open advantage after the 8k observation. |
| HMoE relation | watch item | Issue board documents flat subexpert input and combat-family collapse. | A7 does not repair HMoE unless correct credit signs are learned and coupling still fails in a hierarchy-attributable way. |

## Immediate Next Step

Run `A7-EVC-W Active Update Window Diagnosis`. V proves the protected credit
update lane is live and no longer starved by PPO global clipping, but the
8k observation still does not cross positive legal-open advantage. The next
bounded question is whether the remaining failure is active-window starvation,
curriculum sampling, replay/fixed positive batches, adaptive label scheduling,
or a broader training-loop contract.

## Validation Snapshot

- `python -m compileall -q python/rl/policy_algo/policies.py`: pass.
- `pytest tests/hmoe/test_hmoe_policy.py -q`: pass, `31 passed`.
- `pytest tests/hmoe/test_a6_event_head_update_strength.py -q`: pass,
  `5 passed`.
- `pytest tests/hmoe/test_hmoe_ppo_warmup.py -q`: pass, `8 passed`.
- `git diff --check -- python/rl/policy_algo/policies.py tests/hmoe/test_hmoe_policy.py`: pass.
- `python -m json.tool <A7 active config>`: pass.
- `python -m compileall -q python/training/diagnostics.py tools/diagnostics/air_combat_stage0_process_probe.py`: pass.
- `pytest tests/training/test_a6_event_value_active_config.py -q`: pass,
  `6 passed`.
- `pytest tests/training/test_a6_event_value_diagnostics_callback.py -q`:
  pass, `5 passed`.
- `pytest tests/diagnostics/test_a6_event_value_process_probe.py -q`: pass,
  `3 passed`.
- `pytest tests/training/test_air_combat_active_training_entries.py -q`: pass,
  `13 passed`.
- `pytest tests/training/test_cooperative_diagnostics_callback.py -q`: pass,
  `13 passed`.
- `pytest tests/diagnostics/test_air_combat_process_probe.py -q`: pass,
  `9 passed`.
- `pytest tests/hmoe/test_hmoe_policy.py tests/hmoe/test_a6_event_head_update_strength.py tests/hmoe/test_hmoe_ppo_warmup.py -q`: pass,
  `44 passed`.
- `pytest tests/training/test_a6_event_value_active_config.py tests/training/test_a6_event_value_diagnostics_callback.py tests/training/test_air_combat_active_training_entries.py -q`: pass,
  `24 passed`.
- `pytest tests/diagnostics/test_a6_event_value_process_probe.py tests/diagnostics/test_air_combat_process_probe.py tests/training/test_cooperative_diagnostics_callback.py -q`: pass,
  `25 passed`.
- `git diff --check -- <A7 write set>`: pass.
- `python -m compileall -q python/rl/support/nonfinite_probe.py python/training/diagnostics.py tests/hmoe/test_hmoe_ppo_warmup.py`: pass.
- `pytest tests/hmoe/test_hmoe_ppo_warmup.py::HMoEPPOWarmupTests::test_nonfinite_probe_preserves_a7_event_credit_training_path tests/hmoe/test_hmoe_ppo_warmup.py::HMoEPPOWarmupTests::test_a7_event_credit_only_collects_labels_and_updates_credit_head tests/training/test_a6_event_value_diagnostics_callback.py -q`: pass, `7 passed`.
- A7 r3 TensorBoard scalar check: `a7/event_credit_loss` present at step
  `32768`; active count `450.0`; advantage mean `-0.978105`.
- A7 r3 deterministic probe: `0` requests, `0` releases, `1880`
  open-window steps, open-window fire probability mean/max `23.1%` / `23.3%`,
  and negative prewindow/quality advantage.
- A7 r3 stochastic probe: `3/3` authorized one-shot releases at steps `14`,
  `47`, and `2`, with `0` unauthorized/violation/repeat/budget issues.
- A7-EVC-I label reconstruction:
  - deterministic r3: `1880` active labels, `1076` positives, `804`
    negatives;
  - stochastic r3: `19` active labels, `0` positives, `19` negatives;
  - stochastic early-release episodes still expose `1080`, `1061`, and `1081`
    post-accepted shadow quality states.
- A7-EVC-J focused repair gates: compileall passed for touched policy/diagnostic
  files; `pytest tests/hmoe/test_a6_first_event_hazard.py -q` passed with
  `15 passed`; focused HMoE/PPO tests passed with `14 passed`; focused
  config/diagnostics/active-entry tests passed with `27 passed`.
- A7-EVC-J label reconstruction after repair:
  - old r3 deterministic: `1880` active labels, `1076` positives, `804`
    negatives;
  - old r3 stochastic: `3241` active labels, `3222` positives, `19` negatives,
    with `shadow_quality=3222`;
  - repaired r1 stochastic probe: `3215` active labels, `3209` positives, `6`
    negatives, with `shadow_quality=3209`.
- A7-EVC-J 32k repair run completed `32768` steps under
  `experiments_tmp/a7_shadow_quality_repair_32k_20260604_r1`; deterministic
  probe still records `0` releases with open-window fire probability mean/max
  `25.5%` / `27.2%` and quality-window A7 advantage mean `-0.902`; stochastic
  probe records `3/3` authorized one-shot releases at steps `4`, `43`, and `2`
  with `0` unauthorized/repeat/budget violations.
- A7-EVC-M focused repair gates: compileall passed for
  `first_event_projection.py`, `first_event_hazard.py`, and
  `ppo_adaptive_kl.py`; `pytest tests/hmoe/test_a6_first_event_hazard.py -q`
  passed with `17 passed`; the focused projected-loss PPO test passed with
  `1 passed`; the focused HMoE/PPO group passed with `15 passed`; JSON parsing
  and active config/entry tests passed with `19 passed`; the combined focused
  rerun after docs sync passed with `51 passed`.
- A7-EVC-N diagnostic repair gates: compileall passed for
  `python/rl/policy_algo/ppo_adaptive_kl.py`,
  `python/rl/support/nonfinite_probe.py`, and
  `tests/hmoe/test_hmoe_ppo_warmup.py`; focused projection/nonfinite tests
  passed with `3 passed`.
- A7-EVC-N 32k projection run completed under
  `experiments_tmp/a7_projection_credit_32k_20260604_r3`; TensorBoard at step
  `32768` records `a7/event_credit_loss=0.322098`,
  `a7/event_credit_active_count_mean=450.0`,
  `a7/event_credit_target_positive_frac=0.599887`,
  `a7/event_credit_advantage_mean=-0.962887`,
  `a7/evc_proj_enabled=1.0`, and
  `a7/evc_proj_active_count_mean=0.0`.
- A7-EVC-N deterministic probe records `0` requests and `0` releases, with
  `1880` open-window steps, open-window fire probability mean/max
  `25.2%` / `26.2%`, and quality-window A7 advantage mean `-0.866`.
- A7-EVC-N stochastic probe records `3/3` authorized one-shot releases at
  steps `2`, `47`, and `5`, with `0` unauthorized/repeat/budget violations.
- A7-EVC-O diagnostics: `FirstEventCreditLoss` now records
  projection-candidate and key source counts; normal PPO and nonfinite-probe
  train paths log `a7/evc_proj_candidate_count_mean`,
  `a7/evc_src_shadow_count_mean`, `a7/evc_src_deadline_count_mean`,
  `a7/evc_src_early_count_mean`, and `a7/evc_src_pre_count_mean`.
- A7-EVC-O evidence review: N TensorBoard has `diag/a5_release_executed_count=0`
  and `diag/a5_fire_once_accepted_count=0` in all logged diagnostic snapshots;
  `a7/evc_proj_active_count_mean=0` and
  `a7/evc_proj_unsupported_count_mean=0` across all `31` train records.
- A7-EVC-O probe reconstruction: deterministic N produces `1880` active
  labels from `deadline=1080` and `prewindow=800`; stochastic N produces
  `3291` active labels with `shadow_quality=3280`, `prewindow=8`, and
  `early_accepted=3`.
- A7-EVC-P contract: direct legal-open quality opportunity credit is selected as
  `A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY`; it is positive only on real
  pre-release legal-open quality-window rows and does not route through
  projection.
- A7-EVC-Q focused gates: compileall passed; focused Q tests passed with
  `5 passed`; combined A6/A7/HMoE/active-config pytest passed with `55 passed`.
- A7-EVC-Q source diagnostics now include
  `a7/evc_src_legal_open_quality_count_mean`,
  `a7/evc_src_legal_open_quality_positive_count_mean`, and
  `a7/evc_src_legal_open_quality_advantage_mean`.
- A7-EVC-R 32k opportunity run completed under
  `experiments_tmp/a7_legal_open_opportunity_32k_20260604_r1`; TensorBoard
  step `32768` records `a7/event_credit_active_count_mean=512.0`,
  `a7/event_credit_target_positive_frac=0.648438`,
  `a7/event_credit_advantage_mean=-0.850262`,
  `a7/evc_src_legal_open_quality_count_mean=332.0`, and
  `a7/evc_src_legal_open_quality_positive_count_mean=332.0`.
- A7-EVC-R deterministic probe records `0` requests and `0` releases, `1840`
  open-window steps, open-window fire probability mean/max
  `0.281221` / `0.293340`, and quality-window A7 advantage mean `-0.792674`.
- A7-EVC-R stochastic probe records `3/3` authorized one-shot releases at
  steps `3`, `44`, and `10`, with `0` unauthorized/repeat/budget violations.
- A7-EVC-S focused state-completion gates passed:
  `pytest tests/runtime/mission/test_mission_obs_taxonomy.py tests/runtime/air_combat/test_air_combat_c2_roe_mission_observation.py tests/hmoe/test_hmoe_routing.py tests/hmoe/test_hmoe_policy.py tests/hmoe/test_hmoe_ppo_warmup.py tests/hmoe/test_a6_first_event_hazard.py tests/training/test_a6_event_value_active_config.py tests/training/test_air_combat_active_training_entries.py -q`
  passed with `105 passed`; `git diff --check` passed.
- A7-EVC-S 32k state-completed run completed under
  `experiments_tmp/a7_state_completed_opportunity_32k_20260604_r1`; final
  training logs record `a7/evc_src_legal_open_quality_count_mean=330`,
  `a7/evc_src_legal_open_quality_positive_count_mean=330`,
  `a7/event_credit_target_positive_frac=0.645`, and
  `a7/event_credit_advantage_mean=-0.924`.
- A7-EVC-S deterministic probe records `0` requests and `0` releases across
  `4` episodes; fire-mask-open steps are `[599, 559, 599, 599]`,
  authorized-window event-fire probability mean is `0.2634`, and
  quality-window A7 advantage mean is `-0.8534`.
- A7-EVC-S stochastic probe records `8/8` authorized one-shot releases at
  steps `[6, 42, 4, 2, 5, 46, 3, 46]`, with `0`
  unauthorized/repeat/budget violations. Releases remain early and do not
  demonstrate quality-window timing acceptance.
- A7-EVC-T offline fixed-batch fit probe:
  `tools/diagnostics/a7_credit_head_offline_fit_probe.py` collected `2516`
  active labels with `1356` `LEGAL_OPEN_QUALITY` positives from the S final
  model. Initial legal-open advantage was `-0.8536`; credit-head-only fitting
  flipped legal-open advantage to `+0.6417` with positive sign fraction `1.0`,
  and the value-coef-adjusted budget control still flipped it to `+0.0083`
  with positive sign fraction `1.0`.
- A7-EVC-U online update-path probe:
  `tools/diagnostics/a7_online_update_path_probe.py` completed with
  `experiments_tmp/a7_online_update_path_probe_20260604.json`. Fixed-batch
  A7 value and delta-align gradients conflict in actor/features
  (`cosine=-0.8954` for actor MLP, `-0.9097` for features). Online PPO-alone
  credit-head gradient is `0.0`; PPO+A7 global clipping reduces credit-head
  effective norm from about `0.4855` to `0.00689`.
- A7-EVC-U TensorBoard scalar review of the S run: `train/value_loss` reaches
  max `6526.7822`, while `a7/event_credit_loss` max is `1.0749`; the A7
  advantage mean drifts from about `-0.0442` to `-0.9239` despite final
  positive target fraction `0.6445`.
- A7-EVC-V focused structural gates passed before final rerun: compileall for
  `ppo_adaptive_kl.py`, `policies.py`, `nonfinite_probe.py`, and focused tests;
  direct separate-update and nonfinite-probe tests passed with `2 passed`;
  policy/update-strength focused tests passed with `7 passed`; active-config
  checks passed with `2 passed`.
- A7-EVC-V 8k protected-update observation completed `8192` steps under
  `experiments_tmp/a7_separate_update_8k_v2_20260604`; the separate update lane
  is logged as enabled, early separate-update grad norm is nonzero, and
  `a7/event_credit_advantage_mean` improves to about `-0.0583`.
- A7-EVC-V final probes still hold behavior: fixed-batch legal-open positives
  remain at `1356`, but legal-open positive advantage is
  `-0.05257667228579521` with positive sign fraction `0.0`; process probing
  records `release_count=0` and `fire_once_requested_count=0`.

## Held Items

- M2 release.
- HMoE redesign or soft routing.
- Missile/Pk/fuze/damage authority.
- `2v2`, self-play, and real doctrine.
