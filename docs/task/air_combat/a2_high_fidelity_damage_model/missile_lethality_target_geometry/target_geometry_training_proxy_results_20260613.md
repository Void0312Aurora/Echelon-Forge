# TG-P7-R3 Training Proxy Database Results

Status: `2026-06-13` pass as opt-in training proxy database plus local
64-step training smoke; the default F-16 unit database remains unchanged.

Chinese canonical:
[target_geometry_training_proxy_results_20260613.zh.md](target_geometry_training_proxy_results_20260613.zh.md).

## What Changed

TG-P7-R3 turns the TG-P7-R2 in-memory projection into a selectable training
proxy database. The generator copies the maintained runtime database, replaces
only the proxy copy of `aircraft/units/f16c_block50.json`, and leaves
[f16c_block50.json](/home/void0312/Workshop/CMO/examples/config/database/aircraft/units/f16c_block50.json)
unchanged.

New artifacts:

- [target_geometry_training_proxy_database_20260613.json](review_packets/f16c_20260611/target_geometry_training_proxy_database_20260613.json)
- [target_geometry_training_proxy_database_20260613/](review_packets/f16c_20260611/target_geometry_training_proxy_database_20260613/)
- [target_geometry_training_proxy_database_20260613/aircraft/units/f16c_block50.json](review_packets/f16c_20260611/target_geometry_training_proxy_database_20260613/aircraft/units/f16c_block50.json)
- [air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_v1.json](/home/void0312/Workshop/CMO/examples/config/training/active/air_combat/air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_v1.json)
- [scene.html](review_packets/f16c_20260611/scene.html), now with a
  `TG-P7 Training Proxy Database` section.

Runtime wiring:

- `runtime.database_path` is resolved and validated during training bootstrap.
- `train.py` passes the resolved path to `WorldBatchVecEnv` and
  `CooperativeWorldBatchVecEnv`.
- The active TG-P7 proxy config selects the proxy database explicitly; baseline
  configs still use `examples/config/database`.

## Acceptance Gate

| Gate | Result |
| --- | --- |
| Default database component count | `26` |
| Proxy database component count | `32` |
| Component count delta | `6` |
| Retired parent components | `2` |
| Split receiver components | `8` |
| Default runtime split receivers active | `0` |
| Proxy runtime split receivers active | `8` |
| Duplicate component names | `0` |
| Behavior regression pass | `true` |
| Proxy database materialized | `true` |
| Training database path ready | `true` |
| Repository unit database modified | `false` |
| Runtime database loader smoke | `true` |
| Local 64-step CPU training smoke | `true` |

## Boundary

This is an initial training proxy, not a claim of true F-16 engineering
geometry. The feature flag is `A2_TARGET_GEOMETRY_PROXY_F16C_R22`, the target
path is `damage_model.hitboxes[].components`, and the training opt-in key is
`runtime.database_path`.

Default runtime projection and the maintained unit database are still the
control path. The proxy is ready for a short training/runtime probe as a
geometry-informed initial agent, while Pk, real-weapon calibration, structural
breakup, and debris remain outside this subproject.

## Next Step

TG-P7-R4 has since run the maintained active 8k TG-P7 proxy probe and the
matching baseline world-batch probe:
[target_geometry_training_probe_results_20260614.md](target_geometry_training_probe_results_20260614.md).
The next step is targeted damage-event trace inspection, not another entrypoint
smoke.

## Validation

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

Current focused result: geometry review tests `2 passed`; training bootstrap and
entry contracts `28 passed`; C++ loader smoke `24 passed`; runtime database load
returned `runtime_load_ok=true`.

Local training smoke:

```bash
PYTHONPATH=build-workshop:. python train.py --scenario scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json --train_config /tmp/cmo_tg_p7_proxy_training_smoke_config.json --output_base /tmp/cmo_tg_p7_proxy_train_smoke --run_name tg_p7_proxy_train_smoke_64 --n_envs 1
```

The temporary config keeps the active proxy database path but reduces the run to
`64` CPU timesteps. Result: training completed, checkpoint
`/tmp/cmo_tg_p7_proxy_train_smoke/tg_p7_proxy_train_smoke_64/checkpoints/model_64_steps.zip`
and final model
`/tmp/cmo_tg_p7_proxy_train_smoke/tg_p7_proxy_train_smoke_64/final_model.zip`
were written.
