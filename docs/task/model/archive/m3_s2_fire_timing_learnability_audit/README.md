# M3-S2 Fire-Timing Learnability Audit

Status: `archived on 2026-06-08 / bounded firing gate accepted; timing,
robustness, effects, and kill-chain behavior held`.

This archive preserves the M3-S2 evidence package. The original live path
`docs/task/model/m3_s2_fire_timing_learnability_audit/` is now a lightweight
pointer README only.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Parent archive index: [Model Task Archive](../README.md)
- Active model task index: [Model Tasks](../../README.md)
- M3-S1 timing contract:
  [M3-S1 Censored Optimal-Stopping Timing Contract](../../m3_s1_censored_optimal_stopping_timing_contract/README.md)
- Stage-1 C2/ROE shaped scenario:
  `scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json`
- Maintained M3-S1 probe config:
  `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s1_grouped_stopping_state_completed_world_batch_probe_v1.json`
- Maintained M3-S2 event-window probe config:
  `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json`
- Subproject standard:
  [Subproject Creation Standard](../../../../agent/rules/subproject_creation_standard.md)

## Purpose

M3-S2 audits whether the current one-shot fire-timing problem is learnable at
all under the active Stage-1 environment, reward, C2/ROE mask, and hybrid action
transport. It pauses coefficient tuning and asks a narrower question: if an
oracle supplies the correct legal fire pulse, does the environment expose a
distinguishable signal for when that pulse should occur?

