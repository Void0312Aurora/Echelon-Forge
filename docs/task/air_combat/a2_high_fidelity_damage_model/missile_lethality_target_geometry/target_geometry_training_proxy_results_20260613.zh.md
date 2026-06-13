# TG-P7-R3 训练代理数据库结果

状态：`2026-06-13` pass as opt-in training proxy database plus local
64-step training smoke；默认 F-16 unit database 仍未改变。

英文辅文：
[target_geometry_training_proxy_results_20260613.md](target_geometry_training_proxy_results_20260613.md)。

## 本轮变更

TG-P7-R3 将 TG-P7-R2 的内存投影固化成可显式选择的训练代理数据库。生成器会复制维护中的
runtime database，只替换代理副本中的 `aircraft/units/f16c_block50.json`，并保持
[f16c_block50.json](/home/void0312/Workshop/CMO/examples/config/database/aircraft/units/f16c_block50.json)
不变。

新增产物：

- [target_geometry_training_proxy_database_20260613.json](review_packets/f16c_20260611/target_geometry_training_proxy_database_20260613.json)
- [target_geometry_training_proxy_database_20260613/](review_packets/f16c_20260611/target_geometry_training_proxy_database_20260613/)
- [target_geometry_training_proxy_database_20260613/aircraft/units/f16c_block50.json](review_packets/f16c_20260611/target_geometry_training_proxy_database_20260613/aircraft/units/f16c_block50.json)
- [air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_v1.json](/home/void0312/Workshop/CMO/examples/config/training/active/air_combat/air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_v1.json)
- [scene.html](review_packets/f16c_20260611/scene.html) 已新增
  `TG-P7 Training Proxy Database` section。

Runtime wiring：

- `runtime.database_path` 会在 training bootstrap 阶段解析并校验。
- `train.py` 会把解析后的路径传给 `WorldBatchVecEnv` 与
  `CooperativeWorldBatchVecEnv`。
- active TG-P7 proxy config 显式选择代理数据库；baseline configs 继续使用
  `examples/config/database`。

## 验收门

| Gate | Result |
| --- | --- |
| 默认数据库 component count | `26` |
| 代理数据库 component count | `32` |
| component count delta | `6` |
| 已退役父级 components | `2` |
| split receiver components | `8` |
| 默认 runtime active split receivers | `0` |
| 代理 runtime active split receivers | `8` |
| duplicate component names | `0` |
| behavior regression pass | `true` |
| proxy database materialized | `true` |
| training database path ready | `true` |
| repository unit database modified | `false` |
| Runtime database loader smoke | `true` |
| 本地 64-step CPU training smoke | `true` |

## 边界

这是初始训练代理，不是真实 F-16 工程几何声明。feature flag 是
`A2_TARGET_GEOMETRY_PROXY_F16C_R22`，目标路径是
`damage_model.hitboxes[].components`，训练 opt-in key 是
`runtime.database_path`。

默认 runtime projection 和维护中的 unit database 仍是对照路径。该代理已经可以作为
geometry-informed initial agent 进入短训练/runtime probe；Pk、真实弹种校准、结构解体和残骸仍不属于本子项目。

## 下一步

TG-P7-R4 已运行维护中的 active 8k TG-P7 proxy probe 和匹配的 baseline world-batch probe：
[target_geometry_training_probe_results_20260614.zh.md](target_geometry_training_probe_results_20260614.zh.md)。
TG-P7-R5 也已完成 targeted damage-event trace，并在 proxy event names 中观测到全部
`8` 个 split receivers：
[target_geometry_damage_event_trace_results_20260614.zh.md](target_geometry_damage_event_trace_results_20260614.zh.md)。
TG-P7-R6 已完成 32k proxy/baseline maintained training comparison：
[target_geometry_training_probe_32k_results_20260614.zh.md](target_geometry_training_probe_32k_results_20260614.zh.md)。

## 验证

```bash
python -m py_compile tools/geometry/airframe_geometry_review.py python/training/bootstrap.py train.py tests/tools/test_airframe_geometry_review.py tests/training/test_training_bootstrap_contracts.py tests/training/test_air_combat_training_entry_contracts.py
pytest -q tests/tools/test_airframe_geometry_review.py
pytest -q tests/training/test_training_bootstrap_contracts.py tests/training/test_air_combat_training_entry_contracts.py
python tools/geometry/airframe_geometry_review.py --out docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_20260611
cmake --build build-workshop --target ef_test -j2
./build-workshop/ef_test --test-suite=components_basic
PYTHONPATH=build-workshop:. python - <<'PY'
from pathlib import Path
import ef_py

proxy_db = Path("docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_20260611/target_geometry_training_proxy_database_20260613")
ef_py.RuntimeFacade(1).load_database(str(proxy_db))
print({"runtime_load_ok": True, "proxy_db": str(proxy_db)})
PY
git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry tools/geometry/airframe_geometry_review.py python/training/bootstrap.py train.py tests/tools/test_airframe_geometry_review.py tests/training/test_training_bootstrap_contracts.py tests/training/test_air_combat_training_entry_contracts.py examples/config/training/active/air_combat
```

当前聚焦结果：geometry review tests `2 passed`；training bootstrap 和 entry
contracts `28 passed`；C++ loader smoke `24 passed`；runtime database load 返回
`runtime_load_ok=true`。

本地训练烟测：

```bash
PYTHONPATH=build-workshop:. python train.py --scenario scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json --train_config /tmp/cmo_tg_p7_proxy_training_smoke_config.json --output_base /tmp/cmo_tg_p7_proxy_train_smoke --run_name tg_p7_proxy_train_smoke_64 --n_envs 1
```

临时 config 保留 active proxy database path，但把训练缩短为 `64` 个 CPU timesteps。结果：训练完成，
已写出 checkpoint
`/tmp/cmo_tg_p7_proxy_train_smoke/tg_p7_proxy_train_smoke_64/checkpoints/model_64_steps.zip`
和 final model
`/tmp/cmo_tg_p7_proxy_train_smoke/tg_p7_proxy_train_smoke_64/final_model.zip`。
