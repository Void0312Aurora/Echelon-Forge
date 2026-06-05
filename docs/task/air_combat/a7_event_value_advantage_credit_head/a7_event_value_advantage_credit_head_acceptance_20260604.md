# A7 Acceptance Gate

Status: `2026-06-04` evaluated; `A7-EVC-C/D/E/F/G/H/I/J/K/L/M/N/O/P/Q/R/S/T/U/V`
implementation, validation, learned-evidence, index-sync, target-audit,
shadow-repair, projection-audit, projection-contract, and projected legal-open
prototype/projection-eligibility/opportunity-contract/opportunity-prototype
slices plus explicit state completion, value/policy breakpoint verification,
online update-path isolation, and online credit update repair evaluated. A7
remains held after V because the protected credit-head update lane is live and
improves short-run credit advantage, but legal-open advantage remains negative
and deterministic probing still records `0` releases.

Parent: [README.md](README.md).

## Accepted Scope Target

A7 acceptance is limited to proving that an event-value / advantage-credit
mechanism can teach first-event timing under the existing A3/A5 legal event
surface.

## Gate Matrix

| Gate | Required outcome | Current state |
| --- | --- | --- |
| Objective contract | A7 target gives counterfactual hold/fire credit and names target source. | pass: [objective contract](a7_event_value_advantage_credit_head_objective_contract_20260604.md) |
| Policy head prototype | Head shape, zero init, optimizer lane, default-off behavior, serialization/load, and A6 coexistence are tested. | pass: `tests/hmoe/test_hmoe_policy.py` |
| PPO auxiliary credit | Loss, masks, finite stats, and event-logit coupling are tested. | pass: `tests/hmoe/test_a6_event_head_update_strength.py`, `tests/hmoe/test_hmoe_ppo_warmup.py` |
| Config/diagnostics | Active entries and callback/process-probe metrics expose A7 credit behavior. | pass: [config diagnostics evidence](a7_event_value_advantage_credit_head_config_diagnostics_20260604.md) |
| Legality boundary | A3/A5 masks and state machine remain authoritative. | required |
| HMoE risk handling | HMoE gap is considered in head placement and diagnostics. | partial: A7-C keeps credit at policy-head level and does not redesign HMoE |
| Focused validation | Compile, JSON, focused pytest, and diff gates are clean before training. | pass: [focused validation sweep](a7_event_value_advantage_credit_head_focused_validation_sweep_20260604.md) |
| Learned evidence | Deterministic fires once inside quality window; stochastic early hazard is bounded. | held: [short learned evidence](a7_event_value_advantage_credit_head_short_learned_evidence_20260604.md) and [shadow-quality repair](a7_event_value_advantage_credit_head_shadow_quality_repair_20260604.md) record deterministic `0` releases, early stochastic releases, and negative quality-window advantage. |
| Target construction audit | Early stochastic release does not censor counterfactual quality-window evidence. | pass after repair: [target construction and credit-sign audit](a7_event_value_advantage_credit_head_target_construction_credit_sign_audit_20260604.md) found the zero-positive censoring fault; [shadow-quality repair](a7_event_value_advantage_credit_head_shadow_quality_repair_20260604.md) restores `shadow_quality` positives after early accepted release. |
| Post-repair coupling | Repaired shadow credit changes legal-open quality-state preference. | held: the 32k repair probe still has quality-window A7 advantage mean `-0.902` and deterministic `0` releases. |
| Projection audit | The post-J blocker is separated from missing positives, HMoE redesign, and coefficient-only tuning. | pass: [legal-state projection and coupling audit](a7_event_value_advantage_credit_head_legal_state_projection_coupling_audit_20260604.md) shows most repaired positives are closed-mask value-only shadow rows. |
| Projection contract | Shadow evidence can be mapped to legal-open positive credit without closed-mask delta alignment. | pass; implemented by M: [legal-state projection contract](a7_event_value_advantage_credit_head_legal_state_projection_contract_20260604.md) selects projected legal-open positive value/delta alignment. |
| Projection implementation | Projected legal-open credit is implemented and tested before another learned-policy wave. | pass; held after N: [projected legal-open credit prototype](a7_event_value_advantage_credit_head_projected_legal_open_credit_prototype_20260604.md) implements `first_event_projection.py`, PPO projection loss, metrics, config knobs, and focused tests. |
| Projection learned evidence | Projected credit improves deterministic/stochastic first-shot timing while preserving one-shot legality. | held: [short projection learned evidence](a7_event_value_advantage_credit_head_short_projection_learned_evidence_20260604.md) records projection enabled and one-shot legality preserved, but deterministic remains `0` releases, stochastic releases at steps `2`, `47`, and `5`, and projection active rows stay `0.0`. |
| Projection eligibility audit | Projection active rows are explained before another training wave. | pass: [projection eligibility root-cause audit](a7_event_value_advantage_credit_head_projection_eligibility_root_cause_audit_20260604.md) finds candidate starvation: M projection can activate for `shadow_quality` rows, but N train diagnostics have no accepted releases and therefore no projection candidates. |
| Legal-open opportunity contract | Non-starved legal-open opportunity credit is defined before another implementation/training wave. | pass: [legal-open opportunity credit contract](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_contract_20260604.md) selects `A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY`. |
| Legal-open opportunity implementation | The P contract is implemented and focused tests prove non-starved legal-open positives. | pass: [legal-open opportunity credit prototype](a7_event_value_advantage_credit_head_legal_open_opportunity_credit_prototype_20260604.md) implements source/loss/diagnostic path and passes focused gates. |
| Opportunity learned evidence | Learned behavior after Q is measured before acceptance. | held: [short opportunity learned evidence](a7_event_value_advantage_credit_head_short_opportunity_learned_evidence_20260604.md) shows legal-open source counts are live, but deterministic remains `0` releases, stochastic releases early, and quality-window advantage stays negative. |
| Explicit state completion | Missing window-age/readiness observability is tested before M2 release. | pass; held: [explicit state completion probe](a7_event_value_advantage_credit_head_explicit_state_completion_probe_20260604.md) adds `air_combat_c2_roe_v2`, focused tests, and 32k learned evidence; deterministic remains `0` releases and quality-window advantage stays negative. |
| Value/policy coupling breakpoint | The remaining negative advantage is separated from label starvation, explicit state, and credit-head capacity. | pass; held: [value/policy coupling audit](a7_event_value_advantage_credit_head_value_policy_coupling_audit_20260604.md) shows the fixed S batch has `1356` legal-open positives and can be fit to positive advantage with the credit head alone. |
| Online update-path isolation | The online blocker is separated from direct PPO credit-head overwrite and pure label/state/capacity explanations. | pass; held: [online update-path isolation](a7_event_value_advantage_credit_head_online_update_path_isolation_20260604.md) shows PPO-alone credit-head gradient is `0.0`, while PPO+A7 global clipping reduces credit-head effective norm from about `0.4855` to `0.00689`, and A7 value/delta conflict in shared actor/features. |
| Online credit update contract | A7 value credit is decoupled from shared PPO global clipping and shared actor/features representation drift. | pass; held: [online credit update contract](a7_event_value_advantage_credit_head_online_credit_update_contract_20260604.md) implements separate detached-latent credit-head value updates, protected clipping, positive-only delta alignment, active config flags, and nonfinite-probe parity; behavior remains held after 8k observation. |
| Overclaim refusal | M2, HMoE redesign, missile authority, `2v2`, self-play, and doctrine remain held. | required |