The audit treats the fire decision as an edge-triggered masked stopping problem,
not as generic continuous control. The policy emits a continuous transport
signal `u_t`; the executable fire event occurs only on a low-to-high pulse when
the legal mask is open. A stable high signal before the legal window can be
rejected and then fail to generate a later event.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Release reachability | pass | `legal_mask_fire` oracle releases one authorized missile in every audited episode. | Does not prove learned policy can form the pulse. |
| Release-vs-hold reward | pass | Legal oracle release adds about `450` return over hold-fire. | This is a release bonus, not timing quality. |
| Legal timing identifiability | partial | Delay `0`, `31`, and `63` are flat, but the full delay sweep finds damage and combat-win spikes. | The target exists in the oracle surface but is sparse and reward-ordered toward late close-range wins. |
| Reward ordering | fail | Later combat wins outrank earlier wins because positive per-step shaping accumulates before terminal success. | This is a reward-contract defect, not a proof that no-fire is optimal. |
| Post-release effects | pass/partial | Full sweep observes `270` effects/damage reports and `27` combat wins. | Early bounded probes missed this sparse region. |
| Learned-policy event reachability | fail | Deterministic learned models see open masks but keep `fire_once` probability near `0.3%` and event mode remains `hold`. | The mechanism is the labels-to-credit-to-policy training contract, not environment reachability. |
| Direct event-window supervision | held | M3-S2 reaches executable event logits and produces nonzero gradients, but deterministic probe still records `0` releases with `1080` quality-window steps. | This proves the path is connected; it does not prove behavioral fire timing. |
| Cumulative prewindow hazard | fail | Mean prewindow event probability near `0.0055` implies `0.988` cumulative early-sample risk over `800` prewindow steps. | A row-wise "small" fire probability is catastrophic for one-shot stopping. |
| Support-preserving collection | partial repair | Whole-window shield keeps `grouped_active_group_count = 4` through the 8k run and prevents accepted rollout events during collection. | It repairs training support only; deterministic evaluation still records `0` releases. |
| Event boundary transport | fail | Support-preserving r2 keeps supported rows alive, but `boundary_cross_count = 0` and event logits remain near `-5.4` to `-6.3`. | The remaining failure is policy boundary/adapter transport, not missing rows. |
| Structural toy learnability | pass | Abstract `800 + 1080` one-shot window toy learns prewindow risk below `0.02` and crosses quality-window boundary for both free logits and MLP. | This clears the pure grouped loss object; it does not clear the real rollout/update integration path. |
| Real update path | localized | On real Stage-1 forced-hold rows, reused-optimizer M3-S2 updates reduce loss by lowering prewindow and quality logits together; boundary-only reset-optimizer probes raise quality max logit by about `0.3136`. | The break is the event-mass vs deterministic-boundary contract plus shared PPO Adam state, not an unreachable parameter path. |
| Boundary dedicated short train | partial direction repair / behavior held | 8k run raises logged `m3s2/q_boundary_logit` from about `-5.95` to `-4.71`; deterministic probe still records `0` releases; stochastic probe samples one authorized release at step `623`. | This is online direction evidence, not deterministic timing acceptance. |
| Single-batch window signal | localized | On the latest forced-hold batch, raw mission fields, frozen extractor features, and frozen actor latent are linearly separable, but active M3-S2 overfit and row-wise BCE on the current action path collapse to all-positive/all-high transport. | The remaining break is the executable event-logit contract, not missing observation signal. |
| Stopping-head log-domain adapter | partial numerical repair / behavior held | Log-domain grouped stopping loss lowers deterministic M3 stop probability from about `0.47` to `0.145` in an 8k run, but deterministic release remains `0` and stochastic still samples early at step `5`. | It restores long-prewindow survival gradients; it does not learn the quality-window pulse. |
| Scale-separated stopping contract | diagnostic accepted / behavior held | 8k run lowers logged prewindow hazard from `0.413` to `0.218`, but prewindow and quality logits move down together; deterministic release remains `0`, stochastic still releases early at step `7`. | The contract is wired, but the current executable stopping/action transport still does not learn a prewindow-vs-quality discriminator. |
| Chain breakpoint localization | root localized | On one fixed real forced-hold trajectory, labels pass, standardized frozen actor latent learns `0 / 840` prewindow and `1040 / 1040` quality boundaries, folded head produces one quality pulse, but raw M3 head optimization leaves prewindow positives. | The first localized break is M3 head optimization conditioning/calibration, not missing state signal or action adapter behavior. |
| Head-normalized calibration | negative integration evidence | The 8k run enables M3 LayerNorm and explicit prewindow/quality logit margins, lowers deterministic M3 stop probability to `0.118269`, but deterministic release remains `0`; real-update probing lowers loss by lowering quality logits from `-2.003` to `-2.965`. | Capacity exists, but the online M3-S2 objective still admits global hazard suppression as the lower-loss direction. |
| Window classifier replay | local classifier repair / behavior held | Balanced latent and observation replay make online classifier batches separate positive and negative logits, but saved deterministic probes still record `release_count = 0` and quality-window classifier logits around `-8.24`; stochastic probing releases early at step `48` before quality rows. | Replay fixes a local batch-imbalance issue, not the saved actor/executable trajectory boundary. |
| Calibrated classifier standardization | negative integration evidence | Deterministic latest-balanced standardization avoids random replay-batch coordinate refresh, but the 8k final still records `release_count = 0`; fixed-chain final quality classifier logit mean is `-9.902827` while a fresh head fits the same latent perfectly. | The failure is still online head optimization/training-distribution contract, not standardization randomness. |
| Classifier standardization contract | root localized / behavior held | On the fixed `model_event_hold` trajectory, saved buffers give quality logit mean `-9.837499` and `0 / 1080` quality boundaries. Recomputing only the classifier input standardization buffers on that fixed batch changes quality logit mean to `2.195754` and `1053 / 1080` quality boundaries. | The executable path is using an inference-time normalization contract calibrated to replay/support batches, not to the execution-support trajectory. |
| Classifier execution-support contract | root localized / behavior held | Actor-gradient isolation and post-update best-restore make classifier logs reliable; the 8k run still records deterministic `release_count = 0`, saved quality-window classifier logit mean `-6.336187`, while a fresh standardized head on the same fixed execution latent reaches `1080 / 1080` quality boundaries. | The remaining break is training/replay support versus deterministic execution-support mismatch, not missing state signal, adapter wiring, or final-step logging. |
| Direct fire-boundary owner | bounded firing gate accepted / timing and effects held | Active M3-S2 now trains the executable `hybrid_event_head` directly. The 2026-06-08 continuation run from r3 records one deterministic authorized release at step `423`, zero violations/repeats, and one effects/damage report. The A5 weapon-arm fix clears the focused stochastic reject, and the bounded batch validation passes `16 / 16` deterministic/stochastic episodes with `0` rejected requests, `0` violations, and `0` repeat-before-assessment releases. | The release gate is closed for this active scenario/config pair. Timing quality, effects quality, and kill-chain behavior remain held outside this firing gate. |
| Edge-trigger adapter | hazard | `forced_fire` high from reset creates a rejected `no_target` pulse and no later release. | This is action-transport semantics, not C2/ROE failure. |

## Scope

In scope:

- Add diagnostics that separate hold, early high signal, legal oracle pulse, and
  delayed legal oracle pulses.
