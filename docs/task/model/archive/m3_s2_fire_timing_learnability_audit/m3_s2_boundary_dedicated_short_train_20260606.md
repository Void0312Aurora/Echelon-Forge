# M3-S2 Boundary Dedicated Short Train - 2026-06-06

Parent: [README.md](README.md).

Status: `short-train evidence`; update direction improved, behavioral
deterministic fire timing still held.

## Question

After adding the deterministic quality-window boundary anchor and isolating the
M3-S2 auxiliary optimizer from PPO Adam state, does an 8k short train change the
learned firing behavior?

## Run

Scenario:

```text
scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json
```

Training config:

```text
examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json
```

Command:

```bash
env PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name m3s2_boundary_dedicated_8k_20260606_r2
```

Artifact:

```text
experiments_tmp/m3s2_boundary_dedicated_8k_20260606_r2/final_model.zip
```

The first attempt (`m3s2_boundary_dedicated_8k_20260606_r1`) reached training but
failed during logger dump because two long M3-S2 keys truncated to the same SB3
logger name. The maintained run is `r2` after shortening the M3-S2 log keys.

## Training Signal

Logged batches with quality-window rows show the boundary target moving in the
intended direction:

| Timestep | `window_group_count` | `support_preserving_quality_count` | `m3s2/q_boundary_logit` | `boundary_cross_count` |
| ---: | ---: | ---: | ---: | ---: |
| `3072` | `4` | `924` | `-5.95` | `0` |
| `4096` | `4` | present | `-5.63` | `0` |
| `5120` | `4` | present | `-5.32` | `0` |
| `6144` | `4` | present | `-5.01` | `0` |
| `7168` | `4` | `324` | `-4.71` | `0` |

The final logger dump had no quality rows and therefore reported a neutral
quality-boundary statistic; it is not representative of the behavior window.

## Behavioral Probes

Deterministic probe:

```text
experiments_tmp/m3s2_boundary_dedicated_8k_20260606_r2/m3s2_deterministic_probe.json
```

| Metric | Value |
| --- | ---: |
| `termination_reason` | `combat_timeout` |
| `release_count` | `0` |
| `first_release_step` | `null` |
| `final_missiles` | `4` |
| `fire_mask_open_step_count` | `1880` |
| `a7_quality_window_step_count` | `1080` |
| `policy_event_prob_fire_once_max` | `0.004191798` |
| `policy_event_mode_fire_once_count` | `0` |
| `policy_m3_boundary_cross_count` | `0` |

Stochastic probe:

```text
experiments_tmp/m3s2_boundary_dedicated_8k_20260606_r2/m3s2_stochastic_probe.json
```

| Metric | Value |
| --- | ---: |
| `termination_reason` | `combat_timeout` |
| `release_count` | `1` |
| `first_release_step` | `623` |
| `final_missiles` | `3` |
| `fire_once_accepted_count` | `1` |
| `fire_once_rejected_count` | `0` |
| `a7_quality_window_step_count` | `109` |
| `policy_event_prob_fire_once_max` | `0.004182533` |
| `policy_event_mode_fire_once_count` | `0` |
| `policy_m3_boundary_cross_count` | `0` |

## Decision

The short train does change the update direction: the online quality-boundary
logit rises monotonically across supported batches instead of being pushed down
with the prewindow logits.

It does not yet change deterministic learned behavior. The deterministic policy
still chooses `hold`, never crosses the event boundary, and times out with all
four missiles. The stochastic policy can sample one authorized release, but the
maximum event probability remains about `0.42%`; this is low-probability
sampling, not a learned deterministic stopping boundary.

The current verdict remains held:

- the dedicated optimizer and deterministic boundary anchor repair the local
  update direction;
- 8k training is insufficient to cross executable deterministic mode;
- the remaining problem is still event-boundary calibration / executable pulse
  transport, not environment reachability or missing support rows.
