# M1 Action Interface Split Acceptance

Status: `2026-06-02`, `accepted`. The accepted scope is the
`air_combat_hybrid_v1` training action interface, HMoE hybrid policy transport,
runtime/proprio wiring and Stage-1 diagnostic reachability. This does not accept
a learned `1v1` policy and does not release M2.

## Accepted Scope

- `air_combat_hybrid_v1` remains a 12D flat `Box` transport, interpreted at the
  policy boundary as continuous flight axes, Bernoulli switches/pulses and a
  categorical weapon selector.
- `tms_up`, `fire_weapon` and `fire_gun` become one-step effective pulses from
  raw policy-intent rising edges.
- `proprio` / `proprio_history` record effective transport actions; raw intent
  is retained only for edge memory.
- HMoE policy uses a hybrid parameter head and preserves joint log-prob while
  SB3 rollout buffers still receive flat actions.
- Stage-1 active `full` / hybrid reactive / hybrid temporal configs are paired.

## Validation Commands

```bash
python -m py_compile gym_envs/universal_env_parts/spaces.py gym_envs/universal_env_parts/actions.py gym_envs/universal_env.py python/env_config.py python/rl/policy_algo/policies.py python/rl/runtime/world_batch_vec_env.py train.py python/training/cli.py tools/diagnostics/air_combat_weapon_employment_process_probe.py tools/eval/eval_utils.py tools/eval/sb3_eval_base.py
# pass

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop pytest -q tests/training/test_training_bootstrap_contracts.py tests/runtime/core/test_air_combat_hybrid_action.py tests/runtime/core/test_env_config.py tests/policy/test_execution_policy_surface.py tests/policy/test_auxiliary_training_updates.py tests/training/test_air_combat_training_entry_contracts.py
# 46 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop pytest -q tests/runtime/air_combat/test_diagnostics_probe_contracts.py tests/training/test_training_bootstrap_contracts.py tests/eval/test_evaluation_cli_contracts.py -k "air_combat or cli or single_eval_builds_world_batch_runtime"
# 4 passed, 7 deselected

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop python train.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json --train_config /tmp/cmo_m1_air_combat_hybrid_smoke_config.json --output_base /tmp/cmo_m1_hybrid_smoke_runs --run_name m1_hybrid_smoke_20260602 --n_envs 1 --torch_threads 1 --seed 20260602
# 32-step hybrid smoke train passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop python train.py --scenario scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json --train_config /tmp/cmo_m1_air_combat_hybrid_smoke_config.json --output_base /tmp/cmo_m1_hybrid_smoke_runs --run_name m1_hybrid_smoke_eval_20260602 --n_envs 1 --torch_threads 1 --seed 20260602 --test_only --resume_path /tmp/cmo_m1_hybrid_smoke_runs/m1_hybrid_smoke_20260602/final_model.zip
# 1000-step hybrid load/predict/step smoke passed
```

## Stage-1 Evidence

Scenario:
`scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json`

Same-seed fixed `range_gate_fire`:

| Config | action_mode | first_fire / release | fire attempts | invalid fire | releases | damage reports | miss distance |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `full` baseline | `full` | `1233 / 1233` | `1` | `0` | `1` | `1` | `8.096 m` |
| hybrid reactive | `air_combat_hybrid_v1` | `1233 / 1233` | `1` | `0` | `1` | `1` | `8.096 m` |

Hybrid short-train deterministic model probe:

| Model | termination | steps | radar / master | fire attempts | releases | invalid fire |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `/tmp/cmo_m1_hybrid_smoke_runs/m1_hybrid_smoke_20260602/final_model.zip` | `failfast_deep_stall` | `421` | `1.0 / 1.0` | `0` | `0` | `0` |

Interpretation:

- Fixed range-gate proves the new action interface can produce an effective
  Stage-1 release and preserves the same release/damage chain as `full`.
- The short-train model only proves the training kernel runs; it still did not
  learn a `fire_weapon` pulse and is not policy acceptance.

## Evidence Artifacts

- Diagnostic JSON:
  `/tmp/cmo_m1_hybrid_range_gate_report.json`
- Baseline JSON:
  `/tmp/cmo_m1_full_range_gate_report.json`
- Short-train model probe:
  `/tmp/cmo_m1_hybrid_smoke_model_probe.json`
- Short-train model:
  `/tmp/cmo_m1_hybrid_smoke_runs/m1_hybrid_smoke_20260602/final_model.zip`

These `/tmp` artifacts are checkpoint evidence, not long-lived repository
model artifacts.

## Open Residuals

- Learned policy weapon-employment acceptance remains open: the short-train
  deterministic model has `fire_attempt_count=0`.
- Follow-on shaping/curriculum or longer training is needed before policy can
  produce intentional fire pulses reliably.
- Repeated-release interval and target-engagement memory remain unsolved; the
  next step routes first through A3 C2/ROE shot policy, pending assessment,
  salvo authorization and reattack authorization before deciding whether the
  residual is still policy memory.
- M2 sequence-native PPO remains held and is not released by this acceptance.

## Forbidden Claims

- Do not claim the learned `1v1` policy is mature or accepted.
- Do not claim temporal windows improved repeated firing.
- Do not claim missile physics, damage, ammo, cooldown or release kernel changed.
- Do not claim tactical memory is solved.

## Synced Indexes

- [README.md](README.md)
- [README.zh.md](README.zh.md)
- [m1_action_interface_split_current_status_20260602.md](m1_action_interface_split_current_status_20260602.md)
- [m1_action_interface_split_task_clusters_20260602.md](m1_action_interface_split_task_clusters_20260602.md)
- [../README.md](../../../task/model/archive/owner_migration_20260808/README.md)