## Failure Conditions

A7 remains held or must be re-scoped if:

- the implementation only changes L weights or generic reward magnitude;
- the advantage head is diagnostic-only and does not affect event logits or
  policy updates;
- repaired shadow credit still fails to move legal-open quality states into
  positive `fire_once` advantage;
- projection remains candidate-starved because active positive credit depends on
  sampling early accepted release;
- legal-open opportunity positives appear outside real legal-open quality-window
  rows;
- non-starved legal-open opportunity positives are live but event-credit
  advantage remains negative and deterministic event mode stays `hold`;
- explicit window-age/readiness state is visible but event-credit advantage
  remains negative and deterministic event mode stays `hold`;
- fixed-batch offline credit-head fitting succeeds, but the online learned
  checkpoint still keeps legal-open advantage negative and deterministic mode
  `hold`;
- online update-path isolation localizes the blocker, but the implementation
  still uses a single shared PPO backward/global clip/optimizer contract for A7
  credit;
- protected separate credit update is live, but active positive update windows
  disappear or legal-open advantage remains negative and deterministic mode
  remains `hold`;
- the implementation aligns raw closed-mask `shadow_quality` rows directly to
  event logits instead of projecting them to a legal-open decision surface;
- deterministic fires near-immediately after authorization/contact again;
- stochastic probing violates one-shot release discipline;
- HMoE gap is used to justify a broad architecture rewrite without A7 evidence.