- Record whether legal fire is reachable, rewarded, effect-observable, and
  timing-distinguishable.
- Abstract the failure as a learnability problem before selecting M2, a new
  adapter, or a reward/effect contract.

Out of scope:

- Opening another reward coefficient sweep.
- Weakening C2/ROE masks, one-shot gates, or missile release legality.
- Claiming M2 or a learned policy is accepted.
- Treating stochastic one-shot releases as deterministic timing success.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Freeze the learnability question and formal object. | M3-S1 P5 held learned fire timing. | README defines masked edge-triggered stopping and audit breakpoints. | pass |
| `P1 Diagnostic Tooling` | Add oracle modes and an aggregate audit runner. | Existing process probe records release/effects/reward. | `hold_fire`, `legal_mask_fire`, and aggregate verdict are covered by tests. | pass |
| `P2 Oracle Evidence` | Run bounded Stage-1 oracle comparisons. | P1 tests pass. | Audit JSON records reachability, reward, effects, timing spread, and verdict. | pass |
| `P3 Root-Cause Decision` | Decide the next model or environment contract. | P2 evidence exists. | Current status names the primary breakpoint and candidate remedies. | accepted |
| `P4 Remediation Plan` | Open the next implementation slice only after decision. | P3 accepted. | Follow-on work is split out instead of keeping this package live. | held |
| `P5 Closure` | Sync parent indexes and archive superseded notes. | P4 direction exists or audit is intentionally held. | Parent docs point to the archived evidence and pointer README. | archived |

## Task Clusters

- Task cluster plan:
  [m3_s2_fire_timing_learnability_audit_task_clusters_20260605.md](m3_s2_fire_timing_learnability_audit_task_clusters_20260605.md)

## Outputs And Evidence

- Audit tooling:
  `tools/diagnostics/air_combat_stage0_process_probe.py`
- Aggregate runner:
  `tools/diagnostics/air_combat_fire_timing_learnability_audit.py`
- Focused tests:
  `tests/runtime/air_combat/test_diagnostics_probe_contracts.py`
  `tests/training/test_fire_timing_fault_localization_contracts.py`
- Oracle evidence:
  [m3_s2_fire_timing_learnability_oracle_probe_20260605.md](m3_s2_fire_timing_learnability_oracle_probe_20260605.md)
- Full delay sweep and reward-ordering evidence:
  [m3_s2_fire_timing_reward_delay_sweep_20260605.md](m3_s2_fire_timing_reward_delay_sweep_20260605.md)
- Learned-policy reachability evidence:
  [m3_s2_fire_timing_learned_policy_reachability_probe_20260605.md](m3_s2_fire_timing_learned_policy_reachability_probe_20260605.md)
- Event-window supervision evidence:
  [m3_s2_event_window_supervision_probe_20260605.md](m3_s2_event_window_supervision_probe_20260605.md)
- Cumulative hazard and support-collapse evidence:
  [m3_s2_cumulative_hazard_support_collapse_20260606.md](m3_s2_cumulative_hazard_support_collapse_20260606.md)
- Support-preserving collection evidence:
  [m3_s2_support_preserving_collect_probe_20260606.md](m3_s2_support_preserving_collect_probe_20260606.md)
- Structural toy evidence:
  [m3_s2_structural_toy_probe_20260606.md](m3_s2_structural_toy_probe_20260606.md)
- Real update path evidence:
  [m3_s2_real_update_path_probe_20260606.md](m3_s2_real_update_path_probe_20260606.md)
- Boundary and optimizer contract evidence:
  [m3_s2_boundary_optimizer_contract_probe_20260606.md](m3_s2_boundary_optimizer_contract_probe_20260606.md)
- Boundary dedicated short-train evidence:
  [m3_s2_boundary_dedicated_short_train_20260606.md](m3_s2_boundary_dedicated_short_train_20260606.md)
- Single-batch window-signal evidence:
  [m3_s2_single_batch_window_signal_probe_20260606.md](m3_s2_single_batch_window_signal_probe_20260606.md)
- Stopping-head log-domain short-train evidence:
  [m3_s2_stopping_head_adapter_log_domain_short_train_20260606.md](m3_s2_stopping_head_adapter_log_domain_short_train_20260606.md)
- Scale-separated stopping contract short-train evidence:
  [m3_s2_scale_separated_stopping_contract_short_train_20260606.md](m3_s2_scale_separated_stopping_contract_short_train_20260606.md)
