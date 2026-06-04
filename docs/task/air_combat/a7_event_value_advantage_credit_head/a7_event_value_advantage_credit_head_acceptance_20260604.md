# A7 Acceptance Gate

Status: `2026-06-04` evaluated; `A7-EVC-C/D/E/F/G/H/I/J/K/L/M/N/O/P`
implementation, validation, learned-evidence, index-sync, target-audit,
shadow-repair, projection-audit, projection-contract, and projected legal-open
prototype/projection-eligibility/opportunity-contract slices evaluated. A7
remains held.

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
| Legal-open opportunity implementation | The P contract is implemented and focused tests prove non-starved legal-open positives. | planned next: `A7-EVC-Q Legal-Open Opportunity Credit Prototype`. |
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