## Validation Commands

Initial docs gate:

```bash
git diff --check -- docs/task/air_combat docs/task/issues
```

Implementation gates selected by `A7-EVC-B`:

- policy head shape, zero initialization, and constructor serialization tests;
- first-event credit label tests for pre-quality, quality, early accepted, and
  shadow-quality cases;
- PPO auxiliary-loss finite-value and mask-handling tests;
- diagnostics tests for event advantage signs and cumulative pre-window hazard;
- active config parsing and focused compile/JSON gates.

`A7-EVC-C` focused gates:

```bash
python -m compileall -q python/rl/policy_algo/policies.py
pytest tests/hmoe/test_hmoe_policy.py -q
pytest tests/hmoe/test_a6_event_head_update_strength.py -q
git diff --check -- python/rl/policy_algo/policies.py tests/hmoe/test_hmoe_policy.py
```

Observed outcome: compileall passed; HMoE policy tests passed with `31 passed`;
A6 event-head update-strength tests passed with `3 passed`; diff whitespace check
passed.

`A7-EVC-D` focused gates:

```bash
python -m compileall -q python/rl/policy_algo/first_event_hazard.py python/rl/policy_algo/ppo_adaptive_kl.py
pytest tests/hmoe/test_a6_event_head_update_strength.py -q
pytest tests/hmoe/test_hmoe_ppo_warmup.py -q
pytest tests/hmoe/test_hmoe_policy.py -q
```

Observed outcome: compileall passed; event-head/credit gradient tests passed
with `5 passed`; HMoE PPO warmup tests passed with `8 passed`; HMoE policy tests
passed with `31 passed`.

`A7-EVC-E` focused gates:

```bash
python -m json.tool examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json
python -m compileall -q python/training/diagnostics.py tools/diagnostics/air_combat_stage0_process_probe.py
pytest tests/training/test_a6_event_value_active_config.py -q
pytest tests/training/test_a6_event_value_diagnostics_callback.py -q
pytest tests/diagnostics/test_a6_event_value_process_probe.py -q
pytest tests/training/test_air_combat_active_training_entries.py -q
pytest tests/training/test_cooperative_diagnostics_callback.py -q
pytest tests/diagnostics/test_air_combat_process_probe.py -q
```

Observed outcome: JSON and compileall passed; focused config/diagnostics/active
tests passed with `6 passed`, `5 passed`, `3 passed`, `13 passed`, `13 passed`,
and `9 passed`.

`A7-EVC-F` focused validation sweep:

```bash
python -m json.tool <A7 active config>
python -m compileall -q python/rl/policy_algo/policies.py python/rl/policy_algo/first_event_hazard.py python/rl/policy_algo/ppo_adaptive_kl.py python/training/diagnostics.py tools/diagnostics/air_combat_stage0_process_probe.py
pytest tests/hmoe/test_hmoe_policy.py tests/hmoe/test_a6_event_head_update_strength.py tests/hmoe/test_hmoe_ppo_warmup.py -q
pytest tests/training/test_a6_event_value_active_config.py tests/training/test_a6_event_value_diagnostics_callback.py tests/training/test_air_combat_active_training_entries.py -q
pytest tests/diagnostics/test_a6_event_value_process_probe.py tests/diagnostics/test_air_combat_process_probe.py tests/training/test_cooperative_diagnostics_callback.py -q
git diff --check -- <A7 write set>
```

Observed outcome: JSON and compileall passed; pytest groups passed with
`44 passed`, `24 passed`, and `25 passed`; diff check passed.

