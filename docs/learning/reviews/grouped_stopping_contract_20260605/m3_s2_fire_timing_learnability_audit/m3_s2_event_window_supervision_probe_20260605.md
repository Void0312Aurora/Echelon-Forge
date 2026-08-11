# M3-S2 Event-Window Supervision Probe - 2026-06-05

Parent: [README.md](README.md).

Status: `held evidence`; implementation path connected, behavior not accepted.
See the 2026-06-06 support-preserving follow-up for the collection-support
repair result.

## Question

Can a grouped window-level hazard objective train the executable hybrid
`fire_once` event logits directly, instead of training only an auxiliary
stopping or credit head?

The tested target is not a single hard-coded best release step. It is a window
contract:

- suppress prewindow fire mass;
- place at least one event inside a quality window;
- prefer earlier quality-window mass through a delay penalty;
- require mass before a deadline through a deadline penalty;
- rely on the existing one-shot/C2/ROE state machine to prevent repeated
  releases.

## Implementation

Code and config:

- `python/rl/policy_algo/m3s1_grouped_stopping.py`
  - adds explicit `window_delay_coef`, `window_deadline_coef`, and
    `window_deadline_steps` support to the grouped survival/event-mass loss;
  - records `mean_p_deadline` and `mean_quality_delay`.
- `python/rl/policy_algo/ppo_adaptive_kl.py`
  - adds `m3s2_event_window_*` hyperparameters;
  - reuses the M3-S1 grouped sidecar, but computes logits from
    `policy.get_distribution(obs).fire_event_logit_delta()`;
  - updates only the executable event-policy path in separate-update mode.
- `python/rl/support/nonfinite_probe.py`
  - mirrors the M3-S2 sidecar collection, auxiliary update, and logger path
    while the non-finite probe monkey patch is installed.
- Active config:
  `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json`

## Validation

```bash
python -m compileall -q \
  python/rl/policy_algo/m3s1_grouped_stopping.py \
  python/rl/policy_algo/ppo_adaptive_kl.py \
  python/rl/support/nonfinite_probe.py \
  tests/policy/test_grouped_stopping_loss_contracts.py \
  tests/policy/test_auxiliary_training_updates.py
```

Outcome: pass.

```bash
pytest tests/policy/test_grouped_stopping_loss_contracts.py -q
pytest tests/policy/test_auxiliary_training_updates.py -q
pytest tests/training/test_air_combat_training_entry_contracts.py -q
```

Outcomes:

- `9 passed`
- `23 passed`
- `16 passed`

The HMoE tests include a regression that installs `NonFiniteTrainingProbe` and
verifies that `m3s2/event_window_loss` is logged and that the executable event
head changes.

## Short Training

Command:

```bash
env PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name m3s2_event_window_8k_20260605_r2
```

Artifacts:

```text
experiments_tmp/m3s2_event_window_8k_20260605_r2/final_model.zip
experiments_tmp/m3s2_event_window_8k_20260605_r2/m3s2_deterministic_probe.json
experiments_tmp/m3s2_event_window_8k_20260605_r2/m3s2_stochastic_probe.json
```

Training observations:

| Step | Window groups | Window logit mean | Window mass | Deadline mass | Grad norm |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2048 | 0 | 0.000 | 0.000 | 0.000 | 7.567 |
| 3072 | 1 | -6.247 | 0.332 | 0.110 | 21.615 |
| 4096 | 1 | -5.992 | 0.398 | 0.137 | 20.607 |
| 5120 | 1 | -5.624 | 0.142 | 0.142 | 22.187 |
| 6144 | 0 | 0.000 | 0.000 | 0.000 | 0.000 |
| 7168 | 0 | 0.000 | 0.000 | 0.000 | 0.000 |
| 8192 | 0 | 0.000 | 0.000 | 0.000 | 0.000 |

The path is connected: M3-S2 produced nonzero loss and gradients, and the
window event logit moved upward from about `-6.25` to about `-5.62` while
quality-window groups were present. It still never crossed the deterministic
boundary: `boundary_cross_count` stayed `0`.

## Learned-Policy Probe

Deterministic probe:

```bash
env PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/m3s2_event_window_8k_20260605_r2/final_model.zip \
  --device cuda \
  --episodes 1 \
  --max_steps 2400
```

Result:

- `first_release_step = null`
- `release_count = 0`
- `fire_mask_open_step_count = 1880`
- `a7_quality_window_step_count = 1080`
- `policy_event_prob_fire_once_max = 0.00556`
- `policy_event_mode_fire_once_count = 0`
- `a7_quality_window_event_fire_prob_mean = 0.00555`
- `final_missiles = 4`
- `final_target_health = 40.0`

Stochastic probe:

- `first_release_step = 14`
- `release_count = 1`
- `fire_mask_open_step_count = 11`
- `a7_quality_window_step_count = 0`
- `effects_event_count = 0`
- `damage_report_count = 0`
- `final_missiles = 3`
- `final_target_health = 40.0`

The stochastic release is therefore an early low-probability sample, not a
learned quality-window release.

## Decision

M3-S2 event-window supervision is implemented and reaches the executable event
logit path. It is not accepted as a behavioral solution.

The remaining failure is sharper than before:

- the actor can receive direct window-level gradients;
- those gradients lift the fire logit slightly while supported window groups
  exist;
- support disappears later in the rollout sequence, and the logit remains far
  below the deterministic fire boundary;
- the learned deterministic policy still times out with no release despite
  `1080` quality-window steps.

This points to a deeper support/transport/training-contract problem, not merely
the absence of a direct actor loss. Candidate next work should focus on
maintaining supported quality-window rows and/or converting a learned stopping
decision into an executable low-high-low pulse, before treating longer memory
as the primary fix.

## Follow-Up

Maintained follow-up:
[m3_s2_support_preserving_collect_probe_20260606.md](m3_s2_support_preserving_collect_probe_20260606.md).

That probe implemented support-preserving collection and confirmed that the
training-support collapse can be blocked: the whole-window shield keeps
`grouped_active_group_count = 4` through the 8k run and prevents accepted
rollout events during collection. It does not change the behavioral verdict:
deterministic probing still records `0` releases and `boundary_cross_count`
stays `0`.
