# A3 C2/ROE Learned-Policy Probe - 2026-06-03

Status: `2026-06-03` local learned-policy evidence and post-launch
mission-observation fix. This record does not accept the learned policy and
does not release M2.

Language:

- English canonical: `a3_c2_roe_learned_policy_probe_20260603.md`
- Chinese companion: [a3_c2_roe_learned_policy_probe_20260603.zh.md](a3_c2_roe_learned_policy_probe_20260603.zh.md)

## Scope

This record follows the A3 P4 process probes with a short learned-policy run
against the S1 C2/ROE scenario/config pair:

- `scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json`
- `examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_shaped_world_batch_probe_v1.json`

The question is whether the current hybrid HMoE policy learns acceptable
single-shot discipline once the C2/ROE contract is observable.

## Training Command

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python train.py \
  --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json \
  --train_config examples/config/training/active/air_combat/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_shaped_world_batch_probe_v1.json \
  --output_base experiments_tmp \
  --run_name a3_c2_roe_hybrid_shaped_32k_20260603 \
  --n_envs 4 \
  --torch_threads 1 \
  --seed 20260603
```

Result:

- completed and saved `experiments_tmp/a3_c2_roe_hybrid_shaped_32k_20260603/final_model.zip`;
- no non-finite report was produced;
- training remained `combat_timeout` dominated;
- final `ep_rew_mean=-690`;
- rollout logs repeatedly warned that no missiles remained, so sampled behavior
  still expended missiles.

## Model Probes

Deterministic final-model probe:

- `combat_timeout=1`;
- `fire_attempt_count=0`;
- `release_count=0`;
- stable flight with radar/master-arm on, but no fire pulse.

Stochastic final-model probe over 3 episodes:

- `combat_timeout=3`;
- `fire_attempt_count=16`;
- `release_count=11`;
- `authorized_release_count=3`;
- `violation_release_count=8`;
- `invalid_fire_attempt_count=5`;
- `damage_report_count=1`.

Per-episode stochastic summary:

| Episode | Attempts | Releases | Authorized | Violations | Invalid attempts | Final missiles | Damage reports |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 4 | 3 | 1 | 2 | 1 | 1 | 1 |
| 1 | 5 | 4 | 1 | 3 | 1 | 0 | 0 |
| 2 | 7 | 4 | 1 | 3 | 3 | 0 | 0 |

## Post-Launch Observation Fix

The learned-policy probe exposed a contract gap: A3 reward/probe
classification could see release count, but policy-facing mission observation
still exposed static `shot_budget_remaining`, `pending_assessment`, and
`own_missiles_in_flight_count` values from `mission_cmd`.

The local fix changes `air_combat_c2_roe_v1` mission observation so it derives
known release count from the current missile deficit and reward-side release
count. After a known single-shot release, the policy observes:

- `shot_budget_remaining=0`;
- `pending_assessment=1`;
- `own_missiles_in_flight_count>=1`.

Focused validation after the fix:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/air_combat/test_air_combat_c2_roe_mission_observation.py \
  tests/runtime/mission/test_mission_obs_taxonomy.py \
  tests/world_batch/test_world_batch_vec_env.py::WorldBatchVecEnvTests::test_world_batch_vec_env_uses_air_combat_c2_roe_python_owned_mission_observation
# 9 passed
```

Post-fix process-probe sanity checks kept the same classification surface:

- `forced_fire`: 1 release, 1 authorized, 0 violations;
- `switch_explore`: 4 releases, 1 authorized, 3 violations.

## Interpretation

A3 succeeds as a classifier: it separates the first authorized shot from later
single-shot policy violations. The learned policy is not accepted: deterministic
behavior does not fire, and stochastic behavior still spends missiles with many
violation releases.

The main action item is to rerun reactive/temporal A3 C2/ROE training after the
dynamic post-launch observation fix. M2 remains held until learned-policy
weapon use improves under this observable contract.
