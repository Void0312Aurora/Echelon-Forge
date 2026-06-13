# TG-P7-R2 运行时行为回归结果

状态：`2026-06-13` pass as in-memory behavior regression candidate；仓库 F-16
unit database 仍未改变。

英文辅文：
[target_geometry_runtime_behavior_regression_results_20260613.md](target_geometry_runtime_behavior_regression_results_20260613.md)。

## 本轮变更

TG-P7-R2 将 TG-P7 patch 合同修正为真实 unit-definition 形态：split receiver
records 是 `damage_model.hitboxes[].components` 下的 component records，不是
top-level hitbox records。报告只在内存中应用 TG-P7-R1 candidate：

1. 从 hitbox `2` 移除 `engine_core`，追加它的 `3` 个 split receivers。
2. 从 hitbox `3` 移除 `wing_spar_center`，追加它的 `5` 个 split receivers。
3. 检查 projected component list 是否有重复名、缺失 split receiver 或未退役父级 receiver。

新增 packet 产物：

- [target_geometry_runtime_behavior_regression_20260613.json](review_packets/f16c_20260611/target_geometry_runtime_behavior_regression_20260613.json)
- [target_geometry_runtime_behavior_regression_20260613.csv](review_packets/f16c_20260611/target_geometry_runtime_behavior_regression_20260613.csv)
- [scene.html](review_packets/f16c_20260611/scene.html) 已新增
  `TG-P7 Runtime Behavior Regression Candidate` section。

## 验收门

| Gate | Result |
| --- | --- |
| Base component count | `26` |
| Expected projected component count | `32` |
| Projected component count | `32` |
| patch 后已退役父级 component | `2` |
| patch 后 split component additions present | `8` |
| patch 后 duplicate component names | `0` |
| Runtime active components | `0` |
| Behavior regression pass | `true` |

## 边界

这仍是 in-memory patch regression，不是 active runtime change。它不编辑
[f16c_block50.json](/home/void0312/Workshop/CMO/examples/config/database/aircraft/units/f16c_block50.json)，
不接入 training feature flag，也不声明真实 F-16 内部工程几何。

## 后续

TG-P7-R3 已将该 projection 生成 opt-in training proxy database：
[target_geometry_training_proxy_results_20260613.zh.md](target_geometry_training_proxy_results_20260613.zh.md)。
R3 还完成了本地 `64`-step runtime/training smoke，R4 已完成 active 8k proxy-versus-baseline
对照，同时继续保留默认 `26` component control path；R5 也已完成 targeted
damage-event trace：
[target_geometry_damage_event_trace_results_20260614.zh.md](target_geometry_damage_event_trace_results_20260614.zh.md)。

## 验证

```bash
python -m py_compile tools/geometry/airframe_geometry_review.py
pytest -q tests/tools/test_airframe_geometry_review.py
python tools/geometry/airframe_geometry_review.py --out docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_20260611
cmake --build build-workshop --target ef_test -j2
./build-workshop/ef_test --test-suite=components_basic
git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry tools/geometry/airframe_geometry_review.py tests/tools/test_airframe_geometry_review.py src/tests/test_components_basic.cpp
```

当前聚焦结果：Python geometry review tests `2 passed`；C++ loader smoke
`24 passed`；review packet 已重新生成。