- Chain breakpoint localization evidence:
  [m3_s2_chain_breakpoint_probe_20260606.md](m3_s2_chain_breakpoint_probe_20260606.md)
- Head-normalized calibration short-train evidence:
  [m3_s2_head_norm_calibration_short_train_20260606.md](m3_s2_head_norm_calibration_short_train_20260606.md)
- Window classifier short-train evidence:
  [m3_s2_window_classifier_short_train_20260606.md](m3_s2_window_classifier_short_train_20260606.md)
- Window classifier replay short-train evidence:
  [m3_s2_window_classifier_replay_short_train_20260606.md](m3_s2_window_classifier_replay_short_train_20260606.md)
- Window classifier calibrated-standardization evidence:
  [m3_s2_window_classifier_calibrated_standardization_short_train_20260606.md](m3_s2_window_classifier_calibrated_standardization_short_train_20260606.md)
- Window classifier standardization-contract evidence:
  [m3_s2_window_classifier_standardization_contract_probe_20260606.md](m3_s2_window_classifier_standardization_contract_probe_20260606.md)
- Window classifier execution-support short-train evidence:
  [m3_s2_window_classifier_execution_support_short_train_20260606.md](m3_s2_window_classifier_execution_support_short_train_20260606.md)
- Direct fire-boundary owner evidence:
  [m3_s2_direct_fire_boundary_probe_20260607.md](m3_s2_direct_fire_boundary_probe_20260607.md)
- Direct fire-boundary continuation evidence:
  [m3_s2_direct_fire_boundary_continuation_20260608.md](m3_s2_direct_fire_boundary_continuation_20260608.md)
- Fire-closure validation:
  [m3_s2_fire_closure_validation_20260608.md](m3_s2_fire_closure_validation_20260608.md)
- Fire-closure batch validation:
  [m3_s2_fire_closure_batch_validation_20260608.md](m3_s2_fire_closure_batch_validation_20260608.md)
- Current status:
  [m3_s2_fire_timing_learnability_audit_current_status_20260605.md](m3_s2_fire_timing_learnability_audit_current_status_20260605.md)
- Aggregate artifact:
  `experiments_tmp/air_combat_fire_timing_learnability_audit_20260605.json`

## Archived Acceptance Gate

This package is sealed with a narrow acceptance:

- the oracle and diagnostic breakpoints were recorded;
- direct fire-boundary ownership is wired into the active M3-S2 training path;
- the bounded batch validation passes `16 / 16` deterministic/stochastic
  episodes for the active Stage-1 C2/ROE scenario/config pair;
- the accepted claim is only that learned policy can request and execute one
  authorized release without rejected requests, violation releases, or
  repeat-before-assessment releases in this bounded gate.

Timing quality, cross-config robustness, effects quality, target damage, and
kill-chain behavior are not accepted by this archive.

## Residuals And Next Steps

- Direct fire-boundary ownership is now wired through the active training path
  and passes the bounded firing gate. The 2026-06-08 batch validation checks
  `8` deterministic and `8` stochastic episodes across seeds
  `20260608..20260615`; all `16` episodes produce exactly one accepted
  authorized release, with zero rejected requests, zero violations, and zero
  repeat-before-assessment releases. Timing/effect quality remains held outside
  this gate.
- Current reward breakpoint: the oracle surface has a mathematical optimum, but
  the optimum is a late close-range win because positive per-step shaping
  rewards delayed termination among already-winning shots.
- Current reachability breakpoint: no-fire remains unexplained by the reward
  surface because oracle release and terminal wins are reachable and rewarded.
  Learned-policy probes now narrow the cause to the current training contract:
  episode-level first-event labels were historically damaged by rollout-local
  support, and the surviving A7 bridge trains event logits toward a detached,
  tiny, uncalibrated credit advantage rather than a signed timing target.
- Direct event-window supervision narrows this further: the executable event
  logit path can receive window-level gradients, but a mean prewindow event
  probability near `0.0055` implies almost certain early stochastic consumption
  across a long one-shot prewindow. Once this happens, the runtime correctly
  enters `FiredAssess`, closes `fire_mask`, and removes the supported
  quality-window rows needed to sharpen the boundary.
- Support-preserving collection repairs that collection-time support collapse:
  the whole-window shield keeps active groups present through the 8k run and
  prevents rollout releases from consuming one-shot support. It does not repair
  behavior by itself: deterministic probing still sees `1080` quality-window
  steps, `0` releases, and no event-boundary crossing.