`A7-EVC-G` short learned evidence:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a7_event_credit_launch_window_32k_20260604_r3 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260671
```

Observed outcome: completed `32768` steps; TensorBoard records
`a7/event_credit_loss` at step `32768`, proving the credit path is active.
Deterministic probe records `0` requests and `0` releases with negative
prewindow/quality advantage. Stochastic probe records `3/3` authorized one-shot
releases at steps `14`, `47`, and `2`, with no unauthorized/violation/repeat or
budget issues. This is valid evidence, but not acceptance.

`A7-EVC-H` closure/index sync outcome: A7 remains held, and the next bounded
dispatch is `A7-EVC-I Target Construction And Credit Sign Audit`.

`A7-EVC-I` target-construction audit outcome: A7 remains held. The failing link
is missing shadow-quality target repair after early stochastic accepted release.
`A7-EVC-J` has since repaired that label-censoring path and passed focused
tests. The repaired 32k learned-policy probe is still held: deterministic
probing records `0` releases, stochastic probing releases early at steps `4`,
`43`, and `2`, and quality-window A7 advantage mean is `-0.902`.

`A7-EVC-K` has since closed the projection/coupling audit, `A7-EVC-L` selected
the legal-state projection contract, and `A7-EVC-M` implemented the projected
legal-open prototype. M focused validation passed:

```bash
python -m compileall -q python/rl/policy_algo/first_event_projection.py python/rl/policy_algo/first_event_hazard.py python/rl/policy_algo/ppo_adaptive_kl.py
pytest tests/hmoe/test_a6_first_event_hazard.py -q
pytest tests/hmoe/test_hmoe_ppo_warmup.py::HMoEPPOWarmupTests::test_a7_shadow_quality_projection_aligns_projected_legal_open_event_logits -q
pytest tests/hmoe/test_a6_event_head_update_strength.py tests/hmoe/test_hmoe_ppo_warmup.py -q
python -m json.tool examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json
pytest tests/training/test_a6_event_value_active_config.py tests/training/test_air_combat_active_training_entries.py -q
```

Observed outcome: compileall and JSON passed; focused test groups passed with
`17 passed`, `1 passed`, `15 passed`, and `19 passed`; the combined focused
rerun after docs sync passed with `51 passed`. `A7-EVC-N` has since completed
as held learned evidence.

`A7-EVC-N` short projection learned evidence:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a7_projection_credit_32k_20260604_r3 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260691
```

Observed outcome: completed `32768` steps. TensorBoard records ordinary
event-credit activity at step `32768` with
`a7/event_credit_loss=0.322098`,
`a7/event_credit_active_count_mean=450.0`, and
`a7/event_credit_advantage_mean=-0.962887`; projection is enabled with
`a7/evc_proj_enabled=1.0`, but `a7/evc_proj_active_count_mean=0.0`.
Deterministic probing records `0` requests and `0` releases with
quality-window advantage `-0.866`. Stochastic probing records `3/3`
authorized one-shot releases at steps `2`, `47`, and `5`, with zero
unauthorized/repeat/budget violations. This preserves one-shot legality but
does not satisfy behavior acceptance. This triggered
`A7-EVC-O Projection Eligibility Root-Cause Audit`.

`A7-EVC-O` projection eligibility root-cause audit:

```bash
python -m compileall -q python/rl/policy_algo/first_event_hazard.py python/rl/policy_algo/ppo_adaptive_kl.py python/rl/support/nonfinite_probe.py tests/hmoe/test_hmoe_ppo_warmup.py
pytest tests/hmoe/test_hmoe_ppo_warmup.py::HMoEPPOWarmupTests::test_nonfinite_probe_records_a7_projection_credit_stats tests/hmoe/test_hmoe_ppo_warmup.py::HMoEPPOWarmupTests::test_a7_shadow_quality_projection_aligns_projected_legal_open_event_logits -q
```

