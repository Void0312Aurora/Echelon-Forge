# M3-S2 Fire-Timing Learnability Audit Current Status

Parent: [README.md](README.md).

Status: `2026-06-06` diagnosis active; support-preserving collect repair
partially accepted, boundary-dedicated short training direction improved,
log-domain cumulative-hazard repair accepted, behavioral event timing still
held.

## Formal Object

The active Stage-1 fire problem can be abstracted as a masked, edge-triggered
stopping process:

```text
state/history:      h_t
legal mask:         m_t in {0, 1}
transport output:   u_t in [0, 1]
event pulse:        e_t = 1[u_t > 0.5 and u_{t-1} <= 0.5 and m_t = 1]
early rejection:    q_t = 1[u_t > 0.5 and u_{t-1} <= 0.5 and m_t = 0]
return:             R = shaping + release_bonus * sum(e_t) + downstream_effect_terms
constraint:         sum(e_t) <= 1 unless explicit reattack is authorized
```

The learned policy has to solve two problems simultaneously:

- choose a stopping time inside a useful legal window;
- express that stopping time as a low-to-high executable pulse, not as a
  continuously high scalar.

## Current Diagnosis

| Question | Result | Evidence |
| --- | --- | --- |
| Can an oracle legal pulse release a missile? | yes | `legal_mask_fire_delay_*` releases one authorized missile in both audited episodes. |
| Does the environment distinguish release from no release? | yes | Legal release adds about `450` return over hold-fire. |
| Does the environment distinguish legal timing alternatives? | partial | Delay `0`, `31`, and `63` are flat, but a full `0..1778` delay sweep finds sparse damage and terminal-win spikes. |
| Does the release expose downstream effects? | yes, sparsely | Full sweep records `270` effects/damage reports and `27` combat wins. |
| Does the reward rank useful wins correctly? | no | Later wins outrank earlier wins by about `0.04` return per extra step before terminal success. |
| Do learned deterministic policies choose supported fire? | no | M3-S1 and A7 probes keep event fire probability near `0.3%` while event mode remains `hold`, despite open masks. |
| Is credit support completely absent? | no | Probe rows show positive event-credit advantage around `0.8`, but actor event logits stay about `-5.6` to `-5.8`. |
| Does direct actor event-window supervision solve it? | no | M3-S2 produces nonzero executable-event gradients and raises window logits from about `-6.25` to `-5.62`, but deterministic probing still records `0` releases. |
| Does a small per-step fire probability remain safe over the prewindow? | no | `p ~= 0.0055` over `800` prewindow steps implies `0.988` cumulative early-sample risk. |
| Does support-preserving collection stop rollout support collapse? | yes, for collection | Whole-window shield keeps `grouped_active_group_count = 4` through the 8k run, leaves `closed_mask_row_count = 0` at the end, and prevents accepted rollout events during collection. |
| Does that repair learned deterministic fire? | no | Deterministic probing still records `release_count = 0`, `policy_event_mode_fire_once_count = 0`, and `1080` quality-window steps. |
| Can the pure M3-S2 grouped objective learn the abstract one-shot window pulse? | yes | Structural toy `800 + 1080` passes for both free logits and MLP: prewindow risk falls below `0.02`, no prewindow boundary appears, and quality-window logits cross deterministic mode. |
| Does the real M3-S2 update path raise quality-window logits? | only after contract/optimizer repair | Reused-optimizer event-mass updates lower quality logits, but final boundary-contract probes with reset/dedicated optimizer simulation raise quality max logit by about `0.3136`. |
| Does boundary-dedicated short training change behavior? | direction yes, deterministic behavior no | 8k run raises `m3s2/q_boundary_logit` from about `-5.95` to `-4.71`; deterministic probe still releases `0`, while stochastic probe samples one authorized release at step `623`. |
| Does the policy observation/latent contain the window signal? | yes | On a fixed forced-hold batch, raw mission fields, frozen extractor features, and frozen actor latent are all linearly separable; each reaches about `100%` window-classification accuracy. |
| Can the current executable action path overfit that split? | no | Boundary-only and active-contract overfits raise all legal logits; row-wise BCE on `current` and `current_plus_features` collapses to all-positive majority-class behavior. |
| Does log-domain cumulative-hazard repair improve the stopping-head adapter? | partially | It drops deterministic M3 stop probability from about `0.47` to `0.145`, but deterministic release remains `0` and stochastic still samples an early authorized release at step `5`. |
| Can a high scalar before target acquisition recover later? | no | `forced_fire` records `{"no_target": 2}` and no release because no later rising edge occurs. |

