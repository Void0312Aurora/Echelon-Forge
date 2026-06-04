# A6 Launch-Window Short Learned-Policy Probe

Status: `2026-06-04` completed; held outcome.

Parent: [README.md](README.md). Contract:
[a6_event_value_first_event_timing_launch_window_timing_contract_20260604.md](a6_event_value_first_event_timing_launch_window_timing_contract_20260604.md).

## Scope

This probe tests the `A6-EVT-L` launch-window timing contract in the maintained
S1 C2/ROE learned-policy path. It compares against `A6-EVT-K`, where the
event-head lane crossed deterministic argmax but released almost immediately
after authorization/contact.

Artifacts live under `experiments_tmp/` and must not be staged.

## Training Command

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_launch_window_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a6_launch_window_temporal_32k_20260604 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260641
```

Result:

- Completed `32768` timesteps.
- Final model:
  `experiments_tmp/a6_launch_window_temporal_32k_20260604/final_model.zip`.
- `Rollout buffer: A6FirstEventDeviceDictRolloutBuffer`.
- Launch-window labels were active:
  `a6/launch_window_enabled=1`,
  `a6/launch_window_prewindow_hold_weight=0.3`.
- Training labels were gated rather than dense:
  `target_positive_frac` alternated between positive-heavy rollouts such as
  `0.86` and all-negative/no-active rollouts such as `0.0`.
- Event-head moved but did not cross by the last logged diagnostics:
  at about `30720` timesteps, `event_logit_delta_mean_open=-2.19`,
  `event_fire_prob_mean_open=0.10`, and `pi_event_mode_fire_frac=0`.

## Probe Commands

Deterministic:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_launch_window_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a6_launch_window_temporal_32k_20260604/final_model.zip \
  --episodes 1 \
  --seed 20260642 \
  --max_steps 2400 \
  --json_out experiments_tmp/a6_launch_window_temporal_32k_20260604/a6_launch_window_deterministic_probe.json \
  --csv_out experiments_tmp/a6_launch_window_temporal_32k_20260604/a6_launch_window_deterministic_probe.csv
```

Stochastic:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_launch_window_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a6_launch_window_temporal_32k_20260604/final_model.zip \
  --episodes 3 \
  --seed 20260642 \
  --max_steps 2400 \
  --stochastic \
  --json_out experiments_tmp/a6_launch_window_temporal_32k_20260604/a6_launch_window_stochastic_probe.json \
  --csv_out experiments_tmp/a6_launch_window_temporal_32k_20260604/a6_launch_window_stochastic_probe.csv
```

## Results

| Probe | Episodes | Termination | Fire requests | Accepted | Rejected | Releases | Authorized releases | Violation releases | Repeat / budget violations |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| deterministic | 1 | `combat_timeout=1` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| stochastic | 3 | `combat_timeout=3` | 3 | 3 | 0 | 3 | 3 | 0 | 0 |

Deterministic summary:

| Episode | First contact | First release | Open-window event probability mean / max | Mode-fire count | Final missiles |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 1 | none | `34.6% / 35.0%` | 0 | 4 |

Stochastic summary:

| Episode | First contact | First release | Requests | Accepted | Rejected | Releases | Authorized | Violations | Final missiles |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 1 | 7 | 1 | 1 | 0 | 1 | 1 | 0 | 3 |
| 1 | 41 | 43 | 1 | 1 | 0 | 1 | 1 | 0 | 3 |
| 2 | 1 | 4 | 1 | 1 | 0 | 1 | 1 | 0 | 3 |

## Interpretation

The launch-window contract is live and it changed the learned-policy behavior.
Unlike `A6-EVT-K`, deterministic mode no longer fires immediately after
authorization/contact. The event probability still moved substantially: the
deterministic probe reports `34.6% / 35.0%` open-window fire probability, but
the masked argmax stayed on `hold`.

The result is not A6 acceptance. Stochastic probing still samples early
authorized releases at steps `7`, `43`, and `4`. This is slightly later than the
`A6-EVT-K` stochastic steps `4`, `42`, and `2`, but it does not demonstrate the
intended quality-window timing. The contract therefore suppresses deterministic
early fire, but the current 32k/weight/window setting does not yet create a
stable learned timing policy.

## Held Outcome

`A6-EVT-M` is completed as evidence, but A6 remains held.

Recommended next direction:

- keep A3/A5 legality unchanged;
- keep M2 held;
- follow
  [root-cause re-scope](a6_event_value_first_event_timing_root_cause_rescope_20260604.md):
  pause L parameter tuning and define an `A6-EVT-O` counterfactual event-time
  objective before more training.