Observed outcome: compileall passed; focused projection/nonfinite tests passed
with `2 passed`; post-sync combined A6/A7/HMoE/active-config pytest passed with
`52 passed`, and docs/code diff check passed. The audit separates candidate
starvation from unsupported projection rejection: N train diagnostics logged no
accepted releases, while stochastic probe reconstruction produces `3280`
`shadow_quality` positives only after early sampled release. The next bounded
dispatch is `A7-EVC-P Legal-Open Opportunity Credit Contract`.

`A7-EVC-P` legal-open opportunity credit contract:

```bash
git diff --check -- docs/task/air_combat
```

Observed outcome: the contract selects `A6_FIRST_EVENT_SOURCE_LEGAL_OPEN_QUALITY`
for direct legal-open quality positives, keeps `SHADOW_QUALITY` as projection
repair, and leaves `DEADLINE` as fallback/diagnostic source. The next bounded
dispatch is `A7-EVC-Q Legal-Open Opportunity Credit Prototype`.

`A7-EVC-Q` legal-open opportunity credit prototype:

```bash
python -m compileall -q python/rl/policy_algo/first_event_hazard.py python/rl/policy_algo/ppo_adaptive_kl.py python/rl/support/nonfinite_probe.py tests/hmoe/test_a6_first_event_hazard.py tests/hmoe/test_hmoe_ppo_warmup.py tests/training/test_a6_event_value_active_config.py tests/training/test_air_combat_active_training_entries.py
pytest tests/hmoe/test_a6_first_event_hazard.py tests/hmoe/test_a6_event_head_update_strength.py tests/hmoe/test_hmoe_ppo_warmup.py tests/training/test_a6_event_value_active_config.py tests/training/test_air_combat_active_training_entries.py -q
```

Observed outcome: compileall passed; combined A6/A7/HMoE/active-config pytest
passed with `55 passed`. Q proves the implementation surface only. The next
bounded dispatch was `A7-EVC-R Short Opportunity Learned Evidence`.

`A7-EVC-R` short opportunity learned evidence:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a7_legal_open_opportunity_32k_20260604_r1 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260701
```

Observed outcome: completed `32768` steps. TensorBoard records live direct
legal-open source activity at step `32768` with
`a7/event_credit_active_count_mean=512.0`,
`a7/event_credit_target_positive_frac=0.648438`,
`a7/event_credit_advantage_mean=-0.850262`,
`a7/evc_src_legal_open_quality_count_mean=332.0`, and
`a7/evc_src_legal_open_quality_positive_count_mean=332.0`. Deterministic
probing records `0` requests and `0` releases with open-window fire probability
mean/max `0.281221` / `0.293340` and quality-window advantage `-0.792674`.
Stochastic probing records `3/3` authorized one-shot releases at steps `3`,
`44`, and `10`, with zero unauthorized/repeat/budget violations. R proves
source starvation is fixed, but A7 remains held because timing and advantage
sign acceptance are still not met.

`A7-EVC-S` explicit state completion probe:

```bash
pytest tests/runtime/mission/test_mission_obs_taxonomy.py \
  tests/runtime/air_combat/test_air_combat_c2_roe_mission_observation.py \
  tests/hmoe/test_hmoe_routing.py \
  tests/hmoe/test_hmoe_policy.py \
  tests/hmoe/test_hmoe_ppo_warmup.py \
  tests/hmoe/test_a6_first_event_hazard.py \
  tests/training/test_a6_event_value_active_config.py \
  tests/training/test_air_combat_active_training_entries.py -q
```

Observed outcome: focused tests passed with `105 passed`; `git diff --check`
passed. The 32k state-completed train completed under
`experiments_tmp/a7_state_completed_opportunity_32k_20260604_r1` with final
`a7/evc_src_legal_open_quality_count_mean=330`,
`a7/evc_src_legal_open_quality_positive_count_mean=330`,
`a7/event_credit_target_positive_frac=0.645`, and
`a7/event_credit_advantage_mean=-0.924`. Deterministic probing records `0`
requests and `0` releases across `4` episodes with quality-window A7 advantage
mean `-0.8534`. Stochastic probing records `8/8` authorized one-shot releases
at steps `[6, 42, 4, 2, 5, 46, 3, 46]`, with zero
unauthorized/repeat/budget violations. S improves observability and preserves
one-shot legality, but it does not satisfy behavior acceptance.

`A7-EVC-T` value/policy coupling audit:

```bash
python tools/diagnostics/a7_credit_head_offline_fit_probe.py \
  --episodes 4 \
  --max_steps 640 \
  --fit_steps 1200 \
  --fit_batch_size 512 \
  --eval_batch_size 512 \
  --scopes credit_head,credit_head_actor_mlp \
  --json_out experiments_tmp/a7_credit_head_offline_fit_probe_20260604.json