## Root-Cause Statement

The current failure is not simply "short training did not learn." The evidence
now separates the symptom from the mechanism:

- reward ordering is wrong for already-winning shots: positive per-step shaping
  makes later terminal success score higher than earlier terminal success;
- no-fire is not explained by the reward surface: oracle legal release is
  reachable, rewarded, and can produce terminal wins;
- learned-policy no-fire is the visible symptom: masks are open and stochastic
  samples can release, but deterministic event logits remain on the `hold` side;
- the mechanism is the current training contract. Episode-level first-event
  credit was originally evaluated on rollout-local chunks, which deleted
  shadow-positive support after early stochastic releases. After that support
  issue was repaired, the remaining A7 bridge still trained event logits toward
  a detached, tiny, uncalibrated credit advantage instead of a signed timing
  target. The actor representation therefore never learned the prewindow versus
  quality-window discriminator needed for deterministic `argmax(fire_once)`.

This means reward repair is necessary, but it is not sufficient to explain why
the learned model fails to fire. The remaining reachability question is whether
the learned policy can express a supported fire event through the masked
edge-triggered transport.

The M3-S2 event-window probe removes one candidate explanation: the failure is
not merely that actor event logits lacked a direct supervised loss. They now
receive grouped window-level gradients through the executable event distribution.
The remaining problem is that supported quality-window rows are intermittent and
the learned logit remains far below the deterministic fire boundary.

The sharper 2026-06-06 diagnosis is cumulative prewindow hazard. A row-wise
probability near `0.0055` looks small, but over `800` prewindow steps it implies
almost certain stochastic early consumption of the one-shot event. That early
sample switches the runtime to `FiredAssess`, closes `fire_mask`, and removes
the later quality-window rows that M3-S2 needs for training support.

The support-preserving collection repair confirms that diagnosis. When the
collector holds `fire_once = 0` during the full legal-open support window, the
training trace no longer collapses into closed-mask rows: the 8k support run
ends with `grouped_active_group_count = 4`, `grouped_active_row_count = 1024`,
and `closed_mask_row_count = 0`. However, the learned policy still keeps
`fire_once` on the hold side; deterministic probing records `0` releases, while
stochastic probing can still sample an early release. The remaining break is
therefore event-boundary transport or actor target calibration, not merely
missing quality-window rows.

The structural toy probe removes another possible explanation: the grouped
M3-S2 loss itself can learn the desired boundary. With `800` prewindow steps and
`1080` quality-window steps, `free_logits` reaches prewindow cumulative risk
`0.009140485` and quality max logit `2.393876`; the MLP reaches prewindow
cumulative risk `0.000005254` and quality max logit `9.366981`. Both cross the
quality boundary at step `800` without any prewindow boundary crossing.

The real update path probe then localizes the failure inside the real policy
transport and optimizer contract. A forced-hold Stage-1 sequence has `1880`
legal rows and `1040` quality rows, but the reused-optimizer active M3-S2 update
lowers quality max logit by about `0.265` while reducing loss. Contrastive
real-row margin alone does not repair this: even high contrastive weight still
lowers absolute quality logits. A high quality-boundary anchor without optimizer
reset also steps in the wrong direction and increases the current loss. When the
same boundary update clears optimizer state, the real parameter path raises
quality max logit by about `0.3136`. The current localized break is therefore
twofold: stochastic event-mass supervision is not a deterministic boundary
contract, and the auxiliary update must be isolated from PPO Adam state.

The boundary-dedicated 8k short train confirms this repair only at the update
direction level. Supported training batches raise the online quality-boundary
logit from about `-5.95` to `-4.71`, but deterministic probing still records
`release_count = 0`, `policy_event_mode_fire_once_count = 0`, and
`policy_m3_boundary_cross_count = 0`. The stochastic probe samples one
authorized release at step `623`, with max event probability still around
`0.42%`; this proves executable sampled behavior exists, not that a
deterministic stopping boundary has been learned.

Single-batch window-signal probing then localizes the remaining failure more
deeply. The fixed forced-hold batch contains direct separating mission
features: `launch_window_open = 0` throughout prewindow rows and `1` throughout
quality-window rows. A frozen-feature linear probe reaches near-perfect
classification on raw mission fields, the temporal extractor output, and actor
latent. However, training through the current executable `fire_event_logit_delta`
path does not learn this separator: boundary-only and active-contract overfits
push both prewindow and quality logits above zero, and row-wise BCE on the
current action path collapses to all-positive majority behavior. The current
break is therefore the event-logit/action-transport contract, not missing
state signal.

