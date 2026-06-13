# TG-P7-R5 Damage-Event Trace 结果

状态：`2026-06-14` targeted split-receiver damage-event trace 通过。`8`
个 TG-P7 split receiver 全部能在 opt-in proxy database 的 runtime component
event 名称中被观测到；默认 database 中没有观测到这些 split receiver 名称。

英文辅文：
[target_geometry_damage_event_trace_results_20260614.md](target_geometry_damage_event_trace_results_20260614.md)。

## 执行内容

```bash
PYTHONPATH=build-workshop:. python tools/geometry/target_geometry_damage_event_trace.py --output docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_20260611/target_geometry_damage_event_trace_20260614.json
PYTHONPATH=build-workshop:. pytest -q tests/tools/test_target_geometry_damage_event_trace.py
```

生成证据：

- [target_geometry_damage_event_trace_20260614.json](review_packets/f16c_20260611/target_geometry_damage_event_trace_20260614.json)

## 验收结果

| 验收项 | 结果 |
| --- | ---: |
| 默认 F-16 component count | `26` |
| Proxy F-16 component count | `32` |
| Proxy split receiver component count | `8` |
| Proxy event names 中观测到的 split receiver count | `8` |
| 默认 event names 中观测到的 split receiver count | `0` |
| Proxy event rows 中观测到的 retired parent rows | `0` |
| Duplicate proxy component names | `0` |
| Trace cases passed | `8 / 8` |

已观测到的 proxy split receivers：

- `engine_core_afterburner_segment`
- `engine_core_hot_section_segment`
- `engine_core_forward_compressor_segment`
- `wing_spar_center_left_inner_wing_segment`
- `wing_spar_center_left_root_segment`
- `wing_spar_center_carrythrough_segment`
- `wing_spar_center_right_root_segment`
- `wing_spar_center_right_inner_wing_segment`

## 解释

R5 证明 TG-P7 opt-in proxy 不只是能解析、能进入训练；split receiver 的身份也已经进入
runtime `effects_event`、`component_load_events`，以及在固定 seed 采样触发时进入
`component_damage_events`。这补上了 R4 之后剩余的 targeted trace 缺口。

该 trace 使用 `debug_apply_profiled_local_proximity_hit_with_velocity` 和 synthetic
blast-fragmentation profile。它是几何/event-surface 验收探针，不是真实 AIM-120 Pk、
deterministic fuze、真实 F-16 内部布局，也不是默认路径激活声明。

## 下一步

当前模型已经可以作为下一段维护训练的 opt-in 初始几何代理。默认 runtime 替换仍是独立验收决策，
需要等待更长 proxy training 以及下游 policy/reward 诊断。
