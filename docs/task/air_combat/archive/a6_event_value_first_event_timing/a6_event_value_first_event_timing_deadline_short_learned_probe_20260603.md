# A6 Deadline-Bootstrap Short Learned-Policy Probe

Status: `2026-06-03` completed; held outcome.

Parent: [README.md](README.md). Re-scope note:
[a6_event_value_first_event_timing_deadline_bootstrap_rescope_20260603.md](a6_event_value_first_event_timing_deadline_bootstrap_rescope_20260603.md).

## Scope

This probe tests the deadline-bootstrap wave after the first A6
hazard/curriculum contract stayed held. It does not accept M2, self-play,
`2v2`, missile physics, Pk, fuze, damage authority, or real-world tactics.

Experiment artifacts are under `experiments_tmp/` and must not be staged.

## Training Command

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a6_deadline_bootstrap_temporal_32k_20260603 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260629
```

Result:

- Completed `32768` timesteps.
- Final model:
  `experiments_tmp/a6_deadline_bootstrap_temporal_32k_20260603/final_model.zip`.
- `Rollout buffer: A6FirstEventDeviceDictRolloutBuffer`.
- Deadline knobs were active: `a6/curriculum_coef=0`,
  `a6/deadline_weight=1`, `a6/hazard_coef=0.3`.
- Early training showed real deadline labels:
  `2048` timesteps had `a6/active_count_mean=238`,
  `a6/target_positive_frac=0.812`, `a6/hazard_loss=1.46`.
- Mid/late deadline windows showed sustained positives:
  around `16384` timesteps `active_count_mean=386`,
  `target_positive_frac=1`, `hazard_loss=1.74`;
  around `30720` timesteps open-window event probability was
  `0.45%` and mode-fire remained `0`.
- Final train log still had `active_count_mean=386`,
  `target_positive_frac=1`, and `hazard_loss=1.6`.

## Probe Commands

Deterministic:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a6_deadline_bootstrap_temporal_32k_20260603/final_model.zip \
  --episodes 1 \
  --seed 20260630 \
  --max_steps 2400 \
  --json_out experiments_tmp/a6_deadline_bootstrap_temporal_32k_20260603/a6_deadline_deterministic_probe.json \
  --csv_out experiments_tmp/a6_deadline_bootstrap_temporal_32k_20260603/a6_deadline_deterministic_probe.csv
```

Stochastic:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a6_deadline_bootstrap_temporal_32k_20260603/final_model.zip \
  --episodes 3 \
  --seed 20260630 \
  --max_steps 2400 \
  --stochastic \
  --json_out experiments_tmp/a6_deadline_bootstrap_temporal_32k_20260603/a6_deadline_stochastic_probe.json \
  --csv_out experiments_tmp/a6_deadline_bootstrap_temporal_32k_20260603/a6_deadline_stochastic_probe.csv
```

## Results

| Probe | Episodes | Termination | Fire mask open steps | Fire requests | Accepted | Rejected | Releases | Authorized releases | Violation releases | Repeat / budget violations |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| deterministic | 1 | `combat_timeout=1` | 1840 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| stochastic | 3 | `combat_timeout=3` | 1239 | 4 | 3 | 1 | 3 | 3 | 0 | 0 |

Deterministic summary:

| Episode | Fire mask open | A6 open window | Fire event probability mean / max | Event mode-fire count | Requests | Releases |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 1840 | 1840 | `0.494% / 0.496%` | 0 | 0 | 0 |

Stochastic summary:

| Episode | First release step | Fire mask open | Requests | Accepted | Rejected | Rejected reason | Releases | Authorized | Violations | Final missiles |
| ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 0 | 508 | 487 | 2 | 1 | 1 | `weapon_not_ready=1` | 1 | 1 | 0 | 3 |
| 1 | 572 | 509 | 1 | 1 | 0 | `{}` | 1 | 1 | 0 | 3 |
| 2 | 259 | 243 | 1 | 1 | 0 | `{}` | 1 | 1 | 0 | 3 |

## Interpretation

Deadline bootstrap is connected and produces sustained positive labels. It also
moves the event probability: deterministic open-window mean rose from the first
A6 run's `0.247%` to `0.494%`. However, this is still far below the masked
deterministic `fire_once` argmax threshold, and the deterministic probe remains
at `0` requests.

The stochastic behavior still produces one authorized release in every episode
and preserves zero violation releases, zero repeat releases, and zero shot-budget
violations. It regresses on the stricter no-rejected-request discipline because
episode 0 produced one extra `weapon_not_ready` rejected request before the
accepted release.

Therefore the deadline wave remains held. The blocker is no longer label
plumbing. The next investigation should inspect event-head update strength and
optimizer routing: deadline positives are present, but the event logit only
moves from about `-5.9` to about `-5.3`, not toward positive argmax.

## Held Outcome

A6 is still not accepted.

Recommended next directions:

- audit event-head learning-rate scale, grouped optimizer treatment, KL/clip
  limits, and HMoE residual/head warmup for the `fire_once` event logits;
- add a focused gradient/update probe showing how many optimizer steps are
  required for deadline positives to move event-logit delta from about `-5.3`
  toward `0`;
- consider an explicit event-value / advantage head only after the event-head
  update-strength audit, so architecture risk is separated from optimizer
  blockage;
- keep M2 held unless this narrower event-head evidence proves sequence-native
  modeling is the actual release blocker.
