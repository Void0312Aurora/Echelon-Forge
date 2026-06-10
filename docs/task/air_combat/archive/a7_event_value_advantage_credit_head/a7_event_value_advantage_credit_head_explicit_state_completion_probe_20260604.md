# A7 Explicit State Completion Probe

Status: `2026-06-04` pass; held learned-policy outcome.

Parent: [README.md](README.md).

## Purpose

This slice tested the pre-M2 hypothesis that A7/R remained held because the
policy could not observe enough state to infer the first-shot quality window.
The key suspected gap was `temporal_history_len=16` versus
`a7_event_credit_legal_open_quality_min_window_age_steps=32`, with no explicit
legal-open age, launch-window readiness, or quality-window readiness fields in
`air_combat_c2_roe_v1`.

The experiment added `air_combat_c2_roe_v2` as a compatible, explicit
state-completed observation contract. It preserves v1 and A3/A5 masks while
adding current, non-future-leaking fields:

- `fire_mask_open`
- `launch_window_open`
- `quality_window_ready`
- `legal_open_age_steps` / `legal_open_age_norm`
- `launch_window_age_steps` / `launch_window_age_norm`
- `target_range_m`
- `target_track_age_s`

## Implementation

Code/config surfaces:

- `python/mission_obs_taxonomy.py`: adds `air_combat_c2_roe_v2` with a 29D
  mission layout.
- `gym_envs/scenario_loader/mission_observation.py`: builds explicit legal,
  launch-window, age, target-range, and track-age fields; age counters are keyed
  by loader step to avoid multiple reads inflating age.
- `gym_envs/universal_env_parts/air_combat_event_action.py` and
  `gym_envs/scenario_loader/loading.py`: reset state-completion age counters at
  episode/scenario boundaries.
- `python/rl/policy_algo/policies.py`,
  `python/rl/policy_algo/hmoe_routing.py`,
  `python/rl/policy_algo/ppo_adaptive_kl.py`, and
  `python/rl/policy_algo/first_event_projection.py`: consume v1/v2 layouts by
  taxonomy field names instead of hard-coded 20D checks.
- `python/models/transformer.py`: adds air-combat C2/ROE mission preprocessing
  so explicit age/range fields enter the Transformer at sane scales.
- `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_state_completed_world_batch_probe_v1.json`:
  copies the maintained A7/R config and changes only
  `env.mission_obs_mode` from `air_combat_c2_roe_v1` to
  `air_combat_c2_roe_v2`.

## Validation

Focused contract tests:

```bash
pytest tests/runtime/mission/test_mission_obs_taxonomy.py \
  tests/runtime/air_combat/test_air_combat_c2_roe_mission_observation.py \
  tests/policy/test_routing_contracts.py \
  tests/policy/test_execution_policy_surface.py \
  tests/policy/test_auxiliary_training_updates.py \
  tests/policy/test_first_event_timing_contracts.py \
  tests/training/test_event_timing_training_config_contracts.py \
  tests/training/test_air_combat_training_entry_contracts.py -q
```

Observed: `105 passed in 27.58s`.

Whitespace gate:

```bash
git diff --check
```

Observed: pass.

## Learned Probe

Training command:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_state_completed_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a7_state_completed_opportunity_32k_20260604_r1 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260711
```

Observed: completed `32768` steps and saved
`experiments_tmp/a7_state_completed_opportunity_32k_20260604_r1/final_model.zip`.

Key train observations:

- Early in training, `LEGAL_OPEN_QUALITY` positives became visible quickly:
  `a7/evc_src_legal_open_quality_count_mean=225` at `3072` steps with
  advantage about `-0.153`.
- Mid-run, legal-open quality positives were often dense
  (`410` to `450` per rollout), but event-credit advantage remained negative.
- Final rollout kept `LEGAL_OPEN_QUALITY` live
  (`count_mean=330`, `positive_count_mean=330`,
  `target_positive_frac=0.645`), but event-credit advantage was still about
  `-0.924`.
- Open-window event fire probability rose to about `0.305`, but deterministic
  event mode stayed `hold`.

Deterministic probe:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_state_completed_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a7_state_completed_opportunity_32k_20260604_r1/final_model.zip \
  --episodes 4 \
  --seed 20260711 \
  --max_steps 600 \
  --json_out experiments_tmp/a7_state_completed_opportunity_32k_20260604_r1/probe_deterministic.json \
  --csv_out experiments_tmp/a7_state_completed_opportunity_32k_20260604_r1/probe_deterministic.csv
```

Observed deterministic summary:

- `0` fire requests, `0` accepted releases, `0` violations, `0` repeats.
- Fire mask was open for `[599, 559, 599, 599]` steps across the 4 episodes.
- Authorized-window event-fire probability mean: `0.2634`.
- Quality-window A7 advantage mean: `-0.8534`.
- Pre-window A7 advantage mean: `-0.8571`.

Stochastic probe:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/diagnostics/air_combat_stage0_process_probe.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_state_completed_world_batch_probe_v1.json \
  --mode model \
  --model experiments_tmp/a7_state_completed_opportunity_32k_20260604_r1/final_model.zip \
  --episodes 8 \
  --seed 20260711 \
  --max_steps 600 \
  --stochastic \
  --json_out experiments_tmp/a7_state_completed_opportunity_32k_20260604_r1/probe_stochastic.json \
  --csv_out experiments_tmp/a7_state_completed_opportunity_32k_20260604_r1/probe_stochastic.csv
```

Observed stochastic summary:

- `8` fire requests, `8` accepted releases, `8` release executions.
- `0` unauthorized/violation releases, `0` repeat releases, `0` shot-budget
  violations.
- Release steps: `[6, 42, 4, 2, 5, 46, 3, 46]`.
- Releases remain early and mostly pre-quality-window; quality-window
  advantage is not recovered.

## Conclusion

Explicit state completion improves the observation contract and makes the
window state physically visible to the policy. It also raises open-window
event-fire probability compared with earlier held probes.

It is not the root-cause fix. The model still learns a negative
`Q_fire_once - Q_hold` advantage on both pre-window and quality-window rows,
and deterministic mode remains `hold` despite hundreds of legal-open positive
rows in training. The next slice should not be another coefficient run. It
should isolate why positive labels/value credit are converted into a negative
event advantage and why event-logit coupling follows that negative advantage.

## Next Step

Open the next bounded investigation as a structural value/policy coupling
audit. M2 remains plausible, but this probe shows the immediate failure is not
simply "the policy cannot see the window age"; the learned value/advantage
object itself is still wrong or coupled in the wrong direction.
