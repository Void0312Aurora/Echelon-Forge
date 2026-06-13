# TG-P7-R6 32k opt-in 训练探针结果

状态：`2026-06-14` pass as 32k proxy-versus-baseline maintained
`WorldBatchVecEnv` training probe。Proxy 和 baseline 都完成 `32768` CUDA
timesteps，并写出完整 checkpoint 和 final model。

英文辅文：
[target_geometry_training_probe_32k_results_20260614.md](target_geometry_training_probe_32k_results_20260614.md)。

## 执行内容

Proxy run：

```bash
PYTHONPATH=build-workshop:. timeout 3600 python train.py --scenario scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_32k_v1.json --output_base /tmp/cmo_tg_p7_r6_32k_probe --run_name tg_p7_proxy_32k_20260614
```

Baseline run：

```bash
PYTHONPATH=build-workshop:. timeout 3600 python train.py --scenario scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_f16c_scripted_red_world_batch_probe_32k_v1.json --output_base /tmp/cmo_tg_p7_r6_32k_probe --run_name tg_p7_baseline_32k_20260614
```

生成证据：

- [target_geometry_training_probe_32k_20260614.json](review_packets/f16c_20260611/target_geometry_training_probe_32k_20260614.json)
- [air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_32k_v1.json](/home/void0312/Workshop/CMO/examples/config/training/active/air_combat/air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_32k_v1.json)
- [air_combat_1v1_f16c_scripted_red_world_batch_probe_32k_v1.json](/home/void0312/Workshop/CMO/examples/config/training/active/air_combat/air_combat_1v1_f16c_scripted_red_world_batch_probe_32k_v1.json)

## 结果

| Probe | Database path | Timesteps | Final `ep_len_mean` | Final `ep_rew_mean` | Final `approx_kl` | Final model |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| TG-P7 proxy 32k | `target_geometry_training_proxy_database_20260613` | `32768` | `619.00` | `-401.05` | `0.000469` | `/tmp/cmo_tg_p7_r6_32k_probe/tg_p7_proxy_32k_20260614/final_model.zip` |
| Baseline 32k | default database | `32768` | `609.02` | `-271.04` | `0.000063` | `/tmp/cmo_tg_p7_r6_32k_probe/tg_p7_baseline_32k_20260614/final_model.zip` |

两次运行均写出：

- `model_8192_steps.zip`
- `model_16384_steps.zip`
- `model_24576_steps.zip`
- `model_32768_steps.zip`
- `final_model.zip`

Proxy run 的 config backup 保留 `runtime.database_path` 和
`A2_TARGET_GEOMETRY_PROXY_F16C_R22` 元数据；baseline config backup 没有
database override，也没有 `target_geometry_proxy` 元数据。两条 run 都没有生成
`nonfinite_probe_report.json`。

## 诊断边界

最终 diagnostics window 中，proxy 与 baseline 的
`action_fire_weapon_frac`、`action_master_arm_frac` 和 `action_radar_active_frac`
均为 `0.0`。这说明 R6 是“更长训练入口稳定性 + 同预算对照”证据，不是武器策略已经学会、
proxy 更强或默认路径可替换的证明。

Proxy 32k 的 final reward 低于 baseline 32k。该差异只记录为同预算诊断事实，不作为几何代理
优劣结论；scripted-red full-action surface 仍主要暴露飞控稳定性和终止窗口问题。

## 下一步

TG-P7 已经具备 opt-in proxy database、active 8k probe、targeted damage-event trace
和 32k proxy/baseline 对照。归档收口后，本页只作为下游 handoff evidence 保留；policy/reward
诊断、训练入口调整和默认 database 替换不再作为本几何子项目的下一步。