The stopping-head adapter and log-domain cumulative-hazard repair add one more
layer to the diagnosis. The previous grouped stopping loss computed
`p_window`/`p_none` in probability space and then clamped probabilities at
`eps`; with an `800`-step prewindow this could erase the survival gradient after
underflow. The repaired loss uses log-sum-exp and log survival terms. A focused
real-update probe now lowers prewindow logit mean from `-0.117777` to
`-2.430021` and loss from `1707.144817` to `70.558770`, proving that the long
prewindow survival gradient is restored. The same update also lowers quality
logits and still records `0 / 1040` quality-boundary crossings, so the remaining
contract problem is scale separation: prewindow hazard must approach the
`1 / horizon` scale while the quality window still needs a deterministic pulse.

## Learned-Policy Reachability Evidence

Maintained evidence page:
[m3_s2_fire_timing_learned_policy_reachability_probe_20260605.md](m3_s2_fire_timing_learned_policy_reachability_probe_20260605.md).

Key findings:

- M3-S1 state-completed deterministic probes record open masks for `1880` and
  `1840` steps, but `policy_event_prob_fire_once_max` stays below `0.00384`
  and `policy_event_mode_fire_once_count` is `0`.
- A7 safe-bias deterministic probes record open masks for `639` and `599`
  steps, but `policy_event_prob_fire_once_max` stays below `0.00315` and
  `policy_event_mode_fire_once_count` is `0`.
- Stochastic probes sometimes release one missile, which proves the runtime
  event path is executable when sampled, but those releases are low-probability
  samples rather than a learned deterministic boundary.
- Event-credit advantage can be positive around `0.8` in prewindow and quality
  rows, while actor event probabilities remain almost identical and near
  `0.3%` in both regions.
- The M3 stopping head remains auxiliary: in the M3-S1 deterministic probe it
  reports `stop_prob = 0.5` and boundary crossing every step, but no executable
  `fire_once` action is emitted.
- M3-S2 direct event-window supervision reaches the executable event path:
  `m3s2/event_window_grad_norm` peaks at `22.19`, but deterministic probing
  still sees `1080` quality-window steps, `policy_event_prob_fire_once_max =
  0.00556`, and `policy_event_mode_fire_once_count = 0`.
- The same deterministic probe reports `a7_prewindow_step_count = 800`,
  `a7_prewindow_event_fire_prob_mean = 0.005541579`, and
  `a7_prewindow_event_fire_prob_cum = 0.988269851`; the stochastic probe then
  releases at step `14` before any quality-window row is observed.
- The support-preserving r2 training trace keeps active groups present through
  all logged updates (`min = 4`, `final = 4`) and prevents rollout accepted
  events (`accepted_event_count = 0` throughout), but `boundary_cross_count`
  remains `0`.
- The support-preserving r2 deterministic probe reports `release_count = 0`,
  `a7_quality_window_step_count = 1080`,
  `policy_event_prob_fire_once_max = 0.003296760`, and
  `a7_prewindow_event_fire_prob_cum = 0.927001125`.
- The structural toy probe reports `all_structural_toys_pass = true` for
  `free_logits` and `mlp`; the artifact is
  `experiments_tmp/m3s2_structural_toy_probe_20260606.json`.
- The real update path probe reports `has_quality_rows = true`,
  `any_update_raises_quality_logit = false`, and
  `any_update_quality_boundary = false`; artifacts are
  `experiments_tmp/m3s2_real_update_path_probe_20260606_4step.json` and
  `experiments_tmp/m3s2_real_update_path_probe_20260606_40step_current.json`.
- The boundary/optimizer contract probe reports that contrastive margin alone
  still lowers absolute quality logits, while final boundary-contract updates
  with reset/dedicated optimizer simulation raise quality max logit by `0.313624`;
  artifact:
  `experiments_tmp/m3s2_real_update_path_probe_20260606_final_config_dedicated_sim_4step.json`.
- The boundary-dedicated short train reports online quality-boundary movement
  from about `-5.95` to `-4.71`, deterministic `release_count = 0`, and one
  stochastic authorized release at step `623`; artifacts:
  `experiments_tmp/m3s2_boundary_dedicated_8k_20260606_r2/final_model.zip`,
  `experiments_tmp/m3s2_boundary_dedicated_8k_20260606_r2/m3s2_deterministic_probe.json`,
  and
  `experiments_tmp/m3s2_boundary_dedicated_8k_20260606_r2/m3s2_stochastic_probe.json`.