```

Observed outcome: fixed S batch has `2516` active labels with `1356`
`LEGAL_OPEN_QUALITY` positives; initial legal-open advantage is `-0.8536`;
credit-head-only offline fitting flips legal-open advantage to `+0.6417` with
positive sign fraction `1.0`. A conservative value-coef-adjusted budget control
still flips legal-open advantage to `+0.0083` with positive sign fraction
`1.0`. This is breakpoint evidence, not behavior acceptance.

`A7-EVC-U` online update-path isolation:

```bash
python -m compileall -q tools/diagnostics/a7_online_update_path_probe.py

python tools/diagnostics/a7_online_update_path_probe.py \
  --episodes 4 \
  --max_steps 640 \
  --online_episodes 4 \
  --online_max_steps 640 \
  --batch_size 512 \
  --eval_batch_size 512 \
  --update_steps 8 \
  --device auto \
  --json_out experiments_tmp/a7_online_update_path_probe_20260604.json
```

Observed outcome: compileall passed. Fixed-batch A7 value and delta-align
gradients conflict in actor/features (`cosine=-0.8954` for actor MLP and
`-0.9097` for features). Online PPO-alone credit-head gradient is `0.0`;
PPO+A7 global clipping reduces credit-head effective norm from about `0.4855`
to `0.00689`. S TensorBoard review shows `train/value_loss` max `6526.7822`
versus `a7/event_credit_loss` max `1.0749`. This is blocker-localization
evidence, not behavior acceptance.

`A7-EVC-V` online credit update contract:

```bash
python -m compileall -q python/rl/policy_algo/ppo_adaptive_kl.py python/rl/policy_algo/policies.py python/rl/support/nonfinite_probe.py tests/hmoe/test_hmoe_ppo_warmup.py
pytest tests/hmoe/test_hmoe_ppo_warmup.py::HMoEPPOWarmupTests::test_nonfinite_probe_preserves_a7_event_credit_training_path tests/hmoe/test_hmoe_ppo_warmup.py::HMoEPPOWarmupTests::test_a7_separate_credit_update_only_writes_credit_head -q
pytest tests/hmoe/test_hmoe_policy.py::HMoEPolicyTests::test_hybrid_event_credit_head_gets_dedicated_optimizer_lane_and_zero_outputs tests/hmoe/test_hmoe_policy.py::HMoEPolicyTests::test_hybrid_event_credit_head_exposes_hold_fire_values_without_changing_event_logits tests/hmoe/test_a6_event_head_update_strength.py -q
pytest tests/training/test_a6_event_value_active_config.py::A6EventValueActiveConfigTests::test_a7_event_credit_config_exposes_credit_head_without_reusing_a6_hazard_loss tests/training/test_air_combat_active_training_entries.py::AirCombatActiveTrainingEntryTests::test_stage1_c2_roe_a7_event_credit_probe_is_separate_from_a6_launch_window_baseline -q
```

Observed outcome: compileall passed; focused separate-update and
nonfinite-probe tests passed with `2 passed`; policy/update-strength tests
passed with `7 passed`; active-config tests passed with `2 passed`; the final
combined focused rerun passed with `111 passed`; diff whitespace check passed.

The protected-update 8k observation completed `8192` steps and proved the
separate lane live (`a7/evc_separate_update_enabled=1.0`, nonzero early
separate-update grad norm). It improved A7 credit advantage to about `-0.0583`,
but final fixed-batch probing still reports
`legal_open_quality_positive_advantage_mean=-0.05257667228579521` with positive
sign fraction `0.0`, and process probing records `release_count=0` /
`fire_once_requested_count=0`. V is therefore a structural repair, not behavior
acceptance.
