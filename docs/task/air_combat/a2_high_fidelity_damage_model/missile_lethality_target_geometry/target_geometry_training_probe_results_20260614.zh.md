# TG-P7-R4 active training probe 结果

状态：`2026-06-14` pass as active 8k proxy-versus-baseline training smoke。
两个维护中的 `WorldBatchVecEnv` 探针均完成训练并写出 checkpoint。

英文辅文：
[target_geometry_training_probe_results_20260614.md](target_geometry_training_probe_results_20260614.md)。

## 运行内容

Proxy run：

```bash
PYTHONPATH=build-workshop:. timeout 1800 python train.py --scenario scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_v1.json --output_base /tmp/cmo_tg_p7_active_probe --run_name tg_p7_proxy_8k_20260614
```

Baseline run：

```bash
PYTHONPATH=build-workshop:. timeout 1800 python train.py --scenario scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json --train_config examples/config/training/active/air_combat/air_combat_1v1_f16c_scripted_red_world_batch_probe_8k_v1.json --output_base /tmp/cmo_tg_p7_active_probe --run_name tg_p7_baseline_8k_20260614
```

## 结果

| Probe | Database path | Timesteps | Device | Final `ep_len_mean` | Final `ep_rew_mean` | Final `approx_kl` | Final model |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- |
| TG-P7 proxy | `target_geometry_training_proxy_database_20260613` | `8192` | `cuda` | `662` | `-282` | `0.000507` | `/tmp/cmo_tg_p7_active_probe/tg_p7_proxy_8k_20260614/final_model.zip` |
| Baseline | default database | `8192` | `cuda` | `677` | `-235` | `0.000661` | `/tmp/cmo_tg_p7_active_probe/tg_p7_baseline_8k_20260614/final_model.zip` |

两次运行都使用 `DeviceDictRolloutBuffer`，都完成 `8192` timesteps，均写出
`model_2048_steps.zip`、`model_4096_steps.zip`、`model_6144_steps.zip`、
`model_8192_steps.zip` 和 `final_model.zip`。

Proxy run 打印了解析后的 `World batch database` 绝对路径，指向
`target_geometry_training_proxy_database_20260613`；baseline run 没有打印
database override，因此仍在默认 database 上。

## 解释

这证明 TG-P7 proxy database 能进入维护中的 active training surface，并完成与
baseline 相同的 8k world-batch probe。它不证明 proxy 更强，也不替换默认 damage model。

Damage-component selection 的 authority 仍来自 R3 database gate：proxy 路径有
`32` 个 F-16 components，其中 `8` 个是 split receivers；默认路径保持 `26`
components。训练日志证明 runtime 稳定性和入口选择，不证明武器杀伤率或真实工程几何。

## 下一步

后续已完成 targeted damage-event trace 和 32k proxy/baseline maintained training comparison：
[target_geometry_damage_event_trace_results_20260614.zh.md](target_geometry_damage_event_trace_results_20260614.zh.md)、
[target_geometry_training_probe_32k_results_20260614.zh.md](target_geometry_training_probe_32k_results_20260614.zh.md)。
下一步转入 split-receiver exposure 的下游 policy/reward 诊断，或选择更能激活 combat actions 的训练入口。
