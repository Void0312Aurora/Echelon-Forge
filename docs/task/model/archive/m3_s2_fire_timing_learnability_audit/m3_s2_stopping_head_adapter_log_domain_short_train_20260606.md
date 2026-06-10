# M3-S2 Stopping-Head Adapter Log-Domain Short Train

Parent: [README.md](README.md).

Status: `2026-06-06` repair evidence recorded; log-domain cumulative-hazard
loss accepted as necessary, behavioral fire timing still held.

## Question

After wiring M3-S2 event-window supervision through the dedicated
`m3_stopping_head` adapter, why does short training still fail to produce a
deterministic fire event?

This slice checks two implementation-level candidates:

- the new balanced BCE branch must not fail at runtime;
- long prewindow stopping losses must keep useful gradients after cumulative
  survival probabilities become extremely small.

## Repairs

Code changes:

- `python/rl/policy_algo/m3s1_grouped_stopping.py`
  - fixed the balanced BCE branch to use local `quality_mask` and `legal_mask`
    instead of stale caller-local names;
  - moved the grouped stopping event-mass terms into log-domain computation so
    `-log(p_window)` and `-log(p_none)` do not lose gradients through
    probability underflow or `clamp_min(eps)`;
  - kept event-mass values for diagnostics while using log-sum-exp for window
    mass and deadline mass.
- `tests/policy/test_grouped_stopping_loss_contracts.py`
  - added a long-prewindow regression test that verifies prewindow logits get a
    positive gradient direction and quality-window logits get a negative
    gradient direction when the window hazard is initially too low.

The log-domain repair is structural, not a coefficient change. With an
`800`-step prewindow, row-wise probabilities near `0.5` make survival to the
window astronomically small. The old probability-domain loss could hit the
`eps` clamp and stop carrying the gradient needed to lower early hazard.

## Validation

Focused compile and tests:

```bash
python -m compileall -q \
  python/rl/policy_algo/m3s1_grouped_stopping.py \
  python/rl/policy_algo/policies.py \
  python/rl/policy_algo/ppo_adaptive_kl.py \
  python/rl/support/nonfinite_probe.py \
  tools/diagnostics/m3s2_real_update_path_probe.py

python -m pytest \
  tests/policy/test_grouped_stopping_loss_contracts.py \
  tests/policy/test_execution_policy_surface.py::ExecutionPolicySurfaceTests::test_m3_stopping_head_can_override_hybrid_fire_event_delta \
  tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_m3s2_event_window_can_train_dedicated_stopping_head_adapter \
  tests/policy/test_auxiliary_training_updates.py::AuxiliaryTrainingUpdateTests::test_m3s2_event_window_auxiliary_updates_executable_event_policy_path \
  tests/training/test_air_combat_training_entry_contracts.py::AirCombatTrainingEntryContractTests::test_stage1_m3s2_event_window_probe_extends_state_completed_config_only \
  tests/training/test_fire_timing_fault_localization_contracts.py -q
```

Outcome: `20 passed`.

## Real-Update Probe

Artifact:

```text
experiments_tmp/m3s2_stopping_head_adapter_8k_20260606_r1/m3s2_real_update_stopping_head_probe_log_domain.json
```

The same forced-hold real row batch was updated for `120` steps with
`scope = m3_stopping_head`, `learning_rate = 0.001`, `max_grad_norm = 10`, and
reset optimizer state.

| Metric | Before | After |
| --- | ---: | ---: |
| loss | `1707.144817` | `70.558770` |
| prewindow logit mean | `-0.117777` | `-2.430021` |
| quality logit mean | `-0.116425` | `-1.954641` |
| quality max logit | `-0.114623` | `-0.889170` |
| quality-boundary crossing | `0 / 1040` | `0 / 1040` |
| balanced BCE loss trace | `0.693269` | `1.107806` |
| quality-prewindow margin trace | `0.003341` | `2.559333` |

Interpretation:

- the repair restores the strong survival gradient that lowers prewindow
  hazard;
- the same update still does not raise quality-window logits above the
  deterministic boundary;
- the easier real-row direction is now "survive the long prewindow" rather than
  "emit a window pulse."

## Short Train

Command:

```bash
env PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name m3s2_stopping_head_adapter_log_domain_8k_20260606_r1
```

Artifacts:

```text
experiments_tmp/m3s2_stopping_head_adapter_log_domain_8k_20260606_r1/final_model.zip
experiments_tmp/m3s2_stopping_head_adapter_log_domain_8k_20260606_r1/m3s2_deterministic_probe.json
experiments_tmp/m3s2_stopping_head_adapter_log_domain_8k_20260606_r1/m3s2_stochastic_probe.json
```

Selected online training observations:

| Step | event logit mean | q boundary logit | window mass | boundary crosses |
| ---: | ---: | ---: | ---: | ---: |
| 3072 | `-0.426` | `-0.421` | `1.74e-07` | `0` |
| 4096 | `-0.672` | `-0.667` | `2.93e-06` | `0` |
| 5120 | `-0.891` | `-0.888` | `2.35e-05` | `0` |
| 6144 | `-1.09` | `-1.09` | `0.000127` | `0` |
| 7168 | `-1.29` | `-1.28` | `0.000498` | `0` |
| 8192 | `-1.48` | n/a, no-window batch | `0` | `0` |

The online trace confirms the log-domain repair changed the learning direction:
the stopping head is no longer stuck near a per-step hazard of `0.47`. It is
being pushed downward. It still does not learn a quality-window boundary in this
8k run.

## Behavior Probes

Compared against the pre-log-domain stopping-head adapter run:

| Run | Mode | release count | first release step | M3 stop prob mean | M3 stop prob max | prewindow mean | quality mean |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| pre-log-domain adapter | deterministic | `0` | n/a | `0.470836` | `0.471635` | `0.470496` | `0.470783` |
| pre-log-domain adapter | stochastic | `1` | `3` | `0.470360` | `0.471798` | `0.463445` | `0` |
| log-domain adapter | deterministic | `0` | n/a | `0.145112` | `0.146770` | `0.145016` | `0.145566` |
| log-domain adapter | stochastic | `1` | `5` | `0.144738` | `0.146408` | `0.141813` | `0` |

Interpretation:

- deterministic behavior is still held: no release and no M3 boundary crossing;
- stochastic early release remains possible because `0.14` per legal step is
  still too large for a long one-shot prewindow;
- the repair is therefore a necessary numerical/model-contract fix, not a
  complete fire-timing solution.

## Verdict

Accepted for this slice:

- balanced BCE runtime bug fixed;
- long-prewindow loss now keeps log-domain gradients;
- short training no longer leaves the stopping head near `0.47` per-step hazard.

Still held:

- deterministic quality-window crossing;
- stochastic early-release suppression to the `1 / horizon` scale;
- a learned low-high-low executable pulse.

Next work should treat this as a scale-separated stopping contract problem:
prewindow hazard must be near `1 / horizon` or below, while the quality window
still needs a deterministic pulse. A plain row-wise classifier or uncalibrated
event-mass objective is not enough.
