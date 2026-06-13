# TG-P7-R4 Active Training Probe Results

Status: `2026-06-14` pass as active 8k proxy-versus-baseline training smoke.
Both maintained `WorldBatchVecEnv` probes completed and wrote checkpoints.

Chinese canonical:
[target_geometry_training_probe_results_20260614.zh.md](target_geometry_training_probe_results_20260614.zh.md).

## What Ran

Proxy run:

```bash
PYTHONPATH=build-workshop:. timeout 1800 python train.py --scenario scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_v1.json --output_base /tmp/cmo_tg_p7_active_probe --run_name tg_p7_proxy_8k_20260614
```

Baseline run:

```bash
PYTHONPATH=build-workshop:. timeout 1800 python train.py --scenario scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_f16c_scripted_red_world_batch_probe_8k_v1.json --output_base /tmp/cmo_tg_p7_active_probe --run_name tg_p7_baseline_8k_20260614
```

## Result

| Probe | Database path | Timesteps | Device | Final `ep_len_mean` | Final `ep_rew_mean` | Final `approx_kl` | Final model |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- |
| TG-P7 proxy | `target_geometry_training_proxy_database_20260613` | `8192` | `cuda` | `662` | `-282` | `0.000507` | `/tmp/cmo_tg_p7_active_probe/tg_p7_proxy_8k_20260614/final_model.zip` |
| Baseline | default database | `8192` | `cuda` | `677` | `-235` | `0.000661` | `/tmp/cmo_tg_p7_active_probe/tg_p7_baseline_8k_20260614/final_model.zip` |

Both runs used `DeviceDictRolloutBuffer`, completed `8192` timesteps, emitted
`model_2048_steps.zip`, `model_4096_steps.zip`, `model_6144_steps.zip`,
`model_8192_steps.zip`, and saved `final_model.zip`.

The proxy run printed the resolved absolute `World batch database` path for
`target_geometry_training_proxy_database_20260613`; the baseline run did not
print a database override and therefore remained on the default database.

## Interpretation

This proves the TG-P7 proxy database can enter the maintained active training
surface and complete the same 8k world-batch probe as the baseline. It does not
prove the proxy is better, and it does not replace the default damage model.

Damage-component selection authority still comes from the R3 database gate:
proxy path has `32` F-16 components with `8` split receivers, while default path
remains at `26` components. The training logs prove runtime stability and
entrypoint selection, not weapon lethality or true engineering geometry.

## Next Step

Targeted damage-event trace and the 32k proxy/baseline maintained training
comparison have since completed:
[target_geometry_damage_event_trace_results_20260614.md](target_geometry_damage_event_trace_results_20260614.md),
[target_geometry_training_probe_32k_results_20260614.md](target_geometry_training_probe_32k_results_20260614.md).
After closeout, this page is retained only as downstream handoff evidence.
Policy/reward diagnostics, training-entry adjustments, and default database
replacement are no longer next steps for this geometry subproject.