- Structural toy probing shows the pure grouped M3-S2 objective can learn the
  desired one-shot window boundary when support and quality-window features are
  clean: the long toy drives prewindow cumulative risk below `0.02` and crosses
  the deterministic boundary in the quality window. The remaining failure is
  therefore in the real integration path: feature-to-logit transport, selected
  update parameters, PPO overwrite/dilution, sidecar distribution, or the
  executable pulse adapter.
- Real update probing localizes that integration failure further: on real
  forced-hold Stage-1 rows, the current M3-S2 update has quality rows, large
  gradients, and moving parameters, but lowers both prewindow and quality logits
  instead of raising quality logits. The easier loss direction is global hazard
  suppression, not a sharp prewindow/quality discriminator.
- Boundary-dedicated short training repairs that local update direction online:
  supported batches raise the quality-boundary logit from about `-5.95` to
  `-4.71`. It still does not cross deterministic mode; deterministic probing
  records `0` releases while stochastic probing can sample one authorized
  release from about `0.42%` max event probability.
- Single-batch window-signal probing shows the current model already has the
  needed window signal in frozen features and actor latent. The failure is that
  the current executable action-delta objective admits an all-high transport
  solution and does not train a calibrated prewindow-negative stopping boundary.
- The stopping-head adapter plus log-domain cumulative-hazard repair fixes a
  numerical/model-contract break: long prewindow survival loss no longer loses
  gradient after probability underflow. In the 8k short train, mean M3 stop
  probability drops from about `0.47` to `0.145`. This is still far too high for
  an `800`-step one-shot prewindow, so stochastic probing can still release early
  at step `5`, and deterministic quality-window crossing remains absent.
- The scale-separated stopping contract makes the desired scales explicit, but
  the online model still moves prewindow and quality logits almost identically.
  The 8k run lowers window-bearing prewindow hazard from `0.413` to `0.218`
  against an inferred target of `0.000651`; meanwhile the quality boundary logit
  falls from `-0.346` to `-1.273`. Deterministic behavior remains no-fire and
  stochastic behavior still samples an early release at step `7`.
- The chain breakpoint probe localizes the remaining break. On the same fixed
  real trajectory, the label support is valid (`840` prewindow rows and `1040`
  quality rows), a standardized linear head on frozen actor latent reaches
  perfect separation, and the folded head produces a single quality-window
  edge-trigger pulse through the action adapter. The direct raw M3 head nearly
  learns but leaves a handful of prewindow positives, which is enough to fail
  one-shot stopping. The next repair should target head normalization,
  calibration, and the online auxiliary optimizer contract.
- The head-normalized calibration repair is now tested and held. It wires M3
  `LayerNorm`, explicit logit ceiling/floor losses, logging, diagnostics, and
  active config support. The short train lowers deterministic M3 stop probability
  from the previous scale-separated `0.157226` to `0.118269`, but prewindow and
  quality probabilities remain nearly identical, deterministic release is still
  `0`, and real-update probing lowers loss by pushing quality logits farther
  negative. The remaining issue is the mathematical objective: global hazard
  suppression is still an easier loss-reducing direction than a quality-window
  boundary.
- The current strongest breakpoint is now the executable classifier
  standardization contract. The saved
  `m3_window_classifier_input_mean/std` buffers place the fixed
  execution-support trajectory far off-center (`saved_z_mean_abs_mean =
  2.439337`, `saved_z_std_mean = 0.633167`), yielding `0 / 1080` quality
  boundaries. Recomputing only those buffers on the fixed batch immediately
  raises quality boundary crossings to `1053 / 1080`, proving the head contains
  usable timing signal but is evaluated under the wrong normalization contract.
- Secondary breakpoint: the hybrid fire transport is edge-triggered. A high
  signal before target acquisition can consume the pulse as `no_target` and
  produce no later release.
- Candidate next directions should be evaluated as model-contract changes, not
  coefficient tuning: a real-row contrastive/margin discriminator, a
  feature-to-logit audit through the temporal extractor and actor MLP, an
  event-head-to-executable-pulse adapter, reward-contract repair, or an M2
  memory/sequence release only if its stopping output is wired into an
  executable event.

## Archive

- Archive index: [Model Task Archive](../README.md)
- Pointer README:
  [m3_s2_fire_timing_learnability_audit](../../m3_s2_fire_timing_learnability_audit/README.md)
