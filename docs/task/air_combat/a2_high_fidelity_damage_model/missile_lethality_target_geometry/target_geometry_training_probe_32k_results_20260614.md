# TG-P7-R6 32k Opt-In Training Probe Results

Status: `2026-06-14` pass as a 32k proxy-versus-baseline maintained
`WorldBatchVecEnv` training probe. Both proxy and baseline runs completed
`32768` CUDA timesteps and wrote complete checkpoints plus final models.

Chinese canonical:
[target_geometry_training_probe_32k_results_20260614.zh.md](target_geometry_training_probe_32k_results_20260614.zh.md).

## What Ran

Proxy run:

```bash
PYTHONPATH=build-workshop:. timeout 3600 python train.py --scenario scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_32k_v1.json --output_base /tmp/cmo_tg_p7_r6_32k_probe --run_name tg_p7_proxy_32k_20260614
```

Baseline run:

```bash
PYTHONPATH=build-workshop:. timeout 3600 python train.py --scenario scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_f16c_scripted_red_world_batch_probe_32k_v1.json --output_base /tmp/cmo_tg_p7_r6_32k_probe --run_name tg_p7_baseline_32k_20260614
```

Generated evidence:

- [target_geometry_training_probe_32k_20260614.json](review_packets/f16c_20260611/target_geometry_training_probe_32k_20260614.json)
- [air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_32k_v1.json](/home/void0312/Workshop/CMO/examples/config/training/active/air_combat/air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_32k_v1.json)
- [air_combat_1v1_f16c_scripted_red_world_batch_probe_32k_v1.json](/home/void0312/Workshop/CMO/examples/config/training/active/air_combat/air_combat_1v1_f16c_scripted_red_world_batch_probe_32k_v1.json)

## Result

| Probe | Database path | Timesteps | Final `ep_len_mean` | Final `ep_rew_mean` | Final `approx_kl` | Final model |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| TG-P7 proxy 32k | `target_geometry_training_proxy_database_20260613` | `32768` | `619.00` | `-401.05` | `0.000469` | `/tmp/cmo_tg_p7_r6_32k_probe/tg_p7_proxy_32k_20260614/final_model.zip` |
| Baseline 32k | default database | `32768` | `609.02` | `-271.04` | `0.000063` | `/tmp/cmo_tg_p7_r6_32k_probe/tg_p7_baseline_32k_20260614/final_model.zip` |

Both runs wrote:

- `model_8192_steps.zip`
- `model_16384_steps.zip`
- `model_24576_steps.zip`
- `model_32768_steps.zip`
- `final_model.zip`

The proxy run config backup retains `runtime.database_path` and
`A2_TARGET_GEOMETRY_PROXY_F16C_R22` metadata. The baseline config backup has no
database override and no `target_geometry_proxy` metadata. Neither run emitted
`nonfinite_probe_report.json`.

## Diagnostic Boundary

In the final diagnostics window, both proxy and baseline report
`action_fire_weapon_frac`, `action_master_arm_frac`, and
`action_radar_active_frac` as `0.0`. R6 is therefore evidence for longer
training entrypoint stability and same-budget comparison, not proof of learned
weapon employment, proxy superiority, or default-path replaceability.

The proxy 32k final reward is lower than the baseline 32k final reward. That is
recorded only as a same-budget diagnostic fact; the scripted-red full-action
surface is still mostly exposing flight-stability and termination-window issues.

## Next Step

TG-P7 now has an opt-in proxy database, active 8k probe, targeted damage-event
trace, and 32k proxy/baseline comparison. The next work should move into
downstream policy/reward diagnostics for split-receiver damage-event exposure,
or continue training on a scenario/action interface that actually activates
combat actions. Default database replacement remains a separate acceptance gate.