- Single-batch window-signal probes show all-high collapse under boundary-only
  and active-contract overfits, majority-class collapse under row-wise BCE on
  the current action path, and near-perfect separability in raw mission,
  frozen features, and frozen actor latent; artifacts:
  `experiments_tmp/m3s2_single_batch_boundary_only_overfit_20260606.json`,
  `experiments_tmp/m3s2_single_batch_active_contract_overfit_20260606.json`,
  `experiments_tmp/m3s2_single_batch_row_bce_capacity_20260606.json`,
  `experiments_tmp/m3s2_single_batch_row_bce_capacity_features_20260606.json`,
  `experiments_tmp/m3s2_window_signal_feature_probe_20260606.json`, and
  `experiments_tmp/m3s2_frozen_latent_event_head_balanced_bce_20260606.json`.
- The stopping-head adapter log-domain short train drops deterministic
  `policy_m3_stop_prob_mean` from about `0.470836` to `0.145112`, but still
  reports deterministic `release_count = 0`; stochastic probing releases early
  at step `5`. Artifacts:
  `experiments_tmp/m3s2_stopping_head_adapter_log_domain_8k_20260606_r1/final_model.zip`,
  `experiments_tmp/m3s2_stopping_head_adapter_log_domain_8k_20260606_r1/m3s2_deterministic_probe.json`,
  `experiments_tmp/m3s2_stopping_head_adapter_log_domain_8k_20260606_r1/m3s2_stochastic_probe.json`,
  and
  `experiments_tmp/m3s2_stopping_head_adapter_8k_20260606_r1/m3s2_real_update_stopping_head_probe_log_domain.json`.

## Recommended Next Slice

Do not start with M2 memory as the first fix. Memory may help represent
history, but the current evidence requires an action/event reachability audit
before another sequence-model implementation.

Open the next slice as a contract repair with seven possible tracks:

1. Deterministic boundary contract: keep the quality-window positive bag
   objective as the primary actor target and require at least one supported
   quality-window logit to move toward deterministic mode.
2. Isolated auxiliary optimization: keep M3-S2 event-window updates off the
   shared PPO Adam state through the dedicated optimizer path.
3. Event-to-pulse adapter: convert the selected stopping/event decision into an
   executable low-high-low pulse under `fire_mask`, and audit that deterministic
   stop boundary produces a real release.
4. Reward contract repair: prevent positive per-step shaping from ranking later
   terminal success above earlier terminal success.
5. Learned-policy reachability audit: determine whether no-fire comes from
   logits/probability, mask support, edge consumption, action projection, or PPO
   credit.
6. Actor event-label calibration: train a signed event-logit target that pushes
   prewindow hazard toward the `1 / horizon` scale while requiring quality-window
   logit crossing above deterministic mode.
7. Supported-window maintenance: keep the training support-preserving path as a
   diagnostic guard, but do not count it as behavior acceptance.
8. Cumulative-hazard contract: log and directly constrain prewindow cumulative
   event risk at the group level, because the safe per-step scale is near
   `1 / horizon`, not a generic row-wise small probability.

M2 should remain a candidate only after the action-event adapter and reward
contract have clear acceptance gates, or after M2 explicitly owns the adapter
from stopping output to executable pulse.

## Validation Already Run

```bash
python -m py_compile \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  tools/diagnostics/air_combat_fire_timing_learnability_audit.py \
  tests/diagnostics/test_air_combat_process_probe.py \
  tests/diagnostics/test_air_combat_fire_timing_learnability_audit.py
```

Outcome: pass.

```bash
python -m pytest \
  tests/diagnostics/test_air_combat_process_probe.py \
  tests/diagnostics/test_air_combat_fire_timing_learnability_audit.py -q
```

Outcome: `13 passed`.

Audit artifact:

```text
experiments_tmp/air_combat_fire_timing_learnability_audit_20260605.json
```

Full delay sweep artifacts:

```text
experiments_tmp/air_combat_fire_timing_full_delay_sweep_seed7_ep1_0_1778_20260605_summary.json
experiments_tmp/air_combat_fire_timing_full_delay_sweep_seed7_ep1_0_1778_20260605_compact.csv
experiments_tmp/air_combat_fire_timing_full_delay_sweep_seed7_ep1_0_1778_20260605.png
```

Learned-policy reachability artifacts:

