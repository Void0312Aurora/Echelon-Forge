# A6 Short Learned-Policy Probe

Status: `2026-06-03` completed; A6 engineering path is proven live, but the
first objective contract remains held because deterministic `fire_once` still
argmaxes to `hold`.

Parent: [README.md](README.md). Baseline:
[a6_event_value_first_event_timing_observation_20260603.md](a6_event_value_first_event_timing_observation_20260603.md).

## Scope

This probe checks the first A6 objective contract: masked first-event hazard on
the existing `hold/fire_once` event logit delta, with a bounded curriculum
bootstrap. It does not accept M2, self-play, `2v2`, missile physics, Pk, fuze,
damage authority, or real-world doctrine claims.

Artifacts are under `experiments_tmp/` and must not be staged.

## Fixes Needed Before The Run

The first A6 training attempt exposed two engineering blockers:

- The non-finite probe copied old PPO `collect_rollouts` / `train` logic, so it
  bypassed A6 label attachment and hazard loss.
- The world-batch air-combat path did not merge A5 event-action info back into
  per-step `info`, and `terminal` info mode hid the needed labels.

The accepted engineering correction:

- added A6-aware dict rollout buffers for CPU and device-resident paths;
- attached A6 first-event labels outside policy observations;
- patched the non-finite probe training wrapper to preserve A6 loss and logs;
- made C2/ROE A6 active configs use `step_info_mode=full`;
- aligned `WorldBatchVecEnv` air-combat hybrid actions with
  `UniversalEnv.step()` by applying/finalizing the event-action gate and merging
  event info into step info;
- used the policy-visible event mask from C2/ROE mission observations as the A6
  label window, with runtime `info` only as fallback and accepted-release
  source.

## Training Command

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a6_first_event_hazard_temporal_32k_policymask_20260603 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260628
```

Result:

- Completed `32768` timesteps.
- Final model saved under
  `experiments_tmp/a6_first_event_hazard_temporal_32k_policymask_20260603/final_model.zip`.
- `Rollout buffer: A6FirstEventDeviceDictRolloutBuffer`.
- A6 became live: at `2048` timesteps, `a6/active_count_mean=113`,
  `a6/hazard_loss=0.0113`, `a6/target_positive_frac=0.0175`.
- The bounded curriculum then stopped after one seed per episode; after the
  early window, `a6/active_count_mean` returned to `0`.
- The curriculum coefficient decayed to `0` after the first training quarter.
- Late diagnostics still showed event fire probability near A5 levels:
  at about `30720` timesteps,
  `a6/event_fire_prob_mean_open ~= 0.251%`,
  `pi_event_mode_fire_frac = 0`.

## Probe Commands

Deterministic:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a6_first_event_hazard_temporal_32k_policymask_20260603/final_model.zip \
  --episodes 1 \
  --seed 20260630 \
  --max_steps 2400 \
  --json_out experiments_tmp/a6_first_event_hazard_temporal_32k_policymask_20260603/a6_deterministic_probe.json \
  --csv_out experiments_tmp/a6_first_event_hazard_temporal_32k_policymask_20260603/a6_deterministic_probe.csv
```

Stochastic:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python \
  tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a6_first_event_hazard_temporal_32k_policymask_20260603/final_model.zip \
  --episodes 3 \
  --seed 20260630 \
  --max_steps 2400 \
  --stochastic \
  --json_out experiments_tmp/a6_first_event_hazard_temporal_32k_policymask_20260603/a6_stochastic_probe.json \
  --csv_out experiments_tmp/a6_first_event_hazard_temporal_32k_policymask_20260603/a6_stochastic_probe.csv
```

## Results

| Probe | Episodes | Termination | Fire mask open steps | Fire requests | Accepted | Rejected | Releases | Authorized releases | Violation releases | Repeat / budget violations |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| deterministic | 1 | `combat_timeout=1` | 1840 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| stochastic | 3 | `combat_timeout=3` | 741 | 3 | 3 | 0 | 3 | 3 | 0 | 0 |

Deterministic summary:

| Episode | Fire mask open | A6 open window | Fire event probability mean / max | Event mode-fire count | Requests | Releases |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 1840 | 1840 | `0.247% / 0.248%` | 0 | 0 | 0 |

Stochastic summary:

| Episode | First release step | Fire mask open | Requests | Accepted | Rejected | Releases | Authorized | Violations | Final missiles |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 291 | 280 | 1 | 1 | 0 | 1 | 1 | 0 | 3 |
| 1 | 368 | 302 | 1 | 1 | 0 | 1 | 1 | 0 | 3 |
| 2 | 171 | 159 | 1 | 1 | 0 | 1 | 1 | 0 | 3 |

## Interpretation

A6-EVT-E/F proved the training path is now real: A6 labels are generated, stored
outside policy observations, sampled with PPO minibatches, preserved under the
non-finite probe wrapper, and visible in diagnostics.

The first objective contract is still insufficient. The deterministic policy
again made zero `fire_once` requests despite many open windows. Event
probability remained near `0.25%`, close to the A5 baseline
(`0.217% / 0.278%`). The stochastic probe preserved A5 release discipline:
exactly one authorized release per episode, no rejected requests, no violation
releases, no repeat releases before assessment, and no shot-budget violations.

The residual is therefore no longer an implementation-plumbing failure. It is a
mechanism issue: one early curriculum seed per episode gives a finite A6
gradient, but that signal is too brief to move deterministic event argmax before
the curriculum decays and before accepted-release labels become common.

## Held Outcome

A6 remains held. The recommended next direction is to re-scope the objective,
for example:

- make the first-event hazard provide sustained survival/censoring signal over
  open windows instead of only one early positive seed;
- increase or stage the event-logit curriculum so it affects deterministic
  argmax before decay;
- add an event-value head or advantage-style target for the masked event;
- treat M2/sequence-native modeling as still deferred unless this residual is
  formally voted as the next release blocker.
