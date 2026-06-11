# A6 Event-Head Short Learned-Policy Probe

Status: `2026-06-03` completed; held timing residual.

Parent: [README.md](README.md). Event-head lane:
[a6_event_value_first_event_timing_event_head_optimization_lane_20260603.md](a6_event_value_first_event_timing_event_head_optimization_lane_20260603.md).

## Scope

This probe tests whether the dedicated `hybrid_event_head` optimizer lane can
move the masked `hold/fire_once` event decision in the full S1 C2/ROE learned
policy. It does not accept M2, self-play, `2v2`, missile physics, Pk, fuze,
damage authority, or real-world tactics.

Experiment artifacts are under `experiments_tmp/` and must not be staged.

## Training Command

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a6_event_head_temporal_32k_20260603 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260631
```

Result:

- Completed `32768` timesteps.
- Final model:
  `experiments_tmp/a6_event_head_temporal_32k_20260603/final_model.zip`.
- `Rollout buffer: A6FirstEventDeviceDictRolloutBuffer`.
- Event-head lane was active:
  `a6/event_head_enabled=1`, `a6/event_head_lr_scale=10`.
- Mid-run diagnostics showed the lane was no longer update-starved:
  around `20480` timesteps, `event_head_delta_fire_mean=1.94`,
  `event_logit_delta_mean_open=-1.68`, and open-window fire probability was
  about `15.7%`.
- Around `30720` timesteps the deterministic event row crossed:
  `event_head_delta_fire_mean=3.03`, `event_logit_delta_mean_open=0.747`,
  open-window fire probability about `67.9%`, and
  `pi_event_mode_fire_frac=1`.
- Final train log still had `active_count_mean=386`,
  `target_positive_frac=1`, and `hazard_loss=0.0856`.

## Probe Commands

Deterministic:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a6_event_head_temporal_32k_20260603/final_model.zip \
  --episodes 1 \
  --seed 20260632 \
  --max_steps 2400 \
  --json_out experiments_tmp/a6_event_head_temporal_32k_20260603/a6_event_head_deterministic_probe.json \
  --csv_out experiments_tmp/a6_event_head_temporal_32k_20260603/a6_event_head_deterministic_probe.csv
```

Stochastic:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_weapon_employment_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a6_event_head_temporal_32k_20260603/final_model.zip \
  --episodes 3 \
  --seed 20260632 \
  --max_steps 2400 \
  --stochastic \
  --json_out experiments_tmp/a6_event_head_temporal_32k_20260603/a6_event_head_stochastic_probe.json \
  --csv_out experiments_tmp/a6_event_head_temporal_32k_20260603/a6_event_head_stochastic_probe.csv
```

## Results

| Probe | Episodes | Termination | Fire requests | Accepted | Rejected | Releases | Authorized releases | Violation releases | Repeat / budget violations |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| deterministic | 1 | `combat_timeout=1` | 1 | 1 | 0 | 1 | 1 | 0 | 0 |
| stochastic | 3 | `combat_timeout=3` | 3 | 3 | 0 | 3 | 3 | 0 | 0 |

Deterministic summary:

| Episode | First contact | First authorization | First release | Fire-event max probability | Mode-fire count | Final missiles |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 1 | 0 | 2 | `72.8%` | 1 | 3 |

Stochastic summary:

| Episode | First contact | First release | Requests | Accepted | Rejected | Releases | Authorized | Violations | Final missiles |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 1 | 4 | 1 | 1 | 0 | 1 | 1 | 0 | 3 |
| 1 | 41 | 42 | 1 | 1 | 0 | 1 | 1 | 0 | 3 |
| 2 | 1 | 2 | 1 | 1 | 0 | 1 | 1 | 0 | 3 |

## Interpretation

The event-head lane fixes the narrow update-strength blocker from `A6-EVT-J`.
Unlike the deadline baseline, the deterministic learned policy now crosses the
masked event argmax and executes one accepted authorized release. Stochastic
probing also preserves the A5 release-discipline invariant: one request, one
accepted release, no rejected requests, no violation releases, no repeat
release, and no shot-budget violation in each episode.

This is not full A6 acceptance. The learned behavior collapses toward immediate
release after authorization/contact: deterministic release occurs at step `2`,
and stochastic release steps are `4`, `42`, and `2`. The A6 deadline/open-window
diagnostics become mostly vacated after the early release, so the learned policy
does not prove a mature first-event timing model. It proves the event decision
can now be trained, then exposes a higher-level timing-quality problem.

## Held Outcome

`A6-EVT-K` is complete as evidence, but A6 remains held.

The next bounded direction should not be another raw LR increase. It should
define an engagement-quality or launch-window contract that separates
authorization from good release timing, while keeping A3/A5 masks and
state-machine suppression authoritative.