```text
experiments_tmp/m3s1_p5_state_completed_8k_20260605_r1/m3s1_deterministic_probe.json
experiments_tmp/m3s1_p5_state_completed_8k_20260605_r1/m3s1_stochastic_probe.json
experiments_tmp/a7_event_policy_margin_safe_bias_8k_20260605_r1/deterministic_probe.json
experiments_tmp/a7_event_policy_margin_safe_bias_8k_20260605_r1/stochastic_probe.json
```

M3-S2 event-window artifacts:

```text
experiments_tmp/m3s2_event_window_8k_20260605_r2/final_model.zip
experiments_tmp/m3s2_event_window_8k_20260605_r2/m3s2_deterministic_probe.json
experiments_tmp/m3s2_event_window_8k_20260605_r2/m3s2_stochastic_probe.json
```

M3-S2 support-preserving artifacts:

```text
experiments_tmp/m3s2_support_preserve_8k_20260606_r1/final_model.zip
experiments_tmp/m3s2_support_preserve_8k_20260606_r1/m3s2_deterministic_probe.json
experiments_tmp/m3s2_support_preserve_8k_20260606_r1/m3s2_stochastic_probe.json
experiments_tmp/m3s2_support_preserve_8k_20260606_r2/final_model.zip
experiments_tmp/m3s2_support_preserve_8k_20260606_r2/m3s2_deterministic_probe.json
experiments_tmp/m3s2_support_preserve_8k_20260606_r2/m3s2_stochastic_probe.json
```

M3-S2 boundary-dedicated short-train artifacts:

```text
experiments_tmp/m3s2_boundary_dedicated_8k_20260606_r2/final_model.zip
experiments_tmp/m3s2_boundary_dedicated_8k_20260606_r2/m3s2_deterministic_probe.json
experiments_tmp/m3s2_boundary_dedicated_8k_20260606_r2/m3s2_stochastic_probe.json
```

M3-S2 single-batch window-signal artifacts:

```text
experiments_tmp/m3s2_single_batch_boundary_only_overfit_20260606.json
experiments_tmp/m3s2_single_batch_active_contract_overfit_20260606.json
experiments_tmp/m3s2_single_batch_row_bce_capacity_20260606.json
experiments_tmp/m3s2_single_batch_row_bce_capacity_features_20260606.json
experiments_tmp/m3s2_window_signal_feature_probe_20260606.json
experiments_tmp/m3s2_frozen_latent_event_head_balanced_bce_20260606.json
```

M3-S2 structural toy artifact:

```text
experiments_tmp/m3s2_structural_toy_probe_20260606.json
```

M3-S2 real update path artifacts:

```text
experiments_tmp/m3s2_real_update_path_probe_20260606_4step.json
experiments_tmp/m3s2_real_update_path_probe_20260606_40step_current.json
experiments_tmp/m3s2_real_update_path_probe_20260606_contrastive_4step.json
experiments_tmp/m3s2_real_update_path_probe_20260606_boundary100_window_only_resetopt_4step.json
experiments_tmp/m3s2_real_update_path_probe_20260606_final_config_dedicated_sim_4step.json
experiments_tmp/m3s2_stopping_head_adapter_8k_20260606_r1/m3s2_real_update_stopping_head_probe_log_domain.json
```

M3-S2 stopping-head log-domain short-train artifacts:

```text
experiments_tmp/m3s2_stopping_head_adapter_log_domain_8k_20260606_r1/final_model.zip
experiments_tmp/m3s2_stopping_head_adapter_log_domain_8k_20260606_r1/m3s2_deterministic_probe.json
experiments_tmp/m3s2_stopping_head_adapter_log_domain_8k_20260606_r1/m3s2_stochastic_probe.json
```

Event-window implementation evidence:

```text
docs/task/model/m3_s2_fire_timing_learnability_audit/m3_s2_event_window_supervision_probe_20260605.md
docs/task/model/m3_s2_fire_timing_learnability_audit/m3_s2_cumulative_hazard_support_collapse_20260606.md
docs/task/model/m3_s2_fire_timing_learnability_audit/m3_s2_support_preserving_collect_probe_20260606.md
docs/task/model/m3_s2_fire_timing_learnability_audit/m3_s2_structural_toy_probe_20260606.md
docs/task/model/m3_s2_fire_timing_learnability_audit/m3_s2_real_update_path_probe_20260606.md
docs/task/model/m3_s2_fire_timing_learnability_audit/m3_s2_boundary_optimizer_contract_probe_20260606.md
docs/task/model/m3_s2_fire_timing_learnability_audit/m3_s2_stopping_head_adapter_log_domain_short_train_20260606.md
```
