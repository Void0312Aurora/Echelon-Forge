# TG-P7-R1 运行时激活候选结果

状态：`2026-06-13` pass as parse-ready runtime activation candidate；unit
database 尚未修改，没有 split receiver 进入 runtime active。

英文辅文：
[target_geometry_runtime_activation_results_20260613.md](target_geometry_runtime_activation_results_20260613.md)。

## 本轮变更

TG-P7-R1 将 R22 ownership split payload 转换成面向初始 F-16C 训练几何代理的
unit-database component patch candidate。该 patch 形态明确指向
`damage_model.hitboxes[].components`，使用当前 unit loader 已解析的字段，并且把激活保持在显式
feature flag 之后。

新增 packet 产物：

- [target_geometry_runtime_activation_candidate_20260613.json](review_packets/f16c_20260611/target_geometry_runtime_activation_candidate_20260613.json)
- [target_geometry_runtime_activation_candidate_20260613.csv](review_packets/f16c_20260611/target_geometry_runtime_activation_candidate_20260613.csv)
- [scene.html](review_packets/f16c_20260611/scene.html) 已新增
  `TG-P7 Runtime Activation Candidate` section。

## 验收门

| Gate | Result |
| --- | --- |
| Candidate receiver count | `8` |
| Runtime loader parse-ready count | `8` |
| Unit-database patch additions | `8` |
| Parent receiver retirement plans | `2` |
| Parent receiver retirements applied | `0` |
| Runtime active split components | `0` |
| Behavior tests required before activation | `8` |
| 当前 parse-ready 层 activation blocker count | `0` |
| C++ unit-definition loader parse smoke | pass |

## 候选 Receiver

- `engine_core_afterburner_segment`
- `engine_core_hot_section_segment`
- `engine_core_forward_compressor_segment`
- `wing_spar_center_left_inner_wing_segment`
- `wing_spar_center_left_root_segment`
- `wing_spar_center_carrythrough_segment`
- `wing_spar_center_right_root_segment`
- `wing_spar_center_right_inner_wing_segment`

## 边界

这是真正的 TG-P7 activation package，但还不是已应用的 runtime 改动。JSON 中包含
`unit_database_patch_candidate.add_components` records，可在下一步验收后追加到匹配的
`F-16C_Block50.damage_model.hitboxes[].components` arrays。当前 authority flags 保持：

- `unit_database_modified=false`；
- `runtime_active_component=false`；
- `runtime_damage_model=false`；
- `parent_receiver_retirement_accepted=false`；
- `training_proxy_feature_flag_required=true`。

## 后续

TG-P7-R2 已确认 parent-retirement 与 split-addition projection，TG-P7-R3
已将它生成 opt-in training proxy database：
[target_geometry_training_proxy_results_20260613.zh.md](target_geometry_training_proxy_results_20260613.zh.md)。
R3 还完成了本地 `64`-step proxy training smoke，R4 已完成 active 8k proxy-versus-baseline
对照。下一步是 targeted damage-event trace inspection，而不是继续设计 patch shape。

## 验证

```bash
python -m py_compile tools/geometry/airframe_geometry_review.py
pytest -q tests/tools/test_airframe_geometry_review.py
python tools/geometry/airframe_geometry_review.py --out docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_20260611
cmake --build build-workshop --target ef_test -j2
./build-workshop/ef_test --test-suite=components_basic
```

当前聚焦结果：Python geometry review tests `2 passed`；C++ loader smoke
`24 passed`；review packet 已重新生成。
